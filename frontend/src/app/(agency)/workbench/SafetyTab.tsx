import Link from "next/link";
import { useWorkbenchStore } from "@/stores/workbench";
import type { SafetyResult, PromptBundle, DecisionOutput, FollowUpQuestion } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import { normalizeSafetyResult } from "@/lib/bff-trip-adapters";
import { DECISION_STATE_LABELS, FIELD_LABELS, labelOrTitle, titleCase } from "@/lib/label-maps";
import { getTripRepairRoute } from "@/lib/routes";
import {
  getSafetyCleanupChecklist,
  getSafetyCleanupSummary,
  getSafetyReviewStatusCopy,
} from "@/lib/safety-review-copy";
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

const BLOCKER_LABELS: Record<string, string> = {
  budget_feasibility: "Recheck whether the budget matches the requested trip",
  date_flexibility: "Clarify how flexible the travel dates are",
  incomplete_intake: "Complete the missing trip details",
  missing_passport: "Collect the missing passport details",
  resolved_destination: "Confirm the final destination",
  soft_preferences: "Capture any must-have preferences before quoting",
};

function humanizeBlocker(raw: string): string {
  const normalized = raw.trim().toLowerCase();
  if (BLOCKER_LABELS[normalized]) return BLOCKER_LABELS[normalized];
  return labelOrTitle(FIELD_LABELS, normalized, titleCase(normalized));
}

export default function SafetyTab({ trip }: SafetyTabProps) {
  const {
    result_safety,
    result_traveler_bundle,
    result_internal_bundle,
    result_decision,
    debug_raw_json,
    setDebugRawJson,
  } = useWorkbenchStore();

  const activeSafety = result_safety || normalizeSafetyResult(trip?.safety);
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

  const safety = activeSafety as SafetyResult;
  const travelerBundle = activeTravelerBundle;
  const internalBundle = activeInternalBundle;
  const strippedFields = safety?.leakage_errors || [];
  const isStrictFail = Boolean(safety?.strict_leakage && !safety?.leakage_passed);
  const safetyStatusCopy = getSafetyReviewStatusCopy(safety);
  const cleanupChecklist = getSafetyCleanupChecklist();
  const decisionState = activeDecision?.decision_state ?? null;
  const hasDerivedSafetyContext = !activeSafety && Boolean(activeDecision);
  const hardBlockers = (activeDecision as any)?.hard_blockers ?? [];
  const softBlockers = (activeDecision as any)?.soft_blockers ?? [];
  const followUpQuestions: FollowUpQuestion[] = (activeDecision as any)?.follow_up_questions ?? [];
  const overallConfidence = activeDecision?.confidence?.overall;
  const tripRepairHref = trip?.id ? getTripRepairRoute(trip.id) : null;
  const confidenceLabel =
    typeof overallConfidence === "number" && Number.isFinite(overallConfidence)
      ? `${Math.round(overallConfidence * 100)}%`
      : "Confidence unavailable";

  return (
    <div>
      {activeDecision && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Trip readiness</h3>
          <div className={styles.card}>
            <span className={`${styles.badge} ${URGENCY_STYLES.NORMAL}`}>
              {DECISION_STATE_LABELS[decisionState ?? ""] || "Review Required"}
            </span>
            <div style={{ marginTop: "12px", fontSize: "13px", color: "var(--color-text-muted)" }}>
              Overall Confidence: {confidenceLabel}
            </div>
            {hardBlockers.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong style={{ color: "var(--color-danger)" }}>Needs to be fixed before we can send:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {hardBlockers.map((b: string) => <li key={`hard-${b}`}>{humanizeBlocker(b)}</li>)}
                </ul>
              </div>
            )}
            {softBlockers.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong style={{ color: "var(--color-warning)" }}>Still worth confirming:</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {softBlockers.map((b: string) => <li key={`soft-${b}`}>{humanizeBlocker(b)}</li>)}
                </ul>
              </div>
            )}
            {followUpQuestions.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <strong style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>Questions to ask the traveler</strong>
                <ul style={{ margin: "4px 0 0 16px", fontSize: "13px" }}>
                  {followUpQuestions.map((question, index) => (
                    <li key={`fu-${question.field_name || index}`} style={{ marginBottom: "4px" }}>
                      {question.question}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {!activeSafety && !activeDecision && (
        <div className={styles.emptyState}>
          <p>
            {tripRepairHref
              ? 'No risk review data yet. Open Trip Details to continue repairing the trip.'
              : 'No risk review data yet.'}
          </p>
          {tripRepairHref && (
            <Link
              href={tripRepairHref}
              className="mt-3 inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
            >
              Open Trip Details
            </Link>
          )}
        </div>
      )}

      {!activeSafety && activeDecision && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Customer Message QA</h3>
          <div className={styles.card}>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: 0 }}>
              The message audit is not available for this run yet, so this view is showing the readiness summary instead.
            </p>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              You can still review the traveler-facing draft below before sending.
            </p>
          </div>
          {travelerBundle && hasDerivedSafetyContext && (
            <div className={styles.card} style={{ marginTop: "12px" }}>
              <div style={{ fontSize: "12px", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Customer Message Preview
              </div>
              <p style={{ fontSize: "13px", margin: "6px 0 0 0", whiteSpace: "pre-wrap" }}>
                {travelerBundle.user_message || "-"}
              </p>
            </div>
          )}
        </div>
      )}

      {activeSafety && (
        <>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Customer message check</h3>
        <p style={{ fontSize: "12px", color: "var(--color-text-muted)", margin: "0 0 10px 0" }}>
          We review the traveler-facing draft here before anything leaves the workspace.
        </p>
      {safety.leakage_passed ? (
          <div className={styles.leakagePass}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconSuccess}`} style={{ marginRight: "8px" }}>✓</span>
              {safetyStatusCopy.heading}
            </div>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              {safetyStatusCopy.body}
            </p>
          </div>
        ) : (
          <div className={styles.leakageFail}>
            <div className={styles.leakageTitle}>
              <span className={`${styles.listIcon} ${styles.iconDanger}`} style={{ marginRight: "8px" }}>✗</span>
              {safetyStatusCopy.heading}
            </div>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "8px 0 0 0" }}>
              {safetyStatusCopy.body}
            </p>
          </div>
        )}
      </div>

      {safety.strict_leakage && !safety.leakage_passed && (
        <div className={styles.leakageFail} style={{ border: "2px solid rgba(239, 68, 68, 0.5)", marginBottom: "16px" }}>
          <div className={styles.leakageTitle} style={{ color: "var(--color-danger)", fontWeight: 700 }}>
            Hold before sending
          </div>
          <p style={{ fontSize: "13px", margin: "8px 0 0 0" }}>
            Rewrite the customer-facing reply, then run this review again before sending.
          </p>
        </div>
      )}

      {strippedFields.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>What needs cleanup</h3>
          <div className={styles.card}>
            <p style={{ fontSize: "13px", color: "var(--color-text-muted)", margin: "0 0 10px 0" }}>
              {getSafetyCleanupSummary(safety)}
            </p>
            <ul className={styles.list}>
              {cleanupChecklist.map((item) => (
                <li key={`leak-${item}`} className={styles.listItem}>
                  <span className={`${styles.listIcon} ${styles.iconDanger}`}>•</span>
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
              {isStrictFail ? "Blocked until the draft is cleaned up" : "No customer message available"}
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
            raw_leakage_errors: strippedFields,
            traveler_bundle: activeTravelerBundle,
            internal_bundle: activeInternalBundle,
          }, null, 2)}</pre>
        </div>
      )}
        </>
      )}
    </div>
  );
}
