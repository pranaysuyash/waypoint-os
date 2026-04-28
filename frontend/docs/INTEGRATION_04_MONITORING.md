# Integration Hub & Connectors — Monitoring & Reliability

> Research document for integration health monitoring, error handling, and operational reliability.

---

## Key Questions

1. **How do we monitor integration health across dozens of connectors?**
2. **What's the alerting strategy for integration failures?**
3. **How do we handle graceful degradation when an integration fails?**
4. **What's the incident response playbook for integration issues?**
5. **How do we measure integration reliability and set SLAs?**

---

## Research Areas

### Health Monitoring

```typescript
interface IntegrationHealth {
  integrationId: string;
  agencyId: string;
  overall: HealthStatus;
  checks: HealthCheck[];
  metrics: HealthMetrics;
  lastCheckAt: Date;
  uptime30d: number;                 // Percentage
  incidentCount30d: number;
}

type HealthStatus =
  | 'healthy'                        // All checks passing
  | 'degraded'                       // Some checks failing, core functionality works
  | 'unhealthy'                      // Core functionality impacted
  | 'unknown'                        // No recent health check data
  | 'maintenance';                   // Provider scheduled maintenance

interface HealthCheck {
  name: string;                      // "auth", "search_api", "booking_api"
  status: 'pass' | 'fail' | 'warn';
  responseTimeMs: number;
  lastSuccessAt?: Date;
  lastFailureAt?: Date;
  errorMessage?: string;
}

interface HealthMetrics {
  avgResponseTime: number;
  p95ResponseTime: number;
  errorRate: number;
  successRate: number;
  requestsPerDay: number;
  lastError?: ErrorDetail;
}

// Health check types:
// 1. Liveness: Can we reach the API at all? (ping/health endpoint)
// 2. Authentication: Are our credentials still valid? (test API call)
// 3. Functional: Can we perform core operations? (search, book, cancel)
// 4. Performance: Are response times within SLA? (p95 < 2s)
// 5. Rate limit: Are we approaching rate limits? (< 80% utilization)

// Health check schedule:
// Liveness: Every 1 minute
// Authentication: Every 5 minutes
// Functional: Every 15 minutes (uses test bookings)
// Performance: Continuous (measured on real traffic)
// Rate limit: Continuous (measured on real traffic)
```

### Alerting Framework

```typescript
interface IntegrationAlert {
  alertId: string;
  integrationId: string;
  severity: AlertSeverity;
  type: AlertType;
  message: string;
  detectedAt: Date;
  resolvedAt?: Date;
  acknowledgedBy?: string;
  runbookUrl?: string;
}

type AlertSeverity =
  | 'critical'              // Integration completely down, bookings affected
  | 'high'                  // Core functionality impaired
  | 'medium'                // Degraded performance, workarounds exist
  | 'low';                  // Minor issue, monitoring only

type AlertType =
  | 'integration_down'               // Can't reach API
  | 'auth_failed'                    // Credentials invalid
  | 'high_error_rate'                // Error rate > 5%
  | 'slow_response'                  // P95 > SLA threshold
  | 'rate_limit_hit'                 // Rate limit exceeded
  | 'maintenance_scheduled'          // Provider scheduled maintenance
  | 'certificate_expiring'           // SSL/API cert expiring soon
  | 'credential_expiring'            // API key expiring soon
  | 'cost_over_budget'               // Monthly spend exceeds budget
  | 'data_quality_issue';            // Unexpected response format

// Alert routing:
// Critical → PagerDuty + Slack #incidents + SMS to on-call
// High → Slack #integration-alerts + email to integration owner
// Medium → Slack #integration-alerts only
// Low → Dashboard only (daily digest)

// Alert suppression:
// If same alert fires within 15 minutes → Suppress (don't re-alert)
// If integration is in scheduled maintenance → Suppress all alerts
// If agency has integration disabled → Suppress all alerts
// If alert is acknowledged → Suppress for 1 hour

// Runbook for common alerts:
// "Amadeus API Down" runbook:
// 1. Check Amadeus status page
// 2. If confirmed outage, enable cached results mode
// 3. Notify agents: "Flight search is using cached data"
// 4. Monitor for recovery (every 2 minutes)
// 5. On recovery, flush cache and resume live search
// 6. Post-incident: Review why detection took X minutes
```

### Graceful Degradation

```typescript
interface DegradationPlan {
  integrationId: string;
  fallbackStrategy: FallbackStrategy;
  communicationPlan: CommunicationPlan;
  recoveryPlan: RecoveryPlan;
}

type FallbackStrategy =
  | { type: 'cache'; maxAge: string; refreshOnRecovery: boolean }
  | { type: 'alternative_provider'; provider: string }
  | { type: 'manual_fallback'; message: string; workflow: string }
  | { type: 'queue'; retryOnRecovery: boolean }
  | { type: 'disable_feature'; affectedFeatures: string[] };

// Degradation plans per integration:
// Amadeus (GDS) down:
//   → Cache: Show cached flight results (up to 30 min old)
//   → Banner: "Flight prices may have changed. Confirm before booking."
//   → Queue: Booking requests queued, processed when recovered
//
// Razorpay (payments) down:
//   → Alternative: Switch to PayU (backup gateway)
//   → Manual: "Please collect payment via bank transfer"
//   → Queue: Payment intents queued for processing
//
// WhatsApp Business down:
//   → Alternative: Switch to SMS for urgent messages
//   → Queue: Non-urgent messages queued for later delivery
//   → In-app: Show notifications in workbench only
//
// Hotelbeds (hotel API) down:
//   → Cache: Show cached hotel results (up to 1 hour old)
//   → Banner: "Hotel availability may have changed."
//   → Manual: Agent contacts hotel directly for booking
//
// Tally (accounting) down:
//   → Queue: Invoice sync queued
//   → No user impact (background sync)
//   → Alert accountant of sync delay
```

### Reliability Metrics

```typescript
interface IntegrationSLA {
  integrationId: string;
  provider: string;
  targetUptime: number;              // 99.9%
  targetP95Latency: number;          // 2000ms
  targetErrorRate: number;           // < 1%
  maintenanceWindow: string;
}

interface ReliabilityReport {
  integrationId: string;
  period: string;
  uptime: number;                    // Actual uptime %
  p95Latency: number;                // Actual p95 latency
  errorRate: number;                 // Actual error rate
  incidentCount: number;
  totalDowntime: string;
  mttr: string;                      // Mean time to recovery
  slaCompliance: boolean;
  slaBreaches: SLABreach[];
}

// SLA targets by integration category:
// GDS (Amadeus, Sabre): 99.9% uptime, <2s p95, <0.5% error rate
// Payment gateway: 99.99% uptime, <1s p95, <0.1% error rate
// Hotel APIs: 99.5% uptime, <3s p95, <2% error rate
// Communication (WhatsApp): 99.9% uptime, <1s p95, <1% error rate
// Accounting (Tally): 99% uptime, <5s p95, <3% error rate
// Maps/Weather: 99% uptime, <1s p95, <5% error rate

// Monthly reliability review:
// 1. Which integrations met SLA?
// 2. Which integrations had incidents?
// 3. Root cause analysis for breaches
// 4. Action items for improvement
// 5. Provider escalation if needed
```

---

## Open Problems

1. **Multi-provider aggregation** — If Amadeus AND Sabre are down simultaneously, cached results are the only option. Multi-provider doesn't help if the whole GDS ecosystem has issues.

2. **Silent failures** — Some integrations return success but with stale data. Need data freshness monitoring, not just uptime monitoring.

3. **Cascading failures** — Payment gateway down → Bookings can't be confirmed → Customers cancel → Revenue loss. Need end-to-end impact assessment.

4. **Maintenance windows** — Providers schedule maintenance at inconvenient times (US business hours, which is Indian night). Need pre-notification and cache warming.

5. **Testing degraded modes** — How do we test fallback strategies without actually breaking production integrations? Need integration chaos testing.

---

## Next Steps

- [ ] Design health monitoring dashboard for all integrations
- [ ] Build alerting framework with runbook integration
- [ ] Create degradation plans per integration with fallback strategies
- [ ] Design reliability metrics and SLA tracking
- [ ] Study integration reliability patterns (Stripe reliability, AWS health)
