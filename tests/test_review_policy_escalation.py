import json

from src.analytics.review import process_review_action
from spine_api import persistence
from spine_api.persistence import TripStore


def test_revision_loop_auto_escalates_on_second_request(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path / "trips")
    (tmp_path / "trips").mkdir()

    trip_id = "test-trip-revision-loop"
    trip_file = tmp_path / "trips" / f"{trip_id}.json"
    trip_file.write_text(
        json.dumps(
            {
                "trip_id": trip_id,
                "assigned_to": "agent-1",
                "decision": {"decision_state": "PROCEED_INTERNAL_DRAFT", "suitability_flags": []},
                "analytics": {"requires_review": True, "review_status": "pending", "revision_count": 0},
            }
        )
    )

    process_review_action(trip_id, "request_changes", "First correction", "owner")
    first = TripStore.get_trip(trip_id)
    assert first["analytics"]["revision_count"] == 1
    assert first["analytics"]["review_status"] == "revision_needed"

    process_review_action(trip_id, "request_changes", "Second correction", "owner")
    second = TripStore.get_trip(trip_id)
    assert second["analytics"]["revision_count"] == 2
    assert second["analytics"]["review_status"] == "escalated"
    assert second["analytics"]["requires_review"] is True
    assert second["assigned_to"] == "management_queue"
