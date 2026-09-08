"""
tests/test_pa_wave2_authority_approvals.py — PA-08 wave 2: durable dual-control approval flow.

Before wave 2, an over-cap amount was a terminal ``AuthorityDenied`` — there
was no durable, ratifiable remedy (the audit's "decorative dual control").
This pins the new flow:

1. Approval ledger semantics (memory backend): request → first approve →
   same-person second is a 409-class conflict → distinct second ratifies;
   role check (owner/admin only); ``get_approved`` only returns ratified
   records; deny is CAS.
2. ``enforce_action_authority`` over-cap now raises ``AuthorityApprovalRequired``
   (a distinct outcome callers can resolve via a ratified approval);
   unregistered agent / forbidden action remain ``AuthorityDenied``.
3. Fulfillment router: over-cap 403 body carries ``approval_required`` +
   subject ids; with a ratified approval the fulfillment proceeds and the
   response metadata carries ``authority_approval_id``.

S2 notes (failed-before / passes-after):
- FAILED BEFORE: over-cap fulfillment could only ever return a terminal 403;
  ``AuthorityApprovalRequired`` did not exist and no approval endpoints
  existed (404).
- PASSES AFTER: the same over-cap scenario is approval-remediable and the
  ratified path completes with the approval recorded in response metadata.
"""

import uuid

import pytest

from spine_api.persistence import TripStore
from spine_api.routers.public_proposals import (
    AcceptProposalRequest,
    accept_proposal,
    generate_signed_proposal_token,
)
from spine_api.services.authority_approval_service import (
    AuthorityApprovalLedger,
    ApprovalConflict,
    ApprovalNotAuthorized,
)
from src.governance.registry import (
    AuthorityApprovalRequired,
    AuthorityDenied,
    enforce_action_authority,
    ratified_authority_scope,
)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setenv("SPINE_API_AUTHORITY_APPROVAL_BACKEND", "memory")
    monkeypatch.delenv("SPINE_API_ADVISOR_PAYOUT_BACKEND", raising=False)


@pytest.fixture(autouse=True)
def _isolated_approvals():
    AuthorityApprovalLedger._MEMORY_STORE.clear()
    yield
    AuthorityApprovalLedger._MEMORY_STORE.clear()


# ---------------------------------------------------------------------------
# Approval ledger semantics (memory backend)
# ---------------------------------------------------------------------------


def _request(**overrides):
    kwargs = {
        "agency_id": "agency_A",
        "action": "fulfill_accepted_proposal",
        "subject_type": "trip",
        "subject_id": f"trip_{uuid.uuid4().hex[:8]}",
        "requested_by": "requester_1",
        "amount_usd": 90000.0,
        "reason": "VIP booking above agent cap",
    }
    kwargs.update(overrides)
    return AuthorityApprovalLedger.request_approval(**kwargs)


def test_request_creates_pending_second_record():
    record = _request()
    assert record.approval_id.startswith("APR-")
    d = record.to_dict()
    assert d["status"] == "pending_second"
    assert d["first_approver_id"] is None
    assert d["second_approver_id"] is None
    assert d["amount_usd"] == 90000.0
    assert d["storage_backend"] == "memory"


def test_first_then_same_person_second_is_409_conflict():
    record = _request()
    first = AuthorityApprovalLedger.approve(
        agency_id="agency_A", approval_id=record.approval_id,
        approver_user_id="owner_1", approver_role="owner",
    )
    assert first.status == "pending_second"
    assert first.first_approver_id == "owner_1"
    with pytest.raises(ApprovalConflict, match="same user cannot provide both"):
        AuthorityApprovalLedger.approve(
            agency_id="agency_A", approval_id=record.approval_id,
            approver_user_id="owner_1", approver_role="owner",
        )


def test_distinct_second_approval_ratifies():
    record = _request()
    AuthorityApprovalLedger.approve(
        agency_id="agency_A", approval_id=record.approval_id,
        approver_user_id="owner_1", approver_role="owner",
    )
    ratified = AuthorityApprovalLedger.approve(
        agency_id="agency_A", approval_id=record.approval_id,
        approver_user_id="admin_2", approver_role="admin",
    )
    assert ratified.status == "approved"
    assert ratified.second_approver_id == "admin_2"
    # Third approval attempt is a conflict — nothing is pending.
    with pytest.raises(ApprovalConflict):
        AuthorityApprovalLedger.approve(
            agency_id="agency_A", approval_id=record.approval_id,
            approver_user_id="owner_3", approver_role="owner",
        )


def test_non_privileged_role_is_403_class():
    record = _request()
    with pytest.raises(ApprovalNotAuthorized, match="may not ratify"):
        AuthorityApprovalLedger.approve(
            agency_id="agency_A", approval_id=record.approval_id,
            approver_user_id="advisor_9", approver_role="advisor",
        )


def test_get_approved_only_returns_ratifed_records():
    record = _request()
    assert (
        AuthorityApprovalLedger.get_approved(
            agency_id="agency_A", action="fulfill_accepted_proposal", subject_id=record.subject_id
        )
        is None
    )  # pending is not ratified
    AuthorityApprovalLedger.approve(
        agency_id="agency_A", approval_id=record.approval_id,
        approver_user_id="owner_1", approver_role="owner",
    )
    assert (
        AuthorityApprovalLedger.get_approved(
            agency_id="agency_A", action="fulfill_accepted_proposal", subject_id=record.subject_id
        )
        is None
    )  # one leg is still not ratified
    AuthorityApprovalLedger.approve(
        agency_id="agency_A", approval_id=record.approval_id,
        approver_user_id="admin_2", approver_role="admin",
    )
    ratified = AuthorityApprovalLedger.get_approved(
        agency_id="agency_A", action="fulfill_accepted_proposal", subject_id=record.subject_id
    )
    assert ratified is not None
    assert ratified["approval_id"] == record.approval_id
    # Tenancy: another agency sees nothing.
    assert (
        AuthorityApprovalLedger.get_approved(
            agency_id="agency_B", action="fulfill_accepted_proposal", subject_id=record.subject_id
        )
        is None
    )


def test_deny_is_cas_and_terminal():
    record = _request()
    denied = AuthorityApprovalLedger.deny(
        agency_id="agency_A", approval_id=record.approval_id,
        approver_user_id="owner_1", approver_role="owner", reason="not justified",
    )
    assert denied.status == "denied"
    with pytest.raises(ApprovalConflict):
        AuthorityApprovalLedger.deny(
            agency_id="agency_A", approval_id=record.approval_id,
            approver_user_id="admin_2", approver_role="admin",
        )
    with pytest.raises(ApprovalConflict):
        AuthorityApprovalLedger.approve(
            agency_id="agency_A", approval_id=record.approval_id,
            approver_user_id="admin_2", approver_role="admin",
        )


# ---------------------------------------------------------------------------
# enforce_action_authority: distinct outcomes
# ---------------------------------------------------------------------------


def test_over_cap_raises_approval_required_not_denied():
    with pytest.raises(AuthorityApprovalRequired) as excinfo:
        enforce_action_authority("agent_strategy_01", "build_session_strategy", amount_usd=10000.01)
    assert excinfo.value.agent_id == "agent_strategy_01"
    assert excinfo.value.action == "build_session_strategy"
    assert excinfo.value.amount_usd == 10000.01
    assert excinfo.value.max_budget_impact == 10000.0
    # It must NOT be an AuthorityDenied subclass — gated engines that convert
    # AuthorityDenied to 403 must not swallow the approval-remediable outcome.
    assert not isinstance(excinfo.value, AuthorityDenied)


def test_unregistered_and_forbidden_remain_hard_denials():
    with pytest.raises(AuthorityDenied, match="not registered"):
        enforce_action_authority("agent_missing", "parse_freeform_text")
    with pytest.raises(AuthorityDenied, match="allowed_actions"):
        enforce_action_authority("agent_intake_01", "fulfill_accepted_proposal")


def test_ratified_authority_scope_elevates_then_restores():
    original = None
    from src.governance.registry import governance_registry

    original = governance_registry.get_agent("agent_strategy_01")
    with pytest.raises(AuthorityApprovalRequired):
        enforce_action_authority("agent_strategy_01", "build_session_strategy", amount_usd=20000.0)
    with ratified_authority_scope("agent_strategy_01", "build_session_strategy", 20000.0) as evidence:
        assert evidence["granted"] is True
    restored = governance_registry.get_agent("agent_strategy_01")
    assert restored.max_budget_impact == original.max_budget_impact
    # Cap is restored: over-cap raises again.
    with pytest.raises(AuthorityApprovalRequired):
        enforce_action_authority("agent_strategy_01", "build_session_strategy", amount_usd=20000.0)


# ---------------------------------------------------------------------------
# Boundaries endpoints: request → approve plumbing
# ---------------------------------------------------------------------------


def test_boundaries_approval_endpoints(session_client):
    agency = f"agency_appr_{uuid.uuid4().hex[:8]}"
    created = session_client.post(
        "/api/v1/boundaries/authority-approvals",
        json={
            "action": "authorize_advisor_payout",
            "subject_type": "payout",
            "subject_id": "adv_x:500000",
            "amount_usd": 5000.0,
            "reason": "Annual bonus payout",
        },
        headers={"X-Agency-ID": agency},
    )
    assert created.status_code == 200, created.text
    approval = created.json()
    assert approval["status"] == "pending_second"

    # First leg from the session principal (synthetic owner membership).
    first = session_client.post(
        f"/api/v1/boundaries/authority-approvals/{approval['approval_id']}/approve",
        json={},
        headers={"X-Agency-ID": agency},
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "pending_second"
    assert first.json()["first_approver_id"]

    # Same principal again → 409 (dual-control violation surfaces E2E).
    second = session_client.post(
        f"/api/v1/boundaries/authority-approvals/{approval['approval_id']}/approve",
        json={},
        headers={"X-Agency-ID": agency},
    )
    assert second.status_code == 409

    # Cross-agency visibility is refused (tenant scoping).
    missing = session_client.get(
        f"/api/v1/boundaries/authority-approvals/{approval['approval_id']}",
        headers={"X-Agency-ID": f"agency_other_{uuid.uuid4().hex[:6]}"},
    )
    assert missing.status_code == 404

    listing = session_client.get(
        "/api/v1/boundaries/authority-approvals",
        headers={"X-Agency-ID": agency},
    )
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1


# ---------------------------------------------------------------------------
# SQL backend round-trip (skips gracefully without live Postgres)
# ---------------------------------------------------------------------------


@pytest.mark.require_postgres
def test_sql_approval_roundtrip_cas_and_rls_posture(monkeypatch):
    monkeypatch.setenv("SPINE_API_AUTHORITY_APPROVAL_BACKEND", "sql")
    agency = f"agency_sql_appr_{uuid.uuid4().hex[:10]}"

    record = AuthorityApprovalLedger.request_approval(
        agency_id=agency,
        action="authorize_advisor_payout",
        subject_type="payout",
        subject_id="adv_sql:99000",
        requested_by="operator_sql",
        amount_usd=990.0,
        reason="SQL ledger round-trip",
    )
    d = record.to_dict()
    assert d["storage_backend"] == "sql"
    assert d["status"] == "pending_second"

    AuthorityApprovalLedger.approve(
        agency_id=agency, approval_id=record.approval_id,
        approver_user_id="owner_sql", approver_role="owner",
    )
    with pytest.raises(ApprovalConflict):
        AuthorityApprovalLedger.approve(
            agency_id=agency, approval_id=record.approval_id,
            approver_user_id="owner_sql", approver_role="owner",
        )
    ratified = AuthorityApprovalLedger.approve(
        agency_id=agency, approval_id=record.approval_id,
        approver_user_id="admin_sql", approver_role="admin",
    )
    assert ratified.status == "approved"

    fetched = AuthorityApprovalLedger.get_approved(
        agency_id=agency, action="authorize_advisor_payout", subject_id=d["subject_id"]
    )
    assert fetched is not None
    assert fetched["approval_id"] == record.approval_id
    # Tenancy: a foreign agency cannot resolve the approval.
    assert (
        AuthorityApprovalLedger.get_approved(
            agency_id=f"agency_other_{uuid.uuid4().hex[:6]}",
            action="authorize_advisor_payout",
            subject_id=d["subject_id"],
        )
        is None
    )


# ---------------------------------------------------------------------------
# Fulfillment router: over-cap 403 with approval recipe; ratified → proceeds
# ---------------------------------------------------------------------------


def _seed_trip_and_accept(cost: float = 90000.0):
    trip_id = f"trip_pa08w2_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": "system",
            "status": "assigned",
            "destination": "Paris",
            "packet": {"destination": "Paris", "start_date": "2026-10-15", "end_date": "2026-10-22"},
            "strategy": {
                "recommended_option": {"name": "Cap Buster", "cost": cost, "currency": "USD"}
            },
        },
        agency_id="system",
    )
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    accepted = accept_proposal(
        token=token,
        req=AcceptProposalRequest(
            signer_name="Big Spender", signer_email="big@spender.test", e_signature_consent=True
        ),
    )
    assert accepted.status == "accepted"
    return trip_id, token


@pytest.mark.asyncio
async def test_over_cap_fulfillment_403_carries_approval_recipe():
    trip_id, token = _seed_trip_and_accept()
    from src.orchestration.booking_fulfillment import BookingFulfillmentEngine

    with pytest.raises(AuthorityApprovalRequired) as excinfo:
        await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=trip_id, proposal_token=token, holder_id="test_advisor"
        )
    assert excinfo.value.action == "fulfill_accepted_proposal"
    assert excinfo.value.amount_usd == 90000.0
    # No VCC/GDS/JDG side effects reached the trip record.
    stored = TripStore.get_trip(trip_id)
    assert not stored.get("booking_confirmation")


def _pin_fulfillment_cap():
    """Shrink the fulfillment agent's cap below the fixture trip total so the
    over-cap path is deterministic regardless of the registry's defaults."""
    from src.governance.registry import governance_registry

    original = governance_registry.get_agent("agent_fulfillment_01")
    governance_registry.register(
        type(original)(
            agent_id=original.agent_id,
            role_name=original.role_name,
            tier=original.tier,
            allowed_actions=list(original.allowed_actions),
            max_budget_impact=1.0,
        )
    )
    return original


def _restore_fulfillment_cap(original):
    from src.governance.registry import governance_registry

    governance_registry.register(original)


def test_fulfillment_router_over_cap_403_contains_approval_required(session_client):
    trip_id, token = _seed_trip_and_accept()
    original = _pin_fulfillment_cap()
    try:
        response = session_client.post(
            "/api/v1/fulfillment/proposals/fulfill",
            json={"trip_id": trip_id, "proposal_token": token, "holder_id": "test_advisor"},
        )
    finally:
        _restore_fulfillment_cap(original)
    assert response.status_code == 403, response.text
    detail = response.json()["detail"]
    assert detail["error"] == "authority_denied"
    assert detail["escalation_required"] is True
    assert detail["approval_required"] is True
    assert detail["subject"] == {"type": "trip", "id": trip_id}
    assert detail["approval"]["action"] == "fulfill_accepted_proposal"
    assert detail["approval"]["subject_id"] == trip_id
    assert "how_to_ratify" in detail["approval"]
    # Denied pre-execution: no booking side effects.
    stored = TripStore.get_trip(trip_id)
    assert not stored.get("booking_confirmation")


def test_fulfillment_router_with_ratified_approval_proceeds(session_client):
    trip_id, token = _seed_trip_and_accept()

    # Ratify a dual-control approval for this exact subject (two distinct approvers).
    record = AuthorityApprovalLedger.request_approval(
        agency_id="system",
        action="fulfill_accepted_proposal",
        subject_type="trip",
        subject_id=trip_id,
        requested_by="operator_1",
        amount_usd=90000.0,
        reason="Board-approved VIP booking",
    )
    AuthorityApprovalLedger.approve(
        agency_id="system", approval_id=record.approval_id,
        approver_user_id="owner_1", approver_role="owner",
    )
    AuthorityApprovalLedger.approve(
        agency_id="system", approval_id=record.approval_id,
        approver_user_id="admin_2", approver_role="admin",
    )

    original = _pin_fulfillment_cap()
    try:
        response = session_client.post(
            "/api/v1/fulfillment/proposals/fulfill",
            json={"trip_id": trip_id, "proposal_token": token, "holder_id": "test_advisor"},
        )
    finally:
        _restore_fulfillment_cap(original)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["metadata"]["authority_approval_id"] == record.approval_id
    # The fulfillment actually executed (booking confirmation recorded).
    stored = TripStore.get_trip(trip_id)
    assert stored.get("booking_confirmation")
