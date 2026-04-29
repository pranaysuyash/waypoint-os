# Travel Compliance Automation — Financial Compliance & Taxation

> Research document for automated GST/TCS/TDS compliance, invoice generation, tax filing assistance, and financial regulatory compliance for Indian travel agencies.

---

## Key Questions

1. **How do we automate GST compliance for travel services?**
2. **What TCS (Tax Collected at Source) rules apply to foreign tour packages?**
3. **How do TDS deductions work for international supplier payments?**
4. **What financial reporting does the agency need for compliance?**

---

## Research Areas

### GST Compliance Engine

```typescript
interface GSTCompliance {
  // Indian GST rules for travel services
  gst_rules: {
    // GST on travel services (as of 2026)
    services: {
      DOMESTIC_TRAVEL: {
        description: "Domestic flight, hotel, transport within India";
        gst_rate: 5;                      // 5% with ITC
        hsn_sac: "9985";
        reverse_charge: false;
      };

      INTERNATIONAL_TRAVEL_PACKAGE: {
        description: "Foreign tour package (hotel + transport abroad)";
        gst_rate: 5;                      // 5% on bundled services
        hsn_sac: "9985";
        condition: "If billed as package (not itemized)";
      };

      HOTEL_ACCOMMODATION: {
        description: "Hotel stay in India";
        gst_rate: 18;                     // 18% for >₹1000/night
        threshold: 1000;                  // per night
        below_threshold_rate: 12;         // 12% for ≤₹1000/night
        hsn_sac: "9963";
      };

      AIRLINE_TICKET: {
        description: "Domestic flight ticket";
        gst_rate: 5;                      // economy: 5%
        business_class_rate: 12;          // business: 12%
        hsn_sac: "9985";
        note: "Airlines charge directly, agent commission is 18% GST",
      };

      TOUR_OPERATOR_SERVICE: {
        description: "Tour operator services (planning, coordination)";
        gst_rate: 18;                     // 18% on service fee
        hsn_sac: "9985";
      };
    };

    // Input Tax Credit tracking
    itc_tracking: {
      total_itc_available: number;
      itc_claimed: number;
      itc_pending: number;
      ineligible_itc: number;             // blocked credits
    };
  };
}

interface InvoiceGenerator {
  // Auto-generate GST-compliant invoices
  generate(trip_id: string): GSTInvoice;
}

interface GSTInvoice {
  invoice_number: string;                 // auto-incremented
  invoice_date: string;
  gstin: string;                         // agency GSTIN
  customer_gstin: string | null;

  line_items: {
    description: string;
    hsn_sac: string;
    quantity: number;
    unit_price: number;
    discount: number;
    taxable_amount: number;
    cgst_rate: number;
    cgst_amount: number;
    sgst_rate: number;
    sgst_amount: number;
    igst_rate: number;                    // for inter-state
    igst_amount: number;
    total: number;
  }[];

  subtotal: number;
  total_cgst: number;
  total_sgst: number;
  total_igst: number;
  grand_total: number;
}

// ── GST invoice generation ──
// ┌─────────────────────────────────────────────────────┐
// │  Invoice Generator — GST-Compliant                      │
// │                                                       │
// │  Trip: WP-442 Sharma Singapore                         │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ TAX INVOICE                                     │   │
// │  │ Invoice #: INV-2026-0442                       │   │
// │  │ Date: May 15, 2026                              │   │
// │  │ GSTIN: 07AABCT1234F1Z5                         │   │
// │  │                                               │   │
// │  │ Bill to: Rajesh Sharma                         │   │
// │  │          New Delhi                             │   │
// │  │                                               │   │
// │  │ ──────────────────────────────────────────     │   │
// │  │ Description        │ SAC  │ Amt   │ GST  │Tot  │   │
// │  │ ──────────────────────────────────────────     │   │
// │  │ Singapore Package  │9985  │₹1,60K │ 5%  │₹1,68K│   │
// │  │ (foreign tour pkg) │      │       │₹8,000│      │   │
// │  │                                               │   │
// │  │ Travel Insurance   │9985  │₹4,800 │18%  │₹5,664│   │
// │  │                    │      │       │₹864 │      │   │
// │  │                                               │   │
// │  │ Visa Processing    │9985  │₹2,400 │18%  │₹2,832│   │
// │  │                    │      │       │₹432 │      │   │
// │  │                                               │   │
// │  │ ──────────────────────────────────────────     │   │
// │  │ Subtotal: ₹1,67,200                            │   │
// │  │ CGST (2.5%): ₹4,000                            │   │
// │  │ SGST (2.5%): ₹4,000                            │   │
// │  │ CGST (9%): ₹1,296                              │   │
// │  │ SGST (9%): ₹1,296                              │   │
// │  │ ──────────────────────────────────────────     │   │
// │  │ Grand Total: ₹1,77,792                          │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Download PDF] [Send to Customer] [File GSTR-1]       │
// └─────────────────────────────────────────────────────┘
```

### TCS on Foreign Tour Packages

```typescript
interface TCSCompliance {
  // Tax Collected at Source on foreign tour packages
  tcs_rules: {
    // Section 206C(1G) of Income Tax Act
    FOREIGN_TOUR_PACKAGE: {
      description: "TCS on sale of foreign tour packages";
      threshold: 0;                       // no threshold — applies from ₹1
      rate_resident: 5;                   // 5% for resident
      rate_no_pan: 10;                    // 10% if no PAN
      rate_high_value: 10;                // 10% if amount > ₹7L/year (LRS)

      // What's included in "foreign tour package"
      included: [
        "Overseas hotel accommodation",
        "Overseas transport",
        "Overseas sightseeing",
        "Overseas meals",
        "Travel insurance for foreign trip",
      ];

      // What's NOT included
      excluded: [
        "International flight tickets (separate TCS rule)",
        "Visa fees",
        "Domestic portion of trip",
      ];

      // Collection mechanism
      collection_point: "At the time of receiving payment";
      deposit_deadline: "7th of following month";
      return_filing: "Quarterly TCS return (Form 27EQ)";
    };

    // Per-customer annual tracking
    customer_tracking: {
      pan_number: string;
      total_tcs_collected: number;
      total_package_amount: number;
      transactions: {
        trip_id: string;
        package_amount: number;
        tcs_collected: number;
        tcs_rate: number;
        date: string;
      }[];
    };
  };
}

// ── TCS calculation ──
// ┌─────────────────────────────────────────────────────┐
// │  TCS Calculation — Sharma Singapore                     │
// │                                                       │
// │  Package amount: ₹1,67,200                             │
// │  (Excluding visa fees ₹2,400 — not subject to TCS)     │
// │                                                       │
// │  Customer: Rajesh Sharma · PAN: ABCPS1234K             │
// │  FY 2026-27 foreign packages so far: ₹0                │
// │  (First foreign package of the year)                    │
// │                                                       │
// │  TCS calculation:                                     │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Package: ₹1,67,200                             │   │
// │  │ TCS rate: 5% (under ₹7L threshold for year)    │   │
// │  │ TCS amount: ₹8,360                             │   │
// │  │                                               │   │
// │  │ Customer pays: ₹1,67,200 + ₹8,360 = ₹1,75,560 │   │
// │  │ (TCS is recoverable by customer in ITR)         │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Annual TCS tracking for Rajesh Sharma:                │
// │  FY 2026-27 collected: ₹8,360 / ₹7,00,000 threshold  │
// │  Next package: same 5% (still under ₹7L)              │
// │                                                       │
// │  Deposit deadline: June 7, 2026                        │
// │  [Add to Invoice] [Generate TCS Certificate]           │
// └─────────────────────────────────────────────────────┘
```

### TDS on International Payments

```typescript
interface TDSCompliance {
  // Tax Deducted at Source for international supplier payments
  tds_rules: {
    // Section 195 — Payments to non-residents
    INTERNATIONAL_PAYMENTS: {
      hotel_payments_abroad: {
        rate: 10;                         // 10% TDS (DTAA may reduce)
        condition: "Payment for services received in India";
        note: "If hotel bills directly to customer, no TDS by agent";
      };

      dmc_payments: {
        rate: 10;                         // 10% (may vary by DTAA)
        condition: "Payment to foreign DMC for services";
        form_15CA_CB: true;              // mandatory for >₹5L
      };

      airline_payments: {
        rate: 0;                          // 0% (airline tickets are exempt)
        note: "But agent commission from airline is taxable income",
      };

      activity_provider_abroad: {
        rate: 10;
        condition: "Payment for overseas activities arranged by agent";
      };
    };

    // Compliance forms
    forms: {
      "15CA": "Online declaration for foreign remittance";
      "15CB": "CA certificate for foreign remittance";
      "Form 16A": "TDS certificate to deductee";
    };
  };
}

// ── TDS compliance tracker ──
// ┌─────────────────────────────────────────────────────┐
// │  TDS Compliance — International Payments                │
// │  Month: May 2026                                       │
// │                                                       │
// │  Pending TDS deductions:                               │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Payment                  │ Amount │ TDS │ Form │   │
// │  │ ────────────────────────────────────────────  │   │
// │  │ Singapore DMC (WP-442)   │₹35,000│₹3,500│15CA  │   │
// │  │ Dubai Hotel (WP-448)     │₹28,000│₹2,800│15CA  │   │
// │  │ Thai Activity Co (WP-455)│₹12,000│₹1,200│15CA  │   │
// │  │                                               │   │
// │  │ Total TDS to deduct: ₹7,500                   │   │
// │  │ Deposit deadline: June 7, 2026                │   │
// │  │ CA certificates needed: 3 (15CB)              │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Generate Form 15CA] [Request CA Certificate]          │
// │  [File TDS Return] [Payment Calendar]                   │
// └─────────────────────────────────────────────────────┘
```

### GST Filing Dashboard

```typescript
interface GSTFilingDashboard {
  // Monthly/quarterly filing tracker
  filing_status: {
    gstr_1: {                             // outward supplies
      period: string;
      status: "PENDING" | "PREPARED" | "FILED";
      due_date: string;
      total_invoices: number;
      total_tax: number;
    };

    gstr_3b: {                            // summary return
      period: string;
      status: "PENDING" | "PREPARED" | "FILED";
      due_date: string;
      output_tax: number;
      input_tax_credit: number;
      net_tax_payable: number;
    };
  };

  // ITC reconciliation
  itc_reconciliation: {
    itc_available_gstr_2a: number;        // from supplier filings
    itc_claimed: number;
    itc_reconciliation_gap: number;
    action_needed: string[];
  };
}

// ── GST filing dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  GST Compliance — Filing Dashboard                      │
// │  FY 2026-27                                            │
// │                                                       │
// │  This month (April 2026):                              │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Return │ Status   │ Due Date │ Invoices │ Tax  │   │
// │  │ ────────────────────────────────────────────  │   │
// │  │ GSTR-1 │ PREPARED │ May 11   │   48     │₹2.4L │   │
// │  │ GSTR-3B│ PENDING  │ May 20   │   —      │₹1.8L │   │
// │  │ TCS    │ PENDING  │ Jun 7    │   12     │₹45K  │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ITC Reconciliation:                                  │
// │  Available (GSTR-2A): ₹1.2L                           │
// │  Claimed: ₹98K                                        │
// │  Gap: ₹22K (6 supplier invoices not yet filed)        │
// │  [Follow up with suppliers]                            │
// │                                                       │
// │  Annual summary:                                      │
// │  FY 2025-26 turnover: ₹1.8Cr                         │
// │  GST collected: ₹14.2L                                │
// │  ITC claimed: ₹9.8L                                   │
// │  Net GST paid: ₹4.4L                                  │
// │                                                       │
// │  [File GSTR-1] [Prepare GSTR-3B] [ITC Report]         │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **GST rate complexity** — Different components of a trip have different GST rates. Package bundling changes the applicable rate. Need careful line-item categorization.

2. **DTAA (Double Taxation Avoidance Agreement)** — TDS rates on international payments vary by country based on DTAA. Maintaining country-specific rates for 100+ countries is complex.

3. **E-invoicing mandate** — India is moving toward mandatory e-invoicing for businesses above certain turnover thresholds. The system must generate IRN (Invoice Reference Number) compliant invoices.

4. **Regulatory change frequency** — GST rates, TCS thresholds, and TDS rates change with budget announcements. Need automated rule update mechanism.

---

## Next Steps

- [ ] Build GST invoice generator with auto-categorization
- [ ] Create TCS calculator with per-customer annual tracking
- [ ] Implement TDS deduction tracker for international payments
- [ ] Design GST filing dashboard with ITC reconciliation
