# Travel Itinerary Optimization — Cost Optimization

> Research document for budget-aware itinerary planning, cost modeling, dynamic pricing integration, margin optimization, and cost comparison engines.

---

## Key Questions

1. **How do we optimize itineraries within budget constraints?**
2. **What cost models drive accurate pricing estimates?**
3. **How do we integrate real-time pricing from vendors?**
4. **How do we balance customer value with agency profitability?**

---

## Research Areas

### Cost Modeling Architecture

```typescript
interface CostModel {
  // Per-component cost estimation
  estimateFlight(from: string, to: string, dates: DateRange, pax: number): FlightCost;
  estimateHotel(destination: string, dates: DateRange, rooms: number, tier: HotelTier): HotelCost;
  estimateActivity(destination: string, activity: string, pax: number): ActivityCost;
  estimateTransport(from: string, to: string, mode: TransportMode, pax: number): TransportCost;
  estimateMeals(destination: string, days: number, meal_plan: MealPlan, pax: number): MealCost;

  // Total trip cost
  estimateTotal(components: CostComponent[]): TripCostBreakdown;
}

interface TripCostBreakdown {
  components: {
    flights: Money;
    hotels: Money;
    activities: Money;
    transport: Money;
    meals: Money;
    guides: Money;
    insurance: Money;
    visa: Money;
    miscellaneous: Money;
  };
  subtotal: Money;
  taxes: Money;
  service_fee: Money;
  total_customer_price: Money;
  total_vendor_cost: Money;
  agency_margin: Money;
  margin_percentage: number;
}

// ── Cost breakdown example ──
// ┌─────────────────────────────────────────────────────┐
// │  Singapore 5N/6D — Couple (March 2026)              │
// │                                                       │
// │  Component    │ Vendor Cost │ Markup │ Customer Price │
// │  ─────────────────────────────────────────────────── │
// │  Flights      │ ₹32,000    │ 15%    │ ₹36,800       │
// │  Hotel (5N)   │ ₹45,000    │ 20%    │ ₹54,000       │
// │  Activities   │ ₹12,000    │ 25%    │ ₹15,000       │
// │  Transport    │ ₹8,000     │ 20%    │ ₹9,600        │
// │  Meals (6D)   │ ₹18,000    │ 10%    │ ₹19,800       │
// │  Insurance    │ ₹2,500     │ 30%    │ ₹3,250        │
// │  Visa         │ ₹1,500     │ 50%    │ ₹2,250        │
// │  ─────────────────────────────────────────────────── │
// │  TOTAL        │ ₹1,19,000  │ 17.6%  │ ₹1,40,700     │
// │                                                       │
// │  Agency margin: ₹21,700 (17.6%)                      │
// │  Target margin: 15-20%                                │
// │  ✅ Within target range                               │
// └─────────────────────────────────────────────────────┘
```

### Budget Constraint Optimization

```typescript
interface BudgetOptimizer {
  optimizeWithinBudget(
    preferences: TripPreferences,
    budget: BudgetConstraint
  ): BudgetOptimizedItinerary[];

  findSavings(current: TripCostBreakdown, target_budget: Money): CostSaving[];
}

interface BudgetConstraint {
  max_budget: Money;
  priority: ("DESTINATION" | "HOTEL_QUALITY" | "ACTIVITIES" | "FLIGHTS" | "DURATION")[];
  flexible_areas: string[];            // where to cut costs
  non_negotiable: string[];            // must-haves
}

interface CostSaving {
  component: string;
  current_cost: Money;
  alternative_cost: Money;
  saving: Money;
  trade_off: string;                   // "3-star instead of 4-star hotel"
  impact: "MINIMAL" | "MODERATE" | "SIGNIFICANT";
  recommendation: string;
}

// ── Budget optimization strategies ──
// ┌─────────────────────────────────────────┐
// │  Strategy         | Saving   | Trade-off │
// │  ─────────────────────────────────────── │
// │  Downgrade hotel  | 20-40%   | Lower tier│
// │  Off-peak flights | 15-30%   | Red-eye   │
// │  Skip paid tours  | 10-20%   | Self-guide│
// │  Local restaurants| 30-50%   | No luxury │
// │  Public transport | 40-60%   | No private│
// │  Shorter trip     | ~15%/day | Less time │
// │  Shoulder season  | 20-35%   | Not peak  │
// │  Group discount   | 10-15%   | Group size│
// └───────────────────────────────────────────┘

// Example: Kerala trip over budget by ₹15,000
// ┌─────────────────────────────────────────────────────┐
// │  Current: ₹1,35,000  Target: ₹1,20,000              │
// │                                                       │
// │  Savings found:                                       │
// │  1. Hotel 4★→3★ (Munnar): -₹5,000                   │
// │  2. Skip houseboat premium → standard: -₹4,000       │
// │  3. Local restaurants (2 meals): -₹3,000             │
// │  4. Shared transport Alleppey→Kochi: -₹2,500         │
// │  5. Remove paid Kathakali show: -₹1,500              │
// │                                                       │
// │  Total savings: ₹16,000                              │
// │  New total: ₹1,19,000 ✅                             │
// │  Impact: MODERATE (hotel downgrade is main change)   │
// └─────────────────────────────────────────────────────┘
```

### Dynamic Pricing Integration

```typescript
interface DynamicPricingEngine {
  getRealTimePrice(query: PricingQuery): PriceQuote;
  trackPrices(query: PricingQuery, callback: PriceChangeCallback): PriceTracker;
  forecastTrends(query: PricingQuery): PriceForecast;
}

interface PricingQuery {
  type: "FLIGHT" | "HOTEL" | "ACTIVITY";
  origin?: string;
  destination: string;
  dates: DateRange;
  pax: number;
  tier?: string;
}

interface PriceQuote {
  current_price: Money;
  historical_low: Money;
  historical_high: Money;
  percentile_rank: number;             // 0-100 (100 = most expensive)
  recommendation: "BOOK_NOW" | "WAIT" | "MONITOR";
  reasoning: string;
  valid_until: string;
  source: string;
}

interface PriceForecast {
  trend: "RISING" | "FALLING" | "STABLE" | "VOLATILE";
  predicted_low: { price: Money; likely_date: string };
  confidence: number;
}

// ── Price tracking dashboard ──
// ┌─────────────────────────────────────────┐
// │  Price Alert: Delhi → Singapore          │
// │  Travel: May 15-20, 2026                │
// │                                           │
// │  Current: ₹28,500 (round trip)           │
// │  30-day low: ₹22,100                     │
// │  30-day high: ₹35,800                    │
// │                                           │
// │  ████████████░░░░░░░░ 62nd percentile    │
// │                                           │
// │  Recommendation: WAIT                     │
// │  "Historically drops 15% in April"       │
// │  Alert set for < ₹25,000                 │
// └───────────────────────────────────────────┘
```

### Margin Optimization

```typescript
interface MarginOptimizer {
  optimizeMargin(
    cost_breakdown: TripCostBreakdown,
    constraints: MarginConstraints
  ): MarginOptimizedBreakdown;
}

interface MarginConstraints {
  min_margin_percentage: number;       // agency minimum
  max_customer_price: Money;           // market ceiling
  competitive_position: "BUDGET" | "MID" | "PREMIUM";
  component_markups: Record<string, { min: number; max: number }>;
}

// ── Component markup ranges (Indian market) ──
// ┌─────────────────────────────────────────┐
// │  Component    | Min Markup | Max Markup  │
// │  ─────────────────────────────────────── │
// │  Flights      | 3-5%       | 10-15%     │
// │  Hotels       | 10-15%     | 25-35%     │
// │  Activities   | 15-20%     | 30-50%     │
// │  Transport    | 10-15%     | 25-30%     │
// │  Insurance    | 20-25%     | 40-50%     │
// │  Visa         | 30-40%     | 50-100%    │
// │  Packages     | 15-20%     | 25-35%     │
// │                                           │
// │  Total trip target: 15-25% margin        │
// │  Luxury trips: 25-35% margin             │
// │  Budget trips: 10-15% margin             │
// └───────────────────────────────────────────┘
```

---

## Open Problems

1. **Hidden costs** — GST, TCS, service tax, payment gateway fees, and currency conversion margins are often missed in initial estimates. Need comprehensive cost modeling.

2. **Price volatility** — Flight and hotel prices can change multiple times daily. Quotes are only valid for minutes to hours. Need price locking or guaranteed pricing windows.

3. **Margin transparency** — Indian customers increasingly compare prices online. High margins are easily discovered, eroding trust. Need value-add justification for markups.

4. **Competitive pricing data** — Competitor pricing (MakeMyTrip, Goibibo, SOTC) is needed for positioning but hard to obtain at scale. Need web scraping or pricing intelligence APIs.

---

## Next Steps

- [ ] Build comprehensive cost modeling engine with all tax/fee components
- [ ] Implement budget constraint optimizer with trade-off suggestions
- [ ] Create dynamic pricing integration with alert system
- [ ] Design margin optimization engine with competitive positioning
- [ ] Study Indian travel market pricing patterns and seasonal trends
