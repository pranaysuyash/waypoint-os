"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import styles from "./workbench.module.css";

export function SafetyTab() {
  const {
    result_leakage,
    result_assertions,
    result_traveler_bundle,
    result_internal_bundle,
    strict_leakage,
  } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);

  if (!result_leakage) {
    return (
      <div className={styles.emptyState}>
        <p>No safety data. Run Spine from the Intake tab first.</p>
      </div>
    );
  }

  const leakage = result_leakage as unknown as { ok: boolean; items: string[] };
  const travelerBundle = result_traveler_bundle as Record<string, unknown> | null;
  const internalBundle = result_internal_bundle as Record<string, unknown> | null;
  const assertions = result_assertions as Array<{ type: string; message: string; pass?: boolean }> | null;

  const strippedFields = leakage.items || [];
  const isStrictFail = strict_leakage && !leakage.ok;

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Leakage Status</h3>
        {leakage.ok ? (
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

      {isStrictFail && (
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
                <li key={`leak-${i}-${item.slice(0, 15)}`} className={styles.listItem}>
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
          {travelerBundle && typeof travelerBundle === 'object' ? (
            <div>
              {(travelerBundle as { message?: unknown }).message ? (
                <div style={{ marginBottom: "12px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Message</strong>
                  <p style={{ lineHeight: 1.6, marginTop: "4px" }}>{String((travelerBundle as { message?: unknown }).message)}</p>
                </div>
              ) : null}
              {(travelerBundle as { itinerary?: unknown }).itinerary ? (
                <div>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Itinerary</strong>
                  <pre className={styles.jsonOutput} style={{ marginTop: "8px" }}>
                    {JSON.stringify((travelerBundle as { itinerary?: unknown }).itinerary, null, 2)}
                  </pre>
                </div>
              ) : null}
            </div>
          ) : (
            <p style={{ color: "var(--color-text-muted)" }}>
              {isStrictFail ? "Invalidated due to strict mode failure" : "No traveler bundle available"}
            </p>
          )}
        </div>
      </div>

      {assertions && assertions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Assertion Results</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {assertions.map((assertion, i) => {
                const passed = assertion.pass !== false;
                return (
                  <li key={`assertion-${i}-${assertion.type}`} className={styles.listItem}>
                    <span className={`${styles.listIcon} ${passed ? styles.iconSuccess : styles.iconDanger}`}>
                      {passed ? "✓" : "X"}
                    </span>
                    <div>
                      <strong>{assertion.type}</strong>
                      <p style={{ fontSize: "12px", color: "var(--color-text-muted)", margin: "2px 0 0 0" }}>
                        {assertion.message}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      )}

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
            leakage: result_leakage,
            assertions: result_assertions,
            traveler_bundle: result_traveler_bundle,
            internal_bundle: result_internal_bundle,
          }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
