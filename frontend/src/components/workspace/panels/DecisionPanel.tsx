"use client";

import { useWorkbenchStore } from "@/stores/workbench";
import { useTripContext } from "@/contexts/TripContext";
import type { DecisionState, BudgetBreakdownResult, CostBucketEstimate, DecisionOutput } from "@/types/spine";
import styles from "@/app/workbench/workbench.module.css";

interface DecisionPanelProps {
  trip?: any;
  tripId?: string;
}

/**
 * Canonical badge-class lookup.
 */
const STATE_BADGE_CLASS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE:   styles.stateGreen,
  PROCEED_INTERNAL_DRAFT:  styles.stateAmber,
  BRANCH_OPTIONS:          styles.stateAmber,
  STOP_REVIEW:             styles.stateRed,
  STOP_NEEDS_REVIEW:       styles.stateRed,
  ASK_FOLLOWUP:            styles.stateBlue,
};

/**
 * Known typo/alias variants.
 */
const STATE_ALIASES: Record<string, string> = {
  PROCEED_TRAVERER_SAFE: 'PROCEED_TRAVELER_SAFE',
};

function normalizeDecisionState(raw: string): string {
  return STATE_ALIASES[raw] ?? raw;
}

const STATE_LABELS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE: "Ready to Book",
  PROCEED_INTERNAL_DRAFT: "Draft Quote",
  BRANCH_OPTIONS: "Needs Options",
  STOP_NEEDS_REVIEW: "Needs Attention",
  STOP_REVIEW: "Needs Attention",
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
      <div className={styles.emptyState}>
        <p>No quote status data for trip {tripId || "unknown"}. Process a trip from the "Packet" section first.</p>
      </div>
    );
  }

  const decisionState = normalizeDecisionState(
    (decision.decision_state as string) || 'ASK_FOLLOWUP',
  ) as DecisionState;
  const badgeClass = STATE_BADGE_CLASS[decisionState] ?? styles.stateBlue;

  const hardBlockers = decision.hard_blockers || [];
  const softBlockers = decision.soft_blockers || [];
  const contradictions = decision.contradictions || [];
  const riskFlags = decision.risk_flags || [];
  const followupQuestions = decision.follow_up_questions || [];
  const rationale = decision.rationale || {};
  
  const reviewStatus = trip?.review_status;
  const reviewMetadata = trip?.review_metadata;
  const branchOptions = decision.branch_options || [];
  const budgetBreakdown = decision.budget_breakdown || null;
  const budgetCurrency = budgetBreakdown?.currency as string | undefined;

  return (
    <div>
      {reviewStatus && (
        <div className={styles.reviewStatusBanner}>
          <div className={styles.reviewInfo}>
            <strong className="text-sm">Latest Review Status: {reviewStatus.toUpperCase()}</strong>
            {reviewMetadata?.reviewedBy && <span className="text-xs text-[#8b949e]">checked by {reviewMetadata.reviewedBy}</span>}
          </div>
          {reviewMetadata?.notes && (
            <div className={styles.reviewNotes}>
              <em>"{reviewMetadata.notes}"</em>
            </div>
          )}
        </div>
      )}

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Decision State</h3>
        <div className={styles.card}>
          <span className={`${styles.badge} ${badgeClass}`}>
            {STATE_LABELS[decisionState] || decisionState}
          </span>
          <div style={{ marginTop: "12px", fontSize: "13px", color: "var(--color-text-muted)" }}>
            Overall Confidence: {Math.round((decision.confidence?.overall || 0) * 100)}%
          </div>
          <div style={{ marginTop: "12px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px", fontSize: "11px" }}>
            <div style={{ padding: "4px", background: "rgba(0,0,0,0.03)", borderRadius: "4px", textAlign: "center" }}>
              <div style={{ color: "var(--color-text-muted)", marginBottom: "2px" }}>Data</div>
              <strong>{Math.round((decision.confidence?.data_quality || 0) * 100)}%</strong>
            </div>
            <div style={{ padding: "4px", background: "rgba(0,0,0,0.03)", borderRadius: "4px", textAlign: "center" }}>
              <div style={{ color: "var(--color-text-muted)", marginBottom: "2px" }}>Judgment</div>
              <strong>{Math.round((decision.confidence?.judgment_confidence || 0) * 100)}%</strong>
            </div>
            <div style={{ padding: "4px", background: "rgba(0,0,0,0.03)", borderRadius: "4px", textAlign: "center" }}>
              <div style={{ color: "var(--color-text-muted)", marginBottom: "2px" }}>Comm.</div>
              <strong>{Math.round((decision.confidence?.commercial_confidence || 0) * 100)}%</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Rationale Section */}
      {rationale && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Rationale</h3>
          <div className={styles.card}>
            <div style={{ marginBottom: "8px" }}>
              <strong>Feasibility:</strong> {rationale.feasibility || "—"}
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
                  {rationale.hard_blockers.map((b, i) => <li key={`hb-${b}-${i}`}>{b}</li>)}
                </ul>
              </div>
            )}
            {rationale.soft_blockers && rationale.soft_blockers.length > 0 && (
              <div>
                <strong style={{ color: "var(--color-warning)" }}>Soft Blockers:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {rationale.soft_blockers.map((b, i) => <li key={`sb-${b}-${i}`}>{b}</li>)}
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
              {branchOptions.map((opt, i) => (
                <li key={`branch-${opt}-${i}`} className={styles.listItem}>
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

      {/* Follow-up Questions */}
      {followupQuestions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Follow-up Questions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {followupQuestions.map((q, i) => (
                <li key={`followup-${q.field_name}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconInfo}`}>?</span>
                  <div>
                    <strong>[{q.priority}] {q.field_name}</strong>
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
                {VERDICT_LABELS[budgetBreakdown.verdict] || budgetBreakdown.verdict}
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
                    <td style={{ padding: "8px", fontSize: "13px" }}>{BUCKET_DISPLAY[b.bucket] || b.bucket}</td>
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
