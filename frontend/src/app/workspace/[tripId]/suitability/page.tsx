/**
 * /workspace/[tripId]/suitability/page.tsx
 *
 * Suitability review stage: operator reviews activity suitability concerns
 * and acknowledges critical flags before proceeding to send trip to customer.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import SuitabilityPanel from '@/components/workspace/panels/SuitabilityPanel';
import type { SuitabilityFlag } from '@/components/workspace/panels/SuitabilityPanel';

export default function SuitabilityPage() {
  const router = useRouter();
  const params = useParams();
  const tripId = params.tripId as string;

  const [flags, setFlags] = useState<SuitabilityFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acknowledgedFlags, setAcknowledgedFlags] = useState<string[]>([]);

  useEffect(() => {
    // Fetch trip data including suitability flags
    const fetchTrip = async () => {
      try {
        const response = await fetch(`/api/trips/${tripId}`);
        if (!response.ok) throw new Error('Failed to fetch trip');

        const trip = await response.json();

        // Convert suitability_flags to SuitabilityFlag format
        const formattedFlags: SuitabilityFlag[] = (
          trip.suitability_flags || []
        ).map((flag: any) => ({
          flag_type: flag.flag_type,
          severity: flag.severity,
          reason: flag.reason,
          confidence: flag.confidence,
          details: flag.details,
          affected_travelers: flag.affected_travelers,
        }));

        setFlags(formattedFlags);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
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
        body: JSON.stringify({ acknowledged_flags: flagIds }),
      });

      if (!response.ok) throw new Error('Failed to submit acknowledgments');

      setAcknowledgedFlags(flagIds);

      // Redirect to packet/decision stage
      router.push(`/workspace/${tripId}/packet`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit acknowledgments');
    }
  };

  if (loading) {
    return <div className="p-4">Loading suitability assessment...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">Error: {error}</div>;
  }

  if (flags.length === 0) {
    // No flags, skip this stage
    return (
      <div className="p-4">
        <p className="text-gray-600">No suitability concerns detected.</p>
        <button
          onClick={() => router.push(`/workspace/${tripId}/packet`)}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
