'use client';

/**
 * Bookings — the traveler booking dossier for the selected trip (E1 honest
 * rebuild, 2026-10-25). The former sample surface (fabricated flight/hotel
 * rows, a fake checklist, and a client-side keyword "extractor") is
 * superseded by the REAL booking surfaces that already exist:
 *   - booking_data collected from the customer (collection form → pending →
 *     accepted), rendered read-only here with accept/reject for pendings;
 *   - the customer collection link (generate / copy / revoke);
 *   - payment tracking recorded against the trip.
 * Every value on this page comes from the backend; empty sections say so.
 */

import { useCallback, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  CalendarCheck,
  Check,
  Clock,
  Copy,
  FileCheck,
  Layers,
  Link2,
  Users,
} from 'lucide-react';
import {
  acceptPendingBookingData,
  generateCollectionLink,
  getBookingData,
  getCollectionLink,
  getPendingBookingData,
  rejectPendingBookingData,
  revokeCollectionLink,
} from '@/lib/api-client';
import { useTrips, useTrip } from '@/hooks/useTrips';

function formatTripPickerLabel(trip: {
  id: string;
  destination?: string | null;
  dateWindow?: string | null;
}): string {
  const parts = [trip.destination || 'Unnamed trip', trip.dateWindow].filter(Boolean);
  return `${parts.join(' · ')} (${trip.id})`;
}

function fmtDate(value?: string | null): string {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return value;
  }
}

function fmtMoney(amount?: number | null, currency?: string | null): string {
  if (amount === null || amount === undefined) return '—';
  return `${currency || 'INR'} ${amount.toLocaleString()}`;
}

export default function BookingsPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const urlTripId = searchParams.get('tripId') || searchParams.get('trip') || '';
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

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

  const bookingDataKey = ['booking-data', effectiveSelectedTripId] as const;
  const { data: booking, isLoading: bookingLoading, error: bookingError } = useQuery({
    queryKey: bookingDataKey,
    queryFn: () => getBookingData(effectiveSelectedTripId),
    enabled: Boolean(effectiveSelectedTripId),
    staleTime: 30_000,
  });
  const { data: pending } = useQuery({
    queryKey: ['pending-booking-data', effectiveSelectedTripId],
    queryFn: () => getPendingBookingData(effectiveSelectedTripId),
    enabled: Boolean(effectiveSelectedTripId),
    staleTime: 30_000,
  });
  const { data: collectionLink } = useQuery({
    queryKey: ['collection-link', effectiveSelectedTripId],
    queryFn: () => getCollectionLink(effectiveSelectedTripId),
    enabled: Boolean(effectiveSelectedTripId),
    staleTime: 30_000,
  });

  const invalidateAll = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ['booking-data', effectiveSelectedTripId] });
    void queryClient.invalidateQueries({ queryKey: ['pending-booking-data', effectiveSelectedTripId] });
  }, [queryClient, effectiveSelectedTripId]);

  const acceptPending = useMutation({
    mutationFn: () => acceptPendingBookingData(effectiveSelectedTripId),
    onSuccess: () => {
      setActionError(null);
      invalidateAll();
    },
    onError: () => setActionError('accept'),
  });
  const rejectPending = useMutation({
    mutationFn: () => rejectPendingBookingData(effectiveSelectedTripId),
    onSuccess: () => {
      setActionError(null);
      invalidateAll();
    },
    onError: () => setActionError('reject'),
  });
  const generateLink = useMutation({
    mutationFn: () => generateCollectionLink(effectiveSelectedTripId),
    onSuccess: () => {
      setActionError(null);
      void queryClient.invalidateQueries({ queryKey: ['collection-link', effectiveSelectedTripId] });
    },
    onError: () => setActionError('generate link'),
  });
  const revokeLink = useMutation({
    mutationFn: () => revokeCollectionLink(effectiveSelectedTripId),
    onSuccess: () => {
      setActionError(null);
      void queryClient.invalidateQueries({ queryKey: ['collection-link', effectiveSelectedTripId] });
    },
    onError: () => setActionError('revoke link'),
  });

  const bookingData = booking?.booking_data ?? null;
  const travelers = bookingData?.travelers ?? [];
  const payment = bookingData?.payment_tracking ?? null;
  const pendingData = pending?.pending_booking_data ?? null;
  const hasLink = Boolean(collectionLink?.has_active_token);
  const collectionUrl = collectionLink?.collection_url || '';

  const copyLink = useCallback(() => {
    if (!collectionUrl) return;
    void navigator.clipboard?.writeText(collectionUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [collectionUrl]);

  return (
    <div className='p-6 space-y-6'>
      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <CalendarCheck className='size-6 text-[#3fb950]' />
            Bookings
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            The traveler booking dossier for the selected trip: collected traveler details,
            payment tracking, and customer submissions. Send the collection form to gather
            what is missing.
          </p>
        </div>

        {effectiveSelectedTripId && (
          <div className='flex flex-wrap items-center gap-3'>
            <Link
              href={`/trips/${effectiveSelectedTripId}/ops`}
              className='px-3.5 py-2 bg-[#1f6feb] hover:bg-[#388bfd] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm'
            >
              <Layers className='size-3.5' />
              Open Ops Workspace
            </Link>
            <Link
              href={`/trips/${effectiveSelectedTripId}/timeline`}
              className='px-3.5 py-2 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-xs font-medium rounded-md border border-[#30363d] flex items-center gap-1.5 transition-colors'
            >
              <Clock className='size-3.5 text-[#58a6ff]' />
              Trip Timeline
            </Link>
          </div>
        )}
      </div>

      {/* Trip Picker */}
      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <div className='flex flex-col md:flex-row md:items-center justify-between gap-3'>
          <div className='space-y-1'>
            <label htmlFor='bookings-trip-select' className='block text-xs font-medium text-[#8b949e] uppercase tracking-wider'>
              Active Trip Booking Scope
            </label>
            <select
              id='bookings-trip-select'
              data-testid='bookings-trip-select'
              value={effectiveSelectedTripId}
              onChange={(e) => handleTripChange(e.target.value)}
              className='w-full md:w-[460px] bg-[#161b22] border border-[#30363d] rounded-md p-2 text-sm text-[#e6edf3] focus:border-[#3fb950] outline-none'
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
          </div>

          {selectedTrip && (
            <div className='flex items-center gap-3 text-xs bg-[#161b22] px-3 py-2 rounded-md border border-[#30363d]'>
              <div className='text-[#8b949e]'>
                Destination: <span className='text-[#e6edf3] font-medium'>{selectedTrip.destination || 'Unspecified'}</span>
              </div>
              <div className='w-px h-4 bg-[#30363d]' />
              <div className='text-[#8b949e]'>
                Travel Window: <span className='text-[#58a6ff] font-medium'>{selectedTrip.dateWindow || '—'}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {actionError && (
        <p className='text-xs' style={{ color: 'var(--accent-amber)' }} role='alert'>
          Could not {actionError} — retry, and refresh if it persists.
        </p>
      )}

      {effectiveSelectedTripId ? (
        <div className='grid gap-6 lg:grid-cols-3'>
          {/* Booking dossier */}
          <div className='lg:col-span-2 space-y-4'>
            {/* Customer collection link */}
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-3'>
              <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
                <div className='font-semibold text-sm text-[#e6edf3] flex items-center gap-2'>
                  <Link2 className='size-4 text-[#58a6ff]' />
                  <span>Customer Collection Link</span>
                </div>
                {hasLink && collectionLink?.expires_at && (
                  <span className='text-xs text-[#8b949e]'>expires {fmtDate(collectionLink.expires_at)}</span>
                )}
              </div>
              {hasLink ? (
                <div className='flex flex-wrap items-center gap-2'>
                  <code
                    data-testid='collection-url'
                    className='text-xs font-mono text-[#58a6ff] bg-[#161b22] border border-[#30363d] rounded px-2 py-1 truncate max-w-md'
                  >
                    {collectionUrl || '(link active — URL hidden until reopened)'}
                  </code>
                  {collectionUrl && (
                    <button
                      type='button'
                      onClick={copyLink}
                      className='inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md border border-[#30363d] text-[#e6edf3] hover:bg-[#161b22] transition-colors'
                    >
                      {copied ? <Check className='size-3 text-[#3fb950]' /> : <Copy className='size-3' />}
                      {copied ? 'Copied' : 'Copy'}
                    </button>
                  )}
                  <button
                    type='button'
                    onClick={() => revokeLink.mutate()}
                    disabled={revokeLink.isPending}
                    className='px-2.5 py-1.5 text-xs font-medium rounded-md border border-[#da3633]/40 text-[#f85149] hover:bg-[#da3633]/10 transition-colors disabled:opacity-50'
                  >
                    Revoke
                  </button>
                </div>
              ) : (
                <div className='flex flex-wrap items-center gap-3'>
                  <p className='text-xs text-[#8b949e]'>
                    No active collection form. Generate a signed link for the customer to submit
                    traveler details and documents.
                  </p>
                  <button
                    type='button'
                    onClick={() => generateLink.mutate()}
                    disabled={generateLink.isPending}
                    className='px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md transition-colors disabled:opacity-50'
                  >
                    {generateLink.isPending ? 'Generating…' : 'Generate collection link'}
                  </button>
                </div>
              )}
            </div>

            {/* Pending customer submission */}
            {pendingData && (
              <div
                data-testid='pending-submission'
                className='rounded-lg border border-[#d29922]/40 bg-[#d29922]/5 p-4 space-y-3'
              >
                <div className='font-semibold text-sm text-[#e6edf3] flex items-center gap-2'>
                  <Clock className='size-4 text-[#d29922]' />
                  <span>Customer submission awaiting review</span>
                </div>
                <ul className='text-xs text-[#8b949e] space-y-1'>
                  {pendingData.travelers.map((t) => (
                    <li key={t.traveler_id}>
                      {t.full_name} · {t.nationality || 'nationality not given'}
                    </li>
                  ))}
                  {pendingData.special_requirements && <li>Special requirements: {pendingData.special_requirements}</li>}
                </ul>
                <div className='flex items-center gap-2'>
                  <button
                    type='button'
                    onClick={() => acceptPending.mutate()}
                    disabled={acceptPending.isPending}
                    className='px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md transition-colors disabled:opacity-50'
                  >
                    Accept into dossier
                  </button>
                  <button
                    type='button'
                    onClick={() => rejectPending.mutate()}
                    disabled={rejectPending.isPending}
                    className='px-3 py-1.5 text-xs font-medium rounded-md border border-[#30363d] text-[#e6edf3] hover:bg-[#161b22] transition-colors disabled:opacity-50'
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}

            {/* Traveler details */}
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] overflow-hidden'>
              <div className='p-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]'>
                <div className='flex items-center gap-2 font-semibold text-sm text-[#e6edf3]'>
                  <Users className='size-4 text-[#3fb950]' />
                  <span>Traveler Details</span>
                </div>
                {booking?.updated_at && (
                  <span className='text-xs text-[#8b949e]'>updated {fmtDate(booking.updated_at)}</span>
                )}
              </div>
              {bookingError ? (
                <p className='p-4 text-xs text-[#8b949e]'>Booking dossier unavailable.</p>
              ) : bookingLoading ? (
                <p className='p-4 text-xs text-[#8b949e]'>Loading…</p>
              ) : travelers.length === 0 ? (
                <p className='p-4 text-xs text-[#8b949e]'>
                  No traveler details collected yet. Generate the collection link above and send it
                  to the customer.
                </p>
              ) : (
                <div className='overflow-x-auto'>
                  <table className='w-full text-left text-sm'>
                    <thead>
                      <tr className='border-b border-[#30363d] bg-[#0d1117] text-xs font-semibold text-[#8b949e] uppercase tracking-wider'>
                        <th className='p-3.5'>Traveler</th>
                        <th className='p-3.5'>Date of birth</th>
                        <th className='p-3.5'>Passport</th>
                        <th className='p-3.5'>Expiry</th>
                        <th className='p-3.5'>Nationality</th>
                      </tr>
                    </thead>
                    <tbody className='divide-y divide-[#30363d]'>
                      {travelers.map((t) => (
                        <tr key={t.traveler_id} className='hover:bg-[#161b22] transition-colors'>
                          <td className='p-3.5 font-medium text-[#e6edf3]'>{t.full_name}</td>
                          <td className='p-3.5 text-xs text-[#8b949e]'>{t.date_of_birth || '—'}</td>
                          <td className='p-3.5 font-mono text-xs text-[#58a6ff]'>{t.passport_number || '—'}</td>
                          <td className='p-3.5 text-xs text-[#8b949e]'>{fmtDate(t.passport_expiry)}</td>
                          <td className='p-3.5 text-xs text-[#8b949e]'>{t.nationality || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Right rail: payment + notes */}
          <div className='space-y-4'>
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-3'>
              <div className='font-semibold text-sm text-[#e6edf3] flex items-center gap-2 border-b border-[#30363d] pb-3'>
                <FileCheck className='size-4 text-[#3fb950]' />
                <span>Payment Tracking</span>
              </div>
              {payment ? (
                <dl className='text-xs space-y-2' data-testid='payment-tracking'>
                  <div className='flex justify-between gap-2'>
                    <dt className='text-[#8b949e]'>Agreed</dt>
                    <dd className='text-[#e6edf3] font-mono'>{fmtMoney(payment.agreed_amount, payment.currency)}</dd>
                  </div>
                  <div className='flex justify-between gap-2'>
                    <dt className='text-[#8b949e]'>Paid</dt>
                    <dd className='text-[#e6edf3] font-mono'>{fmtMoney(payment.amount_paid, payment.currency)}</dd>
                  </div>
                  <div className='flex justify-between gap-2'>
                    <dt className='text-[#8b949e]'>Balance due</dt>
                    <dd className='text-[#e6edf3] font-mono'>{fmtMoney(payment.balance_due, payment.currency)}</dd>
                  </div>
                  {payment.payment_status && (
                    <div className='flex justify-between gap-2'>
                      <dt className='text-[#8b949e]'>Status</dt>
                      <dd className='text-[#e6edf3]'>{payment.payment_status}</dd>
                    </div>
                  )}
                  {payment.payment_reference && (
                    <div className='flex justify-between gap-2'>
                      <dt className='text-[#8b949e]'>Reference</dt>
                      <dd className='text-[#e6edf3] font-mono'>{payment.payment_reference}</dd>
                    </div>
                  )}
                </dl>
              ) : (
                <p className='text-xs text-[#8b949e]'>No payment tracking recorded for this trip yet.</p>
              )}
            </div>

            {(bookingData?.special_requirements || bookingData?.booking_notes) && (
              <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-2'>
                <div className='font-semibold text-sm text-[#e6edf3] border-b border-[#30363d] pb-3'>
                  Customer Notes
                </div>
                {bookingData?.special_requirements && (
                  <p className='text-xs text-[#8b949e]'>
                    <span className='text-[#e6edf3] font-medium'>Special requirements: </span>
                    {bookingData.special_requirements}
                  </p>
                )}
                {bookingData?.booking_notes && (
                  <p className='text-xs text-[#8b949e]'>
                    <span className='text-[#e6edf3] font-medium'>Notes: </span>
                    {bookingData.booking_notes}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-8 text-center text-[#8b949e]'>
          {isLoading ? 'Loading booking dossiers…' : 'No trip selected. Choose a trip above to inspect its booking dossier.'}
        </div>
      )}
    </div>
  );
}
