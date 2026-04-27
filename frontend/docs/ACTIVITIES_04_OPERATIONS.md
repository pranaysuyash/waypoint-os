# Activities & Experiences 04: Operations & Cancellations

> Handling changes, cancellations, refunds, and post-booking support

---

## Document Overview

**Focus:** Managing activity bookings after confirmation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Cancellations
- What are the cancellation policies?
- How do we handle customer-initiated cancellations?
- What about operator cancellations?
- How are refunds processed?
- What is the refund timeline?

### 2. Modifications
- What changes can be made? (Date? Time? Participants?)
- How do we handle date changes?
- What about adding/removing participants?
- How does pricing change affect the booking?

### 3. No-Shows
- What constitutes a no-show?
- Is the booking chargeable?
- How do we verify attendance?
- What about partial no-shows? (3 booked, 2 show up)

### 4. Post-Activity
- How do we collect reviews?
- What about complaints?
- How do we handle media sharing?
- What about repeat booking incentives?

---

## Research Areas

### A. Cancellation Policies

**Policy Types:**

| Policy Type | Notice Required | Refund | Common For |
|-------------|-----------------|--------|------------|
| **Flexible** | 24+ hours | 100% | Attraction tickets |
| **Moderate** | 48-72 hours | 50-100% | Small group tours |
| **Strict** | 7+ days | 0-50% | Multi-day trips |
| **Non-refundable** | None | 0% | Discounted rates |

**Research:**
- What are the standard policies by activity type?
- Can we negotiate better terms?
- How do we display policies clearly?

### B. Modification Rules

| Change | Allowed? | Timing Restrictions | Price Impact |
|--------|----------|---------------------|--------------|
| **Date change** | Sometimes | > 24-72 hours | Price difference |
| **Time change** | Often | Up to 24 hours | Usually none |
| **Add participants** | If capacity | Up to start time | Pro-rated |
| **Remove participants** | Sometimes | > 24-48 hours | Partial refund |
| **Name change** | Usually | Any time | Usually none |

**Research:**
- Which operators allow modifications?
- What fees do they charge?
- How do we handle modification requests?

### C. Refund Processing

**Refund Timelines:**

| Scenario | Refund Time | Method |
|----------|-------------|--------|
| **Customer cancellation** | 5-15 business days | Original payment method |
| **Operator cancellation** | 3-10 business days | Original payment method |
| **Weather cancellation** | 5-15 business days | Original payment method |
| **Credit note** | Immediate | Account credit |

**Research:**
- What are the actual refund times?
- Who initiates the refund? (Us or operator)
- What about currency conversion losses?

### D. No-Show Handling

**No-Show Triggers:**

| Trigger | Action | Refund |
|---------|--------|--------|
| **Customer doesn't arrive** | Mark as no-show | None (usually) |
| **Late arrival** | At operator discretion | Maybe partial |
| **Operator no-show** | Full refund + compensation | 100% |

**Research:**
- How do we verify attendance?
- What evidence is required for disputes?
- How do we handle "operator didn't show" claims?

---

## Cancellation State Machine

```
CONFIRMED → CANCELLATION_REQUESTED → CANCELLING → REFUND_PROCESSING → REFUNDED
                                        ↓
                                      CANCELLED
```

**States Explained:**

| State | Meaning | Next Actions |
|-------|---------|--------------|
| CANCELLATION_REQUESTED | Customer requested cancellation | Check policy |
| CANCELLING | Processing cancellation with operator | Await confirmation |
| REFUND_PROCESSING | Operator confirmed, initiating refund | Process refund |
| REFUNDED | Refund complete | Notify customer |
| CANCELLED | Cancellation complete | (final state) |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface ActivityCancellation {
  id: string;
  bookingId: string;
  status: CancellationStatus;

  // Request
  requestedBy: 'customer' | 'agent' | 'operator';
  requestedAt: Date;
  reason: string;

  // Policy
  policy: CancellationPolicy;
  eligibleRefund: Money;
  actualRefund?: Money;

  // Processing
  processedAt?: Date;
  refundMethod?: string;
  refundTransactionId?: string;
  refundCompletedAt?: Date;
}

interface ActivityModification {
  id: string;
  bookingId: string;
  status: ModificationStatus;

  // Changes
  changes: ModificationChange[];

  // Financial
  priceAdjustment: Money;
  additionalPayment?: Money;
  refundAmount?: Money;

  // Processing
  requestedAt: Date;
  processedAt?: Date;
  confirmedAt?: Date;
}

type ModificationChange =
  | { type: 'date_change', from: Date, to: Date }
  | { type: 'time_change', from: Time, to: Time }
  | { type: 'participant_add', count: number }
  | { type: 'participant_remove', count: number }
  | { type: 'name_change', participantId: string, from: string, to: string };
```

---

## Communication Templates

### Cancellation Confirmation

| Field | Content |
|-------|---------|
| Subject | "Booking #[ref] - [activity] cancelled" |
| Body | Confirmation of cancellation, refund amount, expected timeline |

### Modification Confirmation

| Field | Content |
|-------|---------|
| Subject | "Booking #[ref] - Changes confirmed" |
| Body | Summary of changes, new details, price adjustment |

### Refund Confirmation

| Field | Content |
|-------|---------|
| Subject | "Refund processed for booking #[ref]" |
| Body | Refund amount, payment method, expected timeline |

---

## Operator Cancellations

**Scenarios:**

| Scenario | Customer Impact | Resolution |
|----------|-----------------|------------|
| **Underbooked** | Activity cancelled | Full refund + alternative |
| **Weather** | Activity cancelled | Full refund or reschedule |
| **Operator issue** | Activity cancelled | Full refund + compensation? |
| **Force majeure** | Activity cancelled | Credit note? |

**Research:**
- What is our liability when operator cancels?
- How do we find alternatives?
- What compensation do we offer?

---

## Open Problems

### 1. Last-Minute Cancellations
**Challenge:** Customer cancels 1 hour before activity

**Questions:**
- Do they get any refund?
- How do we enforce policies?
- What if they have a "good reason"? (Illness, emergency)

### 2. Dispute Resolution
**Challenge:** Customer says activity was "not as described"

**Questions:**
- How do we investigate?
- What evidence do we accept?
- What compensation is appropriate?

### 3. Partial Attendance
**Challenge:** 4 booked, only 2 show up

**Questions:**
- Is the booking still chargeable in full?
- Can they get partial refund?
- How do we verify?

### 4. Weather Cancellations
**Challenge:** Who decides if weather is "bad enough"?

**Questions:**
- Is it operator decision?
- What about rain forecasts?
- How do we handle disagreements?

---

## Review & Feedback

**Collection:**

| Timing | Method |
|--------|--------|
| **Immediately after** | App prompt |
| **24 hours later** | Email |
| **For completed trips** | Trip summary |

**Research:**
- When is the best time to request reviews?
- How do we incentivize reviews?
- What about photo sharing?

---

## Competitor Research Needed

| Competitor | Cancellation Policy | Notable Patterns |
|------------|---------------------|------------------|
| **Viator** | ? | ? |
| **GetYourGuide** | ? | ? |
| **Klook** | ? | ? |
| **Airbnb Experiences** | ? | ? |

---

## Experiments to Run

1. **Cancellation policy audit:** Map policies by activity type
2. **Refund timeline study:** How long do refunds actually take?
3. **Dispute analysis:** What are common dispute reasons?
4. **No-show rate analysis:** What are actual no-show rates?

---

## References

- [Ground Transportation - Disruptions](./GROUND_TRANSPORTATION_04_DISRUPTIONS.md) — Similar patterns
- [Booking Engine - Cancellations](./BOOKING_ENGINE_06_CANCELLATIONS.md) — Cancellation patterns
- [Trip Builder - Modifications](./TRIP_BUILDER_06_MODIFICATIONS.md) — Modification patterns

---

## Next Steps

1. Map cancellation policies by provider
2. Design cancellation/modification UX
3. Build refund processing system
4. Create communication templates
5. Implement review collection

---

**Status:** Research Phase — Operations patterns unknown

**Last Updated:** 2026-04-27
