"""
Phase 0 verification script.

Run with: PYTHONPATH=spine_api:. uv run python scripts/verify_phase0.py
"""

import asyncio
import sys

sys.path.insert(0, "spine_api")


async def verify_database():
    """Verify async database connection and model operations."""
    from sqlalchemy import select
from spine_api.core.database import async_session_maker
from spine_api.models.tenant import Agency, User, Membership, WorkspaceCode

    async with async_session_maker() as session:
        # Create an agency
        agency = Agency(
            name="Test Agency",
            slug="test-agency",
            email="test@agency.com",
        )
        session.add(agency)
        await session.flush()

        # Create a user
        user = User(
            email="owner@test.com",
            password_hash="hashed_password",
            name="Test Owner",
        )
        session.add(user)
        await session.flush()

        # Create membership
        membership = Membership(
            user_id=user.id,
            agency_id=agency.id,
            role="owner",
            is_primary=True,
        )
        session.add(membership)

        # Create workspace code
        code = WorkspaceCode(
            agency_id=agency.id,
            code="TRI-1234-TEST",
            code_type="internal",
            created_by=user.id,
        )
        session.add(code)

        await session.commit()

        # Verify we can query them back
        result = await session.execute(select(Agency).where(Agency.slug == "test-agency"))
        fetched_agency = result.scalar_one_or_none()
        assert fetched_agency is not None, "Agency not found"
        assert fetched_agency.name == "Test Agency"

        result = await session.execute(select(User).where(User.email == "owner@test.com"))
        fetched_user = result.scalar_one_or_none()
        assert fetched_user is not None, "User not found"
        assert fetched_user.name == "Test Owner"

        result = await session.execute(
            select(Membership).where(Membership.user_id == user.id)
        )
        fetched_membership = result.scalar_one_or_none()
        assert fetched_membership is not None, "Membership not found"
        assert fetched_membership.role == "owner"

        result = await session.execute(
            select(WorkspaceCode).where(WorkspaceCode.code == "TRI-1234-TEST")
        )
        fetched_code = result.scalar_one_or_none()
        assert fetched_code is not None, "WorkspaceCode not found"
        assert fetched_code.code_type == "internal"

        print("✅ Database models: CREATE and QUERY working")

        # Cleanup
        await session.delete(fetched_code)
        await session.delete(fetched_membership)
        await session.delete(fetched_user)
        await session.delete(fetched_agency)
        await session.commit()


def verify_security():
    """Verify password hashing and JWT operations."""
    from core.security import (
        hash_password,
        verify_password,
        create_access_token,
        decode_token,
        create_refresh_token,
    )

    # Test password hashing
    password = "test_password_123"
    hashed = hash_password(password)
    assert verify_password(password, hashed), "Password verification failed"
    assert not verify_password("wrong_password", hashed), "Wrong password should fail"
    print("✅ Password hashing: HASH and VERIFY working")

    # Test JWT creation and decoding
    token = create_access_token(
        user_id="usr_test123",
        agency_id="agy_test456",
        role="owner",
    )
    payload = decode_token(token)
    assert payload["sub"] == "usr_test123", "JWT sub mismatch"
    assert payload["agency_id"] == "agy_test456", "JWT agency_id mismatch"
    assert payload["role"] == "owner", "JWT role mismatch"
    assert payload["type"] == "access", "JWT type mismatch"
    print("✅ JWT tokens: CREATE and DECODE working")

    # Test refresh token
    refresh = create_refresh_token("usr_test123")
    refresh_payload = decode_token(refresh)
    assert refresh_payload["sub"] == "usr_test123"
    assert refresh_payload["type"] == "refresh"
    print("✅ Refresh tokens: CREATE and DECODE working")


async def main():
    print("=" * 60)
    print("PHASE 0 VERIFICATION")
    print("=" * 60)

    try:
        verify_security()
        await verify_database()
        print("=" * 60)
        print("✅ ALL PHASE 0 ACCEPTANCE CRITERIA PASSED")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
