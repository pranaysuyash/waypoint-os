# Loyalty Programs 01: Program Landscape

> Airline miles, hotel points, and rewards program ecosystem

---

## Document Overview

**Focus:** Understanding loyalty and rewards programs
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Program Types
- What are the different loyalty program types? (Airlines, hotels, cards?)
- Who are the major players in each category?
- How do programs differ by region?
- What are the program mechanics?

### 2. API Availability
- Which programs offer APIs?
- What can be done via API? (Balance, earning, redemption?)
- How do we authenticate with programs?
- What are the rate limits?

### 3. Value Proposition
- What is the value of points vs. cash?
- How do we calculate point valuations?
- What are the best redemptions?
- How do we compare across programs?

### 4. Integration Complexity
- How do we integrate with multiple programs?
- What are the technical challenges?
- What are the commercial considerations?
- What are the compliance requirements?

---

## Research Areas

### A. Airline Programs

**Major Indian Carriers:**

| Program | API? | Earning | Redemption | Notes |
|---------|------|--------|------------|-------|
| **Air India** | ? | ? | ? | ? |
| **Vistara** | ? | ? | ? | ? |
| **IndiGo** | ? | ? | ? | ? |
| **SpiceJet** | ? | ? | ? | ? |

**Major International Carriers:**

| Program | Alliance | API? | Notes |
|---------|----------|------|-------|
| **United** | Star | ? | ? |
| **Delta** | SkyTeam | ? | ? |
| **American** | Oneworld | ? | ? |
| **Emirates** | None | ? | ? |
| **Singapore** | Star | ? | ? |
| **Cathay** | Oneworld | ? | ? |

**Research Needed:**
- API availability for each
- Program mechanics
- Point expiration rules

### B. Hotel Programs

**Major Chains:**

| Program | API? | Properties | Notes |
|---------|------|------------|-------|
| **Marriott Bonvoy** | ? | Global | ? |
| **Hilton Honors** | ? | Global | ? |
| **IHG** | ? | Global | ? |
| **Hyatt** | ? | Global | ? |
| **Accor** | ? | Global | ? |
| **Taj** | ? | India | ? |

**Research:**
- API availability
- Point values
| Redemption options

### C. Credit Card Programs

**Indian Cards with Travel Rewards:**

| Card | Program | Points | Transfer Partners | Notes |
|------|---------|--------|-------------------|-------|
| **Axis Magnus** | ? | ? | ? | ? |
| **HDFC Infinia** | ? | ? | ? | ? |
| **SBI Aurum** | ? | ? | ? | ? |
| **Amex Platinum** | ? | ? | ? | ? |

**Research:**
- Transfer partners
- Point earning rates
| Annual fees vs. benefits

### D. Aggregator Platforms

| Platform | What They Do | API? | Notes |
|----------|---------------|------|-------|
| **Points.com** | Loyalty management | ? | ? |
| **AwardWallet** | Balance tracking | ? | ? |
| **UsingMiles** | ? | ? | ? |

**Research:**
- Can we leverage existing aggregators?
| What APIs exist?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface LoyaltyProgram {
  id: string;
  name: string;
  type: ProgramType;
  alliance?: AllianceType;

  // Integration
  hasApi: boolean;
  apiDocumentation?: string;
  authMethod?: AuthMethod;

  // Mechanics
  earning: EarningRules;
  redemption: RedemptionRules;
  expiration: ExpirationRules;

  // Value
  pointValue: PointValuation;  // Estimated value per point
  transferPartners?: TransferPartner[];

  // Customer accounts
  customerAccounts: CustomerAccount[];
}

type ProgramType =
  | 'airline'
  | 'hotel'
  | 'credit_card'
  | 'rental_car'
  | 'other';

interface CustomerAccount {
  id: string;
  customerId: string;
  programId: string;
  accountNumber: string;
  linkedAt: Date;

  // Auth
  credentials?: Credential;

  // Balances
  balances: {
    points: number;
    miles?: number;
    tierCredits?: number;
    tierStatus?: string;
  };

  // Activity
  lastSync?: Date;
  lastActivity?: Date;
}

interface Credential {
  type: 'username_password' | 'api_key' | 'oauth';
  encrypted: string;
}
```

---

## Point Valuation

**Valuation Framework:**

| Program | Point Value (₹) | Best Redemption | Worst Redemption |
|----------|------------------|-----------------|------------------|
| **Airline** | 0.5-1.5 | International flights | Merchandise |
| **Hotel** | 0.4-1.0 | Free nights | Merchandise |
| **Card** | 0.3-1.0 | Travel transfers | Cash back |

**Research:**
- What are the actual valuations?
- How do valuations change?
- How do we calculate this?

---

## Integration Approaches

### 1. Direct API Integration
**Best for:** Programs with open APIs

**Pros:**
- Real-time data
- Full functionality
- Direct relationship

**Cons:**
- Each program different
- Maintenance overhead
| May require partnership

### 2. Aggregator Integration
**Best for:** Quick coverage

**Pros:**
- Single integration
| Multiple programs
| Standardized interface

**Cons:**
- Additional cost
| Dependent on aggregator
| May have limited features

### 3. Manual/Screen Scraping
**Best for:** Programs without APIs

**Pros:**
- Can work with anyone

**Cons:**
- Fragile
| Slow
| Not scalable

---

## Open Problems

### 1. Authentication
**Challenge**: Each program has different auth

**Options:**
- Store customer credentials (risky)
- OAuth where available
| Customer manually connects

**Research**: What are the security implications?

### 2. Real-Time Balance
**Challenge**: Balances change constantly

**Options:**
- Real-time sync via API
- Periodic sync
| Customer-triggered sync

### 3. Point Expiration
**Challenge**: Points expire at different times

**Questions:**
- How do we track this?
| How do we warn customers?
| Can we prevent expiration?

### 4. Commercial Terms
**Challenge**: What are our economics?

**Questions:**
- Do we earn commission on bookings?
| Do we get referral fees?
| What are the restrictions?

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **AwardWallet** | ? | ? |
| **UsingMiles** | ? | ? |
| **Travel agents** | ? | ? |

---

## Experiments to Run

1. **API audit**: Which programs have APIs?
2. **Valuation study**: What are points worth?
3. **Customer survey**: What programs do customers use?
4. **Integration test**: Can we connect to programs?

---

## References

- [Flight Integration](./FLIGHT_INTEGRATION_MASTER_INDEX.md) — Airline programs
| [Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md) — Hotel programs

---

## Next Steps

1. Audit loyalty program APIs
2. Analyze point valuations
3. Design account linking flow
4. Build balance tracking
5. Implement earning/redemption

---

**Status**: Research Phase — Program landscape unknown

**Last Updated**: 2026-04-27
