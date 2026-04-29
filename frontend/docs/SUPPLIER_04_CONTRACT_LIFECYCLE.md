# Supplier Relationship & Contract Intelligence — Contract Lifecycle Management

> Research document for contract lifecycle management, terms extraction, compliance verification, and India-specific legal requirements (GST clauses, TDS, MSME compliance, stamp duty).

---

## Key Questions

1. **How do we manage the full contract lifecycle from template creation to renewal or termination?**
2. **How do we integrate e-signatures into the contract workflow?**
3. **How do we extract and digitize key contract terms from scanned/PDF contracts?**
4. **What key terms need continuous monitoring (commission rates, cancellation policies, allotments)?**
5. **How do we verify contract compliance on an ongoing basis?**
6. **India-specific: How do we verify GST clauses, TDS deduction requirements, and MSME payment timelines?**
7. **India-specific: How do we handle stamp duty and state-specific contract requirements?**

---

## Research Areas

### Contract Lifecycle Phases

```typescript
interface ContractLifecycle {
  contractId: string;
  supplierId: string;
  supplierName: string;
  type: ContractType;
  currentPhase: ContractPhase;
  phases: PhaseRecord[];
  parties: ContractParty[];
  keyDates: ContractDates;
  documents: ContractDocument[];
}

type ContractType =
  | 'rate_agreement'                  // Annual/seasonal rate contract
  | 'service_level_agreement'         // SLA with specific performance targets
  | 'commission_agreement'            // Commission-based relationship
  | 'allotment_agreement'             // Blocked inventory agreement
  | 'master_service_agreement'        // Umbrella agreement covering multiple services
  | 'non_disclosure_agreement'        // NDA for rate information
  | 'addendum';                       // Amendment to existing contract

type ContractPhase =
  | 'draft'                           // Template selected, being filled
  | 'internal_review'                 // Manager/legal review
  | 'sent_to_supplier'                // Supplier reviewing
  | 'negotiation'                     // Terms being negotiated
  | 'signature_pending'               // Final version, awaiting signatures
  | 'partially_signed'                // One party signed, waiting for other
  | 'fully_executed'                  // Both parties signed, active
  | 'active'                          // In effect, within validity period
  | 'amendment_pending'               // Change requested during active period
  | 'renewal_due'                     // Approaching expiration, renewal needed
  | 'expired'                         // Past end date, not renewed
  | 'terminated'                      // Terminated before end date
  | 'archived';                       // Stored for reference, no longer active

interface PhaseRecord {
  phase: ContractPhase;
  enteredAt: Date;
  exitedAt?: Date;
  actor: string;                      // Who initiated this phase
  notes?: string;
}

interface ContractParty {
  role: 'agency' | 'supplier';
  legalName: string;
  registeredAddress: string;
  gstin?: string;                     // GST Identification Number
  pan?: string;                       // Permanent Account Number
  authorizedSignatory: string;
  designation: string;
  contactEmail: string;
  contactPhone: string;
}

interface ContractDates {
  effectiveDate: Date;
  expiryDate: Date;
  autoRenewal: boolean;
  renewalNoticePeriod: string;        // "30 days before expiry"
  nextRenewalDate?: Date;
  terminationNoticePeriod: string;    // "60 days"
}

// Contract lifecycle flow:
//
// +----------+     +--------+     +-----------+     +----------+
// | Template | ---> | Draft  | ---> | Internal  | ---> | Send to  |
// | Selection|     | Create |     | Review    |     | Supplier |
// +----------+     +--------+     +-----------+     +----------+
//                                                       |
//                                         +-------------+
//                                         v
// +----------+     +--------+     +-----------+     +----------+
// | Active   | <--- | Signed | <--- | Signature | <--- | Negoti-  |
// | Contract |     | & Filed|     | Collection|     | ation    |
// +----------+     +--------+     +-----------+     +----------+
//     |
//     v
// +----------+     +----------+
// | Monitor  | --->| Renewal/ |
// | & Enforce|     | Terminate|
// +----------+     +----------+
```

### Contract Template System

```typescript
interface ContractTemplate {
  templateId: string;
  name: string;                       // "Standard Hotel Rate Agreement FY2026-27"
  category: SupplierCategory;
  version: string;
  sections: TemplateSection[];
  variables: TemplateVariable[];
  compliance: ComplianceCheck[];
}

interface TemplateSection {
  order: number;
  title: string;                      // "Rate Schedule", "Payment Terms"
  content: string;                    // Template text with {{variables}}
  isRequired: boolean;
  category: SectionCategory;
}

type SectionCategory =
  | 'parties'                         // Contracting party details
  | 'scope'                           // Services/products covered
  | 'rate_schedule'                   // Rates by season/room type
  | 'payment_terms'                   // Payment schedule, methods
  | 'cancellation'                    // Cancellation policies
  | 'allotment'                       // Inventory commitments
  | 'commission'                      // Commission structure
  | 'sla'                             // Service level commitments
  | 'gst_tax'                         // GST and tax clauses
  | 'tds'                             // TDS deduction clauses
  | 'msme'                            // MSME payment timeline clause
  | 'termination'                     // Termination conditions
  | 'dispute_resolution'              // Arbitration/jurisdiction
  | 'confidentiality'                 // NDA-like terms
  | 'force_majeure'                   // Unforeseeable circumstances
  | 'general_terms';                  // Boilerplate legal terms

interface TemplateVariable {
  name: string;                       // "supplier_name", "rate_table"
  type: 'text' | 'date' | 'number' | 'table' | 'boolean';
  source: 'supplier_profile' | 'rate_card' | 'negotiation' | 'manual';
  required: boolean;
  validation?: string;                // Regex or rule for validation
}

// Template variable resolution:
// {{supplier_legal_name}} → From supplier profile
// {{rate_table}} → From negotiated rate schedule (auto-generated table)
// {{payment_terms_days}} → From negotiation outcome
// {{gstin_agency}} → From agency profile
// {{gstin_supplier}} → From supplier profile
// {{contract_start_date}} → Calculated from negotiation timeline
// {{contract_end_date}} → Typically March 31 (Indian FY end)
// {{jurisdiction_state}} → Determined by supplier's registered state
```

### E-Signature Integration

```typescript
interface ESignatureWorkflow {
  documentId: string;
  contractId: string;
  provider: ESignatureProvider;
  status: ESignatureStatus;
  signers: Signer[];
  auditTrail: SignatureAuditEntry[];
}

type ESignatureProvider =
  | 'adobe_sign'                      // Adobe Acrobat Sign
  | 'docusign'                        // DocuSign
  | 'zoho_sign'                       // Zoho Sign (popular in India)
  | 'msign'                           // MSign (Indian provider)
  | 'emudhra'                         // eMudhra (Indian digital signature)
  | 'manual';                         // Print-sign-scan (fallback)

type ESignatureStatus =
  | 'preparing'                       // Document being prepared for signature
  | 'sent'                            // Sent to signers
  | 'viewed'                          // Signer has opened the document
  | 'signed_by_one'                   // One party signed
  | 'completed'                       // All parties signed
  | 'declined'                        // Signer declined to sign
  | 'expired'                         // Signature request expired
  | 'voided';                         // Cancelled by sender

interface Signer {
  party: 'agency' | 'supplier';
  name: string;
  email: string;
  phone?: string;
  signingOrder: number;               // 1 = signs first
  signingMethod: 'digital_signature'  // DSC token (Indian standard)
                  | 'aadhaar_esign'   // Aadhaar-based eSign
                  | 'email_otp'       // Email-based OTP verification
                  | 'sms_otp';        // SMS-based OTP verification
  signedAt?: Date;
  ipAddress?: string;
}

// India-specific e-signature considerations:
//
// 1. Digital Signature Certificates (DSC):
//    - Class 3 DSC required for company documents
//    - Issued by licensed Certifying Authorities (eMudhra, Sify, Capricorn)
//    - Valid for 1-2 years, must be renewed
//    - USB token-based (most common)
//
// 2. Aadhaar-based eSign:
//    - Valid under IT Act 2000
//    - Uses Aadhaar authentication (OTP or biometric)
//    - Growing acceptance for B2B contracts
//    - Free or low-cost
//
// 3. Hybrid approach (recommended):
//    - Agency signs with DSC (company standard)
//    - Supplier can use Aadhaar eSign or DSC
//    - Fallback: wet signature + scanned copy
//    - Maintain both digital and physical copies
//
// 4. Legal validity:
//    - IT Act 2000 Section 5 recognizes digital signatures
//    - Must use licensed CA for DSC
//    - Aadhaar eSign recognized since 2015
//    - Retain audit trail (timestamp, IP, authentication method)
```

### Contract Terms Extraction & Digitization

```typescript
interface ContractTerms {
  contractId: string;
  extractedAt: Date;
  extractionMethod: 'auto_ocr' | 'manual_entry' | 'template_match';
  confidence: number;
  keyTerms: KeyTerm[];
  monitoringRules: MonitoringRule[];
}

interface KeyTerm {
  category: KeyTermCategory;
  term: string;
  value: string | number | DateRange;
  source: string;                     // Page/section reference in original document
  confidence: number;
  requiresMonitoring: boolean;
}

type KeyTermCategory =
  | 'commission_rate'
  | 'payment_terms'
  | 'cancellation_policy'
  | 'allotment'
  | 'rate_schedule'
  | 'validity_period'
  | 'termination_clause'
  | 'gst_clause'
  | 'tds_clause'
  | 'msme_clause'
  | 'force_majeure'
  | 'exclusivity'
  | 'minimum_commitment'
  | 'dispute_resolution';

// Key term extraction pipeline:
//
// 1. Document ingestion:
//    - PDF contract received (scanned or digital)
//    - Stored in document vault
//    - OCR processing if scanned
//
// 2. Term identification:
//    - Pattern matching for known clauses (regex-based)
//    - NLP extraction for free-form terms
//    - Template matching if contract was generated from our template
//
// 3. Structuring:
//    - Normalize extracted terms into structured format
//    - Cross-reference with supplier profile data
//    - Flag inconsistencies
//
// 4. Monitoring setup:
//    - Create monitoring rules from extracted terms
//    - Set up alerts for key dates (expiry, renewal, rate change)
//    - Link to booking engine for rate enforcement
//
// OCR extraction targets for Indian contracts:
// - GSTIN of both parties (15-char regex)
// - PAN of both parties (10-char regex)
// - Rate tables (season-wise, room-type-wise)
// - Payment terms (net days)
// - Cancellation slabs (e.g., "30 days: 10%, 15 days: 50%, 7 days: 100%")
// - Validity dates
// - Stamp duty paid (state-specific)

interface MonitoringRule {
  ruleId: string;
  contractId: string;
  termCategory: KeyTermCategory;
  ruleType: MonitoringRuleType;
  parameters: Record<string, string>;
  frequency: 'real_time' | 'daily' | 'weekly' | 'monthly';
  alertThreshold?: string;
  notificationTargets: string[];
}

type MonitoringRuleType =
  | 'expiry_alert'                    // Contract expiring in N days
  | 'rate_compliance'                 // Supplier charging per agreed rates
  | 'payment_term_compliance'         // Payments within agreed terms
  | 'cancellation_enforcement'        // Cancellation penalties per contract
  | 'allotment_utilization'           // Allotment usage tracking
  | 'commission_accuracy'             // Commission calculated correctly
  | 'gst_clause_compliance'           // GST invoicing per contract terms
  | 'tds_deduction_compliance'        // TDS deducted per contract
  | 'msme_payment_timeline'           // Payment within MSME-mandated timeline
  | 'exclusivity_check';              // Supplier not selling to direct competitor
```

### Contract Compliance Verification

```typescript
interface ComplianceVerification {
  contractId: string;
  verificationDate: Date;
  checks: ComplianceCheck[];
  overallCompliance: 'fully_compliant' | 'partially_compliant' | 'non_compliant';
  issues: ComplianceIssue[];
  remediation: RemediationAction[];
}

interface ComplianceCheck {
  checkType: ComplianceCheckType;
  expectedValue: string;
  actualValue: string;
  compliant: boolean;
  severity: 'info' | 'warning' | 'critical';
  evidence: string;                   // Invoice number, booking reference, etc.
}

type ComplianceCheckType =
  // Rate compliance
  | 'rate_charged_per_contract'       // Supplier billed at agreed rate
  | 'rate_parity_maintained'          // No lower OTA rates for same period
  | 'seasonal_tier_correct'           // Correct seasonal multiplier applied
  // Payment compliance
  | 'payment_within_terms'            // Agency paid supplier within agreed days
  | 'tds_deducted_correctly'          // TDS deducted at agreed rate
  | 'gst_invoiced_correctly'          // GST on invoice matches contract terms
  // Cancellation compliance
  | 'cancellation_penalty_applied'    // Cancellation charges per contract
  | 'refund_timeliness'               // Refund processed within agreed timeline
  // Allotment compliance
  | 'allotment_honored'               // Supplier honored allotted rooms/seats
  | 'release_period_respected'        // Agency released unneeded allotment on time
  // Service compliance
  | 'sla_met'                         // Service levels per SLA contract
  | 'invoice_documentation'           // Invoices have all required fields
  // Legal compliance
  | 'gst_filing_status'               // Supplier's GSTR-1 filed (for ITC)
  | 'msme_payment_timeline'           // Payment to MSME supplier within 45 days
  | 'stamp_duty_paid'                 // Contract properly stamped
  | 'tds_return_filed';               // TDS return filed for supplier payments

interface ComplianceIssue {
  issueId: string;
  checkType: ComplianceCheckType;
  description: string;
  impact: string;                     // Financial or operational impact
  rootCause: string;
  affectedTransactions: string[];
}

interface RemediationAction {
  action: string;
  responsible: 'agency' | 'supplier';
  deadline: Date;
  status: 'pending' | 'in_progress' | 'completed';
}

// Compliance verification workflow:
//
// Automated checks (run continuously):
// - Rate compliance: Compare every invoice rate to contracted rate
// - Payment timeliness: Compare payment date to contract terms
// - TDS deduction: Verify TDS amount on each payment
// - GST invoicing: Check GSTIN, HSN, tax amounts on invoices
//
// Periodic checks (run weekly/monthly):
// - Rate parity: Spot-check OTA rates vs. contracted rates
// - Allotment utilization: Review allotment usage vs. commitment
// - SLA compliance: Aggregate SLA metrics vs. targets
//
// Event-triggered checks:
// - Invoice received: Verify rate, GST, terms match contract
// - Cancellation: Verify penalty applied per contract
// - Contract renewal: Full compliance review before renewal
```

### India-Specific: GST Clause Verification

```typescript
interface GSTClauseVerification {
  contractId: string;
  supplierGSTIN: string;
  verification: GSTVerification[];
}

interface GSTVerification {
  checkPoint: string;
  expected: string;
  actual: string;
  status: 'pass' | 'fail' | 'warning';
  action?: string;
}

// GST clause checks in supplier contracts:
//
// 1. GSTIN Validation:
//    - Supplier GSTIN must be valid and active
//    - Check: GSTIN regex + GST portal lookup
//    - Must match the state of supplier's registered address
//
// 2. GST Rate Agreement:
//    - Contract must specify applicable GST rate per service
//    - Hotel rooms: 12% (< ₹7,500) or 18% (>= ₹7,500)
//    - Tour packages: 5% with abatement
//    - Transport: 5% with ITC
//    - Verify agreed rate matches actual GST rate law
//
// 3. GST Treatment (Inclusive vs. Exclusive):
//    - Contract must clearly state if rates are GST-inclusive or exclusive
//    - Common ambiguity: "Rate: ₹10,000 per night" — is GST included?
//    - Recommendation: Always specify explicitly in contract
//
// 4. Reverse Charge Mechanism (RCM):
//    - Certain services attract GST under reverse charge (agency pays)
//    - GTA (Goods Transport Agency) services: 5% RCM
//    - Legal services: 18% RCM
//    - Contract must specify who bears RCM liability
//
// 5. Input Tax Credit (ITC) Eligibility:
//    - Agency can claim ITC only if:
//      a. Supplier has filed GSTR-1 (auto-populates in agency's GSTR-2A)
//      b. Invoice has valid GSTIN, HSN code, tax breakup
//      c. Service is used for business (not exempt supply)
//    - Contract should require supplier to file GSTR-1 timely
//    - Include penalty clause for delayed filing causing ITC loss
//
// 6. E-Invoice Compliance:
//    - Suppliers with turnover > ₹5 crore must generate e-invoices
//    - E-invoice IRN (Invoice Reference Number) must be on invoice
//    - Agency should verify IRN for eligible suppliers
```

### India-Specific: TDS Deduction Clauses

```typescript
interface TDSClauseConfig {
  contractId: string;
  supplierPAN: string;
  tdsApplicable: TDSSection[];
}

interface TDSSection {
  section: string;                    // "194C", "194H", "194J"
  description: string;
  rate: number;                       // TDS rate %
  threshold: number;                  // Single payment threshold
  annualThreshold: number;            // Annual threshold
  panRequired: boolean;               // PAN mandatory for lower deduction
  noPANRate?: number;                 // Higher rate if PAN not available
}

// TDS sections relevant to travel agency supplier contracts:
//
// Section 194C — Payment to Contractors:
//   Applicable: Transport, tour operators, event management
//   Rate: 1% (if PAN provided), 20% (without PAN)
//   Threshold: ₹30,000 single payment, ₹1,00,000 annual
//   Contract clause: "Agency shall deduct TDS @ 1% u/s 194C"
//
// Section 194H — Commission:
//   Applicable: Commission paid to agents/sub-agents
//   Rate: 5% (if PAN provided), 20% (without PAN)
//   Threshold: ₹15,000 single payment
//   Contract clause: "Commission payments subject to TDS @ 5% u/s 194H"
//
// Section 194J — Professional Fees:
//   Applicable: Guide fees, consultant fees, photography services
//   Rate: 10% (if PAN provided), 20% (without PAN)
//   Threshold: ₹30,000 single payment, no annual threshold
//   Contract clause: "Professional fees subject to TDS @ 10% u/s 194J"
//
// Section 194I — Rent:
//   Applicable: Office rent, branch rent, equipment rent
//   Rate: 10% (landlord), 2% (plant/machinery)
//   Threshold: ₹2,40,000 annual
//
// Contract TDS clause template:
// "The Agency shall deduct Tax at Source (TDS) as per applicable
//  provisions of the Income Tax Act, 1961. The Supplier shall provide
//  its Permanent Account Number (PAN) to the Agency. In the absence
//  of a valid PAN, TDS shall be deducted at the higher rate of 20%.
//  The Supplier shall furnish Form 15G/15H if eligible for
//  lower/non-deduction of TDS."
```

### India-Specific: MSME Payment Timeline Compliance

```typescript
interface MSMECompliance {
  supplierId: string;
  isMSME: boolean;
  msmeRegistration?: {
    udyamNumber: string;              // Udyam Registration Number
    registrationDate: Date;
    category: 'micro' | 'small' | 'medium';
    investment: number;               // Investment in plant/machinery
    turnover: number;
  };
  paymentTimelineDays: number;        // 45 days for MSME
  complianceTracking: MSMEPaymentTrack[];
}

interface MSMEPaymentTrack {
  invoiceId: string;
  invoiceDate: Date;
  amount: number;
  paymentDueDate: Date;               // invoice date + 45 days (MSME)
  actualPaymentDate?: Date;
  daysTaken?: number;
  compliant: boolean;
  interestLiability?: number;         // If late, compound interest @ bank rate + 3
}

// MSME Samadhan Act compliance:
//
// The Micro, Small and Medium Enterprises Development (MSMED) Act, 2006
// mandates:
//
// 1. Payment timeline:
//    - Buyer must pay MSME supplier within 45 days of accepting goods/services
//    - If no written agreement: 15 days from acceptance
//    - If agreement specifies longer: Cannot exceed 45 days
//
// 2. Interest on delayed payment:
//    - Compound interest at 3x the bank rate notified by RBI
//    - From the date payment was due until actual payment
//    - Example: If bank rate is 6.5%, interest = 19.5% compounded monthly
//
// 3. Contract clause requirement:
//    "In compliance with Section 15 of the MSMED Act, 2006, the Agency
//     shall make payment to the Supplier within 45 (forty-five) days from
//     the date of acceptance of goods/services. In the event of delay,
//     the Agency shall be liable to pay compound interest at the rate
//     specified under Section 16 of the MSMED Act, 2006."
//
// 4. Practical implications:
//    - Must identify which suppliers are MSME-registered
//    - Track 45-day timeline separately for MSME suppliers
//    - Cannot contractually agree to longer payment terms
//    - Late payment interest is a real financial liability
//    - MSME suppliers can file complaints on Samadhan portal
//
// 5. Verification:
//    - Check Udyam Registration Number on udyamregistration.gov.in
//    - Cross-reference with MSME database
//    - Annual re-verification (MSME status can change)
//    - Flag non-MSME suppliers who become MSME-registered mid-contract
```

### India-Specific: Stamp Duty & State Requirements

```typescript
interface StampDutyConfig {
  contractState: string;              // Indian state where contract is executed
  contractType: ContractType;
  contractValue: number;
  stampDuty: StampDutyCalculation;
}

interface StampDutyCalculation {
  state: string;
  dutyType: 'ad_valorem' | 'fixed';   // Percentage of value or fixed amount
  rate: number;                        // % or fixed amount in ₹
  minimumDuty: number;
  maximumDuty?: number;
  calculatedDuty: number;
  paymentMethod: 'e_stamp' | 'physical_stamp' | 'franking';
}

// Stamp duty considerations:
//
// 1. State-specific rates:
//    Stamp duty on agreements varies by state. Some examples:
//    - Maharashtra: 0.1% of contract value (min ₹500)
//    - Karnataka: 1% of contract value (for service agreements)
//    - Delhi: ₹100 for general agreements
//    - Tamil Nadu: 1% of contract value
//    - Gujarat: varies by agreement type
//
// 2. Which state's law applies?
//    - Where the contract is executed (signed)
//    - Or where the property/service is located
//    - For service agreements: typically where the supplier is located
//    - Complex for pan-India suppliers with operations in multiple states
//
// 3. E-stamping (recommended):
//    - Available through Stock Holding Corporation of India (SHCIL)
//    - Also available through authorized banks
//    - More convenient than physical stamp paper
//    - Verifiable online with unique certificate number
//
// 4. Practical approach:
//    - For high-value contracts (> ₹10 lakh): Get e-stamped
//    - For standard rate agreements: Include stamp duty clause
//      in contract (supplier and agency share the cost)
//    - For MSME suppliers: Ensure compliance even for small contracts
//
// 5. State-specific contract requirements:
//    - Some states require registration for contracts > certain value
//    - Karnataka: Agreements > ₹500 must be on stamp paper
//    - Maharashtra: Some agreements must be registered within 4 months
//    - Need a state-wise compliance matrix

interface StateRequirement {
  state: string;
  stampDutyForServiceAgreement: string;
  registrationRequired: boolean;
  registrationThreshold?: number;     // Value above which registration needed
  languageRequirement?: string;       // Some states require bilingual contracts
  specialNotes: string;
}
```

---

## Open Problems

1. **Contract digitization accuracy** — Many existing supplier contracts are physical documents, sometimes handwritten, with stamps and signatures. OCR accuracy on these is poor. Manual digitization is expensive and slow. Need a pragmatic approach for the initial migration.

2. **E-signature adoption among Indian suppliers** — Many small suppliers (homestays, local guides, transport operators) have never used digital signatures. Requiring e-signatures creates friction. But wet-signature contracts are harder to track and enforce. What is the right balance?

3. **GST clause complexity across contract types** — A hotel rate agreement, a transport service agreement, and a tour package contract all have different GST implications. Templates must account for these differences. One-size-fits-all GST clauses will cause compliance issues.

4. **MSME identification is voluntary** — Suppliers self-declare MSME status. Some eligible suppliers don't register (missing benefits). Some may register to enforce 45-day payment. Agency needs to proactively check and maintain current MSME status records.

5. **Stamp duty enforcement is inconsistent** — In practice, many Indian businesses don't properly stamp contracts. The risk is that unstamped contracts are inadmissible in court. But the cost and effort of stamping every contract (especially low-value ones) is disproportionate.

6. **Contract term monitoring at scale** — A mid-size agency may have 200+ active supplier contracts, each with 10-20 key terms to monitor. That is 2,000-4,000 data points to track continuously. Automation is essential, but building monitoring rules for each contract type requires significant upfront investment.

---

## Next Steps

- [ ] Design contract template system with variable substitution
- [ ] Build contract lifecycle state machine with phase transitions
- [ ] Evaluate e-signature providers (Zoho Sign, DocuSign, eMudhra) for India compatibility
- [ ] Build key term extraction pipeline from PDF/OCR contracts
- [ ] Create monitoring rule engine for contract term compliance
- [ ] Build GST clause verification checklist into contract templates
- [ ] Implement MSME payment timeline tracking with 45-day enforcement
- [ ] Research state-wise stamp duty requirements and create compliance matrix
- [ ] Design contract compliance dashboard with automated checks
- [ ] Study contract management platforms (Agiloft, Icertis, Zoho Contracts)
