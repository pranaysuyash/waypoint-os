import { describe, expect, it } from 'vitest';
import {
  buildRepairDeepLinkHref,
  getFirstRepairableFieldName,
  resolveRepairDeepLinkField,
} from '../repair-deep-link';

/**
 * D-09: `?repair=<field>` deep-link resolution for the trip intake repair
 * surface. `?field=<...>` remains a legacy alias; machine packet-unknown names
 * map onto intake editor ids.
 */
describe('resolveRepairDeepLinkField', () => {
  it('accepts canonical planning editor ids', () => {
    expect(resolveRepairDeepLinkField('budget')).toBe('budget');
    expect(resolveRepairDeepLinkField('customerName')).toBe('customerName');
    expect(resolveRepairDeepLinkField('origin')).toBe('origin');
    expect(resolveRepairDeepLinkField('destination')).toBe('destination');
    expect(resolveRepairDeepLinkField('priorities')).toBe('priorities');
    expect(resolveRepairDeepLinkField('flexibility')).toBe('flexibility');
  });

  it('accepts inline editor ids', () => {
    expect(resolveRepairDeepLinkField('type')).toBe('type');
    expect(resolveRepairDeepLinkField('dateWindow')).toBe('dateWindow');
    expect(resolveRepairDeepLinkField('party')).toBe('party');
  });

  it('maps machine packet-unknown names onto intake editors', () => {
    expect(resolveRepairDeepLinkField('date_window')).toBe('dateWindow');
    expect(resolveRepairDeepLinkField('party_size')).toBe('party');
    expect(resolveRepairDeepLinkField('origin_city')).toBe('origin');
    expect(resolveRepairDeepLinkField('budget_raw_text')).toBe('budget');
    expect(resolveRepairDeepLinkField('destination_candidates')).toBe('destination');
    expect(resolveRepairDeepLinkField('contact_name')).toBe('customerName');
    expect(resolveRepairDeepLinkField('trip_priorities')).toBe('priorities');
    expect(resolveRepairDeepLinkField('date_flexibility')).toBe('flexibility');
  });

  it('accepts the legacy `field` param values unchanged', () => {
    expect(resolveRepairDeepLinkField('budget')).toBe('budget');
    expect(resolveRepairDeepLinkField('dateWindow')).toBe('dateWindow');
  });

  it('rejects unknown, empty, and missing values', () => {
    expect(resolveRepairDeepLinkField('not_a_field')).toBeNull();
    expect(resolveRepairDeepLinkField('')).toBeNull();
    expect(resolveRepairDeepLinkField('   ')).toBeNull();
    expect(resolveRepairDeepLinkField(null)).toBeNull();
    expect(resolveRepairDeepLinkField(undefined)).toBeNull();
  });

  it('is case-insensitive for machine names but preserves canonical ids', () => {
    expect(resolveRepairDeepLinkField('DATE_WINDOW')).toBe('dateWindow');
    expect(resolveRepairDeepLinkField('Party_Size')).toBe('party');
  });
});

describe('getFirstRepairableFieldName', () => {
  it('returns the first machine name that maps to an intake editor', () => {
    expect(getFirstRepairableFieldName(['season', 'date_window', 'party_size'])).toBe('date_window');
    expect(getFirstRepairableFieldName(['budget'])).toBe('budget');
  });

  it('returns null when nothing maps', () => {
    expect(getFirstRepairableFieldName(['season', 'travel_style'])).toBeNull();
    expect(getFirstRepairableFieldName([])).toBeNull();
    expect(getFirstRepairableFieldName(null)).toBeNull();
    expect(getFirstRepairableFieldName(undefined)).toBeNull();
  });
});

describe('buildRepairDeepLinkHref', () => {
  it('builds a canonical ?repair= href for a machine field name', () => {
    expect(buildRepairDeepLinkHref('trip_123', 'date_window')).toBe(
      '/trips/trip_123/intake?repair=dateWindow',
    );
    expect(buildRepairDeepLinkHref('trip_123', 'budget')).toBe(
      '/trips/trip_123/intake?repair=budget',
    );
  });

  it('falls back to the plain intake route for unmapped fields', () => {
    expect(buildRepairDeepLinkHref('trip_123', 'season')).toBe('/trips/trip_123/intake');
  });

  it('maps underscore machine names onto camelCase editor ids', () => {
    expect(buildRepairDeepLinkHref('trip_123', 'contact_name')).toBe(
      '/trips/trip_123/intake?repair=customerName',
    );
  });
});
