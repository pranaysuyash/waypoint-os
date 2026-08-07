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


def test_compute_yield_arbitrage(session_client):
    """Verify calculating supplier commission arbitrage and net margin optimization."""
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
    assert len(data["supplier_options"]) >= 3
    assert data["potential_margin_gain"] > 0
    assert "Direct Preferred Resort Contract" in data["optimal_supplier"]
