# Commission Management 01: Calculation

> Commission rules, rates, and calculation logic

---

## Document Overview

**Focus:** Commission calculation rules
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Commission Structures
- What commission structures do we support?
- How do we handle different supplier rates?
- What about tiered commissions?
- How do we handle split commissions?

### Calculation Rules
- How are commissions calculated?
- What's the base amount?
- How do we handle taxes and fees?
- What about cancellations and refunds?

### Commission Types
- What types of commissions exist?
- How do we handle overrides?
- What about special rates?
- How do we handle incentives?

### Timing
- When are commissions earned?
- What about booking vs. travel date?
- How do we handle pending commissions?
- What about clawbacks?

---

## Research Areas

### A. Commission Structures

**Flat Rate:**

| Aspect | Description | Research Needed |
|--------|-------------|-----------------|
| **Percentage** | X% of booking value | ? |
| **Fixed amount** | ₹X per booking | ? |
| **Hybrid** | Base + variable | ? |

**Tiered Structure:**

| Tier | Condition | Rate | Research Needed |
|------|-----------|------|-----------------|
| **Bronze** | ₹0-5L/month | 5% | ? |
| **Silver** | ₹5-15L/month | 7% | ? |
| **Gold** | ₹15L+/month | 10% | ? |

**Split Commissions:**

| Scenario | Split | Research Needed |
|----------|-------|-----------------|
| **Multiple agents** | Custom split | ? |
| **Team lead + member** | Override + base | ? |
| **Referral** | Referrer + booking agent | ? |

### B. Base Calculation

**Commissionable Amount:**

| Component | Commissionable | Research Needed |
|-----------|----------------|-----------------|
| **Base fare/rate** | Yes | ? |
| **Taxes** | Usually no | ? |
| **Fees** | Depends | ? |
| **Surcharges** | Usually no | ? |
| **Service fees** | Yes (if ours) | ? |

**Calculation Formula:**

```
Commission = Commissionable Amount × Commission Rate

For flights:
  Base Fare × Rate = Commission

For hotels:
  Room Rate × Nights × Rate = Commission

For packages:
  Package Price × Rate = Commission
```

**Rounding:**

| Approach | Description | Research Needed |
|----------|-------------|-----------------|
| **Round to nearest** | Standard rounding | ? |
| **Round down** | Conservative | ? |
| **Round up** | Generous | ? |
| **No rounding** | Exact cents | ? |

### C. Commission Types

**Standard Commission:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Supplier commission** | From airline/hotel | ? |
| **Markup** | Our added margin | ? |
| **Service fee** | charged to customer | ? |

**Special Rates:**

| Type | When Used | Research Needed |
|------|-----------|-----------------|
| **Promotional rate** | Limited time offers | ? |
| **Volume bonus** | Threshold targets | ? |
| **New product bonus** | Incentivize sales | ? |
| **Manual override** | Exception handling | ? |

**Overrides:**

| Override Type | Description | Research Needed |
|---------------|-------------|-----------------|
| **Agent-specific** | Custom rate for agent | ? |
| **Booking-specific** | One-time adjustment | ? |
| **Supplier-specific** | Special supplier rate | ? |
| **Customer-specific** | VIP customer rate | ? |

### D. Earning Triggers

**Earned Events:**

| Event | Status | Research Needed |
|-------|--------|-----------------|
| **Booking confirmed** | Pending (can be clawed back) | ? |
| **Payment received** | Pending | ? |
| **Service consumed** | Earned (for most) | ? |
| **Cooling period passed** | Earned (no cancellations) | ? |

**Clawback Scenarios:**

| Scenario | Treatment | Research Needed |
|----------|-----------|-----------------|
| **Cancellation** | Reverse commission | ? |
| **Refund** | Reverse commission | ? |
| **Chargeback** | Reverse commission | ? |
| **Fraud** | Reverse + penalty | ? |

**Holding Periods:**

| Product Type | Holding Period | Research Needed |
|--------------|----------------|-----------------|
| **Flights** | After travel | ? |
| **Hotels** | After checkout | ? |
| **Packages** | After trip completion | ? |
| **Insurance** | After policy start | ? |

---

## Data Model Sketch

```typescript
interface CommissionRule {
  ruleId: string;
  name: string;

  // Scope
  supplierId?: string;
  productType?: ProductType;
  agentId?: string; // For agent-specific rules

  // Rate
  rateType: RateType;
  rateValue: number; // Percentage or fixed amount
  maxAmount?: number; // Cap

  // Calculation
  baseType: BaseType; // What to calculate on
  taxableComponents?: string[]; // What's included

  // Timing
  earningTrigger: EarningTrigger;
  holdingPeriodDays?: number;

  // Validity
  validFrom: Date;
  validTo?: Date;
}

type RateType =
  | 'percentage'
  | 'fixed'
  | 'tiered'
  | 'formula';

type BaseType =
  | 'total'
  | 'base_only'
  | 'base_plus_taxes'
  | 'custom';

type EarningTrigger =
  | 'booking_confirmed'
  | 'payment_received'
  | 'service_consumed'
  | 'holding_period_passed';

interface CommissionCalculation {
  calculationId: string;
  bookingId: string;

  // Input
  bookingAmount: number;
  commissionableAmount: number;
  appliedRule: CommissionRule;

  // Result
  commissionAmount: number;
  calculatedAt: Date;

  // Status
  status: CommissionStatus;
  earnedAt?: Date;
  paidAt?: Date;

  // Adjustments
  adjustments: CommissionAdjustment[];
}

type CommissionStatus =
  | 'pending'
  | 'earned'
  | 'held'
  | 'paid'
  | 'clawed_back';

interface TieredCommission {
  ruleId: string;
  tiers: CommissionTier[];

  // Period
  periodType: 'monthly' | 'quarterly' | 'annual';
}

interface CommissionTier {
  tierId: string;
  name: string;

  // Threshold
  minAmount: number;
  maxAmount?: number;

  // Rate
  rate: number;
}
```

---

## Open Problems

### 1. Rate Complexity
**Challenge:** Many different rates across suppliers

**Options:** Default rules, override system, bulk imports

### 2. Calculation Accuracy
**Challenge:** Getting commissionable amount right

**Options:** Clear rules, supplier data mapping, validation

### 3. Timing Ambiguity
**Challenge:** When is commission actually earned?

**Options:** Clear policy, configurable triggers, hold periods

### 4. Split Complexity
**Challenge:** Fairly splitting complex commissions

**Options:** Predefined splits, workflow approval, audit trail

### 5. Change Management
**Challenge:** Rates change frequently

**Options:** Versioned rules, effective dates, historical accuracy

---

## Next Steps

1. Define commission structure requirements
2. Build calculation engine
3. Create rule management UI
4. Implement tiered commissions

---

**Status:** Research Phase — Calculation patterns unknown

**Last Updated:** 2026-04-27
