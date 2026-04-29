# Customer Lifetime Value & Retention — CLV Modeling

> Research document for customer lifetime value calculation, segmentation by value, RFM analysis, and CLV-informed business decisions.

---

## Key Questions

1. **How do we calculate customer lifetime value for travel?**
2. **What segmentation models work for travel CLV?**
3. **How does CLV differ across customer segments?**
4. **How do we use CLV to inform acquisition spend?**

---

## Research Areas

### CLV Calculation Model

```typescript
interface CustomerLifetimeValue {
  customer_id: string;

  // Historical value
  historical: {
    total_trips: number;
    total_revenue: Money;
    total_margin: Money;
    avg_trip_value: Money;
    avg_margin_pct: number;
    first_trip_date: string;
    last_trip_date: string;
    relationship_years: number;
    annual_value: Money;
  };

  // Predictive CLV
  predicted: {
    clv_1_year: Money;                  // expected value next 12 months
    clv_3_year: Money;                  // expected value next 3 years
    clv_lifetime: Money;                // predicted total remaining value
    confidence: number;                 // 0-100%
    churn_probability: number;          // 0-1
    next_trip_probability_6mo: number;
    recommended_actions: string[];
  };

  // RFM Score
  rfm: {
    recency_days: number;               // days since last trip
    recency_score: number;              // 1-5 (5 = very recent)
    frequency: number;                  // trips per year
    frequency_score: number;            // 1-5
    monetary: Money;                    // total spend
    monetary_score: number;             // 1-5
    rfm_segment: string;                // "Champions", "At Risk", etc.
  };

  // Segment classification
  segment: {
    tier: "PLATINUM" | "GOLD" | "SILVER" | "BRONZE" | "CHURNED";
    segment_name: string;
    segment_description: string;
  };
}

// ── Customer CLV card ──
// ┌─────────────────────────────────────────────────────┐
// │  Customer Lifetime Value — Sharma Family               │
// │                                                       │
// │  Tier: 🥇 GOLD | Segment: Loyal Family Travelers     │
// │                                                       │
// │  Historical:                                          │
// │  • 8 trips in 3.2 years (2.5 trips/year)             │
// │  • Total spend: ₹18.5L | Total margin: ₹3.2L       │
// │  • Avg trip: ₹2.3L | Avg margin: 17.5%              │
// │  • Annual value: ₹5.8L                              │
// │                                                       │
// │  RFM: R=4 (45 days ago) F=5 (high) M=4 (high)       │
// │                                                       │
// │  Predicted CLV:                                       │
// │  • 1-year: ₹5.2L (88% confidence)                   │
// │  • 3-year: ₹14.8L                                   │
// │  • Lifetime: ₹28.5L                                 │
// │  • Churn probability: 12% (low)                      │
// │  • Next trip in 6 months: 78% likely                 │
// │                                                       │
// │  Recommended Actions:                                 │
// │  • Send Kerala monsoon offer (matches profile)       │
// │  • Upgrade pitch: try premium international (Dubai)  │
// │  • Referral program: ₹2K credit per referral        │
// └─────────────────────────────────────────────────────┘
```

### RFM Segmentation Matrix

```typescript
// ── RFM segments for travel agency ──
// ┌─────────────────────────────────────────────────────┐
// │  Customer Segments by RFM Score                        │
// │                                                       │
// │  Segment         | RFM    | Count | %Rev | Action    │
// │  ─────────────────────────────────────────────────── │
// │  Champions       | 555    | 45    | 28%  | Retain    │
// │  Loyal Family    | 545+   | 82    | 22%  | Upsell   │
// │  Recent Big      | 535    | 38    | 12%  | Nurture  │
// │  Frequent Budget | 425    | 65    | 10%  | Upsell   │
// │  Occasional      | 333    | 120   | 12%  | Activate │
// │  At Risk         | 254    | 55    | 8%   | Win-back │
// │  Hibernating     | 152    | 85    | 5%   | Reactivate│
// │  Lost            | 111    | 210   | 3%   | Ignore   │
// │                                                       │
// │  Strategy by segment:                                 │
// │  Champions: Personal concierge, first access to deals│
// │  Loyal: Exclusive offers, referral bonuses           │
// │  At Risk: Urgent win-back call, special discount     │
// │  Lost: Annual re-engagement email only               │
// └─────────────────────────────────────────────────────┘
```

### CLV-Based Acquisition Budget

```typescript
// ── Customer acquisition budget by CLV ──
// ┌─────────────────────────────────────────────────────┐
// │  Acquisition Budget Based on CLV                       │
// │                                                       │
// │  Channel     | Cost/Acq | Avg CLV | CLV/CAC | Budget │
// │  ─────────────────────────────────────────────────── │
// │  WhatsApp    | ₹800     | ₹8.5L   | 106x    | 40%   │
// │  Referral    | ₹1,200   | ₹12L    | 100x    | 25%   │
// │  Google Ads  | ₹2,500   | ₹6.2L   | 25x     | 20%   │
// │  Instagram   | ₹3,200   | ₹4.8L   | 15x     | 10%   │
// │  Walk-in     | ₹500     | ₹3.5L   | 70x     | 5%    │
// │                                                       │
// │  Key insight:                                         │
// │  • WhatsApp leads have highest ROI                    │
// │  • Referral customers have highest CLV               │
// │  • Google Ads are expensive but high volume           │
// │  • Reallocate 10% from Instagram to referral program │
// │                                                       │
// │  Max acceptable CAC by segment:                       │
// │  • Champions: ₹5,000 (high CLV justifies)            │
// │  • Loyal: ₹3,000                                     │
// │  • Budget: ₹800 (low margin, low acquisition spend)  │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Long purchase cycles** — Travel purchases are infrequent (1-3x/year). CLV models need longer observation windows than e-commerce.

2. **Group travel attribution** — One person books for a family. Who is the "customer"? The booker or the entire family unit?

3. **External factors** — CLV drops during pandemics, economic downturns, or when a customer moves abroad. Models must account for exogenous shocks.

4. **Privacy** — CLV scoring uses purchase history, demographics, and behavioral data. Must comply with India DPDP Act for data usage.

---

## Next Steps

- [ ] Build CLV calculation model with RFM scoring
- [ ] Create customer segmentation by CLV tier
- [ ] Implement CLV-based acquisition budget allocation
- [ ] Design CLV dashboard for agency owners
