# Communication Hub — Analytics Deep Dive

> Part 4 of 4 in Communication Hub Exploration Series

---

## Document Overview

**Series:** Communication Hub
**Part:** 4 — Analytics
**Status:** Complete
**Last Updated:** 2026-04-24

---

## Table of Contents

1. [Analytics Overview](#analytics-overview)
2. [Metrics Architecture](#metrics-architecture)
3. [Core Metrics](#core-metrics)
4. [Funnels & Journeys](#funnels--journeys)
5. [Channel Performance](#channel-performance)
6. [Real-Time Monitoring](#real-time-monitoring)
7. [Reporting & Exports](#reporting--exports)
8. [Alerting & Insights](#alerting--insights)

---

## Analytics Overview

### Why Communication Analytics Matter

Communication is the lifeline of travel agency operations. Analytics provide:

- **Delivery Assurance**: Monitor message delivery rates across channels
- **Response Tracking**: Understand customer engagement patterns
- **Cost Optimization**: Identify expensive channels with low ROI
- **Template Performance**: Know which messages resonate best
- **Operational Efficiency**: Track agent productivity and response times

### Analytics Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANALYTICS DATA FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐         │
│  │  Message      │────▶│  Event         │────▶│  ClickHouse    │         │
│  │  Sent/        │     │  Streamer      │     │  Events Table  │         │
│  │  Updated      │     │                │     │                │         │
│  └────────────────┘     └────────────────┘     └────────┬───────┘         │
│                                                             │               │
│  ┌────────────────┐     ┌────────────────┐               │               │
│  │  Webhook       │────▶│  Event         │───────────────┘               │
│  │  Received      │     │  Normalizer    │                               │
│  └────────────────┘     └────────────────┘                               │
│                                                             │               │
│                                                             ▼               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        AGGREGATION LAYER                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │ 1-Minute     │  │  5-Minute    │  │  1-Hour      │               │  │
│  │  │  Rollup      │  │  Rollup      │  │  Rollup      │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                   │                                        │
│                                   ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         QUERY LAYER                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │  Dashboard   │  │  Reports     │  │  API         │               │  │
│  │  │  Queries     │  │  Queries     │  │  Queries     │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Metrics Architecture

### Event Schema (ClickHouse)

```sql
-- ClickHouse schema for message events

CREATE TABLE message_events_local ON CLUSTER '{cluster}' (
  -- Event identification
  event_id UUID DEFAULT generateUUIDv4(),
  event_time DateTime64(3) DEFAULT now64(3),
  event_date Date DEFAULT toDate(event_time),

  -- Agency context
  agency_id UUID,
  agent_id UUID,

  -- Message context
  message_id UUID,
  thread_id UUID,
  trip_id UUID,

  -- Recipient context
  recipient_type LowCardinality(String),
  recipient_id UUID,

  -- Channel context
  channel LowCardinality(String),
  direction LowCardinality(String),

  -- Event details
  event_type LowCardinality(String), -- sent, delivered, read, failed, bounced
  status LowCardinality(String),

  -- Content metrics
  content_length UInt32,
  has_attachment UInt8 DEFAULT 0,
  attachment_count UInt8 DEFAULT 0,

  -- Template usage
  template_id UUID,
  template_category LowCardinality(String),
  template_code String,

  -- Cost tracking
  cost_cents UInt32 DEFAULT 0,

  -- Timing metrics (milliseconds)
  delivery_time_ms UInt32,
  first_read_time_ms UInt32,

  -- Error tracking
  error_category LowCardinality(String),
  error_message String,

  -- Geography
  recipient_country_code FixedString(2),
  recipient_timezone String,

  -- User agent for email opens
  user_agent String,
  device_type LowCardinality(String),
  browser LowCardality(String),

  -- Metadata
  metadata String DEFAULT ''
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (agency_id, event_date, event_time, message_id)
TTL event_date + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- Distributed table
CREATE TABLE message_events AS message_events_local
ENGINE = Distributed('{cluster}', default, message_events_local, rand());

-- Materialized view for daily aggregations
CREATE MATERIALIZED VIEW message_daily_stats_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (agency_id, event_date, channel, event_type)
AS SELECT
  agency_id,
  event_date,
  channel,
  event_type,
  recipient_type,
  template_category,
  count() as message_count,
  sum(cost_cents) as total_cost_cents,
  avg(delivery_time_ms) as avg_delivery_time_ms,
  avg(content_length) as avg_content_length,
  sum(has_attachment) as attachments_count
FROM message_events_local
GROUP BY agency_id, event_date, channel, event_type, recipient_type, template_category;

-- Daily stats table
CREATE TABLE message_daily_stats (
  agency_id UUID,
  event_date Date,
  channel LowCardinality(String),
  event_type LowCardinality(String),
  recipient_type LowCardinality(String),
  template_category LowCardinality(String),
  message_count UInt64,
  total_cost_cents UInt64,
  avg_delivery_time_ms UInt32,
  avg_content_length UInt32,
  attachments_count UInt64
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (agency_id, event_date, channel, event_type);
```

### Event Publishing

```typescript
// services/analytics/event-publisher.service.ts

import { Redis } from 'ioredis';
import { ClickHouse } from 'clickhouse';

export class EventPublisherService {
  private redis: Redis;
  private clickhouse: ClickHouse;
  private eventBuffer: Map<string, any[]> = new Map();
  private bufferFlushInterval = 5000; // 5 seconds

  constructor() {
    this.redis = new Redis();
    this.clickhouse = new ClickHouse({
      url: process.env.CLICKHOUSE_HOST,
      port: parseInt(process.env.CLICKHOUSE_PORT || '8123'),
      user: process.env.CLICKHOUSE_USER,
      password: process.env.CLICKHOUSE_PASSWORD,
      database: 'analytics'
    });

    // Start buffer flush interval
    setInterval(() => this.flushBuffers(), this.bufferFlushInterval);
  }

  /**
   * Publish message event to analytics pipeline
   */
  async publishMessageEvent(event: MessageEvent): Promise<void> {
    // 1. Publish to Redis for real-time consumers
    await this.redis.publish('message:events', JSON.stringify(event));

    // 2. Add to ClickHouse buffer
    this.addToBuffer('message_events', event);

    // 3. Trigger real-time updates
    await this.updateRealtimeMetrics(event);
  }

  /**
   * Add event to buffer for batch insertion
   */
  private addToBuffer(stream: string, event: any): void {
    if (!this.eventBuffer.has(stream)) {
      this.eventBuffer.set(stream, []);
    }

    this.eventBuffer.get(stream)!.push(event);

    // Flush if buffer is too large
    if (this.eventBuffer.get(stream)!.length >= 1000) {
      this.flushBuffer(stream);
    }
  }

  /**
   * Flush buffer to ClickHouse
   */
  private async flushBuffer(stream: string): Promise<void> {
    const events = this.eventBuffer.get(stream);
    if (!events || events.length === 0) {
      return;
    }

    try {
      await this.clickhouse.insert({
        table: stream,
        values: events,
        format: 'JSONEachRow'
      });

      this.eventBuffer.set(stream, []);
    } catch (error) {
      console.error(`Failed to flush ${stream} buffer:`, error);
      // Retry with backoff
      setTimeout(() => this.flushBuffer(stream), 10000);
    }
  }

  /**
   * Flush all buffers
   */
  private async flushBuffers(): Promise<void> {
    for (const stream of this.eventBuffer.keys()) {
      await this.flushBuffer(stream);
    }
  }

  /**
   * Update real-time metrics in Redis
   */
  private async updateRealtimeMetrics(event: MessageEvent): Promise<void> {
    const today = new Date().toISOString().split('T')[0];
    const keys = [
      `metrics:${event.agencyId}:daily:${today}`,
      `metrics:${event.agencyId}:channel:${event.channel}`,
      `metrics:${event.agencyId}:template:${event.templateId}`
    ];

    const pipeline = this.redis.pipeline();

    for (const key of keys) {
      pipeline.hincrby(key, 'total', 1);
      pipeline.hincrby(key, `status:${event.eventType}`, 1);
      pipeline.hincrby(key, 'cost', event.costCents || 0);
      pipeline.expire(key, 86400 * 7); // 7 days TTL
    }

    await pipeline.exec();
  }

  /**
   * Get real-time metrics from Redis
   */
  async getRealtimeMetrics(
    agencyId: string,
    date?: Date
  ): Promise<RealtimeMetrics> {
    const targetDate = date || new Date();
    const dateStr = targetDate.toISOString().split('T')[0];
    const key = `metrics:${agencyId}:daily:${dateStr}`;

    const data = await this.redis.hgetall(key);

    return {
      date: dateStr,
      total: parseInt(data.total || '0'),
      sent: parseInt(data['status:sent'] || '0'),
      delivered: parseInt(data['status:delivered'] || '0'),
      read: parseInt(data['status:read'] || '0'),
      failed: parseInt(data['status:failed'] || '0'),
      totalCost: parseInt(data.cost || '0')
    };
  }
}

interface MessageEvent {
  eventId?: string;
  eventTime?: Date;
  agencyId: string;
  agentId?: string;
  messageId: string;
  threadId?: string;
  tripId?: string;
  recipientType: string;
  recipientId: string;
  channel: string;
  direction: string;
  eventType: 'sent' | 'delivered' | 'read' | 'failed' | 'bounced';
  status: string;
  contentLength?: number;
  hasAttachment?: boolean;
  attachmentCount?: number;
  templateId?: string;
  templateCategory?: string;
  templateCode?: string;
  costCents?: number;
  deliveryTimeMs?: number;
  firstReadTimeMs?: number;
  errorCategory?: string;
  errorMessage?: string;
  recipientCountryCode?: string;
  recipientTimezone?: string;
  userAgent?: string;
  deviceType?: string;
  browser?: string;
  metadata?: Record<string, unknown>;
}

interface RealtimeMetrics {
  date: string;
  total: number;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
  totalCost: number;
}
```

---

## Core Metrics

### KPI Definitions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COMMUNICATION KPIs                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DELIVERY METRICS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Delivery Rate    │ Delivered / Sent × 100%                         │   │
│  │                  │ Target: >95%                                    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Read Rate        │ Read / Delivered × 100%                         │   │
│  │                  │ Target: >60% (varies by channel)                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Failure Rate     │ Failed / Sent × 100%                            │   │
│  │                  │ Target: <5%                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Bounce Rate      │ Bounced / Sent × 100% (email only)              │   │
│  │                  │ Target: <2%                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TIMING METRICS                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Avg Delivery     │ Time from Sent → Delivered                      │   │
│  │  Time            │ Target: <30s (WhatsApp), <5min (Email)          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ First Read       │ Time from Delivered → First Read                │   │
│  │  Time            │ Target: <5min (WhatsApp), <1hour (Email)        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Response Time    │ Time from Sent → First Reply                    │   │
│  │                  │ Target: <1hour for urgent, <24h for normal      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ENGAGEMENT METRICS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Response Rate    │ Messages with Reply / Sent × 100%                │   │
│  │                  │ Target: >40% for outbound                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Click Rate       │ Links Clicked / Links Sent × 100%               │   │
│  │                  │ Target: >10%                                    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Forward Rate     │ Messages Forwarded / Sent × 100%                │   │
│  │                  │ Target: >5% (indicating sharing)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  COST METRICS                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Cost Per         │ Total Cost / Total Messages                     │   │
│  │  Message         │ Target: <₹0.50                                  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Cost Per         │ Total Cost / Bookings from Messages             │   │
│  │  Conversion     │ Target: <₹50                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Metrics Queries

```typescript
// services/analytics/metrics-query.service.ts

export class MetricsQueryService {
  private clickhouse: ClickHouse;

  constructor() {
    this.clickhouse = new ClickHouse({
      url: process.env.CLICKHOUSE_HOST,
      database: 'analytics'
    });
  }

  /**
   * Get delivery metrics for date range
   */
  async getDeliveryMetrics(
    agencyId: string,
    startDate: Date,
    endDate: Date
  ): Promise<DeliveryMetrics> {
    const query = `
      SELECT
        channel,
        countIf(event_type = 'sent') as sent,
        countIf(event_type = 'delivered') as delivered,
        countIf(event_type = 'read') as read,
        countIf(event_type = 'failed') as failed,
        countIf(event_type = 'bounced') as bounced,
        round(delivered / sent * 100, 2) as delivery_rate,
        round(read / delivered * 100, 2) as read_rate,
        round(failed / sent * 100, 2) as failure_rate,
        sum(cost_cents) as total_cost_cents
      FROM message_events
      WHERE agency_id = {agencyId:UUID}
        AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
        AND direction = 'outbound'
      GROUP BY channel
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      }
    });

    const data = await result.json();

    return {
      byChannel: data,
      totals: this.calculateTotals(data)
    };
  }

  /**
   * Get timing metrics
   */
  async getTimingMetrics(
    agencyId: string,
    startDate: Date,
    endDate: Date
  ): Promise<TimingMetrics> {
    const query = `
      SELECT
        channel,
        round(avg(delivery_time_ms) / 1000, 2) as avg_delivery_seconds,
        round(avg(first_read_time_ms) / 1000, 2) as avg_first_read_seconds,
        quantile(0.5)(delivery_time_ms) / 1000 as p50_delivery_seconds,
        quantile(0.95)(delivery_time_ms) / 1000 as p95_delivery_seconds,
        quantile(0.99)(delivery_time_ms) / 1000 as p99_delivery_seconds
      FROM message_events
      WHERE agency_id = {agencyId:UUID}
        AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
        AND delivery_time_ms > 0
      GROUP BY channel
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      }
    });

    const data = await result.json();

    return {
      byChannel: data,
      overall: this.calculateOverallTiming(data)
    };
  }

  /**
   * Get engagement metrics
   */
  async getEngagementMetrics(
    agencyId: string,
    startDate: Date,
    endDate: Date
  ): Promise<EngagementMetrics> {
    const query = `
      SELECT
        channel,
        template_category,
        countIf(event_type = 'sent') as sent,
        countIf(event_type = 'read') as read,
        round(read / sent * 100, 2) as read_rate,
        sum(has_attachment) as with_attachments,
        countIf(has_attachment = 1 AND event_type = 'read') as attachment_reads,
        round(countIf(has_attachment = 1 AND event_type = 'read') / sum(has_attachment) * 100, 2) as attachment_read_rate
      FROM message_events
      WHERE agency_id = {agencyId:UUID}
        AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
        AND direction = 'outbound'
      GROUP BY channel, template_category
      ORDER BY sent DESC
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      }
    });

    const data = await result.json();

    return {
      byChannelAndCategory: data,
      topCategories: this.getTopCategories(data, 5)
    };
  }

  /**
   * Get cost metrics
   */
  async getCostMetrics(
    agencyId: string,
    startDate: Date,
    endDate: Date
  ): Promise<CostMetrics> {
    const query = `
      SELECT
        channel,
        count() as message_count,
        sum(cost_cents) as total_cost_cents,
        round(sum(cost_cents) / count(), 2) as cost_per_message,
        sum(cost_cents) / 100 as total_cost_rupees
      FROM message_events
      WHERE agency_id = {agencyId:UUID}
        AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
        AND event_type = 'sent'
      GROUP BY channel
      ORDER BY total_cost_cents DESC
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      }
    });

    const data = await result.json();

    const totalCost = data.reduce((sum, row) => sum + row.total_cost_cents, 0);
    const totalMessages = data.reduce((sum, row) => sum + row.message_count, 0);

    return {
      byChannel: data,
      totalCostCents: totalCost,
      totalCostRupees: totalCost / 100,
      averageCostPerMessage: totalMessages > 0 ? totalCost / totalMessages : 0,
      mostExpensiveChannel: data[0]?.channel,
      leastExpensiveChannel: data[data.length - 1]?.channel
    };
  }

  /**
   * Get template performance
   */
  async getTemplatePerformance(
    agencyId: string,
    startDate: Date,
    endDate: Date,
    limit: number = 20
  ): Promise<TemplatePerformance[]> {
    const query = `
      SELECT
        template_id,
        template_code,
        template_category,
        channel,
        countIf(event_type = 'sent') as sent,
        countIf(event_type = 'delivered') as delivered,
        countIf(event_type = 'read') as read,
        round(delivered / sent * 100, 2) as delivery_rate,
        round(read / delivered * 100, 2) as read_rate,
        round(avg(content_length), 2) as avg_content_length,
        sum(cost_cents) as total_cost_cents
      FROM message_events
      WHERE agency_id = {agencyId:UUID}
        AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
        AND template_id IS NOT NULL
        AND direction = 'outbound'
      GROUP BY template_id, template_code, template_category, channel
      ORDER BY sent DESC
      LIMIT {limit:UInt32}
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0],
        limit
      }
    });

    return await result.json();
  }

  private calculateTotals(data: any[]): TotalMetrics {
    return data.reduce((acc, row) => ({
      sent: acc.sent + row.sent,
      delivered: acc.delivered + row.delivered,
      read: acc.read + row.read,
      failed: acc.failed + row.failed,
      bounced: acc.bounced + row.bounced,
      totalCostCents: acc.totalCostCents + row.total_cost_cents
    }), {
      sent: 0,
      delivered: 0,
      read: 0,
      failed: 0,
      bounced: 0,
      totalCostCents: 0
    });
  }

  private calculateOverallTiming(data: any[]): OverallTiming {
    if (data.length === 0) {
      return { avgDeliverySeconds: 0, avgFirstReadSeconds: 0 };
    }

    const totalMessages = data.reduce((sum, row) => sum + row.sent, 0);
    const weightedDelivery = data.reduce(
      (sum, row) => sum + row.avg_delivery_seconds * row.sent,
      0
    );

    return {
      avgDeliverySeconds: weightedDelivery / totalMessages,
      avgFirstReadSeconds: data[0]?.avg_first_read_seconds || 0
    };
  }

  private getTopCategories(data: any[], limit: number): any[] {
    const grouped = data.reduce((acc, row) => {
      const key = row.template_category || 'uncategorized';
      if (!acc[key]) {
        acc[key] = { sent: 0, read: 0 };
      }
      acc[key].sent += row.sent;
      acc[key].read += row.read;
      return acc;
    }, {});

    return Object.entries(grouped)
      .map(([category, stats]: [string, any]) => ({
        category,
        ...stats,
        readRate: (stats.read / stats.sent * 100).toFixed(2)
      }))
      .sort((a, b) => b.sent - a.sent)
      .slice(0, limit);
  }
}

interface DeliveryMetrics {
  byChannel: Array<{
    channel: string;
    sent: number;
    delivered: number;
    read: number;
    failed: number;
    bounced: number;
    delivery_rate: number;
    read_rate: number;
    failure_rate: number;
    total_cost_cents: number;
  }>;
  totals: TotalMetrics;
}

interface TotalMetrics {
  sent: number;
  delivered: number;
  read: number;
  failed: number;
  bounced: number;
  totalCostCents: number;
}

interface TimingMetrics {
  byChannel: Array<{
    channel: string;
    avg_delivery_seconds: number;
    avg_first_read_seconds: number;
    p50_delivery_seconds: number;
    p95_delivery_seconds: number;
    p99_delivery_seconds: number;
  }>;
  overall: OverallTiming;
}

interface OverallTiming {
  avgDeliverySeconds: number;
  avgFirstReadSeconds: number;
}

interface EngagementMetrics {
  byChannelAndCategory: Array<{
    channel: string;
    template_category: string;
    sent: number;
    read: number;
    read_rate: number;
    with_attachments: number;
    attachment_reads: number;
    attachment_read_rate: number;
  }>;
  topCategories: Array<{
    category: string;
    sent: number;
    read: number;
    readRate: string;
  }>;
}

interface CostMetrics {
  byChannel: Array<{
    channel: string;
    message_count: number;
    total_cost_cents: number;
    cost_per_message: number;
    total_cost_rupees: number;
  }>;
  totalCostCents: number;
  totalCostRupees: number;
  averageCostPerMessage: number;
  mostExpensiveChannel: string;
  leastExpensiveChannel: string;
}

interface TemplatePerformance {
  template_id: string;
  template_code: string;
  template_category: string;
  channel: string;
  sent: number;
  delivered: number;
  read: number;
  delivery_rate: number;
  read_rate: number;
  avg_content_length: number;
  total_cost_cents: number;
}
```

---

## Funnels & Journeys

### Communication Funnel Analysis

```typescript
// services/analytics/funnel-analysis.service.ts

export class FunnelAnalysisService {
  private clickhouse: ClickHouse;

  /**
   * Get booking communication funnel
   *
   * Funnel stages:
   * 1. Inquiry received
   * 2. Quote sent
   * 3. Follow-up sent
   * 4. Booking confirmed
   * 5. Payment reminder sent
   * 6. Payment received
   * 7. Itinerary sent
   */
  async getBookingFunnel(
    agencyId: string,
    startDate: Date,
    endDate: Date
  ): Promise<FunnelAnalysis> {
    const query = `
      WITH funnel_stages AS (
        SELECT
          trip_id,
          recipient_id,
          countIf(template_category = 'inquiry') as inquiries,
          countIf(template_category = 'booking' AND event_type = 'sent') as quotes_sent,
          countIf(template_category = 'booking' AND event_type = 'read') as quotes_read,
          countIf(template_category = 'payment' AND event_type = 'sent') as payment_reminders,
          countIf(template_category = 'itinerary' AND event_type = 'sent') as itineraries_sent
        FROM message_events
        WHERE agency_id = {agencyId:UUID}
          AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
          AND trip_id IS NOT NULL
        GROUP BY trip_id, recipient_id
      )
      SELECT
        count(DISTINCT trip_id) as total_trips,
        countIf(inquiries > 0) as with_inquiry,
        countIf(quotes_sent > 0) as with_quote,
        countIf(quotes_read > 0) as quote_read,
        countIf(payment_reminders > 0) as with_payment_reminder,
        countIf(itineraries_sent > 0) as with_itinerary
      FROM funnel_stages
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      }
    });

    const data = await result.json();
    const row = data[0];

    const stages: FunnelStage[] = [
      { name: 'Total Trips', count: row.total_trips, percent: 100 },
      { name: 'Inquiry Received', count: row.with_inquiry, percent: (row.with_inquiry / row.total_trips * 100) },
      { name: 'Quote Sent', count: row.with_quote, percent: (row.with_quote / row.total_trips * 100) },
      { name: 'Quote Read', count: row.quote_read, percent: (row.quote_read / row.total_trips * 100) },
      { name: 'Payment Reminder', count: row.with_payment_reminder, percent: (row.with_payment_reminder / row.total_trips * 100) },
      { name: 'Itinerary Sent', count: row.with_itinerary, percent: (row.with_itinerary / row.total_trips * 100) }
    ];

    return {
      stages,
      overallConversion: (row.with_itinerary / row.total_trips * 100),
      dropoffPoints: this.calculateDropoffs(stages)
    };
  }

  /**
   * Get message response funnel
   *
   * Funnel stages:
   * 1. Message sent
   * 2. Message delivered
   * 3. Message read
   * 4. Customer replied
   */
  async getResponseFunnel(
    agencyId: string,
    startDate: Date,
    endDate: Date,
    channel?: string
  ): Promise<FunnelAnalysis> {
    const channelFilter = channel ? `AND channel = '${channel}'` : '';

    const query = `
      WITH message_threads AS (
        SELECT
          thread_id,
          countIf(direction = 'outbound' AND event_type = 'sent') as outbound_sent,
          countIf(direction = 'outbound' AND event_type = 'delivered') as outbound_delivered,
          countIf(direction = 'outbound' AND event_type = 'read') as outbound_read,
          countIf(direction = 'inbound' AND event_type = 'delivered') as inbound_replies
        FROM message_events
        WHERE agency_id = {agencyId:UUID}
          AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
          ${channelFilter}
        GROUP BY thread_id
      )
      SELECT
        countIf(outbound_sent > 0) as sent,
        countIf(outbound_delivered > 0) as delivered,
        countIf(outbound_read > 0) as read,
        countIf(inbound_replies > 0) as replied
      FROM message_threads
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      }
    });

    const data = await result.json();
    const row = data[0];

    const stages: FunnelStage[] = [
      { name: 'Sent', count: row.sent, percent: 100 },
      { name: 'Delivered', count: row.delivered, percent: (row.delivered / row.sent * 100) },
      { name: 'Read', count: row.read, percent: (row.read / row.sent * 100) },
      { name: 'Replied', count: row.replied, percent: (row.replied / row.sent * 100) }
    ];

    return {
      stages,
      overallConversion: (row.replied / row.sent * 100),
      dropoffPoints: this.calculateDropoffs(stages)
    };
  }

  /**
   * Calculate where users drop off in funnel
   */
  private calculateDropoffs(stages: FunnelStage[]): DropoffPoint[] {
    const dropoffs: DropoffPoint[] = [];

    for (let i = 1; i < stages.length; i++) {
      const dropoff = stages[i - 1].count - stages[i].count;
      const dropoffRate = ((stages[i - 1].percent - stages[i].percent) / stages[i - 1].percent * 100);

      dropoffs.push({
        from: stages[i - 1].name,
        to: stages[i].name,
        count: dropoff,
        rate: dropoffRate
      });
    }

    return dropoffs;
  }

  /**
   * Get customer communication journey
   *
   * Shows sequence of communications for a customer leading to conversion
   */
  async getCustomerJourney(
    customerId: string,
    agencyId: string
  ): Promise<CustomerJourney> {
    const query = `
      SELECT
        event_time,
        event_type,
        direction,
        channel,
        template_category,
        template_code,
        content_length,
        has_attachment
      FROM message_events
      WHERE agency_id = {agencyId:UUID}
        AND recipient_id = {customerId:UUID}
      ORDER BY event_time ASC
      LIMIT 100
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId,
        customerId
      }
    });

    const events = await result.json();

    // Analyze journey patterns
    const touchpoints = events.length;
    const outboundCount = events.filter(e => e.direction === 'outbound').length;
    const inboundCount = events.filter(e => e.direction === 'inbound').length;
    const channelsUsed = [...new Set(events.map(e => e.channel))];

    // Calculate response times
    const responseTimes: number[] = [];
    let lastOutboundTime: Date | null = null;

    for (const event of events) {
      if (event.direction === 'outbound' && event.event_type === 'sent') {
        lastOutboundTime = new Date(event.event_time);
      } else if (event.direction === 'inbound' && lastOutboundTime) {
        const responseTime = new Date(event.event_time).getTime() - lastOutboundTime.getTime();
        responseTimes.push(responseTime);
        lastOutboundTime = null;
      }
    }

    const avgResponseTime = responseTimes.length > 0
      ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
      : 0;

    return {
      customerId,
      events,
      touchpoints,
      outboundCount,
      inboundCount,
      channelsUsed,
      avgResponseTimeMinutes: avgResponseTime / 1000 / 60,
      responseRate: (inboundCount / outboundCount * 100) || 0
    };
  }
}

interface FunnelAnalysis {
  stages: FunnelStage[];
  overallConversion: number;
  dropoffPoints: DropoffPoint[];
}

interface FunnelStage {
  name: string;
  count: number;
  percent: number;
}

interface DropoffPoint {
  from: string;
  to: string;
  count: number;
  rate: number;
}

interface CustomerJourney {
  customerId: string;
  events: any[];
  touchpoints: number;
  outboundCount: number;
  inboundCount: number;
  channelsUsed: string[];
  avgResponseTimeMinutes: number;
  responseRate: number;
}
```

---

## Channel Performance

### Channel Comparison Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CHANNEL PERFORMANCE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DELIVERY RATES COMPARISON                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                       │   │
│  │  100% ┤                                                       ■■■  │   │
│  │   90% ┤                                              ■■■■         │   │
│  │   80% ┤                                    ■■■■                 │   │
│  │   70% ┤                         ■■■■                             │   │
│  │   60% ┤               ■■■■                                          │   │
│  │   50% ┤      ■■■                                                      │   │
│  │   40% ┤                                                            │   │
│  │   30% ┤                                                            │   │
│  │   20% ┤                                                            │   │
│  │   10% ┤                                                            │   │
│  │    0% ┼────────────────────────────────────────────────────────  │   │
│  │        WhatsApp   Email    SMS    In-App                          │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  KEY METRICS BY CHANNEL                                                     │
│  ┌────────────┬──────────┬───────────┬──────────┬──────────┬────────────┐   │
│  │ Channel    │ Messages │ Delivered │ Read     │ Failed   │ Cost/Msg   │   │
│  ├────────────┼──────────┼───────────┼──────────┼──────────┼────────────┤   │
│  │ WhatsApp   │  5,234   │   98.5%   │  72.3%   │  1.2%    │   ₹0.05    │   │
│  │ Email      │  3,102   │   96.2%   │  45.1%   │  3.5%    │   ₹0.01    │   │
│  │ SMS        │    812   │   94.8%   │   N/A    │  4.8%    │   ₹0.50    │   │
│  │ In-App     │  1,234   │   100%    │  38.2%   │  0%      │   ₹0.00    │   │
│  └────────────┴──────────┴───────────┴──────────┴──────────┴────────────┘   │
│                                                                             │
│  OPTIMAL CHANNEL RECOMMENDATIONS                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • For booking confirmations: WhatsApp (98.5% delivery, 72% read)  │   │
│  │ • For payment links: Email (higher click-through rate)            │   │
│  │ • For urgent reminders: SMS + WhatsApp (redundancy)               │   │
│  │ • For document sharing: In-App (100% delivery)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Channel Performance Query

```typescript
async getChannelPerformance(
  agencyId: string,
  startDate: Date,
  endDate: Date
): Promise<ChannelPerformanceReport> {
  const query = `
    SELECT
      channel,
      count() as total_messages,
      countIf(direction = 'outbound') as outbound,
      countIf(direction = 'inbound') as inbound,

      -- Delivery metrics
      countIf(event_type = 'delivered') as delivered,
      round(delivered / countIf(direction = 'outbound') * 100, 2) as delivery_rate,

      -- Read metrics
      countIf(event_type = 'read') as read,
      round(read / countIf(event_type = 'delivered') * 100, 2) as read_rate,

      -- Failure metrics
      countIf(event_type = 'failed') as failed,
      countIf(event_type = 'bounced') as bounced,

      -- Timing
      round(avg(delivery_time_ms) / 1000, 2) as avg_delivery_seconds,

      -- Cost
      sum(cost_cents) as total_cost_cents,
      round(sum(cost_cents) / count(), 2) as cost_per_message,

      -- Engagement
      countIf(has_attachment = 1) as with_attachments,
      round(avg(content_length), 2) as avg_content_length
    FROM message_events
    WHERE agency_id = {agencyId:UUID}
      AND event_date BETWEEN {startDate:Date} AND {endDate:Date}
    GROUP BY channel
    ORDER BY total_messages DESC
  `;

  const result = await this.clickhouse.query({
    query,
    query_params: {
      agencyId,
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0]
    }
  });

  const channels = await result.json();

  // Generate recommendations
  const recommendations = this.generateChannelRecommendations(channels);

  return {
    channels,
    recommendations,
    summary: {
      totalMessages: channels.reduce((sum, c) => sum + c.total_messages, 0),
      totalCost: channels.reduce((sum, c) => sum + c.total_cost_cents, 0),
      bestDeliveryChannel: channels.sort((a, b) => b.delivery_rate - a.delivery_rate)[0]?.channel,
      mostCostEffective: channels.sort((a, b) => a.cost_per_message - b.cost_per_message)[0]?.channel,
      highestEngagement: channels.sort((a, b) => b.read_rate - a.read_rate)[0]?.channel
    }
  };
}
```

---

## Real-Time Monitoring

### Live Dashboard Data

```typescript
// services/analytics/realtime-monitor.service.ts

export class RealtimeMonitorService {
  private redis: Redis;

  /**
   * Get live metrics for dashboard
   */
  async getLiveMetrics(agencyId: string): Promise<LiveMetrics> {
    const today = new Date().toISOString().split('T')[0];

    // Get from Redis cache
    const dailyKey = `metrics:${agencyId}:daily:${today}`;
    const daily = await this.redis.hgetall(dailyKey);

    // Get channel breakdown
    const channelKeys = ['whatsapp', 'email', 'sms', 'in_app'];
    const channelMetrics = await Promise.all(
      channelKeys.map(async (channel) => {
        const key = `metrics:${agencyId}:channel:${channel}`;
        const data = await this.redis.hgetall(key);
        return {
          channel,
          sent: parseInt(data['status:sent'] || '0'),
          delivered: parseInt(data['status:delivered'] || '0'),
          read: parseInt(data['status:read'] || '0'),
          failed: parseInt(data['status:failed'] || '0')
        };
      })
    );

    // Get active agents (agents who sent message in last 5 minutes)
    const activeAgents = await this.getActiveAgents(agencyId);

    // Get recent activity
    const recentActivity = await this.getRecentActivity(agencyId, 10);

    return {
      today: {
        total: parseInt(daily.total || '0'),
        sent: parseInt(daily['status:sent'] || '0'),
        delivered: parseInt(daily['status:delivered'] || '0'),
        read: parseInt(daily['status:read'] || '0'),
        failed: parseInt(daily['status:failed'] || '0')
      },
      byChannel: channelMetrics,
      activeAgents,
      recentActivity,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get currently active agents
   */
  private async getActiveAgents(agencyId: string): Promise<string[]> {
    const key = `agency:${agencyId}:active_agents`;
    const agents = await this.redis.smembers(key);
    return agents;
  }

  /**
   * Get recent message activity
   */
  private async getRecentActivity(
    agencyId: string,
    limit: number
  ): Promise<RecentActivity[]> {
    const key = `agency:${agencyId}:recent_activity`;
    const activities = await this.redis.lrange(key, 0, limit - 1);

    return activities.map(a => JSON.parse(a));
  }

  /**
   * Subscribe to live updates
   */
  subscribeToUpdates(
    agencyId: string,
    callback: (update: LiveUpdate) => void
  ): () => void {
    const subscriber = new Redis();

    subscriber.subscribe('message:events');

    subscriber.on('message', (channel, message) => {
      const event = JSON.parse(message);

      if (event.agencyId === agencyId) {
        callback({
          type: 'message_event',
          data: event,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Return unsubscribe function
    return () => {
      subscriber.unsubscribe();
      subscriber.quit();
    };
  }
}

interface LiveMetrics {
  today: {
    total: number;
    sent: number;
    delivered: number;
    read: number;
    failed: number;
  };
  byChannel: Array<{
    channel: string;
    sent: number;
    delivered: number;
    read: number;
    failed: number;
  }>;
  activeAgents: string[];
  recentActivity: RecentActivity[];
  timestamp: string;
}

interface RecentActivity {
  messageId: string;
  channel: string;
  direction: string;
  eventType: string;
  recipientId: string;
  timestamp: string;
}

interface LiveUpdate {
  type: string;
  data: any;
  timestamp: string;
}
```

---

## Reporting & Exports

### Report Generation

```typescript
// services/analytics/report-generator.service.ts

import PDFDocument from 'pdfkit';
import ExcelJS from 'exceljs';

export class ReportGeneratorService {
  /**
   * Generate communication performance report
   */
  async generatePerformanceReport(
    agencyId: string,
    startDate: Date,
    endDate: Date,
    format: 'pdf' | 'excel' | 'json'
  ): Promise<Buffer> {
    // Gather data
    const [
      deliveryMetrics,
      timingMetrics,
      costMetrics,
      channelPerformance,
      templatePerformance
    ] = await Promise.all([
      this.metricsQuery.getDeliveryMetrics(agencyId, startDate, endDate),
      this.metricsQuery.getTimingMetrics(agencyId, startDate, endDate),
      this.metricsQuery.getCostMetrics(agencyId, startDate, endDate),
      this.metricsQuery.getChannelPerformance(agencyId, startDate, endDate),
      this.metricsQuery.getTemplatePerformance(agencyId, startDate, endDate, 10)
    ]);

    const reportData = {
      agencyId,
      period: { startDate, endDate },
      delivery: deliveryMetrics,
      timing: timingMetrics,
      cost: costMetrics,
      channels: channelPerformance,
      templates: templatePerformance,
      generatedAt: new Date()
    };

    // Generate based on format
    switch (format) {
      case 'pdf':
        return this.generatePDF(reportData);

      case 'excel':
        return this.generateExcel(reportData);

      case 'json':
        return Buffer.from(JSON.stringify(reportData, null, 2));

      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  /**
   * Generate PDF report
   */
  private async generatePDF(data: any): Promise<Buffer> {
    const doc = new PDFDocument({ size: 'A4', margin: 50 });
    const chunks: Buffer[] = [];

    doc.on('data', chunk => chunks.push(chunk));

    // Header
    doc.fontSize(20).text('Communication Performance Report', { align: 'center' });
    doc.moveDown();
    doc.fontSize(10).text(
      `Period: ${data.period.startDate} to ${data.period.endDate}`,
      { align: 'center' }
    );
    doc.moveDown();

    // Summary section
    doc.fontSize(14).text('Summary');
    doc.fontSize(10);
    doc.text(`Total Messages: ${data.delivery.totals.sent}`);
    doc.text(`Delivery Rate: ${((data.delivery.totals.delivered / data.delivery.totals.sent) * 100).toFixed(2)}%`);
    doc.text(`Read Rate: ${((data.delivery.totals.read / data.delivery.totals.delivered) * 100).toFixed(2)}%`);
    doc.text(`Total Cost: ₹${(data.delivery.totals.totalCostCents / 100).toFixed(2)}`);
    doc.moveDown();

    // Channel breakdown table
    doc.fontSize(14).text('Channel Performance');
    doc.moveDown();

    // Table header
    const tableTop = doc.y;
    const rowHeight = 20;
    const colWidths = [80, 60, 60, 60, 60];

    doc.fontSize(10);
    ['Channel', 'Sent', 'Delivered', 'Read', 'Cost'].forEach((header, i) => {
      doc.text(header, 50 + colWidths.slice(0, i).reduce((a, b) => a + b, 0), tableTop);
    });

    // Table rows
    data.channels.channels.forEach((channel: any, i: number) => {
      const y = tableTop + rowHeight * (i + 1);
      [
        channel.channel,
        channel.message_count,
        channel.delivered,
        channel.read,
        `₹${channel.total_cost_rupees.toFixed(2)}`
      ].forEach((text, j) => {
        doc.text(
          String(text),
          50 + colWidths.slice(0, j).reduce((a, b) => a + b, 0),
          y
        );
      });
    });

    doc.end();

    return Buffer.concat(chunks);
  }

  /**
   * Generate Excel report
   */
  private async generateExcel(data: any): Promise<Buffer> {
    const workbook = new ExcelJS.Workbook();
    workbook.creator = 'Travel Agency Agent';
    workbook.created = new Date();

    // Summary sheet
    const summarySheet = workbook.addWorksheet('Summary');
    summarySheet.addRow(['Metric', 'Value']);
    summarySheet.addRow(['Period', `${data.period.startDate} - ${data.period.endDate}`]);
    summarySheet.addRow(['Total Messages', data.delivery.totals.sent]);
    summarySheet.addRow(['Delivery Rate', `${((data.delivery.totals.delivered / data.delivery.totals.sent) * 100).toFixed(2)}%`]);
    summarySheet.addRow(['Read Rate', `${((data.delivery.totals.read / data.delivery.totals.delivered) * 100).toFixed(2)}%`]);
    summarySheet.addRow(['Total Cost', `₹${(data.delivery.totals.totalCostCents / 100).toFixed(2)}`]);

    // Channels sheet
    const channelsSheet = workbook.addWorksheet('Channels');
    channelsSheet.addRow(['Channel', 'Messages', 'Delivered', 'Read', 'Failed', 'Cost']);

    data.channels.channels.forEach((channel: any) => {
      channelsSheet.addRow([
        channel.channel,
        channel.message_count,
        channel.delivered,
        channel.read,
        channel.failed,
        `₹${channel.total_cost_rupees.toFixed(2)}`
      ]);
    });

    // Templates sheet
    const templatesSheet = workbook.addWorksheet('Templates');
    templatesSheet.addRow(['Template', 'Category', 'Sent', 'Delivery Rate', 'Read Rate']);

    data.templates.forEach((template: any) => {
      templatesSheet.addRow([
        template.template_code,
        template.template_category,
        template.sent,
        `${template.delivery_rate}%`,
        `${template.read_rate}%`
      ]);
    });

    const buffer = await workbook.xlsx.writeBuffer();
    return Buffer.from(buffer);
  }

  /**
   * Schedule recurring report
   */
  async scheduleRecurringReport(config: {
    agencyId: string;
    name: string;
    frequency: 'daily' | 'weekly' | 'monthly';
    format: 'pdf' | 'excel';
    recipients: string[];
  }): Promise<string> {
    const scheduleId = generateId();

    await db.query(`
      INSERT INTO scheduled_reports (
        id, agency_id, name, frequency, format, recipients, status
      ) VALUES ($1, $2, $3, $4, $5, $6, 'active')
    `, [scheduleId, config.agencyId, config.name, config.frequency, config.format, JSON.stringify(config.recipients)]);

    // Schedule in BullMQ
    const cronExpression = this.getCronExpression(config.frequency);

    await reportQueue.add('generate-report', {
      scheduleId,
      agencyId: config.agencyId,
      format: config.format
    }, {
      repeat: { pattern: cronExpression },
      jobId: scheduleId
    });

    return scheduleId;
  }

  private getCronExpression(frequency: string): string {
    switch (frequency) {
      case 'daily':
        return '0 9 * * *'; // 9 AM daily
      case 'weekly':
        return '0 9 * * 1'; // 9 AM every Monday
      case 'monthly':
        return '0 9 1 * *'; // 9 AM on 1st of month
      default:
        return '0 9 * * *';
    }
  }
}
```

---

## Alerting & Insights

### Alert Configuration

```typescript
// services/analytics/alerting.service.ts

export class AlertingService {
  /**
   * Configure alert rule
   */
  async configureAlert(config: AlertConfig): Promise<string> {
    const alertId = generateId();

    await db.query(`
      INSERT INTO alert_rules (
        id, agency_id, name, metric, condition, threshold,
        window_minutes, recipients, status
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')
    `, [
      alertId,
      config.agencyId,
      config.name,
      config.metric,
      config.condition,
      config.threshold,
      config.windowMinutes,
      JSON.stringify(config.recipients)
    ]);

    return alertId;
  }

  /**
   * Check alert conditions
   */
  async checkAlerts(agencyId: string): Promise<AlertTrigger[]> {
    const activeAlerts = await db.query(`
      SELECT * FROM alert_rules
      WHERE agency_id = $1 AND status = 'active'
    `, [agencyId]);

    const triggers: AlertTrigger[] = [];

    for (const alert of activeAlerts.rows) {
      const value = await this.getMetricValue(
        agencyId,
        alert.metric,
        alert.window_minutes
      );

      const shouldTrigger = this.evaluateCondition(
        value,
        alert.condition,
        alert.threshold
      );

      if (shouldTrigger) {
        triggers.push({
          alertId: alert.id,
          alertName: alert.name,
          metric: alert.metric,
          currentValue: value,
          threshold: alert.threshold,
          condition: alert.condition
        });

        // Send alert
        await this.sendAlert(alert, value);
      }
    }

    return triggers;
  }

  /**
   * Get metric value for alert evaluation
   */
  private async getMetricValue(
    agencyId: string,
    metric: string,
    windowMinutes: number
  ): Promise<number> {
    const redis = getRedisClient();
    const key = `metrics:${agencyId}:current`;

    switch (metric) {
      case 'delivery_rate':
        const total = await redis.hget(key, 'total');
        const delivered = await redis.hget(key, 'delivered');
        return total > 0 ? (parseInt(delivered) / parseInt(total)) * 100 : 0;

      case 'failure_rate':
        const total2 = await redis.hget(key, 'total');
        const failed = await redis.hget(key, 'failed');
        return total2 > 0 ? (parseInt(failed) / parseInt(total2)) * 100 : 0;

      case 'queue_depth':
        return await messageQueue.getJobCountByTypes('waiting', 'delayed');

      case 'avg_delivery_time':
        // Would query ClickHouse for this
        return 0;

      default:
        return 0;
    }
  }

  /**
   * Evaluate alert condition
   */
  private evaluateCondition(
    value: number,
    condition: string,
    threshold: number
  ): boolean {
    switch (condition) {
      case 'greater_than':
        return value > threshold;
      case 'less_than':
        return value < threshold;
      case 'equals':
        return value === threshold;
      case 'percentage_above':
        return value > threshold;
      case 'percentage_below':
        return value < threshold;
      default:
        return false;
    }
  }

  /**
   * Send alert notification
   */
  private async sendAlert(alert: any, value: number): Promise<void> {
    const recipients = JSON.parse(alert.recipients);

    for (const recipient of recipients) {
      await this.redis.publish('alerts', JSON.stringify({
        to: recipient,
        subject: `Alert: ${alert.name}`,
        message: `The metric ${alert.metric} is ${alert.condition} ${alert.threshold}. Current value: ${value}`
      }));
    }
  }

  /**
   * Generate insights from metrics
   */
  async generateInsights(agencyId: string): Promise<Insight[]> {
    const insights: Insight[] = [];

    // Get recent metrics
    const todayMetrics = await this.metricsQuery.getDeliveryMetrics(
      agencyId,
      new Date(Date.now() - 24 * 60 * 60 * 1000),
      new Date()
    );

    const lastWeekMetrics = await this.metricsQuery.getDeliveryMetrics(
      agencyId,
      new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      new Date(Date.now() - 24 * 60 * 60 * 1000)
    );

    // Compare delivery rates
    const todayDeliveryRate = (todayMetrics.totals.delivered / todayMetrics.totals.sent) * 100;
    const weekDeliveryRate = (lastWeekMetrics.totals.delivered / lastWeekMetrics.totals.sent) * 100;

    if (todayDeliveryRate < weekDeliveryRate - 5) {
      insights.push({
        type: 'warning',
        title: 'Delivery rate dropped',
        description: `Delivery rate is ${todayDeliveryRate.toFixed(2)}%, down from ${weekDeliveryRate.toFixed(2)}% last week.`,
        recommendation: 'Check for recent webhook failures or channel issues.'
      });
    }

    // Check cost trends
    const todayCost = todayMetrics.totals.totalCostCents;
    const avgDailyCost = lastWeekMetrics.totals.totalCostCents / 7;

    if (todayCost > avgDailyCost * 1.5) {
      insights.push({
        type: 'info',
        title: 'Higher than usual spending',
        description: `Today's cost (₹${(todayCost / 100).toFixed(2)}) is 50% above the 7-day average.`,
        recommendation: 'Review message volume and consider using more cost-effective channels.'
      });
    }

    // Channel optimization
    const channelPerf = todayMetrics.byChannel;
    const worstChannel = channelPerf.sort((a, b) => a.delivery_rate - b.delivery_rate)[0];

    if (worstChannel && worstChannel.delivery_rate < 90) {
      insights.push({
        type: 'warning',
        title: `${worstChannel.channel} delivery rate below target`,
        description: `${worstChannel.channel} delivery rate is ${worstChannel.delivery_rate}%, below the 95% target.`,
        recommendation: 'Consider switching to alternative channels for urgent messages.'
      });
    }

    return insights;
  }
}

interface AlertConfig {
  agencyId: string;
  name: string;
  metric: 'delivery_rate' | 'failure_rate' | 'queue_depth' | 'avg_delivery_time';
  condition: 'greater_than' | 'less_than' | 'equals' | 'percentage_above' | 'percentage_below';
  threshold: number;
  windowMinutes: number;
  recipients: string[];
}

interface AlertTrigger {
  alertId: string;
  alertName: string;
  metric: string;
  currentValue: number;
  threshold: number;
  condition: string;
}

interface Insight {
  type: 'info' | 'warning' | 'success' | 'error';
  title: string;
  description: string;
  recommendation: string;
}
```

---

## Summary

The Communication Hub Analytics provides:

1. **Comprehensive Metrics**: Delivery, timing, engagement, and cost tracking
2. **Real-Time Monitoring**: Live dashboard with WebSocket updates
3. **Funnel Analysis**: Track conversion through communication journeys
4. **Channel Comparison**: Performance insights across all channels
5. **Template Analytics**: Know which messages resonate best
6. **Alerting**: Proactive notifications for issues
7. **Reporting**: PDF/Excel exports and scheduled reports
8. **Cost Optimization**: Identify spending patterns and savings opportunities

---

**Series Complete:** All 4 Communication Hub documents are now complete. See [Communication Hub Master Index](COMM_HUB_DEEP_DIVE_MASTER_INDEX.md) for navigation.
