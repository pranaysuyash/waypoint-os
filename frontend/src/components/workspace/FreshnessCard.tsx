"use client";

/**
 * FreshnessCard — approval-drift surface (register I-2 / F-14 family).
 *
 * Shows the agency's price-lock freshness picture (72h windows, rate drops)
 * and highlights entries for THIS trip when present. Data comes from the
 * existing price-lock sentinel via the BFF proxy; execution-side re-lock
 * stays gated by F-01/F-14 — this card is display + CTA only.
 */

import { useEffect, useState } from "react";
import { AlertTriangle, Clock, RefreshCw } from "lucide-react";

interface PriceLockOpportunity {
  trip_id: string;
  destination: string;
  supplier_name: string;
  original_net_rate_cents: number;
  current_net_rate_cents: number;
  potential_margin_gain_cents: number;
  margin_gain_pct: number;
  price_lock_expires_at: string;
  hours_remaining: number;
  is_expired: boolean;
}

function fmtCents(cents: number): string {
  return `$${(cents / 100).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function FreshnessCard({ tripId }: { tripId: string }) {
  const [opportunities, setOpportunities] = useState<PriceLockOpportunity[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/price-lock/opportunities", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`status ${response.status}`);
        }
        const data = await response.json();
        if (!cancelled) {
          setOpportunities(Array.isArray(data) ? data : (data.items ?? []));
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tripId]);

  if (error) return null; // freshness is additive — fail silent on the card
  if (opportunities === null) return null;

  const thisTrip = opportunities.filter((o) => o.trip_id === tripId);
  const expiredCount = thisTrip.filter((o) => o.is_expired).length;

  return (
    <div
      data-testid="freshness-card"
      className="mb-3 rounded-lg border border-[rgba(210,153,34,0.22)] bg-[rgba(210,153,34,0.06)] px-3 py-2"
    >
      <div className="flex items-center gap-2 text-[12px] font-medium text-[var(--text-secondary)]">
        <Clock className="size-3.5 shrink-0 text-[var(--accent-amber)]" aria-hidden="true" />
        Price-lock freshness
        {expiredCount > 0 && (
          <span className="inline-flex items-center gap-1 text-[#f85149]">
            <AlertTriangle className="size-3" aria-hidden="true" />
            {expiredCount} expired
          </span>
        )}
      </div>
      {thisTrip.length === 0 ? (
        <p className="mt-1 text-[var(--ui-text-xs)] text-[var(--text-muted)]">
          No price-lock windows recorded for this trip.
        </p>
      ) : (
        <ul className="mt-1 space-y-1">
          {thisTrip.map((o) => (
            <li key={`${o.trip_id}-${o.supplier_name}`} className="text-[var(--ui-text-xs)] text-[var(--text-secondary)]">
              {o.supplier_name}:{" "}
              {o.is_expired ? (
                <span className="text-[#f85149]">window expired</span>
              ) : (
                <span>
                  {Math.round(o.hours_remaining)}h remaining
                </span>
              )}
              {o.potential_margin_gain_cents > 0 && (
                <span className="text-[#3fb950]">
                  {" "}
                  · re-shop saves {fmtCents(o.potential_margin_gain_cents)}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
