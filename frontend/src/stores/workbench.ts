import { create } from "zustand";
import type {
  SpineStage,
  OperatingMode,
  DecisionState,
  LeakageResult,
  SpineRunResponse,
} from "@/types/spine";

interface WorkbenchInputState {
  input_raw_note: string;
  input_owner_note: string;
  input_structured_json: string;
  input_itinerary_text: string;
}

interface WorkbenchConfigState {
  operating_mode: OperatingMode;
  stage: SpineStage;
  scenario_id: string;
  strict_leakage: boolean;
  debug_raw_json: boolean;
}

interface WorkbenchResultState {
  result_packet: SpineRunResponse["packet"] | null;
  result_validation: SpineRunResponse["validation"] | null;
  result_decision: SpineRunResponse["decision"] | null;
  result_strategy: SpineRunResponse["strategy"] | null;
  result_internal_bundle: SpineRunResponse["internal_bundle"] | null;
  result_traveler_bundle: SpineRunResponse["traveler_bundle"] | null;
  result_leakage: LeakageResult | null;
  result_assertions: SpineRunResponse["assertions"] | null;
  result_run_ts: string | null;
}

type WorkbenchStore = WorkbenchInputState &
  WorkbenchConfigState &
  WorkbenchResultState;

export const useWorkbenchStore = create<WorkbenchStore>((set) => ({
  input_raw_note: "",
  input_owner_note: "",
  input_structured_json: "",
  input_itinerary_text: "",

  operating_mode: "normal_intake",
  stage: "discovery",
  scenario_id: "",
  strict_leakage: false,
  debug_raw_json: false,

  result_packet: null,
  result_validation: null,
  result_decision: null,
  result_strategy: null,
  result_internal_bundle: null,
  result_traveler_bundle: null,
  result_leakage: null,
  result_assertions: null,
  result_run_ts: null,
}));

export type { WorkbenchStore };