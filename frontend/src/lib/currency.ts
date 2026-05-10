/**
 * Currency utilities for multi-currency budget display and recording.
 * Focuses on storing budgets in their original currency as specified.
 */

// ============================================================================
// TYPES
// ============================================================================

export type SupportedCurrency =
  | 'INR'
  | 'USD'
  | 'EUR'
  | 'GBP'
  | 'AED'
  | 'SGD'
  | 'THB'
  | 'AUD'
  | 'CAD'
  | 'JPY';

export interface Money {
  amount: number;
  currency: SupportedCurrency;
}

export interface CurrencyConfig {
  code: SupportedCurrency;
  symbol: string;
  name: string;
  locale: string;
  decimals: number;
  flag: string;
}

// ============================================================================
// CURRENCY CONFIGURATION
// ============================================================================

export const CURRENCY_CONFIG: Record<SupportedCurrency, CurrencyConfig> = {
  INR: { code: 'INR', symbol: '₹', name: 'Indian Rupee', locale: 'en-IN', decimals: 0, flag: '🇮🇳' },
  USD: { code: 'USD', symbol: '$', name: 'US Dollar', locale: 'en-US', decimals: 0, flag: '🇺🇸' },
  EUR: { code: 'EUR', symbol: '€', name: 'Euro', locale: 'de-DE', decimals: 0, flag: '🇪🇺' },
  GBP: { code: 'GBP', symbol: '£', name: 'British Pound', locale: 'en-GB', decimals: 0, flag: '🇬🇧' },
  AED: { code: 'AED', symbol: 'د.إ', name: 'UAE Dirham', locale: 'ar-AE', decimals: 0, flag: '🇦🇪' },
  SGD: { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar', locale: 'en-SG', decimals: 0, flag: '🇸🇬' },
  THB: { code: 'THB', symbol: '฿', name: 'Thai Baht', locale: 'th-TH', decimals: 0, flag: '🇹🇭' },
  AUD: { code: 'AUD', symbol: 'A$', name: 'Australian Dollar', locale: 'en-AU', decimals: 0, flag: '🇦🇺' },
  CAD: { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar', locale: 'en-CA', decimals: 0, flag: '🇨🇦' },
  JPY: { code: 'JPY', symbol: '¥', name: 'Japanese Yen', locale: 'ja-JP', decimals: 0, flag: '🇯🇵' },
};

// ============================================================================
// FORMATTING FUNCTIONS
// ============================================================================

/**
 * Format a money value with currency symbol and locale-specific formatting.
 */
const _CURRENCY_FMTS = new Map<string, Intl.NumberFormat>();
const _getFmt = (locale: string, code: string, dec: number) => {
  const k = locale + '|' + code + '|' + dec;
  let f = _CURRENCY_FMTS.get(k);
  if (!f) { f = new Intl.NumberFormat(locale, { style: 'currency', currency: code, minimumFractionDigits: dec, maximumFractionDigits: dec }); _CURRENCY_FMTS.set(k, f); }
  return f;
};

export function formatMoney(amount: number, currency: SupportedCurrency = 'INR'): string {
  const config = CURRENCY_CONFIG[currency];
  return _getFmt(config.locale, config.code, config.decimals).format(amount);
}

/**
 * Format a money value compactly (e.g., ₹2L, $5k).
 */
export function formatMoneyCompact(amount: number, currency: SupportedCurrency = 'INR'): string {
  const config = CURRENCY_CONFIG[currency];
  const absAmount = Math.abs(amount);

  let compactValue: string;
  if (absAmount >= 100000) {
    // For INR: lakhs (1L), for others: k/M
    if (currency === 'INR') {
      compactValue = `${(amount / 100000).toFixed(1)}L`;
    } else {
      compactValue = `${(amount / 1000000).toFixed(1)}M`;
    }
  } else if (absAmount >= 1000) {
    if (currency === 'INR') {
      compactValue = `${(amount / 1000).toFixed(0)}k`;
    } else {
      compactValue = `${(amount / 1000).toFixed(1)}k`;
    }
  } else {
    compactValue = amount.toFixed(0);
  }

  return `${config.symbol}${compactValue}`;
}

/**
 * Parse a budget string like "2 lac", "5000 USD", "$10k" into Money.
 * Detects currency from the string or defaults to INR.
 */
export function parseBudgetString(input: string): Money | null {
  if (!input || typeof input !== 'string') return null;

  const trimmed = input.trim().toUpperCase();

  // Try to extract currency code
  let currency: SupportedCurrency = 'INR'; // Default
  const CURRENCY_KEYS = CURRENCY_CODES;
  for (const code of CURRENCY_KEYS) {
    if (trimmed.includes(code)) {
      currency = code;
      break;
    }
  }

  // Extract number - handle formats like "2 lac", "200000", "10k", "2.5L"
  let amountStr = trimmed
    .replace(/[^\d.\-LK]/gi, '') // Remove everything except digits, dots, minus, L, K
    .replace(/L/g, '00000')
    .replace(/K/g, '000');

  // Handle "lac" specifically
  if (trimmed.includes('LAC') || trimmed.includes('LAKH')) {
    const numMatch = trimmed.match(/[\d.]+/);
    if (numMatch) {
      amountStr = (parseFloat(numMatch[0]) * 100000).toString();
    }
  }

  const amount = parseFloat(amountStr);
  if (isNaN(amount)) return null;

  return { amount, currency };
}

/**
 * Format a Money object as a display string.
 */
export function formatMoneyObject(money: Money | null | undefined): string {
  if (!money) return '-';
  return formatMoney(money.amount, money.currency);
}

/**
 * Format budget with currency code suffix for clarity.
 */
export function formatBudgetWithCode(amount: number, currency: SupportedCurrency): string {
  const formatted = formatMoney(amount, currency);
  return `${formatted} ${currency}`;
}

// ============================================================================
// CURRENCY SELECTOR OPTIONS
// ============================================================================

const CURRENCY_CODES = Object.keys(CURRENCY_CONFIG) as SupportedCurrency[];

export function getCurrencyOptions(): Array<{
  value: SupportedCurrency;
  label: string;
  symbol: string;
  flag: string;
}> {
  return Object.values(CURRENCY_CONFIG).map((config) => ({
    value: config.code,
    label: config.name,
    symbol: config.symbol,
    flag: config.flag,
  }));
}

// ============================================================================
// BUDGET INPUT COMPONENT HELPER
// ============================================================================

export interface BudgetInputValue {
  amount: string;
  currency: SupportedCurrency;
}

/**
 * Parse budget input value into Money.
 */
export function parseBudgetInput(value: BudgetInputValue): Money | null {
  const amount = parseFloat(value.amount);
  if (isNaN(amount) || amount <= 0) return null;
  return { amount, currency: value.currency };
}

/**
 * Create a budget input value from Money.
 */
export function toBudgetInputValue(money: Money): BudgetInputValue {
  return {
    amount: money.amount.toString(),
    currency: money.currency,
  };
}
