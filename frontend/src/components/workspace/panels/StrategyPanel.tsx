"use client";

import { useWorkbenchStore } from "@/stores/workbench";
import type { StrategyOutput } from "@/types/spine";
import styles from "@/app/workbench/workbench.module.css";

interface StrategyPanelProps {
  tripId: string;
}

export function StrategyPanel({ tripId }: StrategyPanelProps) {
  const { result_strategy, debug_raw_json, setDebugRawJson } = useWorkbenchStore();

  if (!result_strategy) {
    return (
      <div className={styles.emptyState}>
        <p>No options data for trip {tripId}. Process a trip from the "New Inquiry" section first.</p>
      </div>
    );
  }

  const strategy = result_strategy as StrategyOutput;

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

      <button
        type="button"
        className={styles.jsonToggle}
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>

      {debug_raw_json && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify({ strategy }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
