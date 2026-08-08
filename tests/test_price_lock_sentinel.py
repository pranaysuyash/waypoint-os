"""
tests/test_price_lock_sentinel.py — Unit & Integration tests for Autonomous Price-Lock Sentinel Engine.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_price_lock_sentinel_lifecycle_end_to_end(session_client):
    """Test price lock opportunity listing, rate feed auditing, and re-locking lower rates."""
    from spine_api.routers.supplier import CONTRACTS_STORE

    # 1. Create a trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Honeymoon to Amalfi Coast for 2 adults. Budget $10,000.",
            "customer_name": "Liam Hemsworth",
        },
        headers={"X-Agency-ID": "agency_pricelock_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # 2. List price lock opportunities
    opps_res = session_client.get(
        "/api/v1/price-lock/opportunities",
        headers={"X-Agency-ID": "agency_pricelock_test"},
    )

    assert opps_res.status_code == 200
    opps_data = opps_res.json()
    assert len(opps_data) >= 1
    matched_opp = next((o for o in opps_data if o["trip_id"] == trip_id), None)
    assert matched_opp is not None
    assert matched_opp["hours_remaining"] > 0
    assert matched_opp["is_expired"] is False

    # 3. Populate a lower rate supplier contract and audit rate
    CONTRACTS_STORE["agency_pricelock_test"] = {
        "c_pricelock": {
            "supplier_name": "Belmond Hotel Caruso",
            "rate_table": [{"net_rate_per_night": 400.0, "rack_rate_per_night": 700.0}],  # 5 nights = $2,000 net vs $3,000 original
        }
    }

    audit_res = session_client.post(
        f"/api/v1/price-lock/{trip_id}/audit-rate",
        headers={"X-Agency-ID": "agency_pricelock_test"},
    )

    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["ok"] is True
    assert audit_data["supplier_name"] == "Belmond Hotel Caruso"
    assert audit_data["rate_drop_detected"] is True
    assert audit_data["potential_margin_gain_cents"] == 100000  # $1,000 savings

    # 4. Re-lock the lower net rate
    relock_res = session_client.post(
        f"/api/v1/price-lock/{trip_id}/re-lock",
        json={
            "trip_id": trip_id,
            "new_net_rate_cents": 200000,
            "supplier_name": "Belmond Hotel Caruso",
            "advisor_note": "Re-locked lower rate hold during 72-hour window",
        },
        headers={"X-Agency-ID": "agency_pricelock_test"},
    )

    assert relock_res.status_code == 200
    relock_data = relock_res.json()
    assert relock_data["ok"] is True
    assert relock_data["margin_saved_cents"] == 100000
    assert relock_data["new_net_rate_cents"] == 200000
