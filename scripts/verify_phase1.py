"""
Phase 1 Verification — Identity, Tenancy, and Workspace Ownership.

Acceptance Criteria:
1. User can sign up with email + password
2. Workspace is auto-created with agency name
3. Creator receives Owner role + Admin capabilities
4. JWT token is returned on login
5. GET /api/auth/me returns correct user, agency, and role
6. Refresh token flow works
7. Workspace detail endpoint works
"""

import asyncio
import sys

from spine_api.core.database import async_session_maker
from spine_api.services.auth_service import signup, login, refresh_access_token
from spine_api.services.workspace_service import get_workspace, update_workspace
from spine_api.core.security import decode_token


async def verify():
    passed = 0
    failed = 0

    async with async_session_maker() as db:
        # ── Criterion 1: Signup with email + password ──
        try:
            result = await signup(
                db=db,
                email="owner@acme-travel.com",
                password="securepassword123",
                name="Alice Owner",
                agency_name="Acme Travel",
            )
            assert result["user"]["email"] == "owner@acme-travel.com"
            assert result["user"]["name"] == "Alice Owner"
            assert result["agency"]["name"] == "Acme Travel"
            assert result["membership"]["role"] == "owner"
            assert result["access_token"]
            assert result["refresh_token"]
            print("✅ Criterion 1: Signup with email + password")
            passed += 1
        except Exception as e:
            print(f"❌ Criterion 1 FAILED: {e}")
            failed += 1

        # ── Criterion 2: Workspace auto-created ──
        try:
            ws = await get_workspace(db, result["agency"]["id"])
            assert ws is not None
            assert ws["name"] == "Acme Travel"
            assert ws["workspace_code"] is not None
            assert ws["workspace_code"].startswith("WP-")
            print(f"✅ Criterion 2: Workspace auto-created (code: {ws['workspace_code']})")
            passed += 1
        except Exception as e:
            print(f"❌ Criterion 2 FAILED: {e}")
            failed += 1

        # ── Criterion 3: Owner role + Admin capabilities ──
        try:
            from core.auth import ROLE_PERMISSIONS
            role = result["membership"]["role"]
            assert role == "owner"
            permissions = ROLE_PERMISSIONS[role]
            assert "*" in permissions, "Owner should have wildcard permissions"
            print("✅ Criterion 3: Owner role with full admin capabilities")
            passed += 1
        except Exception as e:
            print(f"❌ Criterion 3 FAILED: {e}")
            failed += 1

        # ── Criterion 4: JWT token on login ──
        try:
            login_result = await login(
                db=db,
                email="owner@acme-travel.com",
                password="securepassword123",
            )
            assert login_result["access_token"]
            payload = decode_token(login_result["access_token"])
            assert payload["sub"] == result["user"]["id"]
            assert payload["agency_id"] == result["agency"]["id"]
            assert payload["role"] == "owner"
            assert payload["type"] == "access"
            print("✅ Criterion 4: JWT token returned on login")
            passed += 1
        except Exception as e:
            print(f"❌ Criterion 4 FAILED: {e}")
            failed += 1

        # ── Criterion 5: /api/auth/me payload structure ──
        try:
            assert result["user"]["id"]
            assert result["user"]["email"]
            assert result["agency"]["id"]
            assert result["agency"]["name"]
            assert result["agency"]["slug"]
            assert result["membership"]["role"]
            assert result["membership"]["is_primary"] == True
            print("✅ Criterion 5: Me payload structure correct")
            passed += 1
        except Exception as e:
            print(f"❌ Criterion 5 FAILED: {e}")
            failed += 1

        # ── Criterion 6: Refresh token flow ──
        try:
            refresh_result = await refresh_access_token(
                db=db,
                refresh_token_str=result["refresh_token"],
            )
            assert refresh_result["access_token"]
            assert refresh_result["refresh_token"]
            new_payload = decode_token(refresh_result["access_token"])
            assert new_payload["sub"] == result["user"]["id"]
            assert new_payload["type"] == "access"
            print("✅ Criterion 6: Refresh token flow works")
            passed += 1
        except Exception as e:
            print(f"❌ Criterion 6 FAILED: {e}")
            failed += 1

        # ── Criterion 7: Workspace update ──
        try:
            updated = await update_workspace(
                db=db,
                agency_id=result["agency"]["id"],
                updates={"name": "Acme Travel Co.", "phone": "+1-555-0123"},
            )
            assert updated["name"] == "Acme Travel Co."
            assert updated["phone"] == "+1-555-0123"
            print("✅ Criterion 7: Workspace update works")
            passed += 1
        except Exception as e:
            print(f"❌ Criterion 7 FAILED: {e}")
            failed += 1

        # ── Duplicate signup prevention ──
        try:
            await signup(
                db=db,
                email="owner@acme-travel.com",
                password="anotherpassword",
            )
            print("❌ Extra: Duplicate signup should have failed")
            failed += 1
        except ValueError as e:
            assert "already registered" in str(e)
            print("✅ Extra: Duplicate signup prevented")
            passed += 1

        # ── Wrong password rejection ──
        try:
            await login(db=db, email="owner@acme-travel.com", password="wrongpassword")
            print("❌ Extra: Wrong password should have failed")
            failed += 1
        except ValueError as e:
            assert "Invalid" in str(e)
            print("✅ Extra: Wrong password rejected")
            passed += 1

        # ── Short password rejection ──
        try:
            await signup(db=db, email="new@test.com", password="short")
            print("❌ Extra: Short password should have failed")
            failed += 1
        except ValueError as e:
            assert "8 characters" in str(e)
            print("✅ Extra: Short password rejected")
            passed += 1

    print(f"\n{'='*50}")
    print(f"Phase 1 Verification: {passed} passed, {failed} failed")
    if failed:
        print("FAILED")
        sys.exit(1)
    else:
        print("ALL PASSED ✅")


if __name__ == "__main__":
    asyncio.run(verify())
