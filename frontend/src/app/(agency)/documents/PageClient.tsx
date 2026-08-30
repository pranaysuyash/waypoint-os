'use client';

import { useMemo, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import OpsPanel from '../workbench/OpsPanel';
import { useTrip, useTrips } from '@/hooks/useTrips';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';

export default function DocumentsPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const urlTripId = searchParams.get('tripId') || searchParams.get('trip') || '';

  const { data: trips, isLoading } = useTrips({ view: 'workspace', limit: 100 });

  const tripOptions = useMemo(
    () => trips.map((trip) => ({ id: trip.id, label: formatTripPickerLabel(trip) })),
    [trips],
  );
  const selectedTripExists = trips.some((trip) => trip.id === urlTripId);
  const effectiveSelectedTripId = selectedTripExists ? urlTripId : trips[0]?.id ?? '';
  const { data: selectedTrip } = useTrip(effectiveSelectedTripId || null);

  const handleTripChange = useCallback(
    (newTripId: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (newTripId) {
        params.set('tripId', newTripId);
      } else {
        params.delete('tripId');
      }
      router.push(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

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
          onChange={(e) => handleTripChange(e.target.value)}
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

