import { describe, expect, it, vi } from 'vitest';
import { buildActionRequiredItems } from '../buildActionRequiredItems';

describe('buildActionRequiredItems', () => {
  it('ranks overdue and nearer-dated trips ahead of quotes and enquiries', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-05-18T00:00:00Z'));

    const items = buildActionRequiredItems({
      workspaceTrips: [
        {
          id: 'trip_overdue',
          destination: 'Japan',
          type: 'family',
          state: 'amber',
          overdue: true,
          action: 'Customer details are still missing.',
          dateWindow: 'May 24-30, 2026',
          age: '2d',
          createdAt: '2026-05-10T00:00:00Z',
          updatedAt: '2026-05-15T00:00:00Z',
        },
        {
          id: 'trip_red_late',
          destination: 'Maldives',
          type: 'honeymoon',
          state: 'red',
          dateWindow: 'June 20-28, 2026',
          age: '1d',
          createdAt: '2026-05-12T00:00:00Z',
          updatedAt: '2026-05-17T00:00:00Z',
        },
      ],
      pendingReviews: [
        {
          id: 'review_1',
          tripId: 'trip_overdue',
          tripReference: 'TRIP-1',
          destination: 'Italy',
          tripType: 'honeymoon',
          partySize: 2,
          dateWindow: 'June 2026',
          value: 3000,
          currency: 'USD',
          agentId: 'agent_1',
          agentName: 'Agent',
          submittedAt: '2026-05-15T00:00:00Z',
          status: 'pending',
          reason: 'Awaiting owner approval.',
          riskFlags: [],
        },
      ],
      inboxTrips: [
        {
          id: 'lead_1',
          reference: 'REF-1',
          destination: 'Singapore',
          tripType: 'family',
          partySize: 4,
          dateWindow: 'July 2026',
          value: 0,
          priority: 'medium',
          priorityScore: 50,
          urgency: 40,
          importance: 50,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-16T00:00:00Z',
          lastUpdated: '2026-05-16T00:00:00Z',
          daysInCurrentStage: 2,
          slaStatus: 'on_track',
          customerName: 'Amit Shah',
          flags: [],
        },
      ],
    });

    expect(items.map((item) => item.source)).toEqual(['trip', 'trip', 'quote', 'lead']);
    expect(items[0]?.title).toBe('Trip is overdue');
    expect(items[0]?.meta).toContain('Travel');

    vi.useRealTimers();
  });

  it('does not create totals-only lead or system rows', () => {
    const items = buildActionRequiredItems({
      workspaceTrips: [],
      pendingReviews: [],
      inboxTrips: [],
    });

    expect(items).toEqual([]);
  });

  it('uses specific enquiry items when inbox item data is available', () => {
    const items = buildActionRequiredItems({
      workspaceTrips: [],
      pendingReviews: [],
      inboxTrips: [
        {
          id: 'lead_1',
          reference: 'REF-1',
          destination: 'Dubai',
          tripType: 'family',
          partySize: 5,
          dateWindow: 'June 2026',
          value: 0,
          priority: 'high',
          priorityScore: 85,
          urgency: 80,
          importance: 70,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-17T00:00:00Z',
          lastUpdated: '2026-05-17T00:00:00Z',
          daysInCurrentStage: 1,
          slaStatus: 'at_risk',
          customerName: 'Neha Kapoor',
          flags: [],
        },
      ],
    });

    expect(items).toHaveLength(1);
    expect(items[0]?.source).toBe('lead');
    expect(items[0]?.title).toBe('New enquiry waiting');
    expect(items[0]?.subtitle).toContain('Neha Kapoor');
  });

  it('limits output to max 5 specific items', () => {
    const items = buildActionRequiredItems({
      workspaceTrips: [
        { id: 't1', destination: 'A', type: 'x', state: 'red', age: '1', createdAt: '2026', updatedAt: '2026' },
        { id: 't2', destination: 'B', type: 'x', state: 'red', age: '1', createdAt: '2026', updatedAt: '2026' },
        { id: 't3', destination: 'C', type: 'x', state: 'red', age: '1', createdAt: '2026', updatedAt: '2026' },
      ],
      pendingReviews: [
        {
          id: 'review_1',
          tripId: 'trip_1',
          tripReference: 'TRIP-1',
          destination: 'Italy',
          tripType: 'honeymoon',
          partySize: 2,
          dateWindow: 'June 2026',
          value: 3000,
          currency: 'USD',
          agentId: 'agent_1',
          agentName: 'Agent',
          submittedAt: '2026-05-15T00:00:00Z',
          status: 'pending',
          reason: 'Awaiting owner approval.',
          riskFlags: [],
        },
      ],
      inboxTrips: [
        {
          id: 'lead_1',
          reference: 'REF-1',
          destination: 'Dubai',
          tripType: 'family',
          partySize: 5,
          dateWindow: 'June 2026',
          value: 0,
          priority: 'high',
          priorityScore: 85,
          urgency: 80,
          importance: 70,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-17T00:00:00Z',
          lastUpdated: '2026-05-17T00:00:00Z',
          daysInCurrentStage: 1,
          slaStatus: 'at_risk',
          customerName: 'Neha Kapoor',
          flags: [],
        },
        {
          id: 'lead_2',
          reference: 'REF-2',
          destination: 'Singapore',
          tripType: 'family',
          partySize: 4,
          dateWindow: 'July 2026',
          value: 0,
          priority: 'medium',
          priorityScore: 60,
          urgency: 55,
          importance: 60,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-16T00:00:00Z',
          lastUpdated: '2026-05-16T00:00:00Z',
          daysInCurrentStage: 2,
          slaStatus: 'on_track',
          customerName: 'Amit Shah',
          flags: [],
        },
      ],
    });

    expect(items).toHaveLength(5);
  });
});
