# Workflow Automation — Event Triggers & Automated Actions

> Research document for event-driven automation, trigger configuration, and action execution.

---

## Key Questions

1. **What events in the travel lifecycle should trigger automated actions?**
2. **How do we make trigger configuration accessible to non-developers?**
3. **What's the execution model — synchronous, asynchronous, or mixed?**
4. **How do we handle trigger failures and retries?**
5. **How do we prevent infinite loops (action triggers another action)?**

---

## Research Areas

### Event Catalog

```typescript
type TriggerEvent =
  // Trip lifecycle
  | 'trip.created'
  | 'trip.status_changed'
  | 'trip.assigned'
  | 'trip.deadline_approaching'
  // Booking events
  | 'booking.confirmed'
  | 'booking.cancelled'
  | 'booking.modified'
  | 'booking.failed'
  // Customer events
  | 'customer.registered'
  | 'customer.inquiry_received'
  | 'customer.feedback_submitted'
  | 'customer.inactive_days'       // Customer hasn't booked in N days
  // Payment events
  | 'payment.received'
  | 'payment.failed'
  | 'payment.refunded'
  | 'payment.overdue'
  // Spine events
  | 'spine.completed'
  | 'spine.failed'
  | 'spine.result_ready'
  // Time-based
  | 'schedule.daily'
  | 'schedule.weekly'
  | 'schedule.cron'
  // External events
  | 'alert.travel_advisory'
  | 'alert.price_change'
  | 'alert.supplier_update';

interface TriggerConfig {
  triggerId: string;
  name: string;
  event: TriggerEvent;
  conditions?: RuleCondition;       // Additional conditions
  actions: TriggerAction[];
  enabled: boolean;
  cooldown?: string;                // Min time between fires
  maxExecutionsPerHour?: number;
  lastFiredAt?: Date;
}
```

### Action Types

```typescript
type TriggerAction =
  | { type: 'send_notification'; channel: string; template: string; recipients: string[] }
  | { type: 'create_task'; assignee: string; title: string; dueIn: string }
  | { type: 'update_record'; entity: string; fields: Record<string, unknown> }
  | { type: 'send_email'; to: string; template: string; variables: Record<string, string> }
  | { type: 'call_webhook'; url: string; method: string; payload: Record<string, unknown> }
  | { type: 'delay'; duration: string }                              // Wait before next action
  | { type: 'conditional'; condition: RuleCondition; then: TriggerAction[]; else: TriggerAction[] }
  | { type: 'assign_agent'; strategy: 'round_robin' | 'least_busy' | 'skill_based' }
  | { type: 'generate_document'; template: string; deliveryMethod: string }
  | { type: 'update_tag'; tag: string; action: 'add' | 'remove' }
  | { type: 'log_event'; message: string; level: string };
```

### Common Automation Recipes

```typescript
interface AutomationRecipe {
  name: string;
  trigger: TriggerEvent;
  actions: TriggerAction[];
  description: string;
  installCount: number;
}

// Recipe: "Welcome new customer"
// Trigger: customer.registered
// Actions: Send welcome email, create onboarding task for agent

// Recipe: "Booking confirmation package"
// Trigger: booking.confirmed
// Actions: Generate voucher PDF, send email with voucher, send WhatsApp confirmation, create pre-trip reminder (7 days before)

// Recipe: "Payment follow-up"
// Trigger: payment.overdue
// Actions: Send payment reminder email, create task for agent, if >3 days overdue: escalate to manager

// Recipe: "Spine run success"
// Trigger: spine.completed
// Actions: Notify assigned agent, generate itinerary draft, move trip to next stage

// Recipe: "Post-trip feedback"
// Trigger: trip.completed (travel end date reached)
// Actions: Wait 2 days, send feedback email, if no response: send WhatsApp reminder after 3 days

// Recipe: "Re-engage inactive customer"
// Trigger: customer.inactive_days (90)
// Actions: Send "we miss you" email with personalized destination suggestion, create lead for agent follow-up
```

---

## Open Problems

1. **Action ordering and dependencies** — Actions in a trigger may need to run sequentially (generate PDF → then send email with attachment) or in parallel. Need a workflow DAG.

2. **Failure handling** — If action 3 of 5 fails, do we retry just that action or the whole chain? Partial execution state is complex.

3. **Loop prevention** — Trip status change triggers a notification, which triggers a task, which modifies the trip, which triggers another status change. Need cycle detection.

4. **Trigger deduplication** — Customer makes 3 booking changes in 5 minutes. Should the "booking modified" trigger fire 3 times or be debounced?

5. **Testing trigger chains** — How to test an automation recipe end-to-end without affecting real data. Need a simulation environment.

---

## Next Steps

- [ ] Design event bus architecture for trigger system
- [ ] Build initial automation recipe library
- [ ] Study workflow automation platforms (n8n, Temporal, Trigger.dev)
- [ ] Design trigger testing and simulation environment
- [ ] Create cycle detection algorithm for action chains
