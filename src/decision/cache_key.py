"""
decision.cache_key — Deterministic cache key generation for decisions.

This module provides functions to generate consistent cache keys from
CanonicalPacket inputs. The same inputs should always produce the same key.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from intake.packet_models import CanonicalPacket


def generate_cache_key(
    decision_type: str,
    packet: CanonicalPacket,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a deterministic cache key from inputs.

    Only includes fields that actually affect the decision.
    Sorted and normalized for stable hashing.

    Args:
        decision_type: Type of decision (e.g., "elderly_mobility_risk")
        packet: The CanonicalPacket to extract inputs from
        context: Additional context that affects the decision

    Returns:
        A 32-character hex string (SHA-256 hash)
    """
    # Normalize packet to decision-relevant fields
    relevant_fields = _get_relevant_fields(decision_type, packet)

    # Sort and serialize for stable hashing
    normalized = json.dumps(relevant_fields, sort_keys=True, default=str)

    # Add context if provided
    if context:
        normalized += json.dumps(context, sort_keys=True, default=str)

    # Hash for compact key
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def _get_relevant_fields(decision_type: str, packet: CanonicalPacket) -> Dict[str, Any]:
    """
    Extract only fields that matter for this decision type.

    Different decision types care about different packet fields.
    This keeps cache keys focused and avoids false cache misses.
    """
    if decision_type == "elderly_mobility_risk":
        return {
            "destination": _extract_value(packet, "destination_candidates"),
            "has_elderly": _has_composition_member(packet, "elderly"),
            "elderly_count": _get_composition_count(packet, "elderly"),
        }

    elif decision_type == "toddler_pacing_risk":
        return {
            "destination": _extract_value(packet, "destination_candidates"),
            "has_toddler": _has_composition_member(packet, "toddler"),
            "toddler_ages": _extract_value(packet, "child_ages"),
            "duration_days": _get_trip_duration(packet),
        }

    elif decision_type == "budget_feasibility":
        return {
            "destination": _extract_value(packet, "destination_candidates"),
            "resolved_destination": _extract_value(packet, "resolved_destination"),
            "budget_min": _extract_value(packet, "budget_min"),
            "party_size": _extract_value(packet, "party_size"),
            "duration_days": _get_trip_duration(packet),
            "domestic_or_intl": _extract_value(packet.derived_signals, "domestic_or_international"),
        }

    elif decision_type == "visa_timeline_risk":
        return {
            "destination": _extract_value(packet, "destination_candidates"),
            "domestic_or_intl": _extract_value(packet.derived_signals, "domestic_or_international"),
            "urgency": _extract_value(packet.derived_signals, "urgency"),
            "visa_required": _extract_visa_requirement(packet),
        }

    elif decision_type == "composition_risk":
        return {
            "destination": _extract_value(packet, "destination_candidates"),
            "party_composition": _extract_value(packet, "party_composition"),
        }

    else:
        # Default: include all facts (fallback, less efficient)
        return {
            "facts": {k: _extract_value(packet.facts, k) for k in packet.facts},
            "derived_signals": {k: _extract_value(packet.derived_signals, k) for k in packet.derived_signals},
        }


def _extract_value(container: Any, key: str) -> Any:
    """
    Extract a value from a packet container (facts, derived_signals, etc.).

    Handles Slot objects and returns the underlying value.
    """
    if container is None:
        return None

    if hasattr(container, "get"):
        # Dictionary-like
        value = container.get(key)
        if value is not None:
            # If it's a Slot, extract the value
            if hasattr(value, "value"):
                return value.value
            return value
        return None

    if hasattr(container, "__getitem__"):
        # Also dictionary-like but without get()
        try:
            value = container[key]
            if hasattr(value, "value"):
                return value.value
            return value
        except (KeyError, TypeError):
            return None

    return None


def _has_composition_member(packet: CanonicalPacket, member_type: str) -> bool:
    """Check if packet has a specific composition member type."""
    comp = _extract_value(packet.facts, "party_composition")
    if comp and isinstance(comp, dict):
        count = comp.get(member_type, 0)
        return count > 0
    return False


def _get_composition_count(packet: CanonicalPacket, member_type: str) -> int:
    """Get count of a specific composition member type."""
    comp = _extract_value(packet.facts, "party_composition")
    if comp and isinstance(comp, dict):
        return comp.get(member_type, 0)
    return 0


def _get_trip_duration(packet: CanonicalPacket) -> Optional[int]:
    """
    Extract trip duration in days.

    Tries multiple fields to find duration.
    """
    # Try explicit duration field
    duration = _extract_value(packet.facts, "duration_days")
    if duration is not None:
        if isinstance(duration, (int, float)):
            return int(duration)

    # Try to calculate from date window
    date_start = _extract_value(packet.facts, "date_start")
    date_end = _extract_value(packet.facts, "date_end")

    if date_start and date_end:
        try:
            from datetime import datetime
            if isinstance(date_start, str):
                date_start = datetime.fromisoformat(date_start.replace("Z", "+00:00"))
            if isinstance(date_end, str):
                date_end = datetime.fromisoformat(date_end.replace("Z", "+00:00"))

            delta = date_end - date_start
            return delta.days
        except (ValueError, TypeError):
            pass

    return None


def _extract_visa_requirement(packet: CanonicalPacket) -> Optional[str]:
    """Extract visa requirement from packet."""
    visa = _extract_value(packet.facts, "visa_status")
    if visa and isinstance(visa, dict):
        return visa.get("requirement")
    return None


# For testing purposes
def make_test_key(decision_type: str, inputs: Dict[str, Any]) -> str:
    """
    Create a cache key from simple inputs (for testing without a full packet).

    Args:
        decision_type: Type of decision
        inputs: Dictionary of input values

    Returns:
        A 32-character hex string
    """
    normalized = json.dumps(inputs, sort_keys=True, default=str)
    return hashlib.sha256(f"{decision_type}:{normalized}".encode()).hexdigest()[:32]
