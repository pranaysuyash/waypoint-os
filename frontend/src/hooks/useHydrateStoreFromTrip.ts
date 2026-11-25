'use client';

/**
 * useHydrateStoreFromTrip - one-way trip -> workbench store hydration
 *
 * Extracted verbatim from PageClient.tsx (council decision
 * Docs/architecture/WORKBENCH_MODULARIZATION_COUNCIL_DECISION_2026-09-12.md,
 * slice T1.2). Body is intentionally byte-identical to its origin.
 */
import { useEffect, useRef } from 'react';
import type { Trip } from '@/lib/api-client';
import { useWorkbenchStore } from '@/stores/workbench';
import { normalizeSafetyResult } from '@/lib/bff-trip-adapters';

export function useHydrateStoreFromTrip(trip: Trip | null | undefined) {
  const {
    setResultPacket,
    setResultValidation,
    setResultDecision,
    setResultStrategy,
    setResultInternalBundle,
    setResultTravelerBundle,
    setResultSafety,
    setResultFees,
    setResultFrontier,
  } = useWorkbenchStore();
  const hydratedRef = useRef<{ tripId: string; runId?: string } | null>(null);

  useEffect(() => {
    if (!trip?.id) return;
    const sameTrip = hydratedRef.current?.tripId === trip.id;
    if (sameTrip && hydratedRef.current?.runId === trip.runId) return;
    hydratedRef.current = { tripId: trip.id, runId: trip.runId };

    // Always overwrite from current trip (prevent stale cross-trip data)
    setResultPacket(trip.packet ?? null);
    setResultValidation(trip.validation ?? null);
    setResultDecision(trip.decision ?? null);
    setResultStrategy(trip.strategy ?? null);
    setResultInternalBundle(trip.internal_bundle ?? null);
    setResultTravelerBundle(trip.traveler_bundle ?? null);
    setResultSafety(normalizeSafetyResult(trip.safety));
    setResultFees(trip.fees ?? null);
    setResultFrontier(trip.frontier_result ?? null);
    // Refresh outputs for a new run without replacing an open editor.
    if (sameTrip) return;
    useWorkbenchStore.setState({
      input_raw_note: trip.customerMessage ?? '',
      input_owner_note: trip.agentNotes ?? '',
      save_state: 'clean',
    });
  }, [
    trip,
    setResultPacket,
    setResultValidation,
    setResultDecision,
    setResultStrategy,
    setResultInternalBundle,
    setResultTravelerBundle,
    setResultSafety,
    setResultFees,
    setResultFrontier,
  ]);
}
