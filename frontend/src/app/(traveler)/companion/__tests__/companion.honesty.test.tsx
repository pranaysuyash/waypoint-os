// @vitest-environment jsdom

import { describe, expect, it, vi, afterEach, beforeEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

/**
 * AT-05 / AT-18 companion honesty: never mint BA 178 / e-ticket / ON TIME
 * when the journey graph is missing. Sample copy is labeled. Token required.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
  window.localStorage.clear();
});

describe('Traveler companion honesty (AT-05)', () => {
  it('labels sample itinerary and does not mint a live PNR without tripId', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '' },
    });

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    expect(screen.getByText(/Sample data/i)).toBeInTheDocument();
    expect(screen.queryByText(/ON TIME/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/BA 178/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/006-2345678901/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/^SAMPLE$/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/British Airways \(sample\)/i)).toBeInTheDocument();
  });

  it('requires a share token and abstains instead of fabricating an itinerary', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-real-1' },
    });

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => {
      expect(
        screen.getByText(
          /This itinerary can only be opened through the private link your travel advisor sent you/i,
        ),
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/ON TIME/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/BA 178/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\?token=/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/stored/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/payload/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/journey graph/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/UNAVAILABLE/i).length).toBeGreaterThan(0);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('does not advertise emergency connectivity or invented times without itinerary evidence', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-missing-token' },
    });
    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    expect(screen.queryByText(/Direct satellite|consular duty desk link/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/16:45 Local|17:45 Local/)).not.toBeInTheDocument();
    expect(screen.getByText(/Demonstration only — no alert is sent/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'SIMULATE SOS (DEMO)' })).toBeInTheDocument();
  });

  it('shows an identity-scoped loading state while the private itinerary is pending', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-pending&token=share-token' },
    });
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)));

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    expect(screen.getByText('Checking itinerary')).toBeInTheDocument();
    expect(screen.getByText(/Checking your private itinerary link/i)).toBeInTheDocument();
    expect(screen.queryByText(/Your itinerary will appear here as your travel advisor confirms bookings/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/no cached itinerary is shown/i)).not.toBeInTheDocument();
  });

  it('distinguishes a transport failure from an empty or denied itinerary', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-offline&token=share-token' },
    });
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => expect(screen.getByText('Itinerary unavailable')).toBeInTheDocument());
    expect(screen.getByText(/We couldn't reach your private itinerary right now/i)).toBeInTheDocument();
    expect(screen.getByText(/No cached itinerary is shown/i)).toBeInTheDocument();
    expect(screen.queryByText(/Itinerary access denied/i)).not.toBeInTheDocument();
  });

  it.each([401, 403, 404])('labels HTTP %i capability denial as access denial without replaying protected data', async (status) => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-denied&token=revoked-token' },
    });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }));

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => expect(screen.getByText('Itinerary access denied')).toBeInTheDocument());
    expect(screen.getByText(/Ask your travel advisor for a fresh private link/i)).toBeInTheDocument();
    expect(screen.queryByText(/No cached itinerary is shown/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/ON TIME|BA 178/i)).not.toBeInTheDocument();
  });

  it('does not invent PNR or ON TIME when the stored graph abstains', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-real-1&token=share-token' },
    });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          exists: false,
          reality_tier: 'unavailable',
          trip_id: 'trip-real-1',
        }),
      }),
    );

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => {
      expect(
        screen.getByText(
          /Your itinerary will appear here as your travel advisor confirms bookings/i,
        ),
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/ON TIME/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/BA 178/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/UNAVAILABLE/i).length).toBeGreaterThan(0);
  });

  it('preserves an authorized itinerary with a null destination from the backend', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-null-destination&token=share-token' },
    });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        trip_id: 'trip-null-destination',
        destination: null,
        provider_connected: false,
        booking_confirmation: { pnr_locator: 'PRV-NULL-DESTINATION' },
        nodes: [{ node_id: 'flight-null-destination', node_type: 'FLIGHT', title: 'My saved flight', provider: 'Preview carrier' }],
      }),
    }));

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => expect(screen.getByText('My saved flight')).toBeInTheDocument());
    expect(screen.getByText('PRV-NULL-DESTINATION')).toBeInTheDocument();
    expect(screen.getByText(/Destination on file/)).toBeInTheDocument();
    expect(screen.getByText('Preview itinerary')).toBeInTheDocument();
  });

  it.each([
    ['null payload', null],
    ['non-array nodes', { trip_id: 'trip-real-1', nodes: { unexpected: true } }],
  ])('fails closed on a malformed 200 response (%s)', async (_label, payload) => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-real-1&token=share-token' },
    });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => {
      expect(
        screen.getByText(
          /The private itinerary response was not valid/i,
        ),
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/ON TIME/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/UNAVAILABLE/i).length).toBeGreaterThan(0);
  });

  it('labels simulator-generated PNR/e-ticket as preview, never live truth (Part-H P1)', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-real-1&token=share-token' },
    });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          exists: true,
          reality_tier: 'deterministic_preview',
          trip_id: 'trip-real-1',
          destination: 'Tokyo',
          booking_confirmation: {
            pnr_locator: 'PRV123',
            e_ticket_number: '057-0000000001',
            provider_connected: false,
          },
          nodes: [
            {
              node_id: 'n1',
              node_type: 'FLIGHT',
              title: 'Flight to Tokyo (PRV123)',
              provider: 'Amadeus NDC',
              confirmation_code: 'PRV123',
              metadata: { provider_connected: false },
            },
          ],
          edges: [],
        }),
      }),
    );

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => {
      expect(screen.getByText(/Preview itinerary/i)).toBeInTheDocument();
    });
    expect(
      screen.getByText(/references below are placeholders/i),
    ).toBeInTheDocument();
    // Traveler-facing copy speaks traveler language: no internal jargon and
    // no raw reality-tier slugs rendered (Part-K copy pass).
    expect(screen.queryByText(/deterministic/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider not connected/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Stored itinerary/i)).not.toBeInTheDocument();
    // Wallet identifiers are explicitly preview-labeled.
    expect(screen.getByText(/E-Ticket \(preview\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Hotel Voucher \(preview\)/i)).toBeInTheDocument();
    expect(screen.queryByText(/ON TIME/i)).not.toBeInTheDocument();
  });

  it('fails CLOSED on missing provider provenance — legacy data renders as preview (Part-J #4)', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-real-1&token=share-token' },
    });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          exists: true,
          trip_id: 'trip-real-1',
          destination: 'Tokyo',
          booking_confirmation: {
            // Legacy/partial blob: NO provider_connected field at all.
            pnr_locator: 'OLD123',
            e_ticket_number: '057-0000000009',
          },
          nodes: [
            {
              node_id: 'n1',
              node_type: 'FLIGHT',
              title: 'Flight to Tokyo (OLD123)',
              provider: 'Amadeus NDC',
              confirmation_code: 'OLD123',
            },
          ],
          edges: [],
        }),
      }),
    );

    const { default: TravelerCompanionPage } = await import('../page');
    render(<TravelerCompanionPage />);

    await waitFor(() => {
      expect(screen.getByText(/Preview itinerary/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Stored itinerary/i)).not.toBeInTheDocument();
    expect(screen.getByText(/E-Ticket \(preview\)/i)).toBeInTheDocument();
  });

  it('does not let a late response for the previous URL identity replace the current trip', async () => {
    type PendingResponse = { ok: boolean; json: () => Promise<unknown> };
    const pending = new Map<string, (response: PendingResponse) => void>();
    const fetchMock = vi.fn(
      (input: RequestInfo | URL) => new Promise<PendingResponse>((resolve) => pending.set(String(input), resolve)),
    );
    vi.stubGlobal('fetch', fetchMock);
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a&token=share-a' },
    });

    const { default: TravelerCompanionPage } = await import('../page');
    const view = render(<TravelerCompanionPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-b&token=share-b' },
    });
    view.rerender(<TravelerCompanionPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    const currentTripUrl = '/api/public/journey-graph/trip-b?token=share-b';
    const previousTripUrl = '/api/public/journey-graph/trip-a?token=share-a';
    pending.get(currentTripUrl)?.({
      ok: true,
      json: async () => ({
        exists: true,
        provider_connected: false,
        trip_id: 'trip-b',
        destination: 'Osaka',
        booking_confirmation: { pnr_locator: 'B-123', e_ticket_number: 'B-456' },
        nodes: [{ node_id: 'b-flight', node_type: 'FLIGHT', title: 'Flight to Osaka (B)', provider: 'Sample carrier' }],
      }),
    });
    await waitFor(() => expect(screen.getByText(/Flight to Osaka \(B\)/i)).toBeInTheDocument());

    pending.get(previousTripUrl)?.({
      ok: true,
      json: async () => ({
        exists: true,
        provider_connected: false,
        trip_id: 'trip-a',
        destination: 'Tokyo',
        booking_confirmation: { pnr_locator: 'A-123', e_ticket_number: 'A-456' },
        nodes: [{ node_id: 'a-flight', node_type: 'FLIGHT', title: 'Flight to Tokyo (A)', provider: 'Sample carrier' }],
      }),
    });

    await waitFor(() => expect(screen.getByText(/Flight to Osaka \(B\)/i)).toBeInTheDocument());
    expect(screen.queryByText(/Flight to Tokyo \(A\)/i)).not.toBeInTheDocument();
  });

  it('hides a loaded itinerary when its share token is removed from the URL', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        exists: true,
        provider_connected: false,
        trip_id: 'trip-a',
        destination: 'Tokyo',
        booking_confirmation: { pnr_locator: 'A-123', e_ticket_number: 'A-456' },
        nodes: [{ node_id: 'a-flight', node_type: 'FLIGHT', title: 'Flight to Tokyo (A)', provider: 'Sample carrier' }],
      }),
    });
    vi.stubGlobal('fetch', fetchMock);
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a&token=share-a' },
    });
    window.localStorage.setItem('legacy_companion_fixture', 'untouched');

    const { default: TravelerCompanionPage } = await import('../page');
    const view = render(<TravelerCompanionPage />);
    await waitFor(() => expect(screen.getByText(/Flight to Tokyo \(A\)/i)).toBeInTheDocument());

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a' },
    });
    view.rerender(<TravelerCompanionPage />);

    expect(
      screen.getByText(
        /This itinerary can only be opened through the private link your travel advisor sent you/i,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Flight to Tokyo \(A\)/i)).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(window.localStorage.getItem('legacy_companion_fixture')).toBe('untouched');
  });

  it('does not reuse data when the same token returns before revalidation completes', async () => {
    type PendingResponse = { ok: boolean; json: () => Promise<unknown> };
    const pending: ((response: PendingResponse) => void)[] = [];
    const fetchMock = vi.fn(
      () => new Promise<PendingResponse>((resolve) => pending.push(resolve)),
    );
    vi.stubGlobal('fetch', fetchMock);
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a&token=share-a' },
    });

    const { default: TravelerCompanionPage } = await import('../page');
    const view = render(<TravelerCompanionPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    pending[0]({
      ok: true,
      json: async () => ({
        exists: true,
        provider_connected: false,
        trip_id: 'trip-a',
        destination: 'Tokyo',
        booking_confirmation: { pnr_locator: 'A-123', e_ticket_number: 'A-456' },
        nodes: [{ node_id: 'a-flight', node_type: 'FLIGHT', title: 'Flight to Tokyo (initial)', provider: 'Sample carrier' }],
      }),
    });
    await waitFor(() => expect(screen.getByText(/Flight to Tokyo \(initial\)/i)).toBeInTheDocument());

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a' },
    });
    view.rerender(<TravelerCompanionPage />);
    expect(screen.queryByText(/Flight to Tokyo \(initial\)/i)).not.toBeInTheDocument();

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a&token=share-a' },
    });
    view.rerender(<TravelerCompanionPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByText(/Flight to Tokyo \(initial\)/i)).not.toBeInTheDocument();

    pending[1]({
      ok: true,
      json: async () => ({
        exists: true,
        provider_connected: false,
        trip_id: 'trip-a',
        destination: 'Tokyo',
        booking_confirmation: { pnr_locator: 'A-789', e_ticket_number: 'A-999' },
        nodes: [{ node_id: 'a-flight', node_type: 'FLIGHT', title: 'Flight to Tokyo (revalidated)', provider: 'Sample carrier' }],
      }),
    });
    await waitFor(() => expect(screen.getByText(/Flight to Tokyo \(revalidated\)/i)).toBeInTheDocument());
  });

  it('does not restore protected data after a replacement token is denied', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          exists: true,
          provider_connected: false,
          trip_id: 'trip-a',
          destination: 'Tokyo',
          booking_confirmation: { pnr_locator: 'A-123', e_ticket_number: 'A-456' },
          nodes: [{ node_id: 'a-flight', node_type: 'FLIGHT', title: 'Flight to Tokyo (A)', provider: 'Sample carrier' }],
        }),
      })
      .mockResolvedValueOnce({ ok: false, status: 403, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a&token=share-a' },
    });

    const { default: TravelerCompanionPage } = await import('../page');
    const view = render(<TravelerCompanionPage />);
    await waitFor(() => expect(screen.getByText(/Flight to Tokyo \(A\)/i)).toBeInTheDocument());

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a&token=revoked-token' },
    });
    view.rerender(<TravelerCompanionPage />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    await waitFor(() => {
      expect(
        screen.getByText(
          /Itinerary access denied/i,
        ),
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/Ask your travel advisor for a fresh private link/i)).toBeInTheDocument();
    expect(screen.queryByText(/Flight to Tokyo \(A\)/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/A-123/i)).not.toBeInTheDocument();
  });

  /*
   * Supersedes the prior persisted-cache eviction check: this route no longer
   * reads or writes private payloads, so the invariant is no replay after a
   * remount/network failure while unrelated existing storage stays untouched.
   */
  it('does not replay a previously authorized itinerary after a network failure on remount', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          exists: true,
          provider_connected: false,
          trip_id: 'trip-a',
          destination: 'Tokyo',
          booking_confirmation: { pnr_locator: 'A-123', e_ticket_number: 'A-456' },
          nodes: [{ node_id: 'a-flight', node_type: 'FLIGHT', title: 'Flight to Tokyo (A)', provider: 'Sample carrier' }],
        }),
      })
      .mockRejectedValueOnce(new Error('offline'));
    vi.stubGlobal('fetch', fetchMock);
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { search: '?tripId=trip-a&token=share-a' },
    });
    window.localStorage.setItem('legacy_companion_fixture', 'untouched');

    const { default: TravelerCompanionPage } = await import('../page');
    const firstView = render(<TravelerCompanionPage />);
    await waitFor(() => expect(screen.getByText(/Flight to Tokyo \(A\)/i)).toBeInTheDocument());
    firstView.unmount();

    render(<TravelerCompanionPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.queryByText(/Flight to Tokyo \(A\)/i)).not.toBeInTheDocument());
    expect(screen.getByText(/We couldn't reach your private itinerary right now/i)).toBeInTheDocument();
    expect(screen.getByText(/No cached itinerary is shown/i)).toBeInTheDocument();
    expect(window.localStorage.getItem('legacy_companion_fixture')).toBe('untouched');
    expect(Object.keys(window.localStorage)).toEqual(['legacy_companion_fixture']);
  });
});
