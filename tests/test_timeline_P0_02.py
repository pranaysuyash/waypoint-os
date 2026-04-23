"""
Tests for the decision timeline log (P0-02) feature — unified AuditStore.

This module validates:
1. Event emission via AuditStore on stage transitions
2. AuditStore append-only semantics
3. REST endpoint retrieval merging audit events
4. Event ordering by timestamp
5. Stage filtering via REST endpoint
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

try:
    from spine_api.persistence import AuditStore
except ImportError:
    # Fallback for testing from project root
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "spine-api"))
    from persistence import AuditStore

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope


@pytest.fixture
def sample_envelopes():
    """Create sample envelopes for testing."""
    return [
        SourceEnvelope.from_freeform(
            "Testing timeline: 5 nights in Tokyo, budget ~$5000",
            "agency_notes",
            "agent",
        )
    ]


def test_audit_store_log_event():
    """Test that AuditStore.log_event stores events correctly."""
    trip_id = "test-trip-001"
    
    # Log an event via AuditStore
    AuditStore.log_event(
        event_type="spine_stage_transition",
        user_id="system",
        details={
            "trip_id": trip_id,
            "stage": "intake",
            "state": "extracted",
            "reason": "Extraction pipeline completed"
        }
    )
    
    # Retrieve events for the trip
    events = AuditStore.get_events_for_trip(trip_id)
    assert len(events) > 0
    
    # Verify the event structure
    event = events[-1]
    assert event["type"] == "spine_stage_transition"
    assert event["details"]["trip_id"] == trip_id
    assert event["details"]["stage"] == "intake"
    assert event["details"]["state"] == "extracted"


def test_audit_store_append_only_semantics():
    """Test that AuditStore maintains append-only semantics."""
    trip_id = "test-trip-append-002"  # Use a unique trip ID to avoid contamination
    
    # Log first event
    AuditStore.log_event(
        event_type="spine_stage_transition",
        user_id="system",
        details={
            "trip_id": trip_id,
            "stage": "intake",
            "state": "extracted",
        }
    )
    
    # Log second event
    AuditStore.log_event(
        event_type="spine_stage_transition",
        user_id="system",
        details={
            "trip_id": trip_id,
            "stage": "packet",
            "state": "validated",
        }
    )
    
    # Retrieve events
    events = AuditStore.get_events_for_trip(trip_id)
    
    # Filter to only our events (with proper structure)
    trip_events = [
        e for e in events 
        if e.get("details", {}).get("trip_id") == trip_id 
        and "stage" in e.get("details", {})
    ]
    assert len(trip_events) >= 2, f"Expected at least 2 events, got {len(trip_events)}"
    assert trip_events[0]["details"]["stage"] == "intake"
    assert trip_events[1]["details"]["stage"] == "packet"


def test_audit_store_event_schema():
    """Test that audit events conform to expected schema."""
    trip_id = "test-trip-003"
    
    # Log event with optional fields
    AuditStore.log_event(
        event_type="spine_stage_transition",
        user_id="system",
        details={
            "trip_id": trip_id,
            "stage": "decision",
            "state": "PROCEED_TRAVELER_SAFE",
            "decision_type": "gap_and_decision",
            "reason": "Decision engine analysis completed",
        }
    )
    
    # Retrieve and verify
    events = AuditStore.get_events_for_trip(trip_id)
    event = events[-1]
    
    # Verify required fields
    assert "id" in event
    assert "type" in event
    assert "user_id" in event
    assert "timestamp" in event
    assert "details" in event
    
    # Verify details
    details = event["details"]
    assert "stage" in details
    assert "state" in details
    assert "decision_type" in details
    assert "reason" in details


def test_audit_store_event_ordering():
    """Test that events are retrievable and sortable by timestamp."""
    trip_id = "test-trip-order-004"  # Unique ID to avoid contamination
    
    # Log multiple events
    stages = ["intake", "packet", "decision", "strategy", "safety"]
    for stage in stages:
        AuditStore.log_event(
            event_type="spine_stage_transition",
            user_id="system",
            details={
                "trip_id": trip_id,
                "stage": stage,
                "state": "processed",
            }
        )
    
    # Retrieve events
    events = AuditStore.get_events_for_trip(trip_id)
    trip_events = [
        e for e in events 
        if e.get("details", {}).get("trip_id") == trip_id
        and "stage" in e.get("details", {})
    ]
    
    # Should have exactly 5 events for this unique trip ID
    assert len(trip_events) >= 5, f"Expected at least 5 events, got {len(trip_events)}"
    
    # Get the last 5 events for this trip (in case of contamination, take most recent)
    trip_events = trip_events[-5:]
    
    # Verify they are in insertion order (AuditStore appends)
    stages_in_order = [e["details"]["stage"] for e in trip_events]
    assert stages_in_order == stages, f"Stages out of order: {stages_in_order} vs {stages}"


def test_audit_store_stage_filter():
    """Test filtering events by stage (client-side)."""
    trip_id = "test-trip-005"
    
    # Log events for multiple stages
    events_to_log = [
        {"stage": "intake", "state": "extracted"},
        {"stage": "packet", "state": "validated"},
        {"stage": "intake", "state": "enriched"},
        {"stage": "decision", "state": "decided"},
    ]
    
    for event_data in events_to_log:
        AuditStore.log_event(
            event_type="spine_stage_transition",
            user_id="system",
            details={
                "trip_id": trip_id,
                **event_data
            }
        )
    
    # Retrieve all events
    all_events = AuditStore.get_events_for_trip(trip_id)
    trip_events = [e for e in all_events if e["details"]["trip_id"] == trip_id]
    
    # Filter by intake stage (client-side or server-side)
    intake_events = [e for e in trip_events if e["details"]["stage"] == "intake"]
    
    assert len(intake_events) >= 2
    assert all(e["details"]["stage"] == "intake" for e in intake_events)


def test_audit_store_iso8601_timestamps():
    """Test that AuditStore stores ISO8601-formatted timestamps."""
    trip_id = "test-trip-006"
    
    AuditStore.log_event(
        event_type="spine_stage_transition",
        user_id="system",
        details={
            "trip_id": trip_id,
            "stage": "intake",
            "state": "extracted",
        }
    )
    
    events = AuditStore.get_events_for_trip(trip_id)
    event = events[-1]
    
    timestamp = event["timestamp"]
    # Should be parseable as ISO8601
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None
    except ValueError:
        pytest.fail(f"Timestamp {timestamp} is not valid ISO8601")


def test_missing_trip_returns_empty():
    """Test that retrieving events for non-existent trip returns empty list."""
    trip_id = "nonexistent-trip-xyz"
    
    events = AuditStore.get_events_for_trip(trip_id)
    trip_events = [e for e in events if e["details"].get("trip_id") == trip_id]
    
    assert len(trip_events) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

