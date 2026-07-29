"""
src/analytics/kdd/models — Pydantic models for the KDD v0 pipeline.

All models are immutable (frozen) and JSON-serializable by default.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

class OverrideFeatureVector(BaseModel):
    """Structured features extracted from an override event + decision_delta.

    This is the pure-function output that feeds into clustering. Every field
    is JSON-serializable by design.
    """
    model_config = {"frozen": True}

    override_id: str
    trip_id: str
    agency_id: str
    created_at: str

    # Core override features
    flag: str
    action: str
    scope: str
    original_severity: Optional[str] = None
    new_severity: Optional[str] = None

    # AI decision features (from decision_delta)
    ai_decision_state: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_operating_mode: Optional[str] = None
    ai_flag_count: int = 0
    ai_severe_flags: List[str] = Field(default_factory=list)

    # Trip context features (from decision_delta)
    trip_stage: Optional[str] = None
    trip_status: Optional[str] = None
    trip_source: Optional[str] = None
    destination: Optional[str] = None
    party_size: Optional[int] = None
    duration_days: Optional[int] = None


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

class OverrideCluster(BaseModel):
    """A group of similar override events mined from the override corpus.

    Each cluster represents a recurring pattern where operators override the
    same (or similar) AI decision flags under similar trip contexts.
    """
    model_config = {"frozen": True}

    cluster_id: str
    agency_id: str
    mined_at: str
    window_start: str
    window_end: str
    algorithm: str
    feature_version: str

    # Cluster description
    flag: str  # The dominant flag across all overrides in this cluster
    cluster_label: Optional[str] = None  # Human label, nullable until reviewed

    # Size metrics
    sample_size: int  # Number of overrides in this cluster
    support: float  # sample_size / total_overrides_in_window

    # Representative samples (anonymized)
    representative_samples: List[Dict[str, Any]] = Field(default_factory=list)

    # Feature centroid (for debugging / versioning)
    feature_centroid: Dict[str, Any] = Field(default_factory=dict)

    # Dominant action in the cluster
    dominant_action: str

    # Review state
    review_status: Literal["unreviewed", "actionable", "noise", "already_fixed"] = "unreviewed"
    review_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Digest API response
# ---------------------------------------------------------------------------

class KDDOverrideDigestItem(BaseModel):
    """A single cluster as presented to the reviewer in the digest API."""
    cluster_id: str
    flag: str
    label: Optional[str] = None
    sample_size: int
    support: float
    dominant_action: str
    review_status: str = "unreviewed"
    representative_samples: List[Dict[str, Any]] = Field(default_factory=list)
    mined_at: str


class KDDOverrideDigestResponse(BaseModel):
    """Response from GET /api/kdd/override-digest."""
    agency_id: str
    clusters: List[KDDOverrideDigestItem] = Field(default_factory=list)
    total: int = 0
    mined_at: Optional[str] = None


class KDDReviewActionRequest(BaseModel):
    """Request body for POST /api/kdd/override-digest/{cluster_id}/review."""
    action: Literal["actionable", "noise", "already_fixed"]
    note: Optional[str] = None


class KDDReviewActionResponse(BaseModel):
    ok: bool = True
    cluster_id: str
    review_status: str
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Cluster persistence
# ---------------------------------------------------------------------------

_STORED_CLUSTER_FIELDS = {
    "cluster_id", "agency_id", "mined_at", "window_start", "window_end",
    "algorithm", "feature_version", "flag", "cluster_label",
    "sample_size", "support", "representative_samples", "feature_centroid",
    "dominant_action", "review_status", "review_note",
}


def cluster_to_stored_dict(cluster: OverrideCluster) -> dict:
    """Convert an OverrideCluster to a JSON-serializable dict for storage."""
    return {k: getattr(cluster, k) for k in _STORED_CLUSTER_FIELDS}


def cluster_from_stored_dict(data: dict) -> OverrideCluster:
    """Reconstruct an OverrideCluster from a stored dict."""
    return OverrideCluster(**{k: data.get(k) for k in _STORED_CLUSTER_FIELDS})


# ---------------------------------------------------------------------------
# Job result
# ---------------------------------------------------------------------------

class KDDJobResult(BaseModel):
    """Result of a single KDD mining job run."""
    model_config = {"frozen": True}

    ok: bool = True
    overrides_processed: int = 0
    clusters_produced: int = 0
    clusters_persisted: int = 0
    errors: int = 0
    error_messages: List[str] = Field(default_factory=list)
    top_flags: List[str] = Field(default_factory=list)
    window_start: str = ""
    window_end: str = ""
    total_overrides_in_window: int = 0
    elapsed_seconds: float = 0.0
