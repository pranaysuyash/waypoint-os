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

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

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

    except (OSError, KeyError, TypeError, AttributeError) as e:
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

    except (OSError, KeyError, AttributeError) as e:
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


# =============================================================================
# Closed-Loop Learning Pipeline (P0)
# =============================================================================

# Minimum trip-level overrides before a pattern can be auto-graduated
GRADUATION_THRESHOLD = 3

# Maximum strength a pattern can reach from graduation alone
MAX_GRADUATION_STRENGTH = 10


RolloutMode = str  # Type alias for readability

ROLLOUT_MODE_NONE: RolloutMode = "none"
ROLLOUT_MODE_PATTERN_ENRICHED: RolloutMode = "pattern_enriched"
ROLLOUT_MODE_PATTERN_STRENGTHENED: RolloutMode = "pattern_strengthened"
ROLLOUT_MODE_GRADUATED: RolloutMode = "graduated"
ROLLOUT_MODE_CACHE_INVALIDATED: RolloutMode = "cache_invalidated"
ROLLOUT_MODE_DISABLED: RolloutMode = "disabled"


def learn_from_operator_override(
    trip_id: str,
    override_data: Dict[str, Any],
    learn_from_overrides_enabled: bool = True,
    graduation_threshold: int = GRADUATION_THRESHOLD,
) -> Dict[str, Any]:
    """
    Closed-loop learning entry point — called when an operator creates an override.

    This function runs the concrete mutation classes that were previously only
    conceptual:

    1. Context Extraction — extracts the packet context signature from the trip
       and attaches it to pattern-scope overrides so future matching works.
    2. Pattern Strengthening — if a matching pattern already exists, increments
       its strength rather than creating a duplicate.
    3. Rule Graduation — after enough trip-level overrides accumulate for the
       same flag + decision_type, auto-creates a pattern override.
    4. Cache Invalidation — records feedback on cached decisions so stale
       decisions are evicted.
    5. Rollout Metadata — returns structured metadata about what mutations
       were applied, enabling the frontend and audit trail to understand
       how the system learned.

    Args:
        trip_id: The trip being overridden.
        override_data: The raw override dict (as saved to OverrideStore).
        learn_from_overrides_enabled: Whether the agency has learning enabled.
        graduation_threshold: Minimum trip-level overrides before graduation.

    Returns:
        Dict with keys:
            rollout_mode: str — what kind of learning occurred.
            mutations_applied: List[str] — specific mutations executed.
            context_signature: Optional[dict] — extracted context (for audit).
            graduation_created: Optional[dict] — pattern override created by graduation.
            cache_invalidated: bool — whether cache feedback was recorded.
    """
    result: Dict[str, Any] = {
        "rollout_mode": ROLLOUT_MODE_NONE,
        "mutations_applied": [],
        "context_signature": None,
        "graduation_created": None,
        "cache_invalidated": False,
    }

    if not learn_from_overrides_enabled:
        result["rollout_mode"] = ROLLOUT_MODE_DISABLED
        return result

    override_store = _get_override_store()
    flag_name = override_data.get("flag", "")
    decision_type = override_data.get("decision_type") or flag_name
    scope = override_data.get("scope", "this_trip")
    action = override_data.get("action", "")

    # --- Step 1: Context Extraction ---
    context_signature = _extract_trip_context_signature(trip_id, decision_type)
    result["context_signature"] = context_signature

    # --- Step 2: Pattern Enrichment (scope=pattern) ---
    if scope == "pattern" and context_signature:
        enriched = _enrich_pattern_with_context(
            override_store, override_data, context_signature, decision_type
        )
        if enriched:
            result["mutations_applied"].append("pattern_context_enriched")
            result["rollout_mode"] = ROLLOUT_MODE_PATTERN_ENRICHED

    # --- Step 3: Rule Graduation ---
    graduation = _check_and_graduate(
        trip_id, flag_name, decision_type, context_signature,
        override_store=override_store,
        graduation_threshold=graduation_threshold,
    )
    if graduation:
        result["mutations_applied"].append("rule_graduated")
        result["graduation_created"] = graduation
        result["rollout_mode"] = ROLLOUT_MODE_GRADUATED

    # --- Step 4: Cache Invalidation ---
    cache_key = override_data.get("cache_key")
    if cache_key and decision_type:
        invalidated = _record_cache_feedback(
            cache_key, decision_type, success=False
        )
        if invalidated:
            result["mutations_applied"].append("cache_invalidated")
            result["cache_invalidated"] = True
            if result["rollout_mode"] == ROLLOUT_MODE_NONE:
                result["rollout_mode"] = ROLLOUT_MODE_CACHE_INVALIDATED

    # Log the learning event
    if result["mutations_applied"]:
        logger.info(
            "Closed-loop learning for override on %s/%s: mode=%s mutations=%s",
            trip_id, flag_name, result["rollout_mode"], result["mutations_applied"],
        )

    return result


def _extract_trip_context_signature(
    trip_id: str,
    decision_type: str,
) -> Optional[Dict[str, Any]]:
    """
    Extract a context signature from the trip's stored packet data.

    The trip's "extracted" field contains the CanonicalPacket data as a dict.
    We extract the same fields that get_context_signature() would return from
    a live CanonicalPacket, enabling pattern matching for future overrides.
    """
    try:
        from spine_api.persistence import TripStore

        trip = TripStore.get_trip(trip_id)
        if not trip:
            return None

        extracted = trip.get("extracted") or {}
        if not extracted:
            return None

        # Build a minimal context signature from stored packet fields.
        # Mirror the field extraction from cache_key._get_relevant_fields().
        facts = extracted.get("facts") or {}
        derived = extracted.get("derived_signals") or {}

        context: Dict[str, Any] = {}

        # Destination (present in all decision types)
        dest_candidates = facts.get("destination_candidates")
        if dest_candidates:
            if isinstance(dest_candidates, list):
                context["destination"] = dest_candidates[0] if dest_candidates else None
            else:
                context["destination"] = dest_candidates

        resolved_dest = facts.get("resolved_destination")
        if resolved_dest:
            context["resolved_destination"] = resolved_dest

        # Composition fields
        composition = facts.get("party_composition")
        if composition and isinstance(composition, dict):
            context["has_elderly"] = composition.get("elderly", 0) > 0
            context["elderly_count"] = composition.get("elderly", 0)
            context["has_toddler"] = composition.get("toddler", 0) > 0

        child_ages = facts.get("child_ages")
        if child_ages:
            context["toddler_ages"] = child_ages

        # Duration
        duration = facts.get("duration_days")
        if duration is not None:
            context["duration_days"] = duration

        # Party size
        party_size = facts.get("party_size")
        if party_size is not None:
            context["party_size"] = party_size

        # Budget
        budget_min = facts.get("budget_min")
        if budget_min is not None:
            context["budget_min"] = budget_min

        # International/domestic
        dom_intl = derived.get("domestic_or_international")
        if dom_intl is not None:
            context["domestic_or_intl"] = dom_intl

        # Urgency
        urgency = derived.get("urgency")
        if urgency is not None:
            context["urgency"] = urgency

        # Visa
        visa = facts.get("visa_status")
        if visa and isinstance(visa, dict):
            context["visa_required"] = visa.get("requirement")

        return context if context else None

    except (OSError, KeyError, TypeError, AttributeError) as exc:
        logger.debug(
            "Context extraction failed for trip %s / %s: %s",
            trip_id, decision_type, exc,
        )
        return None


def _enrich_pattern_with_context(
    override_store: Any,
    override_data: Dict[str, Any],
    context_signature: Dict[str, Any],
    decision_type: str,
) -> bool:
    """
    Attach context signature to a pattern override.

    If a matching pattern (same context_signature) already exists, strengthens
    it rather than creating a duplicate.  If not, creates a new pattern with
    strength=1.

    Returns True if a pattern was created or strengthened.
    """
    try:
        existing_patterns = override_store.get_pattern_overrides(decision_type)

        # Check for an existing pattern with the same context signature
        if existing_patterns and context_signature:
            matches = match_pattern_overrides(
                context_signature, existing_patterns, min_strength=0,
            )
            if matches:
                # Strengthen the existing pattern
                best = matches[0]
                old_strength = best.get("strength", 0)
                best["strength"] = min(old_strength + 1, MAX_GRADUATION_STRENGTH)
                best["confirmed_by_later_runs"] = best.get("confirmed_by_later_runs", 0) + 1
                best["last_reinforced_at"] = datetime.now(timezone.utc).isoformat()

                # Rewrite the pattern file with updated strength
                _rewrite_pattern_file(
                    override_store, decision_type, existing_patterns
                )
                logger.info(
                    "Strengthened pattern %s: strength %d → %d",
                    best.get("pattern_id", "unknown"),
                    old_strength, best["strength"],
                )
                return True

        # No existing match — create a new pattern.
        # Copy only cross-trip fields; avoid leaking trip_id/override_id into patterns.
        pattern_data = {
            "flag": override_data.get("flag"),
            "decision_type": override_data.get("decision_type"),
            "action": override_data.get("action"),
            "new_severity": override_data.get("new_severity"),
            "overridden_by": override_data.get("overridden_by"),
            "reason": override_data.get("reason"),
            "context_signature": context_signature,
            "strength": 1,
            "confirmed_by_later_runs": 0,
            "pattern_id": f"pat_{uuid4().hex[:12]}",
            "created_as_pattern": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        override_store._add_pattern_override(pattern_data)
        logger.info(
            "Created new pattern %s for %s (strength=1)",
            pattern_data["pattern_id"], decision_type,
        )
        return True

    except (OSError, KeyError, AttributeError) as exc:
        logger.warning("Pattern enrichment failed: %s", exc)
        return False


def _rewrite_pattern_file(
    override_store: Any,
    decision_type: str,
    patterns: List[Dict[str, Any]],
) -> None:
    """
    Rewrite a pattern file with updated pattern records.

    Uses the same file_lock + write path as the original store to ensure
    atomicity.
    """
    import os
    from pathlib import Path
    from spine_api.persistence import file_lock

    patterns_dir = Path(override_store.OVERRIDES_PATTERNS_DIR)
    pattern_file = patterns_dir / f"{decision_type}.jsonl"
    with file_lock(pattern_file):
        tmp = pattern_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            for p in patterns:
                f.write(json.dumps(p) + "\n")
        os.replace(tmp, pattern_file)


def _check_and_graduate(
    trip_id: str,
    flag_name: str,
    decision_type: str,
    context_signature: Optional[Dict[str, Any]],
    override_store: Any = None,
    graduation_threshold: int = GRADUATION_THRESHOLD,
) -> Optional[Dict[str, Any]]:
    """
    Check if enough trip-level overrides exist to auto-create a pattern.

    After `graduation_threshold` overrides of the same flag + decision_type,
    creates a graduated pattern override so future similar trips benefit.

    Returns the graduated pattern dict if one was created, None otherwise.
    """
    try:
        if override_store is None:
            override_store = _get_override_store()

        # Don't graduate if context extraction failed
        if not context_signature:
            return None

        # Count existing patterns for this decision_type to avoid duplicates
        existing_patterns = override_store.get_pattern_overrides(decision_type)
        if existing_patterns:
            matches = match_pattern_overrides(
                context_signature, existing_patterns, min_strength=0,
            )
            if matches:
                # Pattern already exists for this context — don't duplicate
                return None

        # Count trip-level overrides for this flag across all trips.
        # Scan per-trip override files for matching flag + decision_type.
        from spine_api import persistence as _persistence_mod
        OVERRIDES_PER_TRIP_DIR = _persistence_mod.OVERRIDES_PER_TRIP_DIR
        override_count = 0
        dominant_action = "suppress"
        action_counts: Dict[str, int] = {}
        if OVERRIDES_PER_TRIP_DIR.exists():
            for trip_file in OVERRIDES_PER_TRIP_DIR.glob("*.jsonl"):
                try:
                    with open(trip_file) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                rec = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if (
                                rec.get("flag") == flag_name
                                and rec.get("decision_type") == decision_type
                                and not rec.get("rescinded", False)
                                and rec.get("trip_id") != trip_id
                            ):
                                override_count += 1
                                act = rec.get("action", "suppress")
                                action_counts[act] = action_counts.get(act, 0) + 1
                except (OSError, ValueError, KeyError):
                    continue
        if action_counts:
            dominant_action = max(action_counts, key=action_counts.get)  # type: ignore[arg-type]

        if override_count < graduation_threshold - 1:
            # Not enough overrides yet (need threshold total including current)
            return None

        # Graduate: create a pattern override inheriting the dominant action
        graduated = {
            "pattern_id": f"pat_{uuid4().hex[:12]}",
            "flag": flag_name,
            "decision_type": decision_type,
            "action": dominant_action,
            "scope": "pattern",
            "context_signature": context_signature,
            "strength": min(override_count + 1, MAX_GRADUATION_STRENGTH),
            "confirmed_by_later_runs": override_count,
            "graduated_from": "trip_level",
            "graduation_trip_count": override_count + 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "overridden_by": "system",
            "reason": f"Auto-graduated after {override_count + 1} operator overrides of '{flag_name}'",
        }

        override_store._add_pattern_override(graduated)
        logger.info(
            "Auto-graduated pattern for %s/%s after %d overrides (strength=%d)",
            decision_type, flag_name, override_count + 1, graduated["strength"],
        )
        return graduated

    except (OSError, KeyError, TypeError, AttributeError) as exc:
        logger.warning("Graduation check failed: %s", exc)
        return None
