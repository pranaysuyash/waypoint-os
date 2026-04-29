# Agency Financial Dashboard — Master Index

> Comprehensive research on agency financial dashboards, profitability analysis, forecasting, and financial alerts for Indian travel agencies.

---

## Series Overview

This series covers the financial intelligence layer of Waypoint OS — from real-time KPI dashboards and India tax compliance to profitability analytics, revenue forecasting, and proactive financial alerts.

**Target Audience:** Product managers, finance engineers, data analysts, agency owners

**Key Constraint:** Financial data requires exact accuracy (no approximations for tax), real-time alerts must balance sensitivity vs noise, and India-specific compliance (GST/TCS/TDS) adds mandatory complexity.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [FIN_DASH_01_OVERVIEW.md](FIN_DASH_01_OVERVIEW.md) | KPI dashboard, revenue breakdowns, India tax, role-based views |
| 2 | [FIN_DASH_02_PROFITABILITY.md](FIN_DASH_02_PROFITABILITY.md) | Per-trip profitability, destination/agent ranking, seasonal patterns, product mix |
| 3 | [FIN_DASH_03_FORECASTING.md](FIN_DASH_03_FORECASTING.md) | Revenue forecasting, seasonal demand, cash flow projection, budget tracking, tax planning |
| 4 | [FIN_DASH_04_ALERTS.md](FIN_DASH_04_ALERTS.md) | Revenue anomalies, margin erosion, payment tracking, fraud indicators, escalation |

---

## Key Themes

### 1. Financial Visibility
Agency owners need a single view of revenue, costs, margins, and cash position — updated in real-time but with clear "as of" timestamps to avoid confusion over pending transactions.

### 2. India Tax Compliance
GST (with CGST/SGST split), TCS on overseas packages, and TDS on vendor payments create a complex compliance landscape. The dashboard must track filing dates, deposit schedules, and alert before deadlines.

### 3. Profitability Intelligence
Beyond top-line revenue, per-trip profitability reveals which destinations, agents, and segments actually make money. Seasonal patterns and product mix analysis drive strategic decisions.

### 4. Proactive Alerts
Financial problems compound silently. Anomaly detection, margin erosion monitoring, and payment aging alerts catch issues early — before they become crises.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Booking Engine (BOOKING_ENGINE_*) | Booking data feeds revenue and profitability |
| Vendor Management (VENDOR_*) | Vendor costs affect margins and cash flow |
| Payment Processing (PAYMENT_*) | Payment data drives cash flow and receivables |
| CRM (CRM_*) | Customer segment profitability analysis |
| Workforce Management (WORKFORCE_*) | Agent performance and commission tracking |
| Analytics & BI (ANALYTICS_*) | Financial dashboards are a subset of BI |
| Pricing Engine (PRICING_*) | Pricing decisions affect margin analysis |
| Loyalty & Promotions (VOUCHER_*) | Promotion costs impact profitability |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Dashboard UI | React + Recharts | Interactive financial visualizations |
| Data Aggregation | PostgreSQL + materialized views | Fast metric computation |
| Forecasting | Python + Prophet/ARIMA | Revenue and demand forecasting |
| Alert Engine | Node.js + Redis | Real-time threshold monitoring |
| Tax Calculator | Custom (India GST rules) | Exact tax computation |
| Reporting | PDF generation (Puppeteer) | Exportable financial reports |

---

**Created:** 2026-04-29
