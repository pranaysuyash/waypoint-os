# Analytics — Automated Insights & Anomaly Detection

> Research document for automated insight generation, anomaly detection, and proactive analytics.

---

## Key Questions

1. **What business anomalies should the system detect automatically?**
2. **How do we surface insights without creating noise?**
3. **What statistical methods are appropriate for travel industry data?**
4. **How do we distinguish real anomalies from seasonal patterns?**
5. **What's the right delivery mechanism for automated insights?**

---

## Research Areas

### Anomaly Detection Types

```typescript
type AnomalyType =
  // Revenue anomalies
  | 'revenue_drop'              // Revenue significantly below forecast
  | 'margin_compression'        // Margins shrinking unexpectedly
  | 'booking_volume_change'     // Sudden spike or drop in bookings
  // Operational anomalies
  | 'spine_run_failure_spike'   // Processing failures increasing
  | 'supplier_quality_drop'     // Supplier complaints or failures rising
  | 'response_time_degradation' // Agent response times increasing
  // Customer anomalies
  | 'churn_risk'                // Customer showing disengagement signals
  | 'complaint_spike'           // Customer complaints increasing
  | 'cancellation_rate_increase' // Cancellation rate above normal
  // Market anomalies
  | 'price_anomaly'             // Competitor prices significantly changed
  | 'demand_shift'              // Booking patterns shifting to new destinations
  | 'seasonal_deviation';       // Pattern differs from historical seasonal norms

interface AnomalyDetection {
  anomalyType: AnomalyType;
  method: DetectionMethod;
  sensitivity: number;
  baselineWindow: string;
  alertThreshold: number;
}

type DetectionMethod =
  | 'statistical_control'       // Control charts, 3-sigma
  | 'moving_average'            // Deviation from moving average
  | 'seasonal_decomposition'    // Remove seasonality, detect residual anomalies
  | 'machine_learning'          // Isolation forest, autoencoders
  | 'rule_based';               // Business rules (e.g., cancellation > 20%)
```

### Insight Generation

```typescript
interface Insight {
  insightId: string;
  type: InsightType;
  severity: 'informational' | 'actionable' | 'urgent';
  title: string;
  description: string;
  evidence: InsightEvidence[];
  recommendation: string;
  affectedEntities: AffectedEntity[];
  expiresAt: Date;
}

type InsightType =
  | 'trend'             // "Bookings to Thailand are up 40% this month"
  | 'anomaly'           // "Cancellations are 3x higher than usual"
  | 'opportunity'       // "Goa bookings spike during Diwali — increase inventory"
  | 'risk'              // "Supplier X has 30% complaint rate this week"
  | 'benchmark'         // "Your conversion rate is 15% below team average"
  | 'forecast';         // "Expected 200 bookings next week based on pipeline"

interface InsightEvidence {
  metric: string;
  currentValue: number;
  expectedValue: number;
  deviation: number;
  dataPoints: number;
  confidence: number;
}
```

### Proactive Analytics Delivery

```typescript
interface InsightDelivery {
  channel: 'dashboard_widget' | 'daily_digest' | 'real_time_alert' | 'weekly_report';
  frequency: string;
  recipientRoles: string[];
  format: 'card' | 'email' | 'push' | 'in_app';
}
```

---

## Open Problems

1. **Seasonal vs. anomalous** — Travel is inherently seasonal. A spike in Goa bookings in December isn't anomalous — it's expected. Need seasonal decomposition.

2. **Statistical significance with small samples** — When a destination has only 10 bookings/week, anomaly detection is noisy. Need Bayesian approaches for small samples.

3. **Insight fatigue** — Too many automated insights are worse than none. Need to rank insights by actionability and impact.

4. **Causality vs. correlation** — "Bookings dropped when we changed the intake form" — is it causation or coincidence? Automated systems struggle with causal inference.

5. **Cold start** — New agency has no historical data. How to generate insights without a baseline?

---

## Next Steps

- [ ] Research anomaly detection libraries (Prophet, Anodot, custom)
- [ ] Design seasonal decomposition pipeline for travel data
- [ ] Create insight ranking and prioritization algorithm
- [ ] Study automated insight delivery patterns (Google Analytics Intelligence, Mixpanel)
- [ ] Prototype anomaly detection for booking volume and cancellation rate
