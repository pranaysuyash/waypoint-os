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


def test_compute_kpis_exposes_observed_inferred_unknown_and_dark_funnel(isolated_product_b_store):
    store = isolated_product_b_store

    def add_inquiry(inquiry_id: str, event_suffix: str, confidence_tier: str | None):
        store.log_event(
            store.build_event(
                event_name="intake_started",
                session_id=f"sess_{event_suffix}",
                inquiry_id=inquiry_id,
                trip_id=f"trip_{event_suffix}",
                actor_type="traveler",
                actor_id=None,
                workspace_id="waypoint-hq",
                channel="web",
                locale="en-US",
                currency="USD",
                event_id=f"evt_{event_suffix}_1",
                occurred_at="2026-05-07T10:00:00+00:00",
                properties={
                    "input_mode": "freeform_text",
                    "has_destination": True,
                    "has_dates": True,
                    "has_budget_band": False,
                    "has_traveler_profile": True,
                },
            )
        )
        store.log_event(
            store.build_event(
                event_name="first_credible_finding_shown",
                session_id=f"sess_{event_suffix}",
                inquiry_id=inquiry_id,
                trip_id=f"trip_{event_suffix}",
                actor_type="system",
                actor_id=None,
                workspace_id="waypoint-hq",
                channel="api",
                locale="en-US",
                currency="USD",
                event_id=f"evt_{event_suffix}_2",
                occurred_at="2026-05-07T10:00:01+00:00",
                properties={
                    "time_from_intake_start_ms": 800,
                    "finding_id": f"fnd_{event_suffix}",
                    "finding_category": "policy",
                    "severity": "must_fix",
                    "confidence_score": 0.9,
                    "evidence_present": True,
                },
            )
        )
        store.log_event(
            store.build_event(
                event_name="action_packet_shared",
                session_id=f"sess_{event_suffix}",
                inquiry_id=inquiry_id,
                trip_id=f"trip_{event_suffix}",
                actor_type="traveler",
                actor_id=None,
                workspace_id="waypoint-hq",
                channel="web",
                locale="en-US",
                currency="USD",
                event_id=f"evt_{event_suffix}_3",
                occurred_at="2026-05-07T10:00:02+00:00",
                properties={
                    "packet_id": f"pkt_{event_suffix}",
                    "share_channel": "copy_paste",
                    "had_manual_edits": False,
                },
            )
        )
        if confidence_tier is not None:
            store.log_event(
                store.build_event(
                    event_name="agency_revision_reported",
                    session_id=f"sess_{event_suffix}",
                    inquiry_id=inquiry_id,
                    trip_id=f"trip_{event_suffix}",
                    actor_type="traveler",
                    actor_id=None,
                    workspace_id="waypoint-hq",
                    channel="web",
                    locale="en-US",
                    currency="USD",
                    event_id=f"evt_{event_suffix}_4",
                    occurred_at="2026-05-07T10:00:03+00:00",
                    properties={
                        "revision_report_mode": "manual",
                        "revision_outcome": "revised",
                        "time_from_share_ms": 2000,
                        "confidence_tier": confidence_tier,
                    },
                )
            )

    add_inquiry("inq_obs", "obs", "observed")
    add_inquiry("inq_inf", "inf", "inferred")
    add_inquiry("inq_unk", "unk", None)

    kpis = store.compute_kpis(window_days=365, qualified_only=True)

    assert kpis["counts"]["observed_revised"] == 1
    assert kpis["counts"]["inferred_revised"] == 1
    assert kpis["counts"]["unknown_outcomes"] == 1
    assert kpis["kpis"]["dark_funnel_rate"] == pytest.approx(1 / 3)
    assert kpis["confidence_tiers"] == {"observed": 1, "inferred": 1, "unknown": 1}


def test_public_checker_run_is_public_route(session_client, monkeypatch):
    import server

    monkeypatch.setattr(
        server,
        "_run_public_checker_submission",
        lambda _payload: {
            "run_id": "pc-run-1",
            "state": "completed",
            "trip_id": "trip_1",
            "agency_id": "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
            "steps_completed": [],
            "events": [],
            "follow_up_questions": [],
            "hard_blockers": [],
            "soft_blockers": [],
        },
    )

    resp = session_client.post(
        "/api/public-checker/run",
        headers={"Authorization": "Bearer clearly-invalid-token"},
        json={"raw_note": "test note", "retention_consent": True},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["run_id"] == "pc-run-1"


def test_public_checker_run_rejects_unknown_fields(session_client):
    resp = session_client.post(
        "/api/public-checker/run",
        json={"raw_note": "test note", "retention_consent": True, "unknown_field": "boom"},
    )

    assert resp.status_code == 422


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


def test_public_checker_event_api_rejects_malformed_payload(session_client):
    resp = session_client.post(
        "/api/public-checker/events",
        json={
            "event_name": "intake_started",
            "session_id": "sess_1",
            "inquiry_id": "inq_1",
            "actor_type": "traveler",
            "channel": "web",
            "properties": [],
        },
    )

    assert resp.status_code == 422


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


def test_product_b_kpis_requires_auth(session_client):
    resp_invalid = session_client.get(
        "/analytics/product-b/kpis",
        headers={"Authorization": "Bearer clearly-invalid-token"},
    )
    assert resp_invalid.status_code == 401

    resp_missing = session_client.get(
        "/analytics/product-b/kpis",
        headers={"Authorization": ""},
    )
    assert resp_missing.status_code == 401


def test_public_checker_event_api_rejects_oversized_payload(session_client):
    giant_payload = "x" * 20000
    resp = session_client.post(
        "/api/public-checker/events",
        json={
            "event_name": "intake_started",
            "session_id": "sess_1",
            "inquiry_id": "inq_1",
            "actor_type": "traveler",
            "channel": "web",
            "properties": {
                "input_mode": "freeform_text",
                "has_destination": True,
                "has_dates": True,
                "has_budget_band": False,
                "has_traveler_profile": True,
                "oversized": giant_payload,
            },
        },
    )
    assert resp.status_code == 413


def test_public_checker_run_masks_internal_errors(monkeypatch):
    import server
    import spine_api.services.public_checker_service as public_checker_service

    def _raise_internal(*_args, **_kwargs):
        raise RuntimeError("sensitive internal failure details")

    monkeypatch.setattr(public_checker_service, "run_spine_once", _raise_internal)

    with pytest.raises(server.HTTPException) as exc:
        server._run_public_checker_submission({"raw_note": "test note", "retention_consent": True})

    assert exc.value.status_code == 500
    assert "sensitive internal failure details" not in str(exc.value.detail)
    assert "Public checker submission failed" in str(exc.value.detail)


def test_public_checker_export_delete_require_auth(session_client):
    export_resp = session_client.get(
        "/api/public-checker/trip_abc/export",
        headers={"Authorization": ""},
    )
    delete_resp = session_client.delete(
        "/api/public-checker/trip_abc",
        headers={"Authorization": ""},
    )

    assert export_resp.status_code == 401
    assert delete_resp.status_code == 401
