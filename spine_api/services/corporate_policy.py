"""
spine_api.services.corporate_policy — Corporate travel policy validator and approval gatekeeper.

Enforces corporate travel guidelines:
- Cabin class restrictions (Economy under 6h flight duration; Business allowed for long-haul).
- Maximum nightly hotel caps by city tier (e.g. $300 NYC/London, $200 standard).
- Advance booking requirement (minimum 14 days).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class PolicyViolation:
    rule_code: str
    severity: str  # "HARD_BLOCK" | "SOFT_APPROVAL_REQUIRED" | "INFO"
    message: str


@dataclass(slots=True)
class CorporatePolicyAuditResult:
    is_compliant: bool
    requires_manager_approval: bool
    violations: List[PolicyViolation] = field(default_factory=list)
    summary: str = ""


def evaluate_corporate_travel_policy(
    flight_duration_hours: float,
    flight_cabin_class: str,  # "Economy" | "PremiumEconomy" | "Business" | "First"
    hotel_nightly_rate_usd: float,
    destination_city: str,
    days_advance_booking: int,
    max_hotel_cap_usd: float = 250.0,
) -> CorporatePolicyAuditResult:
    """
    Validate a corporate trip against corporate travel governance rules.
    """
    violations: List[PolicyViolation] = []

    # 1. Flight Cabin Class Rules
    if flight_duration_hours < 6.0 and flight_cabin_class in ("Business", "First"):
        violations.append(
            PolicyViolation(
                rule_code="CABIN_CLASS_DURATION_RESTRICTION",
                severity="SOFT_APPROVAL_REQUIRED",
                message=f"{flight_cabin_class} class is not permitted for flights under 6.0 hours ({flight_duration_hours:.1f}h). Requires VP approval.",
            )
        )

    # 2. Hotel Nightly Rate Caps
    city_cap = max_hotel_cap_usd
    if destination_city.lower() in ("new york", "london", "tokyo", "paris", "san francisco", "zurich"):
        city_cap = max(350.0, max_hotel_cap_usd * 1.4)

    if hotel_nightly_rate_usd > city_cap:
        violations.append(
            PolicyViolation(
                rule_code="HOTEL_NIGHTLY_RATE_EXCEEDED",
                severity="SOFT_APPROVAL_REQUIRED",
                message=f"Hotel nightly rate of ${hotel_nightly_rate_usd:.2f} exceeds the policy cap of ${city_cap:.2f} for {destination_city}.",
            )
        )

    # 3. Advance Booking Rule (14-day standard)
    if days_advance_booking < 7:
        violations.append(
            PolicyViolation(
                rule_code="LAST_MINUTE_BOOKING",
                severity="INFO",
                message=f"Trip is booked only {days_advance_booking} days in advance (policy target is $\\ge 14$ days).",
            )
        )

    requires_approval = any(v.severity in ("SOFT_APPROVAL_REQUIRED", "HARD_BLOCK") for v in violations)
    is_compliant = len(violations) == 0

    summary = (
        "Compliant with corporate travel policy."
        if is_compliant
        else f"{len(violations)} policy exception(s) detected. Manager sign-off required."
    )

    return CorporatePolicyAuditResult(
        is_compliant=is_compliant,
        requires_manager_approval=requires_approval,
        violations=violations,
        summary=summary,
    )
