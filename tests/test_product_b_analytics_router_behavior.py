"""Behavior tests for Phase 3 Slice F product-b analytics router extraction."""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from server import app
from routers import product_b_analytics


@pytest.fixture(autouse=True)
def override_product_b_analytics_dependencies():
    """Provide deterministic dependency overrides for route behavior tests."""
    original = dict(app.dependency_overrides)
    app.dependency_overrides[product_b_analytics.get_current_agency] = lambda: SimpleNamespace(id="agency_test")
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


def test_product_b_kpis_preserves_query_and_agency_dependency_profile():
    params = list(inspect.signature(product_b_analytics.get_product_b_kpis).parameters.keys())
    assert params == ["window_days", "qualified_only", "agency"]
    assert "_perm" not in params

    route = _get_route("/analytics/product-b/kpis", "GET")
    dependency_calls = [dep.call for dep in route.dependant.dependencies]

    assert product_b_analytics.get_current_agency in dependency_calls


def test_product_b_kpis_calls_compute_with_window_and_qualified_only(session_client, monkeypatch):
    captured = {}

    def _compute_kpis(*, window_days, qualified_only):
        captured["window_days"] = window_days
        captured["qualified_only"] = qualified_only
        return {
            "window_days": window_days,
            "qualified_only": qualified_only,
            "kpis": {"sessions": 7},
        }

    monkeypatch.setattr(product_b_analytics.ProductBEventStore, "compute_kpis", _compute_kpis)

    resp = session_client.get("/analytics/product-b/kpis?window_days=45&qualified_only=true")
    assert resp.status_code == 200
    assert captured["window_days"] == 45
    assert captured["qualified_only"] is True

    body = resp.json()
    assert body["window_days"] == 45
    assert body["qualified_only"] is True
    assert body["kpis"]["sessions"] == 7
