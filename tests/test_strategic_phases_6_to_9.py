"""
tests/test_strategic_phases_6_to_9.py — Unit & Integration tests for Phases 6, 7, 8, and 9 product features.
"""

import os
import pytest
from spine_api.persistence import TripStore

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_strategic_phases_6_to_9_lifecycle_end_to_end(session_client):
    """End-to-end integration test for FX Sentinel, Disruption Radar, Corporate Policy, and Concierge Up-Sell."""

    # 1. Create a trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Executive business trip to Tokyo for 5 days. High-floor hotel.",
            "customer_name": "Alexander Wright",
        },
        headers={"X-Agency-ID": "agency_phase69_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # --- PHASE 6: FX Sentinel ---
    rates_res = session_client.get("/api/v1/fx/rates")
    assert rates_res.status_code == 200
    assert len(rates_res.json()) >= 5

    exposures_res = session_client.get(
        "/api/v1/fx/exposures",
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert exposures_res.status_code == 200
    assert len(exposures_res.json()) >= 1

    lock_fx_res = session_client.post(
        f"/api/v1/fx/lock-rate/{trip_id}",
        json={"trip_id": trip_id, "locked_rate": 155.0, "notes": "Hedged USD/JPY rate lock"},
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert lock_fx_res.status_code == 200
    lock_fx_data = lock_fx_res.json()
    assert lock_fx_data["ok"] is False
    assert lock_fx_data["status"] == "PREVIEW_ONLY"
    assert lock_fx_data["lock_applied"] is False
    assert lock_fx_data["locked_at"] is None
    assert lock_fx_data["provider_connected"] is False

    # --- PHASE 7: Disruption Radar ---
    # F-38: the radar surfaces only STORED disruption data (the per-trip
    # fabricated CRITICAL alert is gone), so seed one on the trip first.
    phase69_trip = TripStore.get_trip_for_agency(trip_id, "agency_phase69_test")
    phase69_trip["active_disruption"] = {
        "disruption_id": f"dis_{trip_id[:8]}",
        "trip_id": trip_id,
        "destination": "Tokyo",
        "flight_number": "JL711",
        "disruption_type": "DELAYED",
        "urgency_level": "WARNING",
        "delay_minutes": 90,
        "impact_summary": "Typhoon delay — stored preview data",
        "status": "ACTIVE",
        "created_at": "2026-09-05T00:00:00+00:00",
        "reality_tier": "deterministic_preview",
        "provider_connected": False,
        "effects": [],
    }
    TripStore.save_trip(phase69_trip, agency_id="agency_phase69_test")

    alerts_res = session_client.get(
        "/api/v1/disruptions/alerts",
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert alerts_res.status_code == 200
    assert len(alerts_res.json()) >= 1
    disruption_id = alerts_res.json()[0]["disruption_id"]

    rebook_opts_res = session_client.get(
        f"/api/v1/disruptions/{trip_id}/rebook-options",
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert rebook_opts_res.status_code == 200
    assert len(rebook_opts_res.json()) >= 2

    trip_before_rebook = TripStore.get_trip_for_agency(trip_id, "agency_phase69_test")
    rebook_exec_res = session_client.post(
        f"/api/v1/disruptions/{trip_id}/rebook",
        json={
            "trip_id": trip_id,
            "disruption_id": disruption_id,
            "chosen_option_id": "opt_alt_1",
            "advisor_note": "Rebooked onto BA182 business class",
        },
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert rebook_exec_res.status_code == 403
    assert "can_mutate_booking_state" in rebook_exec_res.json()["detail"]
    trip_after_rebook = TripStore.get_trip_for_agency(trip_id, "agency_phase69_test")
    assert trip_after_rebook == trip_before_rebook

    # --- PHASE 8: Corporate Policy Compliance ---
    policy_rules_res = session_client.get("/api/v1/corporate/policy-rules")
    assert policy_rules_res.status_code == 200
    assert policy_rules_res.json()["max_nightly_hotel_usd"] == 350.0

    audit_policy_res = session_client.post(
        f"/api/v1/corporate/audit-policy/{trip_id}",
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert audit_policy_res.status_code == 200
    assert audit_policy_res.json()["ok"] is True
    assert "duty_of_care_risk_level" in audit_policy_res.json()

    override_res = session_client.post(
        f"/api/v1/corporate/approve-policy-override/{trip_id}",
        json={"trip_id": trip_id, "approver_name": "Jane Miller VP", "reason": "Approved executive accommodation cap exception"},
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    # PA-26 adjustment (2026-09-06): a single call no longer approves outright.
    # With require_pre_approval active, the first call stages a dual-control
    # pending_second_approval record (this test previously failed after the
    # change because it asserted immediate override_approved=True from
    # client-supplied free text — the self-certifying behavior PA-26 removed).
    assert override_res.status_code == 200
    assert override_res.json()["override_approved"] is False
    assert override_res.json()["pending_second_approval"] is True
    assert override_res.json()["status"] == "pending_second_approval"

    # --- PHASE 9: Concierge Up-Sell Engine ---
    propose_res = session_client.get(
        f"/api/v1/concierge-upsell/{trip_id}/propose",
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert propose_res.status_code == 200
    assert len(propose_res.json()["recommended_upsells"]) >= 2

    dispatch_res = session_client.post(
        f"/api/v1/concierge-upsell/{trip_id}/dispatch",
        json={
            "trip_id": trip_id,
            "selected_item_ids": ["up_transfer_01", "up_dining_02"],
            "dispatch_channel": "email",
            "advisor_note": "Dispatched pre-departure VIP experience options",
        },
        headers={"X-Agency-ID": "agency_phase69_test"},
    )
    assert dispatch_res.status_code == 200
    assert dispatch_res.json()["dispatched_items_count"] == 2
