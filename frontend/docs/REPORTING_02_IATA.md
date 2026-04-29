# Travel Industry Reporting & Filing — IATA & BSP Reporting

> Research document for IATA accreditation compliance, BSP settlement, ADM/ACM management, and airline billing reconciliation.

---

## Key Questions

1. **What reporting obligations come with IATA accreditation?**
2. **How does BSP settlement work for Indian travel agencies?**
3. **What are ADMs and ACMs and how are they managed?**
4. **How do agency debit memos get tracked and disputed?**
5. **What airline compliance reporting is required?**

---

## Research Areas

### IATA Accreditation Compliance

```typescript
interface IATACompliance {
  accreditation: IATAAccreditation;
  standards: IATAStandards;
  audits: IATAAudit;
  reporting: IATAReporting;
}

// IATA accreditation levels in India:
// ─────────────────────────────────────────
// Level          | Requirements           | Privileges
// ──────────────────────────────────────────────────────────
// Accredited     | Financial guarantee,   | Full BSP access,
// Agent          | staff qualification,   | direct ticketing,
//                | office standards,      | all airlines
//                | security deposit       |
// ──────────────────────────────────────────────────────────
// General        | Lower financial        | Limited BSP,
// Sales Agent    | requirements           | domestic only
// ──────────────────────────────────────────────────────────
// Cargo Agent    | Separate accreditation | Air cargo only
// ──────────────────────────────────────────────────────────
//
// Accreditation requirements:
// - Minimum 2 qualified staff (IATA/UFTAA certified)
// - Minimum 3 years in travel business
// - Financial security: Bank guarantee (₹15L-50L)
// - Separate business premises
// - Compliance with IATA Resolution 818g (India)
// - Agency is in a fit financial condition
// - Two trade references

// IATA reporting obligations:
// ─────────────────────────────────────────
// 1. FINANCIAL:
//    - Monthly financial statements
//    - Quarterly financial review (if required)
//    - Bank guarantee maintenance
//    - BSP remittance on time (critical)
//
// 2. OPERATIONAL:
//    - Staff qualification maintenance
//    - Training record updates
//    - Security compliance (ticket stock)
//
// 3. SALES:
//    - Ticket sales reporting via BSP
//    - Refund processing within timelines
//    - Void ticket management
//    - ADM acceptance/rejection within 30 days

// IATA compliance dashboard:
// ┌─────────────────────────────────────────┐
// │  IATA Compliance Status                  │
// │                                            │
// │  Accreditation: ✅ Active (renewal: Mar 2027)│
// │  IATA Number:  23-3 4567 8               │
// │  Location:     Mumbai, India              │
// │                                            │
// │  Financial:                                │
// │  Bank guarantee: ₹25,00,000 (expires Dec) │
// │  BSP account: ✅ Current                  │
// │  Pending ADMs: 2 (₹12,500)              │
// │                                            │
// │  Staff:                                    │
// │  Qualified staff: 5 (min required: 2) ✅  │
// │  Certifications expiring: 1 (June 2026)  │
// │                                            │
// │  ⚠️ Action Items:                         │
// │  • BSP remittance due: May 5 (₹3.2L)    │
// │  • Bank guarantee renewal: Dec 31        │
// │  • Staff cert renewal: Priya (June 15)   │
// │                                            │
// │  [View BSP Report] [Upload Documents]    │
// └─────────────────────────────────────────────┘
```

### BSP Settlement System

```typescript
interface BSPSettlement {
  cycle: BSPCycle;
  transactions: BSPTransaction[];
  settlement: BSPSettlementProcess;
  reconciliation: BSPReconciliation;
}

// BSP (Billing and Settlement Plan) India:
// ─────────────────────────────────────────
// BSP is the system through which IATA-accredited agents
// report and settle airline ticket sales.
//
// Settlement cycle (typically twice monthly in India):
// Period 1: 1st-15th → Settlement on 25th
// Period 2: 16th-30th/31st → Settlement on 10th of next month
//
// BSP process flow:
// ┌──────────┐    ┌──────────┐    ┌──────────┐
// │ Agent    │    │ BSP      │    │ Airlines │
// │ sells    │───→│ collects │───→│ receive  │
// │ tickets  │    │ data     │    │ payment  │
// │ via GDS  │    │          │    │          │
// └──────────┘    └──────────┘    └──────────┘
//       │                               │
//       │    ┌──────────┐               │
//       └───→│ Agent    │←──────────────┘
//            │ remits   │  BSP bill
//            │ to BSP   │
//            └──────────┘
//
// BSP transaction types:
// 1. Standard Ticket Sale — Agent sells, customer pays agent, agent pays BSP
// 2. Refund — Customer cancels, agent processes refund, BSP credits agent
// 3. Void — Ticket voided same day (before BSP cutoff), no settlement
// 4. Exchange — Ticket reissued, difference settled through BSP
// 5. ADM — Airline debits agent for undercollection or penalty
// 6. ACM — Airline credits agent for overcollection or incentive

interface BSPTransaction {
  id: string;
  type: BSPTransactionType;
  airlineCode: string;                 // "6E" (IndiGo), "AI" (Air India)
  ticketNumber: string;                // "123-4567890123"
  gdsPnr: string;
  passengerName: string;
  fare: number;
  tax: number;
  commission: number;
  netAmount: number;                   // Amount to be settled
  transactionDate: Date;
  bspPeriod: string;                   // "2026-04-P1" (April, Period 1)
  status: BSPStatus;
}

type BSPTransactionType =
  | 'sale'
  | 'refund'
  | 'void'
  | 'exchange'
  | 'adm'                              // Agency Debit Memo
  | 'acm';                             // Agency Credit Memo

type BSPStatus =
  | 'pending'                          // Awaiting BSP processing
  | 'processed'                        // Included in BSP bill
  | 'settled'                          // Payment completed
  | 'disputed'                         // Agent disputes the charge
  | 'rejected';                        // BSP rejected the transaction

// BSP settlement report:
// ┌─────────────────────────────────────────┐
// │  BSP Settlement — April 2026, Period 1   │
// │  Period: Apr 1-15, 2026                  │
// │  Settlement due: Apr 25, 2026            │
// │                                            │
// │  Sales Summary:                            │
// │  ─────────────────────────────────────── │
// │  Total ticket sales:  87 tickets          │
// │  Gross fare:          ₹18,45,000         │
// │  Taxes:               ₹3,22,000          │
// │  Less refunds:        (₹2,15,000)        │
// │  Less voids:          (₹45,000)          │
// │  ─────────────────────────────────────── │
// │  Net billable:        ₹19,07,000         │
// │                                            │
// │  By Airline:                               │
// │  IndiGo (6E)   — 32 tickets — ₹7,80,000  │
// │  Air India (AI) — 28 tickets — ₹5,20,000 │
// │  Vistara (UK)   — 15 tickets — ₹3,40,000 │
// │  SpiceJet (SG)  — 12 tickets — ₹2,67,000 │
// │                                            │
// │  Commission Earned:                        │
// │  IndiGo: 5% = ₹39,000                    │
// │  Air India: 3% = ₹15,600                  │
// │  Vistara: 5% = ₹17,000                   │
// │  Total commission: ₹71,600                │
// │                                            │
// │  Amount payable to BSP: ₹18,35,400        │
// │  (Net billable minus commission)           │
// │                                            │
// │  [Approve & Pay] [Download BSP File]      │
// │  [Reconcile] [Dispute Items]              │
// └─────────────────────────────────────────────┘

// BSP remittance methods:
// 1. Direct debit (agent authorizes BSP to debit bank account)
// 2. Bank transfer (agent transfers to BSP bank account)
// 3. Letter of credit (for large agencies)
//
// Default: Direct debit (most common in India)
// Failure to remit on time → Risk of accreditation suspension
```

### ADM/ACM Management

```typescript
interface ADMACMSystem {
  adm: ADMManagement;
  acm: ACMManagement;
  dispute: DisputeWorkflow;
  analytics: ADMAnalytics;
}

// ADM (Agency Debit Memo) — Airline charges agent:
// Reasons for ADM:
// - Fare undercollection (agent sold at wrong fare)
// - Tax discrepancy (wrong tax calculated)
// - Commission overpayment (airline paid too much commission)
// - Refund penalty (refund processed after deadline)
// - Ticketing violation (booking class not permitted)
// - No-show penalty (customer didn't show, agent didn't cancel)
// - Credit card chargeback
//
// ACM (Agency Credit Memo) — Airline credits agent:
// Reasons for ACM:
// - Fare overcollection (agent charged too much)
// - Commission incentive (performance bonus)
// - Refund credit (refund processed for valid cancellation)
// - Tax correction (tax was over-calculated)
// - Volume incentive (quarterly/yearly bonus)

interface ADMManagement {
  // ADM processing workflow:
  // ┌─────────────────────────────────────────┐
  // │  ADM Received — 6E-2026-04-1234          │
  // │                                            │
  // │  Airline: IndiGo (6E)                     │
  // │  Amount: ₹8,500                           │
  // │  Reason: Fare undercollection             │
  // │  Ticket: 123-4567890123                   │
  // │  Passenger: Rajesh Sharma                 │
  // │  Flight: 6E-234 DEL→COK Mar 15           │
  // │                                            │
  // │  Details:                                  │
  // │  Booked fare: ₹5,200 (S class)            │
  // │  Correct fare: ₹8,900 (S class)           │
  // │  Difference: ₹3,700                       │
  // │  ADM fee: ₹500                            │
  // │  Tax adjustment: ₹4,300                   │
  // │  Total ADM: ₹8,500                        │
  // │                                            │
  // │  Due date: 30 days from receipt           │
  // │                                            │
  // │  Options:                                  │
  // │  [Accept & Pay] [Dispute ADM]             │
  // │  [View Ticket Details] [Contact Airline]  │
  // └─────────────────────────────────────────────┘
  //
  // Dispute process:
  // 1. Agent reviews ADM within 14 days
  // 2. If disputed: Submit evidence to airline via BSPlink
  // 3. Evidence: Booking confirmation, fare quote, GDS screenshot
  // 4. Airline reviews (14-30 days)
  // 5. Resolution: ADM waived, reduced, or upheld
  // 6. If upheld and agent disagrees → Escalate to IATA
  //
  // ADM analytics:
  // ┌─────────────────────────────────────────┐
  // │  ADM Analytics — 2026 YTD               │
  // │                                            │
  // │  Total ADMs: 23 (₹1,85,000)             │
  // │  Accepted: 15 (₹1,12,000)               │
  // │  Disputed: 8 (₹73,000)                  │
  // │  Won: 5 (₹48,000 recovered)             │
  // │  Lost: 3 (₹25,000 paid)                 │
  // │                                            │
  // │  Top ADM reasons:                          │
  // │  1. Fare undercollection — 10 (₹85,000)  │
  // │  2. Refund penalty — 6 (₹42,000)         │
  // │  3. Tax discrepancy — 4 (₹28,000)        │
  // │  4. Ticketing violation — 3 (₹30,000)    │
  // │                                            │
  // │  By airline:                               │
  // │  IndiGo: 8 (₹68,000)                     │
  // │  Air India: 7 (₹52,000)                   │
  // │  Vistara: 5 (₹35,000)                    │
  // │  SpiceJet: 3 (₹30,000)                   │
  // │                                            │
  // │  ⚠️ ADM rate increasing — investigate    │
  // │  fare quoting process for IndiGo          │
  // └─────────────────────────────────────────────┘
}
```

### Airline Commission & Incentive Tracking

```typescript
interface CommissionTracking {
  rates: CommissionRate[];
  earnings: CommissionEarning;
  incentives: IncentiveProgram;
  reconciliation: CommissionReconciliation;
}

// Commission structure:
// ─────────────────────────────────────────
// Airline      | Domestic | International | Incentive
// ──────────────────────────────────────────────────────────
// IndiGo       | 5%       | 3%           | Quarterly volume
// Air India    | 3%       | 5%           | Annual target
// Vistara      | 5%       | 5%           | Monthly volume
// SpiceJet     | 3%       | N/A          | Seasonal promo
// Go First     | 5%       | N/A          | Quarterly
// Akasa Air    | 5%       | N/A          | Introductory
// International | 0-5%   | Varies       | Carrier-specific
// ─────────────────────────────────────────
//
// Commission types:
// 1. Standard commission — % of base fare
// 2. Override commission — Additional % for volume targets
// 3. Incentive commission — Fixed amount per sector above target
// 4. Marketing fund — Cooperative marketing support
// 5. Net fare commission — Markup on net fares

// Commission earnings tracker:
// ┌─────────────────────────────────────────┐
// │  Airline Commission — April 2026         │
// │                                            │
// │  This Month:                               │
// │  Standard commission: ₹1,85,000          │
// │  Override commission: ₹42,000            │
// │  Incentive: ₹15,000                      │
// │  Total: ₹2,42,000                        │
// │                                            │
// │  By Airline:                               │
// │  IndiGo:  ₹85,000 (5% on ₹17L)          │
// │  Air India: ₹52,000 (3% on ₹17.3L)       │
// │  Vistara: ₹65,000 (5% on ₹13L)          │
// │  SpiceJet: ₹28,000 (3% on ₹9.3L)        │
// │  Others: ₹12,000                          │
// │                                            │
// │  Quarterly Target Progress:                │
// │  IndiGo: ████████░░ 78% (₹2.1L of ₹2.7L)│
// │  Air India: ██████░░░░ 62% (₹1.4L of ₹2.2L)│
// │  Vistara: █████████░ 89% (₹1.8L of ₹2.0L)│
// │                                            │
// │  [View Details] [Export Report]            │
// └─────────────────────────────────────────────┘

// Commission reconciliation:
// Commission reported by agent vs. commission paid by airline:
// 1. Agent records expected commission on each ticket sale
// 2. BSP settlement includes commission deduction
// 3. Monthly reconciliation: Expected vs received
// 4. Discrepancies → Follow up with airline
//
// Common discrepancies:
// - Commission rate changed (airline updated rates)
// - Fare basis different from expected (fare class upgrade/downgrade)
// - Incentive tier not applied (volume threshold not met)
// - Refund commission reversal (commission reversed on refund)
```

---

## Open Problems

1. **BSP settlement timing** — The twice-monthly settlement cycle creates cash flow pressure. Large agencies with ₹50L+ in ticket sales must remit significant amounts within days. Cash flow forecasting around BSP dates is critical.

2. **ADM resolution timelines** — Airlines have 9 months to issue an ADM from the date of travel. Agents must maintain booking evidence (fare quotes, GDS screenshots) for extended periods. Storage and retrieval of this evidence is challenging.

3. **Commission rate volatility** — Airlines frequently change commission rates, especially during competitive periods. Keeping the system's commission tables current requires monitoring airline circulars and BSPlink notifications.

4. **Multi-GDS complexity** — Agencies using multiple GDS (Amadeus + Galileo + Sabre) must reconcile BSP data across all systems. Each GDS has different reporting formats and timelines.

5. **Digital ticketing transition** — As airlines move to NDC (New Distribution Capability) and away from traditional GDS, BSP settlement will evolve. NDC orders don't go through BSP, requiring new reconciliation processes.

---

## Next Steps

- [ ] Build BSP settlement tracking with period-based reconciliation
- [ ] Create ADM/ACM management workflow with dispute tracking
- [ ] Implement airline commission tracking with incentive tier monitoring
- [ ] Design IATA compliance dashboard with accreditation status tracking
- [ ] Study BSP systems (BSPlink, IATA Clearing House, airline revenue accounting)
