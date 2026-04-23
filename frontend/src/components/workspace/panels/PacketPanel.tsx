"use client";

import { useWorkbenchStore } from "@/stores/workbench";
import type { SlotValue, Ambiguity, PacketUnknown, PacketContradiction, ValidationReport } from "@/types/spine";

interface PacketPanelProps {
  tripId: string;
}

export function PacketPanel({ tripId }: PacketPanelProps) {
  const { result_packet, result_validation, debug_raw_json, setDebugRawJson } = useWorkbenchStore();

  if (!result_packet) {
    return (
      <div className="p-4 text-sm text-gray-500 italic">
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
          <div key={label} className="bg-[#0a0d11] p-3 rounded-lg border border-[#1c2128]">
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{label}</div>
            <div className="text-sm font-medium text-gray-200 mt-1">{String(value)}</div>
          </div>
        ))}
      </div>

      {/* Facts Section */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Extracted Information</h3>
        <div className="bg-[#0a0d11] rounded-lg border border-[#1c2128] overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-[#161b22] text-gray-400 text-[10px] uppercase">
              <tr>
                <th className="px-4 py-2">Field</th>
                <th className="px-4 py-2">Value</th>
                <th className="px-4 py-2">Confidence</th>
                <th className="px-4 py-2">Authority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1c2128]">
              {Object.entries(facts).map(([field, slot]) => (
                <tr key={`fact-${field}`} className="text-gray-300">
                  <td className="px-4 py-2 font-mono text-xs">{field}</td>
                  <td className="px-4 py-2">{_formatValue(slot.value)}</td>
                  <td className="px-4 py-2 text-gray-500">{_formatConfidence(slot.confidence)}</td>
                  <td className="px-4 py-2 text-gray-500">{slot.authority_level || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Derived Signals */}
      {Object.keys(derivedSignals).length > 0 && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Inferred Details</h3>
          <div className="bg-[#0a0d11] rounded-lg border border-[#1c2128] p-4 divide-y divide-[#1c2128]">
            {Object.entries(derivedSignals).map(([signal, slot]) => (
              <div key={`sig-${signal}`} className="flex justify-between py-2 text-sm text-gray-300">
                <span className="font-medium">{signal}</span>
                <span className="text-gray-500 text-xs">{String(slot.value)} ({_formatConfidence(slot.confidence)})</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Validation/Ambiguities/Unknowns/Contradictions would follow the same pattern... */}

      <button
        type="button"
        className="text-xs text-blue-400 hover:text-blue-300 underline"
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>

      {debug_raw_json && (
        <pre className="bg-[#0a0d11] p-4 rounded text-xs font-mono text-gray-400 overflow-x-auto">
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
