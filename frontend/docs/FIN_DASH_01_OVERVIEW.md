# Agency Financial Dashboard — Overview & KPIs

> Research document for agency financial overview dashboard, real-time KPIs, revenue/cost breakdowns, cash flow projection, and India-specific tax dashboards.

---

## Key Questions

1. **What financial KPIs do agency owners need at a glance?**
2. **How do we visualize revenue across channels, destinations, and agents?**
3. **What cash flow projections are essential?**
4. **What India-specific tax metrics must the dashboard show?**

---

## Research Areas

### Financial Overview Dashboard

```typescript
interface FinancialOverview {
  agency_id: string;
  period: "TODAY" | "THIS_WEEK" | "THIS_MONTH" | "THIS_QUARTER" | "THIS_YEAR";

  // Top-line metrics
  revenue: Money;
  costs: Money;
  gross_margin: Money;
  gross_margin_percentage: number;
  net_profit: Money;

  // Velocity
  new_bookings: number;
  new_bookings_value: Money;
  average_deal_size: Money;
  conversion_rate: number;

  // Cash position
  cash_on_hand: Money;
  receivables: Money;
  payables: Money;
  working_capital: Money;

  // Comparison
  vs_previous_period: {
    revenue_change: number;             // +15%
    bookings_change: number;
    margin_change: number;
  };
}

// ── Dashboard layout ──
// ┌─────────────────────────────────────────────────────┐
// │  Agency Financial Overview — April 2026               │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
// │  │Revenue│ │Costs  │ │Margin │ │Bookings│ │Cash  │     │
// │  │₹42L  │ │₹31L  │ │₹11L  │ │ 128  │ │₹18L  │     │
// │  │+12%  │ │+8%   │ │+22%  │ │+15%  │ │Good  │     │
// │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │
// │                                                       │
// │  Revenue by Channel:                                  │
// │  WhatsApp ████████████ 45% | ₹18.9L                 │
// │  Portal  ██████ 25% | ₹10.5L                         │
// │  Phone   ████ 18% | ₹7.6L                            │
// │  Walk-in ██ 12% | ₹5L                                │
// │                                                       │
// │  Revenue by Destination:                              │
// │  Kerala    ████████████ 28%                          │
// │  Singapore ██████ 18%                                 │
// │  Rajasthan █████ 15%                                  │
// │  Goa       ████ 12%                                  │
// │  Dubai     ███ 10%                                   │
// │  Other     ████ 17%                                  │
// │                                                       │
// │  Cash Flow: In: ₹52L | Out: ₹41L | Net: +₹11L     │
// │  Receivables: ₹8.5L (12 overdue) | Payables: ₹3.2L  │
// └─────────────────────────────────────────────────────┘
```

### India-Specific Tax Dashboard

```typescript
interface IndiaTaxDashboard {
  period: "THIS_MONTH" | "THIS_QUARTER" | "THIS_YEAR";

  // GST
  gst: {
    output_gst: Money;                 // GST collected on sales
    input_gst: Money;                  // GST paid on purchases
    net_gst_payable: Money;
    gstr_1_due: string;               // next filing date
    gstr_3b_due: string;
    filing_status: "FILED" | "DUE_SOON" | "OVERDUE";
  };

  // TCS (Tax Collected at Source)
  tcs: {
    overseas_packages_tcs: Money;       // 5% on overseas packages > ₹7L
    total_tcs_collected: Money;
    tcs_deposited: Money;
    tcs_pending_deposit: Money;
    next_deposit_due: string;
  };

  // TDS (Tax Deducted at Source)
  tds: {
    section_194c: Money;               // contractor payments
    section_194h: Money;               // commission payments
    section_194d: Money;               // insurance commission
    total_tds_deducted: Money;
    tds_deposited: Money;
    tds_pending: Money;
  };
}

// ── Tax dashboard view ──
// ┌─────────────────────────────────────────────────────┐
// │  India Tax Compliance — April 2026                    │
// │                                                       │
// │  GST (Goods & Services Tax):                          │
// │  Output CGST: ₹1.2L + SGST: ₹1.2L = ₹2.4L         │
// │  Input CGST: ₹0.6L + SGST: ₹0.6L = ₹1.2L          │
// │  Net payable: ₹1.2L                                   │
// │  GSTR-1 due: Apr 11 ✅ Filed                         │
// │  GSTR-3B due: Apr 20 ⏳ 3 days left                  │
// │                                                       │
// │  TCS (Tax Collected at Source):                       │
// │  Overseas packages: ₹4.2L collected                  │
// │  Deposited: ₹3.8L | Pending: ₹0.4L                  │
// │  Next deposit: Apr 7 ✅ Done                          │
// │                                                       │
// │  TDS (Tax Deducted at Source):                        │
// │  §194C (contractors): ₹0.8L                          │
// │  §194H (commission): ₹1.2L                           │
// │  Total: ₹2.0L deposited                              │
// └─────────────────────────────────────────────────────┘
```

### Role-Based Views

```typescript
// ── Role-based dashboard filtering ──
// ┌─────────────────────────────────────────────────────┐
// │  Role          | What they see                        │
// │  ─────────────────────────────────────────────────── │
// │  Owner/CEO     | Everything: full P&L, cash flow,   │
// │                | tax, forecasting, department budgets │
// │                                                       │
// │  Finance Head  | Full financials, reconciliation,   │
// │                | tax compliance, vendor payments      │
// │                                                       │
// │  Operations    | Revenue by agent, booking pipeline, │
// │  Manager       | SLA metrics, trip health scores     │
// │                                                       │
// │  Sales Manager| Conversion rates, pipeline value,   │
// │                | agent performance, lead quality      │
// │                                                       │
// │  Agent         | Own revenue, commissions,           │
// │                | trip financials, pending payments    │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Real-time vs batch** — Financial data needs accuracy over speed. Real-time estimates may be wrong (pending payment confirmation). Need "as of" timestamps.

2. **Multi-entity consolidation** — Agencies with branches or subsidiaries need consolidated views. Currency conversion and inter-entity elimination add complexity.

3. **Tax accuracy** — GST/TCS/TDS calculations must be exact. Rounding errors at scale (₹0.01 per invoice × 1000 invoices) create reconciliation nightmares.

---

## Next Steps

- [ ] Build financial overview dashboard with real-time KPIs
- [ ] Create India tax compliance widget (GST/TCS/TDS)
- [ ] Implement role-based dashboard access control
- [ ] Design cash flow projection widget
- [ ] Build revenue breakdown by channel/destination/agent
