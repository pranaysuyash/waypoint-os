# Pricing Engine — Revenue Forecasting & Optimization

> Research document for revenue forecasting, pricing experiments, and revenue management strategies.

---

## Key Questions

1. **How do we forecast revenue at the trip, agent, and company level?**
2. **What pricing experiments can we run, and how do we measure impact?**
3. **How do we optimize pricing across the portfolio (not per-booking)?**
4. **What's the revenue impact of different pricing strategies?**
5. **How do we forecast demand to inform pricing decisions?**

---

## Research Areas

### Revenue Forecasting

```typescript
interface RevenueForecast {
  level: 'trip' | 'agent' | 'team' | 'company';
  period: DateRange;
  forecast: ForecastDataPoint[];
  methodology: ForecastMethod;
  confidence: number;
  assumptions: string[];
}

interface ForecastDataPoint {
  date: Date;
  predictedRevenue: number;
  predictedBookings: number;
  predictedMargin: number;
  confidenceInterval: [number, number];
}

type ForecastMethod =
  | 'pipeline_weighted'      // Weight deals by probability
  | 'historical_trend'       // Extrapolate from past data
  | 'seasonal_decomposition' // Separate trend + seasonality
  | 'ml_model'               // Machine learning forecast
  | 'ensemble';              // Combine multiple methods

// Pipeline-weighted forecast:
// Deal A: ₹1L × 80% probability = ₹80K
// Deal B: ₹3L × 30% probability = ₹90K
// Deal C: ₹50K × 90% probability = ₹45K
// Forecast: ₹2.15L
```

### Pricing Experiments

```typescript
interface PricingExperiment {
  experimentId: string;
  name: string;
  hypothesis: string;
  variants: PricingVariant[];
  trafficAllocation: number;     // % of traffic in experiment
  duration: string;
  metrics: ExperimentMetric[];
  status: 'draft' | 'running' | 'completed';
  result?: ExperimentResult;
}

interface PricingVariant {
  variantId: string;
  name: string;
  pricingStrategy: string;
  markupAdjustment: number;
  priceDisplay: string;
}

// Example experiments:
// 1. "Show savings badge" — Show "Save 15%" vs. no badge
// 2. "Bundle discount" — 10% off for flight+hotel vs. separate pricing
// 3. "Premium tier positioning" — Lead with premium option vs. budget
// 4. "Dynamic markup" — Demand-based markup vs. fixed markup
// 5. "Price anchoring" — Show original price vs. show only current price
```

### Portfolio Pricing Optimization

```typescript
interface PortfolioOptimization {
  // Optimize across all products, not individually
  objective: 'maximize_revenue' | 'maximize_margin' | 'maximize_bookings';
  constraints: OptimizationConstraint[];
  recommendations: PricingRecommendation[];
  projectedImpact: ImpactProjection;
}

interface OptimizationConstraint {
  type: 'min_margin' | 'max_price' | 'parity' | 'contractual' | 'competitive';
  value: number;
  description: string;
}

interface PricingRecommendation {
  product: string;
  segment: string;
  currentPrice: number;
  recommendedPrice: number;
  change: number;
  changePercent: number;
  expectedImpact: {
    revenueDelta: number;
    bookingVolumeDelta: number;
    marginDelta: number;
  };
  confidence: number;
  reasoning: string;
}
```

---

## Open Problems

1. **Experiment interference** — Running multiple pricing experiments simultaneously may interfere with each other. Need proper experimental design.

2. **Price elasticity estimation** — How sensitive are our customers to price changes? Need historical A/B data that we don't have yet.

3. **Seasonal optimization** — Peak season pricing should maximize margin; off-season should maximize volume. Different optimization objectives per season.

4. **Customer perception** — Frequent price changes may be perceived as unfair or manipulative. Need to balance optimization with trust.

5. **Attribution** — Did revenue increase because of pricing changes, marketing campaigns, or seasonal demand? Isolating pricing impact is hard.

---

## Next Steps

- [ ] Design revenue forecasting pipeline with multiple methodologies
- [ ] Build pricing experiment framework with statistical significance tracking
- [ ] Study price elasticity estimation methods
- [ ] Design portfolio optimization model with constraints
- [ ] Research revenue management systems in hospitality/airlines
