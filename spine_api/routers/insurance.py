"""
spine_api/routers/insurance.py — Travel Insurance & CFAR Sentinel Router.

Generates illustrative travel insurance & Cancel For Any Reason (CFAR) quote
options, preserves explicit policy-evidence uncertainty, and attaches insurance
policy coverage to trips.
"""

from datetime import datetime, timezone
import math
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

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
    insurance_provider: str = "Allianz Global Assistance"
    premium_paid_usd: float


class AttachPolicyResponse(BaseModel):
    ok: bool = True
    trip_id: str
    policy_number: str
    plan_id: str
    attached_at: str
    reality_tier: str = "deterministic_preview"
    provider_connected: bool = False
    carrier_confirmed: bool = False


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
def attach_insurance_policy_to_trip(
    trip_id: str,
    body: AttachPolicyRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Attach confirmed insurance policy to trip booking and record coverage audit event."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    trip["insurance_policy"] = {
        "policy_number": body.policy_number,
        "plan_id": body.selected_plan_id,
        "provider": body.insurance_provider,
        "premium_paid_usd": body.premium_paid_usd,
        "attached_at": now_iso,
        "carrier_confirmed": False,
        "reality_tier": "deterministic_preview",
        "provider_connected": False,
    }

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="insurance_policy_attached",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "policy_number": body.policy_number,
            "plan_id": body.selected_plan_id,
            "provider": body.insurance_provider,
            "premium_paid_usd": body.premium_paid_usd,
        },
    )

    return AttachPolicyResponse(
        ok=True,
        trip_id=trip_id,
        policy_number=body.policy_number,
        plan_id=body.selected_plan_id,
        attached_at=now_iso,
        reality_tier="deterministic_preview",
        provider_connected=False,
        carrier_confirmed=False,
    )
