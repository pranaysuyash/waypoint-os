import { useWorkbenchStore } from "@/stores/workbench";
import type { SlotValue, Ambiguity, PacketUnknown, PacketContradiction, ValidationReport } from "@/types/spine";
import { validationLabelFor } from "@/types/spine";
import type { Trip } from "@/lib/api-client";
import { FIELD_LABELS, SIGNAL_LABELS, AMBIGUITY_TYPE_LABELS, labelOrTitle } from "@/lib/label-maps";
import { getTravelerPromptForUnknownField } from "@/lib/traveler-prompts";
import { AlertTriangle, CheckCircle, XCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface PacketTabProps {
  trip?: Trip | null;
}

export default function PacketTab({ trip }: PacketTabProps) {
  const { result_packet, result_validation, debug_raw_json, setDebugRawJson } = useWorkbenchStore();
  const [showRawJson, setShowRawJson] = useState(false);

  const activePacket = result_packet || trip?.packet;
  const activeValidation = result_validation || (trip?.validation as ValidationReport | null);

  if (!activePacket) {
    return (
      <div className="text-center py-10 text-[#8b949e]">
        <p>No booking request data. Process a trip from the &ldquo;New Inquiry&rdquo; section first.</p>
      </div>
    );
  }

  const bookingRequest = activePacket as Record<string, unknown>;
  const validation = activeValidation;

  const facts = (bookingRequest.facts || {}) as Record<string, SlotValue>;
  const derivedSignals = (bookingRequest.derived_signals || {}) as Record<string, SlotValue>;
  const ambiguities = (bookingRequest.ambiguities || []) as Ambiguity[];
  const unknowns = (bookingRequest.unknowns || []) as PacketUnknown[];
  const contradictions = (bookingRequest.contradictions || []) as PacketContradiction[];

  const summaryData = {
    Destination: _getFactValue(facts, "destination_candidates") || "-",
    Origin: _getFactValue(facts, "origin_city") || "-",
    Dates: _getFactValue(facts, "date_window") || _getFactValue(facts, "date_start") || "-",
    Budget: _getFactValue(facts, "budget_raw_text") || "-",
    Party: _getFactValue(facts, "party_size") || "-",
  };

  const summaryCards = Object.entries(summaryData).map((entry) => {
    const [label, value] = entry;
    return {
      label,
      value: _formatValue(value),
    };
  });

  // Derive issues from either legacy shape (errors/warnings arrays) or
  // current backend shape (status/gate/reasons + packet.unknowns).
  const legacyErrors = validation?.errors ?? [];
  const legacyWarnings = validation?.warnings ?? [];
  const unknownFields = (bookingRequest.unknowns || []) as PacketUnknown[];

  const hasLegacyErrors = legacyErrors.length > 0;
  const hasLegacyWarnings = legacyWarnings.length > 0;
  const isBlocked = validation && (validation.is_valid === false || validation.status === "ESCALATED" || validation.status === "BLOCKED");
  const isValid = validation && validation.is_valid === true && !isBlocked;

  return (
    <div className="space-y-6">
      {/* Validation Alert Banner */}
      {isBlocked && (
        <div className="rounded-xl border border-[#f85149]/40 bg-[#2b1011] p-4">
          <div className="flex items-start gap-3">
            <div className="shrink-0 mt-0.5">
              <AlertTriangle className="size-5 text-[#f85149]" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-ui-sm font-semibold text-[#f85149] mb-1">
                {validationLabelFor(validation.gate || validation.stage, 'alert_title')}
              </h3>
              {validation?.reasons && validation.reasons.length > 0 && (
                <p className="text-ui-xs text-[#ffa198] mb-3">
                  {validation.reasons.join("; ")}
                </p>
              )}
              {/* Legacy error list */}
              {(hasLegacyErrors || hasLegacyWarnings) && (
                <div className="space-y-1.5 mb-3">
                  {legacyErrors.map((err, i) => (
                    <div
                      key={`err-${err.code}-${err.field}`}
                      className="flex items-start gap-2 px-3 py-2 rounded-lg text-ui-xs bg-[#f85149]/10 border border-[#f85149]/30"
                    >
                      <XCircle className="size-3.5 text-[#f85149] shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium text-[#e6edf3]">
                          {err.field ? labelOrTitle(FIELD_LABELS, err.field) : err.field}
                        </span>
                        <span className="text-[#a8b3c1] ml-1">{err.message}</span>
                      </div>
                    </div>
                  ))}
                  {legacyWarnings.map((warn, i) => (
                    <div
                      key={`warn-${warn.code}-${warn.field}`}
                      className="flex items-start gap-2 px-3 py-2 rounded-lg text-ui-xs bg-[#d29922]/10 border border-[#d29922]/30"
                    >
                      <AlertTriangle className="size-3.5 text-[#d29922] shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium text-[#e6edf3]">
                          {warn.field ? labelOrTitle(FIELD_LABELS, warn.field) : warn.field}
                        </span>
                        <span className="text-[#a8b3c1] ml-1">{warn.message}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {/* Missing fields from packet unknowns */}
              {unknownFields.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-ui-xs text-[#a8b3c1] font-medium mb-1">Missing fields:</p>
                  {unknownFields.map((unk, i) => (
                    <div
                      key={`unk-${unk.field_name}`}
                      className="flex items-start gap-2 px-3 py-2 rounded-lg text-ui-xs bg-[#58a6ff]/10 border border-[#58a6ff]/30"
                    >
                      <Info className="size-3.5 text-[#58a6ff] shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium text-[#e6edf3]">
                          {labelOrTitle(FIELD_LABELS, unk.field_name)}
                        </span>
                        <span className="text-[#8b949e] ml-1 font-mono">({unk.field_name})</span>
                        <span className="text-[#a8b3c1] ml-1">- {unk.reason.replace(/_/g, " ")}</span>
                        {getTravelerPromptForUnknownField(unk.field_name) && (
                          <p className="text-[#8b949e] mt-1">
                            Prompt: {getTravelerPromptForUnknownField(unk.field_name)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-ui-xs text-[#a8b3c1] mt-3">
                Go back to the <span className="text-[#58a6ff] font-medium">New Inquiry</span> tab, provide the missing details in the Customer Message or Agent Notes, and try again.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Validation passed banner */}
      {isValid && (
        <div className="rounded-xl border border-[#3fb950]/40 bg-[#132b1a] p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="size-5 text-[#3fb950] shrink-0" />
            <div>
              <h3 className="text-ui-sm font-semibold text-[#3fb950]">All Checks Passed</h3>
              {!hasLegacyErrors && !hasLegacyWarnings && (
                <p className="text-ui-xs text-[#7ee787] mt-0.5">No issues found.</p>
              )}
              {hasLegacyWarnings && !hasLegacyErrors && (
                <p className="text-ui-xs text-[#d29922] mt-0.5">
                  {legacyWarnings.length} warning{legacyWarnings.length > 1 ? "s" : ""} found (non-blocking).
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* No validation data */}
      {!validation && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-4">
          <div className="flex items-center gap-3">
            <Info className="size-5 text-[#8b949e] shrink-0" />
            <div>
              <h3 className="text-ui-sm font-semibold text-[#e6edf3]">Validation Pending</h3>
              <p className="text-ui-xs text-[#8b949e] mt-0.5">
                Re-run the pipeline to validate extracted trip details.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {summaryCards.map((card) => (
          <div
            key={card.label}
            className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 text-center"
          >
            <div className="text-ui-xs text-[#8b949e] uppercase tracking-wide mb-1">
              {card.label}
            </div>
            <div className="text-ui-lg font-semibold text-[#e6edf3] truncate">
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* Facts Section */}
      <div>
        <h3 className="text-ui-base font-semibold text-[#e6edf3] mb-3">Extracted Information</h3>
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-[#30363d]">
                <th className="text-left px-3 py-2 text-ui-xs text-[#8b949e] font-medium">Field</th>
                <th className="text-left px-3 py-2 text-ui-xs text-[#8b949e] font-medium">Value</th>
                <th className="text-left px-3 py-2 text-ui-xs text-[#8b949e] font-medium">Confidence</th>
                <th className="text-left px-3 py-2 text-ui-xs text-[#8b949e] font-medium">Authority</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(facts).map((entry) => {
                const [field, slot] = entry;
                return (
                <tr key={`fact-${field}`} className="border-b border-[#30363d] last:border-0">
                  <td className="px-3 py-2 text-ui-sm text-[#e6edf3]">{labelOrTitle(FIELD_LABELS, field)}</td>
                  <td className="px-3 py-2 text-ui-sm text-[#e6edf3]">{_formatValue(slot.value)}</td>
                  <td className="px-3 py-2 text-ui-sm text-[#8b949e]">{_formatConfidence(slot.confidence)}</td>
                  <td className="px-3 py-2 text-ui-sm text-[#8b949e]">{slot.authority_level || "-"}</td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Derived Signals */}
      {Object.keys(derivedSignals).length > 0 && (
        <div>
          <h3 className="text-ui-base font-semibold text-[#e6edf3] mb-3">Inferred Details</h3>
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
            {Object.entries(derivedSignals).map((entry) => {
              const [signal, slot] = entry;
              return (
              <div
                key={`sig-${signal}`}
                className="flex justify-between py-2 border-b border-[#30363d] last:border-0"
              >
                <span className="text-ui-sm text-[#e6edf3]">{labelOrTitle(SIGNAL_LABELS, signal)}</span>
                <span className="text-ui-xs text-[#8b949e]">
                  {_formatValue(slot.value)} ({_formatConfidence(slot.confidence)})
                </span>
              </div>
            )})}
          </div>
        </div>
      )}

      {/* Ambiguities */}
      {ambiguities.length > 0 && (
        <div>
          <h3 className="text-ui-base font-semibold text-[#d29922] mb-3">Ambiguities</h3>
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
            <ul className="space-y-2">
              {ambiguities.map((amb, idx) => (
                <li key={`amb-${amb.field_name}`} className="flex items-start gap-2 py-1.5 border-b border-[#30363d] last:border-0">
                  <span className="text-[#d29922] shrink-0 mt-0.5 text-ui-sm">?</span>
                  <div>
                    <span className="text-ui-sm font-medium text-[#e6edf3]">
                      {labelOrTitle(FIELD_LABELS, amb.field_name)}
                    </span>
                    <span className="text-ui-xs text-[#8b949e] ml-1">
                      ({labelOrTitle(AMBIGUITY_TYPE_LABELS, amb.ambiguity_type)})
                    </span>
                    <p className="text-ui-xs text-[#8b949e] mt-0.5">
                      Raw: {amb.raw_value}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Unknowns */}
      {unknowns.length > 0 && (
        <div>
          <h3 className="text-ui-base font-semibold text-[#58a6ff] mb-3">Unknowns</h3>
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
            <ul className="space-y-2">
              {unknowns.map((unk, idx) => (
                <li key={`unk-${unk.field_name}`} className="flex items-start gap-2 py-1.5 border-b border-[#30363d] last:border-0">
                  <span className="text-[#58a6ff] shrink-0 mt-0.5 text-ui-sm">!</span>
                  <div>
                    <span className="text-ui-sm font-medium text-[#e6edf3]">
                      {labelOrTitle(FIELD_LABELS, unk.field_name)}
                    </span>
                    <span className="text-ui-sm text-[#a8b3c1] ml-1">- {unk.reason}</span>
                    {unk.notes && (
                      <p className="text-ui-xs text-[#8b949e] mt-0.5">{unk.notes}</p>
                    )}
                    {getTravelerPromptForUnknownField(unk.field_name) && (
                      <p className="text-ui-xs text-[#8b949e] mt-0.5">
                        Prompt: {getTravelerPromptForUnknownField(unk.field_name)}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Contradictions */}
      {contradictions.length > 0 && (
        <div>
          <h3 className="text-ui-base font-semibold text-[#f85149] mb-3">Contradictions</h3>
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
            <ul className="space-y-2">
              {contradictions.map((con, idx) => (
                <li key={`con-${con.field_name}`} className="flex items-start gap-2 py-1.5 border-b border-[#30363d] last:border-0">
                  <span className="text-[#f85149] shrink-0 mt-0.5 text-ui-sm font-bold">X</span>
                  <div>
                    <span className="text-ui-sm font-medium text-[#e6edf3]">
                      {labelOrTitle(FIELD_LABELS, con.field_name)}
                    </span>
                    <p className="text-ui-xs text-[#8b949e] mt-0.5">
                      Values: {con.values.map(_formatValue).join(" vs ")}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Raw JSON Toggle */}
      <div className="pt-2">
        <button
          type="button"
          onClick={() => setShowRawJson(!showRawJson)}
          className="flex items-center gap-1.5 text-ui-xs text-[#8b949e] hover:text-[#e6edf3] transition-colors"
        >
          {showRawJson ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
          {showRawJson ? "Hide" : "Show"} Technical Data
        </button>
        {showRawJson && (
          <div className="mt-2 p-4 bg-[#0f1115] border border-[#30363d] rounded-xl">
            <pre className="text-ui-xs font-mono text-[#8b949e] overflow-x-auto whitespace-pre-wrap break-all m-0">
              {JSON.stringify(bookingRequest, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

function _getFactValue(facts: Record<string, SlotValue>, field: string): unknown {
  const slot = facts[field];
  return slot?.value ?? null;
}

function _formatValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (Array.isArray(value)) {
    if (value.length === 0) return "-";
    return value.map(_formatValue).join(", ");
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    if (typeof record.text === "string") {
      const visibility = typeof record.visibility === "string"
        ? ` (${record.visibility.replace(/_/g, " ")})`
        : "";
      return `${record.text}${visibility}`;
    }

    const entries = Object.entries(record).filter(([, entryValue]) => entryValue !== undefined && entryValue !== null);
    if (entries.length === 0) return "-";

    return entries
      .map(([key, entryValue]) => `${labelOrTitle(FIELD_LABELS, key)}: ${_formatValue(entryValue)}`)
      .join("; ");
  }
  return String(value);
}

function _formatConfidence(confidence: number | undefined): string {
  if (confidence === undefined || confidence === null) return "-";
  return `${Math.round(confidence * 100)}%`;
}
