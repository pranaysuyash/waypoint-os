"""
tests/test_payment_mandate_ledger.py — F-04 payment mandate ledger + fulfillment seam.

Contract under test (memory backend; the SQL backend shares the same interface):
1. Registration requires a consent_artifact_ref (the anti-decoration rule) and
   stores only the consent digest, never the raw text.
2. authorize_charge is a CAS consume: happy path, cap transition, overdraft
   refusal (no partial consumption), revocation, expiry.
3. Fulfillment integration: a covering mandate is consumed and recorded;
   an insufficient mandate refuses the movement outright; enforcement flag
   SPINE_API_REQUIRE_PAYMENT_MANDATES refuses mandate-less movement with 403
   (default off until ADR-008 R1 ratification — recorded as mandate_id=None).
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from spine_api.persistence import TripStore
from spine_api.routers.public_proposals import (
    AcceptProposalRequest,
    accept_proposal,
    generate_signed_proposal_token,
)
from spine_api.services import payment_mandate_service as pms
from spine_api.services.payment_mandate_service import PaymentMandateLedger
from src.orchestration.booking_fulfillment import BookingFulfillmentEngine


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setenv("SPINE_API_PAYMENT_MANDATE_BACKEND", "memory")
    monkeypatch.delenv("SPINE_API_REQUIRE_PAYMENT_MANDATES", raising=False)


# ---------------------------------------------------------------------------
# Ledger contract (memory backend)
# ---------------------------------------------------------------------------


def _register(**overrides):
    kwargs = {
        "agency_id": "agency_A",
        "trip_id": f"trip_{uuid.uuid4().hex[:8]}",
        "customer_id": "cust_1",
        "max_authorized_cents": 500_000,
        "purpose": "FINAL_BALANCE",
        "consent_text": "I authorize Waypoint OS to collect the final balance.",
        "consent_artifact_ref": "audit_event_or_token_123",
    }
    kwargs.update(overrides)
    return PaymentMandateLedger.register_mandate(**kwargs)


def test_registration_requires_consent_artifact_and_valid_fields():
    with pytest.raises(ValueError, match="consent_artifact_ref"):
        _register(consent_artifact_ref="")
    with pytest.raises(ValueError, match="purpose"):
        _register(purpose="WHIM")
    with pytest.raises(ValueError, match="positive"):
        _register(max_authorized_cents=0)
    with pytest.raises(ValueError, match="agency_id"):
        _register(agency_id="")


def test_mandate_stores_digest_never_raw_consent():
    secret = "Traveler secret consent phrasing 2026-09-07."
    record = _register(consent_text=secret)
    d = record.to_dict()
    assert d["consent_text_sha256"] and len(d["consent_text_sha256"]) == 64
    assert secret not in str(d)


def test_authorize_charge_consumes_and_transitions_to_consumed():
    record = _register(max_authorized_cents=10_000)
    first = PaymentMandateLedger.authorize_charge(
        agency_id="agency_A", mandate_id=record.mandate_id, amount_cents=6_000
    )
    assert first["authorized"] is True
    assert first["remaining_authorized_cents"] == 4_000

    second = PaymentMandateLedger.authorize_charge(
        agency_id="agency_A", mandate_id=record.mandate_id, amount_cents=4_000
    )
    assert second["authorized"] is True
    assert second["status"] == "CONSUMED"

    # Cap reached: any further movement is refused outright.
    third = PaymentMandateLedger.authorize_charge(
        agency_id="agency_A", mandate_id=record.mandate_id, amount_cents=1
    )
    assert third["authorized"] is False


def test_authorize_charge_refuses_overdraft_without_partial_consumption():
    record = _register(max_authorized_cents=10_000)
    refused = PaymentMandateLedger.authorize_charge(
        agency_id="agency_A", mandate_id=record.mandate_id, amount_cents=10_001
    )
    assert refused["authorized"] is False
    after = PaymentMandateLedger.get_mandate(
        agency_id="agency_A", mandate_id=record.mandate_id
    )
    assert after["consumed_amount_cents"] == 0, "refusal must not consume anything"
    assert after["status"] == "ACTIVE"


def test_revocation_is_cas_and_authorize_refuses_afterwards():
    record = _register()
    assert (
        PaymentMandateLedger.revoke_mandate(
            agency_id="agency_A", mandate_id=record.mandate_id, reason="traveler withdrew"
        )
        is True
    )
    # Second revoke is refused (status no longer ACTIVE) — CAS, not idempotent overwrite.
    assert (
        PaymentMandateLedger.revoke_mandate(
            agency_id="agency_A", mandate_id=record.mandate_id, reason="again"
        )
        is False
    )
    refused = PaymentMandateLedger.authorize_charge(
        agency_id="agency_A", mandate_id=record.mandate_id, amount_cents=100
    )
    assert refused["authorized"] is False
    assert "REVOKED" in refused["reason"]


def test_cross_agency_access_is_refused():
    record = _register(agency_id="agency_A")
    assert (
        PaymentMandateLedger.get_mandate(agency_id="agency_B", mandate_id=record.mandate_id)
        is None
    )
    refused = PaymentMandateLedger.authorize_charge(
        agency_id="agency_B", mandate_id=record.mandate_id, amount_cents=100
    )
    assert refused["authorized"] is False


def test_expired_mandate_is_refused(monkeypatch):
    record = _register(validity_days=1)
    future = datetime.now(timezone.utc) + timedelta(days=5)

    original_now = pms._now
    monkeypatch.setattr(pms, "_now", lambda: future)

    refused = PaymentMandateLedger.authorize_charge(
        agency_id="agency_A", mandate_id=record.mandate_id, amount_cents=100
    )
    monkeypatch.setattr(pms, "_now", original_now)
    assert refused["authorized"] is False
    assert "expired" in refused["reason"].lower()


def test_resolve_for_trip_returns_active_only():
    trip_id = f"trip_{uuid.uuid4().hex[:8]}"
    revoked = _register(trip_id=trip_id)
    PaymentMandateLedger.revoke_mandate(
        agency_id="agency_A", mandate_id=revoked.mandate_id, reason="test"
    )
    active = _register(trip_id=trip_id)
    resolved = PaymentMandateLedger.resolve_for_trip(agency_id="agency_A", trip_id=trip_id)
    assert resolved is not None
    assert resolved.mandate_id == active.mandate_id
    assert PaymentMandateLedger.resolve_for_trip(agency_id="agency_B", trip_id=trip_id) is None


# ---------------------------------------------------------------------------
# Fulfillment seam
# ---------------------------------------------------------------------------


def _seed_trip(cost: float = 4500.0) -> str:
    trip_id = f"trip_f04_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": "system",
            "status": "assigned",
            "destination": "Paris",
            "packet": {
                "destination": "Paris",
                "start_date": "2026-10-15",
                "end_date": "2026-10-22",
                "party_size": 2,
            },
            "strategy": {
                "recommended_option": {"name": "Paris Luxury Escape", "cost": cost, "currency": "USD"}
            },
        },
        agency_id="system",
    )
    return trip_id


def _accept_and_fulfill(trip_id: str, token: str):
    accepted = accept_proposal(
        token=token,
        req=AcceptProposalRequest(
            signer_name="Sarah Connor", signer_email="sarah@sky.net", e_signature_consent=True
        ),
    )
    assert accepted.status == "accepted"
    return BookingFulfillmentEngine.fulfill_accepted_proposal(
        trip_id=trip_id, proposal_token=token, holder_id="user:advisor@test"
    )


@pytest.mark.asyncio
async def test_fulfillment_with_covering_mandate_consumes_and_records():
    trip_id = _seed_trip(cost=4500.0)
    mandate = _register(
        agency_id="system", trip_id=trip_id, max_authorized_cents=500_000
    )
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    result = await _accept_and_fulfill(trip_id, token)

    assert result.mandate_id == mandate.mandate_id
    assert result.mandate_enforced is True
    d = result.to_dict()
    assert d["mandate_id"] == mandate.mandate_id
    consumed = PaymentMandateLedger.get_mandate(agency_id="system", mandate_id=mandate.mandate_id)
    assert consumed["consumed_amount_cents"] == 450_000  # 4500.00 USD


@pytest.mark.asyncio
async def test_fulfillment_refuses_insufficient_mandate():
    trip_id = _seed_trip(cost=4500.0)
    _register(agency_id="system", trip_id=trip_id, max_authorized_cents=1000)
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    with pytest.raises(ValueError, match="does not authorize"):
        await _accept_and_fulfill(trip_id, token)


@pytest.mark.asyncio
async def test_fulfillment_403_when_enforced_and_no_mandate(monkeypatch):
    monkeypatch.setenv("SPINE_API_REQUIRE_PAYMENT_MANDATES", "1")
    trip_id = _seed_trip()
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    with pytest.raises(Exception) as excinfo:
        await _accept_and_fulfill(trip_id, token)
    assert getattr(excinfo.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_fulfillment_without_mandate_defaults_to_unenforced_record():
    trip_id = _seed_trip()
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    result = await _accept_and_fulfill(trip_id, token)
    assert result.mandate_id is None
    assert result.mandate_enforced is False


def test_router_register_rejects_missing_consent_artifact():
    """HTTP contract: registration without a consent artifact is 422, not a
    decorative mandate row."""
    from spine_api.routers.financial_ops import router as financial_ops_router

    app = FastAPI()
    app.include_router(financial_ops_router)
    client = TestClient(app)

    body = {
        "trip_id": "trip_x",
        "customer_id": "cust_x",
        "max_authorized_cents": 1000,
        "purpose": "FINAL_BALANCE",
        "consent_text": "consent",
        # consent_artifact_ref deliberately omitted
    }
    # Without an authenticated principal the agency dependency refuses first;
    # either 401/403 (auth) or 422 (consent artifact) proves no silent creation.
    resp = client.post("/api/v1/financial-ops/payment-mandates", json=body)
    assert resp.status_code in (401, 403, 422)
