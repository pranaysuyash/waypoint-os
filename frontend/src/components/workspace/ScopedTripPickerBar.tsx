'use client';

import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Search } from 'lucide-react';
import { useTrips } from '@/hooks/useTrips';
import type { Trip } from '@/lib/api-client';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';

export interface ScopedTripPickerBarProps {
  /** Visible uppercase label preceding the scope switch & selector */
  label: string;
  /** DOM id & htmlFor for the trip <select> */
  selectId: string;
  /** data-testid for the trip <select> */
  selectTestId: string;
  /** Label for the narrow scope button (e.g. "Documents & Upload-Ready") */
  scopedLabel: string;
  /** Label for the full workspace scope button */
  allLabel: string;
  /** Backend `GET /trips?scope=` value for the primary view */
  scope: 'documents' | 'suppliers';
  /** Externally requested trip ID (e.g. from ?tripId= query param) */
  requestedTripId?: string;
  /** Currently active trip ID in parent state */
  selectedTripId: string;
  /** Callback when active trip selection changes */
  onSelectTrip: (tripId: string, trip: Trip | undefined) => void;
  /** Optional search box placeholder */
  searchPlaceholder?: string;
  /** Optional muted note under the selector */
  helperText?: string;
}

/**
 * Shared searchable & scoped trip context selector for Operations surfaces.
 * Uses canonical `GET /trips` (`scope` + `q`) with automatic fallback to full workspace
 * when a narrow scope is empty (without overriding explicit search queries).
 */
export function ScopedTripPickerBar({
  label,
  selectId,
  selectTestId,
  scopedLabel,
  allLabel,
  scope,
  requestedTripId,
  selectedTripId,
  onSelectTrip,
  searchPlaceholder = 'Search destination or trip ref…',
  helperText,
}: ScopedTripPickerBarProps) {
  const searchInputId = useId();
  const [pickerScope, setPickerScope] = useState<'scoped' | 'all'>('scoped');
  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchInput.trim()), 250);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const {
    data: scopedTripsRaw,
    total: scopedTotal,
    isLoading: scopedLoading,
  } = useTrips({
    view: 'workspace',
    scope,
    limit: 100,
    q: debouncedSearch || undefined,
    enabled: pickerScope === 'scoped',
  });

  const scopedTrips = useMemo(() => scopedTripsRaw ?? [], [scopedTripsRaw]);

  const shouldLoadFallbackAll =
    pickerScope === 'all' || (!scopedLoading && scopedTrips.length === 0 && !debouncedSearch);

  const {
    data: allTripsRaw,
    total: allTotal,
    isLoading: allLoading,
  } = useTrips({
    view: 'workspace',
    limit: 100,
    q: debouncedSearch || undefined,
    enabled: shouldLoadFallbackAll,
  });

  const allTrips = useMemo(() => allTripsRaw ?? [], [allTripsRaw]);

  const usingFallbackAll =
    pickerScope === 'scoped' && !scopedLoading && scopedTrips.length === 0 && !debouncedSearch;

  const trips = pickerScope === 'all' || usingFallbackAll ? allTrips : scopedTrips;
  const isLoading = pickerScope === 'all' || usingFallbackAll ? allLoading : scopedLoading;

  const tripOptions = useMemo(() => {
    if (!requestedTripId) return trips;
    if (trips.some((t) => t.id === requestedTripId)) return trips;
    const fallbackTrip = {
      id: requestedTripId,
      title: `Selected trip · ${requestedTripId.slice(-4).toUpperCase()}`,
      destination: '',
      type: 'custom',
      state: 'blue',
      age: '',
      updated_at: '',
      status: 'assigned',
    } as unknown as Trip;
    return [fallbackTrip, ...trips];
  }, [trips, requestedTripId]);

  const effectiveSelectedTripId = useMemo(() => {
    if (selectedTripId && (tripOptions.some((t) => t.id === selectedTripId) || selectedTripId === requestedTripId)) {
      return selectedTripId;
    }
    if (requestedTripId) return requestedTripId;
    return tripOptions[0]?.id ?? '';
  }, [requestedTripId, selectedTripId, tripOptions]);

  const effectiveTrip = useMemo(
    () => tripOptions.find((t) => t.id === effectiveSelectedTripId),
    [tripOptions, effectiveSelectedTripId]
  );

  const lastNotifiedKeyRef = useRef<string>('');
  const notifyKey = `${effectiveSelectedTripId}|${effectiveTrip?.stage ?? ''}|${effectiveTrip?.status ?? ''}|${effectiveTrip?.destination ?? ''}`;

  useEffect(() => {
    if (lastNotifiedKeyRef.current !== notifyKey) {
      lastNotifiedKeyRef.current = notifyKey;
      onSelectTrip(effectiveSelectedTripId, effectiveTrip);
    }
  }, [notifyKey, effectiveSelectedTripId, effectiveTrip, onSelectTrip]);

  return (
    <div className='rounded-xl border border-[#30363d] bg-[#161b22] p-4 space-y-3'>
      <div className='flex flex-col lg:flex-row lg:items-center justify-between gap-3'>
        <div className='flex items-center gap-2.5 flex-wrap'>
          <label
            htmlFor={selectId}
            className='text-xs font-medium text-[#8b949e] uppercase tracking-wider shrink-0'
          >
            {label}
          </label>
          <div className='inline-flex items-center rounded-md border border-[#30363d] bg-[#0d1117] p-0.5 text-ui-xs'>
            <button
              type='button'
              onClick={() => setPickerScope('scoped')}
              aria-pressed={pickerScope === 'scoped'}
              className={`px-2.5 py-1 rounded font-medium transition-colors tabular-nums ${
                pickerScope === 'scoped'
                  ? 'bg-[#21262d] text-[#e6edf3]'
                  : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}
            >
              {scopedLabel}
              {typeof scopedTotal === 'number' && scopedTotal > 0
                ? ` (${scopedTotal.toLocaleString('en-IN')})`
                : ''}
            </button>
            <button
              type='button'
              onClick={() => setPickerScope('all')}
              aria-pressed={pickerScope === 'all'}
              className={`px-2.5 py-1 rounded font-medium transition-colors tabular-nums ${
                pickerScope === 'all'
                  ? 'bg-[#21262d] text-[#e6edf3]'
                  : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}
            >
              {allLabel}
              {typeof allTotal === 'number' && allTotal > 0
                ? ` (${allTotal.toLocaleString('en-IN')})`
                : ''}
            </button>
          </div>
        </div>

        <div className='relative w-full lg:w-72'>
          <Search
            className='size-3.5 text-[#8b949e] absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none'
            aria-hidden='true'
          />
          <input
            id={searchInputId}
            name='trip_search'
            type='search'
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder={searchPlaceholder}
            aria-label={searchPlaceholder}
            className='w-full bg-[#0d1117] border border-[#30363d] rounded-md pl-8 pr-3 py-1.5 text-xs text-[#e6edf3] placeholder:text-[#8b949e] focus:border-[#3fb950] outline-none'
          />
        </div>
      </div>

      <div className='flex flex-col md:flex-row md:items-center justify-between gap-2.5'>
        <select
          id={selectId}
          name={selectId}
          data-testid={selectTestId}
          value={effectiveSelectedTripId}
          onChange={(e) => {
            const nextId = e.target.value;
            const nextTrip = tripOptions.find((t) => t.id === nextId);
            onSelectTrip(nextId, nextTrip);
          }}
          disabled={isLoading || tripOptions.length === 0}
          className='w-full md:w-[540px] bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:border-[#3fb950] outline-none disabled:opacity-60'
        >
          {tripOptions.length === 0 ? (
            <option value=''>
              {isLoading
                ? 'Loading workspace trips…'
                : debouncedSearch
                  ? `No trips matching "${debouncedSearch}"`
                  : 'No trips available'}
            </option>
          ) : (
            tripOptions.map((trip) => (
              <option key={trip.id} value={trip.id}>
                {formatTripPickerLabel(trip)}
              </option>
            ))
          )}
        </select>

        {helperText && <span className='text-xs text-[#8b949e]'>{helperText}</span>}
      </div>
    </div>
  );
}
