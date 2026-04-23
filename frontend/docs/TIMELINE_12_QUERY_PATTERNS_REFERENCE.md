# Timeline: Query Patterns Reference

> Every query use case with optimized SQL

---

## Part 1: Query Categories

| Category | Description | Complexity |
|----------|-------------|------------|
| **Basic** | Simple event retrieval | Low |
| **Filtered** | Event retrieval with conditions | Medium |
| **Aggregated** | Counts, statistics, summaries | Medium |
| **Temporal** | Time-based queries, trends | High |
| **Relational** | Cross-trip, pattern queries | High |
| **Full-text** | Search across content | Medium |
| **Analytical** | Complex business intelligence | High |

---

## Part 2: Basic Queries

### 2.1 Get All Events for a Trip

**Use Case:** Display timeline

```sql
-- Basic timeline query
SELECT
    id,
    event_type,
    category,
    timestamp,
    actor,
    source,
    content,
    metadata,
    created_at
FROM trip_events
WHERE trip_id = $1
ORDER BY timestamp DESC;

-- Index: idx_trip_events_trip_id
-- Expected rows: 10-500
-- Performance: <10ms
```

**With pagination:**

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
ORDER BY timestamp DESC
LIMIT $2 OFFSET $3;
```

### 2.2 Get Single Event

```sql
SELECT * FROM trip_events
WHERE id = $1;

-- Index: PRIMARY KEY
-- Performance: <1ms
```

### 2.3 Get Latest Event

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
ORDER BY timestamp DESC
LIMIT 1;

-- Index: idx_trip_events_trip_id + timestamp
-- Performance: <5ms
```

---

## Part 3: Filtered Queries

### 3.1 Filter by Event Type

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND event_type = $2
ORDER BY timestamp DESC;

-- Index: idx_trip_events_type
-- Use case: Show only WhatsApp messages
```

### 3.2 Filter by Category

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND category = $2
ORDER BY timestamp DESC;

-- Use case: Show only conversation events
```

### 3.3 Filter by Date Range

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND timestamp BETWEEN $2 AND $3
ORDER BY timestamp DESC;

-- Use case: Show last week's activity
```

### 3.4 Filter by Actor Type

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND actor->>'type' = $2
ORDER BY timestamp DESC;

-- Use case: Show only customer messages
```

### 3.5 Filter by Internal Flag

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND (metadata->>'isInternalOnly')::boolean IS NOT TRUE
ORDER BY timestamp DESC;

-- Use case: Customer-facing timeline
```

### 3.6 Combined Filters

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND category IN ('conversation', 'decision')
  AND timestamp >= NOW() - INTERVAL '30 days'
  AND (metadata->>'isInternalOnly')::boolean IS NOT TRUE
ORDER BY timestamp DESC;

-- Use case: Recent visible activity for dashboard
```

---

## Part 4: Aggregated Queries

### 4.1 Event Count by Type

```sql
SELECT
    event_type,
    COUNT(*) as count
FROM trip_events
WHERE trip_id = $1
GROUP BY event_type
ORDER BY count DESC;

-- Use case: Timeline summary
```

### 4.2 Event Count by Category

```sql
SELECT
    category,
    COUNT(*) as count
FROM trip_events
WHERE trip_id = $1
GROUP BY category
ORDER BY count DESC;

-- Use case: Activity breakdown
```

### 4.3 Event Count by Actor

```sql
SELECT
    actor->>'name' as actor_name,
    actor->>'type' as actor_type,
    COUNT(*) as event_count
FROM trip_events
WHERE trip_id = $1
GROUP BY actor->>'name', actor->>'type'
ORDER BY event_count DESC;

-- Use case: Who contributed most
```

### 4.4 Timeline Statistics

```sql
SELECT
    COUNT(*) as total_events,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event,
    MAX(timestamp) - MIN(timestamp) as duration,
    COUNT(DISTINCT actor->>'type') as actor_types
FROM trip_events
WHERE trip_id = $1;

-- Use case: Trip overview card
```

### 4.5 Daily Activity

```sql
SELECT
    DATE(timestamp) as date,
    COUNT(*) as events
FROM trip_events
WHERE trip_id = $1
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Use case: Activity chart
```

---

## Part 5: Temporal Queries

### 5.1 Events Since Last Update

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND timestamp > (
    SELECT MAX(timestamp)
    FROM trip_events
    WHERE id = $2  -- Last seen event ID
  )
ORDER BY timestamp DESC;

-- Use case: Real-time updates (polling)
```

### 5.2 Events in Time Window

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND timestamp BETWEEN
    NOW() - INTERVAL '1 hour' AND
    NOW()
ORDER BY timestamp DESC;

-- Use case: Recent activity feed
```

### 5.3 First Event of Each Type

```sql
SELECT DISTINCT ON (event_type) *
FROM trip_events
WHERE trip_id = $1
ORDER BY event_type, timestamp ASC;

-- Use case: Timeline milestones
```

### 5.4 Time Between Events

```sql
SELECT
    e1.id as event1_id,
    e2.id as event2_id,
    e1.timestamp as time1,
    e2.timestamp as time2,
    EXTRACT(EPOCH FROM (e2.timestamp - e1.timestamp)) / 60 as minutes_between
FROM trip_events e1
CROSS JOIN trip_events e2
WHERE e1.trip_id = $1
  AND e2.trip_id = $1
  AND e2.timestamp > e1.timestamp
ORDER BY e1.timestamp
LIMIT 10;

-- Use case: Response time analysis
```

### 5.5 Events Before/After Milestone

```sql
-- Events before a specific event
SELECT * FROM trip_events
WHERE trip_id = $1
  AND timestamp < (SELECT timestamp FROM trip_events WHERE id = $2)
ORDER BY timestamp DESC;

-- Events after a specific event
SELECT * FROM trip_events
WHERE trip_id = $1
  AND timestamp > (SELECT timestamp FROM trip_events WHERE id = $2)
ORDER BY timestamp ASC;
```

---

## Part 6: Relational Queries

### 6.1 Find Similar Trips (by destination)

```sql
WITH trip_destinations AS (
    SELECT
        te.trip_id,
        te.content->>'extractedData'->>'destination' as destination
    FROM trip_events te
    WHERE te.event_type = 'inquiry_received'
)
SELECT
    td1.trip_id,
    td2.trip_id as similar_trip_id,
    td1.destination
FROM trip_destinations td1
JOIN trip_destinations td2 ON td1.destination = td2.destination
WHERE td1.trip_id = $1
  AND td2.trip_id != $1
LIMIT 10;

-- Use case: Similar trips feature
```

### 6.2 Find Common Patterns Across Trips

```sql
SELECT
    content->>'extractedData'->>'destination' as destination,
    content->>'extractedData'->>'tripType' as trip_type,
    COUNT(*) as trip_count,
    AVG((content->>'extractedData'->>'budget')::int) as avg_budget
FROM trip_events
WHERE event_type = 'inquiry_received'
  AND timestamp >= NOW() - INTERVAL '90 days'
GROUP BY
    content->>'extractedData'->>'destination',
    content->>'extractedData'->>'tripType'
HAVING COUNT(*) >= 3
ORDER BY trip_count DESC;

-- Use case: Pattern detection
```

### 6.3 Decision State Transitions

```sql
SELECT
    e1.content->>'fromState' as from_state,
    e1.content->>'toState' as to_state,
    COUNT(*) as transition_count,
    AVG(EXTRACT(EPOCH FROM (e1.timestamp - (
        SELECT MAX(timestamp)
        FROM trip_events e2
        WHERE e2.trip_id = e1.trip_id
          AND e2.timestamp < e1.timestamp
    ))) / 3600) as avg_hours_in_state
FROM trip_events e1
WHERE e1.event_type = 'decision_changed'
GROUP BY from_state, to_state
ORDER BY transition_count DESC;

-- Use case: Funnel analysis
```

### 6.4 Trips with Similar Issues

```sql
SELECT
    te.trip_id,
    te.content->>'blocker'->>'type' as blocker_type,
    te.timestamp
FROM trip_events te
WHERE te.event_type = 'blocker_identified'
  AND te.content->>'blocker'->>'type' = (
    SELECT content->>'blocker'->>'type'
    FROM trip_events
    WHERE trip_id = $1
      AND event_type = 'blocker_identified'
    LIMIT 1
  )
ORDER BY te.timestamp DESC
LIMIT 20;

-- Use case: Find similar issues
```

---

## Part 7: Full-Text Search

### 7.1 Basic Text Search

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND to_tsvector('english',
      COALESCE(content->>'message', '') ||
      COALESCE(content->>'summary', '') ||
      COALESCE(content->>'reason', '')
  ) @@ to_tsquery('english', $2)
ORDER BY timestamp DESC;

-- Requires: GIN index on to_tsvector
-- Use case: Search timeline
```

### 7.2 Search with Highlighting

```sql
SELECT
    *,
    ts_headline('english',
        COALESCE(content->>'message', ''),
        to_tsquery('english', $2),
        'MaxWords=50, MinWords=20'
    ) as highlighted_text
FROM trip_events
WHERE trip_id = $1
  AND to_tsvector('english',
      COALESCE(content->>'message', '')
  ) @@ to_tsquery('english', $2);

-- Use case: Search results with context
```

### 7.3 Multi-Field Search

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND to_tsvector('english',
      COALESCE(content->>'message', '') || ' ' ||
      COALESCE(content->>'description', '') || ' ' ||
      COALESCE(content->>'notes', '')
  ) @@ to_tsquery('english', $2)
ORDER BY timestamp DESC;

-- Use case: Comprehensive search
```

### 7.4 Fuzzy Search (pg_trgm)

```sql
SELECT * FROM trip_events
WHERE trip_id = $1
  AND content->>'message' % $2
ORDER BY
    similarity(content->>'message', $2) DESC
LIMIT 20;

-- Requires: pg_trgm extension, GIN index on content
-- Use case: Typo-tolerant search
```

---

## Part 8: Analytical Queries

### 8.1 Conversion Funnel

```sql
WITH funnel_stages AS (
    SELECT
        trip_id,
        MAX(CASE WHEN event_type = 'inquiry_received' THEN timestamp END) as inquiry,
        MAX(CASE WHEN event_type = 'decision_changed' AND content->>'toState' = 'READY_TO_QUOTE' THEN timestamp END) as ready_to_quote,
        MAX(CASE WHEN event_type = 'whatsapp_message_sent' AND content->>'message' LIKE '%quote%' THEN timestamp END) as quote_sent,
        MAX(CASE WHEN event_type = 'decision_changed' AND content->>'toState' = 'READY_TO_BOOK' THEN timestamp END) as ready_to_book,
        MAX(CASE WHEN event_type = 'decision_changed' AND content->>'toState' = 'BOOKED' THEN timestamp END) as booked
    FROM trip_events
    WHERE trip_id = ANY($1)  -- Array of trip IDs
    GROUP BY trip_id
)
SELECT
    COUNT(*) as total_trips,
    COUNT(inquiry) as has_inquiry,
    COUNT(ready_to_quote) as reached_quote_stage,
    COUNT(quote_sent) as quote_sent_count,
    COUNT(ready_to_book) as ready_to_book_count,
    COUNT(booked) as booked_count,
    ROUND(100.0 * COUNT(booked) / NULLIF(COUNT(inquiry), 0), 2) as conversion_rate
FROM funnel_stages;

-- Use case: Funnel analysis dashboard
```

### 8.2 Response Time Analysis

```sql
SELECT
    te1.trip_id,
    te1.timestamp as customer_message_time,
    MIN(te2.timestamp) as first_response_time,
    EXTRACT(EPOCH FROM (MIN(te2.timestamp) - te1.timestamp)) / 60 as response_minutes
FROM trip_events te1
LEFT JOIN trip_events te2 ON
    te2.trip_id = te1.trip_id
    AND te2.timestamp > te1.timestamp
    AND te2.actor->>'type' IN ('agent', 'ai')
WHERE te1.event_type = 'whatsapp_message_received'
  AND te1.timestamp >= NOW() - INTERVAL '30 days'
GROUP BY te1.trip_id, te1.timestamp
ORDER BY response_minutes;

-- Use case: Agent performance metrics
```

### 8.3 Customer Sentiment Trend

```sql
SELECT
    DATE_TRUNC('day', timestamp) as date,
    AVG((metadata->>'aiSentiment'->>'confidence')::float) as avg_sentiment,
    COUNT(*) FILTER (WHERE metadata->>'aiSentiment'->>'sentiment' = 'positive') as positive_count,
    COUNT(*) FILTER (WHERE metadata->>'aiSentiment'->>'sentiment' = 'negative') as negative_count,
    COUNT(*) FILTER (WHERE metadata->>'aiSentiment'->>'sentiment' = 'neutral') as neutral_count
FROM trip_events
WHERE trip_id = $1
  AND metadata ? 'aiSentiment'
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date;

-- Use case: Sentiment analysis chart
```

### 8.4 Trip Duration Analysis

```sql
SELECT
    trip_id,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event,
    MAX(timestamp) - MIN(timestamp) as trip_duration,
    COUNT(*) as event_count,
    COUNT(DISTINCT actor->>'type') as actor_variety
FROM trip_events
WHERE trip_id = ANY($1)  -- Array of trip IDs
GROUP BY trip_id
ORDER BY trip_duration DESC;

-- Use case: Trip complexity analysis
```

### 8.5 Blocker Analysis

```sql
SELECT
    content->>'blocker'->>'type' as blocker_type,
    content->>'blocker'->>'severity' as severity,
    COUNT(*) as occurrence_count,
    AVG(EXTRACT(EPOCH FROM (
        SELECT timestamp
        FROM trip_events resolution
        WHERE resolution.trip_id = trip_events.trip_id
          AND resolution.event_type = 'blocker_resolved'
          AND resolution.content->>'blockerId' = trip_events.id
    ) - trip_events.timestamp) / 3600) as avg_resolution_hours
FROM trip_events
WHERE event_type = 'blocker_identified'
  AND timestamp >= NOW() - INTERVAL '90 days'
GROUP BY blocker_type, severity
ORDER BY occurrence_count DESC;

-- Use case: Common blockers report
```

---

## Part 9: Performance Optimization

### 9.1 Required Indexes

```sql
-- Primary indexes
CREATE INDEX idx_trip_events_trip_id ON trip_events(trip_id);
CREATE INDEX idx_trip_events_timestamp ON trip_events(timestamp DESC);
CREATE INDEX idx_trip_events_type ON trip_events(event_type);
CREATE INDEX idx_trip_events_category ON trip_events(category);

-- Composite indexes
CREATE INDEX idx_trip_events_trip_timestamp ON trip_events(trip_id, timestamp DESC);
CREATE INDEX idx_trip_events_trip_type ON trip_events(trip_id, event_type);
CREATE INDEX idx_trip_events_actor_type ON trip_events((actor->>'type'));

-- GIN indexes for JSONB
CREATE INDEX idx_trip_events_content ON trip_events USING GIN (content);
CREATE INDEX idx_trip_events_metadata ON trip_events USING GIN (metadata);

-- Full-text search
CREATE INDEX idx_trip_events_fts ON trip_events
    USING GIN (to_tsvector('english',
        COALESCE(content->>'message', '') ||
        COALESCE(content->>'summary', '')
    ));

-- Partial indexes
CREATE INDEX idx_trip_events_internal ON trip_events(trip_id, timestamp DESC)
    WHERE (metadata->>'isInternalOnly')::boolean IS NOT TRUE;
```

### 9.2 Query Optimization Tips

| Tip | Description | Impact |
|-----|-------------|--------|
| **Use LIMIT** | Always paginate large results | High |
| **Filter early** | Put WHERE conditions before JOINs | High |
| **Avoid SELECT \*** | Only select needed columns | Medium |
| **Use EXPLAIN ANALYZE** | Check query execution plan | High |
| **Consider materialized views** | For complex aggregations | High |
| **Batch operations** | Use bulk inserts instead of single | Medium |

### 9.3 Materialized Views

```sql
-- Timeline summary (refreshed hourly)
CREATE MATERIALIZED VIEW mv_trip_timeline_summary AS
SELECT
    trip_id,
    COUNT(*) as event_count,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event,
    MAX(timestamp) - MIN(timestamp) as duration,
    COUNT(DISTINCT event_type) as type_variety,
    COUNT(DISTINCT actor->>'name') as actor_count
FROM trip_events
GROUP BY trip_id;

CREATE UNIQUE INDEX mv_trip_timeline_summary_trip_id
    ON mv_trip_timeline_summary(trip_id);

-- Refresh
REFRESH MATERIALIZED VIEW mv_trip_timeline_summary;
```

---

## Part 10: Query Patterns by Feature

### Timeline Display

```sql
-- Main timeline query
SELECT * FROM trip_events
WHERE trip_id = $1
ORDER BY timestamp DESC
LIMIT 50;
```

### Real-time Updates

```sql
-- New events since timestamp
SELECT * FROM trip_events
WHERE trip_id = $1
  AND timestamp > $2
ORDER BY timestamp ASC;
```

### Search

```sql
-- Full-text search
SELECT * FROM trip_events
WHERE trip_id = $1
  AND to_tsvector('english', content) @@ to_tsquery($2)
ORDER BY timestamp DESC;
```

### Filter Panel

```sql
-- Multi-filter query
SELECT * FROM trip_events
WHERE trip_id = $1
  AND event_type = ANY($2)  -- Array of types
  AND timestamp BETWEEN $3 AND $4
  AND actor->>'type' = ANY($5)  -- Array of actor types
ORDER BY timestamp DESC;
```

### Statistics Dashboard

```sql
-- Aggregate stats
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE event_type = 'whatsapp_message_received') as customer_messages,
    COUNT(*) FILTER (WHERE event_type = 'whatsapp_message_sent') as agent_messages,
    MIN(timestamp) as start_date,
    MAX(timestamp) as last_activity
FROM trip_events
WHERE trip_id = $1;
```

---

## Summary

**Query Patterns Summary:**

| Pattern | Complexity | Use Case |
|---------|------------|----------|
| Basic retrieval | Low | Timeline display |
| Filtered | Medium | Filter panel |
| Aggregated | Medium | Statistics |
| Temporal | High | Activity charts |
| Relational | High | Similar trips |
| Full-text | Medium | Search |
| Analytical | High | Business intelligence |

**Performance Targets:**
- Simple queries: <10ms
- Filtered queries: <50ms
- Aggregated queries: <200ms
- Analytical queries: <1s

**Index Strategy:**
- All WHERE columns indexed
- Composite indexes for common patterns
- GIN indexes for JSONB search
- Partial indexes for common filters

---

**Status:** Query patterns reference complete.
**Version:** 1.0
**Last Updated:** 2026-04-23
