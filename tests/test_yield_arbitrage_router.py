"""
tests/test_yield_arbitrage_router.py — Unit & Integration tests for Yield Arbitrage Engine.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"



@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_compute_yield_arbitrage_uncontracted(session_client):
    """Verify reality tier behavior when no supplier contracts are uploaded."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Luxury resort in Maui for 2 adults. Budget $10,000.",
            "customer_name": "Marcus Vance",
        },
        headers={"X-Agency-ID": "agency_yield_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.get(
        f"/api/v1/yield/arbitrage/{trip_id}",
        headers={"X-Agency-ID": "agency_yield_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert data["data_sufficient"] is False
    assert len(data["supplier_options"]) == 0
    assert data["potential_margin_gain"] == 0.0
    assert "None" in data["optimal_supplier"]


def test_compute_yield_arbitrage_with_uploaded_contract(session_client):
    """Verify yield calculation when real agency supplier contracts exist."""
    from spine_api.routers.supplier import CONTRACTS_STORE

    CONTRACTS_STORE["agency_contract_test"] = {
        "c_001": {
            "supplier_name": "Hyatt Preferred",
            "rate_table": [{"net_rate_per_night": 300.0, "rack_rate_per_night": 500.0}],
        }
    }

    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Resort in Hawaii for 2 adults.",
            "customer_name": "Sarah Connor",
        },
        headers={"X-Agency-ID": "agency_contract_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.get(
        f"/api/v1/yield/arbitrage/{trip_id}",
        headers={"X-Agency-ID": "agency_contract_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data_sufficient"] is True
    assert len(data["supplier_options"]) >= 1
    assert "Hyatt Preferred" in data["optimal_supplier"]
