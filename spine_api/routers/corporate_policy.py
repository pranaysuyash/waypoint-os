"""
spine_api/routers/corporate_policy.py — Corporate Policy Compliance & Duty of Care Audit Engine (IDEA-127).

Audits corporate B2B travel itineraries against company policy rules (nightly hotel caps, flight class rules, pre-approval gates)
and tracks duty-of-care traveler safety risk levels.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id, get_current_membership, get_current_user
from spine_api.models.tenant import Membership, User
from spine_api.persistence import AuditStore, TripStore

router = APIRouter(prefix="/api/v1/corporate", tags=["Corporate Policy & Duty of Care"])

# PA-26: policy overrides are an authority action. Only agency owners/admins
# may act as approvers, and the approver identity is the authenticated
# principal — never client-supplied free text.
_OVERRIDE_APPROVER_ROLES = frozenset({"owner", "admin"})


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
    duty_of_care_risk_level: str  # LOW, MODERATE, HIGH, UNKNOWN
    pre_approval_required: bool
    override_approved: bool = False
    cost_evaluated: float = 0.0
    cost_source: str = "recommended_option"
    nights_evaluated: int = 5
    nights_source: str = "itinerary_dates"
    authority: str = "corporate_policy_v1"
    # FND-0338 / roadmap invariant 3: machine-readable basis per violation —
    # the input provenance (sourced vs estimated) travels WITH each finding so
    # consumers can never mistake an estimate-derived flag for sourced data.
    # Values mix strings (rule/basis) and booleans (enforceable).
    violations_detail: List[Dict[str, Any]] = Field(default_factory=list)


class OverrideRequest(BaseModel):
    trip_id: str
    # PA-26: the approver identity is derived from the authenticated
    # principal. This field is retained for client compatibility but is
    # IGNORED — a free-text approver name is self-certifying and is no longer
    # trusted as evidence of who approved.
    approver_name: Optional[str] = None
    reason: str


class OverrideResponse(BaseModel):
    ok: bool = True
    trip_id: str
    override_approved: bool = True
    approved_by: str
    approved_at: str
    # PA-26 additive dual-control state: with require_pre_approval active and
    # no prior recorded approval, the first call stages the approval and a
    # distinct second owner/admin must finalize it.
    status: Optional[str] = None  # "approved" | "pending_second_approval"
    pending_second_approval: bool = False


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
    cost_source = "recommended_option"
    cost = rec_option.get("cost")
    if cost is None:
        budget = trip.get("budget")
        if isinstance(budget, dict) and budget.get("amount"):
            try:
                cost = float(budget["amount"])
                cost_source = "trip_budget"
            except (ValueError, TypeError):
                cost = None
        elif isinstance(budget, (int, float)):
            cost = float(budget)
            cost_source = "trip_budget"
        elif trip.get("total_price"):
            try:
                cost = float(trip["total_price"])
                cost_source = "total_price"
            except (ValueError, TypeError):
                cost = None

    if cost is None:
        cost = 3000.0
        cost_source = "estimated_default"
        warnings.append("Explicit trip cost absent; estimated baseline of $3,000 used for audit evaluation.")

    # Calculate actual itinerary nights when available; fall back with honest warning
    nights_source = "itinerary_dates"
    nights = None
    if trip.get("nights"):
        try:
            nights = int(trip["nights"])
            nights_source = "trip_nights"
        except (ValueError, TypeError):
            nights = None
    elif trip.get("duration_days"):
        try:
            nights = max(1, int(trip["duration_days"]) - 1)
            nights_source = "duration_days"
        except (ValueError, TypeError):
            nights = None
    else:
        date_start = trip.get("date_start") or trip.get("dates", {}).get("start")
        date_end = trip.get("date_end") or trip.get("dates", {}).get("end")
        if date_start and date_end:
            try:
                d1 = datetime.fromisoformat(str(date_start)[:10])
                d2 = datetime.fromisoformat(str(date_end)[:10])
                diff = (d2 - d1).days
                if diff > 0:
                    nights = diff
                    nights_source = "itinerary_dates"
            except Exception:
                nights = None

    if nights is None or nights <= 0:
        nights = 5
        nights_source = "estimated_default"
        warnings.append("Itinerary dates absent; estimated duration of 5 nights used for nightly rate cap evaluation.")

    nightly_rate = cost / float(nights)
    # FND-0338 (Sim #4): an ESTIMATED baseline may warn, never convict. A
    # violation derived from a fabricated $3,000 default asserted a real
    # "$600 nightly exceeds cap" on a lead with no cost data.
    if nightly_rate > policy.max_nightly_hotel_usd:
        rate_finding = (
            f"Nightly hotel rate (${nightly_rate:.2f}) exceeds corporate cap "
            f"(${policy.max_nightly_hotel_usd:.2f})"
        )
        if cost_source == "estimated_default":
            warnings.append(f"{rate_finding} — derived from the estimated-default cost, not a sourced trip cost; confirm before acting.")
        else:
            violations.append(rate_finding)

    # FND-0338: the policy's cabin-class rule (allowed_flight_class +
    # max_flight_duration_for_business_hours) exists in policy-rules but was
    # never evaluated. Grade from the trip's persisted facts when present.
    requested_class = (
        (trip.get("extracted") or {}).get("cabin_class")
        or (trip.get("strategy") or {}).get("cabin_class")
        or (trip.get("analytics") or {}).get("cabin_class")
    )
    route_hours = (trip.get("analytics") or {}).get("route_duration_hours")
    if requested_class and str(requested_class).upper().startswith("BUSINESS") and route_hours:
        try:
            if float(route_hours) > float(policy.max_flight_duration_for_business_hours):
                violations.append(
                    f"Business class booked for a {float(route_hours):.1f}h sector; policy allows business "
                    f"only up to {policy.max_flight_duration_for_business_hours:g}h"
                )
        except (TypeError, ValueError):
            pass

    dest = (trip.get("destination") or "").strip()
    dest_lower = dest.lower()
    if not dest:
        doc_risk = "UNKNOWN"
        warnings.append("Destination is unspecified on trip; duty-of-care advisory risk could not be verified.")
    else:
        high_risk_destinations = ["kabul", "baghdad", "somalia", "syria", "yemen"]
        if any(h in dest_lower for h in high_risk_destinations):
            doc_risk = "HIGH"
            violations.append(f"Destination '{dest}' is listed under High Risk Duty-of-Care Advisory")
        elif any(c in dest_lower for c in ("tokyo", "london", "paris", "maui", "singapore", "new york", "zurich")):
            doc_risk = "LOW"
        else:
            doc_risk = "MODERATE"

    if cost > 5000.0:
        warnings.append("Total trip cost exceeds $5,000 baseline threshold — secondary VP signoff recommended")

    is_comp = len(violations) == 0
    override_approved = trip.get("corporate_policy_override", {}).get("approved", False)

    violations_detail = [
        {
            "rule": "nightly_rate_cap",
            "description": v,
            "basis": ("sourced_trip_cost" if cost_source != "estimated_default" else "estimated_default"),
            "enforceable": cost_source != "estimated_default",
        }
        for v in violations
        if v.startswith("Nightly hotel rate")
    ] + [
        {"rule": "duty_of_care_high_risk", "description": v, "basis": "sourced_destination", "enforceable": True}
        for v in violations
        if "High Risk Duty-of-Care" in v
    ]

    return PolicyAuditResponse(
        ok=True,
        trip_id=trip_id,
        is_compliant=is_comp,
        violations=violations,
        warnings=warnings,
        violations_detail=violations_detail,
        duty_of_care_risk_level=doc_risk,
        pre_approval_required=policy.require_pre_approval,
        override_approved=override_approved,
        cost_evaluated=round(cost, 2),
        cost_source=cost_source,
        nights_evaluated=nights,
        nights_source=nights_source,
        authority="corporate_policy_v1",
    )


@router.post("/approve-policy-override/{trip_id}", response_model=OverrideResponse)
def approve_corporate_policy_override(
    trip_id: str,
    body: OverrideRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
):
    """Approve a corporate policy exception/override for a trip.

    PA-26: this used to be self-certifying (free-text ``approver_name``, no
    role check, ``require_pre_approval`` ignored). Now:
    - the approver identity is the authenticated principal (never client text);
    - only agency owners/admins may approve (403 otherwise);
    - when the policy rule requires pre-approval and no prior approval is
      recorded, the first call stages a ``pending_second_approval`` record
      instead of approving outright; a DISTINCT second owner/admin finalizes
      it (dual control). Self-approval as the second stage is rejected.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    role = (membership.role or "").lower()
    if role not in _OVERRIDE_APPROVER_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Policy overrides require an owner or admin approver (principal role: '{role or 'unknown'}').",
        )

    # Authenticated approver identity — principal-derived, not client-supplied.
    approver_identity = current_user.name or current_user.email
    approver_id = current_user.id

    policy = CorporatePolicyRules()
    now_iso = datetime.now(timezone.utc).isoformat()
    existing = trip.get("corporate_policy_override") or {}

    already_approved = existing.get("approved") is True
    has_staged_first_approval = bool(existing.get("first_approved_by"))

    if not already_approved and policy.require_pre_approval and not has_staged_first_approval:
        # Stage the first approval; a distinct second approver must finalize.
        trip["corporate_policy_override"] = {
            "approved": False,
            "status": "pending_second_approval",
            "first_approved_by": approver_identity,
            "first_approved_by_id": approver_id,
            "reason": body.reason,
            "approved_at": now_iso,
            "require_second_approver": True,
        }
        TripStore.save_trip(trip, agency_id=agency_id)

        AuditStore.log_event(
            event_type="corporate_policy_override_pending_second_approval",
            user_id=agency_id,
            details={
                "trip_id": trip_id,
                "first_approver": approver_identity,
                "first_approver_id": approver_id,
                "reason": body.reason,
            },
        )

        return OverrideResponse(
            ok=True,
            trip_id=trip_id,
            override_approved=False,
            approved_by=approver_identity,
            approved_at=now_iso,
            status="pending_second_approval",
            pending_second_approval=True,
        )

    if not already_approved and has_staged_first_approval:
        # Dual-control finalize: the second approver must be a distinct human.
        if existing.get("first_approved_by_id") == approver_id:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Dual control required: the second approval must come from a "
                    "distinct owner/admin. Self-approval as the second stage is "
                    "not permitted."
                ),
            )

    trip["corporate_policy_override"] = {
        "approved": True,
        "status": "approved",
        "approved_by": approver_identity,
        "approved_by_id": approver_id,
        "reason": body.reason,
        "approved_at": now_iso,
        # Preserve dual-control evidence when this call finalized a staged one.
        **(
            {
                "first_approved_by": existing["first_approved_by"],
                "first_approved_at": existing.get("approved_at"),
            }
            if has_staged_first_approval
            else {}
        ),
    }

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="corporate_policy_override_approved",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "approver_name": approver_identity,
            "approver_id": approver_id,
            "reason": body.reason,
            "dual_control_completed": has_staged_first_approval,
        },
    )

    return OverrideResponse(
        ok=True,
        trip_id=trip_id,
        override_approved=True,
        approved_by=approver_identity,
        approved_at=now_iso,
        status="approved",
        pending_second_approval=False,
    )
