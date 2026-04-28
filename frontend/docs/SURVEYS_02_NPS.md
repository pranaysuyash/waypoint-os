# Surveys & Feedback Collection — NPS & Satisfaction Metrics

> Research document for Net Promoter Score, customer satisfaction tracking, and sentiment analytics.

---

## Key Questions

1. **How do we measure and track NPS for the agency?**
2. **What satisfaction metrics are most actionable?**
3. **How do we analyze feedback sentiment at scale?**
4. **What's the benchmark for travel industry satisfaction?**
5. **How do metrics drive operational improvements?**

---

## Research Areas

### NPS Framework

```typescript
interface NPSMetrics {
  period: string;
  score: number;                      // -100 to +100
  responses: number;
  breakdown: NPSBreakdown;
  trend: NPSTrend;
  segments: NPSSegment[];
}

interface NPSBreakdown {
  promoters: number;                  // Score 9-10 (% of respondents)
  passives: number;                   // Score 7-8
  detractors: number;                 // Score 0-6
}

interface NPSTrend {
  currentScore: number;
  previousScore: number;
  change: number;
  quarterlyHistory: { quarter: string; score: number }[];
}

interface NPSSegment {
  segment: string;
  score: number;
  responses: number;
}

// NPS calculation:
// NPS = % Promoters - % Detractors
// Example: 60% promoters, 20% passives, 20% detractors
// NPS = 60 - 20 = 40

// NPS benchmarks (travel industry):
// Excellent: 50+ (world-class)
// Good: 30-50 (above average)
// Average: 0-30 (typical for travel agencies)
// Below average: <0 (needs improvement)
//
// Indian travel agency average: ~25-35
// Online travel agencies (MakeMyTrip, Cleartrip): ~20-30
// Premium travel agencies: ~40-50
// Luxury travel operators: ~50-60

// NPS by segment:
// By trip type: Leisure vs. Corporate vs. MICE
// By destination: Domestic vs. International
// By budget: Budget vs. Mid-range vs. Premium
// By agent: Per-agent NPS (for performance tracking)
// By customer age: Gen Z vs. Millennial vs. Gen X vs. Boomer
// By trip size: Solo vs. Couple vs. Family vs. Group
```

### CSAT Metrics

```typescript
interface CSATFramework {
  metrics: CSATMetric[];
  targets: CSATTarget[];
}

interface CSATMetric {
  name: string;
  measurement: string;
  scale: string;
  collectionPoint: string;
  frequency: string;
}

// Customer satisfaction metrics:
//
// Overall Trip Satisfaction (1-5):
//   "How would you rate your overall trip experience?"
//   Collected: 2 days after trip completion
//   Target: > 4.2
//
// Agent Service Rating (1-5):
//   "How would you rate your agent's service?"
//   Collected: 2 days after trip completion
//   Target: > 4.5
//
// Itinerary Quality (1-5):
//   "How well did the itinerary match your expectations?"
//   Target: > 4.0
//
// Value for Money (1-5):
//   "How would you rate the value for money?"
//   Target: > 3.8
//
// Communication Quality (1-5):
//   "How satisfied were you with communication during your trip?"
//   Target: > 4.3
//
// Problem Resolution (1-5):
//   "If you had an issue during your trip, how well was it resolved?"
//   Target: > 4.0
//
// Would Book Again (%):
//   "Would you book with us again?"
//   Target: > 80%
//
// Response Rate:
//   What % of surveyed customers respond
//   Target: > 30%

// Operational metrics that correlate with satisfaction:
// Average response time (customer message → agent reply)
// Booking accuracy rate (% of bookings with no errors)
// Cancellation rate (% of bookings cancelled)
// Refund processing time (days from cancellation to refund)
// Document delivery time (days from booking to document delivery)
// Issue resolution time (hours from issue reported to resolved)
```

### Sentiment Analysis

```typescript
interface SentimentAnalysis {
  feedbackId: string;
  text: string;
  sentiment: SentimentScore;
  topics: TopicExtraction[];
  actionItems: ActionItem[];
}

interface SentimentScore {
  overall: 'positive' | 'neutral' | 'negative' | 'mixed';
  confidence: number;
  scores: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

interface TopicExtraction {
  topic: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  relevance: number;
  keywords: string[];
}

// Sentiment analysis on free-text feedback:
// Input: "The hotels were great but the airport transfer was late.
//         Our agent Priya was very helpful throughout."
//
// Analysis:
// Sentiment: Mixed (positive overall, negative on specific topic)
// Topics:
//   - Hotels: Positive (confidence: 0.92)
//   - Airport transfer: Negative (confidence: 0.88)
//   - Agent service: Positive (confidence: 0.95, mentions "Priya")
//
// Action Items:
//   - Flag transfer issue to operations team
//   - Positive feedback for agent Priya
//   - No escalation needed (overall positive)

// Topic categories for travel feedback:
// Accommodation: Room quality, cleanliness, location, amenities
// Transportation: Flights, transfers, car quality, driver behavior
// Activities: Tour quality, guide knowledge, value for money
// Food: Restaurant quality, dietary accommodation, variety
// Communication: Agent responsiveness, clarity, proactiveness
// Documentation: Itinerary quality, voucher accuracy, timeliness
// Value: Pricing transparency, hidden costs, perceived value
// Problem handling: Issue resolution speed, fairness, empathy

// Dashboard insights:
// "Top positive themes this month: Agent responsiveness (+15%),
//  Hotel quality (+10%), Smooth bookings (+8%)"
// "Top negative themes: Airport transfer delays (-12%),
//  Price transparency (-8%), Visa processing time (-5%)"
```

---

## Open Problems

1. **NPS timing** — NPS collected right after a trip (honeymoon glow) vs. 3 months later (reality check) gives different results. When to measure?

2. **Low response rate** — 30% response rate means 70% of opinions are unknown. The silent majority may have very different views.

3. **Sentiment accuracy** — Indian English has unique expressions ("not bad" = good, "just okay" = disappointed). NLP models trained on Western English may misinterpret.

4. **Metric manipulation** — Agents asking customers to give 10/10 skews NPS. Need anonymous collection and pattern detection.

5. **Actionability** — Collecting metrics is easy; acting on them is hard. Need a clear feedback-to-improvement pipeline.

---

## Next Steps

- [ ] Design NPS tracking framework with segment analysis
- [ ] Build CSAT metric collection at key touchpoints
- [ ] Create sentiment analysis pipeline for free-text feedback
- [ ] Design satisfaction analytics dashboard
- [ ] Study customer experience metrics (Qualtrics, Medallia, Satmetrix NPS)
