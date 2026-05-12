from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

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


def test_compute_kpis_returns_formula_definitions_and_sample_rule(isolated_product_b_store):
    store = isolated_product_b_store

    kpis = store.compute_kpis(window_days=14, qualified_only=True)

    definitions = kpis["definitions"]
    assert definitions["qualified_sample_rule"] == {
        "description": "Qualified inquiries require both intake_started and first_credible_finding_shown in the selected window.",
        "required_events": ["intake_started", "first_credible_finding_shown"],
        "exclusions": ["internal_test_traffic", "insufficient_input_quality", "missing_real_trip_intent"],
        "current_enforcement": "event_presence_only",
    }

    assert definitions["kpis"]["time_to_first_credible_finding_ms"] == {
        "description": "Latency from Product B intake start to first evidence-backed finding.",
        "numerator": "first_credible_finding_shown.properties.time_from_intake_start_ms values",
        "denominator": "qualified inquiries with first_credible_finding_shown",
        "aggregation": "p50 and p90 percentile",
        "window_days": 14,
        "data_source": "data/product_b_events/events_normalized.jsonl",
    }
    assert definitions["kpis"]["forward_without_edit_rate"]["numerator"] == "action_packet_shared where properties.had_manual_edits=false"
    assert definitions["kpis"]["forward_without_edit_rate"]["denominator"] == "all action_packet_shared events"
    assert definitions["kpis"]["agency_revision_rate_observed_7d"]["numerator"] == "inquiries with agency_revision_reported revision_outcome=revised and confidence_tier=observed"
    assert definitions["kpis"]["agency_revision_rate_observed_7d"]["denominator"] == "inquiries with at least one action_packet_shared event"
    assert definitions["kpis"]["product_a_pull_through"]["numerator"] == "product_a_interest_signal events"
    assert definitions["kpis"]["product_a_pull_through"]["denominator"] == "qualified inquiries"


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


def test_public_checker_run_rejects_non_object_payload(session_client):
    resp = session_client.post(
        "/api/public-checker/run",
        json=["raw_note", "test note"],
    )

    assert resp.status_code == 422


def test_public_checker_run_rejects_invalid_structured_json_shape(session_client):
    resp = session_client.post(
        "/api/public-checker/run",
        json={
            "raw_note": "test note",
            "retention_consent": True,
            "structured_json": "not-an-object",
        },
    )

    assert resp.status_code == 422


def test_public_checker_run_rejects_non_string_raw_note(session_client):
    resp = session_client.post(
        "/api/public-checker/run",
        json={
            "raw_note": {"nested": "object-not-string"},
            "retention_consent": True,
        },
    )

    assert resp.status_code == 422


def test_public_checker_run_rejects_non_boolean_retention_consent(session_client):
    resp = session_client.post(
        "/api/public-checker/run",
        json={
            "raw_note": "test note",
            "retention_consent": ["not", "a", "bool"],
        },
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


def test_public_checker_run_endpoint_masks_internal_errors(session_client, monkeypatch):
    import spine_api.services.public_checker_service as public_checker_service

    def _raise_internal(*_args, **_kwargs):
        raise RuntimeError("sensitive endpoint failure details")

    monkeypatch.setattr(public_checker_service.ProductBEventStore, "log_event", lambda _payload: {"status": "accepted"})
    monkeypatch.setattr(public_checker_service, "run_spine_once", _raise_internal)

    resp = session_client.post(
        "/api/public-checker/run",
        json={"raw_note": "test note", "retention_consent": True},
    )

    assert resp.status_code == 500
    assert resp.json()["detail"] == "Public checker submission failed"
    assert "sensitive endpoint failure details" not in resp.text


def test_public_checker_run_redacts_raw_submission_fields_without_consent(monkeypatch):
    import spine_api.services.public_checker_service as public_checker_service

    captured: dict[str, object] = {}

    def _fake_run_spine_once(**_kwargs):
        return SimpleNamespace(
            packet={"score": 82},
            validation={"overall_score": 82},
            decision={"hard_blockers": [], "soft_blockers": []},
            strategy={},
            follow_up_questions=[],
        )

    def _fake_save_processed_trip(payload, **kwargs):
        captured["payload"] = payload
        captured["kwargs"] = kwargs
        return "trip_public_1"

    monkeypatch.setattr(public_checker_service.ProductBEventStore, "log_event", lambda _payload: {"status": "accepted"})
    monkeypatch.setattr(public_checker_service, "run_spine_once", _fake_run_spine_once)

    response = public_checker_service.run_public_checker_submission(
        {
            "raw_note": "private note",
            "owner_note": "private owner note",
            "itinerary_text": "private itinerary text",
            "structured_json": {
                "source_payload": {
                    "kind": "file_upload",
                    "uploaded_file": {"extracted_text": "private file text"},
                }
            },
            "retention_consent": False,
        },
        build_envelopes=lambda _request: ["envelope"],
        load_fixture_expectations=lambda _scenario_id: None,
        to_dict=lambda value: value,
        save_processed_trip=_fake_save_processed_trip,
        get_public_checker_agency_id=lambda: "agency_public_checker",
        logger=logging.getLogger("test.public_checker"),
    )

    assert response.trip_id == "trip_public_1"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    submission = payload["meta"]["submission"]
    assert submission["retention_consent"] is False
    assert "raw_note" not in submission
    assert "owner_note" not in submission
    assert "itinerary_text" not in submission
    assert "structured_json" not in submission


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
