/**
 * WorkQueuePanel tests — the consumed half of invariant 4 for the work queue
 * (reachable via route-map AND rendered from the real response shape).
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WorkQueuePanel } from '../WorkQueuePanel';
import * as workItemsApi from '@/lib/work-items-api';
import type { WorkItemQueueResponse } from '@/lib/work-items-api';

const mockQueue = (overrides: Partial<WorkItemQueueResponse> = {}): WorkItemQueueResponse => ({
  ok: true,
  items: [
    {
      item_id: 'wi_1',
      received_at: '2026-10-24T10:00:00Z',
      door: 'inbound_parse',
      origin: 'demand',
      intent: 'new_demand',
      authority: 'explicit_user',
      urgency: 'high',
      channel: 'whatsapp_web',
      trip_id: 'trip_1',
      run_id: null,
      draft_id: null,
      actor: null,
      identity_known: true,
      identity_key: 'abc',
      returning_customer: true,
      memory_entity_id: 'cust_x',
      memory_fact_count: 3,
      duplicate_of: null,
      money_touch: false,
      pii_present: true,
      payload_summary: {},
    },
    {
      item_id: 'wi_2',
      received_at: '2026-10-24T09:00:00Z',
      door: 'proposal_acceptance',
      origin: 'demand',
      intent: 'decision',
      authority: 'explicit_user',
      urgency: 'normal',
      channel: 'proposal_link',
      trip_id: 'trip_2',
      run_id: null,
      draft_id: null,
      actor: 'traveler_proposal_link',
      identity_known: true,
      identity_key: 'def',
      returning_customer: false,
      memory_entity_id: null,
      memory_fact_count: 0,
      duplicate_of: 'wi_0',
      money_touch: true,
      pii_present: false,
      payload_summary: {},
    },
  ],
  total: 12,
  duplicates_flagged: 1,
  returning_customers: 2,
  counts: {
    by_origin: { demand: 10, supply: 0, operator: 1, system: 1, world: 0 },
    by_intent: { new_demand: 8, answer: 1, decision: 1, info: 1, exception: 1, query: 0, meta: 0 },
    by_urgency: { high: 2, normal: 9, low: 1 },
  },
  count_basis: 'work_item_log_total',
  ...overrides,
});

function renderPanel() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <WorkQueuePanel />
    </QueryClientProvider>
  );
}

describe('WorkQueuePanel', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders classified rows with badges from the real response shape', async () => {
    vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(mockQueue());
    renderPanel();

    expect(await screen.findByText('Inbound Parse')).toBeInTheDocument();
    expect(screen.getByText('Proposal Acceptance')).toBeInTheDocument();
    expect(screen.getByText('returning')).toBeInTheDocument();
    expect(screen.getByText('duplicate?')).toBeInTheDocument();
    expect(screen.getByText('money')).toBeInTheDocument();
    // honest totals header
    expect(screen.getByText('2 urgent')).toBeInTheDocument();
    expect(screen.getByLabelText('total work items').textContent).toBe('12 total');
    expect(screen.getByText(/Showing 2 of 12/)).toBeInTheDocument();
  });

  it('renders the empty state when the queue has no items', async () => {
    vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(
      mockQueue({ items: [], total: 0, duplicates_flagged: 0, returning_customers: 0 })
    );
    renderPanel();
    expect(await screen.findByText(/No incoming work recorded yet/i)).toBeInTheDocument();
  });

  it('degrades honestly when the queue is unavailable', async () => {
    vi.spyOn(workItemsApi, 'getWorkItems').mockRejectedValue(new Error('down'));
    renderPanel();
    expect(await screen.findByText(/Work queue unavailable/i)).toBeInTheDocument();
  });
});
