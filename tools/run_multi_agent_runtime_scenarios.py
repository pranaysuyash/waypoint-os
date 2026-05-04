#!/usr/bin/env python3
"""Run deterministic backend multi-agent runtime scenario drills.

This tool avoids production/test database mutation by using an in-memory trip
repository. It writes a Markdown evidence artifact under Docs/status/.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.runtime import AgentSupervisor, build_default_registry


class MemoryTripRepo:
    def __init__(self, trips: list[dict[str, Any]]):
        self.trips = {trip["id"]: dict(trip) for trip in trips}
        self.fail_updates_for: set[str] = set()
        self.update_calls: list[tuple[str, dict[str, Any]]] = []

    def list_active(self):
        return list(self.trips.values())

    def update_trip(self, trip_id: str, updates: dict[str, Any]):
        self.update_calls.append((trip_id, updates))
        if trip_id in self.fail_updates_for:
            return None
        trip = self.trips.get(trip_id)
        if not trip:
            return None
        trip.update(updates)
        return trip


class MemoryAudit:
    def __init__(self):
        self.events: list[dict[str, Any]] = []

    def log(self, event_type: str, trip_id: str, payload: dict[str, Any], user_id: str | None = None):
        self.events.append({"event_type": event_type, "trip_id": trip_id, "payload": payload, "user_id": user_id})


def _result_lines(title: str, results, repo: MemoryTripRepo, audit: MemoryAudit) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(f"- Results: `{[result.to_dict() for result in results]}`")
    lines.append(f"- Trips: `{repo.trips}`")
    lines.append(f"- Audit event types: `{[event['payload']['event_type'] for event in audit.events]}`")
    lines.append("")
    return lines


def run_scenarios() -> str:
    now = datetime.now(timezone.utc)
    generated_at = now.isoformat()
    lines = [
        "# Multi-Agent Runtime Scenario Evidence",
        "",
        f"- Generated at: `{generated_at}`",
        "- Command: `uv run python tools/run_multi_agent_runtime_scenarios.py`",
        "- Storage: in-memory repository; no production/test database writes.",
        "",
    ]

    repo = MemoryTripRepo([
        {"id": "scenario_happy_follow", "status": "in_progress", "follow_up_due_date": (now - timedelta(hours=2)).isoformat()},
        {"id": "scenario_happy_quality", "status": "new", "decision_state": "ESCALATED"},
    ])
    audit = MemoryAudit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)
    lines += _result_lines("Happy path orchestration", supervisor.run_once(), repo, audit)

    repo = MemoryTripRepo([
        {"id": "scenario_retry", "status": "in_progress", "follow_up_due_date": (now - timedelta(hours=2)).isoformat()},
    ])
    repo.fail_updates_for.add("scenario_retry")
    audit = MemoryAudit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)
    first = supervisor.run_once(agent_name="follow_up_agent")
    repo.fail_updates_for.clear()
    second = supervisor.run_once(agent_name="follow_up_agent")
    lines += _result_lines("Transient dependency failure plus retry", first + second, repo, audit)

    repo = MemoryTripRepo([
        {"id": "scenario_poison", "status": "new", "decision_state": "ESCALATED"},
    ])
    repo.fail_updates_for.add("scenario_poison")
    audit = MemoryAudit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)
    results = []
    results += supervisor.run_once(agent_name="quality_escalation_agent")
    results += supervisor.run_once(agent_name="quality_escalation_agent")
    results += supervisor.run_once(agent_name="quality_escalation_agent")
    lines += _result_lines("Terminal failure plus escalation", results, repo, audit)

    repo = MemoryTripRepo([
        {"id": "scenario_idempotent", "status": "in_progress", "follow_up_due_date": (now - timedelta(hours=2)).isoformat()},
    ])
    audit = MemoryAudit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)
    first = supervisor.run_once(agent_name="follow_up_agent")
    second = supervisor.run_once(agent_name="follow_up_agent")
    lines += _result_lines("Ownership collision prevention and idempotent re-entry", first + second, repo, audit)

    repo = MemoryTripRepo([
        {
            "id": "scenario_documents",
            "stage": "proposal",
            "raw_input": {"raw_note": "Indian passports, senior traveler, USA and Canada with Amsterdam transit"},
            "extracted": {
                "facts": {
                    "destination_candidates": {"value": ["United States", "Canada"]},
                    "date_window": {"value": "2026-11-05 to 2026-11-18"},
                }
            },
            "traveler_nationalities": ["Indian"],
            "transit_points": ["Doha", "Amsterdam"],
            "travelers": [{"name": "Adult 1"}, {"name": "Senior", "traveler_type": "senior"}],
        },
    ])
    audit = MemoryAudit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)
    lines += _result_lines("Document readiness checklist", supervisor.run_once(agent_name="document_readiness_agent"), repo, audit)

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md",
        help="Markdown evidence output path.",
    )
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(run_scenarios() + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
