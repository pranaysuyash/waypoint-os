# Marketing Automation 02: Journeys

> Customer journey automation and multi-step campaigns

---

## Document Overview

**Focus:** Automated customer journeys
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Journey Design
- What is a customer journey?
- How do we map touchpoints?
- What are the key stages?
- How do we design for conversion?

### Automation Triggers
- What starts a journey?
- How do we handle branching?
- What about exit criteria?
- How do we handle re-entry?

### Journey Orchestration
- How do we coordinate channels?
- What about timing and pacing?
- How do we handle responses?
- What about real-time events?

### Journey Optimization
- How do we measure success?
- What about drop-off points?
- How do we A/B test journeys?
- What about continuous improvement?

---

## Research Areas

### A. Journey Types

**Acquisition Journeys:**

| Stage | Touchpoints | Research Needed |
|-------|-------------|-----------------|
| **Awareness** | Social ads, content | ? |
| **Interest** | Landing page, lead magnet | ? |
| **Consideration** | Email nurture, retargeting | ? |
| **Conversion** | Offer, urgency | ? |

**Nurture Journeys:**

| Stage | Touchpoints | Research Needed |
|-------|-------------|-----------------|
| **Welcome** | Onboarding series | ? |
| **Education** | Destination content | ? |
| **Engagement** | Surveys, preferences | ? |
| **Conversion** | Special offers | ? |

**Retention Journeys:**

| Stage | Touchpoints | Research Needed |
|-------|-------------|-----------------|
| **Post-booking** | Confirmation, documents | ? |
| **Pre-trip** | Prep, tips, cross-sell | ? |
| **During trip** | Support, updates | ? |
| **Post-trip** | Review, loyalty, next trip | ? |

**Win-Back Journeys:**

| Stage | Touchpoints | Research Needed |
|-------|-------------|-----------------|
| **Identification** | Inactivity trigger | ? |
| **Re-engagement** | We miss you, offers | ? |
| **Incentive** | Special discount | ? |
| **Closing** | Last chance | ? |

### B. Journey Triggers

**Entry Triggers:**

| Trigger | Type | Research Needed |
|---------|------|-----------------|
| **Newsletter signup** | Event | ? |
| **Lead captured** | Event | ? |
| **Booking made** | Event | ? |
| **Trip completed** | Event | ? |
| **Inactive 90 days** | Condition | ? |
| **Abandoned cart** | Event | ? |
| **Date based** | Schedule | ? |

**Branching Logic:**

| Condition | Branch | Research Needed |
|-----------|--------|-----------------|
| **Clicked email** | Send follow-up | ? |
| **Didn't click** | Alternative message | ? |
| **Opened but no click** | Different CTA | ? |
| **Converted** | Exit journey | ? |
| **Unsubscribed** | Exit journey | ? |

**Exit Criteria:**

| Criteria | Action | Research Needed |
|----------|--------|-----------------|
| **Conversion** | Move to retention | ? |
| **Unsubscribe** | Remove from journey | ? |
| **Max duration** | Exit or re-queue | ? |
| **No engagement** | Move to re-engagement | ? |

**Re-entry Rules:**

| Scenario | Re-entry | Research Needed |
|-----------|----------|-----------------|
| **Bounced** | Retry after cleanup | ? |
| **Unsubscribed** | No re-entry | ? |
| **Completed** | Restart after period | ? |
| **Exited** | Trigger-based restart | ? |

### C. Orchestration

**Channel Coordination:**

| Pattern | Description | Research Needed |
|---------|-------------|-----------------|
| **Email first** | Primary channel | ? |
| **SMS follow-up** | For non-openers | ? |
| **Push notification** | App users | ? |
| **Retargeting ad** | Social media | ? |
| **Direct mail** | High-value customers | ? |

**Timing Strategies:**

| Strategy | Use Case | Research Needed |
|----------|----------|-----------------|
| **Immediate** | Transactional | ? |
| **Same day** | Urgent offers | ? |
| **Daily** | Short campaigns | ? |
| **Every few days** | Nurture | ? |
| **Weekly** | Long nurture | ? |

**Response Handling:**

| Response | Next Action | Research Needed |
|----------|-------------|-----------------|
| **Click** | Send related content | ? |
| **Reply** | Route to human | ? |
| **Convert** | Exit journey | ? |
| **No response** | Continue journey | ? |
| **Unsubscribe** | Exit immediately | ? |

**Real-time Events:**

| Event | Impact | Research Needed |
|--------|--------|-----------------|
| **Website visit** | Trigger relevant journey | ? |
| **Search query** | Personalize next email | ? |
| **Price drop** | Send alert | ? |
| **Competitor action** | Counter-offer | ? |

### D. Journey Optimization

**Key Metrics:**

| Metric | Description | Research Needed |
|--------|-------------|-----------------|
| **Entry rate** | People entering journey | ? |
| **Completion rate** | Reach the end | ? |
| **Drop-off points** | Where they leave | ? |
| **Time to convert** | Journey duration | ? |
| **Revenue per journey** | Financial impact | ? |

**Funnel Analysis:**

| Stage | Metric | Benchmark | Research Needed |
|-------|--------|-----------|-----------------|
| **Email 1 sent** | 100% | — | ? |
| **Email 1 opened** | 25-30% | Industry | ? |
| **Email 1 clicked** | 3-5% | Industry | ? |
| **Converted** | 1-2% | Industry | ? |

**A/B Testing:**

| Test | Variants | Research Needed |
|------|---------|-----------------|
| **Journey flow** | Different sequences | ? |
| **Content** | Different messages | ? |
| **Timing** | Different delays | ? |
| **Channels** | Different mixes | ? |

**Continuous Improvement:**

| Tactic | Description | Research Needed |
|--------|-------------|-----------------|
| **Drop-off analysis** | Fix weak points | ? |
| **Content refresh** | Update regularly | ? |
| **Segment refinement** | Better targeting | ? |
| **Personalization** | More relevant | ? |

---

## Data Model Sketch

```typescript
interface CustomerJourney {
  journeyId: string;
  name: string;
  type: JourneyType;

  // Entry
  entryTrigger: JourneyTrigger;

  // Steps
  steps: JourneyStep[];

  // Settings
  status: JourneyStatus;
  priority: number;

  // Limits
  maxDuration?: number; // Days
  maxReentries?: number;

  // Metrics
  enrolled: number;
  active: number;
  completed: number;
  converted: number;
}

type JourneyType =
  | 'acquisition'
  | 'nurture'
  | 'retention'
  | 'win_back'
  | 'transactional';

interface JourneyTrigger {
  type: TriggerType;
  event?: string;
  condition?: TriggerCondition;
  schedule?: ScheduleConfig;
}

type TriggerType = 'event' | 'condition' | 'schedule';

interface JourneyStep {
  stepId: string;
  order: number;

  // Timing
  delay: number; // Minutes from previous or entry
  delayType: 'relative' | 'absolute';
  scheduledTime?: TimeOfDay;

  // Action
  action: StepAction;

  // Branching
  nextStep?: string;
  branches?: StepBranch[];

  // Conditions
  conditions?: StepCondition[];
}

interface StepAction {
  type: ActionType;
  channel?: CommunicationChannel;
  templateId?: string;
  content?: any;
  parameters?: Record<string, any>;
}

type ActionType =
  | 'send_email'
  | 'send_sms'
  | 'send_whatsapp'
  | 'send_push'
  | 'wait'
  | 'check_condition'
  | 'update_field'
  | 'create_task';

interface StepBranch {
  condition: StepCondition;
  nextStep: string;
}

interface StepCondition {
  field: string;
  operator: ComparisonOperator;
  value: any;
  logicalOperator?: 'AND' | 'OR';
}

interface JourneyEnrollment {
  enrollmentId: string;
  journeyId: string;
  customerId: string;

  // State
  currentStep: string;
  status: EnrollmentStatus;

  // Timing
  enrolledAt: Date;
  currentStepStartedAt: Date;
  nextStepScheduledAt?: Date;
  completedAt?: Date;
  exitedAt?: Date;

  // Events
  events: JourneyEvent[];

  // Context
  data: Record<string, any>;
}

type EnrollmentStatus =
  | 'active'
  | 'paused'
  | 'completed'
  | 'exited'
  | 'failed';

interface JourneyEvent {
  eventId: string;
  enrollmentId: string;
  type: EventType;
  timestamp: Date;
  data?: Record<string, any>;
}

type EventType =
  | 'enrolled'
  | 'step_started'
  | 'step_completed'
  | 'email_sent'
  | 'email_opened'
  | 'email_clicked'
  | 'converted'
  | 'exited';

interface JourneyMetrics {
  journeyId: string;
  period: DateRange;

  // Funnel
  enrolled: number;
  active: number;
  completed: number;
  exited: number;

  // By step
  stepMetrics: Map<string, StepMetrics>;

  // Conversion
  conversions: number;
  conversionRate: number;
  revenue: number;

  // Engagement
  opens: number;
  clicks: number;
  openRate: number;
  clickRate: number;

  // Time
  avgDuration: number;
  medianDuration: number;
}

interface StepMetrics {
  stepId: string;
  reached: number;
  completed: number;
  droppedOff: number;
  completionRate: number;
}
```

---

## Open Problems

### 1. Journey Complexity
**Challenge:** Complex journeys are hard to manage

**Options:** Visual builder, templates, testing

### 2. Over-Communication
**Challenge:** Too many messages across journeys

**Options:** Suppression rules, frequency caps, master calendar

### 3. Real-Time Coordination
**Challenge:** Events happen in real-time

**Options:** Event streaming, queue processing, webhooks

### 4. Attribution
**Challenge:** Which journey caused conversion?

**Options:** Multi-touch attribution, journey tagging, first/last touch

### 5. Maintenance
**Challenge:** Journeys need ongoing care

**Options:** Alerts, performance monitoring, regular reviews

---

## Next Steps

1. Define journey templates
2. Build journey builder UI
3. Implement trigger system
4. Create journey analytics

---

**Status:** Research Phase — Journey patterns unknown

**Last Updated:** 2026-04-28
