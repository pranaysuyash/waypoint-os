import { create } from "zustand";
import type {
  SpineStage,
  OperatingMode,
  SafetyResult,
  SpineRunResponse,
} from "@/types/spine";

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
  setOperatingMode: (value: OperatingMode) => void;
  setStage: (value: SpineStage) => void;
  setScenarioId: (value: string) => void;
  setStrictLeakage: (value: boolean) => void;
  setDebugRawJson: (value: boolean) => void;
}

interface WorkbenchResultState {
  result_packet: SpineRunResponse["packet"] | null;
  result_validation: SpineRunResponse["validation"] | null;
  result_decision: SpineRunResponse["decision"] | null;
  result_strategy: SpineRunResponse["strategy"] | null;
  result_internal_bundle: SpineRunResponse["internal_bundle"] | null;
  result_traveler_bundle: SpineRunResponse["traveler_bundle"] | null;
  result_safety: SafetyResult | null;
  result_run_ts: string | null;
  setResultPacket: (value: SpineRunResponse["packet"]) => void;
  setResultValidation: (value: SpineRunResponse["validation"]) => void;
  setResultDecision: (value: SpineRunResponse["decision"]) => void;
  setResultStrategy: (value: SpineRunResponse["strategy"]) => void;
  setResultInternalBundle: (value: SpineRunResponse["internal_bundle"]) => void;
  setResultTravelerBundle: (value: SpineRunResponse["traveler_bundle"]) => void;
  setResultSafety: (value: SafetyResult | null) => void;
  setResultRunTs: (value: string | null) => void;
}

type WorkbenchStore = WorkbenchInputState &
  WorkbenchConfigState &
  WorkbenchResultState;

export const useWorkbenchStore = create<WorkbenchStore>((set) => ({
  input_raw_note: "",
  input_owner_note: "",
  input_structured_json: "",
  input_itinerary_text: "",
  setInputRawNote: (value) => set({ input_raw_note: value }),
  setInputOwnerNote: (value) => set({ input_owner_note: value }),
  setInputStructuredJson: (value) => set({ input_structured_json: value }),
  setInputItineraryText: (value) => set({ input_itinerary_text: value }),

  operating_mode: "normal_intake",
  stage: "discovery",
  scenario_id: "",
  strict_leakage: false,
  debug_raw_json: false,
  setOperatingMode: (value) => set({ operating_mode: value }),
  setStage: (value) => set({ stage: value }),
  setScenarioId: (value) => set({ scenario_id: value }),
  setStrictLeakage: (value) => set({ strict_leakage: value }),
  setDebugRawJson: (value) => set({ debug_raw_json: value }),

  result_packet: null,
  result_validation: null,
  result_decision: null,
  result_strategy: null,
  result_internal_bundle: null,
  result_traveler_bundle: null,
  result_safety: null,
  result_run_ts: null,
  setResultPacket: (value) => set({ result_packet: value }),
  setResultValidation: (value) => set({ result_validation: value }),
  setResultDecision: (value) => set({ result_decision: value }),
  setResultStrategy: (value) => set({ result_strategy: value }),
  setResultInternalBundle: (value) => set({ result_internal_bundle: value }),
  setResultTravelerBundle: (value) => set({ result_traveler_bundle: value }),
  setResultSafety: (value) => set({ result_safety: value }),
  setResultRunTs: (value) => set({ result_run_ts: value }),
}));

export type { WorkbenchStore };
