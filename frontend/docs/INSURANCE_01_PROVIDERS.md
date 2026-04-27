# Travel Insurance 01: Provider Landscape

> Insurance providers, products, and market structure

---

## Document Overview

**Focus:** Understanding the travel insurance ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Provider Landscape
- Who are the major travel insurance providers?
- What are the different types of insurers? (Specialized vs. general)
- Which providers offer APIs vs. manual processing?
- What are the commission structures?
- How do providers differ by region?

### 2. Product Types
- What types of travel insurance exist?
- What does each cover? (Medical, cancellation, baggage, etc.)
- How do products differ by customer type? (Individual vs. corporate)
- What are the common exclusions?

### 3. Regulatory Environment
- What are the regulatory requirements by region?
- Who regulates travel insurance?
- What licenses are required to sell?
- What are the compliance obligations?

### 4. Market Structure
- How is insurance distributed? (Direct, via agents, via platforms)
- What are the economics? (Margins, commissions)
- Who bears the risk? (Insurer, agent, platform)
- What are the common business models?

---

## Research Areas

### A. Global Insurance Providers

**Specialized Travel Insurers:**

| Provider | Regions | API | Notes |
|----------|---------|-----|-------|
| **Allianz** | Global | ? | Market leader? |
| **AXA** | Global | ? | ? |
| **Chubb** | Global | ? | ? |
| **AIG** | Global | ? | ? |
| **Travel Guard** | US | ? | ? |

**Regional Players:**

| Region | Providers | Notes |
|--------|-----------|-------|
| **India** | Tata AIG, Bajaj, HDFC Ergo, ICICI Lombard | ? |
| **SE Asia** | ? | ? |
| **UK/Europe** | ? | ? |
| **Australia** | ? | ? |

**Research Needed:**
- API availability for quoting and binding
- Commission structures
- Integration complexity
- Product offerings

### B. Product Types

**Coverage Categories:**

| Coverage Type | What It Covers | Typical Limits | Research Needed |
|---------------|----------------|----------------|-----------------|
| **Medical** | Emergency medical treatment | $50K-$500K | ? |
| **Medical evacuation** | Air ambulance, medical transport | $100K-$1M | ? |
| **Trip cancellation** | Pre-trip cancellation | Trip cost | ? |
| **Trip interruption** | Cutting trip short | 50-100% of trip | ? |
| **Baggage loss/delay** | Lost, stolen, delayed baggage | $500-$2,500 | ? |
| **Flight accident** | Accidental death/disability | $25K-$500K | ? |
| **Travel delay** | Missed connections, delays | $500-$1,500 | ? |
| **Rental car excess** | Deductible coverage | $500-$5,000 | ? |

**Questions:**
- Which coverages are mandatory vs. optional?
- What are common exclusions?
- How do limits vary by region/destination?

### C. Distribution Models

**Distribution Channels:**

| Channel | How It Works | Economics |
|---------|--------------|-----------|
| **Direct** | Customer buys from insurer | Higher margin for insurer |
| **Agent** | Travel agent sells | Commission 10-30% |
| **Platform** | OTA/website sells | Commission 15-40% |
| **Embedded** | Airline checkout adds | Commission 20-50% |

**Research:**
- Which model works for our use case?
- What are the commission structures?
- What are the volume requirements?

### D. Regulatory Considerations

**By Region:**

| Region | Regulator | Key Requirements | Research Needed |
|--------|-----------|------------------|-----------------|
| **India** | IRDAI | License to sell, disclosure | ? |
| **UK** | FCA | Authorization, conduct rules | ? |
| **EU** | EIOPA (via national) | Insurance Distribution Directive | ? |
| **US** | State commissioners | State-by-state licensing | ? |
| **Australia** | APRA/ASIC | AFSL license | ? |

**Questions:**
- What licenses do we need?
- Can we work without a license? (Referral model?)
- What are the disclosure requirements?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface InsuranceProvider {
  id: string;
  name: string;
  type: 'specialized' | 'general_insurer' | 'broker';

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;
  apiDocumentation?: string;

  // Commercial
  commissionRate: number;
  paymentTerms: PaymentTerms;
  volumeRequirements?: VolumeRequirements;

  // Products
  products: InsuranceProduct[];

  // Regulatory
  licensedRegions: string[];
  complianceRequirements: ComplianceRequirement[];

  // Capabilities
  instantIssuance: boolean;
  onlineClaims: boolean;
  24hAssistance: boolean;
}

interface InsuranceProduct {
  id: string;
  providerId: string;
  name: string;
  type: ProductType;

  // Coverage
  coverages: Coverage[];
  limits: CoverageLimits;
  deductibles?: Deductible[];

  // Eligibility
  minAge: number;
  maxAge: number;
  residentRegions: string[];
  destinationRegions: string[];

  // Pricing
  pricing: PricingModel;

  // Terms
  duration: DurationLimits;
  preExistingConditionPolicy: 'covered' | 'excluded' | 'optional_upgrade';

  // Documentation
  policyDocument: string;
  pdsUrl: string;  // Product Disclosure Statement
}

type ProductType =
  | 'single_trip'
  | 'annual_multi_trip'
  | 'backpacker'
  | 'senior'
  | 'student'
  | 'family'
  | 'corporate';

interface Coverage {
  type: CoverageType;
  included: boolean;
  limit: Money;
  deductible?: Money;
}

type CoverageType =
  | 'medical_emergency'
  | 'medical_evacuation'
  | 'trip_cancellation'
  | 'trip_interruption'
  | 'baggage_loss'
  | 'baggage_delay'
  | 'flight_delay'
  | 'flight_accident'
  | 'rental_car_excess'
  | 'cancel_for_any_reason';
```

---

## Integration Approaches

### 1. Direct API Integration
**Best for:** Large insurers with mature APIs

**Pros:**
- Real-time quotes
- Instant policy issuance
- Automated claims initiation

**Cons:**
- Integration complexity
- Maintenance overhead
- Provider dependency

### 2. Aggregator/Broker Integration
**Best for:** Access to multiple insurers

**Examples:** Cover-More, A&K

**Pros:**
- Single integration
- Multiple products
- Standardized interface

**Cons:**
- Lower margin
- Less control
- Additional layer

### 3. Referral Model
**Best for:** No license, low volume

**Approach:** Redirect customer to insurer, earn referral fee

**Pros:**
- No licensing required
- No operational overhead
- Simple integration

**Cons:**
- Lowest revenue
- Customer leaves platform
- No control over experience

**Research:**
- Which model fits our stage?
- What are the licensing requirements?
- What is the revenue potential?

---

## Key Insurance Concepts

### Premium Calculation Factors

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Trip cost** | Higher cost = higher premium | ? |
| **Destination** | Some destinations higher risk | ? |
| **Duration** | Longer trip = higher premium | ? |
| **Age of travelers** | Older = higher premium | ? |
| **Pre-existing conditions** | May exclude or cost more | ? |
| **Coverage level** | Basic vs. comprehensive | ? |
| **Deductible** | Higher deductible = lower premium | ? |

### Policy Documents

**Required Documents:**

| Document | Purpose | Delivery |
|----------|---------|---------|
| **Policy certificate** | Proof of coverage | Immediate |
| **Policy wording** | Full terms and conditions | At purchase |
| **PDS** | Product Disclosure Statement | At purchase |
| **Claims form** | For making claims | When needed |
| **Emergency contact** | 24/7 assistance | At purchase |

---

## Open Problems

### 1. Pre-Existing Medical Conditions
**Challenge:** Many customers have pre-existing conditions

**Options:**
- Exclude from coverage (standard)
- Offer medical screening
- Cover with surcharge
- Offer "pre-existing condition waiver"

**Research:** What are industry practices?

### 2. Age Limits
**Challenge:** Some insurers won't cover older travelers

**Questions:**
- What are the age limits?
- Can we find products for all ages?
- How do we handle this?

### 3. Regional Licensing
**Challenge:** We sell to customers globally

**Questions:**
- Which regions require local licenses?
- Can we use a partner's license?
- What if we operate without a license?

### 4. Claims Handling
**Challenge:** We don't want to be in the claims business

**Options:**
- All claims go directly to insurer
- We provide support but insurer decides
- We handle simple claims, insurer complex

**Research:** What are customer expectations?

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **Airbnb** | ? | ? |
| **Airline sites** | ? | ? |
| **Local India agents** | ? | ? |

---

## Experiments to Run

1. **API availability test:** Which insurers offer bookable APIs?
2. **Commission analysis:** What are typical commissions?
3. **License research:** What licenses do we need?
4. **Product comparison:** Compare products across insurers

---

## References

- [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Add-on component
- [Payment Processing](./PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) — Premium collection

---

## Next Steps

1. Research insurance providers in key markets
2. Understand licensing requirements
3. Analyze commission structures
4. Compare product offerings
5. Evaluate integration options

---

**Status:** Research Phase — Insurance landscape unknown

**Last Updated:** 2026-04-27
