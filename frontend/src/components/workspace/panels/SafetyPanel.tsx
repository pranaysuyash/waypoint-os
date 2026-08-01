"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { SafetyResult, PromptBundle } from "@/types/spine";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { isDebugJsonAllowed } from "@/lib/privacy-controls";
import {
  getSafetyCleanupChecklist,
  getSafetyCleanupSummary,
  getSafetyReviewStatusCopy,
} from "@/lib/safety-review-copy";

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
  const debugJsonAllowed = isDebugJsonAllowed();
  const effectiveShowRaw = debugJsonAllowed && (debug_raw_json || showRaw);

  if (!result_safety) {
    return (
      <div className="p-6 text-center">
        <h2 className="text-ui-xl font-semibold text-text-primary">Safety review not ready yet</h2>
        <p className="text-ui-sm text-text-muted mt-2">Safety checks will run after trip options are built.</p>
        <div className="mt-6 flex flex-wrap gap-3 justify-center">
          <Link
            href={`/trips/${tripId}/strategy`}
            className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
          >
            Go to Options
          </Link>
        </div>
      </div>
    );
  }

  const safety = result_safety as SafetyResult;
  const travelerBundle = result_traveler_bundle as PromptBundle | null;
  const isStrictFail = safety.strict_leakage && !safety.leakage_passed;
  const safetyStatusCopy = getSafetyReviewStatusCopy(safety);
  const cleanupChecklist = getSafetyCleanupChecklist();

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-2">Message review</h3>
        <p className="text-ui-xs text-text-muted mb-3">
          Final send-readiness check for customer-safe language before anything leaves the workspace.
        </p>
        {safety.leakage_passed ? (
          <div className="border border-[#1c2128] rounded-lg p-4 bg-sidebar">
            <div className="flex items-center text-accent-green font-semibold mb-1">
              <CheckCircle className="size-4 mr-2" />
              {safetyStatusCopy.heading}
            </div>
            <p className="text-ui-sm text-text-muted">
              {safetyStatusCopy.body}
            </p>
          </div>
        ) : (
          <div className="border border-[rgba(var(--accent-red-rgb)/0.4)]/30 rounded-lg p-4 bg-[rgba(var(--accent-red-rgb)/0.18)]/10">
            <div className="flex items-center text-accent-red font-semibold mb-1">
              <XCircle className="size-4 mr-2" />
              {safetyStatusCopy.heading}
            </div>
            <p className="text-ui-sm text-text-muted">
              {safetyStatusCopy.body}
            </p>
          </div>
        )}
      </section>

      {safety.strict_leakage && !safety.leakage_passed && (
        <div className="border-2 border-[rgba(var(--accent-red-rgb)/0.45)]/50 rounded-lg p-4 bg-[rgba(var(--accent-red-rgb)/0.18)]/20">
          <div className="flex items-center text-accent-red font-bold text-ui-sm mb-1">
            <AlertTriangle className="size-4 mr-2" />
            Hold send for now
          </div>
          <p className="text-ui-sm text-text-primary">
            Rewrite the customer-facing reply, then run message review again before sending.
          </p>
        </div>
      )}

      {safety.leakage_errors && safety.leakage_errors.length > 0 && (
        <section>
          <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">What needs cleanup</h3>
          <div className="bg-sidebar rounded-lg border border-[#1c2128] p-4">
            <p className="mb-3 text-ui-sm text-text-muted">
              {getSafetyCleanupSummary(safety)}
            </p>
            <ul className="space-y-2">
              {cleanupChecklist.map((item) => (
                <li key={`leak-${item}`} className="flex items-start text-ui-sm text-text-primary">
                  <span className="mr-2 shrink-0 text-accent-red">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Customer Message QA</h3>
        <div className="bg-sidebar rounded-lg border border-[#1c2128] p-4 space-y-4">
          {travelerBundle && !isStrictFail ? (
            <>
              <div>
                <div className="text-[var(--ui-text-xs)] font-bold text-text-muted uppercase tracking-wider">Background Notes</div>
                <p className="text-ui-sm text-text-secondary mt-1 leading-relaxed whitespace-pre-wrap">
                  {travelerBundle.system_context || "-"}
                </p>
              </div>
              <div>
                <div className="text-[var(--ui-text-xs)] font-bold text-text-muted uppercase tracking-wider">Message Preview</div>
                <p className="text-ui-sm text-text-secondary mt-1 leading-relaxed whitespace-pre-wrap">
                  {travelerBundle.user_message || "-"}
                </p>
              </div>
              {travelerBundle.follow_up_sequence && travelerBundle.follow_up_sequence.length > 0 && (
                <div>
                  <div className="text-[var(--ui-text-xs)] font-bold text-text-muted uppercase tracking-wider">Follow-up Sequence</div>
                  <ul className="mt-1 space-y-1">
                    {travelerBundle.follow_up_sequence.map((f, i) => (
                      <li key={`fseq-${f.field_name}`} className="text-ui-sm text-text-muted">
                        <span className="font-semibold text-text-muted">[{f.priority}]</span> {f.question}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <p className="text-ui-sm text-text-muted italic">
              {isStrictFail ? "Hold send until the customer-facing reply is rewritten." : "No customer message available"}
            </p>
          )}
        </div>
      </section>

      {!debugJsonAllowed && (
        <div className="rounded border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-ui-xs text-amber-200">
          Technical Data is hidden by privacy policy. Set <code>NEXT_PUBLIC_ALLOW_DEBUG_JSON=true</code> in a secure environment to enable.
        </div>
      )}

      <button
        type="button"
        className="text-ui-xs text-accent-blue hover:text-accent-blue underline mt-2 disabled:opacity-50"
        disabled={!debugJsonAllowed}
        onClick={() => setShowRaw((prev) => !prev)}
      >
        {effectiveShowRaw ? "Hide" : "Show"} Diagnostic Data
      </button>

      {effectiveShowRaw && (
        <pre className="bg-sidebar p-4 rounded text-ui-xs font-mono text-text-muted overflow-x-auto border border-[#1c2128]">
          {JSON.stringify({
            safety: result_safety,
            traveler_bundle: result_traveler_bundle,
            internal_bundle: result_internal_bundle,
          }, null, 2)}
        </pre>
      )}
    </div>
  );
}
