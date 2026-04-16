"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import styles from "./workbench.module.css";

interface StrategyOutput {
  session_goal: string;
  priority_sequence: string[];
  tonal_guardrails: string[];
  risk_flags: string[];
  suggested_opening: string;
  exit_criteria: string[];
  next_action: string;
  assumptions: string[];
  suggested_tone: string;
}

interface PromptBundle {
  system_context: string;
  user_message: string;
  follow_up_sequence: Array<{
    field_name: string;
    question: string;
    priority: string;
  }>;
  branch_prompts: unknown[];
  internal_notes: string;
  constraints: string[];
  audience: string;
}

export function StrategyTab() {
  const { result_strategy, result_internal_bundle, result_traveler_bundle } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);

  if (!result_strategy) {
    return (
      <div className={styles.emptyState}>
        <p>No options data. Process a trip from the New Inquiry tab first.</p>
      </div>
    );
  }

  const strategy = result_strategy as StrategyOutput;
  const internalBundle = result_internal_bundle as PromptBundle | null;
  const travelerBundle = result_traveler_bundle as PromptBundle | null;

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Session Goal</h3>
        <div className={styles.card}>
          <p>{strategy.session_goal || "—"}</p>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Suggested Opening</h3>
        <div className={styles.card}>
          <p>"{strategy.suggested_opening || "—"}"</p>
        </div>
      </div>

      {strategy.priority_sequence && strategy.priority_sequence.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Priority Sequence</h3>
          <div className={styles.card}>
            <ol style={{ margin: "0 0 0 20px", padding: 0 }}>
              {strategy.priority_sequence.map((item, i) => (
                <li key={`priority-${item.slice(0, 20)}-${i}`} style={{ padding: "4px 0" }}>{item}</li>
              ))}
            </ol>
          </div>
        </div>
      )}

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Tone: {strategy.suggested_tone || "—"}</h3>
        {strategy.tonal_guardrails && strategy.tonal_guardrails.length > 0 && (
          <div className={styles.card}>
            <ul className={styles.list}>
              {strategy.tonal_guardrails.map((guardrail, i) => (
                <li key={`guard-${guardrail.slice(0, 20)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconInfo}`}>•</span>
                  {guardrail}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {strategy.assumptions && strategy.assumptions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Assumptions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {strategy.assumptions.map((assumption, i) => (
                <li key={`assume-${assumption.slice(0, 20)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconWarning}`}>?</span>
                  {assumption}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Internal vs Traveler-safe Split View */}
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Internal vs Traveler-Safe</h3>
        <div className={styles.splitView}>
          {/* Internal Bundle */}
          <div className={`${styles.splitPanel} ${styles.internalPanel}`}>
            <div className={styles.splitTitle}>Internal Agent View</div>
            {internalBundle ? (
              <div>
                <div style={{ marginBottom: "12px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>System Context</strong>
                  <p style={{ fontSize: "13px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                    {internalBundle.system_context || "—"}
                  </p>
                </div>
                <div style={{ marginBottom: "12px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>User Message</strong>
                  <p style={{ fontSize: "13px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                    {internalBundle.user_message || "—"}
                  </p>
                </div>
                {internalBundle.constraints && internalBundle.constraints.length > 0 && (
                  <div>
                    <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Constraints</strong>
                    <ul style={{ margin: "4px 0 0 16px", fontSize: "12px" }}>
                      {internalBundle.constraints.map((c, i) => (
                        <li key={`icon-${c.slice(0, 20)}-${i}`}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {internalBundle.internal_notes && (
                  <div style={{ marginTop: "12px" }}>
                    <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Internal Notes</strong>
                    <p style={{ fontSize: "13px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                      {internalBundle.internal_notes}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: "var(--color-text-muted)" }}>No internal bundle</p>
            )}
          </div>

          {/* Traveler-safe Bundle */}
          <div className={`${styles.splitPanel} ${styles.travelerPanel}`}>
            <div className={styles.splitTitle}>Traveler-Safe View</div>
            {travelerBundle ? (
              <div>
                <div style={{ marginBottom: "12px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>System Context</strong>
                  <p style={{ fontSize: "13px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                    {travelerBundle.system_context || "—"}
                  </p>
                </div>
                <div style={{ marginBottom: "12px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>User Message</strong>
                  <p style={{ fontSize: "13px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                    {travelerBundle.user_message || "—"}
                  </p>
                </div>
                {travelerBundle.follow_up_sequence && travelerBundle.follow_up_sequence.length > 0 && (
                  <div>
                    <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Follow-up Sequence</strong>
                    <ul style={{ margin: "4px 0 0 16px", fontSize: "12px" }}>
                      {travelerBundle.follow_up_sequence.map((f, i) => (
                        <li key={`fseq-${f.field_name}-${i}`}>{f.question}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: "var(--color-text-muted)" }}>No traveler bundle</p>
            )}
          </div>
        </div>
      </div>

      <button
        type="button"
        className={styles.jsonToggle}
        onClick={() => setShowRaw(!showRaw)}
      >
        {showRaw ? "Hide" : "Show"} Raw JSON
      </button>

      {showRaw && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify({ strategy, internal_bundle: internalBundle, traveler_bundle: travelerBundle }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}