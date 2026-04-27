# Trip Builder 06: Modifications

> Post-booking changes, cancellations, rebooking, and refund processing

---

## Document Overview

**Focus:** Handling changes to booked trips
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Change Types
- What changes are allowed? (Dates? Names? Components?)
- What changes are prohibited? (Destination? Carrier?)
- How do we handle name changes? (Legal? Security?)
- Can components be removed? Added? Swapped?

### 2. Cancellation Rules
- What are the cancellation policies per component type?
- How are penalties calculated?
- What is non-refundable vs. refundable?
- How do partial cancellations work? (One traveler cancels)

### 3. Rebooking Flow
- How do we find alternatives for modified trips?
- What happens to pricing? (Current rates vs. original?)
- How are fare differences handled?
- Can changes be made mid-trip?

### 4. Refund Processing
- How long do refunds take? (Per supplier?)
- What is the refund flow? (Automatic? Manual?)
- How do we handle partial refunds?
- What about taxes and fees?

---

## Research Areas

### A. Modification Categories

**Change Types to Research:**

| Category | Examples | Complexity |
|----------|----------|------------|
| **Date shift** | Move trip earlier/later | Medium (recheck availability) |
| **Pax change** | Add/remove travelers | High (reprice everything) |
| **Component swap** | Different hotel/flight | Medium (new booking + cancel) |
| **Name correction** | Fix typo vs. legal change | Low (API) to High (document) |
| **Destination change** | Different city/country | High (essentially new trip) |
| **Mid-trip change** | Extend stay, change return | High (partial usage) |

**Open Questions:**
- Which changes do agents commonly request?
- What are the deal-breakers for each change type?
- Which changes require full rebooking vs. modification?

### B. Cancellation Policy Complexity

**Factors That Affect Cancellations:**

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Time until departure** | Closer = more penalty | What are the tiers? |
| **Fare type** | Refundable vs. non-refundable | How do we detect? |
| **Supplier policy** | Airline vs. hotel vs. car | How do we retrieve? |
| **Agency markup** | Is our fee refundable? | What's our policy? |
| **Payment method** | Card vs. wallet vs. UPI | Refund path differs? |

**Research Needed:**
- How do we retrieve supplier cancellation policies?
- Can policies be embedded in booking response?
- What are the non-refundable scenarios?

### C. Rebooking Strategies

**Approaches to Explore:**

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **Modify existing** | Change dates on same booking | Same supplier, flexible fare |
| **Cancel + rebook** | Cancel old, book new | Different supplier/route |
| **Exchange** | Airline-specific exchange process | Flight-only, certain carriers |
| **Partial rebook** | Keep some components, redo others | One component unavailable |

**Questions:**
- Which is cheaper for the customer? (Fees vs. new pricing)
- Which is faster for the agent?
- How do we present options clearly?

### D. Refund Orchestration

**Refund States:**
```
REQUESTED → PROCESSING → COMPLETED
             ↓
           FAILED → MANUAL_REVIEW
```

**Questions:**
- How do we track refund status from suppliers?
- What happens when supplier refund fails?
- How long before we escalate to manual?
- Can we provide estimated refund dates?

---

## Integration Points

| System | Integration Question |
|--------|---------------------|
| **Booking Engine** | Reuse cancellation state machine? |
| **Payment Processing** | Refund initiation and tracking? |
| **Supplier Integration** | Modification APIs? |
| **Timeline** | Which modification events are logged? |
| **Communication Hub** | Cancellation notifications? |

---

## Failure Scenarios to Explore

### 1. Modification Failure
**Scenario:** Change requested, but new option not available

**Options:**
- Offer alternatives
- Keep original booking
- Cancel entire trip

**Research:** What do agents expect in this case?

### 2. Refund Delays
**Scenario:** Supplier acknowledges cancellation, but refund takes weeks

**Options:**
- Show estimated refund date
- Agency absorbs refund (credit customer)
- Wait for supplier

**Research:** What are typical refund timelines per supplier?

### 3. Partial Trip Usage
**Scenario:** Customer cancels mid-trip (e.g., hotel portion unused)

**Questions:**
- Are unused nights refundable?
- What about return flight if not taken?
- How do we prove no-show vs. cancellation?

### 4. Fare Difference Calculation
**Scenario:** Rebook at current rates, which may be higher/lower

**Options:**
- Customer pays difference
- Agency absorbs difference (policy?)
- Show options at different price points

**Research:** How do we present trade-offs clearly?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface TripModification {
  tripId: string;
  type: ModificationType;
  status: ModificationStatus;
  requestedBy: string;
  requestedAt: Date;
  changes: ComponentChange[];
  financialImpact: FinancialImpact;
  approvals?: ModificationApproval[];
}

type ModificationType =
  | 'cancellation'
  | 'date_change'
  | 'pax_change'
  | 'component_swap'
  | 'name_correction'
  | 'destination_change';

interface ComponentChange {
  componentBookingId: string;
  action: 'cancel' | 'modify' | 'replace';
  original: ComponentSnapshot;
  modified?: ComponentSnapshot;
  replacement?: ComponentSnapshot;
  fees: ModificationFee[];
}

interface ModificationFee {
  type: 'cancellation_penalty' | 'change_fee' | 'fare_difference' | 'service_fee';
  amount: Money;
  waiveable: boolean;
  paidBy: 'customer' | 'agency';
}

interface FinancialImpact {
  refundAmount: Money;
  additionalCharge: Money;
  netImpact: Money;
  refundMethod: string;
  estimatedRefundDate?: Date;
}
```

---

## Cancellation Policy Retrieval

**Open Questions:**
- Do suppliers provide policy via API?
- Is policy in booking confirmation?
- Do we need to scrape or store manually?
- How often do policies change?

**Research Needed:**
- Audit current supplier integrations for policy availability
- Build a policy catalog for common suppliers
- Design policy display for agents/customers

---

## Refund Tracking

**States to Track:**
- `REFUND_PENDING` — Cancellation processed, refund initiated
- `REFUND_PROCESSING` — Supplier working on refund
- `REFUND_COMPLETED` — Funds returned to customer
- `REFUND_FAILED` — Refund failed, needs attention
- `REFUND_PARTIAL` — Some components refunded, some not

**Questions:**
- How do we match refund transactions to bookings?
- What if refund amount differs from expected?
- Can we track refunds per payment method?

---

## Open Problems

### 1. Cross-Supplier Modifications
**Scenario:** Trip has flights from Airline A and hotel from Hotel B. Customer wants to change dates.

**Complications:**
- Both suppliers must have availability
- One may charge more penalty than the other
- Cancellation windows may differ

**Research:**
- How do we coordinate multi-supplier changes?
- What if only one supplier can accommodate?

### 2. Non-Refundable Components
**Scenario:** Trip has mix of refundable and non-refundable components.

**Questions:**
- Can we modify just the refundable parts?
- How do we clearly show which is which?
- What is the UX for partial cancellation?

### 3. Group Booking Modifications
**Scenario:** Booking for 10 people, 1 person cancels.

**Complexities:**
- Does cancellation break group pricing?
- Are cancellation fees per-person or for the group?
- Does the remaining group get re-priced?

---

## Competitor Research Needed

| Product | Modification Flow | Notable Patterns |
|---------|-------------------|------------------|
| **Expedia** | ? | ? |
| **Airbnb** | ? | ? |
| **Southwest** | ? | ? |
| **TravelPerk** | ? | ? |

---

## Experiments to Run

1. **Modification frequency analysis:** What changes do agents request most?
2. **Policy retrieval test:** Can we get policies from current suppliers?
3. **Refund timeline study:** How long do refunds actually take?
4. **Agent workflow observation:** How do agents handle complex modifications?

---

## References

- [Booking Engine - Cancellations](./BOOKING_ENGINE_06_CANCELLATIONS.md) — Cancellation patterns
- [Booking Engine - Modifications](./BOOKING_ENGINE_05_MODIFICATIONS.md) — Modification patterns
- [Payment Processing - Reconciliation](./PAYMENT_PROCESSING_04_RECONCILIATION_DEEP_DIVE.md) — Refund tracking

---

## Next Steps

1. Interview agents about modification scenarios
2. Audit current supplier capabilities for changes
3. Build cancellation policy catalog
4. Prototype modification quote flow
5. Design refund tracking UX

---

**Status:** Research Phase — Questions identified, exploration needed

**Last Updated:** 2026-04-27
