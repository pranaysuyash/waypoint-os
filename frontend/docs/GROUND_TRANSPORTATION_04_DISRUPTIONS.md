# Ground Transportation 04: Disruptions & Support

> Handling delays, no-shows, cancellations, and customer support

---

## Document Overview

**Focus:** Managing when things don't go as planned
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Flight Delay Integration
- How do we track flight delays for airport pickups?
- How do we communicate delays to drivers/providers?
- What is the waiting time policy?
- Who pays for extended waiting?
- At what point do we cancel/reschedule?

### 2. No-Show Scenarios
- What constitutes a no-show? (Customer? Driver?)
- What is the grace period?
- Is the booking chargeable?
- How do we arrange alternative transport?

### 3. Cancellations
- What are the cancellation windows?
- How are refunds processed?
- What are the cancellation fees?
- How do we handle last-minute cancellations?

### 4. Driver Issues
- What if driver is late?
- What if driver is rude/unprofessional?
- What if vehicle is wrong/dirty?
- What if vehicle breaks down?

---

## Research Areas

### A. Flight Delay Handling

**Delay Scenarios:**

| Delay Duration | Impact | Action Required |
|---------------|--------|-----------------|
| < 30 min | Minor | Inform driver, adjust pickup |
| 30-60 min | Moderate | Inform driver, may incur waiting fee |
| 1-2 hours | Significant | May need to reschedule driver |
| > 2 hours | Major | May need new booking entirely |

**Research Questions:**
- How do we get real-time flight status?
- How much notice do drivers need for schedule changes?
- What is the cost of rescheduling vs. waiting?
- Do customers pay for waiting time?

**Integration Points:**
- Flight status APIs (for tracking)
- Driver communication (for notification)
- Pricing (for waiting fees)

### B. No-Show Policies

**Customer No-Show:**

| Time since pickup | Action | Refund? |
|-------------------|--------|---------|
| 0-15 min | Wait, contact customer | Full |
| 15-30 min | Wait, contact customer, alert driver | Partial? |
| 30-60 min | Consider no-show, partial refund | Partial |
| 60+ min | Confirmed no-show, no refund | None |

**Driver No-Show:**

| Time since scheduled | Action |
|---------------------|--------|
| 0-10 min | Normal variance, wait |
| 10-20 min | Contact provider |
| 20-30 min | Arrange alternative |
| 30+ min | Full replacement, compensation? |

**Research:**
- What are industry standard grace periods?
- How do we prove customer vs. driver no-show?
- What evidence is required?

### C. Cancellation Windows

| Before Pickup | Customer Refund | Provider Fee |
|---------------|-----------------|--------------|
| 48+ hours | 100% | ? |
| 24-48 hours | 50-100% | ? |
| 12-24 hours | 0-50% | ? |
| < 12 hours | 0% | ? |
| No-show | 0% | 100% |

**Research Needed:**
- What are the actual policies by provider?
- Can we negotiate better terms?
- How do we display this clearly to customers?

### D. Driver/Vehicle Issues

| Issue | Detection | Resolution |
|-------|-----------|------------|
| **Driver late** | Customer report, GPS | ETA update, compensation? |
| **Wrong vehicle** | Customer report | Replacement, report to provider |
| **Dirty vehicle** | Customer report | Report to provider, compensation? |
| **Rude driver** | Post-trip feedback | Report to provider, remove? |
| **Breakdown** | Driver report | Arrange replacement |
| **Wrong route** | Customer report, GPS | Redirect, fare adjustment |

---

## Disruption State Machine

```
CONFIRMED → DELAY_DETECTED → HANDLING_DELAY → RESOLVED
            ↓                  ↓
        CANCELLATION      ESCALATION
            ↓                  ↓
        REFUND_PROCESSING  MANUAL_RESOLUTION
```

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface Disruption {
  id: string;
  bookingId: string;
  type: DisruptionType;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: DisruptionStatus;

  // Detection
  detectedAt: Date;
  detectedBy: 'system' | 'customer' | 'driver' | 'provider';
  source: string;  // Flight status API, customer report, etc.

  // Details
  description: string;
  estimatedDelay?: Duration;
  actualImpact?: ImpactAssessment;

  // Resolution
  actionTaken?: DisruptionAction[];
  resolvedAt?: Date;
  resolutionNotes?: string;

  // Financial
  refundAmount?: Money;
  compensationAmount?: Money;
  additionalCost?: Money;
}

type DisruptionType =
  | 'flight_delay'
  | 'customer_late'
  | 'driver_late'
  | 'driver_no_show'
  | 'customer_no_show'
  | 'vehicle_issue'
  | 'booking_error'
  | 'weather'
  | 'traffic';

enum DisruptionStatus {
  DETECTED = 'detected',
  ASSESSING = 'assessing',
  HANDLING = 'handling',
  RESOLVED = 'resolved',
  ESCALATED = 'escalated',
  CANCELLED = 'cancelled'
}
```

---

## Communication Protocols

### For Flight Delays:

| Timing | Notify | Message |
|--------|--------|---------|
| On detection | Customer | "Flight delayed, pickup adjusted to [new time]" |
| On detection | Driver/Provider | "Customer flight delayed, new pickup [new time]" |
| If major change | Customer | "Significant delay, please confirm: keep booking or reschedule?" |
| On resolution | Customer | "Pickup confirmed for [new time], driver [name]" |

### For Driver Issues:

| Timing | Notify | Message |
|--------|--------|---------|
| Customer reports | Provider | "Driver [name] reported: [issue]. Please investigate." |
| Alternative arranged | Customer | "New driver arranged: [name], arriving [time]" |
| Resolution | Customer | "Issue resolved. Compensation: [amount if applicable]" |

---

## SLA Considerations

**Response Times:**

| Priority | Response Time | Resolution Target |
|----------|---------------|-------------------|
| Critical (stranded) | 5 min | 30 min |
| High (delay > 1hr) | 15 min | 1 hour |
| Medium (delay < 1hr) | 30 min | 2 hours |
| Low (info request) | 1 hour | 24 hours |

**Research:**
- What SLAs can providers commit to?
- What SLAs do customers expect?
- How do we measure compliance?

---

## Open Problems

### 1. Flight Tracking Accuracy
**Challenge:** Flight status APIs may be delayed or inaccurate

**Options:**
- Use multiple data sources
- Build in buffer time
- Manual verification for critical bookings

### 2. Proof of No-Show
**Challenge:** Customer says they were there, driver says no-show

**Questions:**
- What evidence is acceptable? (GPS? Photos?)
- How do we handle disputes?
- Who bears the cost in ambiguous cases?

### 3. Cross-Border Disruptions
**Challenge:** Breakdown in foreign country, language barriers

**Questions:**
- How do we arrange help abroad?
- What insurance coverage applies?
- How do we handle language issues?

### 4. Last-Minute Alternatives
**Challenge:** Driver no-show, need immediate replacement

**Questions:**
- How do we find alternatives quickly?
- What if no alternatives available?
- Who pays the difference in cost?

---

## Competitor Research Needed

| Competitor | Disruption Handling | Notable Patterns |
|------------|-------------------|------------------|
| **Uber** | ? | ? |
| **Rentalcars.com** | ? | ? |
| **GetYourGuide** | ? | ? |
| **Local agents** | ? | ? |

---

## Experiments to Run

1. **Flight delay tracking test:** How accurate are APIs?
2. **No-show dispute analysis:** What are the patterns?
3. **Alternative availability test:** Can we find replacements quickly?
4. **Customer expectation survey:** What response times are expected?

---

## References

- [Flight Integration - Operations](./FLIGHT_INTEGRATION_06_OPERATIONS.md) — Disruption patterns
- [Booking Engine - Cancellations](./BOOKING_ENGINE_06_CANCELLATIONS.md) — Cancellation patterns

---

## Next Steps

1. Interview providers about disruption handling
2. Research flight tracking APIs
3. Design disruption detection system
4. Build communication templates
5. Create resolution playbook

---

**Status:** Research Phase — Disruption handling unknown

**Last Updated:** 2026-04-27
