# Supplier Relationship & Contract Intelligence — Performance Scoring

> Research document for supplier performance measurement, scoring frameworks, SLA tracking, performance-based tiering, and automated review aggregation.

---

## Key Questions

1. **What metrics should we track to score supplier performance objectively?**
2. **How do we build a performance dashboard segmented by supplier category (hotels, airlines, transport, activities)?**
3. **How do we define, track, and manage SLAs with measurable breach consequences?**
4. **What does a performance-based tiering system (gold/silver/bronze) look like with real consequences?**
5. **How do we automatically rotate underperforming suppliers out of recommendations?**
6. **How do we aggregate and analyze customer reviews to feed into supplier performance scores?**

---

## Research Areas

### Performance Scoring Framework

```typescript
interface SupplierPerformanceScore {
  supplierId: string;
  supplierName: string;
  category: SupplierCategory;
  overallScore: number;               // 0-100 weighted composite
  grade: PerformanceGrade;
  dimensions: PerformanceDimension[];
  trend: ScoreTrend;
  lastEvaluated: Date;
  evaluationPeriod: DateRange;
}

type PerformanceGrade = 'gold' | 'silver' | 'bronze' | 'at_risk' | 'suspended';

interface PerformanceDimension {
  dimension: PerformanceDimensionType;
  weight: number;                     // % weight in overall score
  score: number;                      // 0-100
  metrics: PerformanceMetric[];
  trend: 'improving' | 'stable' | 'declining';
  lastIncident?: Date;
}

type PerformanceDimensionType =
  | 'service_quality'                 // Customer satisfaction, complaint rate
  | 'responsiveness'                  // Response time, confirmation speed
  | 'issue_resolution'               // How quickly problems are resolved
  | 'price_competitiveness'          // Rate comparison vs. market
  | 'reliability'                     // Confirmation rate, no-show rate
  | 'compliance';                     // GST filing, TDS, documentation quality

// Dimension weights by supplier category:
//
// Dimension            | Hotels | Airlines | Transport | Activities
// ---------------------|--------|----------|-----------|----------
// Service Quality      |  25%   |   20%    |   20%     |   30%
// Responsiveness       |  20%   |   15%    |   25%     |   15%
// Issue Resolution     |  15%   |   15%    |   20%     |   20%
// Price Competitiveness|  20%   |   25%    |   15%     |   15%
// Reliability          |  15%   |   20%    |   15%     |   15%
// Compliance           |   5%   |    5%    |    5%     |    5%
// TOTAL                | 100%   |  100%    |  100%     |  100%

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;                       // "hours", "%", "count", "score"
  target: number;
  threshold: {
    good: number;                     // At or above = good
    acceptable: number;               // At or above = acceptable
    poor: number;                     // Below = poor
  };
  dataPoints: number;                 // How many data points this is based on
  trend: 'improving' | 'stable' | 'declining';
}

// Metric examples per dimension:
//
// Service Quality:
// - Customer satisfaction score (from post-trip surveys): target 4.2/5
// - Complaint rate: target < 3% of bookings
// - NPS from supplier-specific feedback: target > 40
// - Amenity accuracy (what was promised vs. delivered): target 95%+
//
// Responsiveness:
// - Average confirmation time: target < 4 hours
// - Query response time: target < 2 hours (business hours)
// - Availability rate (answer calls/messages): target 90%+
// - Off-hours support availability: measured per SLA
//
// Issue Resolution:
// - Average resolution time: target < 24 hours
// - First-contact resolution rate: target 70%+
// - Escalation rate (issues needing management intervention): target < 10%
// - Repeat issue rate (same problem recurs): target < 5%
//
// Price Competitiveness:
// - Rate vs. market average: target at or below market
// - Rate parity compliance: target 95%+
// - Rate increase vs. inflation: target within 2x inflation
// - Promotional rate availability: measured vs. OTAs
//
// Reliability:
// - Confirmation rate (confirmed vs. requested): target 95%+
// - Overbooking incidents: target 0
// - No-show by supplier (booked but unavailable): target < 1%
// - Service delivery as promised: target 98%+
//
// Compliance:
// - GST invoice accuracy: target 100%
// - GST filing status (GSTR-1 filed on time): target 100%
// - TDS compliance: target 100%
// - Documentation completeness: target 95%+
```

### Performance Dashboard by Category

```typescript
interface PerformanceDashboard {
  category: SupplierCategory;
  period: DateRange;
  summary: CategorySummary;
  suppliers: SupplierScoreCard[];
  alerts: PerformanceAlert[];
}

interface CategorySummary {
  totalSuppliers: number;
  activeSuppliers: number;
  averageScore: number;
  scoreDistribution: {
    gold: number;
    silver: number;
    bronze: number;
    atRisk: number;
    suspended: number;
  };
  topPerformers: string[];           // Supplier names
  bottomPerformers: string[];
  averageResponseTime: string;
  averageSatisfactionScore: number;
}

interface SupplierScoreCard {
  supplierId: string;
  supplierName: string;
  overallScore: number;
  grade: PerformanceGrade;
  bookingsThisPeriod: number;
  revenueThisPeriod: number;
  dimensionScores: Record<string, number>;
  flags: PerformanceFlag[];
}

type PerformanceFlag =
  | 'score_declining'               // Score dropped > 5 points this period
  | 'high_complaint_rate'           // Complaints > 5%
  | 'slow_response'                 // Response time > 2x target
  | 'overbooking_incident'          // Supplier overbooked
  | 'gst_non_compliant'             // GST filing issues
  | 'contract_expiring'             // Contract renewal due in 30 days
  | 'price_increase_pending'        // Rate increase > 10% proposed
  | 'new_supplier'                  // < 6 months relationship
  | 'under_investigation';          // Formal issue being investigated

// Performance dashboard UI sketch (Hotel category):
//
// +------------------------------------------------------------------+
// | Supplier Performance — Hotels | April 2026                       |
// +------------------------------------------------------------------+
// | Overview                                                          |
// | [42 Active] [Avg: 74] [Gold: 8] [Silver: 18] [Bronze: 12]       |
// | [At Risk: 3] [Suspended: 1]                                      |
// +------------------------------------------------------------------+
// | Supplier            | Score | Grade | Bookings | Revenue | Flags  |
// |---------------------|-------|-------|----------|---------|--------|
// | Taj Lake Palace     |  92   |  🥇   |   87     | ₹24.5L  |        |
// | Oberoi Udaivilas    |  88   |  🥇   |   62     | ₹18.2L  |        |
// | ITC Grand Chola     |  81   |  🥈   |   95     | ₹21.0L  |        |
// | Lemon Tree Goa      |  73   |  🥈   |   45     | ₹5.8L   | ⚠️slow |
// | Hotel Sea Queen     |  58   |  🥉   |   22     | ₹2.1L   | ⚠️2flg |
// | Paradise Inn Kochi  |  42   |  ⚠️   |    8     | ₹0.9L   | 🔴inv  |
// +------------------------------------------------------------------+
// | Click supplier for detailed scorecard                             |
// +------------------------------------------------------------------+
```

### SLA Tracking & Breach Management

```typescript
interface SLAConfig {
  supplierId: string;
  category: SupplierCategory;
  effectiveDate: Date;
  terms: SLATerm[];
  breachPenalties: BreachPenalty[];
  escalationContacts: EscalationContact[];
}

interface SLATerm {
  metric: string;
  target: string;                     // "95%", "<4 hours", "100%"
  measurement: SLAMeasurement;
  consequences: SLAConsequence;
}

interface SLAMeasurement {
  frequency: 'per_interaction' | 'daily' | 'weekly' | 'monthly';
  dataSource: string;                 // "confirmation_timestamp", "survey_response"
  calculationMethod: string;          // "average", "percentage_above_threshold"
}

// Standard SLA terms by category:
//
// Hotels:
// - Booking confirmation: Within 4 business hours
// - Rate parity: 95% compliance (OTA rate not lower than our rate)
// - Check-in guarantee: 100% (no overbooking walk-outs)
// - Issue response: Within 2 hours during business hours
// - Invoice delivery: Within 48 hours of checkout
// - Guest satisfaction: Average 4.0/5.0 or above
//
// Airlines:
// - Ticketing: Within 30 minutes of booking (for published fares)
// - Schedule change notification: Within 24 hours of airline notification
// - Refund processing: Within 7 working days
// - BSP reconciliation: Monthly, within 5 business days of BSP cycle
//
// Transport:
// - Vehicle assignment: 24 hours before pickup
// - Driver details: 12 hours before pickup
// - Pickup punctuality: Within 10 minutes of scheduled time
// - Vehicle condition: AC functional, clean interior, safety equipment
// - Incident response: Within 30 minutes
//
// Activities:
// - Booking confirmation: Within 2 business hours
// - Guide assignment: 24 hours before activity
// - Safety briefing: Mandatory before any adventure activity
// - Weather cancellation: Alternative date or full refund within 24 hours

interface BreachPenalty {
  severity: 'minor' | 'major' | 'critical';
  occurrences: number;                // Number of breaches before penalty applies
  penalty: string;                    // "Rate reduction 2%", "Performance tier downgrade"
}

interface SLABreach {
  breachId: string;
  supplierId: string;
  slaTerm: string;
  expectedTarget: string;
  actualPerformance: string;
  breachDate: Date;
  severity: 'minor' | 'major' | 'critical';
  impact: string;                     // Description of customer impact
  affectedBookings: string[];
  resolution: {
    supplierNotified: Date;
    supplierResponse?: string;
    resolutionDate?: Date;
    correctiveAction?: string;
    penaltyApplied?: string;
  };
}

// SLA breach workflow:
//
// Minor breach (1st occurrence):
//   → Log breach, notify supplier
//   → No penalty, warning recorded
//
// Minor breach (2nd occurrence in 90 days):
//   → Formal warning email
//   → Score impact: -5 points
//
// Minor breach (3rd occurrence in 90 days):
//   → Escalates to major breach
//
// Major breach:
//   → Supplier tier downgrade
//   → Rate renegotiation trigger
//   → Score impact: -15 points
//   → Manager review
//
// Critical breach (overbooking, safety incident, fraud):
//   → Immediate suspension from recommendations
//   → Formal investigation
//   → Score impact: -30 points
//   → Owner notification
//   → Potential contract termination
```

### Performance-Based Supplier Tiering

```typescript
interface SupplierTiering {
  tiers: TierDefinition[];
  currentAssignments: TierAssignment[];
  promotionDemotionHistory: TierChange[];
}

interface TierDefinition {
  grade: PerformanceGrade;
  scoreRange: [number, number];       // [min, max]
  benefits: TierBenefit[];
  obligations: TierObligation[];
  reviewFrequency: string;            // "monthly", "quarterly"
}

// Tier definitions:
//
// GOLD (Score 85-100):
//   Benefits:
//   - Priority in search results and recommendations
//   - Featured in marketing materials
//   - Faster payment processing (7 days instead of 14)
//   - Higher allotment allocation
//   - First access to new business opportunities
//   - Annual performance bonus recognition
//   Obligations:
//   - Maintain score above 85
//   - Quarterly business review
//   - Annual contract renewal with pre-agreed terms
//
// SILVER (Score 70-84):
//   Benefits:
//   - Standard recommendation priority
//   - Normal payment terms (14 days)
//   - Included in seasonal promotions
//   Obligations:
//   - Maintain score above 70
//   - Semi-annual performance review
//
// BRONZE (Score 55-69):
//   Benefits:
//   - Included in search results but not prioritized
//   - Standard payment terms (14 days)
//   Obligations:
//   - Performance improvement plan if score drops below 55
//   - Monthly monitoring
//
// AT RISK (Score 40-54):
//   Benefits:
//   - Available in search but with warning badge
//   - Only assigned when gold/silver unavailable
//   Obligations:
//   - Formal improvement plan
//   - Weekly monitoring
//   - Contract review for termination
//
// SUSPENDED (Score 0-39):
//   Benefits:
//   - None. Removed from active supplier pool.
//   Obligations:
//   - Formal review for reactivation or termination
//   - All existing bookings honored, no new bookings

interface TierAssignment {
  supplierId: string;
  currentTier: PerformanceGrade;
  assignedDate: Date;
  nextReviewDate: Date;
  improvementPlan?: ImprovementPlan;
}

interface ImprovementPlan {
  supplierId: string;
  currentScore: number;
  targetScore: number;
  deadline: Date;
  actions: ImprovementAction[];
  checkins: Checkin[];
  outcome?: 'improved' | 'terminated' | 'extended';
}

interface ImprovementAction {
  action: string;
  responsible: 'supplier' | 'agency';
  dueDate: Date;
  status: 'pending' | 'in_progress' | 'completed';
}

interface TierChange {
  supplierId: string;
  date: Date;
  fromTier: PerformanceGrade;
  toTier: PerformanceGrade;
  reason: string;
  scoreAtChange: number;
}
```

### Automatic Supplier Rotation for Underperformers

```typescript
interface RotationEngine {
  rules: RotationRule[];
  queue: RotationCandidate[];
  executionLog: RotationExecution[];
}

interface RotationRule {
  trigger: RotationTrigger;
  action: RotationAction;
  notificationTargets: string[];
  cooldown: string;                   // "30 days" before re-evaluating
}

type RotationTrigger =
  | { type: 'score_threshold'; tier: 'at_risk' | 'suspended' }
  | { type: 'breach_count'; count: number; period: string }
  | { type: 'complaint_rate'; rate: number; period: string }
  | { type: 'confirmation_rate'; rate: number; period: string }
  | { type: 'response_time'; hours: number };

interface RotationAction {
  type: RotationActionType;
  parameters: Record<string, string>;
}

type RotationActionType =
  | 'reduce_recommendation_weight'     // Show less frequently in search
  | 'add_warning_badge'                // "⚠️ Performance concerns" in UI
  | 'require_agent_approval'           // Can't auto-book, agent must approve
  | 'restrict_to_familiarity_bookings' // Only agents who've used them before
  | 'remove_from_search'               // Don't show in search results at all
  | 'suspend_new_bookings'             // No new bookings, honor existing only
  | 'activate_alternative'             // Auto-suggest alternative suppliers
  | 'notify_management';              // Alert owner/manager

// Rotation workflow:
//
// Step 1: Detection (automated, daily)
//   Score drops below threshold OR SLA breach count exceeds limit
//
// Step 2: Verification (automated + manual)
//   System flags supplier, manager reviews in 24 hours
//   Confirm it's not a data anomaly or temporary issue
//
// Step 3: Action (based on severity)
//   At Risk: Reduce recommendation weight, add warning badge
//   Persistent issues: Require agent approval for new bookings
//   Critical: Suspend new bookings, activate alternatives
//
// Step 4: Communication
//   Notify supplier with specific improvement areas
//   Notify affected agents (existing bookings)
//   Update alternative supplier recommendations
//
// Step 5: Monitoring
//   Track improvement (or further decline)
//   Weekly check-in during improvement period
//   Reinstate or terminate based on outcome
//
// Important consideration:
// Rotation should never strand existing bookings. Customers who have
// confirmed bookings with the rotated supplier should be insulated from
// the performance issue (unless it directly affects their trip).
// In that case, proactive rebooking with an alternative supplier.
```

### Review Aggregation from Customer Feedback

```typescript
interface ReviewAggregation {
  supplierId: string;
  period: DateRange;
  aggregatedScore: AggregatedReviewScore;
  reviewBreakdown: ReviewBreakdown;
  sentimentAnalysis: SentimentAnalysis;
  actionableInsights: ActionableInsight[];
}

interface AggregatedReviewScore {
  overallScore: number;               // 0-5, weighted average
  totalReviews: number;
  reviewDistribution: {
    fiveStar: number;
    fourStar: number;
    threeStar: number;
    twoStar: number;
    oneStar: number;
  };
  responseRate: number;               // % of reviews supplier responded to
}

interface ReviewBreakdown {
  categories: ReviewCategoryScore[];
}

interface ReviewCategoryScore {
  category: string;                   // "cleanliness", "location", "staff"
  score: number;
  reviewCount: number;
  topPositiveThemes: string[];
  topNegativeThemes: string[];
}

interface SentimentAnalysis {
  overallSentiment: 'positive' | 'neutral' | 'negative';
  sentimentScore: number;             // -1 to +1
  keyPhrases: {
    positive: string[];
    negative: string[];
  };
  trendingTopics: TrendingTopic[];
}

interface TrendingTopic {
  topic: string;
  sentiment: 'positive' | 'negative';
  frequency: number;                  // How often mentioned
  trend: 'increasing' | 'stable' | 'decreasing';
}

interface ActionableInsight {
  insight: string;
  source: 'internal_reviews' | 'google_reviews' | 'tripadvisor'
         | 'ota_reviews' | 'social_media';
  severity: 'opportunity' | 'warning' | 'critical';
  recommendedAction: string;
  relatedReviews: string[];           // Review IDs
}

// Review aggregation workflow:
//
// 1. Collect:
//    - Internal post-trip surveys (agency's own feedback)
//    - Google Reviews (public, via API)
//    - TripAdvisor reviews (public, via scraping or API)
//    - OTA reviews (MakeMyTrip, Goibibo — if accessible)
//    - Social media mentions (Instagram, Twitter/X)
//
// 2. Normalize:
//    - Different platforms use different scales (1-5, 1-10, thumbs up/down)
//    - Different review criteria per platform
//    - Time-weighting (recent reviews matter more)
//    - Volume weighting (100 reviews > 5 reviews)
//
// 3. Analyze:
//    - Sentiment analysis on review text
//    - Theme extraction (cleanliness, food, location, staff, value)
//    - Trend detection (improving vs. declining)
//    - Comparison with competitors in same geography
//
// 4. Integrate:
//    - Feed review scores into performance scoring
//    - Surface actionable insights to agents
//    - Alert on sudden drops in review scores
//    - Identify training opportunities for suppliers
//
// Review-to-performance mapping:
//   Customer satisfaction dimension weight: 25% for hotels
//   Review score contributes 60% of customer satisfaction dimension
//   Internal survey contributes 30%
//   Complaint rate contributes 10%
```

---

## Open Problems

1. **Score manipulation risk** — Suppliers who know the scoring system may game specific metrics while neglecting others (e.g., fast response times but poor actual service quality). Need balanced scoring with unpredictable audit checks.

2. **Small sample sizes** — New suppliers or suppliers with few bookings have statistically unreliable scores. A single bad review can tank their rating. Need minimum data thresholds and Bayesian smoothing.

3. **Subjectivity in reviews** — Customer reviews are inherently subjective. A 3-star review from a luxury traveler vs. a budget traveler means very different things. Need reviewer-context normalization.

4. **Cross-platform review inconsistency** — A hotel might have 4.5 on Booking.com, 4.0 on TripAdvisor, and 3.8 on Google. Aggregating these fairly is non-trivial, especially with different review volumes per platform.

5. **Tier change frequency** — If a supplier oscillates between silver and bronze monthly, it creates instability for agents and customers. Need hysteresis in tier assignments (require sustained improvement before promotion).

6. **Review scraping legality** — Scraping reviews from OTAs and TripAdvisor may violate terms of service. Need to rely on APIs where available and understand legal boundaries for data collection.

---

## Next Steps

- [ ] Define complete metric set per supplier category with scoring weights
- [ ] Build performance score calculation engine with dimension aggregation
- [ ] Create performance dashboard UI with category-specific views
- [ ] Design SLA template per supplier category with breach workflows
- [ ] Build supplier tiering engine with automatic promotion/demotion logic
- [ ] Implement rotation engine for underperforming supplier management
- [ ] Build review aggregation pipeline (internal surveys + external sources)
- [ ] Research review APIs (Google Places, TripAdvisor, Booking.com)
- [ ] Design improvement plan workflow and tracking system
