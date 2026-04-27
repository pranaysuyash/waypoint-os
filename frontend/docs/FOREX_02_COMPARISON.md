# Forex & Currency Services 02: Rate Comparison

> Comparing exchange rates, fees, and total cost of ownership

---

## Document Overview

**Focus:** How customers compare and select forex options
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Rate Comparison
- How do we get live exchange rates?
- What is the interbank rate?
- How do we calculate provider margin?
- How do we show this transparently?

### 2. Total Cost Calculation
- What are all the fees involved?
- How do we calculate total cost?
- How do we compare across providers?
- What about different usage patterns?

### 3. Recommendation Engine
- How do we recommend the best option?
- What factors matter? (Rate, convenience, reliability?)
- How do we handle different trip types?
- What about large vs. small amounts?

### 4. Transparency
- How do we show hidden fees?
- What about dynamic rates?
- How do we handle rate changes between quote and order?
- What are the disclaimers needed?

---

## Research Areas

### A. Exchange Rate Sources

**Rate Sources:**

| Source | Type | Latency | Cost |
|--------|------|---------|------|
| **Provider API** | Provider's rate | Varies | Free |
| **Independent APIs** | Mid-market | Real-time | Paid |
| **Scraping** | Various | Slow | Free but fragile |

**Independent Rate APIs:**

| Provider | API | Cost | Notes |
|----------|-----|------|-------|
| **Fixer.io** | Yes | Paid | ? |
| **Open Exchange Rates** | Yes | Free/Paid | ? |
| **XE.com** | Maybe | ? | ? |
| **OANDA** | Yes | Paid | ? |

**Research:**
- Which APIs are reliable?
- What are the costs?
- How do we handle rate caching?

### B. Total Cost Calculation

**Cost Components:**

```
Amount to Exchange
× (Exchange Rate - Margin)
= Base Foreign Currency Received

+ Issuance Fee
+ Reload Fee (if applicable)
+ ATM Fees (estimated usage)
+ Cross-Currency Fee (estimated)
= Total Fees

Effective Rate = (Amount + Total Fees) / Amount Received
```

**Example Calculation:**

| Item | Amount |
|------|--------|
| INR to exchange | ₹100,000 |
| Interbank rate | 83 INR/USD |
| Provider rate | 84.5 INR/USD (1.8% margin) |
| USD received | $1,183 |
| Issuance fee | ₹200 |
| Total effective rate | 84.67 INR/USD |

**Research:**
- How do we estimate ATM usage?
- What about cross-currency fees?
- How do we present this clearly?

### C. Usage Pattern Analysis

**Different Patterns:**

| Pattern | Characteristics | Best Option |
|---------|----------------|-------------|
| **Light traveler** | Small amount, occasional ATM | Forex card or credit card |
| **Heavy cash user** | Mostly cash | Currency notes |
| **Digital-first** | Mostly card payments | Forex card or international credit card |
| **Mixed** | Both cash and card | Forex card + some cash |

**Research:**
- What are the common patterns?
- How do we detect pattern from trip details?
- Which option wins for each pattern?

### D. Competitor Comparison

**Comparison Dimensions:**

| Dimension | Weight | Notes |
|-----------|--------|-------|
| **Exchange rate** | High | Biggest cost |
| **Fees** | High | Can add up |
| **Convenience** | Medium | Delivery, reload |
| **Acceptance** | High | Where can it be used |
| **Support** | Medium | 24/7 important |
| **Reloadability** | Medium | For long trips |

---

## Comparison Data Model

```typescript
interface ForexComparison {
  tripId: string;
  customerId: string;

  // Request
  request: {
    fromCurrency: string;
    toCurrency: string;
    amount: Money;
    travelDates: DateRange;
    usagePattern?: UsagePattern;
  };

  // Options
  options: ForexOption[];

  // Recommendations
  recommendations: {
    bestRate: string;  // option ID
    lowestTotalCost: string;
    mostConvenient: string;
  };
}

interface ForexOption {
  provider: string;
  product: ForexProductType;

  // Rates
  exchangeRate: number;
  margin: Percentage;  // vs. interbank
  interbankRate: number;

  // Fees
  fees: {
    issuance: Money;
    reload: Money;
    atmAbroad: Money;
    crossCurrency: Percentage;
  };

  // Totals
  calculations: {
    amountReceived: Money;
    totalFees: Money;
    effectiveRate: number;
    totalCost: Money;
  };

  // Delivery
  deliveryMethod: DeliveryMethod;
  deliveryTime: Duration;

  // Features
  features: {
    multiCurrency: boolean;
    reloadable: boolean;
    contactless: boolean;
  };
}
```

---

## Recommendation Logic

```
Input: Trip details, amount, usage pattern

1. Get current rates from all providers
2. Calculate total cost for each option
3. Factor in delivery time
4. Factor in convenience features
5. Rank by customer priority (rate vs. convenience)
6. Present top 3 options with rationale
```

---

## Transparency Display

**What to Show:**

| Information | Display |
|-------------|---------|
| **Exchange rate** | Provider rate vs. interbank |
| **Margin** | Percentage markup |
| **Fees** | Itemized list |
| **Total cost** | Final effective rate |
| **Delivery** | Time and method |
| **Acceptance** | Where card is accepted |

**Visual Aids:**

- Comparison table
- Cost breakdown chart
- Rate margin indicator
- Badge for "Best Value"

---

## Open Problems

### 1. Rate Changes
**Challenge:** Rate changes between quote and order

**Options:**
- Lock rate for X minutes
- Warn customer of volatility
| Real-time processing

**Research:** How do providers handle this?

### 2. Hidden Fees Discovery
**Challenge:** Some fees are unknown until usage

**Examples:**
- ATM fees (varies by ATM)
- Cross-currency fees
- Dynamic currency conversion (DCC) fees

**Options:**
- Estimate based on averages
- Show ranges
| Disclose unknowns

### 3. Small Amounts
**Challenge:** Fees outweigh benefits for small amounts

**Threshold:** Below $100 equivalent?

**Options:**
- Warn customer
- Recommend credit card instead
- Show effective cost

### 4. Large Amounts
**Challenge**: Different options for large amounts

**Options:**
- Wire transfer may be better
| Negotiated rates
| Split across products

---

## Competitor Research Needed

| Competitor | Comparison UX | Notable Patterns |
|------------|---------------|------------------|
| **BookMyForex** | ? | ? |
| **Wise** | ? | ? |
| **Bank sites** | ? | ? |

---

## Experiments to Run

1. **Rate accuracy test:** How do provider rates compare?
2. **Fee analysis study:** What are the total costs?
3. **User test:** How do customers interpret comparisons?
4. **Conversion tracking:** Which options convert best?

---

## References

- [Connectivity - Comparison](./CONNECTIVITY_02_COMPARISON.md) — Similar comparison patterns
- [Internationalization - Currency](./INTERNATIONALIZATION_03_CURRENCY.md) — Currency handling

---

## Next Steps

1. Integrate rate APIs
2. Build cost calculator
3. Design comparison UI
4. Implement recommendation engine
5. Test with real scenarios

---

**Status:** Research Phase — Comparison framework unknown

**Last Updated:** 2026-04-27
