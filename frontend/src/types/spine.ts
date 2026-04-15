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

export interface LeakageResult {
  leaks: string[];
  is_safe: boolean;
  traveler_bundle_leaks: string[];
  sanitized_view_leaks: string[];
}

export interface SpineRunResponse {
  packet: unknown;
  validation: unknown;
  decision: unknown;
  strategy: unknown;
  internal_bundle: unknown;
  traveler_bundle: unknown;
  leakage: {
    ok: boolean;
    items: string[];
  };
  assertions: unknown;
  run_ts: string;
}