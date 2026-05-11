import { describe, expect, it } from 'vitest';
import {
  CURRENCY_CONFIG,
  formatMoney,
  formatMoneyCompact,
  formatMoneyObject,
  formatBudgetWithCode,
  getCurrencyOptions,
  parseBudgetString,
  parseBudgetInput,
  toBudgetInputValue,
  type BudgetInputValue,
  type Money,
} from '../currency';

describe('currency utilities', () => {
  it('formats money values with locale-aware and compact display helpers', () => {
    expect(formatMoney(200000, 'INR')).toContain('2,00,000');
    expect(formatMoneyCompact(250000, 'INR')).toContain('2.5L');
    expect(formatMoneyCompact(5400, 'USD')).toContain('5.4k');

    const money: Money = { amount: 1200, currency: 'USD' };
    expect(formatMoneyObject(money)).toContain('1,200');
    expect(formatMoneyObject(null)).toBe('-');
    expect(formatBudgetWithCode(9000, 'AED')).toMatch(/AED$/);
  });

  it('parses common agency budget strings without losing the source currency', () => {
    expect(parseBudgetString('2.5 lakh INR')).toEqual({ amount: 250000, currency: 'INR' });
    expect(parseBudgetString('5000 USD')).toEqual({ amount: 5000, currency: 'USD' });
    expect(parseBudgetString('')).toBeNull();
  });

  it('round-trips form budget input values and exposes selector options', () => {
    const input: BudgetInputValue = { amount: '15000', currency: 'SGD' };
    expect(parseBudgetInput(input)).toEqual({ amount: 15000, currency: 'SGD' });
    expect(parseBudgetInput({ amount: '0', currency: 'SGD' })).toBeNull();
    expect(toBudgetInputValue({ amount: 4800, currency: 'GBP' })).toEqual({ amount: '4800', currency: 'GBP' });

    expect(getCurrencyOptions()).toHaveLength(Object.keys(CURRENCY_CONFIG).length);
    expect(getCurrencyOptions()).toContainEqual(expect.objectContaining({ value: 'INR', label: 'Indian Rupee' }));
  });
});
