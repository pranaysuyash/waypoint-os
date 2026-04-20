"""
decision.rules.budget_feasibility — Budget feasibility rule.

Compares stated budget against minimum viable cost for destination + party.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.intake.packet_models import CanonicalPacket



# Minimum viable cost per person by destination (in INR)
# Sourced from historical agency data
BUDGET_FEASIBILITY_TABLE = {
    "Singapore": {"min_per_person": 60000, "maturity": "heuristic"},
    "Japan": {"min_per_person": 120000, "maturity": "heuristic"},
    "Dubai": {"min_per_person": 80000, "maturity": "heuristic"},
    "Thailand": {"min_per_person": 50000, "maturity": "heuristic"},
    "Maldives": {"min_per_person": 100000, "maturity": "heuristic"},
    "Europe": {"min_per_person": 150000, "maturity": "heuristic"},
    "Sri Lanka": {"min_per_person": 40000, "maturity": "heuristic"},
    "Andaman": {"min_per_person": 35000, "maturity": "heuristic"},
    "Andamans": {"min_per_person": 35000, "maturity": "heuristic"},
    "Goa": {"min_per_person": 15000, "maturity": "heuristic"},
    "Kerala": {"min_per_person": 20000, "maturity": "heuristic"},
    "Kashmir": {"min_per_person": 25000, "maturity": "heuristic"},
    "Bangkok": {"min_per_person": 50000, "maturity": "heuristic"},
    "Bali": {"min_per_person": 60000, "maturity": "heuristic"},
    "Vietnam": {"min_per_person": 50000, "maturity": "heuristic"},
    "Nepal": {"min_per_person": 20000, "maturity": "heuristic"},
    "Bhutan": {"min_per_person": 40000, "maturity": "heuristic"},
    "Mauritius": {"min_per_person": 100000, "maturity": "heuristic"},
    "Seychelles": {"min_per_person": 120000, "maturity": "heuristic"},
    "Turkey": {"min_per_person": 80000, "maturity": "heuristic"},
    "Istanbul": {"min_per_person": 80000, "maturity": "heuristic"},
    "Paris": {"min_per_person": 150000, "maturity": "heuristic"},
    "London": {"min_per_person": 150000, "maturity": "heuristic"},
    "Tokyo": {"min_per_person": 120000, "maturity": "heuristic"},
    "Osaka": {"min_per_person": 120000, "maturity": "heuristic"},
    "New York": {"min_per_person": 180000, "maturity": "heuristic"},
    "__default_domestic__": {"min_per_person": 15000, "maturity": "heuristic"},
    "__default_international__": {"min_per_person": 50000, "maturity": "heuristic"},
}


def _get_numeric_budget(packet: CanonicalPacket) -> Optional[int]:
    """Extract budget as integer from packet."""
    budget = packet.facts.get("budget_min")
    if not budget or not budget.value:
        return None

    value = budget.value
    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):
        # Parse budget string
        value = value.lower().replace(",", "").replace("₹", "").replace("inr", "").strip()
        try:
            return int(float(value))
        except ValueError:
            return None

    return None


def _extract_destination(packet: CanonicalPacket) -> Optional[str]:
    """Extract single destination from packet."""
    # Prefer resolved_destination
    resolved = packet.facts.get("resolved_destination")
    if resolved and resolved.value:
        return resolved.value

    # Check destination_candidates
    dest_slot = packet.facts.get("destination_candidates")
    if dest_slot and dest_slot.value:
        dests = dest_slot.value
        if isinstance(dests, list):
            # Only handle single destination case
            if len(dests) == 1:
                return dests[0]
            # Multiple candidates - can't determine
            return None
        return dests

    return None


def rule_budget_feasibility(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Assess budget feasibility against minimum viable cost.

    Returns None if rule cannot handle (missing budget, destination, or party size).
    Returns decision dict with feasible/tight/infeasible status.

    Args:
        packet: CanonicalPacket with travel information

    Returns:
        Decision dict or None
    """
    # Get budget
    budget = _get_numeric_budget(packet)
    if budget is None:
        return None

    # Get destination
    destination = _extract_destination(packet)
    if destination is None:
        return None

    # Get party size
    party_slot = packet.facts.get("party_size")
    if not party_slot or not party_slot.value:
        return None
    party_size = party_slot.value

    # Look up minimum cost per person
    entry = BUDGET_FEASIBILITY_TABLE.get(destination)
    if not entry:
        # Fall back to default based on domestic/international
        intl = packet.derived_signals.get("domestic_or_international")
        if intl and intl.value == "domestic":
            entry = BUDGET_FEASIBILITY_TABLE.get("__default_domestic__")
        else:
            entry = BUDGET_FEASIBILITY_TABLE.get("__default_international__")

    if not entry:
        return None

    min_per_person = entry.get("min_per_person", 0)
    estimated_minimum = min_per_person * party_size
    gap = budget - estimated_minimum

    # Determine feasibility status
    if gap < -0.3 * estimated_minimum:
        status = "infeasible"
        risk_level = "high"
        reasoning = (
            f"Budget ₹{budget:,} is ₹{abs(gap):,} below minimum viable cost "
            f"of ₹{estimated_minimum:,} for {party_size} travelers to {destination}. "
            f"Significant budget increase required."
        )
    elif gap < 0:
        status = "tight"
        risk_level = "medium"
        reasoning = (
            f"Budget ₹{budget:,} is ₹{abs(gap):,} below recommended minimum "
            f"of ₹{estimated_minimum:,} for {party_size} travelers to {destination}. "
            f"Trip possible with compromises."
        )
    else:
        status = "feasible"
        risk_level = "low"
        reasoning = (
            f"Budget ₹{budget:,} is ₹{gap:,} above minimum viable cost "
            f"of ₹{estimated_minimum:,} for {party_size} travelers to {destination}. "
            f"Good budget for this destination."
        )

    return {
        "feasible": status in ("feasible", "tight"),
        "risk_level": risk_level,
        "reasoning": reasoning,
        "estimated_cost_range": f"₹{estimated_minimum:,} minimum",
        "gap_amount": gap,
        "gap_percent": round((gap / estimated_minimum) * 100, 1) if estimated_minimum > 0 else 0,
    }
