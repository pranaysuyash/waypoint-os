'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import OpsPanel from '@/app/(agency)/workbench/OpsPanel';
import { useTrip, useTrips } from '@/hooks/useTrips';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';

export default function DocumentsPage() {
  const { data: trips, isLoading } = useTrips({ view: 'workspace', limit: 100 });
  const [selectedTripId, setSelectedTripId] = useState<string>('');

  const tripOptions = useMemo(
    () => trips.map((trip) => ({ id: trip.id, label: `${trip.destination} (${trip.type})` })),
    [trips],
  );
  const selectedTripExists = trips.some((trip) => trip.id === selectedTripId);
  const effectiveSelectedTripId = selectedTripExists ? selectedTripId : trips[0]?.id ?? '';
  const { data: selectedTrip } = useTrip(effectiveSelectedTripId || null);

  return (
    <div className='p-6 space-y-6'>
      <BackToOverviewLink />
      <div>
        <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Documents</h1>
        <p className='text-ui-sm text-[#8b949e] mt-1'>
          Route-level shell over canonical document contracts. No parallel document workflow.
        </p>
      </div>

      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117]'>
        <label htmlFor='documents-trip-select' className='block text-xs text-[#8b949e] mb-2'>
          Select trip
        </label>
        <select
          id='documents-trip-select'
          data-testid='documents-trip-select'
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
          <div className='mt-3 text-xs text-[#8b949e]'>
            Need full context?{' '}
            <Link className='text-[#58a6ff] hover:text-[#79b8ff]' href={`/trips/${effectiveSelectedTripId}/intake`}>
              Open trip workspace
            </Link>
          </div>
        )}
      </div>

      {selectedTrip ? (
        <OpsPanel trip={selectedTrip} mode='documents' />
      ) : (
        <div className='text-sm text-[#8b949e]'>
          {isLoading ? 'Loading trips…' : 'No trip selected.'}
        </div>
      )}
    </div>
  );
}
