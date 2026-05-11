import { describe, expect, it } from 'vitest';
import {
  formatFieldLabel,
  formatChangeType,
  formatValue,
  getChangeDescription,
  filterChangesByField,
  filterChangesByUser,
  filterChangesByDateRange,
  getRecentChanges,
  getChangeSummary,
  type ChangeSummary,
  type FieldChange,
} from '../audit';

const changes: FieldChange[] = [
  {
    id: 'c1',
    tripId: 'trip-1',
    field: 'destination',
    changeType: 'create',
    previousValue: null,
    newValue: 'Thailand',
    changedBy: 'u1',
    changedByName: 'Asha',
    timestamp: '2026-05-01T10:00:00.000Z',
  },
  {
    id: 'c2',
    tripId: 'trip-1',
    field: 'budget',
    changeType: 'update',
    previousValue: 150000,
    newValue: 175000,
    changedBy: 'u2',
    changedByName: 'Rohan',
    timestamp: '2026-05-02T10:00:00.000Z',
  },
  {
    id: 'c3',
    tripId: 'trip-1',
    field: 'destination',
    changeType: 'restore',
    previousValue: null,
    newValue: 'Bali',
    changedBy: 'u1',
    changedByName: 'Asha',
    timestamp: '2026-05-03T10:00:00.000Z',
  },
];

describe('audit trail helpers', () => {
  it('formats field names, change types, and values for operator-readable history', () => {
    expect(formatFieldLabel('dateWindow')).toBe('Date Window');
    expect(formatChangeType('restore')).toBe('Restored');
    expect(formatValue(null)).toBe('-');
    expect(formatValue('')).toBe('(empty)');
    expect(formatValue(42)).toBe('42');
    expect(getChangeDescription(changes[1])).toBe('Changed Budget from "150000" to "175000"');
  });

  it('filters changes by field, user, and inclusive date ranges', () => {
    expect(filterChangesByField(changes, 'destination')).toHaveLength(2);
    expect(filterChangesByUser(changes, 'u1')).toHaveLength(2);
    expect(filterChangesByDateRange(changes, '2026-05-02T00:00:00.000Z', '2026-05-03T00:00:00.000Z')).toEqual([changes[1]]);
  });

  it('sorts recent changes and summarizes audit activity', () => {
    expect(getRecentChanges(changes, 2).map((change) => change.id)).toEqual(['c3', 'c2']);

    const summary: ChangeSummary = getChangeSummary(changes);
    expect(summary).toMatchObject({
      totalChanges: 3,
      changesByField: { destination: 2, budget: 1 },
      changesByUser: { u1: 2, u2: 1 },
      lastChangeAt: '2026-05-03T10:00:00.000Z',
      lastChangeBy: 'Asha',
    });
  });
});
