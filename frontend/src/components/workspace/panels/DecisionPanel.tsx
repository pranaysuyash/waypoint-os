"use client";

import { useCallback, useState, useEffect } from "react";
import { acknowledgeSuitabilityFlags, transitionTripStage, triageMessage, type LiveMessageTriageResponse } from "@/lib/api-client";
import { useWorkbenchStore } from "@/stores/workbench";
import { useTripContext } from "@/contexts/TripContext";
import type { DecisionState, BudgetBreakdownResult, CostBucketEstimate, DecisionOutput, FollowUpQuestion, SuitabilityFlagData, SuitabilityProfile } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import { SuitabilitySignal } from "./SuitabilitySignal";
import { SuitabilityCard } from "./SuitabilityCard";
import { StageAdvanceButton } from "./StageAdvanceButton";
import { STATE_COLORS } from "@/lib/tokens";
import Link from "next/link";
import { isDebugJsonAllowed } from "@/lib/privacy-controls";
import { titleCase } from "@/lib/label-maps";
import { getTripRepairRoute } from "@/lib/routes";
import { Zap, AlertTriangle, ShieldAlert } from "lucide-react";

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
  ASK_FOLLOWUP: "Waiting on Customer",
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

  const { result_decision, result_validation, debug_raw_json, setDebugRawJson, acknowledged_suitability_flags, acknowledgeFlag, input_raw_note } = useWorkbenchStore();
  const debugJsonAllowed = isDebugJsonAllowed();
  const decision: DecisionOutput | null = result_decision || trip?.decision || null;
  const validation = result_validation || trip?.validation || null;

  const [triageResult, setTriageResult] = useState<LiveMessageTriageResponse | null>(null);

  useEffect(() => {
    const rawNote = input_raw_note?.trim() || (trip?.customerMessage as string | undefined)?.trim();
    if (!rawNote || rawNote.length < 5) {
      setTriageResult(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await triageMessage(rawNote);
        if (res.ok) setTriageResult(res);
      } catch {
        // Non-blocking background advisory
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [input_raw_note, trip?.customerMessage]);

  const handleSuitabilityDrill = useCallback((_flagType: string) => {
    document.querySelector('[data-testid="timeline-panel"]')?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleAcknowledge = useCallback(async (flagType: string) => {
    acknowledgeFlag(flagType);
    if (tripId) {
      try { await acknowledgeSuitabilityFlags(tripId, [flagType]); } catch {}
    }
  }, [tripId, acknowledgeFlag]);

  const tripRepairHref = tripId ? getTripRepairRoute(tripId) : null;

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
          {tripRepairHref && (
            <Link
              href={tripRepairHref}
              className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
            >
              Open Trip Details to repair
            </Link>
          )}
        </div>
      </div>
    );
  }

  const rationale = decision.rationale || {};
  const hardBlockers = decision.hard_blockers || [];
  const softBlockers = decision.soft_blockers || [];
  const contradictions = decision.contradictions || [];
  const riskFlags: string[] = decision.risk_flags || [];
  const followupQuestions: FollowUpQuestion[] = decision.follow_up_questions || [];
  const budgetBreakdown: BudgetBreakdownResult | null = decision.budget_breakdown || null;
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

  const confidence = decision.confidence?.overall;
  const confidenceLabel =
    typeof confidence === "number" && Number.isFinite(confidence)
      ? `${Math.round(confidence * 100)}%`
      : "Confidence unavailable";

  return (
    <div className="space-y-5">

      {/* Live Jev Triage Advisory Banner (Expedition Lane A4) */}
      {triageResult && (
        <div className="rounded-xl p-3 border border-indigo-500/20 bg-indigo-500/5 text-ui-xs">
          <div className="flex items-center justify-between gap-2 flex-wrap mb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-indigo-400">
              <Zap className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
              <span>Jev Live Advisory</span>
              <span className="text-[10px] text-text-placeholder px-1.5 py-0.5 rounded bg-surface border border-indigo-500/20">
                {triageResult.source} • {Math.round(triageResult.latency_ms)}ms
              </span>
            </div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 font-medium">
                {triageResult.intent}
              </span>
              {triageResult.is_urgent && (
                <span className="px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 font-semibold flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" /> Urgent
                </span>
              )}
              {triageResult.has_policy_risk && (
                <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 font-semibold flex items-center gap-1">
                  <ShieldAlert className="h-3 w-3" /> Policy Risk
                </span>
              )}
            </div>
          </div>
          <p className="text-text-muted leading-relaxed">
            <strong className="text-text-primary">Suggested Route:</strong> {triageResult.routing_recommendation} — {triageResult.advisory}
          </p>
        </div>
      )}

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
          <div className="text-right shrink-0">
            <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder mb-1">Confidence</div>
            <div className="text-ui-2xl font-black" style={{ color: stateColor.color, fontFamily: "'Outfit', sans-serif" }}>
              {confidenceLabel}
            </div>
          </div>
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
        const missing = readiness.missing_for_next ?? [];
        const currentStage = trip?.stage ?? (trip?.packet as Record<string, unknown> | undefined)?.stage as string ?? "discovery";
        const baseLabel = tierLabel[readiness.highest_ready_tier ?? ""] ?? "Not Ready";
        const label = missing.length > 0 && readiness.highest_ready_tier === "quote_ready"
          ? "Quote Ready - needs shortlist details"
          : baseLabel;
        const canAutoAdvance = Boolean(
          readiness.suggested_next_stage &&
          readiness.highest_ready_tier &&
          readiness.suggested_next_stage !== currentStage &&
          tripId &&
          missing.length === 0,
        );
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
              {canAutoAdvance ? (
                <StageAdvanceButton
                  tripId={tripId}
                  currentStage={currentStage}
                  targetStage={readiness.suggested_next_stage}
                  tierLabel={tierLabel[readiness.suggested_next_stage] ?? readiness.suggested_next_stage}
                />
              ) : missing.length > 0 ? (
                <span className="text-ui-xs text-text-placeholder">
                  Complete the missing fields to enable automatic advancement.
                </span>
              ) : null}
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

      {/* Contradictions (ported from workbench DecisionTab — Supersession T2) */}
      {contradictions.length > 0 && (
        <div className="rounded-xl p-4 border border-[rgba(var(--accent-red-rgb)/0.25)] bg-[rgba(var(--accent-red-rgb)/0.04)]">
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-accent-red mb-2">
            Contradictions
          </div>
          <ul className="space-y-1.5">
            {contradictions.map((item) => (
              <li key={`contra-${String(item).slice(0, 30)}`} className="flex items-start gap-2 text-ui-sm text-accent-red">
                <span className="mt-0.5 shrink-0">✕</span>
                <span>{titleCase(String(item))}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risk flags (ported from workbench DecisionTab — Supersession T2) */}
      {riskFlags.length > 0 && (
        <div className="rounded-xl p-4 border border-[rgba(var(--accent-amber-rgb)/0.2)] bg-[rgba(var(--accent-amber-rgb)/0.04)]">
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-accent-amber mb-2">
            Risk Flags
          </div>
          <ul className="space-y-1.5">
            {riskFlags.map((item) => (
              <li key={`risk-${String(item).slice(0, 30)}`} className="flex items-start gap-2 text-ui-sm text-accent-amber">
                <span className="mt-0.5 shrink-0">!</span>
                <span>{item}</span>
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

      {/* Branch options — scored alternatives produced by the decision pipeline
          (budget-tier entries and route-structure candidates with scores). */}
      {(() => {
        const options = decision.branch_options ?? [];
        if (options.length === 0) return null;
        return (
          <section className="space-y-2" data-testid="branch-options">
            <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder">Branch Options</div>
            <div className="space-y-2">
              {options.map((option, index) => {
                const entry = typeof option === "string"
                  ? { label: option, description: undefined as string | undefined, route_structure: undefined }
                  : option;
                const score = entry.route_structure?.score;
                return (
                  <div
                    key={`branch-option-${index}-${entry.label.slice(0, 24)}`}
                    className="rounded-xl p-3 border border-[rgba(var(--accent-blue-rgb)/0.25)] bg-[rgba(var(--accent-blue-rgb)/0.04)]"
                  >
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="text-ui-sm font-semibold text-text-primary">{entry.label}</span>
                      {typeof score === "number" && (
                        <span className="text-[var(--ui-text-xs)] font-semibold text-accent-blue">
                          route score {score}
                        </span>
                      )}
                    </div>
                    {entry.description && (
                      <p className="text-ui-sm text-text-muted mt-1 leading-relaxed">{entry.description}</p>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        );
      })()}

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

      {/* Follow-up questions (ported from workbench DecisionTab — Supersession T2).
          These are the same questions the traveler ask loop delivers (FND-0301). */}
      {followupQuestions.length > 0 && (
        <section className="space-y-2" data-testid="decision-followups">
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder">Follow-up Questions</div>
          <ul className="space-y-2">
            {followupQuestions.map((q) => (
              <li key={`followup-${q.field_name}`} className="rounded-xl p-3 border border-[rgba(var(--accent-purple-rgb)/0.25)] bg-[rgba(var(--accent-purple-rgb)/0.04)]">
                <span className="text-ui-sm font-semibold text-text-primary">
                  [{q.priority ? q.priority.charAt(0).toUpperCase() + q.priority.slice(1) : "Medium"}] {titleCase(q.field_name)}
                </span>
                <p className="text-ui-sm text-text-muted mt-1 leading-relaxed">{q.question}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Budget breakdown (ported from workbench DecisionTab — Supersession T2) */}
      {budgetBreakdown && budgetBreakdown.buckets.length > 0 && (
        <section className="space-y-2" data-testid="decision-budget-breakdown">
          <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder">Budget Breakdown</div>
          <div className="rounded-xl p-4 border border-[var(--border-default)] bg-surface">
            <div className="flex items-center gap-3 flex-wrap mb-3">
              <span className="text-ui-sm font-semibold text-text-primary capitalize">{budgetBreakdown.verdict}</span>
              {budgetBreakdown.budget_stated != null && (
                <span className="text-ui-xs text-text-muted">
                  Budget: {budgetBreakdown.budget_stated.toLocaleString()} · Est. range:{" "}
                  {(budgetBreakdown.total_estimated_low ?? 0).toLocaleString()} – {(budgetBreakdown.total_estimated_high ?? 0).toLocaleString()}
                </span>
              )}
            </div>
            <table className="w-full text-left text-ui-sm">
              <thead>
                <tr className="border-b border-[var(--border-default)] text-[var(--ui-text-xs)] font-semibold text-text-placeholder uppercase tracking-wider">
                  <th className="py-2 pr-3">Bucket</th>
                  <th className="py-2 pr-3">Low</th>
                  <th className="py-2 pr-3">High</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {budgetBreakdown.buckets.map((b: CostBucketEstimate) => (
                  <tr key={b.bucket}>
                    <td className="py-2 pr-3">{BUCKET_DISPLAY[b.bucket] || titleCase(b.bucket)}</td>
                    <td className="py-2 pr-3">{(b.low ?? 0).toLocaleString()}</td>
                    <td className="py-2 pr-3">{(b.high ?? 0).toLocaleString()}</td>
                    <td className="py-2">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[var(--ui-text-xs)] font-semibold ${b.covered ? "bg-accent-green/10 text-accent-green" : "bg-accent-red/10 text-accent-red"}`}>
                        {b.covered ? "Covered" : "Gap"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(budgetBreakdown.missing_buckets?.length ?? 0) > 0 && (
              <p className="text-ui-xs text-accent-amber mt-3">
                Missing buckets: {budgetBreakdown.missing_buckets.map((m: string) => BUCKET_DISPLAY[m] || m).join(", ")}
              </p>
            )}
          </div>
        </section>
      )}

      {!debugJsonAllowed && (
        <div className="rounded border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-ui-xs text-amber-200">
          Technical Data is hidden by privacy policy. Set <code>NEXT_PUBLIC_ALLOW_DEBUG_JSON=true</code> in a secure environment to enable.
        </div>
      )}

      <button
        type="button"
        className="text-[var(--ui-text-xs)] text-text-placeholder hover:text-text-muted transition-colors underline underline-offset-2 disabled:opacity-50"
        disabled={!debugJsonAllowed}
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} raw JSON
      </button>
    </div>
  );
}
