"""
src/analytics/kdd/jobs — Mining job orchestrator for KDD v0.

Composes the override mining pipeline:
    1. Read override events from OverrideStore (all trips for an agency)
    2. Extract feature vectors from each override + decision_delta
    3. Cluster similar overrides
    4. Persist clusters to KDDOverrideClusterStore
    5. Return list of new clusters

This module is a pure orchestration layer — no business logic.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from src.analytics.kdd.models import OverrideCluster, cluster_to_stored_dict
from src.analytics.kdd.override_features import (
    extract_batch,
)
from src.analytics.kdd.clustering import (
    cluster_overrides,
    DEFAULT_MIN_CLUSTER_SIZE,
)

logger = logging.getLogger(__name__)

# Default window: mine overrides from the last 30 days
DEFAULT_WINDOW_DAYS = 30


def run_kdd_override_mining(
    agency_id: str,
    store: Any,  # KDDOverrideClusterStore (or duck-typed equivalent)
    window_days: int = DEFAULT_WINDOW_DAYS,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
    now: Optional[datetime] = None,
) -> List[OverrideCluster]:
    """Run the full override mining pipeline for a single agency.

    Steps:
        1. Read all override records across all trips for this agency.
        2. Filter to the rolling window (``window_days``).
        3. Extract feature vectors.
        4. Cluster similar overrides.
        5. Persist new clusters.
        6. Return the clusters.

    Args:
        agency_id: The agency to mine overrides for.
        store: A KDDOverrideClusterStore instance (or duck-typed equivalent).
        window_days: How far back to look for overrides.
        min_cluster_size: Minimum override count for a valid cluster.
        now: Override timestamp for testing determinism.

    Returns:
        List of new OverrideCluster objects that were persisted.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    window_start = (now - timedelta(days=window_days)).isoformat()
    window_end = now.isoformat()

    # Step 1: Read all overrides
    all_overrides = _read_agency_overrides(agency_id, store)

    if not all_overrides:
        logger.info("KDD mining [%s]: no overrides found in window", agency_id)
        return []

    # Step 2: Filter to rolling window
    windowed = _filter_by_window(all_overrides, window_start)
    if not windowed:
        logger.info(
            "KDD mining [%s]: %d overrides found, none in window [%s, %s]",
            agency_id, len(all_overrides), window_start, window_end,
        )
        return []

    # Step 3: Extract feature vectors
    vectors = extract_batch(windowed, agency_id)
    logger.info(
        "KDD mining [%s]: extracted %d feature vectors from %d overrides",
        agency_id, len(vectors), len(windowed),
    )

    # Step 4: Cluster
    clusters = cluster_overrides(
        vectors,
        agency_id=agency_id,
        window_start=window_start,
        window_end=window_end,
        min_cluster_size=min_cluster_size,
    )
    logger.info(
        "KDD mining [%s]: %d clusters from %d vectors (min_size=%d)",
        agency_id, len(clusters), len(vectors), min_cluster_size,
    )

    # Step 5: Persist
    for cluster in clusters:
        store.save_cluster(cluster_to_stored_dict(cluster))

    if clusters:
        logger.info(
            "KDD mining [%s]: persisted %d clusters",
            agency_id, len(clusters),
        )

    return clusters


def _read_agency_overrides(agency_id: str, store: Any) -> List[Dict[str, Any]]:
    """Read all override records for the given agency.

    Iterates all trip-level override files. Inefficient for large numbers
    of trips, but acceptable for v0's scale.

    NOTE(agency-filter): OverrideStore does not yet store agency_id per override,
    so this reads ALL overrides regardless of agency. For v0 with a single test
    agency this is acceptable. Add agency filtering when OverrideStore gains
    tenant-scoped writes (TODO: KDD-3).
    """
    from spine_api import persistence as _persistence_mod

    overrides: List[Dict[str, Any]] = []
    OVERRIDES_PER_TRIP_DIR = _persistence_mod.OVERRIDES_PER_TRIP_DIR

    if not OVERRIDES_PER_TRIP_DIR.exists():
        return overrides

    for trip_file in sorted(OVERRIDES_PER_TRIP_DIR.glob("*.jsonl")):
        trip_id = trip_file.stem  # filename without .jsonl suffix
        try:
            trip_overrides = _persistence_mod.OverrideStore.get_overrides_for_trip(trip_id)
            overrides.extend(trip_overrides)
        except (OSError, ValueError, KeyError) as exc:
            logger.debug("KDD: skipping override file %s: %s", trip_file.name, exc)
            continue

    return overrides


def _filter_by_window(
    overrides: List[Dict[str, Any]],
    window_start_iso: str,
) -> List[Dict[str, Any]]:
    """Keep only overrides created on or after the window start."""
    filtered: List[Dict[str, Any]] = []
    for ov in overrides:
        created = ov.get("created_at", "")
        if created >= window_start_iso:
            filtered.append(ov)
    return filtered
