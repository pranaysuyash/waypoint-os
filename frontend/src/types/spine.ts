/**
 * Spine Types
 *
 * Re-exports all auto-generated types from the backend contract.
 * Frontend-only types that have no backend counterpart remain here.
 *
 * DO NOT manually define types that exist in the generated file.
 * To regenerate: uv run python scripts/generate_types.py
 */

// Re-export all generated contract types
export type {
  SafetyResult,
  AssertionResult,
  AutonomyOutcome,
  RunMeta,
  SpineRunRequest,
  SpineRunResponse,
  OverrideResponse,
  HealthResponse,
  TimelineEvent,
  TimelineResponse,
  DashboardStatsResponse,
  UnifiedStateResponse,
  IntegrityMeta,
  IntegrityAction,
  IntegrityIssue,
  IntegrityIssuesResponse,
  SystemicError,
  OrphanTrip,
  SuitabilitySignal,
} from '@/types/generated/spine-api';

// ============================================================================
// Run polling types (frontend-only — not yet in generated contract)
// ============================================================================

export interface RunAcceptedResponse {
  run_id: string;
  state: string;
}

export interface RunEvent {
  event_id: string;
  event_type: string;
  run_id: string;
  trip_id: string | null;
  timestamp: string;
  stage_name?: string;
  execution_ms?: number;
  error_type?: string;
  error_message?: string;
  stage_at_failure?: string;
  stage?: string;
  operating_mode?: string;
  total_ms?: number;
  block_reason?: string;
}

export interface RunStatusResponse {
  run_id: string;
  state: string;
  trip_id: string | null;
  stage: string | null;
  operating_mode: string | null;
  agency_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  total_ms: number | null;
  created_at: string | null;
  steps_completed: string[];
  events: RunEvent[];
  error_type?: string | null;
  error_message?: string | null;
  stage_at_failure?: string | null;
  block_reason?: string | null;
  validation?: ValidationReport | null;
  packet?: unknown;
}

// ============================================================================
// Frontend-only types (not in backend contract — UI presentation layer)
// ============================================================================

export type SpineStage = "discovery" | "shortlist" | "proposal" | "booking";

export type OperatingMode =
  | "normal_intake"
  | "audit"
  | "emergency"
  | "follow_up"
  | "cancellation"
  | "post_trip"
  | "coordinator_group"
  | "owner_review";

export type DecisionState =
  | "ASK_FOLLOWUP"
  | "PROCEED_INTERNAL_DRAFT"
  | "PROCEED_TRAVELER_SAFE"
  | "BRANCH_OPTIONS"
  | "STOP_NEEDS_REVIEW";

export interface CostBucketEstimate {
  bucket: string;
  low: number;
  high: number;
  covered: boolean;
  notes?: string | null;
}

export interface BudgetBreakdownResult {
  verdict: "realistic" | "borderline" | "not_realistic";
  currency?: string;
  buckets: CostBucketEstimate[];
  missing_buckets: string[];
  total_estimated_low: number;
  total_estimated_high: number;
  budget_stated: number | null;
  gap: number | null;
  risks: string[];
  critical_changes: string[];
  must_confirm: string[];
  alternative: string | null;
  maturity: string;
}

export interface PromptBundle {
  system_context: string;
  user_message: string;
  follow_up_sequence: Array<{
    field_name: string;
    question: string;
    priority: string;
  }>;
  branch_prompts: unknown[];
  internal_notes: string;
  constraints: string[];
  audience: string;
}

export interface FollowUpQuestion {
  field_name: string;
  question: string;
  priority: string;
  suggested_values: unknown[];
}

export interface ConfidenceScorecard {
  data_quality: number;
  judgment_confidence: number;
  commercial_confidence: number;
  overall: number;
}

export interface Rationale {
  hard_blockers: string[];
  soft_blockers: string[];
  contradictions: string[];
  confidence: number;
  confidence_scorecard: {
    data: number;
    judgment: number;
    commercial: number;
  };
  feasibility: string;
}

export interface SuitabilityFlagData {
  flag_type: string;
  severity: "low" | "medium" | "high" | "critical";
  reason: string;
  confidence: number;
  details?: Record<string, any>;
  affected_travelers?: string[];
}

export interface SuitabilityProfile {
  summary: {
    status: "suitable" | "caution" | "unsuitable";
    primaryReason: string;
    overallScore: number;
  };
  dimensions: Array<{
    type: string;
    severity: "low" | "medium" | "high";
    score: number;
    reason: string;
    evidence_id?: string;
  }>;
  overrides?: Array<{
    flag: string;
    overridden: boolean;
    override_action?: string;
    override_reason?: string;
    overridden_by?: string;
    overridden_at?: string;
  }>;
}

/**
 * SuitabilityFlag represents a single suitability concern raised by the spine.
 *
 * This is returned by the GET /trips/{trip_id}/suitability endpoint and represents
 * historical suitability signals that have been evaluated for a trip.
 *
 * Tier 1 (critical/high): Hard blockers requiring operator acknowledgment before approval
 * Tier 2 (medium/low): Warnings for operator review and consideration
 */
export interface SuitabilityFlag {
  id: string;                          // Unique identifier for this flag instance
  trip_id: string;                     // Trip this flag is associated with
  name: string;                        // Machine-readable flag name (e.g., "elderly_mobility_risk")
  confidence: number;                  // 0-100: confidence percentage
  tier: 'critical' | 'high' | 'medium' | 'low'; // Severity tier
  reason?: string;                     // Human-readable explanation
  pre_state?: Record<string, any>;     // Trip state before decision
  post_state?: Record<string, any>;    // Trip state after decision
  created_at?: string;                 // ISO timestamp when flag was raised
  acknowledged_at?: string;            // ISO timestamp when acknowledged (if applicable)
  acknowledged_by?: string;            // User ID who acknowledged (if applicable)
}

/**
 * API response from GET /trips/{trip_id}/suitability
 * Returns all suitability flags for a given trip with confidence and tier information.
 */
export interface SuitabilityFlagsResponse {
  trip_id: string;
  suitability_flags: SuitabilityFlag[];
}

export interface DecisionOutput {
  decision_state: string;
  hard_blockers: string[];
  soft_blockers: string[];
  contradictions: string[];
  risk_flags: string[];
  suitability_flags?: SuitabilityFlagData[];
  suitability_profile?: SuitabilityProfile | null;
  follow_up_questions: FollowUpQuestion[];
  rationale: Rationale;
  confidence: ConfidenceScorecard;
  branch_options: string[];
  commercial_decision: string;
  budget_breakdown: BudgetBreakdownResult | null;
}

export interface StrategyOutput {
  session_goal: string;
  priority_sequence: string[];
  tonal_guardrails: string[];
  risk_flags: string[];
  suggested_opening: string;
  exit_criteria: string[];
  next_action: string;
  assumptions: string[];
  suggested_tone: string;
}

export interface SlotValue {
  value: unknown;
  confidence: number;
  authority_level: string;
  extraction_mode: string;
  evidence_refs?: Array<{ envelope_id: string; excerpt: string }>;
  derived_from: string[];
}

export interface Ambiguity {
  field_name: string;
  ambiguity_type: string;
  raw_value: string;
}

export interface PacketUnknown {
  field_name: string;
  reason: string;
  notes: string | null;
}

export interface PacketContradiction {
  field_name: string;
  values: unknown[];
  sources: string[];
}

export interface ValidationReport {
  is_valid?: boolean;
  status?: string;
  gate?: string;
  reasons?: string[];
  errors?: Array<{ severity: string; code: string; message: string; field: string }>;
  warnings?: Array<{ severity: string; code: string; message: string; field: string }>;
}

export interface FeeBreakdown {
  service: string;
  base_fee: number;
  multiplier: number;
  adjusted_fee: number;
}

export interface FeeCalculationResult {
  service_breakdowns: Record<string, FeeBreakdown>;
  total_base_fee: number;
  total_adjusted_fee: number;
  fee_adjustment: number;
  risk_summary: string;
}
