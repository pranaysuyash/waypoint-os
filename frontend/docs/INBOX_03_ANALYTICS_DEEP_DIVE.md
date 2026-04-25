# INBOX_03: Analytics Deep Dive

> Inbox Management System — Metrics, Funnels, and Performance Analytics

---

## Table of Contents

1. [Overview](#overview)
2. [Key Performance Indicators](#key-performance-indicators)
3. [Funnel Analysis](#funnel-analysis)
4. [Metrics Architecture](#metrics-architecture)
5. [Event Tracking](#event-tracking)
6. [Dashboard Specifications](#dashboard-specifications)
7. [Query Patterns](#query-patterns)
8. [Alerting and Anomaly Detection](#alerting-and-anomaly-detection)
9. [Export and Reporting](#export-and-reporting)

---

## Overview

The Inbox analytics system provides visibility into:
- **Triage effectiveness** — How well the system prioritizes work
- **Agent productivity** — Individual and team performance
- **Process bottlenecks** — Where trips get stuck
- **Customer experience** — Response times and service quality
- **System health** — Performance and reliability metrics

### Analytics Philosophy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     INBOX ANALYTICS PHILOSOPHY                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Actionable Metrics                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐ │
│     │ Every metric must drive a specific action or insight            │ │
│     │ No vanity metrics — only what changes behavior                  │ │
│     └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  2. Multi-Dimensional Analysis                                          │
│     ┌─────────────────────────────────────────────────────────────────┐ │
│     │ Cut data by: agent, time, channel, customer, trip type          │ │
│     │ Enable root cause analysis, not just surface trends             │ │
│     └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  3. Real-Time + Historical                                             │
│     ┌─────────────────────────────────────────────────────────────────┐ │
│     │ Real-time: Operations monitoring, alerting                       │ │
│     │ Historical: Trend analysis, forecasting, planning               │ │
│     └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  4. Funnel-Centric                                                      │
│     ┌─────────────────────────────────────────────────────────────────┐ │
│     │ Track trips through lifecycle: intake → triage → action → close │ │
│     │ Identify drop-off points and conversion issues                  │ │
│     └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Performance Indicators

### Tier 1: Executive Metrics

| Metric | Definition | Target | Calculation |
|--------|-----------|--------|-------------|
| **Response Time (P50)** | Median time to first agent action | < 15 min | `percentile(firstActionTime - createdAt, 50)` |
| **Response Time (P95)** | 95th percentile response time | < 1 hour | `percentile(firstActionTime - createdAt, 95)` |
| **Triage Accuracy** | % of trips in correct priority bucket | > 90% | `correctPriority / totalTrips * 100` |
| **Daily Close Rate** | % of inbox cleared daily | > 80% | `closedToday / receivedToday * 100` |
| **Customer Satisfaction** | Post-service rating | > 4.5/5 | `avg(customerRating)` |

### Tier 2: Operational Metrics

| Metric | Definition | Target | Calculation |
|--------|-----------|--------|-------------|
| **First Contact Resolution** | % resolved in single interaction | > 70% | `singleTouchTrips / totalTrips * 100` |
| **Reassignment Rate** | % of trips reassigned | < 15% | `reassignedTrips / totalTrips * 100` |
| **Escalation Rate** | % escalated to owner/senior | < 10% | `escalatedTrips / totalTrips * 100` |
| **SLA Breach Rate** | % exceeding SLA thresholds | < 5% | `breachedTrips / totalTrips * 100` |
| **Automation Rate** | % auto-triaged without human review | > 60% | `autoTriaged / totalTrips * 100` |

### Tier 3: Agent Performance Metrics

| Metric | Definition | Target | Calculation |
|--------|-----------|--------|-------------|
| **Trips per Day** | Average trips processed per agent | 25-40 | `tripsProcessed / agentDays` |
| **Average Handle Time** | Time from first action to close | 15-30 min | `avg(closedAt - firstActionTime)` |
| **Quality Score** | Audit score on work quality | > 95% | `avg(auditScore)` |
| **Error Rate** | % requiring correction/escalation | < 5% | `errorTrips / processedTrips * 100` |
| **Utilization** | % of workday actively processing | 70-85% | `activeTime / totalTime * 100` |

### Tier 4: System Health Metrics

| Metric | Definition | Target | Calculation |
|--------|-----------|--------|-------------|
| **Inbox Load** | Current trips vs capacity | < 80% | `currentTrips / capacity * 100` |
| **API Latency (P95)** | Request response time | < 200ms | `percentile(responseTime, 95)` |
| **WebSocket Message Latency** | Real-time update delivery | < 100ms | `avg(deliveryTime)` |
| **Index Hit Rate** | Query cache effectiveness | > 95% | `cacheHits / totalQueries * 100` |
| **Error Rate** | Failed operations | < 0.1% | `errors / totalOps * 100` |

---

## Funnel Analysis

### Primary Funnel: Trip Lifecycle

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          TRIP LIFECYCLE FUNNEL                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │   RECEIVED   │────▶│   TRIAGED    │────▶│  ASSIGNED    │              │
│  │              │     │              │     │              │              │
│  │  10,000      │     │   9,500      │     │   9,000      │              │
│  │  (100%)      │     │   (95%)      │     │   (90%)      │              │
│  └──────────────┘     └──────────────┘     └──────────────┘              │
│         │                    │                    │                       │
│         │ 500 (5%)           │ 500 (5%)            │                       │
│         │ Duplicates         │ Auto-closed         │                       │
│         ▼                    ▼                    ▼                       │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │  IN PROGRESS │────▶│   RESOLVED   │────▶│   CLOSED     │              │
│  │              │     │              │     │              │              │
│  │   8,500      │     │   8,000      │     │   7,500      │              │
│  │   (85%)      │     │   (80%)      │     │   (75%)      │              │
│  └──────────────┘     └──────────────┘     └──────────────┘              │
│         │                    │                                            │
│         │ 500 (5%)           │ 500 (5%)                                   │
│         │ Stalled > 7 days   │ Reopened                                   │
│         ▼                    ▼                                            │
│  ┌──────────────┐     ┌──────────────┐                                   │
│  │  ESCALATED   │     │  LOST/CANCEL │                                   │
│  │              │     │              │                                   │
│  │     500      │     │    1,500     │                                   │
│  │    (5%)      │     │   (15%)      │                                   │
│  └──────────────┘     └──────────────┘                                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Overall Conversion: 75% (received to closed)
Drop-off Analysis:
  - Duplication filter: 5% (acceptable)
  - Auto-close: 5% (needs review)
  - Stalled trips: 5% (actionable)
  - Reopened: 5% (quality issue)
  - Lost/cancel: 15% (expected)
```

### Secondary Funnel: Triage Decision

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         TRIAGE DECISION FUNNEL                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                         ┌─────────────────┐                               │
│                         │  NEW TRIP ARR   │                               │
│                         │     10,000      │                               │
│                         └────────┬────────┘                               │
│                                  │                                         │
│              ┌───────────────────┼───────────────────┐                    │
│              │                   │                   │                    │
│              ▼                   ▼                   ▼                    │
│     ┌────────────┐      ┌────────────┐      ┌────────────┐               │
│     │   AUTO     │      │   SMART    │      │  MANUAL    │               │
│     │ TRIAGE     │      │ SUGGEST    │      │ REVIEW     │               │
│     │            │      │            │      │            │               │
│     │   6,000    │      │   3,000    │      │   1,000    │               │
│     │  (60%)     │      │  (30%)     │      │  (10%)     │               │
│     └─────┬──────┘      └─────┬──────┘      └─────┬──────┘               │
│           │                  │                  │                        │
│           │ 5,700 accepted   │ 2,700 accepted   │ 900 accepted           │
│           │ 300 overridden    │ 300 overridden    │ 100 modified          │
│           ▼                  ▼                  ▼                        │
│     ┌─────────────────────────────────────────────────┐                 │
│     │            FINAL TRIAGE ASSIGNMENT              │                 │
│     │                                               │                 │
│     │  Critical: 500 (5%)  │  High: 2,000 (20%)     │                 │
│     │  Medium:   5,000 (50%) │ Low:    2,500 (25%)  │                 │
│     └─────────────────────────────────────────────────┘                 │
│                                                                            │
│ Triage Accuracy: 92% (9,200 correct / 10,000)                            │
│ Override Rate: 8% (800 overridden / 10,000)                              │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Tertiary Funnel: Resolution Path

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         RESOLUTION PATH FUNNEL                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                              ┌──────────────┐                               │
│                              │ ASSIGNED TRIP│                               │
│                              │    9,000     │                               │
│                              └──────┬───────┘                               │
│                                     │                                       │
│         ┌───────────────────────────┼───────────────────────────┐         │
│         │                           │                           │         │
│         ▼                           ▼                           ▼         │
│  ┌────────────┐            ┌────────────┐            ┌────────────┐       │
│  │   QUOTE    │            │  BOOKING   │            │  SUPPORT   │       │
│  │ REQUEST    │            │ REQUEST   │            │  REQUEST   │       │
│  │            │            │            │            │            │       │
│  │   4,000    │            │   3,500    │            │   1,500    │       │
│  │  (44%)     │            │  (39%)     │            │  (17%)     │       │
│  └─────┬──────┘            └─────┬──────┘            └─────┬──────┘       │
│        │                        │                        │               │
│        ▼                        ▼                        ▼               │
│  ┌────────────┐            ┌────────────┐            ┌────────────┐       │
│  │  QUOTED    │            │  BOOKED    │            │ RESOLVED   │       │
│  │ 3,500      │            │  2,800     │            │ 1,200      │       │
│  │  (87%)     │            │  (80%)     │            │  (80%)     │       │
│  └─────┬──────┘            └─────┬──────┘            └─────┬──────┘       │
│        │                        │                        │               │
│        ▼                        ▼                        ▼               │
│  ┌────────────┐            ┌────────────┐            ┌────────────┐       │
│  │ BOOKING    │            │ CONFIRMED  │            │ CLOSED     │       │
│  │ 2,000      │            │  2,500     │            │  1,000     │       │
│  │ (57% quoted)│           │  (89% booked)│           │  (83% resolved)│  │
│  └────────────┘            └────────────┘            └────────────┘       │
│                                                                            │
│ Path Conversions:                                                         │
│   Quote Request → Booking: 50% (2,000 / 4,000)                          │
│   Booking Request → Confirmed: 71% (2,500 / 3,500)                       │
│   Support Request → Resolved: 80% (1,200 / 1,500)                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Metrics Architecture

### Data Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           METRICS DATA FLOW                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌───────────┐  │
│  │   INBOX     │    │  EVENTS     │    │  METRICS    │    │  DASH     │  │
│  │   SERVICE   │───▶│  COLLECTOR  │───▶│  AGGREGATOR │───▶│  BOARD    │  │
│  │             │    │             │    │             │    │           │  │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘    └───────────┘  │
│      │  │                   │                   │                          │
│      │  │                   ▼                   ▼                          │
│      │  │            ┌─────────────┐    ┌─────────────┐                   │
│      │  │            │  KAFKA /    │    │   REDIS     │                   │
│      │  │            │  EVENT BUS  │    │   CACHE     │                   │
│      │  │            │             │    │             │                   │
│      │  │            └──────┬──────┘    └─────────────┘                   │
│      │  │                   │                   │                          │
│      │  │                   ▼                   ▼                          │
│      │  │            ┌─────────────┐    ┌─────────────┐                   │
│      │  └───────────▶│ CLICKHOUSE  │◀───▶ TIMESCALE   │                   │
│      │                │ (OLAP)      │    │ (Time Series)│                  │
│      │                │             │    │             │                   │
│      ▼                └──────┬──────┘    └──────┬──────┘                   │
│  ┌─────────────┐              │                  │                          │
│  │ POSTGRESQL  │              ▼                  ▼                          │
│  │ (Operational│     ┌─────────────────────────────┐                       │
│  │  Data Store)│     │         ANALYTICS           │                       │
│  │             │     │         LAYER               │                       │
│  └─────────────┘     │  • Ad-hoc queries           │                       │
│                      │  • Funnel analysis          │                       │
│                      │  • Trend detection          │                       │
│                      │  • Anomaly detection        │                       │
│                      └─────────────────────────────┘                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Storage Strategy

```typescript
// events/inbox_events.ts
interface InboxEvent {
  id: string;
  eventType: InboxEventType;
  timestamp: Date;
  tripId: string;
  agentId?: string;
  customerId?: string;
  data: Record<string, unknown>;
  metadata: {
    source: 'web' | 'api' | 'websocket' | 'system';
    sessionId?: string;
    requestId?: string;
  };
}

type InboxEventType =
  // Trip lifecycle events
  | 'trip.created'
  | 'trip.assigned'
  | 'trip.reassigned'
  | 'trip.started'
  | 'trip.closed'
  | 'trip.reopened'
  | 'trip.escalated'

  // View events
  | 'inbox.viewed'
  | 'trip.viewed'
  | 'filter.applied'
  | 'sort.changed'

  // Action events
  | 'trip.archived'
  | 'trip.pinned'
  | 'bulk.action'
  | 'export.executed';

// metrics/aggregator.ts
interface MetricAggregation {
  metric: string;
  window: '1m' | '5m' | '15m' | '1h' | '1d' | '1w';
  dimensions: MetricDimension[];
  aggregation: 'count' | 'sum' | 'avg' | 'p50' | 'p95' | 'p99';
  filters: MetricFilter[];
}

type MetricDimension =
  | 'agentId'
  | 'customerId'
  | 'priority'
  | 'status'
  | 'channel'
  | 'tripType'
  | 'timeBucket';

interface TimeSeriesMetric {
  metric: string;
  timestamp: Date;
  value: number;
  dimensions: Record<string, string>;
}

// ClickHouse schema for analytics
const clickHouseSchema = `
CREATE TABLE inbox_events_local (
  event_id UUID,
  event_type String,
  timestamp DateTime64(3),
  trip_id String,
  agent_id String,
  customer_id String,
  priority Enum8('critical'=1, 'high'=2, 'medium'=3, 'low'=4),
  status Enum8('new'=1, 'assigned'=2, 'in_progress'=3, 'resolved'=4, 'closed'=5),
  channel Enum8('email'=1, 'whatsapp'=2, 'web'=3, 'phone'=4),
  trip_type String,
  data String,  // JSON encoded
  metadata String,  // JSON encoded
  date Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_type, timestamp, trip_id)
SETTINGS index_granularity = 8192;

-- Materialized view for funnel analysis
CREATE MATERIALIZED VIEW inbox_funnel_mv
ENGINE = SummingMergeTree()
ORDER BY (date, event_type, trip_id)
AS SELECT
  date,
  event_type,
  trip_id,
  count() as count
FROM inbox_events_local
GROUP BY date, event_type, trip_id;

-- Materialized view for agent metrics
CREATE MATERIALIZED VIEW inbox_agent_metrics_mv
ENGINE = AggregatingMergeTree()
ORDER BY (agent_id, date)
AS SELECT
  agent_id,
  date,
  countState(trip_id) as trips_processed,
  avgState(timestamp - min(timestamp) OVER (PARTITION BY trip_id)) as avg_handle_time
FROM inbox_events_local
WHERE event_type LIKE 'trip.%'
GROUP BY agent_id, date;
`;
```

### Aggregation Jobs

```typescript
// jobs/metrics_aggregation.ts
class MetricsAggregator {
  private readonly windows = {
    '1m': 60,
    '5m': 300,
    '15m': 900,
    '1h': 3600,
    '1d': 86400,
    '1w': 604800,
  };

  async aggregateMetrics(window: string): Promise<void> {
    const events = await this.getEventsForWindow(window);

    await Promise.all([
      this.aggregateFunnelMetrics(events, window),
      this.aggregateAgentMetrics(events, window),
      this.aggregateResponseTimeMetrics(events, window),
      this.aggregateTriageMetrics(events, window),
      this.aggregateSystemMetrics(events, window),
    ]);
  }

  private async aggregateFunnelMetrics(
    events: InboxEvent[],
    window: string
  ): Promise<void> {
    const funnel = {
      received: events.filter(e => e.eventType === 'trip.created').length,
      triaged: events.filter(e => e.eventType === 'trip.assigned').length,
      started: events.filter(e => e.eventType === 'trip.started').length,
      resolved: events.filter(e => e.eventType === 'trip.closed').length,
      reopened: events.filter(e => e.eventType === 'trip.reopened').length,
      escalated: events.filter(e => e.eventType === 'trip.escalated').length,
    };

    await this.storeMetrics('funnel', funnel, window);
  }

  private async aggregateAgentMetrics(
    events: InboxEvent[],
    window: string
  ): Promise<void> {
    const byAgent = this.groupBy(events, 'agentId');

    for (const [agentId, agentEvents] of Object.entries(byAgent)) {
      const metrics = {
        tripsProcessed: agentEvents.filter(e => e.eventType === 'trip.closed').length,
        avgHandleTime: this.calculateAvgHandleTime(agentEvents),
        errorRate: this.calculateErrorRate(agentEvents),
        escalationRate: this.calculateEscalationRate(agentEvents),
      };

      await this.storeMetrics('agent', metrics, window, { agentId });
    }
  }

  private async aggregateResponseTimeMetrics(
    events: InboxEvent[],
    window: string
  ): Promise<void> {
    const tripIds = [...new Set(events.map(e => e.tripId))];
    const responseTimes: number[] = [];

    for (const tripId of tripIds) {
      const tripEvents = events.filter(e => e.tripId === tripId);
      const created = tripEvents.find(e => e.eventType === 'trip.created');
      const started = tripEvents.find(e => e.eventType === 'trip.started');

      if (created && started) {
        const ms = started.timestamp.getTime() - created.timestamp.getTime();
        responseTimes.push(ms);
      }
    }

    await this.storeMetrics('response_time', {
      p50: this.percentile(responseTimes, 50),
      p95: this.percentile(responseTimes, 95),
      p99: this.percentile(responseTimes, 99),
      avg: this.average(responseTimes),
    }, window);
  }

  private async aggregateTriageMetrics(
    events: InboxEvent[],
    window: string
  ): Promise<void> {
    const triageEvents = events.filter(e => e.eventType === 'trip.assigned');

    const autoTriaged = triageEvents.filter(e =>
      e.data.assignmentMethod === 'auto'
    ).length;

    const overridden = triageEvents.filter(e =>
      e.data.overriddenFrom !== undefined
    ).length;

    const correct = triageEvents.filter(e =>
      e.data.priorityCorrect === true
    ).length;

    await this.storeMetrics('triage', {
      automationRate: autoTriaged / triageEvents.length,
      overrideRate: overridden / triageEvents.length,
      accuracy: correct / triageEvents.length,
    }, window);
  }

  private async storeMetrics(
    metricType: string,
    value: Record<string, number>,
    window: string,
    dimensions?: Record<string, string>
  ): Promise<void> {
    const timestamp = this.bucketTimestamp(Date.now(), window);

    await this.clickHouse.insert({
      table: 'inbox_metrics',
      values: Object.entries(value).map(([name, val]) => ({
        metric_type: metricType,
        metric_name: name,
        window,
        timestamp,
        value: val,
        dimensions: JSON.stringify(dimensions || {}),
      })),
    });
  }

  private bucketTimestamp(timestamp: number, window: string): Date {
    const seconds = this.windows[window as keyof typeof this.windows] || 3600;
    return new Date(Math.floor(timestamp / 1000 / seconds) * seconds * 1000);
  }

  private groupBy<T>(items: T[], key: keyof T): Record<string, T[]> {
    return items.reduce((acc, item) => {
      const k = String(item[key] || 'null');
      acc[k] = acc[k] || [];
      acc[k].push(item);
      return acc;
    }, {} as Record<string, T[]>);
  }

  private percentile(arr: number[], p: number): number {
    const sorted = [...arr].sort((a, b) => a - b);
    const index = Math.floor(sorted.length * p / 100);
    return sorted[index] || 0;
  }

  private average(arr: number[]): number {
    return arr.length > 0
      ? arr.reduce((a, b) => a + b, 0) / arr.length
      : 0;
  }
}
```

---

## Event Tracking

### Event Schema

```typescript
// events/schemas.ts
export const inboxEventSchemas = {
  // Trip events
  'trip.created': z.object({
    tripId: z.string(),
    source: z.enum(['email', 'whatsapp', 'web', 'api', 'phone']),
    customerId: z.string(),
    initialPriority: z.enum(['critical', 'high', 'medium', 'low']),
    autoTriaged: z.boolean(),
    assignedTo: z.string().optional(),
  }),

  'trip.assigned': z.object({
    tripId: z.string(),
    assignedTo: z.string(),
    assignedBy: z.string().optional(),
    priority: z.enum(['critical', 'high', 'medium', 'low']),
    assignmentMethod: z.enum(['auto', 'manual', 'round-robin', 'load-balance']),
    previousAssignee: z.string().optional(),
  }),

  'trip.started': z.object({
    tripId: z.string(),
    agentId: z.string(),
    timeToFirstAction: z.number(), // milliseconds
  }),

  'trip.closed': z.object({
    tripId: z.string(),
    agentId: z.string(),
    resolutionType: z.enum(['quoted', 'booked', 'cancelled', 'lost', 'transferred']),
    handleTime: z.number(), // milliseconds
    customerSatisfaction: z.number().min(1).max(5).optional(),
  }),

  'trip.reopened': z.object({
    tripId: z.string(),
    reopenedBy: z.string(),
    reason: z.string(),
    timeSinceClose: z.number(),
  }),

  'trip.escalated': z.object({
    tripId: z.string(),
    escalatedFrom: z.string(),
    escalatedTo: z.string(),
    escalationReason: z.string(),
    escalationLevel: z.enum(['senior_agent', 'team_lead', 'owner']),
  }),

  // View events
  'inbox.viewed': z.object({
    agentId: z.string(),
    viewMode: z.enum(['list', 'table', 'kanban', 'timeline']),
    filters: z.record(z.unknown()),
    sortBy: z.string(),
    sortOrder: z.enum(['asc', 'desc']),
    resultCount: z.number(),
  }),

  'trip.viewed': z.object({
    tripId: z.string(),
    agentId: z.string(),
    viewSource: z.enum(['inbox', 'search', 'direct_link', 'notification']),
    previousTripId: z.string().optional(),
  }),

  // Action events
  'filter.applied': z.object({
    agentId: z.string(),
    filterType: z.string(),
    filterValue: z.unknown(),
    resultCount: z.number(),
  }),

  'bulk.action': z.object({
    agentId: z.string(),
    action: z.enum(['archive', 'assign', 'change_priority', 'export']),
    tripCount: z.number(),
    tripIds: z.array(z.string()),
  }),

  'export.executed': z.object({
    agentId: z.string(),
    exportType: z.enum(['csv', 'excel', 'pdf']),
    tripCount: z.number(),
    filters: z.record(z.unknown()),
    fileSize: z.number(),
  }),
};

// events/collector.ts
class InboxEventCollector {
  private kafka: Kafka;
  private clickHouse: ClickHouse;

  async track(eventType: string, data: unknown): Promise<void> {
    // Validate against schema
    const schema = inboxEventSchemas[eventType as keyof typeof inboxEventSchemas];
    if (!schema) {
      throw new Error(`Unknown event type: ${eventType}`);
    }

    const validated = schema.parse(data);

    // Create event
    const event: InboxEvent = {
      id: crypto.randomUUID(),
      eventType: eventType as InboxEventType,
      timestamp: new Date(),
      tripId: validated.tripId || data.tripId as string,
      agentId: validated.agentId || data.agentId as string,
      customerId: validated.customerId || data.customerId as string,
      data: validated as Record<string, unknown>,
      metadata: {
        source: this.detectSource(),
        sessionId: this.getSessionId(),
        requestId: this.getRequestId(),
      },
    };

    // Emit to Kafka for async processing
    await this.kafka.send('inbox-events', {
      key: event.tripId,
      value: JSON.stringify(event),
    });

    // Store in ClickHouse for analytics
    await this.clickHouse.insert({
      table: 'inbox_events_local',
      values: [{
        event_id: event.id,
        event_type: event.eventType,
        timestamp: event.timestamp,
        trip_id: event.tripId,
        agent_id: event.agentId || '',
        customer_id: event.customerId || '',
        data: JSON.stringify(event.data),
        metadata: JSON.stringify(event.metadata),
      }],
    });
  }

  private detectSource(): 'web' | 'api' | 'websocket' | 'system' {
    // Detect from request context
    return 'web';
  }

  private getSessionId(): string | undefined {
    // Get from session store
    return undefined;
  }

  private getRequestId(): string | undefined {
    // Get from request context
    return undefined;
  }
}

// Singleton instance
export const eventCollector = new InboxEventCollector();
```

---

## Dashboard Specifications

### Executive Dashboard

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         INBOX EXECUTIVE DASHBOARD                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  KEY PERFORMANCE INDICATORS                                          │  │
│  │                                                                       │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐          │  │
│  │  │ RESPONSE  │  │ TRIAGE    │  │ CLOSE     │  │ CUSTOMER  │          │  │
│  │  │ TIME      │  │ ACCURACY  │  │ RATE      │  │ SATISF.   │          │  │
│  │  │           │  │           │  │           │  │           │          │  │
│  │  │  12 min   │  │   92%     │  │   85%     │  │   4.7/5   │          │  │
│  │  │  ▼ 8%     │  │  ▲ 2%     │  │  ▲ 5%     │  │  →        │          │  │
│  │  │  Target:   │  │  Target:  │  │  Target:  │  │  Target:  │          │  │
│  │  │   15 min  │  │   90%     │  │   80%     │  │   4.5     │          │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘          │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  INBOX VOLUME (Last 24 Hours)                                        │  │
│  │                                                                       │  │
│  │  150 ┤                               ╭─────╮                        │  │
│  │      │                           ╭───╯     ╰──╮                     │  │
│  │  100 ┤                      ╭───╮─╮           ╰──╮                  │  │
│  │      │                  ╭───╯   │ ╰──╮          ╰─╮                 │  │
│  │   50 ┤             ╭───╮─╯      ╰────╯            ╰─╮               │  │
│  │      │        ╭───╮─╯ ╰──╮                           ╰──╮           │  │
│  │    0 ┼────────┴───┴─────┴─────────────────────────────┴──────────  │  │
│  │        00:00   04:00   08:00   12:00   16:00   20:00   24:00       │  │
│  │                                                                       │  │
│  │  Incoming │││ Closed   │││ Escalated                              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────┐   │
│  │  TRIP FUNNEL (Today)             │  │  TOP BOTTLENECKS             │   │
│  │                                   │  │                              │   │
│  │  Received      1,247  ━━━━━━━━━━│  │  • High priority: 45 trips   │   │
│  │  Triaged        1,180  ━━━━━━━━━┤  │    avg wait: 2h 15m         │   │
│  │  Assigned       1,100  ━━━━━━━━┤│  │                              │   │
│  │  In Progress      850  ━━━━━━━┤││  │  • Quotes pending: 28 trips  │   │
│  │  Resolved         720  ━━━━━━┤│││  │    avg age: 4h 30m         │   │
│  │  Closed           680  ━━━━┤││││  │                              │   │
│  │                                   │  │  • Stalled >7d: 12 trips    │   │
│  │  Conversion: 54.5%               │  │    needs review             │   │
│  └──────────────────────────────────┘  └──────────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Operations Dashboard

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         INBOX OPERATIONS DASHBOARD                        │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  CURRENT INBOX STATE                                                 │  │
│  │                                                                       │  │
│  │  Critical: 12 │││││││  High: 45 │││││  Medium: 156 │││  Low: 234 ││  │  │
│  │  [████████░░] 12%    [██████████] 100%   [██████░░░░] 60%           │  │
│  │                                                                       │  │
│  │  Total: 447 │ Capacity: 600 │ Utilization: 75% │ Trend: ─╮          │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────┐ │
│  │  AGENT STATUS                       │  │  CHANNEL PERFORMANCE         │ │
│  │                                      │  │                              │ │
│  │  ┌─────────────────────────────┐    │  │  Email     ││││││││ 45%    │ │
│  │  │ Active: 8 / 10              │    │  │  WhatsApp  ││││││││ 35%    │ │
│  │  │ Idle: 1 / 10                │    │  │  Web       ││││││   15%    │ │
│  │  │ Offline: 1 / 10             │    │  │  Phone     ││││     5%    │ │
│  │  └─────────────────────────────┘    │  │                              │ │
│  │                                      │  │  SLA Breach: 3.2% (Target: 5%)│ │
│  │  Load Distribution:                  │  └─────────────────────────────┘ │
│  │  ┌────────────────────────────┐      │                                  │
│  │  │ Agent    │ Load │ Assigns │      │  ┌─────────────────────────────┐ │
│  │  ├──────────┼──────┼─────────┤      │  │  RECENT ACTIVITY            │ │
│  │  │ Sarah    │ 85%  │   12    │      │  │  • Trip #1234 escalated      │ │
│  │  │ Mike     │ 92%  │   14    │      │  │    2 min ago                 │ │
│  │  │ Emma     │ 68%  │    9    │      │  │                              │ │
│  │  │ John     │ 75%  │   10    │      │  │  • 5 trips auto-triaged      │ │
│  │  │ ...      │ ...  │   ...   │      │  │    5 min ago                 │ │
│  │  └──────────┴──────┴─────────┘      │  │                              │ │
│  │                                      │  │  • Sarah completed quote     │ │
│  └─────────────────────────────────────┘  │    for Trip #1198            │ │
│                                            │  • 8 min ago                 │ │
│                                            └─────────────────────────────┘ │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  RESPONSE TIME DISTRIBUTION (Last Hour)                              │  │
│  │                                                                       │  │
│  │  100 ┤   ╭──╮                                                        │  │
│  │      │  ╭╯  ╰╮               ╭──╮                                     │  │
│  │   75 ┤ ╭╯     ╰──╮          ╭╯  ╰╮                                    │  │
│  │      │╭╯         ╰╮       ╭╯     ╰──╮                                │  │
│  │   50 ┼╯           ╰─────╮─╯         ╰──╮                              │  │
│  │      │                 ╰╯              ╰─╮                            │  │
│  │   25 ┤                                   ╰─╮                          │  │
│  │      │                                      ╰──╮                       │  │
│  │    0 ┼────────────────────────────────────────┴────────────────       │  │
│  │        <5m    5-15m  15-30m 30-1h   1-2h   2-4h   >4h                 │  │
│  │                                                                       │  │
│  │  P50: 12m │ P95: 48m │ P99: 1h 45m │ Avg: 18m                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Agent Performance Dashboard

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        AGENT PERFORMANCE DASHBOARD                        │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Agent: Sarah Miller │ Today, Apr 24, 2026 │ Last 30 Days                  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  PERFORMANCE SUMMARY                                                 │  │
│  │                                                                       │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐          │  │
│  │  │ TRIPS     │  │ AVG       │  │ QUALITY   │  │ ERROR     │          │  │
│  │  │ TODAY     │  │ HANDLE    │  │ SCORE     │  │ RATE      │          │  │
│  │  │           │  │ TIME      │  │           │  │           │          │  │
│  │  │    14     │  │  18 min   │  │   98%     │  │   2.1%    │          │  │
│  │  │  ▲ 2      │  │  ▼ 3 min  │  │  →        │  │  ▼ 0.5%   │          │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘          │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  TRIP TYPE BREAKDOWN (Today)                                         │  │
│  │                                                                       │  │
│  │  Quote Requests    ████████████████░░ 10 (71%)                       │  │
│  │  Booking Requests  ████░░░░░░░░░░░░░░ 3 (21%)                        │  │
│  │  Support Issues    █░░░░░░░░░░░░░░░░░ 1 (7%)                         │  │
│  │  Escalations       ░░░░░░░░░░░░░░░░░░ 0 (0%)                         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌───────────────────────────────────────┐  ┌────────────────────────────┐ │
│  │  WEEKLY TREND                         │  │  SKILL ASSESSMENT          │ │
│  │                                       │  │                             │ │
│  │  Trips/Day                            │  │  International Bookings    │ │
│  │  20 ┤   ╭─╮                          │  │  ████████████████░░ 92%    │ │
│  │      │  ╭╯ ╰╮                         │  │                             │ │
│  │  15 ┤ ╭╯   ╰╮     ╭─╮                │  │  Complex Itineraries       │ │
│  │      │╭╯     ╰╮   ╭╯ ╰╮               │  │  ██████████████░░░░ 87%    │ │
│  │  10 ┼╯       ╰───╯   ╰─╮              │  │                             │ │
│  │      │                  ╰─╮            │  │  Customer Communication    │ │
│  │   5 ┤                    ╰──╮          │  │  ██████████████████ 95%   │ │
│  │      │                       ╰──╮       │  │                             │ │
│  │   0 ┼───────────────────────────┴────   │  │  Problem Resolution        │ │
│  │      M   T   W   T   F   S   S         │  │  ████████████░░░░░░ 82%    │ │
│  │                                       │  └────────────────────────────┘ │
│  │  Avg: 13.4 │ Team Avg: 12.1           │                                  │
│  └───────────────────────────────────────┘                                  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  RESPONSE TIME vs TEAM (Today)                                        │  │
│  │                                                                       │  │
│  │  Sarah  ╶───────────────────────────────────────────────────        │  │
│  │  Team   ╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷╷                 │  │
│  │         │                                                         │  │
│  │  0m    10m    20m    30m    40m    50m                          │  │
│  │                                                                       │  │
│  │  Sarah: 18m (better than 78% of team)                               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Query Patterns

### Funnel Queries

```sql
-- ClickHouse: Trip funnel conversion
WITH funnel_steps AS (
  SELECT
    trip_id,
    countIf(event_type = 'trip.created') as received,
    countIf(event_type = 'trip.assigned') as triaged,
    countIf(event_type = 'trip.started') as started,
    countIf(event_type = 'trip.closed') as closed
  FROM inbox_events_local
  WHERE date >= today() - INTERVAL 7 DAY
  GROUP BY trip_id
  HAVING received > 0
)
SELECT
  count() as total,
  sum(triaged) as triaged_count,
  sum(started) as started_count,
  sum(closed) as closed_count,
  round(triaged_count / total * 100, 2) as triaged_rate,
  round(started_count / total * 100, 2) as started_rate,
  round(closed_count / total * 100, 2) as closed_rate
FROM funnel_steps;

-- Time-to-first-action percentiles
SELECT
  quantile(0.50)(time_to_first_action / 60000) as p50_minutes,
  quantile(0.95)(time_to_first_action / 60000) as p95_minutes,
  quantile(0.99)(time_to_first_action / 60000) as p99_minutes,
  avg(time_to_first_action / 60000) as avg_minutes
FROM (
  SELECT
    trip_id,
    minIf(timestamp, event_type = 'trip.started') -
      minIf(timestamp, event_type = 'trip.created') as time_to_first_action
  FROM inbox_events_local
  WHERE date >= today() - INTERVAL 1 DAY
  GROUP BY trip_id
  HAVING time_to_first_action > 0
);

-- Drop-off analysis by stage
SELECT
  last_event_type,
  count() as trips_stuck,
  avg(now() - max_timestamp) as avg_stuck_duration
FROM (
  SELECT
    trip_id,
    argMax(event_type, timestamp) as last_event_type,
    max(timestamp) as max_timestamp
  FROM inbox_events_local
  WHERE date >= today() - INTERVAL 7 DAY
  GROUP BY trip_id
  HAVING max_timestamp < now() - INTERVAL 4 HOUR
)
GROUP BY last_event_type
ORDER BY trips_stuck DESC;
```

### Agent Performance Queries

```sql
-- Agent productivity (last 7 days)
SELECT
  agent_id,
  count() as trips_closed,
  avg(handle_time_minutes) as avg_handle_time,
  quantile(0.95)(handle_time_minutes) as p95_handle_time,
  sum(if(resolution_type = 'quoted', 1, 0)) as quoted,
  sum(if(resolution_type = 'booked', 1, 0)) as booked,
  round(booked / trips_closed * 100, 2) as booking_rate
FROM (
  SELECT
    trip_id,
    agent_id,
    (maxIf(timestamp, event_type = 'trip.closed') -
      minIf(timestamp, event_type = 'trip.started')) / 60 as handle_time_minutes,
    argMax(data, timestamp)::JSONAsString('String', 'resolutionType') as resolution_type
  FROM inbox_events_local
  WHERE date >= today() - INTERVAL 7 DAY
    AND event_type IN ('trip.started', 'trip.closed')
  GROUP BY trip_id, agent_id
  HAVING handle_time_minutes > 0
)
GROUP BY agent_id
ORDER BY trips_closed DESC;

-- Agent quality score
SELECT
  agent_id,
  sum(quality_score) / count() as avg_quality,
  sum(if(quality_score >= 95, 1, 0)) / count() * 100 as pass_rate,
  countIf(escalated) as escalations,
  countIf(reopened) as reopenings
FROM (
  SELECT
    trip_id,
    agent_id,
    -- Quality from audit data or customer feedback
    randUniform(90, 100) as quality_score,  -- Placeholder
    countIf(event_type = 'trip.escalated') > 0 as escalated,
    countIf(event_type = 'trip.reopened') > 0 as reopened
  FROM inbox_events_local
  WHERE date >= today() - INTERVAL 30 DAY
  GROUP BY trip_id, agent_id
)
GROUP BY agent_id
ORDER BY avg_quality DESC;
```

### Trend Analysis Queries

```sql
-- Daily volume trend with moving average
SELECT
  date,
  sum(incoming) as incoming,
  sum(closed) as closed,
  avg(sum(incoming)) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma7_incoming,
  round(closed / incoming * 100, 2) as close_rate
FROM (
  SELECT
    toDate(timestamp) as date,
    countIf(event_type = 'trip.created') as incoming,
    countIf(event_type = 'trip.closed') as closed
  FROM inbox_events_local
  WHERE date >= today() - INTERVAL 30 DAY
  GROUP BY date
)
GROUP BY date
ORDER BY date;

-- Hour-of-day pattern
SELECT
  toHour(timestamp) as hour,
  count() as trip_count,
  countIf(event_type = 'trip.created') as created,
  countIf(event_type = 'trip.closed') as closed
FROM inbox_events_local
WHERE date >= today() - INTERVAL 30 DAY
GROUP BY hour
ORDER BY hour;

-- Channel performance comparison
SELECT
  channel,
  count() as total,
  avg(response_time_minutes) as avg_response_time,
  quantile(0.95)(response_time_minutes) as p95_response_time,
  countIf(event_type = 'trip.closed') / count() * 100 as close_rate
FROM (
  SELECT
    trip_id,
    JSONExtractString(data, 'source') as channel,
    (minIf(timestamp, event_type = 'trip.started') -
      minIf(timestamp, event_type = 'trip.created')) / 60 as response_time_minutes,
    countIf(event_type = 'trip.closed') as closed_count
  FROM inbox_events_local
  WHERE date >= today() - INTERVAL 7 DAY
  GROUP BY trip_id, channel
)
GROUP BY channel
ORDER BY total DESC;
```

---

## Alerting and Anomaly Detection

### Alert Conditions

```typescript
// alerting/conditions.ts
interface AlertCondition {
  id: string;
  name: string;
  severity: 'critical' | 'warning' | 'info';
  check: () => Promise<boolean>;
  notification: AlertNotification;
}

interface AlertNotification {
  channels: ('slack' | 'email' | 'pagerduty' | 'websocket')[];
  recipients: string[];
  cooldown: number; // seconds
}

const inboxAlertConditions: AlertCondition[] = [
  {
    id: 'inbox-overload',
    name: 'Inbox Capacity Exceeded',
    severity: 'critical',
    check: async () => {
      const current = await getTripCount();
      const capacity = await getCapacity();
      return (current / capacity) > 0.9;
    },
    notification: {
      channels: ['slack', 'pagerduty'],
      recipients: ['ops-team', 'team-lead'],
      cooldown: 300,
    },
  },
  {
    id: 'sla-breach-spike',
    name: 'SLA Breach Rate Spike',
    severity: 'warning',
    check: async () => {
      const currentRate = await getSLABreachRate('1h');
      const baselineRate = await getSLABreachRate('24h');
      return currentRate > baselineRate * 2;
    },
    notification: {
      channels: ['slack', 'email'],
      recipients: ['ops-team'],
      cooldown: 600,
    },
  },
  {
    id: 'response-time-degradation',
    name: 'Response Time Degraded',
    severity: 'warning',
    check: async () => {
      const p95 = await getP95ResponseTime('15m');
      return p95 > 3600000; // 1 hour
    },
    notification: {
      channels: ['slack'],
      recipients: ['ops-team'],
      cooldown: 900,
    },
  },
  {
    id: 'agent-stalled',
    name: 'Agent No Activity',
    severity: 'warning',
    check: async () => {
      const agents = await getActiveAgents();
      const stalled = agents.filter(a =>
        a.lastActivity < new Date(Date.now() - 3600000)
      );
      return stalled.length > 0;
    },
    notification: {
      channels: ['slack'],
      recipients: ['team-lead'],
      cooldown: 1800,
    },
  },
  {
    id: 'triage-failure',
    name: 'Triage Accuracy Drop',
    severity: 'warning',
    check: async () => {
      const accuracy = await getTriageAccuracy('1h');
      return accuracy < 0.8;
    },
    notification: {
      channels: ['slack'],
      recipients: ['ops-team'],
      cooldown: 600,
    },
  },
];

// alerting/monitor.ts
class AlertMonitor {
  private conditions: Map<string, AlertCondition>;
  private lastAlerted: Map<string, Date>;

  constructor() {
    this.conditions = new Map();
    this.lastAlerted = new Map();
    inboxAlertConditions.forEach(c => this.conditions.set(c.id, c));
  }

  async checkAll(): Promise<void> {
    const checks = Array.from(this.conditions.values()).map(condition =>
      this.checkCondition(condition)
    );

    await Promise.all(checks);
  }

  private async checkCondition(condition: AlertCondition): Promise<void> {
    try {
      const triggered = await condition.check();

      if (triggered && this.shouldAlert(condition)) {
        await this.sendAlert(condition);
        this.lastAlerted.set(condition.id, new Date());
      }
    } catch (error) {
      console.error(`Alert check failed for ${condition.id}:`, error);
    }
  }

  private shouldAlert(condition: AlertCondition): boolean {
    const lastAlert = this.lastAlerted.get(condition.id);
    if (!lastAlert) return true;

    const elapsed = (Date.now() - lastAlert.getTime()) / 1000;
    return elapsed >= condition.notification.cooldown;
  }

  private async sendAlert(condition: AlertCondition): Promise<void> {
    const message = this.formatAlert(condition);

    for (const channel of condition.notification.channels) {
      switch (channel) {
        case 'slack':
          await this.sendSlackAlert(condition, message);
          break;
        case 'email':
          await this.sendEmailAlert(condition, message);
          break;
        case 'pagerduty':
          await this.sendPagerDutyAlert(condition, message);
          break;
        case 'websocket':
          await this.sendWebSocketAlert(condition, message);
          break;
      }
    }
  }

  private formatAlert(condition: AlertCondition): string {
    const emoji = {
      critical: ':rotating_light:',
      warning: ':warning:',
      info: ':information_source:',
    };

    return `${emoji[condition.severity]} *${condition.name}*`;
  }
}
```

### Anomaly Detection

```typescript
// analytics/anomaly_detection.ts
class AnomalyDetector {
  private readonly baselineWindow = '7d';
  private readonly detectionWindow = '1h';

  async detectAnomalies(): Promise<Anomaly[]> {
    const anomalies: Anomaly[] = [];

    // Volume anomaly
    const volumeAnomaly = await this.detectVolumeAnomaly();
    if (volumeAnomaly) anomalies.push(volumeAnomaly);

    // Response time anomaly
    const responseTimeAnomaly = await this.detectResponseTimeAnomaly();
    if (responseTimeAnomaly) anomalies.push(responseTimeAnomaly);

    // Channel distribution anomaly
    const channelAnomaly = await this.detectChannelAnomaly();
    if (channelAnomaly) anomalies.push(channelAnomaly);

    // Agent behavior anomaly
    const agentAnomaly = await this.detectAgentAnomaly();
    if (agentAnomaly) anomalies.push(agentAnomaly);

    return anomalies;
  }

  private async detectVolumeAnomaly(): Promise<Anomaly | null> {
    const current = await this.getTripCount(this.detectionWindow);
    const baseline = await this.getAverageTripCount(this.baselineWindow);

    // Z-score detection
    const stdDev = await this.getStdDevTripCount(this.baselineWindow);
    const zScore = Math.abs((current - baseline) / stdDev);

    if (zScore > 3) {
      return {
        type: 'volume_spike',
        severity: zScore > 4 ? 'critical' : 'warning',
        description: `Trip volume is ${zScore.toFixed(1)}σ above baseline`,
        currentValue: current,
        baselineValue: baseline,
        recommendation: current > baseline
          ? 'Consider adding agent capacity'
          : 'Investigate drop in incoming trips',
      };
    }

    return null;
  }

  private async detectResponseTimeAnomaly(): Promise<Anomaly | null> {
    const current = await this.getP95ResponseTime(this.detectionWindow);
    const baseline = await this.getAverageP95ResponseTime(this.baselineWindow);

    // Percent change detection
    const percentChange = ((current - baseline) / baseline) * 100;

    if (percentChange > 50) {
      return {
        type: 'response_time_degradation',
        severity: percentChange > 100 ? 'critical' : 'warning',
        description: `P95 response time increased by ${percentChange.toFixed(0)}%`,
        currentValue: current,
        baselineValue: baseline,
        recommendation: 'Check for system issues or agent availability',
      };
    }

    return null;
  }

  private async detectChannelAnomaly(): Promise<Anomaly | null> {
    const current = await this.getChannelDistribution(this.detectionWindow);
    const baseline = await this.getChannelDistribution(this.baselineWindow);

    const anomalies: string[] = [];

    for (const [channel, count] of Object.entries(current)) {
      const baselineCount = baseline[channel] || 0;
      const percentChange = ((count - baselineCount) / baselineCount) * 100;

      if (Math.abs(percentChange) > 30) {
        anomalies.push(
          `${channel}: ${percentChange > 0 ? '+' : ''}${percentChange.toFixed(0)}%`
        );
      }
    }

    if (anomalies.length > 0) {
      return {
        type: 'channel_distribution_shift',
        severity: 'warning',
        description: `Channel distribution shift: ${anomalies.join(', ')}`,
        currentValue: current,
        baselineValue: baseline,
        recommendation: 'Investigate channel-specific issues',
      };
    }

    return null;
  }

  private async detectAgentAnomaly(): Promise<Anomaly | null> {
    const agents = await this.getAgentProductivity(this.detectionWindow);
    const baseline = await this.getAgentProductivityBaseline(this.baselineWindow);

    const underperforming: string[] = [];
    const overperforming: string[] = [];

    for (const [agentId, productivity] of Object.entries(agents)) {
      const agentBaseline = baseline[agentId] || 0;
      const percentChange = ((productivity - agentBaseline) / agentBaseline) * 100;

      if (percentChange < -30) {
        underperforming.push(agentId);
      } else if (percentChange > 50) {
        overperforming.push(agentId);
      }
    }

    if (underperforming.length > 0 || overperforming.length > 0) {
      const messages = [];
      if (underperforming.length > 0) {
        messages.push(`Underperforming: ${underperforming.join(', ')}`);
      }
      if (overperforming.length > 0) {
        messages.push(`Overperforming: ${overperforming.join(', ')}`);
      }

      return {
        type: 'agent_productivity_anomaly',
        severity: 'warning',
        description: messages.join(' | '),
        currentValue: agents,
        baselineValue: baseline,
        recommendation: 'Review agent assignments and workload',
      };
    }

    return null;
  }
}

interface Anomaly {
  type: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  currentValue: unknown;
  baselineValue: unknown;
  recommendation: string;
}
```

---

## Export and Reporting

### Export Configuration

```typescript
// export/configuration.ts
interface ExportConfig {
  format: 'csv' | 'excel' | 'pdf';
  dateRange: {
    start: Date;
    end: Date;
  };
  filters: ExportFilter[];
  columns: ExportColumn[];
  aggregation?: 'trip' | 'agent' | 'daily' | 'weekly';
  includeCharts?: boolean;
}

interface ExportFilter {
  field: string;
  operator: 'equals' | 'contains' | 'in' | 'between';
  value: unknown;
}

interface ExportColumn {
  field: string;
  label: string;
  format?: 'number' | 'currency' | 'date' | 'duration' | 'percentage';
  aggregation?: 'sum' | 'avg' | 'count' | 'min' | 'max';
}

// export/generator.ts
class MetricsExportGenerator {
  async generateExport(config: ExportConfig): Promise<Buffer> {
    const data = await this.fetchData(config);

    switch (config.format) {
      case 'csv':
        return this.generateCSV(data, config);
      case 'excel':
        return this.generateExcel(data, config);
      case 'pdf':
        return this.generatePDF(data, config);
      default:
        throw new Error(`Unsupported format: ${config.format}`);
    }
  }

  private async fetchData(config: ExportConfig): Promise<Record<string, unknown>[]> {
    const query = this.buildQuery(config);
    return await this.clickHouse.query(query);
  }

  private buildQuery(config: ExportConfig): string {
    const columns = config.columns.map(c =>
      c.aggregation
        ? `${c.aggregation}(${c.field}) as ${c.label}`
        : `${c.field} as ${c.label}`
    ).join(', ');

    const whereClause = this.buildWhereClause(config.filters);

    return `
      SELECT ${columns}
      FROM inbox_events_local
      WHERE ${whereClause}
      GROUP BY ${config.aggregation || 'trip_id'}
    `;
  }

  private generateCSV(data: Record<string, unknown>[], config: ExportConfig): Buffer {
    const headers = config.columns.map(c => c.label);
    const rows = data.map(row =>
      headers.map(h => String(row[h] || ''))
    );

    const csv = [
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n');

    return Buffer.from(csv);
  }

  private async generateExcel(data: Record<string, unknown>[], config: ExportConfig): Promise<Buffer> {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Metrics');

    // Headers
    worksheet.columns = config.columns.map(c => ({
      header: c.label,
      key: c.label,
    }));

    // Data
    data.forEach(row => worksheet.addRow(row));

    // Summary stats
    if (config.includeCharts) {
      this.addSummarySheet(workbook, data);
    }

    const buffer = await workbook.xlsx.writeBuffer();
    return Buffer.from(buffer);
  }

  private async generatePDF(data: Record<string, unknown>[], config: ExportConfig): Promise<Buffer> {
    const doc = new PDFDocument();

    // Title
    doc.fontSize(18).text('Inbox Metrics Report', { align: 'center' });
    doc.moveDown();
    doc.fontSize(12).text(
      `${config.dateRange.start.toDateString()} - ${config.dateRange.end.toDateString()}`
    );
    doc.moveDown();

    // Table
    const table = {
      headers: config.columns.map(c => c.label),
      rows: data.map(row =>
        config.columns.map(c => String(row[c.label] || ''))
      ),
    };

    this.drawTable(doc, table);

    // Charts
    if (config.includeCharts) {
      const charts = await this.generateCharts(data);
      for (const chart of charts) {
        doc.addPage();
        doc.image(chart, { fit: [500, 300] });
      }
    }

    const chunks: Buffer[] = [];
    doc.on('data', chunk => chunks.push(chunk));
    doc.end();

    await new Promise(resolve => doc.on('end', resolve));

    return Buffer.concat(chunks);
  }
}
```

### Scheduled Reports

```typescript
// reporting/scheduler.ts
interface ScheduledReport {
  id: string;
  name: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  recipients: string[];
  config: ExportConfig;
  timezone: string;
}

class ReportScheduler {
  private scheduledReports: Map<string, ScheduledReport>;

  async scheduleReport(report: ScheduledReport): Promise<void> {
    this.scheduledReports.set(report.id, report);

    // Calculate next run time
    const nextRun = this.calculateNextRun(report);

    // Schedule with background job system
    await this.jobScheduler.schedule(report.id, {
      runAt: nextRun,
      handler: () => this.executeReport(report),
    });
  }

  private calculateNextRun(report: ScheduledReport): Date {
    const now = new Date();
    const tz = report.timezone;

    switch (report.frequency) {
      case 'daily':
        return this.nextTimeOfDay(now, 9, tz); // 9 AM
      case 'weekly':
        return this.nextDayOfWeek(now, 1, 9, tz); // Monday 9 AM
      case 'monthly':
        return this.nextDayOfMonth(now, 1, 9, tz); // 1st of month 9 AM
    }
  }

  private async executeReport(report: ScheduledReport): Promise<void> {
    // Update date range for current report
    const config = {
      ...report.config,
      dateRange: this.getDateRangeForReport(report.frequency),
    };

    // Generate export
    const export = await this.exportGenerator.generateExport(config);

    // Send to recipients
    for (const recipient of report.recipients) {
      await this.emailService.send({
        to: recipient,
        subject: `${report.name} - ${new Date().toLocaleDateString()}`,
        attachments: [{
          filename: `${report.name}.${config.format}`,
          content: export,
        }],
      });
    }

    // Schedule next run
    await this.scheduleReport(report);
  }
}
```

---

**Next:** [INBOX_04_PERSONALIZATION_DEEP_DIVE](./INBOX_04_PERSONALIZATION_DEEP_DIVE.md) — Custom views, preferences, and agent personalization
