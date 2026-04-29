# Agency Financial Dashboard — Profitability Analysis

> Research document for per-trip profitability, destination/agent/segment ranking, seasonal profit patterns, product mix optimization, and margin analysis.

---

## Key Questions

1. **How do we measure profitability at the trip level?**
2. **Which destinations, agents, and segments are most profitable?**
3. **How do seasonal patterns affect margins?**
4. **How do we optimize the product mix for maximum margin?**

---

## Research Areas

### Per-Trip Profitability

```typescript
interface TripProfitability {
  trip_id: string;
  enquiry_id: string;

  // Revenue breakdown
  total_revenue: Money;
  revenue_components: {
    flights: Money;
    hotels: Money;
    activities: Money;
    transport: Money;
    insurance: Money;
    visa: Money;
    markup: Money;
    service_fee: Money;
  };

  // Cost breakdown
  total_cost: Money;
  cost_components: {
    vendor_payments: Money;
    agent_commission: Money;
    payment_gateway_fees: Money;
    communication_costs: Money;
    support_costs: Money;
    overhead_allocation: Money;
  };

  // Margin analysis
  gross_margin: Money;
  gross_margin_pct: number;
  net_margin: Money;
  net_margin_pct: number;

  // Efficiency
  days_to_close: number;
  agent_hours: number;
  revenue_per_hour: Money;
  cost_per_traveler: Money;
  revenue_per_traveler: Money;

  // Benchmark
  vs_destination_avg: number;           // percentage vs avg for this destination
  vs_agent_avg: number;                 // percentage vs agent's own average
  profitability_grade: "A" | "B" | "C" | "D" | "F";
}

// ── Trip profitability card ──
// ┌─────────────────────────────────────────────────────┐
// │  Trip #WP-2026-0442 — Singapore Family Trip          │
// │                                                       │
// │  Revenue: ₹3,85,000                                   │
// │  ├── Flights:     ₹1,20,000 (markup ₹12,000)        │
// │  ├── Hotels:      ₹1,10,000 (markup ₹15,000)        │
// │  ├── Activities:  ₹65,000  (markup ₹8,000)          │
// │  ├── Transport:   ₹35,000  (markup ₹4,000)          │
// │  ├── Insurance:   ₹15,000  (markup ₹3,000)          │
// │  ├── Visa:        ₹10,000  (markup ₹2,000)          │
// │  └── Service fee: ₹30,000                            │
// │                                                       │
// │  Costs:   ₹3,02,000                                   │
// │  ├── Vendor payments:  ₹2,75,000                     │
// │  ├── Agent commission: ₹11,550 (3%)                  │
// │  ├── Gateway fees:     ₹4,620  (1.2%)                │
// │  └── Overhead:         ₹10,830                       │
// │                                                       │
// │  Gross Margin: ₹83,000 (21.6%)    Grade: B+         │
// │  Net Margin:   ₹58,000 (15.1%)    vs Destination: +3%│
// │  Revenue/traveler: ₹96,250      Revenue/hour: ₹9,625 │
// │  Days to close: 8                                    │
// └─────────────────────────────────────────────────────┘
```

### Destination Profitability Ranking

```typescript
interface DestinationProfitability {
  destination: string;
  period: string;

  // Volume
  trip_count: number;
  traveler_count: number;

  // Revenue
  total_revenue: Money;
  avg_deal_size: Money;

  // Profitability
  gross_margin: Money;
  gross_margin_pct: number;
  net_margin: Money;
  net_margin_pct: number;

  // Trends
  revenue_trend: number;                // +12% YoY
  margin_trend: number;                 // -2% (shrinking margins)
  volume_trend: number;

  // Risk
  cancellation_rate: number;
  payment_default_rate: number;
  vendor_reliability_score: number;

  rank: number;                         // profitability rank
}

// ── Destination profitability table ──
// ┌─────────────────────────────────────────────────────┐
// │  Destination Profitability — FY 2026 Q1               │
// │                                                       │
// │  Rank | Dest.    | Trips | Revenue | Margin% | Trend │
// │  ─────────────────────────────────────────────────── │
// │  1    | Dubai     | 58    | ₹29L   | 24.2%  | ↑ +4% │
// │  2    | Singapore | 65    | ₹32L   | 21.6%  | ↑ +3% │
// │  3    | Kerala    | 85    | ₹28L   | 19.8%  | →  0% │
// │  4    | Goa       | 55    | ₹14L   | 18.5%  | ↓ -2% │
// │  5    | Rajasthan | 72    | ₹24L   | 17.2%  | ↑ +1% │
// │  6    | Thailand  | 42    | ₹18L   | 16.8%  | ↓ -3% │
// │  7    | Kashmir   | 35    | ₹12L   | 14.5%  | →  0% │
// │                                                       │
// │  Insights:                                            │
// │  • International > domestic margin (22% vs 17%)       │
// │  • Goa margin shrinking: vendor costs rising          │
// │  • Thailand: currency risk eating margins             │
// └─────────────────────────────────────────────────────┘
```

### Agent Performance & Profitability

```typescript
interface AgentProfitability {
  agent_id: string;
  agent_name: string;
  period: string;

  // Volume
  trips_handled: number;
  trips_closed: number;
  conversion_rate: number;

  // Revenue
  total_revenue: Money;
  avg_deal_size: Money;

  // Profitability
  total_margin: Money;
  avg_margin_pct: number;

  // Efficiency
  avg_days_to_close: number;
  revenue_per_hour: Money;
  trips_per_day: number;

  // Quality
  customer_satisfaction: number;
  repeat_customer_rate: number;
  complaint_rate: number;

  // Commission
  commission_earned: Money;
  commission_rate: number;

  performance_tier: "PLATINUM" | "GOLD" | "SILVER" | "BRONZE";
}

// ── Agent leaderboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Agent Performance — April 2026                       │
// │                                                       │
// │  Tier   | Agent   | Revenue | Margin% | CSAT | Conv  │
// │  ─────────────────────────────────────────────────── │
// │  🥇 PLAT | Priya   | ₹18.2L | 24.5%  | 4.8  | 72%  │
// │  🥇 PLAT | Rahul   | ₹16.8L | 22.1%  | 4.7  | 68%  │
// │  🥈 GOLD | Anita   | ₹14.5L | 20.3%  | 4.6  | 65%  │
// │  🥈 GOLD | Vikram  | ₹12.8L | 19.8%  | 4.5  | 62%  │
// │  🥉 SILV | Deepa   | ₹10.2L | 18.5%  | 4.4  | 58%  │
// │  🥉 SILV | Arjun   | ₹9.5L  | 17.2%  | 4.3  | 55%  │
// │  🔔 BRON | Neha    | ₹7.8L  | 15.8%  | 4.1  | 48%  │
// │                                                       │
// │  Insights:                                            │
// │  • Priya excels at premium international (high margin)│
// │  • Rahul: highest conversion, great follow-up         │
// │  • Neha needs training: low conversion, low margin    │
// │  • Correlation: CSAT > 4.5 → margin > 20%            │
// └─────────────────────────────────────────────────────┘
```

### Segment Profitability

```typescript
interface SegmentProfitability {
  segment: string;
  trip_count: number;
  revenue: Money;
  margin: Money;
  margin_pct: number;
  avg_deal_size: Money;
  growth_rate: number;
}

// ── Segment analysis ──
// ┌─────────────────────────────────────────────────────┐
// │  Profitability by Customer Segment                    │
// │                                                       │
// │  Segment        | Trips | Revenue | Margin | Growth  │
// │  ─────────────────────────────────────────────────── │
// │  Corporate      | 45    | ₹42L   | 22%   | +18%    │
// │  Honeymoon      | 38    | ₹28L   | 24%   | +12%    │
// │  Family Premium | 52    | ₹35L   | 19%   | +8%     │
// │  Group Tours    | 85    | ₹22L   | 15%   | +5%     │
// │  Senior Citizen | 28    | ₹14L   | 17%   | +15%    │
// │  Budget         | 95    | ₹12L   | 12%   | +22%    │
// │  MICE           | 12    | ₹48L   | 20%   | +25%    │
// │                                                       │
// │  Strategy:                                            │
// │  • Double down on Corporate + MICE (high value)      │
// │  • Honeymoon: best margin, invest in packages        │
// │  • Budget: growing fast but low margin — automate    │
// └─────────────────────────────────────────────────────┘
```

### Seasonal Profit Patterns

```typescript
// ── Monthly margin heatmap ──
// ┌─────────────────────────────────────────────────────┐
// │  Seasonal Profitability Pattern (India)                │
// │                                                       │
// │  Month    | Revenue | Margin% | Demand Level | Notes │
// │  ─────────────────────────────────────────────────── │
// │  January  | ████████ | 20%   | HIGH         | New Yr │
// │  February | ██████   | 18%   | MODERATE     |        │
// │  March    | ██████   | 17%   | MODERATE     | Holi   │
// │  April    | ████████ | 21%   | HIGH         | Summer │
// │  May      | ██████████| 23%  | PEAK         | Summer │
// │  June     | ██████████| 22%  | PEAK         | Summer │
// │  July     | ██████   | 19%   | MODERATE     | Monsoon│
// │  August   | █████    | 16%   | LOW          | Monsoon│
// │  September| █████    | 15%   | LOW          | Slow   │
// │  October  | ███████  | 19%   | HIGH         | Navrtr │
// │  November | ████████ | 21%   | HIGH         | Diwali │
// │  December | ██████████| 24%  | PEAK         | Christ │
// │                                                       │
// │  Patterns:                                            │
// │  • Peak: Apr-Jun (summer holidays), Dec (year-end)   │
// │  • Low: Jul-Sep (monsoon, slow season)               │
// │  • Highest margins in peak: vendors locked in advance │
// │  • Festival bumps: Diwali +12%, Christmas +15%       │
// └─────────────────────────────────────────────────────┘
```

### Product Mix Optimization

```typescript
interface ProductMixAnalysis {
  product_type: string;
  current_revenue_share: number;         // percentage
  current_margin: number;
  recommended_share: number;
  recommended_margin: number;
  opportunity: "GROW" | "MAINTAIN" | "REDUCE";
  reasoning: string;
}

// ── Product mix recommendations ──
// ┌─────────────────────────────────────────────────────┐
// │  Product Mix Optimization                             │
// │                                                       │
// │  Product          | Share | Margin | Action          │
// │  ─────────────────────────────────────────────────── │
// │  Int'l Packages   | 35%   | 22%    | GROW → 42%    │
// │  Domestic Premium | 20%   | 19%    | MAINTAIN 20%  │
// │  Domestic Budget  | 25%   | 12%    | REDUCE → 18%  │
// │  Corporate/MICE   | 10%   | 20%    | GROW → 15%    │
// │  Ancillary*       | 10%   | 35%    | GROW → 15%    │
// │                                                       │
// │  *Ancillary = insurance, visa, forex, tours          │
// │                                                       │
// │  Projected impact (if recommendations adopted):      │
// │  • Revenue: +₹8L/month (+12%)                       │
// │  • Overall margin: 18% → 21%                        │
// │  • Higher-margin international share increases       │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Overhead allocation** — Distributing fixed costs (office rent, software, salaries) across individual trips is inherently imprecise. Activity-based costing is ideal but complex.

2. **Margin cannibalization** — Discounting budget packages may attract customers who would have booked premium anyway. Need counterfactual analysis.

3. **Agent gaming** — If agent commissions are margin-based, agents may push higher-margin products over customer-suited options. Need balanced incentive design.

4. **Multi-currency impact** — International trips have currency risk. INR depreciation between booking and vendor payment can wipe out margins.

---

## Next Steps

- [ ] Build per-trip profitability calculator
- [ ] Create destination/agent/segment ranking dashboards
- [ ] Implement seasonal margin analysis
- [ ] Design product mix optimization engine
- [ ] Build agent incentive alignment framework
