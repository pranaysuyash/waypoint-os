"""
Migrate existing trip data: parse tagged values from agentNotes into
first-class trip_priorities / date_flexibility columns and extracted.facts.

Run:
    uv run python scripts/migrate_agentnotes_to_columns.py [--dry-run]

Idempotent: skips trips that already have values in the target columns.

Tagged note format expected in agentNotes:
    Trip priorities: <value>
    Date flexibility: <value>
    Contact name: <value>
"""

import json
import os
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRIPS_DIR = DATA_DIR / "trips"


def parse_tagged_value(agent_notes: str, prefix: str) -> str | None:
    if not agent_notes:
        return None
    pattern = re.compile(rf"^{re.escape(prefix)}:\s*(.+?)$", re.MULTILINE)
    match = pattern.search(agent_notes)
    return match.group(1).strip() if match else None


def migrate_trip(filepath: Path, dry_run: bool = False) -> dict | None:
    with open(filepath, "r") as f:
        trip = json.load(f)

    agent_notes = trip.get("agentNotes") or trip.get("agent_notes") or ""
    if not agent_notes:
        return None

    changes = {}

    # trip_priorities
    existing_priorities = trip.get("trip_priorities")
    if not existing_priorities:
        priorities = parse_tagged_value(agent_notes, "Trip priorities")
        if priorities:
            changes["trip_priorities"] = priorities

    # date_flexibility
    existing_flex = trip.get("date_flexibility")
    if not existing_flex:
        flexibility = parse_tagged_value(agent_notes, "Date flexibility")
        if flexibility:
            changes["date_flexibility"] = flexibility

    # Sync into extracted.facts for readiness engine
    extracted = trip.get("extracted") or {}
    facts = extracted.get("facts") or {}

    if "trip_priorities" in changes and "trip_priorities" not in facts:
        facts["trip_priorities"] = {
            "value": changes["trip_priorities"],
            "confidence": 0.8,
            "authority_level": "explicit_owner",
        }
        extracted["facts"] = facts
        changes["extracted"] = extracted

    if "date_flexibility" in changes and "date_flexibility" not in facts:
        facts["date_flexibility"] = {
            "value": changes["date_flexibility"],
            "confidence": 0.8,
            "authority_level": "explicit_owner",
        }
        extracted["facts"] = facts
        changes["extracted"] = extracted

    if not changes:
        return None

    if not dry_run:
        trip.update(changes)
        with open(filepath, "w") as f:
            json.dump(trip, f, indent=2)

    return changes


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    if not TRIPS_DIR.exists():
        print(f"No trips directory found at {TRIPS_DIR}")
        return

    trip_files = sorted(TRIPS_DIR.glob("*.json"))
    if not trip_files:
        print(f"No trip files found in {TRIPS_DIR}")
        return

    migrated = 0
    skipped = 0
    total = len(trip_files)

    for filepath in trip_files:
        changes = migrate_trip(filepath, dry_run=dry_run)
        if changes:
            migrated += 1
            fields = ", ".join(changes.keys())
            print(f"  {filepath.name}: migrated {fields}")
        else:
            skipped += 1

    action = "Would migrate" if dry_run else "Migrated"
    print(f"\n{action} {migrated} trips, skipped {skipped} (already populated or no tagged notes)")
    print(f"Total trip files: {total}")


if __name__ == "__main__":
    main()
