# Customer Journey Orchestration — Journey Analytics & Optimization

> Research document for journey performance measurement, funnel analytics, friction detection, A/B testing, and continuous journey optimization.

---

## Key Questions

1. **How do we measure customer journey effectiveness end-to-end?**
2. **What funnel analytics identify conversion bottlenecks?**
3. **How does friction detection find pain points in the journey?**
4. **What A/B testing framework optimizes journey touchpoints?**
5. **How do we predict journey outcomes and intervene proactively?**

---

## Research Areas

### Journey Analytics Framework

```typescript
interface JourneyAnalyticsFramework {
  funnel: FunnelAnalytics;
  velocity: JourneyVelocity;
  quality: JourneyQualityMetrics;
  value: JourneyValueMetrics;
  prediction: JourneyPrediction;
}

// Journey analytics dashboard:
// ┌─────────────────────────────────────────┐
// │  Journey Analytics — April 2026           │
// │                                            │
// │  📊 Funnel Performance                    │
// │  Inquiries: 320                           │
// │  ████████████████████████████████████ 100%│
// │  Quotes sent: 256 (80%)                   │
// │  █████████████████████████████░░░░░░░ 80% │
// │  Quotes viewed: 198 (77% of sent)         │
// │  ███████████████████████████░░░░░░░░ 62%  │
// │  Negotiations: 142 (72% of viewed)        │
// │  █████████████████████░░░░░░░░░░░░░░ 44%  │
// │  Booked: 108 (76% of negotiated)          │
// │  █████████████████░░░░░░░░░░░░░░░░░░ 34%  │
// │  Traveled: 102 (94% of booked)            │
// │  ████████████████░░░░░░░░░░░░░░░░░░░ 32%  │
// │  Satisfied: 89 (87% of traveled)          │
// │  ██████████████░░░░░░░░░░░░░░░░░░░░░ 28%  │
// │  Repeat: 31 (35% of satisfied)            │
// │  █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 10%  │
// │                                            │
// │  ⚠️ Biggest drop-off: Quote viewed → Negotiation│
// │  28% of customers view quote but don't respond│
// │  Hypothesis: Price shock, slow follow-up  │
// │                                            │
// │  📈 Key Metrics                            │
// │  Avg inquiry → booking: 4.2 days          │
// │  Avg booking → travel: 18.5 days          │
// │  Avg trip value: ₹62,500                  │
// │  Customer LTV: ₹1,85,000                  │
// │  Journey NPS: 72                          │
// │                                            │
// │  [Explore Funnel] [Compare Periods]       │
// └─────────────────────────────────────────────┘

interface FunnelAnalytics {
  stages: FunnelStage[];
  conversionRates: ConversionRate[];
  dropOffAnalysis: DropOffAnalysis[];
  segmentComparison: SegmentFunnel[];
}

interface FunnelStage {
  name: string;
  count: number;
  percentageOfTotal: number;
  conversionFromPrevious: number;
  avgTimeToNext: string;               // "2.3 days"
  dropOffReasons: DropOffReason[];
}

interface DropOffReason {
  reason: string;
  percentage: number;
  evidence: string;                    // Data source supporting this reason
}

// Drop-off analysis examples:
//
// AWARENESS → CONSIDERATION (36% drop):
// Reasons:
// • 45% — No response from agent (>15 min wait)
// • 25% — Generic auto-response, not personalized
// • 15% — Customer was just browsing, not serious
// • 10% — Customer chose a different agency
// • 5% — Wrong destination suggested
//
// Evidence: Response time tracking, message content analysis,
// customer feedback surveys, agent activity logs
//
// QUOTE VIEWED → NEGOTIATION (28% drop):
// Reasons:
// • 35% — Price too high (competitor offered lower)
// • 25% — No follow-up from agent after sending quote
// • 20% — Customer found better deal on OTA
// • 12% — Itinerary didn't match expectations
// • 8% — Customer delayed decision
//
// Evidence: Price comparison data, agent follow-up timestamps,
// OTA price monitoring, customer feedback
//
// POST-TRIP → REPEAT (65% of satisfied don't repeat):
// Reasons:
// • 30% — No follow-up contact from agency
// • 25% — Customer booked next trip elsewhere
// • 20% — No relevant trip suggestion at right time
// • 15% — Customer traveling less (life event)
// • 10% — Better deal from competitor
//
// Evidence: Re-engagement campaign data, booking source tracking,
// customer interview insights, competitor monitoring
```

### Journey Velocity & Quality

```typescript
interface JourneyVelocity {
  // Time metrics at each stage:
  // ─────────────────────────────────────────
  // Stage Transition        | Avg Time | Median | P90   | Target
  // ──────────────────────────────────────────────────────────
  // Inquiry → First reply   | 8 min    | 5 min  | 25 min| <15 min
  // First reply → Quote     | 4.2 hrs  | 3 hrs  | 12 hrs| <4 hrs
  // Quote → Negotiation     | 1.8 days | 1 day  | 5 days| <2 days
  // Negotiation → Booking   | 2.1 days | 1 day  | 7 days| <3 days
  // Booking → Payment       | 1.2 days | 4 hrs  | 5 days| <24 hrs
  // Payment → Confirmation  | 3.5 hrs  | 2 hrs  | 12 hrs| <6 hrs
  // Confirmation → Travel   | 18.5 days| 14 days| 45 days| N/A
  // Travel → Feedback       | 2.1 days | 1 day  | 7 days| <3 days
  // Feedback → Next inquiry | 42 days  | 30 days | 90 days| <60 days
  // ─────────────────────────────────────────
  //
  // Velocity trends (month over month):
  // ┌─────────────────────────────────────────┐
  // │  Journey Velocity Trends                 │
  // │                                            │
  // │  Inquiry → Quote time:                    │
  // │  Jan: 5.2h  Feb: 4.8h  Mar: 4.5h  Apr: 4.2h│
  // │  ██████████████████████████████░░ ↓19%    │
  // │  ✅ Improving (faster quoting)             │
  // │                                            │
  // │  Quote → Booking time:                    │
  // │  Jan: 5.1d  Feb: 4.8d  Mar: 4.5d  Apr: 3.9d│
  // │  ████████████████████████████████░ ↓24%   │
  // │  ✅ Improving (better follow-up)           │
  // │                                            │
  // │  Booking → Payment time:                  │
  // │  Jan: 1.5d  Feb: 1.4d  Mar: 1.3d  Apr: 1.2d│
  // │  ████████████████████████████████░ ↓20%   │
  // │  ✅ Improving (UPI instant payment)        │
  // │                                            │
  // │  Post-trip → Next inquiry:                │
  // │  Jan: 55d   Feb: 50d   Mar: 48d   Apr: 42d │
  // │  ████████████████████████████████░ ↓24%   │
  // │  ✅ Improving (better re-engagement)       │
  // └─────────────────────────────────────────────┘
}

interface JourneyQualityMetrics {
  // Quality at each stage:
  // ─────────────────────────────────────────
  // Stage         | Quality Score | Key Driver
  // ──────────────────────────────────────────────────────────
  // Consideration | 82/100        | Response time, personalization
  // Booking       | 78/100        | Price transparency, ease of payment
  // Preparation   | 85/100        | Document readiness, communication
  // Travel        | 88/100        | Issue resolution, daily check-ins
  // Post-trip     | 72/100        | Feedback collection, re-engagement
  // ─────────────────────────────────────────
  //
  // Quality score components (per stage):
  // Consideration quality:
  //   - First response time: <15 min = 100, >1hr = 0
  //   - Personalization score: Custom itinerary = 100, template = 50
  //   - Follow-up timeliness: Within 24h = 100, none = 0
  //   - Customer engagement: Response rate to agent messages
  //
  // Travel quality:
  //   - Proactive check-ins: Daily = 100, none = 0
  //   - Issue resolution time: <30 min = 100, >4 hrs = 0
  //   - Customer satisfaction: In-trip rating
  //   - Communication quality: Clarity and helpfulness

  // Journey satisfaction correlation:
  // ┌─────────────────────────────────────────┐
  // │  What drives journey satisfaction?        │
  // │                                            │
  // │  Agent responsiveness        r = 0.82     │
  // │  ████████████████████████████████████     │
  // │  Issue resolution speed       r = 0.78    │
  // │  █████████████████████████████████░░░     │
  // │  Itinerary personalization    r = 0.75    │
  // │  ███████████████████████████████░░░░░     │
  // │  Proactive communication     r = 0.71    │
  // │  ██████████████████████████████░░░░░░     │
  // │  Price transparency           r = 0.68    │
  // │  ████████████████████████████░░░░░░░░     │
  // │  Document quality            r = 0.62    │
  // │  ██████████████████████████░░░░░░░░░░     │
  // │  OTA comparison support      r = 0.55    │
  // │  █████████████████████░░░░░░░░░░░░░░     │
  // └─────────────────────────────────────────────┘
}
```

### Journey Optimization

```typescript
interface JourneyOptimization {
  abTesting: JourneyABTest[];
  frictionDetection: FrictionDetector;
  interventionEngine: InterventionEngine;
  predictions: JourneyPrediction;
}

interface JourneyABTest {
  id: string;
  name: string;                        // "Follow-up timing: 24h vs 48h"
  stage: JourneyStageType;
  hypothesis: string;
  variants: ABVariant[];
  metric: string;                      // What we're measuring
  startDate: Date;
  endDate: Date;
  minSampleSize: number;
  status: 'draft' | 'running' | 'complete';
  result?: ABResult;
}

// A/B test examples:
//
// TEST 1: First response timing
// Hypothesis: Responding within 5 minutes increases conversion by 15%
// Control: Current avg response (8 min)
// Variant A: Target <5 min response
// Metric: Inquiry → Booking conversion rate
// Sample: 200 customers per variant
//
// TEST 2: Quote format
// Hypothesis: Image-rich WhatsApp quote gets 20% higher engagement
// Control: Text-only quote on WhatsApp
// Variant A: Quote with destination images + pricing table image
// Metric: Quote open rate + negotiation rate
//
// TEST 3: Post-trip follow-up
// Hypothesis: Sending next-trip suggestion within 2 weeks increases repeat by 25%
// Control: Current (no systematic follow-up)
// Variant A: Personalized next-trip suggestion at 2 weeks
// Variant B: Festival-based suggestion (timed to upcoming holiday)
// Metric: Repeat booking rate within 90 days
//
// TEST 4: Feedback survey length
// Hypothesis: 1-question survey gets 2x completion vs 5-question
// Control: 5-question WhatsApp survey
// Variant A: Single NPS question
// Metric: Survey completion rate

interface FrictionDetector {
  // Automatically detect journey friction points:
  //
  // FRICTION SIGNALS:
  // 1. Customer sent 3+ messages without agent response
  // 2. Customer asked about price 3+ times (price sensitivity)
  // 3. Customer mentioned competitor name ("MakeMyTrip has...")
  // 4. Quote viewed but no response in 48+ hours
  // 5. Payment page visited but not completed
  // 6. Customer contacted support during trip (service issue)
  // 7. Customer gave <3 star rating
  // 8. No repeat booking in 12 months despite past satisfaction
  //
  // Friction alert:
  // ┌─────────────────────────────────────────┐
  // │  ⚠️ Friction Alert — TRV-45678           │
  // │                                            │
  // │  Customer: Rajesh Sharma                  │
  // │  Stage: Consideration                     │
  // │  Friction type: Price comparison          │
  // │                                            │
  // │  Signals detected:                         │
  // │  • Asked "Is this the best price?" (2x)  │
  // │  • Mentioned "Goibibo has cheaper rate"   │
  // │  • Quote viewed but no response in 36h    │
  // │                                            │
  // │  Risk of loss: HIGH (78%)                 │
  // │                                            │
  // │  Suggested actions:                        │
  // │  1. Call customer to discuss value         │
  // │  2. Offer price match or added value       │
  // │  3. Share reviews from similar customers   │
  // │                                            │
  // │  [Call Now] [Send Value Message]          │
  // └─────────────────────────────────────────────┘
}

interface JourneyPrediction {
  // Predict journey outcomes:
  //
  // BOOKING LIKELIHOOD:
  // Based on: Response time, personalization, engagement, price fit
  // High (>80%): Fast response, personalized, customer engaged
  // Medium (40-80%): Some friction, but still in conversation
  // Low (<40%): Slow response, OTA comparison, no engagement
  //
  // CUSTOMER LIFETIME VALUE:
  // Based on: First trip value, satisfaction score, demographics
  // High LTV: High first trip value, 5-star satisfaction, family segment
  // Medium LTV: Average first trip, 4-star satisfaction
  // Low LTV: Discount seeker, no satisfaction data
  //
  // CHURN RISK:
  // Based on: Time since last trip, engagement decline, complaint history
  // Active: Booked within 6 months, regular engagement
  // At Risk: 6-12 months since last trip, declining engagement
  // Dormant: 12+ months since last trip, no engagement
  // Churned: Explicitly went to competitor or unsubscribed
  //
  // Prediction dashboard for agents:
  // ┌─────────────────────────────────────────┐
  // │  Customer: Rajesh Sharma                  │
  // │                                            │
  // │  Journey Stage: Consideration              │
  // │  Booking Likelihood: ██████████░░ 78%     │
  // │  Predicted Trip Value: ₹65,000            │
  // │  LTV Potential: ₹2,50,000 (high)         │
  // │  Churn Risk: LOW                          │
  // │                                            │
  // │  AI Recommendations:                       │
  // │  • Send Kerala backwater photos (high engagement)│
  // │  • Include airport transfer in quote       │
  // │  • Offer payment plan (₹30K + ₹35K)      │
  // │                                            │
  // │  [Apply Recommendations] [Customize]      │
  // └─────────────────────────────────────────────┘
}
```

---

## Open Problems

1. **Attribution complexity** — When a customer books after 5 touchpoints across 3 channels, attributing success to any single touchpoint is misleading. Multi-touch attribution models help but are complex and often disagreed upon.

2. **A/B testing sample size** — Travel agencies handle hundreds of customers monthly, not millions. A/B tests require weeks to reach statistical significance, by which time market conditions may have changed.

3. **Prediction accuracy** — Journey prediction models trained on historical data may not generalize to new segments, new destinations, or post-pandemic behavior shifts. Regular retraining and monitoring are essential.

4. **Privacy vs. personalization** — Rich journey analytics require detailed behavioral tracking (message opens, page visits, time spent). DPDP Act requires consent for each tracking purpose. Opt-out rates may reduce data quality.

5. **Cross-agent journey continuity** — When a customer talks to different agents across journey stages, the handoff must be seamless. Journey state must be visible to all agents, not just the assigned one.

---

## Next Steps

- [ ] Build journey funnel analytics with stage-by-stage conversion tracking
- [ ] Create friction detection engine with automated alerts and intervention suggestions
- [ ] Implement A/B testing framework for journey touchpoint optimization
- [ ] Design journey prediction models for booking likelihood and LTV estimation
- [ ] Study journey analytics (Amplitude, Mixpanel, Heap, MoEngage, CleverTap)
