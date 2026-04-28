# Travel Finance & Accounting — Treasury & Cash Flow

> Research document for cash flow management, bank reconciliation, payment scheduling, and working capital optimization.

---

## Key Questions

1. **How do we manage cash flow across advance collections and supplier payments?**
2. **What's the working capital model for a travel agency?**
3. **How do we handle bank reconciliation with multiple payment channels?**
4. **What's the payment scheduling strategy for suppliers?**
5. **How do we forecast cash flow for seasonal demand?**

---

## Research Areas

### Cash Flow Management

```typescript
interface CashFlowManagement {
  current: CashPosition;
  forecast: CashFlowForecast;
  obligations: PaymentObligation[];
  optimization: CashFlowOptimization;
}

interface CashPosition {
  date: Date;
  bankBalances: BankBalance[];
  receivables: Money;                  // Customer advances not yet collected
  payables: Money;                    // Supplier payments not yet made
  netWorkingCapital: Money;
  availableCash: Money;               // Free cash after obligations
}

// Cash flow lifecycle for a travel booking:
//
// Day 0: Customer inquiry
// Day 1: Customer books, pays 30% advance (₹16,500)
//   → Cash IN: +₹16,500
//   → Obligation: None yet (supplier not paid)
//
// Day 7: Agent confirms hotel, pays hotel advance (₹9,000)
//   → Cash OUT: -₹9,000
//   → Net: +₹7,500 (customer advance - hotel advance)
//
// Day 14: Flight booked via BSP (₹14,200)
//   → No immediate cash out (BSP settles weekly)
//   → Obligation: ₹14,200 due on next BSP settlement
//
// Day 30: Balance payment from customer (₹38,500)
//   → Cash IN: +₹38,500
//   → Total cash in: ₹55,000
//
// Day 35: BSP settlement debit (₹14,200)
//   → Cash OUT: -₹14,200
//
// Day 40: Trip starts, hotel balance paid (₹9,000)
//   → Cash OUT: -₹9,000
//
// Day 45: Trip ends, remaining suppliers paid (₹17,800)
//   → Cash OUT: -₹17,800
//
// Final cash position:
// IN:  ₹55,000 (customer)
// OUT: ₹50,000 (suppliers)
// Net: ₹5,000 (agency margin, before overhead)
//
// Working capital requirement:
// Between customer advance and supplier payments, agency holds cash.
// Peak exposure: When flights are booked but customer hasn't paid balance.
// Risk: If customer cancels after supplier is paid, agency bears loss.

interface CashFlowForecast {
  periods: ForecastPeriod[];
  assumptions: ForecastAssumption[];
  scenarios: CashFlowScenario[];
}

interface ForecastPeriod {
  period: string;                     // "2026-05"
  expectedInflow: Money;
  expectedOutflow: Money;
  netCashFlow: Money;
  closingBalance: Money;
  confidence: number;                 // 0-1
}

// Monthly cash flow forecast example:
// ┌──────────────────────────────────────────────┐
// │  Cash Flow Forecast — Q2 2026                │
// │                                              │
// │              Apr       May       Jun         │
// │  Opening:   ₹4.5L    ₹3.2L    ₹5.8L       │
// │  Inflow:    ₹12.0L   ₹15.0L   ₹18.0L      │
// │  Outflow:   ₹13.3L   ₹12.4L   ₹16.5L      │
// │  Net:       -₹1.3L   +₹2.6L   +₹1.5L      │
// │  Closing:   ₹3.2L    ₹5.8L    ₹7.3L       │
// │                                              │
// │  Key obligations:                             │
// │  Apr 15: GST payment ₹1.8L                  │
// │  Apr 20: BSP settlement ₹3.2L               │
// │  May 7: TCS deposit ₹45K                    │
// │  May 30: IATA bank guarantee renewal ₹2L    │
// │                                              │
// │  ⚠️ April is tight — plan supplier payments  │
// │  carefully. Consider staggered payments.     │
// └──────────────────────────────────────────────┘
```

### Working Capital Model

```typescript
interface WorkingCapitalModel {
  cashConversionCycle: CashConversionCycle;
  float: CashFloat;
  creditTerms: CreditTerms;
  optimization: WorkingCapitalOptimization;
}

interface CashConversionCycle {
  daysReceivableOutstanding: number;  // Days to collect from customer
  daysPayableOutstanding: number;     // Days to pay suppliers
  cashConversionDays: number;         // DRO - DPO (negative = good)
}

// Cash conversion cycle for travel:
//
// Customer payment timing:
//   Advance: At booking (Day 0)
//   Balance: 15-30 days before departure (Day -30)
//   DRO: ~15 days (average, from booking to full collection)
//
// Supplier payment timing:
//   Hotels: 7-15 days after checkout (Day +7 to +15)
//   Airlines (BSP): Weekly settlement (Day +3 to +10)
//   Tour operators: 15-30 days after service (Day +15 to +30)
//   DPO: ~12 days (average, from service to payment)
//
// Cash conversion cycle: 15 - 12 = +3 days
// This means the agency needs 3 days of working capital on average.
//
// GOOD: Negative cash conversion (collect before paying)
// BAD: Positive cash conversion (pay before collecting)
//
// Optimization strategies:
// 1. Collect more upfront: 50% advance instead of 30%
// 2. Negotiate longer supplier terms: 30-day payment instead of 15
// 3. Stagger payments: Don't pay all suppliers on same day
// 4. Use credit lines: Bank overdraft for seasonal peaks
//
// Seasonal working capital:
// Peak season (Oct-Mar): High bookings → High advances → Cash positive
// Off-season (Apr-Jun): Low bookings → Fixed costs → Cash tight
// Monsoon (Jul-Sep): Moderate → Plan for lean period
//
// Working capital requirement estimate:
// Monthly fixed costs: ₹3-5 lakh (rent, salaries, technology)
// Supplier advance requirement: ₹2-5 lakh (varies by booking volume)
// Safety buffer: ₹2-3 lakh (for cancellations, emergencies)
// Total working capital needed: ₹7-13 lakh

interface CreditTerms {
  customerTerms: CustomerPaymentTerms;
  supplierTerms: SupplierPaymentTerms;
}

interface CustomerPaymentTerms {
  standardAdvance: number;            // 30% of total
  balanceDueDays: number;             // Days before departure (15-30)
  latePaymentGrace: number;           // 3 days after due date
  latePaymentFee: number;             // % per day after grace
}

// Customer payment schedule templates:
// Budget trips (< ₹25K): 100% upfront
// Standard trips (₹25-75K): 30% now + 70% at 15 days before
// Premium trips (₹75-2L): 25% now + 25% at 30 days + 50% at 15 days
// Luxury trips (> ₹2L): 20% now + 30% at 60 days + 25% at 30 days + 25% at 15 days
//
// Late payment escalation:
// -3 days: WhatsApp reminder
// Due date: Email reminder
// +1 day: WhatsApp + phone call
// +3 days: Grace period ends, late fee starts (1% per day)
// +7 days: Booking at risk, final notice
// +10 days: Booking cancelled, forfeiture per cancellation policy

interface SupplierPaymentTerms {
  hotels: SupplierTerm;
  airlines: SupplierTerm;
  tourOperators: SupplierTerm;
  transporters: SupplierTerm;
}

interface SupplierTerm {
  advanceRequired: number;            // % of total
  balancePaymentTiming: string;       // "7 days after checkout"
  creditPeriod: number;               // Days of credit
  earlyPaymentDiscount?: number;      // % discount for early payment
}

// Supplier payment optimization:
// Hotels: Negotiate 15-day credit after checkout (industry standard)
// Airlines: BSP handles this (weekly settlement)
// Tour operators: Negotiate 30-day credit (competitive market)
// Transporters: Usually on-the-spot payment (less leverage)
//
// Early payment discounts:
// Some hotels offer 3-5% discount for advance payment (30+ days before)
// Calculate: If trip is ₹50K and hotel offers 5% early payment discount
//   Savings: ₹2,500 per booking
//   Cost of capital: ₹50K × 12% annual rate × 30/365 = ₹493
//   Net savings: ₹2,500 - ₹493 = ₹2,007
//   → Always take early payment discount if available
```

### Bank Reconciliation

```typescript
interface BankReconciliation {
  bankAccounts: BankAccount[];
  transactions: BankTransaction[];
  matchingRules: ReconciliationRule[];
  exceptions: ReconciliationException[];
  autoMatchRate: number;
}

interface BankAccount {
  accountId: string;
  bank: string;                       // "ICICI", "HDFC", "SBI"
  accountNumber: string;
  type: 'operating' | 'gst' | 'salary' | 'fixed_deposit';
  balance: Money;
  lastReconciled: Date;
}

// Multi-channel payment reconciliation:
//
// Payment channels to reconcile:
// 1. UPI (GPay, PhonePe, Paytm) → Settled T+1 to bank
// 2. Credit/Debit Card → Settled T+2 to bank (via Razorpay)
// 3. Net Banking → Settled T+1 to bank
// 4. Bank Transfer (NEFT/IMPS) → Settled same day or T+1
// 5. Cash → Manual deposit at bank
// 6. Cheque → Cleared in 2-3 days
//
// Reconciliation challenges:
// - Razorpay settlement lumps multiple payments into one bank deposit
// - GST on payments creates amount mismatch (booking ₹55K, received ₹55K,
//   but ₹2,619 is GST payable, only ₹52,381 is revenue)
// - TCS collection appears as separate line item
// - Refunds create negative entries
// - Payment gateway fees deducted from settlement
//
// Auto-matching rules:
// 1. Exact match: Booking amount = Bank credit amount + GST
// 2. Batch match: Razorpay settlement = Sum of individual payments - Fees
// 3. Date tolerance: Match within ±3 days of expected date
// 4. Partial match: Booking amount differs by <₹100 (rounding)
// 5. Reference match: Payment reference contains booking ID

// Reconciliation dashboard:
// ┌──────────────────────────────────────────┐
// │  Bank Reconciliation — April 2026        │
// │                                          │
// │  ICICI Operating Account                 │
// │  Bank Balance: ₹12,45,000               │
// │  Platform Balance: ₹12,38,500           │
// │  Difference: ₹6,500                      │
// │                                          │
// │  Matched: 186 transactions (94%)         │
// │  Unmatched: 12 transactions              │
// │                                          │
// │  Unmatched Items:                         │
// │  1. Bank credit ₹3,500 (Apr 15)          │
// │     → No matching booking. Bank interest?│
// │  2. Bank debit ₹890 (Apr 18)             │
// │     → Bank charges. Auto-create entry?   │
// │  3. Platform booking ₹55K (Apr 20)       │
// │     → Payment not yet received. Follow up│
// │                                          │
// │  [Auto-Match] [Create Entry] [Follow Up] │
// └──────────────────────────────────────────┘
```

### Payment Scheduling

```typescript
interface PaymentScheduler {
  upcoming: ScheduledPayment[];
  autoPay: AutoPayConfig;
  approvalWorkflow: PaymentApproval;
  batchProcessing: BatchPaymentConfig;
}

interface ScheduledPayment {
  paymentId: string;
  bookingId: string;
  supplier: string;
  amount: Money;
  dueDate: Date;
  status: 'scheduled' | 'pending_approval' | 'approved' | 'paid' | 'overdue';
  priority: 'high' | 'medium' | 'low';
}

// Payment scheduling strategy:
//
// Priority-based payment queue:
// P0 (Immediate): Emergency payments, IATA/BSP settlement
// P1 (This week): Hotel deposits for upcoming trips (within 7 days)
// P2 (This month): Balance payments to suppliers (within 30 days)
// P3 (Future): Advance payments with early-bird discounts
//
// Cash-aware scheduling:
// Don't schedule more payments than available cash allows.
// If ₹10L available and ₹15L in payables:
//   → Pay P0 and P1 first (₹6L)
//   → Hold P2 payments until next cash inflow
//   → Defer P3 payments where possible
//
// Batch payment processing:
// Weekly batch: Aggregate payments to same supplier
//   → Reduces transaction count (lower bank charges)
//   → Easier reconciliation (one payment reference)
//   → Negotiate volume discount with frequent-pay suppliers
//
// Payment approval workflow:
// < ₹5,000: Agent can approve (auto-pay)
// ₹5,000-25,000: Agency admin approval required
// ₹25,000-1,00,000: Agency owner approval required
// > ₹1,00,000: Dual approval (owner + accountant)
// International payments: Always require owner approval
```

---

## Open Problems

1. **Float management** — Agency holds customer money between collection and supplier payment. This float creates opportunity (interest) and risk (if agency uses float for operations and customer cancels).

2. **Seasonal cash crunch** — April-June (off-season) has low bookings but fixed costs continue. Agencies without cash reserves face liquidity crises.

3. **Multi-bank complexity** — Agencies often have 3-4 bank accounts (operating, GST, salary, fixed deposit). Reconciliation across accounts is tedious.

4. **Supplier advance risk** — Paying suppliers before customer has fully paid creates credit risk. If customer cancels, recovering supplier advance is difficult.

5. **Payment gateway settlement timing** — Razorpay settles T+1 or T+2, but customer sees "paid" immediately. Book shows higher balance than actual bank balance during settlement period.

---

## Next Steps

- [ ] Build cash flow management dashboard with forecasting
- [ ] Create working capital model with seasonal planning
- [ ] Design auto-reconciliation engine with multi-channel matching
- [ ] Build payment scheduler with priority-based queue and approval workflow
- [ ] Study treasury management systems (Razorpay Route, Cashfree, Zoho Finance)
