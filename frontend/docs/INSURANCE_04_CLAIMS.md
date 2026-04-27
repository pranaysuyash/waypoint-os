# Travel Insurance 04: Claims & Support

> Claims processing, customer support, and assistance services

---

## Document Overview

**Focus:** Managing insurance claims and providing support
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Claims Process
- How do customers file claims?
- What documentation is required?
- How are claims assessed?
- What are the timelines for resolution?
- What is our role vs. the insurer's role?

### 2. Emergency Assistance
- What is the 24/7 assistance service?
- How do customers access emergency help?
- What can be handled without a claim?
- How do we coordinate medical evacuations?

### 3. Customer Support
- What questions do customers have about their policies?
- How do we handle policy interpretation questions?
- What about coverage clarifications?
- How do we manage customer expectations?

### 4. Post-Claims Experience
- How do we handle claim rejections?
- What about appeals?
- How do we collect feedback?
- What about renewals and repeat business?

---

## Research Areas

### A. Claims Types

**Common Claim Categories:**

| Claim Type | Frequency | Complexity | Average Value |
|------------|-----------|------------|---------------|
| **Medical emergency** | Medium | High | High |
| **Trip cancellation** | High | Low | Medium |
| **Trip interruption** | Medium | Medium | Medium |
| **Baggage loss/delay** | Medium | Low | Low |
| **Flight delay** | High | Low | Low |
| **Missed connection** | Medium | Low | Low |
| **Medical evacuation** | Low | Very High | Very High |

**Research:**
- What are the most common claims?
- Which have the highest rejection rates?
- What documentation is typically required?

### B. Claims Process

**Standard Claims Flow:**

```
Claim Intiated → Documentation Collected → Claim Submitted → Insurer Review
                                                            ↓
                                                    APPROVED or REJECTED
                                                            ↓
                                                    Payment or Appeal
```

**Steps:**

| Step | Owner | Duration |
|------|-------|----------|
| **Claim initiated** | Customer | Instant |
| **Documentation** | Customer | Days to weeks |
| **Submission** | Us or Insurer | Instant |
| **Review** | Insurer | Days to weeks |
| **Decision** | Insurer | Instant |
| **Payment** | Insurer | Days to weeks |

**Research:**
- What documentation is required for each claim type?
- How long does each step typically take?
- Can we track claim status?

### C. Required Documentation

**By Claim Type:**

| Claim Type | Required Documentation |
|------------|------------------------|
| **Medical** | Doctor reports, receipts, medical records |
| **Cancellation** | Proof of cancellation, reason, receipts |
| **Interruption** | Proof of return, unused portions |
| **Baggage** | Property irregularity report, receipts, valuation |
| **Delay** | Airline delay certificate, receipts for expenses |
| **Theft** | Police report, proof of ownership |

**Research:**
- How do we help customers gather documents?
- What happens if documentation is incomplete?
- Can we accept digital copies?

### D. Emergency Assistance

**Assistance Services:**

| Service | Provided By | How Accessed |
|---------|-------------|--------------|
| **Medical referral** | Insurer's assistance company | Phone/app |
| **Medical evacuation** | Insurer's assistance company | Phone (emergency) |
| **Travel assistance** | Insurer's assistance company | Phone/app |
| **Legal referral** | Insurer's assistance company | Phone |
| **Document replacement** | Insurer's assistance company | Phone |

**Research:**
- Who provides the assistance service? (Insurer or third-party)
- What languages are supported?
- What is the quality of service?

---

## Claims Data Model

```typescript
// Research-level model - not final

interface InsuranceClaim {
  id: string;
  policyId: string;
  tripId?: string;

  // Status
  status: ClaimStatus;
  submittedAt: Date;
  resolvedAt?: Date;

  // Claim details
  type: ClaimType;
  incidentDate: Date;
  incidentLocation: string;
  description: string;

  // Financial
  amountClaimed: Money;
  amountApproved?: Money;
  amountPaid?: Money;

  // Documentation
  documentation: ClaimDocument[];

  // Assessment
  assessorNotes?: string;
  decisionReason?: string;
  decisionDate?: Date;

  // Communication
  communications: ClaimCommunication[];
}

type ClaimStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'additional_info_requested'
  | 'approved'
  | 'partially_approved'
  | 'rejected'
  | 'paid'
  | 'appealed';

type ClaimType =
  | 'medical_emergency'
  | 'trip_cancellation'
  | 'trip_interruption'
  | 'baggage_loss'
  | 'baggage_delay'
  | 'flight_delay'
  | 'missed_connection'
  | 'medical_evacuation'
  | 'theft'
  | 'other';

interface ClaimDocument {
  type: DocumentType;
  url: string;
  uploadedAt: Date;
  status: 'pending' | 'accepted' | 'rejected';
}

type DocumentType =
  | 'medical_report'
  | 'receipt'
  | 'cancellation_notice'
  | 'police_report'
  | 'property_irregularity_report'
  | 'airline_certificate'
  | 'other';
```

---

## Our Role vs. Insurer Role

| Activity | Our Role | Insurer Role |
|----------|----------|--------------|
| **Claims submission** | Facilitate | Process |
| **Claims assessment** | None | Assess and decide |
| **Claims payment** | None | Pay |
| **Customer support** | First line, basic questions | Complex questions |
| **Emergency assistance** | None (direct to insurer) | Provide |
| **Appeals** | Facilitate | Decide |

**Research:**
- What is our liability if we give incorrect advice?
- How do we handle complaints?
- What are the escalation procedures?

---

## Open Problems

### 1. Claim Rejection
**Challenge:** Customer's claim is rejected

**Questions:**
- How do we communicate this?
- Can we help with appeals?
- What is our liability if we gave wrong information?

### 2. Documentation Burden
**Challenge:** Customer can't provide required documentation

**Options:**
- Help customer obtain documents
- Accept alternative evidence
- Claim may be denied

**Research:** What flexibility exists?

### 3. Emergency Coordination
**Challenge:** Customer has medical emergency abroad

**Questions:**
- How do we help quickly?
- What if the 24/7 line is unreachable?
- What is our liability?

### 4. Claims Transparency
**Challenge:** Customer doesn't know claim status

**Options:**
- Real-time tracking
- Regular updates
- Portal access

**Research:** What are customer expectations?

---

## Competitor Research Needed

| Competitor | Claims Process | Notable Patterns |
|------------|----------------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **Direct insurers** | ? | ? |

---

## Experiments to Run

1. **Claims audit:** Analyze common claim reasons and outcomes
2. **Documentation study:** What docs are typically problematic?
3. **Customer interview:** What are pain points in claims process?
4. **Assistance test:** Call assistance lines, test quality

---

## References

- [Safety Systems](./SAFETY_DEEP_DIVE_MASTER_INDEX.md) — Risk and incident handling
- [Communication Hub](./COMM_HUB_DEEP_DIVE_MASTER_INDEX.md) — Support patterns

---

## Next Steps

1. Research insurer claims processes
2. Design claims submission flow
3. Build claim tracking system
4. Create customer support guides
5. Test assistance services

---

**Status:** Research Phase — Claims patterns unknown

**Last Updated:** 2026-04-27
