import { useWorkbenchStore } from "@/stores/workbench";
import type { StrategyOutput, PromptBundle } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import styles from "@/components/workbench/workbench.module.css";

interface StrategyTabProps {
  trip?: Trip | null;
}

export default function StrategyTab({ trip }: StrategyTabProps) {
  const { result_strategy, result_internal_bundle, result_traveler_bundle, debug_raw_json, setDebugRawJson } = useWorkbenchStore();

  const activeStrategy = result_strategy || (trip?.strategy as StrategyOutput | null);
  const activeInternalBundle = result_internal_bundle || (trip?.internal_bundle as PromptBundle | null);
  const activeTravelerBundle = result_traveler_bundle || (trip?.traveler_bundle as PromptBundle | null);

  if (!activeStrategy) {
    return (
      <div className={styles.emptyState}>
        <p>Ready to build trip options. Run AI to generate.</p>
      </div>
    );
  }

  const strategy = activeStrategy;
  const internalBundle = activeInternalBundle;
  const travelerBundle = activeTravelerBundle;

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Session Goal</h3>
        <div className={styles.card}>
          <p>{strategy.session_goal || "-"}</p>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Suggested Opening</h3>
        <div className={styles.card}>
          <p>&ldquo;{strategy.suggested_opening || "-"}&rdquo;</p>
        </div>
      </div>

      {strategy.priority_sequence && strategy.priority_sequence.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Priority Sequence</h3>
          <div className={styles.card}>
            <ol style={{ margin: "0 0 0 20px", padding: 0 }}>
              {strategy.priority_sequence.map((item, i) => (
                <li key={`priority-${item.slice(0, 30)}`} style={{ padding: "4px 0" }}>{item}</li>
              ))}
            </ol>
          </div>
        </div>
      )}

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Tone: {strategy.suggested_tone || "-"}</h3>
        {strategy.tonal_guardrails && strategy.tonal_guardrails.length > 0 && (
          <div className={styles.card}>
            <ul className={styles.list}>
              {strategy.tonal_guardrails.map((guardrail, i) => (
                <li key={`guard-${guardrail.slice(0, 30)}`} className={styles.listItem}>
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
                <li key={`assume-${assumption.slice(0, 30)}`} className={styles.listItem}>
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
          <pre>{JSON.stringify({ strategy, internal_bundle: internalBundle, traveler_bundle: travelerBundle }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
