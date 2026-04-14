# Metrics and Analytics

**Date**: 2026-04-14
**Purpose**: What to measure so you know you're building the right thing

---

## Solo Builder Reality

> "What gets measured gets managed. But solo builders shouldn't measure everything."

You have limited time. Track 5-7 metrics max.

---

## North Star Metric

**Trips Processed Per Week**

Not:
- ❌ Total users (vanity, agencies can have 1 user processing 100 trips)
- ❌ Revenue (lagging indicator)
- ❌ Feature usage (doesn't equal value)

**Why**: If agencies are using it to process real trips, you're delivering value.

---

## The 5 Metrics That Matter

### 1. Activation Rate

**Definition**: % of new agencies that process at least 1 trip in first week

| Threshold | Interpretation |
|-----------|----------------|
| < 20% | Onboarding broken or product not clear |
| 20-40% | Needs improvement |
| 40-60% | Good |
| > 60% | Excellent |

**How to track**: Simple database query or event log

**How to improve**: Better onboarding, clearer first steps, example trips

---

### 2. Weekly Active Agencies

**Definition**: Agencies that processed ≥1 trip in the past 7 days

| Threshold | Interpretation |
|-----------|----------------|
| Growing weekly | Product-market fit signal |
| Flat/stagnant | Engagement problem |
| Declining | Churn risk |

**Solo builder tip**: Don't obsess over daily fluctuations. Look at 4-week moving average.

---

### 3. Trips Per Active Agency Per Week

**Definition**: How much they're using it

| Number | Interpretation |
|--------|----------------|
| 0.5-1 | Experimenting, not integrated into workflow |
| 2-5 | Part of workflow |
| 5+ | Core to their operations |

**This is your leading indicator of value.**

---

### 4. Week 4 Retention

**Definition**: % of agencies that signed up 4 weeks ago and are still active

| Threshold | Interpretation |
|-----------|----------------|
| < 20% | Problem — product-market fit gap |
| 20-40% | Needs investigation |
| 40-60% | Good trajectory |
| > 60% | Strong PMF |

**Solo builder tip**: Call agencies that churn. Ask why. You'll learn more than from metrics.

---

### 5. NPS (Net Promoter Score)

**Question**: "How likely are you to recommend this to another travel agent? (0-10)"

| Score | Interpretation |
|-------|----------------|
| < 0 | Major problems |
| 0-20 | Weak |
| 20-40 | Okay |
| 40-70 | Good |
| > 70 | Excellent |

**But more important**: Ask WHY they gave that score.

---

## Quality Metrics (Product-Specific)

### 6. Agent Edit Rate

**Definition**: On average, how much does the agent change your output?

| Metric | How to measure |
|--------|----------------|
| % of suggestions accepted | Count accepted / total suggestions |
| % of text edited | Character diff / original length |
| % of trips with major edits | Subjective threshold |

**Target**: < 30% edit rate on average (agents should tweak, not rewrite)

---

### 7. Time from Intake to Options

**Definition**: How long from first message to bookable options

| Benchmark | Before you | With you |
|-----------|------------|----------|
| Manual | 1-3 days | — |
| Goal | — | < 2 hours |

**How to track**: Timestamp on source envelope → timestamp on execution packet

---

## Anti-Metrics (What NOT to Track)

| Anti-metric | Why to ignore |
|-------------|---------------|
| Total signups | Vanity, doesn't mean usage |
| Page views | Irrelevant for B2B workflow tool |
| Feature usage per se | Usage ≠ value; focus on outcomes |
| Time spent in app | Less is more if you're saving time |
| Social media followers | Doesn't correlate with B2B revenue |

---

## Tracking Setup (Solo-Friendly)

### Option 1: Just Use Your Database

```python
# Simple queries you can run weekly

# Weekly active agencies
SELECT COUNT(DISTINCT agency_id)
FROM trips
WHERE created_at > NOW() - INTERVAL '7 days'

# Trips per agency this week
SELECT agency_id, COUNT(*) as trip_count
FROM trips
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY agency_id
ORDER BY trip_count DESC

# Retention: cohorts by signup week
SELECT
    DATE_TRUNC('week', created_at) as cohort_week,
    COUNT(DISTINCT agency_id) as agencies
FROM agencies
GROUP BY cohort_week
ORDER BY cohort_week DESC;
```

### Option 2: Minimal Analytics Tool

| Tool | Pros | Cons |
|------|------|------|
| **PostHog** | Open source, generous free tier | Learning curve |
| **Plausible** | Privacy-first, simple | Limited features |
| **Mixpanel** | Powerful | Expensive quickly |
| **Google Analytics** | Free | Privacy concerns, complex |

**Solo builder recommendation**: PostHog or Plausible. Or just database logs.

---

## Weekly Review Ritual (30 minutes)

Every Monday morning:

```markdown
## Week of [Date]

### Numbers
- Weekly active agencies: _ (trend: ↗️ → ↘️)
- Trips processed: _ (trend: ↗️ → ↘️)
- Avg trips per agency: _
- New signups: _
- Churned: _

### Highlights
- [Best thing that happened this week]

### Lowlights
- [Worst thing or biggest frustration]

### Next week
- [One thing to improve]

### Agency check-ins
- [Who to call/email this week]
```

---

## A/B Testing (Later, Not Now)

**Don't A/B test yet.** You don't have enough users.

When you have 50+ active agencies, you can test:
- Onboarding flows
- Message templates
- Feature placement

**For now**: Trust your gut + direct feedback.

---

## Dashboard vs. Spreadsheet

| Approach | When to use |
|----------|-------------|
| **Spreadsheet** | < 50 agencies, manual tracking is fine |
| **Simple dashboard** | 50-200 agencies, need at-a-glance view |
| **Full analytics** | 200+ agencies, multiple stakeholders |

**Solo builder**: Spreadsheet + weekly queries is fine for a long time.

---

## Red Flags to Watch

| Metric | Red flag | Action |
|--------|----------|--------|
| Activation rate | < 20% for 3+ weeks | Fix onboarding |
| Weekly active | Declining 3+ weeks | Survey users, check bugs |
| Trips per agency | < 1/week average | Product not useful enough |
| NPS | < 20 | Deep dive interviews |
| Churn | > 20%/month | Major problem, call everyone |

---

## Summary

**Track 5 things**:
1. Trips processed per week (North Star)
2. Weekly active agencies
3. Trips per agency
4. Week 4 retention
5. NPS (quarterly, not weekly)

**Set up**:
- Simple database queries or minimal tool
- 30-min weekly review
- Call churned agencies

**Don't obsess** — build, talk to users, iterate.
