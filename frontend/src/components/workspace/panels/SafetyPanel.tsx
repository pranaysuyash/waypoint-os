"use client";

import { useState } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { SafetyResult, PromptBundle } from "@/types/spine";
import { AlertCircle, CheckCircle, XCircle, AlertTriangle } from "lucide-react";

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
      <div className="p-4 text-sm text-gray-500 italic">
        <p>No review data for trip {tripId}. Process a trip from the "New Inquiry" section first.</p>
      </div>
    );
  }

  const safety = result_safety as SafetyResult;
  const travelerBundle = result_traveler_bundle as PromptBundle | null;
  const isStrictFail = safety.strict_leakage && !safety.leakage_passed;

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Content Review</h3>
        {safety.leakage_passed ? (
          <div className="border border-[#1c2128] rounded-lg p-4 bg-[#0a0d11]">
            <div className="flex items-center text-emerald-400 font-semibold mb-1">
              <CheckCircle className="w-4 h-4 mr-2" />
              PASS — Safe for Customer
            </div>
            <p className="text-sm text-gray-400">
              No internal jargon or sensitive details found in the customer-facing message.
            </p>
          </div>
        ) : (
          <div className="border border-rose-900/30 rounded-lg p-4 bg-rose-950/10">
            <div className="flex items-center text-rose-400 font-semibold mb-1">
              <XCircle className="w-4 h-4 mr-2" />
              FAIL — Internal Jargon Found
            </div>
            <p className="text-sm text-gray-400">
              Internal-only terms were found in the message the customer would see.
            </p>
          </div>
        )}
      </section>

      {safety.strict_leakage && !safety.leakage_passed && (
        <div className="border-2 border-rose-500/50 rounded-lg p-4 bg-rose-950/20">
          <div className="flex items-center text-rose-500 font-bold text-sm mb-1">
            <AlertTriangle className="w-4 h-4 mr-2" />
            NOT SAFE TO SEND
          </div>
          <p className="text-sm text-gray-200">
            Customer message contains internal jargon and cannot be sent until fixed.
          </p>
        </div>
      )}

      {safety.leakage_errors && safety.leakage_errors.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Jargon Found in Customer Message</h3>
          <div className="bg-[#0a0d11] rounded-lg border border-[#1c2128] p-4">
            <ul className="space-y-2">
              {safety.leakage_errors.map((item: string, i: number) => (
                <li key={`leak-${item.slice(0, 15)}-${i}`} className="flex items-center text-sm text-rose-400">
                  <AlertCircle className="w-3.5 h-3.5 mr-2 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Customer-Facing Message</h3>
        <div className="bg-[#0a0d11] rounded-lg border border-[#1c2128] p-4 space-y-4">
          {travelerBundle && !isStrictFail ? (
            <>
              <div>
                <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Background Notes</div>
                <p className="text-sm text-gray-300 mt-1 leading-relaxed whitespace-pre-wrap">
                  {travelerBundle.system_context || "—"}
                </p>
              </div>
              <div>
                <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Message Preview</div>
                <p className="text-sm text-gray-300 mt-1 leading-relaxed whitespace-pre-wrap">
                  {travelerBundle.user_message || "—"}
                </p>
              </div>
              {travelerBundle.follow_up_sequence && travelerBundle.follow_up_sequence.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Follow-up Sequence</div>
                  <ul className="mt-1 space-y-1">
                    {travelerBundle.follow_up_sequence.map((f, i) => (
                      <li key={`fseq-${f.field_name}-${i}`} className="text-sm text-gray-400">
                        <span className="font-semibold text-gray-500">[{f.priority}]</span> {f.question}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-500 italic">
              {isStrictFail ? "Cannot be sent — contains internal jargon" : "No customer message available"}
            </p>
          )}
        </div>
      </section>

      <button
        type="button"
        className="text-xs text-blue-400 hover:text-blue-300 underline mt-2"
        onClick={() => setShowRaw(!effectiveShowRaw)}
      >
        {effectiveShowRaw ? "Hide" : "Show"} Technical Data
      </button>

      {effectiveShowRaw && (
        <pre className="bg-[#0a0d11] p-4 rounded text-xs font-mono text-gray-400 overflow-x-auto border border-[#1c2128]">
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
