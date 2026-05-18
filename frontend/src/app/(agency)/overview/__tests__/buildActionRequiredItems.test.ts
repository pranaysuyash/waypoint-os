import { describe, expect, it } from 'vitest';
import { buildActionRequiredItems } from '../buildActionRequiredItems';

describe('buildActionRequiredItems', () => {
  it('ranks quote before trip before enquiry before system', () => {
    const items = buildActionRequiredItems({
      workspaceTrips: [
        {
          id: 'trip_1',
          destination: 'Maldives',
          type: 'honeymoon',
          state: 'red',
          age: 'Today',
          createdAt: '2026-05-18T00:00:00Z',
          updatedAt: '2026-05-18T00:00:00Z',
        },
      ],
      pendingReviews: [
        {
          id: 'review_1',
          tripId: 'trip_1',
          tripReference: 'TRIP-1',
          destination: 'Italy',
          tripType: 'honeymoon',
          partySize: 2,
          dateWindow: 'June',
          value: 3000,
          currency: 'USD',
          agentId: 'agent_1',
          agentName: 'Agent',
          submittedAt: '2026-05-18T00:00:00Z',
          status: 'pending',
          reason: 'Needs owner approval',
          riskFlags: [],
        },
      ],
      pendingReviewTotal: 2,
      inboxTotal: 3,
      integrityIssuesTotal: 1,
    });

    expect(items.map((item) => item.source)).toEqual(['quote', 'trip', 'lead', 'system']);
  });

  it('includes overdue trip item', () => {
    const items = buildActionRequiredItems({
      workspaceTrips: [
        {
          id: 'trip_overdue',
          destination: 'Japan',
          type: 'family',
          state: 'amber',
          overdue: true,
          age: '2d',
          createdAt: '2026-05-18T00:00:00Z',
          updatedAt: '2026-05-18T00:00:00Z',
        },
      ],
      pendingReviews: [],
      pendingReviewTotal: 0,
      inboxTotal: 0,
      integrityIssuesTotal: 0,
    });

    expect(items).toHaveLength(1);
    expect(items[0]?.source).toBe('trip');
    expect(items[0]?.title).toBe('Trip needs review');
  });

  it('limits output to max 5 items', () => {
    const items = buildActionRequiredItems({
      workspaceTrips: [
        { id: 't1', destination: 'A', type: 'x', state: 'red', age: '1', createdAt: '2026', updatedAt: '2026' },
        { id: 't2', destination: 'B', type: 'x', state: 'red', age: '1', createdAt: '2026', updatedAt: '2026' },
        { id: 't3', destination: 'C', type: 'x', state: 'red', age: '1', createdAt: '2026', updatedAt: '2026' },
        { id: 't4', destination: 'D', type: 'x', state: 'red', age: '1', createdAt: '2026', updatedAt: '2026' },
      ],
      pendingReviews: [],
      pendingReviewTotal: 1,
      inboxTotal: 2,
      integrityIssuesTotal: 1,
    });

    expect(items).toHaveLength(5);
  });

  it('returns empty when no actionable data exists', () => {
    const items = buildActionRequiredItems({
      workspaceTrips: [],
      pendingReviews: [],
      pendingReviewTotal: 0,
      inboxTotal: 0,
      integrityIssuesTotal: 0,
    });

    expect(items).toEqual([]);
  });
});
