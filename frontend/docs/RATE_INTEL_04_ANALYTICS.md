# Supplier Rate Intelligence — Analytics & Rate Intelligence Dashboard

> Research document for the rate intelligence analytics dashboard, pricing trend analysis, supplier performance scoring, and the rate intelligence feedback loop for travel agencies.

---

## Key Questions

1. **What does the rate intelligence dashboard look like?**
2. **How do we analyze pricing trends across destinations and seasons?**
3. **How do we score supplier reliability and value?**
4. **What reports help management make pricing decisions?**

---

## Research Areas

### Rate Intelligence Dashboard

```typescript
interface RateIntelligenceDashboard {
  // Executive overview
  overview: {
    active_monitors: number;
    rate_alerts_today: number;
    avg_margin_this_month: number;
    margin_trend: "UP" | "STABLE" | "DOWN";
    contracts_expiring_30d: number;
    savings_from_rebooking: number;
    competitor_win_rate: number;
  };

  // Quick actions
  actions: {
    monitor_new_rate: boolean;
    check_parity: boolean;
    negotiate_contract: boolean;
    optimize_margins: boolean;
  };
}

// ── Rate intelligence dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Rate Intelligence — Dashboard Home                    │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │  24  │ │   3  │ │ 14.2%│ │ ₹68K │               │
// │  │Moni- │ │Alerts│ │Margin│ │Saved │               │
// │  │tors  │ │Today │ │This  │ │Re-  │               │
// │  │      │ │      │ │Month │ │book  │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │                                                       │
// │  ── Rate Alerts (3 today) ──                          │
// │  🔻 Taj Vivanta SGP: ₹8.5K → ₹7.2K (-15%)         │
// │  🔻 IndiGo DEL-SIN: ₹12.4K → ₹11.2K (-10%)        │
// │  🔺 MBS SGP: ₹18K → ₹21.5K (+19%) ⚠️              │
// │  [View All Alerts]                                    │
// │                                                       │
// │  ── Margin Trend ──                                   │
// │  18% ┤ ╭╮                                            │
// │  16% ┤╭╯╰╮                                           │
// │  14% ┤╯  ╰─╮╌╌╌╌ 14.2%                              │
// │  12% ┤      ╰╮                                       │
// │  10% ┤       ╰─╮                                     │
// │       ├──┬──┬──┬──┬──→                               │
// │       Jan Feb Mar Apr                                 │
// │                                                       │
// │  ── Contracts Expiring ──                             │
// │  ⚠️ Singapore DMC — 45 days (Nov 30)                 │
// │  ⚠️ Dubai Tourism — 60 days (Dec 15)                │
// │  ✅ Taj Hotels — 245 days (Dec 31)                   │
// │                                                       │
// │  ── Quick Actions ──                                  │
// │  [+ Monitor Rate] [Check Parity]                      │
// │  [Negotiate Contract] [Optimize Margins]              │
// └─────────────────────────────────────────────────────┘
```

### Pricing Trend Analysis

```typescript
interface PricingTrends {
  // Destination-level trends
  destination_trends: {
    destination: string;
    period: string;

    // Price indices
    hotel_price_index: number;           // 100 = baseline
    flight_price_index: number;
    package_price_index: number;

    // Trend direction
    overall_trend: "SURGING" | "RISING" | "STABLE" | "FALLING" | "DROPPING";
    trend_velocity: number;              // rate of change
    predicted_peak_date: string | null;
    predicted_trough_date: string | null;

    // Comparison
    vs_same_period_last_year: number;    // percentage change
    vs_competitor_average: number;
  }[];
}

// ── Destination pricing trends ──
// ┌─────────────────────────────────────────────────────┐
// │  Pricing Trends — Top Destinations                     │
// │  April 2026                                           │
// │                                                       │
// │  Destination    │ Hotel │ Flight │ Trend │ YoY        │
// │  ─────────────────────────────────────────────────── │
// │  Singapore      │ 112   │ 108    │ ↑ Rising│ +8%     │
// │  Dubai          │ 95    │ 102    │ → Stable│ +2%     │
// │  Thailand       │ 88    │ 94     │ ↓ Falling│ -6%    │
// │  Europe (Schengen)│135  │ 128    │ ↑↑ Surge│ +18%    │
// │  Kerala         │ 92    │ N/A    │ → Stable│ +1%     │
// │  Bali           │ 105   │ 110    │ ↑ Rising│ +12%    │
// │  Mauritius      │ 98    │ 96     │ → Stable│ -1%     │
// │                                                       │
// │  Key insights:                                        │
// │  • Europe surging due to Schengen visa changes        │
// │  • Thailand falling post-Songkran (seasonal)          │
// │  • Singapore rising ahead of Great Sale (Jun)         │
// │  • Book Thailand now for Jun travel (low prices)      │
// │  • Wait on Europe if possible (prices may stabilize)  │
// │                                                       │
// │  [View Destination Detail] [Export Report]             │
// └─────────────────────────────────────────────────────┘
```

### Supplier Performance Scorecard

```typescript
interface SupplierScorecard {
  supplier: string;

  // Overall score (weighted composite)
  overall_score: number;                 // 0-100
  tier: "GOLD" | "SILVER" | "BRONZE" | "AT_RISK";

  // Score dimensions
  dimensions: {
    pricing_competitiveness: number;     // vs market rates
    rate_stability: number;              // how often rates change
    availability_reliability: number;    // % of requests confirmed
    quality_consistency: number;         // customer satisfaction
    payment_terms: number;               // favorable payment schedules
    responsiveness: number;             // query response time
    cancellation_flexibility: number;    // cancellation terms
    allotment_reliability: number;       // % of allotment honored
  };

  // Risk indicators
  risks: {
    recent_price_increases: number;      // count in last 90 days
    availability_denials: number;
    quality_complaints: number;
    payment_term_changes: number;
    contract_renewal_uncertainty: "LOW" | "MEDIUM" | "HIGH";
  };
}

// ── Supplier scorecard ──
// ┌─────────────────────────────────────────────────────┐
// │  Supplier Scorecard — Taj Hotels                       │
// │  Tier: 🥇 GOLD · Score: 82/100                        │
// │                                                       │
// │  Dimensions:                                          │
// │  Pricing competitiveness  ████████████░░ 85/100       │
// │  Rate stability          ██████████░░░░░ 72/100       │
// │  Availability reliability █████████████░ 90/100       │
// │  Quality consistency     ████████████░░ 88/100        │
// │  Payment terms           ██████████░░░░░ 70/100       │
// │  Responsiveness          ███████████░░░ 78/100        │
// │  Cancellation flexibility████████░░░░░░░ 62/100       │
// │  Allotment reliability   █████████████░ 91/100        │
// │                                                       │
// │  Risk indicators:                                     │
// │  ⚠️ 2 price increases in last 90 days (+8% avg)       │
// │  ⚠️ Tightening cancellation terms (72h → 48h)        │
// │  ✅ No availability denials this quarter               │
// │  ✅ Zero quality complaints in 6 months                │
// │                                                       │
// │  Trend vs last quarter: ▼ -3 points                   │
// │  Primary concern: Price increases eroding margin      │
// │                                                       │
// │  Recommended actions:                                 │
// │  1. Lock 2027 contract at current rates before renewal│
// │  2. Negotiate 48h cancellation as standard            │
// │  3. Increase allotment by 5 rooms (91% utilization)   │
// │                                                       │
// │  [Negotiate] [View History] [Compare Suppliers]        │
// └─────────────────────────────────────────────────────┘
```

### Management Reports

```typescript
interface RateReports {
  // Monthly rate intelligence report
  monthly_report: {
    period: string;

    // Margin health
    margin_health: {
      overall_margin: number;
      by_destination: Record<string, number>;
      by_supplier: Record<string, number>;
      margin_leaks: { component: string; amount: number; reason: string }[];
    };

    // Rate intelligence actions
    actions_taken: {
      rebookings: number;                // trips rebooked at lower rates
      savings: number;                   // total saved
      margin_improvements: number;
      contract_renewals: number;
      new_contracts: number;
    };

    // Competitive position
    competitive: {
      win_rate: number;
      avg_price_position: string;
      market_share_estimate: number;
    };

    // Recommendations
    recommendations: string[];
  };
}

// ── Monthly rate intelligence report ──
// ┌─────────────────────────────────────────────────────┐
// │  Rate Intelligence Report — April 2026                 │
// │                                                       │
// │  EXECUTIVE SUMMARY                                    │
// │  • Overall margin: 14.2% (target: 15%)               │
// │  • Savings from rebooking: ₹68,000 (5 trips)         │
// │  • 3 contracts expiring in next 60 days               │
// │  • Win rate: 42% (up from 38% in March)              │
// │                                                       │
// │  MARGIN HEALTH                                        │
// │  Singapore:  16.2% ✅ (above target)                  │
// │  Dubai:      13.1% ⚠️ (below target)                  │
// │  Thailand:   15.8% ✅                                 │
// │  Europe:     11.2% 🔴 (significant margin leak)      │
// │  Kerala:     18.5% ✅ (best performer)                │
// │                                                       │
// │  TOP MARGIN LEAKS                                     │
// │  1. Europe packages: -₹45K due to dynamic flight costs│
// │  2. Dubai transfers: -₹12K from spot rates           │
// │  3. Singapore activities: -₹8K from ad-hoc bookings  │
// │                                                       │
// │  ACTIONS THIS MONTH                                    │
// │  • Rebooked 5 trips at lower hotel rates (-₹68K)     │
// │  • Renewed IndiGo corporate rate contract             │
// │  • Negotiated Singapore DMC: +4% margin improvement  │
// │                                                       │
// │  RECOMMENDATIONS                                      │
// │  1. Lock Europe flight contracts before summer surge  │
// │  2. Switch Dubai transfer to contracted DMC           │
// │  3. Pre-book Singapore activities for Jun batch       │
// │  4. Target 15% margin for May (focus on Dubai)        │
// │                                                       │
// │  [Export PDF] [Share with Team] [Schedule Review]      │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Rate data normalization** — Different suppliers quote in different currencies, with different inclusions, for different room types. Normalizing to a comparable "per-night-per-person" metric requires careful mapping.

2. **Predictive pricing accuracy** — Historical rate patterns don't always predict future rates (COVID, geopolitical events, airline route changes). Predictions need confidence intervals and regular recalibration.

3. **Supplier scorecard subjectivity** — Some dimensions (quality consistency, responsiveness) are inherently subjective. Need structured feedback collection tied to specific trips.

4. **Report fatigue** — Monthly reports may go unread. Need exception-based reporting: only surface what requires action, with threshold-based alerts.

---

## Next Steps

- [ ] Build rate intelligence dashboard with monitoring and alerts
- [ ] Create pricing trend analysis with destination-level insights
- [ ] Implement supplier performance scorecard with tier system
- [ ] Design monthly management report with actionable recommendations
