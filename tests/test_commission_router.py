"""
tests/test_commission_router.py — Unit & Integration tests for Supplier Commission Reconciliation Engine.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_commission_reconciliation_lifecycle_end_to_end(session_client):
    """Test recording expected commission, reconciling exact/underpaid payouts, and viewing agency summary."""

    # 1. Create a trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Family vacation to Maui. Budget $10,000.",
            "customer_name": "James Henderson",
        },
        headers={"X-Agency-ID": "agency_comm_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # 2. Record expected commission (12% commission, 80% advisor split)
    rec_res = session_client.post(
        "/api/v1/commission/record",
        json={
            "trip_id": trip_id,
            "supplier_name": "Four Seasons Maui",
            "gross_booking_amount_cents": 1000000,  # $10,000
            "expected_commission_pct": 12.0,        # 12% = $1,200
            "advisor_split_pct": 80.0,              # 80% to IC advisor = $960, 20% agency = $240
        },
        headers={"X-Agency-ID": "agency_comm_test"},
    )

    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["expected_commission_cents"] == 120000
    assert rec_data["expected_advisor_payout_cents"] == 96000
    assert rec_data["expected_agency_net_cents"] == 24000
    assert rec_data["status"] == "PENDING"

    # 3. Reconcile exact payout ($1,200)
    reconcile_res = session_client.post(
        "/api/v1/commission/reconcile",
        json={
            "trip_id": trip_id,
            "actual_payout_cents": 120000,
            "supplier_reference": "REM-FS-99201",
            "notes": "Full commission received via ACH",
        },
        headers={"X-Agency-ID": "agency_comm_test"},
    )

    assert reconcile_res.status_code == 200
    recon_data = reconcile_res.json()
    assert recon_data["status"] == "RECONCILED"
    assert recon_data["variance_cents"] == 0
    assert recon_data["actual_advisor_payout_cents"] == 96000

    # 4. Create second trip and test underpaid variance
    inbound_res_2 = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Cruise to Alaska for 2 adults.",
            "customer_name": "Sarah Connor",
        },
        headers={"X-Agency-ID": "agency_comm_test"},
    ).json()

    trip_id_2 = inbound_res_2["trip_id"]

    session_client.post(
        "/api/v1/commission/record",
        json={
            "trip_id": trip_id_2,
            "supplier_name": "Royal Caribbean",
            "gross_booking_amount_cents": 500000,  # $5,000
            "expected_commission_pct": 10.0,       # 10% = $500
            "advisor_split_pct": 70.0,             # 70% = $350
        },
        headers={"X-Agency-ID": "agency_comm_test"},
    )

    underpaid_res = session_client.post(
        "/api/v1/commission/reconcile",
        json={
            "trip_id": trip_id_2,
            "actual_payout_cents": 35000,          # $350 paid instead of $500 ($150 underpaid)
            "supplier_reference": "REM-RC-10293",
            "notes": "Supplier deducted unannounced admin fee",
        },
        headers={"X-Agency-ID": "agency_comm_test"},
    )

    assert underpaid_res.status_code == 200
    underpaid_data = underpaid_res.json()
    assert underpaid_data["status"] == "UNDERPAID"
    assert underpaid_data["variance_cents"] == -15000

    # 5. Get commission summary
    summary_res = session_client.get(
        "/api/v1/commission/summary",
        headers={"X-Agency-ID": "agency_comm_test"},
    )

    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["reconciled_count"] >= 1
    assert summary_data["underpaid_count"] >= 1
    assert summary_data["total_collected_cents"] >= 155000
