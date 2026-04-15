"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import styles from "./workbench.module.css";

export function StrategyTab() {
  const { result_strategy, result_internal_bundle } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);

  if (!result_strategy) {
    return (
      <div className={styles.emptyState}>
        <p>No strategy data. Run Spine from the Intake tab first.</p>
      </div>
    );
  }

  const strategy = result_strategy as Record<string, unknown>;
  const internalBundle = result_internal_bundle as Record<string, unknown> | null;

  const sessionGoal = (strategy.session_goal as string) || "";
  const suggestedOpening = (strategy.suggested_opening as string) || "";
  const prioritySequence = (strategy.priority_sequence as string[]) || [];
  const toneIndicator = (strategy.tone_indicator as string) || "";
  const internalNotes = (strategy.internal_notes as string) || "";
  const constraints = (strategy.constraints as string[]) || [];

  const travelerSafe = internalBundle?.traveler_safe || "";

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Session Goal</h3>
        <div className={styles.card}>
          <p>{sessionGoal || "—"}</p>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Suggested Opening</h3>
        <div className={styles.card}>
          <p>{suggestedOpening || "—"}</p>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Priority Sequence</h3>
        <div className={styles.card}>
          {prioritySequence.length > 0 ? (
            <ol style={{ paddingLeft: "20px", margin: "0" }}>
              {prioritySequence.map((item, i) => (
                <li key={`priority-${item.slice(0, 15)}-${i}`} style={{ padding: "6px 0" }}>
                  {item}
                </li>
              ))}
            </ol>
          ) : (
            <p>—</p>
          )}
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Tone Indicator</h3>
        <div className={styles.card}>
          <span className={styles.badge} style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}>
            {toneIndicator || "—"}
          </span>
        </div>
      </div>

      <div className={styles.splitView}>
        <div className={`${styles.splitPanel} ${styles.internalPanel}`}>
          <h4 className={styles.splitTitle}>Internal View</h4>
          {internalNotes && (
            <div style={{ marginBottom: "16px" }}>
              <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Internal Notes</strong>
              <p style={{ lineHeight: 1.6 }}>{internalNotes}</p>
            </div>
          )}
          {constraints.length > 0 && (
            <div>
              <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Constraints</strong>
              <ul className={styles.list}>
                {constraints.map((item, i) => (
                  <li key={`constraint-${item.slice(0, 15)}-${i}`} className={styles.listItem}>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {!internalNotes && constraints.length === 0 && (
            <p style={{ color: "var(--color-text-muted)" }}>No internal notes</p>
          )}
        </div>

        <div className={`${styles.splitPanel} ${styles.travelerPanel}`}>
          <h4 className={styles.splitTitle}>Traveler-Safe View</h4>
          {travelerSafe ? (
            <p style={{ lineHeight: 1.6 }}>{String(travelerSafe)}</p>
          ) : (
            <p style={{ color: "var(--color-text-muted)" }}>No traveler-safe content</p>
          )}
        </div>
      </div>

      <button
        type="button"
        className={styles.jsonToggle}
        onClick={() => setShowRaw(!showRaw)}
        style={{ marginTop: "20px" }}
      >
        {showRaw ? "Hide" : "Show"} Raw JSON
      </button>

      {showRaw && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify({ strategy, internal_bundle: internalBundle }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
