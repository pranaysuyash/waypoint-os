import type { Trip } from '@/lib/api-client';
import { getPlanningListSummary } from '@/lib/planning-list-display';

export type TripGroup = {
  key: string;
  trips: Trip[];
  primaryTrip: Trip;
  count: number;
};

function normalize(value?: string | null): string {
  return value?.trim().toLowerCase() || '';
}

function buildTripSignature(trip: Trip): string {
  const summary = getPlanningListSummary(trip);
  return [
    normalize(summary.title),
    normalize(summary.subtitle),
    normalize(summary.statusLabel),
    normalize(summary.nextAction),
    normalize(summary.assignmentLabel),
    normalize(summary.budgetLabel),
    normalize(trip.state),
    trip.overdue ? 'overdue' : 'not-overdue',
    normalize(trip.age),
    normalize(summary.missingBadges.join('|')),
  ].join('||');
}

export function groupTripsByOverviewSignature(trips: Trip[]): TripGroup[] {
  const groups = new Map<string, TripGroup>();
  const orderedKeys: string[] = [];

  for (const trip of trips) {
    const key = buildTripSignature(trip);
    const existing = groups.get(key);
    if (existing) {
      existing.trips.push(trip);
      existing.count += 1;
      continue;
    }

    groups.set(key, {
      key,
      trips: [trip],
      primaryTrip: trip,
      count: 1,
    });
    orderedKeys.push(key);
  }

  return orderedKeys.map((key) => groups.get(key)!).filter(Boolean);
}
