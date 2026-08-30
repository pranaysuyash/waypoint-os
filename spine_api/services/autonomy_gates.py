"""
spine_api.services.autonomy_gates — Governance rules and human sign-off autonomy gatekeeper.

Evaluates package risk factors to determine whether an agent can autonomously dispatch
a proposal to a traveler or if human advisor review is mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class AutonomyRiskFactor:
    risk_code: str
    severity: str  # "HIGH" | "MEDIUM" | "LOW"
    description: str


@dataclass(slots=True)
class AutonomyGateDecision:
    can_auto_dispatch: bool
    requires_human_signoff: bool
    autonomy_level: str  # "AUTONOMOUS" | "ADVISOR_REVIEW_REQUIRED" | "RESTRICTED"
    risk_factors: List[AutonomyRiskFactor] = field(default_factory=list)
    rationale: str = ""


def evaluate_autonomy_dispatch_gate(
    total_package_usd: float,
    has_non_refundable_deposit: bool,
    destination_risk_rating: str = "LOW",  # "LOW" | "ELEVATED" | "HIGH"
    unverified_suppliers_count: int = 0,
    advisor_override: bool = False,
) -> AutonomyGateDecision:
    """
    Evaluate if an AI-generated proposal can be dispatched autonomously to a traveler.
    """
    if advisor_override:
        return AutonomyGateDecision(
            can_auto_dispatch=True,
            requires_human_signoff=False,
            autonomy_level="AUTONOMOUS",
            risk_factors=[],
            rationale="Advisor manual override granted for direct dispatch.",
        )

    risk_factors: List[AutonomyRiskFactor] = []

    # 1. High Value Package Threshold ($10,000+)
    if total_package_usd >= 10000.0:
        risk_factors.append(
            AutonomyRiskFactor(
                risk_code="HIGH_TRANSACTION_VALUE",
                severity="HIGH",
                description=f"Package total of ${total_package_usd:,.2f} exceeds the $10,000 autonomous dispatch ceiling.",
            )
        )

    # 2. Non-refundable supplier commitments
    if has_non_refundable_deposit:
        risk_factors.append(
            AutonomyRiskFactor(
                risk_code="NON_REFUNDABLE_EXPOSURE",
                severity="MEDIUM",
                description="Itinerary contains non-refundable hotel or flight deposits.",
            )
        )

    # 3. High Risk Destination
    if destination_risk_rating.upper() in ("ELEVATED", "HIGH"):
        risk_factors.append(
            AutonomyRiskFactor(
                risk_code="DESTINATION_SAFETY_ADVISORY",
                severity="HIGH",
                description=f"Destination has {destination_risk_rating} advisory status; human safety review required.",
            )
        )

    # 4. Unverified suppliers
    if unverified_suppliers_count > 0:
        risk_factors.append(
            AutonomyRiskFactor(
                risk_code="UNVERIFIED_SUPPLIER_PRESENT",
                severity="HIGH",
                description=f"Itinerary references {unverified_suppliers_count} unvetted supplier(s).",
            )
        )

    has_high_risk = any(rf.severity == "HIGH" for rf in risk_factors)
    requires_human = len(risk_factors) > 0 and (has_high_risk or len(risk_factors) >= 2)

    autonomy_level = "ADVISOR_REVIEW_REQUIRED" if requires_human else "AUTONOMOUS"
    can_dispatch = not requires_human

    rationale = (
        "Qualifies for autonomous dispatch."
        if can_dispatch
        else f"Mandatory human sign-off required: {len(risk_factors)} risk trigger(s) detected."
    )

    return AutonomyGateDecision(
        can_auto_dispatch=can_dispatch,
        requires_human_signoff=requires_human,
        autonomy_level=autonomy_level,
        risk_factors=risk_factors,
        rationale=rationale,
    )
