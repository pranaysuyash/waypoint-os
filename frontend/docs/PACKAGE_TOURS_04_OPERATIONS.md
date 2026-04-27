# Package Tours 04: Operations & Support

> Modifications, cancellations, refunds, and customer support

---

## Document Overview

**Focus:** Managing package bookings after confirmation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Modifications
- What changes can customers make? (Dates, travelers, rooming?)
- How do modification fees work?
- What about name changes?
- How do we handle upgrades?

### 2. Cancellations
- What are the cancellation policies?
- How do refunds work?
- What about force majeure?
- What if the operator cancels?

### 3. During Travel
- What if something goes wrong during the trip?
- How do we handle in-trip issues?
- What's our escalation process?
- How do we support customers abroad?

### 4. Post-Travel
- How do we collect feedback?
- What about complaints?
- How do we handle refunds for issues?
- What about loyalty/repeat business?

---

## Research Areas

### A. Modification Rules

**Allowed Changes:**

| Change Type | Allowed? | Timing | Fee | Research Needed |
|-------------|----------|--------|-----|-----------------|
| **Date change** | Sometimes | > 60 days | Price difference + fee | ? |
| **Name change** | Sometimes | Any time | Fee or free | ? |
| **Add traveler** | If capacity | Until deadline | Pro-rated | ? |
| **Remove traveler** | Sometimes | > 60 days | Partial refund | ? |
| **Room change** | Sometimes | Until deadline | Price difference | ? |
| **Upgrade** | Usually | Any time | Price difference | ? |
| **Downgrade** | Rarely | > 60 days | Partial refund | ? |

**Modification Timing:**

| Days Before Travel | What's Allowed | Fee | Research Needed |
|-------------------|----------------|-----|-----------------|
| **60+ days** | Most changes | Minimal | ? |
| **45-60 days** | Name changes only | Moderate | ? |
| **30-45 days** | Limited changes | High | ? |
| **< 30 days** | No changes | Not allowed | ? |
| **< 7 days** | No changes | Not allowed | Emergency only? |

**Research:**
- What are the actual modification rules by operator?
- How do we handle price differences?
- What about airline ticket changes?

### B. Cancellation Policies

**Policy Types:**

| Policy Type | Notice Required | Refund | Common For | Research Needed |
|-------------|-----------------|--------|------------|-----------------|
| **Flexible** | 45+ days | 90-100% | Luxury packages | ? |
| **Standard** | 60 days | 50-80% | Most packages | ? |
| **Strict** | 90+ days | 0-50% | Peak season, groups | ? |
| **Non-refundable** | None | 0% | Special deals | ? |

**Standard Refund Schedule:**

| Days Before Travel | Refund | Deductions | Research Needed |
|-------------------|--------|------------|-----------------|
| **60+ days** | 80-100% | Deposit may be forfeited | ? |
| **45-60 days** | 50-80% | Deposit + penalty | ? |
| **30-45 days** | 25-50% | Higher penalty | ? |
| **15-30 days** | 0-25% | Major penalty | ? |
| **< 15 days** | 0% | No refund | ? |

**Special Cases:**

| Situation | Handling | Research Needed |
|-----------|----------|-----------------|
| **Medical emergency** | Full or partial refund with documentation | Required docs? |
| **Visa refusal** | Full refund with proof | Timeline? |
| **Operator cancellation** | Full refund or rebook | Rebook options? |
| **Force majeure** | Case by case | What qualifies? |
| **Pandemic/COVID** | Special terms | Still applicable? |

### C. In-Trip Support

**Common Issues:**

| Issue Type | Frequency | Resolution | Escalation | Research Needed |
|------------|-----------|------------|------------|-----------------|
| **Hotel problems** | High | Move hotel, compensation | Local operator | ? |
| **Guide issues** | Medium | Replace guide | Local operator | ? |
| **Missed connection** | Medium | Rebook transport | Local operator | ? |
| **Medical emergency** | Low | Hospital, evacuation | Insurance | ? |
| **Lost documents** | Medium | Replace, assist | Embassy | ? |
| **Quality not as described** | Medium | Compensation | Operator or us | ? |

**Support Tiers:**

| Tier | Issues | Resolution | SLA | Research Needed |
|------|--------|------------|-----|-----------------|
| **Self-service** | FAQ, common questions | App, chatbot | Immediate | ? |
| **Local support** | On-ground issues | Local operator, guide | 1-2 hours | ? |
| **Our support** | Booking issues, escalation | Our team | 4-8 hours | ? |
| **Emergency** | Medical, safety | 24/7 line, insurance | Immediate | ? |

**Emergency Protocols:**

| Emergency | Response | Research Needed |
|-----------|----------|-----------------|
| **Medical** | Local hospital, insurance activation | Insurance details? |
| **Lost passport** | Embassy contact, local police | Process? |
| **Natural disaster** | Evacuation, rebooking | Who pays? |
| **Political unrest** | Evacuation, cancellation | Insurance? |
| **Terrorist incident** | Evacuation, trauma support | Government support? |

### D. Post-Travel

**Feedback Collection:**

| Method | Timing | Incentives | Research Needed |
|--------|--------|------------|-----------------|
| **In-app survey** | Immediately after trip | None | Completion rate? |
| **Email survey** | 1 week after | Discount on next | ? |
| **Review request** | 2 weeks after | Loyalty points | ? |
| **Phone call** | For high-value | Personal touch | VIP only? |

**Complaint Handling:**

| Complaint Type | Resolution | Compensation | Research Needed |
|---------------|------------|--------------|-----------------|
| **Service not as described** | Investigation | Partial refund or credit | ? |
| **Hotel quality issue** | Verify with photos | Refund or upgrade | ? |
| **Guide behavior** | Investigate | Apology, compensation | ? |
| **Missed service** | Verify | Refund or reschedule | ? |

**Refund Processing:**

| Refund Type | Timeline | Method | Research Needed |
|-------------|----------|--------|-----------------|
| **Cancellation** | 7-21 days | Original payment | ? |
| **Service failure** | 7-14 days | Credit or refund | ? |
| **Compensation** | Immediate | Future credit | ? |

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

---

## Support Playbook

**Pre-Travel Support:**

| Question | Response |
|----------|----------|
| "When do I get documents?" | 2-4 weeks before travel |
| "What's the baggage allowance?" | Check airline ticket |
| "Can I change my room?" | Contact us, subject to availability |
| "Do I need a visa?" | Check destination requirements |

**During Travel Support:**

| Issue | Immediate Action | Follow-up |
|-------|------------------|-----------|
| Hotel problem | Contact local operator, move if needed | Compensation request |
| Medical issue | Contact insurance, local hospital | Check on recovery |
| Missed flight | Contact airline, rebook | File claim if applicable |
| Lost passport | Contact embassy, local police | Assist with replacement |

**Post-Travel Support:**

| Issue | Resolution |
|-------|------------|
| Billing error | Verify, refund if applicable |
| Service complaint | Investigate, compensate |
| Feedback request | Thank customer, log for improvement |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface PackageModification {
  id: string;
  bookingId: string;
  type: ModificationType;
  status: ModificationStatus;

  // Requested changes
  changes: PackageChange[];

  // Original booking
  originalBooking: PackageBooking;

  // New details if approved
  modifiedBooking?: PackageBooking;

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
  | 'name_change'
  | 'traveler_add'
  | 'traveler_remove'
  | 'room_change'
  | 'upgrade'
  | 'downgrade';

interface PackageCancellation {
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
  | 'visa_refusal'
  | 'operator_cancelled'
  | 'force_majeure'
  | 'other';

interface InTripIssue {
  id: string;
  bookingId: string;
  reporter: string;

  // Issue details
  issueType: IssueType;
  severity: 'low' | 'medium' | 'high' | 'emergency';
  description: string;

  // Resolution
  status: IssueStatus;
  resolution?: string;
  compensation?: Compensation;

  // Timeline
  reportedAt: Date;
  respondedAt?: Date;
  resolvedAt?: Date;
}

type IssueType =
  | 'hotel_problem'
  | 'guide_issue'
  | 'transport_issue'
  | 'medical_emergency'
  | 'lost_documents'
  | 'quality_complaint'
  | 'safety_concern';

type Compensation =
  | { type: 'refund'; amount: Money }
  | { type: 'credit'; amount: Money; forFutureUse: true }
  | { type: 'upgrade'; details: string }
  | { type: 'apology'; details: string };
```

---

## Open Problems

### 1. Last-Minute Cancellations
**Challenge:** Customer cancels just before travel

**Questions:**
- Is any refund possible?
- How strict are operators?
- What about genuine emergencies?
- Insurance coverage?

### 2. Subjective Complaints
**Challenge:** "Hotel wasn't as good as expected"

**Options:**
- Define objective standards
- Photo evidence required
- Operator investigation
- Partial compensation

### 3. Cross-Border Issues
**Challenge:** Legal jurisdiction varies by country

**Questions:**
- Which laws apply?
- How do we handle foreign operators?
- What about consumer protection?

### 4. No-Show Management
**Challenge:** Customer doesn't show up for trip

**Questions:**
- Is this trackable?
- Any refund possible?
- Impact on operator relationship?

---

## Competitor Research Needed

| Competitor | Cancellation Policy | Notable Patterns |
|------------|---------------------|------------------|
| **MakeMyTrip** | ? | ? |
| **Yatra** | ? | ? |
| **TravelTriangle** | ? | ? |
| **TourRadar** | ? | Flexible options? |

---

## Experiments to Run

1. **Modification ease test:** How smooth are changes?
2. **Cancellation rate study:** What % of packages are cancelled?
3. **Refund timing study:** How long do refunds take?
4. **Support quality test:** How do we handle in-trip issues?

---

## References

- [Package Tours - Booking](./PACKAGE_TOURS_03_BOOKING.md) — Booking flow
- [Activities - Operations](./ACTIVITIES_04_OPERATIONS.md) — Similar patterns
- [Flight Integration - Operations](./FLIGHT_INTEGRATION_06_OPERATIONS.md) — Disruption handling

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
