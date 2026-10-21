"use client";

import type { Trip } from "@/lib/api-client";

/**
 * GhostConciergeCard — T11b (decided 2026-09-30).
 *
 * Shows the disruption monitor's real evaluation: overall trip health and
 * the DRAFTED interventions awaiting operator review. The monitor proposes;
 * it never sends anything and never moves money (ADR-008 §7 decision-support
 * rung). Rendered only when a real evaluation exists.
 */

const HEALTH_STYLES: Record<string, { color: string; label: string }> = {
  DISRUPTED: { color: "#ef4444", label: "Disruption detected" },
  DEGRADED: { color: "#f59e0b", label: "Trip degraded" },
  STABLE: { color: "#22c55e", label: "Stable" },
};

const SEVERITY_ORDER: Record<string, number> = { CRITICAL: 0, WARNING: 1, INFO: 2 };

export function GhostConciergeCard({ trip }: { trip: Trip | null | undefined }) {
  const gc = trip?.ghost_concierge;
  if (!gc?.overall_health || gc.overall_health === "STABLE") return null;

  const style = HEALTH_STYLES[gc.overall_health] ?? HEALTH_STYLES.DEGRADED;
  const interventions = [...(gc.drafted_interventions ?? [])].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3),
  );

  return (
    <section
      data-testid="ghost-concierge-card"
      className="rounded-xl p-4 border"
      style={{ borderColor: `${style.color}55`, background: `${style.color}0d` }}
    >
      <div className="text-[var(--ui-text-xs)] font-bold uppercase tracking-widest" style={{ color: style.color }}>
        Concierge Monitor — {style.label}
      </div>

      {interventions.length > 0 ? (
        <ul className="space-y-2 mt-2">
          {interventions.map((i, idx) => (
            <li key={`${i.action_type}-${idx}`} className="text-ui-sm text-text-primary">
              <span
                className="inline-block rounded px-1.5 py-0.5 text-[var(--ui-text-xs)] font-semibold mr-2"
                style={{ background: `${style.color}22`, color: style.color }}
              >
                {i.severity}
              </span>
              {i.summary}
              {i.recommended_action && (
                <div className="text-ui-xs text-text-muted mt-0.5">→ {i.recommended_action}</div>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-ui-sm text-text-muted mt-2">No intervention required.</p>
      )}

      <p className="text-ui-xs text-text-placeholder mt-2">
        Drafted for operator review — nothing is sent automatically.
        {gc.healer_note ? ` ${gc.healer_note}.` : ""}
      </p>
    </section>
  );
}
