# Supplier Invoice & Settlement — Payment Processing

> Research document for supplier payment scheduling, batch processing, payment methods, and settlement workflows.

---

## Key Questions

1. **How do we schedule and execute supplier payments?**
2. **What payment methods are used for different supplier types?**
3. **How do we handle batch payments and payment runs?**
4. **What's the BSP airline settlement process?**
5. **How do we manage advance payments vs. post-service payments?**

---

## Research Areas

### Payment Scheduling & Execution

```typescript
interface SupplierPaymentSystem {
  scheduler: PaymentScheduler;
  execution: PaymentExecution;
  methods: PaymentMethodConfig[];
  reconciliation: PaymentReconciliation;
}

interface PaymentScheduler {
  upcoming: ScheduledPayment[];
  cashAware: CashAwareScheduling;
  priority: PaymentPriority;
  batching: BatchingConfig;
}

interface ScheduledPayment {
  paymentId: string;
  bookingId: string;
  supplierId: string;
  supplierName: string;
  amount: Money;
  dueDate: Date;
  paymentType: PaymentType;
  priority: Priority;
  status: PaymentStatus;
  approvalStatus: ApprovalStatus;
}

type PaymentType =
  | 'advance'                         // Advance payment before service
  | 'balance'                         // Balance after service delivery
  | 'full'                            // Full payment upfront
  | 'reimbursement'                   // Refund/reimbursement to supplier
  | 'bsp_settlement'                  // Airline BSP settlement
  | 'credit_note';                    // Payment against credit note

// Payment scheduling by supplier type:
//
// HOTELS:
// - Advance: 10-30% at booking confirmation
// - Balance: 7-15 days after checkout
// - Seasonal: Some require full prepayment during peak season
// - Method: Bank transfer (NEFT/IMPS) or hotel portal
//
// AIRLINES (BSP):
// - BSP settlement: Weekly (every Thursday)
// - Method: Auto-debit from designated bank account
// - Special: Ad-hoc debit memos (ADM) as they arise
//
// TOUR OPERATORS:
// - Advance: 20-50% at booking confirmation
// - Balance: 15-30 days after trip completion
// - Method: Bank transfer, some accept UPI
//
// TRANSPORT (Cabs/Coaches):
// - Payment: On-the-spot or within 3 days of service
// - Method: UPI (instant), bank transfer (NEFT)
// - Challenge: Many individual drivers, small amounts
//
// ACTIVITY PROVIDERS:
// - Payment: Voucher-based (pay when voucher redeemed) or prepay
// - Method: Bank transfer or platform settlement
// - Timing: Some pay after customer completes activity
//
// INSURANCE:
// - Payment: Monthly or quarterly aggregation
// - Method: Bank transfer
// - Commission: Deducted from premium (agency keeps commission)
//
// FOREX:
// - Payment: Per transaction or weekly aggregation
// - Method: Bank transfer
// - Commission: Built into exchange rate margin

interface PaymentExecution {
  executePayment(payment: ScheduledPayment): PaymentResult;
  batchPayment(payments: ScheduledPayment[]): BatchResult;
  cancelPayment(paymentId: string): CancelResult;
}

// Payment execution flow:
// 1. Payment scheduled and approved
// 2. System checks bank balance (API call to bank)
// 3. If sufficient balance: Execute payment
// 4. If insufficient: Hold, alert agency admin
// 5. Payment initiated via chosen method:
//    - NEFT: ₹0-5L, settles in 30 min (with IFSC)
//    - RTGS: >₹2L, settles in 30 min (real-time)
//    - IMPS: Up to ₹5L, instant 24/7
//    - UPI: Up to ₹1L, instant 24/7 (some banks ₹5L)
//    - SWIFT: International, 1-3 days
// 6. Payment confirmation received
// 7. Reconciliation with booking and invoice
// 8. Journal entry created (debit: supplier payable, credit: bank)
//
// Batch payment processing:
// Weekly payment run: Every Monday
// 1. Collect all approved payments due this week
// 2. Group by supplier (aggregate multiple bookings to same supplier)
// 3. Check total cash requirement vs. available balance
// 4. If cash shortfall: Prioritize P0 and P1 payments
// 5. Execute batch: Generate payment file (NEFT/RTGS format)
// 6. Upload to bank portal (or auto-execute via API)
// 7. Confirmations received within 24 hours
// 8. Reconcile batch vs. individual payments
```

### BSP Airline Settlement

```typescript
interface BSPSettlement {
  period: string;                     // "BSP-IN-2026-W17" (Week 17)
  agentCode: string;                  // IATA numeric code
  transactions: BSPTransaction[];
  settlement: BSPSettlementDetail;
  bankDebit: BSPBankDebit;
}

interface BSPSettlementDetail {
  totalSales: Money;
  totalRefunds: Money;
  totalADMs: Money;                   // Airline Debit Memos
  totalACMs: Money;                   // Airline Credit Memos
  netAmount: Money;
  settlementDate: Date;
}

// BSP settlement process (India):
//
// Weekly cycle (Monday to Sunday):
// Mon: Billing period starts
//   - All tickets issued Mon-Sun are included
//
// Tue: BSP processes transactions
//   - Aggregates sales, refunds, ADMs, ACMs per airline
//   - Calculates net settlement amount
//
// Wed: Statement available
//   - Agent can review and dispute transactions
//   - Dispute window: Until Wednesday midnight
//
// Thu: Settlement
//   - BSP debits agent's bank account (auto-debit mandate)
//   - BSP remits to airlines
//   - Agent must have sufficient balance
//
// Settlement example:
// Week 17 (Apr 21-27, 2026):
//
// Sales:
//   IndiGo 6E-456 (Del-Mum): ₹5,500
//   Air India AI-101 (Del-Cochin): ₹8,200
//   Vistara UK-901 (Cochin-Del): ₹7,800
//   Total Sales: ₹21,500
//
// Refunds:
//   IndiGo 6E-123 (cancelled): -₹4,200
//   Total Refunds: -₹4,200
//
// ADMs:
//   IndiGo: ₹500 (fare difference adjustment)
//   Total ADMs: ₹500
//
// Net Settlement: ₹21,500 - ₹4,200 + ₹500 = ₹17,800
// Settlement date: Thursday, May 1
// Bank debited: ₹17,800
//
// BSP risk management:
// - Bank guarantee covers default risk
// - If agent's bank account has insufficient funds: BSP default
// - Default consequences: IATA accreditation at risk
// - Platform alert: 48 hours before settlement, show expected debit
// - Safety net: Auto-sweep from linked accounts or overdraft facility
```

### Multi-Method Payment Processing

```typescript
interface PaymentMethodConfig {
  method: SupplierPaymentMethod;
  limits: PaymentLimits;
  approval: PaymentApproval;
  preferred: boolean;
}

type SupplierPaymentMethod =
  | 'neft'                            // National Electronic Funds Transfer
  | 'rtgs'                            // Real Time Gross Settlement
  | 'imps'                            // Immediate Payment Service
  | 'upi'                             // Unified Payments Interface
  | 'swift'                           // International wire transfer
  | 'bank_transfer_portal'            // Via supplier's payment portal
  | 'cheque'                          // Physical cheque (rare, legacy)
  | 'cash';                           // Cash payment (avoid, no audit trail)

// Payment method selection:
//
// Domestic payments:
// < ₹1 Lakh: IMPS (instant, 24/7) or UPI
// ₹1-2 Lakh: IMPS or NEFT
// > ₹2 Lakh: RTGS (mandatory for > ₹2L by some banks)
//
// International payments:
// SWIFT wire transfer (1-3 business days)
// Requirements: Supplier bank details (SWIFT code, IBAN/account number)
// RBI compliance: Purpose code (S0302 - Travel agent services)
// FEMA declaration required for foreign exchange outward remittance
// Liberalised Remittance Scheme (LRS): Up to $250,000/year per individual
// For business: No LRS limit, but purpose code and documentation required
//
// Payment method comparison:
// NEFT: Free (most banks), 30 min settlement, banking hours
// RTGS: ₹25-50 fee, 30 min, >₹2L, banking hours
// IMPS: ₹5-15 fee, instant, 24/7, <₹5L
// UPI: Free, instant, 24/7, <₹1L (some ₹5L)
// SWIFT: ₹500-2000 fee, 1-3 days, purpose code needed

interface PaymentReconciliation {
  bankStatement: BankEntry[];
  paymentRecords: PaymentRecord[];
  matched: MatchedPayment[];
  unmatched: UnmatchedPayment[];
}

// Payment reconciliation:
// Match bank statement debits to payment records:
// - NEFT reference number matching
// - Amount matching (exact + tolerance for bank charges)
// - Date matching (within 3 days of execution)
// - Supplier name matching (bank statement payee name vs. supplier name)
//
// Common reconciliation issues:
// - Bank charges (₹5-50) not in payment record
// - GST on bank charges (separate debit)
// - Supplier bank account changed (old account returned, new payment needed)
// - Payment returned (wrong IFSC, account closed)
// - Duplicate payment (two NEFT for same invoice)
```

---

## Open Problems

1. **International payment complexity** — SWIFT transfers require purpose codes, FEMA compliance, and bank-level documentation. Each bank has different requirements.

2. **Cash flow timing** — Multiple large payments due on same day (BSP + hotel advances + salaries) can overwhelm cash position. Need payment staggering.

3. **Supplier bank detail changes** — Suppliers change bank accounts frequently. Wrong account details cause returned payments, delays, and reconciliation issues.

4. **Small supplier payments** — Individual cab drivers, local guides, and small activity providers often want UPI/cash payment immediately. Corporate payment processes don't fit.

5. **Payment proof collection** — Suppliers demand payment proof (UTR number) before confirming bookings. Need instant proof sharing via WhatsApp.

---

## Next Steps

- [ ] Build supplier payment scheduler with priority-based queuing
- [ ] Create BSP settlement monitoring with auto-debit alerts
- [ ] Design multi-method payment execution with bank API integration
- [ ] Build payment reconciliation engine with auto-matching
- [ ] Study payment platforms (Razorpay Route, Cashfree, PayU for Business)
