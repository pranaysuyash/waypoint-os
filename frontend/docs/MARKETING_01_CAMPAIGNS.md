# Marketing Automation 01: Campaigns

> Email campaigns, promotions, and marketing outreach

---

## Document Overview

**Focus:** Marketing campaign management
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Campaign Types
- What types of campaigns do we run?
- How do we structure promotions?
- What about seasonal campaigns?
- How do we handle flash sales?

### Campaign Design
- What makes an effective campaign?
- How do we design for conversion?
- What about subject lines and copy?
- How do we incorporate visuals?

### Targeting
- Who do we target?
- How do we build lists?
- What about exclusions?
- How do we avoid spamming?

### Execution
- How do we schedule campaigns?
- What about send times?
- How do we handle responses?
- What about A/B testing?

---

## Research Areas

### A. Campaign Types

**Promotional Campaigns:**

| Type | Purpose | Timing | Research Needed |
|------|---------|--------|-----------------|
| **Flash sale** | Urgent bookings | 24-48 hours | ? |
| **Seasonal** | Holiday/peak travel | Weeks ahead | ? |
| **Last-minute** | Fill inventory | Days before | ? |
| **Early bird** | Advance bookings | Months ahead | ? |
| **Clearance** | Off-peak promotion | Shoulder season | ? |

**Newsletter Campaigns:**

| Type | Content | Frequency | Research Needed |
|------|---------|-----------|-----------------|
| **Weekly deals** | Current offers | Weekly | ? |
| **Destination focus** | Spotlight | Monthly | ? |
| **Travel tips** | Educational | Monthly | ? |
| **Customer stories** | Social proof | Quarterly | ? |
| **Company news** | Updates | Quarterly | ? |

**Triggered Campaigns:**

| Trigger | Campaign | Research Needed |
|---------|----------|-----------------|
| **Welcome** | New subscriber | ? |
| **Abandoned cart** | Incomplete booking | ? |
| **Post-purchase** | Cross-sell | ? |
| **Post-trip** | Review request | ? |
| **Re-engagement** | Inactive | ? |
| **Birthday** | Special offer | ? |

### B. Campaign Design

**Email Structure:**

| Element | Best Practice | Research Needed |
|---------|---------------|-----------------|
| **Subject line** | 40-50 chars, urgent | ? |
| **Preheader** | Complement subject | ? |
| **Header** | Brand + clear purpose | ? |
| **Hero** | Main offer/image | ? |
| **Body** | Scannable, benefits | ? |
| **CTA** | Clear, action-oriented | ? |
| **Footer** | Legal, unsubscribe | ? |

**Copy Guidelines:**

| Principle | Example | Research Needed |
|-----------|---------|-----------------|
| **Benefit-first** | "Escape to paradise" not "Book now" | ? |
| **Urgency** | "Ends midnight" not "Limited time" | ? |
| **Specific** | "Save ₹5,000" not "Great savings" | ? |
| **Personal** | "Your summer escape" not "Summer sale" | ? |

**Visual Design:**

| Element | Guidance | Research Needed |
|---------|----------|-----------------|
| **Images** | High quality, alt text | ? |
| **Colors** | On-brand, accessible | ? |
| **Layout** | Mobile-responsive | ? |
| **Typography** | Readable, hierarchical | ? |
| **CTA buttons** | Contrasting, clear | ? |

### C. Audience Targeting

**List Building:**

| Source | Description | Research Needed |
|--------|-------------|-----------------|
| **Customers** | Past bookers | ? |
| **Leads** | Not yet booked | ? |
| **Newsletter** | Subscribers | ? |
| **Partners** | Partner audiences | ? |
| **Purchased** | Third-party lists | ? |

**Targeting Criteria:**

| Criterion | Use | Research Needed |
|-----------|-----|-----------------|
| **Past destination** | Similar offers | ? |
| **Budget range** | Appropriate products | ? |
| **Travel dates** | Seasonal relevance | ? |
| **Family status** | Family offers | ? |
| **Engagement** | Active vs inactive | ? |

**Exclusion Rules:**

| Exclude | Reason | Research Needed |
|---------|--------|-----------------|
| **Recent bookings** | Already purchased | ? |
| **Opted out** | Legal/compliance | ? |
| **Unsubscribed** | Respect preference | ? |
| **Bounced** | Invalid email | ? |
| **Complained** | Spam reports | ? |

### D. Campaign Execution

**Send Time Optimization:**

| Factor | Best Time | Research Needed |
|--------|-----------|-----------------|
| **Day of week** | Tue-Thu for B2B | ? |
| **Time of day** | 9-11 AM, 2-4 PM | ? |
| **Timezone** | Recipient's local | ? |
| **Industry** | Travel-specific patterns | ? |

**A/B Testing:**

| Test | Variants | Metric | Research Needed |
|------|---------|--------|-----------------|
| **Subject line** | 2-3 options | Open rate | ? |
| **From name** | Brand vs person | Open rate | ? |
| **Content** | Different copy | Click rate | ? |
| **CTA** | Button vs text | Click rate | ? |
| **Send time** | Morning vs evening | Open rate | ? |
| **Images** | With vs without | Engagement | ? |

**Response Handling:**

| Response | Action | Research Needed |
|----------|--------|-----------------|
| **Click** | Track, retarget | ? |
| **Reply** | Route to agent | ? |
| **Unsubscribe** | Process immediately | ? |
| **Bounce** | Clean list | ? |
| **Complaint** | Investigate | ? |

**Campaign Workflow:**

```
1. Plan
   → Define goals, audience, offer

2. Design
   → Create content, visuals

3. Test
   → A/B variants, preview

4. Schedule
   → Set send time

5. Send
   → Execute campaign

6. Monitor
   → Track real-time metrics

7. Analyze
   → Report, learn, optimize
```

---

## Data Model Sketch

```typescript
interface MarketingCampaign {
  campaignId: string;
  name: string;
  type: CampaignType;

  // Goals
  goals: CampaignGoals;

  // Audience
  segmentIds: string[];
  excludeSegmentIds?: string[];
  estimatedRecipients: number;

  // Content
  subject: string;
  preheader?: string;
  templateId?: string;
  content: CampaignContent;

  // Schedule
  scheduledAt: Date;
  sentAt?: Date;
  timezone?: string;

  // Testing
  abTest?: ABTestConfig;

  // Status
  status: CampaignStatus;

  // Results
  metrics?: CampaignMetrics;
}

type CampaignType =
  | 'promotional'
  | 'newsletter'
  | 'triggered'
  | 'transactional'
  | 'announcement';

interface CampaignGoals {
  primary: GoalType;
  targetValue: number;
  secondary?: GoalType[];
}

type GoalType = 'bookings' | 'revenue' | 'leads' | 'clicks' | 'opens';

interface CampaignContent {
  html: string;
  text?: string;
  ampHtml?: string;

  // Assets
  images: CampaignImage[];
  links: CampaignLink[];

  // Personalization
  variables: ContentVariable[];
}

interface CampaignImage {
  url: string;
  alt: string;
  width?: number;
  height?: number;
}

interface CampaignLink {
  url: string;
  trackingUrl: string;
  label: string;
  utmParameters?: UTMParameters;
}

interface ABTestConfig {
  variants: ABVariant[];
  splitPercentage: number; // Per variant
  winnerCriteria: ABTestMetric;
  testDuration?: number; // Hours
}

interface ABVariant {
  variantId: string;
  name: string;
  changes: VariantChange[];
}

interface VariantChange {
  field: string; // subject, fromName, content, etc.
  value: any;
}

type ABTestMetric = 'open_rate' | 'click_rate' | 'conversion_rate';

type CampaignStatus =
  | 'draft'
  | 'scheduled'
  | 'sending'
  | 'sent'
  | 'paused'
  | 'cancelled';

interface CampaignMetrics {
  // Delivery
  sent: number;
  delivered: number;
  bounced: number;
  complaints: number;

  // Engagement
  opens: number;
  uniqueOpens: number;
  openRate: number;
  clicks: number;
  uniqueClicks: number;
  clickRate: number;
  clickToOpenRate: number;

  // Conversion
  conversions: number;
  conversionRate: number;
  revenue: number;
  bookings: number;

  // Unsubscribes
  unsubscribes: number;
  unsubscribeRate: number;
}

interface CampaignResponse {
  responseId: string;
  campaignId: string;
  recipientId: string;

  // Tracking
  sentAt: Date;
  deliveredAt?: Date;
  openedAt?: Date;
  clickedAt?: Date;
  convertedAt?: Date;

  // Actions
  clicks: LinkClick[];
  reply?: string;

  // Outcome
  status: ResponseStatus;
}

interface LinkClick {
  url: string;
  clickedAt: Date;
  count: number;
}

type ResponseStatus =
  | 'sent'
  | 'delivered'
  | 'opened'
  | 'clicked'
  | 'converted'
  | 'bounced'
  | 'complained'
  | 'unsubscribed';
```

---

## Open Problems

### 1. Deliverability
**Challenge:** Emails go to spam

**Options:** Authentication, reputation management, list hygiene

### 2. Open Rates Declining
**Challenge:** Lower engagement over time

**Options:** Better subject lines, frequency management, list cleaning

### 3. Attribution
**Challenge:** Multi-touch conversions

**Options:** Last-touch, first-touch, multi-touch models

### 4. Content Fatigue
**Challenge:** Same content, different day

**Options:** Content calendar, variety, creativity

### 5. Mobile Optimization
**Challenge:** Many mobile users

**Options:** Responsive design, mobile-first copy, testing

---

## Next Steps

1. Define campaign templates
2. Build campaign builder
3. Implement A/B testing
4. Create reporting dashboard

---

**Status:** Research Phase — Campaign patterns unknown

**Last Updated:** 2026-04-28
