"""
spine-api/contract.py — Canonical contract between backend and frontend.

ALL API response schemas are defined here. Frontend TypeScript types are
auto-generated from these models. If the backend schema changes, the frontend
must regenerate types (via scripts/generate-types.sh), causing a build error
if the UI code is out of sync.

Architecture:
    - Response envelope models (SpineRunResponse, etc.)
    - Dashboard/Aggregator models (UnifiedState, DashboardStats)
    - Shared sub-models (SafetyResult, TimelineEvent, etc.)

Analytics domain models live in src/analytics/models.py and are re-exported here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Shared sub-models
# =============================================================================

class SafetyResult(BaseModel):
    strict_leakage: bool = False
    leakage_passed: bool = True
    leakage_errors: List[str] = Field(default_factory=list)


class AssertionResult(BaseModel):
    type: str
    passed: bool
    message: str
    field: Optional[str] = None


class AutonomyOutcome(BaseModel):
    raw_verdict: str
    effective_action: str
    approval_required: bool
    rule_source: str
    safety_invariant_applied: bool
    mode_override_applied: Optional[str] = None
    warning_override_applied: bool = False
    reasons: List[str] = Field(default_factory=list)


class RunMeta(BaseModel):
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    fixture_id: Optional[str] = None
    execution_ms: float = 0.0


# =============================================================================
# Run request / response envelopes
# =============================================================================

class SpineRunRequest(BaseModel):
    raw_note: Optional[str] = None
    owner_note: Optional[str] = None
    structured_json: Optional[Dict[str, Any]] = None
    itinerary_text: Optional[str] = None
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    strict_leakage: bool = False
    scenario_id: Optional[str] = None

    model_config = {"extra": "forbid"}


class SpineRunResponse(BaseModel):
    ok: bool = True
    run_id: str = ""
    packet: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    traveler_bundle: Optional[Dict[str, Any]] = None
    internal_bundle: Optional[Dict[str, Any]] = None
    safety: SafetyResult = Field(default_factory=SafetyResult)
    fees: Optional[Dict[str, Any]] = None
    autonomy_outcome: Optional[AutonomyOutcome] = None
    assertions: Optional[List[AssertionResult]] = None
    meta: RunMeta = Field(default_factory=RunMeta)


# =============================================================================
# Override models
# =============================================================================

class OverrideRequest(BaseModel):
    flag: str
    decision_type: Optional[str] = None
    action: str
    new_severity: Optional[str] = None
    overridden_by: str
    reason: str
    scope: str = "this_trip"
    original_severity: Optional[str] = None

    model_config = {"extra": "forbid"}


class OverrideResponse(BaseModel):
    ok: bool
    override_id: str
    trip_id: str
    flag: str
    action: str
    new_severity: Optional[str] = None
    cache_invalidated: bool = False
    rule_graduated: bool = False
    pattern_learning_queued: bool = False
    warnings: List[str] = Field(default_factory=list)
    audit_event_id: str


# =============================================================================
# Health / version
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str


# =============================================================================
# Timeline models
# =============================================================================

class TimelineEvent(BaseModel):
    trip_id: str
    timestamp: str
    stage: str
    status: str
    state_snapshot: Dict[str, Any]
    decision: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None
    pre_state: Optional[Dict[str, Any]] = None
    post_state: Optional[Dict[str, Any]] = None


class TimelineResponse(BaseModel):
    trip_id: str
    events: List[TimelineEvent] = Field(default_factory=list)


# =============================================================================
# Review models
# =============================================================================

class ReviewActionRequest(BaseModel):
    action: str
    notes: str
    reassign_to: Optional[str] = None
    error_category: Optional[str] = None


class SuitabilityAcknowledgeRequest(BaseModel):
    acknowledged_flags: List[str]


class SnoozeRequest(BaseModel):
    snooze_until: str


class TeamMember(BaseModel):
    id: str
    email: str
    name: str
    role: str
    capacity: int = 5
    active: bool = True
    created_at: str
    updated_at: Optional[str] = None


class InviteTeamMemberRequest(BaseModel):
    email: str
    name: str
    role: str
    capacity: int = 5


class PipelineStageConfig(BaseModel):
    stage_id: str
    label: str
    order: int
    sla_hours: Optional[int] = None
    auto_actions: List[str] = Field(default_factory=list)


class ApprovalThresholdConfig(BaseModel):
    threshold_id: str
    gate: str
    condition: str
    value: float
    action: str


class ExportRequest(BaseModel):
    time_range: str = "30d"
    format: str = "csv"


class ExportResponse(BaseModel):
    download_url: str
    expires_at: str


# =============================================================================
# Settings models
# =============================================================================

class UpdateOperationalSettings(BaseModel):
    agency_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    target_margin_pct: Optional[float] = Field(None, ge=0, le=100)
    default_currency: Optional[str] = None
    operating_hours_start: Optional[str] = None
    operating_hours_end: Optional[str] = None
    operating_days: Optional[List[str]] = None
    preferred_channels: Optional[List[str]] = None
    brand_tone: Optional[str] = None


class UpdateAutonomyPolicy(BaseModel):
    approval_gates: Optional[Dict[str, str]] = None
    mode_overrides: Optional[Dict[str, Dict[str, str]]] = None
    auto_proceed_with_warnings: Optional[bool] = None
    learn_from_overrides: Optional[bool] = None


# =============================================================================
# Dashboard Aggregator — Unified State response
# =============================================================================

class IntegrityMeta(BaseModel):
    sum_stages: int
    orphan_count: int
    consistent: bool
    last_sync: str


class SystemicError(BaseModel):
    category: str
    count: int


class OrphanTrip(BaseModel):
    id: str
    status: Optional[str] = None
    created_at: Optional[str] = None


class UnifiedStateResponse(BaseModel):
    canonical_total: int
    stages: Dict[str, int]
    sla_breached: int
    orphans: List[OrphanTrip]
    integrity_meta: IntegrityMeta
    systemic_errors: List[SystemicError]


# =============================================================================
# Dashboard Stats — computed by backend aggregator (replaces BFF math)
# =============================================================================

class DashboardStatsResponse(BaseModel):
    active: int
    pending_review: int
    ready_to_book: int
    needs_attention: int


# =============================================================================
# Suitability signal (per-trip, from aggregator)
# =============================================================================

class SuitabilitySignal(BaseModel):
    trip_id: str
    flag_type: str
    severity: Literal["low", "medium", "high", "critical"]
    reason: str
    confidence: float


# =============================================================================
# Trip list response envelope
# =============================================================================

class TripListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int


# =============================================================================
# Re-export analytics models (canonical source: src/analytics/models.py)
# =============================================================================

from src.analytics.models import (
    MonthlyRevenue,
    RevenueMetrics,
    PipelineVelocity,
    InsightsSummary,
    StageMetrics,
    TeamMemberMetrics,
    BottleneckCause,
    BottleneckAnalysis,
    QualityScore,
    AnalyticsPayload,
    OperationalAlert,
)

__all__ = [
    "SafetyResult",
    "AssertionResult",
    "AutonomyOutcome",
    "RunMeta",
    "SpineRunRequest",
    "SpineRunResponse",
    "OverrideRequest",
    "OverrideResponse",
    "HealthResponse",
    "TimelineEvent",
    "TimelineResponse",
    "ReviewActionRequest",
    "SuitabilityAcknowledgeRequest",
    "SnoozeRequest",
    "InviteTeamMemberRequest",
    "PipelineStageConfig",
    "ApprovalThresholdConfig",
    "ExportRequest",
    "ExportResponse",
    "TeamMember",
    "UpdateOperationalSettings",
    "UpdateAutonomyPolicy",
    "IntegrityMeta",
    "SystemicError",
    "OrphanTrip",
    "UnifiedStateResponse",
    "DashboardStatsResponse",
    "SuitabilitySignal",
    "TripListResponse",
    "MonthlyRevenue",
    "RevenueMetrics",
    "PipelineVelocity",
    "InsightsSummary",
    "StageMetrics",
    "TeamMemberMetrics",
    "BottleneckCause",
    "BottleneckAnalysis",
    "QualityScore",
    "AnalyticsPayload",
    "OperationalAlert",
]
