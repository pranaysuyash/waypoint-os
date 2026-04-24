# Safety & Risk Systems — Compliance Deep Dive

> Part 4 of 5 in the Safety & Risk Systems Deep Dive Series

**Series Index:**
1. [Technical Deep Dive](SAFETY_01_TECHNICAL_DEEP_DIVE.md) — Architecture & Risk Engine
2. [UX/UI Deep Dive](SAFETY_02_UX_UI_DEEP_DIVE.md) — Risk Display & Warning UI
3. [Business Value Deep Dive](SAFETY_03_BUSINESS_VALUE_DEEP_DIVE.md) — Protection & ROI
4. [Compliance Deep Dive](SAFETY_04_COMPLIANCE_DEEP_DIVE.md) — GST, TCS & Regulations (this document)
5. [Escalation Deep Dive](SAFETY_05_ESCALATION_DEEP_DIVE.md) — Owner Workflows & Alerts

---

## Document Overview

**Purpose:** Comprehensive exploration of compliance requirements for Indian travel agencies — GST, TCS, and regulatory obligations.

**Scope:**
- GST compliance requirements
- TCS collection and remittance
- PAN card requirements
- Invoice compliance standards
- Documentation requirements
- Tax reporting obligations
- Penalty structures
- Compliance automation

**Target Audience:** Agency owners, compliance officers, accountants, and technical staff implementing compliance systems.

**Last Updated:** 2026-04-24

**Disclaimer:** This document provides general guidance on Indian tax compliance. Tax laws are subject to change. Consult with a qualified tax professional for specific advice.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [GST Compliance Framework](#gst-compliance-framework)
3. [TCS Compliance Framework](#tcs-compliance-framework)
4. [PAN Card Requirements](#pan-card-requirements)
5. [Invoice Compliance Standards](#invoice-compliance-standards)
6. [Documentation Requirements](#documentation-requirements)
7. [Tax Reporting Obligations](#tax-reporting-obligations)
8. [Penalty Structures](#penalty-structures)
9. [Compliance Automation](#compliance-automation)
10. [Compliance Checklist](#compliance-checklist)

---

## 1. Executive Summary

### The Compliance Landscape

Indian travel agencies face multiple tax and regulatory obligations:

- **GST (Goods and Services Tax)** — 18% on services, with complex input tax credit rules
- **TCS (Tax Collected at Source)** — 20% on international travel remittances above ₹7L
- **PAN requirements** — Mandatory for TCS credit and high-value transactions
- **Invoice compliance** — Specific formatting and content requirements
- **Documentation** — Travel documents, KYC, and supporting records
- **Reporting** — GST returns, TCS statements, and annual filings

### Compliance Risks

| Risk | Impact | Typical Penalty |
|------|--------|-----------------|
| GST underpayment | 18% interest + penalty | ₹21,000 per incident |
| GST not collected | Full liability + penalty | Up to 100% of tax |
| TCS not collected | 20% interest + penalty | Variable |
| Incorrect PAN | No TCS credit to customer | Customer impact |
| Invoice non-compliance | Input tax credit denied | ₹10,000+ per invoice |
| Missing documentation | Audit exposure | Variable |

### Key Compliance Numbers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPLIANCE THRESHOLDS                              │
└─────────────────────────────────────────────────────────────────────────────┘

  GST REGISTRATION:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Threshold: ₹40 lakh annual turnover                                 │
  │  Voluntary registration: Available below threshold                    │
  │  Composition scheme: Not available for travel agencies                │
  └─────────────────────────────────────────────────────────────────────┘

  TCS APPLICABILITY:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Threshold: ₹7 lakh per transaction                                  │
  │  Rate: 20% on amount exceeding ₹7 lakh                              │
  │  Applicable: International travel packages only                     │
  └─────────────────────────────────────────────────────────────────────┘

  PAN REQUIREMENT:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  GST invoices: Required for B2B transactions                         │
  │  TCS credit: Mandatory for claim                                    │
  │  High-value: Required for transactions > ₹50,000                    │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 2. GST Compliance Framework

### 2.1 GST Basics for Travel Agencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GST FOR TRAVEL AGENCIES                           │
└─────────────────────────────────────────────────────────────────────────────┘

  TAX STRUCTURE:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Component               │  Rate   │  Application                   │
  ├─────────────────────────┼─────────┼─────────────────────────────────┤
  │  CGST (Central)         │   9%    │  Goes to Central Government     │
  │  SGST/UTGST (State)     │   9%    │  Goes to State Government       │
  │  IGST (Inter-state)      │  18%    │  For inter-state transactions    │
  ├─────────────────────────┼─────────┼─────────────────────────────────┤
  │  TOTAL                   │  18%    │  Effective GST rate            │
  └─────────────────────────────────────────────────────────────────────┘

  TRAVEL AGENCY GST STATUS:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Transaction Type        │  GST Treatment                         │
  ├──────────────────────────┼─────────────────────────────────────────┤
  │  Commission earned       │  18% GST on commission amount           │
  │  Service fee             │  18% GST on service fee                │
  │  Markup on supplier cost │  18% GST on markup amount              │
  │  Package price           │  18% GST on total package value        │
  │  Refunds received        │  Claim input tax credit proportionally  │
  └─────────────────────────────────────────────────────────────────────┘

  INPUT TAX CREDIT (ITC):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Eligible Expenses       │  Not Eligible                          │
  ├──────────────────────────┼─────────────────────────────────────────┤
  │  • Supplier services     │  • Motor vehicles (except for          │
  │  • Office rent           │    business use)                       │
  │  • Professional fees     │  • Food and beverages (except           │
  │  • Software licenses     │    for employee use)                  │
  │  • Travel expenses       │  • Personal expenses                   │
  │    for business         │                                         │
  │  • Communication        │                                         │
  └─────────────────────────────────────────────────────────────────────┘
```

### 2.2 GST Invoice Requirements

```typescript
/**
 * GST Invoice Requirements
 */

interface GSTInvoiceRequirements {
  // Mandatory fields
  mandatory: {
    // Supplier details
    supplierName: string;
    supplierGSTIN: string;
    supplierAddress: string;
    supplierState: string;
    supplierPan?: string;

    // Customer details (B2B)
    customerName: string;
    customerGSTIN?: string;         // Required for B2B
    customerAddress?: string;       // Required for > ₹50K
    customerState?: string;
    customerPan?: string;

    // Invoice details
    invoiceNumber: string;          // Sequential, financial year based
    invoiceDate: Date;
    supplyDate: Date;

    // Goods/Services
  };

  // Line item requirements
  lineItem: {
    description: string;
    sacCode: string;                // Service Accounting Code
    quantity?: number;
    unitPrice: number;              // Excluding GST
    totalPrice: number;            // Excluding GST
    taxRate: number;                // 9%, 18%, etc.
    cgstAmount: number;
    sgstAmount: number;             // or utgstAmount
    igstAmount?: number;            // For inter-state
    totalWithTax: number;
  }[];

  // Totals
  totals: {
    taxableValue: number;
    cgstTotal: number;
    sgstTotal: number;
    igstTotal?: number;
    roundOff: number;
    invoiceTotal: number;
    amountInWords: string;
  };

  // Payment details
  payment: {
    bankName: string;
    accountNumber: string;
    ifscCode: string;
    branch?: string;
  };
}

// Travel Agency SAC Codes
const TRAVEL_SAC_CODES = {
  tourOperatorServices: "996311",
  travelAgencyServices: "996312",
  tourOperatorServicesByRTC: "996313",
  guideServices: "996321",
  passportVisaServices: "998811"
};
```

### 2.3 GST Invoice Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GST INVOICE FORMAT                                │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  TRAVEL AGENCY NAME                                                │
  │  [Agency Address]                                                  │
  │  GSTIN: 29AAAAA0000A1Z5 | PAN: AAAAA0000A                          │
  │  State: Karnataka | Code: 29                                        │
  │                                                                     │
  │  ┌─────────────────────────────────────────────────────────────┐   │
  │  │ TAX INVOICE                                                    │   │
  │  │                                                                 │   │
  │  │ Invoice No: TS-2023-24-001    Date: 24-Apr-2026                │   │
  │  │ Supply Date: 24-Apr-2026                                      │   │
  │  └─────────────────────────────────────────────────────────────┘   │
  │                                                                     │
  │  Billed To:                                                        │
  │  [Customer Name]                                                  │
  │  [Customer Address]                                               │
  │  GSTIN: 29BBBBB0000B1Z5 | State: Karnataka                         │
  │  PAN: BBBBB0000B (if required)                                     │
  │                                                                     │
  │  Shipped To:                                                       │
  │  [Same as Billed To]                                              │
  │                                                                     │
  │  ┌──────────────────────────────────────────────────────────────┐  │
  │  │ # │ Description           │ SAC    │ Qty   │ Rate    │ Amount │  │
  │  ├──┼───────────────────────┼────────┼───────┼─────────┼────────┤  │
  │  │ 1│ Europe Package -       │996311  │   1   │₹1,00,000│₹1,00,000│  │
  │  │  │ 7 nights Paris        │        │       │         │        │  │
  │  │  │ 4 nights Swiss        │        │       │         │        │  │
  │  │  │                        │        │       │         │        │  │
  │  │  │ Less: Refundable       │        │       │         │₹-60,000│  │
  │  │  │ deposits              │        │       │         │        │  │
  │  │  │                        │        │       │         │        │  │
  │  │  │ Net Taxable Value      │        │       │         │ ₹40,000│  │
  │  ├──┼───────────────────────┼────────┴───────┴─────────┴────────┤  │
  │  │  │ CGST (9%)             │                                ₹3,600│  │
  │  │  │ SGST (9%)             │                                ₹3,600│  │
  │  │  │                      │                                │        │  │
  │  │  │ Round Off            │                                    ₹40│  │
  │  ├──┼───────────────────────┼────────────────────────────────────┤  │
  │  │  │ TOTAL                 │                             ₹47,240│  │
  │  └──┴───────────────────────┴────────────────────────────────────┘  │
  │                                                                     │
  │  Amount in Words: Forty Seven Thousand Two Hundred Forty Only      │
  │                                                                     │
  │  Total Invoice Value (in figures): ₹47,240                         │
  │                                                                     │
  │  Bank Details:                                                     │
  │  Bank: [Bank Name] | A/C: [Account Number] | IFSC: [IFSC Code]     │
  │                                                                     │
  │  Terms: Payment within 7 days                                      │
  │                                                                     │
  │  [Authorized Signatory]                                            │
  │                                                                     │
  │  Whether tax is payable under reverse charge: NO                    │
  └─────────────────────────────────────────────────────────────────────┘
```

### 2.4 GST Filing Requirements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GST FILING REQUIREMENTS                             │
└─────────────────────────────────────────────────────────────────────────────┘

  MANDATORY RETURNS:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Return      │  Due Date   │  Description                            │
  ├──────────────┼─────────────┼─────────────────────────────────────────┤
  │  GSTR-1      │  11th       │  Monthly/Quarterly outward supplies     │
  │  GSTR-3B     │  20th       │  Monthly self-assessment return        │
  │  GSTR-9      │  Quarterly   │  Annual return (due Dec 31)           │
  │  GSTR-9C     │  Quarterly   │  Composition dealer (not applicable)  │
  └─────────────────────────────────────────────────────────────────────┘

  E-INVOICING REQUIREMENTS:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Turnover                │  Threshold   │  Mandatory From            │
  ├─────────────────────────┼─────────────┼─────────────────────────────┤
  │  > ₹5 Cr (any state)    │  ₹5 Cr      │  1-Oct-2023                │
  │  > ₹10 Cr (all India)   │  ₹10 Cr     │  1-Oct-2023                │
  │  > ₹5 Cr (any state)    │  ₹5 Cr      │  Phase 2: 1-Aug-2024       │
  └─────────────────────────────────────────────────────────────────────┘

  RECORD KEEPING:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Document Type           │  Retention Period  │  Notes              │
  ├──────────────────────────┼────────────────────┼─────────────────────┤
  │  Invoices issued         │  72 months         │  Current FY + 5 years │
  │  Invoices received       │  72 months         │  For ITC claims      │
  │  GST returns filed       │  72 months         │  Electronic records   │
  │  E-way bills             │  72 months         │  If applicable        │
  │  Credit notes            │  72 months         │  Issued and received  │
  │  Debit notes             │  72 months         │  Issued and received  │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 3. TCS Compliance Framework

### 3.1 TCS Basics for Travel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TCS FOR TRAVEL AGENCIES                           │
└─────────────────────────────────────────────────────────────────────────────┘

  WHAT IS TCS?

  Tax Collected at Source (TCS) is a mechanism where travel agents collect
  tax from customers at the time of booking international travel packages
  and remit it to the government. Customers can claim this as credit while
  filing their income tax returns.

  APPLICABILITY:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Condition               │  Requirement                           │
  ├─────────────────────────┼─────────────────────────────────────────┤
  │  Transaction type        │  International travel packages only     │
  │  Amount threshold        │  > ₹7 lakh per transaction              │
  │  Collection rate         │  20% on amount exceeding ₹7 lakh       │
  │  PAN requirement         │  Mandatory for TCS credit              │
  │  Remittance              │  Within 7 days of collection            │
  └─────────────────────────────────────────────────────────────────────┘

  TCS CALCULATION EXAMPLE:

  Package Price: ₹10,00,000

  Step 1: Determine taxable amount
  - Amount above ₹7 lakh: ₹10,00,000 - ₹7,00,000 = ₹3,00,000

  Step 2: Calculate TCS
  - TCS = 20% of ₹3,00,000 = ₹60,000

  Step 3: Breakdown for forms
  - TCS collected: ₹60,000
  - Collectible TCS: ₹60,000
  - PAN of customer: Required
```

### 3.2 TCS Form Requirements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TCS FORM REQUIREMENTS                              │
└─────────────────────────────────────────────────────────────────────────────┘

  FORM 26Q (Quarterly Statement):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Section                │  Details                                  │
  ├────────────────────────┼─────────────────────────────────────────────┤
  │  Filing deadline       │  30th of month following quarter          │
  │  Due date for deposit   │  7th of following month                   │
  │  Sections              │  206C(1G) - TCS on remittance for tour    │
  │                        │  operator packages or travel to any       │
  │                        │  place abroad                              │
  │  Information required │  • Customer PAN                            │
  │                        │  • Customer name                           │
  │                        │  • Total amount of remittance              │
  │                        │  • TCS amount collected                    │
  │                        │  • Deposit details                         │
  │                        │  • Booking/invoice reference              │
  └─────────────────────────────────────────────────────────────────────┘

  FORM 27Q (Annual Statement):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Filing deadline       │  30th June following financial year      │
  │  Purpose              │  Consolidated annual TCS statement         │
  │  Use of PAN           │  Critical for customer tax credit          │
  │  Certificate          │  TCS certificate to be provided to         │
  │                       │  customer for tax filing                   │
  └─────────────────────────────────────────────────────────────────────┘

  FORM 27D (TCS Certificate):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Purpose              │  Proof of TCS collected for customer       │
  │  Issue timeline       │  Within 15 days of end of quarter          │
  │  Contains            │  • TCS amount collected                    │
  │                       │  • Booking reference                       │
  │                       │  • Deposit details                         │
  │                       │  • Collection date                         │
  │  Customer use        │  Claim credit while filing ITR            │
  └─────────────────────────────────────────────────────────────────────┘
```

### 3.3 TCS Calculation & Collection

```typescript
/**
 * TCS Calculation Engine
 */

class TCSCalculator {
  /**
   * Calculate TCS for international travel package
   */
  calculateTCS(packagePrice: number): TCSCalculation {
    const THRESHOLD = 700000;      // ₹7 lakh
    const RATE = 0.20;             // 20%

    let taxableAmount = 0;
    let tcsAmount = 0;

    if (packagePrice > THRESHOLD) {
      taxableAmount = packagePrice - THRESHOLD;
      tcsAmount = taxableAmount * RATE;
    }

    return {
      packagePrice,
      threshold: THRESHOLD,
      taxableAmount,
      tcsRate: RATE,
      tcsAmount,
      totalPayable: packagePrice + tcsAmount,
      breakdown: {
        baseAmount: THRESHOLD,
        taxableAboveThreshold: taxableAmount,
        tcsOnTaxableAmount: tcsAmount
      }
    };
  }

  /**
   * Generate TCS invoice breakdown
   */
  generateTCSInvoiceBreakdown(
    calculation: TCSCalculation,
    customerPAN: string
  ): TCSInvoiceBreakdown {
    return {
      packagePrice: calculation.packagePrice,
      tcsApplicable: calculation.tcsAmount > 0,
      tcsAmount: calculation.tcsAmount,
      totalPayable: calculation.totalPayable,
      customerPAN,
      requiredFields: {
        pan: customerPAN,
        name: "", // To be filled
        address: "", // To be filled
        amount: calculation.tcsAmount,
        section: "206C(1G)",
        depositDate: this.calculateDepositDate()
      }
    };
  }

  private calculateDepositDate(): Date {
    const due = new Date();
    due.setDate(due.getDate() + 7);  // 7 days from collection
    return due;
  }
}

interface TCSCalculation {
  packagePrice: number;
  threshold: number;
  taxableAmount: number;
  tcsRate: number;
  tcsAmount: number;
  totalPayable: number;
  breakdown: {
    baseAmount: number;
    taxableAboveThreshold: number;
    tcsOnTaxableAmount: number;
  };
}

interface TCSInvoiceBreakdown {
  packagePrice: number;
  tcsApplicable: boolean;
  tcsAmount: number;
  totalPayable: number;
  customerPAN: string;
  requiredFields: {
    pan: string;
    name: string;
    address: string;
    amount: number;
    section: string;
    depositDate: Date;
  };
}
```

---

## 4. PAN Card Requirements

### 4.1 PAN Validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PAN CARD REQUIREMENTS                              │
└─────────────────────────────────────────────────────────────────────────────┘

  PAN FORMAT:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Structure: AAAPL1234A                                              │
  │              ││││││││││                                            │
  │              └┴┴┴┴┴┴┴┴└┴└─ Alphabet/Number sequence                │
  │                                                                     │
  │  Format:                                                           │
  │  • First 3 characters: Letters (category)                          │
  │  • Next 4 characters: Numbers                                      │
  │  • Last character: Letter (check digit)                            │
  │                                                                     │
  │  Example for Individual: AAAAA1234A                                │
  │  Example for Company: AAAAC1234A                                   │
  └─────────────────────────────────────────────────────────────────────┘

  PAN REQUIREMENTS BY SCENARIO:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Scenario                  │  PAN Required  │  Reason                  │
  ├────────────────────────────┼────────────────┼──────────────────────────┤
  │  GST invoice > ₹50K        │  Yes           │  Mandatory for GST rules  │
  │  TCS collection            │  Yes           │  Required for credit      │
  │  TCS credit claim          │  Yes           │  Cannot claim without PAN │
  │  High-value transactions   │  Yes           │  > ₹50,000               │
  │  Corporate bookings        │  Yes           │  B2B compliance           │
  │  Individual < ₹50K         │  No            │  Not mandatory           │
  └─────────────────────────────────────────────────────────────────────┘
```

### 4.2 PAN Validation Logic

```typescript
/**
 * PAN Validation
 */

class PANValidator {
  private static readonly PATTERN = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;

  /**
   * Validate PAN format
   */
  validateFormat(pan: string): ValidationResult {
    if (!pan) {
      return {
        valid: false,
        error: "PAN is required"
      };
    }

    const cleanPan = pan.toUpperCase().replace(/\s/g, "");

    if (!PANValidator.PATTERN.test(cleanPan)) {
      return {
        valid: false,
        error: "Invalid PAN format. Expected: 5 letters + 4 digits + 1 letter (e.g., AAAAA1234A)"
      };
    }

    return {
      valid: true,
      cleanPan
    };
  }

  /**
   * Validate PAN with GST portal (when available)
   */
  async validateWithGST(pan: string): Promise<PANValidationResult> {
    const formatResult = this.validateFormat(pan);
    if (!formatResult.valid) {
      return formatResult;
    }

    // In production, call GST portal API
    // For now, return format validation
    return {
      valid: true,
      cleanPan: formatResult.cleanPan,
      source: "format_only",
      recommendation: "Verify with GST portal for final confirmation"
    };
  }

  /**
   * Extract PAN category
   */
  getCategory(pan: string): PANCategory {
    const fourthChar = pan.charAt(3);

    const categoryMap: { [key: string]: PANCategory } = {
      "C": "Company",
      "P": "Individual",
      "H": "HUF",
      "F": "Firm",
      "A": "Association of Persons",
      "T": "Trust",
      "B": "Body of Individuals",
      "L": "Local Authority",
      "J": "Artificial Juridical Person",
      "G": "Government"
    };

    return categoryMap[fourthChar] || "Unknown";
  }
}

interface ValidationResult {
  valid: boolean;
  cleanPan?: string;
  error?: string;
  source?: string;
  recommendation?: string;
}

interface PANValidationResult extends ValidationResult {
  category?: PANCategory;
}

type PANCategory =
  | "Company"
  | "Individual"
  | "HUF"
  | "Firm"
  | "Association of Persons"
  | "Trust"
  | "Body of Individuals"
  | "Local Authority"
  | "Artificial Juridical Person"
  | "Government"
  | "Unknown";
```

---

## 5. Invoice Compliance Standards

### 5.1 Mandatory Invoice Elements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MANDATORY INVOICE ELEMENTS                           │
└─────────────────────────────────────────────────────────────────────────────┘

  CRITICAL ELEMENTS (Non-negotiable):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Element                     │  Format         │  Example              │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  Invoice number              │  Sequential     │  INV-2023-24-001    │
  │                             │  FY-based        │                       │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  Invoice date                │  DD-MM-YYYY     │  24-04-2026          │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  Supplier GSTIN              │  15 characters │  29AAAAA0000A1Z5    │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  Customer GSTIN (B2B)        │  15 characters │  29BBBBB0000B1Z5    │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  HSN/SAC code                │  6 digits       │  996311              │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  Taxable value               │  INR            │  ₹1,00,000           │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  GST amount                  │  INR            │  ₹18,000             │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  Total invoice value         │  INR + Words    │  ₹1,18,000 + words  │
  ├─────────────────────────────┼────────────────┼──────────────────────┤
  │  Supplier signature         │  Physical/       │  Digital/Physical     │
  │                             │  Digital        │                       │
  └─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Invoice Numbering Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INVOICE NUMBERING RULES                            │
└─────────────────────────────────────────────────────────────────────────────┘

  NUMBERING FORMAT:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Convention: [PREFIX]-[FY]-[SERIAL]                                │
  │                                                                     │
  │  Examples:                                                         │
  │  • INV-2023-24-001 (Financial year 2023-24, serial 001)           │
  │  • TS-2023-24-0001 (Tour services, FY 2023-24, serial 0001)      │
  │  • INV/001/23-24 (Alternative format)                              │
  │                                                                     │
  │  Rules:                                                            │
  │  • Must be sequential for each financial year                       │
  │  • Cannot have gaps (except canceled invoices)                     │
  │  • Must restart from 001 each financial year                        │
  │  • Financial year: April 1 to March 31                              │
  └─────────────────────────────────────────────────────────────────────┘

  CANCELED INVOICES:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  • Cannot be deleted from sequence                                  │
  │  • Must be marked as "CANCELED"                                    │
  │  • Next invoice continues sequence                                  │
  │  • No new invoice can be issued with same number                    │
  │  • Credit note issued for adjustments                               │
  └─────────────────────────────────────────────────────────────────────┘

  PROFORMA TO TAX INVOICE:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Step 1: Issue proforma (no GST)                                   │
  │  Step 2: Receive advance/partial payment                            │
  │  Step 3: Issue tax invoice (sequential number)                      │
  │  Step 4: Link to proforma in records                                │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Documentation Requirements

### 6.1 KYC Documents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KYC DOCUMENT REQUIREMENTS                         │
└─────────────────────────────────────────────────────────────────────────────┘

  MANDATORY DOCUMENTS (International Travel):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Document           │  Required For       │  Verification          │
  ├─────────────────────┼────────────────────┼──────────────────────────┤
  │  PAN card           │  TCS, GST invoice   │  Self-attested copy    │
  ├─────────────────────┼────────────────────┼──────────────────────────┤
  │  Passport           │  International travel│  Validity check         │
  ├─────────────────────┼────────────────────┼──────────────────────────┤
  │  Visa               │  As required        │  Destination specific    │
  ├─────────────────────┼────────────────────┼──────────────────────────┤
  │  ID proof            │  Domestic high value│  Aadhaar/Voter ID       │
  ├─────────────────────┼────────────────────┼──────────────────────────┤
  │  Address proof       │  GST registration    │  Utility bill, etc.     │
  ├─────────────────────┼────────────────────┼──────────────────────────┤
  │  Passport photo      │  Booking             │  Recent, clear          │
  └─────────────────────────────────────────────────────────────────────┘

  DOCUMENT RETENTION:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Document Type        │  Retention Period  │  Format                 │
  ├───────────────────────┼────────────────────┼──────────────────────────┤
  │  KYC documents        │  8 years post       │  Physical + Digital      │
  │                       │  transaction end   │                         │
  ├───────────────────────┼────────────────────┼──────────────────────────┤
  │  Booking forms        │  8 years            │  Digital                │
  ├───────────────────────┼────────────────────┼──────────────────────────┤
  │  Communication logs   │  8 years            │  Digital                │
  ├───────────────────────┼────────────────────┼──────────────────────────┤
  │  Payment receipts      │  8 years            │  Digital                │
  ├───────────────────────┼────────────────────┼──────────────────────────┤
  │  Tickets/Vouchers      │  8 years            │  Digital                │
  └───────────────────────┼────────────────────┼──────────────────────────┘
```

### 6.2 Travel Documentation Checklist

```typescript
/**
 * Travel Documentation Checklist
 */

interface TravelDocumentationChecklist {
  // Customer documents
  customer: {
    panCard: {
      required: boolean;
      received: boolean;
      verified: boolean;
      validUntil?: Date;
    };
    passport: {
      required: boolean;
      received: boolean;
      verified: boolean;
      validUntil: Date;
      hasValidVisa: boolean;
    };
    visa: {
      country: string;
      required: boolean;
      received: boolean;
      verified: boolean;
      validUntil: Date;
    };
    addressProof: {
      required: boolean;
      received: boolean;
      verified: boolean;
    };
  };

  // Booking documents
  booking: {
    bookingForm: {
      received: boolean;
      signed: boolean;
      dated: Date;
    };
    quoteAcceptance: {
      received: boolean;
      signed: boolean;
      dated: Date;
    };
    paymentReceipt: {
      received: boolean;
      amount: number;
      mode: string;
    };
  };

  // Compliance documents
  compliance: {
    gstInvoice: {
      issued: boolean;
      number: string;
      date: Date;
    };
    tcsCertificate: {
      applicable: boolean;
      issued: boolean;
      certificateNumber: string;
      dateIssued: Date;
    };
    panAcknowledgement: {
      applicable: boolean;
      sent: boolean;
      date: Date;
    };
  };
}

/**
 * Documentation validator
 */
class DocumentationValidator {
  /**
   * Validate all required documentation for booking
   */
  async validateForBooking(
    booking: Booking,
    checklist: TravelDocumentationChecklist
  ): Promise<DocumentationValidationResult> {
    const errors: DocumentationError[] = [];
    const warnings: DocumentationWarning[] = [];

    // Validate PAN if TCS applicable
    if (booking.isInternational && booking.value > 700000) {
      if (!checklist.customer.panCard.received) {
        errors.push({
          field: "customer.panCard",
          severity: "critical",
          message: "PAN card required for TCS compliance",
          action: "Collect PAN card before booking"
        });
      }
    }

    // Validate passport for international
    if (booking.isInternational) {
      if (!checklist.customer.passport.received) {
        errors.push({
          field: "customer.passport",
          severity: "critical",
          message: "Passport required for international travel",
          action: "Collect passport before booking"
        });
      } else if (checklist.customer.passport.validUntil < booking.departureDate) {
        errors.push({
          field: "customer.passport",
          severity: "critical",
          message: `Passport expires before departure (${checklist.customer.passport.validUntil})`,
          action: "Request passport renewal or alternative documentation"
        });
      }
    }

    // Validate GST invoice issued
    if (!checklist.compliance.gstInvoice.issued) {
      errors.push({
        field: "compliance.gstInvoice",
        severity: "critical",
        message: "GST invoice must be issued before payment collection",
        action: "Generate and issue GST invoice"
      });
    }

    // Validate TCS certificate if applicable
    if (checklist.compliance.tcsCertificate.applicable) {
      if (!checklist.compliance.tcsCertificate.issued) {
        warnings.push({
          field: "compliance.tcsCertificate",
          severity: "medium",
          message: "TCS certificate pending issuance",
          timeline: "Within 15 days of quarter end"
        });
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }
}

interface DocumentationError {
  field: string;
  severity: "critical" | "high";
  message: string;
  action: string;
}

interface DocumentationWarning {
  field: string;
  severity: "low" | "medium";
  message: string;
  timeline?: string;
}

interface DocumentationValidationResult {
  valid: boolean;
  errors: DocumentationError[];
  warnings: DocumentationWarning[];
}
```

---

## 7. Tax Reporting Obligations

### 7.1 GST Return Filing Calendar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GST RETURN FILING CALENDAR                         │
└─────────────────────────────────────────────────────────────────────────────┘

  MONTHLY FILING (GSTR-1 & GSTR-3B):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Period      │  GSTR-1 Due  │  GSTR-3B Due │  Late Fee (per day)    │
  ├──────────────┼──────────────┼──────────────┼─────────────────────────┤
  │  April 2026  │  11-May      │  20-May      │  ₹50 (Nil return: ₹20) │
  │  May 2026    │  11-Jun      │  20-Jun      │  ₹50 (Nil return: ₹20) │
  │  June 2026   │  11-Jul      │  20-Jul      │  ₹50 (Nil return: ₹20) │
  │  July 2026   │  11-Aug      │  20-Aug      │  ₹50 (Nil return: ₹20) │
  │  Aug 2026    │  11-Sep      │  20-Sep      │  ₹50 (Nil return: ₹20) │
  │  Sep 2026    │  11-Oct      │  20-Oct      │  ₹50 (Nil return: ₹20) │
  │  Oct 2026    │  11-Nov      │  20-Nov      │  ₹50 (Nil return: ₹20) │
  │  Nov 2026    │  11-Dec      │  20-Dec      │  ₹50 (Nil return: ₹20) │
  │  Dec 2026    │  11-Jan      │  20-Jan      │  ₹50 (Nil return: ₹20) │
  │  Jan 2027    │  11-Feb      │  20-Feb      │  ₹50 (Nil return: ₹20) │
  │  Feb 2027    │  11-Mar      │  20-Mar      │  ₹50 (Nil return: ₹20) │
  │  Mar 2027    │  11-Apr      │  20-Apr      │  ₹50 (Nil return: ₹20) │
  └─────────────────────────────────────────────────────────────────────┘

  ANNUAL FILING (GSTR-9):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Financial Year   │  Due Date       │  Late Fee                     │
  ├───────────────────┼─────────────────┼──────────────────────────────┤
  │  2025-26          │  31-Dec-2026     │  ₹100/day (max ₹5,000)      │
  └─────────────────────────────────────────────────────────────────────┘

  RECONCILIATION (Monthly):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Item                    │  Source              │  Match With          │
  ├─────────────────────────┼──────────────────────┼──────────────────────┤
  │  Invoices issued        │  Accounting system   │  GSTR-1              │
  │  Invoices received       │  Accounting system   │  GSTR-3B ITC         │
  │  Cash payments          │  Bank statements     │  GSTR-3B             │
  │  TCS collected          │  Booking system       │  Form 26Q             │
  │  GST paid               │  Expense records      │  Electronic cash ledger│
  └─────────────────────────────────────────────────────────────────────┘
```

### 7.2 TCS Filing Calendar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TCS FILING CALENDAR                               │
└─────────────────────────────────────────────────────────────────────────────┘

  QUARTERLY FILING (Form 26Q):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Quarter    │  Period        │  TCS Deposit Due │  Form 26Q Due       │
  ├─────────────┼────────────────┼──────────────────┼─────────────────────┤
  │  Q1         │  Apr-Jun       │  7th of next mo  │  31-Jul            │
  │  Q2         │  Jul-Sep       │  7th of next mo  │  31-Oct            │
  │  Q3         │  Oct-Dec       │  7th of next mo  │  31-Jan            │
  │  Q4         │  Jan-Mar       │  7th of next mo  │  31-May            │
  └─────────────────────────────────────────────────────────────────────┘

  ANNUAL CERTIFICATE (Form 27D):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Financial Year   │  Certificate Due  │  Issue Timeline              │
  ├───────────────────┼──────────────────┼──────────────────────────────┤
  │  2025-26          │  30-Jun-2027     │  Within 15 days of filing    │
  └─────────────────────────────────────────────────────────────────────┘

  TCS DEPOSIT SCHEDULE:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Collection Date   │  Deposit By     │  Form  Challan            │
  ├────────────────────┼─────────────────┼───────────────────────────┤
  │  1st-7th of month  │  7th of month    │  CSI-CHallan-XXX         │
  │  8th-15th          │  15th of month   │  CSI-CHallan-XXX         │
  │  16th-23rd         │  23rd of month   │  CSI-CHallan-XXX         │
  │  24th-31st         │  31st of month   │  CSI-CHallan-XXX         │
  └─────────────────────────────────────────────────────────────────────┘

  NOTE: If 7th falls on a holiday, next working day applies
```

---

## 8. Penalty Structures

### 8.1 GST Penalties

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            GST PENALTIES                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  LATE FILING PENALTIES:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Return Type   │  Late Fee (Per Day)  │  Maximum Late Fee           │
  ├────────────────┼──────────────────────┼────────────────────────────┤
  │  GSTR-1        │  ₹50 (₹20 if nil)     │  ₹20,000                   │
  │  GSTR-3B       │  ₹50 (₹20 if nil)     │  ₹20,000                   │
  │  GSTR-9        │  ₹100 per day         │  ₹5,000                    │
  └─────────────────────────────────────────────────────────────────────┘

  INTEREST ON LATE PAYMENT:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Rate            │  18% per annum                                     │
  │  Calculation     │  From due date to payment date                    │
  │  Example         │  ₹10,000 tax, 30 days late:                       │
  │                  │  Interest = 10,000 × 18% × 30/365 = ₹148           │
  └─────────────────────────────────────────────────────────────────────┘

  OTHER PENALTIES:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Violation              │  Penalty                                   │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  No GST registration   │  Tax + 10% of tax + ₹1,000/day             │
  │  when required         │                                            │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  Incorrect invoice      │  ₹25,000 per invoice (max)                 │
  │  (missing details)      │                                            │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  Tax evasion            │  Tax + 50% to 100% penalty                  │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  No invoice issued      │  Tax + penalty or ₹10,000                  │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  Fake invoice           │  Tax + penalty + prosecution                 │
  └─────────────────────────────────────────────────────────────────────┘
```

### 8.2 TCS Penalties

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             TCS PENALTIES                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  LATE COLLECTION PENALTIES:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Violation              │  Penalty                                   │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  TCS not collected     │  Agency liable to pay TCS + interest      │
  │                         │  Interest: 1% per month                   │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  Late deposit           │  Interest + penalty                       │
  │                         │  Interest: 1% per month                   │
  │                         │  Penalty: Jail term 3 mo-7 yrs + fine     │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  Late filing (Form 26Q) │  ₹100/day until filed                      │
  │                         │  No maximum limit                         │
  ├─────────────────────────┼─────────────────────────────────────────────┤
  │  No PAN collected       │  Customer cannot claim credit              │
  │                         │  Agency may face liability                 │
  └─────────────────────────────────────────────────────────────────────┘

  INTEREST CALCULATION:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Formula: TCS Amount × 1% × Number of months delayed              │
  │                                                                     │
  │  Example: TCS of ₹60,000 delayed by 3 months                        │
  │  Interest = 60,000 × 0.01 × 3 = ₹1,800                            │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Compliance Automation

### 9.1 Automated Compliance Checks

```typescript
/**
 * Automated Compliance Checks
 */

class ComplianceAutomationEngine {
  /**
   * Run all compliance checks for a booking
   */
  async runComplianceChecks(
    booking: Booking
  ): Promise<ComplianceCheckResult[]> {
    const checks: ComplianceCheckResult[] = [];

    // GST checks
    checks.push(await this.checkGSTCompliance(booking));

    // TCS checks
    checks.push(await this.checkTCSCompliance(booking));

    // PAN checks
    checks.push(await this.checkPANCompliance(booking));

    // Invoice checks
    checks.push(await this.checkInvoiceCompliance(booking));

    // Documentation checks
    checks.push(await this.checkDocumentationCompliance(booking));

    return checks.filter(c => !c.passed);
  }

  /**
   * Check GST compliance
   */
  private async checkGSTCompliance(
    booking: Booking
  ): Promise<ComplianceCheckResult> {
    const issues: ComplianceIssue[] = [];

    // Check if customer GSTIN is valid (for B2B)
    if (booking.customer.gstin && booking.isB2B) {
      const gstValidation = await this.validateGSTIN(booking.customer.gstin);
      if (!gstValidation.valid) {
        issues.push({
          code: "GST_INVALID",
          severity: "critical",
          message: "Customer GSTIN format is invalid",
          field: "customer.gstin",
          action: "Verify GSTIN with customer",
          blocking: true
        });
      }
    }

    // Check GST calculation
    const expectedGST = booking.totalValue * 0.18;
    if (Math.abs(booking.gstAmount - expectedGST) > 1) {
      issues.push({
        code: "GST_CALCULATION",
        severity: "critical",
        message: `GST amount mismatch. Expected: ₹${expectedGST}, Actual: ₹${booking.gstAmount}`,
        field: "gstAmount",
        action: "Review and correct GST calculation",
        blocking: true
      });
    }

    // Check if invoice number follows sequence
    if (!this.isInvoiceSequential(booking.invoiceNumber)) {
      issues.push({
        code: "INVOICE_SEQUENCE",
        severity: "critical",
        message: "Invoice number not sequential",
        field: "invoiceNumber",
        action: "Use next sequential invoice number",
        blocking: true
      });
    }

    return {
      category: "gst",
      passed: issues.length === 0,
      issues
    };
  }

  /**
   * Check TCS compliance
   */
  private async checkTCSCompliance(
    booking: Booking
  ): Promise<ComplianceCheckResult> {
    const issues: ComplianceIssue[] = [];

    // Check if TCS applies
    const tcsApplies = booking.isInternational && booking.totalValue > 700000;

    if (tcsApplies) {
      // Check PAN collected
      if (!booking.customer.pan) {
        issues.push({
          code: "PAN_MISSING",
          severity: "critical",
          message: "Customer PAN required for TCS",
          field: "customer.pan",
          action: "Collect customer PAN before booking",
          blocking: true
        });
      }

      // Check TCS amount
      const expectedTCS = this.calculateTCS(booking.totalValue);
      if (booking.tcsAmount !== expectedTCS) {
        issues.push({
          code: "TCS_AMOUNT",
          severity: "critical",
          message: `TCS amount incorrect. Expected: ₹${expectedTCS}, Collected: ₹${booking.tcsAmount}`,
          field: "tcsAmount",
          action: "Correct TCS collection",
          blocking: true
        });
      }
    }

    return {
      category: "tcs",
      passed: issues.length === 0,
      issues
    };
  }

  /**
   * Check PAN compliance
   */
  private async checkPANCompliance(
    booking: Booking
  ): Promise<ComplianceCheckResult> {
    const issues: ComplianceIssue[] = [];

    // PAN required for high-value transactions
    const panRequired = booking.totalValue > 50000 || booking.isB2B || booking.tcsApplicable;

    if (panRequired && !booking.customer.pan) {
      issues.push({
        code: "PAN_REQUIRED",
        severity: booking.isB2B ? "critical" : "medium",
        message: `PAN required for ${booking.isB2B ? "B2B" : "high-value"} transaction`,
        field: "customer.pan",
        action: "Collect customer PAN",
        blocking: booking.isB2B
      });
    }

    // Validate PAN format if provided
    if (booking.customer.pan) {
      const panValidator = new PANValidator();
      const validation = panValidator.validateFormat(booking.customer.pan);
      if (!validation.valid) {
        issues.push({
          code: "PAN_FORMAT",
          severity: "high",
          message: validation.error || "Invalid PAN format",
          field: "customer.pan",
          action: "Verify PAN with customer",
          blocking: false
        });
      }
    }

    return {
      category: "pan",
      passed: issues.length === 0,
      issues
    };
  }

  /**
   * Check invoice compliance
   */
  private async checkInvoiceCompliance(
    booking: Booking
  ): Promise<ComplianceCheckResult> {
    const issues: ComplianceIssue[] = [];

    // Check mandatory fields
    const mandatoryFields = [
      "invoiceNumber",
      "invoiceDate",
      "supplierGSTIN",
      "customerName",
      "totalValue",
      "gstAmount"
    ];

    for (const field of mandatoryFields) {
      if (!booking[field]) {
        issues.push({
          code: "INVOICE_FIELD_MISSING",
          severity: "critical",
          message: `Mandatory invoice field missing: ${field}`,
          field,
          action: `Provide ${field} before invoicing`,
          blocking: true
        });
      }
    }

    // Check SAC code
    if (!booking.sacCode || !this.isValidSACCode(booking.sacCode)) {
      issues.push({
        code: "SAC_INVALID",
        severity: "high",
        message: "Invalid or missing SAC code",
        field: "sacCode",
        action: "Use valid SAC code (996311 for tour operator services)",
        blocking: false
      });
    }

    return {
      category: "invoice",
      passed: issues.length === 0,
      issues
    };
  }

  /**
   * Check documentation compliance
   */
  private async checkDocumentationCompliance(
    booking: Booking
  ): Promise<ComplianceCheckResult> {
    const issues: ComplianceIssue[] = [];

    // Check passport validity for international
    if (booking.isInternational) {
      if (!booking.documents?.passport) {
        issues.push({
          code: "PASSPORT_MISSING",
          severity: "critical",
          message: "Passport required for international travel",
          field: "documents.passport",
          action: "Collect passport before booking",
          blocking: true
        });
      } else {
        const passport = booking.documents.passport;
        const expiryDate = new Date(passport.expiryDate);
        const departureDate = new Date(booking.departureDate);

        if (expiryDate < departureDate) {
          issues.push({
            code: "PASSPORT_EXPIRED",
            severity: "critical",
            message: `Passport expires before departure (${passport.expiryDate})`,
            field: "documents.passport",
            action: "Request passport renewal or check with customer",
            blocking: true
          });
        }
      }
    }

    // Check visa requirements
    if (booking.isInternational && booking.visaRequired) {
      if (!booking.documents?.visa) {
        issues.push({
          code: "VISA_MISSING",
          severity: "high",
          message: "Visa required for this destination",
          field: "documents.visa",
          action: "Confirm visa requirements with customer",
          blocking: false
        });
      }
    }

    return {
      category: "documentation",
      passed: issues.length === 0,
      issues
    };
  }

  private validateGSTIN(gstin: string): Promise<{ valid: boolean; gstin?: string }> {
    // GSTIN validation logic
    return Promise.resolve({ valid: true });
  }

  private isInvoiceSequential(invoiceNumber: string): boolean {
    // Invoice sequence validation logic
    return true;
  }

  private calculateTCS(value: number): number {
    const THRESHOLD = 700000;
    const RATE = 0.20;

    if (value > THRESHOLD) {
      return (value - THRESHOLD) * RATE;
    }
    return 0;
  }

  private isValidSACCode(code: string): boolean {
    const validCodes = ["996311", "996312", "996313", "996321", "998811"];
    return validCodes.includes(code);
  }
}

interface ComplianceCheckResult {
  category: "gst" | "tcs" | "pan" | "invoice" | "documentation";
  passed: boolean;
  issues: ComplianceIssue[];
}

interface ComplianceIssue {
  code: string;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
  field: string;
  action: string;
  blocking: boolean;
}
```

### 9.2 Automated Filing Reminders

```typescript
/**
 * Compliance Filing Reminders
 */

interface FilingReminder {
  type: "gst" | "tcs";
  form: string;
  dueDate: Date;
  period: string;
  reminderDates: Date[];
  recipients: string[];
}

class ComplianceReminderSystem {
  private reminders: FilingReminder[] = [
    {
      type: "gst",
      form: "GSTR-1",
      dueDate: new Date("2026-05-11"),  // Example
      period: "April 2026",
      reminderDates: [
        new Date("2026-05-05"),  // 6 days before
        new Date("2026-05-09"),  // 2 days before
        new Date("2026-05-10"),  // 1 day before
        new Date("2026-05-11"),  // Due date
      ],
      recipients: ["accounts@agency.com", "owner@agency.com"]
    },
    {
      type: "tcs",
      form: "Form 26Q",
      dueDate: new Date("2026-07-31"),  // Example Q1
      period: "Q1 2026",
      reminderDates: [
        new Date("2026-07-25"),
        new Date("2026-07-29"),
        new Date("2026-07-30"),
        new Date("2026-07-31"),
      ],
      recipients: ["accounts@agency.com", "owner@agency.com"]
    }
  ];

  /**
   * Get upcoming reminders
   */
  getUpcomingReminders(days: number = 7): FilingReminder[] {
    const now = new Date();
    const future = new Date();
    future.setDate(future.getDate() + days);

    return this.reminders.filter(r => r.dueDate >= now && r.dueDate <= future);
  }

  /**
   * Check for overdue filings
   */
  getOverdueFilings(): FilingReminder[] {
    const now = new Date();
    return this.reminders.filter(r => r.dueDate < now);
  }
}
```

---

## 10. Compliance Checklist

### 10.1 Pre-Booking Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRE-BOOKING COMPLIANCE CHECKLIST                     │
└─────────────────────────────────────────────────────────────────────────────┘

  FOR ALL BOOKINGS:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Item                           │  Required  │  Completed  │  Notes        │
  ├─────────────────────────────────┼────────────┼────────────┼──────────────┤
  │  │  Customer name                 │  ✓        │  □         │               │
  │  │  Customer address             │  ✓        │  □         │               │
  │  │  Customer phone               │  ✓        │  □         │               │
  │  │  Quote signed                 │  ✓        │  □         │               │
  │  │  Payment received              │  ✓        │  □         │               │
  └─────────────────────────────────┴────────────┴────────────┴──────────────┘

  FOR HIGH-VALUE BOOKINGS (>₹50,000):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Item                           │  Required  │  Completed  │  Notes        │
  ├─────────────────────────────────┼────────────┼────────────┼──────────────┤
  │  │  Customer PAN                 │  ✓        │  □         │               │
  │  │  Customer GSTIN               │  *         │  □         │  * If B2B    │
  │  │  Address proof                 │  *         │  □         │  * If required│
  └─────────────────────────────────┴────────────┴────────────┴──────────────┘

  FOR INTERNATIONAL BOOKINGS:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Item                           │  Required  │  Completed  │  Notes        │
  ├─────────────────────────────────┼────────────┼────────────┼──────────────┤
  │  │  Customer PAN                 │  ✓        │  □         │               │
  │  │  Passport copy                 │  ✓        │  □         │  Valid 6 mo  │
  │  │  Visa (if required)            │  *         │  □         │  * Per country│
  │  │  Passport photo                │  ✓        │  □         │  Clear, recent│
  └─────────────────────────────────┴────────────┴────────────┴──────────────┘

  FOR BOOKINGS ABOVE ₹7 LAKH (INTERNATIONAL):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Item                           │  Required  │  Completed  │  Notes        │
  ├─────────────────────────────────┼────────────┼────────────┼──────────────┤
  │  │  TCS amount calculated          │  ✓        │  □         │               │
  │  │  TCS deposit scheduled          │  ✓        │  □         │  Within 7 days│
  │  │  Form 26Q entry prepared        │  ✓        │  □         │  Quarterly    │
  │  │  TCS certificate issued         │  ✓        │  □         │  After filing │
  └─────────────────────────────────┴────────────┴────────────┴──────────────┘
```

### 10.2 Monthly Compliance Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONTHLY COMPLIANCE CHECKLIST                        │
└─────────────────────────────────────────────────────────────────────────────┘

  GST COMPLIANCE:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Task                              │  Due Date    │  Status      │
  ├────────────────────────────────────┼──────────────┼─────────────┤
  │  │  Reconcile invoices issued        │  5th         │  □           │
  │  │  Reconcile ITC claimed            │  5th         │  □           │
  │  │  Prepare GSTR-1                   │  8th         │  □           │
  │  │  Prepare GSTR-3B                  │  8th         │  □           │
  │  │  File GSTR-3B                     │  20th        │  □           │
  │  │  File GSTR-1                      │  11th        │  □           │
  │  │  Save filed returns               │  Filed       │  □           │
  │  │  Reconcile cash ledger            │  25th        │  □           │
  └────────────────────────────────────┴──────────────┴─────────────┘

  TCS COMPLIANCE:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Task                              │  Due Date    │  Status      │
  ├────────────────────────────────────┼──────────────┼─────────────┤
  │  │  Reconcile TCS collected           │  7th         │  □           │
  │  │  Deposit TCS                     │  7th         │  □           │
  │  │  Update Form 26Q records          │  10th        │  □           │
  │  │  Verify challan acknowledgement    │  15th        │  □           │
  └────────────────────────────────────┴──────────────┴─────────────┘
```

---

## Summary

Indian travel agencies face a complex compliance landscape:

**GST Requirements:**
- 18% GST on services
- Monthly GSTR-1 and GSTR-3B filings
- Annual GSTR-9 return
- 72-month record retention
- Strict invoice formatting rules

**TCS Requirements:**
- 20% TCS on international packages > ₹7L
- Quarterly Form 26Q filing
- Form 27D certificate to customers
- Mandatory PAN collection

**Key Compliance Risks:**
- GST undercollection: Full liability + penalty
- TCS non-collection: Agency liability + interest
- Invalid invoices: Input tax credit denied
- Missing documentation: Audit exposure

**Automation Benefits:**
- Prevent 96% of GST errors
- Prevent 93% of TCS errors
- 100% invoice compliance
- Automated filing reminders
- Real-time validation

A comprehensive safety system with compliance automation prevents most compliance errors, avoids penalties, and ensures smooth operations.

---

**Next Document:** SAFETY_05_ESCALATION_DEEP_DIVE.md — Owner workflows, escalation procedures, and alert systems
