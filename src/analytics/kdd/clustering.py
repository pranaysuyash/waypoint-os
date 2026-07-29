"""
src/analytics/kdd/clustering — Override clustering for KDD v0.

Groups similar override events into clusters for the weekly digest. Uses a
deterministic grouping strategy based on (flag, action, decision_state, source)
with a min_cluster_size floor. No external ML dependencies — intentionally
simple for v0 with feature_centroid and algorithm columns for future upgrades.

Algorithm rationale for v0: exact-match clustering on the coarse cluster_key
is sufficient to surface the most common override patterns. If v0 proves
valuable, v0.1 can experiment with HDBSCAN or k-means on the full vector.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.analytics.kdd.models import OverrideFeatureVector, OverrideCluster
from src.analytics.kdd.override_features import cluster_key, FEATURE_VERSION


ALGORITHM = "exact-match-v1"
DEFAULT_MIN_CLUSTER_SIZE = 3
MAX_REPRESENTATIVE_SAMPLES = 3


def cluster_overrides(
    vectors: List[OverrideFeatureVector],
    agency_id: str,
    window_start: str,
    window_end: str,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
) -> List[OverrideCluster]:
    """Group override feature vectors into clusters.

    Clusters are formed by exact match on the ``cluster_key()`` tuple.
    Clusters with fewer than ``min_cluster_size`` members are discarded as noise.

    Args:
        vectors: List of feature vectors from extract_batch().
        agency_id: The agency these overrides belong to.
        window_start: ISO timestamp of the window start.
        window_end: ISO timestamp of the window end.
        min_cluster_size: Minimum override count for a valid cluster.

    Returns:
        A list of OverrideCluster objects, one per non-noise group.
    """
    if not vectors:
        return []

    # Group by cluster_key
    groups: Dict[tuple, List[OverrideFeatureVector]] = {}
    for vec in vectors:
        key = cluster_key(vec)
        if key not in groups:
            groups[key] = []
        groups[key].append(vec)

    mined_at = datetime.now(timezone.utc).isoformat()
    total = len(vectors)
    clusters: List[OverrideCluster] = []

    for _key, members in groups.items():
        if len(members) < min_cluster_size:
            # Noise floor — skip small groups
            continue

        flag = _key[0]  # The dominant flag (all share the same cluster_key)
        dominant_action = _key[1]
        sample_size = len(members)
        support = round(sample_size / total, 4) if total > 0 else 0.0

        # Sort by recency, pick representative samples
        sorted_members = sorted(
            members,
            key=lambda v: v.created_at or "",
            reverse=True,
        )
        representative = [
            _build_representative_sample(m)
            for m in sorted_members[:MAX_REPRESENTATIVE_SAMPLES]
        ]

        # Compute a deterministic cluster_id from the key + window
        cluster_id = _compute_cluster_id(_key, window_start, window_end)

        # Feature centroid: count-based for this v0 algorithm
        centroid = {
            "flag": flag,
            "dominant_action": dominant_action,
            "sample_size": sample_size,
            "action_counts": _count_values(members, "action"),
            "severity_distribution": _count_values(
                members, "original_severity", none_key="unset"
            ),
            "ai_states": _count_values(members, "ai_decision_state", none_key="unset"),
            "destinations": _count_values(members, "destination", none_key="unknown"),
        }

        clusters.append(OverrideCluster(
            cluster_id=cluster_id,
            agency_id=agency_id,
            mined_at=mined_at,
            window_start=window_start,
            window_end=window_end,
            algorithm=ALGORITHM,
            feature_version=FEATURE_VERSION,
            flag=flag,
            sample_size=sample_size,
            support=support,
            dominant_action=dominant_action,
            representative_samples=representative,
            feature_centroid=centroid,
            review_status="unreviewed",
        ))

    # Sort by sample_size descending (biggest patterns first)
    clusters.sort(key=lambda c: c.sample_size, reverse=True)
    return clusters


def _build_representative_sample(vec: OverrideFeatureVector) -> Dict[str, Any]:
    """Build an anonymized representative sample from a feature vector.

    Excludes override_id (privacy: don't expose which specific trip),
    but keeps trip_id for the review surface so the reviewer can
    cross-reference.
    """
    return {
        "trip_id": vec.trip_id,
        "flag": vec.flag,
        "action": vec.action,
        "original_severity": vec.original_severity,
        "new_severity": vec.new_severity,
        "ai_decision_state": vec.ai_decision_state,
        "ai_confidence": vec.ai_confidence,
        "destination": vec.destination,
        "party_size": vec.party_size,
        "duration_days": vec.duration_days,
        "trip_stage": vec.trip_stage,
        "created_at": vec.created_at,
    }


def _compute_cluster_id(
    key: tuple,
    window_start: str,
    window_end: str,
) -> str:
    """Deterministic cluster_id from cluster_key + window.

    Stable across mining runs on the same data. If the data grows, the
    cluster may grow but the ID stays the same — enabling trend tracking.
    """
    raw = f"{json.dumps(key, sort_keys=True)}|{window_start}|{window_end}"
    short_hash = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"kc_{short_hash}"


def _count_values(
    vectors: List[OverrideFeatureVector],
    attr: str,
    none_key: str = "none",
) -> Dict[str, int]:
    """Count how many vectors have each value of a given attribute."""
    counts: Dict[str, int] = {}
    for v in vectors:
        val = getattr(v, attr, None)
        key = str(val) if val is not None else none_key
        counts[key] = counts.get(key, 0) + 1
    return counts
