# Trip Builder 05: Booking Management

> Orchestrating bookings across multiple suppliers, status tracking, and confirmation handling

---

## Document Overview

**Focus:** Converting planned trips into actual bookings
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Booking Orchestration
- How do we coordinate multiple simultaneous bookings?
- What happens when one booking fails? (Rollback? Continue?)
- What is the order of operations? (Flights first? Hotels?)
- How do we handle supplier rate limits during bulk booking?

### 2. Status Tracking
- What are all the possible booking states?
- How do we track supplier-side status changes?
- What triggers status updates? (Webhooks? Polling?)
- How do we handle "orphaned" bookings (supplier timeout)?

### 3. Payment Flow
- When is payment captured? (Per-component? All-at-once?)
- What happens on payment failure mid-booking?
- How do we handle partial payments?
- What is the refund window?

### 4. Confirmation & Documents
- How are confirmations retrieved from suppliers?
- What documents are generated? (Itinerary? Vouchers? Invoices?)
- When are documents sent to customers?
- How do we handle missing supplier confirmations?

---

## Research Areas

### A. Booking State Machine

**Proposed States:**
```
PENDING → REQUESTED → CONFIRMED → TICKETED
           ↓           ↓
        FAILED    CANCELLED
           ↓
     RETRY_EXHAUSTED
```

**Open Questions:**
- Is `TICKETED` distinct from `CONFIRMED` for all components?
- What intermediate states exist? (e.g., `PAYMENT_PENDING`, `SUPHOLDER_PENDING`)
- Can a booking be `PARTIALLY_CONFIRMED`?
- How do we represent "held but not confirmed"?

### B. Orchestration Patterns

**Sagas to Research:**

| Pattern | Description | Pros | Cons |
|---------|-------------|------|------|
| **Sequential** | Book one, wait, book next | Simple rollback | Slow, availability loss |
| **Parallel** | Book all simultaneously | Fast | Complex rollback |
| **Dependency-based** | Book flights first, then hotels | Balanced | Complex orchestration |
| **Hold-first** | Hold all, then confirm | Safer | Holds may expire |

**Research Needed:**
- What hold durations do suppliers offer?
- What are the failure rates per component type?
- Can we recover from partial failures?

### C. Supplier Response Handling

**Response Types to Handle:**
- Immediate confirmation
- Async confirmation (webhook callback)
- Pending (manual processing required)
- Soft failure (retry possible)
- Hard failure (not retryable)

**Open Questions:**
- How do we detect timeout vs. slow response?
- What retry backoff strategy?
- When do we escalate to manual review?

### D. Payment Timing

**Approaches to Explore:**

| Timing | Description | Risk |
|--------|-------------|------|
| Pre-auth all | Authorize before any booking | Authorization expires |
| Pay per component | Charge as each confirms | Partial trip problem |
- Pay all at end | Charge after all confirm | Supplier payment terms |
- Deposit then balance | Split payment | Refund complexity |

**Research:**
- What payment terms do suppliers require?
- What are authorization hold periods?
- How do we handle payment failures post-confirmation?

---

## Integration Points

| System | Integration Question |
|--------|---------------------|
| **Booking Engine** | Reuse core booking state machine? |
| **Payment Processing** | Multi-component payment flow? |
| **Supplier Integration** | Status update mechanisms? |
| **Timeline** | Which booking events are logged? |
| **Communication Hub** | Confirmation delivery? |
| **Customer Portal** | Booking status visibility? |

---

## Failure Scenarios to Explore

### 1. Partial Failure
**Scenario:** Flight confirmed, hotel failed

**Options:**
- Rollback flight (lose rate)
- Keep flight, retry hotel (different hotel?)
- Mark trip as partial, prompt agent

**Research:** Which option do agents prefer?

### 2. Price Change During Booking
**Scenario:** Quoted $X, supplier returns $X+Y

**Options:**
- Auto-abort if exceeds threshold
- Prompt for approval
- Auto-proceed within tolerance

**Research:** What tolerance is acceptable?

### 3. Supplier Timeout
**Scenario:** Request sent, no response

**Options:**
- Retry with backoff
- Mark as failed, proceed with others
- Escalate to manual

**Research:** How to detect eventual success vs. failure?

### 4. Post-Booking Cancellation
**Scenario:** Confirmed, then supplier cancels

**Options:**
- Auto-rebook similar
- Hold funds, rebook manually
- Full refund

**Research:** What are supplier cancellation policies?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface TripBooking {
  tripId: string;
  status: BookingStatus;
  components: ComponentBooking[];
  payment: BookingPayment;
  timeline: BookingEvent[];
  documents: BookingDocument[];
}

interface ComponentBooking {
  id: string;
  componentId: string;  // from trip plan
  supplier: string;
  status: ComponentBookingStatus;
  confirmationCode?: string;
  supplierReference?: string;
  bookedAt?: Date;
  ticketedAt?: Date;
  pricing: {
    quoted: Money;
    confirmed?: Money;
    final?: Money;
  };
}

enum BookingStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  PARTIALLY_CONFIRMED = 'partially_confirmed',
  CONFIRMED = 'confirmed',
  TICKETED = 'ticketed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

enum ComponentBookingStatus {
  PENDING = 'pending',
  REQUESTED = 'requested',
  HOLD_PLACED = 'hold_placed',
  CONFIRMED = 'confirmed',
  TICKETED = 'ticketed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  RETRYING = 'retrying'
}
```

---

## Orchestration Pseudocode

```
for each booking_strategy:
  1. Validate all components still available
  2. Calculate total price
  3. Obtain payment authorization
  4. Execute bookings (per strategy)
  5. Confirm success or handle failures
  6. Capture payment
  7. Generate documents
  8. Send confirmations
```

**Research Needed:**
- Step 4: What is the optimal order?
- Step 5: What are the compensating transactions?
- Step 6: When exactly do we capture?

---

## Monitoring & Observability

**Metrics to Track:**
- Booking success rate (per supplier, per component)
- Average booking duration
- Failure reasons (categorized)
- Retry frequency and success
- Price change frequency
- Payment failure rate
- Orphan booking rate

**Alerts to Define:**
- Booking success rate below threshold
- Supplier response time degradation
- Payment failure spike
- Unusual cancellation rate

---

## Open Problems

### 1. Idempotency
Suppliers may deliver duplicate confirmations or callbacks.

**Research:**
- Do suppliers provide idempotency keys?
- How do we detect duplicate confirmations?
- Can duplicate bookings be prevented?

### 2. Cross-Supplier Transactions
When flights and hotels are from different suppliers:

**Questions:**
- How do we maintain transactional integrity?
- What if one succeeds but the other's callback is lost?
- Can we hold flight while hotel books?

### 3. Confirmation Delivery
**Scenario:** Booking confirmed, but confirmation email never arrives.

**Research:**
- How do we detect non-delivery?
- What is the retry mechanism?
- Can customers self-serve resend?

---

## Competitor Research Needed

| Product | Booking Flow | Notable Patterns |
|---------|--------------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **TravelPerk** | ? | ? |
| **Concur** | ? | ? |

---

## Experiments to Run

1. **Failure frequency analysis:** Measure actual booking failure rates
2. **Supplier timeout study:** How long do suppliers typically take?
3. **Payment timing test:** What authorization hold periods work?
4. **Agent workflow observation:** How do agents handle failed bookings?

---

## References

- [Booking Engine - Architecture](./BOOKING_ENGINE_01_ARCHITECTURE.md) — Core booking patterns
- [Booking Engine - State Machine](./BOOKING_ENGINE_08_STATE_MACHINE.md) — State patterns
- [Payment Processing](./PAYMENT_PROCESSING_01_TECHNICAL_DEEP_DIVE.md) — Payment flows
- [Supplier Integration](./SUPPLIER_INTEGRATION_01_TECHNICAL_DEEP_DIVE.md) — Supplier patterns

---

## Next Steps

1. Interview agents about booking failure handling
2. Measure current booking success metrics
3. Research supplier booking APIs and patterns
4. Prototype orchestration engine
5. Design failure recovery UX

---

**Status:** Research Phase — Questions identified, exploration needed

**Last Updated:** 2026-04-27
