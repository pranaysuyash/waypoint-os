# Tenant Operations — Technical Deep Dive

> Comprehensive guide to tenant operations, monitoring, and lifecycle management for the Travel Agency Agent platform

---

## Document Metadata

**Series:** Multi-tenancy Patterns
**Document:** 4 of 4 (Operations)
**Last Updated:** 2026-04-26
**Status:** ✅ Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Tenant Monitoring](#tenant-monitoring)
3. [Per-Tenant Performance Tracking](#per-tenant-performance-tracking)
4. [Resource Quota Management](#resource-quota-management)
5. [Billing and Metering](#billing-and-metering)
6. [Tenant Lifecycle Management](#tenant-lifecycle-management)
7. [Data Export and Portability](#data-export-and-portability)
8. [Support Workflows](#support-workflows)
9. [Implementation](#implementation)
10. [Testing Scenarios](#testing-scenarios)
11. [API Specification](#api-specification)
12. [Metrics and Monitoring](#metrics-and-monitoring)

---

## Overview

Tenant operations encompass the ongoing management of tenants throughout their lifecycle, including monitoring, billing, support, and lifecycle changes like upgrades, suspensions, and termination.

### Operations Areas

- **Monitoring:** Track tenant health, performance, and usage
- **Metering:** Measure resource consumption for billing
- **Lifecycle:** Manage tenant state changes
- **Support:** Handle tenant requests and issues
- **Maintenance:** Perform upgrades and migrations

### Operational Goals

- **Visibility:** Complete observability into each tenant's usage
- **Fairness:** Prevent "noisy neighbor" problems
- **Revenue:** Accurate billing based on usage
- **Retention:** Proactive support to prevent churn
- **Efficiency:** Automated operations at scale

---

## Tenant Monitoring

### Health Monitoring

```typescript
/**
 * Tenant health status
 */
enum TenantHealthStatus {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNHEALTHY = 'unhealthy',
  OFFLINE = 'offline'
}

interface TenantHealth {
  tenantId: string;
  status: TenantHealthStatus;
  checks: HealthCheck[];
  lastChecked: Date;
  issues: HealthIssue[];
}

interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  latency?: number;
  message?: string;
}

interface HealthIssue {
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
  affectedResources: string[];
  startedAt: Date;
}

/**
 * Tenant health monitor
 */
class TenantHealthMonitor {
  private checks: Map<string, HealthCheckFunction[]>;
  private issueTrackers: Map<string, HealthIssue[]>;

  constructor() {
    this.checks = new Map();
    this.issueTrackers = new Map();
  }

  /**
   * Register health check for tenant
   */
  registerCheck(tenantId: string, check: HealthCheckFunction): void {
    if (!this.checks.has(tenantId)) {
      this.checks.set(tenantId, []);
    }
    this.checks.get(tenantId)!.push(check);
  }

  /**
   * Run health checks for tenant
   */
  async checkHealth(tenantId: string): Promise<TenantHealth> {
    const checks = this.checks.get(tenantId) || this.getDefaultChecks();
    const results: HealthCheck[] = [];
    const issues: HealthIssue[] = [];

    for (const check of checks) {
      try {
        const result = await check();
        results.push(result);

        if (result.status === 'fail' || result.status === 'warn') {
          issues.push({
            severity: result.status === 'fail' ? 'high' : 'medium',
            category: check.name,
            description: result.message || `${check.name} failed`,
            affectedResources: [],
            startedAt: new Date()
          });
        }
      } catch (error) {
        results.push({
          name: check.name,
          status: 'fail',
          message: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    const status = this.determineHealthStatus(results);

    return {
      tenantId,
      status,
      checks: results,
      lastChecked: new Date(),
      issues
    };
  }

  /**
   * Get default health checks
   */
  private getDefaultChecks(): HealthCheckFunction[] {
    return [
      this.databaseHealthCheck,
      this.cacheHealthCheck,
      this.apiHealthCheck,
      this.workerHealthCheck,
      this.storageHealthCheck
    ];
  }

  /**
   * Database health check
   */
  private databaseHealthCheck = async (): Promise<HealthCheck> => {
    const start = Date.now();

    try {
      await db.execute('SELECT 1');
      const latency = Date.now() - start;

      return {
        name: 'database',
        status: latency < 100 ? 'pass' : latency < 500 ? 'warn' : 'fail',
        latency,
        message: `Database responding in ${latency}ms`
      };
    } catch (error) {
      return {
        name: 'database',
        status: 'fail',
        message: 'Database connection failed'
      };
    }
  };

  /**
   * Cache health check
   */
  private cacheHealthCheck = async (): Promise<HealthCheck> => {
    const start = Date.now();

    try {
      await cache.ping();
      const latency = Date.now() - start;

      return {
        name: 'cache',
        status: latency < 50 ? 'pass' : latency < 200 ? 'warn' : 'fail',
        latency,
        message: `Cache responding in ${latency}ms`
      };
    } catch (error) {
      return {
        name: 'cache',
        status: 'warn',
        message: 'Cache connection failed'
      };
    }
  };

  /**
   * API health check
   */
  private apiHealthCheck = async (): Promise<HealthCheck> => {
    // Implementation depends on API setup
    return {
      name: 'api',
      status: 'pass',
      message: 'API healthy'
    };
  };

  /**
   * Worker health check
   */
  private workerHealthCheck = async (): Promise<HealthCheck> => {
    // Check worker queue depth
    const queueDepth = await workerQueue.getDepth();

    return {
      name: 'worker',
      status: queueDepth < 1000 ? 'pass' : queueDepth < 5000 ? 'warn' : 'fail',
      message: `Worker queue depth: ${queueDepth}`
    };
  };

  /**
   * Storage health check
   */
  private storageHealthCheck = async (): Promise<HealthCheck> => {
    try {
      await storage.healthCheck();
      return {
        name: 'storage',
        status: 'pass',
        message: 'Storage accessible'
      };
    } catch (error) {
      return {
        name: 'storage',
        status: 'fail',
        message: 'Storage unavailable'
      };
    }
  };

  /**
   * Determine overall health status
   */
  private determineHealthStatus(checks: HealthCheck[]): TenantHealthStatus {
    const failed = checks.filter(c => c.status === 'fail').length;
    const warned = checks.filter(c => c.status === 'warn').length;

    if (failed > 0) return TenantHealthStatus.UNHEALTHY;
    if (warned > 0) return TenantHealthStatus.DEGRADED;
    return TenantHealthStatus.HEALTHY;
  }

  /**
   * Run health checks for all tenants
   */
  async checkAllTenants(): Promise<Map<string, TenantHealth>> {
    const tenants = await db.query.tenants.findMany({
      where: eq(tenants.status, 'active')
    });

    const results = new Map<string, TenantHealth>();

    for (const tenant of tenants) {
      const health = await this.checkHealth(tenant.id);
      results.set(tenant.id, health);

      // Store health result
      await this.storeHealthResult(health);
    }

    return results;
  }

  /**
   * Store health check result
   */
  private async storeHealthResult(health: TenantHealth): Promise<void> {
    await db.insert(tenantHealthHistory).values({
      id: generateId(),
      tenantId: health.tenantId,
      status: health.status,
      checks: JSON.stringify(health.checks),
      issues: JSON.stringify(health.issues),
      checkedAt: health.lastChecked
    });
  }
}

type HealthCheckFunction = () => Promise<HealthCheck>;
```

### Alerting

```typescript
/**
 * Tenant alert manager
 */
class TenantAlertManager {
  private alertRules: AlertRule[];
  private notificationChannels: NotificationChannel[];

  constructor() {
    this.alertRules = this.getDefaultRules();
    this.notificationChannels = [
      new EmailNotificationChannel(),
      new SlackNotificationChannel(),
      new PagerDutyNotificationChannel()
    ];
  }

  /**
   * Evaluate alert rules for tenant
   */
  async evaluateAlerts(tenantId: string, health: TenantHealth): Promise<Alert[]> {
    const alerts: Alert[] = [];

    for (const rule of this.alertRules) {
      const result = await this.evaluateRule(rule, tenantId, health);

      if (result.shouldAlert) {
        const alert: Alert = {
          id: generateId(),
          tenantId,
          ruleId: rule.id,
          severity: rule.severity,
          title: rule.title,
          description: result.description,
          triggeredAt: new Date(),
          status: 'open',
          metadata: result.metadata
        };

        alerts.push(alert);

        // Store alert
        await this.storeAlert(alert);

        // Send notifications
        await this.sendNotifications(alert);
      }
    }

    return alerts;
  }

  /**
   * Evaluate alert rule
   */
  private async evaluateRule(
    rule: AlertRule,
    tenantId: string,
    health: TenantHealth
  ): Promise<{ shouldAlert: boolean; description?: string; metadata?: Record<string, unknown> }> {
    switch (rule.type) {
      case 'health_status':
        return {
          shouldAlert: health.status !== TenantHealthStatus.HEALTHY,
          description: `Tenant health is ${health.status}`,
          metadata: { healthStatus: health.status }
        };

      case 'error_rate':
        const errorRate = await this.getErrorRate(tenantId, rule.window);
        return {
          shouldAlert: errorRate > rule.threshold,
          description: `Error rate is ${errorRate}% (threshold: ${rule.threshold}%)`,
          metadata: { errorRate, threshold: rule.threshold }
        };

      case 'response_time':
        const avgResponseTime = await this.getAverageResponseTime(tenantId, rule.window);
        return {
          shouldAlert: avgResponseTime > rule.threshold,
          description: `Average response time is ${avgResponseTime}ms (threshold: ${rule.threshold}ms)`,
          metadata: { avgResponseTime, threshold: rule.threshold }
        };

      case 'quota_exceeded':
        const usage = await this.getQuotaUsage(tenantId, rule.resource);
        return {
          shouldAlert: usage.percent > rule.threshold,
          description: `${rule.resource} usage is ${usage.percent}% (threshold: ${rule.threshold}%)`,
          metadata: { usage }
        };

      default:
        return { shouldAlert: false };
    }
  }

  /**
   * Get error rate for tenant
   */
  private async getErrorRate(tenantId: string, window: number): Promise<number> {
    const since = new Date(Date.now() - window);

    const result = await db.execute(`
      SELECT
        COUNT(*) FILTER (WHERE status >= 500) as errors,
        COUNT(*) as total
      FROM request_logs
      WHERE tenant_id = '${tenantId}'
        AND timestamp > '${since.toISOString()}'
    `);

    const { errors, total } = result.rows[0];
    return total > 0 ? (errors / total) * 100 : 0;
  }

  /**
   * Get average response time for tenant
   */
  private async getAverageResponseTime(tenantId: string, window: number): Promise<number> {
    const since = new Date(Date.now() - window);

    const result = await db.execute(`
      SELECT AVG(response_time) as avg_time
      FROM request_logs
      WHERE tenant_id = '${tenantId}'
        AND timestamp > '${since.toISOString()}'
    `);

    return Math.round(result.rows[0]?.avg_time || 0);
  }

  /**
   * Get quota usage for tenant
   */
  private async getQuotaUsage(
    tenantId: string,
    resource: string
  ): Promise<{ used: number; limit: number; percent: number }> {
    const quotaManager = new ResourceQuotaManager();
    const usage = await quotaManager.getCurrentUsage(tenantId);
    const quota = await quotaManager.getQuota(tenantId);

    const limit = (quota as any)[resource] || 0;
    const used = (usage as any)[resource] || 0;
    const percent = limit > 0 ? (used / limit) * 100 : 0;

    return { used, limit, percent };
  }

  /**
   * Send notifications for alert
   */
  private async sendNotifications(alert: Alert): Promise<void> {
    for (const channel of this.notificationChannels) {
      if (channel.shouldSend(alert)) {
        await channel.send(alert);
      }
    }
  }

  /**
   * Store alert
   */
  private async storeAlert(alert: Alert): Promise<void> {
    await db.insert(tenantAlerts).values(alert);
  }

  /**
   * Get default alert rules
   */
  private getDefaultRules(): AlertRule[] {
    return [
      {
        id: 'health-status',
        type: 'health_status',
        severity: 'high',
        title: 'Tenant Unhealthy',
        threshold: 0,
        window: 0
      },
      {
        id: 'error-rate',
        type: 'error_rate',
        severity: 'medium',
        title: 'High Error Rate',
        threshold: 5, // 5%
        window: 300000 // 5 minutes
      },
      {
        id: 'response-time',
        type: 'response_time',
        severity: 'medium',
        title: 'Slow Response Time',
        threshold: 1000, // 1 second
        window: 300000
      },
      {
        id: 'storage-quota',
        type: 'quota_exceeded',
        severity: 'medium',
        title: 'Storage Quota Exceeded',
        threshold: 90, // 90%
        window: 0,
        resource: 'storage'
      }
    ];
  }
}

interface AlertRule {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  threshold: number;
  window: number;
  resource?: string;
}

interface Alert {
  id: string;
  tenantId: string;
  ruleId: string;
  severity: string;
  title: string;
  description: string;
  triggeredAt: Date;
  status: 'open' | 'acknowledged' | 'resolved';
  metadata?: Record<string, unknown>;
}
```

---

## Per-Tenant Performance Tracking

### Performance Metrics Collector

```typescript
/**
 * Tenant performance metrics
 */
interface TenantPerformanceMetrics {
  tenantId: string;
  period: {
    start: Date;
    end: Date;
  };
  requests: {
    total: number;
    success: number;
    error: number;
    avgResponseTime: number;
    p50ResponseTime: number;
    p95ResponseTime: number;
    p99ResponseTime: number;
  };
  database: {
    avgQueryTime: number;
    slowQueries: number;
    connectionPoolUsage: number;
  };
  cache: {
    hitRate: number;
    missRate: number;
    avgResponseTime: number;
  };
  storage: {
    readBytes: number;
    writeBytes: number;
    readCount: number;
    writeCount: number;
  };
}

/**
 * Performance metrics collector
 */
class PerformanceMetricsCollector {
  /**
   * Collect metrics for tenant
   */
  async collectMetrics(
    tenantId: string,
    period: { start: Date; end: Date }
  ): Promise<TenantPerformanceMetrics> {
    const [requests, database, cache, storage] = await Promise.all([
      this.collectRequestMetrics(tenantId, period),
      this.collectDatabaseMetrics(tenantId, period),
      this.collectCacheMetrics(tenantId, period),
      this.collectStorageMetrics(tenantId, period)
    ]);

    return {
      tenantId,
      period,
      requests,
      database,
      cache,
      storage
    };
  }

  /**
   * Collect request metrics
   */
  private async collectRequestMetrics(
    tenantId: string,
    period: { start: Date; end: Date }
  ): Promise<TenantPerformanceMetrics['requests']> {
    const result = await db.execute(`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status < 400) as success,
        COUNT(*) FILTER (WHERE status >= 400) as error,
        AVG(response_time) as avg_response_time,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time) as p50,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time) as p95,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time) as p99
      FROM request_logs
      WHERE tenant_id = '${tenantId}'
        AND timestamp BETWEEN '${period.start.toISOString()}' AND '${period.end.toISOString()}'
    `);

    const row = result.rows[0];

    return {
      total: parseInt(row.total),
      success: parseInt(row.success),
      error: parseInt(row.error),
      avgResponseTime: Math.round(row.avg_response_time || 0),
      p50ResponseTime: Math.round(row.p50 || 0),
      p95ResponseTime: Math.round(row.p95 || 0),
      p99ResponseTime: Math.round(row.p99 || 0)
    };
  }

  /**
   * Collect database metrics
   */
  private async collectDatabaseMetrics(
    tenantId: string,
    period: { start: Date; end: Date }
  ): Promise<TenantPerformanceMetrics['database']> {
    const result = await db.execute(`
      SELECT
        AVG(duration) as avg_query_time,
        COUNT(*) FILTER (WHERE duration > 1000) as slow_queries
      FROM query_logs
      WHERE tenant_id = '${tenantId}'
        AND timestamp BETWEEN '${period.start.toISOString()}' AND '${period.end.toISOString()}'
    `);

    // Get connection pool usage
    const poolUsage = await this.getConnectionPoolUsage(tenantId);

    return {
      avgQueryTime: Math.round(result.rows[0]?.avg_query_time || 0),
      slowQueries: parseInt(result.rows[0]?.slow_queries || '0'),
      connectionPoolUsage: poolUsage
    };
  }

  /**
   * Collect cache metrics
   */
  private async collectCacheMetrics(
    tenantId: string,
    period: { start: Date; end: Date }
  ): Promise<TenantPerformanceMetrics['cache']> {
    const result = await db.execute(`
      SELECT
        COUNT(*) FILTER (WHERE hit = true) as hits,
        COUNT(*) FILTER (WHERE hit = false) as misses,
        AVG(duration) as avg_duration
      FROM cache_logs
      WHERE tenant_id = '${tenantId}'
        AND timestamp BETWEEN '${period.start.toISOString()}' AND '${period.end.toISOString()}'
    `);

    const row = result.rows[0];
    const total = (parseInt(row.hits || '0')) + (parseInt(row.misses || '0'));

    return {
      hitRate: total > 0 ? (parseInt(row.hits) / total) * 100 : 0,
      missRate: total > 0 ? (parseInt(row.misses) / total) * 100 : 0,
      avgResponseTime: Math.round(row.avg_duration || 0)
    };
  }

  /**
   * Collect storage metrics
   */
  private async collectStorageMetrics(
    tenantId: string,
    period: { start: Date; end: Date }
  ): Promise<TenantPerformanceMetrics['storage']> {
    const result = await db.execute(`
      SELECT
        SUM(read_bytes) as read_bytes,
        SUM(write_bytes) as write_bytes,
        COUNT(*) FILTER (WHERE operation = 'read') as read_count,
        COUNT(*) FILTER (WHERE operation = 'write') as write_count
      FROM storage_logs
      WHERE tenant_id = '${tenantId}'
        AND timestamp BETWEEN '${period.start.toISOString()}' AND '${period.end.toISOString()}'
    `);

    const row = result.rows[0];

    return {
      readBytes: parseInt(row.read_bytes || '0'),
      writeBytes: parseInt(row.write_bytes || '0'),
      readCount: parseInt(row.read_count || '0'),
      writeCount: parseInt(row.write_count || '0')
    };
  }

  /**
   * Get connection pool usage for tenant
   */
  private async getConnectionPoolUsage(tenantId: string): Promise<number> {
    // Implementation depends on connection pool manager
    return 0;
  }

  /**
   * Compare tenant performance to baseline
   */
  async compareWithBaseline(
    tenantId: string,
    metrics: TenantPerformanceMetrics
  ): Promise<PerformanceComparison> {
    const baseline = await this.getBaseline(tenantId);

    return {
      tenantId,
      responseTimeDiff: metrics.requests.avgResponseTime - baseline.avgResponseTime,
      responseTimePercentChange: ((metrics.requests.avgResponseTime - baseline.avgResponseTime) / baseline.avgResponseTime) * 100,
      errorRateDiff: (metrics.requests.error / metrics.requests.total) * 100 - baseline.errorRate,
      slowQueryDiff: metrics.database.slowQueries - baseline.slowQueries,
      isDegraded: this.isPerformanceDegraded(metrics, baseline)
    };
  }

  /**
   * Get performance baseline for tenant
   */
  private async getBaseline(tenantId: string): Promise<{
    avgResponseTime: number;
    errorRate: number;
    slowQueries: number;
  }> {
    // Calculate from historical data (last 30 days)
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

    const result = await db.execute(`
      SELECT
        AVG(response_time) as avg_response_time,
        AVG(error_rate) as avg_error_rate,
        AVG(slow_queries) as avg_slow_queries
      FROM tenant_performance_daily
      WHERE tenant_id = '${tenantId}'
        AND date > '${thirtyDaysAgo.toISOString()}'
    `);

    const row = result.rows[0];

    return {
      avgResponseTime: Math.round(row.avg_response_time || 500),
      errorRate: parseFloat(row.avg_error_rate || '1'),
      slowQueries: Math.round(row.avg_slow_queries || 10)
    };
  }

  /**
   * Check if performance is degraded
   */
  private isPerformanceDegraded(
    metrics: TenantPerformanceMetrics,
    baseline: { avgResponseTime: number; errorRate: number; slowQueries: number }
  ): boolean {
    const errorRate = (metrics.requests.error / metrics.requests.total) * 100;

    return (
      metrics.requests.avgResponseTime > baseline.avgResponseTime * 1.5 ||
      errorRate > baseline.errorRate * 2 ||
      metrics.database.slowQueries > baseline.slowQueries * 2
    );
  }
}

interface PerformanceComparison {
  tenantId: string;
  responseTimeDiff: number;
  responseTimePercentChange: number;
  errorRateDiff: number;
  slowQueryDiff: number;
  isDegraded: boolean;
}
```

---

## Resource Quota Management

### Quota Enforcement

```typescript
/**
 * Quota enforcement service
 */
class QuotaEnforcementService {
  private quotaManager: ResourceQuotaManager;

  constructor() {
    this.quotaManager = new ResourceQuotaManager();
  }

  /**
   * Check quota before operation
   */
  async checkQuota(
    tenantId: string,
    resource: keyof ResourceUsage,
    amount = 1
  ): Promise<QuotaCheckResult> {
    const quota = await this.quotaManager.getQuota(tenantId);
    const usage = await this.quotaManager.getCurrentUsage(tenantId);

    const quotaKey = this.mapResourceToQuotaKey(resource);
    const limit = (quota as any)[quotaKey] || -1; // -1 = unlimited
    const current = (usage as any)[resource] || 0;

    if (limit === -1) {
      return { allowed: true, remaining: -1, percentUsed: 0 };
    }

    const remaining = limit - current;
    const percentUsed = (current / limit) * 100;

    if (current + amount > limit) {
      return {
        allowed: false,
        remaining,
        percentUsed,
        reason: `Quota exceeded for ${resource}. Current: ${current}, Limit: ${limit}`
      };
    }

    return { allowed: true, remaining: remaining - amount, percentUsed };
  }

  /**
   * Record resource usage
   */
  async recordUsage(
    tenantId: string,
    resource: keyof ResourceUsage,
    amount: number
  ): Promise<void> {
    await this.quotaManager.recordConsumption(tenantId, resource, amount);

    // Log usage for billing
    await this.logUsage(tenantId, resource, amount);
  }

  /**
   * Get quota status for tenant
   */
  async getQuotaStatus(tenantId: string): Promise<QuotaStatus> {
    const quota = await this.quotaManager.getQuota(tenantId);
    const usage = await this.quotaManager.getCurrentUsage(tenantId);

    const resources: Array<{ name: string; used: number; limit: number; percent: number }> = [];

    for (const [key, value] of Object.entries(usage)) {
      const quotaKey = this.mapResourceToQuotaKey(key as keyof ResourceUsage);
      const limit = (quota as any)[quotaKey] || -1;

      resources.push({
        name: key,
        used: value as number,
        limit,
        percent: limit > 0 ? ((value as number) / limit) * 100 : 0
      });
    }

    return {
      tenantId,
      resources,
      tier: await this.getTenantTier(tenantId)
    };
  }

  /**
   * Set quota for tenant
   */
  async setQuota(
    tenantId: string,
    resource: string,
    limit: number
  ): Promise<void> {
    await db.insert(tenantQuotas).values({
      id: generateId(),
      tenantId,
      resource,
      limit,
      updatedAt: new Date()
    }).onConflictDoUpdate({
      target: [tenantQuotas.tenantId, tenantQuotas.resource],
      set: { limit, updatedAt: new Date() }
    });

    this.quotaManager.setQuota(tenantId, {
      ...await this.quotaManager.getQuota(tenantId),
      [resource]: limit
    });
  }

  private mapResourceToQuotaKey(resource: keyof ResourceUsage): string {
    const mapping: Record<keyof ResourceUsage, string> = {
      cpuPercent: 'maxCpuPercent',
      memoryMB: 'maxMemoryMB',
      connections: 'maxConnections',
      requestsThisMinute: 'maxRequestsPerMinute',
      storageGB: 'maxStorageGB',
      concurrentJobs: 'maxConcurrentJobs'
    };
    return mapping[resource];
  }

  private async logUsage(
    tenantId: string,
    resource: string,
    amount: number
  ): Promise<void> {
    await db.insert(usageLogs).values({
      id: generateId(),
      tenantId,
      resource,
      amount,
      timestamp: new Date()
    });
  }

  private async getTenantTier(tenantId: string): Promise<TenantTier> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });
    return tenant?.tier || TenantTier.STARTUP;
  }
}

interface QuotaCheckResult {
  allowed: boolean;
  remaining: number;
  percentUsed: number;
  reason?: string;
}

interface QuotaStatus {
  tenantId: string;
  tier: TenantTier;
  resources: Array<{
    name: string;
    used: number;
    limit: number;
    percent: number;
  }>;
}
```

---

## Billing and Metering

### Usage Meter

```typescript
/**
 * Usage meter for billing
 */
class UsageMeter {
  /**
   * Record billable usage
   */
  async recordUsage(
    tenantId: string,
    usage: {
      resourceType: string;
      amount: number;
      unit: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<void> {
    await db.insert(billingUsage).values({
      id: generateId(),
      tenantId,
      ...usage,
      timestamp: new Date()
    });
  }

  /**
   * Get usage for billing period
   */
  async getUsageForPeriod(
    tenantId: string,
    period: { start: Date; end: Date }
  ): Promise<BillingUsage> {
    const result = await db.execute(`
      SELECT
        resource_type,
        unit,
        SUM(amount) as total_amount,
        COUNT(*) as usage_count
      FROM billing_usage
      WHERE tenant_id = '${tenantId}'
        AND timestamp BETWEEN '${period.start.toISOString()}' AND '${period.end.toISOString()}'
      GROUP BY resource_type, unit
    `);

    const resources: Record<string, { amount: number; unit: string; count: number }> = {};

    for (const row of result.rows) {
      resources[row.resource_type] = {
        amount: parseFloat(row.total_amount),
        unit: row.unit,
        count: parseInt(row.usage_count)
      };
    }

    return {
      tenantId,
      period,
      resources,
      totalCost: 0 // Calculated by billing service
    };
  }

  /**
   * Calculate bill for period
   */
  async calculateBill(
    tenantId: string,
    period: { start: Date; end: Date }
  ): Promise<Bill> {
    const usage = await this.getUsageForPeriod(tenantId, period);
    const pricing = await this.getPricingPlan(tenantId);

    let lineItems: LineItem[] = [];
    let subtotal = 0;

    // Base fee
    lineItems.push({
      description: 'Base subscription',
      quantity: 1,
      unitPrice: pricing.baseFee,
      amount: pricing.baseFee
    });
    subtotal += pricing.baseFee;

    // Usage-based charges
    for (const [resourceType, usageData] of Object.entries(usage.resources)) {
      const rate = pricing.rates[resourceType];

      if (rate) {
        const amount = usageData.amount * rate.price;
        lineItems.push({
          description: rate.description || resourceType,
          quantity: usageData.amount,
          unitPrice: rate.price,
          unit: usageData.unit,
          amount
        });
        subtotal += amount;
      }
    }

    // Calculate total
    const tax = subtotal * pricing.taxRate;
    const total = subtotal + tax;

    return {
      id: generateId(),
      tenantId,
      period,
      lineItems,
      subtotal,
      tax,
      taxRate: pricing.taxRate,
      total,
      currency: pricing.currency,
      generatedAt: new Date()
    };
  }

  /**
   * Get pricing plan for tenant
   */
  private async getPricingPlan(tenantId: string): Promise<PricingPlan> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    const tier = tenant?.tier || TenantTier.STARTUP;

    return pricingPlans[tier];
  }
}

interface BillingUsage {
  tenantId: string;
  period: { start: Date; end: Date };
  resources: Record<string, { amount: number; unit: string; count: number }>;
  totalCost: number;
}

interface Bill {
  id: string;
  tenantId: string;
  period: { start: Date; end: Date };
  lineItems: LineItem[];
  subtotal: number;
  tax: number;
  taxRate: number;
  total: number;
  currency: string;
  generatedAt: Date;
}

interface LineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  unit?: string;
  amount: number;
}

interface PricingPlan {
  baseFee: number;
  currency: string;
  taxRate: number;
  rates: Record<string, { price: number; description?: string }>;
}

// Pricing plans by tier
const pricingPlans: Record<TenantTier, PricingPlan> = {
  [TenantTier.STARTUP]: {
    baseFee: 0,
    currency: 'USD',
    taxRate: 0,
    rates: {
      users: { price: 0, description: 'Active users (included: 5)' },
      trips: { price: 0, description: 'Trips (included: 500)' },
      storage: { price: 0, description: 'Storage (included: 10GB)' }
    }
  },
  [TenantTier.GROWTH]: {
    baseFee: 99,
    currency: 'USD',
    taxRate: 0.1,
    rates: {
      users: { price: 5, description: 'Additional users' },
      trips: { price: 0.5, description: 'Additional trips (beyond 10,000)' },
      storage: { price: 1, description: 'Additional storage per GB (beyond 100GB)' }
    }
  },
  [TenantTier.ENTERPRISE]: {
    baseFee: 499,
    currency: 'USD',
    taxRate: 0.1,
    rates: {
      users: { price: 3, description: 'Users (unlimited base)' },
      trips: { price: 0.1, description: 'Trips' },
      storage: { price: 0.5, description: 'Storage per GB' }
    }
  }
};
```

---

## Tenant Lifecycle Management

### Tier Changes

```typescript
/**
 * Tenant lifecycle manager
 */
class TenantLifecycleManager {
  private migrationService: TenantMigrationService;

  constructor() {
    this.migrationService = new TenantMigrationService();
  }

  /**
   * Upgrade tenant tier
   */
  async upgradeTier(
    tenantId: string,
    toTier: TenantTier,
    options?: {
      scheduleFor?: Date;
      confirmRequired?: boolean;
    }
  ): Promise<TenantMigration> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    if (!tenant) {
      throw new Error('Tenant not found');
    }

    if (!this.isValidUpgrade(tenant.tier, toTier)) {
      throw new Error('Invalid tier upgrade');
    }

    if (options?.confirmRequired) {
      // Send confirmation request
      await this.sendUpgradeConfirmation(tenantId, tenant.tier, toTier);
      // Wait for confirmation...
    }

    if (options?.scheduleFor) {
      // Schedule upgrade
      return this.scheduleMigration(tenantId, toTier, options.scheduleFor);
    }

    // Execute immediately
    return this.migrationService.upgrade(tenantId, toTier);
  }

  /**
   * Downgrade tenant tier
   */
  async downgradeTier(
    tenantId: string,
    toTier: TenantTier,
    options?: {
      force?: boolean;
      dataHandling?: 'keep' | 'archive' | 'delete';
    }
  ): Promise<void> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    if (!tenant) {
      throw new Error('Tenant not found');
    }

    if (!this.isValidDowngrade(tenant.tier, toTier)) {
      throw new Error('Invalid tier downgrade');
    }

    // Check quota compliance
    if (!options?.force) {
      const compliance = await this.checkQuotaCompliance(tenantId, toTier);
      if (!compliance.compliant) {
        throw new Error(`Cannot downgrade: ${compliance.reason}`);
      }
    }

    // Handle data based on option
    switch (options?.dataHandling) {
      case 'archive':
        await this.archiveExcessData(tenantId, toTier);
        break;
      case 'delete':
        await this.deleteExcessData(tenantId, toTier);
        break;
    }

    // Update tier
    await db.update(tenants)
      .set({
        tier: toTier,
        multiTenancyModel: tierConfigs[toTier].multiTenancyModel,
        downgradedAt: new Date()
      })
      .where(eq(tenants.id, tenantId));

    // Apply new configuration
    await applyConfigurationTemplate(tenantId, toTier);
  }

  /**
   * Suspend tenant
   */
  async suspendTenant(
    tenantId: string,
    reason: string,
    options?: {
      suspendBilling?: boolean;
      notifyUsers?: boolean;
      gracePeriodDays?: number;
    }
  ): Promise<void> {
    const updates: any = {
      status: 'suspended',
      suspensionReason: reason,
      suspendedAt: new Date()
    };

    if (options?.gracePeriodDays) {
      updates.gracePeriodUntil = new Date(
        Date.now() + options.gracePeriodDays * 24 * 60 * 60 * 1000
      );
      updates.status = 'grace_period';
    }

    await db.update(tenants)
      .set(updates)
      .where(eq(tenants.id, tenantId));

    // Revoke all sessions
    await db.delete(sessions)
      .where(eq(sessions.tenantId, tenantId));

    // Suspend billing if requested
    if (options?.suspendBilling) {
      await this.suspendBilling(tenantId);
    }

    // Notify users
    if (options?.notifyUsers) {
      await this.notifySuspension(tenantId, reason);
    }
  }

  /**
   * Reactivate tenant
   */
  async reactivateTenant(tenantId: string): Promise<void> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    if (!tenant) {
      throw new Error('Tenant not found');
    }

    if (tenant.status !== 'suspended' && tenant.status !== 'grace_period') {
      throw new Error('Tenant is not suspended');
    }

    await db.update(tenants)
      .set({
        status: 'active',
        suspensionReason: null,
        suspendedAt: null,
        reactivatedAt: new Date()
      })
      .where(eq(tenants.id, tenantId));

    // Resume billing
    await this.resumeBilling(tenantId);

    // Notify users
    await this.notifyReactivation(tenantId);
  }

  /**
   * Terminate tenant
   */
  async terminateTenant(
    tenantId: string,
    options: {
      reason: string;
      exportData?: boolean;
      retentionDays?: number;
      notifyUsers?: boolean;
    }
  ): Promise<void> {
    // Export data if requested
    let exportUrl;
    if (options.exportData) {
      exportUrl = await this.exportTenantData(tenantId);
    }

    // Mark for termination
    await db.update(tenants)
      .set({
        status: 'terminated',
        terminationReason: options.reason,
        terminatedAt: new Date(),
        dataExportUrl: exportUrl,
        deletionScheduledFor: new Date(
          Date.now() + (options.retentionDays || 30) * 24 * 60 * 60 * 1000
        )
      })
      .where(eq(tenants.id, tenantId));

    // Revoke all access
    await db.delete(sessions)
      .where(eq(sessions.tenantId, tenantId));

    // Cancel billing
    await this.cancelBilling(tenantId);

    // Notify users
    if (options.notifyUsers) {
      await this.notifyTermination(tenantId, options.reason, exportUrl);
    }
  }

  /**
   * Delete tenant data (after retention period)
   */
  async deleteTenantData(tenantId: string): Promise<void> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    if (!tenant || tenant.status !== 'terminated') {
      throw new Error('Can only delete data for terminated tenants');
    }

    // Delete all tenant data
    const schemaProvisioner = new DatabaseSchemaProvisioner();
    await schemaProvisioner.dropTenantSchema(tenantId, tenant.tier);

    // Mark as deleted
    await db.update(tenants)
      .set({
        status: 'deleted',
        dataDeletedAt: new Date()
      })
      .where(eq(tenants.id, tenantId));
  }

  /**
   * Check quota compliance for tier
   */
  private async checkQuotaCompliance(
    tenantId: string,
    tier: TenantTier
  ): Promise<{ compliant: boolean; reason?: string }> {
    const quota = tierConfigs[tier];
    const usage = await this.getCurrentUsage(tenantId);

    if (quota.maxUsers > 0 && usage.users > quota.maxUsers) {
      return {
        compliant: false,
        reason: `Too many users: ${usage.users} > ${quota.maxUsers}`
      };
    }

    if (quota.maxTrips > 0 && usage.trips > quota.maxTrips) {
      return {
        compliant: false,
        reason: `Too many trips: ${usage.trips} > ${quota.maxTrips}`
      };
    }

    return { compliant: true };
  }

  private isValidUpgrade(from: TenantTier, to: TenantTier): boolean {
    const order = [TenantTier.STARTUP, TenantTier.GROWTH, TenantTier.ENTERPRISE];
    return order.indexOf(to) > order.indexOf(from);
  }

  private isValidDowngrade(from: TenantTier, to: TenantTier): boolean {
    const order = [TenantTier.STARTUP, TenantTier.GROWTH, TenantTier.ENTERPRISE];
    return order.indexOf(to) < order.indexOf(from);
  }

  private async getCurrentUsage(tenantId: string): Promise<{
    users: number;
    trips: number;
    storage: number;
  }> {
    // Implementation
    return { users: 0, trips: 0, storage: 0 };
  }

  private async archiveExcessData(tenantId: string, tier: TenantTier): Promise<void> { /* ... */ }
  private async deleteExcessData(tenantId: string, tier: TenantTier): Promise<void> { /* ... */ }
  private async suspendBilling(tenantId: string): Promise<void> { /* ... */ }
  private async resumeBilling(tenantId: string): Promise<void> { /* ... */ }
  private async cancelBilling(tenantId: string): Promise<void> { /* ... */ }
  private async sendUpgradeConfirmation(tenantId: string, from: TenantTier, to: TenantTier): Promise<void> { /* ... */ }
  private async scheduleMigration(tenantId: string, toTier: TenantTier, date: Date): Promise<TenantMigration> { /* ... */ }
  private async exportTenantData(tenantId: string): Promise<string> { /* ... */ }
  private async notifySuspension(tenantId: string, reason: string): Promise<void> { /* ... */ }
  private async notifyReactivation(tenantId: string): Promise<void> { /* ... */ }
  private async notifyTermination(tenantId: string, reason: string, exportUrl?: string): Promise<void> { /* ... */ }
}
```

---

## Data Export and Portability

### Data Export Service

```typescript
/**
 * Data export service for tenant portability
 */
class TenantDataExportService {
  /**
   * Export all tenant data
   */
  async exportAllData(
    tenantId: string,
    format: 'json' | 'csv' | 'sql' = 'json'
  ): Promise<ExportResult> {
    const exportId = generateId();
    const exportPath = `/exports/${tenantId}/${exportId}`;

    switch (format) {
      case 'json':
        return this.exportAsJSON(tenantId, exportPath);
      case 'csv':
        return this.exportAsCSV(tenantId, exportPath);
      case 'sql':
        return this.exportAsSQL(tenantId, exportPath);
    }
  }

  /**
   * Export as JSON
   */
  private async exportAsJSON(
    tenantId: string,
    exportPath: string
  ): Promise<ExportResult> {
    await RLSManager.setTenantContext(tenantId);

    const data = {
      version: '1.0',
      exportedAt: new Date().toISOString(),
      tenantId,
      entities: {
        customers: await db.query.customers.findMany(),
        trips: await db.query.trips.findMany(),
        bookings: await db.query.bookings.findMany(),
        quotes: await db.query.quotes.findMany(),
        tags: await db.query.tags.findMany(),
        configurations: await this.getConfigurations(tenantId)
      }
    };

    const json = JSON.stringify(data, null, 2);
    const filename = `${exportPath}/export.json`;

    await storage.put(filename, Buffer.from(json));

    await db.insert(dataExports).values({
      id: generateId(),
      tenantId,
      format: 'json',
      filename,
      size: json.length,
      status: 'completed',
      createdAt: new Date()
    });

    return {
      exportId: filename,
      format: 'json',
      size: json.length,
      downloadUrl: await storage.getSignedUrl(filename, 24 * 60 * 60)
    };
  }

  /**
   * Export as CSV
   */
  private async exportAsCSV(
    tenantId: string,
    exportPath: string
  ): Promise<ExportResult> {
    await RLSManager.setTenantContext(tenantId);

    const tables = ['customers', 'trips', 'bookings', 'quotes'];
    const files: string[] = [];
    let totalSize = 0;

    for (const table of tables) {
      const rows = await db.query[table].findMany();

      if (rows.length === 0) continue;

      const csv = this.toCSV(rows);
      const filename = `${exportPath}/${table}.csv`;

      await storage.put(filename, Buffer.from(csv));

      files.push(filename);
      totalSize += csv.length;
    }

    await db.insert(dataExports).values({
      id: generateId(),
      tenantId,
      format: 'csv',
      filename: exportPath,
      size: totalSize,
      status: 'completed',
      createdAt: new Date()
    });

    return {
      exportId: exportPath,
      format: 'csv',
      size: totalSize,
      downloadUrl: await storage.getSignedUrl(exportPath, 24 * 60 * 60),
      files
    };
  }

  /**
   * Export as SQL
   */
  private async exportAsSQL(
    tenantId: string,
    exportPath: string
  ): Promise<ExportResult> {
    await RLSManager.setTenantContext(tenantId);

    const tables = ['customers', 'trips', 'bookings', 'quotes'];
    let sql = `-- Tenant data export for ${tenantId}\n`;
    sql += `-- Exported at ${new Date().toISOString()}\n\n`;
    sql += `BEGIN;\n\n`;

    for (const table of tables) {
      const rows = await db.query[table].findMany();

      if (rows.length === 0) continue;

      sql += `-- Data for ${table}\n`;

      for (const row of rows) {
        const columns = Object.keys(row);
        const values = columns.map(col => this.formatSQLValue(row[col]));

        sql += `INSERT INTO ${table} (${columns.join(', ')}) VALUES (${values.join(', ')});\n`;
      }

      sql += '\n';
    }

    sql += `COMMIT;\n`;

    const filename = `${exportPath}/export.sql`;
    await storage.put(filename, Buffer.from(sql));

    await db.insert(dataExports).values({
      id: generateId(),
      tenantId,
      format: 'sql',
      filename,
      size: sql.length,
      status: 'completed',
      createdAt: new Date()
    });

    return {
      exportId: filename,
      format: 'sql',
      size: sql.length,
      downloadUrl: await storage.getSignedUrl(filename, 24 * 60 * 60)
    };
  }

  /**
   * Convert array of objects to CSV
   */
  private toCSV(data: any[]): string {
    if (data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];

    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        if (value === null || value === undefined) return '';
        if (typeof value === 'string') return `"${value.replace(/"/g, '""')}"`;
        return String(value);
      });
      csvRows.push(values.join(','));
    }

    return csvRows.join('\n');
  }

  /**
   * Format value for SQL
   */
  private formatSQLValue(value: unknown): string {
    if (value === null || value === undefined) return 'NULL';
    if (typeof value === 'string') return `'${value.replace(/'/g, "''")}'`;
    if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
    if (value instanceof Date) return `'${value.toISOString()}'`;
    return String(value);
  }

  /**
   * Get configurations for export
   */
  private async getConfigurations(tenantId: string): Promise<Record<string, unknown>> {
    const configs = await db.query.tenantConfig.findMany({
      where: eq(tenantConfig.tenantId, tenantId)
    });

    const result: Record<string, unknown> = {};

    for (const config of configs) {
      // Only include non-sensitive configs
      if (!config.isEncrypted) {
        result[config.key] = config.value;
      }
    }

    return result;
  }
}

interface ExportResult {
  exportId: string;
  format: string;
  size: number;
  downloadUrl: string;
  files?: string[];
}
```

---

## Support Workflows

### Support Ticket Management

```typescript
/**
 * Support ticket system
 */
class SupportTicketService {
  /**
   * Create support ticket
   */
  async createTicket(
    tenantId: string,
    input: {
      subject: string;
      description: string;
      category: string;
      priority: 'low' | 'medium' | 'high' | 'urgent';
      attachments?: string[];
      userId?: string;
    }
  ): Promise<SupportTicket> {
    // Check for duplicate tickets
    const duplicate = await this.findDuplicateTicket(tenantId, input);
    if (duplicate) {
      return duplicate;
    }

    // Auto-categorize using AI
    const category = await this.autoCategorize(input);

    // Assign priority score
    const priorityScore = this.calculatePriorityScore(
      input.priority,
      category,
      tenantId
    );

    // Assign to agent
    const assignedTo = await this.assignToAgent(category, priorityScore);

    const ticket = await db.insert(supportTickets).values({
      id: generateId(),
      tenantId,
      ...input,
      category,
      priorityScore,
      status: 'open',
      assignedTo,
      createdAt: new Date()
    }).returning().then(rows => rows[0]);

    // Send notification
    await this.notifyNewTicket(ticket);

    // Create SLA deadlines
    await this.createSLADeadlines(ticket);

    return ticket;
  }

  /**
   * Find duplicate ticket
   */
  private async findDuplicateTicket(
    tenantId: string,
    input: { subject: string; description: string }
  ): Promise<SupportTicket | null> {
    // Check for tickets with similar subject in last 7 days
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

    const similar = await db.query.supportTickets.findMany({
      where: and(
        eq(supportTickets.tenantId, tenantId),
        gte(supportTickets.createdAt, sevenDaysAgo),
        notInArray(supportTickets.status, ['closed', 'resolved'])
      )
    });

    // Use similarity matching
    for (const ticket of similar) {
      const similarity = this.calculateSimilarity(
        input.subject,
        ticket.subject
      );

      if (similarity > 0.8) {
        return ticket;
      }
    }

    return null;
  }

  /**
   * Calculate string similarity
   */
  private calculateSimilarity(str1: string, str2: string): number {
    // Simple implementation - could use more sophisticated algorithms
    const words1 = new Set(str1.toLowerCase().split(/\s+/));
    const words2 = new Set(str2.toLowerCase().split(/\s+/));

    const intersection = new Set(
      [...words1].filter(x => words2.has(x))
    );

    const union = new Set([...words1, ...words2]);

    return intersection.size / union.size;
  }

  /**
   * Auto-categorize ticket using AI
   */
  private async autoCategorize(
    input: { subject: string; description: string; category: string }
  ): Promise<string> {
    // If category provided, validate it
    const validCategories = [
      'technical',
      'billing',
      'feature_request',
      'bug_report',
      'account',
      'integration',
      'performance',
      'security'
    ];

    if (validCategories.includes(input.category)) {
      return input.category;
    }

    // Use AI to categorize
    const text = `${input.subject}\n${input.description}`;
    // AI categorization implementation
    return 'general';
  }

  /**
   * Calculate priority score
   */
  private calculatePriorityScore(
    priority: string,
    category: string,
    tenantId: string
  ): number {
    let score = 0;

    // Base priority
    const priorityValues = { low: 1, medium: 2, high: 3, urgent: 4 };
    score += priorityValues[priority] * 10;

    // Category multiplier
    const categoryMultipliers = {
      security: 2,
      billing: 1.5,
      technical: 1.2,
      bug_report: 1.2,
      performance: 1.1,
      feature_request: 0.5,
      account: 1,
      integration: 1
    };
    score *= categoryMultipliers[category] || 1;

    // Tenant tier multiplier
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    const tierMultipliers = {
      enterprise: 1.5,
      growth: 1.2,
      startup: 1
    };
    score *= tierMultipliers[tenant?.tier] || 1;

    return Math.round(score);
  }

  /**
   * Assign ticket to agent
   */
  private async assignToAgent(
    category: string,
    priorityScore: number
  ): Promise<string | null> {
    // Find agents with capacity for category
    const agents = await db.query.supportAgents.findMany({
      where: and(
        eq(supportAgents.isActive, true),
        sql`${supportAgents.categories} @> ${[`"${category}"`]}`
      )
    });

    // Filter by capacity
    const availableAgents = agents.filter(
      a => a.currentTickets < a.maxTickets
    );

    if (availableAgents.length === 0) {
      return null; // No available agents
    }

    // Sort by workload
    availableAgents.sort((a, b) => a.currentTickets - b.currentTickets);

    return availableAgents[0].id;
  }

  /**
   * Create SLA deadlines
   */
  private async createSLADeadlines(ticket: SupportTicket): Promise<void> {
    const tier = await this.getTenantTier(ticket.tenantId);
    const sla = slaConfig[tier];

    await db.insert(slaDeadlines).values({
      id: generateId(),
      ticketId: ticket.id,
      initialResponse: new Date(Date.now() + sla.initialResponse),
      resolution: new Date(Date.now() + sla.resolution)
    });
  }

  /**
   * Update ticket status
   */
  async updateStatus(
    ticketId: string,
    status: SupportTicket['status'],
    userId?: string,
    comment?: string
  ): Promise<SupportTicket> {
    const update: any = { status };

    if (status === 'resolved' || status === 'closed') {
      update.resolvedAt = new Date();
      update.resolvedBy = userId;
    }

    const ticket = await db.update(supportTickets)
      .set(update)
      .where(eq(supportTickets.id, ticketId))
      .returning()
      .then(rows => rows[0]);

    // Add comment if provided
    if (comment) {
      await this.addComment(ticketId, userId, comment);
    }

    // Send notifications
    await this.notifyStatusChange(ticket);

    return ticket;
  }

  /**
   * Add comment to ticket
   */
  async addComment(
    ticketId: string,
    userId: string | undefined,
    content: string,
    isInternal = false
  ): Promise<void> {
    await db.insert(ticketComments).values({
      id: generateId(),
      ticketId,
      userId,
      content,
      isInternal,
      createdAt: new Date()
    });
  }

  private async getTenantTier(tenantId: string): Promise<TenantTier> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });
    return tenant?.tier || TenantTier.STARTUP;
  }

  private async notifyNewTicket(ticket: SupportTicket): Promise<void> { /* ... */ }
  private async notifyStatusChange(ticket: SupportTicket): Promise<void> { /* ... */ }
}

// SLA configuration by tier
const slaConfig = {
  enterprise: {
    initialResponse: 1 * 60 * 60 * 1000,  // 1 hour
    resolution: 4 * 60 * 60 * 1000         // 4 hours
  },
  growth: {
    initialResponse: 4 * 60 * 60 * 1000,  // 4 hours
    resolution: 24 * 60 * 60 * 1000       // 24 hours
  },
  startup: {
    initialResponse: 8 * 60 * 60 * 1000,  // 8 hours
    resolution: 48 * 60 * 60 * 1000       // 48 hours
  }
};

interface SupportTicket {
  id: string;
  tenantId: string;
  subject: string;
  description: string;
  category: string;
  priority: string;
  priorityScore: number;
  status: 'open' | 'in_progress' | 'waiting' | 'resolved' | 'closed';
  assignedTo: string | null;
  createdAt: Date;
  resolvedAt?: Date;
  resolvedBy?: string;
}
```

---

## Implementation

```typescript
/**
 * Complete tenant operations service
 */
class TenantOperationsService {
  private healthMonitor: TenantHealthMonitor;
  private alertManager: TenantAlertManager;
  private metricsCollector: PerformanceMetricsCollector;
  private quotaService: QuotaEnforcementService;
  private usageMeter: UsageMeter;
  private lifecycleManager: TenantLifecycleManager;
  private exportService: TenantDataExportService;
  private supportService: SupportTicketService;

  constructor() {
    this.healthMonitor = new TenantHealthMonitor();
    this.alertManager = new TenantAlertManager();
    this.metricsCollector = new PerformanceMetricsCollector();
    this.quotaService = new QuotaEnforcementService();
    this.usageMeter = new UsageMeter();
    this.lifecycleManager = new TenantLifecycleManager();
    this.exportService = new TenantDataExportService();
    this.supportService = new SupportTicketService();
  }

  /**
   * Get tenant operations dashboard
   */
  async getDashboard(tenantId: string): Promise<OperationsDashboard> {
    const [
      health,
      metrics,
      quotaStatus,
      recentAlerts,
      openTickets
    ] = await Promise.all([
      this.healthMonitor.checkHealth(tenantId),
      this.metricsCollector.collectMetrics(tenantId, {
        start: new Date(Date.now() - 24 * 60 * 60 * 1000),
        end: new Date()
      }),
      this.quotaService.getQuotaStatus(tenantId),
      this.getRecentAlerts(tenantId),
      this.getOpenTickets(tenantId)
    ]);

    return {
      tenantId,
      health,
      metrics,
      quotaStatus,
      recentAlerts,
      openTickets,
      generatedAt: new Date()
    };
  }

  private async getRecentAlerts(tenantId: string): Promise<Alert[]> {
    return db.query.tenantAlerts.findMany({
      where: and(
        eq(tenantAlerts.tenantId, tenantId),
        inArray(tenantAlerts.status, ['open', 'acknowledged'])
      ),
      orderBy: [desc(tenantAlerts.triggeredAt)],
      limit: 10
    });
  }

  private async getOpenTickets(tenantId: string): Promise<SupportTicket[]> {
    return db.query.supportTickets.findMany({
      where: and(
        eq(supportTickets.tenantId, tenantId),
        notInArray(supportTickets.status, ['closed', 'resolved'])
      ),
      orderBy: [desc(supportTickets.createdAt)]
    });
  }
}

interface OperationsDashboard {
  tenantId: string;
  health: TenantHealth;
  metrics: TenantPerformanceMetrics;
  quotaStatus: QuotaStatus;
  recentAlerts: Alert[];
  openTickets: SupportTicket[];
  generatedAt: Date;
}
```

---

## Testing Scenarios

```typescript
describe('Tenant Operations', () => {
  describe('Health Monitoring', () => {
    it('should detect unhealthy tenant', async () => {
      const monitor = new TenantHealthMonitor();
      const health = await monitor.checkHealth('tenant-123');

      expect(health.status).toBeDefined();
    });
  });

  describe('Quota Enforcement', () => {
    it('should enforce storage quota', async () => {
      const service = new QuotaEnforcementService();
      const result = await service.checkQuota('tenant-123', 'storageGB', 1);

      expect(result.allowed).toBeDefined();
    });
  });

  describe('Billing', () => {
    it('should calculate bill for period', async () => {
      const meter = new UsageMeter();
      const bill = await meter.calculateBill('tenant-123', {
        start: new Date('2026-04-01'),
        end: new Date('2026-04-30')
      });

      expect(bill.total).toBeGreaterThan(0);
    });
  });

  describe('Lifecycle', () => {
    it('should upgrade tenant tier', async () => {
      const manager = new TenantLifecycleManager();
      // Test upgrade
    });
  });
});
```

---

## API Specification

```yaml
paths:
  /api/v1/tenants/{tenantId}/operations/dashboard:
    get:
      summary: Get tenant operations dashboard
      responses:
        '200':
          description: Dashboard data

  /api/v1/tenants/{tenantId}/operations/health:
    get:
      summary: Get tenant health status
      responses:
        '200':
          description: Health status

  /api/v1/tenants/{tenantId}/operations/metrics:
    get:
      summary: Get tenant performance metrics
      parameters:
        - name: period
          in: query
          schema:
            type: string
            enum: [1h, 24h, 7d, 30d]
      responses:
        '200':
          description: Performance metrics

  /api/v1/tenants/{tenantId}/operations/quotas:
    get:
      summary: Get quota status
      responses:
        '200':
          description: Quota status

  /api/v1/tenants/{tenantId}/operations/export:
    post:
      summary: Export tenant data
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                format:
                  type: string
                  enum: [json, csv, sql]
      responses:
        '202':
          description: Export started

  /api/v1/tenants/{tenantId}/operations/support/tickets:
    post:
      summary: Create support ticket
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTicketInput'
      responses:
        '201':
          description: Ticket created

components:
  schemas:
    CreateTicketInput:
      type: object
      required: [subject, description, category, priority]
      properties:
        subject:
          type: string
        description:
          type: string
        category:
          type: string
        priority:
          type: string
          enum: [low, medium, high, urgent]
```

---

## Metrics and Monitoring

```typescript
interface OperationsMetrics {
  totalTenants: number;
  activeTenants: number;
  suspendedTenants: number;
  averageHealthScore: number;
  openAlerts: number;
  openTickets: number;
  averageResponseTime: number;
  totalRevenue: number;
  churnRate: number;
}
```

---

**End of Document**

**End of Series**
