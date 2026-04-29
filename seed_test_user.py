"""
Standalone script to seed mock trips for test agency.
Usage: cd /Users/pranay/Projects/travel_agency_agent && uv run python seed_test_user.py
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

from spine_api.persistence import TripStore


FIXTURE_PATH = PROJECT_ROOT / "data" / "fixtures" / "scenario_alpha.json"
TEST_AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"


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


async def main():
    print(f"Seeding fixture: {FIXTURE_PATH.name}")
    print(f"Target agency : {TEST_AGENCY_ID}")
    print()

    count = await seed_scenario_for_agency(TEST_AGENCY_ID, FIXTURE_PATH)

    print()
    print(f"Done. Seeded {count} new mock trips.")

    # Verify
    all_trips = await TripStore.alist_trips(agency_id=TEST_AGENCY_ID, limit=1000)
    print(f"Total trips for agency now: {len(all_trips)}")


if __name__ == "__main__":
    asyncio.run(main())
