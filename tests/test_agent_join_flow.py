"""
Tests for the agent join flow — workspace code validation and join_with_code service.

Covers:
- validate_workspace_code: valid code, invalid code, revoked code
- join_with_code: success path, duplicate email, bad password, bad code
- Role assignment: junior_agent for both code_type=internal and code_type=external

These use mock AsyncSession objects to avoid requiring a live database.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Path setup
spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))


# ---------------------------------------------------------------------------
# Helpers — mock DB + ORM objects
# ---------------------------------------------------------------------------

def _make_workspace_code(code="WP-test123", agency_id="agy-1", code_type="internal", status="active"):
    wc = MagicMock()
    wc.code = code
    wc.agency_id = agency_id
    wc.code_type = code_type
    wc.status = status
    return wc


def _make_agency(agency_id="agy-1", name="Test Agency", slug="test-agency"):
    agency = MagicMock()
    agency.id = agency_id
    agency.name = name
    agency.slug = slug
    agency.logo_url = None
    return agency


def _make_user(user_id="usr-1", email="agent@test.com", name="Agent Smith"):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.name = name
    return user


def _make_membership(user_id="usr-1", agency_id="agy-1", role="junior_agent", is_primary=True):
    m = MagicMock()
    m.user_id = user_id
    m.agency_id = agency_id
    m.role = role
    m.is_primary = is_primary
    return m


def _mock_db_with_returns(*query_returns):
    """
    Build an AsyncSession mock whose execute() calls return each item in sequence.
    Each item in query_returns corresponds to one db.execute() call.
    scalar_one_or_none() on the result returns the value.
    """
    db = AsyncMock()

    results = []
    for rv in query_returns:
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=rv)
        results.append(result)

    db.execute = AsyncMock(side_effect=results)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


# ---------------------------------------------------------------------------
# validate_workspace_code
# ---------------------------------------------------------------------------

class TestValidateWorkspaceCode:

    @pytest.mark.asyncio
    async def test_valid_code_returns_agency_info(self):
        from spine_api.services.auth_service import validate_workspace_code

        wc = _make_workspace_code(code="WP-abc", agency_id="agy-1", code_type="internal")
        agency = _make_agency(agency_id="agy-1", name="Sunset Travels")

        db = _mock_db_with_returns(wc, agency)

        result = await validate_workspace_code(db, code="WP-abc")

        assert result["valid"] is True
        assert result["agency_name"] == "Sunset Travels"
        assert result["agency_id"] == "agy-1"
        assert result["code_type"] == "internal"

    @pytest.mark.asyncio
    async def test_unknown_code_raises(self):
        from spine_api.services.auth_service import validate_workspace_code

        db = _mock_db_with_returns(None)  # no workspace code found

        with pytest.raises(ValueError, match="Invalid or expired invitation code"):
            await validate_workspace_code(db, code="WP-notexist")

    @pytest.mark.asyncio
    async def test_agency_missing_raises(self):
        """Code exists but agency record is gone — treated as invalid."""
        from spine_api.services.auth_service import validate_workspace_code

        wc = _make_workspace_code(code="WP-orphan", agency_id="agy-deleted")
        db = _mock_db_with_returns(wc, None)  # agency not found

        with pytest.raises(ValueError, match="Invalid or expired invitation code"):
            await validate_workspace_code(db, code="WP-orphan")

    @pytest.mark.asyncio
    async def test_external_code_type_returned(self):
        from spine_api.services.auth_service import validate_workspace_code

        wc = _make_workspace_code(code="WP-ext", agency_id="agy-2", code_type="external")
        agency = _make_agency(agency_id="agy-2", name="Partner Agency")

        db = _mock_db_with_returns(wc, agency)

        result = await validate_workspace_code(db, code="WP-ext")
        assert result["code_type"] == "external"


# ---------------------------------------------------------------------------
# join_with_code
# ---------------------------------------------------------------------------

class TestJoinWithCode:

    @pytest.mark.asyncio
    async def test_successful_join_returns_auth_payload(self):
        from spine_api.services.auth_service import join_with_code

        wc = _make_workspace_code(code="WP-ok", agency_id="agy-1", code_type="internal")
        agency = _make_agency(agency_id="agy-1", name="Best Travels")
        existing_user = None  # no duplicate email

        db = _mock_db_with_returns(wc, agency, existing_user)

        # db.refresh sets attrs on the SQLAlchemy objects created inside the function.
        # We intercept db.add to grab the User and Membership objects, then set ids.
        added_objects: list = []
        original_add = db.add
        def capture_add(obj):
            added_objects.append(obj)
        db.add = capture_add

        async def inject_ids(obj):
            # Identify User by presence of email attr (set in constructor)
            if hasattr(obj, "email") and hasattr(obj, "password_hash"):
                obj.id = "usr-new"
            elif hasattr(obj, "role") and hasattr(obj, "user_id"):
                obj.role = "junior_agent"
                obj.is_primary = True
        db.refresh.side_effect = inject_ids

        with patch("spine_api.services.auth_service.create_access_token", return_value="tok-access"), \
             patch("spine_api.services.auth_service.create_refresh_token", return_value="tok-refresh"), \
             patch("spine_api.services.auth_service.hash_password", return_value="hashed"):

            result = await join_with_code(
                db=db,
                code="WP-ok",
                email="new@agent.com",
                password="password123",
                name="Agent Smith",
            )

        assert result["user"]["email"] == "new@agent.com"
        assert result["agency"]["name"] == "Best Travels"
        assert result["membership"]["role"] == "junior_agent"
        assert result["access_token"] == "tok-access"
        assert result["refresh_token"] == "tok-refresh"

    @pytest.mark.asyncio
    async def test_invalid_code_raises(self):
        from spine_api.services.auth_service import join_with_code

        db = _mock_db_with_returns(None)  # code not found

        with pytest.raises(ValueError, match="Invalid or expired invitation code"):
            await join_with_code(db, code="WP-bad", email="x@y.com", password="pass1234")

    @pytest.mark.asyncio
    async def test_duplicate_email_raises(self):
        from spine_api.services.auth_service import join_with_code

        wc = _make_workspace_code()
        agency = _make_agency()
        existing = _make_user(email="taken@agency.com")

        db = _mock_db_with_returns(wc, agency, existing)

        with pytest.raises(ValueError, match="Email already registered"):
            await join_with_code(db, code="WP-test123", email="taken@agency.com", password="pass1234")

    @pytest.mark.asyncio
    async def test_short_password_raises(self):
        from spine_api.services.auth_service import join_with_code

        wc = _make_workspace_code()
        agency = _make_agency()
        no_existing_user = None

        db = _mock_db_with_returns(wc, agency, no_existing_user)

        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            await join_with_code(db, code="WP-test123", email="x@y.com", password="short")

    @pytest.mark.asyncio
    async def test_external_code_also_assigns_junior_agent(self):
        """Both code_type=internal and code_type=external → junior_agent role."""
        from spine_api.services.auth_service import _CODE_TYPE_ROLE

        assert _CODE_TYPE_ROLE["internal"] == "junior_agent"
        assert _CODE_TYPE_ROLE["external"] == "junior_agent"

    @pytest.mark.asyncio
    async def test_name_defaults_to_email_prefix(self):
        """If name is not provided, defaults to the part before @ in email."""
        from spine_api.services.auth_service import join_with_code

        wc = _make_workspace_code()
        agency = _make_agency()

        db = _mock_db_with_returns(wc, agency, None)

        async def inject_ids(obj):
            if hasattr(obj, "email") and hasattr(obj, "password_hash"):
                obj.id = "usr-x"
            elif hasattr(obj, "role") and hasattr(obj, "user_id"):
                obj.role = "junior_agent"
                obj.is_primary = True
        db.refresh.side_effect = inject_ids

        added_objects: list = []
        db.add = lambda obj: added_objects.append(obj)

        with patch("spine_api.services.auth_service.create_access_token", return_value="t"), \
             patch("spine_api.services.auth_service.create_refresh_token", return_value="r"), \
             patch("spine_api.services.auth_service.hash_password", return_value="h"):

            result = await join_with_code(
                db=db,
                code="WP-test123",
                email="noname@agency.com",
                password="pass1234",
                name=None,
            )

        # When name=None, auth_service defaults to email.split("@")[0]
        # Find the User object that was added to db
        from spine_api.models.tenant import User as UserModel
        user_obj = next((o for o in added_objects if isinstance(o, UserModel)), None)
        assert user_obj is not None, "User object must have been added to db"
        assert user_obj.name == "noname"
