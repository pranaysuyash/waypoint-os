from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
from src.analytics import logger as analytics_logger
from src.evals.audit.public_authority import RoutingHealthAuthority


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
        "routing_metrics": {"fallback_trigger_rate": 0.45},
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
        "review_cascade_timeline": [
            {
                "workflow_unit_id": "evt-1",
                "workflow_type": "extraction",
                "subject_id": "doc-a",
                "subject_type": "document_extraction",
                "input_artifact_id": "doc-a",
                "failure_signature": "passport|gpt-4o|schema_validation_failed",
                "failure_layer": "schema",
                "next_fix_layer": "schema_contract",
                "final_acceptance_status": "pending_review",
                "review_workflow_unit_id": "review-1",
                "cascade": [
                    {
                        "stage": "execution_event",
                        "execution_event_id": "evt-1",
                        "workflow_type": "extraction",
                        "event_type": "extraction_run_completed",
                        "created_at": "2026-06-18T10:00:00+00:00",
                        "timestamp": "2026-06-18T10:00:00+00:00",
                        "failure_signature": "passport|gpt-4o|schema_validation_failed",
                        "failure_layer": "schema",
                        "review_trigger_reason": "manual_review_required",
                        "review_outcome": "manual_apply",
                        "fallback_trigger_reason": None,
                        "fallback_result": None,
                    }
                ],
            }
        ],
    }
    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        AsyncMock(return_value=mocked_summary),
    )
    mocked_authority = RoutingHealthAuthority(
        status="warning",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.1, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: mocked_authority,
    )

    response = session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&min_occurrences=3&window_minutes=1440"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["trip_id"] == trip_id
    assert payload["workflow"] == "extraction"
    assert payload["summary"]["routing_metrics"]["fallback_trigger_rate"] == 0.45
    routing_health = payload["routing_health"]
    assert routing_health["status"] == "warning"
    assert routing_health["alerts"][0]["metric"] == "fallback_trigger_rate"
    assert payload["summary"]["work_items"][0]["failure_signature"].startswith("passport|openai")
    assert payload["summary"]["canonical_evidence_records"][0]["workflow_unit_id"] == "evt-1"
    assert payload["summary"]["review_cascade_timeline"][0]["workflow_unit_id"] == "evt-1"
    assert routing_health["authority"]["source"] == "eval_snapshot"
    assert routing_health["authority"]["status"] == "warning"
    assert isinstance(routing_health["alerts"], list)


def test_agentic_eval_endpoint_rejects_unknown_workflow(offline_session_client):
    response = offline_session_client.get(
        f"/api/trips/{uuid4().hex}/agentic-eval?workflow=unknown_workflow"
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_agentic_eval_endpoint_still_returns_routing_health_when_metrics_missing(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    mocked_summary = {"summary_marker": "no_metrics"}

    async def _summary(*args, **kwargs):
        return mocked_summary

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _summary,
    )

    response = offline_session_client.get(f"/api/trips/{trip_id}/agentic-eval")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["summary"] == mocked_summary
    assert payload["routing_health"]["status"] == "healthy"
    assert payload["routing_health"]["alerts"] == []


def test_agentic_eval_endpoint_enforces_routing_health_alert_contract(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    mocked_summary = {
        "summary_marker": "contract-check",
        "routing_metrics": {
            "fallback_trigger_rate": 0.95,
            "false_escalation_rate": 0.6,
        },
    }

    async def _summary(*args, **kwargs):
        return mocked_summary

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _summary,
    )
    mocked_authority = RoutingHealthAuthority(
        status="critical",
        blocks_ci=True,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.5},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: mocked_authority,
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&window_minutes=30"
    )

    assert response.status_code == 200
    payload = response.json()
    routing_health = payload["routing_health"]
    assert routing_health["status"] == "critical"
    assert routing_health["alert_count"] >= 1
    assert routing_health["alerts"], "expected at least one alert"
    for alert in routing_health["alerts"]:
        assert {"metric", "severity", "actual_value", "threshold", "message"} <= set(alert.keys())
        assert alert["severity"] in {"warning", "critical"}
        assert isinstance(alert["actual_value"], float)
        assert isinstance(alert["threshold"], float)
    assert any(a["severity"] == "critical" for a in routing_health["alerts"])
    assert routing_health["authority"]["source"] == "eval_snapshot"
    assert routing_health["authority"]["status"] == "critical"


def test_agentic_eval_endpoint_emits_routing_health_alert_for_warning_or_critical(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    emitted_alerts = []

    def _capture_alert(trip_id: str, routing_health: dict, authority: dict, **kwargs):
        emitted_alerts.append({
            "trip_id": trip_id,
            "routing_health": routing_health,
            "authority": authority,
            "kwargs": kwargs,
        })

    monkeypatch.setattr(
        confirmations.TripEventLogger,
        "log_routing_health_alert",
        staticmethod(_capture_alert),
    )

    mocked_summary = {
        "routing_metrics": {
            "fallback_trigger_rate": 0.45,
            "false_escalation_rate": 0.2,
        },
    }

    async def _warning_summary(*args, **kwargs):
        return mocked_summary

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _warning_summary,
    )

    warning_authority = RoutingHealthAuthority(
        status="warning",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: warning_authority,
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&window_minutes=30"
    )

    assert response.status_code == 200
    payload = response.json()
    routing_health = payload["routing_health"]
    assert routing_health["status"] == "warning"
    assert routing_health["alert_count"] >= 1
    assert len(emitted_alerts) == 1
    event = emitted_alerts[0]
    assert event["trip_id"] == trip_id
    assert event["routing_health"]["status"] == "warning"
    assert event["authority"]["status"] == "warning"
    assert event["kwargs"]["workflow"] == "extraction"
    assert event["kwargs"]["window_minutes"] == 30
    assert event["kwargs"]["min_occurrences"] == 3
    assert event["kwargs"]["metrics_snapshot"] == routing_health["metrics_snapshot"]

    emitted_alerts.clear()

    async def _healthy_summary(*args, **kwargs):
        return {"routing_metrics": {"fallback_trigger_rate": 0.01}}

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _healthy_summary,
    )

    healthy_authority = RoutingHealthAuthority(
        status="healthy",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: healthy_authority,
    )

    healthy_response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?window_minutes=30"
    )

    assert healthy_response.status_code == 200
    assert healthy_response.json()["routing_health"]["status"] == "healthy"
    assert len(emitted_alerts) == 0


def test_agentic_eval_endpoint_persists_routing_health_alert_event(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    persisted_events = []

    def _capture_log_event(event_type: str, user_id: str, details: dict):
        persisted_events.append({
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        })

    monkeypatch.setattr(analytics_logger.AuditStore, "log_event", _capture_log_event)

    async def _warning_summary(*args, **kwargs):
        return {"routing_metrics": {"fallback_trigger_rate": 0.45}}

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _warning_summary,
    )

    warning_authority = RoutingHealthAuthority(
        status="warning",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: warning_authority,
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&window_minutes=30"
    )

    assert response.status_code == 200
    assert response.json()["routing_health"]["status"] == "warning"
    assert len(persisted_events) == 1
    persisted = persisted_events[0]
    assert persisted["event_type"] == "routing_health_alert"
    assert persisted["user_id"] == "system"
    assert persisted["details"]["trip_id"] == trip_id
    assert persisted["details"]["status"] == "warning"


def test_agentic_eval_endpoint_skips_duplicate_routing_health_alert_event(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    persisted_events = []

    now = datetime.now(timezone.utc).isoformat()
    existing_alert_signature = analytics_logger.TripEventLogger._build_routing_health_alert_signature(
        trip_id=trip_id,
        routing_health={
            "status": "warning",
            "alert_count": 1,
            "alerts": [
                {
                    "metric": "fallback_trigger_rate",
                    "severity": "warning",
                    "actual_value": 0.45,
                    "threshold": 0.3,
                }
            ],
        },
        authority={"status": "warning", "source": "eval_snapshot", "blocks_ci": False},
        workflow="extraction",
        workflow_unit_id=None,
        min_occurrences=3,
        window_minutes=30,
    )

    def _capture_get_events(limit: int = 100):
        return [
            {
                "id": "evt_previous",
                "type": "routing_health_alert",
                "timestamp": now,
                "details": {
                    "trip_id": trip_id,
                    "status": "warning",
                    "alert_count": 1,
                    "alerts": [
                        {
                            "metric": "fallback_trigger_rate",
                            "severity": "warning",
                            "actual_value": 0.45,
                            "threshold": 0.3,
                        }
                    ],
                    "workflow": "extraction",
                    "workflow_unit_id": None,
                    "min_occurrences": 3,
                    "window_minutes": 30,
                    "authority": {"source": "eval_snapshot", "blocks_ci": False},
                    "alert_signature": existing_alert_signature,
                },
            }
        ]

    def _capture_log_event(event_type: str, user_id: str, details: dict):
        persisted_events.append({
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        })

    monkeypatch.setattr(analytics_logger.AuditStore, "get_events", _capture_get_events)
    monkeypatch.setattr(analytics_logger.AuditStore, "log_event", _capture_log_event)

    async def _warning_summary(*args, **kwargs):
        return {"routing_metrics": {"fallback_trigger_rate": 0.45}}

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _warning_summary,
    )

    warning_authority = RoutingHealthAuthority(
        status="warning",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: warning_authority,
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&window_minutes=30"
    )

    assert response.status_code == 200
    assert response.json()["routing_health"]["status"] == "warning"
    assert len(persisted_events) == 0


def test_agentic_eval_endpoint_relogs_routing_health_alert_when_status_changes(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    persisted_events = []

    now = datetime.now(timezone.utc).isoformat()

    def _capture_get_events(limit: int = 100):
        return [
            {
                "id": "evt_previous",
                "type": "routing_health_alert",
                "timestamp": now,
                "details": {
                    "trip_id": trip_id,
                    "status": "warning",
                    "alert_count": 1,
                    "alerts": [
                        {
                            "metric": "fallback_trigger_rate",
                            "severity": "warning",
                            "actual_value": 0.3,
                            "threshold": 0.15,
                        }
                    ],
                    "workflow": "extraction",
                    "workflow_unit_id": None,
                    "min_occurrences": 3,
                    "window_minutes": 30,
                    "authority": {"source": "eval_snapshot", "blocks_ci": False},
                },
            }
        ]

    def _capture_log_event(event_type: str, user_id: str, details: dict):
        persisted_events.append({
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        })

    monkeypatch.setattr(analytics_logger.AuditStore, "get_events", _capture_get_events)
    monkeypatch.setattr(analytics_logger.AuditStore, "log_event", _capture_log_event)

    async def _critical_summary(*args, **kwargs):
        return {"routing_metrics": {"fallback_trigger_rate": 0.95}}

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _critical_summary,
    )

    critical_authority = RoutingHealthAuthority(
        status="critical",
        blocks_ci=True,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.5},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: critical_authority,
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&window_minutes=30"
    )

    assert response.status_code == 200
    assert response.json()["routing_health"]["status"] == "critical"
    assert len(persisted_events) == 1
    assert persisted_events[0]["event_type"] == "routing_health_alert"
    assert persisted_events[0]["details"]["status"] == "critical"


def test_agentic_eval_endpoint_emits_paging_alert_when_warning_persists_across_window(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    persisted_events = []

    now = datetime.now(timezone.utc)
    existing_alert = {
        "id": "evt_previous_1",
        "type": "routing_health_alert",
        "timestamp": (now - timedelta(seconds=120)).isoformat(),
        "details": {
            "trip_id": trip_id,
            "status": "warning",
            "alert_count": 1,
            "alerts": [
                {
                    "metric": "fallback_trigger_rate",
                    "severity": "warning",
                    "actual_value": 0.45,
                    "threshold": 0.3,
                }
            ],
            "workflow": "extraction",
            "workflow_unit_id": None,
            "min_occurrences": 3,
            "window_minutes": 30,
            "authority": {"source": "eval_snapshot", "blocks_ci": False},
        },
    }
    existing_alert_2 = {
        "id": "evt_previous_2",
        "type": "routing_health_alert",
        "timestamp": (now - timedelta(seconds=60)).isoformat(),
        "details": existing_alert["details"].copy(),
    }

    def _capture_get_events(limit: int = 100):
        return [existing_alert, existing_alert_2][:limit]

    def _capture_log_event(event_type: str, user_id: str, details: dict):
        persisted_events.append({
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        })

    monkeypatch.setattr(analytics_logger.AuditStore, "get_events", _capture_get_events)
    monkeypatch.setattr(analytics_logger.AuditStore, "log_event", _capture_log_event)
    monkeypatch.setattr(
        analytics_logger,
        "_ROUTING_HEALTH_ALERT_DEDUPE_WINDOW_SECONDS",
        1,
    )

    async def _warning_summary(*args, **kwargs):
        return {"routing_metrics": {"fallback_trigger_rate": 0.45}}

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _warning_summary,
    )

    warning_authority = RoutingHealthAuthority(
        status="warning",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: warning_authority,
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&window_minutes=30"
    )

    assert response.status_code == 200
    assert response.json()["routing_health"]["status"] == "warning"
    assert len(persisted_events) == 2
    event_types = {item["event_type"] for item in persisted_events}
    assert event_types == {"routing_health_alert", "routing_health_paging_alert"}
    paging_event = next(
        item for item in persisted_events if item["event_type"] == "routing_health_paging_alert"
    )
    assert paging_event["details"]["trip_id"] == trip_id
    assert paging_event["details"]["status"] == "warning"
    assert paging_event["details"]["occurrence_index"] == 3


def test_agentic_eval_endpoint_does_not_emit_duplicate_paging_alert_when_cooldown_active(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    persisted_events = []

    now = datetime.now(timezone.utc)
    existing_alert = {
        "id": "evt_previous_1",
        "type": "routing_health_alert",
        "timestamp": (now - timedelta(seconds=120)).isoformat(),
        "details": {
            "trip_id": trip_id,
            "status": "warning",
            "alert_count": 1,
            "alerts": [
                {
                    "metric": "fallback_trigger_rate",
                    "severity": "warning",
                    "actual_value": 0.45,
                    "threshold": 0.3,
                }
            ],
            "workflow": "extraction",
            "workflow_unit_id": None,
            "min_occurrences": 3,
            "window_minutes": 30,
            "authority": {"source": "eval_snapshot", "blocks_ci": False},
        },
    }
    existing_alert_2 = {
        "id": "evt_previous_2",
        "type": "routing_health_alert",
        "timestamp": (now - timedelta(seconds=60)).isoformat(),
        "details": {
            **existing_alert["details"],
        },
    }
    existing_paging = {
        "id": "evt_paging",
        "type": "routing_health_paging_alert",
        "timestamp": now.isoformat(),
        "details": {
            "trip_id": trip_id,
            "status": "warning",
            "alert_signature": analytics_logger.TripEventLogger._build_routing_health_paging_signature(
                trip_id=trip_id,
                status="warning",
                authority={"source": "eval_snapshot", "blocks_ci": False},
                workflow="extraction",
                workflow_unit_id=None,
                min_occurrences=3,
                window_minutes=30,
            ),
            "occurrence_index": 3,
            "workflow": "extraction",
            "workflow_unit_id": None,
            "window_minutes": 30,
            "min_occurrences": 3,
        },
    }

    def _capture_get_events(limit: int = 100):
        return [existing_alert, existing_alert_2, existing_paging][:limit]

    def _capture_log_event(event_type: str, user_id: str, details: dict):
        persisted_events.append({
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        })

    monkeypatch.setattr(analytics_logger.AuditStore, "get_events", _capture_get_events)
    monkeypatch.setattr(analytics_logger.AuditStore, "log_event", _capture_log_event)
    monkeypatch.setattr(
        analytics_logger,
        "_ROUTING_HEALTH_ALERT_DEDUPE_WINDOW_SECONDS",
        1,
    )

    async def _warning_summary(*args, **kwargs):
        return {"routing_metrics": {"fallback_trigger_rate": 0.45}}

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _warning_summary,
    )

    warning_authority = RoutingHealthAuthority(
        status="warning",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: warning_authority,
    )

    response = offline_session_client.get(
        f"/api/trips/{trip_id}/agentic-eval?workflow=extraction&window_minutes=30"
    )

    assert response.status_code == 200
    assert response.json()["routing_health"]["status"] == "warning"
    assert len(persisted_events) == 1
    assert persisted_events[0]["event_type"] == "routing_health_alert"


def test_agentic_eval_endpoint_does_not_emit_for_healthy_routing_health(
    offline_session_client,
    monkeypatch,
):
    trip_id = f"agentic-eval-{uuid4().hex}"
    emitted_alerts = []

    def _capture_alert(trip_id: str, routing_health: dict, authority: dict, **kwargs):
        emitted_alerts.append({"trip_id": trip_id, "routing_health": routing_health})

    monkeypatch.setattr(
        confirmations.TripEventLogger,
        "log_routing_health_alert",
        staticmethod(_capture_alert),
    )

    async def _summary(*args, **kwargs):
        return {"routing_metrics": {"fallback_trigger_rate": 0.01}}

    monkeypatch.setattr(
        confirmations.agentic_eval_service,
        "get_trip_agentic_eval_summary",
        _summary,
    )

    healthy_authority = RoutingHealthAuthority(
        status="healthy",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3, "fallback_trigger_rate_critical": 0.9},
    )
    monkeypatch.setattr(
        confirmations,
        "resolve_routing_health_authority",
        lambda: healthy_authority,
    )

    response = offline_session_client.get(f"/api/trips/{trip_id}/agentic-eval")

    assert response.status_code == 200
    assert response.json()["routing_health"]["status"] == "healthy"
    assert len(emitted_alerts) == 0


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
