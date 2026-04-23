"use client";

import { useCallback } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import { useTripContext } from "@/contexts/TripContext";
import type { DecisionState, BudgetBreakdownResult, CostBucketEstimate, DecisionOutput, SuitabilityFlagData } from "@/types/spine";
import { SuitabilitySignal } from "./SuitabilitySignal";

interface DecisionPanelProps {
  trip?: any;
  tripId?: string;
}

const STATE_LABELS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE: "Ready to Book",
  PROCEED_INTERNAL_DRAFT: "Draft Quote",
  BRANCH_OPTIONS: "Needs Options",
  STOP_NEEDS_REVIEW: "Needs Attention",
  STOP_REVIEW: "Needs Attention",
  ASK_FOLLOWUP: "Need More Info",
};

const BUCKET_DISPLAY: Record<string, string> = {
  flights: "Flights",
  stay: "Stay",
  food: "Food",
  local_transport: "Local Transport",
  activities: "Activities",
  visa_insurance: "Visa / Insurance",
  shopping: "Shopping",
  buffer: "Buffer",
};

export function DecisionPanel({ trip: propTrip, tripId: propTripId }: DecisionPanelProps) {
  let context;
  try {
    context = useTripContext();
  } catch (e) {}

  const trip = propTrip || context?.trip || null;
  const tripId = propTripId || trip?.id || context?.tripId || "";

  const { result_decision, debug_raw_json, setDebugRawJson } = useWorkbenchStore();
  const decision = (result_decision || trip?.decision) as DecisionOutput;

  if (!decision) {
    return (
      <div className="p-4 text-sm text-gray-500 italic">
        No quote status data for trip {tripId || "unknown"}.
      </div>
    );
  }

  const rationale = decision.rationale || {};
  const hardBlockers = decision.hard_blockers || [];
  const softBlockers = decision.soft_blockers || [];
  const contradictions = decision.contradictions || [];
  const suitabilityFlags: SuitabilityFlagData[] = decision.suitability_flags || [];

  const handleSuitabilityDrill = useCallback((flagType: string) => {
    // Logic remains
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Decision State</h3>
        <span className="inline-block px-2 py-1 text-xs font-medium rounded-md bg-blue-900/30 text-blue-300">
          {STATE_LABELS[decision.decision_state] || decision.decision_state}
        </span>
        <p className="mt-3 text-sm text-gray-300">
          Overall Confidence: {Math.round((decision.confidence?.overall || 0) * 100)}%
        </p>
      </div>

      {/* Rationale Section */}
      <section className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Rationale</h3>
        <div className="bg-[#0a0d11] p-4 rounded-lg border border-[#1c2128]">
          <p className="text-sm text-gray-300">{rationale.feasibility || "—"}</p>
          {(hardBlockers.length > 0 || softBlockers.length > 0) && (
            <div className="mt-4 space-y-2">
              {hardBlockers.length > 0 && (
                <div className="text-xs text-red-400">
                  <strong className="block font-semibold">Hard Blockers:</strong>
                  <ul className="list-disc list-inside mt-1">
                    {hardBlockers.map((b, i) => <li key={i}>{b}</li>)}
                  </ul>
                </div>
              )}
              {softBlockers.length > 0 && (
                <div className="text-xs text-amber-400">
                  <strong className="block font-semibold">Soft Blockers:</strong>
                  <ul className="list-disc list-inside mt-1">
                    {softBlockers.map((b, i) => <li key={i}>{b}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Suitability Audit Results */}
      <SuitabilitySignal 
        flags={suitabilityFlags} 
        tripId={tripId}
        onDrill={handleSuitabilityDrill}
      />

      <button
        type="button"
        className="text-xs text-blue-400 hover:text-blue-300 underline"
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>
    </div>
  );
}
