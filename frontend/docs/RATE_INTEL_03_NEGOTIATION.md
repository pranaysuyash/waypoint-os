# Supplier Rate Intelligence — Supplier Negotiation & Margin Optimization

> Research document for supplier rate negotiation intelligence, margin optimization strategies, B2B rate management, and contract tracking for travel agencies.

---

## Key Questions

1. **How do we track and optimize supplier margins?**
2. **What data supports supplier negotiations?**
3. **How do B2B rate contracts work and when to renegotiate?**
4. **What margin levers can agencies pull without affecting quality?**

---

## Research Areas

### Margin Analysis Engine

```typescript
interface MarginAnalyzer {
  // Per-trip margin breakdown
  trip_margin: {
    trip_id: string;
    destination: string;
    total_revenue: number;

    components: {
      name: string;                      // "Taj Vivanta 5N"
      type: "HOTEL" | "FLIGHT" | "ACTIVITY" | "TRANSFER" | "VISA" | "INSURANCE" | "MEAL" | "GUIDE";
      cost_to_agency: number;
      charged_to_customer: number;
      margin: number;
      margin_percentage: number;
      supplier: string;
      rate_type: "CONTRACTED" | "SPOT" | "DYNAMIC" | "PACKAGE";
    }[];

    total_cost: number;
    total_margin: number;
    overall_margin_percentage: number;
  };

  // Margin benchmarks
  benchmarks: {
    by_component_type: Record<string, {
      agency_avg: number;
      industry_avg: number;
      best_performed: number;
    }>;
  };
}

// ── Margin analysis per trip ──
// ┌─────────────────────────────────────────────────────┐
// │  Margin Analysis — WP-442 Sharma Singapore             │
// │                                                       │
// │  Revenue: ₹1,85,000 · Margin: ₹24,200 (13.1%)        │
// │                                                       │
// │  Component breakdown:                                 │
// │  ┌────────────────────────────────────────────────┐  │
// │  │ Component    │ Cost    │ Price  │ Margin │ %    │  │
// │  │ ───────────────────────────────────────────────│  │
// │  │ Flights (4)  │ ₹62,000 │₹72,000 │₹10,000│16.1%│  │
// │  │ Hotel (5N)   │ ₹35,000 │₹42,000 │ ₹7,000│20.0%│  │
// │  │ Activities   │ ₹18,000 │₹22,000 │ ₹4,000│22.2%│  │
// │  │ Transfers    │ ₹8,500  │₹10,000 │ ₹1,500│17.6%│  │
// │  │ Visa (4)     │ ₹12,000 │₹15,000 │ ₹3,000│25.0%│  │
// │  │ Insurance    │ ₹4,800  │ ₹6,000 │ ₹1,200│25.0%│  │
// │  │ Meals        │ ₹14,000 │₹12,000 │-₹2,000│-14.3%│  │
// │  │ Guide        │ ₹6,500  │ ₹6,000 │ -₹500 │-7.7%│  │
// │  │ ───────────────────────────────────────────────│  │
// │  │ TOTAL        │₹1,60,800│₹1,85,000│₹24,200│13.1%│  │
// │  └────────────────────────────────────────────────┘  │
// │                                                       │
// │  Issues flagged:                                     │
// │  ⚠️ Meals: negative margin (-₹2,000)                 │
// │     → Underpriced meal plan. Increase by ₹2K or      │
// │       remove from package.                           │
// │  ⚠️ Guide: negative margin (-₹500)                    │
// │     → Guide cost exceeds charge. Renegotiate or      │
// │       increase guide fee.                            │
// │                                                       │
// │  vs. benchmarks:                                     │
// │  Hotel margin: 20% (avg 18%) ✅ Above average         │
// │  Flight margin: 16.1% (avg 12%) ✅ Strong              │
// │  Activity margin: 22.2% (avg 25%) ⚠️ Below average    │
// │                                                       │
// │  [Optimize Margins] [Export Report] [Compare Similar]  │
// └─────────────────────────────────────────────────────┘
```

### Supplier Negotiation Intelligence

```typescript
interface NegotiationIntel {
  supplier: string;
  supplier_type: "HOTEL_CHAIN" | "AIRLINE" | "DMC" | "WHOLESALER" | "ACTIVITY_PROVIDER";

  // Negotiation leverage data
  leverage: {
    // Volume leverage
    annual_bookings: number;              // trips booked with this supplier
    annual_revenue_to_supplier: number;   // how much business we give them
    growth_rate: number;                  // year-over-year growth
    market_share_of_their_business: number; // how important are we to them

    // Performance leverage
    on_time_payment_rate: number;         // % of invoices paid on time
    cancellation_rate: number;            // how often we cancel on them
    complaint_rate: number;               // how often customers complain

    // Competitive leverage
    alternative_suppliers: {
      name: string;
      comparable_quality: boolean;
      price_difference: number;           // what we'd pay alternatively
      switching_cost: "LOW" | "MEDIUM" | "HIGH";
    }[];
  };

  // Negotiation recommendations
  recommendations: {
    ask: string;                          // "15% discount on 2026 contract"
    justification: string;
    fallback: string;
    walk_away_point: string;
    timing: string;                       // "Best time: Oct-Nov for 2026 contracts"
  }[];
}

// ── Negotiation brief ──
// ┌─────────────────────────────────────────────────────┐
// │  Negotiation Brief — Taj Hotels 2026 Contract          │
// │                                                       │
// │  Your leverage:                                      │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Metric              │ Value      │ Rating     │   │
// │  │ ───────────────────────────────────────────── │   │
// │  │ Annual bookings     │ 48 trips   │ ●●●○ Medium│   │
// │  │ Revenue to Taj      │ ₹24L/year  │ ●●●● Strong│   │
// │  │ Growth rate         │ +32% YoY   │ ●●●● Strong│   │
// │  │ Payment reliability │ 98% on-time│ ●●●● Strong│   │
// │  │ Cancellation rate   │ 4%         │ ●●●● Low   │   │
// │  │ Your % of Taj biz   │ ~0.5%      │ ●○○○ Weak  │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Alternatives ready:                                  │
// │  • Shangri-La: comparable, +₹800/night               │
// │  • Pan Pacific: comparable, -₹200/night              │
// │  • Hilton: slightly lower, -₹1,200/night             │
// │                                                       │
// │  Recommended asks (priority order):                   │
// │  1. Contracted rate: 12% below rack (current: 8%)    │
// │     Justification: 32% growth + volume commitment    │
// │     Fallback: 10% below rack                         │
// │                                                       │
// │  2. Free cancellation: 48h (current: 72h paid)       │
// │     Justification: Low cancellation rate (4%)        │
// │     Fallback: 72h with 50% refund                    │
// │                                                       │
// │  3. Upgrade vouchers: 2 per quarter for VIP clients  │
// │     Justification: High-value customer acquisition   │
// │     Fallback: 1 per quarter                          │
// │                                                       │
// │  Best timing: October 2026 for 2027 contracts        │
// │  [Schedule Negotiation] [Export Brief]                 │
// └─────────────────────────────────────────────────────┘
```

### B2B Rate Contract Management

```typescript
interface RateContract {
  contract_id: string;
  supplier: string;
  valid_from: string;
  valid_until: string;

  // Contracted rates
  rates: {
    product: string;                     // "Taj Vivanta Delhi, Deluxe, CP"
    season: "PEAK" | "HIGH" | "SHOULDER" | "LOW";
    contracted_rate: number;
    rack_rate: number;
    discount_percentage: number;
    allotment: number | null;            // guaranteed rooms/seats
    release_period: string;              // "48h before check-in"
    cancellation_terms: string;
    meal_plan_included: string;
    blackout_dates: string[];
  }[];

  // Performance tracking
  performance: {
    utilization_rate: number;            // % of allotment used
    revenue_generated: number;
    bookings_fulfilled: number;
    bookings_denied: number;             // sold out when we needed
    avg_margin_achieved: number;
  };

  // Renewal intelligence
  renewal: {
    days_until_expiry: number;
    market_rate_vs_contract: number;     // are we above or below market?
    renegotiation_recommended: boolean;
    historical_performance: "IMPROVING" | "STABLE" | "DECLINING";
  };
}

// ── Contract management dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  B2B Rate Contracts — Overview                         │
// │                                                       │
// │  Active contracts: 18 · Expiring soon: 3             │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Taj Hotels · 2026 Contract                     │   │
// │  │ Valid: Jan 1 - Dec 31, 2026                   │   │
// │  │ Properties: 12 · Rates: 48                    │   │
// │  │ Utilization: 72% · Revenue: ₹18.2L           │   │
// │  │ vs. Market: -8% (good deal) ✅                 │   │
// │  │ [View Details] [Renewals]                      │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ IndiGo Airlines · Corporate Rate               │   │
// │  │ Valid: Apr 1, 2026 - Mar 31, 2027             │   │
// │  │ Routes: 8 · Discount: 12% off published       │   │
// │  │ Utilization: 45% · Revenue: ₹8.5L            │   │
// │  │ vs. Market: -5% (OK deal) ⚠️                   │   │
// │  │ [View Details] [Renegotiate]                   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ⚠️ Expiring in 60 days:                              │
// │  • Singapore DMC (Nov 30) — start renegotiation      │
// │  • Dubai Tourism Board allotment (Dec 15)            │
// │  • Insurance aggregator contract (Dec 31)            │
// │                                                       │
// │  [Add Contract] [Bulk Renew] [Calendar View]          │
// └─────────────────────────────────────────────────────┘
```

### Margin Optimization Strategies

```typescript
interface MarginOptimization {
  // Automated margin improvement suggestions
  suggestions: {
    trip_id: string;
    current_margin: number;
    optimizations: {
      type: "SWITCH_SUPPLIER" | "ADJUST_PRICING" | "REMOVE_COMPONENT" | "ADD_UPSELL" | "BUNDLE";
      description: string;
      margin_impact: number;
      quality_impact: "NONE" | "MINIMAL" | "MODERATE";
      effort: "LOW" | "MEDIUM" | "HIGH";
      automated: boolean;
    }[];
  };
}

// ── Margin optimization suggestions ──
// ┌─────────────────────────────────────────────────────┐
// │  Margin Optimization — Suggested Actions                │
// │                                                       │
// │  High-impact, low-effort:                             │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 💡 Switch: Pan Pacific instead of Taj Vivanta  │   │
// │  │    Save: ₹1,200/night × 5N = ₹6,000          │   │
// │  │    Quality: Similar (4.3 vs 4.4 rating)       │   │
// │  │    Effort: LOW (auto-switch)                   │   │
// │  │    [Apply] [Keep Taj]                           │   │
// │  │                                               │   │
// │  │ 💡 Add: Airport lounge access (₹1,500/pax)     │   │
// │  │    Cost: ₹800/pax · Charge: ₹1,500/pax        │   │
// │  │    Margin: +₹2,800 (4 pax)                    │   │
// │  │    Customer value: HIGH (perceived premium)    │   │
// │  │    [Add to Package] [Skip]                      │   │
// │  │                                               │   │
// │  │ 💡 Bundle: Travel insurance + Visa assistance  │   │
// │  │    Current: separate line items                │   │
// │  │    Bundled price: ₹18,000 (vs ₹19,000 sep)    │   │
// │  │    Margin: +₹800 (volume discount from vendor)│   │
// │  │    [Bundle] [Keep Separate]                     │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Total potential margin improvement: +₹9,600          │
// │  New margin: ₹33,800 (18.3% vs current 13.1%)        │
// │                                                       │
// │  [Apply All Safe] [Review Each] [Dismiss]             │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Supplier data silos** — Each supplier has different rate formats, update frequencies, and API capabilities. Building a unified rate model requires significant normalization effort.

2. **Margin vs. customer experience** — Switching suppliers for margin may reduce quality. Need quality-scored alternatives so margin optimization doesn't sacrifice customer satisfaction.

3. **Contract renewal timing** — Renegotiating too early means missing last-minute deals; too late means losing contracted rates. Need data-driven renewal calendar.

4. **Allotment utilization** — Guaranteed allotments that go unused represent lost margin (some suppliers charge for unused allotment). Need demand forecasting to optimize allotment sizing.

---

## Next Steps

- [ ] Build margin analysis engine with per-component breakdown
- [ ] Create supplier negotiation intelligence with leverage scoring
- [ ] Implement B2B rate contract management with renewal alerts
- [ ] Design automated margin optimization suggestions
