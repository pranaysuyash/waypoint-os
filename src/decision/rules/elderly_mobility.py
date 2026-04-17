"""
decision.rules.elderly_mobility — Elderly mobility risk rule.

Detects destinations with challenging mobility conditions for elderly travelers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from intake.packet_models import CanonicalPacket


# Destinations with challenging mobility for elderly travelers
RISKY_DESTINATIONS = {
    "Maldives",
    "Andaman",
    "Andamans",
    "Bhutan",
    "Nepal",
}


def _extract_destinations(packet: CanonicalPacket) -> Optional[list]:
    """Extract destination list from packet."""
    # Try resolved_destination first (single confirmed destination)
    resolved = packet.facts.get("resolved_destination")
    if resolved and resolved.value:
        return [resolved.value] if not isinstance(resolved.value, list) else resolved.value

    # Fall back to destination_candidates
    dest_slot = packet.facts.get("destination_candidates")
    if dest_slot and dest_slot.value:
        dests = dest_slot.value
        if isinstance(dests, list):
            return dests
        return [dests]

    return None


def _has_elderly_travelers(packet: CanonicalPacket) -> bool:
    """Check if packet has elderly travelers."""
    comp = packet.facts.get("party_composition")
    if comp and comp.value and isinstance(comp.value, dict):
        return comp.value.get("elderly", 0) > 0
    return False


def rule_elderly_mobility_risk(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Assess elderly mobility risk based on destination.

    Returns None if rule cannot handle (e.g., no elderly, no destination).
    Returns decision dict if rule can handle.

    Risk Logic:
    - HIGH: Elderly travelers + risky destinations (Maldives, Andaman, Bhutan, Nepal)
    - LOW: Elderly travelers + other destinations (minor risk)
    - None: No elderly travelers or no destination

    Args:
        packet: CanonicalPacket with travel information

    Returns:
        Decision dict or None
    """
    # Check if elderly travelers present
    if not _has_elderly_travelers(packet):
        return None

    # Extract destinations
    destinations = _extract_destinations(packet)
    if not destinations:
        return None

    # Check for risky destinations
    risky_match = None
    for dest in destinations:
        if dest in RISKY_DESTINATIONS:
            risky_match = dest
            break

    if risky_match:
        return {
            "risk_level": "high",
            "reasoning": (
                f"Elderly travelers visiting {risky_match} — "
                f"destination has limited medical access and challenging mobility conditions. "
                f"Verify traveler fitness and consider alternatives."
            ),
            "recommendations": [
                f"Verify medical fitness for {risky_match} travel conditions",
                "Check travel insurance coverage for medical emergencies",
                "Consider alternative destinations with better infrastructure",
                "Ensure proximity to medical facilities at accommodation",
            ],
        }

    # Elderly travelers but not a risky destination
    dest_str = destinations[0] if destinations else "destination"
    return {
        "risk_level": "low",
        "reasoning": (
            f"Elderly travelers visiting {dest_str} — "
            f"generally accessible destination with standard precautions."
        ),
        "recommendations": [
            "Consider ground-floor accommodation or elevator access",
            "Plan for shorter travel days with rest periods",
            "Verify walking distances for planned activities",
        ],
    }
