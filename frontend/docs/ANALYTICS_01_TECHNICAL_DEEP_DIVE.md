# Analytics Dashboard 01: Technical Deep Dive

> Complete guide to analytics data architecture, aggregation pipeline, and caching

---

## Document Overview

**Series:** Analytics Dashboard Deep Dive (Document 1 of 4)
**Focus:** Technical Architecture — Data pipeline, storage, aggregation, caching
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Analytics Architecture](#analytics-architecture)
3. [Data Storage Strategy](#data-storage-strategy)
4. [Aggregation Pipeline](#aggregation-pipeline)
5. [Query Layer](#query-layer)
6. [Caching Strategy](#caching-strategy)
7. [Real-Time Streaming](#real-time-streaming)
8. [Implementation Reference](#implementation-reference)

---

## Executive Summary

The Analytics Dashboard provides business intelligence through a dedicated analytics pipeline using ClickHouse for columnar storage, materialized views for pre-aggregation, Redis caching for fast response times, and WebSocket streaming for real-time updates.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Fast Queries** | Sub-second response on billions of events |
| **Real-Time Updates** | Live dashboard updates via WebSocket |
| **Role-Based Views** | Different KPIs for Owner, Admin, Agent |
| **Historical Analysis** | Trend analysis over customizable time ranges |
| **Drill-Down** | From aggregate to detailed transaction level |
| **Smart Caching** | Materialized views + Redis for hot data |

---

## Analytics Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANALYTICS ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        DATA SOURCES                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  PostgreSQL  │  │  Timeline    │  │   Comm Hub   │              │   │
│  │  │  (Primary)   │  │   Events     │  │    Events    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    INGESTION LAYER                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  CDC (Change Data Capture)                                      │ │   │
│  │  │  - Debezium for PostgreSQL                                      │ │   │
│  │  │  - Event streaming via Kafka                                    │ │   │
│  │  │  - Topic: analytics.events                                      │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ANALYTICS STORAGE                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    ClickHouse                                   │ │   │
│  │  │                                                                  │ │   │
│  │  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │ │   │
│  │  │  │ events_raw     │  │ events_daily   │  │ aggregates     │    │ │   │
│  │  │  │ (partitioned)  │  │ (materialized) │  │ (pre-computed) │    │ │   │
│  │  │  └────────────────┘  └────────────────┘  └────────────────┘    │ │   │
│  │  │                                                                  │ │   │
│  │  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │ │   │
│  │  │  │ funnels        │  │ cohorts        │  │ trends         │    │ │   │
│  │  │  └────────────────┘  └────────────────┘  └────────────────┘    │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      QUERY LAYER                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  AnalyticsQueryService                                          │ │   │
│  │  │  - Route to appropriate table/view                              │ │   │
│  │  │  - Apply time range filters                                     │ │   │
│  │  │  - Cache management                                             │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      CACHE LAYER                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  Redis                                                           │ │   │
│  │  │  - Query result cache (5 min TTL)                               │ │   │
│  │  │  - Dashboard state cache                                         │ │   │
│  │  │  - Real-time subscription registry                              │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      API LAYER                                       │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │ /api/analytics │  │ /api/metrics   │  │ /api/funnels   │         │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    REAL-TIME LAYER                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  WebSocket Server                                                │ │   │
│  │  │  - Dashboard subscriptions                                       │ │   │
│  │  │  - Live metric updates                                           │ │   │
│  │  │  - Alert notifications                                           │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND                                         │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │ AnalyticsPanel │  │ ChartLibrary   │  │ RealtimeClient │         │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ANALYTICS DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. EVENT PRODUCTION                                                       │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  User Action → Service → PostgreSQL Transaction                  │   │
│     │                                                                  │   │
│     │  Examples:                                                       │   │
│     │  - Booking created → bookings INSERT                             │   │
│     │  - Message sent → communications INSERT                          │   │
│     │  - Quote generated → quotes INSERT                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                              │                                             │
│                              ▼                                             │
│  2. CHANGE DATA CAPTURE                                                    │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Debezium reads WAL → Kafka Topic: analytics.events             │   │
│     │                                                                  │   │
│     │  Event Format:                                                   │   │
│     │  {                                                               │   │
│     │    "type": "booking.created",                                    │   │
│     │    "timestamp": "2026-04-25T10:30:00Z",                          │   │
│     │    "agency_id": "xxx",                                           │   │
│     │    "data": { ... }                                               │   │
│     │  }                                                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                              │                                             │
│                              ▼                                             │
│  3. CLICKHOUSE INGESTION                                                    │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Kafka Consumer → ClickHouse INSERT (batch every 10s)           │   │
│     │                                                                  │   │
│     │  - Deduplication by event_id                                    │   │
│     │  - Partition by date                                            │   │
│     │  - Order by timestamp                                           │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                              │                                             │
│                              ▼                                             │
│  4. MATERIALIZED VIEW REFRESH                                              │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Automatic on INSERT → Pre-aggregated tables updated            │   │
│     │                                                                  │   │
│     │  - events_daily: Summarized by day                              │   │
│     │  - aggregates: Pre-computed KPIs                                │   │
│     │  - funnels: Conversion metrics                                  │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                              │                                             │
│                              ▼                                             │
│  5. CACHE INVALIDATION                                                     │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Redis pub/sub → WebSocket broadcast                            │   │
│     │                                                                  │   │
│     │  - Invalidate affected query caches                             │   │
│     │  - Push update to subscribed dashboards                         │   │
│     │  - Evaluate and trigger alerts                                  │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                              │                                             │
│                              ▼                                             │
│  6. QUERY EXECUTION                                                        │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  API Request → Check Cache → ClickHouse Query → Response       │   │
│     │                                                                  │   │
│     │  Path A: Cache hit → Return immediately (<10ms)                 │   │
│     │  Path B: Cache miss → Query ClickHouse (100-500ms) → Cache      │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Storage Strategy

### ClickHouse Schema Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CLICKHOUSE TABLE STRUCTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  events_raw (Raw Event Storage)                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  CREATE TABLE events_raw (                                      ││   │
│  │  │    event_id        UUID,                                       ││   │
│  │  │    event_type      LowCardinality(String),  -- booking.created  ││   │
│  │  │    timestamp       DateTime,                                   ││   │
│  │  │    agency_id       UUID,                                       ││   │
│  │  │    user_id         UUID,                                       ││   │
│  │  │    trip_id         UUID,                                       ││   │
│  │  │    customer_id     UUID,                                       ││   │
│  │  │    -- Event-specific data (JSON)                               ││   │
│  │  │    properties      String,                                     ││   │
│  │  │    -- Metrics                                                            ││   │
│  │  │    amount          Decimal(18,2),                               ││   │
│  │  │    margin          Decimal(18,2),                               ││   │
│  │  │    -- Metadata                                                          ││   │
│  │  │    created_at      DateTime DEFAULT now()                       ││   │
│  │  │  )                                                                  ││   │
│  │  │  ENGINE = MergeTree()                                               ││   │
│  │  │  PARTITION BY toYYYYMM(timestamp)                                  ││   │
│  │  │  ORDER BY (agency_id, event_type, timestamp)                        ││   │
│  │  │  TTL timestamp + INTERVAL 2 YEAR DELETE                             ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  events_daily (Daily Aggregates - Materialized View)                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  CREATE MATERIALIZED VIEW events_daily                           ││   │
│  │  │  ENGINE = SummingMergeTree()                                     ││   │
│  │  │  PARTITION BY toYYYYMM(date)                                     ││   │
│  │  │  ORDER BY (agency_id, event_type, date)                          ││   │
│  │  │  AS SELECT                                                        ││   │
│  │  │    toDate(timestamp) as date,                                    ││   │
│  │  │    agency_id,                                                    ││   │
│  │  │    event_type,                                                   ││   │
│  │  │    count() as event_count,                                      ││   │
│  │  │    sum(amount) as total_amount,                                 ││   │
│  │  │    sum(margin) as total_margin,                                 ││   │
│  │  │    avg(amount) as avg_amount                                    ││   │
│  │  │  FROM events_raw                                                  ││   │
│  │  │  GROUP BY agency_id, event_type, date                            ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  aggregates (Pre-computed KPIs)                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  CREATE TABLE aggregates (                                       ││   │
│  │  │    agency_id        UUID,                                       ││   │
│  │  │    period           Enum('hour', 'day', 'week', 'month'),       ││   │
│  │  │    period_start     DateTime,                                   ││   │
│  │  │    -- Booking Metrics                                                    ││   │
│  │  │    bookings_created Int32,                                      ││   │
│  │  │    bookings_confirmed Int32,                                   ││   │
│  │  │    bookings_cancelled Int32,                                   ││   │
│  │  │    -- Revenue Metrics                                                     ││   │
│  │  │    revenue_gross    Decimal(18,2),                              ││   │
│  │  │    revenue_net      Decimal(18,2),                              ││   │
│  │  │    margin_total     Decimal(18,2),                              ││   │
│  │  │    margin_pct       Decimal(5,2),                               ││   │
│  │  │    -- Customer Metrics                                                 ││   │
│  │  │    customers_new    Int32,                                      ││   │
│  │  │    customers_returning Int32,                                  ││   │
│  │  │    -- Communication Metrics                                            ││   │
│  │  │    messages_sent    Int32,                                      ││   │
│  │  │    response_time_avg UInt32,  -- seconds                        ││   │
│  │  │    -- Agent Performance                                                ││   │
│  │  │    agent_id         UUID,                                       ││   │
│  │  │    trips_assigned   Int32,                                      ││   │
│  │  │    trips_completed  Int32                                       ││   │
│  │  │  )                                                                  ││   │
│  │  │  ENGINE = SummingMergeTree()                                       ││   │
│  │  │  PARTITION BY toYYYYMM(period_start)                              ││   │
│  │  │  ORDER BY (agency_id, period, period_start, agent_id)              ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Retention Tiers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA RETENTION POLICY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HOT DATA (SSD) - Recent, frequently accessed                        │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - events_raw: Last 30 days                                     ││   │
│  │  │  - aggregates: Hourly for last 7 days, Daily for last 90 days   ││   │
│  │  │  - All materialized views fully up to date                      ││   │
│  │  │  - Redis cache: Last 5 minutes of queries                       ││   │
│  │  │                                                                  ││   │
│  │  │  Storage: Hot partition on SSD                                  ││   │
│  │  │  Query Performance: <100ms                                      ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WARM DATA (HDD) - Historical, occasionally accessed                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - events_raw: 31-365 days                                      ││   │
│  │  │  - aggregates: Daily for 1 year, Weekly for 2 years             ││   │
│  │  │  - Compressed partitions                                         ││   │
│  │  │                                                                  ││   │
│  │  │  Storage: Cold partition on HDD                                  ││   │
│  │  │  Query Performance: 100-500ms                                    ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COLD DATA (S3) - Archive, rarely accessed                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - events_raw: 1-7 years (S3 with ClickHouse S3 integration)    ││   │
│  │  │  - aggregates: Monthly aggregates for 7 years                   ││   │
│  │  │  - Highly compressed                                            ││   │
│  │  │                                                                  ││   │
│  │  │  Storage: S3 Glacier                                             ││   │
│  │  │  Query Performance: 1-5s (requires restore)                      ││   │
│  │  │  Cost: ~90% lower than hot storage                              ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DELETED - Beyond retention                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - events_raw: >7 years automatically deleted                   ││   │
│  │  │  - Aggregates: >7 years retained for legal compliance          ││   │
│  │  │  - Audit logs: Permanent retention                              ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Event Type Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT TYPE TAXONOMY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BOOKING_EVENTS                                                             │
│  ├── booking.created          (New booking created)                         │
│  ├── booking.confirmed        (Booking confirmed with supplier)             │
│  ├── booking.cancelled        (Booking cancelled)                          │
│  ├── booking.modified         (Booking details changed)                    │
│  └── booking.paid             (Payment received)                           │
│                                                                             │
│  TRIP_EVENTS                                                                 │
│  ├── trip.created             (New trip/inquiry)                            │
│  ├── trip.assigned            (Trip assigned to agent)                     │
│  ├── trip.status_changed      (Trip status updated)                        │
│  ├── trip.quote_generated     (Quote created)                              │
│  └── trip.completed           (Trip marked complete)                       │
│                                                                             │
│  COMMUNICATION_EVENTS                                                         │
│  ├── message.sent             (Message sent to customer)                   │
│  ├── message.received         (Message received from customer)             │
│  ├── message.opened           (Customer opened message)                    │
│  ├── message.clicked          (Customer clicked link)                      │
│  └── email.bounced            (Email bounced)                              │
│                                                                             │
│  CUSTOMER_EVENTS                                                              │
│  ├── customer.created         (New customer added)                         │
│  ├── customer.returned        (Repeat customer)                            │
│  └── customer.segment_changed (Customer segment updated)                   │
│                                                                             │
│  DOCUMENT_EVENTS                                                              │
│  ├── document.generated       (Document created)                           │
│  ├── document.delivered       (Document sent to customer)                  │
│  ├── document.viewed          (Customer viewed document)                   │
│  └── document.downloaded      (Customer downloaded document)               │
│                                                                             │
│  FINANCIAL_EVENTS                                                              │
│  ├── payment.initiated        (Payment started)                            │
│  ├── payment.completed        (Payment successful)                         │
│  ├── payment.failed           (Payment failed)                             │
│  ├── payment.refunded         (Refund processed)                           │
│  └── invoice.generated        (Invoice created)                            │
│                                                                             │
│  AGENT_EVENTS                                                                 │
│  ├── agent.login              (Agent logged in)                            │
│  ├── agent.logout             (Agent logged out)                           │
│  ├── agent.action             (Agent performed action)                     │
│  └── agent.performance        (Performance metric updated)                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Aggregation Pipeline

### Aggregation Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AGGREGATION PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAW EVENTS (events_raw)                                                    │
│       │                                                                     │
│       │  Stream: Every event                                               │
│       │  Latency: <1 second                                               │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REAL-TIME AGGREGATION (ClickHouse)                                  │   │
│  │  - 5-minute rolling windows                                         │   │
│  │  - Updated on INSERT                                                │   │
│  │  - Used for live dashboards                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HOURLY AGGREGATES                                                  │   │
│  │  - Sum/Count/Avg by agency, event_type, hour                       │   │
│  │  - Materialized view refresh: Every 5 minutes                       │   │
│  │  - Retention: 30 days                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DAILY AGGREGATES                                                   │   │
│  │  - Sum/Count/Avg by agency, event_type, date                       │   │
│  │  - Materialized view refresh: Every hour                            │   │
│  │  - Retention: 1 year                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WEEKLY AGGREGATES                                                  │   │
│  │  - Sum/Count/Avg by agency, event_type, week                       │   │
│  │  - Computed from daily aggregates                                  │   │
│  │  - Refresh: Daily at 2 AM                                          │   │
│  │  - Retention: 2 years                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  MONTHLY AGGREGATES                                                 │   │
│  │  - Sum/Count/Avg by agency, event_type, month                      │   │
│  │  - Computed from weekly aggregates                                 │   │
│  │  - Refresh: Weekly on Sunday                                       │   │
│  │  - Retention: 7 years                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Materialized View Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MATERIALIZED VIEWS STRATEGY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VIEW NAME              REFRESH STRATEGY        USE CASE                    │
│  ──────────────────     ──────────────────     ──────────────────────     │
│  mv_events_5min         On INSERT              Live dashboard numbers      │
│  mv_events_hourly       Every 5 min            Hourly performance          │
│  mv_events_daily        Every hour             Daily reports               │
│  mv_bookings_funnel     Every hour             Conversion tracking         │
│  mv_agent_metrics       Every hour             Agent performance           │
│  mv_customer_cohorts    Daily (2 AM)           Cohort analysis             │
│  mv_revenue_trends      Daily (3 AM)           Revenue charts              │
│  mv_seasonal_patterns   Weekly (Sunday)        Seasonal forecasting        │
│                                                                             │
│  Refresh Scheduling:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  On INSERT (Immediate)                                         ││   │
│  │  │  - mv_events_5min (real-time counters)                         ││   │
│  │  │  - mv_alerts (alert evaluation)                                ││   │
│  │  │                                                                  ││   │
│  │  │  Trigger: New event in events_raw                              ││   │
│  │  │  Impact: O(1) incremental update                                ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Cron: Every 5 minutes                                        ││   │
│  │  │  - mv_events_hourly (catch-up)                                 ││   │
│  │  │  - mv_dashboard_metrics                                        ││   │
│  │  │                                                                  ││   │
│  │  │  Max lag: 5 minutes                                            ││   │
│  │  │  Impact: Incremental merge                                     ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Cron: Every hour (at :00)                                     ││   │
│  │  │  - mv_events_daily                                            ││   │
│  │  │  - mv_bookings_funnel                                         ││   │
│  │  │  - mv_agent_metrics                                           ││   │
│  │  │                                                                  ││   │
│  │  │  Max lag: 1 hour                                              ││   │
│  │  │  Impact: Batch from hourly                                     ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Cron: Daily (2 AM)                                           ││   │
│  │  │  - mv_customer_cohorts                                        ││   │
│  │  │  - mv_revenue_trends                                          ││   │
│  │  │                                                                  ││   │
│  │  │  Max lag: 24 hours                                            ││   │
│  │  │  Impact: Batch from daily                                     ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Cron: Weekly (Sunday 3 AM)                                    ││   │
│  │  │  - mv_seasonal_patterns                                       ││   │
│  │  │                                                                  ││   │
│  │  │  Max lag: 7 days                                              ││   │
│  │  │  Impact: Batch from weekly/monthly                            ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Query Layer

### Query Router

```typescript
// services/analytics-query.service.ts
import { ClickHouseClient } from '@clickhouse/client';

export class AnalyticsQueryService {
  private clickhouse: ClickHouseClient;
  private cache: Redis;

  async getDashboardMetrics(input: {
    agencyId: string;
    period: 'hour' | 'day' | 'week' | 'month';
    startDate: Date;
    endDate: Date;
  }): Promise<DashboardMetrics> {
    // Check cache first
    const cacheKey = this.getCacheKey('dashboard', input);
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // Determine optimal data source
    const dataSource = this.selectDataSource(input);
    let metrics: DashboardMetrics;

    switch (dataSource) {
      case 'realtime':
        metrics = await this.queryRealtime(input);
        break;
      case 'hourly':
        metrics = await this.queryHourly(input);
        break;
      case 'daily':
        metrics = await this.queryDaily(input);
        break;
      case 'raw':
        metrics = await this.queryRaw(input);
        break;
    }

    // Cache for 5 minutes
    await this.cache.setex(cacheKey, 300, JSON.stringify(metrics));

    return metrics;
  }

  private selectDataSource(input: {
    agencyId: string;
    period: string;
    startDate: Date;
    endDate: Date;
  }): 'realtime' | 'hourly' | 'daily' | 'raw' {
    const daysDiff = (input.endDate.getTime() - input.startDate.getTime()) / (1000 * 60 * 60 * 24);

    // Last 24 hours: Use realtime/hourly for accuracy
    if (daysDiff <= 1) {
      return 'hourly';
    }

    // Last 30 days: Use daily aggregates
    if (daysDiff <= 30) {
      return 'daily';
    }

    // Older: Use daily aggregates (maybe raw if needed)
    return 'daily';
  }

  private async queryHourly(input: {
    agencyId: string;
    startDate: Date;
    endDate: Date;
  }): Promise<DashboardMetrics> {
    const query = `
      SELECT
        toStartOfHour(timestamp) as hour,
        event_type,
        count() as count,
        sum(amount) as total_amount,
        sum(margin) as total_margin
      FROM events_hourly
      WHERE agency_id = {agencyId:UUID}
        AND timestamp >= {startDate:DateTime}
        AND timestamp <= {endDate:DateTime}
      GROUP BY hour, event_type
      ORDER BY hour
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId: input.agencyId,
        startDate: input.startDate.toISOString(),
        endDate: input.endDate.toISOString(),
      },
    });

    return this.transformToDashboardMetrics(result.data);
  }

  private async queryDaily(input: {
    agencyId: string;
    startDate: Date;
    endDate: Date;
  }): Promise<DashboardMetrics> {
    const query = `
      SELECT
        date,
        event_type,
        sum(event_count) as count,
        sum(total_amount) as total_amount,
        sum(total_margin) as total_margin
      FROM events_daily
      WHERE agency_id = {agencyId:UUID}
        AND date >= {startDate:Date}
        AND date <= {endDate:Date}
      GROUP BY date, event_type
      ORDER BY date
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId: input.agencyId,
        startDate: input.startDate.toISOString().split('T')[0],
        endDate: input.endDate.toISOString().split('T')[0],
      },
    });

    return this.transformToDashboardMetrics(result.data);
  }

  async getFunnelMetrics(input: {
    agencyId: string;
    funnel: 'booking' | 'quote' | 'customer';
    startDate: Date;
    endDate: Date;
  }): Promise<FunnelMetrics> {
    // Query pre-computed funnel
    const query = `
      SELECT
        step,
        count,
        conversion_rate,
        avg_time_to_next
      FROM mv_bookings_funnel
      WHERE agency_id = {agencyId:UUID}
        AND date >= {startDate:Date}
        AND date <= {endDate:Date}
        AND funnel_type = {funnel:String}
      ORDER BY step_order
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId: input.agencyId,
        startDate: input.startDate.toISOString().split('T')[0],
        endDate: input.endDate.toISOString().split('T')[0],
        funnel: input.funnel,
      },
    });

    return {
      steps: result.data,
      overall_conversion: result.data[result.data.length - 1]?.cumulative_rate || 0,
    };
  }

  async getAgentPerformance(input: {
    agencyId: string;
    startDate: Date;
    endDate: Date;
  }): Promise<AgentPerformance[]> {
    const query = `
      SELECT
        agent_id,
        agent_name,
        trips_assigned,
        trips_completed,
        completion_rate,
        avg_response_time,
        total_revenue,
        total_margin,
        customer_satisfaction
      FROM mv_agent_metrics
      WHERE agency_id = {agencyId:UUID}
        AND period_start >= {startDate:Date}
        AND period_start <= {endDate:Date}
      ORDER BY total_revenue DESC
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId: input.agencyId,
        startDate: input.startDate.toISOString().split('T')[0],
        endDate: input.endDate.toISOString().split('T')[0],
      },
    });

    return result.data;
  }

  private getCacheKey(type: string, input: any): string {
    const hash = crypto
      .createHash('md5')
      .update(JSON.stringify(input))
      .digest('hex');
    return `analytics:${type}:${hash}`;
  }

  private transformToDashboardMetrics(data: any[]): DashboardMetrics {
    // Transform raw ClickHouse results to typed metrics
    return {
      totalRevenue: data.reduce((sum, row) => sum + (row.total_amount || 0), 0),
      totalMargin: data.reduce((sum, row) => sum + (row.total_margin || 0), 0),
      totalBookings: data.reduce((sum, row) => sum + (row.count || 0), 0),
      byEvent: data.map(row => ({
        type: row.event_type,
        count: row.count,
        amount: row.total_amount,
        margin: row.total_margin,
      })),
    };
  }
}
```

### Query Optimization Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      QUERY OPTIMIZATION PATTERNS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. PARTITION PRUNING                                                      │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Always filter on partition key in WHERE clause                  │   │
│     │                                                                  │   │
│     │  ✅ GOOD: SELECT * FROM events WHERE date >= '2026-04-01'        │   │
│     │  ❌ BAD:  SELECT * FROM events WHERE timestamp >= '2026-04-01'   │   │
│     │                                                                  │   │
│     │  ClickHouse will only scan relevant partitions                  │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. PRE-AGGREGATION                                                         │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Use materialized views for common aggregations                 │   │
│     │                                                                  │   │
│     │  Instead of:                                                    │   │
│     │    SELECT date, COUNT(*) FROM events GROUP BY date              │   │
│     │                                                                  │   │
│     │  Use:                                                           │   │
│     │    SELECT * FROM events_daily                                   │   │
│     │                                                                  │   │
│     │  Performance: 100x faster                                        │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. ASYNC INSERTION                                                         │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Batch inserts for better throughput                            │   │
│     │                                                                  │   │
│     │  INSERT INTO events_raw SETTINGS wait_for_async_insert = 0      │   │
│     │                                                                  │   │
│     │  Returns immediately, background processing                    │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. LIMIT RESULTS                                                           │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  Always use LIMIT for preview queries                           │   │
│     │                                                                  │   │
│     │  SELECT * FROM events WHERE ... LIMIT 1000                      │   │
│     │                                                                  │   │
│     │  Prevents runaway queries on large datasets                     │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. CACHE STRATEGY                                                          │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  - Cache hot queries (Redis, 5 min TTL)                         │   │
│     │  - Invalidate on new data                                       │   │
│     │  - Use query results cache for identical requests               │   │
│     │                                                                  │   │
│     │  Cache hit rate target: >80%                                    │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Caching Strategy

### Cache Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CACHE HIERARCHY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  L1: QUERY RESULTS CACHE (Redis)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Key: analytics:query:{hash}                                        │   │
│  │  TTL: 5 minutes                                                     │   │
│  │  Size: ~100MB                                                        │   │
│  │                                                                      │   │
│  │  Stores: Complete query results for dashboard widgets               │   │
│  │  Invalidated: On new events (pub/sub)                              │   │
│  │  Hit Rate: ~75%                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  L2: DASHBOARD STATE CACHE (Redis)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Key: analytics:dashboard:{agencyId}:{userId}                      │   │
│  │  TTL: 30 minutes                                                    │   │
│  │  Size: ~50MB                                                         │   │
│  │                                                                      │   │
│  │  Stores: Complete dashboard configuration + last query results     │   │
│  │  Invalidated: User manually refreshes                              │   │
│  │  Hit Rate: ~90%                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  L3: MATERIALIZED VIEWS (ClickHouse)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Tables: events_daily, events_hourly, mv_*                         │   │
│  │  TTL: Data retention policy                                        │   │
│  │  Size: GB to TB                                                     │   │
│  │                                                                      │   │
│  │  Stores: Pre-aggregated data for common queries                    │   │
│  │  Refreshed: Scheduled or on INSERT                                 │   │
│  │  Speed: 10-100x faster than raw queries                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Invalidation Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CACHE INVALIDATION STRATEGY                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EVENT FLOW → INVALIDATION                                                  │
│                                                                             │
│  1. NEW EVENT ARRIVES                                                       │
│     │                                                                       │
│     ▼                                                                       │
│  2. PUBLISH TO REDIS                                                        │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  PUBLISH analytics:invalidate:{agencyId}                        │   │
│     │  {                                                               │   │
│     │    "event_type": "booking.created",                              │   │
│     │    "timestamp": "2026-04-25T10:30:00Z",                          │   │
│     │    "affected_queries": [                                         │   │
│     │      "dashboard:revenue",                                         │   │
│     │      "dashboard:bookings",                                        │   │
│     │      "funnel:booking"                                             │   │
│     │    ]                                                              │   │
│     │  }                                                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│     │                                                                       │
│     ▼                                                                       │
│  3. SUBSCRIBERS (API Servers)                                               │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  - Invalidate affected query caches                              │   │
│     │  - Notify WebSocket subscribers                                  │   │
│     │  - Pre-warm critical caches                                      │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│     │                                                                       │
│     ▼                                                                       │
│  4. NEXT REQUEST                                                           │
│     ┌─────────────────────────────────────────────────────────────────┐   │
│     │  - Cache miss                                                   │   │
│     │  - Query ClickHouse                                            │   │
│     │  - Populate cache                                              │   │
│     │  - Return result                                               │   │
│     └─────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INVALIDATION RULES:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  - booking.* → Invalidate revenue, bookings, funnel caches         │   │
│  │  - message.* → Invalidate communication, response time caches      │   │
│  │  - payment.* → Invalidate revenue, margin caches                   │   │
│  │  - trip.* → Invalidate trips, status caches                        │   │
│  │  - Hourly → Invalidate all dashboard caches for agency             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Real-Time Streaming

### WebSocket Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEBSOCKET STREAMING                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CLIENT                        SERVER                    DATA SOURCE         │
│    │                              │                         │               │
│    │  1. CONNECT                  │                         │               │
│    ├─────────────────────────────▶│                         │               │
│    │  ws://api/analytics/stream   │                         │               │
│    │                              │                         │               │
│    │                              │  2. AUTHENTICATE         │               │
│    │                              ├─────────────────────────▶│               │
│    │                              │  Validate JWT            │               │
│    │                              │◀─────────────────────────┤               │
│    │                              │  User: {id, agencyId}    │               │
│    │                              │                         │               │
│    │  3. SUBSCRIBE                 │                         │               │
│    │◀─────────────────────────────┤                         │               │
│    │  {                           │                         │               │
│    │    "type": "subscribe",      │                         │               │
│    │    "channels": [             │                         │               │
│    │      "dashboard:revenue",    │                         │               │
│    │      "dashboard:bookings",   │                         │               │
│    │      "alert:all"             │                         │               │
│    │    ]                         │                         │               │
│    │  }                           │                         │               │
│    ├─────────────────────────────▶│                         │               │
│    │                              │                         │               │
│    │                              │  4. SUBSCRIBE TO REDIS   │               │
│    │                              ├─────────────────────────▶│               │
│    │                              │  SUBSCRIBE analytics:*   │               │
│    │                              │                         │               │
│    │                              │                         │               │
│    │                              │◀─────────────────────────┤               │
│    │  5. CONFIRM                  │  6. NEW EVENT            │               │
│    │◀─────────────────────────────┤  booking.created         │               │
│    │  {"type": "subscribed",      │                         │               │
│    │   "channels": [...]}         │  PUBLISH analytics:*     │               │
│    │                              │◀─────────────────────────┤               │
│    │                              │  {event data}            │               │
│    │  7. LIVE UPDATES             │                         │               │
│    │◀─────────────────────────────┤                         │               │
│    │  {                           │                         │               │
│    │    "type": "update",         │                         │               │
│    │    "channel": "revenue",     │                         │               │
│    │    "data": {                 │                         │               │
│    │      "revenue": 125000,      │                         │               │
│    │      "change": +5000,        │                         │               │
│    │      "timestamp": "..."      │                         │               │
│    │    }                         │                         │               │
│    │  }                           │                         │               │
│    │                              │                         │               │
│    │  ... (continuous updates)    │                         │               │
│    │                              │                         │               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Streaming Service

```typescript
// services/analytics-streaming.service.ts
import { Redis } from 'ioredis';
import { WebSocketServer } from 'ws';
import jwt from 'jsonwebtoken';

export class AnalyticsStreamingService {
  private redis: Redis;
  private wss: WebSocketServer;
  private subscriptions = new Map<string, Set<WebSocket>>();

  constructor() {
    this.redis = new Redis(process.env.REDIS_URL);
    this.wss = new WebSocketServer({ port: 8080, path: '/analytics/stream' });

    this.setupWebSocketServer();
    this.setupRedisSubscriptions();
  }

  private setupWebSocketServer() {
    this.wss.on('connection', (ws, req) => {
      // Authenticate
      const token = new URL(req.url, 'http://localhost').searchParams.get('token');
      let user: any;

      try {
        user = jwt.verify(token, process.env.JWT_SECRET!);
      } catch {
        ws.close(1008, 'Invalid token');
        return;
      }

      // Send initial state
      ws.send(JSON.stringify({
        type: 'connected',
        data: {
          agencyId: user.agencyId,
          channels: this.getAvailableChannels(user),
        },
      }));

      // Handle messages
      ws.on('message', async (data) => {
        try {
          const message = JSON.parse(data.toString());

          switch (message.type) {
            case 'subscribe':
              await this.handleSubscribe(ws, user, message.channels);
              break;
            case 'unsubscribe':
              await this.handleUnsubscribe(ws, message.channels);
              break;
            case 'ping':
              ws.send(JSON.stringify({ type: 'pong' }));
              break;
          }
        } catch (error) {
          ws.send(JSON.stringify({ type: 'error', message: error.message }));
        }
      });

      // Handle disconnect
      ws.on('close', () => {
        this.handleDisconnect(ws, user);
      });
    });
  }

  private setupRedisSubscriptions() {
    const subscriber = this.redis.duplicate();

    subscriber.psubscribe('analytics:*', (err) => {
      if (err) console.error('Redis subscription error:', err);
    });

    subscriber.on('pmessage', (pattern, channel, message) => {
      this.handleRedisMessage(channel, message);
    });
  }

  private async handleSubscribe(
    ws: WebSocket,
    user: any,
    channels: string[]
  ) {
    for (const channel of channels) {
      // Validate user has access to this channel
      if (!this.canAccessChannel(user, channel)) {
        continue;
      }

      // Add to subscriptions
      if (!this.subscriptions.has(channel)) {
        this.subscriptions.set(channel, new Set());
      }
      this.subscriptions.get(channel)!.add(ws);
    }

    ws.send(JSON.stringify({
      type: 'subscribed',
      channels,
    }));
  }

  private handleUnsubscribe(ws: WebSocket, channels: string[]) {
    for (const channel of channels) {
      const subscribers = this.subscriptions.get(channel);
      if (subscribers) {
        subscribers.delete(ws);
        if (subscribers.size === 0) {
          this.subscriptions.delete(channel);
        }
      }
    }

    ws.send(JSON.stringify({
      type: 'unsubscribed',
      channels,
    }));
  }

  private handleRedisMessage(channel: string, messageStr: string) {
    const message = JSON.parse(messageStr);
    const subscribers = this.subscriptions.get(channel);

    if (!subscribers || subscribers.size === 0) {
      return;
    }

    const payload = JSON.stringify({
      type: 'update',
      channel: channel.replace('analytics:', ''),
      data: message.data,
      timestamp: message.timestamp,
    });

    // Broadcast to all subscribers
    for (const ws of subscribers) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(payload);
      }
    }
  }

  private handleDisconnect(ws: WebSocket, user: any) {
    // Remove from all subscriptions
    for (const [channel, subscribers] of this.subscriptions.entries()) {
      subscribers.delete(ws);
      if (subscribers.size === 0) {
        this.subscriptions.delete(channel);
      }
    }
  }

  private canAccessChannel(user: any, channel: string): boolean {
    // Channel format: analytics:{agencyId}:{type}
    const parts = channel.split(':');
    const agencyId = parts[1];

    return user.agencyId === agencyId;
  }

  private getAvailableChannels(user: any): string[] {
    return [
      `analytics:${user.agencyId}:revenue`,
      `analytics:${user.agencyId}:bookings`,
      `analytics:${user.agencyId}:customers`,
      `analytics:${user.agencyId}:agents`,
      `analytics:${user.agencyId}:alerts`,
    ];
  }
}
```

---

## Summary

The Analytics Dashboard technical architecture provides:

- **Fast Queries**: ClickHouse columnar storage with materialized views
- **Smart Caching**: Redis multi-tier cache with intelligent invalidation
- **Real-Time Updates**: WebSocket streaming for live dashboard updates
- **Scalable Storage**: Hot/warm/cold data tiers for cost optimization
- **Efficient Pipeline**: CDC from PostgreSQL to ClickHouse via Kafka

This completes the Technical Deep Dive. The next document covers UX/UI design patterns.

---

**Related Documents:**
- [UX/UI Deep Dive](./ANALYTICS_02_UX_UI_DEEP_DIVE.md) — Dashboard design and interactions
- [Metrics Deep Dive](./ANALYTICS_03_METRICS_DEEP_DIVE.md) — KPI definitions and calculations
- [Real-Time Deep Dive](./ANALYTICS_04_REALTIME_DEEP_DIVE.md) — Streaming and monitoring

**Master Index:** [Analytics Dashboard Deep Dive Master Index](./ANALYTICS_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
