// @vitest-environment jsdom

import { describe, expect, it, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

/**
 * PA-25 frontend honesty test (2026-09-06): ProposalCompilerPanel is
 * compile-and-display only. The fabricated accept → fulfill → VCC chain
 * (hardcoded TRIP-LIVE-772 / PROP-IVE-772) was removed, and the compile flow
 * must surface the sample-data notice plus the simulated-reality metadata.
 */

const okResponse = (body: unknown) => ({
  ok: true,
  json: async () => body,
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('ProposalCompilerPanel honesty (PA-25)', () => {
  it('renders the compiled package with reality metadata, sample-data notice, and no fulfill chain', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okResponse({
        status: 'success',
        proposal_package: {
          proposal_id: 'PROP-TEST-01',
          trip_id: 'TRIP-TEST-01',
          title: 'Bespoke Paris Itinerary for 2 Travelers',
          destination: 'Paris',
          gross_customer_price_usd: 8750,
          net_supplier_cost_usd: 6850,
          gross_margin_usd: 1900,
          optimized_take_rate_pct: 21.7,
          is_feasibility_passed: true,
          proposal_share_url: null,
          share_token: null,
          share_blocked_reason: 'simulated_inventory',
          reality_tier: 'deterministic_preview',
          provider_connected: false,
          breakdown_items: [
            { category: 'Flights', provider: 'Simulated Carrier', amount_usd: 2500 },
          ],
        },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const { default: ProposalCompilerPanel } = await import('../ProposalCompilerPanel');
    render(<ProposalCompilerPanel />);

    expect(screen.getByRole('button', { name: /compile verified proposal/i })).toBeDisabled();
    await userEvent.type(screen.getByLabelText(/trip reference/i), 'trip-test-01');
    await userEvent.click(screen.getByRole('button', { name: /compile verified proposal/i }));

    await waitFor(() => {
      expect(screen.getByText('PROP-TEST-01')).toBeInTheDocument();
    });

    // Reality metadata is surfaced in traveler/operator words (AT-21),
    // with the raw slug no longer rendered raw.
    expect(screen.getByText(/Preview compiled locally — no provider connected/i)).toBeInTheDocument();
    expect(screen.getByText(/treat every price as an estimate/i)).toBeInTheDocument();
    expect(screen.queryByText(/Reality tier:/i)).not.toBeInTheDocument();
    // Share minting blocked for simulated inventory.
    expect(screen.getByText(/Share link unavailable: simulated_inventory/i)).toBeInTheDocument();
    // Sample-data notice replaces the removed fulfill chain.
    expect(screen.getByText(/Sample data notice:/i)).toBeInTheDocument();
    expect(screen.getByText(/compiled from simulated inventory/i)).toBeInTheDocument();

    // The fabricated fulfill chain is gone: no accept/execute button, no
    // confirmed-booking artifacts.
    expect(screen.queryByRole('button', { name: /accept & execute fulfillment/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/Booking Confirmed & VCC Settled/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/CONFIRMED/i)).not.toBeInTheDocument();

    // No hardcoded fabricated trip/proposal records.
    expect(screen.queryByText(/TRIP-LIVE-772/)).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/proposal-compiler/compile',
      expect.objectContaining({ method: 'POST' }),
    );
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body.trip_id).toBe('trip-test-01');
  });

  it('shows a compile error instead of fabricating a local package on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, json: async () => ({ detail: 'compile unavailable' }) }),
    );

    const { default: ProposalCompilerPanel } = await import('../ProposalCompilerPanel');
    render(<ProposalCompilerPanel />);

    await userEvent.type(screen.getByLabelText(/trip reference/i), 'trip-test-01');
    await userEvent.click(screen.getByRole('button', { name: /compile verified proposal/i }));

    await waitFor(() => {
      expect(screen.getByText('compile unavailable')).toBeInTheDocument();
    });
    // The old fallback fabricated PROP-IVE-772 locally; that must never appear.
    expect(screen.queryByText(/PROP-IVE-772/)).not.toBeInTheDocument();
  });
});
