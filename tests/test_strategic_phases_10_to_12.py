"""
tests/test_strategic_phases_10_to_12.py — Unit & Integration tests for Phases 10, 11, and 12 product features.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_strategic_phases_10_to_12_lifecycle_end_to_end(session_client):
    """End-to-end integration test for Passenger Rights, Visa Radar, and IC Advisor Payout Ledgers."""
    from spine_api.services.visa_radar import VisaCheckRequest, audit_visa_and_passport_validity
    from spine_api.services.commission_reconciliation import get_or_create_advisor_ledger, process_advisor_payout_authorization

    # 1. Create a trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Flight BA178 delayed by 4.5 hours from London to New York.",
            "customer_name": "Arthur Pendelton",
        },
        headers={"X-Agency-ID": "agency_phase1012_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # --- PHASE 10: Passenger Rights Claim Engine ---
    eval_res = session_client.post(
        "/api/v1/passenger-rights/evaluate",
        json={
            "trip_id": trip_id,
            "flight_number": "BA178",
            "disruption_type": "DELAYED",
            "delay_hours": 4.5,
            "distance_km": 5500.0,
            "passengers_count": 2,
        },
        headers={"X-Agency-ID": "agency_phase1012_test"},
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["is_eligible"] is True
    assert eval_data["regulatory_framework"] == "EU261"
    assert eval_data["compensation_per_passenger_eur"] == 600.0
    assert eval_data["total_statutory_compensation_eur"] == 1200.0

    gen_claim_res = session_client.post(
        f"/api/v1/passenger-rights/{trip_id}/generate-claim",
        json={
            "trip_id": trip_id,
            "passenger_names": ["Arthur Pendelton", "Guinevere Pendelton"],
            "booking_reference": "PNR-BA-88219",
            "advisor_notes": "Statutory claim filed under EU261 for 4.5h transatlantic delay",
        },
        headers={"X-Agency-ID": "agency_phase1012_test"},
    )
    assert gen_claim_res.status_code == 200
    gen_data = gen_claim_res.json()
    assert gen_data["ok"] is True
    assert "EU261" in gen_data["claim_letter_text"]

    # --- PHASE 11: Real-Time Visa & Passport Validity Radar ---
    visa_req = VisaCheckRequest(
        passport_country="US",
        destination_country="GB",
        passport_expiry_date="2026-10-15T00:00:00Z",
        travel_date="2026-09-01T00:00:00Z",  # Only 1.5 months validity remaining
    )
    visa_result = audit_visa_and_passport_validity(visa_req)
    assert visa_result.passport_validity_compliant is False
    assert visa_result.requires_visa is True
    assert visa_result.visa_type_required == "ETA"
    assert len(visa_result.warnings) >= 2

    # --- PHASE 12: IC Advisor Commission Ledger & Payout Portal ---
    ledger = get_or_create_advisor_ledger(advisor_id="adv_1029", advisor_name="Charlotte Bronte")
    assert ledger.advisor_id == "adv_1029"
    assert ledger.split_tier_pct == 80.0
    assert ledger.pending_payout_cents == 50000

    updated_ledger = process_advisor_payout_authorization(advisor_id="adv_1029", amount_cents=50000, method="ACH_DIRECT")
    assert updated_ledger.pending_payout_cents == 0
    assert updated_ledger.cleared_payout_cents == 200000
    assert len(updated_ledger.payout_history) == 2
