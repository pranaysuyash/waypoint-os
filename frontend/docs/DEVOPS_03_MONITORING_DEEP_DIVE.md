# DEVOPS_03: Monitoring & Observability Deep Dive

> Comprehensive guide to application monitoring, logging, tracing, and alerting for the Travel Agency Agent platform

---

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Philosophy](#monitoring-philosophy)
3. [Metrics Collection](#metrics-collection)
4. [Logging Infrastructure](#logging-infrastructure)
5. [Distributed Tracing](#distributed-tracing)
6. [Error Tracking](#error-tracking)
7. [Alerting System](#alerting-system)
8. [Dashboard Architecture](#dashboard-architecture)
9. [Performance Monitoring](#performance-monitoring)
10. [Incident Response Integration](#incident-response-integration)

---

## Overview

### Goals

- **Visibility**: Complete observability across all system components
- **Proactive Detection**: Identify issues before users are impacted
- **Rapid Debugging**: Pinpoint root causes quickly
- **Data-Driven Decisions**: Use metrics to guide optimization

### Monitoring Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY PLATFORM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   METRICS    │  │    LOGS      │  │    TRACES    │          │
│  │  (Prometheus) │  │   (ELK/Loki) │  │ (Jaeger/OTel)│          │
│  │              │  │              │  │              │          │
│  │ • Counters   │  │ • Structured │  │ • Spans      │          │
│  │ • Gauges     │  │ • Indexed    │  │ • Context    │          │
│  │ • Histograms │  │ • Retention  │  │ • Timeline   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ALERTING LAYER                        │   │
│  │  (Alertmanager → PagerDuty → Slack → Email)            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   DASHBOARD LAYER                       │   │
│  │  (Grafana → Custom Dashboards → Reports)                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Metrics** | Prometheus + Grafana | Time-series data, visualization |
| **Logging** | ELK Stack / Loki | Log aggregation, search |
| **Tracing** | OpenTelemetry + Jaeger | Distributed tracing |
| **Error Tracking** | Sentry | Error aggregation, alerting |
| **APM** | Grafana Pyroscope | Profiling, performance |
| **Uptime** | UptimeRobot / Pingdom | External monitoring |
| **Alerting** | Alertmanager + PagerDuty | Alert routing, escalation |

---

## Monitoring Philosophy

### Golden Signals

Four key metrics that indicate system health:

```
┌────────────────────────────────────────────────────────────────┐
│                       GOLDEN SIGNALS                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. LATENCY          2. TRAFFIC                                │
│  ┌─────────────┐    ┌─────────────┐                           │
│  │  p50: 200ms │    │  1K req/s   │                           │
│  │  p95: 500ms │    │  5K req/s   │                           │
│  │  p99: 1s    │    │  10K req/s  │                           │
│  └─────────────┘    └─────────────┘                           │
│                                                                 │
│  3. ERRORS           4. SATURATION                             │
│  ┌─────────────┐    ┌─────────────┐                           │
│  │  4xx: 2%    │    │  CPU: 60%   │                           │
│  │  5xx: 0.1%  │    │  Memory: 70%│                           │
│  │  Timeouts   │    │  Disk: 50%  │                           │
│  └─────────────┘    └─────────────┘                           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### RED Method (Rate, Errors, Duration)

Applied to each service/component:

```typescript
interface REDMetrics {
  // Rate: Requests per second
  rate: {
    total: number;      // Total requests
    byStatus: Record<number, number>;  // Breakdown by status code
    byEndpoint: Record<string, number>; // Breakdown by route
  };

  // Errors: Failed requests
  errors: {
    rate: number;       // Error rate (errors / total)
    byType: Record<string, number>;    // Error types
    byService: Record<string, number>; // Error source
  };

  // Duration: Request latency
  duration: {
    p50: number;        // Median
    p95: number;        // 95th percentile
    p99: number;        // 99th percentile
    max: number;        // Maximum
  };
}
```

### Monitoring Levels

```
┌──────────────────────────────────────────────────────────────┐
│                    MONITORING PYRAMID                         │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│                    ┌─────────────┐                            │
│                    │   SYNTHETIC │  ← Uptime checks, health   │
│                    │   MONITORING│    probes, canary tests    │
│                    └──────┬──────┘                            │
│                           │                                    │
│                  ┌────────▼─────────┐                          │
│                  │   APPLICATION    │  ← Business metrics,    │
│                  │   LEVEL MONITORING│   feature flags, A/B   │
│                  └────────┬─────────┘                          │
│                           │                                    │
│                 ┌─────────▼──────────┐                        │
│                 │   MIDDLEWARE/      │  ← Request/response,   │
│                 │   SERVICE LEVEL    │   database queries,    │
│                 └─────────┬──────────┘   external API calls   │
│                           │                                    │
│                  ┌────────▼─────────┐                          │
│                  │   INFRASTRUCTURE │  ← CPU, memory, disk,   │
│                  │   LEVEL MONITORING│   network, containers  │
│                  └──────────────────┘                          │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Metrics Collection

### Prometheus Integration

```typescript
// lib/monitoring/metrics.ts

import { Counter, Histogram, Gauge, Registry } from 'prom-client';

// Custom registry for application metrics
export const appRegistry = new Registry();

// ============================================================================
// COUNTERS: Monotonically increasing values
// ============================================================================

export const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code', 'agency_id'] as const,
  registers: [appRegistry],
});

export const bookingsCreated = new Counter({
  name: 'bookings_created_total',
  help: 'Total number of bookings created',
  labelNames: ['agency_id', 'supplier_type', 'booking_type'] as const,
  registers: [appRegistry],
});

export const paymentsProcessed = new Counter({
  name: 'payments_processed_total',
  help: 'Total number of payments processed',
  labelNames: ['agency_id', 'payment_method', 'status'] as const,
  registers: [appRegistry],
});

export const aiRequestsTotal = new Counter({
  name: 'ai_requests_total',
  help: 'Total number of AI API requests',
  labelNames: ['agency_id', 'model', 'operation', 'provider'] as const,
  registers: [appRegistry],
});

// ============================================================================
// HISTOGRAMS: Distributed values (latency, sizes)
// ============================================================================

export const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request latency',
  labelNames: ['method', 'route', 'status_code', 'agency_id'] as const,
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [appRegistry],
});

export const databaseQueryDuration = new Histogram({
  name: 'database_query_duration_seconds',
  help: 'Database query latency',
  labelNames: ['operation', 'table', 'agency_id'] as const,
  buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1],
  registers: [appRegistry],
});

export const externalApiDuration = new Histogram({
  name: 'external_api_duration_seconds',
  help: 'External API call latency',
  labelNames: ['service', 'operation', 'agency_id'] as const,
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60],
  registers: [appRegistry],
});

export const aiResponseDuration = new Histogram({
  name: 'ai_response_duration_seconds',
  help: 'AI API response latency',
  labelNames: ['model', 'operation', 'provider', 'agency_id'] as const,
  buckets: [0.5, 1, 2, 5, 10, 20, 30, 60, 120],
  registers: [appRegistry],
});

// ============================================================================
// GAUGES: Point-in-time values
// ============================================================================

export const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  labelNames: ['type'] as const,
  registers: [appRegistry],
});

export const queueSize = new Gauge({
  name: 'queue_size',
  help: 'Current queue size',
  labelNames: ['queue_name'] as const,
  registers: [appRegistry],
});

export const cacheHitRate = new Gauge({
  name: 'cache_hit_rate',
  help: 'Cache hit rate (0-1)',
  labelNames: ['cache_type'] as const,
  registers: [appRegistry],
});
```

### Middleware Integration

```typescript
// middleware/metrics.ts

import { Request, Response, NextFunction } from 'express';
import {
  httpRequestsTotal,
  httpRequestDuration,
} from '@/lib/monitoring/metrics';

export function metricsMiddleware() {
  return (req: Request, res: Response, next: NextFunction) => {
    const start = Date.now();

    // Track active connections
    activeConnections.inc({ type: 'http' });

    // Intercept response finish
    res.on('finish', () => {
      const duration = (Date.now() - start) / 1000;
      const route = req.route?.path || req.path;
      const agencyId = req.user?.agencyId || 'anonymous';

      // Record metrics
      httpRequestsTotal.inc({
        method: req.method,
        route,
        status_code: res.statusCode,
        agency_id: agencyId,
      });

      httpRequestDuration.observe({
        method: req.method,
        route,
        status_code: res.statusCode,
        agency_id: agencyId,
      }, duration);

      // Decrement active connections
      activeConnections.dec({ type: 'http' });
    });

    next();
  };
}
```

### Business Metrics

```typescript
// lib/monitoring/business-metrics.ts

import { Counter, Histogram, Gauge } from 'prom-client';

// Trip lifecycle metrics
export const tripsByStage = new Gauge({
  name: 'trips_by_stage',
  help: 'Number of trips at each stage',
  labelNames: ['agency_id', 'stage'] as const,
});

export const tripsInStageDuration = new Histogram({
  name: 'trips_stage_duration_hours',
  help: 'Time spent in each stage',
  labelNames: ['agency_id', 'stage'] as const,
  buckets: [1, 6, 24, 72, 168, 336, 720], // 1h, 6h, 1d, 3d, 1w, 2w, 1mo
});

// Agent productivity
export const agentActionsTotal = new Counter({
  name: 'agent_actions_total',
  help: 'Total actions performed by agents',
  labelNames: ['agency_id', 'agent_id', 'action_type'] as const,
});

export const agentResponseTime = new Histogram({
  name: 'agent_response_time_minutes',
  help: 'Time from customer inquiry to first agent response',
  labelNames: ['agency_id', 'channel'] as const,
  buckets: [1, 5, 15, 30, 60, 120, 240, 1440],
});

// Conversion funnel
export const funnelStage = new Gauge({
  name: 'funnel_stage_count',
  help: 'Number of entities at each funnel stage',
  labelNames: ['agency_id', 'funnel_type', 'stage'] as const,
});

// Financial metrics
export const bookingValue = new Histogram({
  name: 'booking_value_usd',
  help: 'Booking value distribution',
  labelNames: ['agency_id', 'booking_type'] as const,
  buckets: [100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000],
});

export const paymentSuccessRate = new Gauge({
  name: 'payment_success_rate',
  help: 'Payment success rate (0-1)',
  labelNames: ['agency_id', 'payment_method'] as const,
});
```

### Metrics Endpoint

```typescript
// app/api/metrics/route.ts

import { register } from 'prom-client';
import { appRegistry } from '@/lib/monitoring/metrics';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';

export async function GET(request: NextRequest) {
  // Basic auth check
  const authHeader = request.headers.get('authorization');
  const expectedAuth = `Bearer ${process.env.METRICS_TOKEN}`;

  if (authHeader !== expectedAuth) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Merge default and app registries
  const metrics = await register.metrics();

  return new NextResponse(metrics, {
    headers: {
      'Content-Type': register.contentType,
    },
  });
}
```

---

## Logging Infrastructure

### Structured Logging

```typescript
// lib/logging/logger.ts

import pino from 'pino';

export interface LogContext {
  userId?: string;
  agencyId?: string;
  tripId?: string;
  requestId?: string;
  sessionId?: string;
  [key: string]: unknown;
}

const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  redact: {
    paths: [
      'req.headers.authorization',
      'req.headers.cookie',
      'req.body.password',
      'req.body.token',
      'req.body.apiKey',
      'res.headers.set-cookie',
    ],
    remove: true,
  },
  ...(isDevelopment
    ? {
        transport: {
          target: 'pino-pretty',
          options: {
            colorize: true,
            translateTime: 'SYS:standard',
            ignore: 'pid,hostname',
          },
        },
      }
    : {}),
  serializers: {
    err: pino.stdSerializers.err,
    req: pino.stdSerializers.req,
    res: pino.stdSerializers.res,
  },
});

// Context-aware logger factory
export function createLogger(context: LogContext) {
  return logger.child(context);
}

// Convenience methods
export const log = {
  debug: (msg: string, obj?: Record<string, unknown>, context?: LogContext) => {
    const childLogger = context ? logger.child(context) : logger;
    childLogger.debug(obj || {}, msg);
  },

  info: (msg: string, obj?: Record<string, unknown>, context?: LogContext) => {
    const childLogger = context ? logger.child(context) : logger;
    childLogger.info(obj || {}, msg);
  },

  warn: (msg: string, obj?: Record<string, unknown>, context?: LogContext) => {
    const childLogger = context ? logger.child(context) : logger;
    childLogger.warn(obj || {}, msg);
  },

  error: (msg: string, error?: Error | unknown, obj?: Record<string, unknown>, context?: LogContext) => {
    const childLogger = context ? logger.child(context) : logger;
    const errObj = error instanceof Error ? { err: error, ...obj } : obj;
    childLogger.error(errObj || {}, msg);
  },

  fatal: (msg: string, error?: Error | unknown, obj?: Record<string, unknown>, context?: LogContext) => {
    const childLogger = context ? logger.child(context) : logger;
    const errObj = error instanceof Error ? { err: error, ...obj } : obj;
    childLogger.fatal(errObj || {}, msg);
  },
};
```

### Request Logging Middleware

```typescript
// middleware/request-logging.ts

import { NextRequest, NextResponse } from 'next/server';
import { requestId } from '@/lib/middleware/request-id';
import { log } from '@/lib/logging/logger';
import type { RequestContext } from '@/types/context';

export async function requestLoggingMiddleware(
  request: NextRequest,
  context: RequestContext
) {
  const start = Date.now();
  const requestId = context.requestId;

  // Log incoming request
  log.info('Incoming request', {
    method: request.method,
    url: request.url,
    userAgent: request.headers.get('user-agent'),
    ip: request.headers.get('x-forwarded-for') || 'unknown',
  },
  { requestId, userId: context.userId, agencyId: context.agencyId }
  );

  // Add response listener
  request.headers.set('x-request-start', start.toString());

  return request;
}

export function logResponse(
  request: NextRequest,
  response: NextResponse,
  context: RequestContext
) {
  const start = parseInt(request.headers.get('x-request-start') || '0');
  const duration = Date.now() - start;

  log.info('Request completed', {
    method: request.method,
    url: request.url,
    status: response.status,
    duration,
  },
  { requestId: context.requestId, userId: context.userId, agencyId: context.agencyId }
  );
}
```

### Log Aggregation

```dockerfile
# docker-compose.logging.yml

version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### Loki Alternative (Lighter Weight)

```yaml
# monitoring/loki-config.yml

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

```typescript
// lib/logging/loki-transport.ts

import pino from 'pino';
import { LokiLogger } from 'pino-loki';

export function createLokiTransport() {
  if (process.env.NODE_ENV === 'development') {
    return; // Use pretty print in dev
  }

  const lokiTransport = new LokiLogger({
    batchSize: 10,
    interval: 5,
    connection: {
      host: process.env.LOKI_HOST || 'http://localhost:3100',
      headers: {
        'X-Scope-OrgID': process.env.LOKI_TENANT_ID || 'travel-agency',
      },
    },
    labels: {
      environment: process.env.NODE_ENV,
      application: 'travel-agency-agent',
    },
  });

  return lokiTransport;
}
```

---

## Distributed Tracing

### OpenTelemetry Setup

```typescript
// lib/monitoring/tracing.ts

import { trace, context, Span, SpanStatusCode } from '@opentelemetry/api';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { JaegerExporter } from '@opentelemetry/exporter-trace-jaeger';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { ExpressInstrumentation } from '@opentelemetry/instrumentation-express';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { PgInstrumentation } from '@opentelemetry/instrumentation-pg';
import { RedisInstrumentation } from '@opentelemetry/instrumentation-redis';
import { registerInstrumentations } from '@opentelemetry/instrumentation';

// Initialize tracer
export function initializeTracer() {
  const provider = new NodeTracerProvider({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'travel-agency-api',
      [SemanticResourceAttributes.SERVICE_VERSION]: process.env.APP_VERSION || '1.0.0',
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV,
    }),
  });

  // Jaeger exporter
  const exporter = new JaegerExporter({
    endpoint: process.env.JAEGER_ENDPOINT || 'http://localhost:14268/api/traces',
  });

  provider.addSpanProcessor(new BatchSpanProcessor(exporter));
  provider.register();

  // Auto-instrumentation
  registerInstrumentations({
    instrumentations: [
      new HttpInstrumentation(),
      new ExpressInstrumentation(),
      new PgInstrumentation(),
      new RedisInstrumentation(),
    ],
  });
}

// Tracing helpers
export const tracer = trace.getTracer('travel-agency');

export interface TraceOptions {
  name: string;
  attributes?: Record<string, string | number | boolean>;
  userId?: string;
  agencyId?: string;
  tripId?: string;
}

export async function withSpan<T>(
  options: TraceOptions,
  fn: (span: Span) => Promise<T>
): Promise<T> {
  const span = tracer.startSpan(options.name, {
    attributes: {
      ...options.attributes,
      'user.id': options.userId,
      'agency.id': options.agencyId,
      'trip.id': options.tripId,
    },
  });

  try {
    const result = await context.with(trace.setSpan(context.active(), span), () => fn(span));
    span.setStatus({ code: SpanStatusCode.OK });
    return result;
  } catch (error) {
    span.recordException(error as Error);
    span.setStatus({ code: SpanStatusCode.ERROR, message: (error as Error).message });
    throw error;
  } finally {
    span.end();
  }
}
```

### Manual Tracing

```typescript
// services/booking.service.ts

import { withSpan } from '@/lib/monitoring/tracing';
import { log } from '@/lib/logging/logger';

export class BookingService {
  async createBooking(bookingData: CreateBookingDTO, context: RequestContext) {
    return withSpan(
      {
        name: 'booking.create',
        attributes: {
          'booking.type': bookingData.type,
          'booking.supplier': bookingData.supplierId,
          'booking.value': bookingData.totalPrice,
        },
        userId: context.userId,
        agencyId: context.agencyId,
        tripId: bookingData.tripId,
      },
      async (span) => {
        // Add events to span
        span.addEvent('validation_started');

        const validated = await this.validateBooking(bookingData);
        span.addEvent('validation_completed', { 'valid': validated.isValid });

        if (!validated.isValid) {
          span.setAttribute('validation.errors', validated.errors.length);
          throw new BookingValidationError(validated.errors);
        }

        span.addEvent('supplier_call_started');
        const supplierResult = await this.callSupplier(bookingData);
        span.addEvent('supplier_call_completed', {
          'supplier.booking_id': supplierResult.bookingId,
        });

        span.addEvent('database_save_started');
        const booking = await this.saveBooking(supplierResult);
        span.addEvent('database_save_completed', { 'booking.id': booking.id });

        // Log completion
        log.info('Booking created successfully',
          { bookingId: booking.id, supplierBookingId: supplierResult.bookingId },
          { requestId: context.requestId, tripId: bookingData.tripId }
        );

        return booking;
      }
    );
  }
}
```

### Trace Context Propagation

```typescript
// lib/monitoring/trace-propagation.ts

import { propagation, context } from '@opentelemetry/api';

export function injectTraceContext(headers: Record<string, string>): void {
  propagation.inject(context.active(), headers);
}

export function extractTraceContext(headers: Record<string, string>): context.Context {
  return propagation.extract(context.active(), headers);
}

// Usage in HTTP requests
export async function tracedFetch(
  url: string,
  options: RequestInit = {},
  serviceName: string
): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  // Inject trace context
  injectTraceContext(headers);

  const response = await fetch(url, { ...options, headers });

  return response;
}
```

---

## Error Tracking

### Sentry Integration

```typescript
// lib/monitoring/sentry.ts

import * as Sentry from '@sentry/nextjs';
import { captureException as sentryCaptureException } from '@sentry/nextjs';

export function initializeSentry() {
  if (process.env.NODE_ENV === 'development') {
    return; // Don't send errors in development
  }

  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV,
    release: process.env.APP_VERSION || '1.0.0',

    // Performance monitoring
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

    // Session replay
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Filter sensitive data
    beforeSend(event, hint) {
      // Don't send events from ignored domains
      const request = event.request;
      if (request?.url) {
        const url = new URL(request.url);
        if (url.hostname === 'localhost') {
          return null;
        }
      }

      // Scrub sensitive data
      if (event.user) {
        delete event.user.email;
        delete event.user.ip_address;
      }

      // Sanitize request headers
      if (event.request?.headers) {
        delete event.request.headers['authorization'];
        delete event.request.headers['cookie'];
        delete event.request.headers['x-api-key'];
      }

      return event;
    },

    // Integrations
    integrations: [
      new Sentry.BrowserTracing(),
      new Sentry.Replay(),
    ],

    // Custom tags
    initialScope: {
      tags: {
        application: 'travel-agency-agent',
      },
    },
  });
}

// Enriched error capture
export interface ErrorContext {
  userId?: string;
  agencyId?: string;
  tripId?: string;
  requestId?: string;
  action?: string;
  [key: string]: unknown;
}

export function captureException(
  error: Error | unknown,
  context: ErrorContext = {}
): void {
  // Add structured context
  Sentry.withScope((scope) => {
    scope.setUser({
      id: context.userId,
    });

    scope.setTags({
      agency_id: context.agencyId,
      trip_id: context.tripId,
      action: context.action,
    });

    scope.setContext('request_context', {
      request_id: context.requestId,
      ...context,
    });

    // Capture breadcrumb for debugging
    scope.addBreadcrumb({
      category: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
      level: 'error',
    });

    sentryCaptureException(error);
  });
}

export function captureMessage(
  message: string,
  level: 'info' | 'warning' | 'error' = 'info',
  context: ErrorContext = {}
): void {
  Sentry.withScope((scope) => {
    scope.setUser({ id: context.userId });
    scope.setTags({
      agency_id: context.agencyId,
      trip_id: context.tripId,
    });
    scope.setContext('message_context', context);
    Sentry.captureMessage(message, level);
  });
}
```

### Error Boundary Integration

```typescript
// components/ErrorBoundary.tsx

'use client';

import { Component, ReactNode } from 'react';
import { captureException } from '@/lib/monitoring/sentry';
import { log } from '@/lib/logging/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: { componentStack: string }) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    const { onError } = this.props;

    // Log to console
    log.error('React Error Boundary caught error', error, {
      componentStack: errorInfo.componentStack,
    });

    // Send to Sentry
    captureException(error, {
      context: 'react_error_boundary',
      componentStack: errorInfo.componentStack,
    });

    // Call custom error handler
    onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>We've been notified of this issue.</p>
          <button onClick={() => window.location.reload()}>Reload Page</button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handler

```typescript
// lib/api/error-handler.ts

import { NextResponse } from 'next/server';
import { captureException } from '@/lib/monitoring/sentry';
import { log } from '@/lib/logging/logger';
import { ApiError } from '@/lib/api/errors';

interface ErrorResponse {
  error: string;
  code?: string;
  details?: unknown;
  requestId: string;
}

export async function handleApiError(
  error: unknown,
  context: { requestId: string; userId?: string; agencyId?: string }
): Promise<NextResponse<ErrorResponse>> {
  const { requestId, userId, agencyId } = context;

  // Known API errors
  if (error instanceof ApiError) {
    log.warn('API error returned',
      { code: error.code, message: error.message, statusCode: error.statusCode },
      { requestId, userId, agencyId }
    );

    return NextResponse.json(
      {
        error: error.message,
        code: error.code,
        requestId,
      },
      { status: error.statusCode }
    );
  }

  // Unexpected errors
  const errorMessage = error instanceof Error ? error.message : 'Unknown error';

  log.error('Unexpected API error',
    error,
    { requestId, userId, agencyId }
  );

  // Send to Sentry
  captureException(error, {
    userId,
    agencyId,
    requestId,
    action: 'api_request',
  });

  return NextResponse.json(
    {
      error: 'An unexpected error occurred',
      requestId,
    },
    { status: 500 }
  );
}
```

---

## Alerting System

### Alert Rules

```typescript
// monitoring/alert-rules.ts

export interface AlertRule {
  id: string;
  name: string;
  severity: 'critical' | 'warning' | 'info';
  condition: string; // PromQL expression
  duration: string; // Alert duration threshold
  labels: Record<string, string>;
  annotations: Record<string, string>;
  actions: AlertAction[];
}

export interface AlertAction {
  type: 'pagerduty' | 'slack' | 'email' | 'webhook';
  config: Record<string, unknown>;
}

export const alertRules: AlertRule[] = [
  // ========================================================================
  // CRITICAL ALERTS
  // ========================================================================

  {
    id: 'high-error-rate',
    name: 'High Error Rate',
    severity: 'critical',
    condition: 'rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05',
    duration: '2m',
    labels: { team: 'platform', category: 'availability' },
    annotations: {
      summary: 'Error rate above 5% for 2 minutes',
      description: 'Error rate is {{ $value | humanizePercentage }}',
      runbook: 'https://docs.internal/runbooks/high-error-rate',
    },
    actions: [
      { type: 'pagerduty', config: { severity: 'critical', routing_key: 'platform-oncall' } },
      { type: 'slack', config: { channel: '#alerts-critical' } },
    ],
  },

  {
    id: 'service-down',
    name: 'Service Down',
    severity: 'critical',
    condition: 'up{job=~"travel-agency.*"} == 0',
    duration: '1m',
    labels: { team: 'platform', category: 'availability' },
    annotations: {
      summary: 'Service {{ $labels.job }} on {{ $labels.instance }} is down',
      description: 'Service has been down for more than 1 minute',
      runbook: 'https://docs.internal/runbooks/service-down',
    },
    actions: [
      { type: 'pagerduty', config: { severity: 'critical', routing_key: 'platform-oncall' } },
      { type: 'slack', config: { channel: '#alerts-critical' } },
    ],
  },

  {
    id: 'database-unavailable',
    name: 'Database Unavailable',
    severity: 'critical',
    condition: 'pg_up{job="postgres"} == 0',
    duration: '30s',
    labels: { team: 'platform', category: 'database' },
    annotations: {
      summary: 'PostgreSQL database is unavailable',
      description: 'Database {{ $labels.instance }} has been down for 30 seconds',
      runbook: 'https://docs.internal/runbooks/database-unavailable',
    },
    actions: [
      { type: 'pagerduty', config: { severity: 'critical', routing_key: 'platform-oncall' } },
      { type: 'slack', config: { channel: '#alerts-critical' } },
    ],
  },

  {
    id: 'payment-failures',
    name: 'Payment Processing Failures',
    severity: 'critical',
    condition: 'rate(payments_processed_total{status="failed"}[5m]) > 10',
    duration: '2m',
    labels: { team: 'payments', category: 'business' },
    annotations: {
      summary: 'High rate of payment failures',
      description: '{{ $value | humanize }} payment failures per second',
      runbook: 'https://docs.internal/runbooks/payment-failures',
    },
    actions: [
      { type: 'pagerduty', config: { severity: 'critical', routing_key: 'payments-oncall' } },
      { type: 'slack', config: { channel: '#alerts-payments' } },
    ],
  },

  // ========================================================================
  // WARNING ALERTS
  // ========================================================================

  {
    id: 'high-latency',
    name: 'High API Latency',
    severity: 'warning',
    condition: 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1',
    duration: '5m',
    labels: { team: 'platform', category: 'performance' },
    annotations: {
      summary: 'p95 latency above 1 second',
      description: 'Current p95: {{ $value | humanizeDuration }}',
      runbook: 'https://docs.internal/runbooks/high-latency',
    },
    actions: [
      { type: 'slack', config: { channel: '#alerts-performance' } },
      { type: 'email', config: { to: 'platform-team@example.com' } },
    ],
  },

  {
    id: 'high-memory-usage',
    name: 'High Memory Usage',
    severity: 'warning',
    condition: 'process_resident_memory_bytes{job="travel-agency-api"} / 1024 / 1024 / 1024 > 2',
    duration: '10m',
    labels: { team: 'platform', category: 'resource' },
    annotations: {
      summary: 'Memory usage above 2GB for 10 minutes',
      description: 'Current usage: {{ $value | humanize }}B',
    },
    actions: [
      { type: 'slack', config: { channel: '#alerts-performance' } },
    ],
  },

  {
    id: 'disk-space-low',
    name: 'Disk Space Low',
    severity: 'warning',
    condition: '(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1',
    duration: '5m',
    labels: { team: 'platform', category: 'infrastructure' },
    annotations: {
      summary: 'Disk space below 10%',
      description: 'Available: {{ $value | humanizePercentage }}',
    },
    actions: [
      { type: 'slack', config: { channel: '#alerts-infra' } },
    ],
  },

  {
    id: 'queue-backlog',
    name: 'Queue Backlog Growing',
    severity: 'warning',
    condition: 'queue_size{queue_name="booking-creation"} > 1000',
    duration: '5m',
    labels: { team: 'platform', category: 'queue' },
    annotations: {
      summary: 'Booking queue backlog above 1000',
      description: 'Queue size: {{ $value }}',
    },
    actions: [
      { type: 'slack', config: { channel: '#alerts-platform' } },
    ],
  },

  {
    id: 'ai-rate-limit',
    name: 'AI API Rate Limiting',
    severity: 'warning',
    condition: 'rate(ai_requests_total{status="rate_limited"}[5m]) > 5',
    duration: '2m',
    labels: { team: 'platform', category: 'external-api' },
    annotations: {
      summary: 'AI API rate limiting detected',
      description: '{{ $value | humanize }} requests/second being rate limited',
    },
    actions: [
      { type: 'slack', config: { channel: '#alerts-platform' } },
    ],
  },

  // ========================================================================
  // INFO ALERTS
  // ========================================================================

  {
    id: 'deployment-detected',
    name: 'New Deployment Detected',
    severity: 'info',
    condition: 'changes(app_version[1m]) > 0',
    duration: '0s',
    labels: { team: 'platform', category: 'deployment' },
    annotations: {
      summary: 'New version deployed: {{ $labels.app_version }}',
      description: 'Deployed at {{ $timestamp }}',
    },
    actions: [
      { type: 'slack', config: { channel: '#deployments' } },
    ],
  },
];
```

### Alertmanager Configuration

```yaml
# monitoring/alertmanager-config.yml

global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true

    # Payment alerts go to payments team
    - match:
        team: payments
      receiver: 'slack-payments'

    # Platform alerts
    - match:
        team: platform
      receiver: 'slack-platform'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        severity: 'critical'
        description: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'slack-payments'
    slack_configs:
      - channel: '#alerts-payments'
        send_resolved: true
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'slack-platform'
    slack_configs:
      - channel: '#alerts-platform'
        send_resolved: true
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  # Inhibit warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']

  # Inhibit alerts if service is down
  - source_match:
      alertname: 'ServiceDown'
    target_match_re:
      alertname: '.*'
    equal: ['instance']
```

### Custom Alert Service

```typescript
// lib/monitoring/alerting.ts

export interface Alert {
  id: string;
  ruleId: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  metadata: Record<string, unknown>;
  timestamp: Date;
  resolved?: boolean;
}

export class AlertService {
  private webhookUrl: string;
  private pagerDutyKey: string;

  async sendAlert(alert: Alert): Promise<void> {
    // Log alert
    log.warn('Alert triggered',
      { alertId: alert.id, ruleId: alert.ruleId, severity: alert.severity },
      { requestId: 'alert-system' }
    );

    // Send to PagerDuty for critical alerts
    if (alert.severity === 'critical') {
      await this.sendToPagerDuty(alert);
    }

    // Send to Slack
    await this.sendToSlack(alert);

    // Store in database for tracking
    await this.storeAlert(alert);
  }

  private async sendToPagerDuty(alert: Alert): Promise<void> {
    const response = await fetch('https://events.pagerduty.com/v2/enqueue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        routing_key: this.pagerDutyKey,
        event_action: 'trigger',
        payload: {
          summary: alert.title,
          severity: alert.severity,
          source: 'travel-agency-agent',
          timestamp: alert.timestamp.toISOString(),
          custom_details: alert.metadata,
        },
        dedup_key: alert.id,
      }),
    });

    if (!response.ok) {
      throw new Error(`PagerDuty API error: ${response.statusText}`);
    }
  }

  private async sendToSlack(alert: Alert): Promise<void> {
    const color = {
      critical: '#ff0000',
      warning: '#ffaa00',
      info: '#0066ff',
    }[alert.severity];

    const response = await fetch(this.webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        attachments: [
          {
            color,
            title: alert.title,
            text: alert.description,
            fields: Object.entries(alert.metadata).map(([key, value]) => ({
              title: key,
              value: String(value),
              short: true,
            })),
            footer: 'Travel Agency Agent',
            ts: Math.floor(alert.timestamp.getTime() / 1000),
          },
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`Slack webhook error: ${response.statusText}`);
    }
  }

  private async storeAlert(alert: Alert): Promise<void> {
    await db.alerts.create({
      data: {
        id: alert.id,
        ruleId: alert.ruleId,
        severity: alert.severity,
        title: alert.title,
        description: alert.description,
        metadata: alert.metadata,
        triggeredAt: alert.timestamp,
      },
    });
  }

  async resolveAlert(alertId: string): Promise<void> {
    await db.alerts.update({
      where: { id: alertId },
      data: { resolvedAt: new Date(), resolved: true },
    });

    log.info('Alert resolved', { alertId });
  }
}
```

---

## Dashboard Architecture

### Grafana Dashboard Definition

```typescript
// monitoring/dashboards/overview-dashboard.json

{
  "dashboard": {
    "title": "Travel Agency Agent - Overview",
    "tags": ["travel-agency", "overview"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{agency_id=\"$agency\"}[5m])) by (status_code)",
            "legendFormat": "{{status_code}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status_code=~\"5..\", agency_id=\"$agency\"}[5m])) / sum(rate(http_requests_total{agency_id=\"$agency\"}[5m]))",
            "legendFormat": "Error Rate"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": { "params": [0.05], "type": "gt" },
              "operator": { "type": "and" },
              "query": { "params": ["A", "5m", "now"] },
              "reducer": { "params": [], "type": "avg" },
              "type": "query"
            }
          ]
        }
      },
      {
        "id": 3,
        "title": "Latency (percentiles)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{agency_id=\"$agency\"}[5m])) by (le))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{agency_id=\"$agency\"}[5m])) by (le))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{agency_id=\"$agency\"}[5m])) by (le))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "id": 4,
        "title": "Active Trips by Stage",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(trips_by_stage{agency_id=\"$agency\"}) by (stage)"
          }
        ]
      },
      {
        "id": 5,
        "title": "Bookings Today",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(bookings_created_total{agency_id=\"$agency\"}[1d]))"
          }
        ]
      },
      {
        "id": 6,
        "title": "Payment Success Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "avg(payment_success_rate{agency_id=\"$agency\"}) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                { "color": "red", "value": 0 },
                { "color": "yellow", "value": 80 },
                { "color": "green", "value": 95 }
              ]
            }
          }
        }
      }
    ]
  }
}
```

### Dashboard Service

```typescript
// lib/monitoring/dashboard.ts

export interface DashboardConfig {
  id: string;
  name: string;
  description: string;
  panels: PanelConfig[];
  refreshInterval?: string;
  timeRange?: string;
}

export interface PanelConfig {
  id: string;
  title: string;
  type: 'graph' | 'stat' | 'table' | 'heatmap' | 'gauge';
  queries: QueryConfig[];
  visualization?: VisualizationConfig;
  alert?: AlertConfig;
}

export interface QueryConfig {
  expr: string; // PromQL expression
  legendFormat?: string;
  interval?: string;
}

export class DashboardService {
  async createDashboard(config: DashboardConfig): Promise<string> {
    const response = await fetch(`${process.env.GRAFANA_URL}/api/dashboards/db`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.GRAFANA_API_KEY}`,
      },
      body: JSON.stringify({
        dashboard: this.toGrafanaFormat(config),
        overwrite: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create dashboard: ${response.statusText}`);
    }

    const data = await response.json();
    return data.url;
  }

  private toGrafanaFormat(config: DashboardConfig) {
    return {
      title: config.name,
      description: config.description,
      refresh: config.refreshInterval || '1m',
      time: {
        from: config.timeRange || 'now-1h',
        to: 'now',
      },
      panels: config.panels.map((panel) => ({
        id: panel.id,
        title: panel.title,
        type: panel.type,
        targets: panel.queries.map((query) => ({
          expr: query.expr,
          legendFormat: query.legendFormat,
          interval: query.interval || '30s',
        })),
        ...this.visualizationConfig(panel),
      })),
    };
  }

  private visualizationConfig(panel: PanelConfig) {
    switch (panel.type) {
      case 'graph':
        return {
          gridPos: { h: 8, w: 12, x: 0, y: 0 },
          fieldConfig: {
            defaults: {
              unit: 'short',
            },
          },
        };

      case 'stat':
        return {
          gridPos: { h: 4, w: 6, x: 0, y: 0 },
          fieldConfig: {
            defaults: {
              unit: 'short',
              thresholds: panel.visualization?.thresholds,
            },
          },
        };

      case 'gauge':
        return {
          gridPos: { h: 8, w: 6, x: 0, y: 0 },
          fieldConfig: {
            defaults: {
              unit: panel.visualization?.unit || 'short',
              min: panel.visualization?.min ?? 0,
              max: panel.visualization?.max ?? 100,
              thresholds: {
                mode: 'absolute',
                steps: panel.visualization?.thresholds,
              },
            },
          },
        };

      default:
        return {};
    }
  }
}
```

### Custom Dashboard Component

```typescript
// components/dashboard/MetricsDashboard.tsx

'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface MetricCardProps {
  title: string;
  query: string;
  format?: 'number' | 'percent' | 'duration';
  threshold?: { value: number; color: string }[];
}

function MetricCard({ title, query, format = 'number', threshold }: MetricCardProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['metric', query],
    queryFn: async () => {
      const response = await fetch(`/api/metrics/query?query=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Failed to fetch metric');
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) return <Card className="h-32 animate-pulse" />;

  const value = data?.data?.result?.[0]?.value?.[1];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{formatValue(value, format)}</div>
      </CardContent>
    </Card>
  );
}

function formatValue(value: string, format: string): string {
  const num = parseFloat(value);

  switch (format) {
    case 'percent':
      return `${(num * 100).toFixed(1)}%`;
    case 'duration':
      return `${num.toFixed(2)}s`;
    default:
      return num.toLocaleString();
  }
}

export function MetricsDashboard() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        title="Active Trips"
        query="sum(trips_by_stage)"
      />
      <MetricCard
        title="Bookings Today"
        query="sum(increase(bookings_created_total[1d]))"
      />
      <MetricCard
        title="Success Rate"
        query="avg(payment_success_rate)"
        format="percent"
        threshold={[
          { value: 0, color: 'red' },
          { value: 95, color: 'yellow' },
          { value: 98, color: 'green' },
        ]}
      />
      <MetricCard
        title="p95 Latency"
        query="histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"
        format="duration"
      />
    </div>
  );
}
```

---

## Performance Monitoring

### APM Integration

```typescript
// lib/monitoring/apm.ts

import { ProfilingIntegration } from '@sentry/profiling-node';

export function initializeProfiling() {
  if (process.env.NODE_ENV !== 'production') {
    return;
  }

  // Enable continuous profiling
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    integrations: [
      new ProfilingIntegration(),
    ],
    profilesSampleRate: 1.0,
  });
}

// Custom performance tracking
export class PerformanceTracker {
  private metrics: Map<string, number[]> = new Map();

  recordTiming(name: string, duration: number): void {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    this.metrics.get(name)!.push(duration);
  }

  getMetrics(name: string): { avg: number; p95: number; p99: number; min: number; max: number } {
    const timings = this.metrics.get(name) || [];
    if (timings.length === 0) {
      return { avg: 0, p95: 0, p99: 0, min: 0, max: 0 };
    }

    const sorted = [...timings].sort((a, b) => a - b);
    return {
      avg: timings.reduce((a, b) => a + b, 0) / timings.length,
      p95: sorted[Math.floor(timings.length * 0.95)],
      p99: sorted[Math.floor(timings.length * 0.99)],
      min: sorted[0],
      max: sorted[sorted.length - 1],
    };
  }

  async track<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      return await fn();
    } finally {
      const duration = performance.now() - start;
      this.recordTiming(name, duration);
    }
  }
}

export const perfTracker = new PerformanceTracker();
```

### Database Query Monitoring

```typescript
// lib/database/query-monitor.ts

import { databaseQueryDuration } from '@/lib/monitoring/metrics';

export class QueryMonitor {
  static async trackQuery<T>(
    operation: string,
    table: string,
    agencyId: string,
    queryFn: () => Promise<T>
  ): Promise<T> {
    const start = Date.now();

    try {
      const result = await queryFn();
      const duration = (Date.now() - start) / 1000;

      databaseQueryDuration.observe({
        operation,
        table,
        agency_id: agencyId,
      }, duration);

      // Alert on slow queries
      if (duration > 1) {
        log.warn('Slow query detected',
          { operation, table, duration },
          { agencyId }
        );
      }

      return result;
    } catch (error) {
      const duration = (Date.now() - start) / 1000;

      databaseQueryDuration.observe({
        operation,
        table,
        agency_id: agencyId,
      }, duration);

      throw error;
    }
  }
}

// Usage example
export class TripRepository {
  async findById(id: string, agencyId: string) {
    return QueryMonitor.trackQuery(
      'select',
      'trips',
      agencyId,
      () => db.trip.findUnique({ where: { id, agencyId } })
    );
  }
}
```

### External API Monitoring

```typescript
// lib/monitoring/external-api.ts

import { externalApiDuration } from '@/lib/monitoring/metrics';

export interface ExternalApiCallOptions {
  service: string;
  operation: string;
  agencyId: string;
  timeout?: number;
  retries?: number;
}

export class ExternalApiMonitor {
  static async call<T>(
    options: ExternalApiCallOptions,
    callFn: () => Promise<T>
  ): Promise<T> {
    const { service, operation, agencyId, timeout = 30000, retries = 3 } = options;

    for (let attempt = 0; attempt < retries; attempt++) {
      const start = Date.now();

      try {
        const result = await Promise.race([
          callFn(),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Timeout')), timeout)
          ),
        ]);

        const duration = (Date.now() - start) / 1000;

        externalApiDuration.observe({
          service,
          operation,
          agency_id: agencyId,
        }, duration);

        return result;
      } catch (error) {
        const duration = (Date.now() - start) / 1000;

        externalApiDuration.observe({
          service,
          operation,
          agency_id: agencyId,
        }, duration);

        if (attempt === retries - 1) {
          log.error('External API call failed after retries',
            error,
            { service, operation, attempts: attempt + 1 },
            { agencyId }
          );
          throw error;
        }

        // Exponential backoff
        await new Promise((resolve) => setTimeout(resolve, Math.pow(2, attempt) * 100));
      }
    }

    throw new Error('Unexpected error in API call retry logic');
  }
}
```

---

## Incident Response Integration

### Incident Creation from Alerts

```typescript
// lib/monitoring/incident.ts

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'investigating' | 'resolved' | 'closed';
  alertId: string;
  assignee?: string;
  createdAt: Date;
  resolvedAt?: Date;
  timeline: IncidentEvent[];
}

export interface IncidentEvent {
  timestamp: Date;
  type: 'note' | 'status_change' | 'assignment';
  author: string;
  content: string;
}

export class IncidentService {
  async createFromAlert(alert: Alert): Promise<Incident> {
    const incident = await db.incident.create({
      data: {
        title: alert.title,
        description: alert.description,
        severity: this.mapSeverity(alert.severity),
        status: 'open',
        alertId: alert.id,
        timeline: {
          create: {
            type: 'status_change',
            author: 'system',
            content: `Incident created from alert: ${alert.ruleId}`,
            timestamp: new Date(),
          },
        },
      },
    });

    // Notify on-call team
    await this.notifyIncidentCreated(incident);

    return incident;
  }

  async addNote(incidentId: string, note: string, author: string): Promise<void> {
    await db.incidentEvent.create({
      data: {
        incidentId,
        type: 'note',
        author,
        content: note,
        timestamp: new Date(),
      },
    });
  }

  async updateStatus(incidentId: string, status: Incident['status'], author: string): Promise<void> {
    await db.incident.update({
      where: { id: incidentId },
      data: { status },
    });

    await db.incidentEvent.create({
      data: {
        incidentId,
        type: 'status_change',
        author,
        content: `Status changed to ${status}`,
        timestamp: new Date(),
      },
    });

    if (status === 'resolved') {
      await this.notifyIncidentResolved(incidentId);
    }
  }

  private async notifyIncidentCreated(incident: Incident): Promise<void> {
    // Create Slack incident channel
    // Post to PagerDuty
    // Send email to on-call team
  }

  private async notifyIncidentResolved(incidentId: string): Promise<void> {
    // Update Slack channel
    // Resolve PagerDuty incident
    // Send post-mortem template
  }

  private mapSeverity(alertSeverity: string): Incident['severity'] {
    const mapping = {
      critical: 'critical',
      warning: 'high',
      info: 'medium',
    };
    return mapping[alertSeverity] || 'low';
  }
}
```

### Runbook Automation

```typescript
// lib/monitoring/runbook.ts

export interface RunbookAction {
  name: string;
  description: string;
  execute: () => Promise<void>;
}

export class RunbookExecutor {
  private runbooks: Map<string, RunbookAction[]> = new Map();

  register(ruleId: string, actions: RunbookAction[]): void {
    this.runbooks.set(ruleId, actions);
  }

  async execute(ruleId: string): Promise<void> {
    const actions = this.runbooks.get(ruleId);
    if (!actions) {
      log.warn(`No runbook found for rule: ${ruleId}`);
      return;
    }

    log.info(`Executing runbook for rule: ${ruleId}`, { actionCount: actions.length });

    for (const action of actions) {
      try {
        log.info(`Running action: ${action.name}`);
        await action.execute();
      } catch (error) {
        log.error(`Runbook action failed: ${action.name}`, error);
      }
    }
  }
}

export const runbookExecutor = new RunbookExecutor();

// Example runbook registration
runbookExecutor.register('high-error-rate', [
  {
    name: 'capture_recent_errors',
    description: 'Fetch recent error logs from Loki',
    execute: async () => {
      // Query Loki for recent errors
    },
  },
  {
    name: 'check_deployment_status',
    description: 'Check if a recent deployment occurred',
    execute: async () => {
      // Check deployment history
    },
  },
  {
    name: 'enable_verbose_logging',
    description: 'Temporarily enable verbose logging',
    execute: async () => {
      // Update feature flag for verbose logging
    },
  },
]);
```

---

## Summary

The Monitoring & Observability system provides comprehensive visibility into:

- **Metrics**: Time-series data for all system components
- **Logging**: Structured, searchable logs with context
- **Tracing**: Distributed tracing for request flows
- **Error Tracking**: Aggregated error reporting with Sentry
- **Alerting**: Proactive notification of issues
- **Dashboards**: Real-time visualization of key metrics
- **APM**: Performance profiling and optimization insights

### Key Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **Metrics** | Time-series data | Prometheus |
| **Logging** | Log aggregation | ELK / Loki |
| **Tracing** | Request flows | OpenTelemetry + Jaeger |
| **Errors** | Error tracking | Sentry |
| **Dashboards** | Visualization | Grafana |
| **Alerting** | Notification | Alertmanager + PagerDuty |

### Next Steps

See [DEVOPS_04_SCALING_DEEP_DIVE.md](./DEVOPS_04_SCALING_DEEP_DIVE.md) for:
- Auto-scaling strategies
- Load balancing
- Caching architectures
- Performance optimization

---

**Last Updated:** 2026-04-25
