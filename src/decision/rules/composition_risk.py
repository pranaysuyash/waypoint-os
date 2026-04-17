"""
decision.rules.composition_risk — Party composition risk rule.

Assesses risks related to diverse party composition (age groups, sizes).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from intake.packet_models import CanonicalPacket


def _get_party_composition(packet: CanonicalPacket) -> Optional[Dict[str, int]]:
    """Get party composition counts."""
    comp = packet.facts.get("party_composition")
    if comp and comp.value and isinstance(comp.value, dict):
        return comp.value
    return None


def _extract_destinations(packet: CanonicalPacket) -> Optional[list]:
    """Extract destination list from packet."""
    resolved = packet.facts.get("resolved_destination")
    if resolved and resolved.value:
        return [resolved.value] if not isinstance(resolved.value, list) else resolved.value

    dest_slot = packet.facts.get("destination_candidates")
    if dest_slot and dest_slot.value:
        dests = dest_slot.value
        if isinstance(dests, list):
            return dests
        return [dests]

    return None


def rule_composition_risk(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Assess risks related to party composition.

    Returns None if:
    - No composition data available
    - Simple adult-only groups (low risk)

    Returns decision dict with risk assessment for complex compositions.

    Args:
        packet: CanonicalPacket with travel information

    Returns:
        Decision dict or None
    """
    composition = _get_party_composition(packet)
    if not composition:
        return None

    # Extract counts
    adults = composition.get("adults", 0)
    teens = composition.get("teens", 0)
    children = composition.get("children", 0)
    toddlers = composition.get("toddlers", 0)
    elderly = composition.get("elderly", 0)

    total_party_size = adults + teens + children + toddlers + elderly

    # Special case: only adults
    if total_party_size == adults and adults <= 8:
        # Simple adult group - low risk
        return {
            "risk_level": "low",
            "reasoning": f"Adult-only group of {adults} — standard travel profile",
            "concerns": [],
            "recommendations": [],
        }

    concerns = []
    recommendations = []

    # Multi-generational travel (elderly + children)
    if elderly > 0 and (children + toddlers) > 0:
        concerns.append("Multi-generational group with elderly and young children")
        recommendations.extend([
            "Balance activity levels for all age groups",
            "Consider separate accommodation wings or connecting rooms",
            "Plan activities that work for both groups (beach vs hiking)",
            "Allow flexibility for different pace preferences",
        ])

    # Large group complexity
    if total_party_size > 8:
        concerns.append(f"Large party size ({total_party_size} travelers)")
        recommendations.extend([
            "Consider splitting into smaller sub-groups for activities",
            "Book group transportation in advance",
            "Allow extra time for logistics coordination",
            "Designate group leader/facilitator",
        ])

    # Single adult with multiple dependents
    dependents = teens + children + toddlers + elderly
    if adults == 1 and dependents > 2:
        concerns.append(f"Single adult managing {dependents} dependents")
        recommendations.extend([
            "High fatigue risk for solo adult leader",
            "Consider additional companion to share responsibilities",
            "Plan shorter activity days",
            "Choose destination with good support infrastructure",
        ])

    # Toddler-specific concerns
    if toddlers > 0:
        if toddlers > 1:
            concerns.append(f"Multiple toddlers ({toddlers}) require significant attention")
            recommendations.append("Stroller-friendly destination essential")

    # Elderly-specific concerns
    if elderly > 1:
        concerns.append(f"Multiple elderly travelers may need medical access coordination")
        recommendations.append("Verify medical facilities at destination")

    # Teen-specific considerations
    if teens > 0 and adults == teens:
        concerns.append("All-teen group may have specific activity preferences")
        recommendations.append("Consider age-appropriate activities and supervision")

    # Determine overall risk level
    if len(concerns) >= 3:
        risk_level = "high"
    elif len(concerns) >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Build reasoning
    destination = _extract_destinations(packet)
    dest_str = destination[0] if destination else "destination"

    composition_desc = []
    if elderly > 0:
        composition_desc.append(f"{elderly} elderly")
    if adults > 0:
        composition_desc.append(f"{adults} adults")
    if teens > 0:
        composition_desc.append(f"{teens} teens")
    if children > 0:
        composition_desc.append(f"{children} children")
    if toddlers > 0:
        composition_desc.append(f"{toddlers} toddlers")

    reasoning = (
        f"Party of {total_party_size} ({', '.join(composition_desc)}) "
        f"visiting {dest_str}"
    )

    if concerns:
        reasoning += " — " + "; ".join(concerns[:2])  # Top 2 concerns

    # Add default recommendations if none were generated
    if not recommendations and risk_level != "low":
        recommendations.append("Review itinerary for all age groups")

    return {
        "risk_level": risk_level,
        "reasoning": reasoning,
        "concerns": concerns,
        "recommendations": recommendations,
        "party_size": total_party_size,
        "composition": composition,
    }
