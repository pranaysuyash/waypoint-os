# Lead Management 02: Qualification

> Lead scoring, routing, and qualification criteria

---

## Document Overview

**Focus:** Lead qualification and routing
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Scoring Models
- How do we score leads?
- What criteria matter?
- How do we weight different factors?
- What about negative scoring?

### Routing Rules
- How do we assign leads?
- What about round-robin vs. skill-based?
- How do we handle capacity?
- What about re-assignment?

### Qualification Criteria
- What makes a lead qualified?
- How do we detect buying signals?
- What about budget authority need?
- How do we handle timing?

### Segmentation
- How do we segment leads?
- What segments are useful?
- How do we update segments?
- What about dynamic segments?

---

## Research Areas

### A. Lead Scoring

**Scoring Factors:**

| Factor | Weight | Example | Research Needed |
|--------|--------|---------|-----------------|
| **Trip value** | High | High budget = high score | ? |
| **Travel urgency** | High | Soon dates = high score | ? |
| **Engagement** | Medium | Opens, clicks | ? |
| **Source** | Medium | Paid vs organic | ? |
| **Demographics** | Low | Location, age | ? |

**Score Calculation:**

```
Lead Score = (Budget Score × 0.3) +
             (Urgency Score × 0.3) +
             (Engagement Score × 0.2) +
             (Source Score × 0.15) +
             (Demographic Score × 0.05)
```

**Scoring Tiers:**

| Score Range | Tier | Treatment | Research Needed |
|-------------|------|-----------|-----------------|
| **80-100** | Hot | Immediate call | ? |
| **50-79** | Warm | Email sequence | ? |
| **20-49** | Cool | Nurture campaign | ? |
| **0-19** | Cold | Occasional email | ? |

**Negative Signals:**

| Signal | Impact | Research Needed |
|--------|--------|-----------------|
| **Wrong destination** | -20 | ? |
| **Unrealistic budget** | -15 | ? |
| **No response** | -5/day | ? |
| **Past bad experience** | -30 | ? |

### B. Lead Routing

**Routing Methods:**

| Method | When To Use | Research Needed |
|--------|-------------|-----------------|
| **Round-robin** | Equal distribution | ? |
| **Skill-based** | Specialized agents | ? |
| **Geographic** | Location-based | ? |
| **Capacity-based** | Workload balancing | ? |
| **Manual** | Strategic accounts | ? |

**Assignment Rules:**

| Rule | Condition | Action | Research Needed |
|------|-----------|--------|-----------------|
| **Destination expert** | Specific country | Assign to expert | ? |
| **Language** | Language preference | Match language | ? |
| **VIP** | High value | Senior agent | ? |
| **Rebooking** | Returning customer | Previous agent | ? |

**Capacity Management:**

| Metric | Limit | Research Needed |
|--------|-------|-----------------|
| **Active leads** | Max per agent | ? |
| **Hot leads** | Priority handling | ? |
| **Response time** | SLA-based | ? |
| **Workload** | Points-based | ? |

**Re-assignment:**

| Trigger | Action | Research Needed |
|---------|--------|-----------------|
| **Agent on leave** | Reassign leads | ? |
| **Over capacity** | Redistribute | ? |
| **No response** | Reassign after X days | ? |
| **Agent request** | Manual reassign | ? |

### C. Qualification Framework

**BANT Framework:**

| Letter | Question | Research Needed |
|--------|----------|-----------------|
| **Budget** | Can they afford? | ? |
| **Authority** | Can they decide? | ? |
| **Need** | Do they need it? | ? |
| **Timing** | When will they buy? | ? |

**Qualification Stages:**

| Stage | Criteria | Research Needed |
|-------|----------|-----------------|
| **MQL** | Marketing qualified | Score threshold | ? |
| **SQL** | Sales qualified | BANT passed | ? |
| **Opportunity** | Proposal stage | Active negotiation | ? |

**Buying Signals:**

| Signal | Strength | Research Needed |
|--------|----------|-----------------|
| **Requested quote** | Strong | ? |
| **Asked dates** | Medium | ? |
| **Downloaded brochure** | Weak | ? |
| **Price inquiry** | Medium | ? |

### D. Lead Segmentation

**Segment Types:**

| Segment | Criteria | Research Needed |
|---------|----------|-----------------|
| **Destination-based** | Country/region interest | ? |
| **Trip type** | Leisure, business, honeymoon | ? |
| **Budget level** | Economy, mid, luxury | ? |
| **Timing** | Immediate, future, dreamer | ? |
| **Lifecycle** | New, returning, lapsed | ? |

**Dynamic Segments:**

| Segment | Rule | Research Needed |
|---------|------|-----------------|
| **Hot leads** | Score > 80 + dates < 30 days | ? |
| **High value** | Budget > ₹5L | ? |
| **At risk** | No activity 7+ days | ? |
| **Ready to buy** | Score > 70 + requested quote | ? |

**Segment Actions:**

| Segment | Action | Research Needed |
|---------|--------|-----------------|
| **Hot leads** | Immediate call | ? |
| **Nurture** | Email sequence | ? |
| **At risk** | Re-engagement campaign | ? |
| **Unqualified** | Remove from active | ? |

---

## Data Model Sketch

```typescript
interface LeadScoring {
  leadId: string;
  agencyId: string;

  // Score
  totalScore: number;
  maxScore: number;
  percentage: number;

  // Components
  components: ScoreComponent[];

  // Qualification
  tier: ScoreTier;
  qualified: boolean;
  qualifiedAt?: Date;

  // History
  scoreHistory: ScoreHistory[];
}

interface ScoreComponent {
  componentId: string;
  name: string;
  weight: number; // 0-1
  score: number;
  maxScore: number;
  details?: string;
}

type ScoreTier = 'hot' | 'warm' | 'cool' | 'cold';

interface ScoreHistory {
  timestamp: Date;
  score: number;
  change: number;
  reason: string;
}

interface LeadRouting {
  leadId: string;

  // Assignment
  assignedTo: string; // Agent ID
  assignedAt: Date;
  assignedBy: string; // System or user

  // Routing
  routingRule: string;
  routingMethod: RoutingMethod;

  // Reassignment
  reassignments: Reassignment[];
}

type RoutingMethod =
  | 'round_robin'
  | 'skill_based'
  | 'geographic'
  | 'capacity_based'
  | 'manual';

interface Reassignment {
  fromAgent: string;
  toAgent: string;
  reason: string;
  reassignedAt: Date;
}

interface AgentCapacity {
  agentId: string;

  // Capacity
  maxActiveLeads: number;
  currentActiveLeads: number;
  availableCapacity: number;

  // Specialization
  specializations: string[]; // Destinations, languages
  languages: string[];

  // Performance
  averageResponseTime: number; // Minutes
  conversionRate: number; // % of leads converted

  // Status
  active: boolean;
  onLeaveUntil?: Date;
}

interface QualificationCriteria {
  criteriaId: string;
  name: string;
  type: QualificationType;

  // Rules
  rules: QualificationRule[];

  // Threshold
  passThreshold: number;

  // Actions
  passActions: string[];
  failActions: string[];
}

type QualificationType = 'MQL' | 'SQL' | 'custom';

interface QualificationRule {
  ruleId: string;
  field: string;
  operator: ComparisonOperator;
  value: any;
  weight: number;
}

type ComparisonOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'contains'
  | 'between';

interface LeadSegment {
  segmentId: string;
  name: string;
  description?: string;

  // Definition
  rules: SegmentRule[];
  matchType: 'all' | 'any'; // All or any rules must match

  // Membership
  leadIds: string[];
  count: number;

  // Actions
  actions: SegmentAction[];

  // Dynamic
  dynamic: boolean;
  refreshInterval?: number; // Minutes
}

interface SegmentRule {
  field: string;
  operator: ComparisonOperator;
  value: any;
}

interface SegmentAction {
  action: string; // Campaign, assignment, etc.
  parameters: Record<string, any>;
}
```

---

## Open Problems

### 1. Score Accuracy
**Challenge:** Scores don't predict conversion

**Options:** Machine learning, feedback loop, regular tuning

### 2. Fair Distribution
**Challenge:** Agents get unequal leads

**Options:** Capacity tracking, adjustment factors, manual override

### 3. False Positives
**Challenge:** Scored leads don't convert

**Options:** Adjust weights, add signals, longer tracking

### 4. Subjectivity
**Challenge:** Different agents have different opinions

**Options:** Clear criteria, calibration, feedback

### 5. Rapid Changes
**Challenge:** Situations change quickly

**Options:** Real-time updates, event-based scoring, alerts

---

## Next Steps

1. Define scoring model
2. Build routing engine
3. Create qualification rules
4. Implement segmentation

---

**Status:** Research Phase — Qualification patterns unknown

**Last Updated:** 2026-04-27
