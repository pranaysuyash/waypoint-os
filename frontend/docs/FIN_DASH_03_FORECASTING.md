# Agency Financial Dashboard — Forecasting & Planning

> Research document for revenue forecasting, seasonal demand modeling, cash flow forecasting, budget vs actual tracking, scenario planning, and India tax projections.

---

## Key Questions

1. **How do we forecast revenue for upcoming periods?**
2. **What cash flow projections are essential for agency operations?**
3. **How do we plan budgets and track variance?**
4. **What India-specific tax projections must we model?**

---

## Research Areas

### Revenue Forecasting

```typescript
interface RevenueForecast {
  period: "NEXT_MONTH" | "NEXT_QUARTER" | "NEXT_YEAR";
  confidence: number;                   // 0-100%

  // Pipeline-based forecast
  pipeline_forecast: {
    confirmed_bookings: Money;          // already confirmed
    advanced_pipeline: Money;           // likely to close (>70%)
    early_pipeline: Money;              // may close (30-70%)
    weighted_pipeline: Money;           // probability-weighted total
  };

  // Historical-based forecast
  historical_forecast: {
    same_period_last_year: Money;
    growth_adjusted: Money;             // adjusted for growth trend
    seasonal_adjusted: Money;           // adjusted for seasonality
  };

  // ML-based forecast
  ml_forecast: {
    predicted: Money;
    confidence_low: Money;
    confidence_high: Money;
    factors: ForecastFactor[];
  };

  // Final blended forecast
  forecast: Money;
  forecast_range: { low: Money; high: Money };
}

interface ForecastFactor {
  factor: string;
  impact: number;                       // +5% or -3%
  confidence: number;
  description: string;
}

// ── Revenue forecast dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Revenue Forecast — Q2 2026 (Apr-Jun)                 │
// │                                                       │
// │  Method          | Forecast | Confidence              │
// │  ─────────────────────────────────────────────────── │
// │  Confirmed       | ₹28L     | 100%                   │
// │  Advanced pipe   | ₹15L     | 75%                    │
// │  Early pipe      | ₹22L     | 40%                    │
// │  Weighted pipe   | ₹52.3L   | —                      │
// │  Historical      | ₹48L     | 70%                    │
// │  ML Model        | ₹54L     | 82%                    │
// │  ─────────────────────────────────────────────────── │
// │  Blended         | ₹52L     | 78%                    │
// │  Range: ₹46L — ₹60L                                 │
// │                                                       │
// │  Key Factors:                                         │
// │  + Summer holiday demand (+18%)                      │
// │  + New corporate client (+₹4L)                       │
// │  - Goa vendor price increase (-3%)                   │
// │  - INR/SGD volatility (-2%)                          │
// └─────────────────────────────────────────────────────┘
```

### Seasonal Demand Model

```typescript
interface SeasonalDemandModel {
  destination: string;
  monthly_demand: {
    month: number;
    demand_index: number;               // 100 = average
    avg_deal_size: Money;
    conversion_rate: number;
    booking_lead_time_days: number;
  }[];

  // Festival impacts (India-specific)
  festival_impacts: {
    festival: string;
    month: number;
    demand_multiplier: number;          // 1.3 = 30% above normal
    price_elasticity: number;
  }[];
}

// ── India seasonal demand patterns ──
// ┌─────────────────────────────────────────────────────┐
// │  Seasonal Demand Index by Destination                 │
// │                                                       │
// │  Destination  | Peak    | Off     | Festival Bump    │
// │  ─────────────────────────────────────────────────── │
// │  Kerala       | Dec-Feb | Jun-Aug | Onam (Sep)      │
// │               | idx:150 | idx:60  | +40%             │
// │  Rajasthan    | Oct-Mar | Apr-Jun | Diwali (Nov)    │
// │               | idx:140 | idx:50  | +35%             │
// │  Goa          | Dec-Feb | Jun-Sep | New Year        │
// │               | idx:180 | idx:40  | +60%             │
// │  Kashmir      | Apr-Jun | Nov-Feb | —               │
// │               | idx:160 | idx:30  |                  │
// │  Singapore    | May-Jun | Sep-Oct | Diwali          │
// │               | idx:130 | idx:70  | +25%             │
// │  Dubai        | Nov-Feb | Jun-Aug | Eid             │
// │               | idx:150 | idx:50  | +20%             │
// │                                                       │
// │  Forecasting model inputs:                            │
// │  • Historical booking curves (3 years)               │
// │  • Lead time distribution per destination            │
// │  • Festival calendar shift (lunar vs solar)          │
// │  • Competitor pricing signals                        │
// │  • Weather patterns (monsoon timing)                 │
// └─────────────────────────────────────────────────────┘
```

### Cash Flow Forecasting

```typescript
interface CashFlowForecast {
  period_weeks: number;

  weekly_forecast: {
    week: string;                       // "2026-W18"
    opening_balance: Money;
    inflows: {
      advance_payments: Money;
      milestone_payments: Money;
      final_payments: Money;
      other_inflows: Money;
    };
    outflows: {
      vendor_advances: Money;
      vendor_final: Money;
      salaries: Money;
      rent: Money;
      tax_payments: Money;
      marketing: Money;
      other_outflows: Money;
    };
    closing_balance: Money;
    min_balance: Money;                 // lowest point in week
  }[];

  // Alerts
  deficit_weeks: string[];              // weeks where balance < threshold
  peak_requirement: Money;              // maximum cash needed
}

// ── Cash flow projection ──
// ┌─────────────────────────────────────────────────────┐
// │  Cash Flow Forecast — Next 12 Weeks                   │
// │                                                       │
// │  Week   | Balance | In     | Out    | Net     | Status│
// │  ─────────────────────────────────────────────────── │
// │  W18    | ₹18L   | ₹8.5L | ₹6.2L | +₹2.3L | ✅    │
// │  W19    | ₹20.3L | ₹7.2L | ₹5.8L | +₹1.4L | ✅    │
// │  W20    | ₹21.7L | ₹5.5L | ₹8.2L | -₹2.7L | ⚠️    │
// │  W21    | ₹19L   | ₹4.2L | ₹9.5L | -₹5.3L | 🔴    │
// │  W22    | ₹13.7L | ₹6.8L | ₹4.5L | +₹2.3L | ⚠️    │
// │  W23    | ₹16L   | ₹8.2L | ₹5.1L | +₹3.1L | ✅    │
// │  ...                                                  │
// │                                                       │
// │  ⚠️ Deficit risk in W21: Large vendor payments due   │
// │     mitigated by ₹4L corporate advance expected      │
// │                                                       │
// │  Summary:                                             │
// │  Opening: ₹18L → Closing: ₹22L (projected)          │
// │  Min balance: ₹13.7L (W22)                          │
// │  Safety threshold: ₹10L                              │
// └─────────────────────────────────────────────────────┘
```

### Budget vs Actual Tracking

```typescript
interface BudgetTracking {
  period: string;
  categories: {
    category: string;
    budget: Money;
    actual: Money;
    committed: Money;                    // contracted but not yet paid
    remaining: Money;
    variance: Money;
    variance_pct: number;
    status: "ON_TRACK" | "AT_RISK" | "OVER_BUDGET";
    forecast_total: Money;               // projected end-of-period
  }[];

  overall: {
    total_budget: Money;
    total_actual: Money;
    total_variance: Money;
    burn_rate: Money;                    // per month
    runway_months: number;               // months of budget remaining
  };
}

// ── Budget tracking view ──
// ┌─────────────────────────────────────────────────────┐
// │  Budget vs Actual — FY 2026-27 (as of Apr)           │
// │                                                       │
// │  Category      | Budget  | Actual  | Var%  | Status │
// │  ─────────────────────────────────────────────────── │
// │  Vendor costs  | ₹1.2Cr | ₹32L    | +2%   | ✅     │
// │  Salaries      | ₹48L   | ₹12L    |  0%   | ✅     │
// │  Rent          | ₹18L   | ₹4.5L   |  0%   | ✅     │
// │  Marketing     | ₹12L   | ₹5.8L   | +45%  | 🔴     │
// │  Technology    | ₹8L    | ₹2.2L    | +10%  | ⚠️    │
// │  Travel        | ₹3L    | ₹1.8L    | +80%  | 🔴     │
// │  Insurance     | ₹2L    | ₹0.5L    |  0%   | ✅     │
// │  ─────────────────────────────────────────────────── │
// │  TOTAL         | ₹2.11Cr| ₹58.8L  | +8%   | ⚠️    │
// │                                                       │
// │  Burn rate: ₹14.7L/month                             │
// │  Runway: 10.4 months of budget remaining             │
// │                                                       │
// │  🔴 Marketing: overspending on Google Ads             │
// │  🔴 Travel: unapproved client entertainment           │
// └─────────────────────────────────────────────────────┘
```

### Scenario Planning

```typescript
interface ScenarioPlan {
  scenario_name: string;
  assumptions: string[];

  financial_impact: {
    revenue_change: number;              // percentage
    margin_impact: number;
    cash_impact: Money;
    breakeven_shift_months: number;      // how much breakeven moves
  };

  probability: number;                  // 0-100%
  mitigation_actions: string[];
}

// ── Scenario planning ──
// ┌─────────────────────────────────────────────────────┐
// │  Scenario Planning — FY 2026-27                       │
// │                                                       │
// │  Scenario 1: Strong Summer (+15% demand)             │
// │  Probability: 60%                                    │
// │  Impact: Revenue +₹18L, Margin +2.1%                │
// │  Action: Pre-book vendor capacity, hire temp agents  │
// │                                                       │
// │  Scenario 2: Monsoon Disruption (-10% domestic)      │
// │  Probability: 35%                                    │
// │  Impact: Revenue -₹8L, push international packages  │
// │  Action: Increase international marketing, rain pkg  │
// │                                                       │
// │  Scenario 3: New Competitor Enters Market            │
// │  Probability: 25%                                    │
// │  Impact: Revenue -₹12L, Margin -3%                  │
// │  Action: Lock in corporate contracts, loyalty push   │
// │                                                       │
// │  Scenario 4: INR Depreciation 5% vs USD/SGD         │
// │  Probability: 30%                                    │
// │  Impact: Int'l costs +₹6L, margins compress         │
// │  Action: Hedging, price adjustments, local packages  │
// └─────────────────────────────────────────────────────┘
```

### India Tax Projection

```typescript
interface IndiaTaxProjection {
  financial_year: string;

  gst_projection: {
    projected_output_gst: Money;
    projected_input_gst: Money;
    projected_net_payable: Money;
    monthly_breakdown: {
      month: string;
      output: Money;
      input: Money;
      net: Money;
    }[];
  };

  tcs_projection: {
    projected_overseas_tcs: Money;
    threshold_applicable: Money;         // packages > ₹7L
    quarterly_deposits: Money[];
  };

  tds_projection: {
    projected_tds: Money;
    sections: {
      section: string;
      projected_amount: Money;
    }[];
  };

  advance_tax: {
    total_advance_tax: Money;
    due_dates: {
      date: string;                      // Jun 15, Sep 15, Dec 15, Mar 15
      percentage: number;                // 15%, 30%, 30%, 25%
      amount: Money;
    }[];
  };
}

// ── Tax projection view ──
// ┌─────────────────────────────────────────────────────┐
// │  India Tax Projection — FY 2026-27                    │
// │                                                       │
// │  GST (Annual Projection):                             │
// │  Output: ₹14.4L | Input: ₹7.2L | Net: ₹7.2L       │
// │  Monthly avg payable: ₹60K                           │
// │                                                       │
// │  TCS (Overseas Packages):                             │
// │  Projected collection: ₹4.8L                         │
// │  Quarterly deposits: ₹1.2L each                      │
// │                                                       │
// │  TDS (Vendor Payments):                               │
// │  Projected: ₹3.6L (§194C: ₹1.8L, §194H: ₹1.8L)   │
// │                                                       │
// │  Advance Tax Schedule:                                │
// │  Jun 15: ₹1.8L (15%)    Sep 15: ₹3.6L (30%)       │
// │  Dec 15: ₹3.6L (30%)    Mar 15: ₹3.0L (25%)       │
// │  Total: ₹12L                                         │
// │                                                       │
// │  Total tax outflow projected: ₹27.6L                 │
// │  Monthly tax budget needed: ₹2.3L                    │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Forecast accuracy** — Travel demand is highly elastic and affected by external shocks (pandemics, geopolitics, weather). No model captures all variables.

2. **Lead time uncertainty** — Bookings made 2-3 months in advance may be cancelled. Pipeline-weighted forecasts need to account for cancellation curves by destination and segment.

3. **Currency risk** — International bookings expose agencies to INR volatility. Forward contracts are available but add complexity and cost.

4. **Tax law changes** — India tax rules (GST rates, TCS thresholds) change with Union Budget (February). Forecasts must be re-run post-budget.

---

## Next Steps

- [ ] Build revenue forecasting engine with pipeline weighting
- [ ] Create seasonal demand model for Indian destinations
- [ ] Implement weekly cash flow forecasting
- [ ] Design budget vs actual tracking dashboard
- [ ] Build India tax projection calculator
- [ ] Create scenario planning sandbox
