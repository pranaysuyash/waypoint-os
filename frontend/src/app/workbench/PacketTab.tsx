"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import styles from "./workbench.module.css";

interface SlotValue {
  value: unknown;
  confidence: number;
  authority_level: string;
  extraction_mode: string;
  evidence_refs?: Array<{ envelope_id: string; excerpt: string }>;
}

interface Ambiguity {
  field_name: string;
  ambiguity_type: string;
  raw_value: string;
}

interface Unknown {
  field_name: string;
  reason: string;
  notes: string | null;
}

interface Contradiction {
  field_name: string;
  values: unknown[];
  sources: string[];
}

interface ValidationReport {
  is_valid: boolean;
  errors: Array<{ severity: string; code: string; message: string; field: string }>;
  warnings: Array<{ severity: string; code: string; message: string; field: string }>;
}

export function PacketTab() {
  const { result_packet, result_validation } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);

  if (!result_packet) {
    return (
      <div className={styles.emptyState}>
        <p>No booking request data. Process a trip from the New Inquiry tab first.</p>
      </div>
    );
  }

  const bookingRequest = result_packet as Record<string, unknown>;
  const validation = result_validation as ValidationReport | null;

  // Extract summary data from facts
  const facts = (bookingRequest.facts || {}) as Record<string, SlotValue>;
  const derivedSignals = (bookingRequest.derived_signals || {}) as Record<string, SlotValue>;
  const ambiguities = (bookingRequest.ambiguities || []) as Ambiguity[];
  const unknowns = (bookingRequest.unknowns || []) as Unknown[];
  const contradictions = (bookingRequest.contradictions || []) as Contradiction[];

  // Build summary from facts
  const summaryData = {
    Destination: _getFactValue(facts, "destination_candidates") || "—",
    Origin: _getFactValue(facts, "origin_city") || "—",
    Dates: _getFactValue(facts, "date_window") || _getFactValue(facts, "date_start") || "—",
    Budget: _getFactValue(facts, "budget_raw_text") || "—",
    Party: _getFactValue(facts, "party_size") || "—",
  };

  const summaryCards = Object.entries(summaryData).map(([label, value]) => ({
    label,
    value: String(value),
  }));

  return (
    <div>
      <div className={styles.summaryGrid}>
        {summaryCards.map((card) => (
          <div key={card.label} className={styles.summaryItem}>
            <div className={styles.summaryLabel}>{card.label}</div>
            <div className={styles.summaryValue}>{card.value}</div>
          </div>
        ))}
      </div>

      {/* Facts Section */}
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Facts</h3>
        <div className={styles.card}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Field</th>
                <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Value</th>
                <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Confidence</th>
                <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Authority</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(facts).map(([field, slot]) => (
                <tr key={`fact-${field}`} style={{ borderBottom: "1px solid var(--color-border)" }}>
                  <td style={{ padding: "8px", fontSize: "13px" }}>{field}</td>
                  <td style={{ padding: "8px", fontSize: "13px" }}>{_formatValue(slot.value)}</td>
                  <td style={{ padding: "8px", fontSize: "13px", color: "var(--color-text-muted)" }}>{_formatConfidence(slot.confidence)}</td>
                  <td style={{ padding: "8px", fontSize: "13px", color: "var(--color-text-muted)" }}>{slot.authority_level || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Derived Signals Section */}
      {Object.keys(derivedSignals).length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Derived Signals</h3>
          <div className={styles.card}>
              {Object.entries(derivedSignals).map(([signal, slot]) => (
              <div key={`sig-${signal}`} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--color-border)" }}>
                <span>{signal}</span>
                <span style={{ color: "var(--color-text-muted)", fontSize: "12px" }}>
                  {String(slot.value)} ({_formatConfidence(slot.confidence)})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ambiguities Section */}
      {ambiguities.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Ambiguities</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {ambiguities.map((amb, idx) => (
                <li key={`amb-${amb.field_name}-${idx}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconWarning}`}>?</span>
                  <div>
                    <strong>{amb.field_name}</strong> ({amb.ambiguity_type})
                    <p style={{ fontSize: "12px", color: "var(--color-text-muted)", margin: "4px 0 0 0" }}>
                      Raw: {amb.raw_value}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Unknowns Section */}
      {unknowns.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Unknowns</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {unknowns.map((unk, idx) => (
                <li key={`unk-${unk.field_name}-${idx}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconInfo}`}>!</span>
                  <div>
                    <strong>{unk.field_name}</strong> — {unk.reason}
                    {unk.notes && (
                      <p style={{ fontSize: "12px", color: "var(--color-text-muted)", margin: "4px 0 0 0" }}>
                        {unk.notes}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Contradictions Section */}
      {contradictions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Contradictions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {contradictions.map((con, idx) => (
                <li key={`con-${con.field_name}-${idx}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  <div>
                    <strong>{con.field_name}</strong>
                    <p style={{ fontSize: "12px", color: "var(--color-text-muted)", margin: "4px 0 0 0" }}>
                      Values: {con.values.join(" vs ")}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Validation Report Section */}
      {validation && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Validation Report</h3>
          <div className={styles.card}>
            <div style={{ marginBottom: "8px" }}>
              <strong>Valid:</strong> {validation.is_valid ? "✓ Yes" : "✗ No"}
            </div>
            {validation.errors.length > 0 && (
              <div style={{ marginBottom: "8px" }}>
                <strong style={{ color: "var(--color-danger)" }}>Errors:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {validation.errors.map((err, i) => (
                    <li key={`err-${err.code}-${err.field}-${i}`}>{err.message} ({err.field})</li>
                  ))}
                </ul>
              </div>
            )}
            {validation.warnings.length > 0 && (
              <div>
                <strong style={{ color: "var(--color-warning)" }}>Warnings:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {validation.warnings.map((warn, i) => (
                    <li key={`warn-${warn.code}-${i}`}>{warn.message}</li>
                  ))}
                </ul>
              </div>
            )}
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
          <pre>{JSON.stringify(bookingRequest, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function _getFactValue(facts: Record<string, SlotValue>, field: string): unknown {
  const slot = facts[field];
  return slot?.value ?? null;
}

function _formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function _formatConfidence(confidence: number | undefined): string {
  if (confidence === undefined || confidence === null) return "—";
  return `${Math.round(confidence * 100)}%`;
}