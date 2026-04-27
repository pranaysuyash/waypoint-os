# Help Desk & Ticketing 01: Tickets

> Support ticket creation, management, and resolution

---

## Document Overview

**Focus:** Ticket lifecycle management
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Ticket Creation
- How do customers create tickets?
- What information is required?
- How do we categorize tickets?
- What about automatic routing?

### Ticket Management
- How do agents work with tickets?
- What about priorities and SLAs?
- How do we handle assignments?
- What about collaboration?

### Resolution
- How do tickets get resolved?
- What about customer satisfaction?
- How do we handle escalations?
- What about closure processes?

### Communication
- How do we talk to customers?
- What about multi-channel support?
- How do we handle internal notes?
- What about templates?

---

## Research Areas

### A. Ticket Creation

**Ticket Sources:**

| Source | Method | Research Needed |
|--------|--------|-----------------|
| **Email** | Support email | ? |
| **Web form** | Self-service portal | ? |
| **WhatsApp** | Chat integration | ? |
| **Phone** | Agent creates ticket | ? |
| **In-app** | From application | ? |
| **Social** | Facebook, Twitter | ? |

**Required Information:**

| Field | Required | Purpose | Research Needed |
|-------|----------|---------|-----------------|
| **Name** | Yes | Identification | ? |
| **Email** | Yes | Communication | ? |
| **Phone** | No | Callback | ? |
| **Booking ID** | No | Context | ? |
| **Category** | Yes | Routing | ? |
| **Subject** | Yes | Summary | ? |
| **Description** | Yes | Details | ? |
| **Priority** | No | Triaging | ? |
| **Attachments** | No | Evidence | ? |

**Automatic Routing:**

| Rule | Route To | Research Needed |
|------|----------|-----------------|
| **Booking issue** | Reservations team | ? |
| **Payment problem** | Billing team | ? |
| **Technical issue** | Tech support | ? |
| **Complaint** | Senior agents | ? |
| **VIP customer** | Priority queue | ? |

**Categorization:**

| Category | Subcategories | Research Needed |
|----------|--------------|-----------------|
| **Bookings** | Changes, cancellations, confirmations | ? |
| **Payments** | Refunds, disputes, invoices | ? |
| **Technical** | Login, bugs, errors | ? |
| **Information** | Questions, requests | ? |
| **Complaints** | Service, quality, behavior | ? |

### B. Ticket Management

**Ticket Statuses:**

| Status | Description | Next Status | Research Needed |
|--------|-------------|-------------|-----------------|
| **New** | Just created | Open, Assigned | ? |
| **Open** | Being worked | Pending, Resolved | ? |
| **Pending** | Awaiting customer | Open, Closed | ? |
| **Resolved** | Solution provided | Closed, Reopened | ? |
| **Closed** | Complete | Reopened | ? |
| **Reopened** | Came back | Open | ? |

**Priority Levels:**

| Level | Response Time | Use Case | Research Needed |
|-------|---------------|----------|-----------------|
| **Critical** | < 1 hour | Travel disruptions | ? |
| **High** | < 4 hours | Urgent issues | ? |
| **Medium** | < 24 hours | Standard issues | ? |
| **Low** | < 48 hours | Questions | ? |

**Assignment Methods:**

| Method | When Used | Research Needed |
|--------|-----------|-----------------|
| **Automatic** | Rule-based routing | ? |
| **Round-robin** | Equal distribution | ? |
| **Skill-based** | Match expertise | ? |
| **Manual** | Complex issues | ? |
| **Self-assign** | Agent picks | ? |

**Collaboration:**

| Feature | Purpose | Research Needed |
|---------|---------|-----------------|
| **Internal notes** | Agent-to-agent | ? |
| **Mentions** | Notify colleagues | ? |
| **Linked tickets** | Related issues | ? |
| **Merging** | Duplicate tickets | ? |
| **Followers** | Keep informed | ? |

### C. Resolution

**Resolution Process:**

```
1. Understand
   → Read ticket
   → Gather context
   → Ask clarifying questions

2. Investigate
   → Check systems
   → Consult colleagues
   → Research solutions

3. Resolve
   → Apply fix
   → Communicate solution
   → Verify with customer

4. Close
   → Confirm satisfaction
   → Document solution
   → Close ticket
```

**Resolution Categories:**

| Category | Example | Research Needed |
|----------|---------|-----------------|
| **Solved** | Issue fixed | ? |
| **Workaround** | Temporary fix | ? |
| **Information** | Answered question | ? |
| **Duplicate** | Already exists | ? |
| **Not reproducible** | Can't replicate | ? |
| **User error** | Education needed | ? |

**Customer Satisfaction:**

| Metric | Measurement | Research Needed |
|--------|-------------|-----------------|
| **CSAT** | Rating 1-5 | ? |
| **NPS** | Likely to recommend | ? |
| **CES** | Effort to solve | ? |
| **First contact** | Resolved on first try | ? |

**Escalation:**

| Trigger | Escalate To | Research Needed |
|---------|------------|-----------------|
| **SLA breach risk** | Team lead | ? |
| **VIP customer** | Senior agent | ? |
| **Complex issue** | Specialist | ? |
| **Unresolved** | Manager | ? |
| **Complaint** | Customer service | ? |

### D. Communication

**Customer Communication:**

| Channel | Best For | Research Needed |
|---------|----------|-----------------|
| **Email** | Detailed issues | ? |
| **WhatsApp** | Quick updates | ? |
| **Phone** | Complex problems | ? |
| **Portal** | Self-service updates | ? |

**Response Templates:**

| Template | Use | Research Needed |
|----------|-----|-----------------|
| **Acknowledgment** | We received your ticket | ? |
| **Investigating** | We're looking into it | ? |
| **Resolution** | Here's the fix | ? |
| **More info needed** | Please provide X | ? |
| **Escalation** | Passed to specialist | ? |
| **Closure** | Ticket closed | ? |

**Internal Notes:**

| Type | Use | Research Needed |
|------|-----|-----------------|
| **Private** | Internal only | ? |
| **Visible to team** | All agents | ? |
| **Visible to customer** | Public response | ? |

**Macros:**

| Macro | Expands To | Research Needed |
|-------|------------|-----------------|
| **Booking lookup** | Find booking details | ? |
| **Refund policy** | Policy text | ? |
| **Cancellation steps** | Step-by-step | ? |
| **Common issue** | Standard response | ? |

---

## Data Model Sketch

```typescript
interface SupportTicket {
  ticketId: string;
  agencyId: string;

  // Customer
  customerId?: string;
  customerName: string;
  customerEmail: string;
  customerPhone?: string;

  // Context
  bookingId?: string;
  tripId?: string;

  // Details
  category: TicketCategory;
  subcategory?: string;
  subject: string;
  description: string;
  priority: TicketPriority;

  // Status
  status: TicketStatus;
  resolution?: TicketResolution;

  // Assignment
  assignedTo?: string; // Agent ID
  team?: string;
  assignedAt?: Date;

  // SLA
  sla?: SLA;
  slaBreachAt?: Date;
  breached: boolean;

  // Timing
  createdAt: Date;
  firstResponseAt?: Date;
  resolvedAt?: Date;
  closedAt?: Date;

  // Satisfaction
  satisfactionRating?: number; // 1-5
  satisfactionFeedback?: string;

  // Metadata
  source: TicketSource;
  channel: CommunicationChannel;
  tags: string[];
  attachments: Attachment[];
}

type TicketCategory =
  | 'bookings'
  | 'payments'
  | 'technical'
  | 'information'
  | 'complaints'
  | 'other';

type TicketPriority = 'critical' | 'high' | 'medium' | 'low';

type TicketStatus =
  | 'new'
  | 'open'
  | 'pending'
  | 'resolved'
  | 'closed'
  | 'reopened';

type TicketResolution =
  | 'solved'
  | 'workaround'
  | 'information'
  | 'duplicate'
  | 'not_reproducible'
  | 'user_error';

type TicketSource =
  | 'email'
  | 'web_form'
  | 'whatsapp'
  | 'phone'
  | 'in_app'
  | 'social';

interface TicketComment {
  commentId: string;
  ticketId: string;

  // Author
  authorId: string;
  authorName: string;
  authorType: 'customer' | 'agent' | 'system';

  // Content
  content: string;
  internal: boolean; // Not visible to customer

  // Attachments
  attachments: Attachment[];

  // Customer notification
  notifyCustomer: boolean;

  // Timing
  createdAt: Date;
}

interface SLA {
  slaId: string;
  name: string;

  // Response
  firstResponseTarget: number; // Minutes
  resolutionTarget: number; // Hours

  // Schedule
  businessHoursOnly: boolean;
  timezone: string;

  // Calendar
  workingDays: number[]; // 0-6 (Sun-Sat)
  workingHours: {
    start: string; // HH:mm
    end: string;
  };

  // Holidays
  holidays: Date[];
}

interface TicketWorkflow {
  workflowId: string;
  name: string;
  trigger: WorkflowTrigger;

  // Steps
  steps: WorkflowStep[];

  // Auto-actions
  autoAssignTo?: string;
  autoReply?: string;
  autoTag?: string[];
}

interface WorkflowStep {
  stepId: string;
  name: string;
  action: WorkflowAction;
  conditions?: StepCondition[];
}

interface WorkflowAction {
  type: 'assign' | 'notify' | 'escalate' | 'close' | 'tag';
  target?: string;
  message?: string;
}

interface SatisfactionSurvey {
  surveyId: string;
  ticketId: string;
  sentAt: Date;
  respondedAt?: Date;

  // Questions
  rating?: number; // 1-5
  likelihoodToRecommend?: number; // 0-10
  effortScore?: number; // 1-5

  // Feedback
  feedback?: string;

  // Follow-up
  followUpRequired: boolean;
  followUpAction?: string;
}
```

---

## Open Problems

### 1. Ticket Volume
**Challenge:** Too many tickets

**Options:** Self-service, automation, deflection

### 2. Response Time
**Challenge:** Customers want instant responses

**Options:** Chatbots, auto-replies, more staff

### 3. Quality Consistency
**Challenge:** Different agents, different quality

**Options:** Templates, training, QA

### 4. Knowledge Sharing
**Challenge:** Solutions not shared

**Options:** Knowledge base, searchable history, collaboration

### 5. Customer Expectations
**Challenge**: Expectations continue to rise

**Options:** Clear communication, proactive updates, transparency

---

## Next Steps

1. Define ticket workflow
2. Build ticket management UI
3. Implement SLA tracking
4. Create template library

---

**Status:** Research Phase — Ticket patterns unknown

**Last Updated:** 2026-04-28
