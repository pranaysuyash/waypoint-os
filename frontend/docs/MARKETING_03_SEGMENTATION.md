# Marketing Automation 03: Segmentation

> Audience targeting, list management, and dynamic segmentation

---

## Document Overview

**Focus:** Customer segmentation and targeting
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Segment Types
- How do we segment customers?
- What are the most valuable segments?
- How do we handle dynamic segments?
- What about lookalike audiences?

### Building Segments
- How do users create segments?
- What criteria are available?
- How do we handle complex logic?
- What about preview and testing?

### List Management
- How do we manage email lists?
- What about hygiene and maintenance?
- How do we handle unsubscribes?
- What about compliance?

### Personalization
- How do we personalize for segments?
- What data powers personalization?
- How do we handle dynamic content?
| What about recommendations?

---

## Research Areas

### A. Segment Types

**Demographic Segments:**

| Segment | Criteria | Use Case | Research Needed |
|---------|----------|----------|-----------------|
| **Age-based** | Age ranges | Family vs adventure | ? |
| **Location** | Geography | Local promotions | ? |
| **Family status** | Single, couple, family | Relevant offers | ? |
| **Income** | Spending power | Premium vs budget | ? |

**Behavioral Segments:**

| Segment | Criteria | Use Case | Research Needed |
|---------|----------|----------|-----------------|
| **Active** | Recent activity | Cross-sell | ? |
| **Inactive** | No recent activity | Re-engagement | ? |
| **Frequent travelers** | High booking rate | Loyalty | ? |
| **Big spenders** | High value | VIP treatment | ? |
| **Deal seekers** | Discount users | Promotions | ? |

**Lifecycle Segments:**

| Segment | Criteria | Use Case | Research Needed |
|---------|----------|----------|-----------------|
| **New** | First-time customers | Onboarding | ? |
| **Nurture** | Not yet purchased | Education | ? |
| **Active** | Regular customers | Retention | ? |
| **At-risk** | Declining activity | Win-back | ? |
| **Churned** | Left | Recovery | ? |

**Interest-Based Segments:**

| Segment | Criteria | Use Case | Research Needed |
|---------|----------|----------|-----------------|
| **Beach lovers** | Beach destinations | Sun & sand offers | ? |
| **Adventure seekers** | Activity trips | Adventure promotions | ? |
| **Luxury travelers** | Premium bookings | Luxury offers | ? |
| **Family travelers** | Family bookings | Family packages | ? |
| **Business travelers** | Work trips | Corporate offers | ? |

### B. Building Segments

**Segment Builder:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Rule builder** | Drag-and-drop rules | ? |
| **Combine conditions** | AND/OR logic | ? |
| **Nested groups** | Complex logic | ? |
| **Save & reuse** | Template segments | ? |
| **Preview** | See who matches | ? |

**Segment Criteria:**

| Category | Criteria | Research Needed |
|----------|----------|-----------------|
| **Booking** | Past destinations, spend, dates | ? |
| **Behavior** | Opens, clicks, visits | ? |
| **Profile** | Demographics, preferences | ? |
| **Engagement** | Last activity, frequency | ? |
| **Custom** | Any data field | ? |

**Dynamic vs. Static:**

| Type | Description | Use Case | Research Needed |
|------|-------------|----------|-----------------|
| **Dynamic** | Real-time membership | Always-current lists | ? |
| **Static** | Snapshot | One-time campaigns | ? |
| **Hybrid** | Dynamic with exclusions | Most campaigns | ? |

**Segment Operations:**

| Operation | Description | Research Needed |
|-----------|-------------|-----------------|
| **Union** | Combine segments | ? |
| **Intersection** | Common members | ? |
| **Exclusion** | Remove members | ? |
| **Difference** | Not in other | ? |

### C. List Management

**List Hygiene:**

| Task | Frequency | Research Needed |
|------|-----------|-----------------|
| **Remove bounces** | After each send | ? |
| **Remove unsubscribes** | Immediate | ? |
| **Remove duplicates** | Regular | ? |
| **Validate emails** | Quarterly | ? |
| **Remove inactives** | Annually | ? |

**Compliance:**

| Requirement | Implementation | Research Needed |
|-------------|----------------|-----------------|
| **Opt-in** | Confirmed subscription | ? |
| **Opt-out** | Easy unsubscribe | ? |
| **Double opt-in** | Verification step | ? |
| **GDPR rights** | Access, delete, port | ? |
| **Consent tracking** | Record management | ? |

**List Growth:**

| Source | Strategy | Research Needed |
|--------|----------|-----------------|
| **Website** | Popups, embedded forms | ? |
| **Social** | Contests, lead magnets | ? |
| **Referrals** | Forward to friend | ? |
| **Partners** | Co-registration | ? |
| **Events** | In-person sign-up | ? |

### D. Personalization

**Content Personalization:**

| Element | Data Source | Research Needed |
|---------|-------------|-----------------|
| **Name** | Profile | ? |
| **Destination** | History, wishlist | ? |
| **Travel dates** | Past bookings | ? |
| **Budget** | Past spend | ? |
| **Preferences** | Profile | ? |

**Dynamic Content Blocks:**

| Block | Personalizes | Research Needed |
|-------|--------------|-----------------|
| **Hero image** | Destination interest | ? |
| **Product offers** | Past bookings | ? |
| **Recommendations** | Collaborative filtering | ? |
| **Pricing** | Budget segment | ? |
| **CTA text** | Journey stage | ? |

**Recommendation Engine:**

| Type | Algorithm | Research Needed |
|------|-----------|-----------------|
| **Collaborative** | Similar customers | ? |
| **Content-based** | Similar items | ? |
| **Hybrid** | Combined | ? |
| **Knowledge-based** | Rules | ? |
| **Trending** | Popular | ? |

---

## Data Model Sketch

```typescript
interface Segment {
  segmentId: string;
  name: string;
  description?: string;

  // Definition
  type: SegmentType;
  rules: SegmentRule[];

  // Membership
  dynamic: boolean;
  memberIds?: string[]; // For static
  estimatedSize?: number; // For dynamic

  // Usage
  usedIn: string[]; // Campaign IDs, journey IDs

  // Status
  active: boolean;
  lastRefreshed?: Date;
  refreshedBy?: string;
}

type SegmentType =
  | 'demographic'
  | 'behavioral'
  | 'lifecycle'
  | 'interest_based'
  | 'custom';

interface SegmentRule {
  ruleId: string;
  field: string;
  operator: SegmentOperator;
  value: any;
  logicalOperator?: 'AND' | 'OR';
  nestedRules?: SegmentRule[];
}

type SegmentOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'contains'
  | 'not_contains'
  | 'starts_with'
  | 'ends_with'
  | 'in'
  | 'not_in'
  | 'is_null'
  | 'is_not_null'
  | 'between'
  | 'in_last'
  | 'not_in_last';

interface SegmentMembership {
  segmentId: string;
  customerId: string;

  // Timing
  addedAt: Date;
  addedBy: string; // System or user
  removedAt?: Date;

  // Reason
  matchScore?: number; // How well they match
  matchingRules?: string[]; // Which rules matched
}

interface EmailList {
  listId: string;
  name: string;

  // Composition
  sourceSegments: string[];
  excludedSegments: string[];

  // Members
  totalSubscribers: number;
  activeSubscribers: number;
  unsubscribes: number;
  bounces: number;

  // Health
  healthScore: number; // 0-100
  lastCleaned?: Date;

  // Settings
  doubleOptIn: boolean;
  welcomeFlow?: string; // Journey ID
}

interface ListMember {
  listId: string;
  customerId: string;
  email: string;

  // Status
  status: MemberStatus;

  // Timestamps
  addedAt: Date;
  removedAt?: Date;

  // Source
  source: string;
  sourceDetails?: string;
}

type MemberStatus =
  | 'subscribed'
  | 'unsubscribed'
  | 'bounced'
  | 'complained';

interface PersonalizationRule {
  ruleId: string;
  name: string;

  // Trigger
  trigger: PersonalizationTrigger;

  // Content
  contentBlock: string; // Template block ID
  fallback: string;

  // Priority
  priority: number;

  // Conditions
  conditions: SegmentRule[];
}

interface PersonalizationTrigger {
  type: 'field' | 'recommendation' | 'calculation';
  field?: string;
  algorithm?: RecommendationAlgorithm;
}

type RecommendationAlgorithm =
  | 'collaborative_filtering'
  | 'content_based'
  | 'trending'
  | 'similar_customers'
  | 'recently_viewed';

interface PersonalizationContext {
  customerId: string;

  // Data available
  profile: CustomerProfile;
  history: BookingHistory[];
  behavior: BehaviorData[];

  // Calculated
  recommendations: Recommendation[];
  predictions: Prediction[];
}

interface Recommendation {
  type: 'destination' | 'hotel' | 'activity' | 'package';
  itemId: string;
  name: string;
  score: number;
  reason: string;
}

interface Prediction {
  type: 'next_destination' | 'budget' | 'timing' | 'churn_risk';
  value: any;
  confidence: number;
}
```

---

## Open Problems

### 1. Segment Accuracy
**Challenge:** Rules don't capture intent

**Options:** ML-based segments, feedback loops, refinement

### 2. Real-Time Updates
**Challenge:** Dynamic segments are slow

**Options:** Caching, incremental updates, streaming

### 3. Over-Personalization
**Challenge:** Creepy factor

**Options:** Transparency, controls, subtlety

### 4. Cold Start
**Challenge:** New customers have no data

**Options:** Defaults, progressive profiling, ask

### 5. List Fatigue
**Challenge:** Same people in every segment

**Options:** Frequency caps, rotation, exclusions

---

## Next Steps

1. Define segment builder
2. Implement dynamic segmentation
3. Create personalization engine
4. Build recommendation system

---

**Status:** Research Phase — Segmentation patterns unknown

**Last Updated:** 2026-04-28
