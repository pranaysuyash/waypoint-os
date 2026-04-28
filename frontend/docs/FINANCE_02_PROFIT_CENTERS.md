# Travel Finance & Accounting — Profit Center Tracking

> Research document for per-trip profitability, customer-level margins, service-line analysis, and revenue attribution.

---

## Key Questions

1. **How do we track profitability per trip, per customer, per service?**
2. **What's the margin structure for different travel services?**
3. **How do we allocate indirect costs to trips?**
4. **What revenue attribution model handles multi-agent contributions?**
5. **How do we identify unprofitable bookings and why they occur?**

---

## Research Areas

### Per-Trip Profitability

```typescript
interface TripProfitability {
  tripId: string;
  bookingId: string;
  revenue: TripRevenue;
  costs: TripCosts;
  margins: TripMargins;
  profitability: ProfitabilityAnalysis;
}

interface TripRevenue {
  packagePrice: Money;                // What customer paid (excl. GST)
  addons: Money;                      // Extra activities, upgrades
  insuranceCommission: Money;
  forexCommission: Money;
  cancellationFeeIncome: Money;       // If applicable
  totalRevenue: Money;
}

interface TripCosts {
  directCosts: DirectCost[];
  allocatedCosts: AllocatedCost[];
  totalCosts: Money;
}

interface DirectCost {
  component: string;                  // "Hotel", "Flight", "Transfer"
  supplier: string;
  baseCost: Money;
  gst: Money;
  markup: Money;                      // Agency markup on this component
  commission: Money;                  // Commission received from supplier
  netCost: Money;                     // baseCost + gst - commission
}

// Per-trip P&L example:
// Kerala Backwaters Tour — TRV-45678
// Customer: Rajesh Sharma (2 adults)
//
// REVENUE:
//   Package price (net of GST):      ₹52,381
//   Travel insurance commission:      ₹1,200
//   Total Revenue:                    ₹53,581
//
// DIRECT COSTS:
//   Hotels (3 nights):               ₹18,000
//   Houseboat (2 nights):            ₹10,500
//   Flights (Delhi-Cochin-Delhi):    ₹14,200
//   Transfers (airport, local):       ₹4,500
//   Activities (sightseeing):         ₹3,000
//   Total Direct Costs:              ₹50,200
//
// GROSS PROFIT:                       ₹3,381
// Gross Margin:                        6.3%
//
// ALLOCATED COSTS (per-trip share):
//   Agent salary allocation:           ₹800
//   Office overhead allocation:        ₹400
//   Technology/platform fee:           ₹250
//   Marketing acquisition cost:        ₹500
//   Total Allocated:                 ₹1,950
//
// NET PROFIT:                         ₹1,431
// Net Margin:                          2.7%
//
// This is a LOW margin trip. Industry target: 8-15% net margin.
// Issue: Flight costs are high (direct airline booking, no commission).
// Recommendation: Use consolidator fare or negotiate group rate.

// Margin by service type (industry benchmarks):
//
// Domestic Tour Packages:     8-15% margin
// International Tour Packages: 10-20% margin
// Flight Tickets (BSP):        3-7% commission
// Hotel Bookings:             10-25% commission
// Visa Processing:            15-30% margin
// Travel Insurance:           15-25% commission
// Forex Services:              1-3% margin (volume-based)
// Car Rentals:                 8-15% commission
// Activities & Experiences:   10-20% commission
//
// Key insight: Package tours and visa services have highest margins.
// Flight ticketing has lowest margins but highest volume.
// A healthy agency has 60% revenue from packages, 30% from tickets,
// 10% from ancillary services.
```

### Customer-Level Profitability

```typescript
interface CustomerProfitability {
  customerId: string;
  lifetime: CustomerLifetime;
  trips: CustomerTripProfit[];
  segments: ProfitSegment;
  ltv: CustomerLTV;
}

interface CustomerLifetime {
  firstBookingDate: Date;
  totalTrips: number;
  totalRevenue: Money;
  totalCost: Money;
  totalProfit: Money;
  avgMarginPercent: number;
  retentionRate: number;
}

interface CustomerLTV {
  historicalValue: Money;             // Profit earned so far
  projectedValue: Money;              // Projected future profit
  projectedTrips: number;             // Expected future bookings
  paybackPeriod: string;              // Time to recoup acquisition cost
  cac: Money;                         // Customer Acquisition Cost
  ltvCacRatio: number;                // Target: > 3:1
}

// Customer profitability segmentation:
//
// Segment: Premium Loyal
//   Trips: 5+ per year
//   Avg margin: 15-20%
//   LTV: ₹3-5 lakh
//   CAC: ₹5,000
//   LTV:CAC = 60-100x (excellent)
//   Strategy: Dedicated agent, priority service, exclusive offers
//
// Segment: Regular Traveler
//   Trips: 2-3 per year
//   Avg margin: 10-15%
//   LTV: ₹1-2 lakh
//   CAC: ₹3,000
//   LTV:CAC = 30-70x (good)
//   Strategy: Cross-sell higher-margin services, upsell packages
//
// Segment: Occasional
//   Trips: 1 per year
//   Avg margin: 8-12%
//   LTV: ₹30,000-80,000
//   CAC: ₹2,000
//   LTV:CAC = 15-40x (acceptable)
//   Strategy: Nurture with content, increase frequency
//
// Segment: One-Time / Price Shopper
//   Trips: 1 (may not return)
//   Avg margin: 3-8%
//   LTV: ₹5,000-20,000
//   CAC: ₹3,000
//   LTV:CAC = 2-7x (marginal)
//   Strategy: Automated follow-up, referral incentive
//
// Segment: Unprofitable
//   High cancellation rate, excessive support requests
//   Margin: Negative
//   Strategy: Price floor, minimum booking value, or graceful exit

// Customer profitability dashboard:
// ┌──────────────────────────────────────────┐
// │  Customer Profitability — Rajesh Sharma   │
// │                                          │
// │  Lifetime Value: ₹1,85,000              │
// │  Total Trips: 4 (1 domestic, 3 intl)    │
// │  Avg Margin: 14.2%                       │
// │  Segment: Regular Traveler               │
// │                                          │
// │  Trip History:                            │
// │  1. Singapore (2024) — ₹42K — 16% margin │
// │  2. Kerala (2025) — ₹55K — 6% margin ⚠️ │
// │  3. Thailand (2025) — ₹38K — 18% margin  │
// │  4. Dubai (2026) — ₹62K — 13% margin     │
// │                                          │
// │  Insight: Kerala trip had low margin      │
// │  due to direct flight booking.            │
// │  Recommendation: Offer package deal next. │
// │                                          │
// │  Next Best Action:                        │
// │  → Plan honeymoon package referral        │
// │    (customer mentioned family planning)   │
// └──────────────────────────────────────────┘
```

### Cost Allocation Model

```typescript
interface CostAllocation {
  model: AllocationModel;
  pools: CostPool[];
  drivers: AllocationDriver[];
  rules: AllocationRule[];
}

interface CostPool {
  poolId: string;
  name: string;                       // "Office Rent", "Staff Salaries"
  totalCost: Money;
  period: string;                     // "2026-04"
  allocationBase: string;             // "trip_count", "revenue", "time_spent"
}

// Indirect cost allocation methods:
//
// 1. Per-Trip Allocation (simplest):
//    Total overhead: ₹2,00,000/month
//    Trips completed: 50
//    Overhead per trip: ₹4,000
//    Pros: Simple, easy to calculate
//    Cons: Penalizes high-volume months
//
// 2. Revenue-Based Allocation:
//    Total overhead: ₹2,00,000/month
//    Total revenue: ₹20,00,000
//    Overhead rate: 10% of revenue
//    Trip with ₹55K revenue: ₹5,500 overhead allocation
//    Pros: Proportional to business value
//    Cons: Penalizes premium trips
//
// 3. Time-Based Allocation:
//    Track agent hours per trip
//    Allocate costs based on time spent
//    Trip A: 5 hours, Trip B: 2 hours
//    Trip A gets 71% of allocated costs
//    Pros: Most accurate
//    Cons: Requires time tracking per trip
//
// 4. Activity-Based Costing (ABC):
//    Activities: Research (₹500), Booking (₹300), Support (₹200)
//    Trip A: 2 research + 1 booking + 3 support = ₹2,200
//    Trip B: 1 research + 1 booking + 0 support = ₹800
//    Pros: Most accurate, identifies cost drivers
//    Cons: Complex to set up, needs activity tracking

interface AllocationRule {
  costPool: string;
  allocationBase: string;
  conditions?: AllocationCondition[];
}

// Recommended allocation for travel agencies:
// Start simple, add sophistication over time:
//
// Phase 1 (0-100 trips/month): Per-trip allocation
// Phase 2 (100-500 trips/month): Revenue-based allocation
// Phase 3 (500+ trips/month): Activity-based costing
//
// Standard allocation rates (India travel agency benchmarks):
// Agent salary allocation: ₹500-1,000 per trip
// Office overhead: ₹200-500 per trip
// Technology/platform: ₹150-300 per trip
// Marketing/acquisition: ₹300-800 per trip
// Communication (phone, WhatsApp): ₹50-100 per trip
// Total indirect cost: ₹1,200-2,700 per trip
```

### Revenue Attribution

```typescript
interface RevenueAttribution {
  tripId: string;
  grossRevenue: Money;
  attribution: RevenueAttributionEntry[];
  commission: CommissionAttribution[];
}

interface RevenueAttributionEntry {
  recipient: string;                  // Agent ID, referral source, channel
  role: AttributionRole;
  percentage: number;
  amount: Money;
}

type AttributionRole =
  | 'primary_agent'                   // Agent who handled the booking
  | 'referral_source'                 // Who referred the customer
  | 'marketing_channel'               // Channel that acquired the customer
  | 'support_agent'                   // Agent who handled modifications
  | 'team_lead';                      // Team lead overseeing the account

// Revenue attribution scenarios:
//
// Scenario 1: Single agent, direct customer
//   Agent Priya handles the entire booking
//   Attribution: Priya gets 100%
//   Commission: Priya gets 3% of net profit
//
// Scenario 2: Handoff between agents
//   Agent Arun takes the inquiry, quotes the trip
//   Agent Priya closes the booking (Arun was on leave)
//   Attribution: Arun 60%, Priya 40%
//   Commission: Split proportionally
//
// Scenario 3: Referral
//   Previous customer Rajesh refers his friend Suresh
//   Agent Priya handles Suresh's booking
//   Attribution: Rajesh (referral) 10%, Priya (booking) 90%
//   Commission: Priya gets full commission
//   Referral: Rajesh gets ₹1,000 credit
//
// Scenario 4: Marketing channel attribution
//   Customer finds agency via Google Ads
//   Calls and Agent Arun handles the booking
//   Attribution: Google Ads (acquisition) + Arun (booking)
//   Cost: Google Ads spend allocated to this booking
//   Net margin: Reduced by marketing acquisition cost
//
// Multi-touch attribution model:
// First touch (discovery): 20% credit
// Last touch (conversion): 50% credit
// Assisting touches: 30% credit (distributed equally)
//
// For commission purposes: Only agent attribution matters
// For profitability analysis: All attribution matters (including marketing cost)
```

---

## Open Problems

1. **Indirect cost accuracy** — Allocating rent, salaries, and overhead to individual trips is inherently imprecise. Over-allocation makes trips look unprofitable; under-allocation hides true costs.

2. **Time tracking burden** — Accurate cost allocation requires agents to log time per trip. Agents resist time tracking as administrative overhead.

3. **Attribution conflict** — When two agents contribute to a booking, attribution splits can create workplace tension. Need transparent, automated attribution rules.

4. **Seasonal margin variation** — Margins vary seasonally (peak season = lower margins due to higher supplier costs). Need year-over-year comparison, not month-over-month.

5. **Customer-level data completeness** — Profitability analysis requires complete cost data. If agents book through channels outside the platform, costs are invisible.

---

## Next Steps

- [ ] Build per-trip profitability tracking with margin analysis
- [ ] Create customer lifetime value (LTV) model with segmentation
- [ ] Design cost allocation engine with phased sophistication
- [ ] Build revenue attribution model for multi-agent and multi-channel
- [ ] Study profitability analytics (ProfitWell, ChartMogul, Baremetrics for travel)
