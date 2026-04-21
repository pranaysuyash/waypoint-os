"use client";

import { useWorkbenchStore } from "@/stores/workbench";
import type { PromptBundle } from "@/types/spine";
import styles from "@/app/workbench/workbench.module.css";

interface OutputPanelProps {
  tripId: string;
}

export function OutputPanel({ tripId }: OutputPanelProps) {
  const { result_internal_bundle, result_traveler_bundle, debug_raw_json, setDebugRawJson } = useWorkbenchStore();

  if (!result_internal_bundle && !result_traveler_bundle) {
    return (
      <div className={styles.emptyState}>
        <p>No output data for trip {tripId}. Process a trip from the "New Inquiry" section first to generate response bundles.</p>
      </div>
    );
  }

  const internalBundle = result_internal_bundle as PromptBundle | null;
  const travelerBundle = result_traveler_bundle as PromptBundle | null;

  return (
    <div>
      {/* Internal vs Traveler-safe Split View */}
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Agent View vs Customer View</h3>
        <div className={styles.splitView}>
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
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>

      {debug_raw_json && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify({ internal_bundle: internalBundle, traveler_bundle: travelerBundle }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
