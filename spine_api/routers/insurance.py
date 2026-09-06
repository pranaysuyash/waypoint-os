"""
spine_api/routers/insurance.py — Travel Insurance & CFAR Sentinel Router.

Generates comprehensive travel insurance & Cancel For Any Reason (CFAR) quotes,
tracks 14-day pre-existing condition waiver deadlines from deposit confirmation,
and attaches insurance policy coverage to trips.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

router = APIRouter(prefix="/api/v1/insurance", tags=["Travel Insurance & CFAR Sentinel"])


class InsurancePlanOption(BaseModel):
    plan_id: str
    plan_name: str
    tier: str  # STANDARD, COMPREHENSIVE, CFAR_PREMIUM
    premium_usd: float
    trip_cancellation_coverage_pct: float
    emergency_medical_usd: float
    medical_evacuation_usd: float
    cfar_included: bool
    pre_existing_waiver_eligible: bool
    estimated_agency_commission_usd: float


class InsuranceQuoteRequest(BaseModel):
    trip_id: Optional[str] = None
    total_trip_cost_usd: float
    traveler_ages: List[int] = Field(default_factory=lambda: [35, 38])
    destination_country: str = "IT"
    deposit_date: Optional[str] = None


class InsuranceQuoteResponse(BaseModel):
    ok: bool = True
    total_trip_cost_usd: float
    cfar_deadline: str
    days_remaining_for_cfar: int
    cfar_deadline_anchor: str = Field(
        "quote_time",
        description="'deposit_date' when the CFAR 14-day window anchors to the supplied deposit, else 'quote_time' (no deposit recorded).",
    )
    plans: List[InsurancePlanOption] = Field(default_factory=list)


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


@router.post("/quote", response_model=InsuranceQuoteResponse)
def generate_insurance_quotes(
    body: InsuranceQuoteRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Generate comprehensive travel insurance and CFAR quotes based on trip cost and traveler profile."""
    cost = max(500.0, body.total_trip_cost_usd)
    now = datetime.now(timezone.utc)

    # CFAR pre-existing-condition waiver is 14 days FROM DEPOSIT (F-31): when a
    # deposit date is supplied it anchors the window; quote time is the honest
    # fallback only when no deposit has been recorded. days_remaining is real
    # remaining time (>=0), not a constant 14.
    anchor_name = "quote_time"
    anchor_dt = now
    if body.deposit_date:
        try:
            parsed_deposit = datetime.fromisoformat(body.deposit_date.replace("Z", "+00:00"))
            if parsed_deposit.tzinfo is None:
                parsed_deposit = parsed_deposit.replace(tzinfo=timezone.utc)
            anchor_dt = parsed_deposit
            anchor_name = "deposit_date"
        except (ValueError, TypeError):
            # Unparseable deposit date: fall back to quote time rather than
            # silently presenting a window the traveler may not have.
            anchor_name = "quote_time"
            anchor_dt = now
    cfar_deadline = (anchor_dt + timedelta(days=14)).isoformat()
    # Date-based remaining days: stable within the anchor day (a window opened
    # today reports 14, not 13.99 floored to 13).
    days_remaining = max(0, ((anchor_dt + timedelta(days=14)).date() - now.date()).days)

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
            pre_existing_waiver_eligible=True,
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
            pre_existing_waiver_eligible=True,
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
            pre_existing_waiver_eligible=True,
            estimated_agency_commission_usd=round(cost * 0.115 * 0.35, 2),  # 35% commission
        ),
    ]

    return InsuranceQuoteResponse(
        ok=True,
        total_trip_cost_usd=cost,
        cfar_deadline=cfar_deadline,
        days_remaining_for_cfar=days_remaining,
        cfar_deadline_anchor=anchor_name,
        plans=plans,
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
    )
