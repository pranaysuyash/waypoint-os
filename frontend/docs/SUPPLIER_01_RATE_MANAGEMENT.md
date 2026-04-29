# Supplier Relationship & Contract Intelligence — Rate Management

> Research document for supplier rate management, contracted vs. dynamic rates, rate parity monitoring, markup calculation, and India-specific tax considerations.

---

## Key Questions

1. **How do we store and manage contracted rates, net rates, and dynamic rates for each supplier?**
2. **How do we compare rates across multiple suppliers for the same product (same hotel, same route, same activity)?**
3. **What does rate parity monitoring look like — detecting when our supplier's OTA price undercuts the rate they gave us?**
4. **How should the rate change notification system work — real-time vs. batch, escalation thresholds?**
5. **What markup calculator model balances margin targets with breakeven analysis and market competitiveness?**
6. **How do we track historical rates and surface trend analysis for negotiation leverage?**
7. **India-specific: How do we handle GST-inclusive vs. exclusive rates, and what are the TCS implications on supplier costs?**

---

## Research Areas

### Rate Types & Data Model

```typescript
type RateType =
  | 'contracted'          // Negotiated fixed rate for a contract period
  | 'net'                 // Supplier gives net rate; agency sets selling price
  | 'dynamic'             // Fluctuates based on demand/supply/season
  | 'published'           // Rack rate / standard published rate
  | 'promotional'         // Time-limited promotional rate
  | 'opaque'              // Supplier hidden (e.g., Priceline Express Deals model)
  | 'commission_based'    // Agency earns % of selling rate
  | 'allotment';          // Blocked inventory at pre-agreed rate

type SeasonTier =
  | 'peak'                // Diwali, Christmas, summer holidays
  | 'high'                // Long weekends, regional festivals
  | 'shoulder'            // Transition periods
  | 'low'                 // Monsoon (varies by region), off-season
  | 'event';              // Specific event (Kumbh Mela, IPL finals)

interface SupplierRate {
  rateId: string;
  supplierId: string;
  productId: string;                // Hotel room type, flight route, activity SKU
  rateType: RateType;
  seasonTier: SeasonTier;
  validity: {
    startDate: Date;
    endDate: Date;
    bookingWindow?: {                // Must book between these dates
      start: Date;
      end: Date;
    };
  };
  pricing: RatePricing;
  inventory?: InventoryConstraint;
  restrictions: RateRestriction[];
  source: RateSource;
  lastUpdated: Date;
}

interface RatePricing {
  currency: 'INR' | 'USD' | 'EUR' | string;
  baseRate: number;                  // Before tax
  taxTreatment: TaxTreatment;
  taxes: TaxComponent[];             // CGST, SGST, IGST breakdown
  totalRate: number;                 // After tax
  mealPlan?: MealPlan;
  commission?: {                     // For commission-based rates
    type: 'percentage' | 'flat';
    value: number;
  };
}

interface TaxTreatment {
  gstInclusive: boolean;             // Is rate GST-inclusive?
  gstRate: number;                   // 5%, 12%, 18%, 28%
  gstBreakdown: {
    cgst?: number;                   // Central GST (same-state)
    sgst?: number;                   // State GST (same-state)
    igst?: number;                   // Integrated GST (inter-state)
  };
  tcsApplicable: boolean;            // TCS under LRS for forex payments
  tcsRate?: number;                  // 5% or 0.5% depending on amount
}

type MealPlan =
  | 'room_only'
  | 'bed_and_breakfast'
  | 'half_board'
  | 'full_board'
  | 'all_inclusive';

interface InventoryConstraint {
  allotment?: number;                // Rooms/seats blocked for agency
  releasePeriod: string;             // "72 hours before check-in"
  overbookingAllowed: boolean;
}

interface RateRestriction {
  type: 'min_stay' | 'max_stay' | 'min_advance' | 'non_refundable'
      | 'no_show_penalty' | 'prepayment_required' | 'blackout_dates';
  value: string;
}
```

### Seasonal Tier System

```typescript
// Indian travel season matrix — varies dramatically by region:
//
// Goa:
//   Peak:  Dec 20 - Jan 5 (Christmas/New Year)
//   High:  Nov - Feb (winter tourism season)
//   Low:   Jun - Sep (monsoon)
//   Shoulder: Mar - May, Oct
//
// Kerala:
//   Peak:  Dec - Jan (winter tourists)
//   High:  Aug - Mar (Ayurveda season starts Aug)
//   Low:   Jun - Jul (heavy monsoon)
//   Shoulder: Apr - May
//
// Rajasthan:
//   Peak:  Oct - Mar (pleasant weather)
//   High:  Aug - Sep (shoulder, some international tourists)
//   Low:   Apr - Jul (extreme heat, 45C+)
//
// Himalayas (Manali, Shimla, Srinagar):
//   Peak:  May - Jun (summer escape), Dec - Jan (snow)
//   High:  Jul - Aug (monsoon — variable), Mar - Apr (spring)
//   Low:   Nov (between seasons)
//
// Andaman:
//   Peak:  Nov - Apr (dry season, diving season)
//   Low:   May - Sep (monsoon, rough seas)
//   Shoulder: Oct

interface SeasonCalendar {
  destination: string;
  state?: string;                    // Indian state
  seasons: SeasonDefinition[];
  festivalPeriods: FestivalPeriod[];  // Affects pricing and availability
}

interface SeasonDefinition {
  tier: SeasonTier;
  startDate: string;                 // MM-DD
  endDate: string;                   // MM-DD
  rateMultiplier: number;            // 1.0 = base, 1.5 = 50% premium
  description: string;
}

interface FestivalPeriod {
  name: string;                      // "Diwali Week", "Durga Puja"
  dates: DateRange;                  // Varies by year
  impactLevel: 'high' | 'medium' | 'low';
  typicalPremium: number;            // 1.3 = 30% above seasonal rate
  bookingWindowAdvance: string;      // "6 weeks" — how early locals book
}
```

### Rate Comparison Engine

```typescript
interface RateComparison {
  productId: string;
  productDetails: {
    name: string;                    // "Taj Lake Palace, Udaipur — Deluxe Lake View"
    category: SupplierCategory;
    serviceDate: Date;
    duration: string;                // "3 nights", "8 hours"
    mealPlan?: MealPlan;
  };
  quotes: SupplierQuote[];
  bestOption: BestQuote;
  parityAlerts: ParityAlert[];
}

interface SupplierQuote {
  supplierId: string;
  supplierName: string;
  rateType: RateType;
  netRate: number;
  totalRate: number;
  commissionEarned?: number;
  mealPlan?: MealPlan;
  cancellationPolicy: string;
  restrictions: string[];
  confidence: number;                // How certain is this rate (cached vs. live)
  quoteExpiry: Date;
  source: 'live_api' | 'cached' | 'contracted' | 'manual';
}

interface BestQuote {
  recommendedSupplierId: string;
  recommendationReason: 'lowest_net' | 'best_value' | 'preferred_supplier'
                       | 'best_cancellation' | 'highest_margin';
  netRate: number;
  suggestedSellingPrice: number;
  expectedMargin: MarginBreakdown;
}

// Rate comparison UI sketch:
//
// +---------------------------------------------------------------+
// | Taj Lake Palace — Deluxe Lake View | 3 Nights | 15-18 Dec    |
// +---------------------------------------------------------------+
// | Supplier        | Rate Type  | Net    | Sell   | Margin | CP  |
// |-----------------|------------|--------|--------|--------|-----|
// | *Taj Direct     | Contracted | 18500  | 24500  | 24.5%  | F   |
// |  Booking.com    | Commission | 21200  | 21200  | 15%    | M   |
// |  MakeMyTrip     | Net        | 19800  | —      | —      | M   |
// |  TBO            | Net        | 19200  | —      | —      | S   |
// |  GTA            | Net        | 20100  | —      | —      | F   |
// +---------------------------------------------------------------+
// | * = Recommended (best margin + preferred supplier + full canc) |
// | CP: F=Free cancellation, M=Moderate, S=Strict                 |
// +---------------------------------------------------------------+
```

### Rate Parity Monitoring

```typescript
interface ParityMonitor {
  monitorId: string;
  productId: string;
  contractedRate: number;            // What supplier committed to
  checks: ParityCheck[];
  violations: ParityViolation[];
  lastChecked: Date;
}

interface ParityCheck {
  channel: string;                   // "Booking.com", "MMT", "Goibibo", "Direct"
  channelRate: number;
  ourRate: number;
  difference: number;
  differencePercent: number;
  isLower: boolean;                  // Channel rate < our contracted rate
  checkedAt: Date;
}

interface ParityViolation {
  violationId: string;
  productId: string;
  supplierId: string;
  channel: string;
  contractedRate: number;
  channelRate: number;
  savingsLost: number;               // What customer would save on channel
  detectedAt: Date;
  status: 'detected' | 'reported' | 'supplier_responded' | 'resolved';
  resolution?: string;
}

// Parity monitoring workflow:
// 1. System periodically checks OTA rates for contracted products
// 2. If OTA rate < contracted rate (or same product is publicly cheaper):
//    a. Flag violation with screenshots
//    b. Alert account manager
//    c. Auto-draft email to supplier requesting rate match
// 3. Track resolution timeline
// 4. Persistent violations → reduce supplier tier, renegotiate
//
// Practical challenge:
// OTA rates fluctuate constantly. A single snapshot check is insufficient.
// Need continuous monitoring at multiple times of day, especially:
// - Early morning (supplier nightly rate updates)
// - Midday (competitor price matching)
// - Evening (flash sales)
//
// India-specific parity issues:
// - Many Indian hotels list different prices on MakeMyTrip vs. Booking.com
//   vs. direct website. Rate parity agreements are weakly enforced.
// - GST treatment varies: some OTAs show GST-inclusive, others exclusive
// - "Member rates" on MMT/Goibibo can undercut contracted rates significantly
```

### Rate Change Notification System

```typescript
interface RateChangeNotification {
  notificationId: string;
  supplierId: string;
  changeType: RateChangeType;
  affectedProducts: AffectedProduct[];
  severity: 'info' | 'warning' | 'critical';
  actionRequired: string;
  createdAt: Date;
}

type RateChangeType =
  | 'rate_increase'            // Supplier raised rates
  | 'rate_decrease'            // Supplier lowered rates
  | 'new_seasonal_tier'        // New season rates published
  | 'promotion_launched'       // Limited-time promotional rate
  | 'promotion_ending'         // Promotion about to expire
  | 'contract_expiring'        // Contract rates expiring soon
  | 'allotment_change'         // Room/seat allotment changed
  | 'policy_change'            // Cancellation, payment terms changed
  | 'new_product';             // New product/rate plan added

interface AffectedProduct {
  productId: string;
  productName: string;
  oldRate: number;
  newRate: number;
  changePercent: number;
  effectiveDate: Date;
  affectedBookings: string[];        // Booking IDs impacted
}

// Notification routing:
//
// Rate increase < 5%:    Info → Agent dashboard notification
// Rate increase 5-15%:   Warning → Email + dashboard, flag open quotes
// Rate increase > 15%:   Critical → WhatsApp + email + dashboard,
//                         auto-pause auto-booking, alert manager
//
// Rate decrease:         Info → Dashboard notification,
//                         suggest re-quoting open trips
//
// Contract expiring:     30 days → Warning to manager
//                        14 days → Critical, auto-draft renewal request
//                         7 days → Critical, escalate to owner
//
// Notification channels (in priority order):
// 1. In-app notification (always)
// 2. Email (warning + critical)
// 3. WhatsApp (critical only)
// 4. Slack/Teams (if configured)
```

### Markup Calculator & Breakeven Analysis

```typescript
interface MarkupCalculator {
  input: MarkupInput;
  calculation: MarkupCalculation;
  scenarios: MarkupScenario[];
  recommendation: MarkupRecommendation;
}

interface MarkupInput {
  netRate: number;
  currency: string;
  taxes: TaxComponent[];
  paymentGatewayFee: number;         // 2% for credit card
  tdsDeductible: number;             // TDS on supplier payment
  operationalCostPerBooking: number;  // Allocated ops cost
  targetMarginPercent: number;
  competitorPrices: number[];         // Market prices for same product
}

interface MarkupCalculation {
  totalCostToAgency: number;         // Net + taxes + fees + ops
  minimumMarkup: number;             // Breakeven markup (0% margin)
  minimumSellingPrice: number;       // Breakeven selling price
  targetMarkup: number;              // Markup to hit target margin
  targetSellingPrice: number;
  actualMargin: number;              // After all costs
  actualMarginPercent: number;
  // Breakeven analysis:
  breakeven: {
    atCurrentPrice: number;          // How many bookings to breakeven
    atTargetPrice: number;
    fixedCostsCovered: number;       // % of fixed costs recovered
  };
}

interface MarkupScenario {
  name: string;                      // "Aggressive", "Standard", "Premium"
  sellingPrice: number;
  marginPerBooking: number;
  marginPercent: number;
  estimatedConversionRate: number;   // Likelihood of customer booking
  expectedRevenue: number;           // margin x estimated_bookings
}

interface MarkupRecommendation {
  recommendedSellingPrice: number;
  recommendedMarkupPercent: number;
  reasoning: string;
  competitivePosition: 'below_market' | 'at_market' | 'above_market';
  risks: string[];
}

// Markup calculation example (Indian context):
//
// Product: Hotel room, Goa, 1 night
// Net rate from supplier:     ₹8,000
// GST (12%):                  ₹960   (₹480 CGST + ₹480 SGST)
// Payment gateway (2%):       ₹200   (on selling price estimate)
// TDS on supplier (1%):       ₹80    (deducted at source)
// Operational cost:           ₹300   (allocated per booking)
// ──────────────────────────────────
// Total cost to agency:       ₹9,540
//
// Target margin: 20%
// Required selling price:     ₹11,925 (₹9,540 / 0.80)
// Actual margin per booking:  ₹2,385
//
// Competitor check:
//   Booking.com: ₹12,500
//   MakeMyTrip:  ₹11,800
//   Goibibo:     ₹11,200
//
// Recommendation: ₹11,800 (match MMT, 19.1% margin)
// Risk: Goibibo undercuts by ₹600. May lose price-sensitive customers.
```

### Historical Rate Tracking & Trend Analysis

```typescript
interface RateHistory {
  productId: string;
  supplierId: string;
  snapshots: RateSnapshot[];
  trends: RateTrend[];
}

interface RateSnapshot {
  date: Date;
  seasonTier: SeasonTier;
  netRate: number;
  sellingRate: number;
  occupancy?: number;                // Hotel occupancy % at snapshot time
  daysBeforeService: number;         // How far in advance this rate was captured
  source: RateSource;
}

type RateSource =
  | 'contracted_rate_card'
  | 'api_quote'
  | 'portal_check'
  | 'booking_confirmed'
  | 'competitor_scrape';

interface RateTrend {
  period: string;                    // "2025-Q4", "Diwali 2025"
  averageRate: number;
  minRate: number;
  maxRate: number;
  changeFromPrevious: number;        // % change
  direction: 'increasing' | 'stable' | 'decreasing';
  volatility: number;                // Standard deviation as % of mean
}

// Trend analysis use cases:
//
// 1. Negotiation leverage:
//    "Supplier X's Goa rates increased 18% this year, but hotel occupancy
//     only grew 5%. The rate increase is not justified by demand."
//
// 2. Booking timing optimization:
//    "Historically, Kerala houseboat rates drop 15-20% in the 2 weeks
//     before travel during shoulder season. Consider waiting to book."
//
// 3. Seasonal planning:
//    "Rajasthan rates for Dec 2026 are already 12% higher than Dec 2025.
//     Lock in rates now before further increases."
//
// 4. Supplier benchmarking:
//    "Taj hotels' rate increases (avg 10%) are in line with market.
//     Oberoi hotels' increases (avg 18%) are above market average (11%)."
```

### India-Specific: GST & TCS Considerations

```typescript
// GST treatment in travel supplier rates:
//
// Hotel rooms:
//   Below ₹1,000/night:   No GST
//   ₹1,000 - ₹7,499:     12% GST
//   ₹7,500 and above:     18% GST
//   Note: GST is on declared tariff, not discounted rate
//
// Restaurant (part of hotel stay):
//   5% GST (no ITC) for standalone
//   Part of hotel package: follows hotel GST rate
//
// Airfare:
//   Economy:    5% GST
//   Business:  12% GST
//
// Tour packages:
//   5% GST (on 25% of gross billing or actual, whichever is more)
//   Abroad tours: 5% on 10% of gross billing
//
// Transport:
//   Cab/rental:  5% GST (with ITC)
//   Bus:         Exempt or 5%
//
// TCS (Tax Collected at Source) under LRS:
//   Applies when customer pays in foreign currency
//   Threshold: ₹7 lakh/year per customer
//   Rate: 5% (0.5% if PAN/Aadhaar verified and < ₹7 lakh)
//   Impact: Increases customer's cost, affects booking decision
//   Agency must collect TCS and deposit with government

interface IndiaTaxConfig {
  gstRates: Record<string, {
    rate: number;
    breakdown: 'cgst_sgst' | 'igst';
    itcEligible: boolean;
    abatement?: number;               // % for tour packages
  }>;
  tdsRates: Record<string, {
    rate: number;
    threshold: number;
    section: string;                  // "194C", "194H", etc.
  }>;
  tcsConfig: {
    enabled: boolean;
    domesticThreshold: number;
    internationalThreshold: number;
    rates: Record<string, number>;
  };
}

// TDS sections relevant to travel agencies:
// 194C: Contract payments (transport, tour operators) — 1% (₹30K single / ₹1L annual)
// 194H: Commission to agents — 5%
// 194I: Rent (for office/branch rent) — 10%
// 194J: Professional fees (consultants, guides) — 10%
```

---

## Open Problems

1. **Rate data freshness vs. cost** — Live API calls for every rate check are expensive. Caching introduces staleness. What is the optimal cache TTL per supplier category? Hotels change rates multiple times per day; airline fares change even more frequently.

2. **Rate parity enforcement is a cat-and-mouse game** — Indian suppliers frequently bypass rate parity agreements. OTAs run flash sales. Member-only prices are invisible to standard monitoring. Scraping is legally grey. Need a pragmatic approach that balances monitoring effectiveness with feasibility.

3. **Markup optimization is multi-dimensional** — Margin, competitiveness, conversion probability, customer segment, booking urgency, and payment method all interact. A simple percentage markup leaves money on the table. But a complex dynamic model is opaque and may produce unexpected results.

4. **GST-inclusive vs. exclusive confusion** — Suppliers quote rates inconsistently. Some include GST, some exclude it. For tour packages with abatement, the calculation is even more complex. Every rate comparison must normalize tax treatment first.

5. **TCS impact on international bookings** — The 5% TCS on foreign remittances above the threshold significantly increases the customer's total cost. Customers compare our TCS-inclusive price against OTA prices that may not prominently show TCS. How do we present this transparently without losing conversions?

6. **Historical rate data is sparse** — Most agencies don't systematically record rate history. Starting from scratch means trends take months to become actionable. Need bootstrapping strategies (competitor data, published rate cards).

---

## Next Steps

- [ ] Design the supplier rate schema and storage model (Supabase tables)
- [ ] Build rate ingestion pipeline for contracted rate cards (CSV/PDF import)
- [ ] Create rate comparison UI with multi-supplier quote table
- [ ] Implement rate parity checking service with scheduled scraping
- [ ] Build markup calculator with breakeven analysis and scenario modeling
- [ ] Research rate monitoring tools (RateGain, AxisRoom, HotelDruid)
- [ ] Design seasonal tier calendar with India-specific festival periods
- [ ] Map GST treatment rules per product category with automation
- [ ] Study TCS workflow for international bookings and customer communication
