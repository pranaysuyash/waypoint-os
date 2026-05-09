"use client";

import Link from "next/link";

interface PlanningStageGateProps {
  tripId: string;
  reason: string;
}

export function PlanningStageGate({ tripId, reason }: PlanningStageGateProps) {
  return (
    <div className="flex min-h-[440px] items-center justify-center p-6">
      <div className="w-full max-w-xl rounded-xl border border-[rgba(210,153,34,0.25)] bg-[rgba(210,153,34,0.05)] p-6">
        <p className="text-[12px] font-semibold uppercase tracking-[0.18em] text-[var(--accent-amber)]">
          Planning gate
        </p>
        <h2 className="mt-2 text-ui-xl font-semibold text-[var(--text-primary)]">
          Before building options
        </h2>
        <p className="mt-2 text-ui-sm text-[var(--text-secondary)]">{reason}</p>
        <Link
          href={`/trips/${tripId}/intake`}
          className="mt-5 inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-elevated)]"
        >
          Go to missing details
        </Link>
      </div>
    </div>
  );
}
