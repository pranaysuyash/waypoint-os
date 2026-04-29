# Multi-Currency & Exchange Rate Management -- Master Index

> Research series on exchange rate management, multi-currency booking, currency risk hedging, and forex products for Indian travel agencies.

---

## Series Overview

**Topic:** Multi-currency and exchange rate management for the travel agency platform
**Scope:** End-to-end currency operations -- from acquiring live rates to settling suppliers, managing risk, and offering forex products to travelers
**Audience:** Engineering, product, and finance teams building the platform
**Status:** Research Complete (4 of 4 documents)
**Last Updated:** 2026-04-28

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 01 | [Live Exchange Rate Management](FOREX_MGMT_01_RATES.md) | Rate sources (RBI, commercial APIs), update pipelines, mark-up engine, historical storage | Complete |
| 02 | [Multi-Currency Booking & Invoicing](FOREX_MGMT_02_MULTI_CURRENCY_BOOKING.md) | Multi-currency pricing, GST currency rules, TCS calculation, customer-facing display | Complete |
| 03 | [Currency Risk Management & Hedging](FOREX_MGMT_03_HEDGING.md) | Exposure tracking, forward contracts, natural hedging, rate alerts, boutique strategies | Complete |
| 04 | [Forex Products for Travelers](FOREX_MGMT_04_FOREX_PRODUCTS.md) | Forex cards, currency notes, wire transfers, LRS compliance, recommendation engine | Complete |

---

## Key Themes

### 1. INR is the Base Currency
Indian travel agencies operate with INR as their accounting and reporting currency. Every foreign currency transaction must be converted to INR at some point. The system must track both the original foreign currency amount and the INR equivalent throughout the booking lifecycle.

### 2. RBI Compliance is Non-Negotiable
The Reserve Bank of India's Foreign Exchange Management Act (FEMA) governs all foreign exchange transactions. LRS limits, TCS collection, EEFC account rules, and authorized dealer requirements are legal mandates. Non-compliance carries penalties. The platform must embed compliance into every forex workflow.

### 3. Rate Locks Protect Both Parties
The exchange rate at booking time determines the customer's cost. The rate at supplier settlement time determines the agency's cost. The gap between these two rates is the agency's currency risk. Rate locks (documented in 01 and 02) and hedging (documented in 03) are the tools to manage this gap.

### 4. Multi-Currency is the Default, Not the Edge Case
A typical international trip from India involves 3-5 currencies. The platform cannot treat foreign currency as an afterthought. Every pricing, invoicing, and settlement flow must be currency-aware from the start.

### 5. Forex Products are a Revenue Opportunity
Offering forex cards, currency notes, and wire transfers alongside trip bookings is a natural upsell. Agencies earn commission (0.5-2%) and improve customer convenience. The recommendation engine (documented in 04) makes this a data-driven feature rather than a manual sales process.

### 6. Boutique Agencies Need Simple Solutions
Most Indian travel agencies are small businesses without dedicated treasury teams. The platform must offer tiered complexity: simple buffer pricing for small agencies, full forward contract management for large ones. One size does not fit all.

---

## Cross-References Table

| Topic | Doc 01 (Rates) | Doc 02 (Booking) | Doc 03 (Hedging) | Doc 04 (Products) |
|-------|:--------------:|:-----------------:|:-----------------:|:------------------:|
| Exchange rate acquisition | **Primary** | Consumes rates | Uses rate history | Uses rates for pricing |
| Rate lock mechanism | Provides lock | **Primary** | Feeds exposure calc | N/A |
| GST on multi-currency | N/A | **Primary** | N/A | N/A |
| TCS calculation | Provides INR rate | **Primary** | N/A | **Primary** |
| Currency exposure tracking | N/A | Provides open bookings | **Primary** | N/A |
| Forward contracts | N/A | N/A | **Primary** | N/A |
| Forex cards | Uses rates | Bundle in trip | Natural hedge tool | **Primary** |
| Wire transfers | Uses rates | N/A | N/A | **Primary** |
| LRS compliance | N/A | TCS interaction | N/A | **Primary** |
| Customer currency display | Provides rate data | **Primary** | N/A | N/A |
| Rate alerts | Publishes alerts | Triggers re-pricing | **Primary** | N/A |
| Mark-up management | **Primary** | Uses marked-up rates | N/A | Uses marked-up rates |
| Historical rate storage | **Primary** | Invoice reference | Volatility analysis | N/A |

---

## Integration Points with Platform

### Booking Engine
- Multi-currency pricing at quote and confirmation
- Rate lock at booking time
- GST and TCS computation
- Supplier settlement currency tracking

### Payment Processing
- Multi-currency payment collection
- TCS deduction and deposit
- Payment gateway currency conversion reconciliation
- EEFC account credits

### Finance & Accounting
- Journal entries in both foreign currency and INR
- Mark-to-market for forward contracts
- GST returns with multi-currency invoices
- TCS returns and Form 16F generation

### Trip Builder
- Display prices in customer's preferred currency
- Currency breakdown in trip cost summary
- Forex product upsell (card, cash, wire)
- Re-pricing alerts when rates move significantly

### CRM / Customer Portal
- Customer PAN tracking for LRS limits
- Forex product recommendations based on trip profile
- Post-trip encashment reminders
- Currency spend analytics

### Supplier Settlement
- Supplier payment in their preferred currency
- Forward contract maturity matching
- EEFC account debit for natural hedging
- Settlement rate vs. booking rate variance tracking

---

## Competitive Landscape

### Indian Travel Platforms with Forex Integration

| Platform | Forex Capability | Notes |
|----------|-----------------|-------|
| **MakeMyTrip** | Basic (shows INR prices) | Multi-currency display but limited forex products |
| **Cleartrip** | Limited | Primarily INR pricing |
| **Yatra** | Forex partnership | Partners with Thomas Cook for forex |
| **Thomas Cook** | Full-stack | AD-II authorized, issues forex cards, currency, wire transfers |
| **Cox & Kings** (defunct) | Was full-stack | Had full forex license |
| **SOTC** | Forex partnership | Partners with Thomas Cook group |
| **Kesari Tours** | Limited | Primarily INR packages |

### Dedicated Forex Platforms (Complementary)

| Platform | API | Travel Agency Partnership | Notes |
|----------|-----|--------------------------|-------|
| **BookMyForex** | Yes | Referral program | Largest marketplace, white-label possible |
| **Wise** | Yes | Business API | Best for wire transfers, growing India presence |
| **EbixCash** | Yes | Agency partnership | Full-stack: cards, notes, wire, insurance |
| **Orient Exchange** | Limited | Branch-based | Good rates, limited digital |

### Global Benchmarks

| Platform | Multi-Currency Approach | Lessons |
|----------|------------------------|---------|
| **Expedia** | Local currency display per market | Show prices in customer's currency with rate lock |
| **Booking.com** | Local currency + "you'll pay in [currency]" | Clear disclosure of payment currency |
| **Trip.com** | Multi-currency + forex upsell | Integrated forex card for Chinese travelers |
| **Agoda** | Dynamic currency conversion | Offers DCC at checkout (controversial) |

---

## Data Model Summary

### Core Interfaces Across the Series

```
FOREX_MGMT_01 (Rates):
  ExchangeRate, RateProvider, RateHistory, MarkupConfig, BookingRateLock, RateUpdateConfig

FOREX_MGMT_02 (Booking):
  MultiCurrencyPrice, CurrencyLineItem, CurrencyTotal, GSTCurrencyRule, GSTInvoice,
  TCSCalculation, PANRemittanceTracker, CurrencyBreakdown, ConversionPolicy

FOREX_MGMT_03 (Hedging):
  RiskExposure, CurrencyExposure, MaturityBucket, ForwardContract, EEFCAccount,
  NaturalHedgeMatch, RateAlert, RateAlertConfig, HedgingStrategy, HedgingApproach,
  HedgingDashboard

FOREX_MGMT_04 (Products):
  ForexCard, CurrencyOrder, WireTransfer, LRSCompliance, LRSSelfDeclaration,
  ForexRecommendation
```

### Shared Currency Enum

```typescript
// Core currencies for Indian travel agencies (in priority order):
type TravelCurrency =
  | 'INR'   // Indian Rupee (base)
  | 'USD'   // US Dollar (universal, cross-rate base)
  | 'EUR'   // Euro (Europe)
  | 'GBP'   // British Pound (UK)
  | 'SGD'   // Singapore Dollar (Singapore -- top destination)
  | 'THB'   // Thai Baht (Thailand -- top destination)
  | 'AED'   // UAE Dirham (Dubai -- top destination)
  | 'MYR'   // Malaysian Ringgit (Malaysia)
  | 'AUD'   // Australian Dollar (Australia)
  | 'CAD'   // Canadian Dollar (Canada)
  | 'CHF'   // Swiss Franc (Switzerland)
  | 'JPY'   // Japanese Yen (Japan)
  | 'KRW'   // South Korean Won (South Korea)
  | 'NZD'   // New Zealand Dollar (New Zealand)
  | 'ZAR'   // South African Rand (South Africa)
  | 'MVR'   // Maldivian Rufiyaa (Maldives)
  | 'LKR'   // Sri Lankan Rupee (Sri Lanka)
  | 'NPR'   // Nepalese Rupee (Nepal)
  | 'BDT'   // Bangladeshi Taka (Bangladesh)
  | 'BTN'   // Bhutanese Ngultrum (Bhutan)
  | 'CNY'   // Chinese Yuan (China)
  | 'TRY'   // Turkish Lira (Turkey)
  | 'RUB'   // Russian Ruble (Russia)
  | 'IDR'   // Indonesian Rupiah (Bali/Indonesia)
  | 'VND'   // Vietnamese Dong (Vietnam)
  | 'PHP'   // Philippine Peso (Philippines)
  | 'HKD'   // Hong Kong Dollar (Hong Kong)
  | 'TWD'   // Taiwan Dollar (Taiwan)
  | 'BRL'   // Brazilian Real (Brazil)
  | 'MXN'   // Mexican Peso (Mexico)
  | 'EGP'   // Egyptian Pound (Egypt)
  | 'JOD'   // Jordanian Dinar (Jordan)
  | 'OMR'   // Omani Rial (Oman)
  | 'QAR'   // Qatari Rial (Qatar)
  | 'BHD'   // Bahraini Dinar (Bahrain)
  | 'KWD'   // Kuwaiti Dinar (Kuwait)
  | 'SAR'   // Saudi Riyal (Saudi Arabia)
  | 'ILS'   // Israeli Shekel (Israel)
  | 'MUR'   // Mauritian Rupee (Mauritius)
  | 'FJD'   // Fijian Dollar (Fiji);
```

---

## Open Problems Summary

| # | Problem | Doc | Severity | Notes |
|---|---------|-----|----------|-------|
| 1 | RBI website scraping reliability | 01 | High | No stable API; format changes break scrapers |
| 2 | GST export-of-services classification | 02 | High | Misclassification = penalty |
| 3 | TCS tracking across multiple agencies | 02 | Medium | No PAN-level LRS query API |
| 4 | Forward contract minimum ticket sizes | 03 | Medium | Boutiques below threshold |
| 5 | Agency authorization for forex sales | 04 | High | Only AD-I/AD-II can sell forex |
| 6 | Double TCS risk (trip + forex product) | 04 | High | Must prevent duplicate collection |
| 7 | Cross-rate accuracy for exotic pairs | 01 | Low | INR/THB via USD compounds error |
| 8 | Supplier rate lock negotiation | 03 | Medium | Not all suppliers cooperate |
| 9 | Weekend/holiday rate gaps | 01 | Low | RBI doesn't publish on holidays |
| 10 | Customer self-declaration for LRS | 04 | Medium | No verification possible |

---

## Implementation Priority

### Phase 1 (Foundation -- Months 1-2)
1. Rate acquisition pipeline (RBI scraper + one commercial API)
2. Basic mark-up engine (flat percentage per currency)
3. Multi-currency line items in booking engine
4. INR-only invoicing with original currency display

### Phase 2 (Compliance -- Months 2-3)
5. TCS calculation engine with PAN tracking
6. GST invoice generation (multi-currency with INR tax amounts)
7. Customer-facing currency display with disclaimers
8. Rate lock mechanism at booking time

### Phase 3 (Risk Management -- Months 3-4)
9. Currency exposure dashboard
10. Rate fluctuation alerts
11. Historical rate storage and reporting
12. Basic hedging recommendations (buffer pricing for boutiques)

### Phase 4 (Forex Products -- Months 4-6)
13. Forex card integration (API partnership with BookMyForex or similar)
14. Currency notes ordering flow
15. Wire transfer facilitation
16. Forex product recommendation engine
17. LRS tracking and Form 16F generation

---

## Related Documentation

| Series | Documents | Relationship |
|--------|-----------|-------------|
| [Finance & Accounting](FINANCE_MASTER_INDEX.md) | Accounting, Profit Centers, Treasury, Reporting | Journal entries, P&L impact of forex |
| [Forex Services](FOREX_MASTER_INDEX.md) | Providers, Comparison, Ordering, Management | Provider landscape (customer-facing forex) |
| [Payment Processing](PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) | Technical, UX, Compliance, Reconciliation | Payment collection, TCS deposit |
| [Internationalization](INTERNATIONALIZATION_MASTER_INDEX.md) | Architecture, Localization, Currency, Compliance | Currency display, locale formatting |
| [Trip Builder](TRIP_BUILDER_MASTER_INDEX.md) | Architecture through Booking Management | Trip pricing, forex upsell |
| [Booking Engine](BOOKING_ENGINE_MASTER_INDEX.md) | Reservation Flow, Inventory, Confirmations | Multi-currency booking lifecycle |
| [Document Generation](DOCUMENT_GENERATION_MASTER_INDEX.md) | Templates, PDF, Delivery, Management | Invoice generation, Form 16F |
| [Identity & KYC](IDENTITY_01_KYC.md) | KYC, Passport, OCR, Privacy | KYC for forex products |

---

**Last Updated:** 2026-04-28
