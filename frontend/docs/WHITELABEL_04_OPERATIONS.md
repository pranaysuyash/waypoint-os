# Multi-Brand & White Label — Operations & Scaling

> Research document for multi-tenant operations, deployment strategies, and platform scaling.

---

## Key Questions

1. **How do we deploy updates across all white-label instances?**
2. **What's the monitoring model across multiple tenants?**
3. **How do we handle tenant-specific configurations during updates?**
4. **What's the disaster recovery model for multi-tenant platforms?**
5. **How do we scale as the number of tenants grows?**

---

## Research Areas

### Multi-Tenant Deployment

```typescript
interface DeploymentStrategy {
  model: DeploymentModel;
  rolloutStrategy: RolloutStrategy;
  rollbackPlan: RollbackPlan;
  tenantCommunication: TenantCommunication;
}

type DeploymentModel =
  | 'single_tenant_code'              // One codebase, all tenants (recommended)
  | 'tenant_isolated'                 // Separate deployment per tenant (enterprise)
  | 'hybrid';                         // Shared for small, isolated for enterprise

// Single-tenant code, multi-tenant data (recommended):
// All tenants run the same code version
// Feature flags control tenant-specific behavior
// Database has row-level security per tenant
// Deployment: Update once, all tenants updated

// Rollout strategy:
interface RolloutStrategy {
  phases: RolloutPhase[];
  canaryTenant?: string;              // First tenant to get update
}

interface RolloutPhase {
  phase: number;
  tenantCount: number;
  durationHours: number;
  successCriteria: string;
  rollbackTrigger: string;
}

// Phased rollout:
// Phase 1: Internal team + 1 canary tenant (4 hours)
// Phase 2: 10% of tenants (8 hours)
// Phase 3: 50% of tenants (12 hours)
// Phase 4: 100% of tenants

// Success criteria per phase:
// Error rate < 1%
// P95 latency < 2s
// No tenant-specific failures
// Support ticket volume < 2x normal

// Rollback plan:
// If success criteria not met → Automatic rollback
// Tenant-specific failure → Roll back that tenant only
// Platform-wide failure → Full rollback
// Communication: Notify all tenant admins of rollback reason
```

### Multi-Tenant Monitoring

```typescript
interface TenantMonitoring {
  platformMetrics: PlatformMetric[];
  tenantMetrics: TenantMetric[];
  alerting: MultiTenantAlerting;
  dashboards: MonitoringDashboard[];
}

interface TenantMetric {
  tenantId: string;
  metricName: string;
  value: number;
  threshold: number;
  status: 'healthy' | 'warning' | 'critical';
}

// Monitoring hierarchy:
// Platform level: Overall system health
//   - Uptime, error rate, latency, CPU/memory
//   - Total trips processed, total revenue
//
// Tenant level: Per-agency health
//   - Agency-specific error rate
//   - Agency-specific latency
//   - Active agents, active trips
//   - Storage utilization
//   - API call utilization
//   - Integration health per tenant

// Multi-tenant alerting:
// Platform-level alerts → Platform engineering team
// Tenant-level alerts → Tenant admin + platform support
// Integration alerts → Tenant admin (their integration credentials)

// Tenant health dashboard (for platform ops):
// ┌──────────────────────────────────────────┐
// │  Tenant Health Overview                   │
// │                                          │
// │  Total tenants: 45                       │
// │  Healthy: 40  Warning: 3  Critical: 2   │
// │                                          │
// │  ⚠ Acme Travel: Payment gateway failing  │
// │  ⚠ Global Tours: Storage 90% full        │
// │  🔴 Holiday Plans: Domain SSL expiring   │
// │  🔴 Travel Co: API limit 95% reached     │
// │                                          │
// │  [View All] [Export Report]              │
// └──────────────────────────────────────────┘
```

### Tenant Configuration Management

```typescript
interface TenantConfigManagement {
  configStore: ConfigStore;
  versioning: ConfigVersioning;
  validation: ConfigValidation;
  migration: ConfigMigration;
}

// Configuration management:
// 1. All tenant configs stored in centralized config service
// 2. Config changes versioned (audit trail)
// 3. Config changes validated before applying
// 4. Config migration on platform updates
// 5. Config rollback supported

// Config migration during platform updates:
// Platform update adds new feature with default config:
// 1. Default config added to config template
// 2. All tenant configs auto-merged with new defaults
// 3. Tenant-specific overrides preserved
// 4. Breaking config changes flagged for manual review
// 5. Migration tested on canary tenant first

// Configuration categories:
// Branding: Colors, logos, fonts (changes rarely)
// Features: Enabled modules, feature flags (changes occasionally)
// Integrations: API keys, credentials (changes rarely)
// Workflows: Approval rules, pricing rules (changes per business need)
// Limits: Usage caps, agent limits (changes on plan upgrade)
// Compliance: GST settings, TCS rates, retention policies (regulatory changes)
```

### Scaling Model

```typescript
interface ScalingPlan {
  tenantGrowth: GrowthProjection;
  resourceScaling: ResourcePlan[];
  costModel: CostProjection;
}

// Growth projections:
// Year 1: 10-50 tenants, 100-500 agents
// Year 2: 50-200 tenants, 500-2000 agents
// Year 3: 200-500 tenants, 2000-5000 agents

// Resource scaling:
// Database: Vertical → Horizontal sharding at 200+ tenants
// API servers: Auto-scale based on request volume
// File storage: Unlimited (per-tenant quotas)
// Search: ElasticSearch cluster scales with data volume
// Cache: Redis cluster, per-tenant namespacing
// Background jobs: Queue workers scale with job volume

// Cost per tenant:
// Infrastructure: ₹500-2,000/month (scales with usage)
// Support: ₹500-5,000/month (depends on tier)
// Revenue per tenant: ₹5,000-50,000/month
// Margin: 60-80% at scale
```

---

## Open Problems

1. **Noisy neighbor** — One tenant's heavy usage degrades performance for all tenants. Need resource isolation and fair scheduling.

2. **Custom code per tenant** — Enterprise tenants want custom features. Custom code in a multi-tenant system creates maintenance burden. Need extension points, not custom code.

3. **Data residency** — Some tenants may require data stored in specific regions (India-only for RBI compliance). Multi-region data residency is complex.

4. **Tenant migration** — Moving a tenant from shared infrastructure to isolated infrastructure (as they grow) without downtime.

5. **Support scalability** — 100 tenants = 100 sets of integration issues, billing questions, and support requests. Need self-service tooling and tiered support.

---

## Next Steps

- [ ] Design multi-tenant deployment with phased rollout
- [ ] Build tenant health monitoring dashboard
- [ ] Create tenant configuration management with versioning
- [ ] Design scaling plan with growth projections
- [ ] Study multi-tenant operations (Salesforce, Shopify, HubSpot multi-tenant architecture)
