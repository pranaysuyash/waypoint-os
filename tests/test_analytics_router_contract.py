"""Contract tests for the canonical analytics router extraction."""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from server import app
from routers import analytics


@pytest.fixture(autouse=True)
def override_analytics_dependencies():
    """Provide deterministic dependency overrides for analytics route tests."""
    original = dict(app.dependency_overrides)
    app.dependency_overrides[analytics.get_current_agency] = lambda: SimpleNamespace(id="agency_test")
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


def test_analytics_router_owns_non_product_b_analytics_paths():
    expected_paths = {
        ("GET", "/analytics/summary"),
        ("GET", "/analytics/pipeline"),
        ("GET", "/analytics/team"),
        ("GET", "/analytics/bottlenecks"),
        ("GET", "/analytics/revenue"),
        ("GET", "/analytics/agent/{agent_id}/drill-down"),
        ("GET", "/analytics/alerts"),
        ("POST", "/analytics/alerts/{alert_id}/dismiss"),
        ("GET", "/analytics/reviews"),
        ("GET", "/analytics/reviews/{review_id}"),
        ("POST", "/analytics/reviews/bulk-action"),
        ("GET", "/analytics/escalations"),
        ("GET", "/analytics/funnel"),
        ("POST", "/analytics/export"),
    }

    for method, path in expected_paths:
        route = _get_route(path, method)
        assert inspect.getmodule(route.endpoint) is analytics


def test_escalations_route_preserves_heatmap_shape(session_client, monkeypatch):
    monkeypatch.setattr(
        analytics.TripStore,
        "list_trips",
        lambda **kwargs: [
            {"assigned_to": "agent-a", "analytics": "legacy-string"},
            {"assigned_to": "agent-a", "analytics": {"escalation_severity": "high"}},
            {"assigned_to": "agent-b", "analytics": {"escalation_severity": "critical"}},
        ],
    )

    response = session_client.get("/analytics/escalations")

    assert response.status_code == 200
    body = response.json()
    by_agent = {item["agent_id"]: item for item in body["items"]}
    assert body["total"] == 2
    assert by_agent["agent-a"]["total"] == 2
    assert by_agent["agent-a"]["escalated"] == 1
    assert by_agent["agent-b"]["total"] == 1
    assert by_agent["agent-b"]["escalated"] == 1


def test_export_route_preserves_response_contract(session_client):
    response = session_client.post("/analytics/export", json={"format": "csv"})

    assert response.status_code == 200
    body = response.json()
    assert body["download_url"].startswith("/api/exports/export_")
    assert body["download_url"].endswith(".csv")
    assert body["expires_at"]
