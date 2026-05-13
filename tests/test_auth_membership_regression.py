"""
Regression tests for orphan users without agency memberships.

These tests ensure that existing users without memberships can still log in
and use the system. The fix backfills a default agency + owner membership
both at startup and at login/refresh time.
"""

import os
import sys
import uuid as uuid_mod
from pathlib import Path

import pytest

spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))


async def _make_session():
    """Create a fresh async DB session for test isolation."""
    from spine_api.core.database import async_session_maker
    return async_session_maker()


class TestOrphanUserLogin:
    """Verify login and refresh succeed for users without memberships."""

    @pytest.mark.asyncio
    async def test_login_creates_membership_for_orphan_user(self):
        """Orphan user login should backfill agency + membership and succeed."""
        from spine_api.services.auth_service import login
        from spine_api.models.tenant import Membership
        from spine_api.services.auth_service import hash_password
        from spine_api.models.tenant import User
        from sqlalchemy import select
        from spine_api.core.rls import apply_rls

        db = await _make_session()
        try:
            unique = uuid_mod.uuid4().hex[:8]
            email = f"orphan-login-{unique}@example.com"

            user = User(
                email=email,
                password_hash=hash_password("testpassword123"),
                name="Orphan Login Test",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Verify no memberships exist
            memberships_result = await db.execute(
                select(Membership).where(Membership.user_id == user.id)
            )
            assert memberships_result.scalar_one_or_none() is None

            # Act: login should backfill and succeed
            result = await login(db=db, email=user.email, password="testpassword123")

            # Assert login result shape
            assert result["user"]["id"] == user.id
            assert result["agency"]["id"] is not None
            assert result["membership"]["role"] == "owner"
            assert result["access_token"] is not None
            assert result["refresh_token"] is not None

            # Verify DB now has a membership by setting RLS on the SAME session
            agency_id = result["agency"]["id"]
            await apply_rls(db, agency_id)
            memberships_result = await db.execute(
                select(Membership).where(Membership.user_id == user.id)
            )
            membership = memberships_result.scalar_one_or_none()
            assert membership is not None
            assert membership.role == "owner"
            assert membership.is_primary is True
        finally:
            await db.rollback()
            await db.close()

    @pytest.mark.asyncio
    async def test_refresh_token_creates_membership_for_orphan_user(self):
        """Orphan user refresh should backfill agency + membership and succeed."""
        from spine_api.services.auth_service import refresh_access_token
        from spine_api.core.security import create_refresh_token, decode_token
        from spine_api.models.tenant import User, Membership
        from spine_api.services.auth_service import hash_password
        from sqlalchemy import select
        from spine_api.core.rls import apply_rls

        db = await _make_session()
        try:
            unique = uuid_mod.uuid4().hex[:8]
            email = f"orphan-refresh-{unique}@example.com"

            user = User(
                email=email,
                password_hash=hash_password("testpassword123"),
                name="Orphan Refresh Test",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Verify no memberships
            memberships_result = await db.execute(
                select(Membership).where(Membership.user_id == user.id)
            )
            assert memberships_result.scalar_one_or_none() is None

            refresh_token_str = create_refresh_token(user_id=user.id)

            # Act
            result = await refresh_access_token(db=db, refresh_token_str=refresh_token_str)

            # Assert tokens returned
            assert result["access_token"] is not None
            assert result["refresh_token"] is not None

            # Decode access token to get agency_id for RLS verification
            payload = decode_token(result["access_token"])
            agency_id = payload.get("agency_id")
            assert agency_id is not None

            # Verify DB now has a membership by setting RLS on the SAME session
            await apply_rls(db, agency_id)
            memberships_result = await db.execute(
                select(Membership).where(Membership.user_id == user.id)
            )
            membership = memberships_result.scalar_one_or_none()
            assert membership is not None
            assert membership.role == "owner"
            assert membership.is_primary is True
        finally:
            await db.rollback()
            await db.close()

    @pytest.mark.asyncio
    async def test_existing_user_with_membership_unchanged(self):
        """Users that already have memberships should not get a duplicate agency."""
        from spine_api.services.auth_service import signup, login

        db = await _make_session()
        try:
            unique = uuid_mod.uuid4().hex[:8]
            email = f"existing-member-{unique}@example.com"

            # Signup creates user + agency + membership
            result = await signup(
                db=db,
                email=email,
                password="testpassword123",
                name="Existing Member",
            )
            original_agency_id = result["agency"]["id"]
            original_membership = result["membership"]

            # Act: login again should return SAME agency/membership
            login_result = await login(
                db=db,
                email=email,
                password="testpassword123",
            )

            assert login_result["agency"]["id"] == original_agency_id
            assert login_result["membership"]["role"] == original_membership["role"]
        finally:
            await db.rollback()
            await db.close()

    @pytest.mark.asyncio
    async def test_backfill_idempotent(self):
        """Calling _ensure_user_membership twice for same orphan user should not create duplicates."""
        from spine_api.services.auth_service import _ensure_user_membership, hash_password
        from spine_api.models.tenant import User, Membership
        from sqlalchemy import select
        from spine_api.core.rls import apply_rls

        db = await _make_session()
        try:
            unique = uuid_mod.uuid4().hex[:8]
            email = f"idempotent-{unique}@example.com"

            user = User(
                email=email,
                password_hash=hash_password("testpassword123"),
                name="Idempotent Test",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # First call
            m1 = await _ensure_user_membership(db, user)
            await db.commit()
            a1 = m1.agency_id

            # Second call
            m2 = await _ensure_user_membership(db, user)
            await db.commit()
            a2 = m2.agency_id

            assert a1 == a2

            # Count memberships by resetting RLS to the agency we know
            await apply_rls(db, a1)
            result = await db.execute(
                select(Membership).where(Membership.user_id == user.id)
            )
            memberships = result.scalars().all()
            assert len(memberships) == 1
        finally:
            await db.rollback()
            await db.close()
