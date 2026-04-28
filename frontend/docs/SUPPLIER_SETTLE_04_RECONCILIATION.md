# Supplier Invoice & Settlement — Reconciliation & Dispute Resolution

> Research document for supplier statement reconciliation, payment verification, dispute workflows, and settlement reporting.

---

## Key Questions

1. **How do we reconcile supplier statements against our records?**
2. **What's the dispute resolution workflow for supplier disagreements?**
3. **How do we track outstanding balances and aging per supplier?**
4. **What settlement reporting is needed for agency management?**
5. **How do we handle year-end supplier reconciliation?**

---

## Research Areas

### Supplier Statement Reconciliation

```typescript
interface SupplierReconciliation {
  supplierId: string;
  period: DateRange;
  supplierStatement: SupplierStatement;
  platformRecords: PlatformRecords;
  matching: ReconciliationResult;
  exceptions: ReconciliationException[];
  adjustments: ReconciliationAdjustment[];
}

interface SupplierStatement {
  supplierId: string;
  statementDate: Date;
  openingBalance: Money;
  transactions: StatementTransaction[];
  closingBalance: Money;
  currency: string;
}

interface StatementTransaction {
  date: Date;
  type: 'invoice' | 'credit_note' | 'payment' | 'adjustment';
  reference: string;
  description: string;
  amount: Money;
  balance: Money;
}

// Supplier reconciliation process:
// 1. Receive supplier statement (monthly or on-demand)
// 2. Import statement into platform (upload PDF/Excel or manual entry)
// 3. Auto-match statement transactions to platform records:
//    a. Invoices: Match supplier invoice to platform booking
//    b. Payments: Match supplier's payment receipt to our payment records
//    c. Credit notes: Match to platform credit note records
//    d. Adjustments: Identify unmatched items
// 4. Calculate: Our balance vs. Supplier's balance
// 5. Investigate differences
// 6. Resolve: Create adjustments or dispute items
// 7. Confirm: Both sides agree on balance
//
// Reconciliation example — Hotel Trident:
// ┌──────────────────────────────────────────────────┐
// │  Supplier Reconciliation — Hotel Trident          │
// │  Period: April 2026                               │
// │                                                    │
// │  Our Records:          Supplier Statement:         │
// │  Opening: ₹0           Opening: ₹0                │
// │  Invoice 1: +₹18,000   Invoice 1: +₹18,000 ✅    │
// │  Invoice 2: +₹22,000   Invoice 2: +₹22,000 ✅    │
// │  Payment 1: -₹18,000   Payment 1: -₹18,000 ✅    │
// │  Credit Note: -₹3,000  Credit Note: -₹2,500 ❌   │
// │  Closing: ₹19,000      Closing: ₹19,500           │
// │                                                    │
// │  Difference: ₹500                                  │
// │  Cause: Credit note amount mismatch               │
// │  Our CN: ₹3,000 (full cancellation)                │
// │  Their CN: ₹2,500 (cancellation minus fee)        │
// │  Action: Dispute ₹500 cancellation fee             │
// └──────────────────────────────────────────────────┘

interface ReconciliationResult {
  totalItems: number;
  matched: number;
  unmatched: number;
  disputed: number;
  matchRate: number;                  // % (target: >95%)
  netDifference: Money;
}

// Matching algorithms:
// 1. Exact match: Reference number + Amount + Date (within 3 days)
// 2. Fuzzy match: Amount within ₹100 + Date within 7 days + Same supplier
// 3. Partial match: One invoice partially paid (installment)
// 4. Aggregate match: Multiple small payments = One large invoice
//
// Auto-matching priorities:
// 1. BSP statement vs. platform flight records (weekly)
// 2. Hotel statements vs. platform hotel bookings (monthly)
// 3. Tour operator statements vs. platform package bookings (monthly)
// 4. Transport statements vs. platform transport records (monthly)
```

### Dispute Resolution Workflow

```typescript
interface DisputeWorkflow {
  disputeId: string;
  supplierId: string;
  type: DisputeType;
  amount: Money;
  status: DisputeStatus;
  timeline: DisputeTimeline;
  resolution: DisputeResolution;
}

type DisputeType =
  | 'overcharge'                      // Supplier charged more than agreed
  | 'wrong_invoice'                   // Invoice for service not received
  | 'credit_shortage'                 // Credit note less than expected
  | 'payment_not_reflected'           // Our payment not shown in their statement
  | 'duplicate_charge'                // Same invoice charged twice
  | 'service_not_provided'            // Charged for service not delivered
  | 'rate_discrepancy'                // Rate differs from contracted rate
  | 'tax_discrepancy';                // GST calculation differs

type DisputeStatus =
  | 'raised'                          // Agency raised the dispute
  | 'evidence_gathering'             // Collecting supporting documents
  | 'submitted_to_supplier'          // Sent to supplier for response
  | 'supplier_responded'             // Supplier accepted/rejected/counter-offered
  | 'negotiation'                    // Back-and-forth negotiation
  | 'resolved'                       // Dispute resolved
  | 'escalated';                     // Escalated to management/legal

// Dispute resolution SLA:
// Low value (< ₹5,000): Resolve within 7 days
// Medium value (₹5-25,000): Resolve within 15 days
// High value (> ₹25,000): Resolve within 30 days
// BSP disputes: Resolve within BSP billing period (1 week)
//
// Dispute evidence checklist:
// [ ] Original booking confirmation / contract
// [ ] Supplier's quoted/agreed rate
// [ ] Invoice in question (both sides)
// [ ] Payment proof (bank statement / UTR number)
// [ ] Communication history (emails, WhatsApp)
// [ ] Service delivery confirmation (voucher, check-in record)
// [ ] Credit note received (if partial settlement)
//
// Resolution outcomes:
// 1. Full credit: Supplier issues credit note for disputed amount
// 2. Partial credit: Supplier issues partial credit, agency accepts remainder
// 3. Offset: Credit applied to next payment
// 4. Rejected: Agency absorbs the cost (or escalates)
// 5. Write-off: Amount too small to dispute (< ₹500)
```

### Aging & Outstanding Reports

```typescript
interface SupplierAging {
  supplierId: string;
  totalOutstanding: Money;
  aging: AgingBucket[];
  overdue: OverdueItem[];
  creditBalance: Money;               // If supplier owes agency
}

interface AgingBucket {
  range: string;                      // "0-30 days", "31-60 days", etc.
  amount: Money;
  invoiceCount: number;
  riskLevel: 'current' | 'watch' | 'overdue' | 'critical';
}

// Supplier aging report:
// ┌──────────────────────────────────────────────────────┐
// │  Supplier Aging Report — As of April 30, 2026         │
// │                                                      │
// │  Supplier          | Total    | 0-30d  | 31-60d | 61-90d | >90d  │
// │  Hotel Trident     | ₹19,500 | ₹19,500| -      | -      | -     │
// │  IndiGo (BSP)      | ₹0      | -      | -      | -      | -     │
// │  Kerala Tours      | ₹45,000 | ₹20,000| ₹25,000| -      | -     │
// │  Raj Transports    | ₹8,500  | -      | ₹3,500 | ₹5,000 | -     │
// │  Spice Routes      | ₹12,000 | ₹12,000| -      | -      | -     │
// │                                                      │
// │  TOTAL             | ₹85,000 | ₹51,500| ₹28,500| ₹5,000 | -     │
// │                                                      │
// │  ⚠️ Raj Transports: ₹5,000 overdue by 61-90 days     │
// │  Action: Follow up on 2 pending invoices              │
// │                                                      │
// │  [View Details] [Export Report] [Send Reminders]     │
// └──────────────────────────────────────────────────────┘

// Aging escalation:
// 0-30 days: Normal — Pay per agreed terms
// 31-60 days: Watch — Follow up with supplier, confirm invoice receipt
// 61-90 days: Overdue — Urgent follow-up, consider withholding future business
// >90 days: Critical — Management escalation, consider legal notice
//
// Credit balance tracking (when supplier owes agency):
// - Unused advance payments
// - Pending credit notes
// - Overpayments
// - These reduce future payments to supplier
```

### Settlement Reporting

```typescript
interface SettlementReporting {
  dashboards: SettlementDashboard[];
  reports: SettlementReport[];
  analytics: SettlementAnalytics;
}

interface SettlementDashboard {
  period: string;
  totalPayables: Money;
  totalReceivables: Money;
  netPosition: Money;
  upcomingPayments: UpcomingPayment[];
  overdueCount: number;
  disputeCount: number;
  reconciliationScore: number;        // % of records reconciled
}

// Settlement analytics:
// - Supplier payment cycle time (invoice receipt to payment)
// - On-time payment rate (target: >95%)
// - Average days payable outstanding (target: 15-30 days)
// - Dispute rate (disputed invoices / total invoices)
// - Reconciliation score (matched items / total items)
// - Cash outflow forecast (next 30 days)
// - Top 10 suppliers by outstanding amount
// - Payment method distribution (NEFT/RTGS/IMPS/UPI)
// - Seasonal payment patterns (plan for peak season supplier advances)
//
// Year-end reconciliation:
// March 31 (Indian financial year end):
// 1. Reconcile all supplier statements for the year
// 2. Confirm balances with major suppliers
// 3. Identify unclaimed credits and pending refunds
// 4. Ensure all credit notes received and processed
// 5. Write off unrecoverable amounts (if any)
// 6. Provision for disputed amounts
// 7. Generate year-end supplier balance confirmation letters
// 8. Support CA audit with supplier reconciliation documents
//
// Audit support:
// - Supplier-wise payment summary for the year
// - GST reconciliation (our ITC claims vs. supplier GSTR-1 filing)
// - Advance payment confirmation (supplier confirms advances received)
// - Year-end balance confirmation from top 20 suppliers
// - TDS certificate reconciliation (TDS deducted vs. certificates received)
```

---

## Open Problems

1. **Supplier portal fragmentation** — Every supplier has a different portal for viewing invoices and statements. No unified access. Agents waste time logging into multiple portals.

2. **Statement timing mismatch** — Supplier sends statement on the 25th, but our records include bookings until month-end. Reconciliation periods don't align.

3. **Foreign supplier reconciliation** — International suppliers issue statements in USD/EUR with different period conventions. Multi-currency reconciliation adds complexity.

4. **Unapplied credits** — Credits from cancelled bookings may not be applied to future payments, resulting in overpayment. Need systematic credit tracking.

5. **Year-end pressure** — March brings a flood of invoices, credit notes, and reconciliation requests as suppliers close their books. Need early-start reconciliation.

---

## Next Steps

- [ ] Build supplier statement reconciliation engine with auto-matching
- [ ] Create dispute resolution workflow with evidence tracking
- [ ] Design aging and outstanding reports with escalation rules
- [ ] Build year-end reconciliation toolkit for audit support
- [ ] Study reconciliation platforms (BlackLine, Trintech, HighRadius)
