"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { DecisionState, BudgetBreakdownResult, CostBucketEstimate } from "@/types/spine";
import styles from "./workbench.module.css";

const STATE_BADGE_CLASS: Record<string, string> = {
  PROCEED_TRAVERER_SAFE: styles.stateGreen,
  PROCEED_TRAVELER_SAFE: styles.stateGreen,
  PROCEED_INTERNAL_DRAFT: styles.stateAmber,
  BRANCH_OPTIONS: styles.stateAmber,
  STOP_NEEDS_REVIEW: styles.stateRed,
  ASK_FOLLOWUP: styles.stateBlue,
};

const STATE_LABELS: Record<string, string> = {
  PROCEED_TRAVELER_SAFE: "PROCEED — TRAVELER SAFE",
  PROCEED_INTERNAL_DRAFT: "PROCEED — INTERNAL DRAFT",
  BRANCH_OPTIONS: "BRANCH OPTIONS",
  STOP_NEEDS_REVIEW: "STOP — NEEDS REVIEW",
  ASK_FOLLOWUP: "ASK FOLLOWUP",
};

interface FollowUpQuestion {
  field_name: string;
  question: string;
  priority: string;
  suggested_values: unknown[];
}

interface Rationale {
  hard_blockers: string[];
  soft_blockers: string[];
  contradictions: string[];
  confidence: number;
  feasibility: string;
}

interface DecisionOutput {
  decision_state: string;
  hard_blockers: string[];
  soft_blockers: string[];
  contradictions: string[];
  risk_flags: string[];
  follow_up_questions: FollowUpQuestion[];
  rationale: Rationale;
  confidence_score: number;
  branch_options: string[];
  commercial_decision: string;
  budget_breakdown: BudgetBreakdownResult | null;
}

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

function formatINR(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

export function DecisionTab() {
  const { result_decision } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);

  if (!result_decision) {
    return (
      <div className={styles.emptyState}>
        <p>No decision data. Run Spine from the Intake tab first.</p>
      </div>
    );
  }

  const decision = result_decision as DecisionOutput;
  const decisionState = (decision.decision_state as DecisionState) || "ASK_FOLLOWUP";

  const hardBlockers = decision.hard_blockers || [];
  const softBlockers = decision.soft_blockers || [];
  const contradictions = decision.contradictions || [];
  const riskFlags = decision.risk_flags || [];
  const followupQuestions = decision.follow_up_questions || [];
  const rationale = decision.rationale || {};
  const branchOptions = decision.branch_options || [];
  const budgetBreakdown = decision.budget_breakdown || null;

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Decision State</h3>
        <div className={styles.card}>
          <span className={`${styles.badge} ${STATE_BADGE_CLASS[decisionState] || styles.stateBlue}`}>
            {STATE_LABELS[decisionState] || decisionState}
          </span>
          <div style={{ marginTop: "12px", fontSize: "13px", color: "var(--color-text-muted)" }}>
            Confidence: {Math.round((decision.confidence_score || 0) * 100)}%
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
                  Budget: {formatINR(budgetBreakdown.budget_stated)} | Est. range: {formatINR(budgetBreakdown.total_estimated_low)} – {formatINR(budgetBreakdown.total_estimated_high)}
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
                    <td style={{ padding: "8px", fontSize: "13px" }}>{formatINR(b.low)}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{formatINR(b.high)}</td>
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
                    <span style={{ fontSize: "13px" }}>{r.replace(/_/g, " ")}</span>
                  </li>
                ))}
              </ul>
            )}
            {budgetBreakdown.critical_changes.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong>Critical Changes:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {budgetBreakdown.critical_changes.map((c: string, i: number) => (
                    <li key={`cc-${i}`}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
            {budgetBreakdown.must_confirm.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong>Must Confirm:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px", color: "var(--color-text-muted)" }}>
                  {budgetBreakdown.must_confirm.map((m: string, i: number) => (
                    <li key={`mc-${i}`}>{m.replace(/_/g, " ")}</li>
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

      <button
        type="button"
        className={styles.jsonToggle}
        onClick={() => setShowRaw(!showRaw)}
      >
        {showRaw ? "Hide" : "Show"} Raw JSON
      </button>

      {showRaw && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify(decision, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}