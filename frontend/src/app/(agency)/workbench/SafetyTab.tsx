import { useWorkbenchStore } from "@/stores/workbench";
import type { SafetyResult, PromptBundle, DecisionOutput } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import styles from "@/components/workbench/workbench.module.css";

interface SpecialtyHit {
  niche: string;
  keywords?: string[];
  checklists?: string[];
  compliance?: string[];
  safety_notes?: string | null;
  urgency?: string;
}

interface SafetyTabProps {
  trip?: Trip | null;
}

const URGENCY_STYLES: Record<string, string> = {
  CRITICAL: styles.stateRed,
  HIGH: styles.stateAmber,
  NORMAL: styles.stateBlue,
};

export default function SafetyTab({ trip }: SafetyTabProps) {
  const {
    result_safety,
    result_traveler_bundle,
    result_internal_bundle,
    result_decision,
    debug_raw_json,
    setDebugRawJson,
  } = useWorkbenchStore();

  const activeSafety = result_safety || (trip?.safety as SafetyResult | null);
  const activeTravelerBundle = (result_traveler_bundle as PromptBundle | null) ?? (trip?.traveler_bundle as PromptBundle | null);
  const activeInternalBundle = (result_internal_bundle as PromptBundle | null) ?? (trip?.internal_bundle as PromptBundle | null);
  const activeDecision = result_decision ?? (trip?.decision as DecisionOutput | null) ?? null;

  const specialtyHits: SpecialtyHit[] = (() => {
    const rationale = activeDecision?.rationale as unknown as Record<string, unknown> | null;
    const frontier = rationale?.frontier as Record<string, unknown> | null;
    if (!frontier) return [];
    const sk = frontier.specialty_knowledge;
    return Array.isArray(sk) ? sk : [];
  })();

  if (!activeSafety) {
    return (
      <div className={styles.emptyState}>
        <p>No risk review data yet. Process a trip from the "New Inquiry" section first.</p>
      </div>
    );
  }

  const safety = activeSafety;
  const travelerBundle = activeTravelerBundle;
  const internalBundle = activeInternalBundle;

  const strippedFields = safety.leakage_errors || [];
  const isStrictFail = safety.strict_leakage && !safety.leakage_passed;

  return (
    <div>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Risk Gate</h3>
        <p style={{ fontSize: "12px", color: "var(--color-text-muted)", margin: "0 0 10px 0" }}>
          Final send-readiness check for customer-safe language and compliance-sensitive terms.
        </p>
        {safety.leakage_passed ? (
          <div className={styles.leakagePass}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconSuccess}`} style={{ marginRight: "8px" }}>✓</span>
              PASS - Safe for Customer
            </div>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              No internal jargon or sensitive details found in the customer-facing message.
            </p>
          </div>
        ) : (
          <div className={styles.leakageFail}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconDanger}`} style={{ marginRight: "8px" }}>✗</span>
              FAIL - Internal Jargon Found
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
              {strippedFields.map((item: any, i: number) => (
                <li key={`leak-${item.slice(0, 30)}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {specialtyHits.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Special Handling Controls</h3>
          {specialtyHits.map((hit, i) => (
            <div key={`sk-${hit.niche}`} className={styles.card} style={{ marginBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <strong style={{ fontSize: "14px" }}>{hit.niche}</strong>
                <span className={`${styles.badge} ${URGENCY_STYLES[hit.urgency ?? "NORMAL"] ?? styles.stateBlue}`}>
                  {hit.urgency ?? "NORMAL"}
                </span>
              </div>
              {hit.checklists && hit.checklists.length > 0 && (
                <div style={{ marginBottom: "8px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Checklist</strong>
                  <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                    {hit.checklists.map((item) => (
                      <li key={`cl-${item.slice(0, 20)}`} style={{ marginBottom: "2px" }}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {hit.compliance && hit.compliance.length > 0 && (
                <div style={{ marginBottom: "8px" }}>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Compliance</strong>
                  <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                    {hit.compliance.map((item) => (
                      <li key={`comp-${item.slice(0, 20)}`} style={{ marginBottom: "2px" }}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {hit.safety_notes && (
                <div>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Risk Notes</strong>
                  <p style={{ fontSize: "13px", margin: "4px 0 0 0", whiteSpace: "pre-wrap" }}>{hit.safety_notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Customer Message QA</h3>
        <div className={styles.card}>
          {travelerBundle && !isStrictFail ? (
            <div>
              <div style={{ marginBottom: "12px" }}>
                <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Generation Context</strong>
                  <p style={{ fontSize: "13px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                    {travelerBundle?.system_context || "-"}
                </p>
              </div>
              <div style={{ marginBottom: "12px" }}>
                <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Message Preview</strong>
                <p style={{ fontSize: "13px", whiteSpace: "pre-wrap", marginTop: "4px" }}>
                  {travelerBundle.user_message || "-"}
                </p>
              </div>
              {travelerBundle.follow_up_sequence && travelerBundle.follow_up_sequence.length > 0 && (
                <div>
                  <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Follow-up Sequence</strong>
                  <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                    {travelerBundle.follow_up_sequence.map((f, i) => (
                      <li key={`fseq-${f.field_name}`} style={{ marginBottom: "4px" }}>
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
                      <li key={`iconst-${c.slice(0, 30)}`}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: "var(--color-text-muted)" }}>
              {isStrictFail ? "Cannot be sent - contains internal jargon" : "No customer message available"}
            </p>
          )}
        </div>
      </div>

      {internalBundle && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Agent-Only Notes</h3>
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
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Diagnostic Data
      </button>

      {debug_raw_json && (
        <div className={styles.jsonOutput}>
          <pre>{JSON.stringify({
            safety: activeSafety,
            traveler_bundle: activeTravelerBundle,
            internal_bundle: activeInternalBundle,
          }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
