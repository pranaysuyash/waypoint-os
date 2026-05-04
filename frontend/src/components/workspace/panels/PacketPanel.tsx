"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AlertTriangle, CheckCircle2, CloudSun, DollarSign, FileText, Plane, ShieldCheck } from "lucide-react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { AgentOperationsMetadata, Trip } from "@/lib/api-client";
import type { SlotValue, Ambiguity, PacketUnknown, PacketContradiction, ValidationReport } from "@/types/spine";
import { FIELD_LABELS, SIGNAL_LABELS, labelOrTitle } from "@/lib/label-maps";
import {
  formatBudgetDisplay,
  formatCustomerDisplay,
  formatDateWindowDisplay,
  formatInquiryReference,
  formatLeadTitle,
  formatPartySizeDisplay,
  hasCustomerName,
  readCustomerName,
} from "@/lib/lead-display";
import { getRequiredPlanningFields } from "@/lib/planning-status";

interface PacketPanelProps {
  tripId: string;
  trip?: Trip | null;
}

export function PacketPanel({ tripId, trip }: PacketPanelProps) {
  const router = useRouter();
  const [isRefreshingAgents, setIsRefreshingAgents] = useState(false);
  const [agentRefreshMessage, setAgentRefreshMessage] = useState<string | null>(null);
  const { result_packet, result_validation, debug_raw_json, setDebugRawJson } = useWorkbenchStore();
  const activePacket = result_packet || trip?.packet;
  const activeValidation = result_validation || (trip?.validation as ValidationReport | null);

  async function refreshAgentChecks() {
    setIsRefreshingAgents(true);
    setAgentRefreshMessage(null);
    try {
      const response = await fetch("/api/agents/runtime/run-once", { method: "POST" });
      if (!response.ok) {
        setAgentRefreshMessage("Agent refresh failed");
        return;
      }
      setAgentRefreshMessage("Agent checks refreshed");
      router.refresh();
    } catch {
      setAgentRefreshMessage("Agent refresh failed");
    } finally {
      setIsRefreshingAgents(false);
    }
  }

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
      {trip && (
        <AgentOperationsPanel
          operations={trip.agentOperations}
          isRefreshing={isRefreshingAgents}
          refreshMessage={agentRefreshMessage}
          onRefresh={refreshAgentChecks}
        />
      )}

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

function AgentOperationsPanel({
  operations,
  isRefreshing,
  refreshMessage,
  onRefresh,
}: {
  operations?: AgentOperationsMetadata;
  isRefreshing: boolean;
  refreshMessage: string | null;
  onRefresh: () => void;
}) {
  const cards = [
    {
      key: "documents",
      label: "Documents",
      icon: FileText,
      status: _readPacketStatus(operations?.documentReadinessChecklist, operations?.documentRiskLevel),
      nextAction: _readNextAction(operations?.documentReadinessChecklist),
      detail: _countDetail("Confirm", operations?.mustConfirmDocuments?.length),
    },
    {
      key: "destination",
      label: "Destination",
      icon: CloudSun,
      status: _readPacketStatus(operations?.destinationIntelligenceSnapshot, operations?.destinationRiskLevel),
      nextAction: _firstString(
        _readNextAction(operations?.destinationIntelligenceSnapshot),
        _countDetail("Recommendation", operations?.destinationIntelligenceRecommendations?.length)
      ),
      detail: _readEvidenceFreshness(operations?.destinationIntelligenceSnapshot),
    },
    {
      key: "weather",
      label: "Weather Pivot",
      icon: CloudSun,
      status: _readPacketStatus(operations?.weatherPivotPacket, operations?.weatherPivotRiskLevel),
      nextAction: _readNextAction(operations?.weatherPivotPacket),
      detail: _formatPacketListCount("Pivot", operations?.weatherPivotPacket, ["activity_pivots", "transfer_pivots", "recommendations"]),
    },
    {
      key: "feasibility",
      label: "Feasibility",
      icon: AlertTriangle,
      status: _readPacketStatus(operations?.constraintFeasibilityAssessment, operations?.feasibilityStatus),
      nextAction: _readNextAction(operations?.constraintFeasibilityAssessment),
      detail: _formatPacketListCount("Blocker", operations?.constraintFeasibilityAssessment, ["hard_blockers", "soft_constraints", "missing_facts"]),
    },
    {
      key: "proposal",
      label: "Proposal",
      icon: CheckCircle2,
      status: _readPacketStatus(operations?.proposalReadinessAssessment, operations?.proposalReadinessStatus),
      nextAction: _readNextAction(operations?.proposalReadinessAssessment),
      detail: _formatPacketListCount("Risk", operations?.proposalReadinessAssessment, ["unresolved_risks", "missing_elements"]),
    },
    {
      key: "booking",
      label: "Booking",
      icon: CheckCircle2,
      status: _readPacketStatus(operations?.bookingReadinessAssessment, operations?.bookingReadinessStatus),
      nextAction: _readNextAction(operations?.bookingReadinessAssessment),
      detail: _formatPacketListCount("Issue", operations?.bookingReadinessAssessment, ["missing_elements", "blocking_risks"]),
    },
    {
      key: "flight",
      label: "Flight Status",
      icon: Plane,
      status: _readPacketStatus(operations?.flightStatusSnapshot, operations?.flightDisruptionRiskLevel),
      nextAction: _readNextAction(operations?.flightStatusSnapshot),
      detail: _readEvidenceFreshness(operations?.flightStatusSnapshot),
    },
    {
      key: "price",
      label: "Price Watch",
      icon: DollarSign,
      status: _readPacketStatus(operations?.ticketPriceWatchAlert, operations?.priceWatchRiskLevel),
      nextAction: operations?.quoteRevalidationRequired ? "quote_revalidation_required" : _readNextAction(operations?.ticketPriceWatchAlert),
      detail: operations?.quoteRevalidationRequired ? "Revalidation required" : _readEvidenceFreshness(operations?.ticketPriceWatchAlert),
    },
    {
      key: "safety",
      label: "Safety",
      icon: ShieldCheck,
      status: _readPacketStatus(operations?.safetyAlertPacket, operations?.safetyRiskLevel),
      nextAction: _readNextAction(operations?.safetyAlertPacket),
      detail: _formatPacketListCount("Alert", operations?.safetyAlertPacket, ["alerts", "affected_travelers"]),
    },
    {
      key: "supplier",
      label: "Supplier / PNR",
      icon: AlertTriangle,
      status: _firstString(operations?.supplierRiskLevel, operations?.pnrShadowRiskLevel, _readPacketStatus(operations?.supplierIntelligenceSnapshot, undefined)),
      nextAction: _firstString(_readNextAction(operations?.supplierIntelligenceSnapshot), _readNextAction(operations?.pnrShadowCheck)),
      detail: _firstString(
        _formatPacketListCount("Supplier risk", operations?.supplierIntelligenceSnapshot, ["supplier_risks"]),
        _formatPacketListCount("PNR issue", operations?.pnrShadowCheck, ["issues"]),
        _countDetail("Canonical object", operations?.canonicalTravelObjects?.length)
      ),
    },
  ].filter((card) => card.status || card.nextAction || card.detail);

  return (
    <section className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-ui-lg font-semibold text-text-primary">Agent Operations</h2>
          <p className="mt-1 text-ui-sm text-text-muted">Live checks, readiness gates, and booking safeguards attached to this trip.</p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          {refreshMessage && <span className="text-ui-xs text-text-muted">{refreshMessage}</span>}
          <button
            type="button"
            className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated disabled:cursor-not-allowed disabled:opacity-60"
            onClick={onRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing..." : "Refresh Agent Checks"}
          </button>
        </div>
        {operations?.lastAgentAction && (
          <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] px-3 py-2 text-right">
            <div className="text-[10px] uppercase tracking-[0.16em] text-text-placeholder">Latest</div>
            <div className="mt-1 text-ui-xs font-medium text-text-primary">{_formatAgentName(operations.lastAgentAction)}</div>
            {operations?.lastAgentActionAt && <div className="mt-0.5 text-[11px] text-text-muted">{_formatDateTime(operations.lastAgentActionAt)}</div>}
          </div>
        )}
      </div>

      {cards.length > 0 ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {cards.map(({ key, label, icon: Icon, status, nextAction, detail }) => {
            const tone = _statusTone(status);
            return (
              <article key={key} className="rounded-lg border bg-[var(--bg-surface)] p-4" style={{ borderColor: tone.border }}>
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md" style={{ background: tone.background, color: tone.color }}>
                    <Icon size={17} aria-hidden="true" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="truncate text-ui-sm font-semibold text-text-primary">{label}</h3>
                      {status && (
                        <span className="shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ borderColor: tone.border, color: tone.color, background: tone.background }}>
                          {_formatStatus(status)}
                        </span>
                      )}
                    </div>
                    {nextAction && <p className="mt-2 text-ui-sm text-text-rationale">{_formatStatus(nextAction)}</p>}
                    {detail && <p className="mt-1 text-ui-xs text-text-muted">{detail}</p>}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="mt-4 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] px-4 py-3 text-ui-sm text-text-muted">
          No agent operation packets are attached yet.
        </div>
      )}
    </section>
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

  const knownDetails: Array<{ label: string; value: string; source: string; field: string }> = [
    { label: "Destination", value: requiredFields.includes("Destination") ? "Destination missing" : trip.destination || "Destination missing", source: trip.destination && !["Unknown","TBD",""].includes(trip.destination) ? "Manual" : "System", field: "destination" },
    { label: "Trip type", value: trip.type || "Trip type missing", source: trip.type ? "System" : "System", field: "type" },
    { label: "Party size", value: formatPartySizeDisplay(trip.party), source: trip.party && trip.party > 0 ? "Manual" : "System", field: "party" },
    { label: "Dates", value: formatDateWindowDisplay(trip.dateWindow), source: trip.dateWindow && !["TBD",""].includes(trip.dateWindow) ? "Manual" : "System", field: "dateWindow" },
    { label: "Budget", value: formatBudgetDisplay(trip.budget), source: trip.budget && formatBudgetDisplay(trip.budget) !== "Budget missing" ? "Manual" : "System", field: "budget" },
    { label: "Origin", value: requiredFields.includes("Origin city") ? "Origin missing" : trip.origin || "Origin missing", source: trip.origin && !["TBD","","patna"].includes(trip.origin) ? "Manual" : trip.origin === "patna" ? "Manual" : "System", field: "origin" },
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
            {knownDetails.map((detail) => {
              const isMissing = detail.value.includes("missing");
              const sourceColor = detail.source === "Manual" ? "#58a6ff" : "#8b949e";
              return (
                <div key={detail.label} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3">
                  <div className="flex items-center justify-between gap-2">
                    <dt className="text-[11px] uppercase tracking-[0.16em] text-text-placeholder">{detail.label}</dt>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ color: sourceColor, background: `${sourceColor}15`, border: `1px solid ${sourceColor}30` }}>
                      {detail.source}
                    </span>
                  </div>
                  <dd className="mt-1 text-ui-sm font-medium" style={{ color: isMissing ? '#d29922' : 'var(--text-primary)' }}>
                    {detail.value}
                  </dd>
                  <div className="mt-2 flex items-center gap-2">
                    <Link
                      href={`${intakeHref}?field=${detail.field}`}
                      className="text-[11px] font-medium hover:underline transition-colors"
                      style={{ color: 'var(--accent-blue)' }}
                    >
                      {isMissing ? `Add ${detail.label.toLowerCase()}` : 'Edit'}
                    </Link>
                  </div>
                </div>
              );
            })}
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-3">
              <dt className="text-[11px] uppercase tracking-[0.16em] text-text-placeholder">Inquiry Ref</dt>
              <dd className="mt-1 text-ui-sm font-medium text-text-primary">{formatInquiryReference(trip.id)}</dd>
            </div>
          </dl>
        </section>

        <aside className="rounded-xl border p-5 xl:col-span-5 space-y-4">
          {/* Trip details */}
          <div className="rounded-xl border border-[rgba(63,185,80,0.2)] bg-[rgba(63,185,80,0.04)] p-4">
            <h3 className="text-ui-sm font-semibold text-text-primary" style={{ color: '#3fb950' }}>Trip details</h3>
            {requiredFields.length > 0 ? (
              <>
                <p className="mt-2 text-ui-sm text-text-muted">{requiredFields.length} required field{requiredFields.length > 1 ? 's' : ''} missing</p>
                <ul className="mt-3 space-y-2">
                  {requiredFields.map((field) => (
                    <li key={field} className="rounded-lg border border-[rgba(248,81,73,0.18)] bg-[rgba(248,81,73,0.04)] px-3 py-2 text-ui-sm text-text-primary flex items-center justify-between">
                      <span>{field}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 flex flex-wrap gap-2">
                  {requiredFields.includes("Budget range") && (
                    <Link href={`${intakeHref}?field=budget`} className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated">Add budget</Link>
                  )}
                  {requiredFields.includes("Origin city") && (
                    <Link href={`${intakeHref}?field=origin`} className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated">Add origin</Link>
                  )}
                  {requiredFields.includes("Travel window") && (
                    <Link href={`${intakeHref}?field=dateWindow`} className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated">Add dates</Link>
                  )}
                  {requiredFields.includes("Traveler count") && (
                    <Link href={`${intakeHref}?field=party`} className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated">Add travelers</Link>
                  )}
                  <Link href={intakeHref} className="inline-flex items-center rounded-lg border border-[rgba(210,153,34,0.35)] bg-[rgba(210,153,34,0.12)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-[rgba(210,153,34,0.18)]">Go to missing details</Link>
                </div>
              </>
            ) : (
              <>
                <p className="mt-2 text-ui-sm text-text-primary">All required fields complete</p>
                <p className="mt-1 text-ui-xs text-text-muted">Trip details are ready for options.</p>
                <Link href={intakeHref} className="mt-4 inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated">Review captured details</Link>
              </>
            )}
          </div>

          {/* Contact details */}
          <div className="rounded-xl border p-4" style={{ borderColor: 'rgba(139,148,158,0.2)', background: 'rgba(139,148,158,0.03)' }}>
            <h3 className="text-ui-sm font-semibold text-text-muted">Contact details</h3>
            {hasCustomerName(trip.rawInput, trip.agentNotes, trip.contactName) ? (
              <>
                <p className="mt-2 text-ui-sm text-text-primary">{trip.contactName || readCustomerName(trip.agentNotes)}</p>
                <Link href={`${intakeHref}?field=customerName`} className="mt-2 inline-flex items-center text-[12px] font-medium hover:underline transition-colors" style={{ color: 'var(--accent-blue)' }}>Edit contact name</Link>
              </>
            ) : (
              <>
                <p className="mt-2 text-ui-sm text-text-muted">Contact name missing</p>
                <Link href={`${intakeHref}?field=customerName`} className="mt-3 inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-primary transition-colors hover:bg-elevated">Add contact name</Link>
              </>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

function _firstString(...values: Array<string | undefined | null>): string | undefined {
  return values.find((value): value is string => typeof value === "string" && value.length > 0);
}

function _readPacketStatus(packet: Record<string, unknown> | undefined, explicitStatus: string | undefined): string | undefined {
  return _firstString(
    explicitStatus,
    typeof packet?.risk_level === "string" ? packet.risk_level : undefined,
    typeof packet?.status === "string" ? packet.status : undefined,
    packet ? "present" : undefined
  );
}

function _readNextAction(packet: Record<string, unknown> | undefined): string | undefined {
  return typeof packet?.operator_next_action === "string" ? packet.operator_next_action : undefined;
}

function _readEvidenceFreshness(packet: Record<string, unknown> | undefined): string | undefined {
  const toolEvidence = packet?.tool_evidence;
  const evidence = typeof toolEvidence === "object" && toolEvidence !== null && !Array.isArray(toolEvidence)
    ? toolEvidence as Record<string, unknown>
    : undefined;
  const fresh = typeof evidence?.fresh === "boolean" ? evidence.fresh : undefined;
  const source = typeof evidence?.source === "string" ? evidence.source : undefined;
  const checkedAt = typeof packet?.checked_at === "string" ? packet.checked_at : undefined;

  if (fresh !== undefined && source) return `${fresh ? "Fresh" : "Stale"} evidence from ${source}`;
  if (fresh !== undefined) return fresh ? "Fresh evidence" : "Stale evidence";
  if (checkedAt) return `Checked ${_formatDateTime(checkedAt)}`;
  return undefined;
}

function _formatPacketListCount(label: string, packet: Record<string, unknown> | undefined, fields: string[]): string | undefined {
  if (!packet) return undefined;
  const count = fields.reduce((total, field) => {
    const value = packet[field];
    return total + (Array.isArray(value) ? value.length : 0);
  }, 0);
  return _countDetail(label, count);
}

function _countDetail(label: string, count: number | undefined): string | undefined {
  if (!count || count <= 0) return undefined;
  return `${count} ${label}${count === 1 ? "" : "s"}`;
}

function _formatStatus(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function _formatAgentName(value: string): string {
  return _formatStatus(value.replace(/_agent$/i, ""));
}

function _formatDateTime(value: string): string {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function _statusTone(value: string | undefined): { color: string; border: string; background: string } {
  const normalized = (value || "").toLowerCase();
  if (["high", "critical", "blocked", "hard", "unknown"].some((needle) => normalized.includes(needle))) {
    return { color: "#f85149", border: "rgba(248,81,73,0.28)", background: "rgba(248,81,73,0.08)" };
  }
  if (["medium", "review", "required", "stale", "soft"].some((needle) => normalized.includes(needle))) {
    return { color: "#d29922", border: "rgba(210,153,34,0.3)", background: "rgba(210,153,34,0.08)" };
  }
  if (["ready", "feasible", "low", "fresh", "complete"].some((needle) => normalized.includes(needle))) {
    return { color: "#3fb950", border: "rgba(63,185,80,0.26)", background: "rgba(63,185,80,0.08)" };
  }
  return { color: "#58a6ff", border: "rgba(88,166,255,0.25)", background: "rgba(88,166,255,0.08)" };
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
