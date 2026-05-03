"use client";

import { useState } from "react";
import { transitionTripStage } from "@/lib/api-client";

interface StageAdvanceButtonProps {
  tripId: string;
  currentStage: string;
  targetStage: string;
  tierLabel: string;
}

export function StageAdvanceButton({
  tripId,
  currentStage,
  targetStage,
  tierLabel,
}: StageAdvanceButtonProps) {
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAdvance = async () => {
    setIsTransitioning(true);
    setError(null);
    try {
      const result = await transitionTripStage(
        tripId,
        targetStage,
        `Advanced from ${currentStage} to ${targetStage}`,
        currentStage,
      );
      if (result.changed) {
        // Refresh to pick up the new stage from the server
        window.location.reload();
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to advance stage";
      setError(message);
      setIsTransitioning(false);
    }
  };

  return (
    <span className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={handleAdvance}
        disabled={isTransitioning}
        className="inline-flex items-center rounded-lg bg-accent-blue px-3 py-1.5 text-[var(--ui-text-xs)] font-semibold text-white transition-colors hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed"
        data-testid="stage-advance-btn"
      >
        {isTransitioning ? "Advancing…" : `Advance to ${tierLabel}`}
      </button>
      {error && (
        <span className="text-[var(--ui-text-xs)] text-accent-red">{error}</span>
      )}
    </span>
  );
}
