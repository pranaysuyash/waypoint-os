# Performance & Scalability Part 5: Monitoring & Alerting

> APM integration, metrics, dashboards, and incident response

**Series:** Performance & Scalability
**Previous:** [Part 4: Scalability Patterns](./PERFORMANCE_SCALABILITY_04_SCALING.md)
**Next:** N/A (Series Complete)

---

## Table of Contents

1. [Monitoring Strategy](#monitoring-strategy)
2. [APM Integration](#apm-integration)
3. [Custom Metrics](#custom-metrics)
4. [Dashboards](#dashboards)
5. [Alerting Rules](#alerting-rules)
6. [Incident Response](#incident-response)

---

## Monitoring Strategy

### Monitoring Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Business Metrics                         │
│  Bookings, Revenue, Conversion Rate, User Satisfaction      │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│                    Application Metrics                      │
│  Requests, Errors, Latency, Saturation, Custom Events      │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Metrics                    │
│  CPU, Memory, Disk, Network, Database Connections           │
└─────────────────────────────────────────────────────────────┘
```

### Signal-to-Noise Ratio

```typescript
// monitoring/signal-classification.ts

interface SignalClassification {
  type: 'golden' | 'silver' | 'bronze' | 'noise';
  definition: string;
  alert: boolean;
  dashboard: string;
}

export const signalCategories: SignalClassification[] = [
  // Golden signals - directly impact user experience
  {
    type: 'golden',
    definition: 'Latency, Traffic, Errors, Saturation',
    alert: true,
    dashboard: 'main-overview',
  },

  // Silver signals - important but less direct
  {
    type: 'silver',
    definition: 'Cache hit rate, Queue depth, DB pool utilization',
    alert: true,
    dashboard: 'infrastructure',
  },

  // Bronze signals - useful for debugging
  {
    type: 'bronze',
    definition: 'Process counts, Thread states, GC pauses',
    alert: false,
    dashboard: 'debugging',
  },

  // Noise - low value, ignore
  {
    type: 'noise',
    definition: 'Individual request logs, Debug spans',
    alert: false,
    dashboard: null,
  },
];
```

---

## APM Integration

### DataDog Setup

```typescript
// lib/monitoring/datadog.ts

import { tracer, metrics } from 'dd-trace';

// Initialize tracer
tracer.init({
  service: 'travel-agency-api',
  env: process.env.NODE_ENV,
  logInjection: true,
  analytics: true,
  sampleRate: 1.0, // 100% tracing in development
});

// Custom metrics
export const ddMetrics = {
  // Count bookings
  countBooking: (status: string) => {
    metrics.increment('booking.created', 1, [`status:${status}`]);
  },

  // Track booking value
  recordBookingValue: (amount: number, currency: string) => {
    metrics.gauge('booking.value', amount, [`currency:${currency}`]);
  },

  // Track API latency
  recordAPILatency: (endpoint: string, duration: number) => {
    metrics.histogram('api.latency', duration, [`endpoint:${endpoint}`]);
  },

  // Track database query time
  recordQueryTime: (table: string, duration: number) => {
    metrics.histogram('db.query.duration', duration, [`table:${table}`]);
  },

  // Track cache performance
  recordCacheHit: (key: string) => {
    metrics.increment('cache.hit', 1, [`key:${key}`]);
  },

  recordCacheMiss: (key: string) => {
    metrics.increment('cache.miss', 1, [`key:${key}`]);
  },
};
```

### Distributed Tracing

```typescript
// lib/monitoring/tracing.ts

import { span, SpanOptions } from 'dd-trace';

// Tracing decorator for API routes
export function traceRoute(operationName: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const options: SpanOptions = {
        service: 'travel-agency-api',
        resource: operationName,
        tags: {
          'resource.name': operationName,
          'span.type': 'web',
        },
      };

      return span(options, async () => {
        const start = Date.now();

        try {
          const result = await originalMethod.apply(this, args);

          // Record success metric
          ddMetrics.recordAPILatency(operationName, Date.now() - start);

          return result;
        } catch (error) {
          // Record error
          tracer.setTags({
            'error.type': error.constructor.name,
            'error.message': error.message,
          });

          throw error;
        }
      });
    };

    return descriptor;
  };
}

// Usage
export class BookingController {
  @traceRoute('booking.create')
  async createBooking(req: Request, res: Response) {
    // Method implementation
  }

  @traceRoute('booking.get')
  async getBooking(req: Request, res: Response) {
    // Method implementation
  }
}
```

---

## Custom Metrics

### Business Metrics

```typescript
// lib/metrics/business.ts

interface BookingMetrics {
  bookingId: string;
  userId: string;
  amount: number;
  currency: string;
  destination: string;
  status: string;
  source: 'web' | 'mobile' | 'api';
}

export class BusinessMetrics {
  // Track booking funnel
  trackFunnelStage(stage: 'search' | 'view' | 'quote' | 'booking' | 'payment', metadata?: any) {
    metrics.increment('funnel.stage', 1, [`stage:${stage}`, ...this.formatTags(metadata)]);
  }

  // Track booking conversion
  trackBooking(booking: BookingMetrics) {
    metrics.increment('booking.created', 1, [
      `status:${booking.status}`,
      `source:${booking.source}`,
      `destination:${booking.destination}`,
    ]);

    metrics.gauge('booking.value', booking.amount, [
      `currency:${booking.currency}`,
    ]);
  }

  // Track payment success/failure
  trackPayment(success: boolean, amount: number, method: string) {
    metrics.increment('payment.attempt', 1, [`method:${method}`]);
    metrics.increment(success ? 'payment.success' : 'payment.failure', 1, [
      `method:${method}`,
    ]);

    if (success) {
      metrics.increment('payment.revenue', amount, [`method:${method}`]);
    }
  }

  // Track user engagement
  trackEngagement(userId: string, action: string, metadata?: any) {
    metrics.increment('user.engagement', 1, [
      `action:${action}`,
      ...this.formatTags(metadata),
    ]);
  }

  // Track search queries
  trackSearch(destination: string, resultsCount: number, duration: number) {
    metrics.histogram('search.duration', duration, [`destination:${destination}`]);
    metrics.gauge('search.results', resultsCount, [`destination:${destination}`]);
  }

  private formatTags(metadata?: any): string[] {
    if (!metadata) return [];

    return Object.entries(metadata).map(([key, value]) => `${key}:${value}`);
  }
}

export const businessMetrics = new BusinessMetrics();
```

### Infrastructure Metrics

```typescript
// lib/metrics/infrastructure.ts

export class InfrastructureMetrics {
  // Database metrics
  trackDatabaseQuery(table: string, operation: string, duration: number) {
    metrics.histogram('db.query.duration', duration, [
      `table:${table}`,
      `operation:${operation}`,
    ]);
  }

  trackConnectionPool(pool: string, active: number, idle: number) {
    metrics.gauge('db.pool.active', active, [`pool:${pool}`]);
    metrics.gauge('db.pool.idle', idle, [`pool:${pool}`]);
  }

  // Cache metrics
  trackCacheOperation(operation: 'hit' | 'miss' | 'set' | 'delete', key: string) {
    metrics.increment(`cache.${operation}`, 1, [`key:${this.sanitizeKey(key)}`]);
  }

  trackCacheMemory(used: number, max: number) {
    metrics.gauge('cache.memory.used', used);
    metrics.gauge('cache.memory.max', max);
    metrics.gauge('cache.memory.utilization', (used / max) * 100);
  }

  // Queue metrics
  trackQueueJob(queue: string, status: 'queued' | 'processing' | 'completed' | 'failed') {
    metrics.increment('queue.job', 1, [`queue:${queue}`, `status:${status}`]);
  }

  trackQueueDepth(queue: string, depth: number) {
    metrics.gauge('queue.depth', depth, [`queue:${queue}`]);
  }

  // API metrics
  trackAPICall(endpoint: string, method: string, statusCode: number, duration: number) {
    metrics.histogram('api.request.duration', duration, [
      `endpoint:${endpoint}`,
      `method:${method}`,
      `status:${statusCode}`,
    ]);

    metrics.increment('api.request.count', 1, [
      `endpoint:${endpoint}`,
      `method:${method}`,
      `status:${statusCode}`,
    ]);
  }

  private sanitizeKey(key: string): string {
    // Remove sensitive data from cache keys
    return key.replace(/token[^a-z]/gi, 'token').replace(/session[^a-z]/gi, 'session');
  }
}

export const infraMetrics = new InfrastructureMetrics();
```

---

## Dashboards

### Main Overview Dashboard

```typescript
// dashboards/overview.json

export const overviewDashboard = {
  name: 'Travel Agency - Overview',
  description: 'High-level view of system health and business metrics',

  templates: [
    // Key metrics at top
    {
      type: 'query_value',
      title: 'Requests/min',
      query: 'sum:requests{*}.as_rate() * 60',
      precision: 0,
    },
    {
      type: 'query_value',
      title: 'Error Rate',
      query: 'sum:errors{*}.as_rate() / sum:requests{*}.as_rate() * 100',
      precision: 2,
      unit: '%',
      alert: { operator: '>', value: 1 },
    },
    {
      type: 'query_value',
      title: 'P95 Latency',
      query: 'avg:api.latency{*}.p95()',
      precision: 0,
      unit: 'ms',
      alert: { operator: '>', value: 500 },
    },
    {
      type: 'query_value',
      title: 'Active Bookings',
      query: 'sum:bookings.active',
      precision: 0,
    },

    // Time series graphs
    {
      type: 'timeseries',
      title: 'Request Rate',
      queries: [
        { query: 'sum:requests{*}.as_rate()', name: 'Total' },
        { query: 'sum:requests{endpoint:/api/bookings/*}.as_rate()', name: 'Bookings' },
        { query: 'sum:requests{endpoint:/api/search/*}.as_rate()', name: 'Search' },
      ],
    },
    {
      type: 'timeseries',
      title: 'Error Rate by Service',
      queries: [
        { query: 'avg:errors{service:api}.as_rate() * 100', name: 'API' },
        { query: 'avg:errors{service:worker}.as_rate() * 100', name: 'Workers' },
        { query: 'avg:errors{service:web}.as_rate() * 100', name: 'Web' },
      ],
    },
    {
      type: 'timeseries',
      title: 'Latency Distribution',
      queries: [
        { query: 'avg:api.latency{*}.p50()', name: 'P50' },
        { query: 'avg:api.latency{*}.p95()', name: 'P95' },
        { query: 'avg:api.latency{*}.p99()', name: 'P99' },
      ],
    },

    // Business metrics
    {
      type: 'timeseries',
      title: 'Booking Rate',
      queries: [
        { query: 'sum:bookings.created{*}.as_rate() * 60', name: 'Bookings/min' },
        { query: 'sum:payments.success{*}.as_rate() * 60', name: 'Payments/min' },
      ],
    },
    {
      type: 'query_value',
      title: 'Revenue (Today)',
      query: 'sum:payment.revenue{*}.rollup(sum, 86400)',
      precision: 2,
      unit: '$',
    },

    // Infrastructure
    {
      type: 'timeseries',
      title: 'CPU Utilization',
      query: 'avg:system.cpu.usage{*} by {host}',
    },
    {
      type: 'timeseries',
      title: 'Memory Utilization',
      query: 'avg:system.mem.used{*} by {host}',
    },
  ],
};
```

### Service Dashboard

```typescript
// dashboards/service.json

export const serviceDashboard = {
  name: 'Service - Booking API',
  description: 'Detailed metrics for the booking service',

  templates: [
    // RED method
    {
      type: 'timeseries',
      title: 'Rate (Requests/sec)',
      query: 'sum:requests{service:booking-api}.as_rate()',
    },
    {
      type: 'timeseries',
      title: 'Errors (Error rate)',
      query: 'sum:errors{service:booking-api}.as_rate() / sum:requests{service:booking-api}.as_rate() * 100',
    },
    {
      type: 'timeseries',
      title: 'Duration (P95 latency)',
      query: 'avg:api.latency{service:booking-api}.p95()',
    },

    // Breakdowns
    {
      type: 'timeseries',
      title: 'Requests by Endpoint',
      query: 'sum:requests{service:booking-api}.as_rate() by {endpoint}',
    },
    {
      type: 'timeseries',
      title: 'Latency by Endpoint',
      query: 'avg:api.latency{service:booking-api}.p95() by {endpoint}',
    },
    {
      type: 'timeseries',
      title: 'Errors by Endpoint',
      query: 'sum:errors{service:booking-api}.as_rate() by {endpoint}',
    },

    // Dependencies
    {
      type: 'list',
      title: 'Database Queries',
      query: 'avg:db.query.duration{service:booking-api}.p95() by {table}',
    },
    {
      type: 'list',
      title: 'Cache Performance',
      query: 'avg:cache.hit_rate{service:booking-api} by {key_prefix}',
    },
  ],
};
```

---

## Alerting Rules

### Alert Severity Levels

```typescript
// monitoring/alerts/severity.ts

export enum AlertSeverity {
  CRITICAL = 'critical',  // Wake someone up immediately
  HIGH = 'high',          // Page within 15 minutes
  MEDIUM = 'medium',      // Slack message
  LOW = 'low',            // Email / Log
}

interface AlertRule {
  name: string;
  query: string;
  condition: string;
  threshold: number;
  severity: AlertSeverity;
  duration: number;       // minutes before alerting
  notification: string[];
  runbook: string;
}

export const alertRules: AlertRule[] = [
  // Critical alerts - immediate action required
  {
    name: 'High Error Rate',
    query: 'sum:errors{*}.as_rate() / sum:requests{*}.as_rate() * 100',
    condition: '>',
    threshold: 5,
    severity: AlertSeverity.CRITICAL,
    duration: 2,
    notification: ['pagerduty'],
    runbook: '/runbooks/high-error-rate.md',
  },
  {
    name: 'Service Down',
    query: 'sum:requests{*}.as_rate()',
    condition: '<',
    threshold: 1,
    severity: AlertSeverity.CRITICAL,
    duration: 1,
    notification: ['pagerduty'],
    runbook: '/runbooks/service-down.md',
  },
  {
    name: 'Database Connection Exhausted',
    query: 'avg:db.pool.available{db:primary}',
    condition: '<=',
    threshold: 2,
    severity: AlertSeverity.CRITICAL,
    duration: 2,
    notification: ['pagerduty'],
    runbook: '/runbooks/db-pool-exhausted.md',
  },

  // High alerts - investigate soon
  {
    name: 'Elevated Error Rate',
    query: 'sum:errors{*}.as_rate() / sum:requests{*}.as_rate() * 100',
    condition: '>',
    threshold: 1,
    severity: AlertSeverity.HIGH,
    duration: 10,
    notification: ['slack'],
    runbook: '/runbooks/elevated-error-rate.md',
  },
  {
    name: 'High Latency',
    query: 'avg:api.latency{*}.p95()',
    condition: '>',
    threshold: 1000,
    severity: AlertSeverity.HIGH,
    duration: 10,
    notification: ['slack'],
    runbook: '/runbooks/high-latency.md',
  },
  {
    name: 'Low Cache Hit Rate',
    query: 'avg:cache.hit_rate{*}',
    condition: '<',
    threshold: 0.5,
    severity: AlertSeverity.HIGH,
    duration: 30,
    notification: ['slack'],
    runbook: '/runbooks/low-cache-hit.md',
  },

  // Medium alerts - monitor
  {
    name: 'Elevated Latency',
    query: 'avg:api.latency{*}.p95()',
    condition: '>',
    threshold: 500,
    severity: AlertSeverity.MEDIUM,
    duration: 15,
    notification: ['slack'],
    runbook: '/runbooks/elevated-latency.md',
  },
  {
    name: 'Queue Depth High',
    query: 'avg:queue.depth{*}',
    condition: '>',
    threshold: 1000,
    severity: AlertSeverity.MEDIUM,
    duration: 15,
    notification: ['slack'],
    runbook: '/runbooks/queue-depth.md',
  },

  // Low alerts - informational
  {
    name: 'Planned Maintenance',
    query: 'sum:requests{*}.as_rate()',
    condition: '>',
    threshold: 0,
    severity: AlertSeverity.LOW,
    duration: 0,
    notification: ['email'],
    runbook: null,
  },
];
```

### SLO-Based Alerting

```typescript
// monitoring/alerts/slo.ts

interface SLO {
  name: string;
  target: number;       // 99.9 for 99.9%
  window: string;       // 7d, 30d
  errorBudgetRemaining: number;
  alertThreshold: number;
}

export const serviceSLOs: SLO[] = [
  {
    name: 'API Availability',
    target: 99.9,
    window: '30d',
    errorBudgetRemaining: 100,
    alertThreshold: 10, // Alert at 10% error budget remaining
  },
  {
    name: 'API Latency',
    target: 95,        // 95% of requests under p95 threshold
    window: '7d',
    errorBudgetRemaining: 100,
    alertThreshold: 20,
  },
  {
    name: 'Booking Success Rate',
    target: 99.5,
    window: '7d',
    errorBudgetRemaining: 100,
    alertThreshold: 15,
  },
];

// Calculate error budget
export function calculateErrorBudget(
  slo: SLO,
  actualValue: number,
  totalRequests: number
): {
  budgetConsumed: number;
  budgetRemaining: number;
  status: 'healthy' | 'warning' | 'burning';
} {
  const targetValue = slo.target;
  const allowedErrors = (totalRequests * (100 - targetValue)) / 100;
  const actualErrors = (totalRequests * (100 - actualValue)) / 100;

  const budgetConsumed = (actualErrors / allowedErrors) * 100;
  const budgetRemaining = 100 - budgetConsumed;

  let status: 'healthy' | 'warning' | 'burning' = 'healthy';
  if (budgetRemaining < slo.alertThreshold) {
    status = 'burning';
  } else if (budgetRemaining < slo.alertThreshold * 2) {
    status = 'warning';
  }

  return { budgetConsumed, budgetRemaining, status };
}
```

---

## Incident Response

### On-Call Rotation

```typescript
// monitoring/oncall/rotation.ts

interface OnCallSchedule {
  primary: string;      // Currently on call
  secondary: string;    // Backup
  escalation: string[]; // Escalation path
  timezone: string;
  handoff: string;      // When handoff occurs
}

export const onCallConfig = {
  // Rotation schedule
  rotation: {
    frequency: 'weekly',      // Weekly rotation
    dayOfWeek: 'monday',      // Handoff on Monday
    time: '09:00',            // 9 AM
    timezone: 'America/New_York',
  },

  // Notification channels
  channels: {
    critical: ['pagerduty', 'sms', 'call'],
    high: ['pagerduty', 'slack'],
    medium: ['slack'],
    low: ['email'],
  },

  // Escalation policy
  escalation: [
    { delay: 15, unit: 'minutes', action: 'page secondary' },
    { delay: 30, unit: 'minutes', action: 'page manager' },
    { delay: 60, unit: 'minutes', action: 'page cto' },
  ],

  // Status page updates
  statusPage: {
    url: 'status.travelagency.com',
    autoUpdate: true,
    severityMapping: {
      critical: 'major-outage',
      high: 'degraded-performance',
      medium: 'partial-outage',
      low: 'operational',
    },
  },
};
```

### Incident Runbook Template

```markdown
# Runbook: [Title]

## Description
Brief description of this incident type.

## Detection
- Alert: [Alert name]
- Dashboard: [Link to relevant dashboard]
- Typical symptoms: [What to look for]

## Initial Diagnosis
1. Check [service/log/dashboard]
2. Run [diagnostic command]
3. Look for [common indicators]

## Resolution Steps
1. [First step to try]
2. [Second step if first doesn't work]
3. [Escalation if needed]

## Verification
- [ ] Symptom resolved
- [ ] Alert cleared
- [ ] Metrics returned to normal

## Follow-up
- Create incident retrospective if:
  - Customer impact
  - Unexpected behavior
  - Action items identified

## Related
- Runbooks: [Links to related runbooks]
- Docs: [Links to relevant documentation]
- Contacts: [Who to contact for help]
```

### Incident Severity Levels

```typescript
// monitoring/incidents/severity.ts

export enum IncidentSeverity {
  SEV1 = 'sev1', // Complete service outage
  SEV2 = 'sev2', // Major functionality broken
  SEV3 = 'sev3', // Minor functionality broken
  SEV4 = 'sev4', // Issues with workarounds
}

export const severityDefinitions = {
  SEV1: {
    name: 'Critical',
    description: 'Service completely down or major data loss',
    impact: 'All users affected',
    responseTime: 15, // minutes
    communication: 'Immediate public update',
    examples: [
      'Booking system completely down',
      'Payment processing failed',
      'Data breach confirmed',
    ],
  },

  SEV2: {
    name: 'High',
    description: 'Major feature broken but workaround exists',
    impact: 'Many users affected',
    responseTime: 30,
    communication: 'Update within 1 hour',
    examples: [
      'Search not working',
      'Login issues for some users',
      'Significant performance degradation',
    ],
  },

  SEV3: {
    name: 'Medium',
    description: 'Minor feature broken',
    impact: 'Some users affected',
    responseTime: 60,
    communication: 'Update within 4 hours',
    examples: [
      'Email notifications delayed',
      'Reports not generating',
      'Single region issues',
    ],
  },

  SEV4: {
    name: 'Low',
    description: 'Cosmetic issues or internal tooling',
    impact: 'Internal or minimal user impact',
    responseTime: 240,
    communication: 'Next business day',
    examples: [
      'Typos in UI',
      'Admin dashboard slow',
      'Internal monitoring alerts',
    ],
  },
};
```

### Incident Lifecycle

```typescript
// monitoring/incidents/lifecycle.ts

export interface Incident {
  id: string;
  severity: IncidentSeverity;
  title: string;
  description: string;
  status: 'detected' | 'acknowledged' | 'investigating' | 'resolved' | 'closed';

  // Timeline
  detectedAt: Date;
  acknowledgedAt?: Date;
  mitigatedAt?: Date;
  resolvedAt?: Date;
  closedAt?: Date;

  // Impact
  affectedServices: string[];
  affectedUsers?: number;
  customerFacing: boolean;

  // Communication
  statusPageUpdated: boolean;
  customerNotified: boolean;

  // Root cause
  rootCause?: string;
  postmortem?: string;
}

export const incidentWorkflow = {
  // Detection
  detect: async (alert: Alert): Promise<Incident> => {
    const incident: Incident = {
      id: generateIncidentId(),
      severity: classifySeverity(alert),
      title: generateTitle(alert),
      description: alert.description,
      status: 'detected',
      detectedAt: new Date(),
      affectedServices: identifyServices(alert),
      customerFacing: isCustomerFacing(alert),
      statusPageUpdated: false,
      customerNotified: false,
    };

    // Store incident
    await storeIncident(incident);

    // Send notification
    await notifyOnCall(incident);

    return incident;
  },

  // Acknowledgment
  acknowledge: async (incidentId: string, onCall: string): Promise<void> => {
    await updateIncident(incidentId, {
      status: 'acknowledged',
      acknowledgedAt: new Date(),
    });

    // Update status page if SEV1/SEV2
    await updateStatusPage(incidentId);
  },

  // Resolution
  resolve: async (
    incidentId: string,
    rootCause: string
  ): Promise<void> => {
    await updateIncident(incidentId, {
      status: 'resolved',
      resolvedAt: new Date(),
      rootCause,
    });

    // Clear alerts
    await clearAlerts(incidentId);

    // Schedule postmortem
    await schedulePostmortem(incidentId);
  },

  // Closure
  close: async (incidentId: string, postmortem: string): Promise<void> => {
    await updateIncident(incidentId, {
      status: 'closed',
      closedAt: new Date(),
      postmortem,
    });
  },
};
```

---

## Summary

Monitoring and alerting strategy:

- **APM Integration**: DataDog for traces, metrics, logs
- **Custom Metrics**: Business metrics, infrastructure metrics
- **Dashboards**: Overview, service-specific, real-time
- **Alerting Rules**: Severity-based, SLO-based
- **Incident Response**: On-call rotation, runbooks, severity levels

**Key Targets:**
- MTTD (Mean Time To Detect): < 5 minutes
- MTTR (Mean Time To Resolve): < 30 minutes (SEV1)
- MTTA (Mean Time To Acknowledge): < 5 minutes
- Alert fatigue: < 10 actionable alerts/week

---

**Series Complete!** See [Performance & Scalability Master Index](./PERFORMANCE_SCALABILITY_MASTER_INDEX.md)
