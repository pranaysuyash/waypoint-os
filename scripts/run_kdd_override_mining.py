#!/usr/bin/env python3
"""
run_kdd_override_mining.py — KDD v0 override mining job.

Extracts feature vectors from all overrides, clusters them by flag/decision_type,
and persists the clusters to KDDOverrideClusterStore.

Usage:
    uv run python scripts/run_kdd_override_mining.py
    uv run python scripts/run_kdd_override_mining.py --min-cluster-size 3

Environment:
    TRIPSTORE_BACKEND    — file or sql (default: file)
    KDD_MAX_CLUSTERS     — max clusters to produce (default: 50)
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure project root and src/ are on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _PROJECT_ROOT / "src"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kdd_mining")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="KDD v0 override mining — extract, cluster, persist."
    )
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=2,
        help="Minimum overrides per cluster (default: 2).",
    )
    parser.add_argument(
        "--agency-id",
        type=str,
        default=None,
        help="Agency ID to mine overrides for (default: test agency).",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=30,
        help="Override window in days (default: 30).",
    )

    import os

    os.chdir(str(_PROJECT_ROOT))

    from spine_api.persistence import KDDOverrideClusterStore, TEST_AGENCY_ID
    from src.analytics.kdd.jobs import run_kdd_override_mining

    args = parser.parse_args()
    agency_id = args.agency_id or TEST_AGENCY_ID

    logger.info(
        "Starting KDD override mining (agency=%s, min_cluster_size=%d, window_days=%d)",
        agency_id,
        args.min_cluster_size,
        args.window_days,
    )

    start = time.monotonic()
    clusters = run_kdd_override_mining(
        agency_id=agency_id,
        store=KDDOverrideClusterStore,
        min_cluster_size=args.min_cluster_size,
        window_days=args.window_days,
    )
    elapsed = time.monotonic() - start

    cluster_count = len(clusters)

    logger.info(
        "KDD override mining complete: %d clusters persisted, %s",
        cluster_count,
        f"{elapsed:.2f}s",
    )

    print(f"\n✅ KDD mining complete: {cluster_count} clusters persisted ({elapsed:.2f}s)")
    if clusters:
        print("   Top clusters:")
        for c in clusters[:5]:
            print(f"   • {c.flag} ({c.sample_size} overrides, action={c.dominant_action})")
    else:
        print("   No clusters found (too few similar overrides)")


if __name__ == "__main__":
    main()
