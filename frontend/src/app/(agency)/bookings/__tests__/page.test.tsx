// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import BookingsPageClient from '../PageClient';
import * as apiClient from '@/lib/api-client';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/bookings',
  useSearchParams: () => new URLSearchParams('tripId=trip_456'),
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrips: () => ({
    data: [
      { id: 'trip_456', destination: 'South Africa', dateWindow: 'Nov 2026', party: 2 },
    ],
    isLoading: false,
  }),
  useTrip: (id: string | null) => ({
    data: id ? { id, destination: 'South Africa', dateWindow: 'Nov 2026', party: 2 } : null,
  }),
}));

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

const trip456 = 'trip_456';

function mockApi(overrides: {
  bookingData?: apiClient.BookingData | null;
  pending?: apiClient.BookingData | null;
  hasLink?: boolean;
} = {}) {
  vi.spyOn(apiClient, 'getBookingData').mockResolvedValue({
    trip_id: trip456,
    booking_data: overrides.bookingData === undefined
      ? {
          travelers: [
            {
              traveler_id: 'trav_1',
              full_name: 'Asha Verma',
              date_of_birth: '1990-04-12',
              passport_number: 'Z1234567',
              passport_expiry: '2031-02-01',
              nationality: 'Indian',
              emergency_contact: null,
            },
          ],
          payer: null,
          special_requirements: 'vegetarian meals',
          booking_notes: null,
          payment_tracking: {
            agreed_amount: 720000,
            currency: 'INR',
            amount_paid: 200000,
            balance_due: 520000,
            payment_status: 'partially_paid',
            payment_method: null,
            payment_reference: 'PAY-88',
            payment_proof_url: null,
            refund_amount_agreed: null,
          },
        }
      : overrides.bookingData,
    updated_at: '2026-10-25T10:00:00Z',
    stage: 'booking',
    readiness: {},
  });
  vi.spyOn(apiClient, 'getPendingBookingData').mockResolvedValue({
    trip_id: trip456,
    pending_booking_data: overrides.pending ?? null,
    booking_data_source: overrides.pending ? 'customer_collection' : null,
  });
  vi.spyOn(apiClient, 'getCollectionLink').mockResolvedValue({
    has_active_token: overrides.hasLink ?? false,
    has_pending_submission: Boolean(overrides.pending),
    token_id: overrides.hasLink ? 'tok_1' : null,
    collection_url: overrides.hasLink ? 'http://localhost:3005/public/booking-collection/a1/tok' : null,
    expires_at: overrides.hasLink ? '2026-11-01T00:00:00Z' : null,
    status: overrides.hasLink ? 'active' : null,
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <BookingsPageClient />
    </QueryClientProvider>
  );
}

describe('BookingsPageClient (honest booking dossier)', () => {
  it('renders the REAL traveler dossier from booking_data — no sample surface', async () => {
    mockApi();
    renderPage();

    expect(await screen.findByText('Asha Verma')).toBeInTheDocument();
    expect(screen.getByText('Z1234567')).toBeInTheDocument();
    expect(screen.getByText('Traveler Details')).toBeInTheDocument();
    // payment block renders real numbers
    expect(screen.getByTestId('payment-tracking')).toHaveTextContent('INR 720,000');
    expect(screen.getByTestId('payment-tracking')).toHaveTextContent('INR 520,000');
    // the fabricated surface is gone
    expect(screen.queryByText('Sample Booking Records')).not.toBeInTheDocument();
    expect(screen.queryByTestId('simulated-badge')).not.toBeInTheDocument();
    expect(screen.queryByText('Sample Operational Checklist')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Preview Booking Document/i })).not.toBeInTheDocument();
  });

  it('shows an honest empty state and the generate-link CTA when nothing is collected', async () => {
    mockApi({ bookingData: null });
    renderPage();

    expect(
      await screen.findByText(/No traveler details collected yet/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Generate collection link/i })
    ).toBeInTheDocument();
  });

  it('surfaces a pending customer submission with accept/reject', async () => {
    mockApi({
      pending: {
        travelers: [
          { traveler_id: 'trav_9', full_name: 'Rohan Verma', date_of_birth: '1993-09-03' },
        ],
        payer: null,
        special_requirements: 'window seat',
        booking_notes: null,
      },
    });
    const acceptSpy = vi
      .spyOn(apiClient, 'acceptPendingBookingData')
      .mockResolvedValue({ trip_id: trip456, booking_data: null, updated_at: null, stage: 'booking', readiness: {} });
    const { getByRole } = renderPage();

    expect(await screen.findByTestId('pending-submission')).toHaveTextContent('Rohan Verma');
    getByRole('button', { name: /Accept into dossier/i }).click();
    await waitFor(() => expect(acceptSpy).toHaveBeenCalledWith(trip456));
  });

  it('manages the customer collection link (active: revoke; absent: generate)', async () => {
    mockApi({ hasLink: true });
    const revokeSpy = vi.spyOn(apiClient, 'revokeCollectionLink').mockResolvedValue({ ok: true });
    const { getByRole, unmount } = renderPage();

    expect(await screen.findByTestId('collection-url')).toHaveTextContent('/public/booking-collection/');
    getByRole('button', { name: 'Revoke' }).click();
    await waitFor(() => expect(revokeSpy).toHaveBeenCalledWith(trip456));
    unmount();

    // absent-link variant renders the generate CTA
    mockApi({ hasLink: false });
    renderPage();
    expect(await screen.findByRole('button', { name: /Generate collection link/i })).toBeInTheDocument();
  });
});
