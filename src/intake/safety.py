"""
intake.safety — NB03 v0.2: Structural Traveler-Safe Sanitization.

This module implements structural sanitization — internal data is not even
passed to the traveler-safe builder (not just hidden from output).

Contract: notebooks/NB03_V02_SPEC.md
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Set

from .packet_models import (
    CanonicalPacket,
    Slot,
    OwnerConstraint,
    Ambiguity,
)


# =============================================================================
# SECTION 1: FORBIDDEN CONCEPTS (leakage detection)
# =============================================================================

# Terms that must never appear in traveler-facing content.
# Each entry is a base form; the check expands to catch plurals and common variants.
# The word-boundary regex ensures exact-match (not substring), and variant expansion
# catches "hypotheses", "blockers", "ambiguities", etc.
FORBIDDEN_TRAVELER_CONCEPTS = {
    "unknown",
    "hypothesis",
    "hypotheses",
    "contradiction",
    "contradictions",
    "blocker",
    "blockers",
    "hard_blocker",
    "hard_blockers",
    "soft_blocker",
    "soft_blockers",
    "internal_only",
    "owner_constraint",
    "owner_constraints",
    "agency_note",
    "agency_notes",
    "decision_state",
    "decision states",
    "confidence_score",
    "confidence scores",
    "ambiguity",
    "ambiguities",
}

# Field names that are internal-only and must be stripped
INTERNAL_ONLY_FIELDS = {
    "agency_notes",
    "owner_priority_signals",
    "owner_margins",
    "commission_rate",
    "net_cost",
    "internal_flags",
}

# Fields that need transformation before being traveler-safe
TRANSFORM_REQUIRED_FIELDS = {
    "owner_constraints",
    "risk_flags",
}


# =============================================================================
# SECTION 2: STRUCTURAL SANITIZATION PIPELINE
# =============================================================================

class SanitizedPacketView:
    """
    A structurally sanitized view of a CanonicalPacket.

    This is NOT the raw packet — it's a filtered view with all internal-only
    data removed at the source level. The data is not even available to the
    traveler-safe builder, ensuring no leakage is possible.
    """

    def __init__(
        self,
        facts: Dict[str, Any],
        derived_signals: Optional[Dict[str, Any]] = None,
    ):
        self.facts = facts
        self.derived_signals = derived_signals or {}
        # Intentionally NO hypotheses, contradictions, unknowns, ambiguities
        # These are internal-only concepts

    def to_dict(self) -> dict:
        return {
            "facts": self.facts,
            "derived_signals": self.derived_signals,
        }


def sanitize_for_traveler(packet: CanonicalPacket) -> SanitizedPacketView:
    """
    Strip all internal-only data from packet before passing to traveler-safe builder.

    This is structural — the data is not even available to the builder, not just hidden.
    """
    sanitized_facts = {}
    sanitized_signals = {}

    # Process facts: filter out internal-only fields
    for field_name, slot in packet.facts.items():
        # Skip internal-only fields entirely
        if field_name in INTERNAL_ONLY_FIELDS:
            continue

        # Transform owner_constraints to traveler-safe version
        if field_name == "owner_constraints":
            visible_constraints = _extract_traveler_safe_constraints(slot.value)
            if visible_constraints:
                sanitized_facts[field_name] = _sanitize_slot(slot, visible_constraints)
            continue

        # Keep other fields as-is
        sanitized_facts[field_name] = slot

    # Process derived_signals: only keep traveler-safe ones that are ACTUALLY produced.
    # trip_duration_days and seasonality are NOT produced by NB01 — removed from
    # allowed list to avoid dead traveler-safe surface area. Re-add when implemented.
    traveler_safe_signals = {
        "domestic_or_international",
    }

    for field_name, slot in packet.derived_signals.items():
        if field_name in traveler_safe_signals:
            sanitized_signals[field_name] = slot

    return SanitizedPacketView(
        facts=sanitized_facts,
        derived_signals=sanitized_signals,
    )


def _extract_traveler_safe_constraints(constraints: Any) -> List[dict]:
    """
    Extract only traveler-safe-transformable owner constraints.

    OwnerConstraint objects have visibility field:
    - "internal_only": skip entirely
    - "traveler_safe_transformable": include (may need text transformation)
    """
    if not constraints:
        return []

    visible = []
    raw_list = constraints if isinstance(constraints, list) else [constraints]

    for item in raw_list:
        # Handle OwnerConstraint objects
        if isinstance(item, OwnerConstraint):
            if item.visibility == "traveler_safe_transformable":
                visible.append({
                    "text": _transform_constraint_text(item.text),
                    "visibility": "traveler_safe",
                })
        # Handle dict representations
        elif isinstance(item, dict):
            visibility = item.get("visibility", "internal_only")
            if visibility == "traveler_safe_transformable":
                text = item.get("text", "")
                visible.append({
                    "text": _transform_constraint_text(text),
                    "visibility": "traveler_safe",
                })

    return visible


def _transform_constraint_text(text: str) -> str:
    """
    Transform internal constraint language to traveler-safe phrasing.

    Examples:
    - "Owner markup required: 15%" → "Agency service fees apply"
    - "Margin protection: min ₹5000" → (skip, financial internal)
    - "Supplier restrictions: no refunds" → "Supplier terms apply"
    """
    text_lower = text.lower()

    # Skip financial-specific constraints
    if any(term in text_lower for term in ["markup", "margin", "commission", "net cost", "profit"]):
        # These are purely internal — don't share
        return ""

    # Transform other constraints to neutral language
    if "refund" in text_lower:
        return "Please review cancellation and refund policies."
    if "supplier" in text_lower and "restriction" in text_lower:
        return "Some supplier restrictions may apply."

    # Default: transform to generic statement
    return "Certain terms and conditions may apply."


def _sanitize_slot(slot: Slot, new_value: Any = None) -> Slot:
    """Create a sanitized slot with traveler-safe value."""
    return Slot(
        value=new_value if new_value is not None else slot.value,
        confidence=slot.confidence,
        authority_level=slot.authority_level,
        extraction_mode=slot.extraction_mode,
        evidence_refs=slot.evidence_refs,
        updated_at=slot.updated_at,
        notes=slot.notes,
    )


# =============================================================================
# SECTION 3: LEAKAGE DETECTION
# =============================================================================

# Strict leakage enforcement: when True, build_traveler_safe_bundle raises on leakage.
# Set via environment variable TRAVELER_SAFE_STRICT=1 or by calling set_strict_mode(True).
_STRICT_MODE: Optional[bool] = None


def set_strict_mode(enabled: bool) -> None:
    """Enable or disable strict leakage enforcement (raises on leakage)."""
    global _STRICT_MODE
    _STRICT_MODE = enabled


def _is_strict_mode() -> bool:
    """Check if strict leakage enforcement is active."""
    global _STRICT_MODE
    if _STRICT_MODE is not None:
        return _STRICT_MODE
    return os.environ.get("TRAVELER_SAFE_STRICT", "").strip() in ("1", "true", "yes")


def check_no_leakage(bundle_or_dict: Any) -> List[str]:
    """
    Verify that traveler-facing content contains no internal concepts.

    Args:
        bundle_or_dict: Either a PromptBundle object or a dict with user_message/system_context

    Returns:
        List of leakage messages (empty if no leakage detected)
    """
    leaks = []

    # Extract text fields based on input type
    if hasattr(bundle_or_dict, 'user_message'):
        text_fields = {
            "user_message": bundle_or_dict.user_message,
            "system_context": bundle_or_dict.system_context,
        }
    elif isinstance(bundle_or_dict, dict):
        text_fields = {
            "user_message": bundle_or_dict.get("user_message", ""),
            "system_context": bundle_or_dict.get("system_context", ""),
        }
    else:
        return ["Invalid input type for leakage check"]

    # Check each text field for forbidden concepts
    for field_name, text in text_fields.items():
        if not text:
            continue

        text_lower = text.lower()

        for forbidden in FORBIDDEN_TRAVELER_CONCEPTS:
            # Check for the forbidden term as a whole word (not substring)
            # to avoid false positives like "knowing" containing "unknown"
            pattern = r'\b' + re.escape(forbidden) + r'\b'
            if re.search(pattern, text_lower):
                # Get excerpt (first 100 chars)
                excerpt = text[:100] + "..." if len(text) > 100 else text
                leaks.append(f"Leakage detected: '{forbidden}' in {field_name} (excerpt: {excerpt})")

    return leaks


def validate_traveler_safe_output(output: Any) -> bool:
    """
    Quick boolean check: is this output traveler-safe?

    Returns True if no leakage detected.
    """
    leaks = check_no_leakage(output)
    return len(leaks) == 0


def enforce_no_leakage(bundle_or_dict: Any, strict: Optional[bool] = None) -> List[str]:
    """
    Verify that traveler-facing content contains no internal concepts.

    In strict mode (default in test, configurable via TRAVELER_SAFE_STRICT env),
    raises ValueError on leakage instead of just logging.

    Args:
        bundle_or_dict: Either a PromptBundle object or a dict with user_message/system_context
        strict: Override strict mode. None = use global config.

    Returns:
        List of leakage messages (empty if no leakage detected)

    Raises:
        ValueError: If strict mode is active and leakage is detected
    """
    leaks = check_no_leakage(bundle_or_dict)

    use_strict = strict if strict is not None else _is_strict_mode()
    if use_strict and leaks:
        raise ValueError(
            f"Traveler-safe leakage detected (strict mode): {'; '.join(leaks)}"
        )

    return leaks


# =============================================================================
# SECTION 4: AMBIGUITY HANDLING
# =============================================================================

def has_blocking_ambiguities(packet: CanonicalPacket) -> bool:
    """
    Check if packet has blocking ambiguities that prevent traveler-safe output.

    Blocking ambiguities (per NB03 spec):
    - unresolved_alternatives (destination)
    - destination_open
    - value_vague (party size)
    """
    blocking_types = {
        "unresolved_alternatives",
        "destination_open",
        "value_vague",
    }

    for amb in packet.ambiguities:
        if amb.ambiguity_type in blocking_types:
            return True

    return False


def get_advisory_ambiguities(packet: CanonicalPacket) -> List[Ambiguity]:
    """
    Get ambiguities that are advisory (not blocking).

    These can be mentioned in traveler-safe output with careful phrasing.
    """
    advisory = []
    blocking_types = {
        "unresolved_alternatives",
        "destination_open",
        "value_vague",
    }

    for amb in packet.ambiguities:
        if amb.ambiguity_type not in blocking_types:
            advisory.append(amb)

    return advisory


# =============================================================================
# SECTION 5: HYPOTHESIS HANDLING
# =============================================================================

def get_hypothesis_summary(packet: CanonicalPacket) -> Dict[str, Any]:
    """
    Get a summary of hypotheses for internal use only.

    This is NEVER passed to traveler-safe builders.
    """
    if not packet.hypotheses:
        return {}

    return {
        "count": len(packet.hypotheses),
        "fields": list(packet.hypotheses.keys()),
        "avg_confidence": sum(h.confidence for h in packet.hypotheses.values()) / len(packet.hypotheses),
    }


# =============================================================================
# SECTION 6: CONTRADICTION HANDLING
# =============================================================================

def get_contradiction_summary(packet: CanonicalPacket) -> Dict[str, Any]:
    """
    Get a summary of contradictions for internal use only.

    This is NEVER passed to traveler-safe builders.
    """
    if not packet.contradictions:
        return {}

    by_field = {}
    for c in packet.contradictions:
        field = c.get("field_name", "unknown")
        if field not in by_field:
            by_field[field] = []
        by_field[field].append(c.get("values", []))

    return {
        "count": len(packet.contradictions),
        "by_field": by_field,
    }


# =============================================================================
# SECTION 7: FIELD VISIBILITY HELPER
# =============================================================================

def is_field_traveler_safe(field_name: str) -> bool:
    """
    Check if a field is safe to show to travelers.

    Returns False for internal-only fields.
    """
    return field_name not in INTERNAL_ONLY_FIELDS


def is_field_internal_only(field_name: str) -> bool:
    """
    Check if a field is internal-only.

    Returns True for fields that should never be traveler-facing.
    """
    return field_name in INTERNAL_ONLY_FIELDS


def get_safe_field_value(packet: CanonicalPacket, field_name: str) -> Optional[Any]:
    """
    Get a field value only if it's traveler-safe.

    Returns None if the field is internal-only or doesn't exist.
    """
    if is_field_internal_only(field_name):
        return None

    # Check facts
    if field_name in packet.facts:
        return packet.facts[field_name].value

    # Check derived signals (only safe ones actually produced)
    safe_signals = {
        "domestic_or_international",
    }
    if field_name in safe_signals and field_name in packet.derived_signals:
        return packet.derived_signals[field_name].value

    return None


# =============================================================================
# SECTION 8: AUDIT HELPERS
# =============================================================================

def audit_packet_internal_data(packet: CanonicalPacket) -> Dict[str, Any]:
    """
    Audit a packet for internal data presence.

    Returns a summary of all internal-only content for audit purposes.
    """
    return {
        "hypotheses": get_hypothesis_summary(packet),
        "contradictions": get_contradiction_summary(packet),
        "ambiguities": {
            "total": len(packet.ambiguities),
            "blocking": sum(1 for a in packet.ambiguities if a.ambiguity_type in {
                "unresolved_alternatives", "destination_open", "value_vague",
            }),
            "advisory": sum(1 for a in packet.ambiguities if a.ambiguity_type not in {
                "unresolved_alternatives", "destination_open", "value_vague",
            }),
        },
        "internal_fields": [
            f for f in packet.facts.keys() if is_field_internal_only(f)
        ],
        "has_internal_owner_constraints": _has_internal_owner_constraints(packet),
    }


def _has_internal_owner_constraints(packet: CanonicalPacket) -> bool:
    """Check if packet has internal-only owner constraints."""
    oc_slot = packet.facts.get("owner_constraints")
    if not oc_slot or not oc_slot.value:
        return False

    for item in oc_slot.value if isinstance(oc_slot.value, list) else [oc_slot.value]:
        visibility = "internal_only"
        if isinstance(item, OwnerConstraint):
            visibility = item.visibility
        elif isinstance(item, dict):
            visibility = item.get("visibility", "internal_only")

        if visibility == "internal_only":
            return True

    return False


# =============================================================================
# SECTION 9: TEXT SANITIZATION (post-generation)
# =============================================================================

def sanitize_text_output(text: str) -> str:
    """
    Post-generation text sanitization as a safety net.

    This is a backup check — structural sanitization should prevent
    internal concepts from ever reaching text generation.

    Uses placeholder replacement for any leaked terms.
    """
    # Replace internal terms with traveler-safe alternatives
    replacements = {
        r'\bhypothes[ie]s\b': "consideration",
        r'\bhypothes[i]s\b': "consideration",
        r'\bcontradictions?\b': "clarification needed",
        r'\bblockers?\b': "item to confirm",
        r'\bhard[-_ ]?blockers?\b': "key detail needed",
        r'\bsoft[-_ ]?blockers?\b': "additional detail",
        r'\bambiguit(?:y|ies)\b': "point to clarify",
        r'\binternal_only\b': "",
        r'\bowner_constraints?\b': "requirement",
        r'\bagency_notes?\b': "",
        r'\bdecision_states?\b': "",
        r'\bconfidence_scores?\b': "",
    }

    sanitized = text
    for pattern, replacement in replacements.items():
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized