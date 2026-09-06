"""
tests/test_p1_findings_hardening.py — Tests for P1 Register Hardening (F-01, F-02, F-14, F-07).

Tests:
1. F-01: Price Lock Optimistic Version Checking & Idempotency Key Re-entry
2. F-02: Public Proposal Cryptographic Capability Tokens (HMAC, TTL, Revocation)
3. F-14: Perishable Deadlines Sentinel (Visa D-30, TTL, CFAR 14d waiver, Supplier Balance)
4. F-07: Agent DLQ Inspector & Poisoned Job Replay / Redaction
"""

import os

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from spine_api.server import app
from spine_api.core.security import create_access_token
from spine_api.persistence import TripStore, TEST_AGENCY_ID
from spine_api.routers.public_proposals import (
    generate_signed_proposal_token,
    verify_proposal_token,
    revoke_proposal_token,
)
import spine_api.routers.public_proposals as _public_proposals
from src.monitoring.perishable_sentinel import (
    PerishableCategory,
    PerishableItem,
    PerishableSentinel,
    PerishableUrgency,
)
from src.agents.dlq_inspector import (
    DLQInspector,
)

os.environ["RUNNING_TESTS"] = "1"


# SPINE_API_DISABLE_AUTH must NOT be set at module level: pytest imports every
# test module during collection, so a module-level write disabled authentication
# for the ENTIRE process (it silently broke the auth-middleware 401 tests).
# Scope it per-test instead; middleware reads the flag at request time.
@pytest.fixture(autouse=True)
def _disable_auth_for_this_module(monkeypatch):
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    # The signed-token lifecycle test exercises the explicitly gated legacy
    # fixture; production requests must not use fabricated proposal content.
    monkeypatch.setenv("PUBLIC_PROPOSAL_DEMO_MODE", "1")


@pytest.fixture(autouse=True)
def _isolate_proposal_revocation_store(tmp_path, monkeypatch):
    """PT-05: revocations persist to disk — point tests at a temp store so the
    repo's real data/proposals/revoked_tokens.json is never touched."""
    monkeypatch.setattr(_public_proposals, "_REVOCATIONS_PATH", tmp_path / "revoked_tokens.json")
    monkeypatch.setattr(_public_proposals, "_REVOKED_TOKENS", {})


token = create_access_token(
    user_id="usr_p1_test",
    agency_id=TEST_AGENCY_ID,
    role="owner",
    expires_delta=timedelta(hours=12),
)
client = TestClient(app, headers={"Authorization": f"Bearer {token}", "X-Agency-ID": TEST_AGENCY_ID})


# ---------------------------------------------------------------------------
# 1. F-01: Price Lock Optimistic Versioning & Idempotency
# ---------------------------------------------------------------------------

def test_price_lock_optimistic_concurrency_conflict():
    """Verify version conflict raises HTTP 409 when trip was modified concurrently."""
    trip_id = "trip_pl_conc_1"
    TripStore.save_trip(
        {
            "id": trip_id,
            "version": 2,
            "strategy": {"recommended_option": {"name": "Lufthansa", "cost": 3000.0}},
        },
        agency_id=TEST_AGENCY_ID,
    )

    # Attempt re-lock with stale expected_version=1
    resp = client.post(
        f"/api/v1/price-lock/{trip_id}/re-lock",
        json={
            "trip_id": trip_id,
            "new_net_rate_cents": 250000,
            "expected_version": 1,  # Stale! Current is 2
        },
    )
    assert resp.status_code == 409
    assert "version mismatch" in resp.json()["detail"].lower()


def test_price_lock_idempotency_caching():
    """Verify identical idempotency_key returns cached response without duplicate increment."""
    trip_id = "trip_pl_idemp_1"
    TripStore.save_trip(
        {
            "id": trip_id,
            "version": 1,
            "strategy": {"recommended_option": {"name": "Emirates", "cost": 3000.0}},
        },
        agency_id=TEST_AGENCY_ID,
    )

    idemp_key = "idemp_abc_123"

    # First call
    resp1 = client.post(
        f"/api/v1/price-lock/{trip_id}/re-lock",
        json={
            "trip_id": trip_id,
            "new_net_rate_cents": 270000,
            "idempotency_key": idemp_key,
        },
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["margin_saved_cents"] == 30000
    assert data1["version"] == 2

    # Duplicate re-entry with same key
    resp2 = client.post(
        f"/api/v1/price-lock/{trip_id}/re-lock",
        json={
            "trip_id": trip_id,
            "new_net_rate_cents": 270000,
            "idempotency_key": idemp_key,
        },
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["margin_saved_cents"] == 30000
    # Version should remain unchanged on replay
    assert data2["version"] == 2


# ---------------------------------------------------------------------------
# 2. F-02: Cryptographic Proposal Capability Tokens
# ---------------------------------------------------------------------------

def test_public_proposal_signed_token_lifecycle():
    """Verify HMAC token generation, verification, and revocation."""
    trip_id = "trip_prop_crypto_1"
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system", ttl_hours=24)

    is_valid, reason, resolved_trip = verify_proposal_token(token)
    assert is_valid is True
    assert resolved_trip == trip_id

    # A valid claim without a persisted agency-bound resource must fail closed;
    # possession of the signing key is not itself proposal content.
    resp = client.get(f"/api/public/proposals/{token}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Proposal resource not found or link expired"

    # Revoke token
    revoke_proposal_token(token)
    is_valid_after_revoke, revoke_reason, _ = verify_proposal_token(token)
    assert is_valid_after_revoke is False
    assert "revoked" in revoke_reason.lower()


def test_public_proposal_tampered_token_rejected():
    """Verify tampered HMAC signature raises 401 Unauthorized."""
    token = generate_signed_proposal_token(trip_id="trip_test", agency_id="system", ttl_hours=24)
    tampered_token = token[:-4] + "ffff"

    resp = client.get(f"/api/public/proposals/{tampered_token}")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 3. F-14: Perishable Deadlines Sentinel
# ---------------------------------------------------------------------------

def test_perishable_sentinel_urgency_classification():
    """Verify sentinel flags critical (<12h), expiring soon (<48h), and expired items."""
    now = datetime.now(timezone.utc)

    items = [
        PerishableItem(
            item_id="per_1",
            trip_id="trip_1",
            traveler_name="Carlos Ruiz",
            category=PerishableCategory.AIRLINE_TICKETING_TTL,
            title="Lufthansa GDS Ticketing Hold",
            deadline_iso=(now + timedelta(hours=6)).isoformat(),
            financial_exposure_usd=1200.0,
        ),
        PerishableItem(
            item_id="per_2",
            trip_id="trip_2",
            traveler_name="Maria Silva",
            category=PerishableCategory.INSURANCE_CFAR_WAIVER_14D,
            title="Allianz CFAR 14-Day Waiver Window",
            deadline_iso=(now + timedelta(hours=36)).isoformat(),
            financial_exposure_usd=500.0,
        ),
        PerishableItem(
            item_id="per_3",
            trip_id="trip_3",
            traveler_name="Elena Petrova",
            category=PerishableCategory.VISA_APPOINTMENT,
            title="Schengen VFS Submission Window",
            deadline_iso=(now - timedelta(hours=2)).isoformat(),
            financial_exposure_usd=3500.0,
        ),
    ]

    summary = PerishableSentinel.audit_perishables(items=items, now_dt=now)

    assert summary.total_tracked_items == 3
    assert summary.critical_urgent_count == 1
    assert summary.expiring_soon_count == 1
    assert summary.expired_count == 1
    assert summary.total_at_risk_exposure_usd == 5200.0

    # Verify order: expired and critical on top
    assert summary.items[0].urgency == PerishableUrgency.EXPIRED_LAPSED
    assert summary.items[1].urgency == PerishableUrgency.CRITICAL_URGENT
    assert summary.items[2].urgency == PerishableUrgency.EXPIRING_SOON


# ---------------------------------------------------------------------------
# 4. F-07: Agent DLQ Inspector & Replay
# ---------------------------------------------------------------------------

def test_dlq_inspector_redaction_and_replay():
    """Verify DLQ registers poisoned tasks, sanitizes secrets, and allows safe replay."""
    job_id = "job_poison_99"
    raw_payload = {
        "traveler_name": "James Bond",
        "api_token": "sk-live-secret-123456",
        "credit_card_pan": "4111222233334444",
        "destination": "London",
    }

    record = DLQInspector.record_poisoned_job(
        job_id=job_id,
        agent_name="TicketingAgent",
        trip_id="trip_007",
        error_message="GDS Terminal Timeout 504 Gateway",
        stack_trace="Traceback: File amadeus.py line 42 in issue_ticket...",
        failed_payload=raw_payload,
    )

    # Verify secret redaction
    assert record.failed_payload["api_token"] == "[REDACTED_BY_DLQ_GUARD]"
    assert record.failed_payload["credit_card_pan"] == "[REDACTED_BY_DLQ_GUARD]"
    assert record.failed_payload["destination"] == "London"

    # List active in DLQ
    poisoned_list = DLQInspector.list_poisoned_jobs()
    assert any(j.job_id == job_id for j in poisoned_list)

    # Replay job with patched payload
    replay_result = DLQInspector.replay_job(
        job_id=job_id,
        patched_payload={"destination": "London", "retry_channel": "NDC"},
    )
    assert replay_result["ok"] is True
    assert replay_result["status"] == "REPLAYED"

    # Job is no longer in active DLQ queue
    assert not any(j.job_id == job_id for j in DLQInspector.list_poisoned_jobs())
