# Currency and Payments — Technical Deep Dive

> Comprehensive guide to multi-currency and international payments for the Travel Agency Agent platform

---

## Document Metadata

**Series:** Internationalization
**Document:** 3 of 4 (Currency)
**Last Updated:** 2026-04-26
**Status:** ✅ Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Multi-Currency Support](#multi-currency-support)
3. [Exchange Rate Integration](#exchange-rate-integration)
4. [Currency Conversion](#currency-conversion)
5. [Localized Payment Methods](#localized-payment-methods)
6. [Regional Payment Gateways](#regional-payment-gateways)
7. [Tax Calculation](#tax-calculation)
8. [Invoice Localization](#invoice-localization)
9. [Refund Handling](#refund-handling)
10. [Implementation](#implementation)
11. [Testing Scenarios](#testing-scenarios)
12. [API Specification](#api-specification)
13. [Metrics and Monitoring](#metrics-and-monitoring)

---

## Overview

International travel agencies must handle multiple currencies, payment methods, and tax regulations across different regions. This document covers the technical implementation of multi-currency support and localized payment processing.

### Business Context

- **Multi-Currency Pricing:** Display prices in customer's preferred currency
- **Dynamic Conversion:** Real-time exchange rate updates
- **Local Payment Methods:** Region-specific payment options (UPI, Alipay, iDEAL, etc.)
- **Tax Compliance:** VAT, GST, TCS calculation by region
- **Invoice Localization:** Tax-compliant invoices in local format

### Technical Objectives

- **Accuracy:** Precise currency conversions and tax calculations
- **Compliance:** Meet regional payment and tax regulations
- **Flexibility:** Easy to add new currencies and payment methods
- **Performance:** Fast payment processing regardless of region
- **Security:** PCI DSS compliance for all payment methods

---

## Multi-Currency Support

### Currency Configuration

```typescript
/**
 * Supported currencies
 */
enum Currency {
  USD = 'USD',    // US Dollar
  EUR = 'EUR',    // Euro
  GBP = 'GBP',    // British Pound
  CAD = 'CAD',    // Canadian Dollar
  AUD = 'AUD',    // Australian Dollar
  JPY = 'JPY',    // Japanese Yen
  INR = 'INR',    // Indian Rupee
  MXN = 'MXN',    // Mexican Peso
  BRL = 'BRL',    // Brazilian Real
  SAR = 'SAR',    // Saudi Riyal
  AED = 'AED',    // UAE Dirham
  CNY = 'CNY',    // Chinese Yuan
  CHF = 'CHF',    // Swiss Franc
}

/**
 * Currency configuration
 */
interface CurrencyConfig {
  code: Currency;
  symbol: string;
  nativeSymbol: string;
  position: 'before' | 'after';
  decimalPlaces: number;
  decimalSeparator: string;
  thousandSeparator: string;
  spaceBetween: boolean;
  regions: string[];
  roundingMode: 'up' | 'down' | 'nearest';
  precision: number;
}

/**
 * Currency configurations
 */
export const CURRENCY_CONFIGS: Record<Currency, CurrencyConfig> = {
  [Currency.USD]: {
    code: Currency.USD,
    symbol: '$',
    nativeSymbol: '$',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: false,
    regions: ['US', 'EC', 'SV', 'PA', 'PR'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.EUR]: {
    code: Currency.EUR,
    symbol: '€',
    nativeSymbol: '€',
    position: 'after', // Some countries use after
    decimalPlaces: 2,
    decimalSeparator: ',',
    thousandSeparator: '.',
    spaceBetween: false,
    regions: ['AT', 'BE', 'CY', 'EE', 'FI', 'FR', 'DE', 'GR', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PT', 'SK', 'SI', 'ES'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.GBP]: {
    code: Currency.GBP,
    symbol: '£',
    nativeSymbol: '£',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: false,
    regions: ['GB', 'IM', 'JE', 'GG'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.INR]: {
    code: Currency.INR,
    symbol: '₹',
    nativeSymbol: '₹',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: true,
    regions: ['IN', 'BT', 'NP', 'PK'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.JPY]: {
    code: Currency.JPY,
    symbol: '¥',
    nativeSymbol: '円',
    position: 'before',
    decimalPlaces: 0,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: false,
    regions: ['JP'],
    roundingMode: 'nearest',
    precision: 0
  },
  [Currency.MXN]: {
    code: Currency.MXN,
    symbol: '$',
    nativeSymbol: '$',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: false,
    regions: ['MX'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.BRL]: {
    code: Currency.BRL,
    symbol: 'R$',
    nativeSymbol: 'R$',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: ',',
    thousandSeparator: '.',
    spaceBetween: true,
    regions: ['BR'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.SAR]: {
    code: Currency.SAR,
    symbol: 'ر.س',
    nativeSymbol: 'ر.س',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: true,
    regions: ['SA'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.AED]: {
    code: Currency.AED,
    symbol: 'د.إ',
    nativeSymbol: 'د.إ',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: true,
    regions: ['AE', 'QA', 'OM', 'BH', 'KW'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.CAD]: {
    code: Currency.CAD,
    symbol: '$',
    nativeSymbol: '$',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: false,
    regions: ['CA'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.AUD]: {
    code: Currency.AUD,
    symbol: '$',
    nativeSymbol: '$',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: ',',
    spaceBetween: false,
    regions: ['AU', 'NR', 'TV', 'NF'],
    roundingMode: 'nearest',
    precision: 2
  },
  [Currency.CHF]: {
    code: Currency.CHF,
    symbol: 'CHF',
    nativeSymbol: 'CHF',
    position: 'before',
    decimalPlaces: 2,
    decimalSeparator: '.',
    thousandSeparator: "'",
    spaceBetween: true,
    regions: ['CH', 'LI', 'DE'],
    roundingMode: 'nearest',
    precision: 2
  }
};

/**
 * Get currency for locale
 */
export function getCurrencyForLocale(locale: SupportedLocale): Currency {
  const config = LOCALE_CONFIGS[locale];
  return config.currency as Currency;
}

/**
 * Get currency for region (country code)
 */
export function getCurrencyForRegion(countryCode: string): Currency {
  for (const [currency, config] of Object.entries(CURRENCY_CONFIGS)) {
    if (config.regions.includes(countryCode)) {
      return currency as Currency;
    }
  }

  return Currency.USD; // Default
}
```

### Multi-Currency Pricing

```typescript
/**
 * Multi-currency pricing manager
 */
class MultiCurrencyPricingManager {
  /**
   * Store price in multiple currencies
   */
  async storePrice(
    itemId: string,
    itemType: 'trip' | 'service' | 'addon',
    prices: Record<Currency, number>
  ): Promise<void> {
    const baseCurrency = Currency.USD;

    await db.transaction(async (tx) => {
      for (const [currency, amount] of Object.entries(prices)) {
        await tx.insert(prices).values({
          id: generateId(),
          itemId,
          itemType,
          currency: currency as Currency,
          amount,
          baseAmount: this.convertToBase(amount, currency as Currency, baseCurrency),
          baseCurrency,
          updatedAt: new Date()
        }).onConflictDoUpdate({
          target: [prices.itemId, prices.itemType, prices.currency],
          set: { amount, baseAmount, updatedAt: new Date() }
        });
      }
    });
  }

  /**
   * Get price in specific currency
   */
  async getPrice(
    itemId: string,
    itemType: 'trip' | 'service' | 'addon',
    currency: Currency
  ): Promise<number | null> {
    const price = await db.query.prices.findFirst({
      where: and(
        eq(prices.itemId, itemId),
        eq(prices.itemType, itemType),
        eq(prices.currency, currency)
      )
    });

    return price?.amount || null;
  }

  /**
   * Get price with fallback to base currency conversion
   */
  async getPriceWithFallback(
    itemId: string,
    itemType: 'trip' | 'service' | 'addon',
    currency: Currency
  ): Promise<{ amount: number; isConverted: boolean }> {
    // Try direct price
    const directPrice = await this.getPrice(itemId, itemType, currency);

    if (directPrice !== null) {
      return { amount: directPrice, isConverted: false };
    }

    // Fall back to conversion from base currency
    const basePrice = await this.getPrice(itemId, itemType, Currency.USD);

    if (basePrice === null) {
      throw new Error('Price not found');
    }

    const convertedAmount = await currencyConverter.convert(
      basePrice,
      Currency.USD,
      currency
    );

    return { amount: convertedAmount, isConverted: true };
  }

  /**
   * Update price for currency
   */
  async updatePrice(
    itemId: string,
    itemType: 'trip' | 'service' | 'addon',
    currency: Currency,
    newAmount: number
  ): Promise<void> {
    await db.update(prices)
      .set({
        amount: newAmount,
        baseAmount: this.convertToBase(newAmount, currency, Currency.USD),
        updatedAt: new Date()
      })
      .where(
        and(
          eq(prices.itemId, itemId),
          eq(prices.itemType, itemType),
          eq(prices.currency, currency)
        )
      );
  }

  /**
   * Convert to base currency
   */
  private async convertToBase(
    amount: number,
    fromCurrency: Currency,
    toCurrency: Currency
  ): Promise<number> {
    if (fromCurrency === toCurrency) return amount;

    return currencyConverter.convert(amount, fromCurrency, toCurrency);
  }
}
```

---

## Exchange Rate Integration

### Exchange Rate Provider

```typescript
/**
 * Exchange rate data
 */
interface ExchangeRate {
  from: Currency;
  to: Currency;
  rate: number;
  timestamp: Date;
  source: string;
}

/**
 * Exchange rate provider interface
 */
interface ExchangeRateProvider {
  name: string;
  getRate(from: Currency, to: Currency): Promise<number>;
  getRates(from: Currency): Promise<Record<Currency, number>>;
  refreshRates(): Promise<void>;
}

/**
 * Fixer.io provider
 */
class FixerIOProvider implements ExchangeRateProvider {
  name = 'fixer.io';
  private apiKey: string;
  private baseUrl = 'https://api.apilayer.com/fixer/latest';

  constructor() {
    this.apiKey = process.env.FIXER_API_KEY || '';
  }

  async getRate(from: Currency, to: Currency): Promise<number> {
    if (from === to) return 1;

    const response = await fetch(
      `${this.baseUrl}?base=${from}&symbols=${to}`,
      {
        headers: {
          'apikey': this.apiKey
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Fixer.io API error: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(`Fixer.io error: ${data.error?.info || 'Unknown error'}`);
    }

    return data.rates[to];
  }

  async getRates(from: Currency): Promise<Record<Currency, number>> {
    const response = await fetch(
      `${this.baseUrl}?base=${from}`,
      {
        headers: {
          'apikey': this.apiKey
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Fixer.io API error: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(`Fixer.io error: ${data.error?.info || 'Unknown error'}`);
    }

    return data.rates;
  }

  async refreshRates(): Promise<void> {
    // Fixer.io provides real-time rates, no refresh needed
  }
}

/**
 * ECB (European Central Bank) provider
 */
class ECBProvider implements ExchangeRateProvider {
  name = 'ecb';
  private baseUrl = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml';

  async getRate(from: Currency, to: Currency): Promise<number> {
    const rates = await this.getRates(from);

    if (!(to in rates)) {
      throw new Error(`Rate not available for ${to}`);
    }

    return rates[to];
  }

  async getRates(from: Currency): Promise<Record<Currency, number>> {
    // ECB only provides rates from EUR
    const response = await fetch(this.baseUrl);

    if (!response.ok) {
      throw new Error(`ECB API error: ${response.statusText}`);
    }

    const xml = await response.text();
    const rates = this.parseECBXML(xml);

    // If from is not EUR, we need to convert
    if (from !== Currency.EUR) {
      const fromRate = rates[from];
      if (!fromRate) {
        throw new Error(`Rate not available for ${from}`);
      }

      // Convert all rates from EUR to target currency
      const convertedRates: Record<Currency, number> = { [from]: 1 };

      for (const [currency, eurRate] of Object.entries(rates)) {
        convertedRates[currency as Currency] = eurRate / fromRate;
      }

      return convertedRates;
    }

    return rates;
  }

  async refreshRates(): Promise<void> {
    // ECB updates daily at 16:00 CET
  }

  private parseECBXML(xml: string): Record<Currency, number> {
    // Parse ECB XML format
    const rates: Record<Currency, number> = {};
    // XML parsing implementation
    return rates;
  }
}

/**
 * Composite exchange rate service
 */
class ExchangeRateService {
  private providers: ExchangeRateProvider[] = [];
  private cache: Map<string, { rate: number; timestamp: Date }>;
  private cacheDuration = 3600000; // 1 hour

  constructor() {
    this.providers = [
      new FixerIOProvider(),
      new ECBProvider()
    ];
    this.cache = new Map();
  }

  /**
   * Get exchange rate
   */
  async getRate(from: Currency, to: Currency): Promise<number> {
    if (from === to) return 1;

    const cacheKey = `${from}-${to}`;
    const cached = this.cache.get(cacheKey);

    if (cached && (Date.now() - cached.timestamp.getTime()) < this.cacheDuration) {
      return cached.rate;
    }

    // Try providers in order
    for (const provider of this.providers) {
      try {
        const rate = await provider.getRate(from, to);

        // Cache the result
        this.cache.set(cacheKey, { rate, timestamp: new Date() });

        // Store in database for historical tracking
        await this.storeRate(from, to, rate, provider.name);

        return rate;
      } catch (error) {
        console.warn(`Provider ${provider.name} failed:`, error);
        continue;
      }
    }

    throw new Error('All exchange rate providers failed');
  }

  /**
   * Get all rates for a currency
   */
  async getRates(from: Currency): Promise<Record<Currency, number>> {
    const rates: Record<Currency, number> = { [from]: 1 };

    // Try providers
    for (const provider of this.providers) {
      try {
        const providerRates = await provider.getRates(from);
        Object.assign(rates, providerRates);
        break;
      } catch (error) {
        console.warn(`Provider ${provider.name} failed:`, error);
        continue;
      }
    }

    return rates;
  }

  /**
   * Refresh all rates
   */
  async refreshAllRates(): Promise<void> {
    // Clear cache
    this.cache.clear();

    // Fetch from all providers
    const baseCurrencies = [Currency.USD, Currency.EUR, Currency.GBP];

    for (const base of baseCurrencies) {
      try {
        await this.getRates(base);
      } catch (error) {
        console.error(`Failed to refresh rates for ${base}:`, error);
      }
    }
  }

  /**
   * Store rate in database
   */
  private async storeRate(
    from: Currency,
    to: Currency,
    rate: number,
    source: string
  ): Promise<void> {
    await db.insert(exchangeRates).values({
      id: generateId(),
      fromCurrency: from,
      toCurrency: to,
      rate,
      source,
      timestamp: new Date()
    }).onConflictDoUpdate({
      target: [exchangeRates.fromCurrency, exchangeRates.toCurrency],
      set: { rate, source, timestamp: new Date() }
    });
  }

  /**
   * Get historical rate
   */
  async getHistoricalRate(
    from: Currency,
    to: Currency,
    date: Date
  ): Promise<number> {
    const result = await db.query.exchangeRates.findFirst({
      where: and(
        eq(exchangeRates.fromCurrency, from),
        eq(exchangeRates.toCurrency, to),
        gte(exchangeRates.timestamp, new Date(date.setHours(0, 0, 0, 0))),
        lte(exchangeRates.timestamp, new Date(date.setHours(23, 59, 59, 999)))
      ),
      orderBy: [desc(exchangeRates.timestamp)]
    });

    if (!result) {
      throw new Error(`Historical rate not found for ${from} to ${to} on ${date.toDateString()}`);
    }

    return result.rate;
  }
}

export const exchangeRateService = new ExchangeRateService();
```

---

## Currency Conversion

### Currency Converter

```typescript
/**
 * Currency converter
 */
class CurrencyConverter {
  private rateService: ExchangeRateService;

  constructor() {
    this.rateService = exchangeRateService;
  }

  /**
   * Convert amount between currencies
   */
  async convert(
    amount: number,
    from: Currency,
    to: Currency
  ): Promise<number> {
    if (from === to) return amount;

    const rate = await this.rateService.getRate(from, to);

    return this.round(amount * rate, to);
  }

  /**
   * Convert with fee
   */
  async convertWithFee(
    amount: number,
    from: Currency,
    to: Currency,
    feePercent: number = 0
  ): Promise<{ converted: number; fee: number; total: number }> {
    const rate = await this.rateService.getRate(from, to);
    const converted = this.round(amount * rate, to);
    const fee = this.round(converted * (feePercent / 100), to);
    const total = this.round(converted - fee, to);

    return { converted, fee, total };
  }

  /**
   * Round amount according to currency precision
   */
  private round(amount: number, currency: Currency): number {
    const config = CURRENCY_CONFIGS[currency];
    const precision = config.precision;
    const mode = config.roundingMode;

    const factor = Math.pow(10, precision);
    const rounded = Math.round(amount * factor) / factor;

    if (mode === 'up') {
      return Math.ceil(amount * factor) / factor;
    } else if (mode === 'down') {
      return Math.floor(amount * factor) / factor;
    }

    return rounded;
  }

  /**
   * Format converted amount
   */
  formatConverted(
    amount: number,
    currency: Currency,
    originalAmount?: number,
    originalCurrency?: Currency
  ): string {
    const formatter = new CurrencyFormatter();
    const formatted = formatter.format(amount, currency);

    if (originalAmount && originalCurrency) {
      const originalFormatted = formatter.format(originalAmount, originalCurrency);
      return `${formatted} (~${originalFormatted})`;
    }

    return formatted;
  }
}

export const currencyConverter = new CurrencyConverter();

/**
 * Currency formatter
 */
class CurrencyFormatter {
  /**
   * Format currency amount
   */
  format(amount: number, currency: Currency): string {
    const config = CURRENCY_CONFIGS[currency];

    // Round to precision
    const rounded = this.round(amount, currency);

    // Format number with separators
    const formattedNumber = this.formatNumber(rounded, config);

    // Add symbol
    if (config.position === 'before') {
      return config.symbol + (config.spaceBetween ? ' ' : '') + formattedNumber;
    } else {
      return formattedNumber + (config.spaceBetween ? ' ' : '') + config.symbol;
    }
  }

  /**
   * Format number with separators
   */
  private formatNumber(amount: number, config: CurrencyConfig): string {
    const parts = amount.toFixed(config.decimalPlaces).split('.');

    // Format integer part with thousand separator
    const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, config.thousandSeparator);

    // Combine with decimal part
    if (parts.length === 2) {
      return integerPart + config.decimalSeparator + parts[1];
    }

    return integerPart;
  }

  /**
   * Round to precision
   */
  private round(amount: number, currency: Currency): number {
    const config = CURRENCY_CONFIGS[currency];
    const factor = Math.pow(10, config.precision);
    return Math.round(amount * factor) / factor;
  }
}
```

---

## Localized Payment Methods

### Payment Method Configuration

```typescript
/**
 * Supported payment methods by region
 */
enum PaymentMethodType {
  CARD = 'card',                    // Credit/debit cards
  BANK_TRANSFER = 'bank_transfer',  // Bank transfer
  WALLET = 'wallet',                // Digital wallets
  CASH = 'cash',                    // Cash payments
  BNPL = 'bnpl',                    // Buy now, pay later
  DIRECT_DEBIT = 'direct_debit',    // Direct debit
  VOUCHER = 'voucher',              // Payment vouchers
  CRYPTO = 'crypto'                 // Cryptocurrency
}

/**
 * Payment method configuration
 */
interface PaymentMethodConfig {
  type: PaymentMethodType;
  name: string;
  regions: string[];
  currencies: Currency[];
  minAmount?: number;
  maxAmount?: number;
  fees: {
    fixed: number;
    percent: number;
    currency: Currency;
  };
  processingTime: string;
  requiresVerification: boolean;
  supportedGateways: string[];
}

/**
 * Payment method configurations
 */
export const PAYMENT_METHODS: Record<string, PaymentMethodConfig> = {
  // Credit/debit cards (global)
  visa: {
    type: PaymentMethodType.CARD,
    name: 'Visa',
    regions: [], // All regions
    currencies: Object.values(Currency),
    fees: { fixed: 0.30, percent: 2.9, currency: Currency.USD },
    processingTime: 'Instant',
    requiresVerification: true,
    supportedGateways: ['stripe', 'adyen', 'braintree']
  },
  mastercard: {
    type: PaymentMethodType.CARD,
    name: 'Mastercard',
    regions: [],
    currencies: Object.values(Currency),
    fees: { fixed: 0.30, percent: 2.9, currency: Currency.USD },
    processingTime: 'Instant',
    requiresVerification: true,
    supportedGateways: ['stripe', 'adyen', 'braintree']
  },

  // India
  upi: {
    type: PaymentMethodType.WALLET,
    name: 'UPI',
    regions: ['IN'],
    currencies: [Currency.INR],
    minAmount: 1,
    maxAmount: 100000,
    fees: { fixed: 0, percent: 0, currency: Currency.INR },
    processingTime: 'Instant',
    requiresVerification: false,
    supportedGateways: ['razorpay', 'cashfree', 'stripe']
  },
  paytm: {
    type: PaymentMethodType.WALLET,
    name: 'Paytm',
    regions: ['IN'],
    currencies: [Currency.INR],
    fees: { fixed: 0, percent: 2, currency: Currency.INR },
    processingTime: 'Instant',
    requiresVerification: false,
    supportedGateways: ['razorpay', 'paytm']
  },

  // Brazil
  pix: {
    type: PaymentMethodType.WALLET,
    name: 'PIX',
    regions: ['BR'],
    currencies: [Currency.BRL],
    minAmount: 1,
    maxAmount: 50000,
    fees: { fixed: 0, percent: 0.99, currency: Currency.BRL },
    processingTime: 'Instant',
    requiresVerification: false,
    supportedGateways: ['stripe', 'adyen', 'mercadopago']
  },
  boleto: {
    type: PaymentMethodType.VOUCHER,
    name: 'Boleto',
    regions: ['BR'],
    currencies: [Currency.BRL],
    minAmount: 5,
    maxAmount: 50000,
    fees: { fixed: 1.50, percent: 1.5, currency: Currency.BRL },
    processingTime: '1-3 business days',
    requiresVerification: false,
    supportedGateways: ['stripe', 'mercadopago', 'adyen']
  },

  // Europe
  sepa: {
    type: PaymentMethodType.DIRECT_DEBIT,
    name: 'SEPA Direct Debit',
    regions: ['AT', 'BE', 'CY', 'EE', 'FI', 'FR', 'DE', 'GR', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PT', 'SK', 'SI', 'ES'],
    currencies: [Currency.EUR],
    minAmount: 1,
    maxAmount: 1000000,
    fees: { fixed: 0.50, percent: 0.5, currency: Currency.EUR },
    processingTime: '5-7 business days',
    requiresVerification: true,
    supportedGateways: ['stripe', 'adyen', 'go_cardless']
  },
  ideal: {
    type: PaymentMethodType.WALLET,
    name: 'iDEAL',
    regions: ['NL'],
    currencies: [Currency.EUR],
    fees: { fixed: 0.30, percent: 0.8, currency: Currency.EUR },
    processingTime: 'Instant',
    requiresVerification: false,
    supportedGateways: ['stripe', 'adyen', 'mollie']
  },
  giropay: {
    type: PaymentMethodType.WALLET,
    name: 'Giropay',
    regions: ['DE'],
    currencies: [Currency.EUR],
    fees: { fixed: 0.30, percent: 1.0, currency: Currency.EUR },
    processingTime: 'Instant',
    requiresVerification: false,
    supportedGateways: ['adyen', 'stripe']
  },

  // UK
  bacs: {
    type: PaymentMethodType.BANK_TRANSFER,
    name: 'BACS',
    regions: ['GB'],
    currencies: [Currency.GBP],
    minAmount: 10,
    maxAmount: 500000,
    fees: { fixed: 0.20, percent: 0, currency: Currency.GBP },
    processingTime: '3-5 business days',
    requiresVerification: true,
    supportedGateways: ['go_cardless', 'adyen']
  },

  // China
  alipay: {
    type: PaymentMethodType.WALLET,
    name: 'Alipay',
    regions: ['CN'],
    currencies: [Currency.CNY],
    fees: { fixed: 0, percent: 0.55, currency: Currency.CNY },
    processingTime: 'Instant',
    requiresVerification: false,
    supportedGateways: ['adyen', 'stripe', 'alipay']
  },
  wechat_pay: {
    type: PaymentMethodType.WALLET,
    name: 'WeChat Pay',
    regions: ['CN'],
    currencies: [Currency.CNY],
    fees: { fixed: 0, percent: 0.6, currency: Currency.CNY },
    processingTime: 'Instant',
    requiresVerification: false,
    supportedGateways: ['adyen', 'stripe']
  },

  // Mexico
  oxxo: {
    type: PaymentMethodType.VOUCHER,
    name: 'OXXO',
    regions: ['MX'],
    currencies: [Currency.MXN],
    minAmount: 10,
    maxAmount: 10000,
    fees: { fixed: 5, percent: 1.2, currency: Currency.MXN },
    processingTime: 'Instant (barcode), 1-3 days (payment)',
    requiresVerification: false,
    supportedGateways: ['stripe', 'mercadopago']
  },

  // Saudi Arabia / UAE
  mada: {
    type: PaymentMethodType.CARD,
    name: 'Mada',
    regions: ['SA'],
    currencies: [Currency.SAR],
    fees: { fixed: 0.50, percent: 1.5, currency: Currency.SAR },
    processingTime: 'Instant',
    requiresVerification: true,
    supportedGateways: ['adyen', 'checkout', 'tap']
  },

  // Buy now, pay later
  klarna: {
    type: PaymentMethodType.BNPL,
    name: 'Klarna',
    regions: ['AT', 'BE', 'DK', 'FI', 'FR', 'DE', 'IE', 'IT', 'NL', 'NO', 'ES', 'SE', 'GB', 'US'],
    currencies: [Currency.USD, Currency.EUR, Currency.GBP, Currency.SEK, Currency.NOK, Currency.DKK],
    minAmount: 10,
    maxAmount: 10000,
    fees: { fixed: 0, percent: 4.29, currency: Currency.USD },
    processingTime: 'Instant',
    requiresVerification: true,
    supportedGateways: ['klarna', 'stripe', 'adyen']
  },
  affirm: {
    type: PaymentMethodType.BNPL,
    name: 'Affirm',
    regions: ['US', 'CA'],
    currencies: [Currency.USD, Currency.CAD],
    minAmount: 50,
    maxAmount: 30000,
    fees: { fixed: 0, percent: 5.99, currency: Currency.USD },
    processingTime: 'Instant',
    requiresVerification: true,
    supportedGateways: ['affirm', 'stripe', 'adyen']
  }
};

/**
 * Get payment methods for region
 */
export function getPaymentMethodsForRegion(
  regionCode: string,
  currency: Currency
): PaymentMethodConfig[] {
  return Object.values(PAYMENT_METHODS).filter(method =>
    (method.regions.length === 0 || method.regions.includes(regionCode)) &&
    method.currencies.includes(currency)
  );
}
```

---

## Regional Payment Gateways

### Gateway Configuration

```typescript
/**
 * Payment gateway interface
 */
interface PaymentGateway {
  name: string;
  regions: string[];
  currencies: Currency[];
  methods: PaymentMethodType[];

  initialize(config: Record<string, unknown>): Promise<void>;
  createPaymentIntent(request: PaymentRequest): Promise<PaymentIntent>;
  confirmPayment(intentId: string, data: Record<string, unknown>): Promise<PaymentResult>;
  refundPayment(transactionId: string, amount?: number): Promise<RefundResult>;
  webhookVerify(signature: string, payload: string): Promise<boolean>;
}

/**
 * Payment gateway registry
 */
class PaymentGatewayRegistry {
  private gateways: Map<string, PaymentGateway>;

  constructor() {
    this.gateways = new Map();
    this.registerGateways();
  }

  private registerGateways(): void {
    // Stripe (global)
    this.register(new StripeGateway());

    // Adyen (global)
    this.register(new AdyenGateway());

    // Razorpay (India)
    this.register(new RazorpayGateway());

    // Mercado Pago (Latin America)
    this.register(new MercadoPagoGateway());

    // GoCardless (Europe - SEPA, BACS)
    this.register(new GoCardlessGateway());
  }

  register(gateway: PaymentGateway): void {
    this.gateways.set(gateway.name.toLowerCase(), gateway);
  }

  get(name: string): PaymentGateway | undefined {
    return this.gateways.get(name.toLowerCase());
  }

  /**
   * Get available gateways for region and currency
   */
  getAvailableGateways(regionCode: string, currency: Currency): PaymentGateway[] {
    return Array.from(this.gateways.values()).filter(gateway =>
      (gateway.regions.length === 0 || gateway.regions.includes(regionCode)) &&
      gateway.currencies.includes(currency)
    );
  }
}

export const paymentGatewayRegistry = new PaymentGatewayRegistry();

/**
 * Stripe gateway implementation
 */
class StripeGateway implements PaymentGateway {
  name = 'Stripe';
  regions: string[] = []; // Global
  currencies: Currency[] = Object.values(Currency);
  methods: PaymentMethodType[] = [PaymentMethodType.CARD, PaymentMethodType.BNPL];

  private client: any;

  async initialize(config: Record<string, unknown>): Promise<void> {
    const Stripe = await import('stripe');
    this.client = new Stripe.default(config.apiKey as string);
  }

  async createPaymentIntent(request: PaymentRequest): Promise<PaymentIntent> {
    const intent = await this.client.paymentIntents.create({
      amount: Math.round(request.amount * 100), // Convert to cents
      currency: request.currency.toLowerCase(),
      customer: request.customerId,
      metadata: request.metadata,
      payment_method_types: this.getStripePaymentMethods(request.paymentMethod)
    });

    return {
      id: intent.id,
      clientSecret: intent.client_secret,
      amount: intent.amount / 100,
      currency: intent.currency.toUpperCase(),
      status: intent.status,
      requiresAction: intent.next_action !== null
    };
  }

  async confirmPayment(intentId: string, data: Record<string, unknown>): Promise<PaymentResult> {
    const intent = await this.client.paymentIntents.confirm(intentId, {
      payment_method: data.payment_method as string
    });

    return {
      success: intent.status === 'succeeded',
      transactionId: intent.id,
      amount: intent.amount / 100,
      currency: intent.currency.toUpperCase(),
      status: intent.status,
      failureCode: intent.last_payment_error?.code,
      failureMessage: intent.last_payment_error?.message
    };
  }

  async refundPayment(transactionId: string, amount?: number): Promise<RefundResult> {
    const refund = await this.client.refunds.create({
      payment_intent: transactionId,
      amount: amount ? Math.round(amount * 100) : undefined
    });

    return {
      id: refund.id,
      amount: refund.amount / 100,
      currency: refund.currency.toUpperCase(),
      status: refund.status,
      createdAt: new Date(refund.created * 1000)
    };
  }

  async webhookVerify(signature: string, payload: string): Promise<boolean> {
    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

    try {
      const Stripe = await import('stripe');
      const stripe = new Stripe.default(process.env.STRIPE_API_KEY!);

      stripe.webhooks.constructEvent(
        payload,
        signature,
        webhookSecret!
      );

      return true;
    } catch {
      return false;
    }
  }

  private getStripePaymentMethods(method: PaymentMethodType): string[] {
    const mapping: Record<PaymentMethodType, string[]> = {
      [PaymentMethodType.CARD]: ['card'],
      [PaymentMethodType.BNPL]: ['klarna', 'affirm', 'afterpay_clearpay'],
      [PaymentMethodType.WALLET]: ['alipay', 'wechat_pay'],
      [PaymentMethodType.BANK_TRANSFER]: ['sepa_debit'],
      [PaymentMethodType.DIRECT_DEBIT]: ['bacs_debit', 'sepa_debit']
    };

    return mapping[method] || ['card'];
  }
}
```

---

## Tax Calculation

### Regional Tax Configuration

```typescript
/**
 * Tax types
 */
enum TaxType {
  VAT = 'vat',           // Value Added Tax (Europe)
  GST = 'gst',           // Goods and Services Tax (Canada, India, Australia)
  SALES_TAX = 'sales',   // Sales Tax (US)
  TCS = 'tcs',           // Tax Collected at Source (India)
  TDS = 'tds',           // Tax Deducted at Source (India)
  IGV = 'igv',           // Impuesto General a las Ventas (Peru)
  NONE = 'none'          // No tax
}

/**
 * Tax configuration
 */
interface TaxConfig {
  type: TaxType;
  country: string;
  rate: number;           // Percentage
  region?: string;        // For regional variations
  appliesTo: string[];    // What the tax applies to
  isInclusive: boolean;   // Whether tax is included in displayed price
  registration?: string;  // Tax registration number format
  reverseCharge: boolean; // Whether reverse charge applies
}

/**
 * Tax configurations by country
 */
export const TAX_CONFIGS: TaxConfig[] = [
  // United States - Sales tax (varies by state)
  {
    type: TaxType.SALES_TAX,
    country: 'US',
    rate: 0, // Varies by state/county
    appliesTo: ['services', 'goods'],
    isInclusive: false,
    reverseCharge: false
  },

  // United Kingdom - VAT
  {
    type: TaxType.VAT,
    country: 'GB',
    rate: 20,
    appliesTo: ['services', 'goods'],
    isInclusive: true,
    registration: 'GB\\d{9}',
    reverseCharge: false
  },

  // Germany - VAT
  {
    type: TaxType.VAT,
    country: 'DE',
    rate: 19,
    appliesTo: ['services', 'goods'],
    isInclusive: true,
    registration: 'DE\\d{9}',
    reverseCharge: true
  },

  // France - VAT
  {
    type: TaxType.VAT,
    country: 'FR',
    rate: 20,
    appliesTo: ['services', 'goods'],
    isInclusive: true,
    registration: 'FR\\d{11}',
    reverseCharge: true
  },

  // India - GST
  {
    type: TaxType.GST,
    country: 'IN',
    rate: 18,
    appliesTo: ['services', 'goods'],
    isInclusive: false,
    registration: '\\d{2}[A-Z]{5}[A-Z0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}',
    reverseCharge: true
  },

  // India - TCS for international travel
  {
    type: TaxType.TCS,
    country: 'IN',
    rate: 5,
    appliesTo: ['international_travel'],
    isInclusive: false,
    reverseCharge: false
  },

  // Canada - GST
  {
    type: TaxType.GST,
    country: 'CA',
    rate: 5,
    appliesTo: ['services', 'goods'],
    isInclusive: false,
    registration: '\\d{9}-RT\\d{4}',
    reverseCharge: false
  },

  // Australia - GST
  {
    type: TaxType.GST,
    country: 'AU',
    rate: 10,
    appliesTo: ['services', 'goods'],
    isInclusive: true,
    registration: '\\d{2}\\d{7}\\d{2}',
    reverseCharge: false
  },

  // Brazil - Regional variations
  {
    type: TaxType.SALES_TAX,
    country: 'BR',
    rate: 0, // Varies by state
    appliesTo: ['services', 'goods'],
    isInclusive: false,
    reverseCharge: false
  },

  // Saudi Arabia - VAT
  {
    type: TaxType.VAT,
    country: 'SA',
    rate: 15,
    appliesTo: ['services', 'goods'],
    isInclusive: true,
    registration: '\\d{15}',
    reverseCharge: false
  },

  // UAE - VAT
  {
    type: TaxType.VAT,
    country: 'AE',
    rate: 5,
    appliesTo: ['services', 'goods'],
    isInclusive: true,
    registration: '\\d{15}',
    reverseCharge: false
  },

  // Mexico - IVA
  {
    type: TaxType.VAT,
    country: 'MX',
    rate: 16,
    appliesTo: ['services', 'goods'],
    isInclusive: false,
    registration: '[A-ZÑ&]{3,4}\\d{6}[A-Z\\d]{3}',
    reverseCharge: false
  }
];

/**
 * Tax calculator
 */
class TaxCalculator {
  /**
   * Calculate tax for booking
   */
  async calculateTax(
    amount: number,
    currency: Currency,
    country: string,
    itemType: 'service' | 'good' | 'international_travel',
    customerTaxId?: string,
    businessPurchase = false
  ): Promise<TaxCalculation> {
    const config = this.getTaxConfig(country, itemType);

    // Check for tax exemption
    if (this.isExempt(customerTaxId, businessPurchase, config)) {
      return {
        amount,
        currency,
        taxAmount: 0,
        taxRate: 0,
        taxType: TaxType.NONE,
        isInclusive: false,
        total: amount
      };
    }

    // Calculate tax
    const taxRate = config.rate / 100;
    let taxAmount: number;

    if (config.isInclusive) {
      // Tax is included in amount
      taxAmount = (amount * taxRate) / (1 + taxRate);
    } else {
      // Tax is added to amount
      taxAmount = amount * taxRate;
    }

    // Round to currency precision
    taxAmount = this.round(taxAmount, currency);

    const total = config.isInclusive ? amount : amount + taxAmount;

    return {
      amount,
      currency,
      taxAmount: this.round(taxAmount, currency),
      taxRate: config.rate,
      taxType: config.type,
      isInclusive: config.isInclusive,
      total: this.round(total, currency),
      country
    };
  }

  /**
   * Get tax configuration for country
   */
  private getTaxConfig(country: string, itemType: string): TaxConfig {
    const config = TAX_CONFIGS.find(c =>
      c.country === country &&
      c.appliesTo.includes(itemType)
    );

    return config || {
      type: TaxType.NONE,
      country,
      rate: 0,
      appliesTo: [],
      isInclusive: false,
      reverseCharge: false
    };
  }

  /**
   * Check if purchase is tax exempt
   */
  private isExempt(
    customerTaxId: string | undefined,
    businessPurchase: boolean,
    config: TaxConfig
  ): boolean {
    // Reverse charge applies for B2B in some regions
    if (config.reverseCharge && businessPurchase && customerTaxId) {
      return true;
    }

    return false;
  }

  /**
   * Round to currency precision
   */
  private round(amount: number, currency: Currency): number {
    const config = CURRENCY_CONFIGS[currency];
    const factor = Math.pow(10, config.precision);
    return Math.round(amount * factor) / factor;
  }

  /**
   * Format tax for invoice
   */
  formatTax(calculation: TaxCalculation, locale: SupportedLocale): string {
    const { t } = i18n;
    const config = LOCALE_CONFIGS[locale];

    const formatter = new CurrencyFormatter();

    if (calculation.taxRate === 0) {
      return t('tax.exempt');
    }

    const taxAmount = formatter.format(calculation.taxAmount, calculation.currency as Currency);
    const taxType = this.getTaxTypeName(calculation.taxType, locale);

    return `${taxType} (${calculation.taxRate}%): ${taxAmount}`;
  }

  /**
   * Get localized tax type name
   */
  private getTaxTypeName(type: TaxType, locale: SupportedLocale): string {
    const names: Record<TaxType, Record<string, string>> = {
      [TaxType.VAT]: {
        'en-US': 'VAT',
        'es-ES': 'IVA',
        'de-DE': 'MwSt',
        'fr-FR': 'TVA'
      },
      [TaxType.GST]: {
        'en-US': 'GST',
        'en-CA': 'GST',
        'en-IN': 'GST',
        'en-AU': 'GST'
      },
      [TaxType.SALES_TAX]: {
        'en-US': 'Sales Tax',
        'es-MX': 'IVA',
        'pt-BR': 'Imposto'
      },
      [TaxType.TCS]: {
        'en-IN': 'TCS',
        'hi-IN': 'स्रोत पर कर संग्रह'
      },
      [TaxType.NONE]: {
        '*': 'No Tax'
      }
    };

    return names[type]?.[locale] || names[type]?.['*'] || type;
  }
}

export const taxCalculator = new TaxCalculator();

interface TaxCalculation {
  amount: number;
  currency: Currency;
  taxAmount: number;
  taxRate: number;
  taxType: TaxType;
  isInclusive: boolean;
  total: number;
  country?: string;
}
```

---

## Invoice Localization

### Invoice Template by Region

```typescript
/**
 * Invoice configuration by region
 */
interface InvoiceConfig {
  country: string;
  locale: SupportedLocale;
  currency: Currency;
  dateFormat: string;
  addressFormat: 'vertical' | 'horizontal';
  showTaxId: boolean;
  showVatNumber: boolean;
  showPurchaseOrder: boolean;
  taxLabel: string;
  paymentTerms: string[];
  requiredFields: string[];
  bankDetailsFormat: 'iban' | 'aba' | 'bic';
}

/**
 * Invoice configurations
 */
export const INVOICE_CONFIGS: Record<string, InvoiceConfig> = {
  'US': {
    country: 'US',
    locale: 'en-US',
    currency: Currency.USD,
    dateFormat: 'MM/DD/YYYY',
    addressFormat: 'vertical',
    showTaxId: false,
    showVatNumber: false,
    showPurchaseOrder: true,
    taxLabel: 'Sales Tax',
    paymentTerms: ['Net 15', 'Net 30', 'Due on Receipt'],
    requiredFields: ['invoice_number', 'date', 'due_date', 'items', 'total'],
    bankDetailsFormat: 'aba'
  },
  'GB': {
    country: 'GB',
    locale: 'en-GB',
    currency: Currency.GBP,
    dateFormat: 'DD/MM/YYYY',
    addressFormat: 'vertical',
    showTaxId: true,
    showVatNumber: true,
    showPurchaseOrder: true,
    taxLabel: 'VAT',
    paymentTerms: ['30 Days', '60 Days'],
    requiredFields: ['invoice_number', 'date', 'due_date', 'vat_number', 'items', 'subtotal', 'vat', 'total'],
    bankDetailsFormat: 'iban'
  },
  'DE': {
    country: 'DE',
    locale: 'de-DE',
    currency: Currency.EUR,
    dateFormat: 'DD.MM.YYYY',
    addressFormat: 'horizontal',
    showTaxId: true,
    showVatNumber: true,
    showPurchaseOrder: true,
    taxLabel: 'MwSt',
    paymentTerms: ['14 Tage', '30 Tage'],
    requiredFields: ['invoice_number', 'date', 'due_date', 'vat_number', 'items', 'subtotal', 'vat', 'total'],
    bankDetailsFormat: 'iban'
  },
  'IN': {
    country: 'IN',
    locale: 'hi-IN',
    currency: Currency.INR,
    dateFormat: 'DD/MM/YYYY',
    addressFormat: 'vertical',
    showTaxId: true,
    showVatNumber: false,
    showPurchaseOrder: true,
    taxLabel: 'GST',
    paymentTerms: ['30 Days', '60 Days', '90 Days'],
    requiredFields: ['invoice_number', 'date', 'due_date', 'gst_number', 'pan_number', 'items', 'subtotal', 'cgst', 'sgst', 'total'],
    bankDetailsFormat: 'aba'
  },
  'BR': {
    country: 'BR',
    locale: 'pt-BR',
    currency: Currency.BRL,
    dateFormat: 'DD/MM/YYYY',
    addressFormat: 'vertical',
    showTaxId: true,
    showVatNumber: false,
    showPurchaseOrder: true,
    taxLabel: 'NF-e',
    paymentTerms: ['30 dias', '60 dias'],
    requiredFields: ['invoice_number', 'date', 'due_date', 'cnpj', 'items', 'subtotal', 'impostos', 'total'],
    bankDetailsFormat: 'aba'
  }
};

/**
 * Localized invoice generator
 */
class LocalizedInvoiceGenerator {
  /**
   * Generate invoice for booking
   */
  async generateInvoice(
    bookingId: string,
    locale: SupportedLocale,
    currency: Currency
  ): Promise<Invoice> {
    const booking = await db.query.bookings.findFirst({
      where: eq(bookings.id, bookingId)
    });

    if (!booking) throw new Error('Booking not found');

    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, booking.tenantId)
    });

    const customer = await db.query.customers.findFirst({
      where: eq(customers.id, booking.customerId)
    });

    const config = this.getInvoiceConfig(tenant!.country);
    const taxCalc = await taxCalculator.calculateTax(
      booking.totalAmount,
      currency,
      tenant!.country,
      'service'
    );

    const invoiceNumber = this.generateInvoiceNumber(tenant!.id, booking.id);

    const invoice: Invoice = {
      invoiceNumber,
      locale,
      currency,
      date: new Date(),
      dueDate: this.calculateDueDate(new Date(), config.paymentTerms[0]),
      from: {
        name: tenant!.name,
        address: tenant!.address,
        taxId: tenant!.taxId,
        vatNumber: tenant!.vatNumber,
        registrationNumber: tenant!.registrationNumber,
        bankDetails: tenant!.bankDetails
      },
      to: {
        name: `${customer!.firstName} ${customer!.lastName}`,
        address: customer!.address,
        taxId: customer!.taxId,
        vatNumber: customer!.vatNumber
      },
      items: await this.getInvoiceItems(booking, locale, currency),
      subtotal: booking.totalAmount,
      tax: taxCalc,
      total: taxCalc.total,
      paymentTerms: config.paymentTerms[0],
      notes: this.getLocalizedNotes(locale, config),
      config
    };

    return invoice;
  }

  /**
   * Generate invoice PDF
   */
  async generateInvoicePDF(invoice: Invoice): Promise<Buffer> {
    const template = await this.loadInvoiceTemplate(invoice.config.country);
    const html = this.renderInvoiceTemplate(invoice, template);

    const pdf = await this.htmlToPDF(html, invoice.config);

    return pdf;
  }

  /**
   * Get invoice items from booking
   */
  private async getInvoiceItems(
    booking: Booking,
    locale: SupportedLocale,
    currency: Currency
  ): Promise<InvoiceItem[]> {
    const items = await db.query.bookingItems.findMany({
      where: eq(bookingItems.bookingId, booking.id)
    });

    return items.map(item => ({
      description: this.translateItemDescription(item.description, locale),
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      total: item.quantity * item.unitPrice,
      currency
    }));
  }

  /**
   * Translate item description
   */
  private translateItemDescription(description: string, locale: SupportedLocale): string {
    // Try to translate using content translation service
    return contentTranslationService.translate(description, locale);
  }

  /**
   * Get localized notes
   */
  private getLocalizedNotes(locale: SupportedLocale, config: InvoiceConfig): string[] {
    const notes: string[] = [];

    // Payment terms
    notes.push(i18n.t('invoice.paymentTerms', { terms: config.paymentTerms[0] }));

    // Thank you message
    notes.push(i18n.t('invoice.thankYou'));

    // Contact information
    notes.push(i18n.t('invoice.contact'));

    return notes;
  }

  private getInvoiceConfig(country: string): InvoiceConfig {
    return INVOICE_CONFIGS[country] || INVOICE_CONFIGS['US'];
  }

  private generateInvoiceNumber(tenantId: string, bookingId: string): string {
    // Format: INV-YYYY-MM-XXXX
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const sequence = this.getNextSequence(tenantId, year, month);

    return `INV-${year}-${month}-${sequence}`;
  }

  private getNextSequence(tenantId: string, year: number, month: number): string {
    // Get next sequence number for tenant/month
    return String(Math.floor(Math.random() * 9999)).padStart(4, '0');
  }

  private calculateDueDate(startDate: Date, terms: string): Date {
    // Parse payment terms (e.g., "Net 30", "30 Days")
    const match = terms.match(/(\d+)/);
    const days = match ? parseInt(match[1]) : 30;

    const dueDate = new Date(startDate);
    dueDate.setDate(dueDate.getDate() + days);

    return dueDate;
  }

  private async loadInvoiceTemplate(country: string): Promise<string> {
    // Load localized invoice template
    return '';
  }

  private renderInvoiceTemplate(invoice: Invoice, template: string): string {
    // Render template with invoice data
    return '';
  }

  private async htmlToPDF(html: string, config: InvoiceConfig): Promise<Buffer> {
    // Generate PDF
    return Buffer.from('');
  }
}

interface Invoice {
  invoiceNumber: string;
  locale: SupportedLocale;
  currency: Currency;
  date: Date;
  dueDate: Date;
  from: InvoiceParty;
  to: InvoiceParty;
  items: InvoiceItem[];
  subtotal: number;
  tax: TaxCalculation;
  total: number;
  paymentTerms: string;
  notes: string[];
  config: InvoiceConfig;
}

interface InvoiceParty {
  name: string;
  address?: Address;
  taxId?: string;
  vatNumber?: string;
  registrationNumber?: string;
  bankDetails?: BankDetails;
}

interface InvoiceItem {
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
  currency: Currency;
}

interface Address {
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postalCode: string;
  country: string;
}

interface BankDetails {
  bankName: string;
  accountNumber: string;
  sortCode?: string;
  iban?: string;
  swift?: string;
}
```

---

## Refund Handling

### Multi-Currency Refunds

```typescript
/**
 * Refund manager
 */
class RefundManager {
  private gatewayRegistry: PaymentGatewayRegistry;
  private converter: CurrencyConverter;

  constructor() {
    this.gatewayRegistry = paymentGatewayRegistry;
    this.converter = currencyConverter;
  }

  /**
   * Process refund
   */
  async processRefund(request: RefundRequest): Promise<RefundResult> {
    // Get original payment
    const payment = await db.query.payments.findFirst({
      where: eq(payments.id, request.paymentId)
    });

    if (!payment) {
      throw new Error('Payment not found');
    }

    // Get gateway
    const gateway = this.gatewayRegistry.get(payment.gateway);

    if (!gateway) {
      throw new Error(`Gateway ${payment.gateway} not found`);
    }

    // Calculate refund amount
    let refundAmount = request.amount || payment.amount;

    // Convert if refunding in different currency
    if (request.currency && request.currency !== payment.currency) {
      const converted = await this.converter.convert(
        refundAmount,
        request.currency,
        payment.currency
      );
      refundAmount = converted;
    }

    // Process refund through gateway
    const gatewayResult = await gateway.refundPayment(
      payment.gatewayTransactionId,
      refundAmount
    );

    // Store refund record
    await db.insert(refunds).values({
      id: generateId(),
      paymentId: request.paymentId,
      amount: refundAmount,
      currency: payment.currency,
      reason: request.reason,
      status: gatewayResult.status,
      gatewayRefundId: gatewayResult.id,
      processedAt: new Date()
    });

    return gatewayResult;
  }

  /**
   * Calculate refund amount with fees
   */
  async calculateRefundAmount(
    paymentId: string,
    partialRefund = false
  ): Promise<{ grossAmount: number; netAmount: number; fees: number }> {
    const payment = await db.query.payments.findFirst({
      where: eq(payments.id, paymentId)
    });

    if (!payment) throw new Error('Payment not found');

    const grossAmount = payment.amount;

    // Calculate non-refundable fees
    const fees = payment.processingFee || 0;

    const netAmount = partialRefund
      ? grossAmount - fees
      : grossAmount - fees;

    return {
      grossAmount,
      netAmount,
      fees
    };
  }

  /**
   * Get refund status
   */
  async getRefundStatus(refundId: string): Promise<RefundStatus> {
    const refund = await db.query.refunds.findFirst({
      where: eq(refunds.id, refundId)
    });

    if (!refund) {
      throw new Error('Refund not found');
    }

    return {
      id: refund.id,
      status: refund.status,
      amount: refund.amount,
      currency: refund.currency,
      reason: refund.reason,
      createdAt: refund.createdAt,
      processedAt: refund.processedAt
    };
  }
}

interface RefundRequest {
  paymentId: string;
  amount?: number;
  currency?: Currency;
  reason: string;
}

interface RefundStatus {
  id: string;
  status: string;
  amount: number;
  currency: Currency;
  reason: string;
  createdAt: Date;
  processedAt?: Date;
}
```

---

## Implementation

```typescript
/**
 * Complete currency and payments service
 */
class CurrencyPaymentsService {
  private pricingManager: MultiCurrencyPricingManager;
  private exchangeRateService: ExchangeRateService;
  private converter: CurrencyConverter;
  private taxCalculator: TaxCalculator;
  private invoiceGenerator: LocalizedInvoiceGenerator;
  private refundManager: RefundManager;

  constructor() {
    this.pricingManager = new MultiCurrencyPricingManager();
    this.exchangeRateService = exchangeRateService;
    this.converter = currencyConverter;
    this.taxCalculator = taxCalculator;
    this.invoiceGenerator = new LocalizedInvoiceGenerator();
    this.refundManager = new RefundManager();
  }

  /**
   * Get price in user's preferred currency
   */
  async getLocalizedPrice(
    itemId: string,
    itemType: 'trip' | 'service' | 'addon',
    userLocale: SupportedLocale
  ): Promise<LocalizedPrice> {
    const currency = getCurrencyForLocale(userLocale);
    const { amount, isConverted } = await this.pricingManager.getPriceWithFallback(
      itemId,
      itemType,
      currency
    );

    return {
      itemId,
      itemType,
      amount,
      currency,
      isConverted,
      formatted: this.formatPrice(amount, currency, userLocale)
    };
  }

  /**
   * Calculate total with tax
   */
  async calculateTotalWithTax(
    amount: number,
    currency: Currency,
    country: string,
    itemType: 'service' | 'good' | 'international_travel'
  ): Promise<TaxCalculation> {
    return this.taxCalculator.calculateTax(
      amount,
      currency,
      country,
      itemType
    );
  }

  /**
   * Format price for display
   */
  formatPrice(amount: number, currency: Currency, locale: SupportedLocale): string {
    const formatter = new CurrencyFormatter();
    return formatter.format(amount, currency);
  }

  /**
   * Generate invoice for booking
   */
  async generateInvoice(
    bookingId: string,
    locale: SupportedLocale
  ): Promise<Invoice> {
    const currency = getCurrencyForLocale(locale);
    return this.invoiceGenerator.generateInvoice(bookingId, locale, currency);
  }

  /**
   * Get available payment methods
   */
  getAvailablePaymentMethods(
    country: string,
    currency: Currency
  ): PaymentMethodConfig[] {
    return getPaymentMethodsForRegion(country, currency);
  }

  /**
   * Process refund
   */
  async processRefund(request: RefundRequest): Promise<RefundResult> {
    return this.refundManager.processRefund(request);
  }
}

export const currencyPaymentsService = new CurrencyPaymentsService();

interface LocalizedPrice {
  itemId: string;
  itemType: string;
  amount: number;
  currency: Currency;
  isConverted: boolean;
  formatted: string;
}
```

---

## Testing Scenarios

```typescript
describe('Currency and Payments', () => {
  describe('Currency Conversion', () => {
    it('should convert between currencies', async () => {
      const converter = new CurrencyConverter();
      const amount = await converter.convert(100, Currency.USD, Currency.EUR);
      expect(amount).toBeGreaterThan(0);
    });

    it('should round according to currency precision', () => {
      const converter = new CurrencyConverter();
      // JPY has 0 decimal places
      // USD has 2 decimal places
    });
  });

  describe('Tax Calculation', () => {
    it('should calculate VAT for Germany', async () => {
      const calc = await taxCalculator.calculateTax(
        1000,
        Currency.EUR,
        'DE',
        'service'
      );
      expect(calc.taxRate).toBe(19);
      expect(calc.isInclusive).toBe(true);
    });

    it('should handle tax exemption', async () => {
      const calc = await taxCalculator.calculateTax(
        1000,
        Currency.GBP,
        'GB',
        'service',
        'GB123456789',
        true
      );
      expect(calc.taxAmount).toBe(0);
    });
  });

  describe('Invoice Generation', () => {
    it('should generate German invoice', async () => {
      const generator = new LocalizedInvoiceGenerator();
      const invoice = await generator.generateInvoice('booking-123', 'de-DE', Currency.EUR);
      expect(invoice.config.taxLabel).toBe('MwSt');
    });
  });
});
```

---

## API Specification

```yaml
paths:
  /api/payments/currencies:
    get:
      summary: Get supported currencies
      responses:
        '200':
          description: List of currencies

  /api/payments/exchange-rate:
    get:
      summary: Get exchange rate
      parameters:
        - name: from
          in: query
          schema:
            type: string
        - name: to
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Exchange rate

  /api/payments/methods:
    get:
      summary: Get available payment methods
      parameters:
        - name: country
          in: query
          schema:
            type: string
        - name: currency
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Payment methods

  /api/payments/calculate-tax:
    post:
      summary: Calculate tax for amount
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [amount, currency, country]
              properties:
                amount:
                  type: number
                currency:
                  type: string
                country:
                  type: string
                itemType:
                  type: string
                customerTaxId:
                  type: string
                businessPurchase:
                  type: boolean
      responses:
        '200':
          description: Tax calculation

  /api/invoices/{bookingId}:
    get:
      summary: Generate invoice for booking
      parameters:
        - name: bookingId
          in: path
          required: true
        - name: locale
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Invoice data

  /api/refunds:
    post:
      summary: Process refund
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RefundRequest'
      responses:
        '201':
          description: Refund processed

components:
  schemas:
    RefundRequest:
      type: object
      required: [paymentId, reason]
      properties:
        paymentId:
          type: string
        amount:
          type: number
        currency:
          type: string
        reason:
          type: string
```

---

## Metrics and Monitoring

```typescript
interface CurrencyPaymentsMetrics {
  transactionsByCurrency: Record<string, number>;
  transactionsByMethod: Record<string, number>;
  conversionRateAccuracy: number;
  taxCalculationErrors: number;
  refundRate: number;
  averageProcessingTime: number;
  gatewaySuccessRates: Record<string, number>;
}
```

---

**End of Document**

**Next:** [Regional Compliance Deep Dive](INTERNATIONALIZATION_04_COMPLIANCE.md)
