# KDD Override Mining Reference Code & v0.1 Upgrade Snippets

**Reference Date**: July 13, 2026  
**Target Repository**: `travel_agency_agent` (`/Users/pranay/Projects/travel_agency_agent`)  
**Associated Audit**: `Docs/audit/KDD_OVERRIDE_MINING_AND_FEEDBACK_LOOP_AUDIT_2026-07-13.md`  

---

## 1. Tenant-Isolated `spine_api/routers/kdd.py` Fix (`Pre-PR Bug Fix`)

```python
@router.get("/kdd/clusters")
def list_clusters(
    limit: int = 50,
    min_overrides: int = 1,
    agency: Agency = Depends(get_current_agency),
):
    """List KDD override clusters with at least `min_overrides` overrides, strictly scoped to current agency."""
    clusters = KDDOverrideClusterStore.list_clusters_with_override_count(
        agency_id=agency.id,  # [SECURITY FIX] Enforce strict tenant isolation
        min_overrides=min_overrides,
    )
    return {"items": clusters[:limit], "total": len(clusters)}


@router.get("/kdd/clusters/{cluster_id}")
def get_cluster(
    cluster_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get a single KDD cluster by ID, ensuring ownership by the current agency."""
    cluster = KDDOverrideClusterStore.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # [SECURITY FIX] Reject cross-tenant cluster inspection
    if cluster.get("agency_id") != agency.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this cluster")
        
    return cluster
```

---

## 2. KDD v0.1 Fuzzy Gower Distance & Density Clustering (`src/analytics/kdd/clustering.py`)

```python
from typing import List, Dict, Any, Tuple
import hashlib
import json
from datetime import datetime, timezone
from src.analytics.kdd.models import OverrideFeatureVector, OverrideCluster

def compute_gower_distance(v1: OverrideFeatureVector, v2: OverrideFeatureVector) -> float:
    """Compute weighted Gower distance between two override feature vectors."""
    cat_weights = {"flag": 3.0, "action": 2.5, "destination": 1.5, "trip_stage": 1.0}
    num_weights = {"party_size": 1.0, "duration_days": 1.0, "ai_confidence": 0.5}
    
    total_weight = sum(cat_weights.values()) + sum(num_weights.values())
    accum = 0.0
    
    # Categorical differences (0 if identical, 1 if different)
    for attr, weight in cat_weights.items():
        val1 = getattr(v1, attr, None)
        val2 = getattr(v2, attr, None)
        if val1 != val2:
            accum += weight
            
    # Numerical differences (normalized to empirical bounds)
    ranges = {"party_size": 20.0, "duration_days": 30.0, "ai_confidence": 1.0}
    for attr, weight in num_weights.items():
        val1 = float(getattr(v1, attr, 0.0) or 0.0)
        val2 = float(getattr(v2, attr, 0.0) or 0.0)
        diff = min(abs(val1 - val2) / ranges[attr], 1.0)
        accum += weight * diff
        
    return accum / total_weight


def agglomerative_gower_cluster(
    vectors: List[OverrideFeatureVector],
    distance_threshold: float = 0.22,
    min_cluster_size: int = 3,
) -> List[List[OverrideFeatureVector]]:
    """Group vectors into density clusters using pairwise Gower distance."""
    if not vectors:
        return []
        
    # Simple hierarchical link graph for zero-external-dependency v0.1
    n = len(vectors)
    adj: Dict[int, List[int]] = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if compute_gower_distance(vectors[i], vectors[j]) <= distance_threshold:
                adj[i].append(j)
                adj[j].append(i)
                
    # Connected components filtering by min_cluster_size
    visited = set()
    clusters = []
    for i in range(n):
        if i not in visited:
            comp = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop(0)
                comp.append(vectors[curr])
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            if len(comp) >= min_cluster_size:
                clusters.append(comp)
                
    return clusters
```
