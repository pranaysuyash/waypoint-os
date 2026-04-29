# Travel Industry Reporting & Filing — Tax & Regulatory Reporting

> Research document for GST returns, TCS filings, TDS reporting, and regulatory submissions required for Indian travel agencies.

---

## Key Questions

1. **What tax reports does an Indian travel agency need to file?**
2. **How does GST reporting work for travel services?**
3. **What TCS obligations apply to overseas travel packages?**
4. **How is TDS on agent commissions and vendor payments managed?**
5. **What automation can reduce compliance burden?**

---

## Research Areas

### GST Reporting for Travel Services

```typescript
interface GSTReportingSystem {
  returns: GSTReturn[];
  hsnSac: HSNSACMapping;
  inputTax: InputTaxCredit;
  reconciliation: GSTReconciliation;
  filing: GSTFilingWorkflow;
}

// GST structure for travel services:
// ─────────────────────────────────────────
// Service Type              | SAC Code | GST Rate | Compounding
// ──────────────────────────────────────────────────────────────
// Hotel accommodation        | 996321   | 5%       | 5% of 40% = 2%
// (room tariff < ₹1000)    |          |          |
// Hotel accommodation        | 996321   | 5%       | 5% of 40% = 2%
// (room tariff ₹1000-7500) |          |          |
// Hotel accommodation        | 996321   | 18%      | 18% of 40%
// (room tariff > ₹7500)    |          |          |
// Tour operator services     | 998513   | 5%       | 5% of 40%
// (with accommodation)     |          |          |
// Tour operator services     | 998513   | 18%      | Full 18%
// (without accommodation)  |          |          |
// Air travel agent           | 998611   | 5%       | 5% of 10% basic fare
// (as commission)          |          |          |
// Air travel agent           | 998611   | 18%      | Full 18%
// (as principal)           |          |          |
// Restaurant in hotel        | 996331   | 5%       | 5%
// (room tariff > ₹7500)    |          |          |
// Travel agent commission    | 998513   | 18%      | Full 18%
// (as service fee)         |          |          |
// Rent-a-cab                | 996602   | 5%       | 5% (with ITC)
//                          |          | 12%      | 12% (without ITC)
// ─────────────────────────────────────────

interface GSTReturn {
  type: GSTReturnType;
  frequency: 'monthly' | 'quarterly';
  dueDate: string;                     // "20th of following month"
  sections: GSTReturnSection[];
  autoPopulated: boolean;
  manualReview: string[];              // Fields requiring manual check
}

type GSTReturnType =
  | 'GSTR_1'                           // Outward supplies (sales)
  | 'GSTR_2B'                          // Inward supplies (auto-populated from suppliers)
  | 'GSTR_3B'                          // Summary return + tax payment
  | 'GSTR_4'                           // Composition scheme return
  | 'GSTR_5'                           // Non-resident taxable person
  | 'GSTR_6'                           // Input service distributor
  | 'GSTR_7'                           // TDS return
  | 'GSTR_8'                           // E-commerce operator
  | 'GSTR_9'                           // Annual return
  | 'GSTR_9B'                          // Annual return (composition)
  | 'GSTR_10'                         ; // Final return (cancellation)

// GSTR-1 (Outward Supplies) for travel agency:
// ┌─────────────────────────────────────────┐
// │  GSTR-1 — April 2026                     │
// │  Period: Apr 1-30, 2026                  │
// │  Due: May 11, 2026                       │
// │                                            │
// │  Summary:                                  │
// │  Total invoices: 245                       │
// │  Taxable value: ₹42,35,000               │
// │  CGST: ₹2,11,750                         │
// │  SGST: ₹2,11,750                         │
// │  IGST: ₹3,42,000                         │
// │  Cess: ₹0                                 │
// │                                            │
// │  Breakdown by SAC:                         │
// │  996321 (Hotel) — 89 invoices — ₹18.2L   │
// │  998513 (Tour operator) — 120 — ₹15.8L   │
// │  998611 (Air agent) — 36 — ₹8.3L         │
// │                                            │
// │  ⚠️ Issues:                               │
// │  • 3 invoices missing HSN/SAC codes       │
// │  • 5 B2B invoices have invalid GSTINs     │
// │                                            │
// │  [Review Issues] [Download JSON] [File]   │
// └─────────────────────────────────────────────┘
//
// Auto-population from trip data:
// Trip confirmed → Invoice generated → GST calculated
//   → Auto-categorize by SAC code
//   → Populate GSTR-1 line items
//   → Flag anomalies (missing GSTIN for B2B, wrong SAC)
//   → Agent reviews, corrects, approves
//   → JSON generated for GST portal upload

// GSTR-3B (Summary Return):
// ┌─────────────────────────────────────────┐
// │  GSTR-3B — April 2026                    │
// │                                            │
// │  1. Outward Supplies & Tax                 │
// │     Taxable: ₹42.35L  CGST: ₹2.12L       │
// │     SGST: ₹2.12L     IGST: ₹3.42L        │
// │                                            │
// │  2. Inward Supplies (ITC Claimed)          │
// │     From GSTR-2B: ₹38.5L matched          │
// │     ITC available: CGST: ₹1.92L           │
// │     SGST: ₹1.92L     IGST: ₹3.10L         │
// │                                            │
// │  3. Net Tax Payable                        │
// │     CGST: ₹0.20L   SGST: ₹0.20L          │
// │     IGST: ₹0.32L    Total: ₹0.72L         │
// │                                            │
// │  4. Liability from earlier returns         │
// │     Late fee pending: ₹500                │
// │                                            │
// │  Total payable: ₹7,700                    │
// │                                            │
// │  [Pay via DRC-03] [Download Challan]      │
// │  [File GSTR-3B]                           │
// └─────────────────────────────────────────────┘

interface HSNSACMapping {
  // Auto-mapping of travel services to SAC codes:
  // ┌──────────────────────┬──────────┬──────┐
  // │ Service              │ SAC Code │ Rate │
  // ├──────────────────────┼──────────┼──────┤
  // │ Hotel booking        │ 996321   │ 5%   │
  // │ Package tour (w/accom)│ 998513  │ 5%   │
  // │ Package tour (no accom)│ 998513 │ 18%  │
  // │ Flight commission    │ 998611   │ 5%   │
  // │ Flight markup        │ 998611   │ 18%  │
  // │ Visa assistance      │ 998599   │ 18%  │
  // │ Travel insurance     │ 997133   │ 18%  │
  // │ Cab rental           │ 996602   │ 5%   │
  // │ Forex service fee    │ 998591   │ 18%  │
  // │ Activity booking     │ 998551   │ 18%  │
  // │ Restaurant in hotel  │ 996331   │ 5%   │
  // └──────────────────────┴──────────┴──────┘
  //
  // Auto-mapping rules:
  // 1. Trip component type → SAC code lookup
  // 2. Price threshold → Rate tier (e.g., hotel > ₹7500 = 18%)
  // 3. Billing mode → Agent vs principal (affects rate)
  // 4. Supply type → Intra-state (CGST+SGST) vs Inter-state (IGST)
  //
  // Validation:
  // - Missing SAC code → Flag for manual assignment
  // - Ambiguous mapping → Suggest options, agent picks
  // - Invalid combination → Block invoice, require correction

  mappingRules: MappingRule[];
  validation: MappingValidation[];
}

interface InputTaxCredit {
  // ITC reconciliation:
  // 1. Supplier uploads GSTR-1 → Appears in agency's GSTR-2B
  // 2. Match supplier invoices with purchase register
  // 3. Matched → ITC can be claimed
  // 4. Unmatched → Follow up with supplier
  // 5. Partial match → Amount mismatch, investigate
  //
  // ITC dashboard:
  // ┌─────────────────────────────────────────┐
  // │  Input Tax Credit — April 2026           │
  // │                                            │
  // │  ITC Summary:                              │
  // │  Available:  ₹7.04L                       │
  // │  Matched:    ₹6.85L (97.3%)              │
  // │  Unmatched:  ₹0.12L (4 suppliers)        │
  // │  Reversed:   ₹0.07L (blocked under 17(5))│
  // │                                            │
  // │  Unmatched Suppliers:                      │
  // │  • Taj Hotels — ₹45,000 (not filed GSTR-1)│
  // │  • Indigo Airlines — ₹32,000 (GSTIN mismatch)│
  // │  • MakeMyTrip — ₹28,000 (amount mismatch)│
  // │  • SOTC — ₹15,000 (not filed GSTR-1)     │
  // │                                            │
  // │  [Send Reminders] [View Details]          │
  // └─────────────────────────────────────────────┘
  //
  // Blocked ITC (Section 17(5)):
  // Travel agencies cannot claim ITC on:
  // - Food and beverages (restaurant)
  // - Health and fitness
  // - Travel benefits to employees
  // - Insurance (unless mandated)
}
```

### TCS on Overseas Travel Packages

```typescript
interface TCSReporting {
  thresholds: TCSThreshold[];
  collection: TCSCollection;
  remittance: TCSRemittance;
  certificates: TCSCertificate;
  reporting: TCSReporting;
}

// TCS on overseas travel (Section 206C(1G)):
// ─────────────────────────────────────────
// Condition                          | TCS Rate
// ──────────────────────────────────────────────────────
// Overseas package (no PAN)          | 10% (w/o PAN: 20%)
// Overseas package (with PAN)        | 5%
// Remittance under LRS (no PAN)      | 10% (w/o PAN: 20%)
// Remittance under LRS (above ₹7L)   | 20% (education: 5%)
// Remittance under LRS (≤₹7L)       | 5% (threshold)
// ─────────────────────────────────────────
//
// Key rules:
// - TCS collected on total package price (including accommodation)
// - If customer has PAN: 5%, no PAN: 20%
// - TCS not collected if remittance is for education/medical (proof required)
// - Travel agent must deposit TCS within specified time
// - Quarterly TCS return filing (Form 27EQ)
// - Annual TCS certificate to buyer (Form 27D)

interface TCSCollection {
  // Auto-TCS calculation on trip booking:
  // ┌─────────────────────────────────────────┐
  // │  TCS Calculation — Thailand Trip         │
  // │                                            │
  // │  Trip price:           ₹78,000            │
  // │  (Domestic flights:    ₹12,000)           │
  // │  (International flight:₹22,000)           │
  // │  (Hotel 4 nights:     ₹18,000)           │
  // │  (Activities:          ₹8,000)            │
  // │  (Transfers:           ₹5,000)            │
  // │  (Markup:              ₹13,000)           │
  // │                                            │
  // │  Overseas component:   ₹66,000            │
  // │  (Excluding domestic flights)             │
  // │                                            │
  // │  Customer PAN: ✅ BQRPK1234A              │
  // │  TCS Rate: 5%                              │
  // │  TCS Amount: ₹3,300                       │
  // │                                            │
  // │  Total bill: ₹78,000 + ₹3,300 = ₹81,300  │
  // │                                            │
  // │  [Confirm TCS] [Override PAN] [Exempt]    │
  // └─────────────────────────────────────────────┘
  //
  // TCS exemption scenarios:
  // - Education abroad: Form 15CA/15CB, university admission proof
  // - Medical treatment: Doctor's letter, hospital estimate
  // - Already taxed at source: Previous remittance receipt
  // - Diplomatic passport: Exempt
  //
  // PAN verification:
  // - Auto-verify via NSDL/UTIITSL API
  // - Invalid PAN → Apply 20% rate
  // - Missing PAN → Apply 20% rate + flag
  // - PAN-Aadhaar linking check (unlinked PAN = invalid post deadline)

  tripId: string;
  customerId: string;
  panStatus: 'verified' | 'invalid' | 'missing';
  overseasComponent: number;
  domesticComponent: number;
  tcsRate: number;
  tcsAmount: number;
  exemptionClaimed: boolean;
  exemptionReason?: string;
}

interface TCSRemittance {
  // TCS deposit timeline:
  // - Collected during 1st-15th of month → Deposit by 7th of next month
  // - Collected during 16th-end of month → Deposit by 7th of next month
  // - Challan: Form 281 (single challan for all TCS)
  //
  // TCS tracking dashboard:
  // ┌─────────────────────────────────────────┐
  // │  TCS Dashboard — April 2026              │
  // │                                            │
  // │  Collected: ₹4,85,000 (127 customers)    │
  // │  Deposited: ₹4,50,000 (120 customers)    │
  // │  Pending:   ₹35,000 (7 customers)        │
  // │                                            │
  // │  Upcoming deadlines:                       │
  // │  • May 7: Deposit ₹35,000 (Apr 16-30 TCS)│
  // │  • May 15: File Apr TCS return            │
  // │  • May 31: Issue Form 27D to customers    │
  // │                                            │
  // │  ⚠️ 3 customers have invalid PAN — 20% rate│
  // │  applied. Request PAN update.             │
  // │                                            │
  // │  [Deposit TCS] [Generate Challan]         │
  // │  [File Return] [Issue Certificates]       │
  // └─────────────────────────────────────────────┘
}

interface TCSCertificate {
  // Form 27D — TCS Certificate to buyer:
  // - Quarterly generation
  // - Contains: TCS amount, PAN, transaction details
  // - Delivered via email + WhatsApp
  // - Customer can claim TCS credit in ITR
  // - Digital signature for authenticity
  //
  // Certificate includes:
  // - TAN of travel agent
  // - PAN of buyer (customer)
  // - Amount collected
  // - Section under which collected
  // - Quarter and financial year
  // - Unique certificate number
}
```

### TDS Reporting

```typescript
interface TDSReporting {
  sections: TDSSection[];
  processing: TDSProcessing;
  returns: TDSReturns;
  certificates: TDSCertificates;
}

// TDS sections relevant to travel agencies:
// ─────────────────────────────────────────
// Section   | Nature of Payment           | TDS Rate
// ──────────────────────────────────────────────────────────
// 194C      | Contractor (transport)      | 1% (ind) / 2% (other)
// 194C      | Tour operator services      | 1-2%
// 194D      | Insurance commission        | 5%
// 194H      | Commission to agents        | 5%
// 194I      | Rent (office space)         | 10%
// 194J      | Professional services       | 10%
// 194O      | E-commerce (if applicable)  | 1%
// 194Q      | Purchase of goods >₹50L     | 0.1%
// 192       | Salary (employees)          | Slab rate
// 192A      | Premature EPF withdrawal    | 10%
// 206C(1H)  | Sale of goods >₹50L         | 0.1%
// ─────────────────────────────────────────

// Key TDS scenarios for travel agencies:
//
// 1. PAYMENT TO SUB-AGENTS (Section 194H):
//    Commission paid to sub-agents → TDS @ 5%
//    Example: ₹10,000 commission → TDS ₹500 → Net ₹9,500
//
// 2. PAYMENT TO TRANSPORT OPERATORS (Section 194C):
//    Cab/tempo bookings → TDS @ 1% (individual) / 2% (company)
//    Example: ₹5,000 cab payment → TDS ₹100 → Net ₹4,900
//
// 3. PAYMENT TO HOTELS (Section 194C):
//    Hotel bookings as agent → TDS @ 2% on payment
//    Exception: If hotel bills customer directly, no TDS
//
// 4. INSURANCE COMMISSION (Section 194D):
//    Commission from insurance company → TDS @ 5%
//
// 5. RENT FOR OFFICE (Section 194I):
//    Office space rent → TDS @ 10%
//
// 6. PROFESSIONAL FEES (Section 194J):
//    Legal, CA, consulting fees → TDS @ 10%

// TDS processing workflow:
// ┌─────────────────────────────────────────┐
// │  TDS Processing — Vendor Payment         │
// │                                            │
// │  Vendor: Rahul Transport Co.              │
// │  Payment: ₹25,000 (airport transfers)     │
// │                                            │
// │  TDS Analysis:                             │
// │  Section: 194C (Contractor — transport)   │
// │  Vendor type: Individual (PAN: BQRPK...)  │
// │  TDS Rate: 1%                             │
// │  TDS Amount: ₹250                         │
// │  Net Payment: ₹24,750                     │
// │                                            │
// │  PAN Status: ✅ Verified                  │
// │  No PAN → Rate: 20%                       │
// │                                            │
// │  Threshold check:                          │
// │  FY total to vendor: ₹1,85,000            │
// │  Single payment threshold: ₹30,000 ✅     │
// │  FY threshold: ₹1,00,000 ✅               │
// │                                            │
// │  [Approve & Pay ₹24,750]                  │
// │  TDS ₹250 auto-deposited                  │
// └─────────────────────────────────────────────┘

// TDS Returns:
// Form 24Q — TDS on salary (quarterly)
// Form 26Q — TDS on non-salary payments (quarterly)
// Form 27Q — TDS on payments to non-residents (quarterly)
//
// Due dates:
// Q1 (Apr-Jun): July 15
// Q2 (Jul-Sep): October 15
// Q3 (Oct-Dec): January 15
// Q4 (Jan-Mar): May 31
//
// TDS Certificates:
// Form 16 — To employees (annual)
// Form 16A — To vendors (quarterly)
```

### Regulatory Filing Calendar

```typescript
interface RegulatoryCalendar {
  filings: RegulatoryFiling[];
  reminders: FilingReminder[];
  automation: FilingAutomation;
}

// Annual regulatory filing calendar for Indian travel agency:
// ─────────────────────────────────────────
// FILING          | DUE DATE      | FREQUENCY  | PLATFORM
// ──────────────────────────────────────────────────────────
// GSTR-1          | 11th monthly  | Monthly    | GST Portal
// GSTR-3B         | 20th monthly  | Monthly    | GST Portal
// TDS Return 24Q  | Quarter end+15| Quarterly  | TRACES
// TDS Return 26Q  | Quarter end+15| Quarterly  | TRACES
// TCS Return 27EQ | Quarter end+15| Quarterly  | TRACES
// GST Annual      | Dec 31        | Annual     | GST Portal
// GSTR-9          | Dec 31        | Annual     | GST Portal
// Income Tax      | Jul 31        | Annual     | IT Portal
// TDS Annual      | Jun 30        | Annual     | TRACES
// PF Return       | 15th monthly  | Monthly    | EPFO Portal
// ESI Return      | 15th monthly  | Monthly    | ESIC Portal
// Professional Tax| Monthly/Quarter| Varies    | State Portal
// IATA BSP        | Weekly/Biweekly| Per period| BSPlink
// ROC Filing      | Oct 30 (AGM)  | Annual     | MCA Portal
// TCS Certificates| Quarter end+15| Quarterly  | Generated
// Form 15CA/15CB  | Before remit  | Per remit  | IT Portal
// ─────────────────────────────────────────

// Filing calendar dashboard:
// ┌─────────────────────────────────────────┐
// │  Compliance Calendar — April 2026        │
// │                                            │
// │  🔴 Due Today                             │
// │  • GSTR-3B for March 2026                 │
// │    [File Now] → GST Portal                │
// │                                            │
// │  🟡 Due This Week                         │
// │  • GSTR-1 for March 2026 (May 11)        │
// │  • TCS deposit for Apr 1-15 (May 7)      │
// │                                            │
// │  🟢 Due This Month                        │
// │  • TCS deposit for Apr 16-30 (May 7)     │
// │  • PF return for April (May 15)          │
// │  • ESI return for April (May 15)         │
// │                                            │
// │  ⚠️ Action Required                       │
// │  • 3 vendor PAN verifications pending     │
// │  • 5 GSTR-2B mismatches to resolve        │
// │  • GSTR-9 annual return due Dec 31        │
// │                                            │
// │  [View Full Calendar] [Export to Excel]   │
// └─────────────────────────────────────────────┘

interface FilingReminder {
  filingId: string;
  reminderDays: number[];              // [7, 3, 1, 0] — days before due
  channels: ('email' | 'whatsapp' | 'in_app' | 'sms')[];
  recipients: string[];
  escalationAfter: number;             // Hours — escalate to manager
}

// Automation levels:
// Level 1: Manual — Agent downloads, reviews, uploads to portal
// Level 2: Semi-auto — System prepares JSON, agent reviews and uploads
// Level 3: Auto-file — System files directly via API (GSTN API, TRACES)
//
// Current target: Level 2 for most filings
// Goal: Level 3 for GSTR-1, GSTR-3B, TDS returns
```

---

## Open Problems

1. **GST rate ambiguity** — Tour packages with mixed components (domestic hotel + international flight) have ambiguous GST treatment. Agents need clear guidance on SAC code selection, but the law itself has gray areas that vary by interpretation.

2. **TCS customer friction** — Adding 5-20% TCS to an ₹80,000 trip is ₹4,000-16,000 extra. Customers often resist or delay bookings due to TCS. Explaining TCS as "adjustable against income tax" requires careful communication.

3. **Multi-state GST compliance** — Agencies operating across states (Mumbai + Delhi + Bangalore) need separate GST registrations and inter-branch accounting. State-specific rules (Kerala tourism tax, Uttarakhand eco-tax) add complexity.

4. **GSTR-2B matching reliability** — ITC claims depend on suppliers filing their GSTR-1 on time. Late-filing suppliers block ITC for the agency, affecting cash flow. Automated reminders to suppliers help but can't guarantee timely filing.

5. **Regulatory change velocity** — GST rates, TCS thresholds, and filing deadlines change frequently. The system needs a regulatory update mechanism that adjusts calculations without code changes.

---

## Next Steps

- [ ] Build GST auto-calculation engine with SAC code mapping and rate determination
- [ ] Create TCS collection workflow with PAN verification and exemption handling
- [ ] Implement TDS processing for vendor payments with section auto-determination
- [ ] Design compliance calendar with automated reminders and filing workflow
- [ ] Study tax platforms (ClearTax, Zoho Tax, Tally, QuickBooks India, ProfitBooks)
