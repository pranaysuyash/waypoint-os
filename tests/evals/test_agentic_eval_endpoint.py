from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from starlette.testclient import TestClient
import pytest

import spine_api.server as spine_api_server
from spine_api.core.security import create_access_token
from spine_api.core import auth as auth_module
from spine_api.core import middleware as middleware_module
from spine_api.routers import confirmations
from spine_api.services import agentic_eval_service


@pytest.fixture
def offline_session_client(monkeypatch):
    fake_user = SimpleNamespace(
        id="323468de-ba3d-437b-aa10-35b281a0c6a6",
        is_active=True,
    )

    class _Result:
        def __init__(self, scalar_result):
            self._scalar_result = scalar_result

        def scalar_one_or_none(self):
            return self._scalar_result

        def scalar(self):
            return self._scalar_result

        def mappings(self):
            return self

        def fetchall(self):
            return []

    class _Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def execute(self, *args, **kwargs):
            return _Result(fake_user)

    class _SessionMaker:
        def __call__(self):
            return _Session()

    class _Membership(SimpleNamespace):
        user_id = "323468de-ba3d-437b-aa10-35b281a0c6a6"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        role = "owner"

    async def _noop_startup_check(*args, **kwargs):
        return None

    monkeypatch.setattr(spine_api_server, "_should_run_startup_mutations", lambda: False)
    monkeypatch.setattr(
        spine_api_server,
        "_ensure_agencies_schema_compatibility",
        _noop_startup_check,
    )
    monkeypatch.setattr(
        spine_api_server,
        "_ensure_memberships_schema_compatibility",
        _noop_startup_check,
    )
    monkeypatch.setattr(
        spine_api_server,
        "_ensure_rls_no_force_on_auth_tables",
        _noop_startup_check,
    )
    monkeypatch.setattr(
        spine_api_server,
        "_deduplicate_memberships_and_agencies",
        _noop_startup_check,
    )
    monkeypatch.setattr(
        spine_api_server,
        "_ensure_users_have_memberships",
        _noop_startup_check,
    )
    monkeypatch.setattr(
        spine_api_server,
        "_validate_public_checker_agency_configuration",
        _noop_startup_check,
    )
    monkeypatch.setattr(
        spine_api_server,
        "_validate_rls_runtime_posture_configuration",
        _noop_startup_check,
    )

    monkeypatch.setattr(middleware_module, "async_session_maker", _SessionMaker())
    original_overrides = dict(spine_api_server.app.dependency_overrides)

    async def _skip_auth():
        return None

    def _fake_membership():
        return _Membership()

    spine_api_server.app.dependency_overrides[auth_module._auth_or_skip] = _skip_auth
    spine_api_server.app.dependency_overrides[
        auth_module.get_current_membership
    ] = _fake_membership
    spine_api_server.app.dependency_overrides[
        auth_module.get_current_agency_id
    ] = lambda: "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"

    token = create_access_token(
        user_id="323468de-ba3d-437b-aa10-35b281a0c6a6",
        agency_id="d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
        role="owner",
        expires_delta=timedelta(hours=12),
    )

    with TestClient(
        spine_api_server.app,
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        try:
            yield client
        finally:
            spine_api_server.app.dependency_overrides = original_overrides


def test_agentic_eval_endpoint_returns_summary_from_mocked_service(
    offline_session_client,
    monkeypatch,
):
    session_client = offline_session_client
    trip_id = f"agentic-eval-{uuid4().hex}"
    mocked_summary = {
        "total_events_considered": 3,
        "window_minutes": 1440,
        "routing_metrics": {"fallback_trigger_count": 2},
        "canonical_evidence_records": [
            {
                "workflow_unit_id": "evt-1",
                "workflow_type": "extraction",
                "input_artifact_id": "doc-a",
                "provider": "openai",
                "model": "gpt-4o",
                "final_acceptance_status": "pending_review",
            }
        ],
        "work_items": [
            {
                "failure_signature": "passport|openai|gpt-4o|schema_validation_failed|attempt-1",
                "failure_layer": "schema",
                "next_fix_layer": "schema_contract",
                "occurrences": 3,
                "first_seen": "2026-06-18T10:00:00+00:00",
                "last_seen": "2026-06-18T10:02:00+00:00",
                "sample_events": ["e1", "e2", "e3"],
            },
        ],
    }
    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        AsyncMock(return_value=mocked_summary),
    )

    response = session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&min_occurrences=3&window_minutes=1440"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["trip_id"] == trip_id
    assert payload["workflow"] == "extraction"
    assert payload["summary"]["routing_metrics"]["fallback_trigger_count"] == 2
    assert payload["summary"]["work_items"][0]["failure_signature"].startswith("passport|openai")
    assert payload["summary"]["canonical_evidence_records"][0]["workflow_unit_id"] == "evt-1"


def test_agentic_eval_endpoint_rejects_unknown_workflow(offline_session_client):
    response = offline_session_client.get(
        f"/api/trips/{uuid4().hex}/agentic-eval?workflow=unknown_workflow"
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_agentic_eval_service_merges_execution_and_review_events(monkeypatch):
    async def fake_get_events(db, trip_id, agency_id, category=None, actor_type=None):
        return [{"id": "evt-1", "event_metadata": {"failure_signature": "sig-a"}}]

    monkeypatch.setattr(
        agentic_eval_service.execution_event_service,
        "get_events",
        fake_get_events,
    )
    monkeypatch.setattr(
        agentic_eval_service.persistence.AuditStore,
        "get_events_for_trip",
        lambda trip_id: [
            {
                "type": "review_action",
                "details": {"trip_id": trip_id, "escalation_outcome": "false_escalation"},
                "timestamp": "2026-06-18T10:00:00+00:00",
            }
        ],
    )
    captured = {}

    def fake_aggregate(events, **kwargs):
        captured["events"] = events
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(agentic_eval_service, "aggregate_eval_records", fake_aggregate)

    result = await agentic_eval_service.get_trip_agentic_eval_summary(
        db=object(),
        trip_id="trip-123",
        agency_id="agency-123",
        workflow="extraction",
        min_occurrences=3,
        window_minutes=60,
    )

    assert result == {"ok": True}
    assert captured["kwargs"]["review_events"][0]["details"]["escalation_outcome"] == "false_escalation"


def test_agentic_eval_endpoint_accepts_workflow_unit_id_filter(
    offline_session_client,
    monkeypatch,
):
    trip_id = uuid4().hex

    async def fake_get_trip_eval_summary(
        db,
        trip_id: str,
        agency_id: str,
        workflow: str | None = None,
        min_occurrences: int = 3,
        window_minutes: int = 24 * 60,
        workflow_unit_id: str | None = None,
        reference_time=None,
    ):
        assert workflow_unit_id == "unit-1"
        return {
            "total_events_considered": 0,
            "window_minutes": window_minutes,
            "routing_metrics": {},
            "canonical_evidence_records": [],
            "work_items": [],
        }

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        AsyncMock(side_effect=fake_get_trip_eval_summary),
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&workflow_unit_id=unit-1"
    )

    assert response.status_code == 200
