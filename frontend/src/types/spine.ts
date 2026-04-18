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

export interface SafetyResult {
  strict_leakage: boolean;
  leakage_passed: boolean;
  leakage_errors: string[];
}

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

export interface RunMeta {
  stage: string;
  operating_mode: string;
  fixture_id: string | null;
  execution_ms: number;
}

export interface AssertionResult {
  type: string;
  passed: boolean;
  message: string;
  field?: string;
}

export interface SpineRunResponse {
  ok: boolean;
  run_id: string;
  packet: unknown | null;
  validation: unknown | null;
  decision: unknown | null;
  strategy: unknown | null;
  internal_bundle: unknown | null;
  traveler_bundle: unknown | null;
  safety: SafetyResult;
  assertions: AssertionResult[] | null;
  meta: RunMeta;
}

export interface SpineRunRequest {
  raw_note?: string | null;
  owner_note?: string | null;
  structured_json?: Record<string, unknown> | null;
  itinerary_text?: string | null;
  stage: SpineStage;
  operating_mode: OperatingMode;
  strict_leakage: boolean;
  scenario_id?: string | null;
}