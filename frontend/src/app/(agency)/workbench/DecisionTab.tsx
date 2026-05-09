"use client";

import { useCallback } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import { acknowledgeSuitabilityFlags } from "@/lib/api-client";
import { SuitabilitySignal } from "@/components/workspace/panels/SuitabilitySignal";
import type { DecisionState, BudgetBreakdownResult, CostBucketEstimate, DecisionOutput, FollowUpQuestion, Rationale, SuitabilityFlagData } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import { DECISION_STATE_LABELS, titleCase, labelOrTitle } from "@/lib/label-maps";
import styles from "@/components/workbench/workbench.module.css";

/**
 * Canonical badge-class lookup.
 * Only contains the correct spelling of each state key.
 * Unknown states fall through to styles.stateBlue (visible, not silent).
 */
const STATE_BADGE_CLASS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE:   styles.stateGreen,
  PROCEED_INTERNAL_DRAFT:  styles.stateAmber,
  BRANCH_OPTIONS:          styles.stateAmber,
  STOP_NEEDS_REVIEW:       styles.stateRed,
  ASK_FOLLOWUP:            styles.stateBlue,
};

/**
 * Known typo/alias variants emitted by older API responses.
 * Maps to the canonical spelling before badge-class lookup.
 * Add entries here when new variants are discovered; never add them
 * to STATE_BADGE_CLASS directly.
 */
const STATE_ALIASES: Record<string, string> = {
  PROCEED_TRAVERER_SAFE: 'PROCEED_TRAVELER_SAFE', // double-r typo (pre-hardening)
};

/**
 * Normalize a raw decision-state string to its canonical form.
 * Returns the original string if no alias matches, allowing the
 * badge-class unknown fallback to render visibly rather than silently.
 */
function normalizeDecisionState(raw: string): string {
  return STATE_ALIASES[raw] ?? raw;
}

const STATE_LABELS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE: "Ready to Book",
  PROCEED_INTERNAL_DRAFT: "Draft Quote",
  BRANCH_OPTIONS: "Needs Options",
  STOP_NEEDS_REVIEW: "Needs Attention",
  ASK_FOLLOWUP: "Need More Info",
};

const VERDICT_BADGE_CLASS: Record<string, string> = {
  realistic: styles.stateGreen,
  borderline: styles.stateAmber,
  not_realistic: styles.stateRed,
};

const VERDICT_LABELS: Record<string, string> = {
  realistic: "REALISTIC",
  borderline: "BORDERLINE",
  not_realistic: "NOT REALISTIC",
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

const CURRENCY_FORMATTERS: Record<string, (n: number) => string> = {
  INR: (n) => `₹${n.toLocaleString("en-IN")}`,
  USD: (n) => `$${n.toLocaleString("en-US")}`,
  EUR: (n) => `€${n.toLocaleString("de-DE")}`,
  GBP: (n) => `£${n.toLocaleString("en-GB")}`,
};

function formatCurrency(n: number, currency?: string): string {
  const formatter = CURRENCY_FORMATTERS[currency || "INR"] || CURRENCY_FORMATTERS.INR;
  return formatter(n);
}

interface DecisionTabProps {
  trip?: Trip | null;
}

export default function DecisionTab({ trip }: DecisionTabProps) {
  const { result_decision, result_fees, debug_raw_json, setDebugRawJson, acknowledged_suitability_flags, acknowledgeFlag } = useWorkbenchStore();

  const tripId = trip?.id;

  const handleAcknowledge = useCallback(async (flagType: string) => {
    acknowledgeFlag(flagType);
    if (tripId) {
      try { await acknowledgeSuitabilityFlags(tripId, [flagType]); } catch {}
    }
  }, [tripId, acknowledgeFlag]);

  const handleDrill = useCallback(() => {
    document.querySelector('[data-testid="timeline-panel"]')?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const activeDecision: DecisionOutput | null = result_decision || trip?.decision || null;

  if (!activeDecision) {
    return (
      <div className={styles.emptyState}>
        <p>No quote status data. Process a trip from the "New Inquiry" section first.</p>
      </div>
    );
  }

  const decision: DecisionOutput = activeDecision!;
  // Normalize state string before lookup - handles alias variants and makes
  // unknown states visible (fallback) rather than silently unstyled.
  const decisionState = normalizeDecisionState(
    (decision.decision_state as string) || 'ASK_FOLLOWUP',
  ) as DecisionState;
  const badgeClass = STATE_BADGE_CLASS[decisionState] ?? styles.stateBlue;

  const hardBlockers: string[] = (decision as any).hard_blockers ?? [];
  const softBlockers: string[] = (decision as any).soft_blockers ?? [];
  const contradictions: string[] = (decision as any).contradictions ?? [];
  const riskFlags: string[] = (decision as any).risk_flags ?? [];
  const suitabilityFlags: SuitabilityFlagData[] = (decision as any).suitability_flags ?? [];
  const followupQuestions: FollowUpQuestion[] = (decision as any).follow_up_questions ?? [];
  const rationale: Rationale = (decision as any).rationale ?? {};
  const branchOptions: string[] = (decision as any).branch_options ?? [];
  const budgetBreakdown: BudgetBreakdownResult | null = (decision as any).budget_breakdown ?? null;
  const budgetCurrency = budgetBreakdown?.currency as string | undefined;

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Decision State</h3>
        <div className={styles.card}>
          <span className={`${styles.badge} ${badgeClass}`}>
            {STATE_LABELS[decisionState] || "Review Required"}
          </span>
          <div style={{ marginTop: "12px", fontSize: "13px", color: "var(--color-text-muted)" }}>
            Overall Confidence: {Math.round((decision.confidence?.overall || 0) * 100)}%
          </div>
        </div>
      </div>

      {/* Rationale Section */}
      {rationale && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Rationale</h3>
          <div className={styles.card}>
            <div style={{ marginBottom: "8px" }}>
              <strong>Feasibility:</strong> {rationale.feasibility || "-"}
            </div>
            {rationale.confidence !== undefined && (
              <div style={{ marginBottom: "8px" }}>
                <strong>Confidence:</strong> {Math.round(rationale.confidence * 100)}%
              </div>
            )}
            {rationale.hard_blockers && rationale.hard_blockers.length > 0 && (
              <div style={{ marginBottom: "8px" }}>
                <strong style={{ color: "var(--color-danger)" }}>Hard Blockers:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {rationale.hard_blockers.map((b) => <li key={`hb-${b}`}>{b}</li>)}
                </ul>
              </div>
            )}
            {rationale.soft_blockers && rationale.soft_blockers.length > 0 && (
              <div>
                <strong style={{ color: "var(--color-warning)" }}>Soft Blockers:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {rationale.soft_blockers.map((b) => <li key={`sb-${b}`}>{b}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Branch Options */}
      {branchOptions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Branch Options</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {branchOptions.map((opt) => (
                <li key={`branch-${opt}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconInfo}`}>→</span>
                  {opt}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Hard Blockers */}
      {hardBlockers.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Hard Blockers</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {hardBlockers.map((item, i) => (
                <li key={`hard-${item}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Soft Blockers */}
      {softBlockers.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Soft Blockers</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {softBlockers.map((item, i) => (
                <li key={`soft-${item}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconWarning}`}>!</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Contradictions */}
      {contradictions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Contradictions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {contradictions.map((item, i) => (
                <li key={`contra-${item}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Risk Flags */}
      {riskFlags.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Risk Flags</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {riskFlags.map((item, i) => (
                <li key={`risk-${item}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconWarning}`}>!</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Suitability Audit Results */}
      {suitabilityFlags.length > 0 && (
        <SuitabilitySignal
          flags={suitabilityFlags}
          tripId={tripId}
          onAcknowledge={handleAcknowledge}
          onDrill={handleDrill}
          acknowledgedFlags={acknowledged_suitability_flags}
        />
      )}

      {/* Follow-up Questions */}
      {followupQuestions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Follow-up Questions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {followupQuestions.map((q) => (
                <li key={`followup-${q.field_name}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconInfo}`}>?</span>
                  <div>
                    <strong>[{q.priority.charAt(0).toUpperCase() + q.priority.slice(1)}] {titleCase(q.field_name)}</strong>
                    <p style={{ fontSize: "13px", marginTop: "4px" }}>{q.question}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Budget Breakdown */}
      {budgetBreakdown && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Budget Breakdown</h3>
          <div className={styles.card}>
            <div style={{ marginBottom: "12px", display: "flex", alignItems: "center", gap: "12px" }}>
              <span className={`${styles.badge} ${VERDICT_BADGE_CLASS[budgetBreakdown.verdict] || styles.stateBlue}`}>
                {VERDICT_LABELS[budgetBreakdown.verdict] || titleCase(budgetBreakdown.verdict)}
              </span>
              {budgetBreakdown.budget_stated != null && (
                <span style={{ fontSize: "13px", color: "var(--color-text-muted)" }}>
                  Budget: {formatCurrency(budgetBreakdown.budget_stated, budgetCurrency)} | Est. range: {formatCurrency(budgetBreakdown.total_estimated_low, budgetCurrency)} – {formatCurrency(budgetBreakdown.total_estimated_high, budgetCurrency)}
                </span>
              )}
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Bucket</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Low</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>High</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {budgetBreakdown.buckets.map((b: CostBucketEstimate) => (
                  <tr key={b.bucket} style={{ borderBottom: "1px solid var(--color-border)" }}>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{BUCKET_DISPLAY[b.bucket] || titleCase(b.bucket)}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{formatCurrency(b.low, budgetCurrency)}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{formatCurrency(b.high, budgetCurrency)}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>
                      <span className={`${styles.badge} ${b.covered ? styles.stateGreen : styles.stateRed}`}>
                        {b.covered ? "Covered" : "Gap"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {budgetBreakdown.missing_buckets.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong style={{ color: "var(--color-warning)" }}>Missing Buckets:</strong>{" "}
                {budgetBreakdown.missing_buckets.map((m: string) => BUCKET_DISPLAY[m] || m).join(", ")}
              </div>
            )}
            {budgetBreakdown.risks.length > 0 && (
              <ul className={styles.list} style={{ marginTop: "12px" }}>
                {budgetBreakdown.risks.map((r: string) => (
                  <li key={`br-${r}`} className={styles.listItem}>
                    <span className={`${styles.listIcon} ${styles.iconWarning}`}>!</span>
                    <span style={{ fontSize: "13px" }}>{titleCase(r)}</span>
                  </li>
                ))}
              </ul>
            )}
            {budgetBreakdown.critical_changes.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong>Critical Changes:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {budgetBreakdown.critical_changes.map((c: string) => (
                    <li key={`cc-${c.slice(0, 30)}`}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
            {budgetBreakdown.must_confirm.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong>Must Confirm:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px", color: "var(--color-text-muted)" }}>
                  {budgetBreakdown.must_confirm.map((m: string) => (
                    <li key={`mc-${m.slice(0, 30)}`}>{titleCase(m)}</li>
                  ))}
                </ul>
              </div>
            )}
            {budgetBreakdown.alternative && (
              <div style={{ marginTop: "12px", padding: "8px 12px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "6px", fontSize: "13px" }}>
                <strong>Alternative:</strong> {budgetBreakdown.alternative}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Fee Breakdown */}
      {result_fees && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Fee Breakdown</h3>
          <div className={styles.card}>
            <div style={{ marginBottom: "12px", display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "13px", color: "var(--color-text-muted)" }}>
                {String(result_fees.risk_summary ?? "")}
              </span>
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Service</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Base Fee</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Multiplier</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Adjusted Fee</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result_fees.service_breakdowns).map((entry) => {
                  const [service, breakdown] = entry;
                  return (
                  <tr key={service} style={{ borderBottom: "1px solid var(--color-border)" }}>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{titleCase(service)}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{formatCurrency(breakdown.base_fee, "USD")}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{breakdown.multiplier}x</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{formatCurrency(breakdown.adjusted_fee, "USD")}</td>
                  </tr>
                );
              })}
                <tr style={{ borderTop: "2px solid var(--color-border)", fontWeight: "bold" }}>
                  <td style={{ padding: "8px", fontSize: "13px" }}>Total</td>
                  <td style={{ padding: "8px", fontSize: "13px" }}>{formatCurrency(result_fees.total_base_fee, "USD")}</td>
                  <td style={{ padding: "8px", fontSize: "13px" }}>-</td>
                  <td style={{ padding: "8px", fontSize: "13px" }}>{formatCurrency(result_fees.total_adjusted_fee, "USD")}</td>
                </tr>
              </tbody>
            </table>
            {(result_fees.fee_adjustment !== 0) && (
              <div style={{ marginTop: "12px", fontSize: "13px", color: result_fees.fee_adjustment > 0 ? "var(--color-warning)" : "var(--color-success)" }}>
                <strong>Adjustment:</strong> {formatCurrency(result_fees.fee_adjustment, "USD")} ({result_fees.fee_adjustment > 0 ? "risk premium" : "discount"})
              </div>
            )}
          </div>
        </div>
      )}

      <button
        type="button"
        className={styles.jsonToggle}
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>

      {debug_raw_json && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify(decision, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}