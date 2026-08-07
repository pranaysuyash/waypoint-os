"""
Test Suite for DMC & Preferred Supplier Wholesale Contract Ingestion & Inventory Soft-Hold Engine
"""

import pytest


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")


def test_upload_supplier_contract_success(session_client):
    """Verify uploading a wholesale DMC rate sheet."""
    payload = {
        "supplier_name": "Marrakech Destination Management Co.",
        "destination": "Marrakech, Morocco",
        "contact_email": "contracts@marrakechdmc.ma",
        "currency": "USD",
        "rate_table": [
            {
                "room_type": "Junior Luxury Suite",
                "net_rate_per_night": 350.0,
                "rack_rate_per_night": 550.0,
                "season_start": "2026-09-01",
                "season_end": "2026-12-15",
                "cancellation_lead_days": 7,
            },
            {
                "room_type": "Royal Medina Villa",
                "net_rate_per_night": 850.0,
                "rack_rate_per_night": 1400.0,
                "season_start": "2026-09-01",
                "season_end": "2026-12-15",
                "cancellation_lead_days": 14,
            },
        ],
        "terms_and_conditions": "100% refundable up to 7 days prior.",
    }

    res = session_client.post("/api/v1/supplier/contracts/upload", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["contract_id"].startswith("contract_")
    assert data["supplier_name"] == "Marrakech Destination Management Co."
    assert data["total_rates_ingested"] == 2
    assert data["status"] == "ACTIVE"


def test_create_inventory_soft_hold_success(session_client):
    """Verify reserving a 48h zero-cost soft hold on DMC wholesale inventory."""
    # 1. Upload contract first
    upload_payload = {
        "supplier_name": "Atlas Luxury DMC",
        "destination": "Marrakech, Morocco",
        "rate_table": [
            {
                "room_type": "Atlas View Suite",
                "net_rate_per_night": 400.0,
                "rack_rate_per_night": 650.0,
            }
        ],
    }
    upload_res = session_client.post("/api/v1/supplier/contracts/upload", json=upload_payload)
    assert upload_res.status_code == 200
    contract_id = upload_res.json()["contract_id"]

    # 2. Place 48h soft hold
    hold_payload = {
        "contract_id": contract_id,
        "room_type": "Atlas View Suite",
        "check_in": "2026-10-10",
        "check_out": "2026-10-15",
        "guest_name": "Sarah Jenkins",
        "agent_id": "agent_test",
    }

    hold_res = session_client.post("/api/v1/supplier/inventory/soft-hold", json=hold_payload)
    assert hold_res.status_code == 200
    hold_data = hold_res.json()

    assert hold_data["hold_id"].startswith("hold_")
    assert hold_data["supplier_name"] == "Atlas Luxury DMC"
    assert hold_data["net_rate_total"] == 2000.0  # 400 * 5 nights
    assert hold_data["rack_rate_total"] == 3250.0 # 650 * 5 nights
    assert hold_data["estimated_agency_margin"] == 1250.0  # 3250 - 2000
    assert hold_data["status"] == "SOFT_HOLD_ACTIVE"
    assert "expires_at" in hold_data
