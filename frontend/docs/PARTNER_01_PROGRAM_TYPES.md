# Partner & Affiliate Management 01: Program Types

> Partner models, affiliate structures, and relationship types

---

## Document Overview

**Focus:** Partner program structures
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Partner Categories
- What types of partners exist?
- How do we categorize them?
- What are the differences?
- How do we manage each type?

### Commission Structures
- How are partners compensated?
- What commission models work?
- How do we handle tiers?
- What about bonuses?

### Program Benefits
- What do partners get?
- How do we structure benefits?
- What about exclusivity?
- How do we differentiate?

### Contract Terms
- What terms are needed?
- How do we handle exclusivity?
- What about termination?
- How do we manage renewals?

---

## Research Areas

### A. Partner Types

**Affiliate Partners:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Relationship** | Arm's length | ? |
| **Compensation** | Commission on referrals | ? |
| **Integration** | Tracking link/API | ? |
| **Examples** | Bloggers, influencers | ? |

**Channel Partners:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Relationship** | Closer, ongoing | ? |
| **Compensation** | Commission + incentives | ? |
| **Integration** | Deeper integration | ? |
| **Examples** | OTAs, travel agents | ? |

**Strategic Partners:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Relationship** | Long-term, strategic | ? |
| **Compensation** | Revenue share | ? |
| **Integration** | Full integration | ? |
| **Examples** | Airlines, hotel chains | ? |

**Referral Partners:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Relationship** | Informal | ? |
| **Compensation** | One-time bounty | ? |
| **Integration** | Manual or light | ? |
| **Examples** | Customers, businesses | ? |

### B. Commission Models

**Percentage-Based:**

| Model | Description | Use Case | Research Needed |
|-------|-------------|----------|-----------------|
| **Flat %** | Fixed % of booking value | Standard | ? |
| **Tiered %** | Higher % for more volume | Growth incentive | ? |
| **Category-based** | Different % by product | Mix management | ? |
| **Lifetime %** | % on all customer bookings | Long-term value | ? |

**Fixed Amount:**

| Model | Description | Use Case | Research Needed |
|-------|-------------|----------|-----------------|
| **Per booking** | Fixed ₹ per booking | Simple | ? |
| **Per lead** | Fixed ₹ per qualified lead | Lead gen | ? |
| **Per signup** | Fixed ₹ for new customer | Acquisition | ? |

**Hybrid Models:**

| Model | Components | Research Needed |
|-------|------------|-----------------|
| **Base + bonus** | Base % + volume bonus | ? |
| **% + bounty** | Commission + signup bounty | ? |
| **Tiered + accelerator** | Tier + growth accelerator | ? |

### C. Program Benefits

**Standard Benefits:**

| Benefit | Tier | Research Needed |
|---------|------|-----------------|
| **Commission** | All | ? |
| **Tracking dashboard** | All | ? |
| **Marketing materials** | All | ? |
| **Support** | All | ? |

**Tiered Benefits:**

| Benefit | Silver | Gold | Platinum | Research Needed |
|---------|--------|------|----------|-----------------|
| **Base commission** | 5% | 7% | 10% | ? |
| **Performance bonus** | — | Quarterly | Monthly | ? |
| **Dedicated manager** | — | — | Yes | ? |
| **Co-marketing** | — | Yes | Yes | ? |
| **Exclusive deals** | — | — | Yes | ? |
| **API access** | — | Yes | Yes | ? |
| **White label** | — | — | Yes | ? |

**Non-Monetary Benefits:**

| Benefit | Description | Research Needed |
|---------|-------------|-----------------|
| **Training** | Product education | ? |
| **Leads** | Customer referrals | ? |
| **Tools** | Booking engine, etc. | ? |
| **Brand** | Association with brand | ? |

### D. Contract Structures

**Standard Terms:**

| Term | Standard | Research Needed |
|------|----------|-----------------|
| **Commission rate** | Defined % | ? |
| **Payment terms** | Net 30/60 | ? |
| **Cookie/Tracking** | 30-90 days | ? |
| **Termination** | 30 days notice | ? |
| **Exclusivity** | Usually non-exclusive | ? |

**Exclusivity Options:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Non-exclusive** | Standard, can work with others | ? |
| **Category exclusive** | Only in specific category | ? |
| **Geographic exclusive** | Only in specific region | ? |
| **Fully exclusive** | Cannot work with competitors | ? |

**Performance Clauses:**

| Clause | Trigger | Consequence | Research Needed |
|---------|---------|-------------|-----------------|
| **Minimum quota** | Below threshold | Rate reduction | ? |
| **Active requirement** | No activity in X months | Termination | ? |
| **Quality clause** | High cancellation rate | Review | ? |

---

## Data Model Sketch

```typescript
interface PartnerProgram {
  programId: string;
  name: string;
  type: PartnerProgramType;

  // Commission
  commissionModel: CommissionModel;
  baseCommissionRate: number;
  tieredRates?: CommissionTier[];

  // Benefits
  benefits: ProgramBenefit[];
  tierBenefits?: Map<PartnerTier, ProgramBenefit[]>;

  // Terms
  standardTerms: ProgramTerms;
  customizationAllowed: string[]; // What can be customized

  // Status
  active: boolean;
  createdAt: Date;
}

type PartnerProgramType =
  | 'affiliate'
  | 'channel'
  | 'strategic'
  | 'referral';

interface CommissionModel {
  type: CommissionType;
  structure: CommissionStructure;

  // Timing
  attributionWindow: number; // Days
  paymentTerms: number; // Days

  // Rules
  recurring?: boolean;
  recurringMonths?: number;
  cap?: number; // Max per period
}

type CommissionType =
  | 'percentage'
  | 'fixed'
  | 'hybrid';

type CommissionStructure =
  | 'flat'
  | 'tiered'
  | 'category_based'
  | 'lifetime';

interface CommissionTier {
  tier: PartnerTier;
  minVolume?: number;
  maxVolume?: number;
  commissionRate: number;
  bonuses?: TierBonus[];
}

type PartnerTier =
  | 'bronze'
  | 'silver'
  | 'gold'
  | 'platinum';

interface TierBonus {
  type: 'percentage' | 'fixed';
  trigger: string;
  value: number;
}

interface ProgramBenefit {
  benefitId: string;
  name: string;
  type: BenefitType;
  description: string;

  // Availability
  tiers?: PartnerTier[];
  requiresApproval?: boolean;

  // Value
  monetaryValue?: number;
}

type BenefitType =
  | 'commission'
  | 'bonus'
  | 'support'
  | 'training'
  | 'marketing'
  | 'tools'
  | 'exclusive';

interface ProgramTerms {
  // Commission
  commissionRate: number;
  paymentTerms: number; // Days
  attributionWindow: number; // Days

  // Contract
  terminationNotice: number; // Days
  autoRenewal: boolean;
  contractLength: number; // Months

  // Restrictions
  exclusivity?: ExclusivityType;
  allowedMarketingMethods: string[];
  prohibitedActions: string[];

  // Performance
  minimumQuota?: number;
  quotaPeriod?: 'monthly' | 'quarterly';
  inactivityPeriod?: number; // Months before termination
}

type ExclusivityType =
  | 'none'
  | 'category'
  | 'geographic'
  | 'full';
```

---

## Open Problems

### 1. Partner Proliferation
**Challenge:** Too many low-value partners

**Options:** Minimum requirements, tiered onboarding, periodic review

### 2. Commission Leakage
**Challenge:** Paying for low-quality referrals

**Options:** Quality filters, performance monitoring, clawbacks

### 3. Attribution Complexity
**Challenge:** Last-click vs. multi-touch

**Options:** Attribution models, split attribution, custom rules

### 4. Partner Fraud
**Challenge:** Fake bookings, self-referrals

**Options:** Detection, verification, penalties

### 5. Program Differentiation
**Challenge:** Standing out from competitors

**Options:** Better terms, unique benefits, strong support

---

## Next Steps

1. Define partner program structure
2. Design commission models
3. Create contract templates
4. Build program management UI

---

**Status:** Research Phase — Program patterns unknown

**Last Updated:** 2026-04-27
