# Corporate Travel 02: Approval Workflows

> Multi-level approval processes for corporate travel

---

## Document Overview

**Focus:** Approval workflow design and implementation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Approval Triggers
- When are approvals required?
- What triggers different approval levels?
- How do we handle policy exceptions?
- What about emergency travel?

### 2. Approvers
- Who are the different approvers?
- How do we delegate approvers?
- What about approver unavailability?
- How do we handle approval chains?

### 3. Workflow Design
- What are the common workflow patterns?
- How do we handle parallel vs. sequential approvals?
- What about conditional approvals?
- How do we handle rejections?

### 4. User Experience
- How do requesters submit for approval?
- How do approvers review requests?
- What about mobile approvals?
- How do we handle urgent requests?

---

## Research Areas

### A. Approval Triggers

**Common Triggers:**

| Trigger | Description | Approval Level | Research Needed |
|---------|-------------|----------------|-----------------|
| **All bookings** | Everything needs approval | Manager | Small companies? |
| **Amount threshold** | Above X amount | Manager + Finance | Thresholds? |
| **Policy exception** | Outside policy | Manager + Travel Admin | ? |
| **International** | Cross-border travel | Manager | Some companies? |
| **Business class** | Premium cabin | Senior management | ? |
| **Last-minute** | < X days before travel | Manager | ? |
| **High-cost destination** | Expensive locations | Finance | ? |

**Trigger Examples:**

| Scenario | Trigger | Approval Chain | Research Needed |
|----------|---------|----------------|-----------------|
| **Domestic economy, within policy** | None | Auto-approve | Common? |
| **Domestic, > ₹50,000** | Amount | Manager → Finance | ? |
| **International, within policy** | International | Manager | ? |
| **Business class** | Class | Manager → Director | ? |
| **Outside policy hotel** | Policy exception | Manager → Travel Admin | ? |

**Emergency Travel:**

| Scenario | Handling | Research Needed |
|----------|----------|-----------------|
| **Same-day booking** | Expedited approval | Auto-approve with notification? |
| **Emergency travel** | Bypass or fast-track | What qualifies? |
| **C-level executive** | Auto-approve | Always? |

### B. Approvers

**Approver Types:**

| Type | Role | Responsibility | Research Needed |
|------|------|----------------|-----------------|
| **Manager** | Line manager | Team travel approvals | Can be anyone? |
| **Budget Owner** | Cost center owner | Budget-related approvals | Who is this? |
| **Travel Admin** | Travel manager | Policy compliance, exceptions | Full override? |
| **Finance** | Finance team | High-value, expense-related | Amount threshold? |
| **Executive** | Senior leadership | Major travel, policy exceptions | ? |

**Delegation:**

| Scenario | Handling | Research Needed |
|----------|----------|-----------------|
| **Manager on leave** | Delegate to backup | How to specify? |
| **No manager assigned** | Default approver | Travel admin? |
| **Matrix reporting** | Multiple managers | All need to approve? |

**Approver Actions:**

| Action | Description | Follow-up | Research Needed |
|--------|-------------|------------|-----------------|
| **Approve** | Request approved | Booking proceeds | ? |
| **Approve with changes** | Approved with modifications | Requester must accept | ? |
| **Reject** | Request denied | Reason required | ? |
| **Request changes** | More info needed | Requester responds | ? |
| **Delegate** | Pass to another approver | Workflow continues | ? |

### C. Workflow Patterns

**Sequential Approval:**

```
Request → Manager → Finance → Travel Admin → Approved
```

**Use Cases:**
- High-value bookings
- International travel
- Policy exceptions

**Parallel Approval:**

```
Request → Manager + Budget Owner → Approved
```

**Use Cases:**
- Where both managers need visibility
- Cross-departmental travel

**Conditional Approval:**

```
IF international THEN Manager ELSE auto-approve
IF amount > threshold THEN Manager + Finance
```

**Use Cases:**
- Complex policies
- Tiered approvals

**Research:**
- Which patterns are most common?
- How do companies design workflows?
- What about exceptions?

### D. Approval UX

**Requester Flow:**

```
1. Search and select travel
2. See if approval required (or find out after booking)
3. Submit for approval
   - Add justification if needed
   - See estimated approval time
4. Wait for approval
5. Receive notification (approved/rejected/changes requested)
6. If approved: proceed to booking
   If rejected: modify or cancel
   If changes: respond and resubmit
```

**Approver Flow:**

```
1. Receive notification (email/app)
2. View request details
   - Trip details
   - Cost breakdown
   - Policy comparison
   - Justification
3. Make decision
   - Approve
   - Reject with reason
   - Request changes
   - Delegate
4. System notifies requester
```

**Mobile Approvals:**

| Feature | Importance | Research Needed |
|----------|------------|-----------------|
| **Push notifications** | High | Real-time alerts |
| **One-tap approve** | High | Quick decisions |
| **View details** | Medium | Full context |
| **Comment** | Medium | Request changes |

---

## State Machine

**Approval State Machine:**

```
PENDING → SUBMITTED → IN_REVIEW →
                              ├── APPROVED → BOOKING_PROCEEDS
                              ├── APPROVED_WITH_CHANGES → CHANGES_REQUESTED → RESUBMITTED → IN_REVIEW
                              ├── REJECTED → REQUESTER_NOTIFIED → CANCELLED_OR_RESUBMITTED
                              ├── CHANGES_REQUESTED → AWAITING_RESPONSE → RESUBMITTED → IN_REVIEW
                              └── DELEGATED → AWAITING_DELEGATE → IN_REVIEW
```

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface ApprovalRequest {
  id: string;
  companyId: string;
  bookingId?: string;
  tripId?: string;

  // Request details
  requesterId: string;
  submittedAt: Date;
  status: ApprovalStatus;

  // Trip details
  tripDetails: TripApprovalDetails;

  // Policy
  policyCompliance: PolicyCompliance;

  // Workflow
  workflow: ApprovalWorkflow;

  // Justification
  justification?: string;
  businessReason?: string;

  // Current step
  currentStep: number;
}

type ApprovalStatus =
  | 'pending'
  | 'submitted'
  | 'in_review'
  | 'approved'
  | 'approved_with_changes'
  | 'rejected'
  | 'changes_requested'
  | 'awaiting_response'
  | 'delegated'
  | 'cancelled';

interface ApprovalWorkflow {
  steps: ApprovalStep[];
  currentStep: number;
  createdAt: Date;
  updatedAt: Date;
}

interface ApprovalStep {
  stepNumber: number;
  approverType: ApproverType;
  approverId?: string; // Specific user if applicable

  // Status
  status: StepStatus;
  completedAt?: Date;
  decision?: ApprovalDecision;
  comments?: string;
}

type StepStatus =
  | 'pending'
  | 'in_progress'
  | 'approved'
  | 'rejected'
  | 'delegated'
  | 'skipped';

type ApprovalDecision =
  | { type: 'approved' }
  | { type: 'approved_with_changes'; changes: string[] }
  | { type: 'rejected'; reason: string }
  | { type: 'changes_requested'; questions: string[] }
  | { type: 'delegated'; to: string };

interface TripApprovalDetails {
  // Trip summary
  tripType: 'domestic' | 'international';
  dates: { start: Date; end: Date };
  destinations: string[];

  // Cost
  estimatedCost: Money;
  costBreakdown: CostBreakdown[];

  // Components
  flights: FlightApproval[];
  hotels: HotelApproval[];
  other: OtherApproval[];

  // Policy comparison
  withinPolicy: boolean;
  policyExceptions: PolicyException[];
}

interface PolicyCompliance {
  withinPolicy: boolean;
  exceptions: PolicyException[];
  warnings: string[];
}

interface PolicyException {
  type: 'class_of_service' | 'hotel_category' | 'advance_booking' | 'cost' | 'other';
  description: string;
  justification?: string;
}
```

---

## Open Problems

### 1. Approval Bottlenecks
**Challenge:** Approvers are busy, delays happen

**Options:**
- Push notifications
- Escalation timeouts
- Backup approvers
- Auto-approve low-risk

### 2. Complex Policies
**Challenge:** Determining if approval is needed is complex

**Options:**
- Simple rules engine
- Clear UI indicators
- Explain why approval needed
- Pre-trip policy check

### 3. Urgent Travel
**Challenge:** Last-minute travel can't wait for approvals

**Options:**
- Fast-track approvals
- Auto-approve with post-trip review
- Emergency contacts
- Mobile-first approval

### 4. Approval Fatigue
**Challenge:** Too many minor approvals

**Options:**
- Auto-approve low-risk bookings
- Batch approvals
- Spend limits without approval
- Trust-based approvals

---

## Competitor Research Needed

| Competitor | Approval UX | Notable Patterns |
|------------|-------------|------------------|
| **Concur** | ? | ? |
| **TravelPerk** | ? | ? |
| **Navan** | ? | ? |

---

## Experiments to Run

1. **Approval timing test:** How long do approvals take?
2. **Mobile approval test:** Do approvers use mobile?
3. **Bottleneck analysis:** Where do delays happen?
4. **Policy clarity test:** Do requesters understand when approval is needed?

---

## References

- [Corporate Travel - Requirements](./CORPORATE_01_REQUIREMENTS.md) — Policy structures
- [Trip Builder - Collaboration](./TRIP_BUILDER_04_COLLABORATION.md) — Similar patterns

---

## Next Steps

1. Design approval workflow engine
2. Build approval UI
3. Implement notification system
4. Create mobile approval flow
5. Measure approval metrics

---

**Status:** Research Phase — Approval patterns unknown

**Last Updated:** 2026-04-27
