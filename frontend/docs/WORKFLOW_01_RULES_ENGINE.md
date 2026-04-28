# Workflow Automation — Business Rules Engine

> Research document for building a configurable business rules engine for travel operations.

---

## Key Questions

1. **What business rules currently live in code that should be configurable?**
2. **What's the right balance between code-based rules and declarative rules?**
3. **How do we version, test, and roll back rules without deployments?**
4. **What's the performance impact of a rules engine on the booking pipeline?**
5. **Who manages rules — developers, operations team, or business users?**

---

## Research Areas

### Rules Taxonomy

```typescript
type RuleCategory =
  // Pricing rules
  | 'pricing_markup'           // Markup rules by segment/product
  | 'discount_eligibility'     // Who gets what discount
  | 'commission_rate'          // Commission calculation rules
  // Booking rules
  | 'cancellation_policy'      // Cancellation windows and penalties
  | 'modification_policy'      // Change rules and fees
  | 'booking_validation'       // Required fields, constraints
  // Workflow rules
  | 'approval_required'        // When bookings need approval
  | 'escalation_trigger'       // When to escalate to manager
  | 'auto_assignment'          // Auto-assign trips to agents
  // Notification rules
  | 'notification_trigger'     // When to send notifications
  | 'reminder_schedule'        // Reminder timing and channels
  // Compliance rules
  | 'visa_requirement'         // Visa check rules by nationality
  | 'document_requirement'     // Required documents per trip type
  | 'regulatory_check';        // Regulatory compliance checks

interface BusinessRule {
  ruleId: string;
  name: string;
  category: RuleCategory;
  description: string;
  priority: number;             // Higher priority evaluated first
  condition: RuleCondition;     // When this rule applies
  action: RuleAction;           // What to do
  enabled: boolean;
  effectiveFrom: Date;
  effectiveTo?: Date;
  version: number;
  createdBy: string;
  approvedBy: string;
}
```

### Rule Condition Language

```typescript
interface RuleCondition {
  operator: 'and' | 'or' | 'not';
  operands: (RuleCondition | RulePredicate)[];
}

interface RulePredicate {
  field: string;                // e.g., "trip.destination.country"
  operator: ComparisonOperator;
  value: string | number | boolean | string[];
}

type ComparisonOperator =
  | 'equals' | 'not_equals'
  | 'greater_than' | 'less_than'
  | 'in' | 'not_in'
  | 'contains' | 'starts_with'
  | 'between' | 'is_null' | 'is_not_null';

// Example rule: "If trip value > ₹5L and destination is international,
//                then require senior agent approval"
// {
//   operator: 'and',
//   operands: [
//     { field: 'trip.totalValue', operator: 'greater_than', value: 500000 },
//     { field: 'trip.destination.type', operator: 'equals', value: 'international' }
//   ]
// }
```

### Rule Engine Architecture

```typescript
interface RuleEngine {
  // Evaluate all applicable rules for a given context
  evaluate(context: RuleContext): RuleResult[];
  // Get all rules that would fire for a context (dry run)
  preview(context: RuleContext): RulePreview[];
  // Test a new rule against historical data
  testRule(rule: BusinessRule, testData: RuleContext[]): TestResult;
}

interface RuleContext {
  entityType: 'trip' | 'booking' | 'customer' | 'agent' | 'payment';
  entityId: string;
  data: Record<string, unknown>;
  eventType: string;
  timestamp: Date;
}

interface RuleResult {
  ruleId: string;
  fired: boolean;
  action: RuleAction;
  priority: number;
  executionTimeMs: number;
}

interface RuleAction {
  type: 'set_value' | 'send_notification' | 'require_approval'
      | 'apply_discount' | 'assign_agent' | 'create_task'
      | 'block_action' | 'trigger_webhook' | 'log_event';
  params: Record<string, unknown>;
}
```

---

## Open Problems

1. **Rule conflicts** — Two rules fire for the same context with contradictory actions. Priority-based resolution is simple but may not capture business intent.

2. **Rule explosion** — As business grows, the number of rules proliferates. Hard to understand which rules are active, redundant, or conflicting.

3. **Performance** — Evaluating 100+ rules per booking adds latency. Need efficient pattern matching (Rete algorithm, decision tables).

4. **Non-technical rule authoring** — Business users want to create rules without writing code. Visual rule builders (like Zapier) are hard to build well.

5. **Testing in production** — How to test a new pricing rule against real booking data without actually applying it? Need shadow mode evaluation.

---

## Next Steps

- [ ] Evaluate rules engine libraries (json-rules-engine, node-rules, Easy Rules)
- [ ] Catalog current hardcoded business rules that should be externalized
- [ ] Design visual rule builder UX for non-technical users
- [ ] Study Rete algorithm for efficient rule evaluation
- [ ] Design rule testing and shadow mode framework
