# Rail Integration 04: Operations & Support

> Refunds, cancellations, and rail disruptions

---

## Document Overview

**Focus:** Managing rail bookings after confirmation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Cancellations
- What are the cancellation policies?
- How do refunds work?
- What about waitlist cancellations?
- What about Tatkal cancellations?

### 2. Modifications
- Can customers change their booking?
- What changes are allowed?
- How do change fees work?
- What about rescheduling?

### 3. Disruptions
- What happens if trains are delayed/cancelled?
- How do we handle missed connections?
- What compensation is available?
- How do we communicate disruptions?

### 4. PNR Management
- How do customers check PNR status?
- What about chart preparation?
- How do waitlists move?
- What about seat upgrades?

---

## Research Areas

### A. Cancellation Policies

**Standard Cancellation Rules (Indian Railways):**

| Time Before Departure | Refund | Clerkage | Research Needed |
|-----------------------|--------|----------|-----------------|
| **More than 48 hours** | Full refund | Minimal | Flat fee? |
| **24-48 hours** | Partial refund | Higher | % deducted? |
| **Less than 24 hours** | No refund | Full fare | Except cases? |
| **After chart preparation** | No refund | N/A | Chart at 4 hrs? |
| **For Tatkal** | No refund | N/A | Confirmed only? |

**Waitlist Cancellations:**

| Scenario | Refund | Timing | Research Needed |
|----------|--------|--------|-----------------|
| **WL cancelled before chart** | Full refund | Immediate | ? |
| **WL not confirmed** | Auto-refund | After chart | ? |
| **WL partially confirmed** | Pro-rated refund | After chart | ? |

**International Cancellations:**

| Policy Type | Notice | Refund | Research Needed |
|-------------|--------|--------|-----------------|
| **Flexible** | Until departure | Full fee | ? |
| **Standard** | 24-48 hours | Partial | ? |
| **Advance** | Before cheaper price ends | Fee only | ? |
| **Non-refundable** | None | None | ? |

**Rail Pass Cancellations:**

| Pass Type | Refund Policy | Research Needed |
|-----------|---------------|-----------------|
| **Eurail** | Varies by type | ? |
| **JR Pass** | Before exchange | % fee? |
| **BritRail** | Before first use | ? |

**Refund Processing:**

| Type | Timeline | Method | Research Needed |
|------|----------|--------|-----------------|
| **E-ticket** | 3-7 days | Original payment | ? |
| **Counter ticket** | At counter only | Cash/card | ? |
| **Rail pass** | 2-4 weeks | Check | ? |

### B. Modifications

**Allowed Changes:**

| Change Type | Allowed? | Timing | Fee | Research Needed |
|-------------|----------|--------|-----|-----------------|
| **Reschedule** | Yes (with conditions) | Before chart | Flat fee | ? |
| **Class upgrade** | Yes | Before chart | Difference + fee | ? |
| **Boarding station change** | Sometimes | Before chart | Fee | ? |
| **Passenger name change** | No | Never | N/A | Strict policy |

**Rescheduling Rules:**

| Scenario | Process | Fee | Research Needed |
|----------|---------|-----|-----------------|
| **Confirmed ticket** | Cancel and rebook | Clerkage | ? |
| **Tatkal ticket** | Not allowed | N/A | No changes |
| **Waitlist ticket** | Cancel and rebook | Fresh booking | ? |

**Research:**
- What are exact rescheduling rules?
- How do fees vary by class?
- What about emergency rescheduling?

### C. Disruptions

**Delay Compensation (Indian Railways):**

| Delay Duration | Compensation | Research Needed |
|---------------|--------------|-----------------|
| **< 2 hours** | None | ? |
| **2-4 hours** | Sometimes (fare refund?) | ? |
| **> 4 hours** | Full fare refund | Process? |
| **Train cancelled** | Full refund | Automatic? |

**International Delay Compensation:**

| Region/Operator | Policy | Research Needed |
|-----------------|--------|-----------------|
| **EU (Regulation 1371/2011)** | Compensation for 1+ hour delay | 25-50% of fare |
| **UK (Delay Repay)** | Compensation for 15+ min delay | % varies by delay |
| **Amtrak** | Varies | ? |
| **Japan** | Rarely, delays uncommon | ? |

**Missed Connections:**

| Scenario | Liability | Research Needed |
|-----------|-----------|-----------------|
| **Same booking** | Generally protected | Rebooking? |
| **Separate bookings** | Not protected | Customer risk |
| **Through ticket** | Protected | Overnight stay? |

**Disruption Communication:**

| Method | Timing | Content | Research Needed |
|--------|--------|---------|-----------------|
| **SMS** | Real-time | Delay info | ? |
| **Email** | Periodic | Updates | ? |
| **App notification** | Real-time | Push alerts | ? |
| **Website** | Real-time | Status board | ? |

### D. PNR Status Management

**Status Tracking:**

| Status | Meaning | Next Action | Research Needed |
|--------|---------|-------------|-----------------|
| **CNF/WL** | Current status | Wait for chart | ? |
| **Chart Prepared** | Final status | Boarding details | ? |
| **RAC** | Seat, not berth | Check at boarding | ? |

**Waitlist Movement:**

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Cancellations** | Moves WL up | How to predict? |
| **Additional quota** | May clear WL | When released? |
| **Chart preparation** | Final assignment | Time varies |

**Chart Preparation:**

| Train Type | Chart Time | Research Needed |
|------------|------------|-----------------|
| **Overnight** | 4 hours before | ? |
| **Day train** | 2-3 hours before | ? |
| **Rajdhani/Duronto** | Varies | ? |

---

## State Machines

**Cancellation State Machine:**

```
CONFIRMED → CANCELLATION_REQUESTED → PROCESSING →
                                        ├── REFUND_APPROVED → REFUND_PROCESSING → REFUNDED
                                        ├── REFUND_DENIED → CANCELLED_NO_REFUND
                                        └── PARTIAL_REFUND → REFUND_PROCESSING → PARTIALLY_REFUNDED
```

**Waitlist Movement State Machine:**

```
WAITLIST → CHART_PREPARATION →
                              ├── CONFIRMED → COACH_BERTH_ASSIGNED → TICKET_UPDATED
                              ├── RAC → SEAT_ASSIGNED → TICKET_UPDATED
                              └── REMAINS_WL → CANCELLED → REFUND_PROCESSING → REFUNDED
```

**Disruption State Machine:**

```
CONFIRMED → DISRUPTION →
                      ├── DELAYED → CUSTOMER_NOTIFIED → TRAVELS_DELAYED
                      ├── CANCELLED → REFUND_PROCESSING → REFUNDED
                      └── DIVERTED → ALTERNATIVE_ARRANGEMENTS → TRAVELS_ALTERNATE
```

---

## Support Playbook

**Pre-Travel Support:**

| Question | Response |
|----------|----------|
| "How do I check my PNR status?" | Use PNR number on website/app |
| "What's my coach and seat?" | Check after chart preparation |
| "Can I cancel my ticket?" | Yes, before chart preparation (except Tatkal) |
| "Will my waitlist confirm?" | Check current status, historical data |
| "What ID do I need?" | Any government ID matching ticket name |

**Disruption Support:**

| Issue | Immediate Action | Follow-up |
|-------|------------------|-----------|
| Train delayed | Inform customer, monitor status | Compensation if eligible |
| Train cancelled | Refund or alternative train | Process refund |
| Missed connection | Rebook if protected | Advise on future bookings |
| Chart prepared, status changed | Update customer, send ticket | Boarding details |

**Post-Travel Support:**

| Issue | Resolution |
|-------|------------|
| Refund not received | Check status, follow up with provider |
| Wrong berth assigned | Complaint to TTE, compensation possible |
| Left item on train | Lost and found process |
| Service complaint | Feedback form, investigation |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface RailCancellation {
  id: string;
  bookingId: string;
  pnrNumber: string;
  status: CancellationStatus;

  // Reason
  reason: CancellationReason;
  details?: string;

  // Refund
  refundAmount: Money;
  refundPercentage: number;
  clerkageFee: Money;
  refundMethod?: string;

  // Processing
  requestedAt: Date;
  requestedBy: string;
  processedAt?: Date;
  refundProcessedAt?: Date;
}

type CancellationReason =
  | 'customer_request'
  | 'train_cancelled'
  | 'chart_prepared_not_confirmed'
  | 'partial_confirmation'
  | 'other';

interface RailDisruption {
  id: string;
  bookingId: string;
  trainNumber: string;
  scheduledDeparture: Date;

  // Disruption details
  disruptionType: DisruptionType;
  delayMinutes?: number;
  reason?: string;

  // Communication
  notifiedAt: Date;
  notificationMethod: 'sms' | 'email' | 'app';

  // Resolution
  status: DisruptionStatus;
  resolution?: string;
  compensation?: Compensation;

  // Actual
  actualDeparture?: Date;
  actualArrival?: Date;
}

type DisruptionType =
  | 'delayed'
  | 'cancelled'
  | 'diverted'
  | 'partially_cancelled';

type DisruptionStatus =
  | 'active'
  | 'resolved'
  | 'compensated'
  | 'refunded';

interface PNRStatusUpdate {
  pnrNumber: string;

  // Status
  currentStatus: 'confirmed' | 'rac' | 'waitlist';
  previousStatus: 'confirmed' | 'rac' | 'waitlist';

  // Waitlist position
  currentWL?: number;
  previousWL?: number;

  // Assignment
  coach?: string;
  berth?: string;

  // Timestamp
  statusDate: Date;
  chartPrepared?: boolean;
}
```

---

## Open Problems

### 1. Strict Cancellation Policy
**Challenge:** Indian Railways has very strict rules

**Questions:**
- How do we communicate this clearly?
- Can we offer travel insurance?
- What about genuine emergencies?
- Tatkal no-refund policy?

### 2. Waitlist Anxiety
**Challenge:** Customers don't know if WL will confirm

**Options:**
- Show historical confirmation rate
- Real-time status updates
- Suggest confirmed alternatives
- Clear communication

### 3. Tatkal Limitations
**Challenge:** Tatkal has strict no-cancellation policy

**Options:**
- Clear disclosure before booking
- Suggest travel insurance
- Emergency exceptions?
- Book in general quota if possible

### 4. Disruption Compensation
**Challenge:** Compensation rules vary, process unclear

**Options:**
- Track eligible delays
- Auto-claim where possible
- Clear guidance
- Assist with claims

---

## Competitor Research Needed

| Competitor | Cancellation Policy | Notable Patterns |
|------------|---------------------|------------------|
| **IRCTC** | ? | ? |
| **MakeMyTrip** | ? | ? |
| **Yatra** | ? | ? |
| **Trainline** | ? | ? |

---

## Experiments to Run

1. **Cancellation ease test:** How smooth are cancellations?
2. **Refund timing test:** How long do refunds take?
3. **PNR status test:** How accurate is status tracking?
4. **Disruption notification test:** How are customers informed?

---

## References

- [Rail - Booking](./RAIL_03_BOOKING.md) — Booking flow
- [Flight Integration - Operations](./FLIGHT_INTEGRATION_06_OPERATIONS.md) — Similar disruption patterns

---

## Next Steps

1. Define cancellation policies
2. Build cancellation system
3. Implement PNR tracking
4. Create disruption notification
5. Measure support metrics

---

**Status:** Research Phase — Operations patterns unknown

**Last Updated:** 2026-04-27
