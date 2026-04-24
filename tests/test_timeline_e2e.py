"""
E2E integration test for timeline P0-02 (unified AuditStore).

Validates that a complete spine run emits timeline events via AuditStore.
"""

import pytest
from datetime import datetime

try:
    from spine_api.persistence import AuditStore
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "spine_api"))
    from persistence import AuditStore

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope


def test_spine_run_emits_audit_events():
    """
    E2E: Run a full spine and verify audit events are created.
    
    Verifies that AuditStore captures timeline events for all stages.
    """
    # Create a test envelope
    envelopes = [
        SourceEnvelope.from_freeform(
            """
            Trip Details:
            - Destination: Paris, France
            - Duration: 7 days
            - Travelers: 2 adults
            - Budget: €4000
            - Dates: May 2025
            - Interests: Museums, food, walking tours
            """,
            "agency_notes",
            "agent",
        )
    ]

    # Run the spine
    result = run_spine_once(
        envelopes=envelopes,
        stage="discovery",
    )

    # Get the trip ID from the result
    trip_id = result.packet.packet_id
    assert trip_id, "Spine should return a trip ID"

    # Retrieve events from AuditStore
    all_events = AuditStore.get_events_for_trip(trip_id)
    
    # Filter to this trip's events
    events = [e for e in all_events if e["details"].get("trip_id") == trip_id]

    # Verify we have at least 2 events (intake and packet minimum)
    assert len(events) >= 2, f"Expected at least 2 timeline events, got {len(events)}"

    # Verify event structure
    for event in events:
        assert "type" in event, "Event missing type"
        assert "timestamp" in event, "Event missing timestamp"
        assert "details" in event, "Event missing details"
        
        details = event["details"]
        assert "stage" in details, "Details missing stage"
        assert "state" in details, "Details missing state"
        
        # Timestamp should be ISO8601
        try:
            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid ISO8601 timestamp: {event['timestamp']}")

    # Verify timestamps are in ascending order
    timestamps = [event["timestamp"] for event in events]
    sorted_timestamps = sorted(timestamps)
    assert timestamps == sorted_timestamps, "Events not in chronological order"

    # Verify we always have at least intake and packet stages
    stages = [e["details"]["stage"] for e in events]
    assert "intake" in stages, "Missing intake stage event"
    assert "packet" in stages, "Missing packet stage event"


def test_audit_events_are_properly_structured():
    """Verify audit events have correct structure for timeline consumption."""
    envelopes = [
        SourceEnvelope.from_freeform(
            """
            Trip: 10 days Bangkok, Thailand
            Budget: $3000 USD
            Travelers: 2
            """,
            "agency_notes",
            "agent",
        )
    ]

    result = run_spine_once(envelopes=envelopes, stage="discovery")
    trip_id = result.packet.packet_id

    # Retrieve events
    all_events = AuditStore.get_events_for_trip(trip_id)
    events = [e for e in all_events if e["details"].get("trip_id") == trip_id]

    assert len(events) > 0, "No events found in AuditStore for trip"

    # Verify structure of each event
    for event in events:
        assert event["type"] == "spine_stage_transition"
        assert isinstance(event["timestamp"], str)
        assert isinstance(event["details"], dict)
        
        details = event["details"]
        assert details["trip_id"] == trip_id
        assert isinstance(details["stage"], str)
        assert isinstance(details["state"], str)
        
        # Optional fields
        if "decision_type" in details:
            assert isinstance(details["decision_type"], str)
        if "reason" in details:
            assert isinstance(details["reason"], str)


def test_timeline_preserves_audit_order():
    """Verify that audit events maintain insertion order (immutability)."""
    envelopes = [
        SourceEnvelope.from_freeform(
            """
            Quick trip: 3 days in Barcelona
            Budget: €2000
            """,
            "agency_notes",
            "agent",
        )
    ]

    result = run_spine_once(envelopes=envelopes, stage="discovery")
    trip_id = result.packet.packet_id

    # Retrieve events
    all_events = AuditStore.get_events_for_trip(trip_id)
    events = [e for e in all_events if e["details"].get("trip_id") == trip_id]

    assert len(events) > 0, "No events found"

    # Verify stages appear in expected order (intake → packet → ...)
    stages = [e["details"]["stage"] for e in events]
    
    # intake should appear before packet
    if "intake" in stages and "packet" in stages:
        intake_idx = stages.index("intake")
        packet_idx = stages.index("packet")
        assert intake_idx < packet_idx, "Stages not in chronological order"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

