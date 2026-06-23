'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { useTrip, useTrips } from '@/hooks/useTrips';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';

export default function SuppliersPage() {
  const { data: trips, isLoading } = useTrips({ view: 'workspace', limit: 100 });
  const [selectedTripId, setSelectedTripId] = useState<string>('');

  const tripOptions = useMemo(
    () => trips.map((trip) => ({ id: trip.id, label: formatTripPickerLabel(trip) })),
    [trips],
  );
  const selectedTripExists = trips.some((trip) => trip.id === selectedTripId);
  const effectiveSelectedTripId = selectedTripExists ? selectedTripId : trips[0]?.id ?? '';
  const { data: selectedTrip } = useTrip(effectiveSelectedTripId || null);
  const supplierRiskLevel = selectedTrip?.agentOperations?.supplierRiskLevel ?? selectedTrip?.agentOperations?.supplierRiskLevel ?? null;
  const supplierSnapshot = selectedTrip?.agentOperations?.supplierIntelligenceSnapshot ?? null;

  return (
    <div className='p-6 space-y-6'>
      <BackToOverviewLink />

      <div>
        <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Suppliers</h1>
        <p className='text-ui-sm text-[#8b949e] mt-1'>
          Canonical supplier intelligence and route-level context. No parallel supplier workflow.
        </p>
      </div>

      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <label htmlFor='suppliers-trip-select' className='block text-xs text-[#8b949e]'>
          Select trip
        </label>
        <select
          id='suppliers-trip-select'
          data-testid='suppliers-trip-select'
          value={effectiveSelectedTripId}
          onChange={(e) => setSelectedTripId(e.target.value)}
          className='w-full md:w-[420px] bg-[#0d1117] border border-[#30363d] rounded p-2 text-sm text-[#e6edf3]'
          disabled={isLoading || tripOptions.length === 0}
        >
          {tripOptions.length === 0 ? (
            <option value=''>No trips in planning</option>
          ) : (
            tripOptions.map((trip) => (
              <option key={trip.id} value={trip.id}>
                {trip.label}
              </option>
            ))
          )}
        </select>

        {effectiveSelectedTripId && (
          <div className='text-xs text-[#8b949e]'>
            Need the full trip context?{' '}
            <Link className='text-[#58a6ff] hover:text-[#79b8ff]' href={`/trips/${effectiveSelectedTripId}/ops`}>
              Open trip workspace
            </Link>
          </div>
        )}
      </div>

      <div className='grid gap-4 md:grid-cols-2'>
        <section className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-2'>
          <h2 className='text-sm font-semibold text-[#e6edf3]'>Supplier risk</h2>
          <p className='text-sm text-[#8b949e]'>
            {supplierRiskLevel ? `Current supplier risk: ${supplierRiskLevel}` : 'No supplier risk level recorded for this trip yet.'}
          </p>
        </section>

        <section className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-2'>
          <h2 className='text-sm font-semibold text-[#e6edf3]'>Supplier intelligence</h2>
          <p className='text-sm text-[#8b949e]'>
            {supplierSnapshot ? 'Supplier intelligence snapshot is available on the selected trip.' : 'No supplier intelligence snapshot stored for this trip yet.'}
          </p>
        </section>
      </div>

      {!selectedTrip && (
        <div className='text-sm text-[#8b949e]'>
          {isLoading ? 'Loading trips…' : 'No trip selected.'}
        </div>
      )}
    </div>
  );
}
