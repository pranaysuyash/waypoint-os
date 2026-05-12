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
