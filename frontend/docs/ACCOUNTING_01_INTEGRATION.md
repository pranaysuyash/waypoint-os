# Accounting Integration — ERP & Bookkeeping Sync

> Research document for accounting system integration, Tally ERP integration, Zoho Books sync, double-entry bookkeeping, chart of accounts for travel agencies, and financial system interoperability for the Waypoint OS platform.

---

## Key Questions

1. **How does the travel platform integrate with accounting systems?**
2. **What chart of accounts structure suits travel agency operations?**
3. **How are transactions synced between the platform and ERP?**
4. **What financial reporting do travel agencies need for compliance?**

---

## Research Areas

### Accounting Integration System

```typescript
interface AccountingIntegration {
  // Connecting the travel platform to accounting/bookkeeping systems
  supported_systems: {
    TALLY_ERP: {
      description: "Most widely used accounting software in Indian travel agencies";
      market_share: "~60% of Indian small-to-mid travel agencies use Tally";
      integration_type: "Tally Prime XML API + ODBC for real-time sync";
      sync_frequency: "Real-time for invoices/payments; daily batch for reconciliation";
    };

    ZOHO_BOOKS: {
      description: "Cloud-based accounting popular with modern agencies";
      market_share: "~20% of agencies, growing fast";
      integration_type: "REST API with webhooks for real-time sync";
      sync_frequency: "Real-time for all transactions";
    };

    MARG_ERP: {
      description: "Travel-specific ERP used by some agencies";
      integration_type: "API + CSV import/export";
    };

    CUSTOM_ERP: {
      description: "Large agencies with custom accounting systems";
      integration_type: "REST API with configurable field mapping";
    };
  };

  chart_of_accounts: {
    description: "Standard chart of accounts for Indian travel agency operations";
    structure: {
      ASSETS: {
        "1000": "Current Assets";
        "1100": {
          "1110": "Accounts Receivable — Customers",
          "1120": "Advances to Suppliers",
          "1130": "Traveler Deposits Held",
          "1140": "GST Input Credit",
          "1150": "TDS Receivable",
          "1160": "Cash and Bank",
        };
      };
      LIABILITIES: {
        "2000": "Current Liabilities";
        "2100": {
          "2110": "Accounts Payable — Suppliers",
          "2120": "Customer Advances (unearned revenue)",
          "2130": "GST Payable",
          "2140": "TCS Collected",
          "2150": "TDS Payable",
          "2160": "Customer Credit Liability",
        };
      };
      REVENUE: {
        "3000": "Operating Revenue";
        "3100": {
          "3110": "Package Sales",
          "3120": "Flight Commissions",
          "3130": "Hotel Commissions",
          "3140": "Activity Commissions",
          "3150": "Service Fees",
          "3160": "Visa Processing Fees",
          "3170": "Insurance Commission",
          "3180": "Forex Commission",
          "3190": "Cancellation Charges",
        };
      };
      EXPENSES: {
        "4000": "Operating Expenses";
        "4100": {
          "4110": "Cost of Travel Services (supplier payments)",
          "4120": "Employee Salaries",
          "4130": "Office Rent and Utilities",
          "4140": "Marketing Expenses",
          "4150": "Technology and Software",
          "4160": "Insurance Premiums",
          "4170": "Bank Charges and Payment Gateway Fees",
        };
      };
    };
  };

  // ── Accounting sync dashboard — finance view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  📊 Accounting Sync · Tally ERP · Today                    │
  // │                                                       │
  // │  Sync Status: ✅ Connected · Last sync: 2 min ago         │
  // │                                                       │
  // │  Today's Activity:                                    │
  // │  · 12 invoices synced to Tally                           │
  // │  · 8 payment receipts synced                             │
  // │  · 3 credit notes generated                             │
  // │  · 2 journal entries (commission accruals)              │
  // │                                                       │
  // │  Pending Sync: 0                                      │
  // │  Failed Sync: 0                                       │
  // │                                                       │
  // │  Monthly Summary (April 2026):                        │
  // │  Revenue: ₹45,20,000                                    │
  // │  Supplier Payments: ₹32,80,000                          │
  // │  Commissions Earned: ₹4,50,000                          │
  // │  GST Collected: ₹8,14,000                               │
  // │  TCS Collected: ₹1,35,600                               │
  // │  TDS Deducted: ₹3,20,000                                │
  // │                                                       │
  // │  [Sync Now] [View Errors] [Export to Tally] [Reports]    │
  // └─────────────────────────────────────────────────────────┘
}
```

### Transaction Sync Rules

```typescript
interface TransactionSyncRules {
  // How different transaction types flow to accounting
  sync_rules: {
    INVOICE_GENERATION: {
      trigger: "When booking is confirmed and invoice generated";
      tally_entry: "Sales voucher with item-level breakup";
      fields_synced: [
        "Customer name and GSTIN",
        "Invoice number (auto-numbered from Tally series)",
        "Line items with HSN/SAC codes",
        "GST breakup (CGST + SGST or IGST)",
        "Payment terms and due date",
      ];
    };

    PAYMENT_RECEIPT: {
      trigger: "When customer payment is received (online, cheque, cash, UPI)";
      tally_entry: "Receipt voucher";
      fields_synced: [
        "Customer name",
        "Amount and payment mode",
        "Bank account credited",
        "Reference number (cheque/transaction ID)",
        "Against which invoice(s)",
      ];
    };

    SUPPLIER_PAYMENT: {
      trigger: "When agency pays supplier for services";
      tally_entry: "Payment voucher";
      fields_synced: [
        "Supplier name and GSTIN",
        "Amount and payment mode",
        "TDS deduction (if applicable)",
        "Against which booking(s)",
        "Bank account debited",
      ];
    };

    CREDIT_NOTE: {
      trigger: "When cancellation refund is processed";
      tally_entry: "Credit note / Sales return voucher";
      fields_synced: [
        "Customer name",
        "Original invoice reference",
        "Credit note amount",
        "Reason (cancellation, partial refund, adjustment)",
        "GST adjustment",
      ];
    };

    COMMISSION_INCOME: {
      trigger: "When commission is earned from suppliers";
      tally_entry: "Journal entry — Commission income";
      frequency: "Monthly accrual or per-booking recognition per agency policy";
    };

    TCS_COLLECTION: {
      trigger: "When overseas travel package is sold (TCS on foreign remittance)";
      tally_entry: "Journal entry — TCS liability";
      reporting: "Quarterly TCS return filing with PAN/Aadhaar tracking";
    };
  };

  reconciliation: {
    DAILY_RECONCILIATION: {
      description: "Match platform transactions with bank statements";
      checks: [
        "Every payment receipt matched to bank credit",
        "Every supplier payment matched to bank debit",
        "Outstanding receivables aged (current, 30, 60, 90+ days)",
        "GST liability vs. GST collected",
      ];
    };

    MONTHLY_CLOSE: {
      description: "Month-end accounting close process";
      steps: [
        "Verify all transactions synced to Tally/Zoho",
        "Reconcile bank statements",
        "Accrue pending commissions",
        "Calculate GST liability and file returns",
        "Generate P&L and balance sheet",
        "Aging reports for receivables and payables",
      ];
    };
  };
}
```

---

## Open Problems

1. **Multi-entity accounting** — Agencies with multiple branches or franchises need separate books per entity with consolidated reporting. Tally multi-entity setup varies by version.

2. **GST complexity for travel** — Different GST rates for different services (5% on hotels, 18% on activities, 5% on tour packages with abatement), reverse charge mechanism, input tax credit eligibility — travel GST is among the most complex.

3. **Commission timing** — Commissions from airlines and hotels may be received months after the booking. Accrual vs. cash basis accounting for commissions affects financial statements significantly.

4. **Multi-currency transactions** — International bookings involve forex transactions that must be recorded at RBI reference rate on transaction date. Exchange rate fluctuations create forex gain/loss that must be tracked.

5. **Data integrity** — Accounting data is sacrosanct. A sync error that duplicates or misses a transaction creates cascading problems. Idempotent sync with error handling and manual override is essential.

---

## Next Steps

- [ ] Build Tally ERP integration with XML API sync
- [ ] Create Zoho Books integration with REST API
- [ ] Implement chart of accounts with travel-specific structure
- [ ] Build transaction sync engine with invoice, payment, credit note, commission, and TCS rules
- [ ] Create daily reconciliation workflow with bank statement matching
- [ ] Build monthly close process automation
- [ ] Implement GST computation engine with travel-specific rates and rules
- [ ] Create financial reporting dashboard (P&L, balance sheet, aging reports)
