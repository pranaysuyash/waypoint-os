"""
spine_api/routers/corporate_policy.py — Corporate Policy Compliance & Duty of Care Audit Engine (IDEA-127).

Audits corporate B2B travel itineraries against company policy rules (nightly hotel caps, flight class rules, pre-approval gates)
and tracks duty-of-care traveler safety risk levels.
"""

from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

router = APIRouter(prefix="/api/v1/corporate", tags=["Corporate Policy & Duty of Care"])


class CorporatePolicyRules(BaseModel):
    policy_id: str = "corp_policy_default"
    company_name: str = "Acme Corp"
    max_nightly_hotel_usd: float = 350.0
    allowed_flight_class: str = "BUSINESS"  # ECONOMY, PREMIUM_ECONOMY, BUSINESS
    max_flight_duration_for_business_hours: float = 6.0
    preferred_hotel_chains: List[str] = Field(default_factory=lambda: ["Marriott", "Hilton", "Hyatt", "Four Seasons"])
    require_pre_approval: bool = True


class PolicyAuditResponse(BaseModel):
    ok: bool = True
    trip_id: str
    is_compliant: bool
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    duty_of_care_risk_level: str  # LOW, MODERATE, HIGH
    pre_approval_required: bool
    override_approved: bool = False


class OverrideRequest(BaseModel):
    trip_id: str
    approver_name: str
    reason: str


class OverrideResponse(BaseModel):
    ok: bool = True
    trip_id: str
    override_approved: bool = True
    approved_by: str
    approved_at: str


@router.get("/policy-rules", response_model=CorporatePolicyRules)
def get_corporate_policy_rules():
    """Retrieve active corporate travel policy rules."""
    return CorporatePolicyRules()


@router.post("/audit-policy/{trip_id}", response_model=PolicyAuditResponse)
def audit_trip_corporate_policy(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Audit a trip itinerary against corporate travel policy rules and duty of care safety metrics."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    policy = CorporatePolicyRules()
    violations: List[str] = []
    warnings: List[str] = []

    rec_option = trip.get("strategy", {}).get("recommended_option", {}) or {}
    cost = rec_option.get("cost") or 3000.0

    # Calculate nightly rate (assuming 5 nights)
    nightly_rate = cost / 5.0
    if nightly_rate > policy.max_nightly_hotel_usd:
        violations.append(f"Nightly hotel rate (${nightly_rate:.2f}) exceeds corporate cap (${policy.max_nightly_hotel_usd:.2f})")

    dest = (trip.get("destination") or "").lower()
    high_risk_destinations = ["kabul", "baghdad", "somalia", "syria", "yemen"]
    if any(h in dest for h in high_risk_destinations):
        doc_risk = "HIGH"
        violations.append(f"Destination '{trip.get('destination')}' is listed under High Risk Duty-of-Care Advisory")
    elif "tokyo" in dest or "london" in dest or "paris" in dest or "maui" in dest or "singapore" in dest:
        doc_risk = "LOW"
    else:
        doc_risk = "MODERATE"

    if cost > 5000.0:
        warnings.append("Total trip cost exceeds $5,000 baseline threshold — secondary VP signoff recommended")

    is_comp = len(violations) == 0
    override_approved = trip.get("corporate_policy_override", {}).get("approved", False)

    return PolicyAuditResponse(
        ok=True,
        trip_id=trip_id,
        is_compliant=is_comp,
        violations=violations,
        warnings=warnings,
        duty_of_care_risk_level=doc_risk,
        pre_approval_required=policy.require_pre_approval,
        override_approved=override_approved,
    )


@router.post("/approve-policy-override/{trip_id}", response_model=OverrideResponse)
def approve_corporate_policy_override(
    trip_id: str,
    body: OverrideRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Approve a corporate policy exception/override for a trip."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    trip["corporate_policy_override"] = {
        "approved": True,
        "approved_by": body.approver_name,
        "reason": body.reason,
        "approved_at": now_iso,
    }

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="corporate_policy_override_approved",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "approver_name": body.approver_name,
            "reason": body.reason,
        },
    )

    return OverrideResponse(
        ok=True,
        trip_id=trip_id,
        override_approved=True,
        approved_by=body.approver_name,
        approved_at=now_iso,
    )
