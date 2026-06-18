from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from spine_api.routers import confirmations
from spine_api.services import agentic_eval_service


def test_agentic_eval_endpoint_returns_summary_from_mocked_service(session_client, monkeypatch):
    trip_id = f"agentic-eval-{uuid4().hex}"
    mocked_summary = {
        "total_events_considered": 3,
        "window_minutes": 1440,
        "routing_metrics": {"fallback_trigger_count": 2},
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


def test_agentic_eval_endpoint_rejects_unknown_workflow(session_client):
    response = session_client.get(
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
