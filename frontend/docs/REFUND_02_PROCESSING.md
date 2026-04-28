# Refund & Cancellation Management — Processing & Workflows

> Research document for refund processing, payment reconciliation, and cancellation workflow automation.

---

## Key Questions

1. **What's the end-to-end refund processing workflow?**
2. **How do refunds flow through the payment chain (customer → agency → supplier)?**
3. **What's the partial refund model for multi-component trips?**
4. **How do we handle refund exceptions and disputes?**
5. **What's the refund tracking and audit model?**

---

## Research Areas

### Refund Processing Pipeline

```typescript
interface RefundProcess {
  refundId: string;
  cancellationId: string;
  status: RefundStatus;
  items: RefundItem[];
  totalRefundAmount: Money;
  refundMethod: RefundMethod;
  timeline: RefundTimeline;
  auditTrail: RefundAuditEntry[];
}

type RefundStatus =
  | 'initiated'
  | 'approved'
  | 'processing'
  | 'partial_completed'
  | 'completed'
  | 'failed'
  | 'disputed';

interface RefundItem {
  itemId: string;
  bookingItemId: string;
  serviceType: ServiceType;
  originalAmount: Money;
  penaltyAmount: Money;
  refundAmount: Money;
  supplierRefund: SupplierRefund;
  agencyRefund: AgencyRefund;
  status: ItemRefundStatus;
}

// Refund chain:
// Customer ← Agency ← Platform ← Payment Gateway ← Supplier
//
// Flow:
// 1. Customer requests cancellation → Agent processes
// 2. System calculates refund quote (penalties per component)
// 3. Agent/customer confirms cancellation
// 4. Platform initiates refund:
//    a. Cancel with supplier (hotel, airline, activity provider)
//    b. Confirm supplier cancellation and refund eligibility
//    c. Calculate agency portion (markup, commission clawback)
//    d. Initiate refund to customer's original payment method
//    e. Track refund until customer receives funds
//
// Refund timing:
// Agency → Customer: 3-7 business days (payment gateway processing)
// Supplier → Agency: 7-30 business days (varies by supplier)
// Agency bears the float during the gap

interface RefundTimeline {
  initiatedAt: Date;
  approvedAt?: Date;
  supplierCancelledAt?: Date;
  supplierRefundExpectedBy?: Date;
  supplierRefundReceivedAt?: Date;
  customerRefundInitiatedAt?: Date;
  customerRefundCompletedAt?: Date;
  totalDaysToCompletion?: number;
}
```

### Payment Chain Reconciliation

```typescript
interface RefundReconciliation {
  refundId: string;
  payments: PaymentChainEntry[];
  reconciliationStatus: 'pending' | 'reconciled' | 'discrepancy';
  discrepancies?: RefundDiscrepancy[];
}

interface PaymentChainEntry {
  layer: string;                     // "customer", "agency", "platform", "supplier"
  originalPayment: Money;
  refundOwed: Money;
  refundPaid: Money;
  stillPending: Money;
  dueDate: Date;
  status: 'pending' | 'partial' | 'completed';
}

// Reconciliation scenarios:
//
// Simple: Customer paid ₹1,00,000 for a hotel
//   Cancellation penalty: ₹15,000 (1 night)
//   Refund to customer: ₹85,000
//   Agency paid hotel: ₹85,000 (after markup removal)
//   Hotel refunds agency: ₹85,000
//   Net: Customer gets ₹85,000, Agency gets ₹0 (penalty goes to hotel)
//
// Complex: Multi-component trip, partial cancellation
//   Customer paid ₹3,50,000 total:
//     Flight: ₹1,20,000 (penalty: ₹24,000 → ₹96,000 refund)
//     Hotel: ₹1,50,000 (penalty: ₹15,000 → ₹1,35,000 refund)
//     Activity: ₹30,000 (full refund)
//     Transfer: ₹20,000 (full refund)
//     Insurance: ₹30,000 (refund as per policy)
//   Total refund: ₹3,11,000
//   Total penalty: ₹39,000
//
//   Each component has different refund timeline:
//     Flight refund: 7-15 days (airline processes)
//     Hotel refund: 3-7 days (hotel confirms)
//     Activity refund: 1-3 days (operator confirms)
//     Insurance refund: 15-30 days (insurance company)

interface RefundDiscrepancy {
  type: DiscrepancyType;
  expected: Money;
  actual: Money;
  reason: string;
  resolution?: string;
}

type DiscrepancyType =
  | 'amount_mismatch'                // Supplier refunded different amount
  | 'currency_difference'            // Forex rate changed between payment and refund
  | 'delayed_refund'                 // Supplier refund overdue
  | 'missing_refund'                 // Supplier confirmed cancellation but no refund
  | 'commission_clawback';           // Commission needs to be reversed
```

### Cancellation Workflow Automation

```typescript
interface CancellationWorkflow {
  workflowId: string;
  trigger: CancellationTrigger;
  steps: WorkflowStep[];
  notifications: CancellationNotification[];
}

type CancellationTrigger =
  | 'customer_request'               // Customer initiated
  | 'agent_initiated'                // Agent cancelled on behalf of customer
  | 'supplier_initiated'             // Supplier cancelled (airline, hotel)
  | 'system_initiated'               // Automated (payment failure, policy violation)
  | 'force_majeure'                  // Natural disaster, pandemic, government order
  | 'no_show';                       // Customer didn't show up

// Automated steps on cancellation:
// 1. Calculate penalties and refund
// 2. Cancel with each supplier (API call where possible)
// 3. Release inventory (make cancelled items available again)
// 4. Process refund to customer
// 5. Reverse commission for the agent
// 6. Update trip status
// 7. Send notification to customer
// 8. Send notification to agent
// 9. Update accounting (Tally sync)
// 10. Generate cancellation invoice
// 11. Log audit entry
// 12. Update customer timeline

// Notification templates:
// Customer: "Your booking for [hotel] has been cancelled. Refund of ₹[amount]
//            will be processed within [X] business days to your [payment method]."
// Agent: "Trip [ID] cancelled by customer. Refund: ₹[amount]. Penalty: ₹[amount].
//         Commission reversal: ₹[amount]."
// Supplier: "Cancellation request for booking [ID]. Please confirm and process refund."
```

### Dispute Resolution

```typescript
interface RefundDispute {
  disputeId: string;
  refundId: string;
  initiatedBy: 'customer' | 'agent' | 'supplier';
  reason: string;
  evidence: DisputeEvidence[];
  status: DisputeStatus;
  resolution?: DisputeResolution;
}

type DisputeStatus =
  | 'raised'
  | 'under_review'
  | 'escalated'
  | 'resolved'
  | 'closed';

// Common dispute scenarios:
// 1. "I cancelled within the free window but was charged a penalty"
//    → Agent checks policy, timing, and booking terms
//
// 2. "The airline cancelled my flight, I should get a full refund"
//    → Verify airline cancellation, apply full refund policy
//
// 3. "I was told the hotel was refundable but it wasn't"
//    → Check booking confirmation terms, agent notes
//
// 4. "Refund was promised in 7 days, it's been 14 days"
//    → Track refund in payment chain, identify bottleneck
//
// 5. "The cancellation penalty seems too high"
//    → Review policy applied, check for errors

// Dispute escalation path:
// Level 1: Agent reviews and resolves (most disputes)
// Level 2: Team lead reviews if agent can't resolve
// Level 3: Manager/owner decision for high-value disputes
// Level 4: Legal/consumer forum for ₹50K+ disputes
```

---

## Open Problems

1. **Refund float risk** — Agency refunds customer immediately but waits 30 days for supplier refund. For ₹10L+ trips, this is significant cash flow impact.

2. **Commission clawback complexity** — Agent earned ₹15,000 commission on a booking that was then cancelled. Should the full commission be reversed? What if it was a supplier-initiated cancellation?

3. **Partial cancellation accounting** — When one component of a package is cancelled, how does the margin recalculate? The original package had a blended margin.

4. **Refund method disputes** — Customer wants refund to credit card but booking was paid via UPI. Or customer wants cash but agency policy is credit note.

5. **Cross-border refund regulations** — RBI guidelines on international refunds, LRS reversal, TCS refund process.

---

## Next Steps

- [ ] Design refund processing pipeline with payment chain tracking
- [ ] Build cancellation workflow automation with supplier API integration
- [ ] Create refund reconciliation system with discrepancy detection
- [ ] Design dispute resolution workflow with escalation paths
- [ ] Study refund UX (Razorpay refunds, Airbnb cancellation, Booking.com)
