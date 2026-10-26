"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getFareDropDisposition,
  updateFareDropDisposition,
  type FareDropDisposition,
  type FareDropDispositionState,
  type FareDropOptions,
  type FareDropSignal,
  type FareDropTravelerDraft,
  type Trip,
} from "@/lib/api-client";

/**
 * FareDropDecisionCard — exploration topic 49 (2026-10-21).
 *
 * A booked trip's fare dropped below what the client paid. The practitioner
 * playbook (r/travelagents, top thread of the year) is: tell the client, frame
 * it as good news, and offer two ways to take advantage — a refund at the
 * lower fare, or an upgrade worth the difference. This card puts both options
 * in front of the advisor with the numbers, and records which they chose.
 *
 * HARD BOUNDARY: the system never reprices, never contacts the supplier, never
 * moves money. The advisor does those things and records the outcome here.
 * All transitions go through PATCH /price-lock/{trip}/fare-drop/disposition,
 * which rejects illegal steps with 409.
 */

const STATE_LABELS: Record<string, string> = {
  DETECTED: "Fare drop detected",
  PRESENTED: "Options presented to client",
  REPRICED: "Client chose the refund",
  UPGRADED: "Client chose the upgrade",
  DEFERRED: "Deferred",
  DISMISSED: "Dismissed",
  CLOSED: "Closed",
};

const STATE_COLORS: Record<string, string> = {
  DETECTED: "#f59e0b",
  PRESENTED: "#3b82f6",
  REPRICED: "#22c55e",
  UPGRADED: "#22c55e",
  DEFERRED: "#9ca3af",
  DISMISSED: "#6b7280",
  CLOSED: "#6b7280",
};

// Legal next steps per state — mirrors spine_api/services/fare_drop_disposition.py.
// Kept here only to decide which buttons to render; the server remains the authority.
const NEXT_STEPS: Record<string, FareDropDispositionState[]> = {
  DETECTED: ["PRESENTED", "DISMISSED"],
  PRESENTED: ["REPRICED", "UPGRADED", "DEFERRED", "DISMISSED"],
  DEFERRED: ["PRESENTED", "CLOSED"],
  REPRICED: ["CLOSED"],
  UPGRADED: ["CLOSED"],
  DISMISSED: ["CLOSED"],
  CLOSED: [],
};

const ACTION_LABELS: Record<FareDropDispositionState, string> = {
  DETECTED: "Fare drop detected",
  PRESENTED: "Mark presented to client",
  REPRICED: "Record: client took the refund",
  UPGRADED: "Record: client took the upgrade",
  DEFERRED: "Defer",
  DISMISSED: "Dismiss",
  CLOSED: "Close",
};

function formatMoney(amount: number | null | undefined, currency?: string | null): string {
  if (typeof amount !== "number" || !Number.isFinite(amount)) return "—";
  const code = (currency || "").toUpperCase();
  try {
    if (code) {
      // Keep cents when the amount has them — the draft text and the backend
      // both do, and one fact must not show two different numbers.
      return new Intl.NumberFormat(undefined, { style: "currency", currency: code, maximumFractionDigits: 2 }).format(amount);
    }
  } catch {
    // Unknown ISO code — fall through to a plain number.
  }
  return `${amount.toLocaleString()}${code ? ` ${code}` : ""}`;
}

function formatSigned(amount: number | null | undefined, currency?: string | null): string {
  if (typeof amount !== "number" || !Number.isFinite(amount)) return "—";
  const sign = amount > 0 ? "+" : amount < 0 ? "−" : "";
  return `${sign}${formatMoney(Math.abs(amount), currency)}`;
}

function relativeAge(iso?: string): string | null {
  if (!iso) return null;
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return null;
  const minutes = Math.max(0, Math.round((Date.now() - then) / 60_000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export interface FareDropDecisionCardProps {
  trip: Trip | null | undefined;
  /** Called after a successful transition so the owner can refetch the trip. */
  onUpdated?: () => void;
}

export function FareDropDecisionCard({ trip, onUpdated }: FareDropDecisionCardProps) {
  const tripId = trip?.id;
  const signalFromTrip = trip?.fare_drop_signal ?? null;

  const [signal, setSignal] = useState<FareDropSignal | null>(signalFromTrip);
  const [disposition, setDisposition] = useState<FareDropDisposition | null>(trip?.fare_drop_disposition ?? null);
  const [options, setOptions] = useState<FareDropOptions | null>(null);
  const [optionsReason, setOptionsReason] = useState<string | null>(null);
  const [draft, setDraft] = useState<FareDropTravelerDraft | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [busy, setBusy] = useState<FareDropDispositionState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [supplierReference, setSupplierReference] = useState<string>("");

  const load = useCallback(async () => {
    if (!tripId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getFareDropDisposition(tripId);
      setSignal(res?.signal ?? null);
      setDisposition(res?.disposition ?? null);
      setOptions(res?.options ?? null);
      setOptionsReason(res?.options_unavailable_reason ?? null);
      setDraft(res?.traveler_draft ?? null);
    } catch (err) {
      setOptions(null);
      setDraft(null);
      setOptionsReason(err instanceof Error ? err.message : "Could not load fare-drop options");
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    if (signalFromTrip?.detection_marker) {
    // eslint-disable-next-line react-hooks/set-state-in-effect
      void load();
    }
  }, [load, signalFromTrip?.detection_marker]);

  const state = disposition?.state ?? "DETECTED";
  const color = STATE_COLORS[state] ?? "#9ca3af";
  const nextSteps = useMemo(() => NEXT_STEPS[state] ?? [], [state]);
  const currency = signal?.booked_currency ?? signal?.current_currency ?? null;
  const isEstimate = options?.basis === "estimate";

  const transition = useCallback(
    async (newState: FareDropDispositionState) => {
      if (!tripId || !signal) return;
      setBusy(newState);
      setError(null);
      const needsOutcome = newState === "REPRICED" || newState === "UPGRADED";
      const outcome = needsOutcome
        ? {
            option: newState === "REPRICED" ? "reprice" : "upgrade",
            client_delta:
              newState === "REPRICED" ? -(options?.reprice.client_saving ?? signal.drop_amount ?? 0) : 0,
            supplier_reference: supplierReference.trim() || undefined,
            executed_by: "operator",
          }
        : undefined;
      try {
        const res = await updateFareDropDisposition(tripId, {
          new_state: newState,
          note: ACTION_LABELS[newState],
          outcome,
          expected_state: state,
          idempotency_key: `${tripId}:${signal.detection_marker ?? "signal"}:${newState}:${Date.now()}`,
        });
        setDisposition(res?.disposition ?? null);
        setOptions(res?.options ?? null);
        setOptionsReason(res?.options_unavailable_reason ?? null);
        setDraft(res?.traveler_draft ?? null);
        onUpdated?.();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not record the decision");
      } finally {
        setBusy(null);
      }
    },
    [tripId, signal, state, options, supplierReference, onUpdated],
  );

  if (!signal?.detection_marker) return null;

  const hasVerifiedNumbers = Boolean(options) && typeof signal.current_price === "number";
  const observedAgo = relativeAge(signal.checked_at);

  return (
    <section
      data-testid="fare-drop-decision-card"
      className="rounded-xl p-4 border mb-4"
      style={{ borderColor: `${color}55`, background: `${color}0d` }}
      aria-labelledby="fare-drop-card-title"
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div id="fare-drop-card-title" className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest" style={{ color }}>
          Fare drop after booking
        </div>
        <div className="flex items-center gap-2 text-[var(--ui-text-xs)] text-text-muted">
          {signal.severity && <span data-testid="fare-drop-severity">severity: {signal.severity}</span>}
          {observedAgo && <span>observed {observedAgo}</span>}
        </div>
      </div>

      <div className="text-ui-lg font-semibold text-text-primary mt-1" style={{ fontFamily: "'Outfit', sans-serif" }}>
        {STATE_LABELS[state] ?? state}
      </div>

      <div className="grid grid-cols-3 gap-3 mt-3 text-ui-sm">
        <div>
          <div className="text-text-placeholder text-ui-xs">Client paid</div>
          <div className="text-text-primary font-medium" data-testid="fare-drop-booked">
            {formatMoney(signal.booked_price, currency)}
          </div>
        </div>
        <div>
          <div className="text-text-placeholder text-ui-xs">Fare now</div>
          <div className="text-text-primary font-medium" data-testid="fare-drop-current">
            {typeof signal.current_price === "number" ? formatMoney(signal.current_price, currency) : "unverified"}
          </div>
        </div>
        <div>
          <div className="text-text-placeholder text-ui-xs">Drop</div>
          <div className="font-medium" style={{ color }} data-testid="fare-drop-amount">
            {typeof signal.drop_amount === "number" ? formatMoney(signal.drop_amount, currency) : "—"}
            {typeof signal.drop_percent === "number" ? ` (${Math.abs(signal.drop_percent)}%)` : ""}
          </div>
        </div>
      </div>

      {/* The two practitioner options, side by side, with the commission basis badge. */}
      {loading && !options ? (
        <p className="text-ui-xs text-text-placeholder mt-3">Computing options…</p>
      ) : hasVerifiedNumbers && options ? (
        <div className="grid grid-cols-2 gap-3 mt-3" data-testid="fare-drop-options">
          <div className="rounded-lg border border-border-default p-3">
            <div className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted">Option A · Refund</div>
            <div className="text-ui-sm text-text-primary mt-1">
              Client saves <strong data-testid="fare-drop-client-saving">{formatMoney(options.reprice.client_saving, currency)}</strong>
            </div>
            <div className="text-ui-xs text-text-muted mt-1">
              Your commission: <span data-testid="fare-drop-reprice-commission">{formatSigned(options.reprice.commission_delta, currency)}</span>
            </div>
          </div>
          <div className="rounded-lg border border-border-default p-3">
            <div className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted">Option B · Upgrade</div>
            <div className="text-ui-sm text-text-primary mt-1">
              Upgrade budget <strong data-testid="fare-drop-upgrade-budget">{formatMoney(options.upgrade.upgrade_budget, currency)}</strong>
            </div>
            <div className="text-ui-xs text-text-muted mt-1">
              Your commission: <span data-testid="fare-drop-upgrade-commission">{formatSigned(options.upgrade.commission_delta, currency)}</span> (preserved)
            </div>
          </div>
          <div className="col-span-2 text-ui-xs text-text-placeholder">
            <span
              data-testid="fare-drop-basis"
              className="inline-block rounded px-1.5 py-0.5 border mr-2"
              style={{ borderColor: isEstimate ? "#f59e0b" : "#22c55e", color: isEstimate ? "#f59e0b" : "#22c55e" }}
            >
              {isEstimate ? "commission: estimate" : "commission: on file"}
            </span>
            {Math.round(options.commission.pct * 100)}% · {options.commission.source}
          </div>
        </div>
      ) : (
        <p className="text-ui-xs text-text-muted mt-3" data-testid="fare-drop-options-unavailable">
          Options not shown: {optionsReason ?? "current fare could not be verified"}.
        </p>
      )}

      {nextSteps.length > 0 && (
        <div className="mt-3">
          {draft && state !== "CLOSED" && (
            <div className="mb-3" data-testid="fare-drop-draft">
              <div className="flex items-center justify-between gap-2">
                <div className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted">
                  Message to client · draft, not sent
                </div>
                <button
                  type="button"
                  data-testid="fare-drop-copy-draft"
                  className="text-ui-xs underline text-text-muted hover:text-text-primary"
                  onClick={() => {
                    void navigator.clipboard?.writeText(draft.body).then(() => {
                      setCopied(true);
                      window.setTimeout(() => setCopied(false), 2000);
                    });
                  }}
                >
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
              <textarea
                readOnly
                aria-label="Draft message to client"
                className="mt-1 w-full rounded border border-border-default bg-transparent px-2 py-1 text-ui-xs text-text-primary"
                rows={6}
                value={draft.body}
              />
            </div>
          )}
          {nextSteps.some((s) => s === "REPRICED" || s === "UPGRADED") && (
            <label className="block text-ui-xs text-text-muted mb-2">
              Supplier reference (optional)
              <input
                data-testid="fare-drop-supplier-reference"
                className="mt-1 w-full rounded border border-border-default bg-transparent px-2 py-1 text-ui-sm text-text-primary"
                value={supplierReference}
                onChange={(e) => setSupplierReference(e.target.value)}
                placeholder="e.g. reissue / upgrade confirmation"
              />
            </label>
          )}
          <div className="flex flex-wrap gap-2">
            {nextSteps.map((step) => (
              <button
                key={step}
                type="button"
                data-testid={`fare-drop-action-${step.toLowerCase()}`}
                aria-label={ACTION_LABELS[step]}
                disabled={busy !== null}
                onClick={() => void transition(step)}
                className="rounded-md border border-border-default px-3 py-1.5 text-ui-xs font-medium text-text-primary hover:bg-[var(--surface-hover,rgba(255,255,255,0.04))] disabled:opacity-50"
              >
                {busy === step ? "Recording…" : ACTION_LABELS[step]}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <p role="alert" className="text-ui-xs text-accent-red mt-2" data-testid="fare-drop-error">
          {error}
        </p>
      )}

      {disposition?.outcome && (
        <div className="text-ui-sm text-text-muted mt-3" data-testid="fare-drop-outcome">
          Recorded: {disposition.outcome.option === "reprice" ? "refund" : disposition.outcome.option}
          {disposition.outcome.supplier_reference ? ` · ref ${disposition.outcome.supplier_reference}` : ""}
          {disposition.outcome.recorded_at ? ` · ${disposition.outcome.recorded_at.slice(0, 10)}` : ""}
        </div>
      )}

      <p className="text-ui-xs text-text-placeholder mt-2">
        You tell the client and work with the supplier. This card records the decision — it never reprices or moves money.
      </p>
    </section>
  );
}
