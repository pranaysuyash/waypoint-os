# Travel Finance & Accounting — Core Accounting

> Research document for agency accounting, chart of accounts, journal entries, and double-entry bookkeeping.

---

## Key Questions

1. **How do we handle double-entry bookkeeping for travel transactions?**
2. **What chart of accounts structure suits a travel agency?**
3. **How do we handle multi-currency transactions?**
4. **What's the accounting treatment for advances and deposits?**
5. **How do we integrate with existing accounting software?**

---

## Research Areas

### Chart of Accounts for Travel Agencies

```typescript
interface ChartOfAccounts {
  agencyId: string;
  accounts: Account[];
  costCenters: CostCenter[];
  profitCenters: ProfitCenter[];
}

interface Account {
  code: string;                       // "1000" — Assets
  name: string;                       // "Cash - Operating Account"
  type: AccountType;
  subType: string;
  normalBalance: 'debit' | 'credit';
  isActive: boolean;
  costCenterRequired: boolean;
}

type AccountType = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';

// Chart of accounts — Travel agency specific:
//
// ASSETS (1000-1999)
// 1100 — Current Assets
//   1110 — Cash
//     1111 — Operating Bank Account (ICICI)
//     1112 — GST Bank Account
//     1113 — Petty Cash
//   1120 — Accounts Receivable
//     1121 — Customer Receivables
//     1122 — Supplier Refunds Receivable
//     1123 — Commission Receivable
//   1130 — Advances
//     1131 — Advance to Suppliers (Hotels)
//     1132 — Advance to Suppliers (Airlines)
//     1133 — Advance to Suppliers (Others)
//   1140 — Other Current Assets
//     1141 — TDS Receivable
//     1142 — GST Input Credit (ITC)
//     1143 — Prepaid Expenses
//
// LIABILITIES (2000-2999)
// 2100 — Current Liabilities
//   2110 — Accounts Payable
//     2111 — Supplier Payables (Hotels)
//     2112 — Supplier Payables (Airlines)
//     2113 — Supplier Payables (Others)
//   2120 — Customer Advances
//     2121 — Advance from Customers
//     2122 — TCS Collected (Payable to Govt)
//   2130 — GST Payable
//     2131 — CGST Payable
//     2132 — SGST Payable
//     2133 — IGST Payable
//   2140 — Statutory Dues
//     2141 — TDS Payable
//     2142 — EPF Payable
//     2143 — Professional Tax Payable
//
// REVENUE (4000-4999)
// 4100 — Operating Revenue
//   4110 — Tour Package Revenue
//     4111 — Domestic Tour Revenue
//     4112 — International Tour Revenue
//   4120 — Air Ticket Revenue
//     4121 — Commission Income (Flights)
//     4122 — Markup Income (Flights)
//   4130 — Service Revenue
//     4131 — Visa Processing Fee
//     4132 — Insurance Commission
//     4133 — Forex Commission
//   4140 — Other Revenue
//     4141 — Cancellation Fee Income
//     4142 — Modification Fee Income
//     4143 — Interest Income
//
// EXPENSES (5000-5999)
// 5100 — Cost of Sales
//   5110 — Direct Trip Costs
//     5111 — Hotel Cost
//     5112 — Flight Cost
//     5113 — Transport Cost
//     5114 — Activity Cost
//     5115 — Insurance Cost
//   5120 — Supplier Payments
//     5121 — Tour Operator Payments
//     5122 — Airline Payments (BSP)
// 5200 — Operating Expenses
//   5210 — Staff Costs
//   5220 — Office Rent & Utilities
//   5230 — Marketing & Advertising
//   5240 — Technology & Software
//   5250 — Travel & Conveyance
//   5260 — Professional Fees (CA, Legal)
//   5270 — Communication (Phone, Internet)
//   5280 — Depreciation
```

### Double-Entry Bookkeeping for Travel

```typescript
interface JournalEntry {
  entryId: string;
  date: Date;
  description: string;
  reference: string;                  // Booking ID, invoice ID, etc.
  lines: JournalLine[];
  status: 'draft' | 'posted' | 'reversed';
  createdBy: string;
  approvedBy?: string;
}

interface JournalLine {
  accountCode: string;
  debit?: Money;
  credit?: Money;
  costCenter?: string;
  profitCenter?: string;
  narration: string;
}

// Booking lifecycle — accounting entries:
//
// 1. Customer pays advance (₹30,000 for Kerala trip)
//    Debit:  1111 — Bank Account          ₹30,000
//    Credit: 2121 — Customer Advances      ₹30,000
//    (Money received, but service not yet delivered)
//
// 2. Agent pays hotel advance (₹15,000)
//    Debit:  1131 — Advance to Suppliers   ₹15,000
//    Credit: 1111 — Bank Account           ₹15,000
//    (Money paid to hotel, but stay not yet consumed)
//
// 3. Trip completed — Revenue recognition
//    Total trip: ₹55,000, Direct costs: ₹40,000
//
//    3a. Revenue recognition:
//    Debit:  2121 — Customer Advances      ₹55,000
//    Credit: 4111 — Domestic Tour Revenue  ₹52,381
//    Credit: 2131 — CGST Payable           ₹1,310
//    Credit: 2132 — SGST Payable           ₹1,310
//    (GST @ 5% on ₹55,000 = ₹2,619, Revenue = ₹52,381)
//    Wait — GST is on the taxable value, not the total.
//    If ₹55,000 is inclusive of 5% GST:
//    Revenue = ₹55,000 / 1.05 = ₹52,381
//    GST = ₹55,000 - ₹52,381 = ₹2,619
//
//    3b. Cost of sales recognition:
//    Debit:  5111 — Hotel Cost              ₹18,000
//    Debit:  5112 — Flight Cost             ₹15,000
//    Debit:  5113 — Transport Cost           ₹5,000
//    Debit:  5114 — Activity Cost             ₹2,000
//    Credit: 1131 — Advance to Suppliers    ₹15,000
//    Credit: 2111 — Supplier Payables        ₹25,000
//    (Recognize costs, settle advances, create payables)
//
//    3c. Balance payment from customer:
//    Debit:  1111 — Bank Account           ₹25,000
//    Credit: 2121 — Customer Advances      ₹25,000
//
//    3d. Supplier payment:
//    Debit:  2111 — Supplier Payables      ₹25,000
//    Credit: 1111 — Bank Account           ₹25,000
//
// Gross margin on this trip:
// Revenue: ₹52,381
// Costs:   ₹40,000
// Margin:  ₹12,381 (23.6%)

// Cancellation accounting:
// Customer cancels 30 days before departure
// Cancellation fee: 20% (₹11,000)
//
// Debit:  2121 — Customer Advances      ₹55,000
// Credit: 1111 — Bank Account           ₹44,000  (Refund)
// Credit: 4141 — Cancellation Fee       ₹10,476  (Fee net of GST)
// Credit: 2131 — CGST Payable             ₹262
// Credit: 2132 — SGST Payable             ₹262
//
// Supplier refund (partial):
// Debit:  1111 — Bank Account           ₹30,000  (Hotel refund)
// Credit: 1131 — Advance to Suppliers   ₹15,000
// Credit: 5111 — Hotel Cost             (15,000)  (Reverse cost)
```

### Multi-Currency Accounting

```typescript
interface MultiCurrencyAccounting {
  baseCurrency: string;               // INR
  foreignCurrency: CurrencyConfig[];
  exchangeRates: ExchangeRateConfig;
  revaluation: RevaluationConfig;
}

interface CurrencyConfig {
  currency: string;                   // "USD", "EUR", "SGD", "THB"
  bankAccount?: string;               // Foreign currency bank account
  defaultRateSource: string;          // "RBI reference rate"
  revaluationFrequency: 'monthly' | 'quarterly';
}

// Multi-currency scenarios in travel:
//
// 1. Customer pays in INR, supplier charges in USD
//    Customer pays: ₹3,50,000 (for Europe tour)
//    Hotel costs: $2,000 (€1,800)
//    Flight costs: ₹1,20,000 (domestic leg in INR)
//
//    Entry (at booking, rate: $1 = ₹83):
//    Debit:  1111 — Bank Account        ₹3,50,000
//    Credit: 2121 — Customer Advances    ₹3,50,000
//
//    Entry (at payment to hotel):
//    Debit:  5111 — Hotel Cost           ₹1,66,000  ($2,000 × ₹83)
//    Credit: 1111 — Bank Account         ₹1,66,000
//
//    If rate changes to ₹84 at settlement:
//    Exchange gain/loss: ₹2,000 × (84 - 83) = ₹2,000 loss
//    Debit:  5111 — Hotel Cost             ₹2,000
//    Credit: 1111 — Bank Account           ₹2,000
//    (Additional ₹2,000 due to rate change)
//
// 2. Forex gain/loss at month-end revaluation:
//    Outstanding supplier payable: $1,000
//    Booked rate: ₹83 → Current rate: ₹84.5
//    Unrealized loss: ₹1,500
//    Debit:  5300 — Exchange Loss          ₹1,500
//    Credit: 2111 — Supplier Payables       ₹1,500
//    (Mark-to-market adjustment)
//
// Exchange rate sources:
// - RBI reference rate (published daily at 4:30 PM IST)
// - Card rate (bank's actual rate for forex transactions)
// - Use RBI rate for booking entries
// - Use card rate for actual settlement
// - Difference = Exchange gain/loss

// GST on imported services (reverse charge):
// Foreign hotel booked for customer:
// Service value: $500 × ₹83 = ₹41,500
// IGST (reverse charge): 18% = ₹7,470
//
// Debit:  5111 — Hotel Cost              ₹41,500
// Credit: 2111 — Supplier Payables        ₹41,500
//
// Debit:  1142 — GST Input Credit         ₹7,470
// Credit: 2133 — IGST Payable             ₹7,470
// (Reverse charge mechanism — agency pays IGST, claims ITC)
```

### Accounting Integration

```typescript
interface AccountingIntegration {
  erpSync: ERPSyncConfig;
  exportFormats: ExportFormat[];
  reconciliation: AutoReconciliation;
  auditTrail: AccountingAuditTrail;
}

interface ERPSyncConfig {
  erp: ERPTarget;
  syncFrequency: 'real_time' | 'daily' | 'on_demand';
  mapping: FieldMapping[];
  validation: SyncValidation;
}

type ERPTarget =
  | 'tally'                           // Most popular in India (70%+ SMEs)
  | 'zoho_books'                      // Growing, cloud-native
  | 'busy'                            // Popular with small businesses
  | 'marg'                            // Desktop-based, traditional
  | 'quickbooks_india'                // Limited India presence
  | 'custom_api';                     // Custom ERP integration

// Tally integration (most important for India):
// - TallyPrime / Tally.ERP 9
// - Import: XML voucher import (journal entries)
// - Export: Day book, trial balance, P&L, balance sheet
// - Sync: Daily batch sync of all journal entries
// - Mapping: Platform accounts → Tally ledger names
//
// Integration flow:
// 1. Platform generates journal entries for all transactions
// 2. Daily batch: Export entries as Tally XML
// 3. Import into Tally via XML import
// 4. Tally handles GST filing, statutory reports
// 5. Agency CA uses Tally for audit and tax filing
//
// Alternative: Zoho Books (for cloud-native agencies)
// - REST API integration (more modern)
// - Real-time sync possible
// - Built-in GST filing (GSTR-1, GSTR-3B auto-file)
// - Auto bank reconciliation
// - Better for agencies that want all-in-one cloud solution

// Auto-reconciliation:
// Bank statement ↔ Platform entries
// - Match: Amount + Date + Reference number
// - Unmatched bank: Bank charges, interest (auto-create entry)
// - Unmatched platform: Pending deposits, uncleared cheques
// - Reconciliation dashboard showing matched/unmatched
```

---

## Open Problems

1. **Revenue recognition timing** — When does a trip become revenue? At booking? At advance payment? At trip completion? Mixed approaches needed (IFRS 15 vs. Indian Accounting Standards).

2. **Supplier invoice lag** — Hotels and airlines often send invoices weeks after service delivery. Can't wait for invoices to recognize costs. Need accrual entries.

3. **Commission accounting** — Agent commissions are expenses, but supplier commissions are revenue. Different agencies handle commission differently (gross vs. net).

4. **Group trip accounting** — 20 people on one trip, some cancel, some modify. Tracking revenue and cost per person within a group booking is complex.

5. **Tax period mismatch** — GST collected in March, supplier invoice received in April. GST liability in March, ITC claim in April. Creates cash flow timing issues.

---

## Next Steps

- [ ] Design chart of accounts specific to travel agency operations
- [ ] Build double-entry bookkeeping engine with travel-specific journal entries
- [ ] Create multi-currency accounting with RBI rate integration
- [ ] Build Tally and Zoho Books integration with daily sync
- [ ] Study travel accounting systems (Tally for Travel, Travel ERP, TRES)
