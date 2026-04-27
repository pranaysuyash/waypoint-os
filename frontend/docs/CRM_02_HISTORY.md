# Customer Relationship Management 02: History

> Booking history, interactions, and customer journey

---

## Document Overview

**Focus:** Customer history tracking
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Booking History
- What booking data do we track?
- How do we organize past trips?
- What about cancelled bookings?
- How do we show history to customers?

### Interaction History
- What interactions do we record?
- How do we track communications?
- What about multi-channel history?
- How do we handle service issues?

### Journey Mapping
- How do we map customer journeys?
- What touchpoints matter?
- How do we identify patterns?
- What about cross-sell opportunities?

### Analytics & Insights
- What insights can we derive?
- How do we predict behavior?
- What about churn risk?
- How do we identify upsell opportunities?

---

## Research Areas

### A. Booking History

**Trip Records:**

| Data | Purpose | Research Needed |
|------|---------|-----------------|
| **Destination** | Travel patterns | ? |
| **Dates** | Seasonality | ? |
| **Companions** | Social connections | ? |
| **Spend** | Value segmentation | ? |
| **Services** | Product usage | ? |

**History Display:**

| View | Content | Research Needed |
|------|---------|-----------------|
| **Timeline** | Chronological trips | ? |
| **Map** | Geographic visualization | ? |
| **Stats** | Summary metrics | ? |
| **Documents** | Past bookings, tickets | ? |

**Status Tracking:**

| Status | Display | Research Needed |
|--------|---------|-----------------|
| **Completed** | Full trip details | ? |
| **Cancelled** | Reason, refund | ? |
| **Upcoming** | Countdown, prep | ? |
| **In planning** | Progress | ? |

**Trip Memories:**

| Content | Capture | Research Needed |
|---------|----------|-----------------|
| **Photos** | Upload, auto-import | ? |
| **Reviews** | Post-trip feedback | ? |
| **Stories** | Trip narrative | ? |
| **Recommendations** | What they loved | ? |

### B. Interaction History

**Interaction Types:**

| Type | Tracked | Research Needed |
|------|---------|-----------------|
| **Calls** | Inbound, outbound | ? |
| **Emails** | Sent, received | ? |
| **WhatsApp** | Conversations | ? |
| **Meetings** | In-person | ? |
| **Support tickets** | Issues, resolutions | ? |
| **Web activity** | Page views, clicks | ? |

**Channel Unification:**

| Challenge | Solution | Research Needed |
|-----------|----------|-----------------|
| **Multiple platforms** | Unified timeline | ? |
| **Different formats** | Standardized display | ? |
| **Thread tracking** | Conversation linking | ? |
| **Agent attribution** | Who did what | ? |

**Sentiment Analysis:**

| Signal | Sentiment | Research Needed |
|--------|----------|-----------------|
| **Language** | Positive/negative words | ? |
| **Tone** | Formal/casual, urgent | ? |
| **Emoji** | Emotional state | ? |
| **Response time** | Satisfaction proxy | ? |

**Issue Tracking:**

| Issue | Details Tracked | Research Needed |
|-------|-----------------|-----------------|
| **Complaints** | Problem, resolution, satisfaction | ? |
| **Disruptions** | Flight delays, cancellations | ? |
| **Special requests** | Fulfilled, missed | ? |
| **Service failures** | Root cause, prevention | ? |

### C. Customer Journey

**Journey Stages:**

| Stage | Touchpoints | Research Needed |
|-------|-------------|-----------------|
| **Awareness** | Ads, referrals, social | ? |
| **Consideration** | Website, reviews, quotes | ? |
| **Booking** | Forms, calls, payments | ? |
| **Pre-trip** | Documents, updates | ? |
| **Travel** | Support, notifications | ? |
| **Post-trip** | Reviews, feedback | ? |

**Journey Mapping:**

| Element | Description | Research Needed |
|---------|-------------|-----------------|
| **Touchpoints** | All interactions | ? |
| **Channels** | Where they happen | ? |
| **Emotions** | How customer feels | ? |
| **Pain points** | Where they struggle | ? |
| **Opportunities** | Where to improve | ? |

**Path Analysis:**

| Path | Frequency | Research Needed |
|------|-----------|-----------------|
| **Direct booking** | Website → book | ? |
| **Assisted** | Call → quote → book | ? |
| **Complex** | Multiple visits, quotes | ? |
| **Repeat** | Logged in → book | ? |

### D. Predictive Insights

**Churn Risk:**

| Indicator | Weight | Research Needed |
|-----------|--------|-----------------|
| **Inactivity** | High | ? |
| **Competitor use** | High | ? |
| **Complaints** | Medium | ? |
| **Price sensitivity** | Medium | ? |

**Upsell Opportunities:**

| Signal | Action | Research Needed |
|--------|--------|-----------------|
| **Family growth** | Family products | ? |
| **Income increase** | Premium options | ? |
| **New destination** | Related services | ? |
| **Seasonal pattern** | Timely offers | ? |

**Lifetime Value Prediction:**

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Past spend** | High | ? |
| **Booking frequency** | High | ? |
| **Referral behavior** | Medium | ? |
| **Loyalty program** | Medium | ? |

---

## Data Model Sketch

```typescript
interface CustomerHistory {
  customerId: string;

  // Bookings
  bookings: BookingHistoryItem[];
  totalBookings: number;
  totalSpent: number;

  // Interactions
  interactions: InteractionHistoryItem[];

  // Metrics
  firstBookingAt?: Date;
  lastBookingAt?: Date;
  lastInteractionAt?: Date;

  // Insights
  churnRisk: ChurnRisk;
  lifetimeValue: number;
  predictedLifetimeValue: number;
}

interface BookingHistoryItem {
  bookingId: string;
  customerId: string;

  // Trip details
  destination: string;
  startDate: Date;
  endDate: Date;

  // Value
  totalAmount: number;
  commissionEarned: number;

  // Components
  components: ComponentSummary[];

  // Companions
  travelers: string[]; // Customer IDs

  // Status
  status: BookingHistoryStatus;

  // Experience
  rating?: number;
  review?: string;
  issues?: ServiceIssue[];

  // Timestamp
  bookedAt: Date;
}

type BookingHistoryStatus =
  | 'completed'
  | 'cancelled'
  | 'upcoming'
  | 'no_show';

interface InteractionHistoryItem {
  interactionId: string;
  customerId: string;

  // Type
  type: InteractionType;
  channel: CommunicationChannel;
  direction: 'inbound' | 'outbound';

  // Content
  subject?: string;
  content?: string;
  attachments?: string[];

  // Participants
  agent?: string;
  otherParticipants?: string[];

  // Metadata
  timestamp: Date;
  duration?: number; // Seconds/minutes

  // Sentiment
  sentiment?: SentimentScore;
  tags?: string[];

  // Related
  bookingId?: string;
  ticketId?: string;
}

type InteractionType =
  | 'call'
  | 'email'
  | 'whatsapp'
  | 'sms'
  | 'meeting'
  | 'support';

interface SentimentScore {
  score: number; // -1 to 1
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
}

interface ServiceIssue {
  issueId: string;
  type: IssueType;
  severity: 'low' | 'medium' | 'high';
  description: string;

  // Resolution
  resolved: boolean;
  resolvedAt?: Date;
  resolution?: string;
  compensation?: Compensation;

  // Impact
  customerSatisfaction?: number; // 1-5
}

type IssueType =
  | 'flight_delay'
  | 'cancellation'
  | 'booking_error'
  | 'quality_issue'
  | 'communication'
  | 'other';

interface Compensation {
  type: 'refund' | 'voucher' | 'upgrade' | 'other';
  amount?: number;
  description: string;
}

interface CustomerJourney {
  journeyId: string;
  customerId: string;
  bookingId?: string;

  // Stages
  stages: JourneyStage[];

  // Timeline
  startedAt: Date;
  completedAt?: Date;
  duration?: number; // Days

  // Outcome
  converted: boolean;
  value?: number;
}

interface JourneyStage {
  stage: JourneyStageType;
  enteredAt: Date;
  exitedAt?: Date;
  touchpoints: Touchpoint[];

  // Experience
  satisfaction?: number;
  friction?: FrictionPoint[];
}

type JourneyStageType =
  | 'awareness'
  | 'consideration'
  | 'booking'
  | 'pre_trip'
  | 'travel'
  | 'post_trip';

interface Touchpoint {
  type: string;
  channel: CommunicationChannel;
  timestamp: Date;
  metadata?: Record<string, any>;
}

interface FrictionPoint {
  description: string;
  severity: 'low' | 'medium' | 'high';
  impact: string;
}

interface CustomerInsights {
  customerId: string;
  generatedAt: Date;

  // Churn
  churnRisk: ChurnRisk;
  churnFactors: ChurnFactor[];

  // Value
  lifetimeValue: number;
  predictedLifetimeValue: number;
  valueTier: ValueTier;

  // Opportunities
  upsellOpportunities: UpsellOpportunity[];
  crossSellOpportunities: CrossSellOpportunity[];

  // Preferences (inferred)
  inferredPreferences: InferredPreference[];

  // Next best action
  nextBestAction: NextBestAction;
}

type ChurnRisk = 'low' | 'medium' | 'high';

interface ChurnFactor {
  factor: string;
  impact: number;
  description: string;
}

type ValueTier = 'bronze' | 'silver' | 'gold' | 'platinum';

interface UpsellOpportunity {
  product: string;
  likelihood: number;
  reason: string;
  suggestedOffer?: string;
}

interface CrossSellOpportunity {
  product: string;
  likelihood: number;
  reason: string;
}

interface InferredPreference {
  preference: string;
  confidence: number;
  source: string;
}

interface NextBestAction {
  action: string;
  priority: number;
  expectedValue: number;
  channel: CommunicationChannel;
}
```

---

## Open Problems

### 1. Data Volume
**Challenge:** History grows large

**Options:** Summarization, archival, smart querying

### 2. Cross-Channel Linking
**Challenge:** Connecting disparate interactions

**Options:** Customer IDs, cookies, probabilistic matching

### 3. Privacy
**Challenge:** Storing sensitive history

**Options:** Retention policies, anonymization, access controls

### 4. Accuracy
**Challenge:** Inferred insights may be wrong

**Options:** Human review, feedback, confidence scoring

### 5. Actionability
**Challenge:** Insights not used

**Options:** Integration with workflows, alerts, recommendations

---

## Next Steps

1. Define history schema
2. Build interaction tracking
3. Implement journey mapping
4. Create insights engine

---

**Status:** Research Phase — History patterns unknown

**Last Updated:** 2026-04-27
