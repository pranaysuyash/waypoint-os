# Commission Management 02: Tracking

> Commission accrual, status tracking, and earning management

---

## Document Overview

**Focus:** Commission tracking and status management
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Accrual Process
- How do commissions accrue?
- When is tracking initiated?
- How do we track partial payments?
- What about pending commissions?

### Status Management
- What are commission statuses?
- How do statuses transition?
- What triggers status changes?
- How do we handle holds?

### Visibility
- How do agents see their commissions?
- What information is shown?
- How is real-time status provided?
- What about historical tracking?

### Disputes
- How are commission disputes handled?
- What evidence is needed?
- Who resolves disputes?
- What are the outcomes?

---

## Research Areas

### A. Accrual Workflow

**Tracking Initiation:**

| Trigger | Action | Research Needed |
|---------|--------|-----------------|
| **Booking created** | Create commission record | ? |
| **Booking modified** | Recalculate commission | ? |
| **Payment received** | Update status | ? |
| **Service consumed** | Mark as earned | ? |

**Accrual Timeline:**

```
Booking Created
    ↓
Commission Calculated (Pending)
    ↓
Payment Received (Held)
    ↓
Holding Period (Held)
    ↓
Service Consumed (Earned)
    ↓
Payout Ready (Payable)
```

**Partial Tracking:**

| Scenario | Handling | Research Needed |
|----------|----------|-----------------|
| **Partial payment** | Proportional accrual | ? |
| **Installment booking** | Track per installment | ? |
| **Split commission** | Track per recipient | ? |

### B. Status Definitions

**Commission Lifecycle:**

| Status | Description | Can Transition To | Research Needed |
|--------|-------------|-------------------|-----------------|
| **Pending** | Initial, not confirmed | Held, Cancelled | ? |
| **Held** | Awaiting earning trigger | Earned, Clawed Back | ? |
| **Earned** | Ready for payout | Payable, Adjusted | ? |
| **Payable** | Approved for payment | Paid | ? |
| **Paid** | Payment complete | — | ? |
| **Clawed Back** | Reversed | — | ? |
| **Disputed** | Under review | Earned, Cancelled | ? |

**Status Transitions:**

| Transition | Trigger | Research Needed |
|------------|---------|-----------------|
| Pending → Held | Payment received | ? |
| Held → Earned | Service consumed + hold period | ? |
| Earned → Payable | Payout calculation complete | ? |
| Payable → Paid | Payment processed | ? |
| Any → Clawed Back | Cancellation/refund | ? |
| Any → Disputed | Agent raises dispute | ? |

### C. Agent Visibility

**Dashboard View:**

| Metric | Display | Research Needed |
|--------|---------|-----------------|
| **Total earned** | This period | ? |
| **Pending** | Not yet earned | ? |
| **Payable** | Awaiting payout | ? |
| **Recent activity** | Latest commissions | ? |

**Commission Detail:**

| Field | Display | Research Needed |
|-------|---------|-----------------|
| **Booking ID** | Link to booking | ? |
| **Customer** | Name | ? |
| **Amount** | Booking value | ? |
| **Rate** | Applied rate | ? |
| **Commission** | Calculated amount | ? |
| **Status** | Current status | ? |
| **Expected payout** | Date | ? |

**Tracking Views:**

| View | Purpose | Research Needed |
|------|---------|-----------------|
| **Summary** | Period overview | ? |
| **By booking** | Detailed list | ? |
| **By supplier** | Supplier breakdown | ? |
| **By status** | Filtered list | ? |

### D. Dispute Management

**Dispute Reasons:**

| Reason | Description | Research Needed |
|--------|-------------|-----------------|
| **Wrong amount** | Calculation error | ? |
| **Wrong rate** | Incorrect rate applied | ? |
| **Missing commission** | Not tracked | ? |
| **Split issue** | Unfair split | ? |
| **Clawback dispute** | Wrongly reversed | ? |

**Dispute Workflow:**

```
1. Agent raises dispute
   → Reason, evidence

2. Admin notified
   → Review booking
   → Verify calculation

3. Resolution
   → Adjust commission
   → Reject dispute
   → Escalate

4. Communication
   → Notify agent
   → Update status
```

**Evidence Types:**

| Evidence | Acceptable | Research Needed |
|----------|------------|-----------------|
| **Booking confirmation** | Yes | ? |
| **Supplier commission statement** | Yes | ? |
| **Communication** | Sometimes | ? |
| **Screenshots** | Sometimes | ? |

---

## Data Model Sketch

```typescript
interface CommissionTracking {
  commissionId: string;
  bookingId: string;
  agentId: string;

  // Calculation
  bookingAmount: number;
  commissionableAmount: number;
  rate: number;
  commissionAmount: number;

  // Status
  status: CommissionStatus;
  previousStatus?: CommissionStatus;

  // Timing
  createdAt: Date;
  earnedAt?: Date;
  payableAt?: Date;
  paidAt?: Date;

  // Payout
  payoutBatchId?: string;

  // Adjustments
  originalAmount?: number; // Before adjustments
  adjustments: CommissionAdjustment[];

  // Dispute
  dispute?: CommissionDispute;
}

interface CommissionAdjustment {
  adjustmentId: string;
  type: AdjustmentType;
  amount: number;
  reason: string;
  createdAt: Date;
  createdBy: string;
}

type AdjustmentType =
  | 'correction'
  | 'bonus'
  | 'penalty'
  | 'clawback'
  | 'manual_override';

interface CommissionDispute {
  disputeId: string;
  commissionId: string;

  // Details
  reason: DisputeReason;
  description: string;
  evidence: string[]; // File URLs

  // Status
  status: DisputeStatus;

  // Resolution
  resolution?: DisputeResolution;
  resolvedAt?: Date;
  resolvedBy?: string;

  // Timing
  raisedAt: Date;
  raisedBy: string;
}

type DisputeReason =
  | 'wrong_amount'
  | 'wrong_rate'
  | 'missing_commission'
  | 'split_issue'
  | 'clawback_dispute'
  | 'other';

type DisputeStatus =
  | 'open'
  | 'under_review'
  | 'resolved'
  | 'rejected';

interface AgentCommissionView {
  agentId: string;
  period: DateRange;

  // Summary
  totalEarned: number;
  totalPending: number;
  totalPayable: number;
  totalPaid: number;

  // Breakdown
  byStatus: Map<CommissionStatus, number>;
  bySupplier: Map<string, number>;
  byProduct: Map<ProductType, number>;

  // Commissions
  commissions: CommissionTracking[];
}
```

---

## Open Problems

### 1. Real-time Updates
**Challenge:** Agents want to see changes immediately

**Options:** Websockets, polling, periodic refresh

### 2. Historical Accuracy
**Challenge:** Rates change, need historical accuracy

**Options:** Versioning, snapshots, effective dating

### 3. Complex Splits
**Challenge:** Multiple agents with varying splits

**Options:** Workflow approval, audit trail, clear documentation

### 4. Dispute Volume
**Challenge:** Many disputes can overwhelm

**Options:** Self-service tools, clear documentation, fast resolution

### 5. Supplier Delays
**Challenge:** Supplier doesn't pay on time

**Options:** Pay anyway, track receivables, risk management

---

## Next Steps

1. Define commission lifecycle
2. Build tracking dashboard
3. Implement dispute workflow
4. Create notification system

---

**Status:** Research Phase — Tracking patterns unknown

**Last Updated:** 2026-04-27
