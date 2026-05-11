/**
 * /workspace/[tripId]/suitability/page.tsx
 *
 * Suitability review stage: operator reviews activity suitability concerns
 * and acknowledges critical flags before proceeding to send trip to customer.
 */

'use client';

import React, { useEffect, useReducer, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { SuitabilityPanel, type SuitabilityFlag } from '@/components/workspace/panels/SuitabilityPanel';

type SuitabilityPageState =
  | { status: 'loading'; flags: SuitabilityFlag[]; error: null }
  | { status: 'success'; flags: SuitabilityFlag[]; error: null }
  | { status: 'error'; flags: SuitabilityFlag[]; error: string };

type SuitabilityPageAction =
  | { type: 'loaded'; flags: SuitabilityFlag[] }
  | { type: 'failed'; error: string };

function suitabilityPageReducer(
  state: SuitabilityPageState,
  action: SuitabilityPageAction,
): SuitabilityPageState {
  switch (action.type) {
    case 'loaded':
      return { status: 'success', flags: action.flags, error: null };
    case 'failed':
      return { status: 'error', flags: state.flags, error: action.error };
    default:
      return state;
  }
}

export default function SuitabilityPage() {
  const { push } = useRouter();
  const params = useParams();
  const tripId = params.tripId as string;

  const [state, dispatch] = useReducer(suitabilityPageReducer, {
    status: 'loading',
    flags: [],
    error: null,
  });
  const { flags, error } = state;
  const acknowledgedFlagsRef = useRef<string[]>([]);
  const setAcknowledgedFlags = (flagIds: string[]) => { acknowledgedFlagsRef.current = flagIds; };

  useEffect(() => {
    // OK: fetch is run once on mount for suitability assessment
    const fetchTrip = async () => {
      try {
        // eslint-disable-next-line -- dynamic tripId param, auth via credentials: "include"
        const response = await fetch(`/api/trips/${tripId}`, {
          credentials: "include",
          cache: "no-store",
        });
        // cache: no-store ensures fresh trip data every render
        if (!response.ok) throw new Error('Failed to fetch trip');

        const trip = await response.json();

        // Convert suitability_flags to SuitabilityFlag format
        const formattedFlags: SuitabilityFlag[] = (
          trip.suitability_flags || []
        ).map((flag: any) => {
          return {
            flag_type: flag.flag_type,
            severity: flag.severity,
            reason: flag.reason,
            confidence: flag.confidence,
            details: flag.details,
            affected_travelers: flag.affected_travelers,
          };
        });

        dispatch({ type: 'loaded', flags: formattedFlags });
      } catch (err) {
        dispatch({ type: 'failed', error: err instanceof Error ? err.message : 'Unknown error' });
      }
    };

    fetchTrip();
  }, [tripId]);

  const handleAcknowledge = async (flagIds: string[]) => {
    try {
      // Submit acknowledgments to backend
      const response = await fetch(`/api/trips/${tripId}/suitability/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: "include",
        body: JSON.stringify({ acknowledged_flags: flagIds }),
      });

      if (!response.ok) throw new Error('Failed to submit acknowledgments');

      setAcknowledgedFlags(flagIds);

      // Redirect to packet/decision stage
      push(`/trips/${tripId}/packet`);
    } catch (err) {
      dispatch({ type: 'failed', error: err instanceof Error ? err.message : 'Failed to submit acknowledgments' });
    }
  };

  if (state.status === 'loading') {
    return <div className="p-4">Loading suitability assessment…</div>;
  }

  if (error) {
    return <div className="p-4 text-accent-red">Error: {error}</div>;
  }

  if (flags.length === 0) {
    // No flags, skip this stage
    return (
      <div className="p-4">
        <p className="text-text-secondary">No suitability concerns detected.</p>
        <button
          onClick={() => push(`/trips/${tripId}/packet`)}
          className="mt-4 px-4 py-2 bg-[rgba(var(--accent-blue-rgb)/0.30)] text-white rounded-lg hover:bg-[rgba(var(--accent-blue-rgb)/0.26)]"
        >
          Continue to Review Packet
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <SuitabilityPanel flags={flags} onAcknowledge={handleAcknowledge} />
    </div>
  );
}
