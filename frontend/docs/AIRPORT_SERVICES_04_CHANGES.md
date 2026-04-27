# Airport Services 04: Changes & Support

> Modifications, cancellations, and customer support

---

## Document Overview

**Focus:** Managing airport service bookings after confirmation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Modifications
- What changes can be made? (Date? Time? Passenger count?)
- How do we handle flight changes?
- What are the modification fees?
- How do we process changes?

### 2. Cancellations
- What are the cancellation policies?
- How far in advance can cancellations be made?
| What are the refund policies?
| How do we handle same-day cancellations?

### 3. Support Issues
- What if customer can't access the service?
- What if service is not as described?
| What about quality complaints?
| How do we handle disputes?

### 4. Flight Disruptions
- How do flight delays/cancellations affect bookings?
- What happens if terminal changes?
| What if customer misses flight?
| How do we handle rebooking?

---

## Research Areas

### A. Modification Rules

**Allowed Changes:**

| Change | Allowed? | Timing | Fee |
|--------|----------|--------|-----|
| **Date change** | Sometimes | > 24-48 hours | Price difference |
| **Time change** | Usually | Any time | Usually none |
| **Add passengers** | If capacity | Up to flight time | Pro-rated |
| **Remove passengers** | Sometimes | > 24 hours | Partial refund |
| **Flight change** | Sometimes | If same airport | Fee |

**Research:**
- What are the exact rules by provider?
| How do we handle flight changes?
| What are the modification fees?

### B. Cancellation Policies

**Policy Types:**

| Policy Type | Notice Required | Refund | Common For |
|-------------|-----------------|--------|------------|
| **Flexible** | 24+ hours | 100% | Lounges |
| **Moderate** | 48-72 hours | 50-100% | Meet & greet |
| **Strict** | 7+ days | 0-50% | Specialized services |
| **Non-refundable** | None | 0% | Discounted rates |

**Research:**
- What are the standard policies?
| Can we negotiate better terms?
| How do we display policies clearly?

### C. Flight Impact Handling

**Flight Change Scenarios:**

| Scenario | Impact on Booking | Resolution |
|----------|-------------------|------------|
| **Same airport, different terminal** | May affect service location | Rebook or refund |
| **Different airport** | Service not usable | Full refund |
| **Time change < 2 hours** | Usually no impact | No action |
| **Time change > 2 hours** | May miss service | Rebook or refund |
| **Flight cancelled** | Service not usable | Full refund |

**Research:**
- How do we detect flight changes?
- How do we automatically rebook?
| What is our refund policy?

### D. Common Support Issues

| Issue | Frequency | Resolution | Escalation |
|-------|-----------|------------|------------|
| **Can't find lounge** | High | Directions | Staff assistance |
| **QR code doesn't work** | Medium | Manual verification | Provider |
| **Lounge full** | Low | Wait list | Provider |
| **Service not as described** | Low | Complaint | Provider |
| **Wrong terminal** | Medium | Rebook | Provider or us |

**Research:**
- What are the actual issue frequencies?
| Which can we resolve vs. provider?
| How do we measure resolution time?

---

## Modification Data Model

```typescript
interface AirportServiceModification {
  id: string;
  bookingId: string;
  type: ModificationType;
  status: ModificationStatus;

  // Requested changes
  changes: ServiceChange[];

  // Original booking
  originalBooking: AirportServiceBooking;

  // New details
  newBooking?: AirportServiceBooking;

  // Financial
  priceAdjustment: Money;
  additionalPayment?: Money;
  refundAmount?: Money;

  // Processing
  requestedAt: Date;
  processedAt?: Date;
  confirmedAt?: Date;
}

type ModificationType =
  | 'date_change'
  | 'time_change'
  | 'flight_change'
  | 'passenger_add'
  | 'passenger_remove';

interface ServiceChange {
  type: string;
  from: any;
  to: any;
}
```

---

## Cancellation State Machine

```
CONFIRMED → CANCELLATION_REQUESTED → PROCESSING → REFUND_PROCESSING → REFUNDED
                                        ↓
                                      CANCELLED
```

---

## Support Playbook

**Tier 1: Self-Service**

| Issue | Resource |
|-------|----------|
| Finding location | Map, directions in confirmation |
| Access problems | FAQ, troubleshooting guide |
| Modification | Self-service portal |

**Tier 2: Our Support**

| Issue | Action |
|-------|--------|
| Simple changes | Process modification |
| Refund requests | Process within policy |
| Directions | Provide guidance |

**Tier 3: Provider Escalation**

| Issue | Action |
|-------|--------|
| Access denied | Provider verification |
| Quality issues | Provider complaint |
| Complex changes | Provider rebooking |

---

## Open Problems

### 1. Last-Minute Cancellations
**Challenge:** Customer cancels 1 hour before flight

**Questions:**
- Is any refund possible?
| How do we enforce policies?
| What if there's a "good reason"?

### 2. Service Quality Disputes
**Challenge:** Customer says lounge was "awful"

**Options:**
- Partial refund
| Credit for future
| Dismiss complaint

**Research:** How do we assess quality?

### 3. No-Show
**Challenge:** Customer booked but didn't use service

**Questions:**
- Is this trackable?
| Can we verify no-show?
| Should we refund?

### 4. Multiple Bookings
**Challenge:** Customer books same service twice (mistake)

**Options:**
- Detect and warn
| Auto-refund duplicate
| Strict policy

---

## Competitor Research Needed

| Competitor | Cancellation Policy | Notable Patterns |
|------------|---------------------|------------------|
| **Priority Pass** | ? | ? |
| **Airlines** | ? | ? |
| **Airport directly** | ? | ? |

---

## Experiments to Run

1. **Modification ease test:** How smooth are changes?
2. **Cancellation rate study:** What % of bookings are cancelled?
3. **Refund timing study:** How long do refunds take?
4. **Dispute analysis:** What are common complaints?

---

## References

- [Activities - Operations](./ACTIVITIES_04_OPERATIONS.md) — Similar patterns
| [Ground Transportation - Disruptions](./GROUND_TRANSPORTATION_04_DISRUPTIONS.md) — Disruption patterns

---

## Next Steps

1. Define modification policies
2. Build modification system
3. Implement cancellation flow
4. Create support documentation
5. Measure support metrics

---

**Status:** Research Phase — Support patterns unknown

**Last Updated:** 2026-04-27
