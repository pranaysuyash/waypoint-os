"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { SafetyResult, PromptBundle } from "@/types/spine";
import styles from "@/app/workbench/workbench.module.css";

interface SafetyPanelProps {
  tripId: string;
}

export function SafetyPanel({ tripId }: SafetyPanelProps) {
  const {
    result_safety,
    result_traveler_bundle,
    result_internal_bundle,
    debug_raw_json,
  } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);
  const effectiveShowRaw = debug_raw_json || showRaw;

  if (!result_safety) {
    return (
      <div className={styles.emptyState}>
        <p>No review data for trip {tripId}. Process a trip from the "New Inquiry" section first.</p>
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
        <h3 className={styles.sectionTitle}>Content Review</h3>
        {safety.leakage_passed ? (
          <div className={styles.leakagePass}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconSuccess}`} style={{ marginRight: "8px" }}>✓</span>
              PASS — Safe for Customer
            </div>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              No internal jargon or sensitive details found in the customer-facing message.
            </p>
          </div>
        ) : (
          <div className={styles.leakageFail}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconDanger}`} style={{ marginRight: "8px" }}>✗</span>
              FAIL — Internal Jargon Found
            </div>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              Internal-only terms were found in the message the customer would see.
            </p>
          </div>
        )}
      </div>

      {safety.strict_leakage && !safety.leakage_passed && (
        <div className={styles.leakageFail} style={{ border: "2px solid rgba(239, 68, 68, 0.5)", marginBottom: "16px" }}>
          <div className={styles.leakageTitle} style={{ color: "var(--color-danger)", fontWeight: 700 }}>
            NOT SAFE TO SEND
          </div>
          <p style={{ fontSize: "13px", margin: "8px 0 0 0" }}>
            Customer message contains internal jargon and cannot be sent until fixed.
          </p>
        </div>
      )}

      {strippedFields.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Jargon Found in Customer Message</h3>
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
        <h3 className={styles.sectionTitle}>Customer-Facing Message</h3>
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
            </div>
          ) : (
            <p style={{ color: "var(--color-text-muted)" }}>
              {isStrictFail ? "Cannot be sent — contains internal jargon" : "No customer message available"}
            </p>
          )}
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
