# Lead Management 04: Conversion

> Closing leads, handoff to booking, and conversion tracking

---

## Document Overview

**Focus:** Lead conversion and closing
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Conversion Process
- How do we convert leads to bookings?
- What is the handoff process?
- How do we track conversion rates?
- What about lost leads?

### Closing Strategies
- What closing techniques work?
- How do we handle objections?
- What about urgency creation?
- How do we negotiate?

### Handoff to Operations
- How does the handoff work?
- What information is transferred?
- How do we ensure smooth transition?
- What about customer experience?

### Analytics & Optimization
- How do we measure conversion?
- What metrics matter most?
- How do we identify bottlenecks?
- What about A/B testing?

---

## Research Areas

### A. Conversion Workflow

**Stages:**

| Stage | Description | Research Needed |
|-------|-------------|-----------------|
| **Proposal** | Send quote/itinerary | ? |
| **Negotiation** | Discuss terms | ? |
| **Commitment** | Customer agrees | ? |
| **Payment** | Collect deposit | ? |
| **Booking** | Create booking | ? |
| **Handoff** | Transfer to operations | ? |

**Conversion Triggers:**

| Trigger | Action | Research Needed |
|---------|--------|-----------------|
| **Proposal accepted** | Create booking | ? |
| **Deposit paid** | Confirm booking | ? |
| **Form signed** | Lock in price | ? |
| **Verbal confirmation** | Send payment link | ? |

**Time to Convert:**

| Stage | Typical Duration | Research Needed |
|-------|------------------|-----------------|
| **Proposal to decision** | 2-7 days | ? |
| **Decision to payment** | 1-3 days | ? |
| **Payment to booking** | Same day | ? |

### B. Closing Strategies

**Urgency Tactics:**

| Tactic | Use When | Research Needed |
|--------|----------|-----------------|
| **Limited time offer** | Price valid until | ? |
| **Availability warning** | Few seats left | ? |
| **Price increase** | Rates going up | ? |
| **Bonus expires** | Add-on deadline | ? |

**Objection Handling:**

| Objection | Response | Research Needed |
|-----------|----------|-----------------|
| **Too expensive** | Value justification | ? |
| **Need to think** | Set follow-up | ? |
| **Check elsewhere** | Confidence + differentiation | ? |
| **Not ready** | Nurture + timing | ? |

**Negotiation:**

| Scenario | Approach | Research Needed |
|----------|----------|-----------------|
| **Price objection** | Add value, don't discount | ? |
| **Competitor price** | Differentiate, match if needed | ? |
| **Group discount** | Volume-based | ? |
| **Loyalty** | Future value | ? |

### C. Handoff Process

**Handoff Checklist:**

| Item | Description | Research Needed |
|------|-------------|-----------------|
| **Customer profile** | All collected data | ? |
| **Trip details** | Itinerary, preferences | ? |
| **Communication history** | Notes, interactions | ? |
| **Special requests** | Must-haves | ? |
| **Payment status** | Deposit, balance | ? |

**Handoff Methods:**

| Method | Best For | Research Needed |
|--------|----------|-----------------|
| **Automatic** | Standard bookings | ? |
| **Meeting** | Complex trips | ? |
| **Call** | VIP customers | ? |
| **Document** | Full handover file | ? |

**Post-Conversion:**

| Action | Timing | Research Needed |
|--------|--------|-----------------|
| **Welcome email** | Immediately | ? |
| **Documentation** | Within 24 hours | ? |
| **Check-in** | Before trip | ? |
| **Feedback** | After trip | ? |

### D. Lost Lead Analysis

**Loss Reasons:**

| Reason | Frequency | Research Needed |
|--------|-----------|-----------------|
| **Price** | High | ? |
| **Timing** | Medium | ? |
| **Went elsewhere** | High | ? |
| **Decided not to travel** | Low | ? |
| **No response** | High | ? |

**Win-Back Campaigns:**

| Trigger | Message | Research Needed |
|---------|---------|-----------------|
| **Lost on price** | New deals, promotions | ? |
| **Lost on timing** | Reconnect when timing better | ? |
| **No response** | Different approach | ? |
| **Seasonal** | Relevant travel time | ? |

**Learning:**

| Metric | Use | Research Needed |
|--------|-----|-----------------|
| **Conversion rate** | Overall performance | ? |
| **Time to convert** | Process efficiency | ? |
| **Lost reasons** | Improvement areas | ? |
| **Win-back rate** | Recovery potential | ? |

---

## Data Model Sketch

```typescript
interface LeadConversion {
  conversionId: string;
  leadId: string;
  bookingId?: string;

  // Process
  stage: ConversionStage;
  startedAt: Date;
  convertedAt?: Date;

  // Proposal
  proposalId?: string;
  proposalAmount?: number;
  finalAmount?: number;

  // Outcome
  outcome: ConversionOutcome;
  lostReason?: string;
  lostDetails?: string;

  // Attribution
  convertedBy?: string; // Agent ID
  conversionPath: Touchpoint[];

  // Handoff
  handoffCompleted: boolean;
  handoffAt?: Date;
  handoffTo?: string;
}

type ConversionStage =
  | 'proposal'
  | 'negotiation'
  | 'commitment'
  | 'payment'
  | 'booking'
  | 'handoff'
  | 'complete';

type ConversionOutcome =
  | 'converted'
  | 'lost'
  | 'deferred';

interface ConversionProposal {
  proposalId: string;
  leadId: string;

  // Content
  itinerary: ItinerarySummary;
  pricing: PricingBreakdown;
  terms: ProposalTerms;

  // Status
  status: ProposalStatus;
  sentAt: Date;
  expiresAt?: Date;

  // Engagement
  viewedAt?: Date;
  acceptedAt?: Date;
  rejectedAt?: Date;
  feedback?: string;
}

type ProposalStatus =
  | 'draft'
  | 'sent'
  | 'viewed'
  | 'accepted'
  | 'rejected'
  | 'expired';

interface ItinerarySummary {
  destination: string;
  duration: number; // Days
  departureDate: Date;
  components: ComponentSummary[];
}

interface ComponentSummary {
  type: string;
  name: string;
  description?: string;
}

interface PricingBreakdown {
  currency: string;
  items: PricingItem[];
  subtotal: number;
  taxes: number;
  total: number;
}

interface PricingItem {
  category: string;
  description: string;
  amount: number;
}

interface ProposalTerms {
  validUntil: Date;
  paymentSchedule: PaymentSchedule[];
  cancellationPolicy: string;
  inclusions: string[];
  exclusions: string[];
}

interface LostLeadAnalysis {
  leadId: string;
  conversionId?: string;

  // Loss details
  reason: LostReason;
  subReason?: string;
  details: string;

  // Competitor info
  competitor?: string;
  competitorPrice?: number;

  // Recovery
  winBackAttempts: WinBackAttempt[];
  recoverable: boolean;

  // Learning
  feedback: string;

  // Timestamp
  recordedAt: Date;
  recordedBy: string;
}

type LostReason =
  | 'price'
  | 'timing'
  | 'competitor'
  | 'no_response'
  | 'not_interested'
  | 'decided_not_to_travel'
  | 'other';

interface WinBackAttempt {
  attemptId: string;
  date: Date;
  method: CommunicationChannel;
  message: string;
  response?: string;
  successful: boolean;
}

interface ConversionMetrics {
  period: DateRange;

  // Funnel
  totalLeads: number;
  qualifiedLeads: number;
  proposalsSent: number;
  proposalsAccepted: number;
  bookingsCreated: number;

  // Rates
  qualificationRate: number; // % qualified
  proposalRate: number; // % proposals sent
  acceptanceRate: number; // % accepted
  conversionRate: number; // % converted

  // Time
  avgTimeToProposal: number; // Days
  avgTimeToConversion: number; // Days

  // Value
  avgProposalValue: number;
  avgConversionValue: number;
  totalRevenue: number;

  // Losses
  totalLost: number;
  lostReasons: Map<LostReason, number>;
}
```

---

## Open Problems

### 1. Price Transparency
**Challenge:** Online prices visible

**Options:** Value add, price match, exclusive deals

### 2. Long Sales Cycle
**Challenge:** Travel planning takes time

**Options:** Nurture campaigns, stay visible, build trust

### 3. No-Show Leads
**Challenge:** Disappear after proposal

**Options:** Follow-up automation, value content, different approach

### 4. Handoff Gaps
**Challenge:** Information lost in transition

**Options:** Structured handoff, documentation, shared systems

### 5. Attribution
**Challenge:** Who gets credit?

**Options:** Clear rules, shared credit, first/last touch

---

## Next Steps

1. Define conversion workflow
2. Build proposal system
3. Implement handoff process
4. Create analytics dashboard

---

**Status:** Research Phase — Conversion patterns unknown

**Last Updated:** 2026-04-27
