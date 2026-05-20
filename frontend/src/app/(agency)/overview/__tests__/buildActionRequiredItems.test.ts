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
    expect(items[0]).toMatchObject({
      label: 'Trip',
      title: 'Japan family trip',
      priority: 'urgent',
      meta: 'Planning overdue',
    });
    expect(items[0]?.subtitle).toContain('Travel');

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
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-05-18T00:00:00Z'));

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
    expect(items[0]).toMatchObject({
      source: 'lead',
      label: 'Enquiry',
      title: 'Dubai family enquiry',
      priority: 'high',
      meta: 'Received 17 May · 1d waiting',
      reason: 'Qualification due soon',
    });
    expect(items[0]?.subtitle).toContain('Neha Kapoor');
    expect(items[0]?.subtitle).toContain('5 pax');
    expect(items[0]?.title).not.toBe('New enquiry waiting');

    vi.useRealTimers();
  });

  it('keeps fixture-like enquiry identifiers out of the prominent customer copy', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-05-19T00:00:00Z'));

    const items = buildActionRequiredItems({
      workspaceTrips: [],
      pendingReviews: [],
      inboxTrips: [
        {
          id: 'lead_fixture',
          reference: 'SC-901',
          destination: '',
          tripType: 'leisure',
          partySize: 1,
          dateWindow: '',
          value: 0,
          priority: 'high',
          priorityScore: 90,
          urgency: 90,
          importance: 80,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-04-23T00:00:00Z',
          lastUpdated: '2026-04-23T00:00:00Z',
          daysInCurrentStage: 26,
          slaStatus: 'breached',
          customerName: 'test_fixture_f7d9b8ef',
          flags: [],
        },
      ],
    });

    expect(items[0]).toMatchObject({
      title: 'Leisure enquiry',
      subtitle: 'Unnamed customer · 1 pax · Travel TBD · Not assigned',
      meta: 'Received 23 Apr · 26d waiting',
      reason: 'Qualification overdue',
      priority: 'urgent',
      reference: 'Ref SC-901',
      criticalityLabel: 'Breached SLA · 26d waiting',
      pendingActions: ['Qualify', 'Assign owner (26d waiting)', 'Identify customer', 'Confirm basics'],
      nextAction: 'Open oldest, assign, qualify.',
    });
    expect(`${items[0]?.title} ${items[0]?.subtitle}`).not.toContain('test_fixture_f7d9b8ef');

    vi.useRealTimers();
  });

  it('collapses repeated overdue enquiries into one group with top examples', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-05-19T00:00:00Z'));

    const items = buildActionRequiredItems({
      workspaceTrips: [],
      pendingReviews: [],
      inboxTotal: 2425,
      inboxStats: {
        total: 2425,
        unassigned: 1184,
        critical: 0,
        atRisk: 0,
        breached: 2425,
        incomplete: 932,
        missingCustomer: 1184,
        missingTripBasics: 932,
        oldestWaitingDays: 25,
        oldestUnassignedWaitingDays: 25,
        statsCoverage: 2425,
      },
      inboxTrips: [
        {
          id: 'oldest',
          reference: 'SC-901',
          destination: '',
          tripType: 'leisure',
          partySize: 1,
          dateWindow: '',
          value: 0,
          priority: 'high',
          priorityScore: 90,
          urgency: 90,
          importance: 80,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-04-24T00:00:00Z',
          lastUpdated: '2026-04-24T00:00:00Z',
          daysInCurrentStage: 25,
          slaStatus: 'breached',
          customerName: 'test_fixture_f7d9b8ef',
          flags: [],
        },
        {
          id: 'middle',
          reference: 'SC-902',
          destination: '',
          tripType: 'leisure',
          partySize: 5,
          dateWindow: 'Feb 9-14, 2026',
          value: 0,
          priority: 'high',
          priorityScore: 90,
          urgency: 90,
          importance: 80,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-05T00:00:00Z',
          lastUpdated: '2026-05-05T00:00:00Z',
          daysInCurrentStage: 14,
          slaStatus: 'breached',
          customerName: 'demo-9a33',
          flags: [],
        },
        {
          id: 'newest',
          reference: 'SC-903',
          destination: '',
          tripType: 'leisure',
          partySize: 1,
          dateWindow: '',
          value: 0,
          priority: 'high',
          priorityScore: 90,
          urgency: 90,
          importance: 80,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-08T00:00:00Z',
          lastUpdated: '2026-05-08T00:00:00Z',
          daysInCurrentStage: 11,
          slaStatus: 'breached',
          customerName: 'sample_93',
          flags: [],
        },
      ],
    });

    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({
      id: 'group-lead:Qualification overdue:urgent',
      variant: 'group',
      title: 'Overdue enquiries',
      subtitle: '2,425 enquiries in queue · 1,184 unassigned · oldest 25d waiting',
      reason: 'Qualification overdue',
      ctaLabel: 'Open oldest enquiry',
      secondaryCtaLabel: 'Open all enquiries',
      hidePriorityBadge: true,
      itemCount: 2425,
      criticalityLabel: 'Breached SLA · 2,425 breached · unassigned oldest 25d waiting',
      pendingActions: ['Qualify', 'Assign 1,184 unowned (25d waiting)', 'Identify 1,184 customers', 'Complete 932 basics'],
      nextAction: 'Open oldest, clear basics, continue by age.',
    });
    expect(items[0]?.examples).toHaveLength(2);
    expect(items[0]?.examples).toEqual([
      {
        id: 'lead-oldest',
        title: '25d waiting',
        detail: 'Unnamed customer · 1 pax · Travel TBD · Not assigned · Ref SC-901',
        href: '/inbox',
      },
      {
        id: 'lead-middle',
        title: '14d waiting',
        detail: 'Unnamed customer · 5 pax · Travel Feb 9-14, 2026 · Not assigned · Ref SC-902',
        href: '/inbox',
      },
    ]);

    vi.useRealTimers();
  });

  it('sorts breached enquiries before at-risk enquiries, then by oldest submitted date', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-05-19T00:00:00Z'));

    const items = buildActionRequiredItems({
      workspaceTrips: [],
      pendingReviews: [],
      inboxTrips: [
        {
          id: 'at_risk_old',
          reference: 'REF-1',
          destination: 'Italy',
          tripType: 'honeymoon',
          partySize: 2,
          dateWindow: 'June 2026',
          value: 0,
          priority: 'medium',
          priorityScore: 70,
          urgency: 70,
          importance: 60,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-01T00:00:00Z',
          lastUpdated: '2026-05-01T00:00:00Z',
          daysInCurrentStage: 18,
          slaStatus: 'at_risk',
          customerName: 'Riya',
          flags: [],
        },
        {
          id: 'breached_newer',
          reference: 'REF-2',
          destination: 'Japan',
          tripType: 'family',
          partySize: 4,
          dateWindow: 'July 2026',
          value: 0,
          priority: 'high',
          priorityScore: 80,
          urgency: 80,
          importance: 70,
          stage: 'new',
          stageNumber: 1,
          submittedAt: '2026-05-10T00:00:00Z',
          lastUpdated: '2026-05-10T00:00:00Z',
          daysInCurrentStage: 9,
          slaStatus: 'breached',
          customerName: 'Amit',
          flags: [],
        },
      ],
    });

    expect(items.map((item) => item.title)).toEqual(['Japan family enquiry', 'Italy honeymoon enquiry']);

    vi.useRealTimers();
  });

  it('limits output by visible work groups instead of raw records', () => {
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

    expect(items).toHaveLength(4);
    expect(items.some((item) => item.variant === 'group')).toBe(true);
    expect(items.map((item) => item.title)).toContain('Trips needing review');
  });
});
