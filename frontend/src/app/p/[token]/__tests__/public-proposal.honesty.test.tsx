// @vitest-environment jsdom

import { describe, expect, it, vi, afterEach, beforeEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';

/**
 * AT-20 public proposal honesty: an invalid, expired, revoked, or unreachable
 * share link must render an abstention screen — never placeholder itinerary
 * copy ("Italian Grand Tour", $5,030, "100% Verified & Protected") the
 * backend did not send.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
});

const Fabricated = () => {
  expect(screen.queryByText(/Italian Grand Tour/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/5,030/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Verified & Protected/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Our Valued Travelers/i)).not.toBeInTheDocument();
};

describe('Public proposal page honesty (AT-20)', () => {
  it('abstains with an expired/revoked notice on 410 — no fabricated itinerary', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 410,
        json: async () => ({ detail: 'share token expired' }),
      }),
    );

    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: 'tok-expired' }} />);

    await waitFor(() => {
      expect(screen.getByText(/Proposal unavailable/i)).toBeInTheDocument();
      expect(screen.getByText(/expired or was revoked/i)).toBeInTheDocument();
    });
    Fabricated();
  });

  it('abstains on network failure instead of rendering offline demo data', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('network down')),
    );

    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: 'tok-offline' }} />);

    await waitFor(() => {
      expect(screen.getByText(/could not be loaded right now/i)).toBeInTheDocument();
    });
    Fabricated();
  });

  it('renders the real proposal when the signed token resolves', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          token: 'tok-real',
          title: 'Kyoto & Osaka Family Week',
          destination: 'Japan',
          duration_days: 7,
          traveler_name: 'The Mehta Family',
          base_price_usd: 4100,
          selected_total_price_usd: 4620,
          currency: 'USD',
          status: 'sent',
          days: [],
          available_options: [],
        }),
      }),
    );

    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: 'tok-real' }} />);

    await waitFor(() => {
      expect(screen.getAllByText(/Kyoto & Osaka Family Week/i).length).toBeGreaterThan(0);
    });
    expect(screen.getByText(/Japan/)).toBeInTheDocument();
    expect(screen.getByText(/The Mehta Family/)).toBeInTheDocument();
    expect(screen.queryByText(/Italian Grand Tour/i)).not.toBeInTheDocument();
  });

  it('abstains instead of rendering $0 when a 200 payload is incomplete', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          token: 'tok-partial',
          title: 'Incomplete Proposal',
          destination: 'Nowhere',
          // selected_total_price_usd missing — the old code rendered "$0".
          duration_days: 5,
          traveler_name: 'Someone',
          days: [],
          available_options: [],
        }),
      }),
    );

    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: 'tok-partial' }} />);

    await waitFor(() => {
      expect(screen.getByText(/details are incomplete/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/\$0/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Total Package/i)).not.toBeInTheDocument();
  });

  it('badges the gated demo fixture as demo content (Part-H P1)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          token: 'prop_demo_italy_123',
          title: 'Italian Grand Tour: Rome, Florence & Amalfi',
          destination: 'Italy',
          duration_days: 8,
          traveler_name: 'Demo Traveler',
          base_price_usd: 4500,
          selected_total_price_usd: 5030,
          currency: 'USD',
          status: 'open',
          reality_tier: 'demo',
          days: [],
          available_options: [],
        }),
      }),
    );

    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: 'prop_demo_italy_123' }} />);

    await waitFor(() => {
      expect(screen.getByText(/Demo content/i)).toBeInTheDocument();
    });
  });
});
