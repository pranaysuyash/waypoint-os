"""
src/analytics/kdd/override_features — Feature extraction for KDD v0.

Pure functions that extract structured features from override events + their
decision_delta snapshots. No I/O; fully unit-testable.

Every override event in OverrideStore now carries a ``decision_delta`` dict
with ``ai_decision``, ``operator_decision``, and ``trip_context`` keys.
This module extracts a flat ``OverrideFeatureVector`` from that enrichment.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.analytics.kdd.models import OverrideFeatureVector


# Version that must be bumped whenever the feature schema changes.
# Stored alongside each cluster so we can re-mine deterministically.
FEATURE_VERSION = "v0.1.0"


def extract_features(
    override: Dict[str, Any],
    agency_id: str,
) -> Optional[OverrideFeatureVector]:
    """Extract a feature vector from a single override event.

    Expects the override to have the ``decision_delta`` field populated
    (set by ``legacy_ops._capture_decision_delta`` during override creation).
    If ``decision_delta`` is missing, falls back gracefully by extracting
    what is available from the top-level override fields.

    Args:
        override: A single override record (dict) from OverrideStore.
        agency_id: The agency this override belongs to.

    Returns:
        An OverrideFeatureVector if the override has minimum required fields,
        or None if the override cannot be parsed.
    """
    override_id = override.get("override_id", "")
    trip_id = override.get("trip_id", "")
    if not override_id or not trip_id:
        return None

    created_at = override.get("created_at", "")
    flag = override.get("flag", "")
    action = override.get("action", "")
    if not flag or not action:
        return None

    delta = override.get("decision_delta") or {}
    ai = delta.get("ai_decision", {}) or {}
    op = delta.get("operator_decision", {}) or {}
    tc = delta.get("trip_context", {}) or {}

    # Extract AI decision features
    ai_state = ai.get("decision_state")
    ai_confidence = _to_float(ai.get("confidence"))
    ai_mode = ai.get("operating_mode")
    ai_flag_count = ai.get("flag_count", 0) or 0
    ai_severe = ai.get("severe_flags", []) or []

    # Extract trip context features
    destination = _first_string(tc.get("destination"))
    party_size = _to_int(tc.get("party_size"))
    duration_days = _to_int(tc.get("duration_days"))
    trip_stage = tc.get("stage")
    trip_status = tc.get("status")
    trip_source = tc.get("source")

    return OverrideFeatureVector(
        override_id=override_id,
        trip_id=trip_id,
        agency_id=agency_id,
        created_at=created_at,
        flag=flag,
        action=action,
        scope=override.get("scope", "this_trip"),
        original_severity=override.get("original_severity") or op.get("original_severity"),
        new_severity=override.get("new_severity") or op.get("new_severity"),
        ai_decision_state=ai_state,
        ai_confidence=ai_confidence,
        ai_operating_mode=ai_mode,
        ai_flag_count=_to_int(ai_flag_count),
        ai_severe_flags=ai_severe if isinstance(ai_severe, list) else [],
        trip_stage=trip_stage,
        trip_status=trip_status,
        trip_source=trip_source,
        destination=destination,
        party_size=party_size,
        duration_days=duration_days,
    )


def extract_batch(
    overrides: List[Dict[str, Any]],
    agency_id: str,
) -> List[OverrideFeatureVector]:
    """Extract feature vectors from a batch of override records.

    Silently skips overrides that cannot be parsed (missing required fields).
    """
    vectors: List[OverrideFeatureVector] = []
    for override in overrides:
        vec = extract_features(override, agency_id)
        if vec is not None:
            vectors.append(vec)
    return vectors


def cluster_key(vector: OverrideFeatureVector) -> Tuple[str, str, str, str]:
    """Return a grouping key for clustering: (flag, action, ai_decision_state, trip_source).

    Two overrides with the same cluster_key are candidates for the same cluster.
    This is intentionally coarse — the clustering phase applies a similarity
    threshold over the full feature vector.
    """
    return (
        vector.flag or "",
        vector.action or "",
        vector.ai_decision_state or "unknown",
        vector.trip_source or "unknown",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _first_string(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, list) and val:
        if isinstance(val[0], str):
            return val[0]
        if isinstance(val[0], dict):
            return val[0].get("value") or str(val[0])
        return str(val[0])
    if isinstance(val, dict):
        return val.get("value") or val.get("name") or str(val)
    return str(val)
