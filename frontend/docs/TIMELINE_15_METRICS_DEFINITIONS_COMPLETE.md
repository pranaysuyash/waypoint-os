# Timeline: Metrics Definitions (Complete)

> Every metric, calculation, and KPI definition

---

## Part 1: Metrics Overview

### Metric Categories

| Category | Purpose | Stakeholders |
|----------|---------|--------------|
| **Adoption** | Feature usage | Product, Growth |
| **Engagement** | User activity | Product, UX |
| **Performance** | System health | Engineering |
| **Quality** | Data integrity | Engineering, Data |
| **Business** | Value delivery | Leadership, Sales |
| **Customer** | Satisfaction | CS, Support |

---

## Part 2: Adoption Metrics

### 2.1 Timeline Penetration

**Definition:** Percentage of trips with timeline events

```sql
SELECT
    COUNT(DISTINCT trip_id) as trips_with_timeline,
    (SELECT COUNT(*) FROM trips) as total_trips,
    ROUND(
        100.0 * COUNT(DISTINCT trip_id) / NULLIF((SELECT COUNT(*) FROM trips), 0),
        2
    ) as penetration_percentage
FROM trip_events;
```

**Targets:**
- Phase 1 end: 60%
- Phase 2 end: 80%
- Phase 3 end: 95%

### 2.2 Event Capture Rate

**Definition:** Percentage of actual events captured

```sql
-- Estimate based on expected vs actual
SELECT
    trip_id,
    -- Expected events based on trip stage
    expected_events,
    -- Actual events captured
    actual_events,
    -- Capture rate
    ROUND(100.0 * actual_events / NULLIF(expected_events, 0), 2) as capture_rate
FROM trip_capture_analysis;
```

**Targets:**
- Phase 1: 70% (core events only)
- Phase 2: 90% (including communications)
- Phase 3: 95% (comprehensive)

### 2.3 User Adoption

**Definition:** Percentage of agents using timeline

```sql
SELECT
    COUNT(DISTINCT actor->>'id') as active_agents,
    (SELECT COUNT(*) FROM users WHERE role = 'agent') as total_agents,
    ROUND(
        100.0 * COUNT(DISTINCT actor->>'id') / NULLIF(
            (SELECT COUNT(*) FROM users WHERE role = 'agent'), 0
        ),
        2
    ) as adoption_rate
FROM trip_events
WHERE actor->>'type' = 'agent'
  AND timestamp >= NOW() - INTERVAL '7 days';
```

**Targets:**
- Week 1: 20%
- Week 4: 60%
- Week 12: 90%

---

## Part 3: Engagement Metrics

### 3.1 Timeline Views Per Trip

**Definition:** Average number of timeline views per trip

```sql
SELECT
    AVG(view_count) as avg_views_per_trip,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY view_count) as median_views,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY view_count) as p90_views
FROM trip_timeline_stats;
```

**Targets:**
- Phase 1: 2 views/trip
- Phase 2: 4 views/trip
- Phase 3: 6 views/trip

### 3.2 Time Spent in Timeline

**Definition:** Average session duration in timeline

```sql
SELECT
    AVG(session_duration_seconds) as avg_session_seconds,
    AVG(session_duration_seconds) / 60 as avg_session_minutes
FROM timeline_sessions
WHERE session_start >= NOW() - INTERVAL '7 days';
```

**Targets:**
- Target: 2-5 minutes per session
- Too low (<30s): Not finding value
- Too high (>10min): Hard to use

### 3.3 Feature Usage

**Definition:** Usage of specific timeline features

```sql
-- Filter usage
SELECT
    COUNT(DISTINCT session_id) as filter_users,
    COUNT(DISTINCT trip_id) as total_trips,
    ROUND(100.0 * COUNT(DISTINCT session_id) / NULLIF(COUNT(DISTINCT trip_id), 0), 2) as usage_rate
FROM timeline_filter_sessions;

-- Search usage
SELECT
    COUNT(*) as total_searches,
    COUNT(DISTINCT user_id) as unique_searchers,
    AVG(result_count) as avg_results,
    AVG(NULLIF(result_clicked, false)::int) as click_rate
FROM timeline_search_logs
WHERE searched_at >= NOW() - INTERVAL '7 days';

-- Export usage
SELECT
    export_type,
    COUNT(*) as total_exports,
    COUNT(DISTINCT user_id) as unique_exporters
FROM timeline_exports
WHERE exported_at >= NOW() - INTERVAL '30 days'
GROUP BY export_type;
```

**Targets:**
- Filters: 40% of sessions
- Search: 30% of sessions
- Export: 10% of trips

---

## Part 4: Performance Metrics

### 4.1 Query Latency

**Definition:** Time to return timeline data

```sql
SELECT
    endpoint,
    AVG(response_time_ms) as avg_latency,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY response_time_ms) as p50_latency,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_latency,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_latency
FROM api_metrics
WHERE path LIKE '/timeline/v1/%'
  AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY endpoint;
```

**Targets:**
- P50: <50ms
- P95: <200ms
- P99: <500ms

### 4.2 Event Ingestion Latency

**Definition:** Time from event occurrence to storage

```sql
SELECT
    event_type,
    AVG(
        EXTRACT(EPOCH FROM (ingested_at - occurred_at))
    ) as avg_delay_seconds,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (ingested_at - occurred_at))
    ) as p95_delay_seconds
FROM trip_events
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY event_type;
```

**Targets:**
- P50: <1 second
- P95: <5 seconds
- P99: <30 seconds

### 4.3 Real-time Update Latency

**Definition:** Time from event creation to client delivery

```sql
SELECT
    AVG(
        EXTRACT(EPOCH FROM (client_received_at - event_created_at))
    ) as avg_delay_seconds
FROM websocket_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours';
```

**Targets:**
- P50: <100ms
- P95: <500ms
- P99: <2000ms

---

## Part 5: Quality Metrics

### 5.1 Data Completeness

**Definition:** Percentage of required fields populated

```sql
SELECT
    trip_id,
    COUNT(*) as total_events,
    COUNT(*) FILTER (
        WHERE content IS NOT NULL
        AND actor IS NOT NULL
        AND timestamp IS NOT NULL
    ) as complete_events,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE content IS NOT NULL
            AND actor IS NOT NULL
            AND timestamp IS NOT NULL
        ) / NULLIF(COUNT(*), 0),
        2
    ) as completeness_rate
FROM trip_events
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY trip_id;
```

**Targets:**
- Overall: >99%
- Critical events: 100%

### 5.2 Duplicate Rate

**Definition:** Percentage of duplicate events

```sql
SELECT
    COUNT(*) FILTER (WHERE is_duplicate = true) as duplicate_count,
    COUNT(*) as total_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_duplicate = true) / NULLIF(COUNT(*), 0),
        2
    ) as duplicate_rate
FROM trip_events
WHERE created_at >= NOW() - INTERVAL '7 days';
```

**Targets:**
- <0.1% duplicates

### 5.3 Search Relevance

**Definition:** User satisfaction with search results

```sql
SELECT
    AVG(
        CASE
            WHEN clicked_result THEN 1
            WHEN refined_search THEN 0.5
            ELSE 0
        END
    ) as relevance_score
FROM timeline_search_logs
WHERE searched_at >= NOW() - INTERVAL '7 days';
```

**Targets:**
- Relevance score: >0.7

---

## Part 6: Business Value Metrics

### 6.1 Handoff Time Savings

**Definition:** Time saved on agent handoffs

```sql
-- Before timeline (baseline)
SELECT
    AVG(handoff_duration_minutes) as baseline_handoff_minutes
FROM handoff_logs
WHERE timestamp < '2026-04-01';  -- Before timeline

-- After timeline
SELECT
    AVG(handoff_duration_minutes) as timeline_handoff_minutes
FROM handoff_logs
WHERE timestamp >= '2026-04-01'  -- After timeline
  AND timeline_used = true;

-- Savings
SELECT
    baseline_handoff_minutes - timeline_handoff_minutes as time_saved_minutes,
    ROUND(
        100.0 * (baseline_handoff_minutes - timeline_handoff_minutes) / NULLIF(baseline_handoff_minutes, 0),
        2
    ) as percent_improvement;
```

**Targets:**
- Phase 1: 10 minutes saved
- Phase 2: 15 minutes saved
- Phase 3: 20 minutes saved

### 6.2 Dispute Resolution Time

**Definition:** Time to resolve customer disputes

```sql
SELECT
    AVG(
        EXTRACT(EPOCH FROM (resolved_at - raised_at)) / 3600
    ) as avg_resolution_hours,
    COUNT(*) FILTER (
        WHERE resolution_used_timeline = true
    ) as timeline_resolutions,
    AVG(
        EXTRACT(EPOCH FROM (resolved_at - raised_at)) / 3600
    ) FILTER (
        WHERE resolution_used_timeline = true
    ) as timeline_resolution_hours
FROM customer_disputes
WHERE resolved_at >= NOW() - INTERVAL '90 days';
```

**Targets:**
- 50% reduction in resolution time

### 6.3 Training Ramp-up Time

**Definition:** Time for new agents to reach productivity

```sql
SELECT
    agent_id,
    hired_at,
    FIRST_VALUE(productive_at) OVER (
        PARTITION BY agent_id
        ORDER BY productive_at
    ) as first_productive_date,
    EXTRACT(DAY FROM (
        FIRST_VALUE(productive_at) OVER (
            PARTITION BY agent_id
            ORDER BY productive_at
        ) - hired_at
    )) as days_to_productivity
FROM agent_performance
WHERE hired_at >= NOW() - INTERVAL '6 months';
```

**Targets:**
- Before timeline: 90 days
- With timeline: 60 days
- Improvement: 33% faster

---

## Part 7: Customer-Facing Metrics

### 7.1 Portal Adoption

**Definition:** Percentage of customers accessing portal

```sql
SELECT
    COUNT(DISTINCT customer_id) as active_customers,
    (SELECT COUNT(DISTINCT customer_id) FROM bookings WHERE created_at >= NOW() - INTERVAL '30 days') as total_customers,
    ROUND(
        100.0 * COUNT(DISTINCT customer_id) / NULLIF(
            (SELECT COUNT(DISTINCT customer_id) FROM bookings WHERE created_at >= NOW() - INTERVAL '30 days'),
            0
        ),
        2
    ) as portal_adoption_rate
FROM customer_portal_visits
WHERE visited_at >= NOW() - INTERVAL '30 days';
```

**Targets:**
- Phase 5 launch: 20%
- Phase 5 + 3 months: 50%
- Phase 5 + 6 months: 70%

### 7.2 Customer Satisfaction

**Definition:** CSAT related to timeline transparency

```sql
SELECT
    AVG(rating) as avg_csat,
    COUNT(*) as response_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE rating >= 4) / NULLIF(COUNT(*), 0),
        2
    ) as positive_rate
FROM customer_surveys
WHERE question = 'timeline_transparency'
  AND created_at >= NOW() - INTERVAL '90 days';
```

**Targets:**
- Average CSAT: >4.2/5
- Positive rate: >80%

### 7.3 Reduction in Status Inquiries

**Definition:** Fewer "what's the status" contacts

```sql
SELECT
    COUNT(*) FILTER (WHERE has_timeline_access = true) as timeline_inquiries,
    COUNT(*) FILTER (WHERE has_timeline_access = false) as no_timeline_inquiries,
    ROUND(
        100.0 * (COUNT(*) FILTER (WHERE has_timeline_access = false) - COUNT(*) FILTER (WHERE has_timeline_access = true)) /
        NULLIF(COUNT(*) FILTER (WHERE has_timeline_access = false), 0),
        2
    ) as reduction_percentage
FROM customer_inquiries
WHERE inquiry_type = 'status_check'
  AND created_at >= NOW() - INTERVAL '90 days';
```

**Targets:**
- 60% reduction in status inquiries

---

## Part 8: AI Feature Metrics

### 8.1 Summarization Usage

**Definition:** Usage and effectiveness of AI summaries

```sql
SELECT
    COUNT(*) FILTER (WHERE ai_summary IS NOT NULL) as events_with_summary,
    COUNT(*) as total_events,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE ai_summary IS NOT NULL) / NULLIF(COUNT(*), 0),
        2
    ) as summary_coverage,
    AVG(
        CASE
            WHEN summary_helpful THEN 1
            WHEN summary_not_helpful THEN 0
            ELSE NULL
        END
    ) as helpfulness_score
FROM trip_events
WHERE created_at >= NOW() - INTERVAL '30 days');
```

**Targets:**
- Coverage: 90% of eligible events
- Helpfulness: >0.8

### 8.2 Pattern Detection Accuracy

**Definition:** Accuracy of detected patterns

```sql
SELECT
    pattern_type,
    COUNT(*) as total_detections,
    COUNT(*) FILTER (WHERE verified_correct = true) as correct_detections,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE verified_correct = true) / NULLIF(COUNT(*), 0),
        2
    ) as accuracy_rate
FROM pattern_detections
WHERE detected_at >= NOW() - INTERVAL '90 days'
GROUP BY pattern_type;
```

**Targets:**
- Accuracy: >75%

### 8.3 Similar Trips Relevance

**Definition:** User satisfaction with similar trip recommendations

```sql
SELECT
    AVG(relevance_rating) as avg_relevance,
    COUNT(*) FILTER (WHERE acted_on = true) as used_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE acted_on = true) / NULLIF(COUNT(*), 0),
        2
    ) as action_rate
FROM similar_trip_feedback
WHERE created_at >= NOW() - INTERVAL '90 days');
```

**Targets:**
- Relevance: >4/5
- Action rate: >40%

---

## Part 9: Dashboard Configuration

### Executive Dashboard

```typescript
interface ExecutiveDashboard {
  adoption: {
    timelinePenetration: number;
    eventCaptureRate: number;
    userAdoption: number;
  };
  value: {
    handoffTimeSaved: number;
    disputeReduction: number;
    trainingAcceleration: number;
  };
  performance: {
    p95Latency: number;
    uptime: number;
    errorRate: number;
  };
  quality: {
    dataCompleteness: number;
    duplicateRate: number;
    searchRelevance: number;
  };
}
```

### Product Dashboard

```typescript
interface ProductDashboard {
  engagement: {
    avgViewsPerTrip: number;
    avgSessionDuration: number;
    featureUsage: {
      filters: number;
      search: number;
      export: number;
    };
  };
  ai: {
    summarizationCoverage: number;
    patternAccuracy: number;
    similarTripsRelevance: number;
  };
  customer: {
    portalAdoption: number;
    csat: number;
    statusInquiryReduction: number;
  };
}
```

### Engineering Dashboard

```typescript
interface EngineeringDashboard {
  performance: {
    queryLatency: {
      p50: number;
      p95: number;
      p99: number;
    };
    ingestionLatency: {
      p50: number;
      p95: number;
    };
    realtimeLatency: {
      p50: number;
      p95: number;
    };
  };
  reliability: {
    uptime: number;
    errorRate: number;
    alertCount: number;
  };
  scale: {
    totalEvents: number;
    eventsPerSecond: number;
    storageUsed: number;
  };
}
```

---

## Part 10: Alert Thresholds

### Critical Alerts

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Query P95 latency** | >500ms | Page on-call |
| **Error rate** | >1% | Page on-call |
| **Event ingestion delay** | >5min | Investigate |
| **Duplicate rate** | >0.5% | Investigate |
| **Uptime** | <99.9% | Page on-call |

### Warning Alerts

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Query P95 latency** | >200ms | Create ticket |
| **Search relevance** | <0.6 | Review algorithm |
| **Adoption rate** | <target | Review outreach |
| **CSAT** | <4.0 | Review feedback |

---

## Summary

**Metrics Summary:**

| Category | Key Metrics | Update Frequency |
|----------|-------------|------------------|
| **Adoption** | 5 metrics | Daily |
| **Engagement** | 8 metrics | Hourly |
| **Performance** | 9 metrics | Real-time |
| **Quality** | 5 metrics | Daily |
| **Business Value** | 6 metrics | Weekly |
| **Customer** | 5 metrics | Weekly |
| **AI Features** | 6 metrics | Daily |
| **Total** | **44 metrics** | - |

**Data Retention:**
- Raw metrics: 90 days
- Aggregated metrics: 2 years
- Dashboard snapshots: Indefinite

**Access:**
- Executive dashboards: Owners, C-level
- Product dashboards: Product managers, UX
- Engineering dashboards: Engineering leads
- Real-time alerts: On-call engineers

---

**Status:** Metrics definitions complete.
**Version:** 1.0
**Last Updated:** 2026-04-23
