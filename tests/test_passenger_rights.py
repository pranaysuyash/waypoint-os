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


def test_passenger_rights_api_endpoint(session_client):
    """Verify POST /api/v1/passenger-rights/evaluate endpoint."""
    res = session_client.post(
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
