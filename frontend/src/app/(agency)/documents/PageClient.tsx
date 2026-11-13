'use client';

import { useCallback, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { CalendarCheck, FileText, Info, Layers } from 'lucide-react';
import { useTrip } from '@/hooks/useTrips';
import type { Trip } from '@/lib/api-client';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';
import { ScopedTripPickerBar } from '@/components/workspace/ScopedTripPickerBar';
import OpsPanel from '../workbench/OpsPanel';

export default function DocumentsPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const searchParamsString = searchParams.toString();
  const urlTripId = searchParams.get('tripId') || searchParams.get('trip') || '';
  const [selectedTripId, setSelectedTripId] = useState<string>(urlTripId);
  const [selectedTripSummary, setSelectedTripSummary] = useState<Trip | undefined>(undefined);
  const { data: selectedTripDetail } = useTrip(selectedTripId || null);

  const selectedTrip = selectedTripDetail ?? selectedTripSummary;

  const handleSelectTrip = useCallback(
    (tripId: string, trip: Trip | undefined) => {
      const changedBySelection = Boolean(selectedTripId && tripId && tripId !== selectedTripId);
      setSelectedTripId(tripId);
      setSelectedTripSummary(trip);
      if (changedBySelection) {
        const next = new URLSearchParams(searchParamsString);
        next.set('tripId', tripId);
        router.replace(`${pathname}?${next.toString()}`, { scroll: false });
      }
    },
    [pathname, router, searchParamsString, selectedTripId]
  );

  const currentStage = (selectedTrip?.stage || 'intake').toLowerCase();
  const canUploadForStage = currentStage === 'proposal' || currentStage === 'booking';

  return (
    <div className='p-6 space-y-6'>
      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <FileText className='size-5 text-[#58a6ff]' aria-hidden='true' />
            Documents
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Verify traveler passports, visas, tickets, and AI extraction fields across active trips.
          </p>
        </div>

        {selectedTripId && (
          <div className='flex flex-wrap items-center gap-2.5'>
            <Link
              href={`/trips/${selectedTripId}/ops`}
              className='px-3 py-1.5 bg-[#1f6feb] hover:bg-[#388bfd] text-white text-ui-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm'
            >
              <Layers className='size-3.5' aria-hidden='true' />
              Open Ops Workspace
            </Link>
            <Link
              href={`/bookings?tripId=${selectedTripId}`}
              className='px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-ui-xs font-medium rounded-md border border-[#30363d] flex items-center gap-1.5 transition-colors'
            >
              <CalendarCheck className='size-3.5 text-[#3fb950]' aria-hidden='true' />
              Booking Dossier
            </Link>
            <Link
              href={`/trips/${selectedTripId}/intake`}
              className='px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-ui-xs font-medium rounded-md border border-[#30363d] transition-colors'
            >
              Open Trip Workspace
            </Link>
          </div>
        )}
      </div>

      {/* Scoped Searchable Trip Selector */}
      <ScopedTripPickerBar
        label='Trip'
        selectId='documents-trip-select'
        selectTestId='documents-trip-select'
        scope='documents'
        scopedLabel='Documents & Upload-Ready'
        allLabel='All Workspace Trips'
        requestedTripId={urlTripId}
        selectedTripId={selectedTripId}
        onSelectTrip={handleSelectTrip}
        searchPlaceholder='Search destination, ref, or traveler…'
        helperText={
          selectedTrip
            ? `Selected: ${formatTripPickerLabel(selectedTrip)} · Stage: ${currentStage}`
            : undefined
        }
      />

      {selectedTrip && !canUploadForStage && (
        <div
          data-testid='documents-stage-notice'
          className='rounded-lg border border-[#30363d] bg-[#161b22] px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-ui-xs text-[#8b949e]'
        >
          <div className='flex items-start sm:items-center gap-2.5'>
            <Info className='size-4 text-[#d29922] shrink-0 mt-0.5 sm:mt-0' aria-hidden='true' />
            <span>
              Document uploads activate once a trip reaches{' '}
              <strong className='text-[#e6edf3]'>Proposal</strong> or{' '}
              <strong className='text-[#e6edf3]'>Booking</strong> stage (current stage:{' '}
              <span className='font-mono text-[#e6edf3]'>{currentStage}</span>). Existing files can still
              be reviewed below.
            </span>
          </div>
          <Link
            href={`/trips/${selectedTrip.id}/intake`}
            className='text-[#58a6ff] hover:underline font-medium shrink-0'
          >
            Advance stage in Intake →
          </Link>
        </div>
      )}

      {/* Canonical Document Ops Panel */}
      {selectedTrip ? (
        <div className='rounded-xl border border-[#30363d] bg-[#0d1117] p-4'>
          <OpsPanel trip={selectedTrip} mode='documents' />
        </div>
      ) : (
        <div className='rounded-xl border border-[#30363d] bg-[#161b22] p-8 text-center text-ui-sm text-[#8b949e]'>
          Select a trip above to inspect or upload traveler documents.
        </div>
      )}
    </div>
  );
}
