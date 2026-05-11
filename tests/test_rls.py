"""
Tests for PostgreSQL RLS integration (spine_api/core/rls.py).

What's tested:
  - set_rls_agency / get_rls_agency round-trip via ContextVar
  - ContextVar isolation between asyncio tasks (cross-request bleed prevention)
  - apply_rls issues the correct transaction-local SQL statement
  - get_rls_db calls apply_rls when agency_id is set
  - get_rls_db skips apply_rls when ContextVar is unset (unauthenticated path)
  - auth.get_current_membership calls set_rls_agency as a side-effect

These tests do NOT require a live PostgreSQL database.
apply_rls and get_rls_db use an AsyncSession mock.
"""

import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure spine_api is importable without install
spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))

if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"


# ── ContextVar round-trip ─────────────────────────────────────────────────────

class TestRlsContextVar:

    def test_set_and_get(self):
        from spine_api.core.rls import set_rls_agency, get_rls_agency, _current_agency_id
        token = _current_agency_id.set(None)  # reset for isolation
        try:
            assert get_rls_agency() is None
            set_rls_agency("agy-test-001")
            assert get_rls_agency() == "agy-test-001"
        finally:
            _current_agency_id.reset(token)

    def test_default_is_none(self):
        from spine_api.core.rls import get_rls_agency, _current_agency_id
        token = _current_agency_id.set(None)
        try:
            assert get_rls_agency() is None
        finally:
            _current_agency_id.reset(token)

    @pytest.mark.asyncio
    async def test_context_isolated_between_tasks(self):
        """
        Two concurrent asyncio tasks must not share the same ContextVar value.
        Task A sets agency A; task B sets agency B; neither sees the other's value.
        """
        from spine_api.core.rls import set_rls_agency, get_rls_agency, _current_agency_id

        results = {}

        async def task_a():
            token = _current_agency_id.set(None)
            try:
                set_rls_agency("agy-aaaa")
                await asyncio.sleep(0)  # yield to event loop — task B may run here
                results["a"] = get_rls_agency()
            finally:
                _current_agency_id.reset(token)

        async def task_b():
            token = _current_agency_id.set(None)
            try:
                set_rls_agency("agy-bbbb")
                await asyncio.sleep(0)
                results["b"] = get_rls_agency()
            finally:
                _current_agency_id.reset(token)

        await asyncio.gather(task_a(), task_b())

        assert results["a"] == "agy-aaaa", f"Task A saw wrong agency: {results['a']}"
        assert results["b"] == "agy-bbbb", f"Task B saw wrong agency: {results['b']}"


# ── apply_rls SQL generation ──────────────────────────────────────────────────

class TestApplyRls:

    @pytest.mark.asyncio
    async def test_issues_transaction_local_setting(self):
        """apply_rls must set app.current_agency_id transaction-locally with a bound param."""
        from spine_api.core.rls import apply_rls

        session = AsyncMock()
        await apply_rls(session, "agy-test-123")

        assert session.execute.called
        call_args = session.execute.call_args
        # First positional arg is the text() clause
        sql_clause = call_args[0][0]
        sql_str = str(sql_clause)
        assert "set_config" in sql_str
        assert "app.current_agency_id" in sql_str
        assert "true" in sql_str

        # Second arg is the parameter dict
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert params.get("agency_id") == "agy-test-123"

    @pytest.mark.asyncio
    async def test_uses_parameterized_query(self):
        """
        apply_rls must use a bound parameter, not string interpolation.
        This prevents SQL injection via a crafted agency_id.
        """
        from spine_api.core.rls import apply_rls

        session = AsyncMock()
        evil = "'; DROP TABLE trips; --"
        await apply_rls(session, evil)

        call_args = session.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        # The evil string must appear in the parameters dict, never in the SQL string
        sql_str = str(call_args[0][0])
        assert evil not in sql_str, "agency_id must be parameterized, not interpolated"
        assert params.get("agency_id") == evil


# ── get_rls_db dependency ─────────────────────────────────────────────────────

class TestGetRlsDb:

    @pytest.mark.asyncio
    async def test_calls_apply_rls_when_agency_set(self):
        """get_rls_db must call apply_rls when ContextVar holds an agency_id."""
        from spine_api.core import rls

        mock_session = AsyncMock()

        async def fake_get_db():
            yield mock_session

        with patch.object(rls, "_current_agency_id") as mock_cv, \
             patch.object(rls, "apply_rls", new_callable=AsyncMock) as mock_apply:

            mock_cv.get.return_value = "agy-test-001"

            # Drain the async generator
            gen = rls.get_rls_db(db=mock_session)
            session = await gen.__anext__()
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_apply.assert_awaited_once_with(mock_session, "agy-test-001")
            assert session is mock_session

    @pytest.mark.asyncio
    async def test_skips_apply_rls_when_no_agency(self):
        """get_rls_db must NOT call apply_rls when ContextVar is unset."""
        from spine_api.core import rls

        mock_session = AsyncMock()

        with patch.object(rls, "_current_agency_id") as mock_cv, \
             patch.object(rls, "apply_rls", new_callable=AsyncMock) as mock_apply:

            mock_cv.get.return_value = None

            gen = rls.get_rls_db(db=mock_session)
            session = await gen.__anext__()
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_apply.assert_not_awaited()
            assert session is mock_session


# ── Auth wires RLS ────────────────────────────────────────────────────────────

class TestAuthWiresRls:
    """
    Verify that get_current_membership calls set_rls_agency as a side-effect.
    This ensures the ContextVar is populated for every authenticated request
    without route handlers needing to call it explicitly.
    """

    @pytest.mark.asyncio
    async def test_get_current_membership_sets_rls_agency(self):
        from spine_api.core import auth

        user = MagicMock()
        user.id = "usr-001"

        membership = MagicMock()
        membership.user_id = "usr-001"
        membership.agency_id = "agy-test-777"
        membership.is_primary = True

        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=membership)

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result_mock)

        # Patch the name as bound inside auth.py (not in the rls module).
        with patch("spine_api.core.auth.set_rls_agency") as mock_set:
            result = await auth.get_current_membership(user=user, db=db)

        mock_set.assert_called_once_with("agy-test-777")
        assert result.agency_id == "agy-test-777"

    @pytest.mark.asyncio
    async def test_get_current_membership_does_not_set_rls_on_missing_membership(self):
        """If membership lookup fails (403), set_rls_agency must NOT be called."""
        from fastapi import HTTPException
        from spine_api.core import auth

        user = MagicMock()
        user.id = "usr-ghost"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=None)

        db = AsyncMock()
        db.execute = AsyncMock(return_value=result_mock)

        with patch("spine_api.core.auth.set_rls_agency") as mock_set:
            with pytest.raises(HTTPException) as exc:
                await auth.get_current_membership(user=user, db=db)

        mock_set.assert_not_called()
        assert exc.value.status_code == 403


# ── Runtime posture evaluation ────────────────────────────────────────────────

class TestRlsRuntimePosture:

    def test_non_owner_role_with_enabled_rls_has_no_risks(self):
        from spine_api.core.rls import RlsRuntimePosture, RlsTablePosture

        posture = RlsRuntimePosture(
            current_user="waypoint_app",
            is_superuser=False,
            bypasses_rls=False,
            tables=(
                RlsTablePosture(
                    table_name="trips",
                    owner="waypoint_owner",
                    rls_enabled=True,
                    force_rls=False,
                ),
            ),
            expected_tables=("trips",),
        )

        assert posture.risks == ()
        assert posture.is_enforced_for_runtime_role is True

    def test_owner_role_without_force_rls_is_reported_as_bypass_risk(self):
        from spine_api.core.rls import RlsRuntimePosture, RlsTablePosture

        posture = RlsRuntimePosture(
            current_user="waypoint",
            is_superuser=False,
            bypasses_rls=False,
            tables=(
                RlsTablePosture(
                    table_name="trips",
                    owner="waypoint",
                    rls_enabled=True,
                    force_rls=False,
                ),
            ),
            expected_tables=("trips",),
        )

        assert posture.is_enforced_for_runtime_role is False
        assert posture.risks == (
            "trips is owned by runtime role waypoint and FORCE RLS is disabled",
        )

    def test_missing_or_disabled_tables_are_reported_as_risks(self):
        from spine_api.core.rls import RlsRuntimePosture, RlsTablePosture

        posture = RlsRuntimePosture(
            current_user="waypoint_app",
            is_superuser=False,
            bypasses_rls=False,
            tables=(
                RlsTablePosture(
                    table_name="trips",
                    owner="waypoint_owner",
                    rls_enabled=False,
                    force_rls=False,
                ),
            ),
            expected_tables=("trips", "memberships"),
        )

        assert posture.risks == (
            "memberships is missing from the live database",
            "trips has row-level security disabled",
        )
