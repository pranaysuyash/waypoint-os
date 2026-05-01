"use client";

import Link from "next/link";
import { useWorkbenchStore } from "@/stores/workbench";
import type { Trip } from "@/lib/api-client";
import type { SlotValue, Ambiguity, PacketUnknown, PacketContradiction, ValidationReport } from "@/types/spine";
import { FIELD_LABELS, SIGNAL_LABELS, labelOrTitle } from "@/lib/label-maps";
import {
  formatBudgetDisplay,
  formatCustomerDisplay,
  formatDateWindowDisplay,
  formatInquiryReference,
  formatLeadTitle,
  formatPartySizeDisplay,
} from "@/lib/lead-display";
import { getRequiredPlanningFields } from "@/lib/planning-status";

interface PacketPanelProps {
  tripId: string;
  trip?: Trip | null;
}

export function PacketPanel({ tripId, trip }: PacketPanelProps) {
  const { result_packet, result_validation, debug_raw_json, setDebugRawJson } = useWorkbenchStore();
  const activePacket = result_packet || trip?.packet;
  const activeValidation = result_validation || (trip?.validation as ValidationReport | null);

  if (!activePacket) {
    return <TripDetailsFallback tripId={tripId} trip={trip ?? null} />;
  }

  const bookingRequest = activePacket as Record<string, unknown>;
  const validation = activeValidation;

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

function TripDetailsFallback({ tripId, trip }: { tripId: string; trip: Trip | null }) {
  const requiredFields = getRequiredPlanningFields(trip);
  const intakeHref = `/trips/${tripId}/intake`;

  if (!trip) {
    return (
      <div className="space-y-4 rounded-xl border border-[rgba(210,153,34,0.25)] bg-[rgba(210,153,34,0.05)] p-6">
        <h2 className="text-ui-xl font-semibold text-text-primary">Trip details need customer input</h2>
        <p className="text-ui-sm text-text-muted">Confirm budget range and origin city before building options.</p>
        <Link
          href={intakeHref}
          className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
        >
          Go to missing details
        </Link>
      </div>
    );
  }

  const knownDetails = [
    { label: "Title", value: formatLeadTitle(trip.destination, trip.type) },
    { label: "Customer", value: formatCustomerDisplay(trip.rawInput) },
    {
      label: "Destination",
      value: requiredFields.includes("Destination") ? "Destination missing" : trip.destination || "Destination missing",
    },
    { label: "Trip type", value: trip.type || "Trip type missing" },
    { label: "Party size", value: formatPartySizeDisplay(trip.party) },
    { label: "Dates", value: formatDateWindowDisplay(trip.dateWindow) },
    {
      label: "Budget",
      value: formatBudgetDisplay(trip.budget),
    },
    {
      label: "Origin",
      value: requiredFields.includes("Origin city") ? "Origin missing" : trip.origin || "Origin missing",
    },
    { label: "Inquiry Ref", value: formatInquiryReference(trip.id) },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] p-5">
        <h2 className="text-ui-xl font-semibold text-text-primary">Trip Details</h2>
        <p className="mt-1 text-ui-sm text-text-muted">
          Review known customer details here. Add anything missing before building options.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-12">
        <section className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] p-5 xl:col-span-7">
          <h3 className="text-ui-sm font-semibold text-text-primary">Known details</h3>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            {knownDetails.map((detail) => (
              <div key={detail.label} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3">
                <dt className="text-[11px] uppercase tracking-[0.16em] text-text-placeholder">{detail.label}</dt>
                <dd className="mt-1 text-ui-sm font-medium text-text-primary">{detail.value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <aside className="rounded-xl border border-[rgba(210,153,34,0.25)] bg-[rgba(210,153,34,0.05)] p-5 xl:col-span-5">
          <h3 className="text-ui-sm font-semibold text-text-primary">Missing required details</h3>
          {requiredFields.length > 0 ? (
            <>
              <ul className="mt-4 space-y-3">
                {requiredFields.map((field) => (
                  <li key={field} className="rounded-xl border border-[rgba(248,81,73,0.18)] bg-[rgba(248,81,73,0.04)] px-3 py-2 text-ui-sm text-text-primary">
                    {field}
                  </li>
                ))}
              </ul>
              <div className="mt-5 flex flex-wrap gap-2">
                {requiredFields.includes("Budget range") && (
                  <Link
                    href={`${intakeHref}?field=budget`}
                    className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
                  >
                    Add budget
                  </Link>
                )}
                {requiredFields.includes("Destination") && (
                  <Link
                    href={`${intakeHref}?field=destination`}
                    className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
                  >
                    Add destination
                  </Link>
                )}
                {requiredFields.includes("Origin city") && (
                  <Link
                    href={`${intakeHref}?field=origin`}
                    className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
                  >
                    Add origin
                  </Link>
                )}
                {requiredFields.includes("Travel window") && (
                  <Link
                    href={`${intakeHref}?field=dateWindow`}
                    className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
                  >
                    Add dates
                  </Link>
                )}
                {requiredFields.includes("Traveler count") && (
                  <Link
                    href={`${intakeHref}?field=party`}
                    className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
                  >
                    Add travelers
                  </Link>
                )}
                <Link
                  href={intakeHref}
                  className="inline-flex items-center rounded-lg border border-[rgba(210,153,34,0.35)] bg-[rgba(210,153,34,0.12)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-[rgba(210,153,34,0.18)]"
                >
                  Go to missing details
                </Link>
              </div>
            </>
          ) : (
            <>
              <p className="mt-3 text-ui-sm font-medium text-text-primary">
                Required details complete
              </p>
              {trip?.decision?.soft_blockers?.some(s => s === 'incomplete_intake') ? (
                <p className="mt-2 text-ui-sm text-text-muted">
                  AI extraction may still be processing. Refresh or check recommended fields.
                </p>
              ) : (
                <p className="mt-2 text-ui-sm text-text-muted">
                  All required trip details are confirmed. Trip is ready for options.
                </p>
              )}
              <Link
                href={intakeHref}
                className="mt-5 inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated"
              >
                Review captured details
              </Link>
            </>
          )}
        </aside>
      </div>
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
