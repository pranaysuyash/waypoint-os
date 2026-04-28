# Task Management & Assignment — Automation & Reminders

> Research document for task automation, recurring tasks, smart reminders, and proactive alerts.

---

## Key Questions

1. **Which tasks can be fully automated vs. partially automated vs. must be manual?**
2. **How do we schedule recurring tasks tied to trip milestones?**
3. **What's the reminder strategy — when, how often, through which channels?**
4. **How do we detect tasks that are at risk of being overdue?**
5. **How do automated tasks interact with the workflow automation engine?**

---

## Research Areas

### Task Automation

```typescript
interface TaskAutomation {
  automationId: string;
  name: string;
  trigger: AutomationTrigger;
  conditions: AutomationCondition[];
  actions: AutomationAction[];
  enabled: boolean;
  lastTriggeredAt?: Date;
  triggerCount: number;
}

type AutomationTrigger =
  | { type: 'trip_created' }
  | { type: 'trip_stage_changed'; fromStage?: string; toStage: string }
  | { type: 'task_completed'; taskType: TaskType }
  | { type: 'booking_confirmed'; bookingType: string }
  | { type: 'payment_received' }
  | { type: 'date_approaching'; daysBefore: number; event: string }
  | { type: 'customer_message_received' }
  | { type: 'schedule'; cron: string };

// Automation examples:
//
// "Pre-departure reminder"
// Trigger: date_approaching(daysBefore=3, event="travel_start")
// Actions:
//   1. Create task: "Pre-departure call with customer"
//   2. Send document package to customer (if not already sent)
//   3. Check visa status (flag if not approved)
//
// "Payment follow-up"
// Trigger: trip_stage_changed(toStage="quoted")
// Conditions: payment_status = "pending"
// Actions:
//   1. Wait 24 hours
//   2. Create task: "Follow up on payment"
//   3. Send payment reminder to customer
//   4. If no payment in 48 hours, escalate to team lead
//
// "Visa deadline tracker"
// Trigger: date_approaching(daysBefore=21, event="travel_start")
// Conditions: visa_required = true, visa_status != "approved"
// Actions:
//   1. Create task: "URGENT: Visa not yet approved"
//   2. Set task priority to critical
//   3. Notify assigned agent + team lead
```

### Recurring Tasks

```typescript
interface RecurringTask {
  recurringTaskId: string;
  name: string;
  description: string;
  schedule: RecurringSchedule;
  assigneeRule: AssigneeRule;
  checklistTemplate: ChecklistItem[];
  active: boolean;
}

type RecurringSchedule =
  | { type: 'trip_milestone'; milestone: string; offsetDays: number }
  | { type: 'relative_to_event'; event: string; offsetDays: number }
  | { type: 'cron'; expression: string }
  | { type: 'interval'; days: number };

// Recurring tasks for travel platform:
// Trip-level:
// - Day -30: Check passport validity
// - Day -21: Visa application deadline reminder
// - Day -14: Final payment due reminder
// - Day -7: Pre-departure document package
// - Day -3: Pre-departure call
// - Day -1: Final itinerary confirmation
// - Day 0: Travel day check-in
// - Day +1: Safe arrival check
// - Day +2: Post-trip feedback request
// - Day +7: Review submission reminder
// - Day +14: Post-trip follow-up for next booking

// Business-level:
// Daily: Overdue task review (team lead)
// Weekly: Agent performance summary
// Monthly: Supplier performance review
// Quarterly: Compliance audit tasks
```

### Smart Reminders

```typescript
interface SmartReminder {
  reminderId: string;
  taskId: string;
  agentId: string;
  type: ReminderType;
  channel: ReminderChannel;
  scheduledFor: Date;
  message: string;
  escalationPath: ReminderEscalation[];
  sentAt?: Date;
  acknowledgedAt?: Date;
}

type ReminderType =
  | 'task_due'                       // Task is due today
  | 'task_overdue'                   // Task is past due
  | 'task_at_risk'                   // Task likely to be overdue
  | 'dependency_resolved'            // Blocking task completed
  | 'customer_waiting'               // Customer is waiting for action
  | 'milestone_approaching'          // Trip milestone coming up
  | 'handoff_reminder'               // Shift handoff approaching
  | 'quality_check';                 // Verify completed task quality

type ReminderChannel =
  | 'in_app'
  | 'push_notification'
  | 'whatsapp'
  | 'email'
  | 'slack';

// Smart reminder rules:
// Task due today → In-app notification at 9 AM
// Task due in 2 hours → Push notification
// Task overdue by 1 hour → WhatsApp message
// Task overdue by 4 hours → Notify team lead
// Task at risk (agent has 5+ tasks due today) → In-app warning badge
// Customer waiting > 30 min → Push notification + in-app
// Customer waiting > 2 hours → WhatsApp to agent + team lead
```

### Risk Detection

```typescript
interface TaskRiskDetector {
  rules: RiskRule[];
  predictions: RiskPrediction[];
}

interface RiskRule {
  ruleId: string;
  name: string;
  condition: string;
  riskLevel: RiskLevel;
  action: string;
}

type RiskLevel =
  | 'low'                    // Monitor
  | 'medium'                 // Flag to agent
  | 'high'                   // Alert agent + team lead
  | 'critical';              // Escalate immediately

interface RiskPrediction {
  taskId: string;
  tripId: string;
  riskFactor: string;
  probability: number;               // 0-1, likelihood of missing deadline
  impactLevel: 'low' | 'medium' | 'high';
  recommendedAction: string;
  detectedAt: Date;
}

// Risk detection patterns:
// Pattern: "Spiraling"
// Agent has 3+ overdue tasks → Medium risk on all new tasks
// Action: Flag to team lead for workload redistribution
//
// Pattern: "Forgotten"
// Task not viewed in 48 hours, due in 3 days → High risk
// Action: Send reminder + suggest reassignment
//
// Pattern: "Blocked cascade"
// Task A is blocked → Tasks B, C, D (dependent) also blocked → Critical
// Action: Escalate blocker to team lead
//
// Pattern: "Customer ghost"
// Customer hasn't responded in 5+ days → Low risk for now
// Action: Agent reminder to follow up, suggest alternative contact method
//
// Pattern: "Seasonal spike"
// Agent's overdue rate jumps > 2x weekly average → Medium risk
// Action: Team lead review, suggest temporary task redistribution
```

---

## Open Problems

1. **Automation trust** — Agents may not trust automated task creation. If auto-generated tasks are irrelevant, they'll be ignored. Need accuracy tracking and feedback loop.

2. **Reminder fatigue** — Too many reminders = all ignored. Need smart frequency control based on agent response patterns and task urgency.

3. **Automated reassignment** — Should the system auto-reassign overdue tasks? Agents may feel their work is being "stolen." Need sensitivity and opt-out for reasonable delays.

4. **Risk prediction accuracy** — Predicting task risk from historical data is unreliable for edge cases. Need calibration against actual outcomes.

5. **Timezone handling** — Agents and customers may be in different timezones. Reminders need timezone-aware scheduling that respects working hours.

---

## Next Steps

- [ ] Design task automation rule engine with trip-specific triggers
- [ ] Build recurring task templates for common trip milestones
- [ ] Create smart reminder system with channel escalation
- [ ] Design task risk detection patterns
- [ ] Study reminder UX (Todoist, Things, Linear notifications)
