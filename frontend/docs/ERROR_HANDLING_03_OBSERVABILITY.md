# Error Handling & Resilience — Observability & Alerting

> Research document for error monitoring, distributed tracing, and incident management.

---

## Key Questions

1. **What errors need immediate human attention vs. can be logged and reviewed?**
2. **How do we trace a request across frontend → API → spine → external services?**
3. **What's the error alerting strategy — when to page vs. when to log?**
4. **How do we build error dashboards for the engineering team?**
5. **What's the incident response workflow for production errors?**

---

## Research Areas

### Error Monitoring Stack

```typescript
interface ErrorMonitoringConfig {
  // Error tracking
  errorTracking: {
    tool: 'sentry' | 'datadog' | 'rollbar' | 'custom';
    environment: string;
    releaseTracking: boolean;
    userContext: boolean;
  };
  // Distributed tracing
  tracing: {
    tool: 'jaeger' | 'datadog' | 'zipkin' | 'custom';
    samplingRate: number;
    propagationFormat: 'w3c' | 'b3';
  };
  // Logging
  logging: {
    tool: 'datadog' | 'cloudwatch' | 'elastic' | 'custom';
    structuredLogging: boolean;
    logLevels: ('debug' | 'info' | 'warn' | 'error' | 'fatal')[];
    retentionDays: number;
  };
}
```

### Error Severity & Alerting

```typescript
interface ErrorAlertRule {
  errorPattern: string;
  severity: AlertSeverity;
  frequency: string;              // How often to alert
  channels: AlertChannel[];
  escalation: EscalationRule;
}

type AlertSeverity =
  | 'p1_critical'           // System down, customers affected
  | 'p2_high'               // Major feature broken, workaround exists
  | 'p3_medium'             // Degraded experience, not blocking
  | 'p4_low';               // Minor issue, log for review

type AlertChannel =
  | 'slack_critical'        // #incidents channel
  | 'slack_engineering'     // #engineering channel
  | 'pager_duty'            // On-call page
  | 'email_digest'          // Daily error digest
  | 'dashboard_only';       // No push notification

// Alert rules:
// Error rate > 5% of requests → P2, Slack engineering
// Payment gateway down → P1, PagerDuty + Slack critical
// Spine failure rate > 10% → P2, Slack engineering
// External API timeout rate > 20% → P2, Slack engineering
// Validation errors increasing → P3, dashboard only
// Session expiry spike → P4, daily digest
```

### Distributed Tracing

```typescript
interface TraceContext {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  // Propagated through all service calls
}

// Trace flow for a booking request:
// [Frontend] Submit booking (span: booking.submit)
//   [API] Receive request (span: api.booking.create)
//     [Spine] Validate booking (span: spine.validate)
//     [Hotel API] Check availability (span: external.hotel.check)
//     [Airline API] Book flight (span: external.airline.book)
//     [Payment] Process payment (span: payment.charge)
//     [DB] Save booking (span: db.booking.insert)
//     [Notification] Send confirmation (span: notify.email)
//   [API] Return response
// [Frontend] Show confirmation (span: booking.confirm_ui)

// Each span records:
// - Start time, duration
// - Status (ok, error)
// - Tags (supplier, booking type, agent)
// - Logs (key events within the span)
```

### Error Dashboard

```typescript
interface ErrorDashboard {
  // Error rate (errors / total requests)
  errorRate: TimeSeriesChart;
  // Top errors by frequency
  topErrors: ErrorRanking[];
  // Error breakdown by category
  errorByCategory: PieChart;
  // Recent error samples
  recentErrors: ErrorSample[];
  // Affected users
  affectedUsers: AffectedUserStats;
  // MTTR (mean time to resolve)
  mttr: MetricCard;
}
```

---

## Open Problems

1. **Trace context propagation** — Frontend → Next.js API → Python spine API → external services. Each boundary uses different frameworks. Need consistent trace propagation.

2. **Error sampling** — At high volume, logging every error is expensive. Need sampling strategies that don't miss rare critical errors.

3. **Alert fatigue** — Too many alerts = ignored alerts. Need smart deduplication and severity calibration.

4. **Frontend error attribution** — An error in the browser may be caused by a backend issue, bad data, or a browser bug. Attribution is hard.

5. **Cost of observability** — Sentry, Datadog, and tracing tools charge per event. At scale, observability can be surprisingly expensive.

---

## Next Steps

- [ ] Evaluate error monitoring tools (Sentry, Datadog, Rollbar) for cost and features
- [ ] Implement correlation ID propagation across frontend and backend
- [ ] Design error alerting rules with severity calibration
- [ ] Build error dashboard for engineering team
- [ ] Study distributed tracing setup for Next.js + Python architecture
