// @vitest-environment jsdom

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import QuotesPageClient from '../PageClient';

// T4 (FND-0303): the page renders the REAL quote read model from
// /api/v1/trips/{id}/quotes. These tests supersede the FND-0260 sample-data
// pins — the fabricated tier matrix is deleted, so the honesty contract here
// is stronger: nothing on the page is invented, and a trip without persisted
// spine inputs renders an explicit not-ready state.

const QUOTES_PAYLOAD_READY = {
  trip_id: 'trip_123',
  quote_ready: true,
  quotes: [
    {
      trip_id: 'trip_123',
      title: 'Cape Town Signature Journey',
      currency: 'USD',
      net_cost: 4200,
      net_cost_basis: 'persisted_modeled_cost',
      margin_percent: 18.42,
      margin_basis: 'policy_preview',
      margin_provenance: {
        applied_rule_id: 'mp_custom_tour_default@2026-09-14',
        markup_amount_usd: 588,
        flat_planning_fee_usd: 150,
      },
      tax_percent: null,
      rack_price: 4938,
      rack_price_basis: 'computed_preview',
      status: 'approved',
      created_at: '2026-09-20T10:00:00Z',
      updated_at: '2026-09-25T12:00:00Z',
      highlights: ['Boutique Villa', 'Private Chauffeur'],
      summary: 'Curated Cape Town itinerary.',
    },
  ],
  branches: [{ label: 'Budget-tier options', description: 'Different budget interpretations.', priced: false }],
  budget_breakdown: {
    verdict: 'realistic',
    buckets: [
      { bucket: 'stay', low: 1400, high: 1800, covered: true },
      { bucket: 'flights', low: 900, high: 1200, covered: false },
    ],
    missing_buckets: ['flights'],
    total_estimated_low: 2300,
    total_estimated_high: 3000,
  },
  missing: [],
};

const QUOTES_PAYLOAD_NOT_READY = {
  trip_id: 'trip_123',
  quote_ready: false,
  quotes: [],
  branches: [],
  budget_breakdown: null,
  missing: ['strategy.recommended_option (run the spine to produce a recommended itinerary)'],
};

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/quotes',
  useSearchParams: () => new URLSearchParams('tripId=trip_123'),
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrips: () => ({
    data: [
      {
        id: 'trip_123',
        destination: 'Cape Town',
        type: 'luxury',
        origin: 'London',
        budget: '$4,500',
        dateWindow: 'November 2026',
        tripPurpose: 'vacation',
        party: 2,
        validation: { is_valid: true, errors: [], warnings: [] },
      },
    ],
    isLoading: false,
  }),
}));

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

describe('QuotesPageClient (real read model, T4)', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(QUOTES_PAYLOAD_READY) })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the spine-derived quote with provenance and real status', async () => {
    render(<QuotesPageClient />);

    await waitFor(() => {
      expect(screen.getByTestId('quote-title')).toHaveTextContent('Cape Town Signature Journey');
    });
    expect(screen.getByTestId('quote-net-cost')).toHaveTextContent('4,200');
    expect(screen.getByTestId('quote-rack-price')).toHaveTextContent('4,938');
    expect(screen.getByTestId('quote-margin')).toHaveTextContent('18.42%');
    expect(screen.getByTestId('quote-status')).toHaveTextContent('approved');
    // Policy provenance is surfaced, not hidden.
    expect(screen.getByText(/mp_custom_tour_default@2026-09-14/)).toBeInTheDocument();
    // Real highlights from the persisted recommendation.
    expect(screen.getByText('Boutique Villa')).toBeInTheDocument();
  });

  it('renders cost buckets with coverage and missing-bucket callouts', async () => {
    render(<QuotesPageClient />);

    await waitFor(() => {
      expect(screen.getByText('Cost basis buckets')).toBeInTheDocument();
    });
    expect(screen.getByText('$1,400–$1,800')).toBeInTheDocument();
    expect(screen.getByText(/Not yet estimated: flights/)).toBeInTheDocument();
    expect(screen.getByText(/Verdict: realistic/)).toBeInTheDocument();
  });

  it('renders open decision branches as unpriced', async () => {
    render(<QuotesPageClient />);

    await waitFor(() => {
      expect(screen.getByText('Open decision branches')).toBeInTheDocument();
    });
    expect(screen.getByText(/no price until the spine prices them/)).toBeInTheDocument();
    expect(screen.getByText('Budget-tier options')).toBeInTheDocument();
  });

  it('keeps the real workflow links (output artifacts + review queue)', async () => {
    render(<QuotesPageClient />);

    await waitFor(() => {
      expect(screen.getByText('Generate Output Artifacts')).toBeInTheDocument();
    });
    expect(screen.getByText('Quote Review Queue')).toBeInTheDocument();
  });
});

describe('QuotesPageClient not-ready + honesty (T4 supersedes FND-0260)', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(QUOTES_PAYLOAD_NOT_READY) })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders an explicit not-ready state with the missing persisted inputs', async () => {
    render(<QuotesPageClient />);

    await waitFor(() => {
      expect(screen.getByTestId('quotes-not-ready')).toBeInTheDocument();
    });
    expect(screen.getByText(/No quote yet for this trip/)).toBeInTheDocument();
    expect(screen.getByText(/strategy.recommended_option/)).toBeInTheDocument();
  });

  it('never fabricates prices, tiers, or a sample-data badge', async () => {
    render(<QuotesPageClient />);

    await waitFor(() => {
      expect(screen.getByTestId('quotes-not-ready')).toBeInTheDocument();
    });
    // The fabricated tier theater is gone — no badge, no banner, no tiers.
    expect(screen.queryByTestId('simulated-badge')).not.toBeInTheDocument();
    expect(screen.queryByTestId('quotes-sample-banner')).not.toBeInTheDocument();
    expect(screen.queryByText('Essential Saver')).not.toBeInTheDocument();
    expect(screen.queryByText('Signature Curator')).not.toBeInTheDocument();
    expect(screen.queryByText('Ultra Prestige Suite')).not.toBeInTheDocument();
    // No dollar figure can appear when quote_ready is false.
    expect(screen.queryByTestId('quote-rack-price')).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\$4,200/);
  });
});

describe('QuotesPageClient error state', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders an inline error instead of silent blankness', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })),
    );
    render(<QuotesPageClient />);

    await waitFor(() => {
      expect(screen.getByTestId('quotes-error')).toBeInTheDocument();
    });
    expect(screen.getByText(/Quote lookup failed \(500\)/)).toBeInTheDocument();
  });

  it('preserves known native cost and renders unpriced retail without a crash', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ...QUOTES_PAYLOAD_READY,
        quote_ready: false,
        quotes: [{
          ...QUOTES_PAYLOAD_READY.quotes[0], currency: 'INR', net_cost: 100000,
          rack_price: null, margin_percent: null, pricing_status: 'pricing_review',
          rack_price_basis: 'unpriced', margin_basis: 'unpriced', margin_provenance: {},
        }],
        missing: ['Native currency retail requires operator approval and evidence.'],
      }),
    }));
    render(<QuotesPageClient />);
    expect(await screen.findByTestId('quote-net-cost')).toHaveTextContent('100,000');
    expect(screen.getByTestId('quote-rack-price')).toHaveTextContent(/Pricing review/i);
    expect(screen.getByTestId('quote-margin')).toHaveTextContent(/Awaiting retail/i);
    expect(screen.getByText(/Native currency retail requires/)).toBeInTheDocument();
    expect(screen.queryByText('No quote yet for this trip')).not.toBeInTheDocument();
  });
});
