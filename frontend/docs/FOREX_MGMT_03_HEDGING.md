# Multi-Currency & Exchange Rate Management 03: Currency Risk Management & Hedging

> Research document for currency risk identification, hedging strategies, forward contracts, and rate fluctuation monitoring for Indian travel agencies.

---

## Document Overview

**Focus:** How travel agencies manage exchange rate risk when they book in foreign currencies but collect in INR
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Currency Risk Identification
- What is the agency's net foreign currency exposure at any given time? (Sum of all booked-but-unsettled supplier commitments)
- Which currencies represent the highest risk? (SGD, THB, AED, EUR for typical Indian agencies)
- What is the typical time lag between booking and supplier settlement? (30-90 days for hotels, 7-15 days for airlines via BSP)
- How much can INR move against key currencies in 30/60/90 days? (Historical volatility analysis)
- What is the financial impact of a 2% INR depreciation on the agency's monthly P&L?

### 2. Forward Contract Booking
- Can boutique agencies book forward contracts with banks? (Typically yes, but minimum ticket sizes apply)
- What are the minimum contract sizes for INR/USD, INR/EUR, INR/SGD forwards?
- What is the cost of a forward contract? (Margin money: 4-5% of contract value, plus bank charges)
- How do we match forward contract maturity dates with supplier payment dates?
- What happens if the trip is cancelled but the forward contract is already booked?

### 3. Natural Hedging
- Can the agency match foreign currency receipts (customers paying in SGD) with foreign currency payments (settling SGD hotels)?
- Do any Indian agencies maintain foreign currency accounts (EEFC accounts) for this purpose?
- What are the RBI rules on EEFC (Exchange Earners' Foreign Currency) accounts for travel agencies?
- Can the agency negotiate with suppliers to accept INR or USD instead of local currency?

### 4. Rate Fluctuation Monitoring
- What alerting thresholds are practical? (2% daily move? 5% weekly move?)
- How do we monitor multiple currency pairs simultaneously?
- What actions should be triggered by rate alerts? (Re-price pending quotes? Hedge open positions?)
- How do we visualize currency exposure for the finance team?

### 5. Simple Hedging for Boutique Agencies
- Most boutique agencies (5-20 employees, INR 5-50 crore annual revenue) lack dedicated treasury teams. What practical hedging strategies exist?
- Pre-buying forex at favorable rates and holding in EEFC accounts
- Negotiating rate locks with key suppliers (especially hotel chains)
- Using credit card forex products that lock rates for 30 days
- Building a forex buffer (over-price by 1-2% to absorb normal fluctuation)

---

## Research Areas

### A. Currency Risk Exposure Model

```typescript
interface RiskExposure {
  id: string;
  agencyId: string;
  calculatedAt: string;
  totalExposureINR: number;           // Net open position across all currencies
  exposuresByCurrency: CurrencyExposure[];
  exposureByMaturity: MaturityBucket[];
  riskLevel: 'low' | 'moderate' | 'high' | 'critical';
  riskScore: number;                  // 0-100, based on volatility and exposure size
}

interface CurrencyExposure {
  currency: string;                   // "SGD"
  netPosition: number;                // Positive = receivable, Negative = payable
  // Example: -5000 means agency owes SGD 5,000 to suppliers
  netPositionInINR: number;           // Converted at current rate
  averageMaturityDays: number;        // Weighted average days until settlement
  currentRate: number;                // INR per unit
  rate30DaysAgo: number;
  rate60DaysAgo: number;
  volatility30Day: number;            // Standard deviation of daily returns
  maxAdverseMove30Day: number;        // Worst case INR depreciation in 30 days (historical)
  potentialLossINR: number;           // maxAdverseMove30Day * abs(netPosition)
  hedgedAmount: number;               // Amount covered by forwards/locks
  unhedgedAmount: number;             // Net position minus hedged amount
  hedgeRatio: number;                 // hedgedAmount / abs(netPosition), 0-1
}

interface MaturityBucket {
  period: '0-7_days' | '8-15_days' | '16-30_days' | '31-60_days' | '61-90_days' | '90+_days';
  totalExposureINR: number;
  breakdownByCurrency: { currency: string; amountINR: number }[];
}
```

**Practical Example -- Agency Currency Exposure:**

```
Agency: "Wanderlust Travels" (boutique, INR 15 crore annual revenue)
Date: April 28, 2026

Open Positions (booked but not yet settled):
+ SGD 45,000  (hotels in Singapore, payable in 30-60 days)
+ THB 180,000 (hotels + activities in Thailand, payable in 15-30 days)
+ EUR 12,000  (hotels in Europe, payable in 45-75 days)
+ AED 25,000  (hotels in Dubai, payable in 30 days)
- SGD 8,000   (customer prepayment in SGD via forex card, receivable)

Net exposure:
  SGD: -37,000 (owed to suppliers)
  THB: -180,000
  EUR: -12,000
  AED: -25,000

At current rates:
  SGD exposure: 37,000 * 64.01 = INR 23,68,370
  THB exposure: 180,000 * 2.45 = INR 4,41,000
  EUR exposure: 12,000 * 89.50 = INR 10,74,000
  AED exposure: 25,000 * 22.72 = INR 5,68,000

Total open exposure: INR 44,51,370

If INR depreciates 3% across the board (typical in a volatile quarter):
  Potential additional cost: INR 44,51,370 * 0.03 = INR 1,33,541

For an agency with 8% net margin, this is equivalent to losing
the margin on ~INR 16.7 lakh of bookings.
```

### B. Forward Contracts

```typescript
interface ForwardContract {
  id: string;
  agencyId: string;
  bankName: string;                   // "HDFC Bank", "ICICI Bank"
  contractNumber: string;
  currencyPair: string;               // "USD/INR", "SGD/INR"
  direction: 'buy' | 'sell';          // Agency buys foreign currency (to pay supplier)
  notionalAmount: number;             // Foreign currency amount
  notionalAmountInINR: number;        // At forward rate
  spotRate: number;                   // Rate on booking date
  forwardRate: number;                // Agreed rate for maturity date
  forwardPoints: number;              // forwardRate - spotRate
  maturityDate: string;               // When the contract settles
  bookingDate: string;
  marginDeposited: number;            // 4-5% of notional in INR
  marginRefunded: boolean;
  status: 'booked' | 'active' | 'partially_settled' | 'settled' | 'cancelled' | 'rolled_over';
  linkedBookings: string[];           // Booking IDs this hedge covers
  supplierPayments: {
    supplierId: string;
    amount: number;
    settledAt: string | null;
  }[];
  profitLoss: number | null;          // vs. spot rate at maturity
  cancelledAt: string | null;
  cancellationCharge: number | null;
  rolledOverTo: string | null;        // New contract ID if rolled over
  createdAt: string;
}

// Forward contract economics for boutique agencies:
//
// Minimum ticket size: Typically USD 25,000-50,000 equivalent
// (Smaller agencies may not qualify or may find it uneconomical)
//
// Margin: 4-5% of notional value
// For SGD 37,000 forward at 64.01: Notional = INR 23,68,370
// Margin required: INR 94,735 - 1,18,419 (4-5%)
//
// Cost: Bank charges 0.1-0.3% of notional
// For above: INR 2,368 - 7,105
//
// Benefit: Locks the rate, eliminates uncertainty
// If INR depreciates 3% during contract period, savings = INR 71,051
// Net benefit after cost: INR 63,946 - 68,683
```

### C. Natural Hedging and EEFC Accounts

```typescript
interface EEFCAccount {
  id: string;
  agencyId: string;
  bankName: string;
  accountNumber: string;
  accountCurrency: string;            // "USD", "EUR", "SGD"
  balances: {
    currency: string;
    amount: number;
    lastUpdated: string;
  }[];
  // EEFC rules:
  // - 100% of foreign exchange earnings can be credited
  // - No interest paid on EEFC balances (as of current rules)
  // - Can be used for permissible payments (supplier settlements)
  // - Must be used within specified period (currently no mandatory conversion)
  // - RBI Master Direction on Export of Services governs usage
}

interface NaturalHedgeMatch {
  id: string;
  currency: string;
  receivables: {
    source: string;                   // Customer prepayment, forex card load, etc.
    amount: number;
    expectedDate: string;
  }[];
  payables: {
    supplier: string;
    amount: number;
    dueDate: string;
  }[];
  matchedAmount: number;              // Amount that can be naturally hedged
  unmatchedAmount: number;            // Requires forward contract or acceptance of risk
  savingsVsForward: number;           // Cost saved by not needing forward contract
}

// Natural hedging strategy:
// 1. Encourage customers to pay in foreign currency for foreign components
//    (via forex card load, international wire, or foreign currency demand draft)
// 2. Hold these receipts in EEFC account
// 3. Settle suppliers from EEFC account in same currency
// 4. No conversion risk for the matched portion
//
// Limitation: Most Indian customers prefer to pay in INR.
// Natural hedging covers only 10-30% of exposure for typical agencies.
```

### D. Rate Fluctuation Alerts

```typescript
interface RateAlert {
  id: string;
  agencyId: string;
  currency: string;
  alertType: 'daily_move' | 'weekly_move' | 'threshold' | 'volatility_spike';
  threshold: number;                  // Percentage (e.g., 2 for 2%)
  currentRate: number;
  previousRate: number;               // Rate at comparison point
  changePercent: number;              // Actual change
  direction: 'inr_stronger' | 'inr_weaker' | 'stable';
  impactEstimate: {
    openExposureINR: number;
    estimatedImpactINR: number;       // Potential P&L impact
  };
  triggeredAt: string;
  acknowledgedBy: string | null;
  actionTaken: string | null;
  relatedAlerts: string[];            // IDs of alerts for other currencies triggered together
}

interface RateAlertConfig {
  agencyId: string;
  currencies: string[];
  alertRules: {
    type: 'daily_move' | 'weekly_move' | 'threshold';
    threshold: number;                // Percentage
    severity: 'info' | 'warning' | 'critical';
    notificationChannels: ('email' | 'sms' | 'dashboard' | 'slack')[];
    recipients: string[];
  }[];
  quietHours: {
    start: string;                    // "22:00" IST
    end: string;                      // "08:00" IST
  };
  weekendAlerts: boolean;             // Alert on weekend moves?
}
```

**Alert Severity Matrix:**

| Move | 1-Day | 1-Week | Action |
|------|-------|--------|--------|
| < 1% | Info | Info | No action required |
| 1-2% | Warning | Info | Monitor, review open quotes |
| 2-3% | Warning | Warning | Re-price pending quotes, consider hedging |
| 3-5% | Critical | Warning | Immediate review, hedge if unhedged |
| > 5% | Critical | Critical | Emergency review, all open quotes re-priced |

### E. Hedging Strategy for Boutique Agencies

```typescript
interface HedgingStrategy {
  agencyId: string;
  agencyProfile: {
    annualRevenue: number;            // INR
    monthlyForeignSpend: number;      // INR equivalent
    currencies: string[];
    averageBookingLeadTime: number;   // Days between booking and travel
    riskAppetite: 'conservative' | 'moderate' | 'aggressive';
    hasDedicatedTreasury: boolean;
  };
  recommendedApproach: HedgingApproach[];
}

interface HedgingApproach {
  type: 'buffer_pricing' | 'pre_buy_forex' | 'supplier_rate_lock' | 'forward_contract' | 'option_contract';
  description: string;
  applicableFor: string;              // Agency size / revenue range
  cost: string;
  benefit: string;
  risk: string;
  complexity: 'low' | 'medium' | 'high';
  prerequisites: string[];
}

// Tiered recommendations:
//
// TIER 1: Micro agencies (Revenue < INR 5 crore)
// Strategy: Buffer pricing (add 2-3% to foreign currency quotes)
// - Simplest approach, no financial instruments needed
// - Absorbs normal 30-day fluctuation (INR rarely moves >3% in 30 days)
// - Downside: Pricing may be uncompetitive vs. agencies with better hedging
// - No forward contracts (below bank minimum ticket size)
//
// TIER 2: Small agencies (Revenue INR 5-25 crore)
// Strategy: Buffer pricing + selective forwards for large exposures
// - Buffer pricing for routine bookings
// - Forward contracts for large group bookings (INR 10+ lakh foreign component)
// - Pre-buy forex via EEFC account when rates are favorable
// - Negotiate rate locks with top 5 suppliers
//
// TIER 3: Medium agencies (Revenue INR 25-100 crore)
// Strategy: Active hedging program
// - Dedicated treasury oversight (even if not full-time)
// - Forward contracts for top 3 currency exposures
// - EEFC accounts for natural hedging
// - Supplier rate lock agreements
// - Monthly exposure review and hedge rebalancing
//
// TIER 4: Large agencies (Revenue > INR 100 crore)
// Strategy: Professional treasury management
// - Dedicated treasury team or outsourced treasury
// - Full forward contract program
// - Currency options for asymmetric protection
// - Multi-bank relationship for competitive forward pricing
// - Daily exposure monitoring and automated alerting
```

### F. Hedging Position Dashboard

```typescript
interface HedgingDashboard {
  agencyId: string;
  asOfDate: string;
  summary: {
    totalExposureINR: number;
    totalHedgedINR: number;
    totalUnhedgedINR: number;
    overallHedgeRatio: number;        // 0-1
    unrealizedGainLossINR: number;     // Mark-to-market of forward positions
  };
  positionsByCurrency: {
    currency: string;
    exposure: number;
    hedged: number;
    hedgeRatio: number;
    avgHedgedRate: number;
    currentMarketRate: number;
    unrealizedGL: number;             // On hedged portion
  }[];
  upcomingMaturities: {
    contractId: string;
    currency: string;
    amount: number;
    maturityDate: string;
    daysToMaturity: number;
    matchedBookings: string[];
  }[];
  alerts: RateAlert[];
}
```

---

## Open Problems

### 1. Forward Contract Accessibility
- Indian banks typically require a minimum ticket size of USD 25,000-50,000 equivalent for forward contracts. Many boutique agencies have individual exposures below this threshold.
- Aggregating exposures across multiple bookings to meet minimums is operationally complex.
- **Research needed:** Which banks offer the lowest minimum ticket sizes? Do NBFCs or fintech platforms offer smaller forward contracts?

### 2. Forward Contract Rollover Risk
- If a trip is delayed or rescheduled, the forward contract maturity may not match the new payment date.
- Rolling over a contract incurs additional cost and may result in a less favorable rate.
- How do we handle this in the booking lifecycle? (Link forward maturity to payment schedule with buffer.)

### 3. Supplier Rate Lock Negotiation
- Can agencies negotiate rate locks with hotel chains and activity providers? (e.g., "Lock SGD rate for 60 days for confirmed bookings")
- Some global hotel chains (Marriott, Hilton) may offer rate locks for volume partners.
- Smaller/local suppliers are unlikely to offer rate locks.
- **Research needed:** Survey of rate lock options from key suppliers in Singapore, Thailand, Dubai, Europe.

### 4. Measuring Hedge Effectiveness
- For accounting purposes (Ind AS 109), hedge effectiveness must be measured and documented.
- Most boutique agencies are not required to comply with Ind AS 109 (applies to companies above certain thresholds).
- However, measuring whether hedging actually reduced risk is important for business decisions.
- Need a simple effectiveness metric: "Did the hedge save money vs. not hedging?"

### 5. Currency Risk in Package Pricing
- When quoting a fixed INR price for a package with foreign components, the agency absorbs all currency risk until the trip is settled.
- For packages quoted 3-6 months in advance, this risk is substantial.
- Should package pricing include an explicit "currency risk surcharge"? (Customer may resist.)
- Alternative: Quote in foreign currency with INR indicative, convert at booking time.

---

## Next Steps

1. **Build exposure calculator** -- Implement `RiskExposure` computation from open bookings, supplier payables, and customer receivables. Show net position per currency.
2. **Historical volatility analysis** -- Pull 2-year rate history for INR/SGD, INR/THB, INR/EUR, INR/AED. Calculate 30-day, 60-day, 90-day volatility and worst-case moves.
3. **Bank survey for forward contracts** -- Contact HDFC, ICICI, Axis, SBI for forward contract terms (minimum ticket size, margin, charges, currency pairs available).
4. **EEFC account feasibility** -- Research RBI rules on EEFC accounts for travel agencies. Identify which banks offer EEFC with multi-currency support.
5. **Rate alert prototype** -- Implement `RateAlertConfig` with daily monitoring and multi-channel notification.
6. **Supplier rate lock survey** -- Contact key hotel and activity suppliers to assess willingness to offer rate locks.
7. **Hedging strategy guide for agencies** -- Create a decision framework: when to hedge, how much to hedge, which instrument to use, based on agency size and risk appetite.

---

## Cross-References

| Document | Relevance |
|----------|-----------|
| [FOREX_MGMT_01_RATES](FOREX_MGMT_01_RATES.md) | Rate history feeds volatility analysis and hedging decisions |
| [FOREX_MGMT_02_MULTI_CURRENCY_BOOKING](FOREX_MGMT_02_MULTI_CURRENCY_BOOKING.md) | Open bookings create currency exposure |
| [FOREX_MGMT_04_FOREX_PRODUCTS](FOREX_MGMT_04_FOREX_PRODUCTS.md) | Forex cards and wire transfers as natural hedge tools |
| [FINANCE_03_TREASURY](FINANCE_03_TREASURY.md) | Treasury management and cash flow |
| [FINANCE_01_ACCOUNTING](FINANCE_01_ACCOUNTING.md) | Accounting for hedge instruments and mark-to-market |
| [SUPPLIER_SETTLE_02_PAYMENTS](SUPPLIER_SETTLE_02_PAYMENTS.md) | Supplier payment scheduling drives hedge maturity matching |

---

**Last Updated:** 2026-04-28
