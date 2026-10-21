"""
Behavior tests for Slice D followups router extraction.

Covers:
- dashboard filesystem scan + agency filter
- mark-complete success and error paths
- snooze success and error paths
- reschedule success and error paths
- audit event payload assertions
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from server import app
from routers import followups


@pytest.fixture(autouse=True)
def override_agency_dependency():
    """Force followups routes to run under a deterministic agency id."""
    original = dict(app.dependency_overrides)
    app.dependency_overrides[followups.get_current_agency] = lambda: SimpleNamespace(id="agency_test")
    try:
        yield
    finally:
        app.dependency_overrides = original


@pytest.fixture
def dashboard_trips_dir(tmp_path, monkeypatch):
    """Create isolated data/trips root for dashboard endpoint path semantics."""
    fake_module_path = tmp_path / "spine_api" / "routers" / "followups.py"
    fake_module_path.parent.mkdir(parents=True, exist_ok=True)
    fake_module_path.write_text("# test module path sentinel\n", encoding="utf-8")

    # Endpoint resolves trips_dir via Path(__file__).resolve().parents[2] / "data" / "trips"
    monkeypatch.setattr(followups, "__file__", str(fake_module_path))

    trips_dir = tmp_path / "data" / "trips"
    trips_dir.mkdir(parents=True, exist_ok=True)
    return trips_dir


def _write_trip(path: Path, payload: dict):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_followups_dashboard_agency_filter_and_sort(session_client, dashboard_trips_dir):
    now = datetime.now(timezone.utc)

    trip_due_later = {
        "id": "trip-later",
        "agency_id": "agency_test",
        "traveler_name": "Later",
        "agent_name": "Agent-A",
        "follow_up_due_date": (now + timedelta(days=2)).isoformat(),
        "follow_up_status": "pending",
        "status": "in_progress",
    }
    trip_due_soon = {
        "id": "trip-soon",
        "agency_id": "agency_test",
        "traveler_name": "Soon",
        "agent_name": "Agent-B",
        "follow_up_due_date": (now + timedelta(hours=4)).isoformat(),
        "follow_up_status": "pending",
        "status": "in_progress",
    }
    other_agency_trip = {
        "id": "trip-other-agency",
        "agency_id": "agency_other",
        "traveler_name": "Other",
        "agent_name": "Agent-C",
        "follow_up_due_date": (now + timedelta(days=1)).isoformat(),
        "follow_up_status": "pending",
        "status": "in_progress",
    }

    _write_trip(dashboard_trips_dir / "trip_due_later.json", trip_due_later)
    _write_trip(dashboard_trips_dir / "trip_due_soon.json", trip_due_soon)
    _write_trip(dashboard_trips_dir / "trip_other.json", other_agency_trip)
    (dashboard_trips_dir / "broken.json").write_text("{not-json", encoding="utf-8")

    resp = session_client.get("/followups/dashboard")
    assert resp.status_code == 200

    data = resp.json()
    assert data["total"] == 2
    assert [item["trip_id"] for item in data["items"]] == ["trip-soon", "trip-later"]
    assert all(item["trip_id"] != "trip-other-agency" for item in data["items"])


def test_mark_followup_complete_success_and_audit(session_client, monkeypatch):
    trip = {
        "id": "trip-1",
        "agency_id": "agency_test",
        "follow_up_due_date": "2026-05-15T14:00:00+00:00",
        "follow_up_status": "pending",
    }

    captured = {}

    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    def _update_trip(trip_id, updates):
        return {**trip, **updates, "id": trip_id}

    monkeypatch.setattr(followups.TripStore, "update_trip", _update_trip)

    def _log_event(event_type, actor, payload):
        captured["event_type"] = event_type
        captured["actor"] = actor
        captured["payload"] = payload

    monkeypatch.setattr(followups.AuditStore, "log_event", _log_event)

    resp = session_client.patch("/followups/trip-1/mark-complete")
    assert resp.status_code == 200
    body = resp.json()
    assert body["follow_up_status"] == "completed"
    assert "follow_up_completed_at" in body

    assert captured["event_type"] == "followup_completed"
    assert captured["actor"] == "operator"
    assert captured["payload"]["trip_id"] == "trip-1"
    assert captured["payload"]["due_date"] == "2026-05-15T14:00:00+00:00"
    assert "completed_at" in captured["payload"]


def test_mark_followup_complete_not_found(session_client, monkeypatch):
    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: None)

    resp = session_client.patch("/followups/missing-trip/mark-complete")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Trip not found"


def test_mark_followup_complete_without_scheduled_followup(session_client, monkeypatch):
    trip = {"id": "trip-1", "agency_id": "agency_test"}
    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    resp = session_client.patch("/followups/trip-1/mark-complete")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Trip has no follow-up scheduled"


def test_snooze_followup_success_and_audit(session_client, monkeypatch):
    trip = {
        "id": "trip-2",
        "agency_id": "agency_test",
        "follow_up_due_date": "2026-05-15T14:00:00+00:00",
        "follow_up_status": "pending",
    }

    captured = {}

    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    def _update_trip(trip_id, updates):
        return {**trip, **updates, "id": trip_id}

    monkeypatch.setattr(followups.TripStore, "update_trip", _update_trip)

    def _log_event(event_type, actor, payload):
        captured["event_type"] = event_type
        captured["actor"] = actor
        captured["payload"] = payload

    monkeypatch.setattr(followups.AuditStore, "log_event", _log_event)

    resp = session_client.patch("/followups/trip-2/snooze", params={"days": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert body["follow_up_status"] == "snoozed"

    original_dt = datetime.fromisoformat(trip["follow_up_due_date"])
    expected_new_dt = (original_dt + timedelta(days=3)).isoformat()
    assert body["follow_up_due_date"] == expected_new_dt

    assert captured["event_type"] == "followup_snoozed"
    assert captured["actor"] == "operator"
    assert captured["payload"]["trip_id"] == "trip-2"
    assert captured["payload"]["original_due_date"] == "2026-05-15T14:00:00+00:00"
    assert captured["payload"]["new_due_date"] == expected_new_dt
    assert captured["payload"]["snooze_days"] == 3


def test_snooze_followup_invalid_days(session_client, monkeypatch):
    trip = {
        "id": "trip-2",
        "agency_id": "agency_test",
        "follow_up_due_date": "2026-05-15T14:00:00+00:00",
    }
    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    resp = session_client.patch("/followups/trip-2/snooze", params={"days": 2})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "days must be 1, 3, or 7"


def test_snooze_followup_invalid_due_date_format(session_client, monkeypatch):
    trip = {
        "id": "trip-2",
        "agency_id": "agency_test",
        "follow_up_due_date": "not-a-date",
    }
    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    resp = session_client.patch("/followups/trip-2/snooze", params={"days": 1})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid follow_up_due_date format"


def test_reschedule_followup_success_and_audit(session_client, monkeypatch):
    trip = {
        "id": "trip-3",
        "agency_id": "agency_test",
        "follow_up_due_date": "2026-05-20T10:00:00+00:00",
        "follow_up_status": "snoozed",
    }
    new_date = "2026-05-25T09:30:00+00:00"

    captured = {}

    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    def _update_trip(trip_id, updates):
        return {**trip, **updates, "id": trip_id}

    monkeypatch.setattr(followups.TripStore, "update_trip", _update_trip)

    def _log_event(event_type, actor, payload):
        captured["event_type"] = event_type
        captured["actor"] = actor
        captured["payload"] = payload

    monkeypatch.setattr(followups.AuditStore, "log_event", _log_event)

    resp = session_client.patch("/followups/trip-3/reschedule", params={"new_date": new_date})
    assert resp.status_code == 200
    body = resp.json()
    assert body["follow_up_due_date"] == new_date
    assert body["follow_up_status"] == "pending"

    assert captured["event_type"] == "followup_rescheduled"
    assert captured["actor"] == "operator"
    assert captured["payload"]["trip_id"] == "trip-3"
    assert captured["payload"]["old_due_date"] == "2026-05-20T10:00:00+00:00"
    assert captured["payload"]["new_due_date"] == new_date


def test_reschedule_followup_invalid_date_format(session_client, monkeypatch):
    trip = {
        "id": "trip-3",
        "agency_id": "agency_test",
        "follow_up_due_date": "2026-05-20T10:00:00+00:00",
    }
    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    resp = session_client.patch("/followups/trip-3/reschedule", params={"new_date": "05/25/2026 09:30"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid date format. Use ISO-8601"


# ---------------------------------------------------------------------------
# FND-0301: send open follow-up questions to the traveler
# ---------------------------------------------------------------------------

def test_send_followup_questions_records_ask_and_dispatches(session_client, monkeypatch):
    trip = {
        "id": "trip-ask-9",
        "agency_id": "agency_test",
        "destination": "Kerala",
        "packet": {"destination": "Kerala"},
        "decision": {
            "follow_up_questions": [
                {"field_name": "origin_city", "question": "Which city would you fly out from?", "priority": "high"},
            ],
        },
        "traveler_asks": [],
    }
    captured_updates = {}

    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    def _update(trip_id, agency_id, fields):
        captured_updates.update(fields)
        trip.update(fields)
        return trip

    monkeypatch.setattr(followups.TripStore, "update_trip_for_agency", _update)

    import spine_api.services.message_dispatch as dispatch_mod
    monkeypatch.setattr(
        followups,
        "dispatch_outbound_message",
        None,
        raising=False,
    )
    # followups imports dispatch lazily inside the endpoint; patch the service
    monkeypatch.setattr(
        dispatch_mod,
        "dispatch_outbound_message",
        lambda *, recipient, channel, content: {
            "dispatch_status": "NOT_CONFIGURED",
            "provider": "whatsapp_cloud_api",
            "detail": "creds absent (test)",
        },
    )
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)

    # The endpoint signs a real proposal token; ensure the signing key exists.
    monkeypatch.setenv("PROPOSAL_SIGNING_KEY", "test-signing-key-for-fnd0301-0123456789abcdef")

    resp = session_client.post(
        "/followups/trip-ask-9/send",
        json={"recipient": "+919820000000", "channel": "whatsapp"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["dispatch_status"] == "NOT_CONFIGURED"  # honest: no creds in test env
    assert body["question_count"] == 1
    assert "/a/" in body["ask_path"]

    asks = captured_updates["traveler_asks"]
    assert len(asks) == 1
    assert asks[0]["fields"] == ["origin_city"]
    assert asks[0]["dispatch_status"] == "NOT_CONFIGURED"
    assert asks[0]["token"].startswith("prop_")


def test_send_followup_questions_409_without_open_questions(session_client, monkeypatch):
    trip = {"id": "trip-ask-empty", "agency_id": "agency_test", "decision": {"follow_up_questions": []}, "traveler_asks": []}
    monkeypatch.setattr(followups.TripStore, "get_trip_for_agency", lambda trip_id, agency_id: trip)

    resp = session_client.post(
        "/followups/trip-ask-empty/send",
        json={"recipient": "+919820000000", "channel": "whatsapp"},
    )
    assert resp.status_code == 409
    assert "no open follow-up questions" in resp.json()["detail"]
