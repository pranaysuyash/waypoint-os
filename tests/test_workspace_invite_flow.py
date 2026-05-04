"""
Tests for workspace invite flow — workspace_service and workspace router.

Covers:
- generate_workspace_code: new code created, old codes revoked (status → replaced)
- get_workspace: returns workspace_code field (active code only)
- workspace router: POST /api/workspace/codes endpoint signature

These are unit tests using mock AsyncSession — no live DB needed.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_agency(agency_id="agy-1", name="Test Agency", slug="test-agency"):
    a = MagicMock()
    a.id = agency_id
    a.name = name
    a.slug = slug
    a.email = "owner@test.com"
    a.phone = None
    a.logo_url = None
    a.plan = "starter"
    a.settings = {}
    return a


def _make_active_code(code="WP-abc123", agency_id="agy-1"):
    wc = MagicMock()
    wc.code = code
    wc.agency_id = agency_id
    wc.status = "active"
    return wc


def _make_db(execute_returns: list):
    """Build an AsyncSession mock where execute() returns results in sequence."""
    db = AsyncMock()
    results = []
    for rv in execute_returns:
        r = MagicMock()
        if isinstance(rv, list):
            scalars_mock = MagicMock()
            scalars_mock.all = MagicMock(return_value=rv)
            r.scalars = MagicMock(return_value=scalars_mock)
        else:
            r.scalar_one_or_none = MagicMock(return_value=rv)
        results.append(r)
    db.execute = AsyncMock(side_effect=results)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ── workspace_service: generate_workspace_code ───────────────────────────────

class TestGenerateWorkspaceCode:

    @pytest.mark.asyncio
    async def test_new_code_is_created(self):
        from spine_api.services.workspace_service import generate_workspace_code

        old_code = _make_active_code(code="WP-old")
        db = _make_db([[old_code]])  # first execute returns scalars list for old codes

        async def set_code_attr(obj):
            obj.code = "WP-new123"
        db.refresh.side_effect = set_code_attr

        with patch("spine_api.services.workspace_service.secrets.token_urlsafe", return_value="new123"):
            result = await generate_workspace_code(db, agency_id="agy-1", created_by="usr-1")

        assert result == "WP-new123"
        db.add.assert_called_once()
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_old_codes_are_revoked(self):
        """All previously active codes must be set to status='replaced' before the new one is added."""
        from spine_api.services.workspace_service import generate_workspace_code

        old1 = _make_active_code(code="WP-old1")
        old2 = _make_active_code(code="WP-old2")
        db = _make_db([[old1, old2]])

        async def set_code_attr(obj):
            obj.code = "WP-fresh"
        db.refresh.side_effect = set_code_attr

        with patch("spine_api.services.workspace_service.secrets.token_urlsafe", return_value="fresh"):
            await generate_workspace_code(db, agency_id="agy-1", created_by="usr-1")

        assert old1.status == "replaced"
        assert old2.status == "replaced"

    @pytest.mark.asyncio
    async def test_no_existing_codes_still_works(self):
        """Agency with no prior codes: generate succeeds."""
        from spine_api.services.workspace_service import generate_workspace_code

        db = _make_db([[]])  # empty list — no existing codes

        async def set_code_attr(obj):
            obj.code = "WP-first"
        db.refresh.side_effect = set_code_attr

        with patch("spine_api.services.workspace_service.secrets.token_urlsafe", return_value="first"):
            result = await generate_workspace_code(db, agency_id="agy-2", created_by="usr-2")

        assert result == "WP-first"
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_code_type_stored_on_new_code(self):
        """code_type is passed through to the new WorkspaceCode object."""
        from spine_api.services.workspace_service import generate_workspace_code
        from spine_api.models.tenant import WorkspaceCode as WorkspaceCodeModel

        db = _make_db([[]])
        async def noop_refresh(obj): obj.code = "WP-x"
        db.refresh.side_effect = noop_refresh

        added: list = []
        db.add = lambda obj: added.append(obj)

        with patch("spine_api.services.workspace_service.secrets.token_urlsafe", return_value="x"):
            await generate_workspace_code(db, agency_id="agy-1", created_by="usr-1", code_type="external")

        new_code_obj = next((o for o in added if isinstance(o, WorkspaceCodeModel)), None)
        assert new_code_obj is not None, "WorkspaceCode must be added to db"
        assert new_code_obj.code_type == "external"


# ── workspace_service: get_workspace ────────────────────────────────────────

class TestGetWorkspace:

    @pytest.mark.asyncio
    async def test_returns_workspace_code_when_active(self):
        from spine_api.services.workspace_service import get_workspace

        agency = _make_agency()
        active_code = _make_active_code(code="WP-current")
        db = _make_db([agency, active_code])

        result = await get_workspace(db, "agy-1")

        assert result is not None
        assert result["workspace_code"] == "WP-current"

    @pytest.mark.asyncio
    async def test_returns_none_for_workspace_code_when_no_active_code(self):
        from spine_api.services.workspace_service import get_workspace

        agency = _make_agency()
        db = _make_db([agency, None])

        result = await get_workspace(db, "agy-1")

        assert result is not None
        assert result["workspace_code"] is None

    @pytest.mark.asyncio
    async def test_returns_none_when_agency_not_found(self):
        from spine_api.services.workspace_service import get_workspace

        db = _make_db([None])

        result = await get_workspace(db, "agy-ghost")

        assert result is None


# ── workspace router: POST /api/workspace/codes ───────────────────────────────

class TestWorkspaceCodesEndpoint:

    def test_post_codes_handler_exists(self):
        from spine_api.routers.workspace import router

        routes = {r.path: r for r in router.routes}
        assert "/api/workspace/codes" in routes, "POST /api/workspace/codes route must exist"

    def test_post_codes_handler_requires_team_manage_permission(self):
        """
        The codes endpoint must use require_permission("team:manage") so that
        junior_agent and viewer roles cannot revoke the workspace invite link.
        """
        import inspect
        from spine_api.routers.workspace import post_generate_workspace_code
        from spine_api.core.auth import ROLE_PERMISSIONS

        params = list(inspect.signature(post_generate_workspace_code).parameters.keys())
        assert "membership" in params, (
            "post_generate_workspace_code must have membership dep (provided by require_permission)"
        )
        # Verify the permission matrix: only owner/admin have team:manage.
        for role in ("owner", "admin"):
            perms = ROLE_PERMISSIONS.get(role, [])
            assert "*" in perms or "team:manage" in perms, (
                f"{role} must have team:manage to generate invite codes"
            )
        for role in ("senior_agent", "junior_agent", "viewer"):
            perms = ROLE_PERMISSIONS.get(role, [])
            assert "team:manage" not in perms and "*" not in perms, (
                f"{role} must NOT have team:manage — invite link regeneration is owner/admin only"
            )

    def test_generate_code_request_allows_internal_and_external(self):
        from spine_api.routers.workspace import GenerateCodeRequest

        req_internal = GenerateCodeRequest(code_type="internal")
        assert req_internal.code_type == "internal"

        req_external = GenerateCodeRequest(code_type="external")
        assert req_external.code_type == "external"

    def test_generate_code_request_rejects_invalid_type(self):
        from pydantic import ValidationError
        from spine_api.routers.workspace import GenerateCodeRequest

        with pytest.raises(ValidationError):
            GenerateCodeRequest(code_type="superadmin")
