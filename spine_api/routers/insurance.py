"""
spine_api/routers/insurance.py — Travel Insurance & CFAR Sentinel Router.

Generates illustrative travel insurance & Cancel For Any Reason (CFAR) quote
options, preserves explicit policy-evidence uncertainty, and attaches insurance
policy coverage to trips.

Provenance rule: quotes are internally computed previews
(``reality_tier="deterministic_preview"``) and attached policies carry a
server-derived ``provider_source="agent_recorded"`` marker. No internal
formula or recorded policy may be attributed to a specific insurer (e.g.
Allianz) unless that insurer was explicitly named by the caller.
"""

from datetime import datetime, timezone
import logging
import math
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import (
    ROLE_PERMISSIONS,
    get_current_agency_id,
    get_current_membership,
    get_current_user,
)
from spine_api.models.tenant import Membership, User
from spine_api.persistence import AuditStore, TripStore
from spine_api.services import confirmation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/insurance", tags=["Travel Insurance & CFAR Sentinel"])


class InsuranceEvidence(BaseModel):
    """Minimal provenance for a quote assertion or deliberately unevaluated state."""

    policy_rule_status: str = "not_adopted"
    source: Optional[str] = None
    verification: str = "not_evaluated"
    deposit_date_utc: Optional[str] = None
    unresolved_predicates: List[str] = Field(
        default_factory=lambda: ["provider_rule", "plan_version", "coverage_facts"]
    )


class InsurancePlanOption(BaseModel):
    plan_id: str
    plan_name: str
    tier: str  # STANDARD, COMPREHENSIVE, CFAR_PREMIUM
    premium_usd: float
    trip_cancellation_coverage_pct: float
    emergency_medical_usd: float
    medical_evacuation_usd: float
    cfar_included: bool
    pre_existing_waiver_eligible: Optional[bool] = None
    pre_existing_waiver_status: str = "not_evaluated"
    eligibility_evidence: InsuranceEvidence
    estimated_agency_commission_usd: float


class InsuranceQuoteRequest(BaseModel):
    trip_id: Optional[str] = None
    total_trip_cost_usd: float
    traveler_ages: Optional[List[int]] = None
    destination_country: str = "IT"
    deposit_date: Optional[datetime] = None

    @field_validator("total_trip_cost_usd")
    @classmethod
    def validate_total_trip_cost(cls, value: float) -> float:
        if not math.isfinite(value) or value <= 0:
            raise ValueError("total_trip_cost_usd must be a finite positive number")
        return value

    @field_validator("total_trip_cost_usd", mode="before")
    @classmethod
    def reject_boolean_trip_cost(cls, value):
        if isinstance(value, bool):
            raise ValueError("total_trip_cost_usd must be a numeric amount")
        return value

    @field_validator("deposit_date", mode="before")
    @classmethod
    def parse_deposit_date(cls, value):
        if value is None or isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            raise ValueError("deposit_date must be an ISO-8601 datetime string")
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("deposit_date must be an ISO-8601 datetime string") from exc

    @field_validator("deposit_date")
    @classmethod
    def normalize_deposit_date(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("deposit_date must include a timezone offset")

        try:
            normalized = value.astimezone(timezone.utc)
        except (OverflowError, ValueError) as exc:
            raise ValueError("deposit_date is outside the supported UTC date range") from exc
        if normalized > datetime.now(timezone.utc):
            raise ValueError("deposit_date cannot be in the future")
        return normalized


class InsuranceQuoteResponse(BaseModel):
    ok: bool = True
    total_trip_cost_usd: float
    cfar_deadline: Optional[str] = None
    days_remaining_for_cfar: Optional[int] = None
    cfar_deadline_anchor: str = Field(
        "not_evaluated",
        description="No deadline is emitted until an adopted versioned policy rule and required evidence exist.",
    )
    cfar_timing_status: str = "not_evaluated"
    cfar_evidence: InsuranceEvidence = Field(default_factory=InsuranceEvidence)
    plans: List[InsurancePlanOption] = Field(default_factory=list)
    reality_tier: str = "deterministic_preview"
    provider_connected: bool = False
    carrier_confirmed: bool = False


class AttachPolicyRequest(BaseModel):
    trip_id: str
    selected_plan_id: str
    policy_number: str
    # No default: the insurer must be explicitly named by the caller. Fabricating
    # a vendor attribution (e.g. defaulting to "Allianz Global Assistance") would
    # present an internally recorded policy as carrier-issued coverage.
    insurance_provider: str = Field(..., min_length=1)
    premium_paid_usd: float

    @field_validator("insurance_provider")
    @classmethod
    def reject_blank_provider(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("insurance_provider must name the actual insurer explicitly")
        return value.strip()

    @field_validator("premium_paid_usd", mode="before")
    @classmethod
    def reject_boolean_premium(cls, value):
        # Booleans must not coerce into money (True -> 1.0), mirroring the
        # quote contract's explicit boolean rejection.
        if isinstance(value, bool):
            raise ValueError("premium_paid_usd must be a numeric amount")
        return value

    @field_validator("premium_paid_usd")
    @classmethod
    def validate_premium(cls, value: float) -> float:
        # Money recorded as evidence must be a real non-negative amount, mirroring
        # the quote contract's rejection of non-finite numbers.
        if not math.isfinite(value) or value < 0:
            raise ValueError("premium_paid_usd must be a finite non-negative number")
        return value


class AttachPolicyResponse(BaseModel):
    ok: bool = True
    trip_id: str
    policy_number: str
    plan_id: str
    attached_at: str
    # Provenance of the provider assertion: the policy was recorded by the
    # agent (not carrier-verified, not provider-connected). Server-derived;
    # clients cannot assert a stronger provenance than the system supports.
    provider_source: str = "agent_recorded"
    reality_tier: str = "deterministic_preview"
    provider_connected: bool = False
    carrier_confirmed: bool = False
    # F-31 (FND-0118) additive evidence fields:
    confirmation_id: Optional[str] = None
    actor_id: Optional[str] = None
    replayed: bool = False
    audit_recorded: bool = True


def _trip_assignee(trip: dict) -> Optional[str]:
    """Best-effort assignee identity on the trip record, for assigned-write checks."""
    for field_name in ("assigned_to", "assignee_id", "owner_id"):
        value = trip.get(field_name) if isinstance(trip, dict) else None
        if isinstance(value, str) and value.strip():
            return value
    return None


def _assert_attach_permission(membership: Membership, trip: dict, user_id: str) -> None:
    """F-31 action-permission contract: membership alone must not grant mutation.

    ``trips:write`` (or the wildcard) authorizes any tenant trip. The narrower
    ``trips:write:assigned`` capability authorizes only trips explicitly
    assigned to the caller — the broader permission must not silently absorb
    it, and viewers are rejected outright.
    """
    permissions = ROLE_PERMISSIONS.get(membership.role.lower(), [])
    if "*" in permissions or "trips:write" in permissions:
        return
    if "trips:write:assigned" in permissions:
        if _trip_assignee(trip) == user_id:
            return
        raise HTTPException(
            status_code=403,
            detail="Permission denied: trip not assigned to you",
        )
    raise HTTPException(
        status_code=403,
        detail="Permission denied: insurance policy attachment requires write access",
    )


@router.post("/quote", response_model=InsuranceQuoteResponse)
def generate_insurance_quotes(
    body: InsuranceQuoteRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Generate comprehensive travel insurance and CFAR quotes based on trip cost and traveler profile."""
    if body.trip_id and not TripStore.get_trip_for_agency(body.trip_id, agency_id):
        raise HTTPException(status_code=404, detail="Trip not found")

    cost = body.total_trip_cost_usd
    cfar_evidence = InsuranceEvidence(
        source="request.deposit_date" if body.deposit_date else None,
        verification="unverified" if body.deposit_date else "not_available",
        deposit_date_utc=body.deposit_date.isoformat() if body.deposit_date else None,
    )
    eligibility_evidence = InsuranceEvidence(
        source="request.deposit_date" if body.deposit_date else None,
        verification="unverified" if body.deposit_date else "not_available",
        deposit_date_utc=body.deposit_date.isoformat() if body.deposit_date else None,
    )

    plans: List[InsurancePlanOption] = [
        InsurancePlanOption(
            plan_id="ins_std_01",
            plan_name="Classic Post-Departure & Medical",
            tier="STANDARD",
            premium_usd=round(cost * 0.045, 2),
            trip_cancellation_coverage_pct=100.0,
            emergency_medical_usd=50000.0,
            medical_evacuation_usd=250000.0,
            cfar_included=False,
            pre_existing_waiver_eligible=None,
            pre_existing_waiver_status="not_evaluated",
            eligibility_evidence=eligibility_evidence,
            estimated_agency_commission_usd=round(cost * 0.045 * 0.30, 2),  # 30% commission
        ),
        InsurancePlanOption(
            plan_id="ins_comp_02",
            plan_name="Comprehensive Deluxe Travel Protection",
            tier="COMPREHENSIVE",
            premium_usd=round(cost * 0.075, 2),
            trip_cancellation_coverage_pct=100.0,
            emergency_medical_usd=100000.0,
            medical_evacuation_usd=500000.0,
            cfar_included=False,
            pre_existing_waiver_eligible=None,
            pre_existing_waiver_status="not_evaluated",
            eligibility_evidence=eligibility_evidence,
            estimated_agency_commission_usd=round(cost * 0.075 * 0.30, 2),
        ),
        InsurancePlanOption(
            plan_id="ins_cfar_03",
            plan_name="Cancel For Any Reason (CFAR) Platinum",
            tier="CFAR_PREMIUM",
            premium_usd=round(cost * 0.115, 2),
            trip_cancellation_coverage_pct=100.0,
            emergency_medical_usd=250000.0,
            medical_evacuation_usd=1000000.0,
            cfar_included=True,
            pre_existing_waiver_eligible=None,
            pre_existing_waiver_status="not_evaluated",
            eligibility_evidence=eligibility_evidence,
            estimated_agency_commission_usd=round(cost * 0.115 * 0.35, 2),  # 35% commission
        ),
    ]

    return InsuranceQuoteResponse(
        ok=True,
        total_trip_cost_usd=cost,
        cfar_deadline=None,
        days_remaining_for_cfar=None,
        cfar_deadline_anchor="not_evaluated",
        cfar_timing_status="not_evaluated",
        cfar_evidence=cfar_evidence,
        plans=plans,
        reality_tier="deterministic_preview",
        provider_connected=False,
        carrier_confirmed=False,
    )


@router.post("/{trip_id}/attach-policy", response_model=AttachPolicyResponse)
async def attach_insurance_policy_to_trip(
    trip_id: str,
    body: AttachPolicyRequest,
    agency_id: str = Depends(get_current_agency_id),
    user: User = Depends(get_current_user),
    membership: Membership = Depends(get_current_membership),
):
    """Attach confirmed insurance policy to trip booking and record coverage audit event.

    F-31 (FND-0118) evidence migration: this handler is now an adapter to the
    canonical ``insurance`` ``BookingConfirmation`` lifecycle —

    - the durable authority is the canonical SQL row (encrypted private
      fields), committed atomically with its required execution events;
    - a deterministic confirmation key replays the recorded outcome instead of
      double-attaching, and a second active policy for the trip is a
      deliberate 409 (immutable-create contract backed by
      ``uq_bc_trip_type_active``);
    - the actor is the authenticated principal (``user.id``); the agency is a
      separate tenant dimension, never the audit actor;
    - the legacy ``trip["insurance_policy"]`` blob is preserved as a projection
      (the F-31 design keeps it until field-by-field salvage/migration is
      verified) and the audit event is written strictly AFTER the durable
      commit — audit failure never rolls back the save but is surfaced on the
      response.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Action permission BEFORE any mutation (viewer denial, assigned-junior
    # rights stay explicit).
    _assert_attach_permission(membership, trip, user.id)

    try:
        outcome = await confirmation_service.attach_insurance_confirmation(
            agency_id=agency_id,
            trip_id=trip_id,
            actor_id=user.id,
            insurance_provider=body.insurance_provider,
            policy_number=body.policy_number,
            selected_plan_id=body.selected_plan_id,
            premium_paid_usd=body.premium_paid_usd,
        )
    except confirmation_service.ConfirmationAttachConflict as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "reason": str(exc),
                "existing_confirmation_id": exc.existing_confirmation_id,
            },
        )
    except confirmation_service.ConfirmationAttachUnavailable as exc:
        # Fail closed: no successful response without durable required evidence.
        raise HTTPException(status_code=503, detail=str(exc))

    confirmation_id = outcome.get("confirmation_id")
    replayed = bool(outcome.get("replayed"))
    attached_at = outcome.get("recorded_at") or datetime.now(timezone.utc).isoformat()

    # Legacy trip policy projection (NOT the authority). Skipped on replay: a
    # replay must re-record nothing, not even projections.
    if not replayed:
        trip["insurance_policy"] = {
            "policy_number": body.policy_number,
            "plan_id": body.selected_plan_id,
            "provider": body.insurance_provider,
            "provider_source": "agent_recorded",
            "premium_paid_usd": body.premium_paid_usd,
            "attached_at": attached_at,
            "carrier_confirmed": False,
            "reality_tier": "deterministic_preview",
            "provider_connected": False,
            "confirmation_id": confirmation_id,
        }
        TripStore.save_trip(trip, agency_id=agency_id)

    # Audit strictly AFTER the durable commit. The event attributes the action
    # to the authenticated principal and keeps agency as a tenant dimension.
    # Policy/customer secrets stay out of general logs: the policy number is
    # referenced through the canonical confirmation row, never copied here.
    audit_recorded = True
    try:
        AuditStore.log_event(
            event_type=(
                "insurance_policy_attach_replayed" if replayed else "insurance_policy_attached"
            ),
            user_id=user.id,
            details={
                "agency_id": agency_id,
                "trip_id": trip_id,
                "confirmation_id": confirmation_id,
                "plan_id": body.selected_plan_id,
                "provider": body.insurance_provider,
                "provider_source": "agent_recorded",
                "premium_paid_usd": body.premium_paid_usd,
                "has_policy_number": True,
                "replayed": replayed,
            },
        )
    except Exception as exc:
        # Surfaced, never fatal: the save is already durable.
        audit_recorded = False
        logger.warning(
            "insurance attach audit failed after durable commit (trip=%s, confirmation=%s): %s",
            trip_id,
            confirmation_id,
            exc,
        )

    return AttachPolicyResponse(
        ok=True,
        trip_id=trip_id,
        policy_number=body.policy_number,
        plan_id=body.selected_plan_id,
        attached_at=attached_at,
        provider_source="agent_recorded",
        reality_tier="deterministic_preview",
        provider_connected=False,
        carrier_confirmed=False,
        confirmation_id=confirmation_id,
        actor_id=user.id,
        replayed=replayed,
        audit_recorded=audit_recorded,
    )
