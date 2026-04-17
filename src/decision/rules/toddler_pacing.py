"""
decision.rules.toddler_pacing — Toddler pacing risk rule.

Detects pacing issues for trips with young children (under 4 years).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from intake.packet_models import CanonicalPacket


TODDLER_AGE_THRESHOLD = 4  # Under 4 years = pacing risk


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


def _get_toddler_ages(packet: CanonicalPacket) -> List[int]:
    """Get list of toddler ages (children under TODDLER_AGE_THRESHOLD)."""
    ages_slot = packet.facts.get("child_ages")
    if ages_slot and ages_slot.value:
        ages = ages_slot.value
        if isinstance(ages, list):
            return [a for a in ages if a < TODDLER_AGE_THRESHOLD]
        return [ages] if ages < TODDLER_AGE_THRESHOLD else []

    # Check party composition for toddlers
    comp = packet.facts.get("party_composition")
    if comp and comp.value and isinstance(comp.value, dict):
        toddler_count = comp.value.get("toddlers", 0)
        if toddler_count > 0:
            # Return placeholder ages (can't determine exact ages from count)
            return list(range(toddler_count))

    return []


def _has_toddlers(packet: CanonicalPacket) -> bool:
    """Check if packet has toddler-age travelers."""
    return len(_get_toddler_ages(packet)) > 0


def rule_toddler_pacing_risk(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Assess toddler pacing risk based on trip duration and complexity.

    Returns None if rule cannot handle (e.g., no toddlers).
    Returns decision dict if rule can handle.

    Risk Logic:
    - HIGH: Toddlers + long duration (>7 days) OR multiple destinations
    - MEDIUM: Toddlers + standard trip
    - None: No toddlers

    Args:
        packet: CanonicalPacket with travel information

    Returns:
        Decision dict or None
    """
    # Check if toddlers present
    toddler_ages = _get_toddler_ages(packet)
    if not toddler_ages:
        return None

    # Get trip duration
    duration_days = None
    duration_slot = packet.facts.get("duration_days")
    if duration_slot and duration_slot.value:
        duration_days = duration_slot.value
    else:
        # Try to calculate from date window
        date_start = packet.facts.get("date_start")
        date_end = packet.facts.get("date_end")
        if date_start and date_start.value and date_end and date_end.value:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(date_start.value) if isinstance(date_start.value, str) else date_start.value
                end = datetime.fromisoformat(date_end.value) if isinstance(date_end.value, str) else date_end.value
                duration_days = (end - start).days
            except (ValueError, TypeError):
                pass

    # Get destinations
    destinations = _extract_destinations(packet)
    num_destinations = len(destinations) if destinations else 0

    # Determine risk level
    youngest_age = min(toddler_ages) if toddler_ages else 0
    risk_level = "medium"
    reasoning_parts = []
    recommendations = [
        "Plan for frequent breaks (every 2-3 hours)",
        "Book direct transfers where possible",
        "Choose accommodation with play areas or pools",
    ]

    # High risk conditions
    is_long_trip = duration_days and duration_days > 7
    is_multi_dest = num_destinations > 1

    if is_long_trip or is_multi_dest:
        risk_level = "high"

        if is_long_trip:
            reasoning_parts.append(f"Long trip duration ({duration_days} days)")
            recommendations.extend([
                f"Consider splitting the {duration_days}-day trip with rest days",
                "Avoid more than 1 activity per day",
            ])

        if is_multi_dest:
            reasoning_parts.append(f"Multiple destinations ({num_destinations})")
            recommendations.extend([
                f"Minimize transfers between {num_destinations} destinations",
                "Consider base-camping instead of moving hotels",
            ])
    else:
        # Medium risk
        if duration_days:
            reasoning_parts.append(f"Trip duration: {duration_days} days")
        if num_destinations == 1:
            reasoning_parts.append(f"Single destination: {destinations[0]}")

    reasoning_parts.insert(0, f"Toddler ({youngest_age} years old)")
    reasoning = " | ".join(reasoning_parts)

    if risk_level == "high":
        recommendations.extend([
            "Consider postponing until child is older",
            "Or reduce trip complexity significantly",
        ])

    return {
        "risk_level": risk_level,
        "reasoning": reasoning + " — pacing and transfer complexity concerns",
        "recommendations": recommendations,
        "toddler_ages": toddler_ages,
        "duration_days": duration_days,
    }
