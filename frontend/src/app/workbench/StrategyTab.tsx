"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { StrategyOutput, PromptBundle } from "@/types/spine";
import styles from "./workbench.module.css";

export function StrategyTab() {
  const { result_strategy, result_internal_bundle, result_traveler_bundle, debug_raw_json } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);
  const effectiveShowRaw = debug_raw_json || showRaw;

  if (!result_strategy) {
    return (
      <div className={styles.emptyState}>
        <p>No options data. Process a trip from the "New Inquiry" section first.</p>
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
        <h3 className={styles.sectionTitle}>Agent View vs Customer View</h3>
        <div className={styles.splitView}>
          {/* Internal Bundle */}
          <div className={`${styles.splitPanel} ${styles.internalPanel}`}>
            <div className={styles.splitTitle}>For You (Agent)</div>
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
              <p style={{ color: "var(--color-text-muted)" }}>No agent notes</p>
            )}
          </div>

          {/* Traveler-safe Bundle */}
          <div className={`${styles.splitPanel} ${styles.travelerPanel}`}>
            <div className={styles.splitTitle}>For Customer</div>
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
              <p style={{ color: "var(--color-text-muted)" }}>No customer message</p>
            )}
          </div>
        </div>
      </div>

      <button
        type="button"
        className={styles.jsonToggle}
        onClick={() => setShowRaw(!effectiveShowRaw)}
      >
        {effectiveShowRaw ? "Hide" : "Show"} Technical Data
      </button>

      {effectiveShowRaw && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify({ strategy, internal_bundle: internalBundle, traveler_bundle: travelerBundle }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}