"""
spine_api/routers/subagent_payouts.py — Independent Contractor (IC) Advisor Commission Ledger & Payout Router.

Provides self-serve endpoints for independent contractor advisors to view commission statements,
track pending vs cleared balances, and authorize ACH direct deposit payouts.

PA-08: payout authorization is gated by the governance registry before any
ledger mutation. PA-08 wave 2: an over-cap payout is approval-remediable —
a ratified dual-control approval for (action="authorize_advisor_payout",
subject_id=<payout request id>) bypasses the cap (the approval IS the
authority); without one the endpoint returns 403 with ``approval_required``
and the exact subject ids an operator needs to ratify.
PA-23: payouts write through the durable payout store (SQL when the SQL
backend is active — the SQL ledger starts at true zero and is never seeded;
memory fallback for tests/preview), and settlement reconciliation links
booking totals to recorded payouts via ``reconcile_trip_commission``.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore
from spine_api.services.authority_approval_service import AuthorityApprovalLedger
from spine_api.services.commission_reconciliation import (
    AdvisorPayoutLedger,
    get_or_create_advisor_ledger,
    process_advisor_payout_authorization,
    reconcile_trip_commission,
)
from src.governance.registry import (
    AuthorityApprovalRequired,
    AuthorityDenied,
    enforce_action_authority,
)

router = APIRouter(prefix="/api/v1/subagent-payouts", tags=["IC Advisor Payout Portal"])

# PA-08: the payout execution identity in the governance registry. Its
# registration carries a conservative max_budget_impact ($2,000) and the
# allowlisted action below; exceeding it fails closed with an
# escalation-required denial.
_PAYOUT_AGENT_ID = "advisor_payout"
_PAYOUT_ACTION = "authorize_advisor_payout"

_HOW_TO_RATIFY = (
    "Request a dual-control approval via POST /api/v1/boundaries/authority-approvals "
    "(action='authorize_advisor_payout', subject_type='payout', subject_id=<payout request id>, "
    "amount_usd), then collect two DISTINCT owner/admin approvals via "
    "POST /api/v1/boundaries/authority-approvals/{approval_id}/approve. Once ratified, "
    "retry this payout with the same request_id."
)


class RequestPayoutBody(BaseModel):
    amount_cents: int
    payout_method: str = "DIRECT_DEPOSIT"  # DIRECT_DEPOSIT, ACH, STRIPE_CONNECT
    notes: Optional[str] = None
    # PA-08 wave 2 / PA-23: stable subject id for the dual-control approval and
    # an optional trip link for settlement reconciliation. Additive fields.
    request_id: Optional[str] = Field(
        None, description="Stable payout request id — the approval subject_id. Derived when omitted."
    )
    trip_id: Optional[str] = Field(None, description="Optional trip link for settlement reconciliation")


@router.get("/{advisor_id}/ledger", response_model=AdvisorPayoutLedger)
def get_advisor_ledger(
    advisor_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Retrieve commission statement, split breakdown, and payout balance for an IC advisor."""
    return get_or_create_advisor_ledger(advisor_id, agency_id=agency_id)


@router.get("/reconciliation/{trip_id}")
def get_trip_commission_reconciliation(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Reconcile a trip's booking total against recorded advisor payouts (PA-23).

    Reports expected vs recorded commission with real delta math. A mismatch
    is reported for operator review — never auto-fixed.
    """
    return reconcile_trip_commission(trip_id=trip_id, agency_id=agency_id)


@router.post("/{advisor_id}/request-payout", response_model=AdvisorPayoutLedger)
def request_advisor_payout(
    advisor_id: str,
    body: RequestPayoutBody,
    agency_id: str = Depends(get_current_agency_id),
):
    """Authorize and initiate a payout transfer from cleared commission funds."""
    subject_id = body.request_id or f"{advisor_id}:{body.amount_cents}"

    # PA-08: enforce registry authority BEFORE recording any ledger movement.
    authority: Dict[str, Any]
    try:
        authority = dict(
            enforce_action_authority(
                _PAYOUT_AGENT_ID,
                _PAYOUT_ACTION,
                amount_usd=body.amount_cents / 100.0,
            )
        )
    except AuthorityApprovalRequired as exc:
        # Over-cap: a ratified dual-control approval for this exact payout
        # request IS the authority; without one, fail closed with the
        # ratification recipe.
        ratified = AuthorityApprovalLedger.get_approved(
            agency_id=agency_id,
            action=_PAYOUT_ACTION,
            subject_id=subject_id,
        )
        if ratified is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "authority_denied",
                    "escalation_required": True,
                    "approval_required": True,
                    "agent": exc.agent_id,
                    "action": exc.action,
                    "amount_usd": exc.amount_usd,
                    "subject": {"type": "payout", "id": subject_id},
                    "reason": exc.reason,
                    "message": (
                        "Payout authorization was denied by the governance registry. "
                        "The requested amount exceeds this payout identity's budget "
                        "authority; a ratified dual-control approval is required."
                    ),
                    "approval": {
                        "action": _PAYOUT_ACTION,
                        "subject_type": "payout",
                        "subject_id": subject_id,
                        "amount_usd": exc.amount_usd,
                        "how_to_ratify": _HOW_TO_RATIFY,
                    },
                },
            ) from exc
        authority = {
            "granted": True,
            "ratified_bypass": True,
            "authority_approval_id": ratified["approval_id"],
            "agent": exc.agent_id,
            "action": exc.action,
            "checked_amount_usd": exc.amount_usd,
            "max_budget_impact": exc.max_budget_impact,
        }
    except AuthorityDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "authority_denied",
                "escalation_required": True,
                "agent": exc.agent_id,
                "action": exc.action,
                "reason": exc.reason,
                "message": (
                    "Payout authorization was denied by the governance registry. "
                    "The payout identity or action is not authorized; escalate "
                    "to a human operator."
                ),
            },
        ) from exc

    updated = process_advisor_payout_authorization(
        advisor_id=advisor_id,
        amount_cents=body.amount_cents,
        method=body.payout_method,
        agency_id=agency_id,
        recorded_by=subject_id,
        trip_id=body.trip_id,
        note=body.notes,
        authority_approval_id=authority.get("authority_approval_id"),
    )

    AuditStore.log_event(
        event_type="advisor_payout_requested",
        user_id=agency_id,
        details={
            "advisor_id": advisor_id,
            "amount_cents": body.amount_cents,
            "method": body.payout_method,
            "payout_request_subject_id": subject_id,
            "trip_id": body.trip_id,
            "remaining_pending_cents": updated.pending_payout_cents,
            "cleared_payout_cents": updated.cleared_payout_cents,
            "authority": authority,
            "ledger_backend": updated.storage_backend,
        },
    )

    return updated
