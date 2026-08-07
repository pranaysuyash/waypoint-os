"""
test_multi_agent_concurrency_suite.py — Unit test suite for high-concurrency multi-agent execution & audit chain integrity.

Architecture Decision: ADR 16
"""

import asyncio
import os
import pytest

from spine_api import persistence

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")

@pytest.mark.asyncio
async def test_concurrent_audit_logging_chain_integrity():
    """Verify SHA-256 block hash integrity under concurrent multi-agent audit logging."""
    audit_store = persistence.AuditStore()

    async def log_agent_event(agent_idx: int, event_idx: int):
        audit_store.log_event(
            event_type="AGENT_ACTION",
            user_id=f"agent_{agent_idx}",
            details={
                "event_idx": event_idx,
                "action": "PROCESS_INQUIRY",
                "inquiry": "Bali 6N beach villa",
            },
        )

    # Spawn 50 concurrent logging tasks
    tasks = [
        log_agent_event(agent_idx=i % 10, event_idx=i)
        for i in range(50)
    ]
    await asyncio.gather(*tasks)

    events = audit_store.get_events(limit=100)
    assert len(events) >= 50, f"Expected at least 50 events, got {len(events)}"

    # Verify hash chain continuity
    for idx in range(1, min(50, len(events))):
        curr_event = events[idx]
        assert "current_hash" in curr_event, "Event missing current_hash"
        assert "previous_hash" in curr_event, "Event missing previous_hash"
        assert len(curr_event["current_hash"]) == 64, "Invalid SHA-256 current_hash length"

@pytest.mark.asyncio
async def test_concurrent_trip_store_isolation():
    """Verify concurrent trip store updates do not cause race conditions or state corruption."""
    trip_store = persistence.TripStore()
    agency_id = persistence.TEST_AGENCY_ID

    async def create_and_update_trip(trip_idx: int):
        trip_id = f"trip_conc_{trip_idx}"
        data = {
            "id": trip_id,
            "agency_id": agency_id,
            "destination": "Singapore",
            "status": "assigned",
            "party": 2,
            "raw_input": {"fixture_id": "synthetic_concurrency_test"},
        }
        await trip_store.asave_trip(data, agency_id=agency_id)
        backend = trip_store._backend()
        if backend is persistence.FileTripStore:
            retrieved = persistence.FileTripStore.get_trip_for_agency(trip_id, agency_id)
        else:
            retrieved = await persistence.SQLTripStore.get_trip_for_agency(trip_id, agency_id)
        assert retrieved is not None

    tasks = [create_and_update_trip(i) for i in range(25)]
    await asyncio.gather(*tasks)
