# Cruise Booking 04: Operations & Support

> Modifications, cancellations, and customer support for cruises

---

## Document Overview

**Focus:** Managing cruise bookings after confirmation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Modifications
- What changes can customers make? (Dates, cabin, passengers?)
- How do modification fees work?
- What about upgrading/downgrading cabins?
- How do we handle name changes?

### 2. Cancellations
- What are the cancellation policies?
- How do refunds work?
- What about cruise line cancellations?
- What about force majeure?

### 3. During Cruise
- What if something goes wrong during the cruise?
- How do we handle in-cruise issues?
- What's our escalation process?
- How do we support customers at sea?

### 4. Missed Port & Itinerary Changes
- What happens if the ship misses a port?
- How do we handle itinerary changes?
- What compensation is due?
- How do we communicate changes?

---

## Research Areas

### A. Modification Rules

**Allowed Changes:**

| Change Type | Allowed? | Timing | Fee | Research Needed |
|-------------|----------|--------|-----|-----------------|
| **Date change** | Sometimes | > 90 days | Fee + price difference | ? |
| **Ship change** | Sometimes | > 90 days | Fee + price difference | ? |
| **Cabin upgrade** | Usually | Any time until sail | Price difference | ? |
| **Cabin downgrade** | Rarely | > 60 days | Partial refund | ? |
| **Name change** | Sometimes | Until check-in | Fee or free | ? |
| **Add passenger** | If capacity | Until deadline | Pro-rated | ? |
| **Remove passenger** | Sometimes | > 60 days | Partial refund | ? |

**Modification Timing by Cruise Line:**

| Days Before Sail | What's Allowed | Typical Fee | Research Needed |
|-------------------|----------------|-------------|-----------------|
| **120+ days** | Most changes | Minimal | ? |
| **90-120 days** | Some changes | Moderate | ? |
| **60-90 days** | Limited changes | High | ? |
| **30-60 days** | Name changes only | Moderate | ? |
| **< 30 days** | No changes | Not allowed | Emergency only? |
| **< 7 days** | No changes | Not allowed | Medical emergency? |

**Research:**
- What are the actual modification rules by cruise line?
- How do fees vary by cabin category?
- What about loyalty program benefits?

### B. Cancellation Policies

**Standard Refund Schedule:**

| Days Before Sail | Refund | Cruise Line Deposit | Non-Refundable Deposit | Research Needed |
|-------------------|--------|---------------------|------------------------|-----------------|
| **120+ days** | 100% or deposit forfeited | Varies | Some lines have NRD | ? |
| **90-120 days** | 75-100% | Deposit forfeited | Deposit forfeited | ? |
| **60-90 days** | 50-75% | Deposit + penalty | Deposit forfeited | ? |
| **30-60 days** | 25-50% | Higher penalty | Deposit forfeited | ? |
| **15-30 days** | 0-25% | Major penalty | Deposit forfeited | ? |
| **< 15 days** | 0% | No refund | No refund | ? |

**Non-Refundable Deposit (NRD):**

| Policy | Description | Price Benefit | Research Needed |
|---------|-------------|----------------|-----------------|
| **NRD Fares** | Deposit non-refundable, lower fare | 10-20% cheaper | Popular? |
| **Standard Fares** | Refundable until deadline | Higher price | Default? |

**Special Cases:**

| Situation | Handling | Research Needed |
|-----------|----------|-----------------|
| **Medical emergency** | Full or partial refund with documentation | Required docs? |
| **Death in family** | Full or partial refund | Documentation? |
| **Visa refusal** | Full refund with proof | Timeline? |
| **Cruise line cancellation** | Full refund or rebook | Rebook options? |
| **Force majeure** | Case by case | What qualifies? |
| **Pandemic/COVID** | Special terms | Still applicable? |
| **Pregnancy** | Restricted after 24 weeks | Medical waiver? |

### C. During Cruise Support

**Common Issues:**

| Issue Type | Frequency | Resolution | Escalation | Research Needed |
|------------|-----------|------------|------------|-----------------|
| **Cabin issues** | High | Move cabin, compensation | Hotel director | ? |
| **Dining issues** | Medium | Change seating, restaurant | Maitre d' | ? |
| **Medical emergency** | Low | Ship medical, evacuation | Insurance | ? |
| **Missed port** | Medium | Communication, compensation | Cruise line | ? |
| **Service quality** | Medium | Address with staff | Hotel director | ? |
| **Lost property** | Medium | Search, report | Security | ? |
| **Behavioral issues** | Low | Security intervention | Security | ? |

**Support Levels:**

| Level | Issues | Resolution | SLA | Research Needed |
|-------|--------|------------|-----|-----------------|
| **Self-service** | FAQ, common questions | App, info channel | Immediate | ? |
| **Ship staff** | On-board issues | Immediate resolution | Immediate | ? |
| **Our support** | Booking issues, pre-cruise | Our team | 4-24 hours | ? |
| **Emergency** | Medical, safety | Ship medical, 24/7 line | Immediate | ? |

**At-Sea Communication:**

| Method | Availability | Cost | Research Needed |
|--------|--------------|------|-----------------|
| **Ship Wi-Fi** | Available | Expensive, slow | ? |
| **Cellular (at sea)** | Available | Very expensive | ? |
| **Ship phones** | Cabin phones | Expensive | ? |
| **Port Wi-Fi** | In port only | Cheaper | ? |

### D. Missed Ports & Itinerary Changes

**Reasons for Missed Ports:**

| Reason | Frequency | Compensation | Research Needed |
|--------|-----------|--------------|-----------------|
| **Weather** | Common | None or partial | Policy? |
| **Mechanical** | Less common | Partial refund or future credit | ? |
| **Strikes** | Rare | Varies | ? |
| **Political unrest** | Rare | Varies | ? |
| **Medical emergency** | Rare | None (ship diverts) | ? |

**Compensation for Missed Ports:**

| Scenario | Typical Compensation | Research Needed |
|----------|---------------------|-----------------|
| **Weather-related** | Usually none | ? |
| **Mechanical (overnight)** | Future cruise credit + refund | % of fare? |
| **Mechanical (missed port)** | Small credit or none | $? |
| **Multiple missed ports** | Significant credit or refund | ? |
| **Circuit breaker** | Full refund + future credit | ? |

**Communication:**

| Timing | Method | Content | Research Needed |
|--------|--------|---------|-----------------|
| **Before departure** | Email, phone | Notification of change | ? |
| **During cruise** | Announcement, app | Reason, new plan | ? |
| **After cruise** | Email | Compensation offer | ? |

---

## State Machines

**Modification State Machine:**

```
CONFIRMED → MODIFICATION_REQUESTED → UNDER_REVIEW →
                                        ├── APPROVED → MODIFIED → CONFIRMED
                                        └── DENIED → CONFIRMED
```

**Cancellation State Machine:**

```
CONFIRMED → CANCELLATION_REQUESTED → PROCESSING →
                                        ├── REFUND_APPROVED → REFUND_PROCESSING → REFUNDED
                                        ├── REFUND_DENIED → CANCELLED_NO_REFUND
                                        └── PARTIAL_REFUND → REFUND_PROCESSING → PARTIALLY_REFUNDED
```

**Itinerary Change State Machine:**

```
CONFIRMED → ITINERARY_CHANGE → CUSTOMER_NOTIFIED →
                                       ├── ACCEPTED → ITINERARY_UPDATED
                                       ├── COMPENSATION_OFFERED → CUSTOMER_RESPONDS
                                       └── CANCELLATION_OFFERED → CUSTOMER_RESPONDS
```

---

## Support Playbook

**Pre-Cruise Support:**

| Question | Response |
|----------|----------|
| "When do I get documents?" | 2-4 weeks before travel |
| "What's the baggage allowance?" | Check cruise line policy |
| "Can I change my cabin?" | Contact us, subject to availability |
| "Do I need a visa?" | Check itinerary requirements |
| "Can I bring wine?" | Check cruise line policy |

**During Cruise Support:**

| Issue | Immediate Action | Follow-up |
|-------|------------------|-----------|
| Cabin problem | Contact guest services, move if needed | Compensation request |
| Medical issue | Ship medical center, insurance activation | Check on recovery |
| Missed port | Communication about reason, alternative | Compensation if applicable |
| Service complaint | Contact guest services | Follow up after cruise |

**Post-Cruise Support:**

| Issue | Resolution |
|-------|------------|
| Billing error | Verify, refund if applicable |
| Service complaint | Investigate, compensate |
| Feedback request | Thank customer, log for improvement |
| Dispute resolution | Review evidence, fair outcome |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface CruiseModification {
  id: string;
  bookingId: string;
  type: ModificationType;
  status: ModificationStatus;

  // Requested changes
  changes: CruiseChange[];

  // Original booking
  originalBooking: CruiseBooking;

  // New details if approved
  modifiedBooking?: CruiseBooking;

  // Financial
  priceAdjustment: Money;
  additionalPayment?: Money;
  refundAmount?: Money;
  modificationFee?: Money;

  // Processing
  requestedAt: Date;
  requestedBy: string;
  processedAt?: Date;
  approvedBy?: string;
  reason?: string;
}

type ModificationType =
  | 'date_change'
  | 'ship_change'
  | 'cabin_upgrade'
  | 'cabin_downgrade'
  | 'name_change'
  | 'passenger_add'
  | 'passenger_remove';

interface CruiseCancellation {
  id: string;
  bookingId: string;
  status: CancellationStatus;

  // Reason
  reason: CancellationReason;
  details?: string;

  // Refund
  refundAmount: Money;
  refundPercentage: number;
  refundMethod?: string;

  // Insurance claim
  insuranceClaim?: boolean;
  insuranceClaimId?: string;

  // Documentation
  documentation?: string[];

  // Processing
  requestedAt: Date;
  requestedBy: string;
  processedAt?: Date;
  approvedBy?: string;
  refundProcessedAt?: Date;
}

type CancellationReason =
  | 'customer_request'
  | 'medical_emergency'
  | 'death_in_family'
  | 'visa_refusal'
  | 'cruise_line_cancelled'
  | 'force_majeure'
  | 'pregnancy'
  | 'other';

interface ItineraryChange {
  id: string;
  bookingId: string;
  cruiseId: string;

  // Change details
  changeType: ItineraryChangeType;
  originalItinerary: CruiseItinerary;
  newItinerary?: CruiseItinerary;

  // Affected elements
  missedPorts: Port[];
  addedPorts?: Port[];
  changedTiming?: TimingChange[];

  // Reason
  reason: string;

  // Compensation
  compensationOffered?: CompensationOffer;
  compensationAccepted?: boolean;

  // Communication
  notifiedAt: Date;
  customerResponse?: 'accepted' | 'declined' | 'pending';
}

type ItineraryChangeType =
  | 'missed_port'
  | 'multiple_missed_ports'
  | 'route_change'
  | 'timing_change'
  | 'cruise_cancelled';

interface InCruiseIssue {
  id: string;
  bookingId: string;
  reporter: 'passenger' | 'crew' | 'other';

  // Issue details
  issueType: InCruiseIssueType;
  severity: 'low' | 'medium' | 'high' | 'emergency';
  description: string;
  location?: string; // On ship location

  // Resolution
  status: IssueStatus;
  resolution?: string;
  shipResolution?: string; // What ship staff did
  compensation?: Compensation;

  // Timeline
  reportedAt: Date;
  respondedAt?: Date;
  resolvedAt?: Date;
}

type InCruiseIssueType =
  | 'cabin_problem'
  | 'dining_issue'
  | 'medical_emergency'
  | 'behavioral_issue'
  | 'service_complaint'
  | 'maintenance_issue'
  | 'safety_concern';

type CompensationOffer =
  | { type: 'refund'; amount: Money; percentage: number }
  | { type: 'future_credit'; amount: Money; expiryDate: Date }
  | { type: 'upgrade'; details: string }
  | { type: 'onboard_credit'; amount: Money };
```

---

## Open Problems

### 1. Strict Cancellation Policies
**Challenge:** Cruise cancellation policies are very strict

**Questions:**
- How do we communicate this clearly?
- Should we offer travel insurance?
- What about genuine emergencies?
- Insurance coverage options?

### 2. Itinerary Changes
**Challenge:** Ships miss ports, itineraries change

**Questions:**
- How do we set customer expectations?
- What compensation is fair?
- How do we communicate changes quickly?
- Who handles complaints?

### 3. At-Sea Support
**Challenge:** Limited ability to help while customer is at sea

**Options:**
- Rely on ship staff
- Emergency contact only
- Expensive communication options
- Post-cruise resolution

### 4. Solo Traveler Challenges
**Challenge:** Single supplements, solo dining

**Options:**
- Clear disclosure
- Solo-friendly options
- Single share matching
- Solo promotions

---

## Competitor Research Needed

| Competitor | Cancellation Policy | Notable Patterns |
|------------|---------------------|------------------|
| **Expedia Cruises** | ? | ? |
| **CruiseDirect** | ? | ? |
| **Cruise Line Direct** | ? | ? |

---

## Experiments to Run

1. **Modification ease test:** How smooth are changes?
2. **Cancellation rate study:** What % of cruises are cancelled?
3. **Refund timing study:** How long do refunds take?
4. **Itinerary change impact:** How do customers react?

---

## References

- [Cruise - Booking](./CRUISE_03_BOOKING.md) — Booking flow
- [Package Tours - Operations](./PACKAGE_TOURS_04_OPERATIONS.md) — Similar patterns

---

## Next Steps

1. Define modification policies
2. Build modification system
3. Implement cancellation flow
4. Create support documentation
5. Measure support metrics

---

**Status:** Research Phase — Operations patterns unknown

**Last Updated:** 2026-04-27
