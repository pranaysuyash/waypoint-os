"""
decision.rules.additional_rules — Additional rules for common scenarios.

These rules cover additional patterns to increase rule hit rate toward 60%+.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from src.intake.packet_models import CanonicalPacket



def rule_budget_domestic_default(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Default budget feasibility for domestic destinations.

    For domestic trips with budget >= ₹15k/person, return feasible.
    """
    # Check if domestic
    intl = packet.derived_signals.get("domestic_or_international")
    if not (intl and intl.value and intl.value == "domestic"):
        return None

    # Get budget and party size
    budget_min_slot = packet.facts.get("budget_min")
    party_size_slot = packet.facts.get("party_size")

    if not (budget_min_slot and budget_min_slot.value and party_size_slot and party_size_slot.value):
        return None

    budget_min = budget_min_slot.value
    party_size = party_size_slot.value

    # Domestic minimum: ₹15k per person
    domestic_min_per_person = 15000
    budget_per_person = budget_min / party_size if party_size > 0 else 0

    if budget_per_person >= domestic_min_per_person:
        return {
            "feasible": True,
            "risk_level": "low",
            "budget_per_person": budget_per_person,
            "min_required": domestic_min_per_person * party_size,
            "reasoning": f"Domestic trip with ₹{budget_per_person:.0f}/person (≥₹{domestic_min_per_person} minimum)",
        }

    return None


def rule_visa_international_default(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Default visa timeline for international trips.

    For international trips without visa info, return medium risk
    with conservative 30-day lead time assumption.
    """
    # Check if international
    intl = packet.derived_signals.get("domestic_or_international")
    if not (intl and intl.value and intl.value == "international"):
        return None

    # Get visa status if available
    visa_slot = packet.facts.get("visa_status")
    if visa_slot and visa_slot.value:
        # If we have visa info, let the main rule handle it
        return None

    # No visa info for international trip - return medium risk
    return {
        "risk_level": "medium",
        "reasoning": "International trip - visa requirement unknown. Verify visa needs for destination.",
        "visa_lead_time_days": 30,
        "recommendations": [
            "Check visa requirements for your destination",
            "Start visa application at least 30 days before travel",
        ],
    }


def rule_elderly_domestic_low_risk(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Elderly travelers to domestic destinations have low mobility risk.

    Domestic destinations in India generally have better accessibility
    infrastructure than remote international destinations.
    """
    # Check if domestic
    intl = packet.derived_signals.get("domestic_or_international")
    if not (intl and intl.value and intl.value == "domestic"):
        return None

    # Check for elderly
    composition = packet.facts.get("party_composition")
    if composition and composition.value:
        comp = composition.value
        if isinstance(comp, dict) and comp.get("elderly", 0) > 0:
            return {
                "risk_level": "low",
                "reasoning": "Elderly travelers visiting domestic destination - generally good accessibility",
                "concerns": [],
                "recommendations": [
                    "Choose accommodations with ground floor rooms",
                    "Prefer direct transportation options",
                ],
            }

    return None


def rule_toddler_domestic_short_trip_low_risk(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Toddlers on short domestic trips have low pacing risk.

    Short domestic trips (≤5 days) with toddlers are manageable.
    """
    # Check for toddlers
    composition = packet.facts.get("party_composition")
    has_toddler = False
    if composition and composition.value:
        comp = composition.value
        if isinstance(comp, dict) and comp.get("toddlers", 0) > 0:
            has_toddler = True

    if not has_toddler:
        return None

    # Check if domestic
    intl = packet.derived_signals.get("domestic_or_international")
    is_domestic = intl and intl.value and intl.value == "domestic"
    if not is_domestic:
        return None

    # Check duration
    duration_slot = packet.facts.get("duration_days")
    if duration_slot and duration_slot.value:
        duration = duration_slot.value
        if duration <= 5:
            return {
                "risk_level": "low",
                "reasoning": f"Short domestic trip ({duration} days) with toddler - manageable pacing",
                "concerns": [],
                "recommendations": [
                    "Plan 1-2 activities per day",
                    "Include nap time in schedule",
                ],
            }

    return None


def rule_budget_not_applicable(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Handle cases where budget information is missing.

    Returns medium risk with a recommendation to gather budget info.
    """
    # Check if budget_min exists
    budget_min = packet.facts.get("budget_min")
    if budget_min and budget_min.value is not None:
        return None  # Let main rule handle it

    # No budget info - return explicit decision
    return {
        "feasible": None,  # Unknown without budget
        "risk_level": "medium",
        "reasoning": "Budget information not provided. Cannot assess feasibility without knowing budget constraints.",
        "recommendations": [
            "Ask traveler for their budget range",
            "Provide minimum viable cost estimate for destination",
        ],
    }


def rule_party_size_from_composition(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Derive party_size from party_composition for budget checks.

    This enables budget feasibility rules when only composition is available.
    """
    # Skip if party_size already exists
    if packet.facts.get("party_size") and packet.facts.get("party_size").value:
        return None

    # Get party composition
    composition = packet.facts.get("party_composition")
    if not composition or not composition.value:
        return None

    comp = composition.value
    if not isinstance(comp, dict):
        return None

    # Calculate total party size
    total = (
        comp.get("elderly", 0) +
        comp.get("adults", 0) +
        comp.get("teens", 0) +
        comp.get("children", 0) +
        comp.get("toddlers", 0)
    )

    if total == 0:
        return None

    # Check for budget info
    budget_min = packet.facts.get("budget_min")
    if not budget_min or not budget_min.value:
        return None

    # Get destination
    intl = packet.derived_signals.get("domestic_or_international")
    is_domestic = intl and intl.value and intl.value == "domestic"

    # Use domestic/international minimums
    if is_domestic:
        min_per_person = 15000
    else:
        min_per_person = 50000

    budget = budget_min.value
    if isinstance(budget, str):
        # Try to parse
        budget = budget.lower().replace(",", "").replace("₹", "").replace("inr", "").strip()
        try:
            budget = int(float(budget))
        except ValueError:
            return None

    budget_per_person = budget / total
    estimated_minimum = min_per_person * total
    gap = budget - estimated_minimum

    if gap >= 0:
        status = "feasible"
        risk = "low"
    elif gap > -0.3 * estimated_minimum:
        status = "tight"
        risk = "medium"
    else:
        status = "infeasible"
        risk = "high"

    return {
        "feasible": status in ("feasible", "tight"),
        "risk_level": risk,
        "reasoning": f"Budget ₹{budget:,} for {total} travelers (₹{budget_per_person:.0f}/person) vs ₹{estimated_minimum:,} minimum needed.",
        "estimated_cost_range": f"₹{estimated_minimum:,} minimum",
        "party_size_derived": total,
    }
