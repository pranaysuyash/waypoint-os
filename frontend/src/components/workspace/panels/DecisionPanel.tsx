"use client";

import { useCallback } from "react";
import { acknowledgeSuitabilityFlags } from "@/lib/api-client";
import { useWorkbenchStore } from "@/stores/workbench";
import { useTripContext } from "@/contexts/TripContext";
import type { DecisionState, BudgetBreakdownResult, CostBucketEstimate, DecisionOutput, SuitabilityFlagData, SuitabilityProfile } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import { SuitabilitySignal } from "./SuitabilitySignal";
import { SuitabilityCard } from "./SuitabilityCard";

interface DecisionPanelProps {
  trip?: Trip | null;
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

  const { result_decision, debug_raw_json, setDebugRawJson, acknowledged_suitability_flags, acknowledgeFlag } = useWorkbenchStore();
  const decision: DecisionOutput | null = result_decision || trip?.decision || null;

  if (!decision) {
    return (
      <div className="p-4 text-sm text-[#8b949e] italic">
        No quote status data for trip {tripId || "unknown"}.
      </div>
    );
  }

  const rationale = decision.rationale || {};
  const hardBlockers = decision.hard_blockers || [];
  const softBlockers = decision.soft_blockers || [];
  const contradictions = decision.contradictions || [];
  const suitabilityFlags: SuitabilityFlagData[] = decision.suitability_flags || [];

  // Shadow-field pattern: prefer structured suitability_profile when available,
  // fall back to flat suitability_flags for backward compatibility.
  const suitabilityProfile: SuitabilityProfile | null | undefined =
    decision.suitability_profile;

  const handleSuitabilityDrill = useCallback((_flagType: string) => {
    document.querySelector('[data-testid="timeline-panel"]')?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleAcknowledge = useCallback(async (flagType: string) => {
    acknowledgeFlag(flagType);
    if (tripId) {
      try { await acknowledgeSuitabilityFlags(tripId, [flagType]); } catch {}
    }
  }, [tripId, acknowledgeFlag]);

  // Map decision state to visual treatment
  const stateColor = {
    PROCEED_TRAVELER_SAFE:  { color: '#3fb950', bg: 'rgba(63,185,80,0.1)',   border: 'rgba(63,185,80,0.25)'  },
    PROCEED_INTERNAL_DRAFT: { color: '#58a6ff', bg: 'rgba(88,166,255,0.1)',  border: 'rgba(88,166,255,0.25)' },
    BRANCH_OPTIONS:         { color: '#d29922', bg: 'rgba(210,153,34,0.1)',  border: 'rgba(210,153,34,0.25)' },
    STOP_NEEDS_REVIEW:      { color: '#f85149', bg: 'rgba(248,81,73,0.08)',  border: 'rgba(248,81,73,0.25)'  },
    STOP_REVIEW:            { color: '#f85149', bg: 'rgba(248,81,73,0.08)',  border: 'rgba(248,81,73,0.25)'  },
    ASK_FOLLOWUP:           { color: '#a371f7', bg: 'rgba(163,113,247,0.1)', border: 'rgba(163,113,247,0.25)'},
  }[decision.decision_state] ?? { color: '#8b949e', bg: 'rgba(139,148,158,0.08)', border: 'rgba(139,148,158,0.2)' };

  const confidence = Math.round((decision.confidence?.overall || 0) * 100);

  return (
    <div className="space-y-5">

      {/* Decision state card */}
      <div
        className="rounded-xl p-4 border"
        style={{ background: stateColor.bg, borderColor: stateColor.border }}
      >
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: stateColor.color }}>
              Quote Assessment
            </div>
            <div className="text-lg font-semibold text-[#e6edf3]" style={{ fontFamily: "'Outfit', sans-serif" }}>
              {STATE_LABELS[decision.decision_state] || "Review Required"}
            </div>
          </div>
          {confidence > 0 && (
            <div className="text-right shrink-0">
              <div className="text-[10px] font-bold uppercase tracking-widest text-[#484f58] mb-1">Confidence</div>
              <div className="text-2xl font-black" style={{ color: stateColor.color, fontFamily: "'Outfit', sans-serif" }}>
                {confidence}%
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hard blockers — prominent */}
      {hardBlockers.length > 0 && (
        <div className="rounded-xl p-4 border border-[rgba(248,81,73,0.3)] bg-[rgba(248,81,73,0.06)]">
          <div className="text-[10px] font-bold uppercase tracking-widest text-[#f85149] mb-2">
            Hard Blockers — must resolve before quoting
          </div>
          <ul className="space-y-1.5">
            {hardBlockers.map((b, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#f85149]">
                <span className="mt-0.5 shrink-0">✕</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Soft blockers */}
      {softBlockers.length > 0 && (
        <div className="rounded-xl p-4 border border-[rgba(210,153,34,0.25)] bg-[rgba(210,153,34,0.06)]">
          <div className="text-[10px] font-bold uppercase tracking-widest text-[#d29922] mb-2">
            Soft Blockers — worth discussing
          </div>
          <ul className="space-y-1.5">
            {softBlockers.map((b, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#d29922]">
                <span className="mt-0.5 shrink-0">△</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Rationale */}
      {rationale.feasibility && (
        <section className="space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-widest text-[#484f58]">Rationale</div>
          <div className="rounded-xl p-4 border border-[#1c2128] bg-[#0d1117]">
            <p className="text-sm text-[#c9d1d9] leading-relaxed">{rationale.feasibility}</p>
          </div>
        </section>
      )}

      {/* Suitability */}
      {suitabilityProfile ? (
        <section className="space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-widest text-[#484f58]">Suitability Audit</div>
          <SuitabilityCard profile={suitabilityProfile} />
        </section>
      ) : suitabilityFlags.length > 0 ? (
        <SuitabilitySignal
          flags={suitabilityFlags}
          tripId={tripId}
          onDrill={handleSuitabilityDrill}
          onAcknowledge={handleAcknowledge}
          acknowledgedFlags={acknowledged_suitability_flags}
        />
      ) : null}

      <button
        type="button"
        className="text-[11px] text-[#484f58] hover:text-[#8b949e] transition-colors underline underline-offset-2"
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} raw JSON
      </button>
    </div>
  );
}
