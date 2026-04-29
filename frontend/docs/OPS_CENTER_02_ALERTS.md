# Agency Operations Command Center — Alert System

> Research document for the operations alert system: alert categories, severity levels, routing, escalation rules, fatigue prevention, multi-channel notifications, and resolution workflows.

---

## Key Questions

1. **What alert categories and severity levels are needed for travel agency operations?**
2. **How do we route alerts to the right person without overwhelming anyone?**
3. **What escalation rules prevent alerts from languishing unacknowledged?**
4. **How do we prevent alert fatigue while ensuring critical issues never get missed?**
5. **What notification channels are appropriate per alert severity, and what is the cost trade-off?**
6. **What does the end-to-end alert lifecycle look like from detection to resolution?**

---

## Research Areas

### Alert Data Model

```typescript
interface OpsAlert {
  alertId: string;
  correlationId?: string;                 // Group related alerts
  category: AlertCategory;
  severity: AlertSeverity;
  status: AlertStatus;
  source: AlertSource;

  // What happened
  title: string;
  description: string;
  affectedEntities: AffectedEntity[];

  // When
  detectedAt: Date;
  firstOccurrenceAt: Date;                // May differ if deduplicated
  lastOccurrenceAt: Date;
  occurrenceCount: number;

  // Who
  assignedTo?: string;
  assignedTeam?: string;
  acknowledgedBy?: string;
  acknowledgedAt?: Date;
  resolvedBy?: string;
  resolvedAt?: Date;

  // Routing
  routingRule: string;                    // ID of the rule that matched
  notificationChannels: NotificationChannel[];
  escalationLevel: number;                // 0 = initial, 1+ = escalated

  // Context
  metadata: Record<string, unknown>;
  relatedAlerts: string[];                // Alert IDs
  suggestedActions: string[];
}

type AlertCategory =
  | 'trip'               // Trip-related issues
  | 'payment'            // Payment failures, refund issues
  | 'compliance'         // GST, TCS, TDS, regulatory
  | 'supplier'           // Supplier issues (airline, hotel, etc.)
  | 'customer'           // Customer complaints, escalations
  | 'system'             // Infrastructure, API failures
  | 'fraud'              // Suspicious activity
  | 'safety';            // Traveler safety concerns

type AlertSeverity = 'info' | 'warning' | 'critical' | 'emergency';

type AlertStatus =
  | 'new'                // Just detected
  | 'acknowledged'       // Someone is looking at it
  | 'investigating'      // Actively being worked on
  | 'escalated'          // Pushed to higher authority
  | 'resolved'           // Fixed
  | 'dismissed'          // False alarm or not actionable
  | 'snoozed';           // Temporarily suppressed

interface AlertSource {
  type: 'automated' | 'manual' | 'external';
  system: string;                        // e.g., "payment_gateway", "sla_monitor", "agent"
  ruleId?: string;                       // The detection rule that fired
}

interface AffectedEntity {
  type: 'trip' | 'booking' | 'customer' | 'agent' | 'supplier' | 'payment' | 'document';
  id: string;
  label: string;                         // Human-readable name
}
```

### Severity Levels & Response Expectations

```typescript
interface SeverityDefinition {
  level: AlertSeverity;
  label: string;
  color: string;                         // For UI
  sound?: string;                        // Audio alert tone
  responseTimeTarget: string;            // SLA for acknowledgment
  notificationChannels: NotificationChannel[];
  autoEscalateAfter: string;             // Time before auto-escalation
  examples: string[];
}

const SEVERITY_DEFINITIONS: SeverityDefinition[] = [
  {
    level: 'info',
    label: 'Informational',
    color: '#3B82F6',                    // Blue
    responseTimeTarget: '24 hours',
    notificationChannels: ['in_app'],
    autoEscalateAfter: '48 hours',
    examples: [
      'New trip assigned to you',
      'GST filing window opens in 7 days',
      'Supplier rate update available',
      'Monthly report is ready',
    ],
  },
  {
    level: 'warning',
    label: 'Needs Attention',
    color: '#F59E0B',                    // Amber
    responseTimeTarget: '4 hours',
    notificationChannels: ['in_app', 'push_web', 'push_mobile'],
    autoEscalateAfter: '8 hours',
    examples: [
      'Trip #4213 in quoting stage for 3 hours (SLA approaching)',
      'Payment gateway latency > 5 seconds',
      'Customer response pending > 24 hours',
      'TCS deposit due in 3 days',
    ],
  },
  {
    level: 'critical',
    label: 'Urgent',
    color: '#EF4444',                    // Red
    sound: 'alert_critical.mp3',
    responseTimeTarget: '30 minutes',
    notificationChannels: ['in_app', 'push_web', 'push_mobile', 'sms', 'whatsapp'],
    autoEscalateAfter: '1 hour',
    examples: [
      'Payment of ₹2.5L declined for booking #4213',
      'Trip #3891 SLA breached — customer waiting 6+ hours',
      'Airline SpiceJet cancelled flight SG-123 affecting 4 trips',
      'GST filing deadline tomorrow — returns not filed',
    ],
  },
  {
    level: 'emergency',
    label: 'Crisis',
    color: '#7F1D1D',                    // Dark red
    sound: 'alert_emergency.mp3',
    responseTimeTarget: '5 minutes',
    notificationChannels: ['in_app', 'push_web', 'push_mobile', 'sms', 'whatsapp', 'voice'],
    autoEscalateAfter: '15 minutes',
    examples: [
      'Traveler safety incident — customer in distress abroad',
      'Payment gateway completely down — all transactions failing',
      'Natural disaster at destination affecting 12+ active trips',
      'Suspected fraud — multiple bookings with stolen card',
    ],
  },
];
```

### Alert Routing Rules

```typescript
interface AlertRoutingRule {
  ruleId: string;
  name: string;
  description: string;
  enabled: boolean;
  priority: number;                      // Higher = evaluated first

  // When this rule applies
  conditions: RoutingCondition[];

  // Who to notify
  recipients: RoutingRecipient[];

  // Channel override (if different from severity defaults)
  channelOverride?: NotificationChannel[];
}

interface RoutingCondition {
  field: string;                         // e.g., "category", "severity", "affectedEntities.type"
  operator: 'equals' | 'contains' | 'in' | 'greater_than';
  value: string | number | string[];
}

interface RoutingRecipient {
  type: 'user' | 'role' | 'team' | 'on_call';
  identifier: string;                    // User ID, role name, team name
  notifyDelay: string;                   // "0s" = immediately, "5m" = delay 5 min
}

// Example routing rules:
//
// Rule 1: Trip alerts → assigned agent
//   conditions: [{ field: "category", operator: "equals", value: "trip" }]
//   recipients: [{ type: "user", identifier: "{{trip.assignedAgent}}", notifyDelay: "0s" }]
//
// Rule 2: Payment failures > ₹50K → finance team + ops manager
//   conditions: [
//     { field: "category", operator: "equals", value: "payment" },
//     { field: "metadata.amount", operator: "greater_than", value: 50000 }
//   ]
//   recipients: [
//     { type: "team", identifier: "finance", notifyDelay: "0s" },
//     { type: "role", identifier: "ops_manager", notifyDelay: "0s" }
//   ]
//
// Rule 3: Safety alerts → on-call manager + owner
//   conditions: [
//     { field: "category", operator: "equals", value: "safety" },
//     { field: "severity", operator: "in", value: ["critical", "emergency"] }
//   ]
//   recipients: [
//     { type: "on_call", identifier: "ops_lead", notifyDelay: "0s" },
//     { type: "role", identifier: "owner", notifyDelay: "0s" }
//   ]
//
// Rule 4: GST compliance warnings → CA + manager
//   conditions: [
//     { field: "category", operator: "equals", value: "compliance" },
//     { field: "metadata.complianceType", operator: "equals", value: "gst" }
//   ]
//   recipients: [
//     { type: "role", identifier: "accounts_ca", notifyDelay: "0s" },
//     { type: "role", identifier: "manager", notifyDelay: "5m" }
//   ]
```

### Escalation Engine

```typescript
interface EscalationPolicy {
  policyId: string;
  name: string;
  appliesTo: EscalationScope;
  levels: EscalationLevel[];
  terminalAction?: TerminalAction;       // What happens if all levels exhausted
}

interface EscalationScope {
  categories?: AlertCategory[];
  severities?: AlertSeverity[];
  teams?: string[];
}

interface EscalationLevel {
  level: number;                         // 0 = initial notification
  triggerAfter: string;                  // Duration since alert creation
  recipients: RoutingRecipient[];
  channels: NotificationChannel[];
  actions: EscalationAction[];
}

interface EscalationAction {
  type: 'reassign' | 'create_ticket' | 'page_on_call' | 'broadcast' | 'auto_respond';
  config: Record<string, unknown>;
}

type TerminalAction =
  | 'page_owner'                         // Escalate to agency owner
  | 'auto_acknowledge'                   // System acknowledges with note
  | 'create_incident';                   // Create formal incident

// Example escalation policy for payment alerts:
//
// Level 0 (immediate):
//   Recipients: Assigned agent
//   Channels: in-app, push
//   Actions: none
//
// Level 1 (after 30 min unacknowledged):
//   Recipients: Team lead
//   Channels: in-app, push, SMS
//   Actions: reassign to team lead
//
// Level 2 (after 1 hour unacknowledged):
//   Recipients: Operations manager
//   Channels: in-app, push, SMS, WhatsApp
//   Actions: create_ticket
//
// Level 3 (after 2 hours unacknowledged):
//   Recipients: Agency owner
//   Channels: in-app, push, SMS, WhatsApp, voice
//   Actions: page_on_call, broadcast
//   Terminal: page_owner

interface EscalationEvent {
  alertId: string;
  fromLevel: number;
  toLevel: number;
  triggeredAt: Date;
  reason: 'timeout' | 'manual' | 'auto_rule';
  notifiedRecipients: string[];
  actionsTaken: string[];
}
```

### Alert Fatigue Prevention

```typescript
interface AlertFatigueConfig {
  // Deduplication: group identical alerts
  deduplication: {
    enabled: boolean;
    windowMs: number;                    // Group identical alerts within this window
    maxGroupSize: number;                // After this many, auto-escalate
    groupBy: string[];                   // Fields to match for dedup
  };

  // Rate limiting: cap alerts per user per time window
  rateLimiting: {
    maxAlertsPerUserPerHour: number;     // Default: 20
    maxAlertsPerCategoryPerHour: number; // Default: 10
    burstAllowance: number;              // Allow short bursts up to this
  };

  // Suppression: temporarily mute known issues
  suppression: {
    maintenanceWindows: MaintenanceWindow[];
    knownIssues: KnownIssue[];
    mutedRules: string[];                // Rule IDs temporarily muted
  };

  // Aggregation: batch low-severity alerts
  aggregation: {
    enabled: boolean;
    batchInterval: string;               // e.g., "15m"
    maxBatchSize: number;                // Max alerts in one digest
    minSeverity: AlertSeverity;          // Only aggregate info/warning
  };

  // Smart throttling: AI-based prioritization
  smartThrottling: {
    enabled: boolean;
    model: string;                       // ML model for alert prioritization
    features: string[];                  // Features used for scoring
    actionabilityThreshold: number;      // Suppress alerts below this score
  };
}

interface MaintenanceWindow {
  id: string;
  description: string;
  start: Date;
  end: Date;
  suppressedCategories: AlertCategory[];
  suppressedSeverities: AlertSeverity[];
}

interface KnownIssue {
  issueId: string;
  title: string;
  description: string;
  detectedAt: Date;
  suppressDuplicates: boolean;
  affectedSystems: string[];
  workaround?: string;
  resolutionEta?: Date;
}

// Example: Deduplication rule for airline cancellation
// deduplication: {
//   groupBy: ["category", "metadata.airline", "metadata.flightNumber", "metadata.date"],
//   windowMs: 3600000,  // 1 hour
//   maxGroupSize: 10    // After 10 trips affected, auto-escalate to emergency
// }
```

### Notification Channel Integration

```typescript
interface AlertNotification {
  notificationId: string;
  alertId: string;
  channel: NotificationChannel;
  recipient: string;
  status: 'queued' | 'sent' | 'delivered' | 'read' | 'failed';
  sentAt?: Date;
  deliveredAt?: Date;
  readAt?: Date;
  failedReason?: string;
  retryCount: number;
  content: NotificationContent;
}

interface NotificationContent {
  title: string;
  body: string;
  actions: NotificationAction[];
  deepLink?: string;                     // URL to open the relevant page
}

interface NotificationAction {
  label: string;
  action: 'acknowledge' | 'resolve' | 'escalate' | 'snooze' | 'view' | 'assign';
  deepLink: string;
}

// Channel-specific content adaptation:
//
// IN-APP: Rich card with full details, action buttons, related entity links
// PUSH: Title + 2-line body + deep link
// SMS: 160 chars, critical alerts only, link to details
// WHATSAPP: Template message with action buttons
// EMAIL: Full HTML with context, action buttons, related alerts
// VOICE: Pre-recorded message with key details, "Press 1 to acknowledge"

// Channel selection by severity (with cost estimate):
//
// ┌─────────────┬──────────────────────────────────────────────────┬──────────┐
// │ Severity    │ Channel Sequence                                │ Cost/100 │
// ├─────────────┼──────────────────────────────────────────────────┼──────────┤
// │ Info        │ in-app                                          │ ₹0       │
// │ Warning     │ in-app → push → (digest email)                  │ ₹0-5     │
// │ Critical    │ in-app + push + SMS + WhatsApp → email          │ ₹45-75   │
// │ Emergency   │ in-app + push + SMS + WhatsApp + voice → email │ ₹175-375 │
// └─────────────┴──────────────────────────────────────────────────┴──────────┘
```

### Alert Resolution Workflow

```typescript
interface AlertResolution {
  alertId: string;
  timeline: ResolutionEvent[];
  rootCause?: string;
  resolutionNote: string;
  preventionAction?: string;             // How to prevent this in the future
  followUpRequired: boolean;
  followUpDate?: Date;
  feedbackRequested: boolean;            // Ask user if alert was useful
}

interface ResolutionEvent {
  timestamp: Date;
  actor: string;                         // User ID or "system"
  action: AlertStatus;
  note?: string;
  metadata?: Record<string, unknown>;
}

// Alert lifecycle:
//
//  DETECTED ──→ ROUTED ──→ NOTIFIED ──→ ACKNOWLEDGED ──→ INVESTIGATING
//                                                          │
//                                    ┌─────────────────────┼───────────────────┐
//                                    │                     │                   │
//                                  RESOLVED           ESCALATED            DISMISSED
//                                    │                     │
//                                    │               RE-ROUTED
//                                    │                     │
//                                    └────→ FEEDBACK ←────┘
//                                          (was alert useful?)
//
// Time boundaries:
//   DETECTED → ACKNOWLEDGED: tracked per severity SLA
//   ACKNOWLEDGED → RESOLVED: tracked per category benchmark
//   Total MTTR (Mean Time To Resolve): reported in ops dashboard

interface AlertMetrics {
  period: DateRange;
  totalAlerts: number;
  byCategory: Record<AlertCategory, number>;
  bySeverity: Record<AlertSeverity, number>;

  // Response metrics
  medianAckTime: number;                 // ms
  p95AckTime: number;
  medianResolveTime: number;
  p95ResolveTime: number;
  mttr: number;                          // Mean time to resolve

  // Quality metrics
  falsePositiveRate: number;             // Dismissed as not actionable
  escalationRate: number;                // % alerts that got escalated
  autoResolvedRate: number;              // % resolved by automation
  duplicateRate: number;                 // % that were duplicates

  // Fatigue metrics
  alertsPerAgentPerDay: number;
  unacknowledgedAlerts: number;
  staleAlerts: number;                   // Older than 24h still open
}
```

### Alert UI Wireframe

```typescript
// ┌─────────────────────────────────────────────────────────────────────┐
// │  ALERT CENTER                                    🔔 3  ⚠ 2  🔴 1 │
// ├─────────────────────────────────────────────────────────────────────┤
// │  [All] [Trip] [Payment] [Compliance] [Supplier] [System]          │
// │  Filter: [Severity ▾] [Status ▾] [Assignee ▾] [Time ▾]           │
// ├─────────────────────────────────────────────────────────────────────┤
// │                                                                     │
// │  🔴 EMERGENCY  Traveler safety — Ms. Sharma in Bangkok             │
// │     Hospitalized after accident. 4 active trips in region.         │
// │     Detected: 3 min ago  │  Unacknowledged                        │
// │     [Acknowledge] [Escalate] [View Trip] [Contact Customer]        │
// │  ─────────────────────────────────────────────────────────────────  │
// │  🔴 CRITICAL  Payment declined — ₹2.5L for Trip #4213            │
// │     Customer: Rajesh Kumar  │  Gateway: Razorpay                   │
// │     Detected: 18 min ago  │  Assigned to: Priya                    │
// │     [Acknowledge] [Retry Payment] [Contact Customer] [View Trip]   │
// │  ─────────────────────────────────────────────────────────────────  │
// │  ⚠ WARNING  SLA approaching — Trip #3891 in quoting 3h+           │
// │     Agent: Amit  │  Customer waiting since 10:30 AM                │
// │     Detected: 12 min ago  │  Auto-escalate in 45 min               │
// │     [Acknowledge] [Reassign] [View Trip] [Snooze 30m]             │
// │  ─────────────────────────────────────────────────────────────────  │
// │  ⚠ WARNING  TCS deposit due — ₹8.5L by April 7th                 │
// │     3 trips with uncollected TCS  │  5 deposits pending            │
// │     Detected: 2h ago  │  Assigned to: Accounts                     │
// │     [Acknowledge] [View Report] [Mark In Progress]                 │
// │  ─────────────────────────────────────────────────────────────────  │
// │  🔵 INFO  New trip assigned — #4298 Goa Weekend Package            │
// │     Customer: Mehta family (4 pax)  │  Value: ₹1.2L               │
// │     Detected: 5 min ago                                            │
// │     [View Trip] [Start Processing] [Dismiss]                       │
// │                                                                     │
// └─────────────────────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Alert-actionability gap** — Many alerts fire but are not actionable (e.g., "payment gateway is slow"). Need clear guidance on what the recipient should do, or else suppress it.

2. **Deduplication accuracy** — Two alerts about the same airline cancellation affecting different trips should be grouped, but two payment failures for different customers should not. The grouping keys need careful design per category.

3. **Night-time alerting** — Indian travel agencies often serve customers across time zones. Critical alerts at 3 AM need different handling (on-call rotation) vs. business hours (direct agent notification).

4. **WhatsApp Business API limitations** — Alert messages via WhatsApp require pre-approved templates. Emergency alerts with variable content may not fit template constraints. Need to design templates that accommodate operational variability.

5. **Feedback loop** — Without tracking whether alerts were useful, the system cannot improve. Need lightweight "thumbs up/down" on resolved alerts and periodic review of alert rule effectiveness.

6. **Cross-agency alert correlation** — A single airline cancellation may generate 50+ individual trip alerts. The dashboard must show this as one incident with 50 affected trips, not 50 separate alerts.

---

## Next Steps

- [ ] Catalog all alert-generating events in the current system
- [ ] Design alert deduplication rules per category
- [ ] Build severity-severity matrix with response SLAs
- [ ] Research on-call rotation systems (PagerDuty, Opsgenie, VictoriamMetrics)
- [ ] Design WhatsApp template library for operational alerts
- [ ] Prototype alert fatigue scoring model
- [ ] Create escalation policy templates for each alert category
- [ ] Design alert metrics dashboard (MTTR, false positive rate, etc.)
