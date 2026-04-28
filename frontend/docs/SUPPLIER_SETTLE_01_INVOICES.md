# Supplier Invoice & Settlement — Invoice Processing

> Research document for supplier invoice receipt, matching, approval workflows, and invoice lifecycle management.

---

## Key Questions

1. **How do we receive and process supplier invoices?**
2. **What's the invoice-to-booking matching process?**
3. **What approval workflows govern invoice processing?**
4. **How do we handle invoice discrepancies and disputes?**
5. **What's the document management system for invoices?**

---

## Research Areas

### Invoice Receipt & Capture

```typescript
interface InvoiceProcessing {
  invoiceId: string;
  source: InvoiceSource;
  capture: InvoiceCapture;
  matching: InvoiceMatching;
  approval: InvoiceApproval;
  accounting: InvoiceAccounting;
}

type InvoiceSource =
  | 'email_attachment'                // Supplier emails invoice PDF
  | 'portal_upload'                   // Agent uploads from supplier portal
  | 'api_integration'                 // Automated from supplier API
  | 'whatsapp_document'               // Supplier sends via WhatsApp
  | 'physical_scan'                   // Paper invoice scanned
  | 'bsp_statement';                  // BSP billing statement

interface InvoiceCapture {
  method: CaptureMethod;
  extractedData: InvoiceData;
  confidence: number;
  requiresReview: boolean;
}

type CaptureMethod =
  | 'ocr_auto'                        // Automated OCR extraction
  | 'manual_entry'                    // Agent manually enters data
  | 'api_auto';                       // Structured data from API

interface InvoiceData {
  supplierName: string;
  supplierGSTIN: string;
  invoiceNumber: string;
  invoiceDate: Date;
  dueDate: Date;
  lineItems: InvoiceLineItem[];
  subtotal: Money;
  tax: TaxBreakdown;
  total: Money;
  paymentTerms: string;
  bookingReference?: string;
}

interface InvoiceLineItem {
  description: string;
  hsnCode?: string;
  quantity: number;
  unitPrice: Money;
  taxRate: number;
  taxAmount: Money;
  total: Money;
}

// Invoice processing pipeline:
// 1. Receipt: Invoice arrives (email, WhatsApp, upload, API)
// 2. OCR: Extract structured data from PDF/image
// 3. Validation: Check GSTIN format, HSN codes, tax calculations
// 4. Matching: Match to booking/trip in the system
// 5. Discrepancy check: Compare to quoted/agreed prices
// 6. Approval: Route to appropriate approver
// 7. Accounting: Create journal entries
// 8. Payment scheduling: Add to payment queue
// 9. Archive: Store in document vault
//
// OCR extraction for Indian invoices:
// Challenges:
// - Varied invoice formats across suppliers
// - Multi-language invoices (English + Hindi + regional)
// - Scanned quality varies (blurry, skewed, stamp marks)
// - GSTIN and HSN code extraction must be precise (for ITC)
//
// Key fields to extract with high accuracy:
// - Supplier GSTIN (15-character, regex: ^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$)
// - Invoice number (for GSTR-2 matching)
// - Tax amounts (CGST, SGST, IGST separately — needed for ITC claims)
// - HSN codes (for GSTR-1 reporting)
// - Total amount (for payment processing)
//
// OCR accuracy targets:
// GSTIN: 99%+ (regex validation helps)
// Invoice number: 95%+
// Tax amounts: 98%+ (cross-validated with totals)
// Line items: 90%+ (more complex, may need manual review)
```

### Invoice-to-Booking Matching

```typescript
interface InvoiceMatching {
  matchStrategy: MatchStrategy;
  matches: InvoiceMatch[];
  unmatched: UnmatchedInvoice[];
  discrepancies: InvoiceDiscrepancy[];
}

type MatchStrategy =
  | 'booking_reference'               // Invoice references booking ID
  | 'supplier_date_amount'            // Match by supplier + date range + amount
  | 'component_level'                 // Match individual line items to trip components
  | 'manual';                         // Agent manually matches

interface InvoiceMatch {
  invoiceId: string;
  bookingId: string;
  matchType: MatchType;
  matchConfidence: number;
  matchedBy: string;
  matchedAt: Date;
}

type MatchType =
  | 'exact'                           // Booking reference matches, amount matches
  | 'close'                           // Amount within 5% tolerance
  | 'partial'                         // Invoice covers part of booking
  | 'aggregated';                     // One invoice covers multiple bookings

// Matching scenarios:
//
// 1. Direct match (ideal):
//    Invoice: "Booking TRV-45678, Kerala tour, Hotel Trident, 3 nights"
//    System: Found booking TRV-45678, Hotel component ₹18,000
//    Invoice amount: ₹18,000 → Match: Exact ✅
//
// 2. Amount discrepancy:
//    Invoice: ₹19,500 (₹18,000 + ₹1,500 seasonal surcharge)
//    Expected: ₹18,000
//    Discrepancy: ₹1,500 (+8.3%)
//    Action: Flag for agent review → Agent confirms seasonal surcharge
//
// 3. Partial invoice:
//    Booking: ₹55,000 total (Hotel + Flight + Transport + Activities)
//    Invoice: ₹18,000 (Hotel only)
//    Expected: More invoices to come for other components
//    Action: Partial match, await remaining invoices
//
// 4. Aggregated invoice:
//    Tour operator sends one invoice for 5 bookings in March
//    Total: ₹4,50,000
//    Individual bookings: ₹85K + ₹92K + ₹78K + ₹95K + ₹100K
//    Action: Match each booking, create aggregated payment
//
// 5. No match:
//    Invoice received with no clear booking reference
//    Possible: Supplier sent wrong invoice, or booking not in system
//    Action: Flag for manual matching, alert agent

interface InvoiceDiscrepancy {
  invoiceId: string;
  bookingId?: string;
  type: DiscrepancyType;
  expectedAmount: Money;
  actualAmount: Money;
  difference: Money;
  resolution: DiscrepancyResolution;
}

type DiscrepancyType =
  | 'price_increase'                  // Supplier charged more than quoted
  | 'extra_charge'                    // Additional charges not in quote
  | 'tax_difference'                  // GST calculation differs
  | 'wrong_booking'                   // Invoice for wrong booking
  | 'duplicate_invoice'               // Same invoice received twice
  | 'currency_difference';            // Exchange rate differs from booking

// Discrepancy resolution:
// Price increase (>5%): Agent contacts supplier → Negotiate or accept
// Extra charge: Agent verifies if charge is valid → Approve or reject
// Tax difference: Auto-reconcile (GST calculation rules)
// Wrong booking: Return to supplier, request correct invoice
// Duplicate: Detect and flag (same invoice number + supplier + amount)
// Currency difference: Accept card rate, book exchange gain/loss
```

### Invoice Approval Workflow

```typescript
interface InvoiceApproval {
  workflow: ApprovalWorkflow;
  rules: ApprovalRule[];
  delegation: ApprovalDelegation;
  audit: ApprovalAudit;
}

interface ApprovalWorkflow {
  steps: ApprovalStep[];
  autoApprove: AutoApproveConfig;
  escalation: EscalationConfig;
}

interface ApprovalStep {
  step: number;
  approver: string;                   // Role: 'agent', 'admin', 'owner', 'accountant'
  conditions: ApprovalCondition[];
  timeLimit: string;                  // "24 hours"
}

// Invoice approval matrix:
//
// Auto-approve (no human needed):
// - Invoice amount matches booking exactly (within ₹100 tolerance)
// - GSTIN and tax amounts validated
// - Invoice from pre-approved supplier
// - Amount < ₹10,000
//
// Agent approval:
// - Invoice matched to booking, amount within 5% tolerance
// - Amount ₹10,000-25,000
// - Time limit: 24 hours
//
// Admin approval:
// - Amount ₹25,000-1,00,000
// - Or: Discrepancy between 5-15%
// - Or: New supplier (first invoice)
// - Time limit: 48 hours
//
// Owner approval:
// - Amount > ₹1,00,000
// - Or: Discrepancy > 15%
// - Or: Disputed invoice
// - Time limit: 72 hours
//
// Escalation:
// If not approved within time limit:
// - Step 1: Remind approver (WhatsApp + email)
// - Step 2: Escalate to next level
// - Step 3: Auto-approve if no response within 2x time limit
//          (configurable, default: off)

// Approval audit trail:
// Every approval/rejection logged with:
// - Who approved/rejected
// - When
// - Original invoice amount vs. approved amount
// - Any conditions or notes
// - Changes made (e.g., corrected amount)
```

---

## Open Problems

1. **Invoice format chaos** — Every supplier has a different invoice format. No standardization in Indian travel industry. OCR must handle 50+ distinct formats.

2. **GST reconciliation complexity** — Supplier's GSTR-1 must match agency's GSTR-2A for ITC claim. If supplier hasn't filed, agency can't claim ITC. Need to track supplier filing status.

3. **Timeliness** — Suppliers often send invoices late (weeks after service). Can't wait for invoices to process payments. Need accrual-based processing with invoice-backing later.

4. **Paper invoices** — Many Indian suppliers still issue paper invoices. Scanning and OCR adds friction and error risk.

5. **Multi-invoice bookings** — A single trip generates 5-10 supplier invoices (hotel, airline, transport, activities, insurance, meals). Tracking all invoices for one booking is complex.

---

## Next Steps

- [ ] Build invoice receipt pipeline with OCR extraction
- [ ] Create invoice-to-booking matching engine with tolerance rules
- [ ] Design approval workflow with role-based matrix
- [ ] Build discrepancy detection and resolution workflow
- [ ] Study invoice processing platforms (Rippling, Bill.com, India-specific: Clear, myBillBook)
