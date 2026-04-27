# Help Desk & Ticketing 03: SLA

> Service level agreements and performance tracking

---

## Document Overview

**Focus:** SLA management and compliance
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### SLA Definition
- What are our service levels?
- How do we define response times?
- What about resolution targets?
- How do we handle different priorities?

### SLA Tracking
- How do we track SLA compliance?
- What about breach warnings?
- How do we measure performance?
- What about reporting?

### SLA Configuration
- How do we set up SLAs?
- What about customer-specific SLAs?
- How do we handle business hours?
- What about holidays?

### Performance Management
- How do we improve SLA performance?
- What about agent productivity?
- How do we handle chronic breaches?
- What about capacity planning?

---

## Research Areas

### A. SLA Definitions

**Response Time Targets:**

| Priority | Initial Response | Update Frequency | Resolution | Research Needed |
|----------|-----------------|------------------|------------|-----------------|
| **Critical** | 15 min | Every 30 min | 4 hours | ? |
| **High** | 1 hour | Every 2 hours | 8 hours | ? |
| **Medium** | 4 hours | Daily | 24 hours | ? |
| **Low** | 24 hours | Every 2 days | 72 hours | ? |

**Resolution Targets:**

| Category | Target | Research Needed |
|----------|--------|-----------------|
| **Simple inquiry** | First contact resolved | ? |
| **Booking change** | 24 hours | ? |
| **Refund request** | 48 hours | ? |
| **Technical issue** | Depends on complexity | ? |
| **Complaint** | 48 hours with acknowledgment | ? |

**Customer-Specific SLAs:**

| Customer Tier | Response Time | Resolution Time | Research Needed |
|---------------|--------------|----------------|-----------------|
| **VIP** | Immediate | Priority handling | ? |
| **Corporate** | 1 hour | 4 hours | ? |
| **Regular** | Standard | Standard | ? |
| **Basic** | 24 hours | Best effort | ? |

**Calendar Rules:**

| Rule | Configuration | Research Needed |
|------|--------------|-----------------|
| **Business hours** | 9 AM - 6 PM IST | ? |
| **Working days** | Mon-Sat | ? |
| **Holidays** | National holidays | ? |
| **Timezones** | Customer's timezone | ? |

### B. SLA Tracking

**Breach Stages:**

| Stage | Threshold | Action | Research Needed |
|-------|-----------|--------|-----------------|
| **On track** | < 50% of SLA used | None | ? |
| **Warning** | 50-75% of SLA used | Notify agent | ? |
| **At risk** | 75-90% of SLA used | Notify + escalate | ? |
| **Critical** | > 90% of SLA used | Alert manager | ? |
| **Breached** | SLA exceeded | Incident report | ? |

**SLA Calculations:**

| Factor | Handling | Research Needed |
|--------|----------|-----------------|
| **Business hours only** | Count only working hours | ? |
| **Weekends** | Exclude if business hours | ? |
| **Holidays** | Exclude | ? |
| **Timezone** | Convert to customer's | ? |
| **Pause** | Customer response pauses clock | ? |

**Pause Triggers:**

| Trigger | Pause | Resume | Research Needed |
|---------|-------|--------|-----------------|
| **Customer reply** | On reply | After our response | ? |
| **Waiting customer** | On request | On information received | ? |
| **External dependency** | On waiting | On response | ? |
| **Agent assigned** | Never | — | ? |

**Metrics:**

| Metric | Calculation | Research Needed |
|--------|-------------|-----------------|
| **SLA compliance** | % within SLA | ? |
| **Avg response time** | Mean first response | ? |
| **Avg resolution time** | Mean resolution | ? |
| **Breaches** | Count, % | ? |
| **Breach rate** | % breached | ? |

### C. SLA Configuration

**SLA Policies:**

| Policy | Configuration | Research Needed |
|---------|--------------|-----------------|
| **Default SLA** | Standard service levels | ? |
| **Priority matrix** | Priority × Category | ? |
| **Customer overrides** | VIP, corporate | ? |
| **Channel rules** | Different for phone vs email | ? |

**Business Hours:**

| Setting | Options | Research Needed |
|---------|---------|-----------------|
| **Start time** | Configurable hour | ? |
| **End time** | Configurable hour | ? |
| **Days** | Select working days | ? |
| **Timezone** | Agency timezone | ? |
| **Breaks** | Lunch, other | ? |

**Holiday Calendar:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Public holidays** | Pre-loaded | ? |
| **Custom holidays** | Agency-specific | ? |
| **Partial days** | Half-days | ? |
| **Recurring** | Yearly holidays | ? |

### D. Performance Management

**Agent Performance:**

| Metric | Good | Needs Improvement | Research Needed |
|--------|------|-------------------|-----------------|
| **SLA compliance** | > 95% | < 90% | ? |
| **First response** | Within target | Exceeds target | ? |
| **Resolution** | Within target | Exceeds target | ? |
| **Customer satisfaction** | > 4.5/5 | < 4/5 | ? |
| **Ticket volume** | Appropriate capacity | Over/under utilized | ? |

**Team Performance:**

| Metric | Target | Research Needed |
|--------|--------|-----------------|
| **Team SLA** | > 90% | ? |
| **Queue depth** | < 2x capacity | ? |
| **Avg wait time** | < 30 min | ? |
| **Abandonment** | < 5% | ? |

**Capacity Planning:**

| Factor | Calculation | Research Needed |
|--------|-------------|-----------------|
| **Required agents** | Ticket volume / handling capacity | ? |
| **Forecasting** | Historical trends + seasonality | ? |
| **Shrinkage** | Breaks, training, absence | ? |
| **Peak load** | Maximum capacity needed | ? |

**Improvement Actions:**

| Issue | Action | Research Needed |
|-------|--------|-----------------|
| **Chronic breaches** | Investigate root cause | ? |
| **Agent struggles** | Training, coaching | ? |
| **Process issues** | Workflow optimization | ? |
| **Capacity shortage** | Hiring, scheduling | ? |

---

## Data Model Sketch

```typescript
interface SLAPolicy {
  policyId: string;
  name: string;
  description?: string;

  // Scope
  appliesTo: PolicyScope;
  customerTier?: CustomerTier;

  // Targets
  responseTargets: Map<TicketPriority, ResponseTarget>;
  resolutionTargets: Map<TicketCategory, ResolutionTarget>;

  // Calendar
  businessHoursOnly: boolean;
  businessHours: BusinessHours;
  holidays: string[]; // Holiday calendar IDs

  // Pause rules
  pauseRules: PauseRule[];

  // Escalation
  escalationRules: EscalationRule[];

  // Active
  active: boolean;
  version: number;
}

interface PolicyScope {
  categories?: TicketCategory[];
  priorities?: TicketPriority[];
  channels?: CommunicationChannel[];
  customers?: string[]; // Customer IDs
}

interface ResponseTarget {
  initialResponse: number; // Minutes
  updateFrequency: number; // Minutes
  maxResolution: number; // Hours
}

interface ResolutionTarget {
  category: TicketCategory;
  target: number; // Hours
  firstContactResolution?: number; // % target
}

interface BusinessHours {
  timezone: string;
  days: {
    dayOfWeek: number; // 0-6
    working: boolean;
    start?: string; // HH:mm
    end?: string;
  }[];
}

interface PauseRule {
  ruleId: string;
  trigger: PauseTrigger;
  autoResume: boolean;
  maxPauseDuration?: number; // Hours
}

type PauseTrigger =
  | 'customer_reply'
  | 'waiting_customer'
  | 'external_dependency'
  | 'agent_assigned';

interface SLATracking {
  trackingId: string;
  ticketId: string;
  policyId: string;

  // Targets
  initialResponseTarget: Date;
  resolutionTarget: Date;

  // Current status
  status: SLAStatus;
  percentageUsed: number;
  breachAt: Date;

  // Paused
  paused: boolean;
  pausedAt?: Date;
  pauseReason?: string;
  totalPausedTime: number; // Minutes

  // History
  milestones: SLAMilestone[];
}

type SLAStatus =
  | 'on_track'
  | 'warning'
  | 'at_risk'
  | 'critical'
  | 'breached';

interface SLAMilestone {
  milestoneId: string;
  type: MilestoneType;
  target: Date;
  actual?: Date;
  met: boolean;
}

type MilestoneType =
  | 'initial_response'
  | 'update'
  | 'resolution';

interface SLABreach {
  breachId: string;
  ticketId: string;
  policyId: string;

  // Details
  milestoneType: MilestoneType;
  target: Date;
  actual: Date;
  overdueBy: number; // Minutes

  // Impact
  impact: BreachImpact;
  customerNotified: boolean;

  // Resolution
  rootCause?: string;
  correctiveAction?: string;
  resolved: boolean;
}

type BreachImpact =
  | 'minor'
  | 'moderate'
  | 'significant'
  | 'severe';

interface SLAReport {
  reportId: string;
  period: DateRange;

  // Summary
  totalTickets: number;
  slaCompliant: number;
  slaBreached: number;
  complianceRate: number;

  // By priority
  byPriority: Map<TicketPriority, PriorityMetrics>;

  // By category
  byCategory: Map<TicketCategory, CategoryMetrics>;

  // By agent
  byAgent: Map<string, AgentMetrics>;

  // By team
  byTeam: Map<string, TeamMetrics>;

  // Trends
  trends: TrendData[];

  // Breaches
  breaches: SLABreach[];

  // Recommendations
  recommendations: SLARecommendation[];
}

interface PriorityMetrics {
  total: number;
  compliant: number;
  breached: number;
  complianceRate: number;
  avgResponseTime: number;
  avgResolutionTime: number;
}

interface CategoryMetrics {
  total: number;
  compliant: number;
  breached: number;
  complianceRate: number;
  avgResolutionTime: number;
  firstContactResolution: number;
}

interface AgentMetrics {
  agentId: string;
  agentName: string;

  // Volume
  totalAssigned: number;
  totalResolved: number;

  // SLA
  slaCompliant: number;
  slaBreached: number;
  complianceRate: number;

  // Time
  avgResponseTime: number;
  avgResolutionTime: number;

  // Quality
  satisfaction: number;
}

interface SLARecommendation {
  type: RecommendationType;
  priority: number;
  description: string;
  action: string;
  expectedImpact: string;
}

type RecommendationType =
  | 'training'
  | 'staffing'
  | 'process'
  | 'tool'
  | 'policy';
```

---

## Open Problems

### 1. Unrealistic SLAs
**Challenge:** Promises we can't keep

**Options:** Data-driven targets, buffer time, transparency

### 2. Pause Gaming
**Challenge:** Agents pause to avoid breach

**Options:** Audit pauses, auto-resume, manager approval

### 3. Customer Perception
**Challenge:** SLA met but customer unhappy

**Options:** Quality metrics, customer feedback, first contact resolution

### 4. Resource Constraints
**Challenge:** Can't meet SLAs with current staff

**Options:** Hiring, outsourcing, automation, prioritize

### 5. Reporting Complexity
**Challenge:** SLA reports are hard to understand

**Options:** Simplified dashboards, clear visuals, actionable insights

---

## Next Steps

1. Define SLA policies
2. Build SLA tracking engine
3. Create breach alerts
4. Implement performance reporting

---

**Status:** Research Phase — SLA patterns unknown

**Last Updated:** 2026-04-28
