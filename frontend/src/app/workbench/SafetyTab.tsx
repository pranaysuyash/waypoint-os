"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { SafetyResult } from "@/types/spine";
import styles from "./workbench.module.css";

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

export function SafetyTab() {
  const {
    result_safety,
    result_traveler_bundle,
    result_internal_bundle,
  } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);

  if (!result_safety) {
    return (
      <div className={styles.emptyState}>
        <p>No safety data. Run Spine from the Intake tab first.</p>
      </div>
    );
  }

  const safety = result_safety as SafetyResult;
  const travelerBundle = result_traveler_bundle as PromptBundle | null;
  const internalBundle = result_internal_bundle as PromptBundle | null;

  const strippedFields = safety.leakage_errors || [];
  const isStrictFail = safety.strict_leakage && !safety.leakage_passed;

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Leakage Status</h3>
        {safety.leakage_passed ? (
          <div className={styles.leakagePass}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconSuccess}`} style={{ marginRight: "8px" }}>✓</span>
              PASS - No Leakage Detected
            </div>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              All internal terms have been properly sanitized for traveler-safe output.
            </p>
          </div>
        ) : (
          <div className={styles.leakageFail}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconDanger}`} style={{ marginRight: "8px" }}>✗</span>
              FAIL - Leakage Detected
            </div>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              Internal terms were found in the traveler-facing output.
            </p>
          </div>
        )}
      </div>

      {safety.strict_leakage && !safety.leakage_passed && (
        <div className={styles.leakageFail} style={{ border: "2px solid rgba(239, 68, 68, 0.5)", marginBottom: "16px" }}>
          <div className={styles.leakageTitle} style={{ color: "var(--color-danger)", fontWeight: 700 }}>
            STRICT MODE FAILURE
          </div>
          <p style={{ fontSize: "13px", margin: "8px 0 0 0" }}>
            Leakage detected with strict mode enabled. Traveler bundle is invalidated.
          </p>
        </div>
      )}

      {strippedFields.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Stripped Fields / Terms</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {strippedFields.map((item, i) => (
                <li key={`leak-${item.slice(0, 15)}-${i}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Traveler-Safe Bundle</h3>
        <div className={styles.card}>
          {travelerBundle && !isStrictFail ? (
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
                  <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                    {travelerBundle.follow_up_sequence.map((f, i) => (
                      <li key={`fseq-${f.field_name}-${i}`} style={{ marginBottom: "4px" }}>
                        <strong>[{f.priority}]</strong> {f.question}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {travelerBundle.constraints && travelerBundle.constraints.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Constraints</strong>
                  <ul style={{ margin: "4px 0 0 16px", fontSize: "12px" }}>
                    {travelerBundle.constraints.map((c, i) => (
                      <li key={`iconst-${c.slice(0, 20)}-${i}`}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: "var(--color-text-muted)" }}>
              {isStrictFail ? "Invalidated due to strict mode failure" : "No traveler bundle available"}
            </p>
          )}
        </div>
      </div>

      {internalBundle && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Internal Bundle (Reference)</h3>
          <div className={styles.card}>
            <pre className={styles.jsonOutput}>
              {JSON.stringify(internalBundle, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <button
        type="button"
        className={styles.jsonToggle}
        onClick={() => setShowRaw(!showRaw)}
      >
        {showRaw ? "Hide" : "Show"} Full Raw Data
      </button>

      {showRaw && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify({
            safety: result_safety,
            traveler_bundle: result_traveler_bundle,
            internal_bundle: result_internal_bundle,
          }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}