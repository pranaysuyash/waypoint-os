"""
Static guardrails for async run contract.

These checks prevent accidental drift back to synchronous /run payload semantics.
"""

from __future__ import annotations

from fastapi.routing import APIRoute

from spine_api.contract import RunAcceptedResponse, RunStatusResponse, SpineRunResponse
from spine_api.server import app


def _route(path: str, method: str) -> APIRoute:
    method_upper = method.upper()
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method_upper in route.methods:
            return route
    raise AssertionError(f"Route not found: {method_upper} {path}")


def test_post_run_uses_run_accepted_response_model() -> None:
    route = _route("/run", "POST")
    assert route.response_model is RunAcceptedResponse


def test_run_accepted_response_shape_is_minimal_async_contract() -> None:
    fields = set(RunAcceptedResponse.model_fields.keys())
    assert fields == {"run_id", "state"}


def test_run_accepted_response_excludes_sync_payload_fields() -> None:
    forbidden_sync_fields = {
        "ok",
        "packet",
        "validation",
        "decision",
        "strategy",
        "traveler_bundle",
        "internal_bundle",
        "safety",
        "meta",
    }
    fields = set(RunAcceptedResponse.model_fields.keys())
    assert fields.isdisjoint(forbidden_sync_fields)


def test_run_status_response_includes_polling_fields() -> None:
    fields = set(RunStatusResponse.model_fields.keys())
    assert "state" in fields
    assert "steps_completed" in fields
    assert "events" in fields


def test_legacy_spine_run_response_is_not_used_by_post_run() -> None:
    route = _route("/run", "POST")
    assert route.response_model is not SpineRunResponse


def test_unknown_run_events_returns_404_contract() -> None:
    route = _route("/runs/{run_id}/events", "GET")
    assert route.response_model is None
