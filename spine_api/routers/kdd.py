"""
KDD (Knowledge-Driven Development) router.

Provides API endpoints for override mining results (clusters, feature vectors,
decision deltas). This is the query surface for Phase 1 of Knowledge Management.

All data is written by the mining job runner (scripts/run_kdd_override_mining.py)
and read by this router.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

logger = logging.getLogger("spine_api.kdd")

KDDOverrideClusterStore = persistence.KDDOverrideClusterStore
OverrideStore = persistence.OverrideStore

router = APIRouter()


@router.get("/kdd/clusters")
def list_clusters(
    limit: int = 50,
    min_overrides: int = 1,
    agency: Agency = Depends(get_current_agency),
):
    """List KDD override clusters with at least `min_overrides` overrides."""
    _ = agency
    clusters = KDDOverrideClusterStore.list_clusters_with_override_count(
        min_overrides=min_overrides
    )
    return {"items": clusters[:limit], "total": len(clusters)}


@router.get("/kdd/clusters/{cluster_id}")
def get_cluster(
    cluster_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get a single KDD cluster by ID, including its member overrides."""
    _ = agency
    cluster = KDDOverrideClusterStore.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.get("/kdd/digest")
def get_kdd_digest(
    limit: int = 50,
    agency: Agency = Depends(get_current_agency),
):
    """Return a KDD digest: cluster count, override counts per flag, top clusters."""
    _ = agency
    clusters = KDDOverrideClusterStore.list_clusters(limit=limit)

    cluster_count = len(clusters)
    override_count = sum(len(c.get("override_ids", [])) for c in clusters)

    # Aggregate by flag name across all clusters for the digest
    flag_counts: dict[str, int] = {}
    for c in clusters:
        flag = c.get("flag_name") or c.get("decision_type") or "unknown"
        flag_counts[flag] = flag_counts.get(flag, 0) + len(c.get("override_ids", []))

    top_flags = sorted(flag_counts.items(), key=lambda x: -x[1])[:10]

    return {
        "cluster_count": cluster_count,
        "total_override_ids": override_count,
        "top_flags": [{"flag": k, "override_count": v} for k, v in top_flags],
        "clusters": clusters[:10],
    }


@router.delete("/kdd/clusters/{cluster_id}")
def delete_cluster(
    cluster_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Delete a KDD cluster by ID."""
    _ = agency
    ok = KDDOverrideClusterStore.delete_cluster(cluster_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return {"ok": True, "cluster_id": cluster_id}
