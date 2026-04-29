# Travel Industry Reporting & Filing — Master Index

> Comprehensive research on tax reporting, IATA/BSP compliance, government filings, and management reporting for Indian travel agencies.

---

## Series Overview

This series covers every reporting and filing obligation an Indian travel agency faces — from GST returns and TCS deposits to IATA BSP settlement, tourism board registrations, and board-level business reporting. Compliance is not optional; automation makes it survivable.

**Target Audience:** Backend engineers, finance team, operations managers, compliance officers, agency owners

**Key Constraint:** Indian regulatory complexity — GST, TCS, TDS, FEMA, LRS, consumer protection, state tourism, labor law — all overlapping with different deadlines and portals

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [REPORTING_01_GST.md](REPORTING_01_GST.md) | GST returns, TCS on overseas travel, TDS processing, filing calendar |
| 2 | [REPORTING_02_IATA.md](REPORTING_02_IATA.md) | IATA accreditation, BSP settlement, ADM/ACM management, airline commission |
| 3 | [REPORTING_03_GOVERNMENT.md](REPORTING_03_GOVERNMENT.md) | Tourism board registration, RBI/FEMA reporting, consumer protection, statutory compliance |
| 4 | [REPORTING_04_BUSINESS.md](REPORTING_04_BUSINESS.md) | Management reports, financial statements, forecasting, benchmarking |

---

## Key Themes

### 1. Compliance as Infrastructure
Tax filing, BSP settlement, and regulatory reporting are not features — they are the operational backbone. Miss a BSP payment and IATA suspends accreditation. Miss a GST return and penalties compound. The platform must make compliance effortless.

### 2. Automation Over Manual Filing
Every filing that can be automated should be. Auto-calculate GST from trip invoices, auto-generate TCS on overseas bookings, auto-match GSTR-2B for ITC. The agency owner should review and approve, not manually prepare.

### 3. Financial Visibility
Agency owners need real-time visibility into revenue, margins, receivables, and cash position. A daily briefing, weekly team review, and monthly P&L should be auto-generated from transaction data.

### 4. India-Specific Regulatory Stack
India's regulatory environment for travel agencies is uniquely complex — GST with multiple SAC codes, TCS on overseas packages, FEMA for forex, state tourism registrations, and consumer protection. The platform must handle this complexity natively.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Travel Finance (FINANCE_*) | Accounting engine, double-entry bookkeeping, profit centers |
| Supplier Settlement (SUPPLIER_SETTLE_*) | Supplier invoicing, payment reconciliation |
| Travel Finance (FINANCE_*) | Treasury management, cash flow |
| Fraud Detection (FRAUD_*) | Suspicious transaction reporting (STR/FIU-IND) |
| Multi-Currency (FOREX_MGMT_*) | RBI reporting, FEMA compliance, LRS tracking |
| Regulatory & Licensing (REGULATORY_*) | IATA accreditation, government licensing |
| Data Privacy (PRIVACY_*) | DPDP Act reporting, breach notification |
| Analytics & BI (ANALYTICS_*) | Business intelligence and dashboards |
| Operations Command Center (OPS_CENTER_*) | Real-time operational dashboards |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Tax Engine | Custom + ClearTax API | GST/TCS/TDS calculation and filing |
| BSP Integration | BSPlink API | Airline settlement data |
| GST Portal | GSTN API | GSTR-1/3B filing |
| TDS Portal | TRACES API | Form 24Q/26Q filing |
| RBI Portal | RBI EARS API | FEMA/forex reporting |
| Accounting | Tally API / custom | Double-entry, P&L, balance sheet |
| BI / Reports | Metabase / Looker | Management dashboards |
| Document Vault | Custom + S3 | Compliance document storage |
| Calendar | Custom | Filing deadline tracking |
| Notifications | WhatsApp + Email | Filing reminders and alerts |

---

**Created:** 2026-04-29
