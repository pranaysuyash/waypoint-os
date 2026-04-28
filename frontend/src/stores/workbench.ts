import { create } from "zustand";
import type {
  SpineStage,
  OperatingMode,
  SafetyResult,
  SpineRunResponse,
  DecisionOutput,
  StrategyOutput,
  PromptBundle,
  FeeCalculationResult,
  ValidationReport,
} from "@/types/spine";

// ============================================================================
// TYPES
// ============================================================================

interface WorkbenchInputState {
  input_raw_note: string;
  input_owner_note: string;
  input_structured_json: string;
  input_itinerary_text: string;
  setInputRawNote: (value: string) => void;
  setInputOwnerNote: (value: string) => void;
  setInputStructuredJson: (value: string) => void;
  setInputItineraryText: (value: string) => void;
}

interface WorkbenchConfigState {
  operating_mode: OperatingMode;
  stage: SpineStage;
  scenario_id: string;
  strict_leakage: boolean;
  debug_raw_json: boolean;
  enable_ghost_concierge: boolean;
  enable_sentiment_analysis: boolean;
  federated_intelligence_opt_in: boolean;
  audit_confidence_threshold: number;
  enable_auto_negotiation: boolean;
  negotiation_margin_threshold: number;
  setOperatingMode: (value: OperatingMode) => void;
  setStage: (value: SpineStage) => void;
  setScenarioId: (value: string) => void;
  setStrictLeakage: (value: boolean) => void;
  setDebugRawJson: (value: boolean) => void;
  setEnableGhostConcierge: (value: boolean) => void;
  setEnableSentimentAnalysis: (value: boolean) => void;
  setFederatedIntelligenceOptIn: (value: boolean) => void;
  setAuditConfidenceThreshold: (value: number) => void;
  setEnableAutoNegotiation: (value: boolean) => void;
  setNegotiationMarginThreshold: (value: number) => void;
}

interface WorkbenchResultState {
  result_packet: unknown;
  result_validation: ValidationReport | null;
  result_decision: DecisionOutput | null;
  result_strategy: StrategyOutput | null;
  result_internal_bundle: unknown;
  result_traveler_bundle: unknown;
  result_safety: SafetyResult | null;
  result_fees: FeeCalculationResult | null;
  result_frontier: any | null;
  result_run_ts: string | null;
  // Suitability acknowledgment — cross-tab session state.
  // Populated optimistically when an operator acknowledges a Tier 1 flag;
  // cleared on pipeline reset. Consumed by ReviewControls to gate approval.
  acknowledged_suitability_flags: ReadonlySet<string>;
  setResultPacket: (value: unknown) => void;
  setResultValidation: (value: ValidationReport | null) => void;
  setResultDecision: (value: DecisionOutput | null) => void;
  setResultStrategy: (value: StrategyOutput | null) => void;
  setResultInternalBundle: (value: unknown) => void;
  setResultTravelerBundle: (value: unknown) => void;
  setResultSafety: (value: SafetyResult | null) => void;
  setResultFees: (value: FeeCalculationResult | null) => void;
  setResultFrontier: (value: any | null) => void;
  setResultRunTs: (value: string | null) => void;
  acknowledgeFlag: (flagType: string) => void;
  clearResults: () => void;
  clearTransientRunResults: () => void;
  resetAll: () => void;
}

type WorkbenchStore = WorkbenchInputState &
  WorkbenchConfigState &
  WorkbenchResultState;

// ============================================================================
// STORE
// ============================================================================

export const useWorkbenchStore = create<WorkbenchStore>((set) => ({
  // Input state
  input_raw_note: "",
  input_owner_note: "",
  input_structured_json: "",
  input_itinerary_text: "",
  setInputRawNote: (value) => set({ input_raw_note: value }),
  setInputOwnerNote: (value) => set({ input_owner_note: value }),
  setInputStructuredJson: (value) => set({ input_structured_json: value }),
  setInputItineraryText: (value) => set({ input_itinerary_text: value }),

  // Config state
  operating_mode: "normal_intake",
  stage: "discovery",
  scenario_id: "",
  strict_leakage: false,
  debug_raw_json: false,
  enable_ghost_concierge: true,
  enable_sentiment_analysis: true,
  federated_intelligence_opt_in: true,
  audit_confidence_threshold: 0.9,
  setOperatingMode: (value) => set({ operating_mode: value }),
  setStage: (value) => set({ stage: value }),
  setScenarioId: (value) => set({ scenario_id: value }),
  setStrictLeakage: (value) => set({ strict_leakage: value }),
  setDebugRawJson: (value) => set({ debug_raw_json: value }),
  setEnableGhostConcierge: (value) => set({ enable_ghost_concierge: value }),
  setEnableSentimentAnalysis: (value) => set({ enable_sentiment_analysis: value }),
  setFederatedIntelligenceOptIn: (value) => set({ federated_intelligence_opt_in: value }),
  setAuditConfidenceThreshold: (value) => set({ audit_confidence_threshold: value }),
  enable_auto_negotiation: true,
  negotiation_margin_threshold: 0.15,
  setEnableAutoNegotiation: (value) => set({ enable_auto_negotiation: value }),
  setNegotiationMarginThreshold: (value) => set({ negotiation_margin_threshold: value }),

  // Result state
  result_packet: null,
  result_validation: null,
  result_decision: null,
  result_strategy: null,
  result_internal_bundle: null,
  result_traveler_bundle: null,
  result_safety: null,
  result_fees: null,
  result_frontier: null,
  result_run_ts: null,
  acknowledged_suitability_flags: new Set<string>(),
  setResultPacket: (value) => set({ result_packet: value }),
  setResultValidation: (value) => set({ result_validation: value }),
  setResultDecision: (value) => set({ result_decision: value }),
  setResultStrategy: (value) => set({ result_strategy: value }),
  setResultInternalBundle: (value) => set({ result_internal_bundle: value }),
  setResultTravelerBundle: (value) => set({ result_traveler_bundle: value }),
  setResultSafety: (value) => set({ result_safety: value }),
  setResultFees: (value) => set({ result_fees: value }),
  setResultFrontier: (value) => set({ result_frontier: value }),
  setResultRunTs: (value) => set({ result_run_ts: value }),
  acknowledgeFlag: (flagType) =>
    set((state) => ({
      acknowledged_suitability_flags: new Set([...state.acknowledged_suitability_flags, flagType]),
    })),

  clearResults: () => set({
    result_packet: null,
    result_validation: null,
    result_decision: null,
    result_strategy: null,
    result_internal_bundle: null,
    result_traveler_bundle: null,
    result_safety: null,
    result_fees: null,
    result_frontier: null,
    result_run_ts: null,
    acknowledged_suitability_flags: new Set<string>(),
  }),

  clearTransientRunResults: () => set({
    result_frontier: null,
    result_run_ts: null,
    acknowledged_suitability_flags: new Set<string>(),
  }),

  resetAll: () => set({
    input_raw_note: "",
    input_owner_note: "",
    input_structured_json: "",
    input_itinerary_text: "",
    result_packet: null,
    result_validation: null,
    result_decision: null,
    result_strategy: null,
    result_internal_bundle: null,
    result_traveler_bundle: null,
    result_safety: null,
    result_frontier: null,
    result_run_ts: null,
    acknowledged_suitability_flags: new Set<string>(),
  }),
}));

export type { WorkbenchStore };
