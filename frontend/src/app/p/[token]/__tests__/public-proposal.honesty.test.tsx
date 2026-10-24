// @vitest-environment jsdom

import { describe, expect, it, vi, afterEach, beforeEach } from 'vitest';
import { render, screen, waitFor, cleanup, fireEvent } from '@testing-library/react';

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

  const proposal = {
    token: 'tok-revision', trip_id: 'trip-revision',
    title: 'Kyoto Garden Journey', destination: 'Japan', duration_days: 7,
    traveler_name: 'Traveler', currency: 'INR', status: 'open',
    base_price: 125000, selected_total_price: 125000,
    base_price_usd: 125000, selected_total_price_usd: 125000,
    revision_id: 'agreement-revision-123', reality_tier: 'persisted_observed',
    days: [], available_options: [],
  };

  async function submitAcceptance() {
    fireEvent.change(screen.getByPlaceholderText('e.g. Priya Sharma'), { target: { value: 'Test Traveler' } });
    fireEvent.change(screen.getByPlaceholderText('priya@example.com'), { target: { value: 'traveler@example.test' } });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm & E-Sign Proposal' }));
  }

  it('binds acceptance to the received revision and displays native currency', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => proposal })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...proposal, status: 'accepted' }) });
    vi.stubGlobal('fetch', fetch);
    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: proposal.token }} />);
    await screen.findByPlaceholderText('e.g. Priya Sharma');
    await submitAcceptance();
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    const body = JSON.parse(fetch.mock.calls[1][1].body);
    expect(body.revision_id).toBe(proposal.revision_id);
    expect(screen.queryByText(/125,000 USD/)).not.toBeInTheDocument();
    expect(screen.getAllByText(/₹1,25,000|₹125,000/).length).toBeGreaterThan(0);
  });

  it('shows a recoverable error when the revision changed before acceptance', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => proposal })
      .mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({ detail: 'This proposal changed. Review the latest version before accepting.' }) });
    vi.stubGlobal('fetch', fetch);
    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: proposal.token }} />);
    await screen.findByPlaceholderText('e.g. Priya Sharma');
    await submitAcceptance();
    expect(await screen.findByRole('alert')).toHaveTextContent(/changed|latest version/i);
    expect(screen.queryByText('Proposal Successfully Accepted')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Review latest proposal/i })).toBeInTheDocument();
  });

  it('shows previously accepted terms when a new version needs renewed consent', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ...proposal,
        requires_reacceptance: true,
        accepted_agreement: {
          revision_id: 'older-revision', selected_total_price: 100000,
          currency: 'INR', accepted_at: '2026-10-22T10:00:00Z',
        },
      }),
    }));
    const { default: PublicProposalPage } = await import('../page');
    render(<PublicProposalPage params={{ token: proposal.token }} />);
    expect(await screen.findByText(/previously accepted/i)).toBeInTheDocument();
    expect(screen.getByText(/review.*updated.*proposal|updated.*proposal.*accept/i)).toBeInTheDocument();
    expect(screen.queryByText('Proposal Successfully Accepted')).not.toBeInTheDocument();
  });
});
