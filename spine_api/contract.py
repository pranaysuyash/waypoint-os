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

from typing import Any, Dict, List, Literal, Optional, Union
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
    raw_note: Optional[str] = Field(default=None, max_length=100_000)
    owner_note: Optional[str] = Field(default=None, max_length=50_000)
    structured_json: Optional[Dict[str, Any]] = None
    itinerary_text: Optional[str] = Field(default=None, max_length=200_000)
    retention_consent: bool = False
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    strict_leakage: bool = False
    scenario_id: Optional[str] = Field(default=None, max_length=100)
    follow_up_due_date: Optional[str] = Field(default=None, max_length=50)
    pace_preference: Optional[str] = Field(default=None, max_length=100)
    lead_source: Optional[str] = Field(default=None, max_length=200)
    activity_provenance: Optional[str] = Field(default=None, max_length=500)
    trip_priorities: Optional[str] = Field(default=None, max_length=1000)
    date_flexibility: Optional[str] = Field(default=None, max_length=500)
    date_year_confidence: Optional[str] = Field(default=None, max_length=50)
    draft_id: Optional[str] = Field(default=None, max_length=100)

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
    frontier_result: Optional[FrontierOrchestrationResult] = None


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
    escalation_outcome: Optional[Literal[
        "false_escalation",
        "missed_escalation",
        "correct_escalation",
        "not_applicable",
    ]] = None


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
    sub_brand: Optional[str] = None
    plan_label: Optional[str] = None
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


class UpdateAiAgentSettings(BaseModel):
    """Request model for updating AI agent settings."""
    enable_auto_intake: Optional[bool] = None
    enable_auto_shortlist: Optional[bool] = None
    enable_auto_proposal: Optional[bool] = None
    enable_auto_negotiation: Optional[bool] = None
    enable_frontier_orchestration: Optional[bool] = None
    enable_checker_agent: Optional[bool] = None
    enable_call_capture: Optional[bool] = None
    enable_document_extraction: Optional[bool] = None
    preferred_model: Optional[str] = None
    fallback_model: Optional[str] = None
    extraction_model: Optional[str] = None
    checker_model: Optional[str] = None
    max_negotiation_rounds: Optional[int] = None
    proposal_confidence_threshold: Optional[float] = None
    auto_advance_stages: Optional[bool] = None
    require_owner_review_above_value: Optional[float] = None
    brand_voice: Optional[str] = None
    response_language: Optional[str] = None
    max_follow_up_questions: Optional[int] = None


class UpdateSupportSettings(BaseModel):
    """Request model for updating support channel settings."""
    enable_email_support: Optional[bool] = None
    enable_chat_support: Optional[bool] = None
    enable_phone_support: Optional[bool] = None
    enable_whatsapp_support: Optional[bool] = None
    default_response_sla_hours: Optional[int] = None
    urgent_response_sla_hours: Optional[int] = None
    auto_route_by_destination: Optional[bool] = None
    auto_route_by_language: Optional[bool] = None
    escalation_after_sla_breach: Optional[bool] = None
    escalation_contact_email: Optional[str] = None
    escalation_contact_phone: Optional[str] = None
    support_hours_start: Optional[str] = None
    support_hours_end: Optional[str] = None
    support_days: Optional[List[str]] = None
    timezone: Optional[str] = None
    enable_auto_acknowledgement: Optional[bool] = None
    auto_acknowledgement_message: Optional[str] = None
    out_of_hours_message: Optional[str] = None
    enable_csat_survey: Optional[bool] = None
    csat_trigger: Optional[str] = None


class UpdateCommSettings(BaseModel):
    """Request model for updating communication preferences."""
    default_outbound_channel: Optional[str] = None
    allow_channel_switching: Optional[bool] = None
    enable_template_library: Optional[bool] = None
    default_greeting: Optional[str] = None
    default_sign_off: Optional[str] = None
    respect_operating_hours: Optional[bool] = None
    send_immediately_during_hours: Optional[bool] = None
    queue_outside_hours: Optional[bool] = None
    max_emails_per_day_per_trip: Optional[int] = None
    max_whatsapp_per_day_per_trip: Optional[int] = None
    auto_detect_language: Optional[bool] = None
    default_language: Optional[str] = None
    supported_languages: Optional[List[str]] = None
    translate_outbound: Optional[bool] = None
    enable_auto_followup: Optional[bool] = None
    auto_followup_delay_days: Optional[int] = None
    max_auto_followups: Optional[int] = None
    followup_escalate_after_max: Optional[bool] = None
    notify_on_customer_reply: Optional[bool] = None
    notify_on_sla_warning: Optional[bool] = None
    notify_on_escalation: Optional[bool] = None
    digest_frequency: Optional[str] = None
    include_agency_signature: Optional[bool] = None
    include_unsubscribe_link: Optional[bool] = None
    compliance_footer: Optional[str] = None


class UpdateAutonomyPolicy(BaseModel):
    approval_gates: Optional[Dict[str, str]] = None
    mode_overrides: Optional[Dict[str, Dict[str, str]]] = None
    auto_proceed_with_warnings: Optional[bool] = None
    learn_from_overrides: Optional[bool] = None
    auto_reprocess_on_edit: Optional[bool] = None
    allow_explicit_reassess: Optional[bool] = None
    auto_reprocess_stages: Optional[Dict[str, bool]] = None


class UpdateSeasonalPolicy(BaseModel):
    """Agency-level policy controls that govern seasonal campaign behavior."""

    active_seasons_enabled: Optional[bool] = None
    default_quarter_window_months: Optional[int] = Field(default=None, ge=1, le=24)
    channel_mix: Optional[Dict[str, float]] = None
    weather_risk_threshold: Optional[float] = None
    budget_guardrail_multiplier: Optional[float] = Field(default=None, gt=0.0)
    micro_seasonality_window_days: Optional[int] = Field(default=None, ge=1, le=365)
    quarterly_recalibration_enabled: Optional[bool] = None
    prelaunch_blocklist: Optional[List[str]] = None


class SeasonSimulationRequest(BaseModel):
    scenario: str = "baseline"


class SeasonDispatchRequest(BaseModel):
    dry_run: bool = True
    scenario: Optional[str] = None


class AgencySeasonalSettingsResponse(BaseModel):
    active_seasons_enabled: bool
    default_quarter_window_months: int
    channel_mix: Dict[str, float]
    weather_risk_threshold: float
    budget_guardrail_multiplier: float
    micro_seasonality_window_days: int
    quarterly_recalibration_enabled: bool
    prelaunch_blocklist: List[str]


class SeasonalCampaignPlan(BaseModel):
    """Canonical plan schema for campaign-level seasonal planning governance."""

    plan_id: str
    name: str
    status: Literal["draft", "active", "paused", "archived"] = "draft"
    destination: Optional[str] = None
    campaign_window_start_month: Optional[int] = Field(default=None, ge=1, le=12)
    campaign_window_end_month: Optional[int] = Field(default=None, ge=1, le=12)
    channel_mix: Dict[str, float] = Field(default_factory=dict)
    target_budget_min: Optional[float] = None
    target_budget_max: Optional[float] = None
    notes: Optional[str] = None
    blocklist: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    is_recalibrated: bool = False
    score: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateSeasonalCampaignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    status: Literal["draft", "active", "paused", "archived"] = "draft"
    destination: Optional[str] = None
    campaign_window_start_month: Optional[int] = Field(default=None, ge=1, le=12)
    campaign_window_end_month: Optional[int] = Field(default=None, ge=1, le=12)
    channel_mix: Dict[str, float] = Field(default_factory=dict)
    target_budget_min: Optional[float] = None
    target_budget_max: Optional[float] = None
    notes: Optional[str] = None
    blocklist: List[str] = Field(default_factory=list)


class UpdateSeasonalCampaignRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[Literal["draft", "active", "paused", "archived"]] = None
    destination: Optional[str] = None
    campaign_window_start_month: Optional[int] = Field(default=None, ge=1, le=12)
    campaign_window_end_month: Optional[int] = Field(default=None, ge=1, le=12)
    channel_mix: Optional[Dict[str, float]] = None
    target_budget_min: Optional[float] = None
    target_budget_max: Optional[float] = None
    notes: Optional[str] = None
    blocklist: Optional[List[str]] = None
    is_recalibrated: Optional[bool] = None


class SeasonalCampaignListResponse(BaseModel):
    items: List[SeasonalCampaignPlan] = Field(default_factory=list)
    total: int


class SeasonPreflightCheck(BaseModel):
    check: str
    status: Literal["pass", "warn", "fail"]
    details: Optional[str] = None


class SeasonPreflightResponse(BaseModel):
    plan_id: str
    ok: bool
    checks: List[SeasonPreflightCheck] = Field(default_factory=list)
    risk_score: float = 0.0


class SeasonDispatchResponse(BaseModel):
    plan_id: str
    ok: bool
    dispatched_channels: List[str] = Field(default_factory=list)
    dry_run: bool
    executed_at: str


class SeasonSimulationResponse(BaseModel):
    plan_id: str
    scenario: str
    projected_leads: int
    projected_bookings: int
    projected_margin_pct: float
    confidence: float
    notes: List[str] = Field(default_factory=list)


class SeasonRecalibrationResponse(BaseModel):
    plan_id: str
    recalibrated: bool
    before_status: Optional[str] = None
    after_status: str
    next_recalibration_due: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


class SeasonExplorationCell(BaseModel):
    destination: str
    month: int
    relative_demand: float
    weather_risk: float
    suggested_channels: List[str] = Field(default_factory=list)


class SeasonExplorationMapResponse(BaseModel):
    generated_at: str
    cells: List[SeasonExplorationCell] = Field(default_factory=list)


class ExplicitReassessRequest(BaseModel):
    reason: Optional[str] = None
    stage: Optional[str] = None
    operating_mode: Optional[str] = None
    strict_leakage: Optional[bool] = None


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

# =============================================================================
# Trip Response — canonical API contract for GET /trips/{id} and PATCH /trips/{id}
# =============================================================================

class TripResponse(BaseModel):
    """Canonical response shape for individual trip endpoints.

    Uses resolve_trip_field() as the single source of truth for field resolution —
    no ad-hoc path hunting here. Any field not in this model is invisible to the
    frontend; add fields here and regenerate TypeScript types via openapi-typescript.

    `extracted` is passed through opaquely so backend integration tests that
    verify fact-sync side effects can still inspect raw extracted data.
    Frontend consumers should use the resolved canonical fields above.
    """
    id: str
    status: str
    stage: Optional[str] = None
    dateWindow: Optional[str] = None
    destination: Optional[str] = None
    origin: Optional[str] = None
    budget: Optional[Union[float, str]] = None
    party: Optional[int] = None
    tripType: Optional[str] = None
    customerName: Optional[str] = None
    follow_up_due_date: Optional[str] = None
    extracted: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    # Phase 2 structured intake fields — stored as DB columns, returned verbatim.
    # These are set by direct PATCH or extracted from call/intake pipeline.
    party_composition: Optional[str] = None
    pace_preference: Optional[str] = None
    date_year_confidence: Optional[str] = None
    lead_source: Optional[str] = None
    activity_provenance: Optional[str] = None
    trip_priorities: Optional[str] = None
    date_flexibility: Optional[str] = None

    @classmethod
    def from_dict(cls, trip: Dict[str, Any]) -> "TripResponse":
        from spine_api.services.inbox_projection import (
            resolve_trip_field, _derive_customer_name, _get_nested,
        )
        trip_id = trip.get("id", "")

        # Budget: prefer numeric value; surface raw text for display when numeric unavailable.
        # This matches the frontend's existing rawText ?? budgetVal ?? budgetValue() chain.
        budget_numeric = resolve_trip_field(trip, "budget")  # returns int (0 if unknown)
        budget_raw = _get_nested(trip, "extracted.facts.budget_raw_text.value", None)
        if budget_raw and not budget_raw.strip():
            budget_raw = None
        budget: Optional[Union[float, str]] = (
            float(budget_numeric) if budget_numeric else (budget_raw or None)
        )

        # Normalize sentinel strings to None for clean Optional contract.
        def _clean_str(v: Optional[str]) -> Optional[str]:
            if not v or v in ("Unknown", "TBD", ""):
                return None
            return v

        def _clean_text_value(value: Any) -> Optional[str]:
            if value is None:
                return None
            if isinstance(value, list):
                joined = ", ".join(
                    item.strip() for item in value if isinstance(item, str) and item.strip()
                )
                return _clean_str(joined or None)
            if isinstance(value, (int, float, bool)):
                return _clean_str(str(value))
            if isinstance(value, str):
                return _clean_str(value.strip())
            return None

        return cls(
            id=trip_id,
            status=trip.get("status", "new"),
            stage=trip.get("stage") or None,
            dateWindow=_clean_str(resolve_trip_field(trip, "date_window")),
            destination=_clean_str(resolve_trip_field(trip, "destination")),
            origin=_clean_str(resolve_trip_field(trip, "origin")),
            budget=budget,
            party=resolve_trip_field(trip, "party_size") or None,
            tripType=resolve_trip_field(trip, "trip_type") or None,
            customerName=_derive_customer_name(trip, trip_id) or None,
            follow_up_due_date=trip.get("follow_up_due_date") or None,
            extracted=trip.get("extracted") or None,
            validation=trip.get("validation") or None,
            # Phase 2 structured fields — read directly from storage dict.
            party_composition=trip.get("party_composition") or None,
            pace_preference=trip.get("pace_preference") or None,
            date_year_confidence=trip.get("date_year_confidence") or None,
            lead_source=trip.get("lead_source") or None,
            activity_provenance=trip.get("activity_provenance") or None,
            trip_priorities=_clean_text_value(
                trip.get("trip_priorities")
                or _get_nested(trip, "extracted.facts.trip_priorities.value", None)
            ),
            date_flexibility=_clean_text_value(
                trip.get("date_flexibility")
                or _get_nested(trip, "extracted.facts.date_flexibility.value", None)
            ),
        )


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
    urgency: int = 50
    importance: int = 50
    urgencyBreakdown: Dict[str, float] = Field(default_factory=dict)
    importanceBreakdown: Dict[str, float] = Field(default_factory=dict)
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
    breached: int = 0
    incomplete: int = 0
    missingCustomer: int = 0
    missingTripBasics: int = 0
    oldestWaitingDays: Optional[int] = None
    oldestUnassignedWaitingDays: Optional[int] = None
    statsCoverage: int = 0


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
    "UpdateSeasonalPolicy",
    "AgencySeasonalSettingsResponse",
    "CreateSeasonalCampaignRequest",
    "UpdateSeasonalCampaignRequest",
    "SeasonalCampaignPlan",
    "SeasonalCampaignListResponse",
    "SeasonSimulationRequest",
    "SeasonDispatchRequest",
    "SeasonPreflightCheck",
    "SeasonPreflightResponse",
    "SeasonDispatchResponse",
    "SeasonSimulationResponse",
    "SeasonRecalibrationResponse",
    "SeasonExplorationMapResponse",
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
    "TripResponse",
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
