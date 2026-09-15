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

    # 4. Re-lock the lower net rate — PREVIEW-ONLY since PA-06 (2026-09-06).
    # FAILED BEFORE: re-lock persisted the simulated rate onto the trip and
    # bumped its version. PASSES AFTER: the endpoint is preview-only, so the
    # guards (expected_version + idempotency_key, now mandatory -> 422 when
    # absent) are supplied and the response carries effects:[] with
    # would_persist: false. The trip must remain byte-identical.
    from spine_api.persistence import TripStore

    trip_before = TripStore.get_trip_for_agency(trip_id, "agency_pricelock_test")

    relock_no_guards = session_client.post(
        f"/api/v1/price-lock/{trip_id}/re-lock",
        json={
            "trip_id": trip_id,
            "new_net_rate_cents": 200000,
            "supplier_name": "Belmond Hotel Caruso",
            "advisor_note": "Re-locked lower rate hold during 72-hour window",
        },
        headers={"X-Agency-ID": "agency_pricelock_test"},
    )
    # Guards are mandatory now (422) — no unguarded simulated write path.
    assert relock_no_guards.status_code == 422

    relock_res = session_client.post(
        f"/api/v1/price-lock/{trip_id}/re-lock",
        json={
            "trip_id": trip_id,
            "new_net_rate_cents": 200000,
            "supplier_name": "Belmond Hotel Caruso",
            "advisor_note": "Re-locked lower rate hold during 72-hour window",
            "expected_version": 1,
            "idempotency_key": "idem_pricelock_sentinel_1",
        },
        headers={"X-Agency-ID": "agency_pricelock_test"},
    )

    assert relock_res.status_code == 200
    relock_data = relock_res.json()
    assert relock_data["ok"] is True
    assert relock_data["margin_saved_cents"] == 100000
    assert relock_data["new_net_rate_cents"] == 200000
    assert relock_data["would_persist"] is False
    assert relock_data["not_persisted_reason"] == "simulated_rate_source"
    assert relock_data["effects"] == []
    assert relock_data["provider_connected"] is False

    trip_after = TripStore.get_trip_for_agency(trip_id, "agency_pricelock_test")
    assert trip_after == trip_before  # simulated rate never mutates real state


def test_fnd_0119_social_write_canonical_visible_to_sentinel(session_client):
    """FND-0119 (legacy F-32) regression: a social-channel write must land in
    the CANONICAL strategy location and be visible to the price-lock sentinel
    (previously the writer used the trip top-level key while the sentinel read
    strategy, and the 72h recompute fallback masked the divergence)."""
    from datetime import datetime

    from spine_api.persistence import TEST_AGENCY_ID, TripStore
    from spine_api.routers.price_lock import (
        _get_price_lock_expires_at,
        get_price_lock_expires_at_raw,
    )

    parse_res = session_client.post(
        "/api/v1/inbox/parse_social",
        json={
            "raw_text": "Santorini honeymoon for 2 in June, budget $9,000, boutique cave suite with caldera view.",
            "source": "instagram_dm",
            "creator_id": "creator_fnd_0119",
            "client_name": "Regression Probe",
        },
    )
    assert parse_res.status_code == 200, parse_res.text
    trip_id = parse_res.json()["trip_id"]

    try:
        trip = TripStore.get_trip_for_agency(trip_id, TEST_AGENCY_ID)
        assert trip is not None

        # 1. Writer persisted the CANONICAL location; the legacy top-level
        #    key must NOT be written for new rows (prevents split-brain).
        written = (trip.get("strategy") or {}).get("price_lock_expires_at")
        assert written, "social inbound must write strategy.price_lock_expires_at (canonical)"
        assert not trip.get("price_lock_expires_at"), "legacy top-level location must not be used for new rows"

        # 2. The shared canonical-then-legacy reader returns the persisted value.
        assert get_price_lock_expires_at_raw(trip) == written

        # 3. Sentinel sees the WRITTEN expiry exactly — the 72h-from-created_at
        #    fallback would recompute a different (later) timestamp and mask
        #    the divergence.
        assert _get_price_lock_expires_at(trip) == datetime.fromisoformat(written)

        # 4. The sentinel's public surface reports the persisted expiry too.
        opps_res = session_client.get("/api/v1/price-lock/opportunities")
        assert opps_res.status_code == 200
        matched = next((o for o in opps_res.json() if o["trip_id"] == trip_id), None)
        assert matched is not None
        assert datetime.fromisoformat(matched["price_lock_expires_at"]) == datetime.fromisoformat(written)

        # 5. Legacy rows (top-level only) remain visible via the read fallback.
        legacy_trip = {"id": "trip_legacy", "price_lock_expires_at": written}
        assert get_price_lock_expires_at_raw(legacy_trip) == written
        assert _get_price_lock_expires_at(legacy_trip) == datetime.fromisoformat(written)
    finally:
        try:
            TripStore.delete_trip_for_agency(trip_id, TEST_AGENCY_ID)
        except Exception:
            pass
