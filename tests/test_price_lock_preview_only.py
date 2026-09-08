"""
tests/test_price_lock_preview_only.py — PA-06 S2 evidence (2026-09-06).

Proves the price-lock re-lock endpoint is PREVIEW-ONLY:

1. FAILED BEFORE: POST /re-lock persisted the simulated rate onto the real
   trip (strategy.recommended_option.cost overwritten, version bumped, audit
   event ``price_lock_arbitrage_saved`` written) even though the "current
   rate" was fabricated from the first in-memory contract row with hardcoded
   fallbacks.
2. PASSES AFTER: a re-lock call leaves the trip record byte-identical
   (deep-equal snapshot read from the store before and after), returns
   ``effects: []`` / ``would_persist: false`` with reason
   ``simulated_rate_source``, and rejects requests missing the now-mandatory
   optimistic-version guard or idempotency key with 422.

Data safety: unique per-run trip ids, deleted on teardown; the canonical test
agency's seeded trips are never touched.
"""

from __future__ import annotations

import copy
import uuid

import pytest

from spine_api.persistence import TEST_AGENCY_ID, TripStore
from spine_api.routers.supplier import CONTRACTS_STORE

_RELOCK_BODY = {
    "new_net_rate_cents": 200000,
    "supplier_name": "Preview Supplier",
}


@pytest.fixture(autouse=True)
def _seed_contract_store():
    """Simulated rate source: one in-memory contract row (this is exactly the
    fabrication PA-06 flagged — which is why the endpoint must not persist)."""
    CONTRACTS_STORE[TEST_AGENCY_ID] = {
        "c_preview": {
            "supplier_name": "Preview Supplier",
            "rate_table": [{"net_rate_per_night": 400.0, "rack_rate_per_night": 700.0}],
        }
    }
    yield
    CONTRACTS_STORE.pop(TEST_AGENCY_ID, None)


@pytest.fixture()
def preview_trip_id():
    trip_id = f"trip_pl_preview_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "version": 3,
            "status": "assigned",
            "stage": "proposal",
            "strategy": {
                "recommended_option": {"name": "Original Supplier", "cost": 3000.0}
            },
        },
        agency_id=TEST_AGENCY_ID,
    )
    yield trip_id
    try:
        TripStore.delete_trip_for_agency(trip_id, TEST_AGENCY_ID)
    except Exception:
        pass


def test_relock_leaves_trip_byte_identical(session_client, preview_trip_id):
    """Core PA-06 S2 proof: trip before == trip after, effects empty."""
    trip_before = TripStore.get_trip_for_agency(preview_trip_id, TEST_AGENCY_ID)
    snapshot = copy.deepcopy(trip_before)

    resp = session_client.post(
        f"/api/v1/price-lock/{preview_trip_id}/re-lock",
        json={
            **_RELOCK_BODY,
            "trip_id": preview_trip_id,
            "expected_version": 3,
            "idempotency_key": "idem_prev_1",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["preview"] is True
    assert data["margin_saved_cents"] == 100000  # $3,000 -> $2,000
    assert data["effects"] == []
    assert data["would_persist"] is False
    assert data["not_persisted_reason"] == "simulated_rate_source"
    assert data["provider_connected"] is False
    assert data["reality_tier"] == "deterministic_preview"
    assert data["version"] == 3  # echoes current version; never bumped

    trip_after = TripStore.get_trip_for_agency(preview_trip_id, TEST_AGENCY_ID)
    assert trip_after == snapshot  # byte-identical: simulated rate never persisted


def test_relock_missing_guards_rejected_422(session_client, preview_trip_id):
    """Optimistic-version and idempotency-key guards are REQUIRED (422)."""
    for partial in (
        {"expected_version": 3},  # idempotency_key missing
        {"idempotency_key": "idem_prev_2"},  # expected_version missing
        {},  # both missing
    ):
        resp = session_client.post(
            f"/api/v1/price-lock/{preview_trip_id}/re-lock",
            json={**_RELOCK_BODY, "trip_id": preview_trip_id, **partial},
        )
        assert resp.status_code == 422, f"body={partial} -> {resp.status_code}"


def test_relock_stale_version_still_conflicts_409(session_client, preview_trip_id):
    """The F-01 optimistic-concurrency guard still fires under the preview."""
    resp = session_client.post(
        f"/api/v1/price-lock/{preview_trip_id}/re-lock",
        json={
            **_RELOCK_BODY,
            "trip_id": preview_trip_id,
            "expected_version": 1,  # stale; current is 3
            "idempotency_key": "idem_prev_3",
        },
    )
    assert resp.status_code == 409
    assert "version mismatch" in resp.json()["detail"].lower()


def test_opportunities_endpoint_stays_read_only(session_client, preview_trip_id):
    """GET /opportunities unchanged: read-only scan (PA-06 scope note)."""
    resp = session_client.get("/api/v1/price-lock/opportunities")
    assert resp.status_code == 200
    matched = next(
        (o for o in resp.json() if o["trip_id"] == preview_trip_id), None
    )
    assert matched is not None
    assert matched["current_net_rate_cents"] == 200000  # 400/night x 5 (simulated)
