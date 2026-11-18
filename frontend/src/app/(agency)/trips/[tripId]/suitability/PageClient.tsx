/**
 * /workspace/[tripId]/suitability/page.tsx
 *
 * Suitability review stage: operator reviews activity suitability concerns
 * and acknowledges critical flags before proceeding to send trip to customer.
 */

'use client';

import React, { useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SuitabilityPanel, type SuitabilityFlag } from '@/components/workspace/panels/SuitabilityPanel';
import { useTripContext } from '@/contexts/TripContext';
import { api } from '@/lib/api-client';
import { getTripRoute } from '@/lib/routes';
import { InlineLoading } from '@/components/ui/loading';
import { InlineError } from '@/components/error-boundary';

export default function SuitabilityPage() {
  const { push } = useRouter();
  const { tripId, trip, isLoading, error: tripError, refetchTrip } = useTripContext();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const acknowledgedFlagsRef = useRef<string[]>([]);

  const flags: SuitabilityFlag[] = useMemo(() => {
    const rawFlags = ((trip as { suitability_flags?: Array<Record<string, unknown>> } | null)?.suitability_flags ?? []);
    return rawFlags.map((flag) => ({
      flag: String(flag.flag_type ?? ''),
      flag_type: String(flag.flag_type ?? ''),
      severity: String(flag.severity ?? 'medium') as SuitabilityFlag['severity'],
      reason: String(flag.reason ?? ''),
      confidence: typeof flag.confidence === 'number' ? flag.confidence : 0,
      details: flag.details && typeof flag.details === 'object' ? (flag.details as Record<string, unknown>) : undefined,
      affected_travelers: Array.isArray(flag.affected_travelers)
        ? flag.affected_travelers.map(String)
        : undefined,
    }));
  }, [trip]);

  const handleAcknowledge = async (flagIds: string[]) => {
    if (!tripId) return;
    setSubmitError(null);
    try {
      await api.post(`/api/trips/${tripId}/suitability/acknowledge`, {
        acknowledged_flags: flagIds,
      });
      acknowledgedFlagsRef.current = flagIds;
      refetchTrip();
      push(getTripRoute(tripId, 'packet'));
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit acknowledgments');
    }
  };

  if (isLoading && !trip) {
    return (
      <div className="p-6">
        <InlineLoading message="Loading suitability assessment…" />
      </div>
    );
  }

  const displayError = submitError || tripError?.message;
  if (displayError) {
    return (
      <div className="p-6">
        <InlineError title="Suitability assessment unavailable" message={displayError} />
      </div>
    );
  }

  if (flags.length === 0) {
    return (
      <div className="p-6">
        <p className="text-text-secondary">No suitability concerns detected.</p>
        <button
          type="button"
          onClick={() => push(getTripRoute(tripId, 'packet'))}
          className="mt-4 px-4 py-2 bg-[rgba(var(--accent-blue-rgb)/0.30)] text-white rounded-lg hover:bg-[rgba(var(--accent-blue-rgb)/0.26)]"
        >
          Continue to Trip Details
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl">
      <SuitabilityPanel flags={flags} onAcknowledge={handleAcknowledge} />
    </div>
  );
}
