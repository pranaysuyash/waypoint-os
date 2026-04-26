# Multi-tenancy Architecture — Technical Deep Dive

> Comprehensive guide to multi-tenant architecture patterns for the Travel Agency Agent platform

---

## Document Metadata

**Series:** Multi-tenancy Patterns
**Document:** 1 of 4 (Architecture)
**Last Updated:** 2026-04-26
**Status:** ✅ Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Multi-tenancy Models](#multi-tenancy-models)
3. [Tenant Identification and Routing](#tenant-identification-and-routing)
4. [Tenant Context Propagation](#tenant-context-propagation)
5. [Tenant Configuration](#tenant-configuration)
6. [Data Modeling](#data-modeling)
7. [API Design](#api-design)
8. [Connection Pooling](#connection-pooling)
9. [Migration Strategies](#migration-strategies)
10. [Implementation](#implementation)
11. [Testing Scenarios](#testing-scenarios)
12. [API Specification](#api-specification)
13. [Metrics and Monitoring](#metrics-and-monitoring)

---

## Overview

Multi-tenancy enables the Travel Agency Agent platform to serve multiple agencies (tenants) from a single application instance while maintaining isolation between their data, configurations, and resources.

### Business Context

- **Target Users:** Independent travel agencies, small to medium travel companies
- **Scale:** Hundreds to thousands of tenants
- **Isolation Requirements:** Data separation, branding, configuration independence
- **Efficiency Goals:** Cost optimization through shared infrastructure

### Technical Objectives

- **Data Isolation:** Complete separation of tenant data
- **Performance:** No performance degradation from multi-tenancy
- **Scalability:** Support tenant growth without re-architecture
- **Security:** Prevent cross-tenant data access
- **Operational Efficiency:** Simplified deployment and maintenance

---

## Multi-tenancy Models

### Model Comparison

| Model | Description | Pros | Cons | Best For |
|-------|-------------|------|------|----------|
| **Database per Tenant** | Separate database for each tenant | Complete isolation, easy backup | High cost, complex management | Enterprise, <100 tenants |
| **Schema per Tenant** | Same DB, separate schemas per tenant | Good isolation, moderate cost | Schema management overhead | <1000 tenants |
| **Shared Schema** | Same DB/schema, tenant_id column | Lowest cost, simple ops | Application-level isolation | SaaS, >1000 tenants |
| **Hybrid** | Combination based on tier | Optimized for segments | Complex to implement | Multi-tier SaaS |

### Recommended Model: Shared Schema with Row-Level Security

The Travel Agency Agent uses a shared schema model with PostgreSQL Row-Level Security (RLS) for database-enforced isolation.

```typescript
/**
 * Multi-tenancy model selection
 */
enum MultiTenancyModel {
  DATABASE_PER_TENANT = 'database_per_tenant',
  SCHEMA_PER_TENANT = 'schema_per_tenant',
  SHARED_SCHEMA = 'shared_schema',
  HYBRID = 'hybrid'
}

interface MultiTenancyConfig {
  model: MultiTenancyModel;
  defaultTenantId: string;
  tenantIdColumn: string;
  enforceRLS: boolean;
  connectionPoolConfig: ConnectionPoolConfig;
}

const travelAgencyMultiTenancyConfig: MultiTenancyConfig = {
  model: MultiTenancyModel.SHARED_SCHEMA,
  defaultTenantId: 'default',
  tenantIdColumn: 'tenant_id',
  enforceRLS: true,
  connectionPoolConfig: {
    maxConnections: 100,
    minConnections: 10,
    acquireTimeoutMillis: 10000,
    idleTimeoutMillis: 30000
  }
};
```

### Tenant Tiers

```typescript
/**
 * Tenant tiers with different isolation levels
 */
enum TenantTier {
  STARTUP = 'startup',        // Shared everything
  GROWTH = 'growth',          // Dedicated schema
  ENTERPRISE = 'enterprise'   // Dedicated database
}

interface TenantTierConfig {
  tier: TenantTier;
  multiTenancyModel: MultiTenancyModel;
  maxUsers: number;
  maxTrips: number;
  maxStorage: number;         // in GB
  supportLevel: 'community' | 'email' | 'priority' | 'dedicated';
}

const tierConfigs: Record<TenantTier, TenantTierConfig> = {
  [TenantTier.STARTUP]: {
    tier: TenantTier.STARTUP,
    multiTenancyModel: MultiTenancyModel.SHARED_SCHEMA,
    maxUsers: 5,
    maxTrips: 500,
    maxStorage: 10,
    supportLevel: 'community'
  },
  [TenantTier.GROWTH]: {
    tier: TenantTier.GROWTH,
    multiTenancyModel: MultiTenancyModel.SCHEMA_PER_TENANT,
    maxUsers: 50,
    maxTrips: 10000,
    maxStorage: 100,
    supportLevel: 'email'
  },
  [TenantTier.ENTERPRISE]: {
    tier: TenantTier.ENTERPRISE,
    multiTenancyModel: MultiTenancyModel.DATABASE_PER_TENANT,
    maxUsers: -1,              // unlimited
    maxTrips: -1,
    maxStorage: -1,
    supportLevel: 'dedicated'
  }
};
```

---

## Tenant Identification and Routing

### Tenant Identification Methods

```typescript
/**
 * Tenant identification methods
 */
enum TenantIdentificationMethod {
  SUBDOMAIN = 'subdomain',           // agency-name.travelagent.com
  CUSTOM_DOMAIN = 'custom_domain',   // agency-name.com
  PATH_PREFIX = 'path_prefix',       // travelagent.com/t/agency-name
  HEADER = 'header',                 // X-Tenant-ID header
  API_KEY = 'api_key',               // API key with tenant binding
  USER_CONTEXT = 'user_context'      // Derived from authenticated user
}

interface TenantResolution {
  tenantId: string;
  method: TenantIdentificationMethod;
  confidence: 'certain' | 'probable' | 'ambiguous';
  metadata: Record<string, unknown>;
}
```

### Subdomain-Based Routing

```typescript
/**
 * Subdomain-based tenant resolver
 */
class SubdomainTenantResolver {
  private baseDomain: string;
  private reservedSubdomains: Set<string>;

  constructor(baseDomain: string) {
    this.baseDomain = baseDomain;
    this.reservedSubdomains = new Set([
      'www', 'api', 'admin', 'app', 'dashboard',
      'staging', 'dev', 'test', 'docs', 'blog'
    ]);
  }

  async resolve(host: string): Promise<TenantResolution | null> {
    // Extract subdomain
    const subdomain = this.extractSubdomain(host);
    if (!subdomain) {
      return null;
    }

    // Skip reserved subdomains
    if (this.reservedSubdomains.has(subdomain)) {
      return null;
    }

    // Look up tenant
    const tenant = await this.findTenantBySubdomain(subdomain);
    if (!tenant) {
      return null;
    }

    return {
      tenantId: tenant.id,
      method: TenantIdentificationMethod.SUBDOMAIN,
      confidence: 'certain',
      metadata: { subdomain, domain: host }
    };
  }

  private extractSubdomain(host: string): string | null {
    const parts = host.split('.');
    if (parts.length < 2) return null;

    const baseParts = this.baseDomain.split('.');
    const subdomainParts = parts.slice(0, -baseParts.length);

    return subdomainParts.length > 0
      ? subdomainParts.join('.')
      : null;
  }

  private async findTenantBySubdomain(subdomain: string): Promise<Tenant | null> {
    // Database lookup
    return db.query.tenants.findFirst({
      where: eq(tenants.subdomain, subdomain.toLowerCase())
    });
  }
}
```

### Custom Domain Routing

```typescript
/**
 * Custom domain tenant resolver
 */
class CustomDomainTenantResolver {
  async resolve(host: string): Promise<TenantResolution | null> {
    const domainMapping = await this.findDomainMapping(host);
    if (!domainMapping) {
      return null;
    }

    // Verify SSL certificate is valid
    if (!(await this.verifyCertificate(host))) {
      throw new Error('SSL certificate not valid for domain');
    }

    return {
      tenantId: domainMapping.tenantId,
      method: TenantIdentificationMethod.CUSTOM_DOMAIN,
      confidence: 'certain',
      metadata: {
        customDomain: host,
        verifiedAt: domainMapping.verifiedAt
      }
    };
  }

  private async findDomainMapping(domain: string) {
    return db.query.tenantDomains.findFirst({
      where: eq(tenantDomains.domain, domain.toLowerCase())
    });
  }

  private async verifyCertificate(domain: string): Promise<boolean> {
    // Check against Let's Encrypt or other CA
    const certInfo = await sslChecker(domain);
    return certInfo.valid === true;
  }
}
```

### Header-Based Routing (API)

```typescript
/**
 * Header-based tenant resolver for API calls
 */
class HeaderTenantResolver {
  private headerName = 'X-Tenant-ID';
  private fallbackHeaderName = 'X-Tenant-Subdomain';

  async resolve(headers: Headers): Promise<TenantResolution | null> {
    // Try explicit tenant ID first
    const tenantId = headers.get(this.headerName);
    if (tenantId) {
      return this.resolveById(tenantId);
    }

    // Fall back to subdomain
    const subdomain = headers.get(this.fallbackHeaderName);
    if (subdomain) {
      return this.resolveBySubdomain(subdomain);
    }

    return null;
  }

  private async resolveById(tenantId: string): Promise<TenantResolution | null> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    if (!tenant) {
      return null;
    }

    return {
      tenantId: tenant.id,
      method: TenantIdentificationMethod.HEADER,
      confidence: 'certain',
      metadata: { header: this.headerName }
    };
  }

  private async resolveBySubdomain(subdomain: string): Promise<TenantResolution | null> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.subdomain, subdomain.toLowerCase())
    });

    if (!tenant) {
      return null;
    }

    return {
      tenantId: tenant.id,
      method: TenantIdentificationMethod.HEADER,
      confidence: 'probable',
      metadata: { header: this.fallbackHeaderName, subdomain }
    };
  }
}
```

### Chained Resolver

```typescript
/**
 * Chained tenant resolver - tries multiple methods in order
 */
class ChainedTenantResolver {
  private resolvers: TenantResolver[];

  constructor(resolvers: TenantResolver[]) {
    this.resolvers = resolvers;
  }

  async resolve(request: Request): Promise<TenantResolution | null> {
    const host = request.headers.get('host') || '';
    const headers = request.headers;

    for (const resolver of this.resolvers) {
      let resolution: TenantResolution | null = null;

      if (resolver instanceof SubdomainTenantResolver) {
        resolution = await resolver.resolve(host);
      } else if (resolver instanceof CustomDomainTenantResolver) {
        resolution = await resolver.resolve(host);
      } else if (resolver instanceof HeaderTenantResolver) {
        resolution = await resolver.resolve(headers);
      }

      if (resolution) {
        return resolution;
      }
    }

    return null;
  }
}

// Usage
const resolver = new ChainedTenantResolver([
  new CustomDomainTenantResolver(),
  new SubdomainTenantResolver('travelagent.com'),
  new HeaderTenantResolver()
]);
```

---

## Tenant Context Propagation

### Tenant Context Interface

```typescript
/**
 * Tenant context - carried through request lifecycle
 */
interface TenantContext {
  tenantId: string;
  tier: TenantTier;
  subdomain?: string;
  customDomain?: string;
  configuration: TenantConfiguration;
  quotas: TenantQuotas;
  features: TenantFeatures;
  metadata: {
    resolvedAt: Date;
    resolutionMethod: TenantIdentificationMethod;
    confidence: 'certain' | 'probable' | 'ambiguous';
  };
}

interface TenantConfiguration {
  branding: {
    name: string;
    logo: string;
    primaryColor: string;
    favicon: string;
  };
  settings: {
    timezone: string;
    currency: string;
    dateFormat: string;
    locale: string;
  };
  integrations: {
    emailProvider: string;
    smsProvider: string;
    paymentGateway: string;
  };
}

interface TenantQuotas {
  maxUsers: number;
  maxTrips: number;
  maxStorage: number;
  currentUsers: number;
  currentTrips: number;
  currentStorage: number;
}

interface TenantFeatures {
  whiteLabel: boolean;
  customDomain: boolean;
  apiAccess: boolean;
  advancedAnalytics: boolean;
  prioritySupport: boolean;
  customIntegrations: boolean;
}
```

### AsyncLocalStorage for Context Propagation

```typescript
/**
 * Tenant context storage using AsyncLocalStorage
 */
import { AsyncLocalStorage } from 'node:async_hooks';

const tenantContextStorage = new AsyncLocalStorage<TenantContext>();

class TenantContextManager {
  /**
   * Get current tenant context
   */
  static getContext(): TenantContext | undefined {
    return tenantContextStorage.getStore();
  }

  /**
   * Run callback with tenant context
   */
  static async withContext<T>(
    context: TenantContext,
    callback: () => Promise<T>
  ): Promise<T> {
    return tenantContextStorage.run(context, callback);
  }

  /**
   * Get current tenant ID - throws if not set
   */
  static getTenantId(): string {
    const context = this.getContext();
    if (!context) {
      throw new Error('Tenant context not set');
    }
    return context.tenantId;
  }

  /**
   * Check if feature is enabled for current tenant
   */
  static hasFeature(feature: keyof TenantFeatures): boolean {
    const context = this.getContext();
    return context?.features[feature] ?? false;
  }

  /**
   * Get tenant configuration value
   */
  static getConfig<K extends keyof TenantConfiguration>(
    key: K
  ): TenantConfiguration[K] {
    const context = this.getContext();
    if (!context) {
      throw new Error('Tenant context not set');
    }
    return context.configuration[key];
  }
}
```

### Middleware Integration

```typescript
/**
 * Express middleware to establish tenant context
 */
async function tenantContextMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    // Resolve tenant
    const resolution = await resolver.resolve(req);

    if (!resolution) {
      res.status(400).json({ error: 'Unable to determine tenant' });
      return;
    }

    // Load full tenant context
    const tenant = await loadTenantContext(resolution.tenantId);

    if (!tenant) {
      res.status(404).json({ error: 'Tenant not found' });
      return;
    }

    // Check if tenant is active
    if (tenant.status !== 'active') {
      res.status(403).json({
        error: 'Tenant is not active',
        status: tenant.status
      });
      return;
    }

    // Set context for this request
    const context: TenantContext = {
      tenantId: tenant.id,
      tier: tenant.tier,
      subdomain: tenant.subdomain,
      customDomain: tenant.customDomain,
      configuration: tenant.configuration,
      quotas: await loadTenantQuotas(tenant.id),
      features: await loadTenantFeatures(tenant.id),
      metadata: {
        resolvedAt: new Date(),
        resolutionMethod: resolution.method,
        confidence: resolution.confidence
      }
    };

    // Run remaining middleware/route with context
    await TenantContextManager.withContext(context, async () => {
      // Attach tenant info to request for debugging
      (req as any).tenant = context;
      next();
    });
  } catch (error) {
    console.error('Tenant context error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}
```

---

## Tenant Configuration

### Configuration Schema

```typescript
/**
 * Tenant configuration storage
 */
interface TenantConfigEntry {
  id: string;
  tenantId: string;
  key: string;
  value: unknown;
  type: 'string' | 'number' | 'boolean' | 'json' | 'array';
  category: 'branding' | 'settings' | 'integrations' | 'features' | 'quotas';
  isEncrypted: boolean;
  isPublic: boolean;          // Can be exposed to frontend
  defaultValue?: unknown;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    enum?: unknown[];
  };
  updatedAt: Date;
  updatedBy: string;
}

/**
 * Configuration manager
 */
class TenantConfigurationManager {
  /**
   * Get configuration value for tenant
   */
  async get<T>(
    tenantId: string,
    key: string,
    defaultValue?: T
  ): Promise<T | undefined> {
    const config = await db.query.tenantConfig.findFirst({
      where: and(
        eq(tenantConfig.tenantId, tenantId),
        eq(tenantConfig.key, key)
      )
    });

    if (!config) {
      return defaultValue;
    }

    let value = config.value;

    // Decrypt if needed
    if (config.isEncrypted) {
      value = await decrypt(value);
    }

    return value as T;
  }

  /**
   * Set configuration value for tenant
   */
  async set(
    tenantId: string,
    key: string,
    value: unknown,
    options: {
      type?: TenantConfigEntry['type'];
      category?: TenantConfigEntry['category'];
      isEncrypted?: boolean;
      isPublic?: boolean;
      updatedBy?: string;
    } = {}
  ): Promise<void> {
    const {
      type = inferType(value),
      category = 'settings',
      isEncrypted = isSensitiveKey(key),
      isPublic = false,
      updatedBy = 'system'
    } = options;

    const encrypted = isEncrypted ? await encrypt(value) : value;

    await db.insert(tenantConfig).values({
      id: generateId(),
      tenantId,
      key,
      value: encrypted,
      type,
      category,
      isEncrypted,
      isPublic,
      updatedAt: new Date(),
      updatedBy
    }).onConflictDoUpdate({
      target: [tenantConfig.tenantId, tenantConfig.key],
      set: {
        value: encrypted,
        type,
        isEncrypted,
        isPublic,
        updatedAt: new Date(),
        updatedBy
      }
    });
  }

  /**
   * Get all public configuration for frontend
   */
  async getPublicConfig(tenantId: string): Promise<Record<string, unknown>> {
    const configs = await db.query.tenantConfig.findMany({
      where: and(
        eq(tenantConfig.tenantId, tenantId),
        eq(tenantConfig.isPublic, true)
      )
    });

    return configs.reduce((acc, config) => {
      acc[config.key] = config.value;
      return acc;
    }, {} as Record<string, unknown>);
  }

  /**
   * Bulk set configuration
   */
  async setMany(
    tenantId: string,
    configs: Record<string, unknown>,
    options?: { updatedBy?: string }
  ): Promise<void> {
    const entries = Object.entries(configs);

    await db.transaction(async (tx) => {
      for (const [key, value] of entries) {
        await this.set(tenantId, key, value, {
          ...options,
          category: inferCategory(key)
        });
      }
    });
  }
}

function isSensitiveKey(key: string): boolean {
  const sensitiveKeys = ['api_key', 'secret', 'token', 'password', 'webhook'];
  return sensitiveKeys.some(sk => key.toLowerCase().includes(sk));
}

function inferType(value: unknown): TenantConfigEntry['type'] {
  if (typeof value === 'string') return 'string';
  if (typeof value === 'number') return 'number';
  if (typeof value === 'boolean') return 'boolean';
  if (Array.isArray(value)) return 'array';
  return 'json';
}

function inferCategory(key: string): TenantConfigEntry['category'] {
  if (key.startsWith('branding.')) return 'branding';
  if (key.startsWith('integration.')) return 'integrations';
  if (key.startsWith('feature.')) return 'features';
  if (key.startsWith('quota.')) return 'quotas';
  return 'settings';
}
```

### Configuration Templates

```typescript
/**
 * Configuration templates for new tenant onboarding
 */
interface ConfigTemplate {
  name: string;
  description: string;
  category: TenantTier;
  configs: Record<string, {
    value: unknown;
    type: TenantConfigEntry['type'];
    isEncrypted: boolean;
    isPublic: boolean;
    category: TenantConfigEntry['category'];
  }>;
}

const configurationTemplates: Record<TenantTier, ConfigTemplate> = {
  [TenantTier.STARTUP]: {
    name: 'Startup Tier',
    description: 'Basic configuration for startup agencies',
    category: TenantTier.STARTUP,
    configs: {
      'branding.name': { value: '', type: 'string', isEncrypted: false, isPublic: true, category: 'branding' },
      'branding.primaryColor': { value: '#3B82F6', type: 'string', isEncrypted: false, isPublic: true, category: 'branding' },
      'settings.timezone': { value: 'UTC', type: 'string', isEncrypted: false, isPublic: true, category: 'settings' },
      'settings.currency': { value: 'USD', type: 'string', isEncrypted: false, isPublic: true, category: 'settings' },
      'settings.locale': { value: 'en-US', type: 'string', isEncrypted: false, isPublic: true, category: 'settings' },
      'feature.whiteLabel': { value: false, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.customDomain': { value: false, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.apiAccess': { value: false, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'quota.maxUsers': { value: 5, type: 'number', isEncrypted: false, isPublic: false, category: 'quotas' },
      'quota.maxTrips': { value: 500, type: 'number', isEncrypted: false, isPublic: false, category: 'quotas' }
    }
  },
  [TenantTier.GROWTH]: {
    name: 'Growth Tier',
    description: 'Enhanced configuration for growing agencies',
    category: TenantTier.GROWTH,
    configs: {
      // Inherits startup configs with overrides
      'feature.whiteLabel': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.customDomain': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.apiAccess': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'quota.maxUsers': { value: 50, type: 'number', isEncrypted: false, isPublic: false, category: 'quotas' },
      'quota.maxTrips': { value: 10000, type: 'number', isEncrypted: false, isPublic: false, category: 'quotas' }
    }
  },
  [TenantTier.ENTERPRISE]: {
    name: 'Enterprise Tier',
    description: 'Full-featured configuration for enterprise agencies',
    category: TenantTier.ENTERPRISE,
    configs: {
      'feature.whiteLabel': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.customDomain': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.apiAccess': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.advancedAnalytics': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.prioritySupport': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'feature.customIntegrations': { value: true, type: 'boolean', isEncrypted: false, isPublic: false, category: 'features' },
      'quota.maxUsers': { value: -1, type: 'number', isEncrypted: false, isPublic: false, category: 'quotas' },
      'quota.maxTrips': { value: -1, type: 'number', isEncrypted: false, isPublic: false, category: 'quotas' }
    }
  }
};

/**
 * Apply configuration template to tenant
 */
async function applyConfigurationTemplate(
  tenantId: string,
  tier: TenantTier
): Promise<void> {
  const template = configurationTemplates[tier];
  const manager = new TenantConfigurationManager();

  for (const [key, config] of Object.entries(template.configs)) {
    await manager.set(tenantId, key, config.value, {
      type: config.type,
      category: config.category,
      isEncrypted: config.isEncrypted,
      isPublic: config.isPublic
    });
  }
}
```

---

## Data Modeling

### Tenant-Aware Tables

```typescript
/**
 * Base schema for all tenant-aware tables
 */
interface TenantAwareTable {
  id: string;
  tenant_id: string;           // ALWAYS present for tenant isolation
  created_at: DateTime;
  updated_at: DateTime;
  created_by?: string;         // User ID within tenant
  updated_by?: string;
}

/**
 * Schema examples with tenant_id
 */
// Customers table
interface Customer extends TenantAwareTable {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  // ... other fields
}

// Trips table
interface Trip extends TenantAwareTable {
  customer_id: string;
  status: TripStatus;
  destination: string;
  // ... other fields
}

// Bookings table
interface Booking extends TenantAwareTable {
  trip_id: string;
  supplier_id: string;
  booking_reference: string;
  // ... other fields
}
```

### Row-Level Security Policies

```typescript
/**
 * Row-Level Security policy manager
 */
class RLSPolicyManager {
  /**
   * Enable RLS on a table
   */
  async enableRLS(tableName: string): Promise<void> {
    await db.execute(`
      ALTER TABLE ${tableName} ENABLE ROW LEVEL SECURITY;
    `);
  }

  /**
   * Create tenant isolation policy
   */
  async createTenantIsolationPolicy(
    tableName: string,
    policyName: string
  ): Promise<void> {
    await db.execute(`
      CREATE POLICY ${policyName}
      ON ${tableName}
      USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    `);
  }

  /**
   * Create policy with check for inserts
   */
  async createTenantPolicyWithCheck(
    tableName: string,
    policyName: string
  ): Promise<void> {
    await db.execute(`
      CREATE POLICY ${policyName}
      ON ${tableName}
      FOR ALL
      USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
      WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
    `);
  }

  /**
   * Apply tenant ID filter for session
   */
  async setTenantContext(tenantId: string): Promise<void> {
    await db.execute(`
      SET LOCAL app.current_tenant_id = '${tenantId}';
    `);
  }

  /**
   * Initialize RLS for all tenant tables
   */
  async initializeRLS(): Promise<void> {
    const tables = [
      'customers',
      'trips',
      'bookings',
      'quotes',
      'suppliers',
      'users',
      'inquiries',
      'packets',
      'communications'
    ];

    for (const table of tables) {
      await this.enableRLS(table);
      await this.createTenantPolicyWithCheck(
        table,
        `${table}_tenant_isolation`
      );
    }
  }
}
```

### Tenant-Aware Query Builder

```typescript
/**
 * Tenant-aware query builder
 */
class TenantQueryBuilder<T> {
  private tenantId: string;
  private tableName: string;

  constructor(tenantId: string, tableName: string) {
    this.tenantId = tenantId;
    this.tableName = tableName;
  }

  /**
   * Set tenant context and execute query
   */
  async query<R>(
    callback: (qb: QueryBuilder<T>) => QueryBuilder<T>
  ): Promise<R[]> {
    // Set tenant context for RLS
    await db.execute(`
      SET LOCAL app.current_tenant_id = '${this.tenantId}';
    `);

    // Build and execute query
    const builder = callback(db.query(this.tableName));
    return builder.execute();
  }

  /**
   * Find by ID (ensures tenant isolation)
   */
  async findById(id: string): Promise<T | null> {
    const results = await this.query((qb) =>
      qb.where(eq(`${this.tableName}.id`, id))
    );
    return results[0] || null;
  }

  /**
   * Find many with filters
   */
  async findMany(filters: Record<string, unknown>): Promise<T[]> {
    return this.query((qb) => {
      let query = qb;
      for (const [key, value] of Object.entries(filters)) {
        query = query.where(eq(`${this.tableName}.${key}`, value));
      }
      return query;
    });
  }

  /**
   * Insert with tenant_id
   */
  async insert(data: Omit<T, 'id' | 'tenant_id' | 'created_at' | 'updated_at'>): Promise<T> {
    const record = {
      ...data,
      tenant_id: this.tenantId,
      id: generateId(),
      created_at: new Date(),
      updated_at: new Date()
    } as T;

    await db.execute(`
      SET LOCAL app.current_tenant_id = '${this.tenantId}';
    `);

    await db.insert(this.tableName).values(record);
    return record;
  }

  /**
   * Update with tenant check
   */
  async update(
    id: string,
    data: Partial<Omit<T, 'id' | 'tenant_id' | 'created_at'>>
  ): Promise<T | null> {
    await db.execute(`
      SET LOCAL app.current_tenant_id = '${this.tenantId}';
    `);

    await db.update(this.tableName)
      .set({ ...data, updated_at: new Date() })
      .where(eq(`${this.tableName}.id`, id));

    return this.findById(id);
  }

  /**
   * Delete with tenant check
   */
  async delete(id: string): Promise<boolean> {
    await db.execute(`
      SET LOCAL app.current_tenant_id = '${this.tenantId}';
    `);

    const result = await db.delete(this.tableName)
      .where(eq(`${this.tableName}.id`, id));

    return result.rowCount > 0;
  }
}
```

---

## API Design

### Tenant-Aware API Routes

```typescript
/**
 * Tenant-aware route handler wrapper
 */
function withTenant<T>(
  handler: (context: TenantContext, req: Request) => Promise<T>
): RequestHandler {
  return async (req, res, next) => {
    const context = TenantContextManager.getContext();

    if (!context) {
      return res.status(500).json({ error: 'Tenant context not available' });
    }

    try {
      const result = await handler(context, req as Request);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

/**
 * Example: GET /api/trips
 */
app.get('/api/trips',
  tenantContextMiddleware,
  withTenant(async (context, req) => {
    const qb = new TenantQueryBuilder(context.tenantId, 'trips');

    const trips = await qb.findMany({
      status: req.query.status
    });

    return {
      data: trips,
      meta: {
        tenantId: context.tenantId,
        total: trips.length
      }
    };
  })
);

/**
 * Example: POST /api/trips
 */
app.post('/api/trips',
  tenantContextMiddleware,
  withTenant(async (context, req) => {
    const qb = new TenantQueryBuilder(context.tenantId, 'trips');

    const trip = await qb.insert(req.body);

    return {
      data: trip,
      meta: {
        tenantId: context.tenantId
      }
    };
  })
);
```

### API Key Authentication

```typescript
/**
 * API key with tenant binding
 */
interface ApiKey {
  id: string;
  tenantId: string;
  keyHash: string;
  name: string;
  scopes: string[];
  userId?: string;             // Optional: bind to specific user
  isActive: boolean;
  lastUsedAt?: Date;
  expiresAt?: Date;
  createdAt: Date;
}

/**
 * API key authentication middleware
 */
async function apiKeyAuthMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing API key' });
  }

  const apiKey = authHeader.substring(7);

  // Find API key
  const keyRecord = await db.query.apiKeys.findFirst({
    where: eq(apiKeys.keyHash, hashApiKey(apiKey))
  });

  if (!keyRecord || !keyRecord.isActive) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  // Check expiration
  if (keyRecord.expiresAt && keyRecord.expiresAt < new Date()) {
    return res.status(401).json({ error: 'API key expired' });
  }

  // Update last used
  await db.update(apiKeys)
    .set({ lastUsedAt: new Date() })
    .where(eq(apiKeys.id, keyRecord.id));

  // Load tenant context
  const tenant = await loadTenantContext(keyRecord.tenantId);

  if (!tenant || tenant.status !== 'active') {
    return res.status(403).json({ error: 'Tenant not active' });
  }

  // Set tenant context
  const context: TenantContext = {
    tenantId: tenant.id,
    tier: tenant.tier,
    configuration: tenant.configuration,
    quotas: await loadTenantQuotas(tenant.id),
    features: await loadTenantFeatures(tenant.id),
    metadata: {
      resolvedAt: new Date(),
      resolutionMethod: TenantIdentificationMethod.API_KEY,
      confidence: 'certain'
    }
  };

  await TenantContextManager.withContext(context, async () => {
    // Store API key info for rate limiting
    (req as any).apiKey = {
      id: keyRecord.id,
      name: keyRecord.name,
      scopes: keyRecord.scopes
    };
    next();
  });
}
```

---

## Connection Pooling

### Tenant-Aware Connection Pool

```typescript
/**
 * Connection pool configuration for multi-tenancy
 */
interface TenantConnectionPool {
  tenantId: string;
  pool: Pool;
  connections: number;
  maxConnections: number;
  lastUsed: Date;
}

/**
 * Multi-tenant connection pool manager
 */
class MultiTenantConnectionManager {
  private pools: Map<string, TenantConnectionPool>;
  private config: ConnectionPoolConfig;
  private cleanupInterval: NodeJS.Timeout;

  constructor(config: ConnectionPoolConfig) {
    this.pools = new Map();
    this.config = config;
    this.cleanupInterval = setInterval(
      () => this.cleanupIdlePools(),
      60000  // Every minute
    );
  }

  /**
   * Get or create connection pool for tenant
   */
  async getConnection(tenantId: string): Promise<PoolClient> {
    let poolEntry = this.pools.get(tenantId);

    if (!poolEntry) {
      const pool = this.createPool(tenantId);
      poolEntry = {
        tenantId,
        pool,
        connections: 0,
        maxConnections: this.config.maxConnectionsPerTenant || 10,
        lastUsed: new Date()
      };
      this.pools.set(tenantId, poolEntry);
    }

    poolEntry.lastUsed = new Date();
    poolEntry.connections++;

    return poolEntry.pool.connect();
  }

  /**
   * Create new pool for tenant
   */
  private createPool(tenantId: string): Pool {
    return new Pool({
      host: process.env.DB_HOST,
      database: process.env.DB_NAME,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      max: this.config.maxConnectionsPerTenant || 10,
      idleTimeoutMillis: this.config.idleTimeoutMillis || 30000,
      connectionTimeoutMillis: this.config.connectionTimeoutMillis || 10000,
      // Set tenant on connection
      beforeConnect: (conn) => {
        conn.query(`SET app.current_tenant_id = '${tenantId}'`);
      }
    });
  }

  /**
   * Release connection back to pool
   */
  async releaseConnection(tenantId: string, client: PoolClient): Promise<void> {
    const poolEntry = this.pools.get(tenantId);
    if (poolEntry) {
      poolEntry.connections--;
      client.release();
    }
  }

  /**
   * Clean up idle pools
   */
  private cleanupIdlePools(): void {
    const now = Date.now();
    const idleTimeout = this.config.poolIdleTimeoutMillis || 300000; // 5 minutes

    for (const [tenantId, poolEntry] of this.pools.entries()) {
      if (poolEntry.connections === 0 &&
          (now - poolEntry.lastUsed.getTime()) > idleTimeout) {
        poolEntry.pool.end();
        this.pools.delete(tenantId);
      }
    }
  }

  /**
   * Close all pools
   */
  async closeAll(): Promise<void> {
    clearInterval(this.cleanupInterval);

    const closePromises = Array.from(this.pools.values()).map(
      entry => entry.pool.end()
    );

    await Promise.all(closePromises);
    this.pools.clear();
  }

  /**
   * Get pool statistics
   */
  getStats(): { totalPools: number; activeConnections: number } {
    let activeConnections = 0;

    for (const poolEntry of this.pools.values()) {
      activeConnections += poolEntry.connections;
    }

    return {
      totalPools: this.pools.size,
      activeConnections
    };
  }
}
```

---

## Migration Strategies

### Tenant Migration Between Tiers

```typescript
/**
 * Tenant migration from one tier to another
 */
enum MigrationType {
  UPGRADE = 'upgrade',       // Startup -> Growth
  DOWNGRADE = 'downgrade',   // Growth -> Startup
  MIGRATE = 'migrate'        // Between models
}

interface TenantMigration {
  id: string;
  tenantId: string;
  from: {
    tier: TenantTier;
    model: MultiTenancyModel;
  };
  to: {
    tier: TenantTier;
    model: MultiTenancyModel;
  };
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'rolled_back';
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
}

/**
 * Tenant migration service
 */
class TenantMigrationService {
  /**
   * Upgrade tenant to higher tier
   */
  async upgrade(
    tenantId: string,
    toTier: TenantTier
  ): Promise<TenantMigration> {
    const tenant = await loadTenantContext(tenantId);

    if (tenant.tier === toTier) {
      throw new Error('Tenant already at this tier');
    }

    if (!this.isValidUpgrade(tenant.tier, toTier)) {
      throw new Error('Invalid tier upgrade');
    }

    const migration: TenantMigration = {
      id: generateId(),
      tenantId,
      from: {
        tier: tenant.tier,
        model: tenant.multiTenancyModel
      },
      to: {
        tier: toTier,
        model: tierConfigs[toTier].multiTenancyModel
      },
      status: 'pending'
    };

    await db.insert(tenantMigrations).values(migration);

    // Execute migration asynchronously
    this.executeMigration(migration.id).catch(console.error);

    return migration;
  }

  /**
   * Execute tenant migration
   */
  private async executeMigration(migrationId: string): Promise<void> {
    await db.update(tenantMigrations)
      .set({ status: 'in_progress', startedAt: new Date() })
      .where(eq(tenantMigrations.id, migrationId));

    const migration = await db.query.tenantMigrations.findFirst({
      where: eq(tenantMigrations.id, migrationId)
    });

    if (!migration) {
      throw new Error('Migration not found');
    }

    try {
      // Step 1: Create new schema/database
      await this.createTargetEnvironment(migration);

      // Step 2: Migrate data
      await this.migrateData(migration);

      // Step 3: Update DNS/routing
      await this.updateRouting(migration);

      // Step 4: Update tenant record
      await db.update(tenants)
        .set({
          tier: migration.to.tier,
          multiTenancyModel: migration.to.model
        })
        .where(eq(tenants.id, migration.tenantId));

      // Step 5: Apply new configuration template
      await applyConfigurationTemplate(
        migration.tenantId,
        migration.to.tier
      );

      // Mark complete
      await db.update(tenantMigrations)
        .set({
          status: 'completed',
          completedAt: new Date()
        })
        .where(eq(tenantMigrations.id, migrationId));

    } catch (error) {
      // Rollback on failure
      await this.rollbackMigration(migration);

      await db.update(tenantMigrations)
        .set({
          status: 'rolled_back',
          error: error instanceof Error ? error.message : 'Unknown error'
        })
        .where(eq(tenantMigrations.id, migrationId));
    }
  }

  /**
   * Create target environment for migration
   */
  private async createTargetEnvironment(
    migration: TenantMigration
  ): Promise<void> {
    const targetModel = migration.to.model;

    switch (targetModel) {
      case MultiTenancyModel.SCHEMA_PER_TENANT:
        await this.createTenantSchema(migration.tenantId);
        break;

      case MultiTenancyModel.DATABASE_PER_TENANT:
        await this.createTenantDatabase(migration.tenantId);
        break;

      case MultiTenancyModel.SHARED_SCHEMA:
        // No special setup needed
        break;
    }
  }

  /**
   * Create dedicated schema for tenant
   */
  private async createTenantSchema(tenantId: string): Promise<void> {
    await db.execute(`
      CREATE SCHEMA tenant_${tenantId};

      -- Copy table structure
      CREATE TABLE tenant_${tenantId}.customers
        (LIKE public.customers INCLUDING ALL);

      CREATE TABLE tenant_${tenantId}.trips
        (LIKE public.trips INCLUDING ALL);

      -- ... other tables
    `);
  }

  /**
   * Create dedicated database for tenant
   */
  private async createTenantDatabase(tenantId: string): Promise<void> {
    await db.execute(`
      CREATE DATABASE tenant_${tenantId}
        TEMPLATE template0;

      -- Connect to new database and create tables
      \c tenant_${tenantId}

      -- Run schema migration scripts
    `);
  }

  /**
   * Migrate data from source to target
   */
  private async migrateData(
    migration: TenantMigration
  ): Promise<void> {
    const { tenantId, from, to } = migration;

    // If moving to isolated environment
    if (to.model !== MultiTenancyModel.SHARED_SCHEMA) {
      await this.copyDataToIsolatedEnvironment(tenantId, to.model);
    }

    // If moving from isolated to shared
    if (from.model !== MultiTenancyModel.SHARED_SCHEMA &&
        to.model === MultiTenancyModel.SHARED_SCHEMA) {
      await this.copyDataToSharedEnvironment(tenantId, from.model);
    }
  }

  /**
   * Copy data to isolated schema/database
   */
  private async copyDataToIsolatedEnvironment(
    tenantId: string,
    targetModel: MultiTenancyModel
  ): Promise<void> {
    const tables = ['customers', 'trips', 'bookings', 'quotes'];

    for (const table of tables) {
      const targetTable = targetModel === MultiTenancyModel.SCHEMA_PER_TENANT
        ? `tenant_${tenantId}.${table}`
        : `${table}`;  // Different database connection

      await db.execute(`
        INSERT INTO ${targetTable}
        SELECT * FROM public.${table}
        WHERE tenant_id = '${tenantId}';
      `);
    }
  }

  /**
   * Update routing after migration
   */
  private async updateRouting(
    migration: TenantMigration
  ): Promise<void> {
    // Update routing configuration if needed
    // This might involve DNS changes or load balancer updates
  }

  /**
   * Rollback failed migration
   */
  private async rollbackMigration(
    migration: TenantMigration
  ): Promise<void> {
    // Drop created schema/database
    const targetModel = migration.to.model;

    switch (targetModel) {
      case MultiTenancyModel.SCHEMA_PER_TENANT:
        await db.execute(`DROP SCHEMA IF EXISTS tenant_${migration.tenantId} CASCADE;`);
        break;

      case MultiTenancyModel.DATABASE_PER_TENANT:
        await db.execute(`DROP DATABASE IF EXISTS tenant_${migration.tenantId};`);
        break;
    }
  }

  /**
   * Validate tier upgrade is valid
   */
  private isValidUpgrade(from: TenantTier, to: TenantTier): boolean {
    const tierOrder = [
      TenantTier.STARTUP,
      TenantTier.GROWTH,
      TenantTier.ENTERPRISE
    ];

    return tierOrder.indexOf(to) > tierOrder.indexOf(from);
  }
}
```

---

## Implementation

### Complete Tenant Service

```typescript
/**
 * Complete tenant management service
 */
class TenantService {
  private resolver: ChainedTenantResolver;
  private connectionManager: MultiTenantConnectionManager;
  private migrationService: TenantMigrationService;

  constructor() {
    this.resolver = new ChainedTenantResolver([
      new CustomDomainTenantResolver(),
      new SubdomainTenantResolver('travelagent.com'),
      new HeaderTenantResolver()
    ]);
    this.connectionManager = new MultiTenantConnectionManager({
      maxConnections: 100,
      maxConnectionsPerTenant: 10,
      poolIdleTimeoutMillis: 300000
    });
    this.migrationService = new TenantMigrationService();
  }

  /**
   * Create new tenant
   */
  async createTenant(input: {
    name: string;
    subdomain: string;
    tier: TenantTier;
    adminEmail: string;
    adminName: string;
  }): Promise<Tenant> {
    // Validate subdomain availability
    const existing = await db.query.tenants.findFirst({
      where: eq(tenants.subdomain, input.subdomain.toLowerCase())
    });

    if (existing) {
      throw new Error('Subdomain already taken');
    }

    // Create tenant record
    const tenant = await db.insert(tenants).values({
      id: generateId(),
      name: input.name,
      subdomain: input.subdomain.toLowerCase(),
      tier: input.tier,
      multiTenancyModel: tierConfigs[input.tier].multiTenancyModel,
      status: 'provisioning',
      createdAt: new Date()
    }).returning().then(rows => rows[0]);

    // Apply configuration template
    await applyConfigurationTemplate(tenant.id, input.tier);

    // Create admin user
    const adminUser = await this.createAdminUser(tenant.id, {
      email: input.adminEmail,
      name: input.adminName
    });

    // Provision tenant environment
    await this.provisionTenant(tenant.id);

    // Mark tenant as active
    await db.update(tenants)
      .set({ status: 'active' })
      .where(eq(tenants.id, tenant.id));

    return tenant;
  }

  /**
   * Provision tenant environment
   */
  private async provisionTenant(tenantId: string): Promise<void> {
    const tenant = await loadTenantContext(tenantId);

    switch (tenant.multiTenancyModel) {
      case MultiTenancyModel.SCHEMA_PER_TENANT:
        await this.createTenantSchema(tenantId);
        break;

      case MultiTenancyModel.DATABASE_PER_TENANT:
        await this.createTenantDatabase(tenantId);
        break;

      case MultiTenancyModel.SHARED_SCHEMA:
        // No special provisioning needed
        break;
    }

    // Seed default data
    await this.seedDefaultData(tenantId);
  }

  /**
   * Seed default data for tenant
   */
  private async seedDefaultData(tenantId: string): Promise<void> {
    // Create default tags
    await db.insert(tags).values([
      { id: generateId(), tenantId, name: 'Hot Lead', color: '#EF4444' },
      { id: generateId(), tenantId, name: 'Follow Up', color: '#F59E0B' },
      { id: generateId(), tenantId, name: 'Closed', color: '#10B981' }
    ]);

    // Create default email templates
    // ... additional seed data
  }

  /**
   * Create admin user for tenant
   */
  private async createAdminUser(
    tenantId: string,
    input: { email: string; name: string }
  ): Promise<User> {
    const hashedPassword = await hashPassword(generateTemporaryPassword());

    return db.insert(users).values({
      id: generateId(),
      tenantId,
      email: input.email,
      name: input.name,
      passwordHash: hashedPassword,
      role: 'admin',
      isActive: true,
      createdAt: new Date()
    }).returning().then(rows => rows[0]);
  }

  /**
   * Suspend tenant
   */
  async suspendTenant(
    tenantId: string,
    reason: string
  ): Promise<void> {
    await db.update(tenants)
      .set({
        status: 'suspended',
        suspensionReason: reason,
        suspendedAt: new Date()
      })
      .where(eq(tenants.id, tenantId));

    // Revoke all active sessions
    await db.delete(sessions)
      .where(eq(sessions.tenantId, tenantId));
  }

  /**
   * Terminate tenant
   */
  async terminateTenant(
    tenantId: string,
    options: {
      exportData?: boolean;
      retentionDays?: number;
    } = {}
  ): Promise<void> {
    // Export data if requested
    if (options.exportData) {
      await this.exportTenantData(tenantId);
    }

    // Mark for deletion
    await db.update(tenants)
      .set({
        status: 'terminated',
        terminatedAt: new Date(),
        deletionScheduledAt: new Date(
          Date.now() + (options.retentionDays || 30) * 24 * 60 * 60 * 1000
        )
      })
      .where(eq(tenants.id, tenantId));
  }

  /**
   * Export tenant data
   */
  private async exportTenantData(tenantId: string): Promise<string> {
    const data = {
      customers: await db.query.customers.findMany({
        where: eq(customers.tenantId, tenantId)
      }),
      trips: await db.query.trips.findMany({
        where: eq(trips.tenantId, tenantId)
      }),
      bookings: await db.query.bookings.findMany({
        where: eq(bookings.tenantId, tenantId)
      })
      // ... other entities
    };

    const exportPath = `/exports/${tenantId}/${Date.now()}.json`;
    await fs.writeFile(exportPath, JSON.stringify(data, null, 2));

    return exportPath;
  }
}
```

---

## Testing Scenarios

### Unit Tests

```typescript
describe('SubdomainTenantResolver', () => {
  const resolver = new SubdomainTenantResolver('travelagent.com');

  it('should resolve tenant from subdomain', async () => {
    const result = await resolver.resolve('acme.travelagent.com');

    expect(result).toEqual({
      tenantId: 'tenant-123',
      method: TenantIdentificationMethod.SUBDOMAIN,
      confidence: 'certain',
      metadata: { subdomain: 'acme', domain: 'acme.travelagent.com' }
    });
  });

  it('should skip reserved subdomains', async () => {
    const result = await resolver.resolve('www.travelagent.com');
    expect(result).toBeNull();
  });

  it('should handle non-matching domains', async () => {
    const result = await resolver.resolve('example.com');
    expect(result).toBeNull();
  });
});

describe('TenantContextManager', () => {
  it('should propagate context through async operations', async () => {
    const context: TenantContext = {
      tenantId: 'test-tenant',
      tier: TenantTier.STARTUP,
      configuration: {} as any,
      quotas: {} as any,
      features: {} as any,
      metadata: {} as any
    };

    const result = await TenantContextManager.withContext(context, async () => {
      return TenantContextManager.getTenantId();
    });

    expect(result).toBe('test-tenant');
  });

  it('should throw when context not set', () => {
    expect(() => TenantContextManager.getTenantId()).toThrow();
  });
});

describe('TenantQueryBuilder', () => {
  it('should include tenant_id in inserts', async () => {
    const qb = new TenantQueryBuilder('tenant-123', 'customers');

    const customer = await qb.insert({
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@example.com'
    });

    expect(customer.tenant_id).toBe('tenant-123');
  });
});
```

### Integration Tests

```typescript
describe('Multi-tenancy Integration', () => {
  let tenantService: TenantService;
  let tenantId: string;

  beforeAll(async () => {
    tenantService = new TenantService();
  });

  it('should create and provision new tenant', async () => {
    const tenant = await tenantService.createTenant({
      name: 'Test Agency',
      subdomain: `test-${Date.now()}`,
      tier: TenantTier.STARTUP,
      adminEmail: 'admin@test.com',
      adminName: 'Admin User'
    });

    tenantId = tenant.id;
    expect(tenant.status).toBe('active');
  });

  it('should isolate data between tenants', async () => {
    // Create customer in tenant 1
    const qb1 = new TenantQueryBuilder(tenantId, 'customers');
    await qb1.insert({
      firstName: 'Jane',
      lastName: 'Smith',
      email: 'jane@tenant1.com'
    });

    // Create customer in tenant 2
    const tenant2Id = 'tenant-456';
    const qb2 = new TenantQueryBuilder(tenant2Id, 'customers');
    await qb2.insert({
      firstName: 'Bob',
      lastName: 'Jones',
      email: 'bob@tenant2.com'
    });

    // Verify isolation
    const tenant1Customers = await qb1.findMany({});
    const tenant2Customers = await qb2.findMany({});

    expect(tenant1Customers).toHaveLength(1);
    expect(tenant2Customers).toHaveLength(1);
    expect(tenant1Customers[0].email).toBe('jane@tenant1.com');
    expect(tenant2Customers[0].email).toBe('bob@tenant2.com');
  });

  it('should prevent cross-tenant data access via RLS', async () => {
    const qb = new TenantQueryBuilder(tenantId, 'customers');

    // Try to access other tenant's customer
    const otherCustomer = await qb.findById('customer-from-other-tenant');

    expect(otherCustomer).toBeNull();
  });

  it('should apply configuration template', async () => {
    const configManager = new TenantConfigurationManager();

    const maxUsers = await configManager.get<number>(
      tenantId,
      'quota.maxUsers'
    );

    expect(maxUsers).toBe(5); // Startup tier default
  });
});
```

---

## API Specification

### Tenant Management API

```yaml
# OpenAPI specification for tenant management
openapi: 3.0.0
info:
  title: Travel Agency Agent - Tenant API
  version: 1.0.0

paths:
  /api/v1/tenants:
    post:
      summary: Create new tenant
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, subdomain, tier, adminEmail]
              properties:
                name:
                  type: string
                subdomain:
                  type: string
                  pattern: '^[a-z0-9-]+$'
                tier:
                  type: string
                  enum: [startup, growth, enterprise]
                adminEmail:
                  type: string
                  format: email
                adminName:
                  type: string
      responses:
        '201':
          description: Tenant created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Tenant'

  /api/v1/tenants/{tenantId}:
    get:
      summary: Get tenant details
      parameters:
        - name: tenantId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Tenant details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Tenant'

    put:
      summary: Update tenant
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                tier:
                  type: string
                  enum: [startup, growth, enterprise]
      responses:
        '200':
          description: Tenant updated

    delete:
      summary: Terminate tenant
      parameters:
        - name: exportData
          in: query
          schema:
            type: boolean
        - name: retentionDays
          in: query
          schema:
            type: integer
            default: 30
      responses:
        '202':
          description: Tenant termination scheduled

  /api/v1/tenants/{tenantId}/upgrade:
    post:
      summary: Upgrade tenant tier
      parameters:
        - name: tenantId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [toTier]
              properties:
                toTier:
                  type: string
                  enum: [growth, enterprise]
      responses:
        '202':
          description: Migration initiated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Migration'

  /api/v1/tenants/{tenantId}/config:
    get:
      summary: Get tenant configuration
      responses:
        '200':
          description: Configuration
          content:
            application/json:
              schema:
                type: object

    put:
      summary: Update tenant configuration
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Configuration updated

  /api/v1/tenants/{tenantId}/domains:
    post:
      summary: Add custom domain
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [domain]
              properties:
                domain:
                  type: string
      responses:
        '201':
          description: Domain added

components:
  schemas:
    Tenant:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        subdomain:
          type: string
        tier:
          type: string
          enum: [startup, growth, enterprise]
        status:
          type: string
          enum: [provisioning, active, suspended, terminated]
        createdAt:
          type: string
          format: date-time

    Migration:
      type: object
      properties:
        id:
          type: string
        tenantId:
          type: string
        from:
          type: object
          properties:
            tier:
              type: string
            model:
              type: string
        to:
          type: object
          properties:
            tier:
              type: string
            model:
              type: string
        status:
          type: string
          enum: [pending, in_progress, completed, failed, rolled_back]
```

---

## Metrics and Monitoring

### Key Metrics

```typescript
/**
 * Multi-tenancy metrics
 */
interface MultiTenancyMetrics {
  // Tenant counts
  totalTenants: number;
  activeTenants: number;
  suspendedTenants: number;
  tenantsByTier: Record<TenantTier, number>;

  // Resource usage
  totalStorage: number;
  storageByTenant: Array<{ tenantId: string; size: number }>;
  databaseConnections: number;
  connectionPoolSize: number;

  // Migration metrics
  pendingMigrations: number;
  completedMigrations: number;
  failedMigrations: number;
  averageMigrationTime: number;

  // Onboarding metrics
  newTenantsToday: number;
  averageProvisioningTime: number;

  // Performance metrics
  averageQueryTimeByTenant: Array<{ tenantId: string; avgTime: number }>;
  slowQueriesByTenant: Array<{ tenantId: string; count: number }>;
}

/**
 * Metrics collector
 */
class MultiTenancyMetricsCollector {
  /**
   * Collect tenant metrics
   */
  async collectMetrics(): Promise<MultiTenancyMetrics> {
    const [
      totalTenants,
      activeTenants,
      suspendedTenants,
      tenantsByTier,
      storageMetrics,
      migrationMetrics
    ] = await Promise.all([
      this.getTenantCounts(),
      this.getTenantCountsByStatus(),
      this.getTenantCountsByTier(),
      this.getStorageMetrics(),
      this.getMigrationMetrics()
    ]);

    return {
      totalTenants,
      activeTenants,
      suspendedTenants,
      tenantsByTier,
      ...storageMetrics,
      ...migrationMetrics
    };
  }

  private async getTenantCounts(): Promise<number> {
    const result = await db.execute(`
      SELECT COUNT(*) as count FROM tenants;
    `);
    return parseInt(result.rows[0].count);
  }

  private async getTenantCountsByStatus(): Promise<{
    active: number;
    suspended: number;
  }> {
    const result = await db.execute(`
      SELECT status, COUNT(*) as count
      FROM tenants
      GROUP BY status;
    `);

    return {
      active: result.rows.find(r => r.status === 'active')?.count || 0,
      suspended: result.rows.find(r => r.status === 'suspended')?.count || 0
    };
  }

  private async getTenantCountsByTier(): Promise<Record<TenantTier, number>> {
    const result = await db.execute(`
      SELECT tier, COUNT(*) as count
      FROM tenants
      WHERE status = 'active'
      GROUP BY tier;
    `);

    return {
      startup: result.rows.find(r => r.tier === 'startup')?.count || 0,
      growth: result.rows.find(r => r.tier === 'growth')?.count || 0,
      enterprise: result.rows.find(r => r.tier === 'enterprise')?.count || 0
    };
  }

  private async getStorageMetrics(): Promise<{
    totalStorage: number;
    storageByTenant: Array<{ tenantId: string; size: number }>;
    databaseConnections: number;
    connectionPoolSize: number;
  }> {
    // Implementation depends on database and storage system
    return {
      totalStorage: 0,
      storageByTenant: [],
      databaseConnections: 0,
      connectionPoolSize: 0
    };
  }

  private async getMigrationMetrics(): Promise<{
    pendingMigrations: number;
    completedMigrations: number;
    failedMigrations: number;
    averageMigrationTime: number;
  }> {
    const result = await db.execute(`
      SELECT
        status,
        COUNT(*) as count,
        AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_time
      FROM tenant_migrations
      WHERE started_at IS NOT NULL
      GROUP BY status;
    `);

    return {
      pendingMigrations: result.rows.find(r => r.status === 'pending')?.count || 0,
      completedMigrations: result.rows.find(r => r.status === 'completed')?.count || 0,
      failedMigrations: result.rows.find(r => r.status === 'failed')?.count || 0,
      averageMigrationTime: parseFloat(
        result.rows.find(r => r.status === 'completed')?.avg_time || '0'
      )
    };
  }
}
```

---

**End of Document**

**Next:** [Tenant Isolation Deep Dive](MULTI_TENANCY_02_ISOLATION.md)
