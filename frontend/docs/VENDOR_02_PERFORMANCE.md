# Vendor Performance — KPI Tracking & Scorecards

> Research document for measuring, tracking, and acting on supplier performance.

---

## Key Questions

1. **Which performance indicators actually predict booking outcome quality?**
2. **How do we collect performance data without creating reporting burden for suppliers?**
3. **What's the right scoring model — weighted composite, traffic-light, or percentile-based?**
4. **How do we compare performance across heterogeneous supplier types (hotels vs. guides vs. airlines)?**
5. **What triggers a supplier moving between tiers (preferred → approved → probationary)?**
6. **How do we isolate supplier performance from booking complexity factors?**

---

## Research Areas

### Performance KPI Framework

```typescript
interface SupplierKPI {
  kpiId: string;
  category: KPICategory;
  name: string;
  description: string;
  measurementUnit: string;
  dataSource: 'automated' | 'reported' | 'surveyed';
  targetValue: number;
  warningThreshold: number;
  criticalThreshold: number;
  weight: number;  // 0-1, for composite scoring
}

type KPICategory =
  | 'quality'        // Service quality metrics
  | 'reliability'    // Consistency and dependability
  | 'responsiveness' // Communication and turnaround
  | 'financial'      // Payment and pricing behavior
  | 'compliance'     // Regulatory and contractual adherence
  | 'customer_satisfaction';  // End-customer feedback
```

### KPI Examples by Category

**Quality:**
- Service delivery match rate (booked vs. delivered)
- Customer satisfaction score (post-stay/flight/activity survey)
- Complaint rate per 100 bookings
- Quality audit scores (for inspected suppliers)

**Reliability:**
- Confirmation turnaround time
- Overbooking incident rate
- Last-minute cancellation rate
- On-time performance (transfers, activities)
- Availability accuracy (inventory shown vs. actually available)

**Responsiveness:**
- Average response time to booking requests
- Average response time to modification requests
- Average response time to complaints
- Resolution rate for issues

**Financial:**
- Commission payment timeliness
- Invoice accuracy rate
- Price competitiveness vs. market
- Rate parity compliance

**Compliance:**
- Credential currency rate (% of valid certifications)
- Contract adherence score
- Regulatory violation count
- Data privacy compliance

**Data collection questions:**
- Which KPIs can be automatically derived from booking data?
- Which require explicit customer feedback?
- Which need supplier self-reporting?
- What's the minimum data collection threshold for a reliable score?

### Scorecard Model

```typescript
interface SupplierScorecard {
  supplierId: string;
  period: ScoringPeriod;
  overallScore: number;         // 0-100 composite
  categoryScores: CategoryScore[];
  trend: 'improving' | 'stable' | 'declining';
  tierRecommendation: SupplierTier;
  reviewNotes: string[];
  flaggedIssues: FlaggedIssue[];
}

interface CategoryScore {
  category: KPICategory;
  score: number;                // 0-100
  trend: 'improving' | 'stable' | 'declining';
  contributingKPIs: KPIScore[];
}

interface KPIScore {
  kpiId: string;
  value: number;
  score: number;                // Normalized to 0-100
  trend: 'improving' | 'stable' | 'declining';
}

interface FlaggedIssue {
  issueId: string;
  severity: 'warning' | 'critical';
  description: string;
  detectedAt: Date;
  actionRequired: string;
}

type ScoringPeriod = 'monthly' | 'quarterly' | 'annual';
```

**Open questions:**
- How many bookings are needed for statistically meaningful scores?
- Should new suppliers have a "no data" state or a neutral starting score?
- How to handle seasonal suppliers (ski resorts) who only operate part of the year?

### Tier Management Rules

**Research needed:**
- What thresholds trigger tier promotions and demotions?
- How long should a supplier sustain improved performance before promotion?
- What's the appeal process for tier demotion?
- How do tier changes affect booking routing (auto-preferred vs. manual selection)?

---

## Open Problems

1. **Small sample bias** — A supplier with 3 bookings has noisy performance data. How to build confidence-adjusted scores?

2. **Attribution problem** — A bad hotel experience could be the hotel's fault, the agent's poor recommendation, or external factors (weather, strike). How to isolate supplier performance?

3. **Gaming the metrics** — Suppliers may optimize for measured KPIs at the expense of unmeasured quality. Need balanced scorecard design.

4. **Cross-category normalization** — Hotels, airlines, and tour operators have fundamentally different service delivery models. Comparing them on the same scale is misleading.

5. **Real-time vs. periodic scoring** — Real-time scoring catches issues faster but may overreact to single incidents. Periodic scoring is smoother but slower to detect problems.

---

## Next Steps

- [ ] Research vendor performance scoring models in travel industry
- [ ] Design category-specific KPI sets for top 5 supplier types
- [ ] Study statistical methods for small-sample performance estimation
- [ ] Prototype scorecard visualization and dashboard
- [ ] Investigate automated data collection from booking pipeline events
