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

export interface RunMeta {
  stage: string;
  operating_mode: string;
  fixture_id: string | null;
  execution_ms: number;
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