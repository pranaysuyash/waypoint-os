# Tour Guide & Escort Management — Performance Analytics

> Research document for guide KPIs, performance dashboards, training gap analysis, seasonal trends, and benchmarking.

---

## Key Questions

1. **What KPIs measure guide performance effectively?**
2. **How do we visualize performance for agents and managers?**
3. **How do we identify training gaps from performance data?**
4. **What seasonal patterns affect guide performance?**

---

## Research Areas

### Guide KPI Framework

```typescript
interface GuideKPIs {
  guide_id: string;
  period: DateRange;

  // Customer satisfaction
  avg_rating: number;                  // 1-5
  nps_score: number;                   // -100 to 100
  complaint_rate: number;              // per 100 tours
  praise_rate: number;                 // per 100 tours

  // Operational
  on_time_rate: number;                // percentage
  cancellation_rate: number;           // guide-cancelled
  no_show_rate: number;
  incident_rate: number;               // per 100 tours

  // Financial
  revenue_generated: Money;
  avg_trip_value: Money;
  upsell_rate: number;                 // optional extras sold
  cost_to_company: Money;
  revenue_per_day: Money;

  // Engagement
  tours_completed: number;
  customers_hosted: number;
  repeat_customer_rate: number;
  referral_generated_rate: number;

  // Compliance
  certification_currency: number;      // percentage valid
  briefing_acknowledgment_rate: number;
  report_submission_rate: number;
  daily_checkin_rate: number;
}

// ── KPI Dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Guide Performance — April 2026                       │
// │                                                       │
// │  ┌─── Top Performers ────────────────────────────    │
// │  │  Ravi    ★ 4.9  │ 12 tours │ ₹8.5L revenue      │
// │  │  Priya   ★ 4.8  │ 10 tours │ ₹6.2L revenue      │
// │  │  Amit    ★ 4.7  │  8 tours │ ₹5.8L revenue      │
// │  └────────────────────────────────────────────────    │
// │                                                       │
// │  ┌─── Attention Needed ──────────────────────────    │
// │  │  Suresh  ★ 3.2  │ 3 complaints │ 2 late arrivals│
// │  │  Meena   ★ 3.5  │ 1 no-show    │ cert expired   │
// │  └────────────────────────────────────────────────    │
// │                                                       │
// │  ┌─── Averages ──────────────────────────────────    │
// │  │  Rating: 4.4  | On-time: 94%  | NPS: 62        │
// │  │  Complaints: 0.3/100 | Revenue: ₹42L           │
// │  └────────────────────────────────────────────────    │
// └─────────────────────────────────────────────────────┘
```

### Performance Scoring Model

```typescript
interface GuidePerformanceScore {
  guide_id: string;
  overall_score: number;               // 0-100

  dimensions: {
    customer_satisfaction: {
      score: number;
      weight: 0.30;
      components: {
        avg_rating: number;
        nps: number;
        complaint_rate: number;
        review_sentiment: number;
      };
    };
    operational_reliability: {
      score: number;
      weight: 0.25;
      components: {
        on_time_rate: number;
        cancellation_rate: number;
        incident_rate: number;
        checkin_compliance: number;
      };
    };
    revenue_contribution: {
      score: number;
      weight: 0.20;
      components: {
        revenue_generated: number;
        avg_trip_value: number;
        upsell_rate: number;
        repeat_customer_rate: number;
      };
    };
    professional_development: {
      score: number;
      weight: 0.15;
      components: {
        certifications_current: number;
        training_completed: number;
        new_destinations_learned: number;
        peer_teaching_sessions: number;
      };
    };
    team_contribution: {
      score: number;
      weight: 0.10;
      components: {
        mentorship_hours: number;
        knowledge_sharing: number;
        substitute_acceptance_rate: number;
        briefing_quality: number;
      };
    };
  };
}

// ── Performance tiers ──
// ┌─────────────────────────────────────────┐
// │  Score Range | Tier       | Action       │
// │  ─────────────────────────────────────── │
// │  90-100     | Exceptional | Bonus + promo │
// │  75-89      | Strong      | Bonus         │
// │  60-74      | Good        | Standard      │
// │  40-59      | Needs Work  | Training plan │
// │  0-39       | At Risk     | PIP + review  │
// └───────────────────────────────────────────┘
```

### Training Gap Analysis

```typescript
interface TrainingGapAnalysis {
  guide_id: string;
  current_skills: SkillAssessment[];
  required_skills: SkillRequirement[];
  gaps: SkillGap[];
  recommended_training: TrainingRecommendation[];
}

interface SkillGap {
  skill: string;
  current_level: number;               // 0-100
  required_level: number;
  gap: number;
  impact: "HIGH" | "MEDIUM" | "LOW";
}

interface TrainingRecommendation {
  gap_id: string;
  training_type: "ONLINE_COURSE" | "WORKSHOP" | "SHADOW_TRIP" | "CERTIFICATION" | "LANGUAGE_CLASS";
  title: string;
  duration_hours: number;
  priority: "IMMEDIATE" | "THIS_QUARTER" | "THIS_YEAR";
  estimated_cost: Money;
}

// ── Gap analysis example ──
// ┌─────────────────────────────────────────┐
// │  Guide: Suresh                            │
// │                                           │
// │  Skill Gaps Identified:                   │
// │  ┌────────────┬──────┬──────┬──────────┐│
// │  │ Skill      │ Have │ Need │ Priority ││
// │  ├────────────┼──────┼──────┼──────────┤│
// │  │ English    │ 45   │ 80   │ HIGH     ││
// │  │ First Aid  │ 30   │ 70   │ HIGH     ││
// │  │ Wildlife   │ 60   │ 85   │ MEDIUM   ││
// │  │ Photography│ 20   │ 50   │ LOW      ││
// │  └────────────┴──────┴──────┴──────────┘│
// │                                           │
// │  Recommendations:                         │
// │  1. English course (60h, ₹8,000)         │
// │  2. First Aid cert renewal (8h, ₹3,000) │
// │  3. Shadow wildlife trip (2 days)        │
// └───────────────────────────────────────────┘
```

### Seasonal Performance Trends

```typescript
// ── Seasonal patterns ──
// ┌─────────────────────────────────────────┐
// │  Guide Utilization by Month               │
// │                                           │
// │  Jan ████████░░░░░░░░░░░░ 35%            │
// │  Feb ██████████░░░░░░░░░░ 42%            │
// │  Mar ██████████████░░░░░░ 58%            │
// │  Apr ██████████████████░░ 75%            │
// │  May ████████████████████ 90% (peak)     │
// │  Jun ███████████████████░ 82%            │
// │  Jul ██████████░░░░░░░░░░ 40% (monsoon)  │
// │  Aug ████████████░░░░░░░░ 48%            │
// │  Sep ████████████████░░░░ 65%            │
// │  Oct ████████████████████ 95% (Diwali)   │
// │  Nov ██████████████████░░ 78%            │
// │  Dec ████████████████████ 88% (Christmas)│
// │                                           │
// │  Insights:                                │
// │  - Oct peak: Hire freelancers early      │
// │  - Jul low: Training window              │
// │  - Dec peak: Avoid leave approvals       │
// └───────────────────────────────────────────┘

interface SeasonalInsight {
  month: number;
  utilization: number;
  avg_rating: number;
  incident_rate: number;
  recommendation: string;
}
```

### Peer Benchmarking

```typescript
interface PeerBenchmark {
  guide_id: string;
  rank: number;
  total_guides: number;
  percentile: number;

  comparisons: {
    vs_average: PerformanceDelta;
    vs_top_10_percent: PerformanceDelta;
    vs_same_experience: PerformanceDelta;
  };
}

interface PerformanceDelta {
  overall: number;                     // +/- percentage
  customer_satisfaction: number;
  operational: number;
  revenue: number;
}
```

---

## Open Problems

1. **Rating inflation** — Customers tend to give 4-5 stars by default, making it hard to distinguish truly exceptional guides. Need weighted ratings (verified reviews, detailed feedback).

2. **Attribution** — A low rating could be due to factors outside the guide's control (bad hotel, flight delay). Need to separate guide performance from trip quality.

3. **Seasonal comparison fairness** — Comparing a guide's July performance (monsoon, low demand) with October (Diwali, high demand) is unfair. Need season-adjusted benchmarks.

4. **Peer competition** — Ranking guides against each other can create toxic competition. Emphasize personal improvement trends over relative ranking.

---

## Next Steps

- [ ] Build multi-dimensional performance scoring engine
- [ ] Create guide performance dashboard with drill-down
- [ ] Implement training gap auto-detection from KPI patterns
- [ ] Design season-adjusted benchmarking algorithm
- [ ] Build peer comparison with emphasis on improvement trends
