# SECURITY_04: Audit Deep Dive

> Logging, monitoring, alerting, and incident response

---

## Table of Contents

1. [Overview](#overview)
2. [Audit Event Taxonomy](#audit-event-taxonomy)
3. [Logging Infrastructure](#logging-infrastructure)
4. [Security Monitoring](#security-monitoring)
5. [Alerting and Notifications](#alerting-and-notifications)
6. [Incident Response](#incident-response)
7. [Compliance Reporting](#compliance-reporting)
8. [Log Retention and Archival](#log-retention-and-archival)

---

## Overview

### Audit Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIT ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    APPLICATIONS                          │    │
│  │  • API calls  • Auth events  • Data access             │    │
│  └────────────────────┬────────────────────────────────────┘    │
│                       │                                          │
│                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    AUDIT SERVICE                         │    │
│  │  • Event normalization  • Enrichment  • Validation      │    │
│  └────────────────────┬────────────────────────────────────┘    │
│                       │                                          │
│           ┌───────────┼───────────┬──────────────┐             │
│           ▼           ▼           ▼              ▼             │
│  ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐      │
│  │ Elasticsearch│ │  Loki   │ │  Cloud  │ │    S3       │      │
│  │   (Search)  │ │ (Logs)  │ │ Watch   │ │  (Archive)  │      │
│  └─────────────┘ └─────────┘ └─────────┘ └─────────────┘      │
│                                                                  │
│           ┌──────────────────────────────────────────┐          │
│           │          ALERTING & ANALYTICS            │          │
│           │  • Grafana  • PagerDuty  • Slack        │          │
│           └──────────────────────────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Audit Goals

| Goal | Description | Use Case |
|------|-------------|----------|
| **Compliance** | Meet regulatory requirements | GST audits, data protection laws |
| **Security** | Detect and investigate threats | Unauthorized access, data breaches |
| **Operations** | Debug and troubleshoot | Performance issues, error tracking |
| **Forensics** | Reconstruct events after incident | Security investigations, legal disputes |

---

## Audit Event Taxonomy

### Event Categories

```typescript
type AuditEventType =
  // Authentication
  | 'auth_login'
  | 'auth_logout'
  | 'auth_failed'
  | 'auth_mfa_enabled'
  | 'auth_mfa_disabled'
  | 'auth_password_changed'
  | 'auth_password_reset'
  | 'auth_session_revoked'

  // Authorization
  | 'authz_permission_denied'
  | 'authz_role_assigned'
  | 'authz_role_revoked'

  // Data Access
  | 'data_read'
  | 'data_created'
  | 'data_updated'
  | 'data_deleted'
  | 'data_exported'
  | 'pii_access'
  | 'pii_export'

  // Business Operations
  | 'trip_created'
  | 'trip_updated'
  | 'trip_deleted'
  | 'quote_created'
  | 'quote_sent'
  | 'booking_confirmed'
  | 'payment_processed'
  | 'payment_refunded'

  // System
  | 'system_api_call'
  | 'system_config_changed'
  | 'system_error'
  | 'system_slow_query'
  | 'system_rate_limit_exceeded'

  // Security
  | 'security_suspicious_activity'
  | 'security_impossible_travel'
  | 'security_brute_force'
  | 'security_data_breach'
  | 'security_malware_detected';

interface AuditEvent {
  id: string;
  type: AuditEventType;
  category: 'auth' | 'authz' | 'data' | 'business' | 'system' | 'security';

  // Actor
  userId?: string;
  agencyId?: string;
  sessionId?: string;
  apiKeyId?: string;

  // Action
  action: string;
  resourceType: string;
  resourceId?: string;

  // Context
  ip: string;
  userAgent: string;
  location?: {
    country: string;
    city: string;
    timezone: string;
  };

  // Details
  details: Record<string, any>;

  // Result
  result: 'success' | 'failure' | 'partial';
  errorMessage?: string;

  // Timing
  timestamp: Date;
  duration?: number; // ms

  // Correlation
  requestId?: string;
  traceId?: string;
  parentEventId?: string;

  // Severity
  severity: 'info' | 'warning' | 'error' | 'critical';

  // Tags
  tags?: string[];
}
```

### Event Schemas

```typescript
export const AUDIT_EVENT_SCHEMAS: Record<AuditEventType, z.ZodSchema> = {
  // Authentication events
  auth_login: z.object({
    method: z.enum(['password', 'sso', 'magic_link', 'api_key']),
    mfa_used: z.boolean(),
    device_fingerprint: z.string().optional(),
  }),

  auth_failed: z.object({
    reason: z.enum(['invalid_credentials', 'account_locked', 'mfa_required']),
    attempt_count: z.number(),
  }),

  auth_password_changed: z.object({
    method: z.enum(['self', 'admin_reset', 'recovery']),
    previous_password_hash: z.string().optional(), // For detecting reuse
  }),

  // Data access events
  pii_access: z.object({
    resource_type: z.string(),
    resource_id: z.string(),
    fields_accessed: z.array(z.string()),
    access_reason: z.string().optional(),
  }),

  pii_export: z.object({
    resource_type: z.string(),
    record_count: z.number(),
    export_format: z.enum(['csv', 'xlsx', 'pdf', 'json']),
    export_reason: z.string(),
  }),

  // Business events
  quote_sent: z.object({
    trip_id: z.string(),
    customer_id: z.string(),
    quote_amount: z.number(),
    currency: z.string(),
    delivery_method: z.enum(['email', 'whatsapp', 'in_app']),
  }),

  payment_processed: z.object({
    booking_id: z.string(),
    amount: z.number(),
    currency: z.string(),
    payment_method: z.string(),
    gateway: z.string(),
    transaction_id: z.string(),
  }),

  // Security events
  security_suspicious_activity: z.object({
    activity_type: z.enum([
      'impossible_travel',
      'multiple_failed_logins',
      'unusual_access_pattern',
      'data_access_spike',
      'api_key_abuse',
    ]),
    description: z.string(),
    indicators: z.array(z.string()),
  }),

  // System events
  system_slow_query: z.object({
    query: z.string(),
    duration_ms: z.number(),
    threshold_ms: z.number(),
    table: z.string(),
  }),

  system_rate_limit_exceeded: z.object({
    limit_type: z.enum(['api_key', 'ip', 'user']),
    limit_value: z.number(),
    actual_count: z.number(),
    window_minutes: z.number(),
  }),
};
```

---

## Logging Infrastructure

### Centralized Logging Service

```typescript
export class AuditService {
  private queue: AuditEvent[] = [];
  private flushInterval: NodeJS.Timeout;
  private readonly MAX_BATCH_SIZE = 100;
  private readonly FLUSH_INTERVAL = 5000; // 5 seconds

  constructor(
    private elasticsearch: ElasticsearchClient,
    private s3: S3Client,
    private redis: Redis
  ) {
    // Periodic flush
    this.flushInterval = setInterval(() => this.flush(), this.FLUSH_INTERVAL);

    // Flush on process exit
    process.on('beforeExit', () => this.flush());
    process.on('SIGINT', () => this.flush());
    process.on('SIGTERM', () => this.flush());
  }

  // Log an audit event
  async log(event: Omit<AuditEvent, 'id' | 'timestamp'>): Promise<string> {
    const auditEvent: AuditEvent = {
      ...event,
      id: this.generateEventId(),
      timestamp: new Date(),
    };

    // Validate event schema
    const schema = AUDIT_EVENT_SCHEMAS[event.type];
    if (schema) {
      const validation = schema.safeParse(event.details);
      if (!validation.success) {
        console.error('Invalid audit event details:', validation.error);
      }
    }

    // Add to queue
    this.queue.push(auditEvent);

    // Flush if queue is full
    if (this.queue.length >= this.MAX_BATCH_SIZE) {
      await this.flush();
    }

    // Also write to Redis for real-time monitoring
    await this.writeToRedis(auditEvent);

    return auditEvent.id;
  }

  // Flush events to storage
  private async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, this.MAX_BATCH_SIZE);

    try {
      // Write to Elasticsearch for search
      await this.writeToElasticsearch(batch);

      // Write critical events to S3 for archival
      const critical = batch.filter((e) => e.severity === 'critical');
      if (critical.length > 0) {
        await this.writeToS3(critical);
      }

      // Send alerts for critical events
      for (const event of critical) {
        await this.sendAlert(event);
      }
    } catch (error) {
      console.error('Failed to flush audit events:', error);

      // Put events back in queue
      this.queue.unshift(...batch);
    }
  }

  private async writeToElasticsearch(events: AuditEvent[]): Promise<void> {
    const bulkBody = events.flatMap((event) => [
      { index: { _index: this.getIndexName(event.timestamp) } },
      this.sanitizeEvent(event),
    ]);

    await this.elasticsearch.bulk({
      refresh: true,
      body: bulkBody,
    });
  }

  private async writeToS3(events: AuditEvent[]): Promise<void> {
    const key = `audit/${this.getDatePrefix()}/${Date.now()}.jsonl`;
    const body = events.map((e) => JSON.stringify(e)).join('\n');

    await this.s3.send(new PutObjectCommand({
      Bucket: process.env.AUDIT_LOG_BUCKET!,
      Key: key,
      Body: body,
      ServerSideEncryption: 'AES256',
    }));
  }

  private async writeToRedis(event: AuditEvent): Promise<void> {
    const key = `audit:realtime:${event.category}`;
    await this.redis.lpush(key, JSON.stringify(event));
    await this.redis.ltrim(key, 0, 999); // Keep last 1000

    // TTL for real-time logs
    await this.redis.expire(key, 86400); // 24 hours
  }

  private getIndexName(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `audit-${year}-${month}`;
  }

  private getDatePrefix(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}/${month}/${day}`;
  }

  private sanitizeEvent(event: AuditEvent): any {
    // Remove sensitive data from logs
    const sanitized = { ...event };

    // Never log passwords
    if (sanitized.details.password) {
      delete sanitized.details.password;
    }

    // Never log full API keys
    if (sanitized.details.api_key) {
      sanitized.details.api_key = '***REDACTED***';
    }

    // Mask PII in details
    if (sanitized.details.email) {
      sanitized.details.email = this.maskEmail(sanitized.details.email);
    }

    return sanitized;
  }

  private generateEventId(): string {
    return `evt_${Date.now()}_${crypto.randomBytes(8).toString('hex')}`;
  }

  private async sendAlert(event: AuditEvent): Promise<void> {
    await alertService.send({
      severity: event.severity,
      title: `Critical Audit Event: ${event.type}`,
      message: event.errorMessage || event.action,
      event,
    });
  }

  private maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    if (local.length <= 2) return `***@${domain}`;
    return `${local[0]}***${local[local.length - 1]}@${domain}`;
  }
}
```

### Express Middleware for Request Logging

```typescript
export const auditMiddleware = (
  auditService: AuditService
): RequestHandler => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    const requestId = crypto.randomUUID();

    // Attach to request
    req.requestId = requestId;
    res.setHeader('X-Request-ID', requestId);

    // Log request
    await auditService.log({
      type: 'system_api_call',
      category: 'system',
      userId: req.user?.id,
      agencyId: req.user?.agencyId,
      sessionId: req.user?.sessionId,
      action: req.method,
      resourceType: req.route?.path || req.path,
      ip: req.ip,
      userAgent: req.headers['user-agent'],
      details: {
        method: req.method,
        path: req.path,
        query: this.sanitizeQuery(req.query),
      },
      result: 'success',
      severity: 'info',
      requestId,
    });

    // Capture response
    const originalSend = res.send;
    res.send = function (data) {
      res.send = originalSend;

      // Calculate duration
      const duration = Date.now() - startTime;

      // Log response
      auditService.log({
        type: 'system_api_call',
        category: 'system',
        userId: req.user?.id,
        agencyId: req.user?.agencyId,
        action: `${req.method} ${req.path}`,
        resourceType: 'response',
        ip: req.ip,
        userAgent: req.headers['user-agent'],
        details: {
          statusCode: res.statusCode,
          duration,
        },
        result: res.statusCode >= 400 ? 'failure' : 'success',
        severity: res.statusCode >= 500 ? 'error' : 'info',
        requestId,
        duration,
      });

      return res.send(data);
    };

    next();
  };

  private sanitizeQuery(query: any): any {
    const sanitized = { ...query };

    // Remove sensitive query params
    const sensitive = ['password', 'token', 'api_key', 'secret'];
    for (const key of sensitive) {
      if (key in sanitized) {
        sanitized[key] = '***REDACTED***';
      }
    }

    return sanitized;
  }
};
```

---

## Security Monitoring

### Anomaly Detection

```typescript
export class SecurityMonitoringService {
  private readonly BASELINE_WINDOW = 7 * 24 * 60 * 60 * 1000; // 7 days

  async detectAnomalies(userId: string): Promise<Anomaly[]> {
    const anomalies: Anomaly[] = [];

    // Check for impossible travel
    const travelAnomaly = await this.detectImpossibleTravel(userId);
    if (travelAnomaly) anomalies.push(travelAnomaly);

    // Check for unusual access patterns
    const accessAnomaly = await this.detectUnusualAccess(userId);
    if (accessAnomaly) anomalies.push(accessAnomaly);

    // Check for data access spike
    const dataAnomaly = await this.detectDataAccessSpike(userId);
    if (dataAnomaly) anomalies.push(dataAnomaly);

    // Check for failed login spike
    const loginAnomaly = await this.detectFailedLoginSpike(userId);
    if (loginAnomaly) anomalies.push(loginAnomaly);

    return anomalies;
  }

  private async detectImpossibleTravel(userId: string): Promise<Anomaly | null> {
    const recentEvents = await auditService.search({
      userId,
      type: 'auth_login',
      timestamp: { gte: new Date(Date.now() - this.BASELINE_WINDOW) },
      sort: [{ timestamp: 'asc' }],
    });

    for (let i = 0; i < recentEvents.length - 1; i++) {
      const e1 = recentEvents[i];
      const e2 = recentEvents[i + 1];

      if (!e1.location || !e2.location) continue;

      const distance = this.calculateDistance(e1.location, e2.location);
      const timeDiff = e2.timestamp.getTime() - e1.timestamp.getTime();

      // Impossible: >1000km in <1 hour
      if (distance > 1000 && timeDiff < 3600000) {
        return {
          type: 'impossible_travel',
          severity: 'critical',
          description: `Login from ${e2.location.city} just ${timeDiff / 60000} minutes after login from ${e1.location.city}`,
          events: [e1.id, e2.id],
        };
      }
    }

    return null;
  }

  private async detectUnusualAccess(userId: string): Promise<Anomaly | null> {
    // Get baseline access patterns
    const baseline = await this.getAccessBaseline(userId);

    // Get recent access
    const recent = await auditService.search({
      userId,
      timestamp: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) },
    });

    // Check for access at unusual times
    const unusualTimeEvents = recent.filter((e) => {
      const hour = e.timestamp.getHours();
      return !baseline.usualHours.includes(hour);
    });

    if (unusualTimeEvents.length > baseline.unusualTimeThreshold) {
      return {
        type: 'unusual_access_time',
        severity: 'warning',
        description: `${unusualTimeEvents.length} logins outside usual hours`,
        events: unusualTimeEvents.map((e) => e.id),
      };
    }

    // Check for access from new location
    const newLocations = recent.filter((e) =>
      e.location && !baseline.knownLocations.includes(e.location.country)
    );

    if (newLocations.length > 0) {
      return {
        type: 'new_location',
        severity: 'warning',
        description: `Access from new location: ${newLocations[0].location?.city}`,
        events: newLocations.map((e) => e.id),
      };
    }

    return null;
  }

  private async detectDataAccessSpike(userId: string): Promise<Anomaly | null> {
    // Get recent data access events
    const recent = await auditService.search({
      userId,
      type: 'pii_access',
      timestamp: { gte: new Date(Date.now() - 60 * 60 * 1000) }, // Last hour
    });

    // Get baseline
    const baseline = await this.getDataAccessBaseline(userId);

    // Check if recent exceeds baseline by 3x
    if (recent.length > baseline.averagePerHour * 3) {
      return {
        type: 'data_access_spike',
        severity: 'high',
        description: `${recent.length} PII access events in last hour (baseline: ${baseline.averagePerHour})`,
        events: recent.map((e) => e.id),
      };
    }

    return null;
  }

  private async detectFailedLoginSpike(userId: string): Promise<Anomaly | null> {
    const recent = await auditService.search({
      type: 'auth_failed',
      details: { userId },
      timestamp: { gte: new Date(Date.now() - 15 * 60 * 1000) }, // Last 15 minutes
    });

    if (recent.length >= 5) {
      return {
        type: 'brute_force suspected',
        severity: 'critical',
        description: `${recent.length} failed login attempts in last 15 minutes`,
        events: recent.map((e) => e.id),
      };
    }

    return null;
  }

  private async getAccessBaseline(userId: string): Promise<AccessBaseline> {
    const events = await auditService.search({
      userId,
      type: 'auth_login',
      timestamp: { gte: new Date(Date.now() - this.BASELINE_WINDOW) },
    });

    // Calculate usual hours
    const hourCounts = new Array(24).fill(0);
    const locations = new Set<string>();

    for (const event of events) {
      hourCounts[event.timestamp.getHours()]++;
      if (event.location?.country) {
        locations.add(event.location.country);
      }
    }

    // Find hours with significant activity (>5% of total)
    const total = events.length;
    const usualHours = hourCounts
      .map((count, hour) => ({ hour, count }))
      .filter(({ count }) => count / total > 0.05)
      .map(({ hour }) => hour);

    return {
      usualHours,
      knownLocations: Array.from(locations),
      unusualTimeThreshold: Math.max(3, Math.floor(total / 7)),
    };
  }

  private async getDataAccessBaseline(userId: string): Promise<{ averagePerHour: number }> {
    const events = await auditService.search({
      userId,
      type: 'pii_access',
      timestamp: { gte: new Date(Date.now() - this.BASELINE_WINDOW) },
    });

    const hoursInWindow = this.BASELINE_WINDOW / (60 * 60 * 1000);
    return {
      averagePerHour: Math.ceil(events.length / hoursInWindow),
    };
  }

  private calculateDistance(
    loc1: { country: string; city: string },
    loc2: { country: string; city: string }
  ): number {
    // Simplified distance calculation
    // In production, use proper geolocation distance
    if (loc1.country === loc2.country) return 100; // Same country
    if (loc1.country === loc2.country) return 500; // Neighboring
    return 2000; // Different continents
  }
}

interface Anomaly {
  type: string;
  severity: 'info' | 'warning' | 'high' | 'critical';
  description: string;
  events: string[];
}

interface AccessBaseline {
  usualHours: number[];
  knownLocations: string[];
  unusualTimeThreshold: number;
}
```

### Real-Time Monitoring Dashboard

```typescript
// Grafana dashboard queries for security monitoring
export const SECURITY_DASHBOARD_QUERIES = {
  // Failed logins over time
  failedLogins: {
    title: 'Failed Login Attempts',
    query: {
      bool: {
        must: [
          { term: { type: 'auth_failed' } },
          { range: { timestamp: { gte: 'now-24h' } } },
        ],
      },
    },
    groupBy: '@timestamp',
    interval: '1h',
  },

  // PII access by user
  piiAccessByUser: {
    title: 'PII Access by User',
    query: {
      bool: {
        must: [
          { term: { type: 'pii_access' } },
          { range: { timestamp: { gte: 'now-24h' } } },
        ],
      },
    },
    groupBy: 'userId',
    topN: 10,
  },

  // Unusual locations
  unusualLocations: {
    title: 'Logins from Unusual Locations',
    query: {
      bool: {
        must: [
          { term: { type: 'auth_login' } },
          { range: { timestamp: { gte: 'now-7d' } } },
        ],
      },
    },
    groupBy: 'location.country',
  },

  // Data exports
  dataExports: {
    title: 'Data Export Events',
    query: {
      bool: {
        must: [
          { term: { type: 'pii_export' } },
          { range: { timestamp: { gte: 'now-24h' } } },
        ],
      },
    },
    groupBy: ['userId', 'details.resource_type'],
  },

  // Security events by severity
  securityEvents: {
    title: 'Security Events by Severity',
    query: {
      bool: {
        must: [
          { terms: { category: ['security', 'auth_failed'] } },
          { range: { timestamp: { gte: 'now-24h' } } },
        ],
      },
    },
    groupBy: 'severity',
  },
};
```

---

## Alerting and Notifications

### Alert Rules

```typescript
interface AlertRule {
  id: string;
  name: string;
  description: string;
  severity: 'info' | 'warning' | 'high' | 'critical';
  enabled: boolean;

  // Trigger condition
  condition: AlertCondition;

  // Throttling
  throttleMinutes: number;
  cooldownMinutes: number;

  // Notifications
  channels: NotificationChannel[];

  // Escalation
  escalationRules?: EscalationRule[];
}

interface AlertCondition {
  type: 'threshold' | 'spike' | 'pattern' | 'composite';

  // For threshold
  metric?: string;
  operator?: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  threshold?: number;
  windowMinutes?: number;

  // For spike
  spikeMultiplier?: number;
  baselineWindowMinutes?: number;

  // For pattern
  pattern?: string;

  // For composite
  conditions?: AlertCondition[];
  logic?: 'and' | 'or';
}

interface NotificationChannel {
  type: 'email' | 'slack' | 'pagerduty' | 'sms' | 'webhook';
  config: Record<string, any>;
}

interface EscalationRule {
  waitMinutes: number;
  severity: string;
  channels: NotificationChannel[];
}

export const ALERT_RULES: AlertRule[] = [
  {
    id: 'brute-force-detected',
    name: 'Brute Force Attack Detected',
    description: 'Multiple failed login attempts from same IP',
    severity: 'critical',
    enabled: true,
    condition: {
      type: 'threshold',
      metric: 'auth_failed_count_by_ip',
      operator: 'gte',
      threshold: 10,
      windowMinutes: 5,
    },
    throttleMinutes: 15,
    cooldownMinutes: 30,
    channels: [
      { type: 'slack', config: { channel: '#security-alerts' } },
      { type: 'pagerduty', config: { severity: 'critical' } },
    ],
    escalationRules: [
      {
        waitMinutes: 15,
        severity: 'critical',
        channels: [
          { type: 'sms', config: {} },
        ],
      },
    ],
  },

  {
    id: 'pii-export-large',
    name: 'Large PII Export',
    description: 'User exporting more than 100 records',
    severity: 'high',
    enabled: true,
    condition: {
      type: 'threshold',
      metric: 'pii_export_record_count',
      operator: 'gt',
      threshold: 100,
      windowMinutes: 5,
    },
    throttleMinutes: 60,
    cooldownMinutes: 120,
    channels: [
      { type: 'slack', config: { channel: '#security-alerts' } },
      { type: 'email', config: { to: 'security@company.com' } },
    ],
  },

  {
    id: 'impossible-travel',
    name: 'Impossible Travel Detected',
    description: 'Login from geographically impossible location',
    severity: 'critical',
    enabled: true,
    condition: {
      type: 'pattern',
      pattern: 'impossible_travel',
    },
    throttleMinutes: 5,
    cooldownMinutes: 30,
    channels: [
      { type: 'slack', config: { channel: '#security-alerts' } },
      { type: 'pagerduty', config: { severity: 'critical' } },
    ],
  },

  {
    id: 'api-rate-limit-exceeded',
    name: 'API Rate Limit Exceeded',
    description: 'API key exceeding rate limit',
    severity: 'warning',
    enabled: true,
    condition: {
      type: 'threshold',
      metric: 'rate_limit_violations',
      operator: 'gte',
      threshold: 5,
      windowMinutes: 1,
    },
    throttleMinutes: 10,
    cooldownMinutes: 30,
    channels: [
      { type: 'slack', config: { channel: '#api-alerts' } },
    ],
  },
];
```

### Alert Engine

```typescript
export class AlertEngine {
  private alertState: Map<string, AlertState> = new Map();

  constructor(
    private auditService: AuditService,
    private notificationService: NotificationService
  ) {
    // Start evaluation loop
    this.startEvaluationLoop();
  }

  async evaluateRules(): Promise<void> {
    for (const rule of ALERT_RULES) {
      if (!rule.enabled) continue;

      const state = this.getAlertState(rule.id);
      if (state.inCooldown) continue;

      const triggered = await this.evaluateCondition(rule.condition);

      if (triggered) {
        await this.triggerAlert(rule);
      }
    }
  }

  private async evaluateCondition(condition: AlertCondition): Promise<boolean> {
    switch (condition.type) {
      case 'threshold':
        return this.evaluateThreshold(condition);

      case 'spike':
        return this.evaluateSpike(condition);

      case 'pattern':
        return this.evaluatePattern(condition);

      case 'composite':
        return this.evaluateComposite(condition);

      default:
        return false;
    }
  }

  private async evaluateThreshold(condition: AlertCondition): Promise<boolean> {
    const query = {
      bool: {
        must: [
          { range: { timestamp: { gte: `now-${condition.windowMinutes}m` } } },
        ],
      },
    };

    // Add metric-specific query
    if (condition.metric === 'auth_failed_count_by_ip') {
      query.bool.must.push({ term: { type: 'auth_failed' } });
    } else if (condition.metric === 'pii_export_record_count') {
      query.bool.must.push({
        bool: {
          must: [
            { term: { type: 'pii_export' } },
            { range: { 'details.record_count': { [condition.operator!]: condition.threshold } } },
          ],
        },
      });
      return true; // Special case for PII export
    }

    const events = await this.auditService.search(query);

    if (condition.metric === 'auth_failed_count_by_ip') {
      // Group by IP and check threshold
      const byIp = new Map<string, number>();
      for (const event of events) {
        byIp.set(event.ip, (byIp.get(event.ip) || 0) + 1);
      }
      return Array.from(byIp.values()).some((count) =>
        this.compare(count, condition.operator!, condition.threshold!)
      );
    }

    return this.compare(events.length, condition.operator!, condition.threshold!);
  }

  private async evaluateSpike(condition: AlertCondition): Promise<boolean> {
    const now = Date.now();
    const currentWindow = now - condition.windowMinutes! * 60 * 1000;
    const baselineStart = now - condition.baselineWindowMinutes! * 60 * 1000;
    const baselineEnd = currentWindow;

    const [currentEvents, baselineEvents] = await Promise.all([
      this.auditService.search({
        timestamp: { gte: new Date(currentWindow) },
      }),
      this.auditService.search({
        timestamp: { gte: new Date(baselineStart), lte: new Date(baselineEnd) },
      }),
    ]);

    const currentRate = currentEvents.length / condition.windowMinutes!;
    const baselineRate = baselineEvents.length / (condition.baselineWindowMinutes! - condition.windowMinutes!);

    return currentRate > baselineRate * condition.spikeMultiplier!;
  }

  private async evaluatePattern(condition: AlertCondition): Promise<boolean> {
    // Check for events matching pattern
    const events = await this.auditService.search({
      type: 'security_suspicious_activity',
      'details.activity_type': condition.pattern,
      timestamp: { gte: 'now-5m' },
    });

    return events.length > 0;
  }

  private async evaluateComposite(condition: AlertCondition): Promise<boolean> {
    const results = await Promise.all(
      condition.conditions!.map((c) => this.evaluateCondition(c))
    );

    return condition.logic === 'and'
      ? results.every((r) => r)
      : results.some((r) => r);
  }

  private compare(value: number, operator: string, threshold: number): boolean {
    switch (operator) {
      case 'gt': return value > threshold;
      case 'lt': return value < threshold;
      case 'eq': return value === threshold;
      case 'gte': return value >= threshold;
      case 'lte': return value <= threshold;
      default: return false;
    }
  }

  private async triggerAlert(rule: AlertRule): Promise<void> {
    const state = this.getAlertState(rule.id);

    // Check throttle
    if (state.lastTriggered && Date.now() - state.lastTriggered < rule.throttleMinutes * 60 * 1000) {
      return;
    }

    // Send notifications
    for (const channel of rule.channels) {
      await this.notificationService.send({
        channel: channel.type,
        config: channel.config,
        severity: rule.severity,
        title: rule.name,
        message: rule.description,
        ruleId: rule.id,
      });
    }

    // Update state
    state.lastTriggered = Date.now();
    state.inCooldown = true;
    this.alertState.set(rule.id, state);

    // Schedule escalation checks
    if (rule.escalationRules) {
      this.scheduleEscalation(rule);
    }

    // Schedule cooldown end
    setTimeout(() => {
      const s = this.getAlertState(rule.id);
      s.inCooldown = false;
      this.alertState.set(rule.id, s);
    }, rule.cooldownMinutes * 60 * 1000);
  }

  private scheduleEscalation(rule: AlertRule): void {
    for (const escalation of rule.escalationRules!) {
      setTimeout(async () => {
        // Check if alert is still active
        const isActive = await this.evaluateCondition(rule.condition);
        if (!isActive) return;

        // Send escalation notifications
        for (const channel of escalation.channels) {
          await this.notificationService.send({
            channel: channel.type,
            config: channel.config,
            severity: escalation.severity,
            title: `${rule.name} - Escalated`,
            message: `Alert has been active for ${escalation.waitMinutes} minutes`,
            ruleId: rule.id,
          });
        }
      }, escalation.waitMinutes * 60 * 1000);
    }
  }

  private getAlertState(ruleId: string): AlertState {
    return (
      this.alertState.get(ruleId) || {
        lastTriggered: null,
        inCooldown: false,
      }
    );
  }

  private startEvaluationLoop(): void {
    setInterval(() => {
      this.evaluateRules();
    }, 60000); // Every minute
  }
}

interface AlertState {
  lastTriggered: number | null;
  inCooldown: boolean;
}
```

---

## Incident Response

### Incident Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   INCIDENT RESPONSE WORKFLOW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DETECT                                                       │
│     └─ Alert triggers, anomaly detected                        │
│                                                                  │
│  2. TRIAGE                                                       │
│     ├── Assess severity                                         │
│     ├── Determine scope                                         │
│     └─ Assign owner                                             │
│                                                                  │
│  3. CONTAIN                                                      │
│     ├── Block malicious IPs                                     │
│     ├── Revoke compromised credentials                          │
│     └─ Isolate affected systems                                 │
│                                                                  │
│  4. ERADICATE                                                   │
│     ├── Remove malware / malicious accounts                     │
│     ├── Patch vulnerabilities                                   │
│     └─ Verify removal                                           │
│                                                                  │
│  5. RECOVER                                                     │
│     ├── Restore from backups if needed                          │
│     ├── Monitor for recurrence                                  │
│     └─ Return to normal operations                              │
│                                                                  │
│  6. POST-INCIDENT                                               │
│     ├── Root cause analysis                                     │
│     ├── Update detection rules                                  │
│     └─ Document lessons learned                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Incident Management

```typescript
type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';
type IncidentStatus = 'detected' | 'triaging' | 'containing' | 'eradicating' | 'recovering' | 'closed';

interface Incident {
  id: string;
  title: string;
  description: string;

  // Classification
  severity: IncidentSeverity;
  status: IncidentStatus;
  type: string;

  // Assignment
  assignedTo?: string;
  team: string;

  // Timeline
  detectedAt: Date;
  acknowledgedAt?: Date;
  containedAt?: Date;
  resolvedAt?: Date;
  closedAt?: Date;

  // Details
  affectedSystems: string[];
  affectedUsers?: string[];
  rootCause?: string;
  resolution?: string;

  // Related events
  eventIds: string[];
  alertIds: string[];

  // Actions taken
  actions: IncidentAction[];

  // Communication
  stakeholdersNotified: boolean;
  customerImpact: string;

  // Metrics
  mttd?: number; // Mean Time To Detect (ms)
  mttr?: number; // Mean Time To Resolve (ms)
}

interface IncidentAction {
  timestamp: Date;
  action: string;
  takenBy: string;
  result: string;
}

export class IncidentService {
  async createIncident(alert: Alert): Promise<Incident> {
    const incident = await IncidentRepository.create({
      title: this.generateTitle(alert),
      description: alert.description,
      severity: this.mapSeverity(alert.severity),
      status: 'detected',
      type: this.classifyType(alert),
      team: this.assignTeam(alert),
      detectedAt: new Date(),
      eventIds: alert.eventIds || [],
      alertIds: [alert.id],
      affectedSystems: alert.affectedSystems || [],
      actions: [],
      stakeholdersNotified: false,
      customerImpact: 'unknown',
    });

    // Auto-assign for critical incidents
    if (incident.severity === 'critical') {
      await this.autoAssign(incident);
    }

    // Notify on-call
    await this.notifyOnCall(incident);

    return incident;
  }

  async updateStatus(
    incidentId: string,
    status: IncidentStatus,
    userId: string
  ): Promise<void> {
    const incident = await IncidentRepository.findById(incidentId);
    if (!incident) throw new ValidationError('INCIDENT_NOT_FOUND', 'Incident not found');

    const updates: Partial<Incident> = { status };

    // Update timestamps based on status
    switch (status) {
      case 'triaging':
        updates.acknowledgedAt = new Date();
        updates.mttd = updates.acknowledgedAt.getTime() - incident.detectedAt.getTime();
        break;

      case 'containing':
        updates.containedAt = new Date();
        break;

      case 'recovering':
        updates.resolvedAt = new Date();
        updates.mttr = updates.resolvedAt.getTime() - incident.detectedAt.getTime();
        break;

      case 'closed':
        updates.closedAt = new Date();
        break;
    }

    // Add action
    await this.addAction(incidentId, {
      timestamp: new Date(),
      action: `Status changed to ${status}`,
      takenBy: userId,
      result: 'success',
    });

    await IncidentRepository.update(incidentId, updates);

    // Send notifications
    await this.notifyStatusChange(incidentId, status);
  }

  async addAction(
    incidentId: string,
    action: Omit<IncidentAction, 'timestamp'>
  ): Promise<void> {
    const incident = await IncidentRepository.findById(incidentId);
    if (!incident) throw new ValidationError('INCIDENT_NOT_FOUND', 'Incident not found');

    const newAction: IncidentAction = {
      ...action,
      timestamp: new Date(),
    };

    await IncidentRepository.addAction(incidentId, newAction);
  }

  async getRunbook(incidentType: string): Promise<Runbook | null> {
    return RunbookRepository.findByType(incidentType);
  }

  async generatePostmortem(incidentId: string): Promise<Postmortem> {
    const incident = await IncidentRepository.findById(incidentId);
    const events = await auditService.search({
      incidentId,
      sort: [{ timestamp: 'asc' }],
    });

    // Generate timeline
    const timeline = events.map((e) => ({
      time: e.timestamp,
      event: e.type,
      description: e.action,
    }));

    // Generate metrics
    const metrics = {
      mttd: incident.mttd,
      mttr: incident.mttr,
      totalEvents: events.length,
      affectedUsers: incident.affectedUsers?.length || 0,
      customerImpact: incident.customerImpact,
    };

    return {
      incidentId,
      title: incident.title,
      timeline,
      metrics,
      rootCause: incident.rootCause || 'unknown',
      resolution: incident.resolution || 'ongoing',
      actionsTaken: incident.actions,
      lessonsLearned: [],
      followUpItems: [],
    };
  }

  private generateTitle(alert: Alert): string {
    return `${alert.ruleName}: ${alert.description}`;
  }

  private mapSeverity(severity: string): IncidentSeverity {
    switch (severity) {
      case 'critical': return 'critical';
      case 'high': return 'high';
      case 'warning': return 'medium';
      default: return 'low';
    }
  }

  private classifyType(alert: Alert): string {
    if (alert.ruleId === 'brute-force-detected') return 'security_breach';
    if (alert.ruleId === 'pii-export-large') return 'data_exposure';
    if (alert.ruleId === 'impossible-travel') return 'account_compromise';
    return 'security_incident';
  }

  private assignTeam(alert: Alert): string {
    if (alert.category === 'security') return 'security';
    if (alert.category === 'auth') return 'identity';
    return 'operations';
  }

  private async autoAssign(incident: Incident): Promise<void> {
    // Assign to on-call security engineer
    const onCall = await OnCallService.getCurrent('security');
    await IncidentRepository.update(incident.id, {
      assignedTo: onCall.userId,
    });
  }

  private async notifyOnCall(incident: Incident): Promise<void> {
    await notificationService.send({
      severity: incident.severity,
      title: `New Incident: ${incident.title}`,
      message: incident.description,
      channels: ['slack', 'pagerduty'],
    });
  }

  private async notifyStatusChange(incidentId: string, status: IncidentStatus): Promise<void> {
    const incident = await IncidentRepository.findById(incidentId);

    await notificationService.send({
      severity: 'info',
      title: `Incident ${incidentId} status: ${status}`,
      message: `${incident.title} is now ${status}`,
      channels: ['slack'],
    });
  }
}

interface Postmortem {
  incidentId: string;
  title: string;
  timeline: Array<{ time: Date; event: string; description: string }>;
  metrics: {
    mttd?: number;
    mttr?: number;
    totalEvents: number;
    affectedUsers: number;
    customerImpact: string;
  };
  rootCause: string;
  resolution: string;
  actionsTaken: IncidentAction[];
  lessonsLearned: string[];
  followUpItems: string[];
}
```

---

## Compliance Reporting

### Report Templates

```typescript
export class ComplianceReportService {
  // Generate GDPR compliance report
  async generateGDPRReport(
    startDate: Date,
    endDate: Date,
    agencyId?: string
  ): Promise<GdprReport> {
    // Data access events
    const dataAccess = await auditService.search({
      type: 'pii_access',
      timestamp: { gte: startDate, lte: endDate },
      ...(agencyId && { agencyId }),
    });

    // Data export events
    const dataExports = await auditService.search({
      type: 'pii_export',
      timestamp: { gte: startDate, lte: endDate },
      ...(agencyId && { agencyId }),
    });

    // Data deletion requests
    const deletionRequests = await GdprRequestRepository.findCompleted(
      startDate,
      endDate,
      agencyId
    );

    // Security incidents involving PII
    const incidents = await IncidentRepository.find({
      type: 'data_exposure',
      detectedAt: { gte: startDate, lte: endDate },
      ...(agencyId && { agencyId }),
    });

    return {
      period: { start: startDate, end: endDate },
      agencyId,
      generatedAt: new Date(),

      metrics: {
        totalDataAccessEvents: dataAccess.length,
        totalDataExports: dataExports.length,
        uniqueUsersAccessed: new Set(dataAccess.map((e) => e.userId)).size,
        totalDeletionRequests: deletionRequests.length,
        avgDeletionTime: this.calculateAvgDeletionTime(deletionRequests),
        securityIncidents: incidents.length,
      },

      details: {
        dataAccessByUser: this.groupBy(dataAccess, 'userId'),
        dataAccessByType: this.groupBy(dataAccess, 'resourceType'),
        dataExportsByUser: this.groupBy(dataExports, 'userId'),
        deletionRequestsByStatus: this.groupBy(deletionRequests, 'status'),
      },

      incidents: incidents.map((i) => ({
        id: i.id,
        title: i.title,
        severity: i.severity,
        affectedUsers: i.affectedUsers?.length || 0,
        resolvedAt: i.resolvedAt,
      })),
    };
  }

  // Generate security audit report
  async generateSecurityReport(
    startDate: Date,
    endDate: Date
  ): Promise<SecurityReport> {
    // Authentication events
    const authEvents = await auditService.search({
      type: { in: ['auth_login', 'auth_failed', 'auth_password_changed'] },
      timestamp: { gte: startDate, lte: endDate },
    });

    // Security events
    const securityEvents = await auditService.search({
      category: 'security',
      timestamp: { gte: startDate, lte: endDate },
    });

    // Incidents
    const incidents = await IncidentRepository.find({
      detectedAt: { gte: startDate, lte: endDate },
    });

    return {
      period: { start: startDate, end: endDate },
      generatedAt: new Date(),

      authentication: {
        totalLogins: authEvents.filter((e) => e.type === 'auth_login').length,
        failedLogins: authEvents.filter((e) => e.type === 'auth_failed').length,
        passwordChanges: authEvents.filter((e) => e.type === 'auth_password_changed').length,
        uniqueUsers: new Set(authEvents.map((e) => e.userId)).size,
      },

      security: {
        totalEvents: securityEvents.length,
        byType: this.groupBy(securityEvents, 'type'),
        bySeverity: this.groupBy(securityEvents, 'severity'),
      },

      incidents: {
        total: incidents.length,
        bySeverity: this.groupBy(incidents, 'severity'),
        byStatus: this.groupBy(incidents, 'status'),
        avgMTTD: this.average(incidents, (i) => i.mttd),
        avgMTTR: this.average(incidents, (i) => i.mttr),
      },

      recommendations: this.generateRecommendations(incidents, securityEvents),
    };
  }

  // Generate access log for specific user
  async generateUserAccessReport(
    userId: string,
    startDate: Date,
    endDate: Date
  ): Promise<UserAccessReport> {
    const events = await auditService.search({
      userId,
      timestamp: { gte: startDate, lte: endDate },
      sort: [{ timestamp: 'desc' }],
    });

    const user = await UserRepository.findById(userId);

    return {
      user: {
        id: user!.id,
        name: user!.name,
        email: user!.email,
        role: user!.role,
        agencyId: user!.agencyId,
      },
      period: { start: startDate, end: endDate },
      generatedAt: new Date(),

      summary: {
        totalEvents: events.length,
        byType: this.groupBy(events, 'type'),
        byCategory: this.groupBy(events, 'category'),
        uniqueIPs: new Set(events.map((e) => e.ip)).size,
        uniqueLocations: new Set(
          events.filter((e) => e.location).map((e) => e.location?.country)
        ).size,
      },

      events: events.map((e) => ({
        timestamp: e.timestamp,
        type: e.type,
        action: e.action,
        resource: e.resourceType,
        ip: e.ip,
        location: e.location,
        result: e.result,
      })),
    };
  }

  private groupBy<T>(items: T[], key: string): Record<string, number> {
    return items.reduce((acc, item) => {
      const k = String(item[key]);
      acc[k] = (acc[k] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  private calculateAvgDeletionTime(requests: any[]): number {
    const times = requests
      .filter((r) => r.completedAt && r.createdAt)
      .map((r) => r.completedAt.getTime() - r.createdAt.getTime());

    if (times.length === 0) return 0;
    return times.reduce((a, b) => a + b, 0) / times.length;
  }

  private average<T>(items: T[], getter: (item: T) => number | undefined): number {
    const values = items.map(getter).filter((v) => v !== undefined) as number[];
    if (values.length === 0) return 0;
    return values.reduce((a, b) => a + b, 0) / values.length;
  }

  private generateRecommendations(
    incidents: Incident[],
    events: AuditEvent[]
  ): string[] {
    const recommendations: string[] = [];

    // Analyze incidents
    const criticalIncidents = incidents.filter((i) => i.severity === 'critical');
    if (criticalIncidents.length > 0) {
      recommendations.push(
        `${criticalIncidents.length} critical incidents detected. Review incident response procedures.`
      );
    }

    // Analyze failed logins
    const failedLogins = events.filter((e) => e.type === 'auth_failed');
    const topFailedIPs = this.groupBy(failedLogins, 'ip');
    const suspiciousIPs = Object.entries(topFailedIPs)
      .filter(([_, count]) => count > 10)
      .map(([ip]) => ip);

    if (suspiciousIPs.length > 0) {
      recommendations.push(
        `Consider blocking IPs with excessive failed logins: ${suspiciousIPs.slice(0, 5).join(', ')}`
      );
    }

    // Analyze PII exports
    const largeExports = events.filter((e) =>
      e.type === 'pii_export' && e.details.record_count > 100
    );

    if (largeExports.length > 0) {
      recommendations.push(
        `${largeExports.length} large PII exports detected. Consider requiring approval for exports >100 records.`
      );
    }

    return recommendations;
  }
}
```

---

## Log Retention and Archival

### Retention Policy

```typescript
export const LOG_RETENTION_POLICY = {
  // Hot storage (Elasticsearch) - fast search
  hot: {
    duration: '30 days',
    storage: 'elasticsearch',
    indices: ['audit-*'],
  },

  // Warm storage (S3 Standard) - infrequent access
  warm: {
    duration: '1 year',
    storage: 's3',
    storageClass: 'STANDARD',
    path: 'audit-logs/',
  },

  // Cold storage (S3 Glacier) - archival
  cold: {
    duration: '7 years',
    storage: 's3',
    storageClass: 'GLACIER',
    path: 'audit-logs-archive/',
  },

  // Per-category overrides
  overrides: {
    auth_logs: { hot: '90 days', warm: '7 years', cold: 'forever' },
    security_events: { hot: '90 days', warm: 'forever', cold: 'forever' },
    api_logs: { hot: '7 days', warm: '30 days', cold: 'none' },
    audit_logs: { hot: '30 days', warm: '7 years', cold: 'forever' },
  },
};
```

### Archive Service

```typescript
export class ArchiveService {
  async archiveLogs(): Promise<void> {
    // Find indices older than hot retention
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 30);

    const indicesToArchive = await this.findIndicesOlderThan(cutoffDate);

    for (const index of indicesToArchive) {
      await this.archiveIndex(index);
    }
  }

  private async archiveIndex(index: string): Promise<void> {
    // Export all documents from index
    const documents = await this.exportIndex(index);

    // Upload to S3
    const key = `audit-logs/${index}/${Date.now()}.ndjson`;
    const body = documents.map((d) => JSON.stringify(d)).join('\n');

    await this.s3.send(new PutObjectCommand({
      Bucket: process.env.AUDIT_LOG_BUCKET!,
      Key: key,
      Body: body,
      StorageClass: 'STANDARD',
      ServerSideEncryption: 'AES256',
      Metadata: {
        originalIndex: index,
        archivedAt: new Date().toISOString(),
      },
    }));

    // Delete index after successful archival
    await this.elasticsearch.indices.delete({ index });
  }

  private async findIndicesOlderThan(date: Date): Promise<string[]> {
    const { indices } = await this.elasticsearch.cat.indices({
      format: 'json',
    });

    return indices
      .filter((i) => i.index.startsWith('audit-'))
      .filter((i) => {
        const indexDate = this.parseIndexDate(i.index);
        return indexDate < date;
      })
      .map((i) => i.index);
  }

  private async exportIndex(index: string): Promise<any[]> {
    const result = await this.elasticsearch.helpers.bulk({
      datasource: {
        index,
        size: 1000,
      },
      onDocument: (doc) => doc,
    });

    return result;
  }

  private parseIndexDate(index: string): Date {
    // Parse date from index name (e.g., audit-2024-01)
    const match = index.match(/audit-(\d{4})-(\d{2})/);
    if (!match) return new Date();

    const [, year, month] = match;
    return new Date(parseInt(year), parseInt(month) - 1, 1);
  }
}
```

---

**Last Updated:** 2026-04-25

**Series Complete:** Security Architecture Deep Dive Series (4/4 documents)
