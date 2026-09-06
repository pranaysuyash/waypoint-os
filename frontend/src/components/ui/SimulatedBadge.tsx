import React from 'react';

/**
 * GM-01 honesty badge (frontend honesty batch, 2026-09-02).
 *
 * Single canonical visual marker for panels that render simulated/sample
 * content. Classes mirror the IMP-03 "Sample data" badge precedent in
 * RepeatTravelerRecallCard.tsx so every honesty marker looks identical.
 *
 * - `label="Sample data"` → content is a hardcoded frontend fixture.
 * - `label="Simulated"`   → content comes from a deterministic backend
 *   simulator (no external calls, holds, issuances, or transmissions).
 *
 * Never use this badge for real, live-wired surfaces.
 */
export interface SimulatedBadgeProps {
  label?: string;
}

export function SimulatedBadge({ label = 'Simulated' }: SimulatedBadgeProps) {
  return (
    <span
      data-testid='simulated-badge'
      className='inline-flex shrink-0 items-center px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 text-[10px] font-semibold uppercase tracking-wide border border-amber-500/30'
    >
      {label}
    </span>
  );
}

export default SimulatedBadge;
