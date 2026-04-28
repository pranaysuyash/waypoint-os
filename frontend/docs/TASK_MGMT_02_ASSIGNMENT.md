# Task Management & Assignment — Assignment & Workload

> Research document for agent assignment algorithms, workload balancing, and capacity management.

---

## Key Questions

1. **How do we match tasks to the right agent based on skills, workload, and availability?**
2. **What's the workload model — how much is too much for one agent?**
3. **How do we handle reassignment when an agent is unavailable?**
4. **What's the SLA model for task completion?**
5. **How do we balance fairness (equal distribution) with efficiency (specialist routing)?**

---

## Research Areas

### Agent Capacity Model

```typescript
interface AgentCapacity {
  agentId: string;
  capacity: CapacityConfig;
  currentLoad: CurrentLoad;
  availability: AvailabilitySchedule;
  skills: AgentSkill[];
  preferences: AgentPreferences;
}

interface CapacityConfig {
  maxActiveTrips: number;           // Max simultaneous trips
  maxActiveTasks: number;           // Max simultaneous tasks
  maxRevenueInProgress: number;     // Max ₹ value of active trips
  maxUrgentItems: number;           // Max critical/high priority tasks
  workingHoursPerDay: number;
}

interface CurrentLoad {
  activeTrips: number;
  activeTasks: number;
  revenueInProgress: number;
  urgentItemCount: number;
  utilizationPercent: number;       // 0-100, target 70-85%
  tasksDueToday: number;
  overdueTasks: number;
  averageTaskCompletionTime: number;
}

interface AvailabilitySchedule {
  regularHours: { start: string; end: string; days: number[] }[];
  timeOff: { start: Date; end: Date; type: string }[];
  currentStatus: 'available' | 'busy' | 'in_meeting' | 'on_break' | 'off_duty' | 'on_leave';
  nextAvailableAt?: Date;
}

// Capacity limits by agent level:
// Junior agent: maxActiveTrips=8, maxRevenueInProgress=₹5L
// Mid-level agent: maxActiveTrips=12, maxRevenueInProgress=₹15L
// Senior agent: maxActiveTrips=15, maxRevenueInProgress=₹50L
// Team lead: maxActiveTrips=5, oversight of team + escalation handling
```

### Skill-Based Assignment

```typescript
interface AgentSkill {
  skillId: string;
  category: SkillCategory;
  level: SkillLevel;
  certified: boolean;
  lastUsedAt?: Date;
  successfulBookings: number;
}

type SkillCategory =
  | 'destination_expertise'          // Singapore, Europe, Domestic India
  | 'trip_type'                      // Leisure, Corporate, MICE, Luxury
  | 'supplier_system'                // Amadeus, Sabre, specific hotel chains
  | 'product_type'                   // Flights, Hotels, Visa, Insurance
  | 'customer_segment'               // Budget, Premium, Corporate, Group
  | 'language'                       // English, Hindi, Tamil, etc.
  | 'special_process';               // Visa processing, Group booking, MICE

type SkillLevel =
  | 'learning'               // Can handle with guidance
  | 'proficient'             // Can handle independently
  | 'expert'                 // Can handle complex cases and train others
  | 'specialist';            // Go-to person for this skill

interface AssignmentScore {
  agentId: string;
  score: number;                    // 0-100
  factors: ScoreFactor[];
  recommendation: AssignmentRecommendation;
}

interface ScoreFactor {
  factor: string;
  weight: number;
  score: number;
  reason: string;
}

// Scoring factors:
// Skill match (40%) → Does the agent have the right skills?
// Capacity (25%) → Does the agent have room for more work?
// Performance (15%) → Has the agent done well on similar tasks?
// Availability (10%) → Is the agent available now?
// Fairness (5%) → Has the agent been getting equitable distribution?
// Preference (5%) → Does the agent prefer this type of work?
```

### Auto-Assignment Engine

```typescript
interface AssignmentEngine {
  strategy: AssignmentStrategy;
  rules: AssignmentRule[];
  overrides: AssignmentOverride[];
}

type AssignmentStrategy =
  | 'best_match'                     // Highest scoring agent
  | 'round_robin'                    // Equal distribution
  | 'skill_based'                    // Skill match first, then capacity
  | 'workload_balanced'              // Least loaded agent first
  | 'customer_preference'            // Customer requested agent
  | 'hybrid';                        // Weighted combination

interface AssignmentRule {
  ruleId: string;
  condition: string;                 // Task attributes to match
  strategy: AssignmentStrategy;
  priority: number;                  // Higher priority rules evaluated first
  active: boolean;
}

// Assignment rules:
// VIP customer trip → customer_preference (if agent specified) or best_match
// Visa processing task → skill_based (visa specialist)
// MICE inquiry → skill_based (MICE specialist)
// General trip intake → workload_balanced (round robin among available)
// High-value trip (₹10L+) → best_match (senior agent with high performance)
// Urgent task → best_match with availability filter (must be available now)

// Auto-assignment flow:
// 1. Task created (manual or auto-generated)
// 2. Engine evaluates assignment rules in priority order
// 3. Rule matches → Score all eligible agents
// 4. Top-scoring agent proposed (with reasoning)
// 5. Agent notified, can accept or reject (with reason)
// 6. If rejected, second-best agent proposed
// 7. If no agent accepts within SLA, escalate to team lead
```

### SLA Framework

```typescript
interface TaskSLA {
  slaId: string;
  taskType: TaskType;
  priority: TaskPriority;
  responseTime: string;             // First action after assignment
  resolutionTime: string;           // Complete the task
  escalationRules: EscalationRule[];
}

interface EscalationRule {
  trigger: string;                   // "overdue by 1 hour" | "no response in 30 min"
  action: EscalationAction;
  notify: string[];
}

type EscalationAction =
  | 'notify_agent'                   // Send reminder
  | 'notify_team_lead'               // Alert team lead
  | 'reassign'                       // Auto-reassign to another agent
  | 'escalate_priority'              // Bump task priority up
  | 'customer_communicate';          // Proactively inform customer of delay

// SLA examples:
// Customer communication (critical):
//   Response: 15 minutes | Resolution: 2 hours
//   Escalation: No response in 30 min → notify team lead + reassign
//
// Supplier interaction (high):
//   Response: 1 hour | Resolution: 4 hours
//   Escalation: Overdue by 2 hours → notify team lead
//
// Document preparation (medium):
//   Response: 4 hours | Resolution: 1 business day
//   Escalation: Overdue by 1 day → notify team lead
//
// Post-trip tasks (low):
//   Response: 1 business day | Resolution: 3 business days
//   Escalation: Overdue by 3 days → weekly digest to team lead
```

---

## Open Problems

1. **Skill decay** — An agent who hasn't handled European trips in 6 months may be rusty. Need skill freshness scoring alongside skill level.

2. **Customer relationship continuity** — Customers prefer "their agent." Auto-assignment should factor in past customer-agent relationships, not just skills and workload.

3. **Assignment gaming** — Agents may reject undesirable tasks to get better ones. Need fairness monitoring and rejection reason tracking.

4. **Cross-team tasks** — A trip needs both a domestic agent (for flights) and an international agent (for hotels). Need split assignment within one trip.

5. **Peak season capacity** — During peak travel season, everyone is overloaded. Normal capacity models break down. Need surge staffing plans.

---

## Next Steps

- [ ] Design agent skill taxonomy and proficiency levels
- [ ] Build auto-assignment scoring engine with configurable weights
- [ ] Create SLA framework per task type and priority
- [ ] Design workload dashboard for team leads
- [ ] Study workforce management patterns (call centers, hospital scheduling)
