"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import styles from "./workbench.module.css";

export function PacketTab() {
  const { result_packet, result_validation } = useWorkbenchStore();
  const [showRaw, setShowRaw] = useState(false);

  if (!result_packet) {
    return (
      <div className={styles.emptyState}>
        <p>No packet data. Run Spine from the Intake tab first.</p>
      </div>
    );
  }

  const packet = result_packet as Record<string, unknown>;
  const validation = result_validation as Record<string, unknown> | null;

  const summaryCards = [
    { label: "Destination", value: (packet.destination as string) || "—" },
    { label: "Dates", value: (packet.dates as string) || "—" },
    { label: "Budget", value: (packet.budget as string) || "—" },
    { label: "Party Size", value: (packet.party_size as string) || "—" },
    { label: "Confidence", value: (packet.confidence as string) || "—" },
  ];

  const facts = (packet.facts as Array<{ field: string; value: string; authority: string }>) || [];
  const derivedSignals = (packet.derived_signals as Array<{ signal: string; maturity: string }>) || [];
  const ambiguities = (packet.ambiguities as string[]) || [];
  const unknowns = (packet.unknowns as string[]) || [];
  const contradictions = (packet.contradictions as string[]) || [];

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

      {facts.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Facts</h3>
          <div className={styles.card}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Field</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Value</th>
                  <th style={{ textAlign: "left", padding: "8px", fontSize: "12px", color: "var(--color-text-muted)" }}>Authority</th>
                </tr>
              </thead>
              <tbody>
                {facts.map((fact, i) => (
                  <tr key={`${fact.field}-${i}`} style={{ borderBottom: "1px solid var(--color-border)" }}>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{fact.field}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{fact.value}</td>
                    <td style={{ padding: "8px", fontSize: "13px", color: "var(--color-text-muted)" }}>{fact.authority}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {derivedSignals.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Derived Signals</h3>
          <div className={styles.card}>
            {derivedSignals.map((sig, i) => (
              <div key={`${sig.signal}-${i}`} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--color-border)" }}>
                <span>{sig.signal}</span>
                <span style={{ color: "var(--color-text-muted)", fontSize: "12px" }}>{sig.maturity}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {ambiguities.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Ambiguities</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {ambiguities.map((item, idx) => (
                <li key={`amb-${idx}-${item.slice(0, 10)}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconWarning}`}>?</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {unknowns.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Unknowns</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {unknowns.map((item, idx) => (
                <li key={`unk-${idx}-${item.slice(0, 10)}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconInfo}`}>!</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {contradictions.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Contradictions</h3>
          <div className={styles.card}>
            <ul className={styles.list}>
              {contradictions.map((item, idx) => (
                <li key={`con-${idx}-${item.slice(0, 10)}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {validation && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Validation Report</h3>
          <div className={styles.card}>
            <pre className={styles.jsonOutput} style={{ whiteSpace: "pre-wrap" }}>
              {JSON.stringify(validation, null, 2)}
            </pre>
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
          <pre>{JSON.stringify(packet, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
