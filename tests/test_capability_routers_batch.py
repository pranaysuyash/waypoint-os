"""
tests/test_capability_routers_batch.py — Unit & Integration tests for Visa Radar, Sub-Agent Payouts, Insurance, Loyalty, and Feedback routers.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


@pytest.fixture(autouse=True)
def materialize_attach_tenant(boundary_principal_factory):
    """F-31 (FND-0118): the insurance attach path now writes the canonical SQL
    BookingConfirmation whose agency_id is an FK to agencies.id, so the batch
    test tenant must exist in SQL. Additive only (ON CONFLICT DO NOTHING)."""
    boundary_principal_factory("usr_batch_test_attach", "agency_batch_test")


def test_capability_routers_batch_end_to_end(session_client):
    """End-to-end integration test covering all 5 new capability routers."""

    # 1. Create a trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Honeymoon luxury tour in Paris and Rome for 10 days.",
            "customer_name": "Eleanor Vance",
        },
        headers={"X-Agency-ID": "agency_batch_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # --- 1. VISA RADAR ROUTER ---
    check_visa_res = session_client.post(
        "/api/v1/visa-radar/check",
        json={
            "passport_country": "US",
            "destination_country": "FR",
            "passport_expiry_date": "2027-06-01T00:00:00Z",
            "travel_date": "2026-10-01T00:00:00Z",
        },
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert check_visa_res.status_code == 200
    assert check_visa_res.json()["passport_validity_compliant"] is True

    reqs_res = session_client.get(
        f"/api/v1/visa-radar/{trip_id}/requirements?passport_country=US",
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert reqs_res.status_code == 200
    assert reqs_res.json()["destination"] != ""

    # --- 2. SUB-AGENT PAYOUTS ROUTER ---
    ledger_res = session_client.get(
        "/api/v1/subagent-payouts/adv_batch_01/ledger",
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert ledger_res.status_code == 200
    assert ledger_res.json()["split_tier_pct"] == 80.0

    # FND-0221: payouts require a payout-scope payment mandate — grant one
    # for the batch test agency and reference it in the payout call.
    from spine_api.services.payment_mandate_service import PaymentMandateLedger

    payout_mandate = PaymentMandateLedger.register_mandate(
        agency_id="agency_batch_test",
        trip_id=trip_id,
        customer_id="adv_batch_01",
        max_authorized_cents=100_000,
        purpose="",
        scope="payout",
        consent_text="Authorize advisor commission payouts for capability batch testing.",
        consent_artifact_ref="approval_event_batch_test",
        payer_ref="user:operator@batch.test",
    )
    payout_res = session_client.post(
        "/api/v1/subagent-payouts/adv_batch_01/request-payout",
        json={
            "amount_cents": 25000,
            "payout_method": "DIRECT_DEPOSIT",
            "mandate_id": payout_mandate.mandate_id,
        },
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert payout_res.status_code == 200
    assert payout_res.json()["cleared_payout_cents"] > 150000

    # --- 3. TRAVEL INSURANCE ROUTER ---
    quote_res = session_client.post(
        "/api/v1/insurance/quote",
        json={
            "trip_id": trip_id,
            "total_trip_cost_usd": 12000.0,
            "destination_country": "FR",
        },
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert quote_res.status_code == 200
    quote_data = quote_res.json()
    assert len(quote_data["plans"]) == 3
    assert quote_data["days_remaining_for_cfar"] is None
    assert quote_data["cfar_timing_status"] == "not_evaluated"
    assert quote_data["cfar_evidence"]["policy_rule_status"] == "not_adopted"

    attach_ins_res = session_client.post(
        f"/api/v1/insurance/{trip_id}/attach-policy",
        json={
            "trip_id": trip_id,
            "selected_plan_id": "ins_cfar_03",
            "policy_number": "POL-CFAR-992144",
            "insurance_provider": "Allianz Global Assistance",
            "premium_paid_usd": 1380.0,
        },
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert attach_ins_res.status_code == 200
    assert attach_ins_res.json()["policy_number"] == "POL-CFAR-992144"

    # --- 4. LOYALTY & AWARDS ROUTER ---
    award_res = session_client.post(
        "/api/v1/loyalty/award-search",
        json={
            "origin": "JFK",
            "destination": "NRT",
            "departure_date": "2026-11-01",
            "cabin_class": "BUSINESS",
        },
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert award_res.status_code == 200
    assert len(award_res.json()["award_options"]) >= 2

    balances_res = session_client.get(
        "/api/v1/loyalty/cust_9921/balances",
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert balances_res.status_code == 200
    assert balances_res.json()["programs"] == []
    assert balances_res.json()["reality_tier"] == "unavailable"
    assert balances_res.json()["provider_connected"] is False

    # --- 5. FEEDBACK & NPS ROUTER ---
    survey_res = session_client.post(
        f"/api/v1/feedback/{trip_id}/trigger-survey",
        json={"trip_id": trip_id, "delivery_channel": "email"},
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert survey_res.status_code == 200
    assert "https://feedback.waypointos.com" in survey_res.json()["survey_url"]

    # Record a real response first (E-10): the scorecard aggregates only from
    # stored responses — the old "average_agency_nps >= 80" expectation relied
    # on the fabricated demo rows that no longer exist.
    response_res = session_client.post(
        f"/api/v1/feedback/{trip_id}/response",
        json={
            "nps_score": 9,
            "supplier_ratings": [{"supplier_name": "Emirates", "category": "AIRLINE", "score": 5}],
        },
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert response_res.status_code == 200
    assert response_res.json()["memory_writes_persisted"] >= 1

    scorecard_res = session_client.get(
        "/api/v1/feedback/supplier-scorecard",
        headers={"X-Agency-ID": "agency_batch_test"},
    )
    assert scorecard_res.status_code == 200
    assert scorecard_res.json()["data_source"] == "computed_from_responses"
    assert scorecard_res.json()["total_feedback_submissions"] >= 1
    assert scorecard_res.json()["average_agency_nps"] == 9
