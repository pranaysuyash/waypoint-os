import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  MICRO_LABEL_THRESHOLD,
  computeSLAPercentage,
  formatContextualSLA,
  DEFAULT_STAGE_SLA_HOURS,
  getSLAHoursForStage,
  serializeFilters,
  deserializeFilters,
  compareTrips,
  tripMatchesQuery,
  getMetricsForProfile,
  getInboxVisitCount,
  incrementInboxVisitCount,
  shouldShowMicroLabels,
  getMicroLabel,
  getSavedViewProfile,
  saveViewProfile,
  roleToViewProfile,
  viewProfileToRole,
  type SortKey,
  type SortDirection,
} from '@/lib/inbox-helpers';
import type { InboxTrip } from '@/types/governance';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('inbox-helpers', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  // ========================================================================
  // SLA Computation
  // ========================================================================

  describe('computeSLAPercentage', () => {
    it('returns N/A for invalid SLA hours', () => {
      expect(computeSLAPercentage(6, 0)).toBe('N/A');
      expect(computeSLAPercentage(6, -1)).toBe('N/A');
    });

    it('computes percentage correctly for intake (24h)', () => {
      expect(computeSLAPercentage(6, 24)).toBe('600%');
    });

    it('computes percentage correctly for booking (336h)', () => {
      expect(computeSLAPercentage(6, 336)).toBe('43%');
    });

    it('computes percentage correctly for options (72h)', () => {
      expect(computeSLAPercentage(3, 72)).toBe('100%');
    });
  });

  describe('formatContextualSLA', () => {
    it('formats contextual SLA string', () => {
      expect(formatContextualSLA(6, 24)).toBe('6d · 600% of SLA');
      expect(formatContextualSLA(6, 336)).toBe('6d · 43% of SLA');
    });
  });

  describe('getSLAHoursForStage', () => {
    it('uses stage config when available', () => {
      const configs = [{ stage: 'intake', slaHours: 48 }];
      expect(getSLAHoursForStage('intake', configs)).toBe(48);
    });

    it('falls back to defaults', () => {
      expect(getSLAHoursForStage('intake')).toBe(24);
      expect(getSLAHoursForStage('booking')).toBe(336);
      expect(getSLAHoursForStage('unknown')).toBe(168);
    });
  });

  // ========================================================================
  // Filter Serialization
  // ========================================================================

  describe('serializeFilters', () => {
    it('serializes multi-select filters', () => {
      const filters = {
        priority: ['critical', 'high'] as const,
        stage: ['intake', 'options'],
        slaStatus: ['at_risk', 'breached'] as const,
      };
      const serialized = serializeFilters(filters);
      expect(serialized).toContain('priority=critical%2Chigh');
      expect(serialized).toContain('stage=intake%2Coptions');
      expect(serialized).toContain('slaStatus=at_risk%2Cbreached');
    });

    it('serializes value range', () => {
      const filters = { minValue: 1000, maxValue: 50000 };
      const serialized = serializeFilters(filters);
      expect(serialized).toContain('minValue=1000');
      expect(serialized).toContain('maxValue=50000');
    });

    it('omits undefined filters', () => {
      const filters = {};
      expect(serializeFilters(filters)).toBe('');
    });
  });

  describe('deserializeFilters', () => {
    it('deserializes all filter types', () => {
      const query =
        'priority=critical%2Chigh&stage=intake&assignedTo=agent-1&slaStatus=breached&minValue=1000&maxValue=50000&dateFrom=2026-01-01&dateTo=2026-12-31';
      const filters = deserializeFilters(query);

      expect(filters.priority).toEqual(['critical', 'high']);
      expect(filters.stage).toEqual(['intake']);
      expect(filters.assignedTo).toEqual(['agent-1']);
      expect(filters.slaStatus).toEqual(['breached']);
      expect(filters.minValue).toBe(1000);
      expect(filters.maxValue).toBe(50000);
      expect(filters.dateRange).toEqual({
        from: '2026-01-01',
        to: '2026-12-31',
      });
    });

    it('returns empty object for empty query', () => {
      expect(deserializeFilters('')).toEqual({});
    });
  });

  describe('serialize ↔ deserialize round-trip', () => {
    it('preserves filter state', () => {
      const original = {
        priority: ['critical'] as const,
        stage: ['intake', 'booking'],
        slaStatus: ['at_risk'] as const,
      };
      const serialized = serializeFilters(original);
      const deserialized = deserializeFilters(serialized);

      expect(deserialized.priority).toEqual(['critical']);
      expect(deserialized.stage).toEqual(['intake', 'booking']);
      expect(deserialized.slaStatus).toEqual(['at_risk']);
    });
  });

  // ========================================================================
  // Sort Helpers
  // ========================================================================

  const mockTrip = (overrides: Partial<InboxTrip> = {}): InboxTrip => ({
    id: 'TRIP-1',
    reference: 'REF-1',
    destination: 'Paris',
    tripType: 'Leisure',
    partySize: 4,
    dateWindow: 'June 2026',
    value: 10000,
    priority: 'medium',
    priorityScore: 50,
    urgency: 50,
    importance: 50,
    stage: 'intake',
    stageNumber: 1,
    submittedAt: '2026-04-23',
    lastUpdated: '2026-04-23',
    daysInCurrentStage: 3,
    slaStatus: 'on_track',
    customerName: 'Test Customer',
    flags: [],
    ...overrides,
  });

  describe('compareTrips', () => {
    it('sorts by priority descending', () => {
      const a = mockTrip({ priority: 'critical' });
      const b = mockTrip({ priority: 'low' });
      expect(compareTrips(a, b, 'priority', 'desc')).toBeLessThan(0);
      expect(compareTrips(b, a, 'priority', 'desc')).toBeGreaterThan(0);
    });

    it('sorts by value descending', () => {
      const a = mockTrip({ value: 50000 });
      const b = mockTrip({ value: 10000 });
      expect(compareTrips(a, b, 'value', 'desc')).toBeLessThan(0);
    });

    it('sorts by destination ascending', () => {
      const a = mockTrip({ destination: 'Paris' });
      const b = mockTrip({ destination: 'Zurich' });
      expect(compareTrips(a, b, 'destination', 'asc')).toBeLessThan(0);
    });

    it('sorts by SLA status ascending (breached first)', () => {
      const a = mockTrip({ slaStatus: 'breached' });
      const b = mockTrip({ slaStatus: 'on_track' });
      expect(compareTrips(a, b, 'sla', 'asc')).toBeLessThan(0);
    });
  });

  // ========================================================================
  // Search Matching
  // ========================================================================

  describe('tripMatchesQuery', () => {
    const trip = mockTrip({
      destination: 'Bali',
      customerName: 'Sharma Family',
      assignedToName: 'Alex Agent',
    });

    it('matches destination', () => {
      expect(tripMatchesQuery(trip, 'bali')).toBe(true);
    });

    it('matches customer name', () => {
      expect(tripMatchesQuery(trip, 'sharma')).toBe(true);
    });

    it('matches assigned agent name', () => {
      expect(tripMatchesQuery(trip, 'alex')).toBe(true);
    });

    it('matches trip type', () => {
      expect(tripMatchesQuery(trip, 'leisure')).toBe(true);
    });

    it('does not match non-existent field', () => {
      expect(tripMatchesQuery(trip, 'nonexistent')).toBe(false);
    });

    it('returns true for empty query', () => {
      expect(tripMatchesQuery(trip, '')).toBe(true);
      expect(tripMatchesQuery(trip, '   ')).toBe(true);
    });

    it('handles missing optional fields gracefully', () => {
      const tripWithoutAssignee = mockTrip({ assignedToName: undefined });
      expect(tripMatchesQuery(tripWithoutAssignee, 'alex')).toBe(false);
      expect(tripMatchesQuery(tripWithoutAssignee, 'paris')).toBe(true);
    });
  });

  // ========================================================================
  // View Profile Helpers
  // ========================================================================

  describe('getMetricsForProfile', () => {
    it('returns operations metrics', () => {
      expect(getMetricsForProfile('operations')).toEqual([
        'partySize',
        'dateWindow',
        'value',
        'daysInCurrentStage',
      ]);
    });

    it('returns teamLead metrics', () => {
      expect(getMetricsForProfile('teamLead')).toEqual([
        'assignedToName',
        'slaStatus',
        'daysInCurrentStage',
        'priority',
      ]);
    });

    it('returns finance metrics', () => {
      expect(getMetricsForProfile('finance')).toEqual([
        'value',
        'stage',
        'dateWindow',
        'priority',
      ]);
    });

    it('returns fulfillment metrics', () => {
      expect(getMetricsForProfile('fulfillment')).toEqual([
        'dateWindow',
        'assignedToName',
        'stage',
        'partySize',
      ]);
    });
  });

  // ========================================================================
  // Micro-Labels
  // ========================================================================

  describe('visit count tracking', () => {
    it('starts at zero', () => {
      expect(getInboxVisitCount()).toBe(0);
    });

    it('increments visit count', () => {
      incrementInboxVisitCount();
      expect(getInboxVisitCount()).toBe(1);
      incrementInboxVisitCount();
      expect(getInboxVisitCount()).toBe(2);
    });

    it('shows micro-labels when below threshold', () => {
      for (let i = 0; i < MICRO_LABEL_THRESHOLD - 1; i++) {
        incrementInboxVisitCount();
      }
      expect(shouldShowMicroLabels()).toBe(true);
    });

    it('hides micro-labels at threshold', () => {
      for (let i = 0; i < MICRO_LABEL_THRESHOLD; i++) {
        incrementInboxVisitCount();
      }
      expect(shouldShowMicroLabels()).toBe(false);
    });
  });

  describe('getMicroLabel', () => {
    it('returns labels for known values', () => {
      expect(getMicroLabel('critical')).toBe('needs human review');
      expect(getMicroLabel('intake')).toBe('just arrived');
      expect(getMicroLabel('breached')).toBe('overdue');
    });

    it('returns undefined for unknown values', () => {
      expect(getMicroLabel('unknown')).toBeUndefined();
    });
  });

  describe('View Profile Persistence', () => {
    beforeEach(() => {
      localStorageMock.clear();
    });

    it('returns undefined when no profile saved', () => {
      expect(getSavedViewProfile()).toBeUndefined();
    });

    it('saves and retrieves view profile', () => {
      saveViewProfile('teamLead');
      expect(getSavedViewProfile()).toBe('teamLead');
    });

    it('returns undefined for invalid stored profile', () => {
      localStorageMock.setItem('inbox_view_profile', 'invalid');
      expect(getSavedViewProfile()).toBeUndefined();
    });

    it('overwrites previous profile', () => {
      saveViewProfile('operations');
      saveViewProfile('finance');
      expect(getSavedViewProfile()).toBe('finance');
    });
  });

  describe('roleToViewProfile', () => {
    it('maps ops to operations', () => {
      expect(roleToViewProfile('ops')).toBe('operations');
    });

    it('maps mgr to teamLead', () => {
      expect(roleToViewProfile('mgr')).toBe('teamLead');
    });

    it('maps unknown roles to operations', () => {
      expect(roleToViewProfile('unknown')).toBe('operations');
    });
  });

  describe('viewProfileToRole', () => {
    it('maps operations to ops', () => {
      expect(viewProfileToRole('operations')).toBe('ops');
    });

    it('maps teamLead to mgr', () => {
      expect(viewProfileToRole('teamLead')).toBe('mgr');
    });

    it('maps finance to finance', () => {
      expect(viewProfileToRole('finance')).toBe('finance');
    });

    it('maps fulfillment to fulfillment', () => {
      expect(viewProfileToRole('fulfillment')).toBe('fulfillment');
    });
  });
});
