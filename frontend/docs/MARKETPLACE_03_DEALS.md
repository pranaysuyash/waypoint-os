# Travel Marketplace & Aggregator — Deals & Dynamic Pricing

> Research document for flash deals, last-minute offers, early bird pricing, dynamic deal generation, and pricing intelligence.

---

## Key Questions

1. **How do we detect and surface travel deals from multiple sources?**
2. **What dynamic pricing models apply to travel inventory?**
3. **How do we generate "deals" from available inventory?**
4. **What's the lifecycle of a travel deal from creation to expiry?**
5. **How do we prevent deal fraud and misleading pricing?**

---

## Research Areas

### Deal Detection & Generation

```typescript
interface DealEngine {
  sources: DealSource[];
  detection: DealDetection;
  generation: DealGeneration;
  lifecycle: DealLifecycle;
  pricing: DynamicPricing;
}

interface DealSource {
  type: DealSourceType;
  detection: DealDetectionRule[];
  reliability: number;
}

type DealSourceType =
  | 'supplier_promo'                    // Supplier-provided promotion
  | 'price_drop'                       // Automated price drop detection
  | 'distress_inventory'               // Unsold inventory at deep discount
  | 'seasonal_promo'                   // Seasonal/season-end offers
  | 'early_bird'                       // Advance booking discounts
  | 'loyalty_deal'                     // Loyalty program exclusive
  | 'flash_sale'                       // Time-limited flash sale
  | 'bundle_deal';                     // Package bundle discount

// Deal detection patterns:
//
// 1. PRICE DROP DETECTION:
// Monitor prices for popular routes/hotels:
// - If current price < 7-day average by 15%+ → Generate "Price Drop" deal
// - If current price < 30-day average by 25%+ → Generate "Great Deal" deal
// - If current price = lowest in 90 days → Generate "Best Price" deal
//
// Price monitoring targets:
// Top 50 domestic routes (Delhi-Mumbai, Delhi-Bangalore, etc.)
// Top 100 hotels in top 20 destinations
// Popular international routes (India-Singapore, India-Dubai, India-Thailand)
// Check frequency: Every 30 minutes for flights, every 2 hours for hotels
//
// 2. DISTRESS INVENTORY DETECTION:
// Hotels with <30% occupancy for upcoming weekend → Flag for last-minute deal
// Airlines with <60% load factor 7 days before departure → Fare drop expected
// Tour operators with unsold group slots → Discount opportunity
//
// 3. SUPPLIER PROMOTION INGESTION:
// RSS feeds / email parsing from suppliers:
// - "Taj Hotels: 30% off summer sale"
// - "IndiGo: ₹999 base fare sale"
// - "Singapore Tourism: Free attraction passes with hotel booking"
// - Auto-ingest, parse, normalize, and publish as deals

interface DealDetection {
  priceMonitor: PriceMonitor;
  inventoryMonitor: InventoryMonitor;
  promoParser: PromoParser;
}

interface PriceMonitor {
  targets: PriceTarget[];
  frequency: number;                   // Minutes between checks
  threshold: PriceThreshold;
  alert: PriceAlertConfig;
}

interface PriceTarget {
  type: 'flight' | 'hotel' | 'package';
  route?: string;                      // "DEL-BOM"
  hotelId?: string;
  dateRange: DateRange;
  sourceIds: string[];                 // Sources to monitor
}

// Price monitoring example:
// Target: Delhi → Mumbai flights, next 30 days
// Sources: Amadeus, TBO, NDC (IndiGo, Vistara)
// Frequency: Every 30 minutes
// Thresholds:
//   - Price drop > 10%: "Price Drop" alert
//   - Price drop > 20%: "Great Deal" alert
//   - Price drop > 30%: "Incredible Deal" alert
//   - New low for 90-day period: "Best Price" badge
//
// Price history tracking:
// Route: DEL-BOM
// Date: Oct 15, 2026
// 90-day history: Avg ₹6,200 | Min ₹4,100 | Max ₹9,800
// Current lowest: ₹4,500 (from TBO, IndiGo 6E-123)
// Assessment: 27% below average → "Great Deal" (threshold: 20%)

interface DealGeneration {
  rules: DealRule[];
  templates: DealTemplate[];
  personalization: DealPersonalization;
}

// Deal generation rules:
// 1. If price drop detected AND route is popular (>100 searches/week)
//    → Generate public deal for all agents
//
// 2. If distress inventory AND hotel is 4-star+ AND destination is in-season
//    → Generate exclusive deal for premium agents
//
// 3. If supplier promo AND discount > 20% AND valid for >7 days
//    → Generate time-limited deal with countdown timer
//
// 4. If package components individually cheaper than any pre-built package
//    → Generate "Build Your Own" deal showing savings
//
// 5. If customer has incomplete trip (searched but not booked)
//    → Generate personalized deal for their specific search

interface Deal {
  id: string;
  type: DealType;
  title: string;                       // "Delhi-Mumbai Flights from ₹3,999"
  description: string;                 // "IndiGo flash sale — 35% off base fare"
  discount: DiscountInfo;
  originalPrice: number;
  dealPrice: number;
  savings: number;                     // ₹ saved
  savingsPercent: number;              // % saved
  validFrom: Date;
  validTo: Date;
  inventory: DealInventory;
  restrictions: DealRestriction[];
  source: string;
  category: DealCategory;
  urgency: DealUrgency;
}

// Deal example:
// Title: "Kerala 5N Package — ₹35,000 per person (was ₹48,000)"
// Type: flash_sale
// Discount: 27% off (₹13,000 savings per person)
// Valid: Oct 1-31 (travel by Dec 15)
// Inventory: 12 spots remaining
// Restrictions: Min 2 travelers, non-refundable, select dates only
// Urgency: high (selling fast — 8 bookings in last 24h)
//
// Deal urgency levels:
// low: Plenty of inventory, 2+ weeks validity
// medium: Limited inventory or <1 week validity
// high: Very limited inventory AND <3 days validity
// critical: <5 inventory AND <24 hours validity

// Deal category tags:
// 🔥 Flash Sale: Limited time, limited inventory
// 💰 Best Price: Lowest price in 90+ days
// ⏰ Last Minute: Departing within 7 days, deep discount
// 🐦 Early Bird: Book 60+ days ahead, significant savings
// 🎁 Bundle: Package deal (flight + hotel + activity)
// ⭐ Loyalty: Exclusive for repeat customers
// 🏖️ Seasonal: Season-specific promotion
// 🎉 New: New route/destination launch offer
```

### Dynamic Pricing Intelligence

```typescript
interface DynamicPricing {
  monitoring: PriceMonitoring;
  forecasting: PriceForecast;
  alerts: PriceAlert;
  recommendations: PricingRecommendation;
}

interface PriceForecast {
  type: 'flight' | 'hotel';
  route?: string;
  hotelId?: string;
  currentPrice: number;
  forecast: PriceForecastPoint[];
  recommendation: ForecastRecommendation;
  confidence: number;
}

interface PriceForecastPoint {
  date: string;                        // "2026-10-15"
  predictedPrice: number;
  confidenceBand: [number, number];    // [low, high] at 80% confidence
}

// Price forecasting model:
// Based on historical pricing patterns for the same route/hotel/dates:
//
// Delhi → Mumbai, Oct 15:
// Current price: ₹5,200
// 7-day forecast: ₹5,000-5,800 (likely stable)
// 14-day forecast: ₹4,800-6,200 (may dip)
// Recommendation: "Wait and watch — prices may drop ₹200-400 next week"
//
// Delhi → Mumbai, Dec 25:
// Current price: ₹8,500
// 7-day forecast: ₹9,000-12,000 (will increase significantly)
// Recommendation: "Book now — Christmas prices rising fast"
//
// Hotel Taj Palace Mumbai, Oct 15:
// Current rate: ₹16,800/night
// 30-day trend: Stable (₹16,200-17,500 range)
// Recommendation: "Good rate — book now or risk paying ₹17,000+"
//
// Price forecasting methodology:
// 1. Historical analysis: Same route/hotel, same month, last 3 years
// 2. Seasonal adjustment: Peak/off-peak/shoulder multipliers
// 3. Demand indicators: Search volume trend, booking pace
// 4. Supply factors: New routes, capacity changes, competitor pricing
// 5. External factors: Fuel prices, events, holidays, weather
// 6. Machine learning: Time-series model (Prophet/LSTM) for price prediction
//
// Forecast accuracy:
// 7-day forecast: ±8% (reliable)
// 14-day forecast: ±15% (moderate)
// 30-day forecast: ±25% (directional guidance only)

interface PriceAlert {
  id: string;
  userId: string;                      // Agent or customer
  target: PriceTarget;
  condition: AlertCondition;
  status: 'active' | 'triggered' | 'expired';
  lastChecked: Date;
  notificationHistory: NotificationRecord[];
}

type AlertCondition =
  | { type: 'below'; price: number }   // Alert when price drops below ₹X
  | { type: 'drop_percent'; percent: number } // Alert on X% price drop
  | { type: 'best_price_90d' }         // Alert when 90-day best price
  | { type: 'forecast_buy' };          // Alert when forecast says "buy now"

// Price alert examples:
// Agent sets: "Alert me when Delhi-Singapore drops below ₹15,000"
// System monitors daily → Price drops to ₹14,800 → Alert triggered
// Notification: "Delhi-Singapore at ₹14,800! Book now on [Airline].
//               This is 18% below the 30-day average. Deal valid for 48h."
//
// Customer sets: "Alert me when Goa hotels drop below ₹4,000/night"
// System monitors hourly → Rate found at ₹3,800 → Alert triggered
// Notification: "Goa hotel alert! [Hotel Name] at ₹3,800/night for your dates.
//               4-star rated, 200m from beach. 3 rooms left at this price."

interface PricingRecommendation {
  target: PriceTarget;
  action: 'buy_now' | 'wait' | 'monitor';
  rationale: string;
  priceHistory: PriceHistorySummary;
  forecast: ForecastSummary;
  savingsOpportunity: string;
}

// Pricing recommendation output:
// "BUY NOW: Delhi → Goa flights for December
//  Current: ₹6,200 (IndiGo, non-stop)
//  30-day trend: Rising (was ₹4,800 a month ago)
//  Forecast: Expected to reach ₹8,000+ by November
//  Recommendation: Book today — prices only going up for December travel
//  Potential savings: ₹1,800+ vs. booking in November"
```

---

## Open Problems

1. **Deal authenticity** — Showing a "was ₹48,000, now ₹35,000" deal requires proof that the original price was real and recently available. Fake "was" prices erode trust and violate advertising standards.

2. **Price forecasting accuracy** — Travel pricing is influenced by unpredictable factors (competitor moves, fuel price shocks, pandemic disruptions). Forecasts need wide confidence bands and honest uncertainty communication.

3. **Deal cannibalization** — Aggressive deals may train customers to wait for discounts instead of booking at standard rates. Balancing deal frequency with full-price bookings is a delicate strategic question.

4. **Multi-source price attribution** — When a deal is detected, attributing it to the right source (airline promo vs. consolidator discount vs. distress inventory) determines commission structure and booking terms.

5. **Regulatory compliance** — India's Advertising Standards Council (ASCI) requires that "discounts" be genuine and "limited time" offers actually be limited. Misleading deal claims can result in regulatory action.

---

## Next Steps

- [ ] Build deal detection engine with price monitoring and threshold alerts
- [ ] Create deal generation pipeline from inventory distress and supplier promos
- [ ] Implement price forecasting model with historical analysis
- [ ] Design price alert system with push notifications
- [ ] Study deal platforms (Hopper, Secret Flying, The Points Guy, Skyscanner price alerts)
