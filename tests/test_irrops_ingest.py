"""IRROPS operator-reported signal ingestion (R2-H tranche, 2026-11-04).

Deterministic severity + closed trigger taxonomy per
Docs/architecture/IRROPS_SEMANTICS_2026-11-04.md; the report endpoint writes
trip["active_disruption"] — the surface the disruption radar already renders
honestly (F-38: no fabricated alerts on empty).
"""

from __future__ import annotations

import pytest

from spine_api.services.irrops import (
    IrropsReportError,
    evaluate_irrops_report,
)


def _trip(stage: str = "booked"):
    return {"id": "trip_irrops_1", "stage": stage}


def test_cancellation_is_critical_with_marker():
    alert = evaluate_irrops_report(
        _trip(), trigger_kind="cancellation", flight_ref="AI-471",
        now_iso="2026-11-04T10:30:00+00:00",
    )
    assert alert["severity"] == "critical"
    assert alert["source"] == "operator_reported"
    assert alert["idempotency_marker"] == "irrops:trip_irrops_1:AI-471:cancellation:2026-11-04T10"
    assert alert["comp_relevant"] is False  # delay-independent triggers set comp flag off


def test_delay_180min_is_critical_and_comp_relevant():
    alert = evaluate_irrops_report(
        _trip(), trigger_kind="delay", flight_ref="UK-913", delay_minutes=185,
        now_iso="2026-11-04T10:30:00+00:00",
    )
    assert alert["severity"] == "critical"
    assert alert["comp_relevant"] is True


def test_delay_threshold_bands():
    assert evaluate_irrops_report(
        _trip(), trigger_kind="delay", flight_ref="F1", delay_minutes=60,
    )["severity"] == "high"
    assert evaluate_irrops_report(
        _trip(), trigger_kind="delay", flight_ref="F2", delay_minutes=45,
    )["severity"] == "medium"


def test_delay_report_without_minutes_is_rejected():
    with pytest.raises(IrropsReportError, match="delay_minutes"):
        evaluate_irrops_report(_trip(), trigger_kind="delay", flight_ref="F3")


def test_unknown_trigger_kind_rejected_closed_taxonomy():
    with pytest.raises(IrropsReportError, match="Unknown trigger kind"):
        evaluate_irrops_report(_trip(), trigger_kind="meteor_strike", flight_ref="F4")


def test_missing_flight_ref_rejected():
    with pytest.raises(IrropsReportError, match="flight_ref"):
        evaluate_irrops_report(_trip(), trigger_kind="cancellation", flight_ref="  ")


def test_terminal_stage_rejected():
    with pytest.raises(IrropsReportError, match="terminal"):
        evaluate_irrops_report(_trip(stage="completed"), trigger_kind="cancellation", flight_ref="F5")


def test_schedule_change_severity_uses_delay_input():
    assert evaluate_irrops_report(
        _trip(), trigger_kind="schedule_change", flight_ref="F6", delay_minutes=200,
    )["severity"] == "high"
    assert evaluate_irrops_report(
        _trip(), trigger_kind="schedule_change", flight_ref="F7", delay_minutes=30,
    )["severity"] == "medium"


def test_duplicate_window_marker_is_detectable():
    a1 = evaluate_irrops_report(
        _trip(), trigger_kind="delay", flight_ref="F8", delay_minutes=200,
        now_iso="2026-11-04T10:15:00+00:00",
    )
    a2 = evaluate_irrops_report(
        _trip(), trigger_kind="delay", flight_ref="F8", delay_minutes=210,
        now_iso="2026-11-04T10:45:00+00:00",
    )
    assert a1["idempotency_marker"] == a2["idempotency_marker"]
    a3 = evaluate_irrops_report(
        _trip(), trigger_kind="delay", flight_ref="F8", delay_minutes=210,
        now_iso="2026-11-04T11:05:00+00:00",
    )
    assert a3["idempotency_marker"] != a1["idempotency_marker"]


# ── Router endpoint ────────────────────────────────────────────────────


def test_report_endpoint_writes_active_disruption(session_client, monkeypatch):
    import spine_api.routers.disruption_radar as dr

    trip = {"id": "trip_r1", "stage": "booked", "active_disruption": None}
    stored = {}
    monkeypatch.setattr(
        dr.TripStore, "get_trip_for_agency",
        lambda tid, aid: trip if tid == "trip_r1" else None,
    )
    monkeypatch.setattr(
        dr.TripStore, "update_trip_for_agency",
        lambda tid, aid, fields: stored.update(fields) or trip,
    )

    res = session_client.post(
        "/api/v1/disruptions/trip_r1/report",
        json={"trigger_kind": "cancellation", "flight_ref": "AI-471", "notes": "carrier email"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True
    assert body["disruption"]["severity"] == "critical"
    assert stored["active_disruption"]["source"] == "operator_reported"
    # Radar integration (runtime-walk fix, 2026-11-06): the stored row must
    # carry the DisruptionAlert contract keys so /alerts renders it instead
    # of silently skipping it on construction.
    stored_row = stored["active_disruption"]
    for key in ("disruption_id", "trip_id", "flight_number", "disruption_type",
                "urgency_level", "delay_minutes", "impact_summary", "created_at"):
        assert key in stored_row, f"missing radar key {key}"
    assert stored_row["disruption_type"] == "CANCELLATION"
    assert stored_row["urgency_level"] == "CRITICAL"


def test_report_endpoint_422_on_unknown_kind(session_client, monkeypatch):
    import spine_api.routers.disruption_radar as dr

    monkeypatch.setattr(
        dr.TripStore, "get_trip_for_agency",
        lambda tid, aid: {"id": "trip_r1", "stage": "booked"},
    )
    res = session_client.post(
        "/api/v1/disruptions/trip_r1/report",
        json={"trigger_kind": "meteor_strike", "flight_ref": "X"},
    )
    assert res.status_code == 422


def test_resolve_archives_and_clears_active_disruption(session_client, monkeypatch):
    import spine_api.routers.disruption_radar as dr

    trip = {"id": "trip_r2", "stage": "booked", "active_disruption": None, "disruption_history": []}
    stored = {}
    monkeypatch.setattr(
        dr.TripStore, "get_trip_for_agency",
        lambda tid, aid: trip if tid == "trip_r2" else None,
    )
    monkeypatch.setattr(
        dr.TripStore, "update_trip_for_agency",
        lambda tid, aid, fields: (trip.update(fields), stored.update(fields), trip)[2],
    )

    res = session_client.post(
        "/api/v1/disruptions/trip_r2/report",
        json={"trigger_kind": "cancellation", "flight_ref": "AI-471"},
    )
    assert res.status_code == 200
    assert trip["active_disruption"] is not None

    res2 = session_client.post("/api/v1/disruptions/trip_r2/resolve")
    assert res2.status_code == 200, res2.text
    assert res2.json()["ok"] is True
    # archived with full provenance, active cleared
    hist = stored["disruption_history"]
    assert len(hist) == 1 and hist[0]["status"] == "RESOLVED"
    assert "idempotency_marker" in hist[0]
    assert stored["active_disruption"] is None


def test_resolve_409_when_no_active_disruption(session_client, monkeypatch):
    import spine_api.routers.disruption_radar as dr

    trip = {"id": "trip_r3", "stage": "booked", "active_disruption": None}
    monkeypatch.setattr(
        dr.TripStore, "get_trip_for_agency",
        lambda tid, aid: trip if tid == "trip_r3" else None,
    )
    res = session_client.post("/api/v1/disruptions/trip_r3/resolve")
    assert res.status_code == 409
    assert "no active disruption" in res.json()["detail"]
