# Supplier Rate Intelligence — Competitor Pricing & Market Analysis

> Research document for competitor price tracking, market positioning analysis, dynamic pricing intelligence, and the rate intelligence feedback loop for travel agencies.

---

## Key Questions

1. **How do we track competitor pricing for identical trips?**
2. **What market positioning insights help agencies price competitively?**
3. **How does dynamic pricing intelligence inform quotation strategy?**
4. **What competitive advantages can agencies derive from rate data?**

---

## Research Areas

### Competitor Price Tracking

```typescript
interface CompetitorTracker {
  // Competitor profiles
  competitors: {
    name: string;                        // "MakeMyTrip", "Thomas Cook", "SOTC"
    type: "OTA" | "TRADITIONAL_AGENCY" | "ONLINE_AGENCY" | "DMC";
    market_focus: string[];              // ["Southeast Asia", "Europe"]
    target_segment: "BUDGET" | "MID" | "PREMIUM" | "ALL";
    monitoring_enabled: boolean;
  }[];

  // Trip-level price comparison
  price_comparison: {
    trip_description: string;            // "5N Singapore, Family of 4, 3-star"
    our_price: number;
    our_margin: number;

    comparisons: {
      competitor: string;
      price: number;
      price_difference: number;          // vs our price
      includes: string[];                // what's included
      excludes: string[];                // what they don't include
      hidden_costs: string[];            // things not obvious (transfers, tips)
      effective_price: number;           // price including hidden costs
      value_rating: "BETTER" | "SIMILAR" | "WORSE";
    }[];
  };
}

// ── Competitor price comparison ──
// ┌─────────────────────────────────────────────────────┐
// │  Competitor Analysis — Singapore 5N Family Package     │
// │  4 travelers · Jun 1-6, 2026 · 3-star hotels          │
// │                                                       │
// │  Your quote: ₹1,85,000                                │
// │                                                       │
// │  ┌────────────────────────────────────────────────┐  │
// │  │ Competitor     │ Listed  │ Effective │ Delta   │  │
// │  │ ───────────────────────────────────────────────│  │
// │  │ MakeMyTrip     │ ₹1,72K  │ ₹1,89K   │ +₹4K   │  │
// │  │ (excl: transfers, tips)                         │  │
// │  │                                                │  │
// │  │ Thomas Cook    │ ₹1,95K  │ ₹1,95K   │ +₹10K  │  │
// │  │ (all included)                                  │  │
// │  │                                                │  │
// │  │ SOTC           │ ₹1,68K  │ ₹1,82K   │ -₹3K   │  │
// │  │ (excl: visa, insurance)                         │  │
// │  │                                                │  │
// │  │ Yatra          │ ₹1,79K  │ ₹1,91K   │ +₹6K   │  │
// │  │ (excl: some meals, transfers)                   │  │
// │  │                                                │  │
// │  │ Local Agent A  │ ₹1,90K  │ ₹1,90K   │ +₹5K   │  │
// │  │ (all included, unknown hotel quality)            │  │
// │  └────────────────────────────────────────────────┘  │
// │                                                       │
// │  Your effective price rank: 2nd cheapest              │
// │  Your value rank: BEST (most inclusions)               │
// │                                                       │
// │  Recommendation:                                      │
// │  → Quote is competitive on effective price            │
// │  → Highlight "all inclusive" vs MakeMyTrip exclusions │
// │  → Use as sales talking point: "no hidden costs"      │
// └─────────────────────────────────────────────────────┘
```

### Market Positioning Map

```typescript
interface MarketPosition {
  destination: string;
  segment: string;                       // "Family", "Honeymoon", "Corporate"

  // Positioning grid
  positioning: {
    x_axis: "PRICE";                     // low ← → high
    y_axis: "SERVICE_LEVEL";             // basic ← → premium
    our_position: { x: number; y: number };
    competitors: {
      name: string;
      position: { x: number; y: number };
      market_share_estimate: number;
    }[];
  };

  // White space analysis
  white_space: {
    underserved_segments: string[];
    price_gaps: {
      range: string;                     // "₹1.5L-2L family packages"
      competitors_in_range: number;
      demand_indicators: string;
    }[];
  };
}

// ── Market positioning map ──
// ┌─────────────────────────────────────────────────────┐
// │  Market Positioning — Singapore Outbound                │
// │                                                       │
// │  Service Level                                        │
// │  HIGH ┤                                               │
// │       │        ·Thomas Cook        ·YOU              │
// │       │                            ★                 │
// │  MED  │   ·SOTC                                    │
// │       │              ·Local Agents                   │
// │       │   ·Yatra                                     │
// │  LOW  │        ·MakeMyTrip                           │
// │       │                                              │
// │       └──┬──────────┬──────────┬──────────┬─→       │
// │        ₹1.5L      ₹2.0L      ₹2.5L     ₹3.0L     │
// │                     Price                            │
// │                                                       │
// │  White space:                                        │
// │  → ₹1.5-1.8L premium service (undercut Thomas Cook) │
// │  → ₹2.5L+ luxury family (no strong competitor)      │
// │                                                       │
// │  Your positioning: Mid-premium price, premium service │
// │  Strategy: "Premium service at fair prices"           │
// └─────────────────────────────────────────────────────┘
```

### Dynamic Pricing Intelligence

```typescript
interface DynamicPricingEngine {
  // Rate factors that should influence agency pricing
  factors: {
    // Supply-side factors
    hotel_occupancy: number;              // % occupancy at destination
    flight_load_factor: number;           // % seats filled
    seasonal_demand_index: number;        // 1-100, based on historical data
    event_impact: number | null;          // price multiplier from events

    // Demand-side factors
    search_volume_trend: "RISING" | "STABLE" | "FALLING";
    booking Pace: "AHEAD" | "ON_TRACK" | "BEHIND";
    competitor_availability: "WIDELY" | "LIMITED" | "SOLD_OUT";

    // Cost factors
    exchange_rate_trend: "FAVORABLE" | "STABLE" | "UNFAVORABLE";
    fuel_surcharge_trend: "RISING" | "STABLE" | "FALLING";
    supplier_promotions: string[];        // active deals from suppliers
  };

  // Pricing recommendation
  recommendation: {
    current_quote: number;
    recommended_price: number;
    adjustment: number;
    confidence: "HIGH" | "MEDIUM" | "LOW";
    reasoning: string[];
    valid_until: string;
  };
}

// ── Dynamic pricing recommendation ──
// ┌─────────────────────────────────────────────────────┐
// │  Pricing Intelligence — Singapore 5N Quote             │
// │                                                       │
// │  Current quote: ₹1,85,000                             │
// │                                                       │
// │  Market signals:                                      │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Factor              │ Signal      │ Impact    │   │
// │  │ ────────────────────────────────────────────  │   │
// │  │ Hotel occupancy     │ 72% (moderate)│ Neutral  │   │
// │  │ Flight load         │ 85% (high)  │ ↑ +3%    │   │
// │  │ Seasonal demand     │ 68/100      │ Neutral  │   │
// │  │ Event: Great Sale   │ +15% hotels │ ↑ +₹5K   │   │
// │  │ Exchange rate       │ ₹66.2/SGD   │ ↓ -₹2K   │   │
// │  │ Competitor stock    │ Limited     │ ↑ +₹3K   │   │
// │  │ Supplier promo      │ 10% off Taj │ ↓ -₹4K   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Recommendation: ₹1,87,000 (+₹2,000)                 │
// │  Confidence: MEDIUM                                   │
// │                                                       │
// │  Reasoning:                                           │
// │  • Great Sale event pushing hotel rates up            │
// │  • High flight load suggests limited seat availability│
// │  • Offset by favorable SGD rate and Taj promo         │
// │  • Net: small upward adjustment justified             │
// │  • Competitor sold out = pricing power for you        │
// │                                                       │
// │  [Apply Recommendation] [Keep Current] [Adjust Manually]│
// └─────────────────────────────────────────────────────┘
```

### Quotation Strategy Feedback Loop

```typescript
interface QuotationFeedback {
  // Track what happens to quotes
  quote_tracking: {
    quote_id: string;
    destination: string;
    quoted_price: number;
    competitor_prices_at_time: number[];

    // Outcome
    outcome: "WON" | "LOST" | "NEGOTIATING" | "EXPIRED" | "WITHDRAWN";
    lost_to_competitor: string | null;
    lost_to_price: boolean | null;
    final_negotiated_price: number | null;
    margin_actual: number | null;

    // Time to decision
    days_from_quote_to_outcome: number;
    days_from_quote_to_booking: number | null;
  };

  // Aggregate learnings
  learnings: {
    win_rate_by_destination: Record<string, number>;
    win_rate_by_price_position: Record<string, number>;  // "cheapest", "mid", "expensive"
    common_loss_reasons: { reason: string; frequency: number }[];
    optimal_margin_range: { min: number; max: number };
    average_negotiation_delta: number;   // how much price drops in negotiation
  };
}

// ── Quotation feedback dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Quotation Intelligence — Win/Loss Analysis             │
// │  Q1 2026 (Jan-Mar)                                    │
// │                                                       │
// │  Overall win rate: 42% (168 won / 400 quoted)         │
// │                                                       │
// │  Win rate by price position:                          │
// │  Cheapest:    58% (72/124)                            │
// │  Mid-market:  41% (68/166)                            │
// │  Most expensive: 21% (28/110)                         │
// │                                                       │
// │  Win rate by destination:                             │
// │  Singapore:   48%                                     │
// │  Dubai:       45%                                     │
// │  Thailand:    52%                                     │
// │  Europe:      31%                                     │
// │  Kerala:      65%                                     │
// │                                                       │
// │  Top loss reasons:                                    │
// │  1. Price too high (38%)                              │
// │  2. Customer went to OTA directly (24%)               │
// │  3. Competitor offered better itinerary (18%)         │
// │  4. Customer decided not to travel (12%)              │
// │  5. Lost to another agency (8%)                       │
// │                                                       │
// │  Optimal margin band: 12-18%                          │
// │  Above 18%: win rate drops to 22%                     │
// │  Below 10%: win rate 55% but unsustainable margin     │
// │                                                       │
// │  Recommendation: Target 14-16% margin for Singapore   │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Competitor data collection** — Competitor prices are publicly visible but change frequently. Manual collection doesn't scale; authorized data feeds are limited for Indian agencies. Need hybrid approach: automated for OTAs, manual spot-checks for traditional agencies.

2. **Quote-to-outcome tracking** — Agencies rarely learn why they lost a deal. Need low-friction loss tracking (WhatsApp quick-reply: "Why didn't you book? A) Price B) Found better C) Changed plans").

3. **Dynamic pricing without dynamic costs** — Agencies can't change supplier costs dynamically. Recommendations must account for locked-in B2B rates vs. flexible retail rates.

4. **Price transparency vs. margin** — Showing competitor prices to agents helps them sell, but showing to customers may trigger race-to-bottom pricing. Need agent-facing intelligence, not customer-facing.

---

## Next Steps

- [ ] Build competitor price tracking with OTA scraping (authorized)
- [ ] Create market positioning analysis with white space detection
- [ ] Implement dynamic pricing intelligence with multi-factor signals
- [ ] Design quotation feedback loop with win/loss analytics
