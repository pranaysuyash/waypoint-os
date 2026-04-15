"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { DecisionState } from "@/types/spine";
import styles from "./workbench.module.css";

const STATE_BADGE_CLASS: Record<DecisionState, string> = {
  PROCEED_TRAVELER_SAFE: styles.stateGreen,
  PROCEED_INTERNAL_DRAFT: styles.stateAmber,
  BRANCH_OPTIONS: styles.stateAmber,
  STOP_NEEDS_REVIEW: styles.stateRed,
  ASK_FOLLOWUP: styles.stateBlue,
};

const STATE_LABELS: Record<DecisionState, string> = {
  PROCEED_TRAVELER_SAFE: "PROCEED - TRAVELER SAFE",
  PROCEED_INTERNAL_DRAFT: "PROCEED - INTERNAL DRAFT",
  BRANCH_OPTIONS: "BRANCH OPTIONS",
  STOP_NEEDS_REVIEW: "STOP - NEEDS REVIEW",
  ASK_FOLLOWUP: "ASK FOLLOWUP",
};

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

  const decision = result_decision as Record<string, unknown>;
  const decisionState = (decision.decision_state as DecisionState) || "ASK_FOLLOWUP";

  const hardBlockers = (decision.hard_blockers as string[]) || [];
  const softBlockers = (decision.soft_blockers as string[]) || [];
  const contradictions = (decision.contradictions as string[]) || [];
  const riskFlags = (decision.risk_flags as string[]) || [];
  const followupQuestions = (decision.followup_questions as string[]) || [];
  const rationale = (decision.rationale as string) || "";

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Decision State</h3>
        <div className={styles.card}>
          <span className={`${styles.badge} ${STATE_BADGE_CLASS[decisionState]}`}>
            {STATE_LABELS[decisionState]}
          </span>
        </div>
      </div>

      {hardBlockers.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Hard Blockers</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {hardBlockers.map((item, i) => (
                <li key={`hard-blocker-${item.slice(0, 20)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {softBlockers.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Soft Blockers</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {softBlockers.map((item, i) => (
                <li key={`soft-blocker-${item.slice(0, 20)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconWarning}`}>!</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {contradictions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Contradictions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {contradictions.map((item, i) => (
                <li key={`contradiction-${item.slice(0, 20)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {riskFlags.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Risk Flags</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {riskFlags.map((item, i) => (
                <li key={`risk-flag-${item.slice(0, 20)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconWarning}`}>!</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {followupQuestions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Follow-up Questions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {followupQuestions.map((item, i) => (
                <li key={`followup-${item.slice(0, 20)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconInfo}`}>?</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {rationale && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Rationale</h3>
          <div className={styles.card}>
            <p style={{ lineHeight: 1.6 }}>{rationale}</p>
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
