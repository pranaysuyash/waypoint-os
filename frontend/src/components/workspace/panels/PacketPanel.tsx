"use client";

import { useWorkbenchStore } from "@/stores/workbench";
import type { SlotValue, Ambiguity, PacketUnknown, PacketContradiction, ValidationReport } from "@/types/spine";
import { FIELD_LABELS, SIGNAL_LABELS, labelOrTitle } from "@/lib/label-maps";

interface PacketPanelProps {
  tripId: string;
}

export function PacketPanel({ tripId }: PacketPanelProps) {
  const { result_packet, result_validation, debug_raw_json, setDebugRawJson } = useWorkbenchStore();

  if (!result_packet) {
    return (
      <div className="p-4 text-ui-sm text-text-muted italic">
        No booking request data for trip {tripId}. Process a trip from the "Intake" section first.
      </div>
    );
  }

  const bookingRequest = result_packet as Record<string, unknown>;
  const validation = result_validation as ValidationReport | null;

  const facts = (bookingRequest.facts || {}) as Record<string, SlotValue>;
  const derivedSignals = (bookingRequest.derived_signals || {}) as Record<string, SlotValue>;
  const ambiguities = (bookingRequest.ambiguities || []) as Ambiguity[];
  const unknowns = (bookingRequest.unknowns || []) as PacketUnknown[];
  const contradictions = (bookingRequest.contradictions || []) as PacketContradiction[];

  const summaryData = {
    Destination: _getFactValue(facts, "destination_candidates") || "—",
    Origin: _getFactValue(facts, "origin_city") || "—",
    Dates: _getFactValue(facts, "date_window") || _getFactValue(facts, "date_start") || "—",
    Budget: _getFactValue(facts, "budget_raw_text") || "—",
    Party: _getFactValue(facts, "party_size") || "—",
  };

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {Object.entries(summaryData).map(([label, value]) => (
          <div key={label} className="bg-elevated p-3 rounded-xl border border-[var(--border-default)]">
            <div className="text-[var(--ui-text-xs)] font-bold text-text-placeholder uppercase tracking-widest mb-1">{label}</div>
            <div className="text-ui-sm font-semibold text-text-primary font-mono">{String(value)}</div>
          </div>
        ))}
      </div>

      {/* Facts Section */}
      <section>
        <h3 className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder mb-3">Extracted Information</h3>
        <div className="bg-[#0a0d11] rounded-lg border border-highlight overflow-hidden">
          <table className="w-full text-ui-sm text-left">
            <thead className="bg-elevated text-text-placeholder text-[var(--ui-text-xs)] uppercase tracking-widest">
              <tr>
                <th className="px-4 py-2">Field</th>
                <th className="px-4 py-2">Value</th>
                <th className="px-4 py-2">Confidence</th>
                <th className="px-4 py-2">Authority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1c2128]">
              {Object.entries(facts).map(([field, slot]) => (
                <tr key={`fact-${field}`} className="text-text-rationale">
                  <td className="px-4 py-2 text-ui-xs">{labelOrTitle(FIELD_LABELS, field)}</td>
                  <td className="px-4 py-2">{_formatValue(slot.value)}</td>
                  <td className="px-4 py-2 text-text-muted">{_formatConfidence(slot.confidence)}</td>
                  <td className="px-4 py-2 text-text-muted">{slot.authority_level || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Derived Signals */}
      {Object.keys(derivedSignals).length > 0 && (
        <section>
          <h3 className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-text-placeholder mb-3">Inferred Details</h3>
          <div className="bg-[#0a0d11] rounded-lg border border-highlight p-4 divide-y divide-[#1c2128]">
            {Object.entries(derivedSignals).map(([signal, slot]) => (
              <div key={`sig-${signal}`} className="flex justify-between py-2 text-ui-sm text-text-rationale">
                <span className="font-medium">{labelOrTitle(SIGNAL_LABELS, signal)}</span>
                <span className="text-text-muted text-ui-xs">{String(slot.value)} ({_formatConfidence(slot.confidence)})</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Validation/Ambiguities/Unknowns/Contradictions would follow the same pattern... */}

      <button
        type="button"
        className="text-ui-xs text-text-placeholder hover:text-text-muted underline"
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>

      {debug_raw_json && (
        <pre className="bg-rationale border border-[var(--border-default)] p-4 rounded-xl text-[var(--ui-text-xs)] font-mono text-text-muted overflow-x-auto leading-relaxed">
          {JSON.stringify(bookingRequest, null, 2)}
        </pre>
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
