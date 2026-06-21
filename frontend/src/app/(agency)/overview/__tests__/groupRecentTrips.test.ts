import { describe, expect, it } from 'vitest';
import type { Trip } from '@/lib/api-client';
import { groupTripsByOverviewSignature } from '@/lib/trip-grouping';

function trip(overrides: Partial<Trip>): Trip {
  return {
    id: overrides.id ?? 'trip_1',
    destination: overrides.destination ?? 'Bali',
    type: overrides.type ?? 'leisure',
    state: overrides.state ?? 'blue',
    age: overrides.age ?? 'Today',
    createdAt: overrides.createdAt ?? '2026-06-01T00:00:00Z',
    updatedAt: overrides.updatedAt ?? '2026-06-01T00:00:00Z',
    party: overrides.party ?? 2,
    dateWindow: overrides.dateWindow ?? 'September 2026',
    origin: overrides.origin ?? 'Mumbai',
    budget: overrides.budget ?? 'INR 300000',
    status: overrides.status ?? 'in_progress',
    contactName: overrides.contactName ?? 'Asha',
    rawInput: overrides.rawInput ?? {},
    decision: overrides.decision ?? null,
    validation: overrides.validation ?? null,
    ...overrides,
  } as Trip;
}

describe('groupTripsByOverviewSignature', () => {
  it('collapses identical overview cards into a single grouped trip', () => {
    const groups = groupTripsByOverviewSignature([
      trip({ id: 'trip_1' }),
      trip({ id: 'trip_2' }),
      trip({ id: 'trip_3', destination: 'Singapore' }),
    ]);

    expect(groups).toHaveLength(2);
    expect(groups[0]?.count).toBe(2);
    expect(groups[0]?.primaryTrip.id).toBe('trip_1');
    expect(groups[1]?.count).toBe(1);
    expect(groups[1]?.primaryTrip.id).toBe('trip_3');
  });
});
