"""
Behavior tests for legacy ops router extraction.

Covers:
- route registration and handler dependency profile parity
- assignment listing agency-scope filtering
- override stale-severity conflict semantics
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from server import app
from routers import legacy_ops


@pytest.fixture(autouse=True)
def override_legacy_ops_dependencies():
    """Run legacy-ops routes under deterministic agency/user context."""
    original = dict(app.dependency_overrides)
    app.dependency_overrides[legacy_ops.get_current_agency] = lambda: SimpleNamespace(id="agency_test")
    try:
        yield
    finally:
        app.dependency_overrides = original


def _get_route(path: str, method: str):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
            return route
    raise AssertionError(f"Route not found: {method} {path}")


def test_legacy_ops_reassign_route_registered_with_permission_dependency_presence():
    params = list(inspect.signature(legacy_ops.reassign_trip).parameters.keys())
    assert params == ["trip_id", "agent_id", "agent_name", "reassigned_by", "agency", "_perm"]

    route = _get_route("/trips/{trip_id}/reassign", "POST")
    dependency_calls = [dep.call for dep in route.dependant.dependencies]
    assert legacy_ops.get_current_agency in dependency_calls


def test_list_assignments_filters_to_current_agency_trips(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_a1"}, {"id": "trip_a2"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AssignmentStore,
        "_load_assignments",
        lambda: {
            "asg_1": {"trip_id": "trip_a1", "agent_id": "agent_1"},
            "asg_2": {"trip_id": "trip_other", "agent_id": "agent_2"},
        },
    )

    resp = session_client.get("/assignments")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["trip_id"] == "trip_a1"


def test_override_conflict_when_original_severity_is_stale(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "get_trip",
        lambda trip_id: {
            "id": trip_id,
            "agency_id": "agency_test",
            "decision": {"suitability_flags": [{"flag": "budget_risk", "severity": "critical"}]},
        },
    )

    payload = {
        "flag": "budget_risk",
        "decision_type": "suitability",
        "action": "downgrade",
        "new_severity": "warning",
        "overridden_by": "owner_1",
        "reason": "Reviewed with operator",
        "scope": "this_trip",
        "original_severity": "warning",
    }
    resp = session_client.post("/trips/trip_123/override", json=payload)
    assert resp.status_code == 409
    assert "Stale override" in resp.json()["detail"]


def test_get_audit_events_supports_event_type_filter(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}, {"id": "trip_beta"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {"type": "routing_health_alert", "details": {"trip_id": "trip_alpha", "status": "warning"}},
            {"type": "override_created", "details": {"trip_id": "trip_alpha"}},
            {"type": "routing_health_alert", "details": {"trip_id": "trip_beta", "status": "critical"}},
            {"type": "routing_health_alert", "details": {"trip_id": "trip_alpha", "status": "critical"}},
        ][:limit],
    )

    resp = session_client.get("/audit?event_type=routing_health_alert")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert {item["type"] for item in data["items"]} == {"routing_health_alert"}


def test_get_audit_events_supports_trip_status_filter(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {"type": "routing_health_alert", "details": {"trip_id": "trip_alpha", "status": "warning"}},
            {"type": "routing_health_alert", "details": {"trip_id": "trip_alpha", "status": "critical"}},
            {"type": "routing_health_alert", "details": {"trip_id": "trip_alpha", "status": "warning"}},
            {"type": "override_created", "details": {"trip_id": "trip_alpha", "status": "warning"}},
            {"type": "routing_health_alert", "details": {"trip_id": "trip_gamma", "status": "critical"}},
        ][:limit],
    )

    resp = session_client.get("/audit?event_type=routing_health_alert&trip_status=critical")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["details"]["status"] == "critical"
    assert data["items"][0]["details"]["trip_id"] == "trip_alpha"


def test_routing_health_alert_triage_logs_audit_event_for_current_agency(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {
                "id": "alert-1",
                "type": "routing_health_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T10:00:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "critical",
                    "workflow": "extraction",
                },
            },
        ][:limit],
    )

    logged_events: list[dict] = []

    def log_event_stub(event_type: str, user_id: str, details: dict):
        logged_events.append({"event_type": event_type, "user_id": user_id, "details": details})
        return {
            "id": "triage-evt-1",
            "type": event_type,
            "user_id": user_id,
            "timestamp": "2026-07-01T10:01:00.000Z",
            "details": details,
        }

    monkeypatch.setattr(legacy_ops.AuditStore, "log_event", log_event_stub)

    payload = {"action": "escalate", "note": "Escalate to operator"}
    resp = session_client.post("/audit/alert-1/triage", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["target_event_id"] == "alert-1"
    assert data["action"] == "escalate"
    assert data["triage_event"]["id"] == "triage-evt-1"
    assert logged_events == [
        {
            "event_type": "routing_health_alert_triage",
            "user_id": "agency_test",
            "details": {
                "target_event_id": "alert-1",
                "target_event_type": "routing_health_alert",
                "trip_id": "trip_alpha",
                "status": "critical",
                "workflow": "extraction",
                "note": "Escalate to operator",
                "action": "escalate",
            },
        },
    ]


def test_routing_health_alert_triage_rejects_invalid_action(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {
                "id": "alert-1",
                "type": "routing_health_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T10:00:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "warning",
                    "workflow": "extraction",
                },
            },
        ][:limit],
    )

    resp = session_client.post("/audit/alert-1/triage", json={"action": "invalid"})
    assert resp.status_code == 422


def test_routing_health_alert_triage_is_404_when_event_not_found(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {
                "id": "other-alert",
                "type": "routing_health_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T10:00:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "critical",
                    "workflow": "extraction",
                },
            },
        ][:limit],
    )

    resp = session_client.post("/audit/alert-1/triage", json={"action": "acknowledge"})
    assert resp.status_code == 404


def test_batch_routing_health_triage_handles_success_and_fail_paths(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {
                "id": "alert-1",
                "type": "routing_health_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T09:00:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "warning",
                    "workflow": "extraction",
                },
            },
            {
                "id": "alert-2",
                "type": "routing_health_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T09:01:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "critical",
                    "workflow": "trip_scoring",
                },
            },
        ][:limit],
    )

    logged_events: list[dict] = []

    def log_event_stub(event_type: str, user_id: str, details: dict):
        logged_events.append({"event_type": event_type, "user_id": user_id, "details": details})
        return {
            "id": f"triage-{details['target_event_id']}",
            "type": event_type,
            "user_id": user_id,
            "timestamp": "2026-07-01T09:10:00.000Z",
            "details": details,
        }

    monkeypatch.setattr(legacy_ops.AuditStore, "log_event", log_event_stub)

    payload = [
        {"event_id": "alert-1", "action": "acknowledge", "note": "Handled first"},
        {"event_id": "alert-2", "action": "close"},
        {"event_id": "alert-3", "action": "escalate", "note": "Needs escalation"},
    ]
    resp = session_client.post("/audit/routing-health/batch-triage", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["requested"] == 3
    assert data["succeeded"] == 2
    assert data["failed"] == 1

    results_by_id = {item["event_id"]: item for item in data["results"]}
    assert set(results_by_id.keys()) == {"alert-1", "alert-2", "alert-3"}

    alert_1 = results_by_id["alert-1"]
    assert alert_1["success"] is True
    assert alert_1["action"] == "acknowledge"
    assert alert_1["note"] == "Handled first"
    assert alert_1["triage_event"]["details"]["note"] == "Handled first"
    assert alert_1["triage_event"]["details"]["action"] == "acknowledge"
    assert alert_1.get("error") in (None, "")

    alert_2 = results_by_id["alert-2"]
    assert alert_2["success"] is True
    assert alert_2["action"] == "close"
    assert alert_2["note"] in (None, "")
    assert alert_2["triage_event"]["details"]["note"] == ""
    assert alert_2["triage_event"]["details"]["action"] == "close"
    assert alert_2.get("error") in (None, "")

    alert_3 = results_by_id["alert-3"]
    assert alert_3["success"] is False
    assert alert_3["action"] == "escalate"
    assert alert_3["error"] == "Routing health alert not found"
    assert alert_3["triage_event"] is None

    assert logged_events == [
        {
            "event_type": "routing_health_alert_triage",
            "user_id": "agency_test",
            "details": {
                "target_event_id": "alert-1",
                "target_event_type": "routing_health_alert",
                "trip_id": "trip_alpha",
                "status": "warning",
                "workflow": "extraction",
                "note": "Handled first",
                "action": "acknowledge",
            },
        },
        {
            "event_type": "routing_health_alert_triage",
            "user_id": "agency_test",
            "details": {
                "target_event_id": "alert-2",
                "target_event_type": "routing_health_alert",
                "trip_id": "trip_alpha",
                "status": "critical",
                "workflow": "trip_scoring",
                "note": "",
                "action": "close",
            },
        },
    ]


def test_suppress_routing_health_paging_creates_auditable_event(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {
                "id": "paging-1",
                "type": "routing_health_paging_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T09:15:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "critical",
                    "occurrence_index": 3,
                },
            },
        ][:limit],
    )

    logged_events: list[dict] = []

    def log_event_stub(event_type: str, user_id: str, details: dict):
        logged_events.append({"event_type": event_type, "user_id": user_id, "details": details})
        return {
            "id": "suppressed-1",
            "type": event_type,
            "user_id": user_id,
            "timestamp": "2026-07-01T09:16:00.000Z",
            "details": details,
        }

    monkeypatch.setattr(legacy_ops.AuditStore, "log_event", log_event_stub)

    payload = {"note": "Mute paging for one hour", "suppress_for_minutes": 60}
    resp = session_client.post("/audit/paging-1/suppress-routing-health-paging", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["event_id"] == "paging-1"
    assert data["suppression_event"]["id"] == "suppressed-1"
    assert data["suppression_event"]["type"] == "routing_health_paging_alert_suppressed"
    assert data["suppression_event"]["details"]["target_event_id"] == "paging-1"
    assert data["suppression_event"]["details"]["target_event_type"] == "routing_health_paging_alert"
    assert data["suppression_event"]["details"]["trip_id"] == "trip_alpha"
    assert data["suppression_event"]["details"]["status"] == "critical"
    assert data["suppression_event"]["details"]["occurrence_index"] == 3
    assert data["suppression_event"]["details"]["suppress_for_minutes"] == 60
    assert isinstance(data["suppression_event"]["details"]["suppress_until"], str)
    assert data["suppression_event"]["details"]["note"] == "Mute paging for one hour"
    assert len(logged_events) == 1
    assert logged_events[0]["event_type"] == "routing_health_paging_alert_suppressed"


def test_export_routing_health_evidence_supports_csv(session_client, monkeypatch):
    monkeypatch.setattr(
        legacy_ops.TripStore,
        "list_trips",
        lambda agency_id, limit=10000: [{"id": "trip_alpha"}] if agency_id == "agency_test" else [],
    )
    monkeypatch.setattr(
        legacy_ops.AuditStore,
        "get_events",
        lambda limit=100: [
            {
                "id": "alert-1",
                "type": "routing_health_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T09:00:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "critical",
                    "workflow": "extraction",
                    "metric": "fallback_trigger_rate",
                    "min_occurrences": 6,
                    "window_minutes": 120,
                },
            },
            {
                "id": "paging-1",
                "type": "routing_health_paging_alert",
                "user_id": "system",
                "timestamp": "2026-07-01T09:05:00.000Z",
                "details": {
                    "trip_id": "trip_alpha",
                    "status": "critical",
                    "occurrence_index": 2,
                    "sustained_window_seconds": 600,
                    "paging_cooldown_seconds": 1200,
                },
            },
        ][:limit],
    )

    response = session_client.get("/audit/routing-health/export?format=csv&include_paging=true&limit=100")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    text = response.text
    assert "id,type,trip_id,timestamp,status,workflow,metric" in text
    assert "routing_health_alert" in text
