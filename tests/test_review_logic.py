import pytest
import json
from src.analytics.review import process_review_action, trip_to_review
from spine_api import persistence
from spine_api.persistence import TripStore, AuditStore

def test_approve_action_behavior(tmp_path, monkeypatch):
    # Force file store for these tests (they write JSON files directly)
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setattr(persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path / "trips")
    (tmp_path / "trips").mkdir()
    
    # Create a trip needing review
    trip_id = "test-trip-001"
    trip_file = tmp_path / "trips" / f"{trip_id}.json"
    trip_file.write_text(json.dumps({
        "trip_id": trip_id,
        "assigned_to": "agent-1",
        "analytics": {"requires_review": True, "review_status": "pending"}
    }))
    
    # Execute approve
    process_review_action(trip_id, "approve", "Looks good", "owner")
    
    # Verify state
    updated = TripStore.get_trip(trip_id)
    assert updated["analytics"]["review_status"] == "approved"
    assert updated["analytics"]["requires_review"] is False
    assert updated["analytics"]["review_metadata"]["owner_approved"] is True

def test_request_changes_mandatory_reassignment(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setattr(persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path / "trips")
    (tmp_path / "trips").mkdir()
    
    trip_id = "test-trip-002"
    trip_file = tmp_path / "trips" / f"{trip_id}.json"
    trip_file.write_text(json.dumps({
        "trip_id": trip_id,
        "assigned_to": "agent-1",
        "analytics": {"requires_review": True, "review_status": "pending"}
    }))
    
    # Execute request_changes with explicit reassignment
    process_review_action(trip_id, "request_changes", "Refine budget", "owner", reassign_to="agent-2")
    
    # Verify reassignment
    updated = TripStore.get_trip(trip_id)
    assert updated["assigned_to"] == "agent-2"
    assert updated["analytics"]["review_status"] == "revision_needed"
    assert updated["analytics"]["requires_review"] is False

def test_audit_delta_capture(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setattr(persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path / "trips")
    monkeypatch.setattr(persistence.AuditStore, "AUDIT_FILE", tmp_path / "audit.json")
    (tmp_path / "trips").mkdir()
    
    trip_id = "test-trip-003"
    trip_file = tmp_path / "trips" / f"{trip_id}.json"
    trip_file.write_text(json.dumps({
        "trip_id": trip_id,
        "assigned_to": "agent-1",
        "analytics": {"requires_review": True, "review_status": "pending"}
    }))
    
    process_review_action(trip_id, "reject", "Too expensive", "owner")
    
    # Check audit log
    events = AuditStore.get_events()
    assert len(events) > 0
    payload = events[0]["details"]
    assert "pre_state" in payload
    assert "post_state" in payload
    assert payload["pre_state"]["review_status"] == "pending"
    assert payload["post_state"]["review_status"] == "rejected"


def test_escalation_outcome_persists_in_review_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setattr(persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path / "trips")
    (tmp_path / "trips").mkdir()

    trip_id = "test-trip-004"
    trip_file = tmp_path / "trips" / f"{trip_id}.json"
    trip_file.write_text(json.dumps({
        "trip_id": trip_id,
        "assigned_to": "agent-1",
        "analytics": {"requires_review": True, "review_status": "pending"}
    }))

    process_review_action(
        trip_id,
        "escalate",
        "Needs owner review",
        "owner",
        escalation_outcome="false_escalation",
    )

    updated = TripStore.get_trip(trip_id)
    assert updated["analytics"]["review_metadata"]["escalation_outcome"] == "false_escalation"


def test_trip_to_review_falls_back_to_generic_id_field():
    review = trip_to_review(
        {
            "id": "trip-abc123",
            "assigned_to": "agent-1",
            "analytics": {"requires_review": True, "review_status": "pending"},
            "packet": {"destination": "Italy", "trip_type": "leisure", "party_size": 2},
        }
    )

    assert review["id"] == "trip-abc123"
    assert review["tripId"] == "trip-abc123"
    assert review["tripReference"] == "TRIP-ABC123"
