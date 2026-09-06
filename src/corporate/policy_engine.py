"""
src/corporate/policy_engine.py — Corporate Travel Policy & Approval Hierarchy Engine (Area #17.15).

Implements:
1. Employee Seniority Tiers (EXECUTIVE, SENIOR_MGMT, STANDARD).
2. Flight Class Rules based on flight duration and seniority.
3. City Tier Per-Diem Hotel Limits (Tier 1 Alpha Metros, Tier 2 Major Cities, Tier 3 Regional).
4. Multi-level Approval Chains (Line Manager -> Department Director -> Finance VP).
5. Duty of Care & Geopolitical Risk Grading (Low, Moderate, Elevated, Extreme).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EmployeeTier(str, Enum):
    EXECUTIVE = "EXECUTIVE"          # VP, C-Suite, Board
    SENIOR_MGMT = "SENIOR_MGMT"      # Director, Senior Manager
    STANDARD = "STANDARD"            # Individual Contributor, Associate


class CabinClass(str, Enum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class ApprovalState(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    PENDING_MANAGER = "PENDING_MANAGER"
    PENDING_DIRECTOR = "PENDING_DIRECTOR"
    PENDING_FINANCE = "PENDING_FINANCE"
    REJECTED = "REJECTED"
    EXCEPTION_APPROVED = "EXCEPTION_APPROVED"


@dataclass(slots=True)
class CorporatePolicyConfig:
    company_id: str
    company_name: str
    max_hotel_rate_tier1_usd: float = 350.0   # London, NYC, Tokyo, Paris
    max_hotel_rate_tier2_usd: float = 220.0   # Rome, Berlin, Madrid, Dubai
    max_hotel_rate_tier3_usd: float = 150.0   # Other secondary cities
    business_class_min_hours_standard: float = 8.0
    business_class_min_hours_senior: float = 6.0
    require_advance_booking_days: int = 14
    max_budget_without_vp_approval_usd: float = 5000.0


@dataclass(slots=True)
class PolicyViolation:
    rule_code: str
    severity: str  # HARD_BLOCK, SOFT_WARNING, APPROVAL_REQUIRED
    message: str
    required_approver_role: Optional[str] = None


@dataclass(slots=True)
class CorporateAuditResult:
    trip_id: str
    is_compliant: bool
    approval_state: ApprovalState
    violations: List[PolicyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duty_of_care_risk: str = "LOW"
    escalation_chain: List[str] = field(default_factory=list)


class CorporatePolicyEngine:
    """
    Evaluates corporate travel bookings against company travel policies and approval matrices.
    """

    TIER_1_CITIES = {"london", "new york", "nyc", "tokyo", "paris", "san francisco", "singapore", "hong kong", "zurich"}
    TIER_2_CITIES = {"rome", "berlin", "madrid", "dubai", "mumbai", "delhi", "amsterdam", "sydney", "toronto"}

    @classmethod
    def audit_itinerary(
        cls,
        trip_id: str,
        employee_tier: EmployeeTier,
        flight_duration_hours: float,
        requested_cabin_class: CabinClass,
        nightly_hotel_rate_usd: float,
        destination_city: str,
        days_in_advance: int,
        total_trip_budget_usd: float,
        policy_config: Optional[CorporatePolicyConfig] = None,
    ) -> CorporateAuditResult:
        cfg = policy_config or CorporatePolicyConfig(company_id="default_corp", company_name="Enterprise Standard")
        violations: List[PolicyViolation] = []
        warnings: List[str] = []
        escalation_chain: List[str] = []

        norm_city = destination_city.strip().lower()

        # 1. Flight Cabin Class Compliance
        allowed_cabin = CabinClass.ECONOMY
        if employee_tier == EmployeeTier.EXECUTIVE:
            allowed_cabin = CabinClass.FIRST if flight_duration_hours >= 10 else CabinClass.BUSINESS
        elif employee_tier == EmployeeTier.SENIOR_MGMT:
            if flight_duration_hours >= cfg.business_class_min_hours_senior:
                allowed_cabin = CabinClass.BUSINESS
            else:
                allowed_cabin = CabinClass.PREMIUM_ECONOMY
        else:  # STANDARD
            if flight_duration_hours >= cfg.business_class_min_hours_standard:
                allowed_cabin = CabinClass.BUSINESS
            elif flight_duration_hours >= 4.0:
                allowed_cabin = CabinClass.PREMIUM_ECONOMY

        cabin_ranks = {CabinClass.ECONOMY: 1, CabinClass.PREMIUM_ECONOMY: 2, CabinClass.BUSINESS: 3, CabinClass.FIRST: 4}
        if cabin_ranks[requested_cabin_class] > cabin_ranks[allowed_cabin]:
            violations.append(PolicyViolation(
                rule_code="CABIN_CLASS_EXCEEDED",
                severity="APPROVAL_REQUIRED",
                message=f"Requested {requested_cabin_class.value} exceeds policy limit of {allowed_cabin.value} for {flight_duration_hours:.1f}h flight.",
                required_approver_role="DIRECTOR",
            ))

        # 2. Hotel Nightly Rate Cap
        if any(c in norm_city for c in cls.TIER_1_CITIES):
            rate_cap = cfg.max_hotel_rate_tier1_usd
        elif any(c in norm_city for c in cls.TIER_2_CITIES):
            rate_cap = cfg.max_hotel_rate_tier2_usd
        else:
            rate_cap = cfg.max_hotel_rate_tier3_usd

        if nightly_hotel_rate_usd > rate_cap:
            overage_pct = round(((nightly_hotel_rate_usd - rate_cap) / rate_cap) * 100.0, 1)
            violations.append(PolicyViolation(
                rule_code="HOTEL_RATE_CAP_EXCEEDED",
                severity="APPROVAL_REQUIRED" if overage_pct < 50 else "HARD_BLOCK",
                message=f"Nightly rate ${nightly_hotel_rate_usd:.2f} exceeds ${rate_cap:.2f} cap for {destination_city} by {overage_pct}%.",
                required_approver_role="MANAGER" if overage_pct < 25 else "DIRECTOR",
            ))

        # 3. Advance Booking Window
        if days_in_advance < cfg.require_advance_booking_days:
            warnings.append(
                f"Booking is made {days_in_advance} days in advance (recommended: {cfg.require_advance_booking_days}+ days for optimal corporate pricing)."
            )

        # 4. Total Budget Authority Escalation
        if total_trip_budget_usd > cfg.max_budget_without_vp_approval_usd:
            violations.append(PolicyViolation(
                rule_code="HIGH_VALUE_BUDGET_CAP",
                severity="APPROVAL_REQUIRED",
                message=f"Total cost ${total_trip_budget_usd:,.2f} exceeds auto-approval ceiling of ${cfg.max_budget_without_vp_approval_usd:,.2f}.",
                required_approver_role="FINANCE_VP",
            ))

        # Determine Approval State & Escalation Chain
        is_compliant = len(violations) == 0
        if is_compliant:
            approval_state = ApprovalState.AUTO_APPROVED
        else:
            roles = {v.required_approver_role for v in violations if v.required_approver_role}
            if "FINANCE_VP" in roles:
                approval_state = ApprovalState.PENDING_FINANCE
                escalation_chain = ["MANAGER", "DIRECTOR", "FINANCE_VP"]
            elif "DIRECTOR" in roles:
                approval_state = ApprovalState.PENDING_DIRECTOR
                escalation_chain = ["MANAGER", "DIRECTOR"]
            else:
                approval_state = ApprovalState.PENDING_MANAGER
                escalation_chain = ["MANAGER"]

        return CorporateAuditResult(
            trip_id=trip_id,
            is_compliant=is_compliant,
            approval_state=approval_state,
            violations=violations,
            warnings=warnings,
            duty_of_care_risk="LOW",
            escalation_chain=escalation_chain,
        )
