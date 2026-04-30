# Accounting Integration — Master Index

> Research on Tally ERP integration, Zoho Books sync, chart of accounts for travel agencies, transaction sync rules, GST computation, TCS/TDS tracking, and financial system interoperability for the Waypoint OS platform.

---

## Series Overview

This series covers accounting integration — the bridge between the travel platform and the agency's bookkeeping system. From Tally ERP and Zoho Books real-time sync to a travel-specific chart of accounts and GST computation for travel services (5% hotels, 18% activities, 5% tour packages with abatement), accounting integration ensures every booking, payment, refund, commission, and tax liability is accurately recorded without manual double-entry.

**Target Audience:** Finance managers, product managers, operations managers

**Key Insight:** Indian travel agencies spend 15-20 hours per week on manual accounting — copying booking data into Tally, calculating GST for different service types, tracking TCS on foreign remittances, and reconciling bank statements. Automated accounting integration saves 80% of this time and eliminates the #1 source of financial errors in travel agencies: manual data entry mistakes.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [ACCOUNTING_01_INTEGRATION.md](ACCOUNTING_01_INTEGRATION.md) | Tally/Zoho integration, chart of accounts, transaction sync (invoices, payments, credit notes, commissions, TCS), daily reconciliation, monthly close, GST computation, multi-currency handling |

---

## Key Themes

### 1. No Manual Double-Entry
Every booking, payment, refund, and commission should flow automatically to the accounting system. Manual double-entry is error-prone and time-consuming. The platform should be the single source of truth.

### 2. GST Is Complex in Travel
Different GST rates for hotels (5%), activities (18%), tour packages (5% with 40% abatement), and airline tickets (varies) make travel GST among the most complex. Automated GST computation based on service type is essential.

### 3. Tally Dominates Indian Agencies
60% of Indian travel agencies use Tally ERP. Integration with Tally isn't optional — it's the #1 integration requirement. Zoho Books is growing but Tally is the baseline.

### 4. Accounting Data Is Sacrosanct
A sync error in accounting creates cascading problems (wrong GST filing, incorrect P&L, tax notices). Idempotent sync, error handling, and manual override mechanisms are essential.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Finance (FINANCE_*) | Core financial operations |
| Financial Reconciliation (FINANCIAL_RECONCILIATION_*) | Bank reconciliation |
| Payment Processing (PAYMENT_PROCESSING_*) | Payment transaction data |
| Reporting (REPORTING_*) | GST and tax reporting |
| Commission (COMMISSION_*) | Commission accrual entries |
| Customer Credit (CUSTOMER_CREDIT_*) | Credit liability accounting |
| Refund & Cancellation (REFUND_CANCELLATION_*) | Credit note generation |
| Supplier Settlement (SUPPLIER_SETTLE_*) | Supplier payment entries |
| Forex Management (FOREX_MGMT_*) | Multi-currency accounting |
| Revenue Architecture (REVENUE_ARCH_*) | Revenue recognition rules |
| Tax Compliance (REPORTING_01_GST) | GST computation |

---

**Created:** 2026-04-30
