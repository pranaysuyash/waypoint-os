# Refund & Cancellation Management — Policies & Rules

> Research document for cancellation policies, penalty structures, and refund rule engines.

---

## Key Questions

1. **What cancellation policies apply across different travel services?**
2. **How do we calculate cancellation penalties dynamically?**
3. **What's the policy hierarchy when multiple rules conflict?**
4. **How do we handle force majeure and airline-initiated cancellations?**
5. **What's the customer communication flow for cancellations?**

---

## Research Areas

### Policy Model

```typescript
interface CancellationPolicy {
  policyId: string;
  name: string;
  serviceType: ServiceType;
  rules: CancellationRule[];
  forceMajeureClause?: ForceMajeureClause;
}

type ServiceType =
  | 'flight_domestic'
  | 'flight_international'
  | 'hotel'
  | 'activity'
  | 'transfer'
  | 'insurance'
  | 'visa_service'
  | 'package'
  | 'mice_event'
  | 'cruise';

interface CancellationRule {
  ruleId: string;
  timeWindow: TimeWindow;
  penalty: PenaltyStructure;
  refundMethod: RefundMethod;
  conditions?: string[];
}

interface TimeWindow {
  description: string;
  fromDaysBefore: number;            // e.g., 30 days before travel
  toDaysBefore: number;              // e.g., 15 days before travel
  orLater?: boolean;                 // "this or later" vs "this window"
}

interface PenaltyStructure {
  type: 'percentage' | 'flat_fee' | 'per_night' | 'non_refundable';
  value: number;
  minimumPenalty?: number;
  maximumPenalty?: number;
  currency: string;
}

type RefundMethod =
  | 'original_payment'               // Refund to original payment method
  | 'credit_note'                    // Issue credit for future booking
  | 'agency_credit'                  // Credit with the agency
  | 'supplier_credit'                // Credit with the supplier (airline miles, etc.)
  | 'no_refund';                     // Non-refundable

// Standard cancellation policies by service type:
//
// Hotels:
//   72+ hours before check-in: Free cancellation (or 1 night penalty)
//   24-72 hours before: 1 night charge
//   <24 hours or no-show: Full stay charge
//   Peak season (Dec 20-Jan 5): Non-refundable or 50% at booking
//
// Domestic Flights (India):
//   >24 hours before departure: ₹2,500-3,500 cancellation fee per person
//   <24 hours: No refund (airline policy varies)
//   Indigo: ₹2,500-3,500 per segment
//   SpiceJet: ₹2,500 per passenger per segment
//   Air India: Varies by fare class
//
// International Flights:
//   Varies by airline and fare class
//   Economy: 50-100% penalty depending on timing
//   Business: 25-50% penalty (more flexible)
//   Non-refundable fares: No refund, taxes may be refundable
//
// Activities/Tours:
//   48+ hours: Full refund
//   24-48 hours: 50% refund
//   <24 hours: No refund
//
// Insurance:
//   Pre-departure: Full refund (free look period 15 days)
//   Post-departure: As per policy terms
//
// Visa services:
//   Before submission: Service fee refundable (government fee non-refundable)
//   After submission: No refund
```

### Penalty Calculation Engine

```typescript
interface CancellationQuote {
  quoteId: string;
  bookingId: string;
  cancelledAt: Date;
  travelStartDate: Date;
  daysBeforeTravel: number;
  items: CancellationItem[];
  totalRefund: Money;
  totalPenalty: Money;
  refundTimeline: string;
  refundMethod: RefundMethod;
}

interface CancellationItem {
  itemId: string;
  itemType: ServiceType;
  originalAmount: Money;
  penalty: Money;
  refundable: Money;
  penaltyReason: string;
  supplierRefundPolicy: string;
  agencyMarkupRefund: boolean;       // Does the agency markup get refunded?
}

// Penalty calculation flow:
// 1. Customer/agent initiates cancellation
// 2. System calculates days before travel
// 3. For each booked item:
//    a. Look up applicable cancellation rule
//    b. Calculate penalty based on time window
//    c. Check supplier's actual policy (may differ from standard)
//    d. Determine refundable amount
// 4. Sum all items → Total refund amount
// 5. Determine refund method (original payment vs. credit)
// 6. Present cancellation quote to agent/customer
// 7. On confirmation, process refund

// Special cases:
// Partial cancellation:
//   - Cancel 1 of 3 hotel nights → Recalculate remaining nights (may change rate)
//   - Cancel 1 of 4 travelers → Recalculate per-person rate (may be higher)
//   - Cancel activity but keep flights/hotel → Only activity refund
//
// Supplier-initiated cancellation:
//   - Airline cancels flight → Full refund (EU261/Indian DGCA rules)
//   - Hotel overbooked → Full refund + alternative accommodation
//   - Activity cancelled by operator → Full refund or reschedule
//
// Force majeure:
//   - Natural disaster, pandemic, government advisory
//   - Force majeure clause determines refund level
//   - Usually: Full refund minus non-recoverable costs
//   - Travel insurance may cover the difference
```

### Policy Hierarchy

```typescript
interface PolicyResolution {
  layers: PolicyLayer[];
  resolutionStrategy: 'strictest_wins' | 'most_generous' | 'customer_choice';
}

interface PolicyLayer {
  layer: number;
  source: string;
  policy: CancellationPolicy;
  precedence: number;
}

// Policy hierarchy (highest to lowest precedence):
// Layer 1: Contractual (supplier-specific contract terms)
//   - "Taj Hotels corporate contract: 48-hour free cancellation"
//   - Overrides standard Taj policy
//
// Layer 2: Supplier standard policy
//   - Airline's published cancellation policy
//   - Hotel's standard terms
//
// Layer 3: Agency policy
//   - Agency's own cancellation policy overlay
//   - "Our agency adds ₹500 processing fee on all cancellations"
//
// Layer 4: Platform default
//   - Default policy when no other policy applies
//   - Used for manual/offline bookings

// Conflict resolution:
// If supplier says "free cancellation" but agency says "₹500 fee":
// → Show both to agent, agent decides what to charge customer
// → Default: customer gets best deal (supplier policy wins)
```

---

## Open Problems

1. **Multi-segment partial cancellation** — A trip with flights + hotels + activities. Customer cancels 2 days before travel. Each component has different penalties. The total penalty calculation is complex and error-prone.

2. **Supplier vs. agency refund timing** — The airline refunds in 7 days, but the customer wants immediate refund. Agency bears the float risk. Need clear refund timeline management.

3. **Non-refundable vs. flexible pricing** — Customers want the cheaper non-refundable rate but then ask for flexibility. Need clear communication at booking time about what "non-refundable" means.

4. **Group booking cancellations** — If 3 of 10 people cancel, does the hotel rate change? Does the group discount disappear? Group cancellations have cascading effects.

5. **Cross-border refund complexity** — International booking paid in INR, refund needs to go back in INR but forex rate has changed. Who bears the difference?

---

## Next Steps

- [ ] Design cancellation policy rule engine with time-window penalties
- [ ] Build penalty calculation engine for multi-component trips
- [ ] Create policy hierarchy resolution system
- [ ] Design cancellation quote presentation for agents and customers
- [ ] Study cancellation UX (Booking.com, MakeMyTrip, Airbnb cancellation flows)
