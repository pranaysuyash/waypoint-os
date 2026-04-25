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
  SystemicError,
  OrphanTrip,
  SuitabilitySignal,
} from '@/types/generated/spine-api';

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

export interface DecisionOutput {
  decision_state: string;
  hard_blockers: string[];
  soft_blockers: string[];
  contradictions: string[];
  risk_flags: string[];
  suitability_flags?: SuitabilityFlagData[];
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
  is_valid: boolean;
  errors: Array<{ severity: string; code: string; message: string; field: string }>;
  warnings: Array<{ severity: string; code: string; message: string; field: string }>;
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
