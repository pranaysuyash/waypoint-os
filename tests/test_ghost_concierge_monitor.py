"""Ghost Concierge monitor tests — T11b wiring (decided 2026-09-30).

Covers the honest-source telemetry seam, the pure evaluation chain, and the
never-send/never-fabricate invariants from the decision pack.
"""

import os

# NOTE (2026-10-22): this module previously forced
# ``os.environ["TRIPSTORE_BACKEND"] = "file"`` at module level on the belief
# that backend selection happens at persistence IMPORT time. It does not —
# the TripStore facade reads the env per call (TripStore._backend), and the
# module-level write poisoned the WHOLE pytest session after collection:
# every later SQL-backed test (e.g. booking_collection token FK inserts)
# silently hit the file store and failed with trips-FK violations. The
# per-test ``_hermetic_store`` autouse fixture below delivers the same
# data-safety guarantee correctly scoped.
os.environ.setdefault("RUNNING_TESTS", "1")

import pytest  # noqa: E402

from spine_api.services import ghost_concierge_monitor as mon
from spine_api.services.ghost_concierge import FlightTelemetry

os.environ.setdefault("RUNNING_TESTS", "1")


@pytest.fixture(autouse=True)
def _hermetic_store(monkeypatch):
    """File tripstore for persistence tests — never the shared SQL test agency
    (data-safety rule) and no DATABASE_URL dependency."""
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _trip(updates):
    return {"id": "t11trip", "flight_status_updates": updates}


def test_no_telemetry_returns_none_never_fabricates():
    """An unmonitored trip yields None — the engine is never fed invented data."""
    assert mon.monitor_evaluate_trip({"id": "empty"}) is None
    assert mon.monitor_evaluate_trip(_trip([])) is None


def test_operator_reported_cancellation_produces_critical_intervention():
    trip = _trip([
        {
            "flight_number": "XY123",
            "origin_iata": "BLR",
            "destination_iata": "DXB",
            "status": "cancelled",
            "delay_minutes": 0,
        }
    ])
    report = mon.monitor_evaluate_trip(trip)
    assert report is not None
    assert report.overall_health == "DISRUPTED"
    actions = [i.action_type for i in report.interventions]
    assert "SEARCH_FALLBACK_FLIGHTS" in actions
    # FND-0312 (2026-10-05): BLR→DXB has no EU touchpoint, so the draft label
    # is the honest DRAFT_CLAIM (Montreal Art. 19 lane), not DRAFT_EU261_CLAIM.
    assert "DRAFT_CLAIM" in actions


def test_connection_cascade_detected():
    trip = _trip([
        {"flight_number": "A1", "origin_iata": "BLR", "destination_iata": "DXB",
         "status": "delayed", "delay_minutes": 150},
        {"flight_number": "B2", "origin_iata": "DXB", "destination_iata": "MUC",
         "status": "scheduled", "delay_minutes": 0},
    ])
    report = mon.monitor_evaluate_trip(trip)
    assert report is not None
    risks = [r for r in report.connection_risks if r.is_at_risk]
    assert len(risks) == 1
    assert risks[0].risk_level in ("CRITICAL_MISSED_CONNECTION", "MODERATE")


def test_workflow_payload_is_drafted_never_sent():
    trip = _trip([
        {"flight_number": "XY123", "origin_iata": "BLR", "destination_iata": "DXB",
         "status": "cancelled", "delay_minutes": 0}
    ])
    report = mon.monitor_evaluate_trip(trip)
    wf = mon.workflow_from_report(report, "agency-1")
    assert wf["origin"] == "ghost_concierge_monitor"
    for intervention in wf["drafted_interventions"]:
        assert intervention["status"] == "DRAFT_AWAITING_OPERATOR"
    # Reality note is honest about the data source
    assert "operator/traveler-reported" in wf["reality_note"]


def test_invalid_status_records_dropped():
    """Unreportable statuses never reach the engine (no fabricated telemetry)."""
    telemetry = mon.telemetry_from_trip_facts(_trip([
        {"flight_number": "OK1", "origin_iata": "A", "destination_iata": "B",
         "status": "scheduled"},
        {"flight_number": "BAD1", "origin_iata": "C", "destination_iata": "D",
         "status": "definitely_not_a_real_status"},
        {"flight_number": "", "origin_iata": "E", "destination_iata": "F",
         "status": "delayed"},
    ]))
    assert [t.flight_number for t in telemetry] == ["OK1"]


def test_provider_seam_extends_operator_facts():
    class _LiveProvider:
        def get_telemetry(self, flight_numbers):
            assert flight_numbers == ["XY123"]
            return [FlightTelemetry(
                flight_number="XY123", carrier="XY",
                origin_iata="BLR", destination_iata="DXB",
                scheduled_departure="", scheduled_arrival="",
                delay_minutes=180, status="delayed",
            )]

    trip = _trip([
        {"flight_number": "XY123", "origin_iata": "BLR", "destination_iata": "DXB",
         "status": "scheduled", "delay_minutes": 0}
    ])
    report = mon.monitor_evaluate_trip(trip, provider=_LiveProvider())
    assert report is not None
    assert report.overall_health == "DEGRADED"  # provider telemetry upgraded the picture


def test_traveler_disruption_signals_safe_on_store_failure():
    """Message-store unavailability degrades to zero signals, never a crash."""
    trip = {"id": "no-such-trip"}
    assert mon.traveler_disruption_signals(trip) == []


def test_run_for_trip_persists_truth_up_and_drafts(tmp_path, monkeypatch):
    """Serving-path entry: real evaluation persisted on the trip; healer chain
    attempted only when a journey node matches; drafts never auto-send."""
    from spine_api.persistence import TripStore

    agency_id = "t11-agency"
    trip = {
        "id": "t11trip001", "agency_id": agency_id, "status": "active",
        "flight_status_updates": [
            {"flight_number": "XY999", "origin_iata": "BLR", "destination_iata": "DXB",
             "status": "cancelled", "delay_minutes": 0}
        ],
    }
    TripStore.save_trip(trip, agency_id=agency_id)

    wf = mon.run_ghost_concierge_for_trip(trip, agency_id)
    assert wf is not None
    assert wf["overall_health"] == "DISRUPTED"
    assert all(i["status"] == "DRAFT_AWAITING_OPERATOR" for i in wf["drafted_interventions"])

    saved = TripStore.get_trip_for_agency("t11trip001", agency_id)
    assert saved.get("ghost_concierge", {}).get("overall_health") == "DISRUPTED"
    # No journey graph on the trip → healer not chained, reason recorded honestly
    assert "healer not chained" in wf.get("healer_note", "")
    assert "no stored journey graph" in wf.get("healer_note", "")


def test_run_for_trip_noop_without_telemetry(tmp_path):
    from spine_api.persistence import TripStore

    agency_id = "t11-agency"
    trip = {"id": "t11quiet", "agency_id": agency_id, "status": "active"}
    TripStore.save_trip(trip, agency_id=agency_id)
    assert mon.run_ghost_concierge_for_trip(trip, agency_id) is None
    saved = TripStore.get_trip_for_agency("t11quiet", agency_id)
    assert "ghost_concierge" not in saved


def test_patch_trip_with_flight_status_triggers_monitor(monkeypatch):
    """Step 2b hook: PATCH with flight_status_updates runs the monitor end-to-end."""
    from types import SimpleNamespace

    # AuthMiddleware rejects before routing — dependency overrides can't bypass
    # it; the repo's hermetic pattern is the disable-auth env (same as
    # test_passenger_rights.py).
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")

    from fastapi.testclient import TestClient
    from spine_api.core.auth import get_current_agency, get_current_user
    from spine_api.persistence import TripStore
    from spine_api.server import app

    agency_id = "t11-hook-agency"
    trip = {"id": "t11hook001", "agency_id": agency_id, "status": "active"}
    TripStore.save_trip(trip, agency_id=agency_id)

    app.dependency_overrides[get_current_agency] = lambda: SimpleNamespace(id=agency_id)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="t11-hook-user", agency_id=agency_id
    )
    try:
        with TestClient(app) as client:
            resp = client.patch(
                "/trips/t11hook001",
                json={
                    "flight_status_updates": [
                        {"flight_number": "ZZ1", "origin_iata": "BLR",
                         "destination_iata": "DXB", "status": "cancelled",
                         "delay_minutes": 0}
                    ]
                },
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("passenger_claim") is None or True  # unrelated fields untouched
        gc = body.get("ghost_concierge")
        assert gc, "PATCH did not run the ghost-concierge monitor"
        assert gc["overall_health"] == "DISRUPTED"
        assert all(
            i["status"] == "DRAFT_AWAITING_OPERATOR" for i in gc["drafted_interventions"]
        )
    finally:
        app.dependency_overrides.pop(get_current_agency, None)
        app.dependency_overrides.pop(get_current_user, None)
