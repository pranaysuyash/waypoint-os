/**
 * WorkQueuePanel tests — the consumed half of invariant 4 for the work queue
 * (reachable via route-map AND rendered from the real response shape),
 * including the §14 lifecycle action surface (claim/release/dismiss/resolve).
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
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
      state: 'open',
      claimed_by: null,
      headline: 'New trip request',
      meta: ['WhatsApp', 'Trip — Bali, 2 travelers'],
      group_count: 1,
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
      state: 'claimed',
      claimed_by: 'newuser@test.com',
      headline: 'Proposal decision received',
      meta: ['by traveler_proposal_link'],
      group_count: 1,
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
  actionable: 2,
  duplicates_flagged: 1,
  returning_customers: 2,
  counts: {
    by_origin: { demand: 10, supply: 0, operator: 1, system: 1, world: 0 },
    by_intent: { new_demand: 8, answer: 1, decision: 1, info: 1, exception: 1, query: 0, meta: 0 },
    by_urgency: { high: 2, normal: 9, low: 1 },
    by_state: { open: 1, claimed: 1, resolved: 9, dismissed: 1 },
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

    // human display vocabulary (work_intake.display_for), not raw door enums
    expect(await screen.findByText('New trip request')).toBeInTheDocument();
    expect(screen.getByText('Proposal decision received')).toBeInTheDocument();
    // meta line is human; raw classification axes live only in the tooltip
    expect(screen.getByText('WhatsApp · Trip — Bali, 2 travelers')).toBeInTheDocument();
    expect(screen.getByText('by traveler_proposal_link')).toBeInTheDocument();
    expect(screen.queryByText(/explicit_user/)).not.toBeInTheDocument();
    expect(screen.getByTitle(/Classification: demand · new_demand · explicit_user/)).toBeInTheDocument();
    expect(screen.getByText('returning')).toBeInTheDocument();
    expect(screen.getByText('duplicate?')).toBeInTheDocument();
    expect(screen.getByText('money')).toBeInTheDocument();
    // claimed item shows its lifecycle badge
    expect(screen.getByText('claimed')).toBeInTheDocument();
    // honest totals header
    expect(screen.getByText('2 urgent')).toBeInTheDocument();
    expect(screen.getByLabelText('total work items').textContent).toBe('12 total');
    expect(screen.getByText(/Showing 2 of 12/)).toBeInTheDocument();
  });

  it('shows the collapse chip (×N) on grouped rows with its meaning in the tooltip', async () => {
    const base = mockQueue();
    const grouped = { ...base, items: [{ ...base.items[0], group_count: 3 }] };
    vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(grouped);
    renderPanel();

    expect(await screen.findByText('×3')).toBeInTheDocument();
    expect(
      screen.getByTitle(/3 identical items on this entity collapsed/)
    ).toBeInTheDocument();
  });

  it('shows open-item actions (Claim/Dismiss) and claimed-item actions (Resolve/Release)', async () => {
    vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(mockQueue());
    renderPanel();

    expect(await screen.findByText('New trip request')).toBeInTheDocument();
    // open row (wi_1)
    expect(screen.getAllByTitle(/Claim this item/).length).toBe(1);
    expect(screen.getAllByTitle(/Dismiss/).length).toBe(1);
    // claimed row (wi_2)
    expect(screen.getAllByTitle(/Mark resolved/).length).toBe(1);
    expect(screen.getAllByTitle(/Release the claim/).length).toBe(1);
  });

  it('claims an item through the lifecycle mutation and refetches', async () => {
    const getSpy = vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(mockQueue());
    const actSpy = vi
      .spyOn(workItemsApi, 'actOnWorkItem')
      .mockResolvedValue({ ok: true, item_id: 'wi_1', state: 'claimed' });
    renderPanel();

    fireEvent.click(await screen.findByTitle(/Claim this item/));
    await vi.waitFor(() => expect(actSpy).toHaveBeenCalledWith('wi_1', 'claim', undefined));
    // invalidation triggers a refetch of the queue
    await vi.waitFor(() => expect(getSpy.mock.calls.length).toBeGreaterThanOrEqual(2));
  });

  it('surfaces an honest error line when a lifecycle action fails', async () => {
    vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(mockQueue());
    vi.spyOn(workItemsApi, 'actOnWorkItem').mockRejectedValue(new Error('conflict'));
    renderPanel();

    // claim (direct action) fails -> honest alert
    fireEvent.click(await screen.findByTitle(/Claim this item/));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Could not claim/i);
  });

  it('opens the note editor for dismiss and submits the note with the action', async () => {
    const getSpy = vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(mockQueue());
    const actSpy = vi
      .spyOn(workItemsApi, 'actOnWorkItem')
      .mockResolvedValue({ ok: true, item_id: 'wi_1', state: 'dismissed' });
    renderPanel();

    fireEvent.click(await screen.findByTitle(/Dismiss/));
    const input = await screen.findByLabelText('Outcome note for dismiss');
    fireEvent.change(input, { target: { value: 'duplicate of an existing lead' } });
    fireEvent.click(screen.getByTitle(/Confirm dismiss/));

    await vi.waitFor(() =>
      expect(actSpy).toHaveBeenCalledWith('wi_1', 'dismiss', 'duplicate of an existing lead')
    );
    // editor closes and the queue refetches
    await vi.waitFor(() => expect(getSpy.mock.calls.length).toBeGreaterThanOrEqual(2));
    expect(screen.queryByLabelText('Outcome note for dismiss')).not.toBeInTheDocument();
  });

  it('toggles the history reader: done rows appear with state badge and no actions', async () => {
    const base = mockQueue();
    const doneItem = {
      ...base.items[0],
      item_id: 'wi_done',
      state: 'resolved' as const,
      claimed_by: null,
    };
    const getSpy = vi
      .spyOn(workItemsApi, 'getWorkItems')
      .mockImplementation(async (_limit = 8, includeDone = false) =>
        includeDone ? { ...base, items: [...base.items, doneItem] } : base
      );
    renderPanel();

    // mockQueue has by_state.resolved=9 + dismissed=1 -> toggle visible
    fireEvent.click(await screen.findByText('show 10 done'));

    await vi.waitFor(() => expect(getSpy).toHaveBeenCalledWith(8, true));
    expect(await screen.findByText('hide done')).toBeInTheDocument();
    // the done row renders with its state badge and NO action buttons
    const doneRow = screen.getByText('resolved').closest('li');
    expect(doneRow).not.toBeNull();
    expect(doneRow?.querySelector('button')).toBeNull();
  });

  it('renders the empty state when the queue has no items', async () => {
    vi.spyOn(workItemsApi, 'getWorkItems').mockResolvedValue(
      mockQueue({
        items: [],
        total: 0,
        actionable: 0,
        duplicates_flagged: 0,
        returning_customers: 0,
      })
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
