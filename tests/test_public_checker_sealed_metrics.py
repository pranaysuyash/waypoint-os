"""WOBS 2026-09-09 P1 — server-sealed funnel metrics (Poisoned-Pipe Gate 0).

check_completed is emitted only by public_checker_service after the trip row
is persisted. The client-fed /events endpoint must reject it (403); the store
must accept the service-shaped envelope and enforce its required properties.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from spine_api.product_b_events import ProductBEventStore
from spine_api.services.public_checker_service import build_check_completed_event


@pytest.fixture()
def isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "product_b_events"
    monkeypatch.setattr(ProductBEventStore, "DATA_DIR", data_dir)
    monkeypatch.setattr(ProductBEventStore, "RAW_FILE", data_dir / "events_raw.jsonl")
    monkeypatch.setattr(ProductBEventStore, "NORMALIZED_FILE", data_dir / "events_normalized.jsonl")
    return ProductBEventStore


def _service_event() -> dict:
    return build_check_completed_event(
        session_id="sess_x",
        inquiry_id="inq_x",
        trip_id="trip_abc123",
        workspace_id="agency-1",
        input_mode="freeform_text",
        finding_count=3,
        hard_blocker_count=1,
        soft_blocker_count=2,
        overall_score=61,
        execution_ms=812.4,
    )


def test_service_event_passes_store_schema(isolated_store):
    result = isolated_store.log_event(_service_event())
    assert result["status"] == "accepted"
    assert result["event_name"] == "check_completed"


def test_service_event_dedupes(isolated_store):
    event = _service_event()
    assert isolated_store.log_event(event)["status"] == "accepted"
    assert isolated_store.log_event(event)["status"] == "duplicate"


def test_missing_required_property_rejected(isolated_store):
    event = _service_event()
    event["properties"].pop("finding_count")
    with pytest.raises(ValueError, match="finding_count"):
        isolated_store.log_event(event)


def test_overall_score_optional(isolated_store):
    event = build_check_completed_event(
        session_id="s",
        inquiry_id="i",
        trip_id="trip_x",
        workspace_id="w",
        input_mode="upload",
        finding_count=0,
        hard_blocker_count=0,
        soft_blocker_count=0,
        overall_score=None,
        execution_ms=100.0,
    )
    assert "overall_score" not in event["properties"]
    assert isolated_store.log_event(event)["status"] == "accepted"


def test_client_events_endpoint_rejects_check_completed(session_client):
    resp = session_client.post(
        "/api/public-checker/events",
        json={
            "event_name": "check_completed",
            "session_id": "sess_bot",
            "inquiry_id": "inq_bot",
            "actor_type": "system",
            "channel": "api",
            "properties": {
                "input_mode": "freeform_text",
                "finding_count": 99,
                "execution_ms": 1,
            },
        },
    )
    assert resp.status_code == 403
