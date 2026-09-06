"use client";

/**
 * LifecycleChip — derived lifecycle read-model chip (register N-4).
 *
 * Renders the single joined answer to "where is this trip?" from the six
 * backend vocabularies, plus blocker count and the next operator action.
 * Pure derivation via lib/trip-lifecycle — no fetching, no new backend calls.
 */

import { deriveTripLifecycle } from "@/lib/trip-lifecycle";
import type { Trip } from "@/lib/api-client";

const TONE_STYLES: Record<string, { color: string; bg: string; border: string }> = {
  neutral: { color: "#8b949e", bg: "rgba(139,148,158,0.08)", border: "rgba(139,148,158,0.22)" },
  info: { color: "#58a6ff", bg: "rgba(88,166,255,0.08)", border: "rgba(88,166,255,0.22)" },
  warn: { color: "#d29922", bg: "rgba(210,153,34,0.08)", border: "rgba(210,153,34,0.22)" },
  danger: { color: "#f85149", bg: "rgba(248,81,73,0.08)", border: "rgba(248,81,73,0.22)" },
  success: { color: "#3fb950", bg: "rgba(63,185,80,0.08)", border: "rgba(63,185,80,0.22)" },
};

export function LifecycleChip({ trip }: { trip: Trip }) {
  const derived = deriveTripLifecycle(trip);
  const tone = TONE_STYLES[derived.tone] ?? TONE_STYLES.neutral;

  const detailLines = [
    ...derived.blockers.map((b) => `• ${b.label}`),
    derived.nextActions.length ? `Next: ${derived.nextActions[0]}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-ui-xs font-bold"
      style={{ color: tone.color, background: tone.bg, border: `1px solid ${tone.border}` }}
      title={detailLines || derived.label}
      data-lifecycle-state={derived.state}
      data-blocker-count={derived.blockers.length}
    >
      <span
        className="size-1.5 rounded-full"
        style={{ background: tone.color, boxShadow: `0 0 4px ${tone.color}` }}
      />
      {derived.label}
      {derived.blockers.length > 0 && (
        <span
          className="ml-0.5 inline-flex items-center justify-center rounded-full text-[10px] font-bold leading-none px-1.5 py-0.5"
          style={{ background: tone.color, color: "#0d1117" }}
        >
          {derived.blockers.length}
        </span>
      )}
    </span>
  );
}
