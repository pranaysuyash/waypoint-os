# Regulatory & Licensing — IATA Accreditation & BSP

> Research document for IATA accreditation, Billing and Settlement Plan (BSP), airline accreditation, and GDS compliance.

---

## Key Questions

1. **What is IATA accreditation and why does it matter?**
2. **How does the Billing and Settlement Plan (BSP) work in India?**
3. **What are the financial requirements for IATA accreditation?**
4. **How do GDS (Amadeus, Sabre, Travelport) integrations work?**
5. **What compliance is needed for airline ticketing?**

---

## Research Areas

### IATA Accreditation Model

```typescript
interface IATAAccreditation {
  agencyId: string;
  accreditation: AccreditationDetail;
  bsp: BSPDetail;
  financial: IATAFinancial;
  compliance: IATACompliance;
}

interface AccreditationDetail {
  iataNumber: string;                 // 8-digit IATA numeric code
  name: string;
  location: string;
  category: IATACategory;
  status: IATAStatus;
  accreditedDate: Date;
  lastReviewDate: Date;
  nextReviewDate: Date;
}

type IATACategory =
  | 'accredited_agent'                // Full accreditation (can ticket all airlines)
  | 'cargo_agent'                     // Cargo accreditation only
  | 'general_sales_agent'             // GSA for specific airlines
  | 'consolidator';                   // Wholesale ticketing agent

type IATAStatus =
  | 'active'
  | 'probation'
  | 'suspended'
  | 'terminated'
  | 'application_pending';

// IATA Accreditation requirements (India):
//
// 1. Business Requirements:
//    - Registered business entity (min 2 years for full accreditation)
//    - Minimum 2 qualified staff (IATA/UFTAA certified or equivalent)
//    - Physical office location (not home office)
//    - Computer reservation system (GDS) access
//    - Minimum annual sales: Varies by location tier
//      Tier 1 cities: ₹5 crore annual airline sales
//      Tier 2 cities: ₹2 crore annual airline sales
//      Tier 3 cities: ₹50 lakh annual airline sales
//
// 2. Financial Requirements:
//    - Financial guarantee: Bank guarantee or cash deposit
//      Amount: Based on expected monthly billing (typically ₹5-25 lakh)
//    - Minimum net worth: ₹5 lakh (varies by location)
//    - Positive net worth in last audited financial statements
//    - No outstanding airline debts
//
// 3. Operational Requirements:
//    - GDS access (Amadeus, Sabre, or Travelport)
//    - BSP-compatible ticketing system
//    - Secure premises with safe for blank ticket stock
//    - Dedicated phone line and email
//    - Office signage with IATA logo (once accredited)
//
// 4. Staff Qualifications:
//    - At least 1 staff with IATA/UFTAA Foundation Diploma
//    - OR equivalent training (airline-recognized certification)
//    - Staff must pass IATA Agency Examiner assessment
//    - Ongoing training requirements (annual refresher)

interface BSPDetail {
  billingPeriod: string;              // e.g., "BSP-IN-2026-04"
  settlementCurrency: string;         // INR
  billingFrequency: 'weekly' | 'biweekly' | 'monthly';
  airlines: BSPAirline[];
  transactions: BSPTransaction[];
  settlement: BSPSettlement;
}

// BSP (Billing and Settlement Plan) India:
//
// BSP is the system through which IATA-accredited agents:
// 1. Issue airline tickets on behalf of airlines
// 2. Report ticket sales to airlines
// 3. Settle payments through a central clearing house
//
// BSP flow:
// Agent issues ticket via GDS → BSP records transaction
//   → Agent reports sales to BSP → BSP aggregates per airline
//   → BSP deducts from agent's bank account → BSP pays airlines
//   → Settlement cycle: Typically weekly (every Thursday)
//
// BSP financial model:
// - Agent collects payment from customer
// - Agent holds funds until BSP settlement date
// - BSP debits agent's bank account on settlement date
// - Risk: If agent doesn't have funds → BSP default
// - Mitigation: Bank guarantee covers default risk
//
// BSP billing:
// Sales: Tickets issued during billing period (debits)
// Refunds: Tickets refunded during billing period (credits)
// ADMs: Airline Debit Memos (additional charges from airlines)
// ACMs: Airline Credit Memos (refunds from airlines)
// Net billing: Sales - Refunds + ADMs - ACMs = Amount due

interface BSPTransaction {
  transactionId: string;
  type: BSPTransactionType;
  airline: string;
  ticketNumber: string;
  amount: Money;
  date: Date;
  status: 'pending' | 'settled' | 'disputed';
}

type BSPTransactionType =
  | 'sale'                            // Ticket issued
  | 'refund'                          // Ticket refunded
  | 'void'                            // Ticket voided (within 24 hours)
  | 'exchange'                        // Ticket exchanged/reissued
  | 'adm'                             // Airline Debit Memo
  | 'acm';                            // Airline Credit Memo

// BSP reporting timeline:
// Monday: Agent's billing period ends
// Tuesday: BSP processes agent's transactions
// Wednesday: BSP statement available for review
// Thursday: Settlement — BSP debits agent's account
// Friday: BSP remits to airlines
// Agent has until Wednesday to dispute any transactions
```

### GDS Integration & Compliance

```typescript
interface GDSIntegration {
  provider: GDSProvider;
  access: GDSAccess;
  pnr: PNRManagement;
  ticketing: TicketingSystem;
  compliance: GDSCompliance;
}

type GDSProvider =
  | 'amadeus'                         // Market leader in India (~45%)
  | 'sabre'                           // Second largest (~30%)
  | 'travelport';                     // Galileo/Worldspan (~25%)

interface GDSAccess {
  pseudoCityCode: string;             // PCC (agent's GDS office ID)
  username: string;
  contractType: 'full' | 'web';      // Full GDS access or web-based
  segments: string[];                 // Air, Hotel, Car, etc.
  trainingComplete: boolean;
  contractExpiry: Date;
}

// GDS access types:
// Full access: Terminal-based (cryptic commands), API access
//   - Used by: Large agencies with trained staff
//   - Training: 2-4 weeks certification
//   - Cost: ₹15,000-50,000/month (based on segments)
//
// Web-based: Browser-based booking tool
//   - Used by: Small-to-medium agencies
//   - Training: 2-3 days
//   - Cost: ₹5,000-15,000/month
//
// API access: Programmatic integration
//   - Used by: OTAs and tech-savvy agencies
//   - Cost: Per-segment pricing + minimum commitment
//   - Our platform: Uses GDS APIs behind the scenes

interface PNRManagement {
  pnrCreation: PNRWorkflow;
  queueManagement: QueueConfig;
  qualityControl: QCConfig;
}

// PNR (Passenger Name Record) lifecycle:
// 1. Create PNR: Agent searches flights → Selects → Creates PNR
// 2. Add passengers: Name, DOB, passport info
// 3. Add segments: Flight segments with class and fare
// 4. Add contact: Phone, email for each passenger
// 5. Add SSRs: Special service requests (meal, wheelchair, infant)
// 6. Add OSI: Other service information (FQTV numbers, corporate ID)
// 7. Add remarks: Internal agent notes
// 8. Price and store fare: Fare quote → Store in PNR
// 9. Ticket: Issue ticket (creates ticket number)
// 10. Post-ticketing: Seat assignment, baggage, check-in
//
// PNR quality control:
// - Mandatory fields check: Name matches passport, contact info present
// - Fare rules check: Ticketing deadline not missed, fare valid
// - Duplicate booking check: Same passenger, same flight, same date
// - Segment validation: Connection time sufficient, no impossible routing
// - Name format: Last/FIRST MIDDLE (IATA standard)

interface TicketingSystem {
  ticketingRules: TicketingRule[];
  voidWindow: number;                 // Hours (usually 24 for void)
  refundProcessing: RefundConfig;
  reissueRules: ReissueRule[];
}

// Ticketing compliance:
// VOID: Cancel within 24 hours of issuance, no penalty
//   - Must be done before BSP cutoff (Monday night)
//   - Full refund, no airline penalty
//
// REFUND: After void window
//   - Subject to fare rules (cancellation penalty)
//   - Refund processed via BSP (appears as credit)
//   - Timeline: 7-30 days for processing
//
// REISSUE/EXCHANGE: Change ticket
//   - Subject to fare rules (change penalty + fare difference)
//   - New ticket issued, old ticket referenced
//   - Additional collection or residual value
//
// NDC (New Distribution Capability):
// - IATA's new standard for airline distribution
// - XML-based API (vs. traditional GDS EDIFACT)
// - Airlines: Offering richer content (branded fares, ancillaries)
// - India adoption: IndiGo, Vistara, Air India piloting NDC
// - Future: NDC will complement or replace traditional GDS
```

### IATA Financial Compliance

```typescript
interface IATAFinancial {
  bankGuarantee: BankGuarantee;
  bspSettlement: BSPSettlementConfig;
  financialReview: FinancialReview;
  riskAssessment: IATARiskAssessment;
}

interface BankGuarantee {
  bankName: string;
  guaranteeAmount: Money;
  expiryDate: Date;
  renewalStatus: 'current' | 'renewal_pending' | 'expired';
}

// Bank guarantee management:
// Amount: Based on 2× average monthly BSP billing
// Example: ₹10 lakh average monthly billing → ₹20 lakh bank guarantee
//
// Renewal: 30 days before expiry
// Process:
// 1. Bank issues renewal letter
// 2. Submit to IATA regional office
// 3. IATA acknowledges receipt
// 4. If not renewed: IATA may suspend accreditation
//
// Cost: 1-2% of guarantee amount per year (₹2-4 lakh for ₹20 lakh BG)
// Shared across: Agency bears the cost

interface BSPSettlementConfig {
  bankAccount: string;
  autoDebit: boolean;
  settlementDay: string;              // "Thursday"
  creditLimit: Money;
  alertThreshold: number;             // % of credit limit
}

// BSP settlement risk management:
// - Auto-debit from agency bank account on settlement day
// - Must maintain sufficient balance on settlement day
// - If insufficient funds: BSP default → Suspension risk
// - Platform alert: 48 hours before settlement, show expected debit
// - Platform feature: Auto-sweep from linked accounts
// - Credit limit: Pre-approved overdraft for settlement (bank-dependent)

interface IATARiskAssessment {
  riskScore: number;                  // 0-100 (lower = safer)
  factors: RiskFactor[];
  reviewDate: Date;
  recommendations: string[];
}

// IATA risk factors:
// - Settlement timeliness (missed settlements = high risk)
// - Financial ratio (debt-to-equity, current ratio)
// - BSP billing volume trends (declining = concern)
// - ADM frequency (high ADMs = quality issues)
// - Staff turnover (new staff = training risk)
// - Years of accreditation (new agencies = higher risk)
```

---

## Open Problems

1. **NDC transition** — Airlines are pushing NDC but GDS providers and agencies are slow to adopt. Need to support both traditional and NDC channels.

2. **BSP settlement risk** — Agent collects customer money but doesn't settle with BSP. This creates airline debt and potential accreditation loss. Need real-time settlement monitoring.

3. **Staff certification cost** — IATA/UFTAA training costs ₹50,000-1,50,000 per staff. Small agencies struggle with this investment.

4. **Multi-GDS complexity** — Agencies often need 2-3 GDS contracts (different airlines prefer different GDS). Managing multiple systems is complex.

5. **Airline direct deals** — Airlines increasingly push direct booking (IndiGo app, Air India website). IATA accreditation value is declining for domestic airlines.

---

## Next Steps

- [ ] Build IATA accreditation tracking and renewal management
- [ ] Design BSP settlement monitoring with risk alerts
- [ ] Create GDS integration architecture (Amadeus + Sabre)
- [ ] Build ticketing compliance with void/refund/reissue workflows
- [ ] Study IATA systems (BSPlink, IATA Accreditation, NDC standard)
