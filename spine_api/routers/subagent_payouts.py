"""
spine_api/routers/subagent_payouts.py — Independent Contractor (IC) Advisor Commission Ledger & Payout Router.

Provides self-serve endpoints for independent contractor advisors to view commission statements,
track pending vs cleared balances, and authorize ACH direct deposit payouts.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Header

from spine_api.persistence import TEST_AGENCY_ID, AuditStore
from spine_api.services.commission_reconciliation import (
    AdvisorPayoutLedger,
    get_or_create_advisor_ledger,
    process_advisor_payout_authorization,
)

router = APIRouter(prefix="/api/v1/subagent-payouts", tags=["IC Advisor Payout Portal"])


class RequestPayoutBody(BaseModel):
    amount_cents: int
    payout_method: str = "DIRECT_DEPOSIT"  # DIRECT_DEPOSIT, ACH, STRIPE_CONNECT
    notes: Optional[str] = None


@router.get("/{advisor_id}/ledger", response_model=AdvisorPayoutLedger)
def get_advisor_ledger(
    advisor_id: str,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Retrieve commission statement, split breakdown, and payout balance for an IC advisor."""
    return get_or_create_advisor_ledger(advisor_id)


@router.post("/{advisor_id}/request-payout", response_model=AdvisorPayoutLedger)
def request_advisor_payout(
    advisor_id: str,
    body: RequestPayoutBody,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Authorize and initiate a payout transfer from cleared commission funds."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    updated = process_advisor_payout_authorization(
        advisor_id=advisor_id,
        amount_cents=body.amount_cents,
        method=body.payout_method,
    )

    AuditStore.log_event(
        event_type="advisor_payout_requested",
        user_id=agency_id,
        details={
            "advisor_id": advisor_id,
            "amount_cents": body.amount_cents,
            "method": body.payout_method,
            "remaining_pending_cents": updated.pending_payout_cents,
            "cleared_payout_cents": updated.cleared_payout_cents,
        },
    )

    return updated
