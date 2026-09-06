"""Behavior tests for Phase 3 Slice F product-b analytics router extraction."""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from server import app
from routers import product_b_analytics
from spine_api.core.auth import get_current_user
from spine_api.models.product_b_analytics import ProductBKpiResponse


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
    assert route.response_model is ProductBKpiResponse


def test_product_b_kpis_calls_compute_with_window_and_qualified_only(session_client, monkeypatch):
    captured = {}

    def _compute_kpis(*, window_days, qualified_only, workspace_id):
        captured["window_days"] = window_days
        captured["qualified_only"] = qualified_only
        captured["workspace_id"] = workspace_id
        return {
            "scope": {"type": "agency", "workspace_id": workspace_id, "workspace_count": 1},
            "window_days": window_days,
            "qualified_only": qualified_only,
            "kpis": {"sessions": 7},
            "sample": {},
            "confidence_tiers": {},
            "counts": {},
            "definitions": {},
            "provenance": {"data_source": "test", "generated_at": "2026-09-03T00:00:00+00:00"},
        }

    monkeypatch.setattr(product_b_analytics.ProductBEventStore, "compute_kpis", _compute_kpis)

    resp = session_client.get("/analytics/product-b/kpis?window_days=45&qualified_only=true")
    assert resp.status_code == 200
    assert captured["window_days"] == 45
    assert captured["qualified_only"] is True
    assert captured["workspace_id"] == "agency_test"

    body = resp.json()
    assert body["window_days"] == 45
    assert body["qualified_only"] is True
    assert body["kpis"]["sessions"] == 7


def test_platform_product_b_kpis_requires_platform_role():
    route = _get_route("/platform/admin/analytics/product-b/kpis", "GET")
    dependency_calls = [dep.call for dep in route.dependant.dependencies]

    assert any(call.__name__ == "platform_role_guard" for call in dependency_calls)
    assert route.response_model is ProductBKpiResponse


def test_platform_product_b_kpis_denies_ordinary_agency_principal(session_client):
    response = session_client.get("/platform/admin/analytics/product-b/kpis")
    assert response.status_code == 403
    assert response.json()["detail"] == "Platform administrator access required"


def test_platform_product_b_kpis_uses_global_scope(session_client, monkeypatch):
    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="platform-owner",
        platform_role="super_admin",
    )
    captured = {}

    def _compute_kpis(*, window_days, qualified_only):
        captured.update(window_days=window_days, qualified_only=qualified_only)
        return {
            "scope": {"type": "global", "workspace_id": None, "workspace_count": 2},
            "window_days": window_days,
            "qualified_only": qualified_only,
            "kpis": {},
            "sample": {},
            "confidence_tiers": {},
            "counts": {},
            "definitions": {},
            "provenance": {"data_source": "test", "generated_at": "2026-09-03T00:00:00+00:00"},
        }

    monkeypatch.setattr(product_b_analytics.ProductBEventStore, "compute_kpis", _compute_kpis)
    try:
        response = session_client.get("/platform/admin/analytics/product-b/kpis?window_days=7&qualified_only=true")
    finally:
        app.dependency_overrides = original

    assert response.status_code == 200
    assert captured == {"window_days": 7, "qualified_only": True}
    assert response.headers["x-ratelimit-limit"] == "60"
    assert response.json()["scope"] == {"type": "global", "workspace_id": None, "workspace_count": 2}
