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
FND-0221: every payout is ALSO gated by a payment authorization mandate —
an active, unexpired, payout-scope mandate for the same agency (+ trip when
the payout is trip-linked) must cover the amount BEFORE the ledger moves;
absent/insufficient mandates refuse with the typed
``payment_mandate_required`` / ``payment_mandate_refused`` errors and an
audit event records the mandate id + principal at the seam. A payout retry
with the same request id executes once (mandate movement idempotency).
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
from spine_api.services.payment_mandate_service import PaymentMandateLedger
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

# FND-0221: how to obtain the payer-authorization artifact this seam requires.
_HOW_TO_MANDATE = (
    "Grant a payout-scope payment mandate via POST /api/v1/financial-ops/payment-mandates "
    "(scope='payout', trip_id=<trip>, evidence_ref=<proposal/approval artifact>, payer_ref=<granting "
    "principal>), then retry this payout with mandate_id or the same trip_id."
)


def _mandate_refusal(
    error: str,
    message: str,
    *,
    agency_id: str,
    advisor_id: str,
    amount_cents: int,
    trip_id: Optional[str],
    mandate_id: Optional[str] = None,
    reason: Optional[str] = None,
) -> HTTPException:
    """Typed FND-0221 refusal (403) — also audited so refusals are provable."""
    detail: Dict[str, Any] = {
        "error": error,
        "escalation_required": True,
        "mandate_scope": "payout",
        "advisor_id": advisor_id,
        "amount_cents": amount_cents,
        "trip_id": trip_id,
        "message": message,
    }
    if mandate_id:
        detail["mandate_id"] = mandate_id
    if reason:
        detail["reason"] = reason
    detail["how_to_mandate"] = _HOW_TO_MANDATE
    AuditStore.log_event(
        "advisor_payout_mandate_refused",
        agency_id,
        {
            "error": error,
            "advisor_id": advisor_id,
            "amount_cents": amount_cents,
            "trip_id": trip_id,
            "mandate_id": mandate_id,
            "refusal_reason": reason or message,
        },
    )
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _enforce_payout_mandate(
    *,
    agency_id: str,
    advisor_id: str,
    amount_cents: int,
    trip_id: Optional[str],
    mandate_id: Optional[str],
    movement_idempotency_key: str,
    money_mode: str,
) -> Dict[str, Any]:
    """FND-0221 seam gate: require an active payout mandate BEFORE the ledger moves.

    Composition with ADR-008 (they gate different questions): money_execution_mode
    gates WHO may trigger the movement; the mandate gates WHETHER this specific
    movement is authorized by a payer consent artifact. Mirrors the fulfillment
    seam posture: required under fully_human/hybrid (default), recorded-if-present
    under fully_autonomous.

    Returns the mandate authorization outcome (``replayed: True`` when the
    movement idempotency key has already executed — callers must NOT move
    money again). Raises the typed 403 refusals otherwise.
    """
    resolution = "explicit" if mandate_id else ("trip" if trip_id else None)

    if resolution is None:
        if money_mode == "fully_autonomous":
            # Agency ratified autonomous movement; no mandate exists to chain.
            return {"authorized": True, "mandate_id": None, "enforced": False}
        raise _mandate_refusal(
            "payment_mandate_required",
            (
                f"No payment mandate can be resolved for advisor payout '{advisor_id}' "
                f"({amount_cents} cents, agency '{agency_id}'): pass mandate_id or trip_id "
                "so the movement chains to a payer authorization artifact (FND-0221)."
            ),
            agency_id=agency_id,
            advisor_id=advisor_id,
            amount_cents=amount_cents,
            trip_id=trip_id,
        )

    if resolution == "explicit":
        mandate = PaymentMandateLedger.get_mandate(agency_id=agency_id, mandate_id=mandate_id or "")
        if mandate is None:
            # get_mandate is agency-scoped: a foreign-agency id reads as absent.
            raise _mandate_refusal(
                "payment_mandate_required",
                f"Payment mandate '{mandate_id}' was not found for agency '{agency_id}' "
                "(or belongs to another agency). No mandate, no movement (FND-0221).",
                agency_id=agency_id,
                advisor_id=advisor_id,
                amount_cents=amount_cents,
                trip_id=trip_id,
                mandate_id=mandate_id,
            )
        # Wrong trip: an explicit mandate must cover THIS payout's trip when linked.
        if trip_id and mandate.get("trip_id") != trip_id:
            raise _mandate_refusal(
                "payment_mandate_required",
                (
                    f"Payment mandate '{mandate_id}' covers trip '{mandate.get('trip_id')}', "
                    f"not trip '{trip_id}'. A mandate must match the movement's agency AND "
                    "trip (FND-0221)."
                ),
                agency_id=agency_id,
                advisor_id=advisor_id,
                amount_cents=amount_cents,
                trip_id=trip_id,
                mandate_id=mandate_id,
            )
    else:
        mandate_record = PaymentMandateLedger.resolve_for_trip(
            agency_id=agency_id, trip_id=trip_id or "", allowed_scopes=("payout",)
        )
        if mandate_record is None:
            raise _mandate_refusal(
                "payment_mandate_required",
                (
                    f"No active payout-scope payment mandate exists for trip '{trip_id}' "
                    f"(agency '{agency_id}'). Advisor payouts move agency money and require "
                    "a payer authorization artifact (FND-0221)."
                ),
                agency_id=agency_id,
                advisor_id=advisor_id,
                amount_cents=amount_cents,
                trip_id=trip_id,
            )
        mandate = mandate_record.to_dict()
        mandate_id = mandate["mandate_id"]

    authz = PaymentMandateLedger.authorize_charge(
        agency_id=agency_id,
        mandate_id=mandate_id or "",
        amount_cents=amount_cents,
        scope="payout",
        movement_idempotency_key=movement_idempotency_key,
    )
    if not authz.get("authorized"):
        raise _mandate_refusal(
            "payment_mandate_refused",
            (
                f"Payment mandate '{mandate_id}' does not authorize this payout: "
                f"{authz.get('reason')} The payer's consent must not be exceeded "
                "(FND-0221)."
            ),
            agency_id=agency_id,
            advisor_id=advisor_id,
            amount_cents=amount_cents,
            trip_id=trip_id,
            mandate_id=mandate_id,
            reason=authz.get("reason"),
        )
    # FND-0221: the mandate's payer_ref is the authenticated principal whose
    # consent authorizes this movement — travels to the seam audit event.
    authz["payer_ref"] = mandate.get("payer_ref") or mandate.get("granted_by") or ""
    authz["evidence_ref"] = mandate.get("evidence_ref") or mandate.get("consent_artifact_ref") or ""
    authz["enforced"] = True
    return authz


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
    # FND-0221: the payout authorization mandate. Either pass an explicit
    # ``mandate_id`` or a ``trip_id`` so the payout-scope mandate can be
    # resolved for that trip; one of them is required before money moves
    # (unless the agency runs fully_autonomous, where a present mandate is
    # still consumed + audited but not required).
    mandate_id: Optional[str] = Field(
        None, description="Explicit payout-scope payment mandate id (FND-0221)."
    )
    idempotency_key: Optional[str] = Field(
        None,
        description=(
            "Movement idempotency key (FND-0221). Defaults to 'payout:<request_id>' — "
            "a retry with the same request id executes once, never a double movement."
        ),
    )


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

    # ADR-008 item 1 (Addendum 9 amendment): payouts read the agency
    # money_execution_mode — under fully_human, an automated payout identity
    # is refused; only an authenticated advisor-initiated payout proceeds.
    from src.intake.config.agency_settings import AgencySettingsStore

    payout_mode = AgencySettingsStore.load(agency_id).autonomy.money_execution_mode
    if payout_mode == "fully_human" and str(advisor_id) in (
        "system", "auto_payout", "fulfillment_agent",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "money_execution_mode_refusal",
                "escalation_required": True,
                "money_execution_mode": "fully_human",
                "message": (
                    f"Agency '{agency_id}' operates under 'fully_human' money "
                    "execution mode (ADR-008): payouts require an authenticated "
                    "human advisor as the approving principal."
                ),
            },
        )

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

    # FND-0221: payer-authorization mandate gate BEFORE any ledger mutation.
    # The movement idempotency key defaults to the payout request id, so the
    # documented "retry with the same request_id" path executes exactly once.
    movement_key = body.idempotency_key or f"payout:{subject_id}"
    mandate_authz = _enforce_payout_mandate(
        agency_id=agency_id,
        advisor_id=advisor_id,
        amount_cents=body.amount_cents,
        trip_id=body.trip_id,
        mandate_id=body.mandate_id,
        movement_idempotency_key=movement_key,
        money_mode=payout_mode,
    )
    if mandate_authz.get("replayed"):
        # Same idempotency key → same outcome: the first execution already
        # moved (or refused) this movement. Never move again.
        replay_ledger = get_or_create_advisor_ledger(advisor_id, agency_id=agency_id)
        AuditStore.log_event(
            "advisor_payout_replayed",
            agency_id,
            {
                "advisor_id": advisor_id,
                "amount_cents": body.amount_cents,
                "movement_idempotency_key": movement_key,
                "mandate_id": mandate_authz.get("mandate_id"),
                "payer_ref": mandate_authz.get("payer_ref"),
                "payout_request_subject_id": subject_id,
                "trip_id": body.trip_id,
            },
        )
        return replay_ledger

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
            # FND-0221: mandate id + granting principal chained to the movement.
            "mandate_id": mandate_authz.get("mandate_id"),
            "mandate_enforced": mandate_authz.get("enforced", False),
            "mandate_scope": "payout",
            "mandate_payer_ref": mandate_authz.get("payer_ref"),
            "mandate_evidence_ref": mandate_authz.get("evidence_ref"),
            "movement_idempotency_key": movement_key,
            "money_execution_mode": payout_mode,
        },
    )

    return updated
