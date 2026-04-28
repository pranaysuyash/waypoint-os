# Supplier Invoice & Settlement — Master Index

> Exploration of supplier invoice processing, payment execution, credit notes, and reconciliation.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Invoice Processing](SUPPLIER_SETTLE_01_INVOICES.md) | Invoice receipt, OCR capture, matching, approval workflow |
| 02 | [Payment Processing](SUPPLIER_SETTLE_02_PAYMENTS.md) | Payment scheduling, batch processing, BSP settlement, multi-method execution |
| 03 | [Credit Notes & Adjustments](SUPPLIER_SETTLE_03_CREDITS.md) | Credit notes, ADMs/ACMs, GST reversal, adjustment accounting |
| 04 | [Reconciliation & Disputes](SUPPLIER_SETTLE_04_RECONCILIATION.md) | Statement reconciliation, dispute workflow, aging reports, year-end close |

---

## Key Themes

- **Every rupee is tracked** — From invoice receipt to payment execution to reconciliation. No payment leaves the agency without matching to a booking, an approved invoice, and a journal entry.
- **BSP is a world of its own** — Airline settlement through BSP has unique rules, weekly cycles, ADMs, and bank guarantee requirements. It demands dedicated handling.
- **GST reconciliation is the hardest part** — Supplier GSTR-1 must match agency GSTR-2A for ITC claims. Non-filing suppliers create blocked credits. Need proactive tracking.
- **Credit notes are cash** — Unclaimed credits, unused advances, and pending refunds are agency money sitting in supplier accounts. Active credit management is working capital recovery.
- **Reconciliation is continuous** — Don't wait for year-end. Weekly BSP reconciliation, monthly supplier reconciliation, and quarterly full reconciliation. Continuous matching prevents surprises.

## Integration Points

- **Travel Finance & Accounting** — Journal entries for all invoices, payments, and adjustments
- **Booking Engine** — Invoice matching to bookings, cost tracking per trip
- **Supplier Integration** — Invoice receipt via API, portal sync
- **Payment Processing** — Bank API integration for payment execution
- **Regulatory & Licensing** — GST reconciliation, TDS/TCS tracking
- **Analytics & BI** — Settlement dashboards, aging reports, payment analytics
