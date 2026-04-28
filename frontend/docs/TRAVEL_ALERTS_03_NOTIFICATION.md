# Travel Alerts — Alert Delivery & Escalation

> Research document for delivering alerts to the right people through the right channels at the right time.

---

## Key Questions

1. **Who receives alerts — the traveler, the agent, the operations team, or all?**
2. **What notification channels are appropriate for different severity levels?**
3. **How do we avoid notification fatigue while ensuring critical alerts are never missed?**
4. **What escalation rules apply when an alert isn't acknowledged?**
5. **How do we deliver actionable alerts (with next steps) rather than just information?**

---

## Research Areas

### Notification Routing

```typescript
interface NotificationRule {
  ruleId: string;
  alertSeverity: AlertSeverity[];
  recipientRoles: RecipientRole[];
  channels: NotificationChannel[];
  templateId: string;
  escalation: EscalationRule;
  suppression: SuppressionRule;
}

type RecipientRole =
  | 'assigned_agent'      // Agent managing this trip
  | 'operations_team'     // Operations/support team
  | 'duty_manager'        // On-call manager
  | 'traveler'            // End traveler
  | 'group_coordinator'   // Group trip coordinator
  | 'corporate_travel';   // Corporate travel manager

type NotificationChannel =
  | 'in_app'              // Dashboard notification
  | 'push'                // Mobile push notification
  | 'sms'                 // SMS text message
  | 'whatsapp'            // WhatsApp message
  | 'email'               // Email notification
  | 'phone_call'          // Automated or manual phone call
  | 'slack'               // Slack/Teams notification
  | 'dashboard_alert';    // Persistent dashboard banner

// Severity-to-channel mapping:
// informational → in_app, email digest
// advisory → in_app, email, push
// warning → in_app, email, push, SMS
// critical → all channels + phone call
```

### Escalation Framework

```typescript
interface EscalationRule {
  steps: EscalationStep[];
  autoEscalate: boolean;
}

interface EscalationStep {
  stepNumber: number;
  triggerAfterMinutes: number;
  action: EscalationAction;
  escalateTo: RecipientRole[];
}

// Example for CRITICAL alert:
// Step 1: Notify assigned agent (immediate)
// Step 2: If not acknowledged in 15 min → operations team
// Step 3: If not acknowledged in 30 min → duty manager
// Step 4: If not acknowledged in 60 min → director + phone call
```

### Actionable Alert Content

```typescript
interface ActionableAlert {
  alertId: string;
  tripId: string;
  summary: string;                    // One-line summary
  details: string;                    // Full description
  impact: string;                     // What this means for the trip
  suggestedActions: SuggestedAction[];
  deadline?: Date;                    // Time by which action must be taken
  relatedBookings: string[];
  oneClickOptions: OneClickOption[];
}

interface SuggestedAction {
  action: string;
  effortLevel: 'immediate' | 'planned' | 'monitor';
  automated: boolean;
  cost?: number;
  description: string;
}

interface OneClickOption {
  label: string;
  action: 'rebook' | 'cancel' | 'reroute' | 'contact_supplier' | 'contact_traveler';
  preFilledData: Record<string, unknown>;
}
```

---

## Open Problems

1. **Traveler-facing alerts** — Should we send alerts directly to travelers, or always through agents? Direct alerts improve safety but may cause panic.

2. **Multi-timezone coordination** — An alert at 3 AM destination time. Do we wake the agent? The traveler? How do timezone preferences work?

3. **Alert aggregation for agents** — An agent managing 50 trips to Thailand during a flooding event gets 50 individual alerts. Need aggregation into "12 trips in affected area, 3 critical."

4. **Channel reliability** — SMS delivery in some countries is unreliable. WhatsApp has read receipts. Push notifications may be silenced. Need delivery confirmation and fallback channels.

5. **Post-alert tracking** — After an alert is sent, how do we track whether action was taken? Did the agent rebook? Is the traveler safe?

---

## Next Steps

- [ ] Design notification routing matrix by severity and role
- [ ] Research multi-channel notification services (Twilio, SendGrid, OneSignal)
- [ ] Create alert templates for top 10 alert scenarios
- [ ] Design escalation workflow with acknowledgment tracking
- [ ] Study how OTAs handle traveler communication during disruptions
