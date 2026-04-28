# Multi-Currency & Exchange Rate Management 01: Live Exchange Rate Management

> Research document for exchange rate data sources, rate update pipelines, mark-up management, and historical rate storage.

---

## Document Overview

**Focus:** Real-time and near-real-time exchange rate acquisition, transformation, and storage
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Exchange Rate Data Sources
- What is the canonical source for INR reference rates? (RBI publishes daily reference rates)
- What commercial forex APIs are available? (Fixer.io, Open Exchange Rates, XE, CurrencyLayer, ExchangeRate-API)
- How do RBI reference rates compare to market rates from commercial APIs?
- What is the reliability and latency of each source?
- Can we use multiple providers for cross-verification?
- Are there free/government sources vs. paid commercial feeds?
- What about rates from supplier APIs directly (Amadeus, hotel aggregators quote in local currency)?

### 2. Rate Update Frequency
- RBI publishes reference rates once daily (typically by 12:30 PM IST) -- is this sufficient?
- For volatile currencies (TRY, ARS, BRL), do we need intraday updates?
- What is the practical update frequency for a boutique agency? (Hourly? Every 15 minutes?)
- How do we handle weekend/holiday gaps when RBI does not publish?
- What is the staleness threshold before a rate is considered unreliable?
- Should we support both a "daily rate" mode and a "live rate" mode?

### 3. Base Currency and Quote Model
- Should INR be the base currency (how many INR per 1 USD) or the quote currency?
- What quote currencies are essential for Indian travel agencies? (USD, EUR, GBP, SGD, THB, AED, MYR, AUD, CAD, CHF, JPY, CNY, LKR, NPR, BDT, MVR, BTN)
- How do we handle exotic currencies that may not have direct INR quotes? (Cross-rate via USD)
- What about currency pairs where no direct market exists? (INR/THB via INR/USD and USD/THB)

### 4. Mark-up Management
- What is a typical agency spread over market rate? (1-3% common for Indian agencies)
- Should mark-up be configurable per currency, per supplier, per trip type?
- How do we handle mark-up for different products? (forex card vs. wire transfer vs. booking component)
- When should mark-up be visible to the customer vs. hidden in the final price?
- How do we prevent mark-up arbitrage (customer comparing our rate to live market rate)?
- Should we offer a "locked rate" product where the agency absorbs fluctuation risk?

### 5. Historical Rate Storage
- Do we store the rate at time of booking, or time of payment, or time of invoicing?
- How does this interact with GST invoicing requirements?
- What is the retention policy for historical rates? (7 years for tax audit in India)
- How do we handle rate corrections or provider errors retroactively?
- Do we need a complete time-series for reporting, or just snapshots at key transaction points?

---

## Research Areas

### A. Exchange Rate Data Sources

#### RBI Reference Rate (Primary, Authoritative)

The Reserve Bank of India publishes daily reference rates for 22 major currencies against the INR. These rates are derived from a weighted average of interbank transaction rates.

```typescript
interface RBIReferenceRate {
  date: string;                        // "2026-04-28" (YYYY-MM-DD)
  publishedAt: string;                 // ISO 8601, typically ~12:30 PM IST
  currency: string;                    // ISO 4217 code: "USD", "EUR", etc.
  rate: number;                        // INR per unit of foreign currency
  // Example: USD rate = 83.4527 means 1 USD = 83.4527 INR
  source: 'RBI_DAILY_REFERENCE';
  sourceUrl: string;                   // Link to RBI publication
}
```

**Characteristics:**
- Free, authoritative, legally defensible
- Published once daily (Mon-Fri, excluding RBI holidays)
- Covers ~22 currencies
- Not suitable for intraday pricing
- URL: `https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx`

#### Commercial Forex APIs (Secondary, Real-Time)

```typescript
interface RateProvider {
  id: string;
  name: string;                        // "Fixer", "Open Exchange Rates", "XE"
  type: 'free_tier' | 'paid' | 'enterprise';
  baseUrl: string;
  apiKeyRequired: boolean;
  rateLimit: {
    requestsPerMinute: number;
    requestsPerMonth: number | null;   // null = unlimited
  };
  supportedCurrencies: string[];       // ISO 4217 codes
  updateFrequency: string;            // "daily", "hourly", "live", "60min"
  historicalData: boolean;
  historicalDataRange: string;         // "1 year", "unlimited"
  reliability: number;                // uptime percentage (99.9, 99.5, etc.)
  costPerMonth: number | null;        // USD per month, null = free
  notes: string;
}
```

| Provider | Free Tier | Update Freq | Historical | INR Support | Cost (Paid) |
|----------|-----------|-------------|------------|-------------|-------------|
| **Fixer.io** | 100 req/mo, daily | Live (paid) | 1 year | Yes | $14-99/mo |
| **Open Exchange Rates** | 1000 req/mo, hourly | Hourly | Full | Yes | $12-97/mo |
| **ExchangeRate-API** | 1500 req/mo, daily | Daily | Limited | Yes | $14-79/mo |
| **XE Currency Data** | No | Live | 30 days | Yes | Custom |
| **CurrencyLayer** | 100 req/mo, daily | Live (paid) | Full | Yes | $9-79/mo |
| **Frankfurter** | Unlimited, daily | Daily | Since 1999 | Yes | Free (ECB) |
| **RBI (scraped)** | Unlimited, daily | Daily | Since 1998 | Base=INR | Free |

#### Cross-Rate Computation

For currencies without a direct INR quote, compute via USD:

```typescript
interface CrossRateComputation {
  baseCurrency: string;               // "INR"
  targetCurrency: string;             // "THB"
  viaCurrency: string;                // "USD"
  baseToVia: number;                  // INR/USD = 83.4527
  viaToTarget: number;                // USD/THB = 35.12
  computedRate: number;               // INR/THB = 83.4527 / 35.12 = 2.3762
  computationTimestamp: string;
  confidence: 'direct' | 'cross_via_usd' | 'cross_via_eur' | 'estimated';
}
```

### B. Rate Update Pipeline

```typescript
interface RateUpdateJob {
  id: string;
  providerId: string;
  triggerType: 'scheduled' | 'on_demand' | 'webhook';
  scheduledAt: string;
  executedAt: string | null;
  completedAt: string | null;
  status: 'pending' | 'running' | 'success' | 'failed' | 'partial';
  currenciesRequested: string[];
  currenciesReceived: string[];
  ratesInserted: number;
  error: string | null;
}

interface RateUpdateConfig {
  agencyId: string;
  primaryProvider: string;            // "RBI" for Indian agencies
  secondaryProviders: string[];       // ["Fixer", "Open Exchange Rates"]
  updateFrequency: 'daily' | 'hourly' | 'every_15_min' | 'live';
  dailyUpdateTime: string;            // "13:00" IST — after RBI publishes
  fallbackProvider: string;           // Used when primary fails
  currencies: string[];               // Agency's active currencies
  maxRateStaleness: number;           // Hours before rate is considered stale
  alertOnStaleRate: boolean;
  alertOnRateChange: number;          // Alert if rate moves > this % (e.g., 2)
}
```

**Pipeline Flow:**
1. Scheduled trigger (cron) or on-demand
2. Fetch rates from primary provider (RBI for daily, commercial API for intraday)
3. Cross-verify with secondary provider (flag if deviation > 1%)
4. Apply agency mark-up to generate customer-facing rates
5. Store raw rate and marked-up rate in rate history
6. Publish update event for downstream consumers (booking engine, invoicing)

### C. Mark-up and Spread Management

```typescript
interface MarkupConfig {
  id: string;
  agencyId: string;
  currency: string;                   // "USD", "EUR", or "ALL" for global default
  markupType: 'percentage' | 'flat' | 'tiered';
  markupValue: number;                // e.g., 2.5 for 2.5%
  flatMarkupInINR: number | null;     // Used when markupType = 'flat'
  tiers: MarkupTier[] | null;         // Used when markupType = 'tiered'
  applicableTo: 'booking' | 'forex_product' | 'invoice' | 'all';
  isActive: boolean;
  effectiveFrom: string;
  effectiveTo: string | null;
  createdBy: string;
  createdAt: string;
}

interface MarkupTier {
  minAmount: number;                  // Amount in foreign currency
  maxAmount: number | null;           // null = no upper limit
  markupType: 'percentage' | 'flat';
  markupValue: number;
}

// Example: Agency charges 2.5% on USD, 3% on THB, 1.5% on EUR
// Market rate USD/INR = 83.45
// Agency rate USD/INR = 83.45 * 1.025 = 85.54
// Customer pays INR 85.54 per USD instead of 83.45
```

**Mark-up Strategy for Indian Travel Agencies:**

| Currency | Typical Spread | Rationale |
|----------|---------------|-----------|
| USD | 1.0 - 1.5% | Highly liquid, tight spreads |
| EUR | 1.5 - 2.0% | Liquid but wider INR/EUR spread |
| GBP | 1.5 - 2.0% | Similar to EUR |
| SGD | 2.0 - 2.5% | Moderate liquidity for INR |
| THB | 2.5 - 3.5% | Less liquid, cross-rate via USD |
| AED | 1.5 - 2.0% | Pegged to USD, predictable |
| MYR | 2.5 - 3.0% | Less liquid |
| Exotic (LKR, BDT) | 3.0 - 5.0% | Very illiquid, wide spreads |

### D. Exchange Rate Data Model

```typescript
interface ExchangeRate {
  id: string;
  currency: string;                   // ISO 4217: "USD"
  baseCurrency: string;               // "INR"
  rate: number;                       // 83.4527 (INR per 1 USD)
  inverseRate: number;                // 0.01198 (USD per 1 INR)
  source: string;                     // "RBI", "Fixer", "OpenExchangeRates"
  sourceRate: number;                 // Raw rate from provider (before markup)
  markupApplied: number;              // Percentage markup applied
  agencyRate: number;                 // Rate after markup (customer-facing)
  timestamp: string;                  // ISO 8601
  effectiveDate: string;              // "2026-04-28" — for daily rates
  isLive: boolean;                    // true for real-time, false for daily snapshot
  confidence: 'direct' | 'cross_rate' | 'estimated';
  crossRateVia: string | null;        // "USD" if computed via cross-rate
}

interface RateHistory {
  id: string;
  currency: string;
  date: string;                       // YYYY-MM-DD
  openRate: number | null;            // For intraday series
  closeRate: number;
  highRate: number | null;
  lowRate: number | null;
  rbiReferenceRate: number | null;    // Official RBI rate for that day
  agencyClosingRate: number;          // Rate with markup
  source: string;
  createdAt: string;
}

// For invoicing: lock the rate at booking time
interface BookingRateLock {
  id: string;
  bookingId: string;
  currency: string;
  lockedRate: number;                 // INR per foreign currency unit
  sourceRate: number;                 // Raw market rate
  markupAt: number;                   // Markup applied
  lockedAt: string;                   // ISO 8601 timestamp
  lockedBy: string;                   // User/system
  validUntil: string;                 // Rate lock expiry
  status: 'active' | 'expired' | 'superseded';
  supersededBy: string | null;        // New rate lock ID if re-locked
}
```

### E. Historical Rate Storage and Querying

```typescript
interface RateStorageConfig {
  retentionDays: number;              // 2557 days (~7 years, per Indian tax law)
  storageBackend: 'timeseries_db' | 'relational_db';
  granularity: 'daily' | 'hourly' | 'per_transaction';
  compression: boolean;               // Compress old daily rates
  archiveAfterDays: number;           // Move to cold storage after N days
}

interface RateQuery {
  currency: string;
  from: string;                       // Date or timestamp
  to: string;
  granularity: 'daily' | 'hourly' | 'point_in_time';
  pointInTime: string | null;         // For booking rate lookups
  includeRbiRate: boolean;            // Include official RBI rate for comparison
  includeMarkup: boolean;             // Include agency markup rates
}

interface RateQueryResult {
  currency: string;
  baseCurrency: string;
  dataPoints: {
    timestamp: string;
    marketRate: number;
    rbiRate: number | null;
    agencyRate: number;
  }[];
  summary: {
    averageRate: number;
    minRate: number;
    maxRate: number;
    standardDeviation: number;
    totalChangePercent: number;
  };
}
```

**Practical Example -- Rate at Booking Time:**

A customer books a Singapore trip on April 15. The hotel costs SGD 1,200.

```
Market rate on April 15:   1 SGD = 62.45 INR
Agency markup (2.5%):      62.45 * 1.025 = 64.01 INR
Locked rate for booking:   1 SGD = 64.01 INR
Hotel cost in INR:         1,200 * 64.01 = INR 76,812

If the customer pays on April 25 when SGD has strengthened:
Market rate on April 25:   1 SGD = 63.20 INR
Agency markup (2.5%):      63.20 * 1.025 = 64.78 INR

The booking uses the LOCKED rate (64.01), not the current rate.
The agency bears the difference: 64.78 - 64.01 = 0.77 INR per SGD
On SGD 1,200: agency absorbs INR 924 in currency fluctuation.
```

---

## Open Problems

### 1. Rate Source Reliability
- RBI's official website does not offer a stable, versioned API. The rates page is subject to format changes. We need a scraping layer with fallback.
- Free-tier commercial APIs have low rate limits (100-1500 requests/month) which may not suffice for a multi-currency, multi-agency platform.
- **Research needed:** What is the actual reliability of RBI's RSS feed vs. HTML scraping?

### 2. Cross-Rate Accuracy
- Computing INR/THB via USD introduces two sources of error. For high-volume currencies (THB, SGD for Indian agencies), should we find a direct quote source?
- Cross-rate staleness compounds: if INR/USD is from 10:00 AM and USD/THB from 10:15 AM, the computed INR/THB is inconsistent.

### 3. Mark-up Transparency
- Indian customers increasingly compare agency rates to live market rates (Google shows live rates). A 2-3% markup is easily visible.
- Should we display "Rate includes 2.5% service margin" or embed it opaquely?
- Competitive pressure from platforms like BookMyForex that show "live interbank rate" alongside their rate.

### 4. Weekend and Holiday Gaps
- RBI does not publish on weekends and bank holidays. For bookings made on Saturday, what rate do we use? Friday's close? Monday's open?
- Forex markets trade 24/5 globally. Saturday bookings may need Saturday market rates from commercial APIs, not Friday's RBI rate.

### 5. Rate Lock Duration
- How long should a rate lock be valid? 24 hours? 48 hours? Until trip departure?
- For long-lead bookings (6+ months), a rate lock is impractical. Should we re-quote periodically?
- What happens if a locked rate expires and the new rate is significantly different?

---

## Next Steps

1. **Evaluate commercial API providers** -- Sign up for free tiers of Fixer, Open Exchange Rates, and ExchangeRate-API. Test reliability, latency, and data quality over 1 week.
2. **Build RBI rate scraper** -- Create a reliable scraper for RBI reference rates with error handling and fallback to previous day's rate.
3. **Design rate update scheduler** -- Implement the `RateUpdateConfig` with configurable frequency, fallback chains, and alerting.
4. **Prototype mark-up engine** -- Build the `MarkupConfig` CRUD and rate calculation pipeline. Test with real RBI rates + agency spreads.
5. **Define rate lock policy** -- Work with finance team to define lock duration, re-quoting rules, and customer communication for rate changes.
6. **Historical rate migration** -- Import 2+ years of historical RBI rates to seed the `RateHistory` table for reporting.
7. **Rate deviation alerting** -- Implement alerts when market rates deviate >2% from previous day for key currencies (USD, EUR, SGD, GBP, AED, THB).

---

## Cross-References

| Document | Relevance |
|----------|-----------|
| [FOREX_MGMT_02_MULTI_CURRENCY_BOOKING](FOREX_MGMT_02_MULTI_CURRENCY_BOOKING.md) | Consumes rates for booking and invoicing |
| [FOREX_MGMT_03_HEDGING](FOREX_MGMT_03_HEDGING.md) | Uses rate history for risk analysis |
| [FOREX_MGMT_04_FOREX_PRODUCTS](FOREX_MGMT_04_FOREX_PRODUCTS.md) | Forex products use marked-up rates |
| [FINANCE_01_ACCOUNTING](FINANCE_01_ACCOUNTING.md) | Journal entries reference locked rates |
| [PAYMENT_PROCESSING_03_COMPLIANCE](PAYMENT_PROCESSING_03_COMPLIANCE_DEEP_DIVE.md) | TCS calculation uses INR conversion |
| [INTERNATIONALIZATION_03_CURRENCY](INTERNATIONALIZATION_03_CURRENCY.md) | Currency display and formatting |
| [FOREX_01_PROVIDERS](FOREX_01_PROVIDERS.md) | Forex provider landscape and APIs |

---

**Last Updated:** 2026-04-28
