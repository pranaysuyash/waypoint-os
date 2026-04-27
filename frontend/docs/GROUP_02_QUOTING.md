# Group Travel 02: Quoting

> Group quote generation and pricing

---

## Document Overview

**Focus:** Creating quotes for group travel
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Quote Process
- How do we generate group quotes?
- What information is needed?
- How long are quotes valid?
- What about revisions?

### Pricing
- How do group rates work?
- What are the typical discounts?
- How do we price different components?
- What about F&B minimums?

### Proposals
- What goes into a group proposal?
- How do we present options?
- What about comparison pricing?
- How do we handle negotiations?

### Contracts
- When does a quote become a contract?
- What are the key contract terms?
- What about deposits and cancellations?
- How do we handle signatures?

---

## Research Areas

### A. Quote Requirements

**Information Needed:**

| Requirement | Description | Research Needed |
|-------------|-------------|-----------------|
| **Group size** | Number of people | ? |
| **Dates** | Travel dates, flexibility | ? |
| **Destination** | Where they're going | ? |
| **Budget** | Per person or total | ? |
| **Accommodation** | Room types, categories | ? |
| **Activities** | What they want to do | ? |
| **Transport** | How they're getting there | ? |
| **F&B** | Meal requirements | ? |
| **Special needs** | Accessibility, dietary | ? |

### B. Group Pricing

**Typical Discounts:**

| Component | Typical Group Discount | Research Needed |
|-----------|----------------------|-----------------|
| **Hotels** | 10-20% | ? |
| **Airlines** | 5-10% | ? |
| **Activities** | 15-25% | ? |
| **Transport** | 10-15% | ? |

**Pricing Models:**

| Model | Description | Use | Research Needed |
|-------|-------------|-----|-----------------|
| **Per person** | Price per individual | Most common | ? |
| **Total group** | Lump sum | Less common | ? |
| **Tiered** | Price varies by room type | Upsell opportunity | ? |
| **Package** | All-inclusive | Simplicity | ? |

**Additional Costs:**

| Cost | Description | Research Needed |
|-------|-------------|-----------------|
| **Deposit** | Secures space | %? |
| **Change fees** | Modifications | ? |
| **Cancellation fees** | Tiered by timing | ? |
| **F&B minimum** | Required spend | Common? |

### C. Quote Presentation

**Proposal Elements:**

| Element | Description | Research Needed |
|---------|-------------|-----------------|
| **Trip overview** | Summary | ? |
| **Day-by-day itinerary** | Schedule | ? |
| **Accommodation details** | Hotels, room types | ? |
| **Activity descriptions** | What's included | ? |
| **Pricing breakdown** | Costs per person | ? |
| **Inclusions/exclusions** | What's included | ? |
| **Terms & conditions** | Contract terms | ? |
| **Payment schedule** | When to pay | ? |

### D. Contract Terms

**Key Contract Elements:**

| Element | Description | Research Needed |
|---------|-------------|-----------------|
| **Room block** | Number of rooms held | ? |
| **Rates** | Agreed pricing | ? |
| **Deposit** | Amount and timing | ? |
| **Final payment** | Timing | ? |
| **Cancellation** | Policy and penalties | ? |
| **Attrition** | Allowed reduction | %? |
| **Cut-off date** | Last date for changes | ? |
| **F&B minimum** | Required spend | If applicable |

---

## Quote Process

```
1. Receive inquiry
   → Collect requirements
   → Ask clarifying questions

2. Prepare quote
   → Search options
   → Calculate pricing
   → Create proposal

3. Present quote
   → Send proposal
   → Explain options
   → Answer questions

4. Negotiate (if needed)
   → Adjust pricing
   → Modify inclusions
   → Finalize terms

5. Convert to contract
   → Send contract
   → Collect deposit
   → Confirm booking
```

---

## Data Model Sketch

```typescript
interface GroupQuote {
  id: string;
  groupId: string;

  // Quote details
  validUntil: Date;
  status: QuoteStatus;
  revision: number;

  // Pricing
  totalCost: Money;
  perPersonCost: Money;
  pricingBreakdown: QuotePricingBreakdown;

  // Inclusions
  inclusions: string[];
  exclusions: string[];

  // Terms
  terms: QuoteTerms;
}

type QuoteStatus =
  | 'draft'
  | 'sent'
  | 'revised'
  | 'accepted'
  | 'rejected'
  | 'expired';

interface QuoteTerms {
  deposit: {
    amount: Money;
    percentage: number;
    dueBy: Date;
  };
  finalPayment: {
    amount: Money;
    dueBy: Date;
  };
  cancellation: CancellationPolicy;
  changes: ChangePolicy;
}
```

---

## Open Problems

### 1. Quote Validity
**Challenge:** Prices change, quotes expire

**Options:** Short validity (7-14 days), price disclaimers

### 2. Accurate Pricing
**Challenge:** Group pricing isn't always public

**Options:** Supplier relationships, estimated pricing

### 3. Scope Creep
**Challenge:** Requirements keep changing

**Options:** Clear scope, revision limits, change fees

### 4. Comparison Shopping
**Challenge:** Groups compare quotes

**Options:** Value proposition, bundle pricing

---

## Next Steps

1. Design quote builder
2. Create proposal templates
3. Build pricing engine
4. Implement contract system

---

**Status:** Research Phase — Quoting patterns unknown

**Last Updated:** 2026-04-27
