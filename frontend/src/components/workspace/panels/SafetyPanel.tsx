"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { SafetyResult, PromptBundle } from "@/types/spine";
import { AlertCircle, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import Link from "next/link";

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

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-2">Risk Gate</h3>
        <p className="text-ui-xs text-text-muted mb-3">
          Final send-readiness check for customer-safe language and compliance-sensitive terms.
        </p>
        {safety.leakage_passed ? (
          <div className="border border-[#1c2128] rounded-lg p-4 bg-sidebar">
            <div className="flex items-center text-accent-green font-semibold mb-1">
              <CheckCircle className="size-4 mr-2" />
              PASS - Safe for Customer
            </div>
            <p className="text-ui-sm text-text-muted">
              No internal jargon or sensitive details found in the customer-facing message.
            </p>
          </div>
        ) : (
          <div className="border border-[rgba(var(--accent-red-rgb)/0.4)]/30 rounded-lg p-4 bg-[rgba(var(--accent-red-rgb)/0.18)]/10">
            <div className="flex items-center text-accent-red font-semibold mb-1">
              <XCircle className="size-4 mr-2" />
              FAIL - Internal Jargon Found
            </div>
            <p className="text-ui-sm text-text-muted">
              Internal-only terms were found in the message the customer would see.
            </p>
          </div>
        )}
      </section>

      {safety.strict_leakage && !safety.leakage_passed && (
        <div className="border-2 border-[rgba(var(--accent-red-rgb)/0.45)]/50 rounded-lg p-4 bg-[rgba(var(--accent-red-rgb)/0.18)]/20">
          <div className="flex items-center text-accent-red font-bold text-ui-sm mb-1">
            <AlertTriangle className="size-4 mr-2" />
            NOT SAFE TO SEND
          </div>
          <p className="text-ui-sm text-text-primary">
            Customer message contains internal jargon and cannot be sent until fixed.
          </p>
        </div>
      )}

      {safety.leakage_errors && safety.leakage_errors.length > 0 && (
        <section>
          <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Jargon Found in Customer Message</h3>
          <div className="bg-sidebar rounded-lg border border-[#1c2128] p-4">
            <ul className="space-y-2">
              {safety.leakage_errors.map((item: string, i: number) => (
                <li key={`leak-${item.slice(0, 15)}`} className="flex items-center text-ui-sm text-accent-red">
                  <AlertCircle className="size-3.5 mr-2 shrink-0" />
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
              {isStrictFail ? "Cannot be sent - contains internal jargon" : "No customer message available"}
            </p>
          )}
        </div>
      </section>

      <button
        type="button"
        className="text-ui-xs text-accent-blue hover:text-accent-blue underline mt-2"
        onClick={() => setShowRaw(!effectiveShowRaw)}
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
