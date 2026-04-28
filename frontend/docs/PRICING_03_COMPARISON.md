# Pricing Engine — Price Comparison & Rate Parity

> Research document for price comparison across channels, rate parity monitoring, and competitive positioning.

---

## Key Questions

1. **How do we monitor competitor pricing without violating terms of service?**
2. **What's rate parity, and how do we handle parity violations by suppliers?**
3. **How do we present price comparisons to customers (cheapest, best value, premium)?**
4. **What's the architecture for real-time price comparison across suppliers?**
5. **How do we handle currency differences when comparing international prices?**

---

## Research Areas

### Competitive Price Monitoring

```typescript
interface PriceMonitor {
  monitorId: string;
  service: string;                  // "hotel_marriott_mumbai"
  suppliers: SupplierPrice[];
  competitors: CompetitorPrice[];
  lastChecked: Date;
  checkFrequency: string;
}

interface SupplierPrice {
  supplierId: string;
  price: number;
  currency: string;
  availability: boolean;
  terms: string;
  source: 'api' | 'scraped' | 'manual';
  fetchedAt: Date;
}

interface CompetitorPrice {
  competitor: string;               // "booking.com", "makemytrip.com"
  price: number;
  currency: string;
  url: string;
  inclusions: string[];             // Breakfast, wifi, etc.
  fetchedAt: Date;
}

// Price comparison normalization:
// 1. Convert all to base currency (INR)
// 2. Normalize inclusions (add/subtract for breakfast, etc.)
// 3. Adjust for cancellation policy flexibility
// 4. Account for loyalty program value
```

### Rate Parity Management

```typescript
interface RateParityCheck {
  checkId: string;
  supplierId: string;
  ourRate: number;
  marketRates: MarketRate[];
  parityStatus: ParityStatus;
  violations: ParityViolation[];
  checkedAt: Date;
}

type ParityStatus =
  | 'at_parity'           // Our rate matches market
  | 'below_parity'        // We're cheaper (good for customer)
  | 'above_parity'        // We're more expensive (risk)
  | 'insufficient_data';  // Can't compare

interface ParityViolation {
  competitor: string;
  theirRate: number;
  ourRate: number;
  difference: number;
  differencePercent: number;
  action: ParityAction;
}

type ParityAction =
  | 'alert_supplier'      // Ask supplier to fix
  | 'match_rate'          // Lower our rate
  | 'add_value'           // Keep rate but add perks
  | 'accept_difference'   // Premium positioning
  | 'escalate';           // Management decision
```

### Price Presentation Strategies

```typescript
interface PricePresentation {
  strategy: PresentationStrategy;
  options: PriceOption[];
  recommendation: PriceRecommendation;
}

type PresentationStrategy =
  | 'lowest_first'          // Show cheapest option prominently
  | 'best_value'            // Highlight best value (price/quality ratio)
  | 'premium_first'         // Lead with premium, show budget as alternative
  | 'comparison_table'      // Side-by-side comparison
  | 'price_range'           // Show range with "from" pricing
  | 'tiered';               // Budget / Standard / Premium tiers

interface PriceOption {
  optionId: string;
  name: string;
  price: number;
  savings?: number;             // vs. regular price
  savingsPercent?: number;
  badge?: 'best_value' | 'lowest_price' | 'premium' | 'popular';
  inclusions: string[];
  exclusions: string[];
  rating: number;
}
```

---

## Open Problems

1. **Scraping legality** — Scraping competitor prices may violate their terms of service. Need legitimate data sources or partnerships.

2. **Real-time comparison cost** — Checking 5 suppliers + 3 competitors for every search is expensive and slow. Caching helps but introduces staleness.

3. **Apple-to-apple comparison** — A ₹5,000 room on MakeMyTrip with breakfast vs. ₹4,500 on our platform without breakfast. How to normalize inclusions?

4. **Rate parity enforcement** — Suppliers may offer lower rates on OTAs that violate our contract. Confronting suppliers risks the relationship.

5. **Price transparency backlash** — Showing "cheapest option is elsewhere" builds trust but loses the booking. Showing only our rates builds revenue but risks discovery.

---

## Next Steps

- [ ] Research legitimate price comparison data sources
- [ ] Design rate parity monitoring system
- [ ] Study price normalization algorithms for inclusions/policies
- [ ] Design price presentation A/B testing framework
- [ ] Map rate parity clauses in standard supplier contracts
