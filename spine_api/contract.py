"""
spine_api/contract.py — Canonical contract between backend and frontend.

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

from src.intake.constants import DecisionState


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
    raw_verdict: DecisionState
    effective_action: str
    approval_required: bool
    rule_source: str
    safety_invariant_applied: bool
    mode_override_applied: Optional[str] = None
    warning_override_applied: bool = False
    reasons: List[str] = Field(default_factory=list)


class NegotiationLog(BaseModel):
    id: str
    supplier_name: str
    status: Literal["OPEN", "NEGOTIATING", "WON", "LOST"]
    best_bid: Optional[float] = None
    original_price: Optional[float] = None
    savings: Optional[float] = None
    next_action: Optional[str] = None
    last_message: Optional[str] = None


class SpecialtyKnowledgeHit(BaseModel):
    niche: str
    keywords: List[str]
    checklists: List[str]
    compliance: List[str] = Field(default_factory=list)
    safety_notes: Optional[str] = None
    urgency: str = "NORMAL"


class FrontierOrchestrationResult(BaseModel):
    ghost_triggered: bool = False
    ghost_workflow_id: Optional[str] = None
    sentiment_score: float = 0.5
    anxiety_alert: bool = False
    intelligence_hits: List[Dict[str, Any]] = Field(default_factory=list)
    specialty_knowledge: List[SpecialtyKnowledgeHit] = Field(default_factory=list)
    mitigation_applied: bool = False
    requires_manual_audit: bool = False
    audit_reason: Optional[str] = None
    negotiation_active: bool = False
    negotiation_logs: List[NegotiationLog] = Field(default_factory=list)


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
    retention_consent: bool = False
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    strict_leakage: bool = False
    scenario_id: Optional[str] = None
    follow_up_due_date: Optional[str] = None
    pace_preference: Optional[str] = None
    lead_source: Optional[str] = None
    activity_provenance: Optional[str] = None
    trip_priorities: Optional[str] = None
    date_flexibility: Optional[str] = None
    date_year_confidence: Optional[str] = None
    draft_id: Optional[str] = None  # Links run to a pre-trip draft

    model_config = {"extra": "forbid"}


class SpineRunResponse(BaseModel):
    ok: bool = True
    run_id: str = ""
    packet: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    plan_candidate: Optional[Dict[str, Any]] = None
    traveler_bundle: Optional[Dict[str, Any]] = None
    internal_bundle: Optional[Dict[str, Any]] = None
    safety: SafetyResult = Field(default_factory=SafetyResult)
    fees: Optional[Dict[str, Any]] = None
    autonomy_outcome: Optional[AutonomyOutcome] = None
    assertions: Optional[List[AssertionResult]] = None
    frontier_result: Optional[FrontierOrchestrationResult] = None
    meta: RunMeta = Field(default_factory=RunMeta)


class RunAcceptedResponse(BaseModel):
    """Returned immediately by POST /run — the run is queued, poll for status."""
    run_id: str
    state: str = "queued"


class RunStatusResponse(BaseModel):
    """Returned by GET /runs/{run_id} — full run state for polling UI."""
    run_id: str
    state: str
    trip_id: Optional[str] = None
    stage: Optional[str] = None
    operating_mode: Optional[str] = None
    agency_id: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_ms: Optional[float] = None
    steps_completed: List[str] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stage_at_failure: Optional[str] = None
    block_reason: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None
    packet: Optional[Dict[str, Any]] = None
    decision_state: Optional[DecisionState] = None
    follow_up_questions: List[Dict[str, Any]] = Field(default_factory=list)
    hard_blockers: List[str] = Field(default_factory=list)
    soft_blockers: List[str] = Field(default_factory=list)


class PublicCheckerArtifactUpload(BaseModel):
    file_name: str
    mime_type: str
    file_size: int
    extraction_method: str
    archive_path: Optional[str] = None
    extracted_text_chars: Optional[int] = None


class PublicCheckerArtifactManifest(BaseModel):
    trip_id: str
    saved_at: str
    retention_consent: bool = True
    artifact_type: str = "public_checker_upload"
    uploaded_file: Optional[PublicCheckerArtifactUpload] = None
    trip_snapshot: Optional[Dict[str, Any]] = None


class PublicCheckerExportResponse(BaseModel):
    trip_id: str
    trip: Dict[str, Any]
    artifact_manifest: Optional[PublicCheckerArtifactManifest] = None


class PublicCheckerDeleteResponse(BaseModel):
    ok: bool = True
    trip_id: str
    deleted_trip: bool = False
    deleted_artifacts: bool = False


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
    components: Optional[Dict[str, Any]] = None
    issues: Optional[List[str]] = None


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
    actor: Optional[str] = None  # Who performed this action (user ID or "system"/"owner")
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
    user_id: str
    email: str
    name: str
    role: str
    capacity: int = 5
    status: str = "active"
    specializations: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: Optional[str] = None


class InviteTeamMemberRequest(BaseModel):
    email: str
    name: str
    role: str
    capacity: int = 5
    specializations: Optional[List[str]] = Field(default_factory=list)


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


class IntegrityAction(BaseModel):
    id: str
    label: str
    description: str
    destructive: bool
    requires_confirmation: bool


class IntegrityIssue(BaseModel):
    id: str
    entity_id: str
    entity_type: Literal["lead", "workspace", "trip", "review", "unknown"]
    issue_type: Literal[
        "orphaned_record",
        "missing_owner",
        "broken_reference",
        "invalid_transition",
        "duplicate_workspace",
    ]
    severity: Literal["low", "medium", "high", "critical"]
    reason: str
    current_status: Optional[str] = None
    created_at: Optional[str] = None
    detected_at: str
    allowed_actions: List[IntegrityAction] = Field(default_factory=list)


class IntegrityIssuesResponse(BaseModel):
    items: List[IntegrityIssue] = Field(default_factory=list)
    total: int


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


class SuitabilityFlagsResponse(BaseModel):
    """Response from GET /trips/{trip_id}/suitability endpoint.
    
    Returns all suitability flags for a given trip with confidence and tier information.
    """
    trip_id: str
    suitability_flags: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of suitability flags with id, name, confidence, tier, etc."
    )


# =============================================================================
# Trip list + inbox response envelopes
# =============================================================================

class TripListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int


class FilterCounts(BaseModel):
    all: int
    at_risk: int
    incomplete: int
    unassigned: int


class InboxTripItem(BaseModel):
    """Typed projection of a trip in the Inbox view.

    These fields are computed by the service layer, not stored directly in the DB.
    FastAPI validates and serializes this shape so the frontend contract is guaranteed.
    """
    id: str
    reference: str
    destination: str
    tripType: str
    partySize: int
    dateWindow: str
    value: int
    priority: Literal["low", "medium", "high", "critical"]
    priorityScore: int
    stage: str
    stageNumber: int
    assignedTo: Optional[str] = None
    assignedToName: Optional[str] = None
    submittedAt: str
    lastUpdated: str
    daysInCurrentStage: int
    slaStatus: Literal["on_track", "at_risk", "breached"]
    customerName: str
    flags: List[str] = Field(default_factory=list)


class InboxResponse(BaseModel):
    """Canonical inbox payload — service-level projected and filtered."""
    items: List[InboxTripItem]
    total: int
    hasMore: bool = False
    filterCounts: FilterCounts


class InboxStatsResponse(BaseModel):
    total: int
    unassigned: int
    critical: int
    atRisk: int


class AssignInboxRequest(BaseModel):
    """Assign trips to an agent."""
    tripIds: List[str]
    assignTo: str
    notifyAssignee: bool = False


class AssignInboxResponse(BaseModel):
    success: bool
    assigned: int


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
    "RunAcceptedResponse",
    "RunStatusResponse",
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
    "IntegrityAction",
    "IntegrityIssue",
    "IntegrityIssuesResponse",
    "OrphanTrip",
    "UnifiedStateResponse",
    "DashboardStatsResponse",
    "SuitabilitySignal",
    "TripListResponse",
    "SuitabilityFlagsResponse",
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
    "FrontierOrchestrationResult",
]
