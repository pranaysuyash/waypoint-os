"use client";

/**
 * OnFileMemoryCard — E-D slot 2 display surface (ADR-008 §7 row 4).
 *
 * Shows the traveler's on-file memory facts ("On file from <date>: <fact>")
 * for THIS trip's contact, with a purge affordance. Strictly display-only by
 * ratified contract: facts never render as confirmed trip data, never enter
 * the trip packet, and never satisfy a gate — the backend enforces that; this
 * card exists so the agency can see (and purge) what memory holds.
 *
 * Honesty styling: chips are labeled with observed dates and a
 * "not confirmed for this trip" note so memory is never mistaken for
 * traveler-stated trip data.
 */

import { useCallback, useEffect, useState } from "react";
import { Brain, Trash2 } from "lucide-react";

interface OnFileFact {
  field_name: string | null;
  value: string;
  observed_at: string;
  source: string; // "memory" (durable) | "memory:profile" (registry fallback)
}

interface OnFileResponse {
  ok: boolean;
  memory_found: boolean;
  customer_id: string | null;
  customer_name: string | null;
  facts: OnFileFact[];
}

function fmtObserved(iso: string): string {
  if (!iso) return "date unknown";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "date unknown";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function OnFileMemoryCard({ tripId }: { tripId: string }) {
  const [data, setData] = useState<OnFileResponse | null>(null);
  const [forgetting, setForgetting] = useState(false);

  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/customers/on-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tripId }),
        cache: "no-store",
      });
      if (!response.ok) return; // on-file memory is additive — fail silent
      const json = (await response.json()) as OnFileResponse;
      setData(json?.memory_found ? json : { ...json, facts: [] });
    } catch {
      // additive surface — fail silent
    }
  }, [tripId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await load();
      if (cancelled) return;
    })();
    return () => {
      cancelled = true;
    };
  }, [load]);

  if (!data || data.facts.length === 0) return null; // fail silent when nothing on file

  const forget = async () => {
    if (!data.customer_id) return;
    const confirmed = window.confirm(
      "Erase all on-file memory for this traveler? This cannot be undone and applies across trips for this agency."
    );
    if (!confirmed) return;
    setForgetting(true);
    try {
      const response = await fetch("/api/customers/forget", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customerId: data.customer_id }),
        cache: "no-store",
      });
      if (response.ok) {
        setData({ ...data, memory_found: false, facts: [] });
      }
    } catch {
      // keep chips visible on failure — never fake an erase
    } finally {
      setForgetting(false);
    }
  };

  return (
    <div
      data-testid="on-file-memory-card"
      className="mb-3 rounded-lg border border-[rgba(88,166,255,0.22)] bg-[rgba(88,166,255,0.06)] px-3 py-2"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-[12px] font-medium text-[var(--text-secondary)]">
          <Brain className="size-3.5 shrink-0 text-[var(--accent-blue)]" aria-hidden="true" />
          On file from memory
          {data.customer_name && (
            <span className="text-[var(--text-muted)]">· {data.customer_name}</span>
          )}
        </div>
        <button
          type="button"
          onClick={forget}
          disabled={forgetting}
          data-testid="on-file-forget-button"
          className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] text-[var(--text-muted)] hover:bg-[rgba(248,81,73,0.12)] hover:text-[#f85149] disabled:opacity-50"
          aria-label="Erase on-file memory for this traveler"
        >
          <Trash2 className="size-3" aria-hidden="true" />
          {forgetting ? "Erasing…" : "Forget"}
        </button>
      </div>
      <p className="mt-0.5 text-[11px] text-[var(--text-muted)]">
        Not confirmed for this trip — shown for context only.
      </p>
      <ul className="mt-1 space-y-1">
        {data.facts.map((fact, index) => (
          <li
            key={`${fact.field_name ?? "fact"}-${index}`}
            className="text-[var(--ui-text-xs)] text-[var(--text-secondary)]"
          >
            {fact.field_name && (
              <span className="text-[var(--text-muted)]">
                {fact.field_name.replace(/_/g, " ")}:{" "}
              </span>
            )}
            {fact.value}
            <span className="text-[var(--text-muted)]">
              {" "}
              · on file from {fmtObserved(fact.observed_at)}
              {fact.source === "memory:profile" ? " (profile)" : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
