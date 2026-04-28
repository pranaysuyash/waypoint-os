# Financial Reporting — Reporting & Close

> Research document for financial reporting, period close, and compliance reporting.

---

## Key Questions

1. **What financial reports are essential for a travel agency's daily/weekly/monthly operations?**
2. **How do we accelerate period close from days to hours?**
3. **What statutory reporting requirements apply (GST, TDS, TCS, income tax)?**
4. **How do we build financial dashboards that drive actionable decisions?**
5. **What's the audit trail requirement for financial transactions?**

---

## Research Areas

### Report Framework

```typescript
interface FinancialReport {
  reportId: string;
  type: ReportType;
  period: ReportPeriod;
  generatedAt: Date;
  sections: ReportSection[];
  status: 'draft' | 'under_review' | 'approved' | 'published';
}

type ReportType =
  // Operational reports
  | 'daily_cash_position'
  | 'daily_booking_revenue'
  | 'weekly_pipeline'
  | 'monthly_pnl'
  // Reconciliation reports
  | 'payment_reconciliation'
  | 'supplier_payables'
  | 'customer_receivables'
  | 'commission_payable'
  // Statutory reports
  | 'gst_return'
  | 'tds_return'
  | 'tcs_return'
  | 'foreign_remittance'
  // Analytical reports
  | 'revenue_by_segment'
  | 'margin_analysis'
  | 'supplier_spend_analysis'
  | 'customer_lifetime_value'
  // Management reports
  | 'budget_vs_actual'
  | 'cash_flow_forecast'
  | 'working_capital';

interface ReportPeriod {
  type: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual' | 'custom';
  startDate: Date;
  endDate: Date;
}
```

### Period Close Workflow

**Travel agency close challenges:**
- Bookings span multiple periods (booked in Jan, traveled in Mar, paid supplier in Apr)
- Supplier invoices arrive late
- Commission calculations depend on travel completion, not booking date
- Currency conversions create timing differences
- Refunds and cancellations span periods

```typescript
interface CloseProcess {
  period: ReportPeriod;
  status: CloseStatus;
  steps: CloseStep[];
  cutOffDate: Date;
  targetCloseDate: Date;
  actualCloseDate?: Date;
}

type CloseStatus =
  | 'pre_close'
  | 'reconciliation'
  | 'adjustments'
  | 'review'
  | 'finalized';

interface CloseStep {
  step: string;
  owner: string;
  status: 'pending' | 'in_progress' | 'complete' | 'blocked';
  dependencies: string[];
  checklist: string[];
}
```

### GST Compliance

**GST in travel agency context:**

| Service | GST Rate | Point of Taxation |
|---------|----------|-------------------|
| Hotel booking (room < ₹1000) | Nil | At check-out |
| Hotel booking (₹1000-7500) | 12% | At check-out |
| Hotel booking (> ₹7500) | 18% | At check-out |
| Airline tickets (economy) | 5% | At ticketing |
| Airline tickets (business) | 12% | At ticketing |
| Tour packages | 5% (60% abatement) | At invoicing |
| Foreign tour packages | 5% | At invoicing |
| Travel agent services | 18% | At invoicing |

**Open questions:**
- How do we handle the 60% abatement calculation for tour packages?
- What's the GST treatment for commission earned vs. service fees charged?
- How do we manage input tax credit on supplier invoices?

---

## Open Problems

1. **Revenue recognition timing** — When is revenue recognized: at booking, at travel, or at supplier payment? This affects monthly P&L accuracy.

2. **Multi-entity consolidation** — If the agency operates through multiple GST registrations or legal entities, consolidation adds complexity.

3. **Automated close** — Can we get to a T+1 close (next business day) for operational reporting? What's blocking this?

4. **Cash flow forecasting** — Travel is seasonal with large cash inflows in booking season and large outflows during travel season. How to build reliable forecasts?

5. **Audit readiness** — Being perpetually audit-ready requires real-time transaction integrity, not month-end reconciliation scrambles.

---

## Next Steps

- [ ] Research travel agency accounting standards and revenue recognition
- [ ] Design GST calculation engine for different service categories
- [ ] Study period close automation approaches
- [ ] Map statutory reporting calendar and requirements
- [ ] Design financial dashboard KPIs for operational decision-making
