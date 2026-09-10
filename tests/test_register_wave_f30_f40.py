"""
Tests for the 2026-09-05 register-wave fixes (F-30..F-40 partial + PT-08).

Covers:
- F-31: insurance preview preserves illustrative plans without claiming an
  unsupported CFAR deadline or pre-existing-condition eligibility.
- F-32: price-lock expiry reads BOTH write locations (strategy + trip top-level).
- F-35: metrics conversion counts terminal statuses writers emit (delivered).
- F-36: feedback honesty — survey staged (not "DISPATCHED"), scorecard labeled
  demo_static.
- F-37 (slice): CanonicalPacket.to_dict serializes assumptions.
- F-38: /alerts returns only stored disruptions — no fabricated CRITICAL alert.
- F-40: GET /stats exists and returns the TripStats contract keys.
- PT-08: idempotency-backend startup assertion fails in staging without sql.
"""

import os
from datetime import datetime, timedelta, timezone

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import uuid

import pytest

from spine_api import persistence

TripStore = persistence.TripStore

AGENCY = "test_agency_wave_f30"


@pytest.fixture(autouse=True)
def wave_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _headers() -> dict:
    return {"X-Agency-ID": AGENCY}


def _make_trip(extra: dict | None = None) -> str:
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    record = {
        "id": trip_id,
        "agency_id": AGENCY,
        "status": "new",
        "destination": "Tokyo",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    record.update(extra or {})
    TripStore.save_trip(record, agency_id=AGENCY)
    return trip_id


# ---------------------------------------------------------------- F-31


def test_f31_quote_without_deposit_is_not_evaluated(session_client):
    resp = session_client.post(
        "/api/v1/insurance/quote",
        json={"total_trip_cost_usd": 5000.0},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cfar_deadline"] is None
    assert data["days_remaining_for_cfar"] is None
    assert data["cfar_deadline_anchor"] == "not_evaluated"
    assert data["cfar_timing_status"] == "not_evaluated"
    assert data["cfar_evidence"]["policy_rule_status"] == "not_adopted"
    assert all(plan["pre_existing_waiver_eligible"] is None for plan in data["plans"])


def test_f31_quote_with_recent_deposit_keeps_timing_unresolved(session_client):
    deposit = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
    resp = session_client.post(
        "/api/v1/insurance/quote",
        json={"total_trip_cost_usd": 5000.0, "deposit_date": deposit},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cfar_deadline"] is None
    assert data["days_remaining_for_cfar"] is None
    assert data["cfar_deadline_anchor"] == "not_evaluated"
    assert data["cfar_timing_status"] == "not_evaluated"
    assert data["cfar_evidence"]["source"] == "request.deposit_date"
    assert data["cfar_evidence"]["verification"] == "unverified"


def test_f31_quote_with_stale_deposit_does_not_invent_expiry(session_client):
    deposit = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    resp = session_client.post(
        "/api/v1/insurance/quote",
        json={"total_trip_cost_usd": 5000.0, "deposit_date": deposit},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cfar_deadline"] is None
    assert data["days_remaining_for_cfar"] is None
    assert data["cfar_deadline_anchor"] == "not_evaluated"
    assert data["cfar_timing_status"] == "not_evaluated"


def test_f31_unparseable_deposit_is_a_validation_error(session_client):
    resp = session_client.post(
        "/api/v1/insurance/quote",
        json={"total_trip_cost_usd": 5000.0, "deposit_date": "not-a-date"},
        headers=_headers(),
    )
    assert resp.status_code == 422
    assert any(
        "deposit_date" in str(error.get("loc", []))
        for error in resp.json()["detail"]
    )


def test_f31_attach_policy_still_works(session_client):
    trip_id = _make_trip()
    resp = session_client.post(
        f"/api/v1/insurance/{trip_id}/attach-policy",
        json={
            "trip_id": trip_id,
            "selected_plan_id": "ins_cfar_03",
            "policy_number": "POL-WAVE-1",
            "premium_paid_usd": 100.0,
        },
        headers=_headers(),
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------- F-32


def test_f32_price_lock_reads_top_level_write_location():
    from spine_api.routers.price_lock import _get_price_lock_expires_at

    written = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
    trip = {"id": "trip_x", "price_lock_expires_at": written}  # social_inbound shape

    assert _get_price_lock_expires_at(trip).date() == datetime.fromisoformat(written).date()


def test_f32_price_lock_still_reads_strategy_location():
    from spine_api.routers.price_lock import _get_price_lock_expires_at

    written = (datetime.now(timezone.utc) + timedelta(hours=30)).isoformat()
    trip = {"id": "trip_x", "strategy": {"price_lock_expires_at": written}}

    assert _get_price_lock_expires_at(trip).date() == datetime.fromisoformat(written).date()


def test_f32_price_lock_strategy_wins_over_top_level():
    from spine_api.routers.price_lock import _get_price_lock_expires_at

    strategy_ts = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()
    trip = {
        "id": "trip_x",
        "strategy": {"price_lock_expires_at": strategy_ts},
        "price_lock_expires_at": (datetime.now(timezone.utc) + timedelta(hours=99)).isoformat(),
    }
    assert _get_price_lock_expires_at(trip).date() == datetime.fromisoformat(strategy_ts).date()


# ---------------------------------------------------------------- F-35


def test_f35_metrics_count_delivered_as_converted():
    from src.analytics.metrics import aggregate_insights

    trips = [
        {"id": "t1", "status": "delivered", "analytics": {}},
        {"id": "t2", "status": "new", "analytics": {}},
    ]
    insights = aggregate_insights(trips, days=30)
    assert insights.conversionRate > 0  # delivered now counts


# ---------------------------------------------------------------- F-36


def test_f36_survey_is_staged_not_dispatched(session_client):
    trip_id = _make_trip()
    resp = session_client.post(
        f"/api/v1/feedback/{trip_id}/trigger-survey",
        json={"trip_id": trip_id, "delivery_channel": "whatsapp"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    saved = TripStore.get_trip(trip_id)
    feedback = saved["post_trip_feedback"]
    assert feedback["status"] == "STAGED"
    assert feedback["dispatched"] is False


def test_f36_scorecard_honest_aggregation(session_client):
    """Scorecard aggregates from stored responses and labels its source —
    the fabricated demo rows are gone (superseded by the E-10 build)."""
    resp = session_client.get("/api/v1/feedback/supplier-scorecard", headers=_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["data_source"] == "computed_from_responses"
    assert data["total_feedback_submissions"] == 0
    assert data["suppliers"] == []


# ---------------------------------------------------------------- F-37 slice


def test_f37_to_dict_serializes_assumptions():
    from src.intake.packet_models import AssumptionRecord, CanonicalPacket

    packet = CanonicalPacket(packet_id="pkt_wave_test")
    packet.assumptions = [
        AssumptionRecord(
            slot_name="budget_max",
            assumed_value=5000,
            rationale="defaulted from season norm",
            criticality="preference",
        )
    ]
    data = packet.to_dict()
    assert len(data["assumptions"]) == 1
    assert data["assumptions"][0]["slot_name"] == "budget_max"


# ---------------------------------------------------------------- F-38
# Each alert test uses a FRESH agency: the file store persists across runs,
# and the empty-vs-stored assertions are per-agency scans.


def test_f38_alerts_empty_without_stored_disruption(session_client):
    fresh = f"agency_f38_{uuid.uuid4().hex[:8]}"
    TripStore.save_trip(
        {"id": f"trip_{uuid.uuid4().hex[:12]}", "agency_id": fresh, "status": "new"},
        agency_id=fresh,
    )
    resp = session_client.get("/api/v1/disruptions/alerts", headers={"X-Agency-ID": fresh})
    assert resp.status_code == 200
    assert resp.json() == []  # no fabricated CRITICAL alert


def test_f38_alerts_returns_stored_disruption(session_client):
    fresh = f"agency_f38_{uuid.uuid4().hex[:8]}"
    stored = {
        "disruption_id": f"dis_{uuid.uuid4().hex[:8]}",
        "trip_id": "trip_x",
        "destination": "Tokyo",
        "flight_number": "JL711",
        "disruption_type": "DELAYED",
        "urgency_level": "WARNING",
        "delay_minutes": 90,
        "impact_summary": "stored test disruption",
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    TripStore.save_trip(
        {
            "id": f"trip_{uuid.uuid4().hex[:12]}",
            "agency_id": fresh,
            "status": "new",
            "active_disruption": stored,
        },
        agency_id=fresh,
    )
    resp = session_client.get("/api/v1/disruptions/alerts", headers={"X-Agency-ID": fresh})
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) == 1
    assert alerts[0]["impact_summary"] == "stored test disruption"


# ---------------------------------------------------------------- F-40
# GET /stats resolves the Agency row via get_current_agency, so this test uses
# the canonical seeded test agency. Read-only (counts only) per data safety.


def test_f40_stats_route_returns_contract_keys(session_client):
    resp = session_client.get(
        "/stats",
        headers={"X-Agency-ID": "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"active", "pendingReview", "readyToBook", "needsAttention"}
    assert all(isinstance(v, int) for v in data.values())
    assert data["active"] >= 0


# ---------------------------------------------------------------- PT-08


def test_pt08_idempotency_assertion_fails_in_staging_when_unset(monkeypatch):
    from spine_api.core.startup_assertions import _check_idempotency_backend

    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.delenv("SPINE_API_IDEMPOTENCY_BACKEND", raising=False)
    ok, message = _check_idempotency_backend()
    assert not ok
    assert "cross-process" in message


def test_pt08_idempotency_assertion_passes_with_sql(monkeypatch):
    from spine_api.core.startup_assertions import _check_idempotency_backend

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SPINE_API_IDEMPOTENCY_BACKEND", "sql")
    ok, _ = _check_idempotency_backend()
    assert ok


def test_pt08_idempotency_assertion_allows_dev_fallback(monkeypatch):
    from spine_api.core.startup_assertions import _check_idempotency_backend

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("SPINE_API_IDEMPOTENCY_BACKEND", raising=False)
    ok, _ = _check_idempotency_backend()
    assert ok
