# Travel Insurance 02: Quoting & Comparison

> Generating quotes, assessing risk, and comparing products

---

## Document Overview

**Focus:** How customers get insurance quotes and select policies
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Quote Requirements
- What data is needed to generate a quote?
- How do we handle incomplete information?
- What are the mandatory vs. optional fields?
- How do we handle pre-existing conditions?

### 2. Risk Assessment
- How is premium calculated?
- What factors affect pricing?
- How do we handle high-risk destinations?
- What about age and health factors?

### 3. Product Comparison
- How do we present multiple options?
- What differences matter to customers?
- How do we handle different coverage levels?
- What about price vs. coverage trade-offs?

### 4. Quote Validity
- How long is a quote valid?
- What happens when prices change?
- Can we lock in rates?
- How do we handle currency differences?

---

## Research Areas

### A. Quote Data Requirements

**Mandatory Information:**

| Field | Required | Notes |
|-------|----------|-------|
| **Trip dates** | Yes | Duration affects premium |
| **Destination(s)** | Yes | Risk varies by location |
| **Traveler ages** | Yes | Pricing factor |
| **Trip cost** | Sometimes | For cancellation coverage |
| **Residence country** | Yes | Eligibility |
| **Coverage type** | Yes | Single vs. annual, etc. |
| **Pre-existing conditions** | Sometimes | May affect eligibility |

**Optional Information:**

| Field | When Needed | Impact |
|-------|-------------|--------|
| **Pre-existing conditions** | For coverage | May exclude or surcharge |
| **Activities** | Adventure sports | May need additional coverage |
| **Deductible preference** | For pricing | Higher deductible = lower premium |
| **Coverage limits** | For comparison | Affects premium |

**Research:**
- What is the minimum viable data for a quote?
- Can we provide estimates with limited data?
- How do we collect sensitive medical information?

### B. Pricing Models

**Premium Calculation:**

```
Base Premium = f(Trip Cost, Duration, Destination, Ages)
Loading = Risk Adjustment (Destination, Activities, Health)
Discounts = (No Claims, Multi-Policy, etc.)
Final Premium = Base Premium + Loading - Discounts + Fees/Taxes
```

**Factors by Impact:**

| Factor | Impact | Relative Weight |
|--------|--------|-----------------|
| **Trip cost** | High | For cancellation coverage |
| **Duration** | Medium | Longer = more expensive |
| **Destination** | High | Risk varies significantly |
| **Age** | Medium | Older = more expensive |
| **Coverage level** | High | More coverage = more cost |
| **Deductible** | Medium | Higher deductible = lower cost |

**Research:**
- What are the actual pricing formulas?
- How do insurers weigh different factors?
- Can we get real-time pricing from APIs?

### C. Product Comparison

**Comparison Dimensions:**

| Dimension | Customer Impact | Research Needed |
|-----------|-----------------|-----------------|
| **Price** | Primary decision factor | ? |
| **Medical limit** | Critical for medical emergencies | ? |
| **Cancellation coverage** | Important for expensive trips | ? |
| **Deductible** | Affects out-of-pocket costs | ? |
| **Exclusions** | Critical for claims | ? |
| **Insurer rating** | Confidence in claims | ? |
| **24/7 assistance** | Important value-add | ? |

**Display Strategy:**

| Approach | When to Use |
|----------|-------------|
| **Price leader** | Price-sensitive customers |
| **Best value** | Balance of price and coverage |
| **Most coverage** | Coverage-focused customers |
| **Recommended** | Our selection based on typical needs |

**Research:**
- How do competitors present comparisons?
- What information is most important?
- How do we avoid overwhelming customers?

### D. Quote Validity & Timing

| Consideration | Industry Practice |
|---------------|-------------------|
| **Quote validity** | 24-72 hours typically |
| **Price lock** | Some insurers offer, most don't |
| **Currency** | Usually customer's residence currency |
| **Price changes** | Can happen until policy is issued |

**Research:**
- How do we handle quote expiration?
- What if price changes between quote and purchase?
- How do we show currency conversion?

---

## Quote Request Model

```typescript
// Research-level model - not final

interface InsuranceQuoteRequest {
  // Trip details
  tripDates: {
    startDate: Date;
    endDate: Date;
  };
  destination: string[];  // Countries or regions
  tripCost?: Money;  // For cancellation coverage

  // Travelers
  travelers: {
    count: number;
    ages: number[];
    primaryResidence: string;  // Country code
  };

  // Coverage preferences
  coverageType: CoverageType;
  coverageLevel?: 'basic' | 'standard' | 'comprehensive';
  deductibles?: DeductibleOption;

  // Additional
  activities?: string[];  // Adventure sports, etc.
  preExistingConditions?: PreExistingConditionInfo;

  // Meta
  quoteId?: string;
  expiresAt?: Date;
}

type CoverageType =
  | 'single_trip'
  | 'annual_multi_trip'
  | 'backpacker'
  | 'long_stay';

interface PreExistingConditionInfo {
  hasConditions: boolean;
  details?: string[];  // Collected only if needed
}
```

---

## Quote Response Model

```typescript
interface InsuranceQuoteResponse {
  quoteId: string;
  validUntil: Date;
  requestedAt: Date;

  // Options
  options: QuoteOption[];

  // Metadata
  currency: string;
  disclaimers: string[];
}

interface QuoteOption {
  insurer: string;
  productName: string;

  // Pricing
  pricing: {
    basePremium: Money;
    taxes: Money;
    fees: Money;
    total: Money;
  };

  // Coverage highlights
  coverage: {
    medical: CoverageDetail;
    evacuation: CoverageDetail;
    cancellation: CoverageDetail;
    baggage: CoverageDetail;
    other: CoverageDetail[];
  };

  // Terms
  deductible: Money;
    excess?: Money;

  // Policy
  policyDocument: string;
  pdsUrl: string;

  // Badges
  badges?: Badge[];  // "Best value", "Most coverage", etc.

  // Rating
    rating?: number;
  reviews?: number;
}
```

---

## Risk Assessment

**High-Risk Indicators:**

| Factor | Risk Level | Impact |
|--------|-----------|--------|
| **Destination** | War zone, high crime | May not insure |
| **Age** | >70, <1 | Higher premium or exclude |
| **Activities** | Extreme sports | Exclusion or surcharge |
| **Health** | Serious pre-existing | Exclusion or loading |
| **Duration** | >6 months | Different product needed |

**Research:**
- What are the high-risk destinations?
- How do we handle customers we can't insure?
- What activities require special coverage?

---

## Open Problems

### 1. Pre-Existing Conditions Declaration
**Challenge:** Collecting sensitive medical information

**Options:**
- Simple yes/no, then medical screening
- Detailed declaration form
- Anonymous screening

**Research:** What are best practices? Privacy considerations?

### 2. Quote Accuracy
**Challenge:** Quote differs from final price

**Questions:**
- How do we ensure accuracy?
- What if customer provides incorrect info?
- How do we handle disputes?

### 3. Comparison Paralysis
**Challenge:** Too many options confuse customers

**Options:**
- Limit to 3-5 options
- Provide "recommended" option
- Progressive disclosure (show more details on demand)

**Research:** What is the optimal number of options?

### 4. Cross-Border Issues
**Challenge:** Customer lives in Country A, buying insurance for trip from Country B

**Questions:**
- Which country's regulations apply?
- Can we sell across borders?
- What about currency?

---

## Competitor Research Needed

| Competitor | Quote UX | Notable Patterns |
|------------|----------|------------------|
| **Compare the Market** | ? | ? |
| **Squaremouth** | ? | ? |
| **InsureMyTrip** | ? | ? |
| **Indian insurers** | ? | ? |

---

## Experiments to Run

1. **Quote API test:** How fast and accurate are insurer APIs?
2. **Data collection study:** What data can we collect without drop-off?
3. **Comparison UX test:** How do customers compare options?
4. **Price sensitivity study:** How much does price matter vs. coverage?

---

## References

- [Activities - Search](./ACTIVITIES_02_SEARCH.md) — Similar comparison patterns
- [Flight Integration - Pricing](./FLIGHT_INTEGRATION_03_PRICING.md) — Pricing models

---

## Next Steps

1. Test insurer quote APIs
2. Design quote data collection flow
3. Build comparison algorithm
4. Create quote-to-bind conversion tracking
5. Optimize for conversion

---

**Status:** Research Phase — Quoting patterns unknown

**Last Updated:** 2026-04-27
