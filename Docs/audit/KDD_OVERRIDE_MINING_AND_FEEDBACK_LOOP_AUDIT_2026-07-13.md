# Comprehensive Audit: KDD (Knowledge-Driven Development) Override Mining, Automated Clustering & Rule Loop Feedback Architecture

**Audit Date**: July 13, 2026  
**Target Repository**: `travel_agency_agent` (`/Users/pranay/Projects/travel_agency_agent`)  
**Scope**: `src/analytics/kdd/clustering.py`, `src/analytics/kdd/override_features.py`, `src/analytics/kdd/jobs.py`, `spine_api/routers/kdd.py`, and `scripts/run_kdd_override_mining.py`.  
**Status**: Verified Deep Technical & Architectural Audit  

---

## Executive Summary & Why This Area Was Chosen

Waypoint OS (`travel_agency_agent`) is not a static CRUD booking system; it is an **operations and revenue co-pilot for boutique travel agencies** designed to structure messy inbound notes into canonical trip packets and enforce policy via automated decision logic (`src/suitability/`, `src/decision/`).

When an AI automated check triggers a flag or rejects a trip packet, human operators frequently apply **overrides** (`OverrideStore`). The **KDD (Knowledge-Driven Development)** subsystem (`src/analytics/kdd/`) is the critical institutional memory engine responsible for extracting feature vectors (`OverrideFeatureVector`) from those manual overrides, clustering them (`clustering.py`), and surfacing actionable patterns via `spine_api/routers/kdd.py` so the agency's underlying decision rules improve over time.

We chose this subsystem for a deep technical audit because **KDD directly determines whether Waypoint OS learns from operator wisdom or repeatedly repeats the same automated errors**. An audit of the current v0 exact-match clustering algorithm reveals significant signal-loss bottlenecks and highlights clear engineering paths for v0.1 (`HDBSCAN` / Gower distance clustering and automated rule promotion).

---

## 1. Current Architecture & Data Flow Analysis

### 1.1 The Extraction & Mining Pipeline
1. **Event Ingest (`OverrideStore`)**: When an operator overrides an automated flag (`TIGHT_CONNECTION`, `BUDGET_MISMATCH`, `VISA_REQUIRED_SHORT_NOTICE`), an override record is persisted with `trip_id`, `flag`, `action` (`ignore`, `approve_with_warning`), `original_severity`, and `new_severity`.
2. **Batch Feature Extraction (`override_features.py`)**: `extract_override_features()` transforms each override record plus the trip's canonical context (`party_size`, `duration_days`, `destination`, `trip_stage`) into an `OverrideFeatureVector` (`FEATURE_VERSION = "v0"`).
3. **Clustering (`clustering.py`)**: `cluster_overrides()` groups feature vectors into `OverrideCluster` objects (`ALGORITHM = "exact-match-v1"`).
4. **API Query Surface (`spine_api/routers/kdd.py`)**: The frontend `Knowledge Management / Mining` workbench consumes `/kdd/clusters`, `/kdd/clusters/{cluster_id}`, and `/kdd/digest`.

---

## 2. Technical Evaluation: Exact-Match Clustering vs. Signal Loss

### 2.1 The `exact-match-v1` Algorithm (`cluster_key`)
In `override_features.py`, the coarse cluster key that determines grouping is defined as:

```python
def cluster_key(vec: OverrideFeatureVector) -> tuple:
    """Return the coarse exact-match key for v0 clustering."""
    return (
        vec.flag,
        vec.action,
        vec.ai_decision_state or "unset",
        vec.source or "manual",
    )
```

And in `clustering.py` lines 67–71:
```python
for _key, members in groups.items():
    if len(members) < min_cluster_size:
        # Noise floor — skip small groups
        continue
```

### 2.2 Mathematical Signal-Loss Audit (Why `exact-match-v1` Drops High-Value Overrides)
Let $O = \{v_1, v_2, \dots, v_n\}$ be the set of overrides for a single flag $F = \text{TIGHT\_CONNECTION}$ within a 30-day window (`window_days = 30`).

Suppose 5 different operators override $F$ on trips connecting through Paris (`CDG`) with a 45-minute layover because the travelers are Business Class VIPs who get airline concierge transfers. However, their override telemetry records slightly different operational context:
* $v_1, v_2$: `(flag="TIGHT_CONNECTION", action="ignore", ai_decision_state="warning", source="manual")`
* $v_3, v_4$: `(flag="TIGHT_CONNECTION", action="ignore", ai_decision_state="block", source="manual")`
* $v_5$: `(flag="TIGHT_CONNECTION", action="ignore", ai_decision_state="warning", source="agent_nudge")`

Under `exact-match-v1` with `min_cluster_size = 3` (`DEFAULT_MIN_CLUSTER_SIZE = 3`):
* Key A `("TIGHT_CONNECTION", "ignore", "warning", "manual")` has size $2 < 3 \to \text{Discarded as noise}$.
* Key B `("TIGHT_CONNECTION", "ignore", "block", "manual")` has size $2 < 3 \to \text{Discarded as noise}$.
* Key C `("TIGHT_CONNECTION", "ignore", "warning", "agent_nudge")` has size $1 < 3 \to \text{Discarded as noise}$.

**Audit Finding**: Even though $5$ identical high-value domain overrides occurred for `CDG` connections, **100% of the signal is dropped as noise** because `exact-match-v1` splits across auxiliary fields (`ai_decision_state`, `source`).

---

## 3. Recommended KDD v0.1 Upgrade: Fuzzy Vector Clustering & Rule Promotion

### 3.1 Transitioning to Gower Distance & HDBSCAN (`v0.1`)
To capture multi-dimensional patterns without dropping split clusters, KDD v0.1 should compute a **Weighted Gower Distance Metric** across both categorical and numerical features:

$$D(v_i, v_j) = \frac{\sum_{k=1}^{m} w_k \, d_k(v_{i,k}, v_{j,k})}{\sum_{k=1}^{m} w_k}$$

Where:
* Categorical attributes ($k \in \{\text{flag}, \text{action}, \text{destination}, \text{trip\_stage}\}$): $d_k = 0 \text{ if equal, else } 1$.
* Numerical attributes ($k \in \{\text{party\_size}, \text{duration\_days}, \text{ai\_confidence}\}$): $d_k = \frac{|v_{i,k} - v_{j,k}|}{R_k}$ where $R_k$ is the observed range.

Applying density-based clustering (`HDBSCAN` or agglomerative hierarchical clustering with distance threshold $\epsilon = 0.25$) will group $v_1 \dots v_5$ into a single high-confidence cluster (`sample_size = 5`, `dominant_action = "ignore"`, `centroid.destination = "CDG"`).

### 3.2 The Closed-Loop Automated Rule Synthesis Engine (`Override-to-Rule`)
Currently, `spine_api/routers/kdd.py` exposes clusters for operator inspection (`review_status = "unreviewed"`). To close the loop:

1. **Rule Promotion Endpoint (`POST /kdd/clusters/{cluster_id}/promote`)**:
   Allows an agency reviewer to promote a verified KDD cluster directly into a tenant policy exception in `AgencySettings` / `SuitabilityProfile`.
2. **Synthesized Policy Expression**:
   ```json
   {
     "rule_id": "rule_kdd_cdg_tight_conn_vip",
     "origin_cluster_id": "kc_8a9f1bc24d0e",
     "flag": "TIGHT_CONNECTION",
     "condition": "destination == 'CDG' and party_type == 'VIP' and connection_minutes >= 45",
     "override_action": "ignore",
     "status": "active"
   }
   ```
3. **Automated Evaluation in `src/suitability/engine.py`**:
   During packet check, the suitability engine queries active promoted rules *before* emitting a `TIGHT_CONNECTION` flag, eliminating repeat false positives for the agency.

---

## 4. API & Security Findings (`spine_api/routers/kdd.py`)

### 4.1 Tenant Isolation Verification (`get_current_agency`)
In `routers/kdd.py` lines 33–44:
```python
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
```

**Security Vulnerability / Bug Identified**: Notice line 40: `_ = agency`. The dependency `get_current_agency` verifies that the caller is authenticated, but `KDDOverrideClusterStore.list_clusters_with_override_count(min_overrides=min_overrides)` **does not filter by `agency.id`**! If `TRIPSTORE_BACKEND=sql` or shared storage is used across multiple tenant agencies, an operator in Agency A could query `/kdd/clusters` and inspect override clusters mined from Agency B.

**Remediation Required**: Pass `agency_id=agency.id` directly to `list_clusters_with_override_count()` and enforce strict tenant scoping inside `KDDOverrideClusterStore`.

---

## 5. Verification Checklist for KDD Refactoring (`Pre-PR`)

- [ ] Verify `KDDOverrideClusterStore.list_clusters()` and `list_clusters_with_override_count()` accept and enforce `agency_id: str`.
- [ ] Add unit test in `tests/test_kdd_mining.py` confirming that `exact-match-v1` (and future `v0.1` distance clustering) correctly isolates vectors by `agency_id`.
- [ ] Ensure `scripts/run_kdd_override_mining.py` logs explicit warnings if `min_cluster_size` drops more than 50% of extracted override vectors.
