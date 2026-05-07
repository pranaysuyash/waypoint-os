from __future__ import annotations

from pathlib import Path

import pytest

from spine_api.product_b_events import ProductBEventStore


@pytest.fixture
def isolated_product_b_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "product_b_events"
    raw_file = data_dir / "events_raw.jsonl"
    normalized_file = data_dir / "events_normalized.jsonl"
    monkeypatch.setattr(ProductBEventStore, "DATA_DIR", data_dir)
    monkeypatch.setattr(ProductBEventStore, "RAW_FILE", raw_file)
    monkeypatch.setattr(ProductBEventStore, "NORMALIZED_FILE", normalized_file)
    return ProductBEventStore


def _base_event(store: type[ProductBEventStore], event_name: str = "intake_started"):
    properties = {
        "input_mode": "freeform_text",
        "has_destination": True,
        "has_dates": True,
        "has_budget_band": False,
        "has_traveler_profile": True,
    }
    if event_name == "first_credible_finding_shown":
        properties = {
            "time_from_intake_start_ms": 1200,
            "finding_id": "fnd_1",
            "finding_category": "logistics",
            "severity": "must_fix",
            "confidence_score": 0.82,
            "evidence_present": True,
        }
    return store.build_event(
        event_name=event_name,
        session_id="sess_1",
        inquiry_id="inq_1",
        trip_id="trip_1",
        actor_type="traveler",
        actor_id=None,
        workspace_id="waypoint-hq",
        channel="web",
        locale="en-US",
        currency="USD",
        properties=properties,
        event_id="evt_1",
        occurred_at="2026-05-07T10:00:00+00:00",
    )


def test_log_event_accepts_and_deduplicates(isolated_product_b_store):
    store = isolated_product_b_store
    payload = _base_event(store)

    first = store.log_event(payload)
    second = store.log_event(payload)

    assert first["status"] == "accepted"
    assert second["status"] == "duplicate"

    rows = store.list_events(window_days=365)
    assert len(rows) == 1
    assert rows[0]["event_id"] == "evt_1"


def test_first_credible_requires_evidence_true(isolated_product_b_store):
    store = isolated_product_b_store
    payload = _base_event(store, "first_credible_finding_shown")
    payload["properties"]["evidence_present"] = False

    with pytest.raises(ValueError, match="evidence_present=true"):
        store.log_event(payload)


def test_compute_kpis_respects_qualified_filter(isolated_product_b_store):
    store = isolated_product_b_store

    intake = store.build_event(
        event_name="intake_started",
        session_id="sess_a",
        inquiry_id="inq_a",
        trip_id="trip_a",
        actor_type="traveler",
        actor_id=None,
        workspace_id="waypoint-hq",
        channel="web",
        locale="en-US",
        currency="USD",
        event_id="evt_a1",
        occurred_at="2026-05-07T10:00:00+00:00",
        properties={
            "input_mode": "freeform_text",
            "has_destination": True,
            "has_dates": True,
            "has_budget_band": True,
            "has_traveler_profile": True,
        },
    )
    credible = store.build_event(
        event_name="first_credible_finding_shown",
        session_id="sess_a",
        inquiry_id="inq_a",
        trip_id="trip_a",
        actor_type="system",
        actor_id=None,
        workspace_id="waypoint-hq",
        channel="api",
        locale="en-US",
        currency="USD",
        event_id="evt_a2",
        occurred_at="2026-05-07T10:00:01+00:00",
        properties={
            "time_from_intake_start_ms": 1000,
            "finding_id": "fnd_a",
            "finding_category": "policy",
            "severity": "must_fix",
            "confidence_score": 0.9,
            "evidence_present": True,
        },
    )
    shared = store.build_event(
        event_name="action_packet_shared",
        session_id="sess_a",
        inquiry_id="inq_a",
        trip_id="trip_a",
        actor_type="traveler",
        actor_id=None,
        workspace_id="waypoint-hq",
        channel="web",
        locale="en-US",
        currency="USD",
        event_id="evt_a3",
        occurred_at="2026-05-07T10:00:02+00:00",
        properties={
            "packet_id": "pkt_a",
            "share_channel": "copy_paste",
            "had_manual_edits": False,
        },
    )

    unqualified_shared = store.build_event(
        event_name="action_packet_shared",
        session_id="sess_b",
        inquiry_id="inq_b",
        trip_id="trip_b",
        actor_type="traveler",
        actor_id=None,
        workspace_id="waypoint-hq",
        channel="web",
        locale="en-US",
        currency="USD",
        event_id="evt_b1",
        occurred_at="2026-05-07T11:00:02+00:00",
        properties={
            "packet_id": "pkt_b",
            "share_channel": "copy_paste",
            "had_manual_edits": True,
        },
    )

    for event in (intake, credible, shared, unqualified_shared):
        store.log_event(event)

    all_kpis = store.compute_kpis(window_days=365, qualified_only=False)
    qualified_kpis = store.compute_kpis(window_days=365, qualified_only=True)

    assert all_kpis["counts"]["action_packet_shared"] == 2
    assert qualified_kpis["counts"]["action_packet_shared"] == 1
    assert qualified_kpis["sample"]["qualified_inquiries"] == 1


def test_public_checker_event_api_validation_error(session_client, monkeypatch):
    import server

    def _raise_value_error(_payload):
        raise ValueError("bad event payload")

    monkeypatch.setattr(server.ProductBEventStore, "log_event", _raise_value_error)

    resp = session_client.post(
        "/api/public-checker/events",
        json={
            "event_name": "intake_started",
            "session_id": "sess_1",
            "inquiry_id": "inq_1",
            "actor_type": "traveler",
            "channel": "web",
            "properties": {},
        },
    )

    assert resp.status_code == 400
    assert "bad event payload" in resp.text


def test_product_b_kpis_endpoint_returns_payload(session_client, monkeypatch):
    import server

    monkeypatch.setattr(
        server.ProductBEventStore,
        "compute_kpis",
        lambda window_days, qualified_only: {
            "window_days": window_days,
            "qualified_only": qualified_only,
            "kpis": {"product_a_pull_through": 0.3},
            "sample": {"qualified_inquiries": 5},
        },
    )

    resp = session_client.get("/analytics/product-b/kpis?window_days=14&qualified_only=true")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["window_days"] == 14
    assert data["qualified_only"] is True
    assert data["kpis"]["product_a_pull_through"] == 0.3
