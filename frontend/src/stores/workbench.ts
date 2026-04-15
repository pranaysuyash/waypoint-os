import { create } from "zustand";
import type {
  SpineStage,
  OperatingMode,
  SafetyResult,
  SpineRunResponse,
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

// Which state properties should sync with URL
interface UrlSyncState {
  url_stage: SpineStage;
  url_mode: OperatingMode;
  url_scenario: string;
  setUrlStage: (value: SpineStage) => void;
  setUrlMode: (value: OperatingMode) => void;
  setUrlScenario: (value: string) => void;
}

type WorkbenchStore = WorkbenchInputState &
  WorkbenchConfigState &
  WorkbenchResultState &
  UrlSyncState;

// ============================================================================
// URL SYNC MIDDLEWARE
// ============================================================================

function urlSyncMiddleware<T extends WorkbenchStore>(
  config: (set: any, get: any, api: any) => T
): (set: any, get: any, api: any) => T {
  return (set, get, api) => {
    const store = config(set, get, api);

    // Initialize from URL on first load
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);

      const urlStage = params.get("stage") as SpineStage | null;
      const urlMode = params.get("mode") as OperatingMode | null;
      const urlScenario = params.get("scenario");

      if (urlStage && ["discovery", "shortlist", "proposal", "booking"].includes(urlStage)) {
        store.setStage(urlStage);
        store.setUrlStage(urlStage);
      }
      if (urlMode) {
        store.setOperatingMode(urlMode);
        store.setUrlMode(urlMode);
      }
      if (urlScenario) {
        store.setScenarioId(urlScenario);
        store.setUrlScenario(urlScenario);
      }
    }

    // Override setters to update URL
    const originalSetStage = store.setStage.bind(store);
    const originalSetOperatingMode = store.setOperatingMode.bind(store);
    const originalSetScenarioId = store.setScenarioId.bind(store);

    store.setStage = (value: SpineStage) => {
      originalSetStage(value);
      store.setUrlStage(value);
    };

    store.setOperatingMode = (value: OperatingMode) => {
      originalSetOperatingMode(value);
      store.setUrlMode(value);
    };

    store.setScenarioId = (value: string) => {
      originalSetScenarioId(value);
      store.setUrlScenario(value);
    };

    // Listen for URL sync changes and update URL
    api.subscribe((state: T) => {
      if (typeof window === "undefined") return;

      const url = new URL(window.location.href);
      const { url_stage, url_mode, url_scenario } = state as unknown as UrlSyncState;

      // Update URL without triggering navigation
      if (url_stage) url.searchParams.set("stage", url_stage);
      if (url_mode) url.searchParams.set("mode", url_mode);
      if (url_scenario) url.searchParams.set("scenario", url_scenario);

      const newUrl = url.toString();
      if (newUrl !== window.location.href) {
        window.history.replaceState(null, "", newUrl);
      }
    });

    return store;
  };
}

// ============================================================================
// STORE
// ============================================================================

export const useWorkbenchStore = create<WorkbenchStore>()(
  urlSyncMiddleware((set) => ({
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
    setOperatingMode: (value) => set({ operating_mode: value }),
    setStage: (value) => set({ stage: value }),
    setScenarioId: (value) => set({ scenario_id: value }),
    setStrictLeakage: (value) => set({ strict_leakage: value }),
    setDebugRawJson: (value) => set({ debug_raw_json: value }),

    // Result state
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

    // URL sync state (separate from actual config to avoid loops)
    url_stage: "discovery",
    url_mode: "normal_intake",
    url_scenario: "",
    setUrlStage: (value) => set({ url_stage: value }),
    setUrlMode: (value) => set({ url_mode: value }),
    setUrlScenario: (value) => set({ url_scenario: value }),
  }))
);

export type { WorkbenchStore };
