"""
tests/test_pa_authority_enforcement.py — PA-08: governance registry enforcement.

Before PA-08, `validate_action`/`max_budget_impact` had zero execution-path
callers (authority was a diagram, not a property). These tests pin the new
`enforce_action_authority` gate on the two consequential paths: booking
fulfillment and advisor payout authorization.

S2 adjustment (PA-08 wave 2, 2026-09-07 — failed-before / passes-after):
- FAILED BEFORE (under wave-1 semantics): an over-cap amount raised
  `AuthorityDenied`, which the fulfillment engine converted into a terminal
  HTTPException(403, "authority_denied") — there was no ratifiable remedy.
- PASSES AFTER: an over-cap amount raises `AuthorityApprovalRequired` (the
  approval-remediable outcome; the engine's AuthorityDenied handler no longer
  intercepts it), and the fulfillment router resolves it — 403 with
  `approval_required` + ratification recipe when unratified, or a completed
  fulfillment carrying `authority_approval_id` in metadata when ratified.
  The 403 HTTP contract is pinned by
  tests/test_pa_wave2_authority_approvals.py; this module keeps pinning the
  registry-level outcomes and the payout endpoint's 403 escalation body.
"""

import uuid

import pytest

from spine_api.persistence import TripStore
from spine_api.routers.public_proposals import (
    AcceptProposalRequest,
    _get_or_create_proposal,
    accept_proposal,
    generate_signed_proposal_token,
)
from src.governance.registry import (
    AgentRegistration,
    AgentTier,
    AuthorityApprovalRequired,
    AuthorityDenied,
    enforce_action_authority,
    governance_registry,
)
from src.orchestration.booking_fulfillment import BookingFulfillmentEngine


# ---------------------------------------------------------------------------
# Unit: enforce_action_authority semantics
# ---------------------------------------------------------------------------

def test_in_cap_action_passes_and_returns_evidence():
    evidence = enforce_action_authority("agent_intake_01", "parse_freeform_text", amount_usd=0.0)
    assert evidence["granted"] is True
    assert evidence["agent"] == "agent_intake_01"
    assert evidence["checked_amount_usd"] == 0.0
    assert evidence["checked_at"]


def test_unregistered_agent_is_denied():
    with pytest.raises(AuthorityDenied, match="not registered"):
        enforce_action_authority("agent_does_not_exist", "parse_freeform_text")


def test_disallowed_action_is_denied():
    with pytest.raises(AuthorityDenied, match="allowed_actions"):
        enforce_action_authority("agent_intake_01", "fulfill_accepted_proposal")


def test_amount_over_budget_cap_is_denied():
    # S2 (wave 2): over-cap is approval-remediable (AuthorityApprovalRequired),
    # not a terminal AuthorityDenied — see module docstring.
    # agent_strategy_01 has max_budget_impact=10000.0
    with pytest.raises(AuthorityApprovalRequired, match="max_budget_impact"):
        enforce_action_authority("agent_strategy_01", "build_session_strategy", amount_usd=10000.01)
    # Boundary: exactly at cap passes.
    enforce_action_authority("agent_strategy_01", "build_session_strategy", amount_usd=10000.0)


def test_amount_none_checks_permission_only():
    evidence = enforce_action_authority("agent_strategy_01", "build_session_strategy", amount_usd=None)
    assert evidence["granted"] is True


# ---------------------------------------------------------------------------
# Integration: payout authorize endpoint enforces the registry cap
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_payout_over_cap_yields_403_escalation(session_client):
    response = session_client.post(
        "/api/v1/subagent-payouts/adv_pa08_cap/request-payout",
        json={"amount_cents": 500000, "payout_method": "DIRECT_DEPOSIT"},  # $5,000 > $2,000 cap
        headers={"X-Agency-ID": "agency_pa08_test"},
    )
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["error"] == "authority_denied"
    assert detail["escalation_required"] is True
    assert detail["agent"] == "advisor_payout"
    assert "max_budget_impact" in detail["reason"]

    # Denied request must not mutate the ledger.
    ledger = session_client.get(
        "/api/v1/subagent-payouts/adv_pa08_cap/ledger",
        headers={"X-Agency-ID": "agency_pa08_test"},
    ).json()
    assert ledger["cleared_payout_cents"] == 150000  # seeded demo baseline only


def test_payout_in_cap_passes(session_client):
    response = session_client.post(
        "/api/v1/subagent-payouts/adv_pa08_ok/request-payout",
        json={"amount_cents": 25000, "payout_method": "DIRECT_DEPOSIT"},  # $250 ≤ $2,000 cap
        headers={"X-Agency-ID": "agency_pa08_test"},
    )
    assert response.status_code == 200
    assert response.json()["cleared_payout_cents"] > 150000


# ---------------------------------------------------------------------------
# Integration: fulfillment enforces the registry cap pre-execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fulfillment_over_cap_raises_403_escalation():
    trip_id = f"trip_pa08_{uuid.uuid4().hex[:10]}"
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
            },
            "strategy": {"recommended_option": {"name": "Cap Buster", "cost": 90000.0, "currency": "USD"}},
        },
        agency_id="system",
    )
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    accept_proposal(
        token=token,
        req=AcceptProposalRequest(signer_name="Big Spender", signer_email="big@spender.test", e_signature_consent=True),
    )
    # Registry row built from the trip must show accepted + the $90k total.
    proposal = _get_or_create_proposal(token)
    assert proposal.status == "accepted"

    # Shrink the fulfillment agent's cap so the package total exceeds it.
    original = governance_registry.get_agent("agent_fulfillment_01")
    governance_registry.register(
        AgentRegistration(
            agent_id="agent_fulfillment_01",
            role_name=original.role_name,
            tier=AgentTier.AUTONOMOUS_BOUNDED,
            allowed_actions=list(original.allowed_actions),
            max_budget_impact=1.0,
        )
    )
    try:
        with pytest.raises(AuthorityApprovalRequired) as excinfo:
            await BookingFulfillmentEngine.fulfill_accepted_proposal(
                trip_id=trip_id,
                proposal_token=token,
                holder_id="test_advisor",
            )
        # Wave 2: over-cap is approval-remediable, not a terminal denial. The
        # exception carries the exact (action, amount) an operator ratifies.
        assert excinfo.value.action == "fulfill_accepted_proposal"
        assert excinfo.value.amount_usd == 90000.0
        assert not isinstance(excinfo.value, AuthorityDenied)
    finally:
        governance_registry.register(original)

    # No VCC/GDS/JDG side effects may have reached the trip record.
    stored = TripStore.get_trip(trip_id)
    assert not stored.get("booking_confirmation")
