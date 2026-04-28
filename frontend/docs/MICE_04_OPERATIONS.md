# MICE Operations — On-Site Operations & Post-Event

> Research document for event execution, on-site management, and post-event analysis.

---

## Key Questions

1. **What's the operational checklist for event day execution?**
2. **How do we handle real-time issues and emergencies during events?**
3. **What post-event activities are essential (settlement, feedback, documentation)?**
4. **How do we measure MICE event success?**
5. **What's the settlement and invoicing workflow for multi-vendor events?**

---

## Research Areas

### On-Site Operations

```typescript
interface OnSiteOps {
  eventId: string;
  opsLead: string;
  team: OpsTeamMember[];
  checklists: OpsChecklist[];
  communicationPlan: CommunicationPlan;
  emergencyProtocol: EmergencyProtocol;
  issueLog: Issue[];
}

interface OpsTeamMember {
  name: string;
  role: string;
  responsibilities: string[];
  contactNumber: string;
  location: string;
  shift: TimeRange;
}

interface OpsChecklist {
  phase: 'pre_event' | 'setup' | 'event_day' | 'teardown' | 'post_event';
  items: ChecklistItem[];
}

interface ChecklistItem {
  itemId: string;
  task: string;
  assignedTo: string;
  deadline: Date;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  notes: string;
}
```

### Issue Management During Events

```typescript
interface EventIssue {
  issueId: string;
  eventId: string;
  reportedAt: Date;
  reportedBy: string;
  category: IssueCategory;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  impact: string;
  assignedTo: string;
  status: 'open' | 'in_progress' | 'resolved' | 'escalated';
  resolution?: string;
  resolvedAt?: Date;
  clientNotified: boolean;
}

type IssueCategory =
  | 'venue'           // Room not ready, capacity issue, AC failure
  | 'catering'        // Food quality, quantity, timing
  | 'av_technology'   // Equipment failure, connectivity
  | 'transport'       // Vehicle delay, no-show
  | 'accommodation'   // Room issues, check-in problems
  | 'safety'          // Medical emergency, security concern
  | 'weather'         // Rain, storm affecting outdoor events
  | 'vendor'          // Vendor no-show, quality issue
  | 'attendee'        // Registration, special needs, complaint
  | 'other';
```

### Post-Event Workflow

```typescript
interface PostEventProcess {
  eventId: string;
  settlement: EventSettlement;
  feedback: EventFeedback[];
  documentation: PostEventDocumentation;
  lessonsLearned: LessonLearned[];
}

interface EventSettlement {
  totalBudget: number;
  totalCommitted: number;
  totalInvoiced: number;
  totalPaid: number;
  pendingInvoices: InvoiceSummary[];
  outstandingPayments: OutstandingPayment[];
  reconciliationStatus: 'pending' | 'in_progress' | 'completed';
}

interface InvoiceSummary {
  vendorId: string;
  vendorName: string;
  invoiceNumber: string;
  amount: number;
  status: 'received' | 'verified' | 'approved' | 'paid' | 'disputed';
  discrepancy?: string;
}

interface EventFeedback {
  source: 'attendee' | 'client' | 'internal' | 'vendor';
  overallRating: number;
  categoryRatings: { category: string; rating: number }[];
  highlights: string[];
  improvements: string[];
  wouldRepeat: boolean;
  nps: number;
}
```

### Event Success Metrics

```typescript
interface EventMetrics {
  eventId: string;
  financial: FinancialMetrics;
  satisfaction: SatisfactionMetrics;
  operational: OperationalMetrics;
  business: BusinessMetrics;
}

interface FinancialMetrics {
  budgetVariance: number;        // % over/under budget
  costPerAttendee: number;
  revenueGenerated?: number;     // For ticketed events
  roi?: number;                  // Client-calculated ROI
}

interface SatisfactionMetrics {
  attendeeNPS: number;
  clientSatisfaction: number;     // 1-10
  wouldRepeatRate: number;        // %
  complaintRate: number;          // Complaints per 100 attendees
}

interface OperationalMetrics {
  taskCompletionRate: number;     // % of planned tasks completed on time
  issueCount: number;
  criticalIssueCount: number;
  averageIssueResolutionTime: number;  // Minutes
  vendorPerformanceScore: number;
}

interface BusinessMetrics {
  repeatBookingRate: number;      // % of clients who book again
  referralGenerated: boolean;
  upsellRevenue: number;
  crossSellSuccess: number;       // Other services sold
}
```

---

## Open Problems

1. **Multi-vendor settlement** — A single event may involve 10-15 vendors, each with separate invoices, advance payments, and retention amounts. Reconciliation is complex.

2. **Real-time issue escalation** — During a live event, issue resolution speed is critical. How to enable rapid communication without creating noise?

3. **Post-event data collection** — Attendee feedback response rates are typically low (10-20%). How to increase engagement with post-event surveys?

4. **Knowledge capture** — Experienced event planners carry institutional knowledge. How to capture lessons learned in a structured, searchable format?

5. **Vendor settlement disputes** — Post-event, vendors may dispute quantities, quality claims, or deductions. Need a structured dispute resolution workflow.

6. **Crisis management** — What's the playbook for event-cancelling crises (weather, safety incidents, political unrest)?

---

## Next Steps

- [ ] Research event operations management tools (Bizzabo, SpotMe, Attendify)
- [ ] Design post-event settlement workflow with multi-vendor reconciliation
- [ ] Study crisis management playbooks for events
- [ ] Create event feedback survey templates
- [ ] Investigate automated issue logging from on-ground team inputs
- [ ] Design lessons-learned knowledge base structure
