"""
Standalone script to seed test user + agency + owner membership, then mock trips.

Usage: cd /Users/pranay/Projects/travel_agency_agent && uv run python seed_test_user.py

Creates (idempotently):
  - User: newuser@test.com / testpass123  (role=owner → all permissions)
  - Agency + Membership + WorkspaceCode
  - Mock trips from scenario_alpha.json
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "spine_api"))

# Must set env before importing persistence
os.environ.setdefault("TRIPSTORE_BACKEND", "sql")

from spine_api.persistence import TripStore, TEST_AGENCY_ID

FIXTURE_PATH = PROJECT_ROOT / "data" / "fixtures" / "scenario_alpha.json"

# Default test user credentials (owner role → all permissions)
TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "newuser@test.com")
TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "testpass123")
TEST_USER_NAME = os.environ.get("TEST_USER_NAME", "Test User")


async def seed_scenario_for_agency(agency_id: str, fixture_path: Path) -> int:
    """Load fixture trips and associate them with a specific agency."""
    if not fixture_path.exists():
        print(f"Fixture not found: {fixture_path}")
        return 0

    with open(fixture_path) as f:
        trips = json.load(f)

    if not isinstance(trips, list):
        print("Fixture must be a JSON array of trips")
        return 0

    loaded = 0
    for trip_data in trips:
        trip_id = trip_data.get("id")
        if not trip_id:
            continue

        existing = await TripStore.aget_trip(trip_id)
        if existing:
            print(f"  Skipping existing trip: {trip_id}")
            continue

        trip_record = {
            "id": trip_id,
            "run_id": f"seed_{trip_id}",
            "source": "seed_scenario",
            "status": trip_data.get("status", "new"),
            "created_at": trip_data.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": trip_data.get("updated_at"),
            "extracted": trip_data.get("extracted"),
            "validation": trip_data.get("validation"),
            "decision": trip_data.get("decision"),
            "analytics": trip_data.get("analytics"),
            "assigned_to": trip_data.get("assignedTo"),
            "assigned_to_name": trip_data.get("assignedToName"),
            "meta": trip_data.get("meta", {"stage": trip_data.get("status", "new"), "seed": True}),
            "agency_id": agency_id,
        }

        await TripStore.asave_trip(trip_record, agency_id=agency_id)
        loaded += 1
        print(f"  Seeded: {trip_id} (status={trip_record['status']})")

    return loaded


async def ensure_test_user() -> dict:
    """Ensure the test user exists with owner role and all permissions.

    Idempotent: skips creation if the user already exists.
    Returns a dict with user_id, agency_id, and role for logging.
    """
    import secrets as _secrets
    import uuid as _uuid

    from sqlalchemy import text
    from spine_api.core.database import async_session_maker
    from spine_api.core.security import hash_password

    now = datetime.now(timezone.utc).isoformat()
    pw_hash = hash_password(TEST_USER_PASSWORD)

    async with async_session_maker() as conn:
        # 1. Check if user exists
        row = (await conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": TEST_USER_EMAIL},
        )).mappings().first()

        if row:
            user_id = row["id"]
            print(f"  User {TEST_USER_EMAIL} already exists (id={user_id[:8]}...)")
        else:
            user_id = str(_uuid.uuid4())
            await conn.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, name, is_active, created_at) "
                    "VALUES (:id, :email, :pw, :name, true, :now)"
                ),
                {"id": user_id, "email": TEST_USER_EMAIL, "pw": pw_hash, "name": TEST_USER_NAME, "now": now},
            )
            print(f"  Created user: {TEST_USER_EMAIL} (id={user_id[:8]}...)")

        # 2. Check if user has an owner membership
        row = (await conn.execute(
            text("SELECT agency_id FROM memberships WHERE user_id = :uid AND role = 'owner'"),
            {"uid": user_id},
        )).mappings().first()

        if row:
            agency_id = row["agency_id"]
            print(f"  Owner membership exists (agency={agency_id[:8]}..., role=owner)")
        else:
            agency_id = _uuid.uuid4().hex[:12]
            slug = f"test-agency-{agency_id[:8]}"
            code_value = f"WP-{_secrets.token_urlsafe(8)}"

            # Create agency
            await conn.execute(
                text(
                    "INSERT INTO agencies (id, name, slug, email, is_test, created_at) "
                    "VALUES (:id, :name, :slug, :email, true, :now)"
                ),
                {"id": agency_id, "name": "Test Agency", "slug": slug, "email": TEST_USER_EMAIL, "now": now},
            )

            # Create owner membership
            await conn.execute(
                text(
                    "INSERT INTO memberships (id, user_id, agency_id, role, is_primary, status, created_at) "
                    "VALUES (:id, :uid, :aid, 'owner', true, 'active', :now)"
                ),
                {"id": str(_uuid.uuid4()), "uid": user_id, "aid": agency_id, "now": now},
            )

            # Create workspace code
            await conn.execute(
                text(
                    "INSERT INTO workspace_codes (agency_id, code, code_type, status, created_by, created_at) "
                    "VALUES (:aid, :code, 'internal', 'active', :uid, :now)"
                ),
                {"aid": agency_id, "code": code_value, "uid": user_id, "now": now},
            )

            print(f"  Created agency ({agency_id[:8]}...) + owner membership + workspace code: {code_value}")

        await conn.commit()

    return {"user_id": user_id, "agency_id": agency_id, "role": "owner"}


async def main():
    print("=== Test User Bootstrap ===")
    print(f"  Email    : {TEST_USER_EMAIL}")
    print(f"  Password : {TEST_USER_PASSWORD}")
    print(f"  Role     : owner (all permissions)")
    print()

    user_info = await ensure_test_user()
    agency_id = user_info["agency_id"]

    print()
    print("=== Trip Seeding ===")
    print(f"  Fixture : {FIXTURE_PATH.name}")
    print(f"  Agency  : {agency_id[:8]}...")
    print()

    count = await seed_scenario_for_agency(agency_id, FIXTURE_PATH)

    print()
    print(f"Done. Seeded {count} new mock trips.")

    # Verify
    all_trips = await TripStore.alist_trips(agency_id=agency_id, limit=1000)
    print(f"Total trips for agency now: {len(all_trips)}")
    print(f"Login: POST /api/auth/login with {{email: \"{TEST_USER_EMAIL}\", password: \"{TEST_USER_PASSWORD}\"}}")


if __name__ == "__main__":
    asyncio.run(main())
