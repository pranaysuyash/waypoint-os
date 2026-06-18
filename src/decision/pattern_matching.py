"""
decision.pattern_matching — Match packet context against pattern overrides.

When an operator records a pattern-scope override, the context signature
(destination, party composition, etc.) is stored alongside it. This module
matches new packets against those stored signatures so future similar trips
receive the operator's learned signal.

Matching strategy:
  - Exact key match on all non-None fields.
  - Fuzzy match on destination (case-insensitive, alias-aware).
  - A match requires ALL stored signature fields to be satisfied.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Destination normalization aliases (same as cache_key._DESTINATION_ALIASES)
_DESTINATION_ALIASES: Dict[str, str] = {
    "Andamans": "Andaman",
    "Istanbul": "Turkey",
    "Paris": "Europe",
    "London": "Europe",
    "Tokyo": "Japan",
    "Osaka": "Japan",
    "Bangkok": "Thailand",
}


def _normalize_destination(dest: Any) -> str:
    """Normalize a destination value for comparison."""
    if dest is None:
        return ""
    if isinstance(dest, list):
        dest = dest[0] if dest else ""
    s = str(dest).strip().lower()
    # Resolve alias to canonical form
    canonical = _DESTINATION_ALIASES.get(dest, dest)
    if isinstance(canonical, str):
        s = canonical.strip().lower()
    return s


def _normalize_bool(val: Any) -> Optional[bool]:
    """Coerce various truthy representations to bool."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return None


def _match_signature_field(
    sig_key: str,
    sig_value: Any,
    packet_value: Any,
) -> bool:
    """Check if a single signature field matches the packet value."""
    if sig_value is None:
        return True  # None means "don't care"

    # Boolean fields (has_elderly, has_toddler, etc.)
    if sig_key.startswith("has_"):
        sig_bool = _normalize_bool(sig_value)
        pkt_bool = _normalize_bool(packet_value)
        if sig_bool is None:
            return True
        return sig_bool == pkt_bool

    # Destination fields — fuzzy match with aliases
    if sig_key in ("destination", "resolved_destination"):
        return _normalize_destination(sig_value) == _normalize_destination(packet_value)

    # Integer fields (elderly_count, toddler_ages, duration_days, party_size)
    if isinstance(sig_value, (int, float)):
        if packet_value is None:
            return False
        if isinstance(packet_value, (int, float)):
            return int(sig_value) == int(packet_value)
        # Lists: check membership
        if isinstance(packet_value, list):
            return int(sig_value) in [int(v) for v in packet_value if isinstance(v, (int, float))]
        return False

    # List fields (toddler_ages, party_composition)
    if isinstance(sig_value, list):
        if packet_value is None:
            return False
        if isinstance(packet_value, list):
            # Check overlap
            return bool(set(str(v) for v in sig_value) & set(str(v) for v in packet_value))
        return str(packet_value) in [str(v) for v in sig_value]

    # String fields — case-insensitive containment
    sig_str = str(sig_value).strip().lower()
    if packet_value is None:
        return False
    pkt_str = str(packet_value).strip().lower()
    return sig_str == pkt_str


def match_pattern_overrides(
    context_signature: Dict[str, Any],
    pattern_overrides: List[Dict[str, Any]],
    min_strength: int = 2,
) -> List[Dict[str, Any]]:
    """
    Find pattern overrides that match the given context signature.

    Args:
        context_signature: The packet's relevant fields (from get_context_signature).
        pattern_overrides: List of pattern override records from OverrideStore.
        min_strength: Minimum strength to consider a match (default 2).

    Returns:
        List of matching pattern overrides, sorted by strength descending.
    """
    if not context_signature or not pattern_overrides:
        return []

    matches: List[Dict[str, Any]] = []

    for pattern in pattern_overrides:
        sig = pattern.get("context_signature")
        if not sig or not isinstance(sig, dict):
            continue

        strength = pattern.get("strength", 0)
        if strength < min_strength:
            continue

        # Check that ALL signature fields in the pattern match the context
        all_match = True
        for key, value in sig.items():
            packet_value = context_signature.get(key)
            if not _match_signature_field(key, value, packet_value):
                all_match = False
                break

        if all_match:
            matches.append(pattern)

    matches.sort(key=lambda m: m.get("strength", 0), reverse=True)
    return matches
