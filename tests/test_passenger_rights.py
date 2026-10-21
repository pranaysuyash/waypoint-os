"""
tests/test_passenger_rights.py — Unit and router integration tests for EU261 Passenger Rights Engine.
"""

import os
import pytest

from src.decision.passenger_rights import DisruptionType, Jurisdiction, PassengerRightsEngine

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_passenger_rights_short_haul_delay():
    """Verify €250 compensation for <= 1500km flight with 3+ hour delay."""
    claim = PassengerRightsEngine.evaluate_eu261(
        disruption_type=DisruptionType.DELAY,
        flight_distance_km=950.0,
        delay_arrival_hours=3.5,
    )
    assert claim.is_eligible_for_compensation is True
    assert claim.compensation_amount == 250.0
    assert claim.compensation_currency == "EUR"
    assert claim.jurisdiction == Jurisdiction.EU_261
    assert claim.right_to_care_required is True


def test_passenger_rights_long_haul_delay():
    """Verify €600 compensation for > 3500km flight with 4+ hour delay."""
    claim = PassengerRightsEngine.evaluate_eu261(
        disruption_type=DisruptionType.DELAY,
        flight_distance_km=5800.0,
        delay_arrival_hours=4.5,
    )
    assert claim.is_eligible_for_compensation is True
    assert claim.compensation_amount == 600.0


def test_passenger_rights_extraordinary_circumstances():
    """Verify extraordinary circumstances waive monetary compensation but preserve duty of care."""
    claim = PassengerRightsEngine.evaluate_eu261(
        disruption_type=DisruptionType.DELAY,
        flight_distance_km=2200.0,
        delay_arrival_hours=6.0,
        is_extraordinary_circumstances=True,
    )
    assert claim.is_eligible_for_compensation is False
    assert claim.compensation_amount == 0.0
    assert claim.right_to_care_required is True
    assert claim.is_eligible_for_full_refund is True


def test_passenger_rights_api_endpoint(api_client):
    """Verify POST /api/v1/passenger-rights/evaluate endpoint.

    Blast-radius fix (2026-09-30, same pass as the T10 tranche): this test
    previously consumed the DB-provisioning ``session_client`` fixture, which
    made an evaluate-contract assertion depend on a reachable Postgres —
    ``/evaluate`` needs no database. Now uses the file's hermetic client
    (auth disabled via the autouse env fixture, file tripstore). Assertions
    unchanged; the DB is no longer load-bearing for the evaluate contract.
    """
    res = api_client.post(
        "/api/v1/passenger-rights/evaluate",
        json={
            "flight_number": "AF1234",
            "disruption_type": "DELAYED",
            "delay_hours": 3.2,
            "distance_km": 1200.0,
        },
        headers={"X-Agency-ID": "agency_rights_test"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["is_eligible"] is True
    assert data["compensation_per_passenger_eur"] == 250.0
    assert data["regulatory_framework"] == "EU261"


# ---------------------------------------------------------------------------
# T10 disposition ledger — endpoint integration (FND-0233, decided 2026-09-30)
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client():
    # Context-managed so the app lifespan (DB pool) shuts down — an unmanaged
    # TestClient hangs the pytest process at exit (observed 2026-09-30).
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from spine_api.core.auth import get_current_agency
    from spine_api.server import app

    # /trips/{trip_id} resolves the full Agency from Postgres; the disposition
    # tranche tests only exercise the claim ledger, so override the dependency
    # with the repo's canonical pattern (team_router_behavior.py:29).
    app.dependency_overrides[get_current_agency] = lambda: SimpleNamespace(
        id="t10-test-agency"
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_agency, None)


@pytest.fixture()
def trip_with_claim(api_client, tmp_path, monkeypatch):
    """A real trip with a generated claim, via the actual generate endpoint."""
    from spine_api.persistence import TripStore

    agency_id = "t10-test-agency"
    trip = {
        "id": "t10trip001",
        "agency_id": agency_id,
        "status": "active",
        "destination": "Munich",
    }
    TripStore.save_trip(trip, agency_id=agency_id)

    resp = api_client.post(
        "/api/v1/passenger-rights/t10trip001/generate-claim",
        json={
            "trip_id": "t10trip001",
            "passenger_names": ["Ada Test"],
            "booking_reference": "BK-T10",
        },
        headers={"X-Agency-Id": agency_id},
    )
    assert resp.status_code == 200, resp.text
    claim_id = resp.json()["claim_id"]
    return agency_id, "t10trip001", claim_id


def test_generate_claim_auto_creates_disposition(api_client, trip_with_claim):
    agency_id, trip_id, claim_id = trip_with_claim
    resp = api_client.get(
        f"/api/v1/passenger-rights/{trip_id}/claims/{claim_id}/disposition",
        headers={"X-Agency-Id": agency_id},
    )
    assert resp.status_code == 200
    body = resp.json()["disposition"]
    assert body["state"] == "SUBMITTED"  # letter generated ⇒ submitted
    assert body["overdue"] is False
    assert [h["state"] for h in body["history"]] == ["SUBMITTED"]


def test_disposition_happy_path_transitions(api_client, trip_with_claim):
    agency_id, trip_id, claim_id = trip_with_claim
    url = f"/api/v1/passenger-rights/{trip_id}/claims/{claim_id}/disposition"
    headers = {"X-Agency-Id": agency_id}

    for state, outcome in (
        ("AIRLINE_ACCEPTED", None),
        ("TRAVELER_PAID", {"amount_eur": 400.0, "channel": "bank_transfer"}),
        ("CLOSED", None),
    ):
        resp = api_client.patch(
            url,
            json={"new_state": state, "note": "operator recorded reality", "outcome": outcome},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
    assert resp.json()["disposition"]["state"] == "CLOSED"
    # Outcome recorded verbatim; system moved nothing.
    assert resp.json()["disposition"]["outcome"]["amount_eur"] == 400.0

    # Terminal is frozen → 409
    frozen = api_client.patch(url, json={"new_state": "SUBMITTED"}, headers=headers)
    assert frozen.status_code == 409


def test_disposition_illegal_transition_rejected_409(api_client, trip_with_claim):
    agency_id, trip_id, claim_id = trip_with_claim
    resp = api_client.patch(
        f"/api/v1/passenger-rights/{trip_id}/claims/{claim_id}/disposition",
        json={"new_state": "TRAVELER_PAID"},  # skipping airline reply
        headers={"X-Agency-Id": agency_id},
    )
    assert resp.status_code == 409
    assert "illegal transition" in resp.json()["detail"].lower()


def test_disposition_unknown_claim_404(api_client, trip_with_claim):
    agency_id, trip_id, _ = trip_with_claim
    resp = api_client.get(
        f"/api/v1/passenger-rights/{trip_id}/claims/nope/disposition",
        headers={"X-Agency-Id": agency_id},
    )
    assert resp.status_code == 404


def test_trip_response_carries_disposition(api_client, trip_with_claim):
    """The silent-strip guard: the claim ledger must reach the operator UI via
    GET /trips — same failure class as the branch_options serving gap."""
    agency_id, trip_id, claim_id = trip_with_claim
    resp = api_client.get(f"/trips/{trip_id}", headers={"X-Agency-Id": agency_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("passenger_claim"), "TripResponse dropped passenger_claim"
    assert body["passenger_claim"]["disposition"]["state"] == "SUBMITTED"
