# Regulatory & Licensing — GST/TCS Compliance & Filing

> Research document for GST compliance, TCS on overseas tours, invoicing requirements, and tax filing automation.

---

## Key Questions

1. **How does GST apply to travel agency services?**
2. **What is TCS on overseas tour packages and how do we comply?**
3. **What are the invoicing requirements for travel services?**
4. **How do we automate GST return filing?**
5. **What are the record-keeping and audit requirements?**

---

## Research Areas

### GST for Travel Agencies

```typescript
interface GSTConfig {
  agencyId: string;
  gstin: string;
  registrationType: GSTRegistrationType;
  rates: GSTRateConfig;
  invoicing: GSTInvoicing;
  filing: GSTFiling;
  inputTaxCredit: ITCManagement;
}

type GSTRegistrationType =
  | 'regular'                         // Monthly filing, ITC eligible
  | 'composition';                    // Quarterly filing, no ITC, lower rate

// GST rates for travel services:
//
// 1. Air Travel Agent Services:
//    - Domestic flight tickets: 5% GST (2.5% CGST + 2.5% SGST)
//    - International flight tickets: 5% GST (on commission/markup, not ticket value)
//    - Option: Pay 0.6% of basic fare as GST (deemed value) or actual commission × 5%
//
// 2. Tour Packages:
//    - Domestic tour: 5% GST (with ITC on inputs)
//    - Or 1.8% GST (without ITC) — for accommodation-inclusive packages
//    - International tour (sold in India): 5% GST on package value
//
// 3. Hotel Accommodation:
//    - Room tariff < ₹1,000/night: 0% (exempt)
//    - Room tariff ₹1,000-2,500/night: 12% GST
//    - Room tariff ₹2,500-7,500/night: 12% GST
//    - Room tariff > ₹7,500/night: 18% GST
//    - Note: If bundled in tour package, package GST rate applies
//
// 4. Other Services:
//    - Visa assistance: 18% GST
//    - Travel insurance: 18% GST
//    - Forex services: 18% GST
//    - Car rental: 5% GST (with ITC)
//    - Restaurant (in hotel): 5% GST
//
// GST on tour package example:
// Kerala Backwaters Tour: ₹45,000 per person
//   Breakdown: Flights ₹12,000 + Hotels ₹15,000 + Transport ₹8,000
//             + Activities ₹6,000 + Agent margin ₹4,000
//   GST (5%): ₹2,250 per person
//   Total invoice: ₹47,250 per person

interface GSTInvoicing {
  invoiceFormat: GSTInvoiceFormat;
  hsnCodes: HSNCodeConfig;
  eInvoicing: EInvoiceConfig;
  creditNotes: CreditNoteConfig;
}

interface GSTInvoiceFormat {
  mandatoryFields: string[];
  templateTypes: InvoiceTemplateType[];
  autoGeneration: boolean;
}

// GST Invoice mandatory fields:
// - GSTIN of supplier (agency)
// - GSTIN of recipient (if registered, for B2B)
// - Invoice number (sequential, unique per financial year)
// - Invoice date
// - Place of supply (state code)
// - HSN/SAC code for each service
// - Taxable value, CGST, SGST, IGST amounts
// - Total invoice value
// - Reverse charge indicator (if applicable)
//
// HSN/SAC codes for travel:
// - 998421: Tour operator services
// - 998413: Air passenger transport (booking agency)
// - 996331: Accommodation services
// - 998511: Visa processing services
// - 997133: Travel insurance services
// - 9996: Car rental services
//
// e-Invoicing (mandatory for turnover > ₹5 crore):
// - Generate IRN (Invoice Reference Number) via GST portal
// - Submit JSON to Invoice Registration Portal (IRP)
// - QR code on invoice for verification
// - Applicability: Most established travel agencies qualify
// - Platform integration: Auto-generate and submit e-invoices

interface GSTFiling {
  gstr1: GSTR1Config;                 // Outward supplies
  gstr3b: GSTR3BConfig;               // Summary return
  gstr9: GSTR9Config;                 // Annual return
  autoFiling: AutoFilingConfig;
}

// GST filing workflow:
// Every booking creates GST entries:
//   - Taxable value, CGST, SGST/IGST calculated per line item
//   - Invoice auto-generated with GST details
//   - Entry recorded for GSTR-1 reporting
//
// GSTR-1 (Outward supplies) — Due: 11th of following month:
// - B2B Invoices: Invoice-wise details
// - B2C Large (> ₹2.5 lakh): Invoice-wise details
// - B2C Small: Consolidated by rate
// - Credit/Debit notes
// - Export details (if international packages)
//
// Platform auto-generates GSTR-1 from booking data:
// 1. Pull all bookings for the billing period
// 2. Categorize: B2B vs B2C, Large vs Small
// 3. Calculate GST per HSN code
// 4. Generate GSTR-1 JSON file
// 5. Agency reviews and files via GST portal (or auto-files with API)
//
// ITC (Input Tax Credit) management:
// - ITC on hotel stays (agency's own business travel)
// - ITC on office rent, utilities, services
// - ITC on flight bookings (if acting as consolidator)
// - Must match with GSTR-2A (auto-populated from supplier filings)
// - ITC reversal: If payment to supplier not made within 180 days
```

### TCS on Overseas Tour Packages

```typescript
interface TCSConfig {
  enabled: boolean;
  threshold: Money;                   // ₹7 lakh (as of current rules)
  rates: TCSRates;
  collection: TCSCollection;
  filing: TCSFiling;
}

interface TCSRates {
  withPAN: number;                    // 5% above threshold
  withoutPAN: number;                 // 10% above threshold
  thresholdPerPerson: Money;          // ₹7 lakh per individual per year
  note: string;
}

// TCS (Tax Collected at Source) on overseas tour packages:
// Section 206C(1G) of Income Tax Act:
//
// Applies to: Overseas tour packages sold by travel agents
// Rate: 5% of amount exceeding ₹7 lakh per person per year
// Rate: 10% if PAN not available
// Threshold: ₹7 lakh per individual per financial year
//
// Example:
// Customer books Europe tour: ₹3,50,000
// Previous overseas tours this year: ₹5,00,000
// Total: ₹8,50,000
// TCS applicable on: ₹8,50,000 - ₹7,00,000 = ₹1,50,000
// TCS amount: 5% of ₹1,50,000 = ₹7,500
// Invoice total: ₹3,50,000 + ₹7,500 (TCS) = ₹3,57,500
//
// TCS tracking per customer:
// Must track total overseas tour spend per PAN per financial year
// Customer may book from multiple agencies (need PAN-based tracking)
// Agency only tracks own sales, but threshold is aggregate across all agencies
// Customer can claim TCS credit in their income tax return

interface TCSCollection {
  tracking: TCSTracking;
  collectionWorkflow: TCSCollectionWorkflow;
  certificate: TCSCertificate;
}

interface TCSTracking {
  customerId: string;
  customerPAN: string;
  financialYear: string;
  totalOverseasSpend: Money;
  threshold: Money;
  tcsCollected: Money;
  transactions: TCSTransaction[];
}

interface TCSTransaction {
  bookingId: string;
  packageType: 'overseas_tour';
  destination: string;
  amount: Money;
  tcsApplicable: boolean;
  tcsAmount: Money;
  collectedDate: Date;
}

// TCS collection workflow:
// 1. Customer inquires about overseas tour
// 2. Agent asks for PAN (mandatory for TCS)
// 3. System checks cumulative overseas spend for this PAN
// 4. If total > ₹7 lakh: Calculate TCS on excess amount
// 5. TCS shown as separate line item on invoice
// 6. Customer pays TCS along with package cost
// 7. TCS deposited to government by 7th of following month
// 8. TCS certificate (Form 27D) issued to customer within 15 days

// TCS filing:
// Form 27EQ: Quarterly TCS return
// Due dates: July 15, October 15, January 15, May 15
// Details: PAN of buyer, amount collected, TCS rate, TCS amount
// Penalty: If TCS not collected: 100% of TCS amount as penalty
//          If TCS not deposited: Interest @ 1% per month
```

### Record Keeping & Audit

```typescript
interface RecordKeeping {
  retention: RetentionPolicy;
  auditTrail: AuditTrailConfig;
  documentStorage: DocumentStorageConfig;
  auditPreparation: AuditPrepConfig;
}

interface RetentionPolicy {
  financialRecords: number;           // 8 years (Income Tax Act)
  gstRecords: number;                 // 6 years from end of financial year
  tcsRecords: number;                 // 7 years from end of financial year
  bookingRecords: number;             // 8 years (aligned with financial)
  customerData: string;               // Per DPDP Act (to be determined)
  contracts: number;                  // 3 years after contract ends
}

// Record retention requirements:
// GST: All invoices, credit notes, debit notes, e-invoices — 6 years
// Income Tax: All financial records, TDS/TCS certificates — 8 years
// Companies Act: Board minutes, financial statements — 8 years
// Consumer Protection: Booking records, communication — 3 years
//
// Audit requirements:
// Statutory audit: Required for all companies (Companies Act)
// Tax audit: Required if turnover > ₹1 crore (₹50 lakh for professions)
// GST audit: Required if turnover > ₹5 crore
// Internal audit: Required for companies with paid-up capital > ₹5 crore
//
// Audit preparation features:
// - Organized financial records by year and category
// - GST reconciliation (books vs. filed returns)
// - TDS/TCS reconciliation (collected vs. deposited)
// - Booking revenue reconciliation (invoices vs. payments)
// - Commission tracking (agent commissions as expense)
// - Expense categorization (travel, office, marketing, salaries)
// - Export all records in auditor-friendly format (Excel + PDF)
```

---

## Open Problems

1. **GST rate complexity** — Different GST rates for different service components within a tour package. Bundled vs. unbundled pricing affects GST liability. Need clear guidance.

2. **TCS threshold tracking** — Customer books overseas tours from multiple agencies. No single agency knows the customer's total overseas spend. Potential over/under-collection.

3. **e-Invoicing adoption** — e-Invoicing requires API integration with GST portal. GST portal APIs are not always reliable. Need fallback mechanisms.

4. **Composition scheme limitation** — Small agencies on composition scheme can't claim ITC, limiting growth. Regular scheme compliance burden is high for small agencies.

5. **Interstate vs. intrastate** — GST splits into CGST+SGST (intrastate) or IGST (interstate). Agent location vs. customer location vs. service location creates complexity.

---

## Next Steps

- [ ] Design GST calculation engine with rate matrix for all service types
- [ ] Build TCS tracking and collection system with PAN-based threshold monitoring
- [ ] Create automated GST filing with GSTR-1 and GSTR-3B generation
- [ ] Build audit preparation toolkit with reconciliation reports
- [ ] Study tax compliance platforms (ClearTax, Zoho Books, Tally, myBillBook)
