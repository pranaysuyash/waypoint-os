"""
Part-K (2026-09-07): lease heartbeat + Stripe livemode fail-closed.

- ``lease_heartbeat`` renews the fulfillment lease DURING long provider
  awaits and fails loud on exit if the fence was lost mid-window.
- ``StripeIssuingAdapter.issue_single_use_card`` under sk_live_* refuses to
  mint a fixture as a "live" instrument (§13 claim reality), and the sandbox
  path derives instruments deterministically from the idempotency key
  (Part-H P0 / Part-J #1).
"""

import os

import pytest

os.environ["RUNNING_TESTS"] = "1"

import asyncio

from src.orchestration.agent_lease import (
    DurableAgentLeaseManager,
    lease_heartbeat,
)
from spine_api.providers.stripe_issuing_adapter import (
    StripeIssuingAdapter,
    VirtualCardIssuanceRequest,
)


@pytest.mark.asyncio
async def test_lease_heartbeat_renews_during_body(monkeypatch):
    renewals = []
    monkeypatch.setattr(
        DurableAgentLeaseManager,
        "renew_lease",
        classmethod(lambda cls, trip_id, token, ttl_seconds=30: renewals.append(token)),
    )

    async with lease_heartbeat("trip_hb", "tok", interval_seconds=0.01, ttl_seconds=60):
        await asyncio.sleep(0.05)

    assert len(renewals) >= 1


@pytest.mark.asyncio
async def test_lease_heartbeat_fails_loud_when_lease_lost(monkeypatch):
    def _lost(trip_id, token, ttl_seconds=30):
        raise RuntimeError("lease expired")

    monkeypatch.setattr(
        DurableAgentLeaseManager,
        "renew_lease",
        classmethod(lambda cls, trip_id, token, ttl_seconds=30: _lost(trip_id, token, ttl_seconds)),
    )

    with pytest.raises(RuntimeError, match="Lease lost during heartbeat window"):
        async with lease_heartbeat("trip_hb_lost", "tok", interval_seconds=0.01, ttl_seconds=60):
            await asyncio.sleep(0.05)


def test_stripe_sandbox_is_deterministic_per_idempotency_key():
    request = VirtualCardIssuanceRequest(
        amount_cents=450000,
        currency="USD",
        trip_id="trip_x",
        idempotency_key="key-42",
    )
    first = asyncio.run(StripeIssuingAdapter().issue_single_use_card(request))
    second = asyncio.run(StripeIssuingAdapter().issue_single_use_card(request))
    assert first.card_id == second.card_id
    assert first.last4 == second.last4


@pytest.mark.asyncio
async def test_stripe_livemode_refuses_to_mint_fake_live_instrument(monkeypatch):
    """Part-K: under sk_live_* the adapter must FAIL CLOSED — returning a
    fixture labeled live would fabricate a real instrument."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_test_nonexistent")
    adapter = StripeIssuingAdapter()
    assert adapter.is_livemode is True
    with pytest.raises(RuntimeError, match="refuses to mint a simulated card"):
        await adapter.issue_single_use_card(
            VirtualCardIssuanceRequest(amount_cents=1000, idempotency_key="k")
        )
