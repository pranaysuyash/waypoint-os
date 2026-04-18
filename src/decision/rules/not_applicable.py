"""
decision.rules.not_applicable — Rules for "not applicable" risk scenarios.

Returns "low" risk when a decision type doesn't apply to the current packet.
For example: no elderly travelers = no elderly mobility risk.
This reduces default fallback rate by handling negative cases explicitly.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from intake.packet_models import CanonicalPacket


def rule_elderly_not_applicable(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Return low risk when there are no elderly travelers.

    This prevents elderly_mobility_risk from falling through to default
    when the packet doesn't contain elderly travelers.
    """
    composition = packet.facts.get("party_composition")
    if composition and composition.value:
        comp = composition.value
        if isinstance(comp, dict):
            elderly_count = comp.get("elderly", 0)
            if elderly_count == 0:
                return {
                    "risk_level": "low",
                    "reasoning": "No elderly travelers in party - elderly mobility risks not applicable",
                    "concerns": [],
                    "recommendations": [],
                }
    return None


def rule_toddler_not_applicable(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Return low risk when there are no toddlers.

    This prevents toddler_pacing_risk from falling through to default
    when the packet doesn't contain toddlers.
    """
    composition = packet.facts.get("party_composition")
    if composition and composition.value:
        comp = composition.value
        if isinstance(comp, dict):
            toddler_count = comp.get("toddlers", 0)
            if toddler_count == 0:
                return {
                    "risk_level": "low",
                    "reasoning": "No toddlers in party - toddler pacing risks not applicable",
                    "concerns": [],
                    "recommendations": [],
                }
    return None


def rule_visa_not_applicable(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Return low risk for domestic trips (no visa needed).

    This provides an explicit rule for domestic travel visa risk.
    """
    intl = packet.derived_signals.get("domestic_or_international")
    if intl and intl.value and intl.value == "domestic":
        return {
            "risk_level": "low",
            "reasoning": "Domestic travel - visa not required for Indian citizens",
            "visa_lead_time_days": 0,
        }
    return None


def rule_composition_not_applicable(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Return low risk for simple adult-only groups.

    Handles the case where there's no complex composition but the packet
    has some party information.
    """
    composition = packet.facts.get("party_composition")
    if composition and composition.value:
        comp = composition.value
        if isinstance(comp, dict):
            adults = comp.get("adults", 0)
            total = (
                comp.get("elderly", 0) +
                comp.get("adults", 0) +
                comp.get("teens", 0) +
                comp.get("children", 0) +
                comp.get("toddlers", 0)
            )

            # If only adults and small group
            if total == adults and adults > 0 and adults <= 8:
                return {
                    "risk_level": "low",
                    "reasoning": f"Adult-only group of {adults} - standard travel profile",
                    "concerns": [],
                    "recommendations": [],
                    "party_size": total,
                    "composition": comp,
                }
    return None


def rule_no_composition_info(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Return low risk when party composition is unknown.

    If no composition info is available, assume standard adult travel
    rather than falling through to default.
    """
    composition = packet.facts.get("party_composition")
    if composition and composition.value is not None:
        # Have composition info, let main rule handle it
        return None

    # No composition info - assume standard adult travel
    return {
        "risk_level": "low",
        "reasoning": "No specific traveler composition information - assuming standard adult travel profile",
        "concerns": [],
        "recommendations": [],
    }


def rule_elderly_toddler_no_composition(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Return low risk for elderly/toddler when composition is unknown.

    If we don't have party_composition data, we can't assess specific
    elderly or toddler risks, so assume low risk rather than default.
    """
    composition = packet.facts.get("party_composition")
    if composition and composition.value is not None:
        # Have composition info, let main rules handle it
        return None

    # No composition info - can't assess specific risks
    # Return low for both elderly and toddler decisions
    return {
        "risk_level": "low",
        "reasoning": "No traveler composition data available - unable to assess specific elderly/toddler risks",
        "concerns": [],
        "recommendations": ["Gather traveler composition information for detailed risk assessment"],
    }
