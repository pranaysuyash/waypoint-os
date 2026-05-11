import { describe, expect, it } from 'vitest';
import {
  normalizeValue,
  valuesMatch,
  calculateSimilarity,
  findFuzzyMatches,
  findNearDuplicate,
  addCustomOption,
  getGroupedOptions,
  TRIP_TYPE_OPTIONS,
  DESTINATION_OPTIONS,
  SEASON_OPTIONS,
  ACCOMMODATION_OPTIONS,
  MEAL_PLAN_OPTIONS,
  type ComboboxOption,
  type FuzzyMatch,
} from '../combobox';

describe('combobox utilities', () => {
  it('normalizes labels and compares values using title-case agency semantics', () => {
    expect(normalizeValue('  beach and culture  ')).toBe('Beach and Culture');
    expect(valuesMatch('north east', 'North East')).toBe(true);
    expect(valuesMatch('north east', 'South East')).toBe(false);
  });

  it('scores and sorts fuzzy matches for typo-tolerant field entry', () => {
    const options: ComboboxOption[] = [
      { value: 'Thailand', label: 'Thailand' },
      { value: 'Maldives', label: 'Maldives' },
      { value: 'Rajasthan', label: 'Rajasthan' },
    ];

    expect(calculateSimilarity('thailand', 'Thailand')).toBe(1);
    const matches: FuzzyMatch[] = findFuzzyMatches('Thiland', options, 0.7);
    expect(matches[0]).toMatchObject({ option: { value: 'Thailand' } });
    expect(findNearDuplicate('Maldves', options, 0.75)).toMatchObject({ value: 'Maldives' });
  });

  it('adds only genuinely custom options and keeps predefined options first', () => {
    const options: ComboboxOption[] = [
      { value: 'Hotel', label: 'Hotel' },
      { value: 'Villa', label: 'Villa' },
      { value: 'Treehouse', label: 'Treehouse', isCustom: true },
    ];

    expect(addCustomOption('hotel', options)).toMatchObject({ wasAdded: false, normalizedValue: 'Hotel' });

    const added = addCustomOption('boutique stay', options);
    expect(added.wasAdded).toBe(true);
    expect(added.normalizedValue).toBe('Boutique Stay');
    expect(getGroupedOptions(added.options).predefined.map((option) => option.value)).toEqual(['Hotel', 'Villa']);
    expect(getGroupedOptions(added.options).custom.map((option) => option.value)).toEqual(['Boutique Stay', 'Treehouse']);
  });

  it('keeps predefined travel taxonomies available as supported public inputs', () => {
    expect(TRIP_TYPE_OPTIONS).toEqual(expect.arrayContaining([expect.objectContaining({ value: 'Honeymoon' })]));
    expect(DESTINATION_OPTIONS).toEqual(expect.arrayContaining([expect.objectContaining({ value: 'Thailand' })]));
    expect(SEASON_OPTIONS).toEqual(expect.arrayContaining([expect.objectContaining({ value: 'Flexible Dates' })]));
    expect(ACCOMMODATION_OPTIONS).toEqual(expect.arrayContaining([expect.objectContaining({ value: 'Hotel' })]));
    expect(MEAL_PLAN_OPTIONS).toEqual(expect.arrayContaining([expect.objectContaining({ value: 'Breakfast' })]));
  });
});
