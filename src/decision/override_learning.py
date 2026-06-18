"""
decision.override_learning — Apply operator overrides to future decisions.

This module implements the learning loop described in AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md.
When an operator records an override (suppress/downgrade/acknowledge), this module:

1. Checks trip-level overrides and applies them to risk flags
2. Checks pattern-level overrides and adds soft confidence hints
3. Re-evaluates decision state invariants after adjustments
4. Records feedback on cached decisions for cache invalidation

Safety invariants:
- document_risk, visa_not_applied, traveler_safe_leakage_risk cannot be suppressed
- Only acknowledged for these safety-critical flags
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.intake.packet_models import CanonicalPacket
from src.decision.pattern_matching import match_pattern_overrides
from src.decision.cache_key import get_context_signature

logger = logging.getLogger(__name__)

# Safety-critical flags that cannot be suppressed or downgraded
SAFETY_INVARIANT_FLAGS = frozenset({
    "document_risk",
    "visa_not_applied",
    "traveler_safe_leakage_risk",
})

# Minimum pattern strength before patterns influence scoring
DEFAULT_PATTERN_MIN_STRENGTH = 2


def _get_override_store():
    """Lazy import to avoid circular dependencies."""
    from spine_api.persistence import OverrideStore
    return OverrideStore


def _get_cache_storage():
    """Lazy import to cache storage."""
    from src.decision.cache_storage import get_default_storage
    return get_default_storage()


def apply_override_adjustments(
    risk_flags: List[Dict[str, Any]],
    trip_id: str,
    packet: CanonicalPacket,
    decision_type: Optional[str] = None,
    cache_key: Optional[str] = None,
    pattern_min_strength: int = DEFAULT_PATTERN_MIN_STRENGTH,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply stored overrides to risk flags.

    This function runs after generate_risk_flags() but before the DecisionResult
    is returned. It modifies the risk_flags list and returns override metadata.

    Args:
        risk_flags: List of risk flag dictionaries from generate_risk_flags()
        trip_id: Current trip ID
        packet: CanonicalPacket for context signature extraction
        decision_type: Optional decision type for pattern matching
        cache_key: Optional cache key for feedback recording
        pattern_min_strength: Minimum strength for pattern overrides (default 2)

    Returns:
        Tuple of (adjusted_risk_flags, override_metadata)
        override_metadata contains what was applied for audit/rationale
    """
    if not risk_flags:
        return risk_flags, {}

    override_store = _get_override_store()
    metadata: Dict[str, Any] = {
        "trip_overrides_applied": {},
        "pattern_hints": {},
        "cache_feedback_recorded": False,
    }

    adjusted_flags = []
    flags_to_remove = set()

    for flag in risk_flags:
        flag_name = flag.get("flag", "")
        if not flag_name:
            adjusted_flags.append(flag)
            continue

        # Safety invariant check — cannot suppress safety flags
        is_safety_invariant = flag_name in SAFETY_INVARIANT_FLAGS

        # Check trip-level overrides
        trip_overrides = override_store.get_active_overrides_for_flag(trip_id, flag_name)
        applied_override = _apply_trip_overrides(
            flag, trip_overrides, is_safety_invariant, flag_name
        )

        if applied_override:
            action = applied_override.get("action")
            if action == "suppress":
                # Flag removed — don't add to adjusted_flags
                flags_to_remove.add(flag_name)
                metadata["trip_overrides_applied"][flag_name] = applied_override
                continue
            elif action == "downgrade":
                # Severity changed — add annotated flag
                adjusted_flags.append(flag)
                metadata["trip_overrides_applied"][flag_name] = applied_override
                continue
            elif action == "acknowledge":
                # Flag preserved but annotated — owner accepted risk
                adjusted_flags.append(flag)
                metadata["trip_overrides_applied"][flag_name] = applied_override
                continue

        # No trip-level override — check pattern overrides
        if decision_type and not is_safety_invariant:
            pattern_hint = _check_pattern_override(
                packet, decision_type, flag_name, pattern_min_strength,
                override_store=override_store,
            )
            if pattern_hint:
                flag["pattern_override_hint"] = pattern_hint
                metadata["pattern_hints"][flag_name] = pattern_hint

        adjusted_flags.append(flag)

    # Record cache feedback for suppressed flags
    if flags_to_remove and cache_key and decision_type:
        _record_cache_feedback(cache_key, decision_type, success=False)
        metadata["cache_feedback_recorded"] = True

    return adjusted_flags, metadata


def _apply_trip_overrides(
    flag: Dict[str, Any],
    trip_overrides: List[Dict[str, Any]],
    is_safety_invariant: bool,
    flag_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Apply trip-level overrides to a single risk flag.

    Returns the applied override metadata if an override was applied, None otherwise.
    """
    if not trip_overrides:
        return None

    # Get the most recent non-rescinded override (already sorted by OverrideStore)
    override = trip_overrides[-1]
    action = override.get("action", "")
    override_id = override.get("override_id", "unknown")
    overridden_by = override.get("overridden_by", "unknown")
    reason = override.get("reason", "")

    # Safety invariant enforcement
    if is_safety_invariant and action in ("suppress", "downgrade"):
        logger.warning(
            "Safety invariant flag %s cannot be %s — ignoring override %s",
            flag_name, action, override_id,
        )
        return None

    if action == "suppress":
        logger.info(
            "Suppressing flag %s per override %s (by %s)",
            flag_name, override_id, overridden_by,
        )
        return {
            "override_id": override_id,
            "action": "suppress",
            "overridden_by": overridden_by,
            "reason": reason,
        }

    elif action == "downgrade":
        new_severity = override.get("new_severity")
        if not new_severity:
            logger.warning(
                "Downgrade override %s missing new_severity — ignoring",
                override_id,
            )
            return None

        original_severity = flag.get("severity", "low")
        flag["severity"] = new_severity
        logger.info(
            "Downgrading flag %s from %s to %s per override %s",
            flag_name, original_severity, new_severity, override_id,
        )
        return {
            "override_id": override_id,
            "action": "downgrade",
            "original_severity": original_severity,
            "new_severity": new_severity,
            "overridden_by": overridden_by,
            "reason": reason,
        }

    elif action == "acknowledge":
        # Keep flag as-is but annotate — owner accepted risk
        flag["override_acknowledged"] = True
        flag["acknowledged_by"] = overridden_by
        flag["acknowledgement_reason"] = reason
        logger.info(
            "Acknowledging flag %s per override %s (by %s)",
            flag_name, override_id, overridden_by,
        )
        return {
            "override_id": override_id,
            "action": "acknowledge",
            "overridden_by": overridden_by,
            "reason": reason,
        }

    return None


def _check_pattern_override(
    packet: CanonicalPacket,
    decision_type: str,
    flag_name: str,
    min_strength: int,
    override_store: Any = None,
) -> Optional[Dict[str, Any]]:
    """
    Check if any pattern overrides match the current packet context.

    Returns a hint dict if a matching pattern is found, None otherwise.
    """
    try:
        if override_store is None:
            override_store = _get_override_store()
        pattern_overrides = override_store.get_pattern_overrides(decision_type)

        if not pattern_overrides:
            return None

        context_signature = get_context_signature(decision_type, packet)
        if not context_signature:
            return None

        matches = match_pattern_overrides(
            context_signature,
            pattern_overrides,
            min_strength=min_strength,
        )

        if not matches:
            return None

        # Use the strongest match
        best_match = matches[0]
        strength = best_match.get("strength", 0)
        pattern_id = best_match.get("pattern_id", "unknown")
        override_count = best_match.get("confirmed_by_later_runs", 0) + 1

        logger.info(
            "Pattern override match for %s: pattern_id=%s strength=%d overrides=%d",
            flag_name, pattern_id, strength, override_count,
        )

        return {
            "pattern_id": pattern_id,
            "strength": strength,
            "confidence": "soft",
            "note": f"Previously overridden in {override_count} similar cases",
            "action": best_match.get("action", "suppress"),
        }

    except Exception as e:
        logger.warning("Pattern override check failed for %s: %s", flag_name, e)
        return None


def _record_cache_feedback(
    cache_key: str,
    decision_type: str,
    success: bool,
    cache_storage: Any = None,
) -> bool:
    """
    Record feedback on a cached decision.

    Uses the exponential moving average in CachedDecision.record_feedback().
    When success=False, the success_rate drops, eventually causing is_valid()
    to return False and the entry to be evicted on next access.

    Returns True if feedback was recorded, False otherwise.
    """
    try:
        cache_storage = _get_cache_storage()
        cached = cache_storage.get(cache_key, decision_type)

        if cached is None:
            # Cache entry doesn't exist — nothing to invalidate
            return False

        cached.record_feedback(success=success)
        cache_storage.set(cache_key, decision_type, cached)

        logger.info(
            "Recorded cache feedback for %s/%s: success=%s new_rate=%.2f",
            decision_type, cache_key[:8], success, cached.success_rate,
        )
        return True

    except Exception as e:
        logger.warning("Cache feedback recording failed: %s", e)
        return False


def should_suppress_flag_for_decision_state(
    flag_name: str,
    override_metadata: Dict[str, Any],
) -> bool:
    """
    Check if a flag was suppressed by an override and should not count
    toward decision_state escalation.

    Returns True if the flag was suppressed, False otherwise.
    """
    trip_overrides = override_metadata.get("trip_overrides_applied", {})
    override_info = trip_overrides.get(flag_name)
    if override_info and override_info.get("action") == "suppress":
        return True
    return False


def get_overrides_summary_for_rationale(
    override_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract override summary for inclusion in DecisionResult.rationale.

    Returns a dict with overrides_applied and pattern_hints keys.
    """
    return {
        "overrides_applied": override_metadata.get("trip_overrides_applied", {}),
        "pattern_hints": override_metadata.get("pattern_hints", {}),
    }
