"""
decision.rules.visa_timeline — Visa timeline risk rule.

Assesses visa processing time risk based on trip urgency and destination.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from intake.packet_models import CanonicalPacket


# Typical visa lead times by destination (in days)
# Conservative estimates including buffer
VISA_LEAD_TIMES = {
    # Long processing times
    "USA": {"days": 60, "notes": "Schengen/US visas require advance booking"},
    "Schengen": {"days": 45, "notes": "Europe Schengen visa"},
    "Europe": {"days": 45, "notes": "Europe Schengen visa"},
    "UK": {"days": 30, "notes": "UK visa"},
    "London": {"days": 30, "notes": "UK visa"},
    "Japan": {"days": 14, "notes": "e-Visa available"},
    "Tokyo": {"days": 14, "notes": "e-Visa available"},
    "China": {"days": 30, "notes": "Paper visa required"},
    # Medium processing times
    "Singapore": {"days": 7, "notes": "e-Visa available"},
    "Thailand": {"days": 7, "notes": "Visa on arrival for Indians"},
    "Bangkok": {"days": 7, "notes": "Visa on arrival for Indians"},
    "Dubai": {"days": 7, "notes": "e-Visa available"},
    "Turkey": {"days": 7, "notes": "e-Visa available"},
    "Istanbul": {"days": 7, "notes": "e-Visa available"},
    "Vietnam": {"days": 7, "notes": "e-Visa available"},
    "Bali": {"days": 7, "notes": "Visa on arrival"},
    # Minimal processing
    "Maldives": {"days": 1, "notes": "Visa on arrival"},
    "Sri Lanka": {"days": 1, "notes": "e-Visa/ETA"},
    "Nepal": {"days": 1, "notes": "Visa on arrival for Indians"},
    "Bhutan": {"days": 14, "notes": "Permit required via licensed tour operator"},
    "Mauritius": {"days": 1, "notes": "Visa on arrival"},
    "Seychelles": {"days": 1, "notes": "Visa on arrival"},
    "Goa": {"days": 0, "notes": "Domestic - no visa"},
    "Kerala": {"days": 0, "notes": "Domestic - no visa"},
    "Kashmir": {"days": 0, "notes": "Domestic - no visa"},
    "Andaman": {"days": 0, "notes": "Domestic - permit required but fast"},
    "Andamans": {"days": 0, "notes": "Domestic - permit required but fast"},
}


def _extract_destination(packet: CanonicalPacket) -> Optional[str]:
    """Extract single destination from packet."""
    resolved = packet.facts.get("resolved_destination")
    if resolved and resolved.value:
        return resolved.value

    dest_slot = packet.facts.get("destination_candidates")
    if dest_slot and dest_slot.value:
        dests = dest_slot.value
        if isinstance(dests, list):
            if len(dests) == 1:
                return dests[0]
            return None
        return dests

    return None


def _get_urgency(packet: CanonicalPacket) -> Optional[str]:
    """Get trip urgency level."""
    urgency_slot = packet.derived_signals.get("urgency")
    if urgency_slot and urgency_slot.value:
        return urgency_slot.value
    return None


def _get_visa_requirement(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """Get visa requirement from packet."""
    visa = packet.facts.get("visa_status")
    if visa and visa.value and isinstance(visa.value, dict):
        return visa.value
    return None


def _get_domestic_or_intl(packet: CanonicalPacket) -> Optional[str]:
    """Check if trip is domestic or international."""
    intl = packet.derived_signals.get("domestic_or_international")
    if intl and intl.value:
        return intl.value
    return None


def rule_visa_timeline_risk(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Assess visa timeline risk based on trip urgency and destination.

    Returns None if:
    - Domestic trip (no visa needed)
    - Visa already obtained
    - No visa requirement info available

    Returns decision dict with risk assessment.

    Args:
        packet: CanonicalPacket with travel information

    Returns:
        Decision dict or None
    """
    # Check domestic vs international
    domestic_or_intl = _get_domestic_or_intl(packet)
    if domestic_or_intl == "domestic":
        return {
            "risk_level": "low",
            "reasoning": "Domestic destination — no visa required",
            "visa_lead_time_days": 0,
        }

    # Get visa requirement status
    visa_info = _get_visa_requirement(packet)
    if not visa_info:
        return None  # Can't assess without info

    requirement = visa_info.get("requirement")
    status = visa_info.get("status")

    # If visa already obtained or not required
    if requirement == "not_required" or status == "approved":
        return {
            "risk_level": "low",
            "reasoning": f"Visa {requirement or 'already approved'} — no timeline risk",
            "visa_lead_time_days": 0,
        }

    # If visa required but not yet applied
    if requirement == "required" and status in ("not_applied", "pending"):
        destination = _extract_destination(packet)
        if not destination:
            return {
                "risk_level": "medium",
                "reasoning": "Visa required for international trip — destination unknown for lead time estimate",
                "visa_lead_time_days": 30,  # Conservative default
            }

        # Get lead time for destination
        visa_info = VISA_LEAD_TIMES.get(destination, {"days": 30, "notes": "International visa"})

        # Check urgency
        urgency = _get_urgency(packet)
        lead_time_days = visa_info["days"]

        # Assess risk based on urgency and lead time
        if urgency == "high":
            if lead_time_days > 14:
                risk_level = "high"
                reasoning = (
                    f"High urgency trip to {destination} — "
                    f"visa requires ~{lead_time_days} days processing. "
                    f"Timeline risk: trip may need postponement or visa expediting."
                )
            elif lead_time_days > 0:
                risk_level = "medium"
                reasoning = (
                    f"High urgency trip to {destination} — "
                    f"visa requires ~{lead_time_days} days processing. "
                    f"Tight but manageable if started immediately."
                )
            else:
                risk_level = "low"
                reasoning = (
                    f"High urgency trip to {destination} — "
                    f"visa on arrival or fast processing. No timeline risk."
                )
        else:
            # Normal/low urgency
            if lead_time_days > 30:
                risk_level = "medium"
                reasoning = (
                    f"Trip to {destination} — "
                    f"visa requires ~{lead_time_days} days processing. "
                    f"Start application soon to avoid delays."
                )
            else:
                risk_level = "low"
                reasoning = (
                    f"Trip to {destination} — "
                    f"visa requires ~{lead_time_days} days processing. "
                    f"Standard timeline, no special concerns."
                )

        return {
            "risk_level": risk_level,
            "reasoning": reasoning,
            "visa_lead_time_days": lead_time_days,
            "visa_notes": visa_info.get("notes", ""),
        }

    return None
