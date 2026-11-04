// @vitest-environment jsdom

import { describe, expect, it, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CommissionStatementsTab from '../CommissionStatementsTab';

// R2-B / Travefy bar (2026-11-03): paste-in statement ingest with honest
// preview-grade labeling, manual-link fallback, and no fabricated money truth.

const BATCH = {
  batch_id: 'ci_abc123',
  source_format: 'csv',
  source_label: 'csv',
  created_at: '2026-11-04T00:00:00Z',
  durable: false,
  row_count: 2,
  matched_count: 1,
  manual_candidate_count: 1,
  unmatched_count: 0,
  rows: [
    {
      row_index: 0,
      supplier_name: 'Bali Villas Direct',
      booking_ref: 'BVD-88231',
      amount: 2400,
      currency: 'USD',
      date: '2026-10-12',
      raw_text: 'Bali Villas Direct,BVD-88231,2400.00,USD,2026-10-12',
      match_status: 'matched',
      match_trip_id: 'trip_bali',
      match_method: 'booking_ref',
      match_confidence: 0.95,
    },
    {
      row_index: 1,
      supplier_name: 'Unknown Tours',
      booking_ref: 'XT-99999',
      amount: 500,
      currency: 'USD',
      date: '2026-10-15',
      raw_text: 'Unknown Tours,XT-99999,500.00,USD,2026-10-15',
      match_status: 'manual_candidate',
      match_trip_id: null,
      match_method: null,
      match_confidence: null,
    },
  ],
  linked: {},
};

describe('CommissionStatementsTab (R2-B)', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('ingests pasted content and renders matched + manual-candidate rows', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/commission/ingest') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(BATCH) });
      }
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<CommissionStatementsTab />);
    await userEvent.type(
      screen.getByLabelText('Statement content'),
      'Bali Villas Direct,BVD-88231,2400.00,USD,2026-10-12',
    );
    await userEvent.click(screen.getByTestId('commission-ingest-submit'));

    const table = await screen.findByTestId('commission-ingest-batch');
    expect(table).toBeInTheDocument();
    expect(screen.getByText(/2 statement rows/)).toBeInTheDocument();
    expect(screen.getByText('Needs manual link')).toBeInTheDocument();
    const openTrip = screen.getByText('open trip');
    expect(openTrip).toHaveAttribute('href', '/trips/trip_bali');
    // The ingest POST carried the parsed content.
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/commission/ingest',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('links a manual candidate to a trip through the fallback endpoint', async () => {
    const calls: Array<{ url: string; body?: unknown }> = [];
    const fetchMock = vi.fn((url: string, init?: { method?: string; body?: string }) => {
      calls.push({ url, body: init?.body });
      if (url === '/api/commission/ingest') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(BATCH) });
      }
      if (url === '/api/commission/ingest/ci_abc123/link') {
        const updated = {
          ...BATCH,
          rows: BATCH.rows.map((r) =>
            r.row_index === 1
              ? { ...r, match_status: 'matched', match_trip_id: 'trip_kerala', match_method: 'manual_link' }
              : r,
          ),
          linked: { '1': 'trip_kerala' },
        };
        return Promise.resolve({ ok: true, json: () => Promise.resolve(updated) });
      }
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<CommissionStatementsTab />);
    await userEvent.type(
      screen.getByLabelText('Statement content'),
      'statement content',
    );
    await userEvent.click(screen.getByTestId('commission-ingest-submit'));
    await screen.findByTestId('commission-ingest-batch');

    await userEvent.type(screen.getByLabelText('Trip ID for row 1'), 'trip_kerala');
    await userEvent.click(screen.getByText('Link trip'));

    await waitFor(() => {
      expect(screen.getByTestId('commission-link-feedback')).toHaveTextContent(
        'Row 1 linked to trip_kerala.',
      );
    });
    expect(calls.some((c) => c.url === '/api/commission/ingest/ci_abc123/link')).toBe(true);
  });

  it('refuses to submit empty content', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    render(<CommissionStatementsTab />);
    await userEvent.click(screen.getByTestId('commission-ingest-submit'));
    expect(screen.getByRole('alert')).toHaveTextContent(/Paste the statement content first/i);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('labels candidates as preview-grade, not money truth', () => {
    vi.stubGlobal('fetch', vi.fn());
    render(<CommissionStatementsTab />);
    expect(screen.getByText(/Preview-grade candidates/i)).toBeInTheDocument();
    expect(screen.getByText(/durable payout store/i)).toBeInTheDocument();
  });
});
