# Pricing Engine — Dynamic Pricing Algorithms

> Research document for dynamic pricing strategies, rate management, and price optimization.

---

## Key Questions

1. **What pricing models exist in travel (fixed, dynamic, opaque, bundled)?**
2. **How do suppliers change rates, and how do we react?**
3. **What factors should influence our markup — demand, competition, margin target, customer segment?**
4. **How do we handle price changes after a quote is sent but before booking?**
5. **What's the real-time pricing architecture for live rate feeds?**

---

## Research Areas

### Pricing Models in Travel

```typescript
type PricingModel =
  | 'fixed_rate'         // Published rate, no negotiation
  | 'negotiated_rate'    // Contracted rate with supplier
  | 'dynamic_rate'       // Fluctuates based on demand/supply
  | 'opaque_rate'        // Hidden supplier name (like Priceline Express Deals)
  | 'bundled_rate'       // Package price (flight + hotel)
  | 'commission_based'   // Agency earns % of supplier rate
  | 'markup_based'       // Agency adds markup to net rate
  | 'net_rate'           // Supplier gives net, agency sets selling price
  | 'bid_price'          // Customer states budget, agents compete;

interface PriceComponent {
  componentId: string;
  type: PriceComponentType;
  baseAmount: number;
  currency: string;
  markup: MarkupConfig;
  taxes: TaxComponent[];
  fees: FeeComponent[];
  finalAmount: number;
}

type PriceComponentType =
  | 'room_rate'
  | 'flight_fare'
  | 'transfer_rate'
  | 'activity_rate'
  | 'insurance_premium'
  | 'visa_fee'
  | 'service_fee'
  | 'commission';

interface MarkupConfig {
  type: 'percentage' | 'flat' | 'tiered' | 'dynamic';
  value: number;
  minValue?: number;           // Minimum markup
  maxValue?: number;           // Maximum markup
  rules?: MarkupRule[];
}

interface MarkupRule {
  condition: string;           // e.g., "demand_level > 0.8"
  adjustment: number;          // Adjust markup by this amount
}
```

### Dynamic Pricing Factors

```typescript
interface PricingContext {
  // Demand signals
  demand: {
    searchVolume: number;        // Searches for this destination/service
    bookingPace: number;         // How fast bookings are coming in
    availabilityPercent: number; // How much inventory remains
    daysToTravel: number;
  };
  // Competition
  competition: {
    lowestCompetitorPrice: number;
    averageCompetitorPrice: number;
    ourPricePosition: 'below' | 'at' | 'above';
  };
  // Customer signals
  customer: {
    segment: string;
    priceSensitivity: number;
    loyaltyStatus: string;
    bookingHistory: number;
  };
  // Market conditions
  market: {
    season: 'peak' | 'shoulder' | 'off';
    eventNearby: boolean;
    economicIndicator: string;
    currencyTrend: string;
  };
}
```

### Real-Time Rate Architecture

```typescript
interface RateFeed {
  supplierId: string;
  serviceType: string;
  rates: RateEntry[];
  lastUpdated: Date;
  cacheExpiry: Date;
  source: 'api' | 'scraped' | 'file' | 'manual';
}

interface RateEntry {
  rateKey: string;
  serviceDate: Date;
  occupancy: string;
  mealPlan: string;
  netRate: number;
  sellingRate: number;
  currency: string;
  cancellationPolicy: string;
  inventoryAvailable: number;
  restrictions: string[];        // e.g., "min_2_nights"
}
```

---

## Open Problems

1. **Rate volatility** — Hotel rates can change multiple times per day. When do we lock a rate for a customer — at quote time, at booking time, or at confirmation?

2. **Margin vs. competitiveness** — Higher margins mean higher prices, losing competitive edge. How to optimize margin while maintaining conversion?

3. **Price consistency** — Customer sees ₹15,000 on our site but ₹12,000 on Booking.com. Rate parity issues damage trust.

4. **Bulk pricing** — Group bookings and corporate accounts need different pricing logic than individual bookings. Multiple pricing engines running simultaneously.

5. **Price anchoring** — Showing "was ₹20,000, now ₹15,000" is effective but must reflect genuine price history. Regulatory risk with fake discounts.

---

## Next Steps

- [ ] Research dynamic pricing algorithms in travel (airline revenue management)
- [ ] Design pricing rules engine with configurable strategies
- [ ] Study rate caching and real-time update architecture
- [ ] Map pricing models per supplier category
- [ ] Design margin optimization model with competitiveness constraints
