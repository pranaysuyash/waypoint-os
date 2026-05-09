"use client";

import { useCallback, useState } from "react";
import { acknowledgeSuitabilityFlags, transitionTripStage } from "@/lib/api-client";
import { useWorkbenchStore } from "@/stores/workbench";
import { useTripContext } from "@/contexts/TripContext";
import type { DecisionState, BudgetBreakdownResult, CostBucketEstimate, DecisionOutput, SuitabilityFlagData, SuitabilityProfile } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import { SuitabilitySignal } from "./SuitabilitySignal";
import { SuitabilityCard } from "./SuitabilityCard";
import { StageAdvanceButton } from "./StageAdvanceButton";
import { STATE_COLORS } from "@/lib/tokens";
import Link from "next/link";

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
  const context = useTripContext({ optional: true });

  const trip = propTrip || context?.trip || null;
  const tripId = propTripId || trip?.id || context?.tripId || "";

  const { result_decision, result_validation, debug_raw_json, setDebugRawJson, acknowledged_suitability_flags, acknowledgeFlag } = useWorkbenchStore();
  const decision: DecisionOutput | null = result_decision || trip?.decision || null;
  const validation = result_validation || trip?.validation || null;

  const handleSuitabilityDrill = useCallback((_flagType: string) => {
    document.querySelector('[data-testid="timeline-panel"]')?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleAcknowledge = useCallback(async (flagType: string) => {
    acknowledgeFlag(flagType);
    if (tripId) {
      try { await acknowledgeSuitabilityFlags(tripId, [flagType]); } catch {}
    }
  }, [tripId, acknowledgeFlag]);

  if (!decision) {
    return (
      <div className="p-6 text-center">
        <h2 className="text-ui-xl font-semibold text-text-primary">Build options first</h2>
        <p className="text-ui-sm text-text-muted mt-2">Quote assessment will appear after trip options are generated.</p>
        <div className="mt-6 flex flex-wrap gap-3 justify-center">
          <Link
            href={`/trips/${tripId}/strategy`}
            className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
          >
            Go to Options
          </Link>
        </div>
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

  // Map decision state to visual treatment
  const STATE_KEY: Record<string, keyof typeof STATE_COLORS> = {
    PROCEED_TRAVELER_SAFE: "green",
    PROCEED_INTERNAL_DRAFT: "blue",
    BRANCH_OPTIONS: "amber",
    STOP_NEEDS_REVIEW: "red",
    STOP_REVIEW: "red",
    ASK_FOLLOWUP: "purple",
  };
  const stateColor = STATE_COLORS[STATE_KEY[decision.decision_state] ?? "neutral"];

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
            <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest mb-1.5" style={{ color: stateColor.color }}>
              Quote Assessment
            </div>
            <div className="text-ui-lg font-semibold text-text-primary" style={{ fontFamily: "'Outfit', sans-serif" }}>
              {STATE_LABELS[decision.decision_state] || "Review Required"}
            </div>
          </div>
          {confidence > 0 && (
            <div className="text-right shrink-0">
              <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder mb-1">Confidence</div>
              <div className="text-ui-2xl font-black" style={{ color: stateColor.color, fontFamily: "'Outfit', sans-serif" }}>
                {confidence}%
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Readiness banner */}
      {(() => {
        const readiness = (validation as Record<string, unknown> | null)?.readiness as {
          highest_ready_tier: string | null;
          suggested_next_stage: string;
          should_auto_advance_stage: boolean;
          missing_for_next: string[];
        } | undefined;
        if (!readiness) return null;
        const tierLabel: Record<string, string> = {
          intake_minimum: "Intake",
          quote_ready: "Quote Ready",
          proposal_ready: "Proposal Ready",
          booking_ready: "Booking Ready",
        };
        const label = tierLabel[readiness.highest_ready_tier ?? ""] ?? "Not Ready";
        const missing = readiness.missing_for_next ?? [];
        const currentStage = trip?.stage ?? (trip?.packet as Record<string, unknown> | undefined)?.stage as string ?? "discovery";
        const canAdvance = readiness.suggested_next_stage && readiness.highest_ready_tier && readiness.suggested_next_stage !== currentStage && tripId;
        return (
          <div className="rounded-xl p-3 border border-[rgba(var(--accent-blue-rgb)/0.2)] bg-[rgba(var(--accent-blue-rgb)/0.04)]">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-accent-blue">Readiness</span>
              <span className="inline-flex items-center rounded-full bg-accent-blue/10 px-2 py-0.5 text-[var(--ui-text-xs)] font-semibold text-accent-blue">{label}</span>
              {missing.length > 0 && (
                <span className="text-ui-sm text-text-muted">
                  {missing.length} field{missing.length !== 1 ? "s" : ""} needed for {tierLabel[readiness.suggested_next_stage] ?? readiness.suggested_next_stage}
                </span>
              )}
              {canAdvance && (
                <StageAdvanceButton
                  tripId={tripId}
                  currentStage={currentStage}
                  targetStage={readiness.suggested_next_stage}
                  tierLabel={tierLabel[readiness.suggested_next_stage] ?? readiness.suggested_next_stage}
                />
              )}
            </div>
          </div>
        );
      })()}

      {/* Hard blockers - prominent */}
      {hardBlockers.length > 0 && (
        <div className="rounded-xl p-4 border border-[rgba(var(--accent-red-rgb)/0.3)] bg-[rgba(var(--accent-red-rgb)/0.06)]">
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-accent-red mb-2">
            Hard Blockers - must resolve before quoting
          </div>
          <ul className="space-y-1.5">
            {hardBlockers.map((b) => (
              <li key={`hb-${b.slice(0, 30)}`} className="flex items-start gap-2 text-ui-sm text-accent-red">
                <span className="mt-0.5 shrink-0">✕</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Soft blockers */}
      {softBlockers.length > 0 && (
        <div className="rounded-xl p-4 border border-[rgba(var(--accent-amber-rgb)/0.25)] bg-[rgba(var(--accent-amber-rgb)/0.06)]">
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-accent-amber mb-2">
            Soft Blockers - worth discussing
          </div>
          <ul className="space-y-1.5">
            {softBlockers.map((b) => (
              <li key={`sb-${b.slice(0, 30)}`} className="flex items-start gap-2 text-ui-sm text-accent-amber">
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
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder">Rationale</div>
          <div className="rounded-xl p-4 border border-highlight bg-rationale">
            <p className="text-ui-sm text-text-rationale leading-relaxed">{rationale.feasibility}</p>
          </div>
        </section>
      )}

      {/* Suitability */}
      {suitabilityProfile ? (
        <section className="space-y-2">
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder">Suitability Audit</div>
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
        className="text-[var(--ui-text-xs)] text-text-placeholder hover:text-text-muted transition-colors underline underline-offset-2"
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} raw JSON
      </button>
    </div>
  );
}
