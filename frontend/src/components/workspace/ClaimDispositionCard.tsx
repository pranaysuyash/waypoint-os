"use client";

import type { Trip } from "@/lib/api-client";

/**
 * ClaimDispositionCard — T10 (FND-0233, decided 2026-09-30).
 *
 * Parcel-tracking model for statutory passenger-rights claims: the operator
 * records what the airline actually did; the card shows where the claim
 * stands and what the airline ultimately paid the traveler directly.
 *
 * HARD BOUNDARY: this system never initiates, holds, or receives money —
 * the card is a scorecard, not a bank. All state changes are operator-entered
 * facts about the real world (PATCH /passenger-rights/.../disposition).
 */

const STATE_STEPS = ["SUBMITTED", "AIRLINE_REPLY", "TRAVELER_PAID", "CLOSED"] as const;

const STATE_LABELS: Record<string, string> = {
  DRAFTED: "Drafted",
  SUBMITTED: "Sent to airline",
  ESCALATED: "Escalated",
  AIRLINE_ACCEPTED: "Airline accepted",
  AIRLINE_PARTIAL: "Airline partial offer",
  AIRLINE_REJECTED: "Airline rejected",
  TRAVELER_PAID: "Traveler paid",
  CLOSED: "Closed",
};

const STATE_COLORS: Record<string, string> = {
  DRAFTED: "#9ca3af",
  SUBMITTED: "#3b82f6",
  ESCALATED: "#f59e0b",
  AIRLINE_ACCEPTED: "#22c55e",
  AIRLINE_PARTIAL: "#f59e0b",
  AIRLINE_REJECTED: "#ef4444",
  TRAVELER_PAID: "#22c55e",
  CLOSED: "#6b7280",
};

export function ClaimDispositionCard({ trip }: { trip: Trip | null | undefined }) {
  const claim = trip?.passenger_claim;
  const disposition = claim?.disposition;
  if (!claim?.claim_id || !disposition?.state) return null;

  const state = disposition.state;
  const color = STATE_COLORS[state] ?? "#9ca3af";
  const outcome = disposition.outcome;

  // Parcel-tracking progress: which of the four user-facing milestones is done.
  const milestoneIndex = (() => {
    if (state === "CLOSED" || state === "TRAVELER_PAID") return 3;
    if (state.startsWith("AIRLINE_")) return 2;
    if (state === "ESCALATED") return 1;
    return 0; // SUBMITTED / DRAFTED
  })();

  return (
    <section
      data-testid="claim-disposition-card"
      className="rounded-xl p-4 border"
      style={{ borderColor: `${color}55`, background: `${color}0d` }}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest" style={{ color }}>
          Passenger Rights Claim
        </div>
        {disposition.overdue && (
          <span className="text-[var(--ui-text-xs)] font-semibold text-accent-amber">
            ⏰ Awaiting airline reply — follow up
          </span>
        )}
      </div>

      <div className="text-ui-lg font-semibold text-text-primary mt-1" style={{ fontFamily: "'Outfit', sans-serif" }}>
        {STATE_LABELS[state] ?? state}
      </div>

      {/* Milestone track */}
      <div className="flex items-center gap-1.5 mt-3" aria-hidden>
        {STATE_STEPS.map((step, i) => (
          <div
            key={step}
            className="h-1.5 flex-1 rounded-full"
            style={{ background: i <= milestoneIndex ? color : "var(--border-default, #333)" }}
          />
        ))}
      </div>

      {outcome && (
        <div className="text-ui-sm text-text-muted mt-3">
          Airline paid traveler directly:{" "}
          {typeof outcome.amount_eur === "number" ? `€${outcome.amount_eur.toLocaleString()}` : "amount on file"}
          {outcome.channel ? ` · ${outcome.channel}` : ""}
          {outcome.date ? ` · ${outcome.date}` : ""}
        </div>
      )}

      <p className="text-ui-xs text-text-placeholder mt-2">
        The airline pays the traveler directly. This tracker records the outcome — it never moves money.
      </p>
    </section>
  );
}
