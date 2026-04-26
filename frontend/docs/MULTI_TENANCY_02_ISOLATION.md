# Tenant Isolation — Technical Deep Dive

> Comprehensive guide to tenant isolation mechanisms for the Travel Agency Agent platform

---

## Document Metadata

**Series:** Multi-tenancy Patterns
**Document:** 2 of 4 (Isolation)
**Last Updated:** 2026-04-26
**Status:** ✅ Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Data Isolation](#data-isolation)
3. [Row-Level Security](#row-level-security)
4. [Application-Layer Isolation](#application-layer-isolation)
5. [Resource Isolation](#resource-isolation)
6. [Network Isolation](#network-isolation)
7. [Encryption Per Tenant](#encryption-per-tenant)
8. [Audit Logging](#audit-logging)
9. [Leakage Prevention](#leakage-prevention)
10. [Implementation](#implementation)
11. [Testing Scenarios](#testing-scenarios)
12. [API Specification](#api-specification)
13. [Metrics and Monitoring](#metrics-and-monitoring)

---

## Overview

Tenant isolation ensures that each tenant's data, resources, and operations are completely separated from other tenants. This is critical for security, compliance, and trust.

### Isolation Requirements

- **Data Separation:** No cross-tenant data access
- **Performance Isolation:** No "noisy neighbor" problems
- **Security:** Prevent data leakage between tenants
- **Compliance:** Meet regulatory requirements for data handling
- **Auditability:** Track all tenant-specific operations

### Threat Model

| Threat | Description | Mitigation |
|--------|-------------|------------|
| **Cross-tenant data access** | One tenant accessing another's data | RLS, application-level checks |
| **Data leakage in logs** | Sensitive data exposed in logs | Log scrubbing, structured logging |
| **Resource exhaustion** | One tenant affecting others | Quotas, rate limiting |
| **Side-channel attacks** | Inferring data through timing/cache | Constant-time operations, cache isolation |
| **Metadata leakage** | Exposing tenant existence | Generic error messages |

---

## Data Isolation

### Isolation Levels

```typescript
/**
 * Data isolation levels
 */
enum DataIsolationLevel {
  SHARED_SCHEMA = 'shared_schema',     // tenant_id column with RLS
  SEPARATE_SCHEMA = 'separate_schema', // separate schema per tenant
  SEPARATE_DATABASE = 'separate_database' // separate DB per tenant
}

interface IsolationConfig {
  level: DataIsolationLevel;
  enforceRLS: boolean;
  enableAuditLog: boolean;
  enableEncryption: boolean;
  encryptionKeySource: 'kms' | 'vault' | 'internal';
}
```

### Tenant Data Mapper

```typescript
/**
 * Tenant data mapper - ensures all queries include tenant_id
 */
class TenantDataMapper<T extends { tenant_id?: string }> {
  private tenantId: string;
  private tableName: string;

  constructor(tenantId: string, tableName: string) {
    this.tenantId = tenantId;
    this.tableName = tableName;
  }

  /**
   * Prepare data for insert - add tenant_id
   */
  prepareForInsert(data: Omit<T, 'tenant_id' | 'id' | 'created_at' | 'updated_at'>): T {
    return {
      ...data,
      tenant_id: this.tenantId
    } as T;
  }

  /**
   * Prepare filter - add tenant_id
   */
  prepareFilter(filter: Record<string, unknown>): Record<string, unknown> {
    return {
      ...filter,
      tenant_id: this.tenantId
    };
  }

  /**
   * Validate tenant ownership before operation
   */
  async validateOwnership(id: string): Promise<boolean> {
    const result = await db.execute(`
      SELECT 1 FROM ${this.tableName}
      WHERE id = $1 AND tenant_id = $2
      LIMIT 1;
    `, [id, this.tenantId]);

    return result.rowCount > 0;
  }

  /**
   * Validate batch ownership
   */
  async validateBatchOwnership(ids: string[]): Promise<Set<string>> {
    if (ids.length === 0) return new Set();

    const result = await db.execute(`
      SELECT id FROM ${this.tableName}
      WHERE id = ANY($1) AND tenant_id = $2;
    `, [ids, this.tenantId]);

    const validIds = new Set(result.rows.map(r => r.id));
    return validIds;
  }
}
```

### Foreign Key Tenant Validation

```typescript
/**
 * Cross-table tenant validation
 */
class TenantForeignKeyValidator {
  /**
   * Validate that referenced entity belongs to same tenant
   */
  async validateForeignKey(
    tenantId: string,
    referencedTable: string,
    referencedId: string
  ): Promise<boolean> {
    const result = await db.execute(`
      SELECT 1 FROM ${referencedTable}
      WHERE id = $1 AND tenant_id = $2
      LIMIT 1;
    `, [referencedId, tenantId]);

    return result.rowCount > 0;
  }

  /**
   * Batch validate foreign keys
   */
  async validateForeignKeys(
    tenantId: string,
    references: Array<{ table: string; id: string }>
  ): Promise<{ valid: boolean; invalid: Array<{ table: string; id: string }> }> {
    const invalid: Array<{ table: string; id: string }> = [];

    for (const ref of references) {
      const isValid = await this.validateForeignKey(tenantId, ref.table, ref.id);
      if (!isValid) {
        invalid.push(ref);
      }
    }

    return {
      valid: invalid.length === 0,
      invalid
    };
  }

  /**
   * Create foreign key with tenant constraint
   */
  async createTenantAwareForeignKey(
    table: string,
    column: string,
    referencedTable: string,
    referencedColumn: string
  ): Promise<void> {
    await db.execute(`
      ALTER TABLE ${table}
      ADD CONSTRAINT ${table}_${column}_tenant_fk
      FOREIGN KEY (${column}, tenant_id)
      REFERENCES ${referencedTable}(${referencedColumn}, tenant_id);

      -- Also add check to ensure tenant_id matches
      ALTER TABLE ${table}
      ADD CONSTRAINT ${table}_${column}_tenant_check
      CHECK (tenant_id = (
        SELECT tenant_id FROM ${referencedTable}
        WHERE ${referencedTable}.${referencedColumn} = ${table}.${column}
      ));
    `);
  }
}
```

---

## Row-Level Security

### RLS Policy Generator

```typescript
/**
 * Row-Level Security policy generator
 */
class RLSPolicyGenerator {
  /**
   * Generate tenant isolation policy SQL
   */
  generateTenantIsolationPolicy(config: {
    tableName: string;
    policyName: string;
    tenantIdColumn?: string;
    checkInsert?: boolean;
  }): string {
    const {
      tableName,
      policyName,
      tenantIdColumn = 'tenant_id',
      checkInsert = true
    } = config;

    const selectClause = `USING (${tenantIdColumn} = current_setting('app.current_tenant_id', true)::uuid)`;
    const insertClause = checkInsert
      ? `WITH CHECK (${tenantIdColumn} = current_setting('app.current_tenant_id', true)::uuid)`
      : '';

    return `
      DROP POLICY IF EXISTS ${policyName} ON ${tableName};

      CREATE POLICY ${policyName}
      ON ${tableName}
      FOR ALL
      ${selectClause}
      ${checkInsert ? insertClause : ''};
    `;
  }

  /**
   * Generate selective RLS policy (some rows public)
   */
  generateSelectiveIsolationPolicy(config: {
    tableName: string;
    policyName: string;
    publicCondition?: string;
  }): string {
    const { tableName, policyName, publicCondition = 'is_public = true' } = config;

    return `
      DROP POLICY IF EXISTS ${policyName} ON ${tableName};

      CREATE POLICY ${policyName}
      ON ${tableName}
      FOR ALL
      USING (
        ${publicCondition} OR
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
      )
      WITH CHECK (
        (${publicCondition}) OR
        (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
      );
    `;
  }

  /**
   * Generate admin bypass policy
   */
  generateAdminBypassPolicy(config: {
    tableName: string;
    policyName: string;
    adminRole: string;
  }): string {
    const { tableName, policyName, adminRole = 'platform_admin' } = config;

    return `
      DROP POLICY IF EXISTS ${policyName} ON ${tableName};

      CREATE POLICY ${policyName}
      ON ${tableName}
      FOR ALL
      USING (
        current_setting('app.is_platform_admin', true)::boolean OR
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
      )
      WITH CHECK (
        current_setting('app.is_platform_admin', true)::boolean OR
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
      );
    `;
  }
}
```

### RLS Manager

```typescript
/**
 * Complete RLS management service
 */
class RLSManager {
  private generator: RLSPolicyGenerator;

  constructor() {
    this.generator = new RLSPolicyGenerator();
  }

  /**
   * Enable RLS on a table
   */
  async enableRLS(tableName: string): Promise<void> {
    await db.execute(`ALTER TABLE ${tableName} ENABLE ROW LEVEL SECURITY;`);
  }

  /**
   * Disable RLS on a table (use with caution)
   */
  async disableRLS(tableName: string): Promise<void> {
    await db.execute(`ALTER TABLE ${tableName} DISABLE ROW LEVEL SECURITY;`);
  }

  /**
   * Apply tenant isolation to table
   */
  async applyTenantIsolation(tableName: string): Promise<void> {
    await this.enableRLS(tableName);

    const policySql = this.generator.generateTenantIsolationPolicy({
      tableName,
      policyName: `${tableName}_tenant_isolation`
    });

    await db.execute(policySql);
  }

  /**
   * Apply isolation to all tables
   */
  async applyIsolationToAllTables(tables: string[]): Promise<void> {
    for (const table of tables) {
      try {
        await this.applyTenantIsolation(table);
      } catch (error) {
        console.error(`Failed to apply RLS to ${table}:`, error);
        throw error;
      }
    }
  }

  /**
   * Set tenant context for database session
   */
  async setTenantContext(tenantId: string, isAdmin = false): Promise<void> {
    await db.execute(`SET LOCAL app.current_tenant_id = '${tenantId}';`);
    if (isAdmin) {
      await db.execute(`SET LOCAL app.is_platform_admin = 'true';`);
    }
  }

  /**
   * Clear tenant context
   */
  async clearTenantContext(): Promise<void> {
    await db.execute(`RESET app.current_tenant_id;`);
    await db.execute(`RESET app.is_platform_admin;`);
  }

  /**
   * Verify RLS is working
   */
  async verifyIsolation(
    tableName: string,
    tenant1Id: string,
    tenant2Id: string,
    testRecordId: string
  ): Promise<boolean> {
    // Create test record for tenant 1
    await db.execute(`
      INSERT INTO ${tableName} (id, tenant_id, data)
      VALUES ('${testRecordId}', '${tenant1Id}', 'test');
    `);

    // Try to access as tenant 2
    await this.setTenantContext(tenant2Id);
    const result = await db.execute(`
      SELECT * FROM ${tableName} WHERE id = '${testRecordId}';
    `);

    await this.clearTenantContext();

    // Clean up
    await db.execute(`DELETE FROM ${tableName} WHERE id = '${testRecordId}';`);

    // Should return 0 rows
    return result.rowCount === 0;
  }

  /**
   * Get RLS policy status for table
   */
  async getPolicyStatus(tableName: string): Promise<{
    rlsEnabled: boolean;
    policies: Array<{ name: string; cmd: string; roles: string[] }>;
  }> {
    const rlsResult = await db.execute(`
      SELECT relrowsecurity FROM pg_class WHERE relname = '${tableName}';
    `);

    const policiesResult = await db.execute(`
      SELECT
        policyname as name,
        cmd,
        array_agg(roleid::regrole::text) as roles
      FROM pg_policy
      WHERE tablename = '${tableName}'::regclass
      GROUP BY policyname, cmd;
    `);

    return {
      rlsEnabled: rlsResult.rows[0]?.relrowsecurity || false,
      policies: policiesResult.rows
    };
  }
}
```

### RLS with Complex Conditions

```typescript
/**
 * Advanced RLS policies for complex scenarios
 */
class AdvancedRLSPolicies {
  /**
   * Policy for shared resources (e.g., supplier catalogs)
   */
  async applySharedResourcePolicy(tableName: string): Promise<void> {
    await db.execute(`
      DROP POLICY IF EXISTS ${tableName}_shared_policy ON ${tableName};

      CREATE POLICY ${tableName}_shared_policy
      ON ${tableName}
      FOR SELECT
      USING (is_shared = true);
    `);
  }

  /**
   * Policy for hierarchical tenant access
   */
  async applyHierarchicalPolicy(
    tableName: string,
    hierarchyTable: string
  ): Promise<void> {
    await db.execute(`
      DROP POLICY IF EXISTS ${tableName}_hierarchical_policy ON ${tableName};

      CREATE POLICY ${tableName}_hierarchical_policy
      ON ${tableName}
      FOR ALL
      USING (
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
        OR EXISTS (
          SELECT 1 FROM ${hierarchyTable}
          WHERE parent_id = current_setting('app.current_tenant_id', true)::uuid
          AND child_id = ${tableName}.tenant_id
        )
      );
    `);
  }

  /**
   * Policy with time-based access
   */
  async applyTimeBasedPolicy(
    tableName: string,
    accessColumn: string
  ): Promise<void> {
    await db.execute(`
      DROP POLICY IF EXISTS ${tableName}_time_policy ON ${tableName};

      CREATE POLICY ${tableName}_time_policy
      ON ${tableName}
      FOR SELECT
      USING (
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
        AND ${accessColumn} >= NOW() - INTERVAL '1 year'
      );
    `);
  }

  /**
   * Policy for user-scoped access within tenant
   */
  async applyUserScopedPolicy(
    tableName: string,
    userColumn: string
  ): Promise<void> {
    await db.execute(`
      DROP POLICY IF EXISTS ${tableName}_user_policy ON ${tableName};

      CREATE POLICY ${tableName}_user_policy
      ON ${tableName}
      FOR ALL
      USING (
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
        AND (
          ${userColumn} = current_setting('app.current_user_id', true)::uuid
          OR ${userColumn} IS NULL  -- Shared within tenant
        )
      );
    `);
  }
}
```

---

## Application-Layer Isolation

### Tenant-Aware Repository Pattern

```typescript
/**
 * Base repository with tenant isolation
 */
abstract class TenantAwareRepository<T extends { id: string; tenant_id: string }> {
  protected tableName: string;
  protected tenantId: string;

  constructor(tenantId: string, tableName: string) {
    this.tenantId = tenantId;
    this.tableName = tableName;
  }

  /**
   * Find by ID (with tenant isolation)
   */
  async findById(id: string): Promise<T | null> {
    await RLSManager.setTenantContext(this.tenantId);

    const result = await db.query[this.tableName].findFirst({
      where: eq(this.tableName + '.id', id)
    });

    return result || null;
  }

  /**
   * Find many with filters
   */
  async findMany(filters: Record<string, unknown> = {}): Promise<T[]> {
    await RLSManager.setTenantContext(this.tenantId);

    return db.query[this.tableName].findMany({
      where: filters
    });
  }

  /**
   * Create entity
   */
  async create(data: Omit<T, 'id' | 'tenant_id' | 'created_at' | 'updated_at'>): Promise<T> {
    await RLSManager.setTenantContext(this.tenantId);

    const entity = {
      ...data,
      id: generateId(),
      tenant_id: this.tenantId,
      created_at: new Date(),
      updated_at: new Date()
    } as T;

    await db.insert(this.tableName).values(entity);
    return entity;
  }

  /**
   * Update entity
   */
  async update(
    id: string,
    data: Partial<Omit<T, 'id' | 'tenant_id' | 'created_at'>>
  ): Promise<T | null> {
    await RLSManager.setTenantContext(this.tenantId);

    await db.update(this.tableName)
      .set({ ...data, updated_at: new Date() })
      .where(eq(this.tableName + '.id', id));

    return this.findById(id);
  }

  /**
   * Delete entity
   */
  async delete(id: string): Promise<boolean> {
    await RLSManager.setTenantContext(this.tenantId);

    const result = await db.delete(this.tableName)
      .where(eq(this.tableName + '.id', id));

    return result.rowCount > 0;
  }

  /**
   * Count entities
   */
  async count(filters: Record<string, unknown> = {}): Promise<number> {
    await RLSManager.setTenantContext(this.tenantId);

    const result = await db.execute(`
      SELECT COUNT(*) as count FROM ${this.tableName}
      WHERE 1=1
      ${Object.entries(filters).map(([k, v]) => `AND ${k} = '${v}'`).join(' ')};
    `);

    return parseInt(result.rows[0].count);
  }
}

/**
 * Customer repository with tenant isolation
 */
class CustomerRepository extends TenantAwareRepository<Customer> {
  constructor(tenantId: string) {
    super(tenantId, 'customers');
  }

  async findByEmail(email: string): Promise<Customer | null> {
    await RLSManager.setTenantContext(this.tenantId);

    return db.query.customers.findFirst({
      where: eq(customers.email, email)
    });
  }

  async searchByName(query: string): Promise<Customer[]> {
    await RLSManager.setTenantContext(this.tenantId);

    return db.query.customers.findMany({
      where: or(
        ilike(customers.firstName, `%${query}%`),
        ilike(customers.lastName, `%${query}%`)
      )
    });
  }
}
```

### Service Layer Isolation

```typescript
/**
 * Tenant-aware service decorator
 */
function TenantIsolated(
  target: any,
  propertyKey: string,
  descriptor: PropertyDescriptor
) {
  const originalMethod = descriptor.value;

  descriptor.value = async function (...args: any[]) {
    const context = TenantContextManager.getContext();

    if (!context) {
      throw new Error('Tenant context required');
    }

    // Add tenant context to log context
    const logContext = {
      tenantId: context.tenantId,
      method: propertyKey,
      args: scrubSensitiveData(args)
    };

    console.log('[TenantIsolated] Entering', logContext);

    try {
      const result = await originalMethod.apply(this, args);
      console.log('[TenantIsolated] Success', logContext);
      return result;
    } catch (error) {
      console.error('[TenantIsolated] Error', {
        ...logContext,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  };

  return descriptor;
}

/**
 * Trip service with tenant isolation
 */
class TripService {
  @TenantIsolated
  async createTrip(input: CreateTripInput): Promise<Trip> {
    const context = TenantContextManager.getContext()!;

    // Verify customer belongs to tenant
    const customer = await new CustomerRepository(context.tenantId)
      .findById(input.customerId);

    if (!customer) {
      throw new Error('Customer not found');
    }

    const repo = new TenantAwareRepository<Trip>(context.tenantId, 'trips');
    return repo.create(input);
  }

  @TenantIsolated
  async getTrip(id: string): Promise<Trip | null> {
    const context = TenantContextManager.getContext()!;
    const repo = new TenantAwareRepository<Trip>(context.tenantId, 'trips');
    return repo.findById(id);
  }

  @TenantIsolated
  async listTrips(filters: TripFilters): Promise<Trip[]> {
    const context = TenantContextManager.getContext()!;
    const repo = new TenantAwareRepository<Trip>(context.tenantId, 'trips');
    return repo.findMany(filters);
  }
}
```

---

## Resource Isolation

### Compute Resource Quotas

```typescript
/**
 * Resource quota definition
 */
interface ResourceQuota {
  tenantId: string;
  maxCpuPercent: number;
  maxMemoryMB: number;
  maxConnections: number;
  maxRequestsPerMinute: number;
  maxStorageGB: number;
  maxConcurrentJobs: number;
}

/**
 * Resource quota manager
 */
class ResourceQuotaManager {
  private quotas: Map<string, ResourceQuota>;
  private usage: Map<string, ResourceUsage>;

  constructor() {
    this.quotas = new Map();
    this.usage = new Map();
  }

  /**
   * Set quota for tenant
   */
  setQuota(tenantId: string, quota: Omit<ResourceQuota, 'tenantId'>): void {
    this.quotas.set(tenantId, { tenantId, ...quota });
  }

  /**
   * Check if tenant can consume resource
   */
  async canConsume(
    tenantId: string,
    resource: keyof ResourceUsage
  ): Promise<boolean> {
    const quota = this.quotas.get(tenantId);
    if (!quota) return true; // No quota = unlimited

    const current = this.usage.get(tenantId) || this.getCurrentUsage(tenantId);
    const quotaKey = this.mapResourceToQuotaKey(resource);

    return current[resource] < (quota as any)[quotaKey];
  }

  /**
   * Record resource consumption
   */
  recordConsumption(
    tenantId: string,
    resource: keyof ResourceUsage,
    amount: number
  ): void {
    const usage = this.usage.get(tenantId) || this.getCurrentUsage(tenantId);
    (usage as any)[resource] += amount;
    this.usage.set(tenantId, usage);
  }

  /**
   * Get current usage for tenant
   */
  private getCurrentUsage(tenantId: string): ResourceUsage {
    return {
      cpuPercent: 0,
      memoryMB: 0,
      connections: 0,
      requestsThisMinute: 0,
      storageGB: 0,
      concurrentJobs: 0
    };
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
}

interface ResourceUsage {
  cpuPercent: number;
  memoryMB: number;
  connections: number;
  requestsThisMinute: number;
  storageGB: number;
  concurrentJobs: number;
}
```

### Rate Limiting Per Tenant

```typescript
/**
 * Tenant-aware rate limiter
 */
class TenantRateLimiter {
  private limiters: Map<string, RateLimiter>;
  private defaultLimit: number;
  private defaultWindow: number; // in seconds

  constructor(defaultLimit = 100, defaultWindow = 60) {
    this.defaultLimit = defaultLimit;
    this.defaultWindow = defaultWindow;
    this.limiters = new Map();
  }

  /**
   * Check if request is allowed
   */
  async checkLimit(
    tenantId: string,
    cost = 1
  ): Promise<{ allowed: boolean; remaining: number; resetAt: Date }> {
    let limiter = this.limiters.get(tenantId);

    if (!limiter) {
      const quota = await this.getTenantQuota(tenantId);
      limiter = new RateLimiter({
        tokensPerInterval: quota.rateLimit || this.defaultLimit,
        interval: this.defaultWindow * 1000
      });
      this.limiters.set(tenantId, limiter);
    }

    const result = await limiter.removeTokens(cost);

    return {
      allowed: result.allowed,
      remaining: result.remainingTokens,
      resetAt: new Date(result.nextRefillAt)
    };
  }

  /**
   * Reset rate limit for tenant
   */
  resetLimit(tenantId: string): void {
    this.limiters.delete(tenantId);
  }

  private async getTenantQuota(tenantId: string): Promise<{ rateLimit?: number }> {
    const config = await db.query.tenantConfig.findFirst({
      where: and(
        eq(tenantConfig.tenantId, tenantId),
        eq(tenantConfig.key, 'rate_limit')
      )
    });

    return {
      rateLimit: config?.value as number || undefined
    };
  }
}

/**
 * Rate limiter implementation
 */
class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private tokensPerInterval: number;
  private interval: number;

  constructor(config: { tokensPerInterval: number; interval: number }) {
    this.tokensPerInterval = config.tokensPerInterval;
    this.interval = config.interval;
    this.tokens = config.tokensPerInterval;
    this.lastRefill = Date.now();
  }

  async removeTokens(count = 1): Promise<{
    allowed: boolean;
    remainingTokens: number;
    nextRefillAt: number
  }> {
    this.refill();

    if (this.tokens >= count) {
      this.tokens -= count;
      return {
        allowed: true,
        remainingTokens: this.tokens,
        nextRefillAt: this.lastRefill + this.interval
      };
    }

    return {
      allowed: false,
      remainingTokens: this.tokens,
      nextRefillAt: this.lastRefill + this.interval
    };
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastRefill;

    if (elapsed >= this.interval) {
      this.tokens = this.tokensPerInterval;
      this.lastRefill = now;
    }
  }
}
```

### Storage Quotas

```typescript
/**
 * Storage quota manager
 */
class StorageQuotaManager {
  /**
   * Get storage usage for tenant
   */
  async getStorageUsage(tenantId: string): Promise<{
    total: number;
    byType: Record<string, number>;
  }> {
    const usage = {
      total: 0,
      byType: {
        documents: 0,
        images: 0,
        database: 0,
        logs: 0,
        backups: 0
      }
    };

    // Database size
    const dbResult = await db.execute(`
      SELECT
        pg_total_relation_size('customers') +
        pg_total_relation_size('trips') +
        pg_total_relation_size('bookings') as size
      WHERE tenant_id = '${tenantId}';
    `);
    usage.byType.database = parseInt(dbResult.rows[0]?.size || '0') / (1024 * 1024);

    // File storage
    const files = await db.query.fileStorage.findMany({
      where: eq(fileStorage.tenantId, tenantId)
    });

    for (const file of files) {
      const size = file.size || 0;
      usage.total += size;
      usage.byType[file.type] = (usage.byType[file.type] || 0) + size;
    }

    return usage;
  }

  /**
   * Check if tenant can upload file
   */
  async canUpload(
    tenantId: string,
    fileSize: number
  ): Promise<{ allowed: boolean; reason?: string }> {
    const [usage, quota] = await Promise.all([
      this.getStorageUsage(tenantId),
      this.getQuota(tenantId)
    ]);

    const totalBytes = usage.total + fileSize;
    const quotaBytes = quota.maxStorage * 1024 * 1024 * 1024; // GB to bytes

    if (totalBytes > quotaBytes) {
      return {
        allowed: false,
        reason: `Storage quota exceeded. Current: ${(usage.total / 1024 / 1024 / 1024).toFixed(2)}GB, Quota: ${quota.maxStorage}GB`
      };
    }

    return { allowed: true };
  }

  private async getQuota(tenantId: string): Promise<{ maxStorage: number }> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });

    const tierConfig = tierConfigs[tenant?.tier || TenantTier.STARTUP];
    return {
      maxStorage: tierConfig.maxStorage
    };
  }
}
```

---

## Network Isolation

### Tenant-Specific API Endpoints

```typescript
/**
 * Tenant API gateway
 */
class TenantAPIGateway {
  /**
   * Get tenant-specific base URL
   */
  getTenantBaseUrl(tenantId: string, request: Request): string {
    const host = request.headers.get('host') || '';

    // Check for custom domain
    const customDomain = this.getCustomDomain(tenantId);
    if (customDomain && host === customDomain) {
      return `${request.protocol}://${customDomain}`;
    }

    // Check for subdomain
    const subdomain = this.getSubdomain(tenantId);
    if (subdomain) {
      return `${request.protocol}://${subdomain}.${this.getBaseDomain()}`;
    }

    // Fall back to path-based routing
    return `${request.protocol}://${this.getBaseDomain()}/t/${tenantId}`;
  }

  /**
   * Get tenant-specific WebSocket endpoint
   */
  getTenantWebSocketUrl(tenantId: string): string {
    const subdomain = this.getSubdomain(tenantId);
    const wsProtocol = this.getBaseProtocol() === 'https' ? 'wss' : 'ws';

    if (subdomain) {
      return `${wsProtocol}://${subdomain}.${this.getBaseDomain()}/ws`;
    }

    return `${wsProtocol}://${this.getBaseDomain()}/ws/${tenantId}`;
  }

  private getBaseDomain(): string {
    return process.env.BASE_DOMAIN || 'travelagent.com';
  }

  private getBaseProtocol(): string {
    return process.env.PROTOCOL || 'https';
  }

  private async getCustomDomain(tenantId: string): Promise<string | null> {
    const domain = await db.query.tenantDomains.findFirst({
      where: eq(tenantDomains.tenantId, tenantId)
    });
    return domain?.domain || null;
  }

  private async getSubdomain(tenantId: string): Promise<string | null> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, tenantId)
    });
    return tenant?.subdomain || null;
  }
}
```

### Network Policies (Kubernetes)

```typescript
/**
 * Kubernetes network policy for tenant isolation
 */
interface NetworkPolicy {
  metadata: {
    name: string;
    namespace: string;
    labels: Record<string, string>;
  };
  spec: {
    podSelector: Record<string, string>;
    policyTypes: string[];
    ingress?: Array<{
      from: Array<{ podSelector?: Record<string, string> }>;
      ports?: Array<{ port: number; protocol: string }>;
    }>;
    egress?: Array<{
      to: Array<{ podSelector?: Record<string, string> }>;
      ports?: Array<{ port: number; protocol: string }>;
    }>;
  };
}

/**
 * Generate tenant-specific network policy
 */
function generateTenantNetworkPolicy(tenantId: string): NetworkPolicy {
  return {
    metadata: {
      name: `tenant-${tenantId}-network-policy`,
      namespace: 'travel-agency',
      labels: {
        tenant: tenantId,
        app: 'travel-agency'
      }
    },
    spec: {
      podSelector: {
        tenant: tenantId
      },
      policyTypes: ['Ingress', 'Egress'],
      ingress: [
        {
          from: [
            { podSelector: { tenant: tenantId } }  // Allow same-tenant traffic
          ],
          ports: [
            { port: 3000, protocol: 'TCP' },
            { port: 8080, protocol: 'TCP' }
          ]
        },
        {
          from: [],  // Allow from ingress controller
          ports: [
            { port: 3000, protocol: 'TCP' }
          ]
        }
      ],
      egress: [
        {
          to: [{ podSelector: { tenant: tenantId } }],
          ports: [
            { port: 5432, protocol: 'TCP' }  // Database
          ]
        },
        {
          to: [],  // Allow external egress
          ports: [
            { port: 443, protocol: 'TCP' }  // HTTPS
          ]
        }
      ]
    }
  };
}
```

---

## Encryption Per Tenant

### Tenant-Specific Encryption Keys

```typescript
/**
 * Encryption key per tenant
 */
interface TenantEncryptionKey {
  tenantId: string;
  keyId: string;
  encryptedKey: string;    // Key encrypted with master key
  algorithm: string;
  createdAt: Date;
  rotatedAt?: Date;
}

/**
 * Tenant encryption service
 */
class TenantEncryptionService {
  private kms: KMSClient;
  private cache: Map<string, string>; // tenantId -> decrypted key

  constructor() {
    this.kms = new KMSClient();
    this.cache = new Map();
  }

  /**
   * Generate encryption key for tenant
   */
  async generateKey(tenantId: string): Promise<TenantEncryptionKey> {
    // Generate random key
    const key = crypto.randomBytes(32); // 256-bit

    // Encrypt with master key
    const encryptedKey = await this.kms.encrypt({
      KeyId: process.env.MASTER_KEY_ID,
      Plaintext: key
    });

    const keyRecord: TenantEncryptionKey = {
      tenantId,
      keyId: generateId(),
      encryptedKey: Buffer.from(encryptedKey.CiphertextBlob).toString('base64'),
      algorithm: 'AES-256-GCM',
      createdAt: new Date()
    };

    await db.insert(tenantEncryptionKeys).values(keyRecord);

    // Cache decrypted key
    this.cache.set(tenantId, key.toString('base64'));

    return keyRecord;
  }

  /**
   * Get decrypted key for tenant
   */
  async getKey(tenantId: string): Promise<string> {
    // Check cache first
    const cached = this.cache.get(tenantId);
    if (cached) {
      return cached;
    }

    // Fetch from database
    const keyRecord = await db.query.tenantEncryptionKeys.findFirst({
      where: eq(tenantEncryptionKeys.tenantId, tenantId)
    });

    if (!keyRecord) {
      throw new Error('No encryption key found for tenant');
    }

    // Decrypt key
    const decrypted = await this.kms.decrypt({
      CiphertextBlob: Buffer.from(keyRecord.encryptedKey, 'base64')
    });

    const key = Buffer.from(decrypted.Plaintext as Uint8Array).toString('base64');
    this.cache.set(tenantId, key);

    return key;
  }

  /**
   * Encrypt data for tenant
   */
  async encrypt(tenantId: string, plaintext: string): Promise<{
    ciphertext: string;
    nonce: string;
    keyId: string;
  }> {
    const key = await this.getKey(tenantId);
    const nonce = crypto.randomBytes(12);

    const cipher = crypto.createCipheriv(
      'aes-256-gcm',
      Buffer.from(key, 'base64'),
      nonce
    );

    let ciphertext = cipher.update(plaintext, 'utf8', 'base64');
    ciphertext += cipher.final('base64');

    const authTag = cipher.getAuthTag();

    return {
      ciphertext: ciphertext + '.' + authTag.toString('base64'),
      nonce: nonce.toString('base64'),
      keyId: await this.getKeyId(tenantId)
    };
  }

  /**
   * Decrypt data for tenant
   */
  async decrypt(tenantId: string, data: {
    ciphertext: string;
    nonce: string;
  }): Promise<string> {
    const key = await this.getKey(tenantId);
    const nonce = Buffer.from(data.nonce, 'base64');

    const [ciphertext, authTag] = data.ciphertext.split('.');

    const decipher = crypto.createDecipheriv(
      'aes-256-gcm',
      Buffer.from(key, 'base64'),
      nonce
    );

    decipher.setAuthTag(Buffer.from(authTag, 'base64'));

    let plaintext = decipher.update(ciphertext, 'base64', 'utf8');
    plaintext += decipher.final('utf8');

    return plaintext;
  }

  /**
   * Rotate encryption key for tenant
   */
  async rotateKey(tenantId: string): Promise<void> {
    const oldKey = await this.getKey(tenantId);

    // Generate new key
    await this.generateKey(tenantId);

    // Re-encrypt all sensitive data with new key
    await this.reencryptTenantData(tenantId, oldKey);
  }

  private async reencryptTenantData(tenantId: string, oldKey: string): Promise<void> {
    // Find all encrypted data for tenant
    const encryptedData = await db.query.encryptedData.findMany({
      where: eq(encryptedData.tenantId, tenantId)
    });

    for (const data of encryptedData) {
      // Decrypt with old key
      const plaintext = await this.decryptWithKey(oldKey, {
        ciphertext: data.ciphertext,
        nonce: data.nonce
      });

      // Encrypt with new key
      const encrypted = await this.encrypt(tenantId, plaintext);

      // Update record
      await db.update(encryptedData)
        .set({
          ciphertext: encrypted.ciphertext,
          nonce: encrypted.nonce,
          keyId: encrypted.keyId
        })
        .where(eq(encryptedData.id, data.id));
    }
  }

  private async getKeyId(tenantId: string): Promise<string> {
    const keyRecord = await db.query.tenantEncryptionKeys.findFirst({
      where: eq(tenantEncryptionKeys.tenantId, tenantId)
    });
    return keyRecord?.keyId || '';
  }

  private async decryptWithKey(
    key: string,
    data: { ciphertext: string; nonce: string }
  ): Promise<string> {
    const nonce = Buffer.from(data.nonce, 'base64');
    const [ciphertext, authTag] = data.ciphertext.split('.');

    const decipher = crypto.createDecipheriv(
      'aes-256-gcm',
      Buffer.from(key, 'base64'),
      nonce
    );

    decipher.setAuthTag(Buffer.from(authTag, 'base64'));

    let plaintext = decipher.update(ciphertext, 'base64', 'utf8');
    plaintext += decipher.final('utf8');

    return plaintext;
  }
}
```

---

## Audit Logging

### Tenant Audit Log

```typescript
/**
 * Audit log entry
 */
interface AuditLogEntry {
  id: string;
  tenantId: string;
  userId?: string;
  action: string;
  resource: string;
  resourceId?: string;
  details: Record<string, unknown>;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

/**
 * Audit logger
 */
class TenantAuditLogger {
  /**
   * Log action for tenant
   */
  async log(entry: Omit<AuditLogEntry, 'id' | 'timestamp'>): Promise<void> {
    const logEntry: AuditLogEntry = {
      id: generateId(),
      timestamp: new Date(),
      ...entry
    };

    await db.insert(auditLogs).values(logEntry);

    // Also send to external logging service
    await this.sendToExternalLog(logEntry);
  }

  /**
   * Query audit logs for tenant
   */
  async query(
    tenantId: string,
    filters: {
      startDate?: Date;
      endDate?: Date;
      action?: string;
      resource?: string;
      userId?: string;
      severity?: AuditLogEntry['severity'];
    } = {}
  ): Promise<AuditLogEntry[]> {
    const conditions = [eq(auditLogs.tenantId, tenantId)];

    if (filters.startDate) {
      conditions.push(gte(auditLogs.timestamp, filters.startDate));
    }
    if (filters.endDate) {
      conditions.push(lte(auditLogs.timestamp, filters.endDate));
    }
    if (filters.action) {
      conditions.push(eq(auditLogs.action, filters.action));
    }
    if (filters.resource) {
      conditions.push(eq(auditLogs.resource, filters.resource));
    }
    if (filters.userId) {
      conditions.push(eq(auditLogs.userId, filters.userId));
    }
    if (filters.severity) {
      conditions.push(eq(auditLogs.severity, filters.severity));
    }

    return db.query.auditLogs.findMany({
      where: and(...conditions),
      orderBy: [desc(auditLogs.timestamp)],
      limit: 1000
    });
  }

  /**
   * Get compliance report for tenant
   */
  async getComplianceReport(
    tenantId: string,
    startDate: Date,
    endDate: Date
  ): Promise<{
    totalActions: number;
    actionsByType: Record<string, number>;
    actionsByUser: Record<string, number>;
    failedActions: number;
    criticalEvents: AuditLogEntry[];
  }> {
    const logs = await this.query(tenantId, { startDate, endDate });

    const actionsByType: Record<string, number> = {};
    const actionsByUser: Record<string, number> = {};
    let failedActions = 0;
    const criticalEvents: AuditLogEntry[] = [];

    for (const log of logs) {
      actionsByType[log.action] = (actionsByType[log.action] || 0) + 1;

      if (log.userId) {
        actionsByUser[log.userId] = (actionsByUser[log.userId] || 0) + 1;
      }

      if (log.severity === 'error' || log.severity === 'critical') {
        failedActions++;
      }

      if (log.severity === 'critical') {
        criticalEvents.push(log);
      }
    }

    return {
      totalActions: logs.length,
      actionsByType,
      actionsByUser,
      failedActions,
      criticalEvents
    };
  }

  private async sendToExternalLog(entry: AuditLogEntry): Promise<void> {
    // Send to SIEM, logging service, etc.
    // Implementation depends on external service
  }
}
```

---

## Leakage Prevention

### Log Scrubbing

```typescript
/**
 * Log scrubber - removes sensitive data
 */
class LogScrubber {
  private patterns: Array<{
    pattern: RegExp;
    replacement: string;
    description: string;
  }>;

  constructor() {
    this.patterns = [
      {
        pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
        replacement: '***@***.***',
        description: 'Email addresses'
      },
      {
        pattern: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g,
        replacement: '****-****-****-****',
        description: 'Credit card numbers'
      },
      {
        pattern: /\b\d{3}-\d{2}-\d{4}\b/g,
        replacement: '***-**-****',
        description: 'SSN'
      },
      {
        pattern: /Bearer\s+[A-Za-z0-9\-._~+/]+=*/gi,
        replacement: 'Bearer ***',
        description: 'Bearer tokens'
      },
      {
        pattern: /api[_-]?key["']?\s*[:=]\s*["']?[A-Za-z0-9\-._~+/]+=*/gi,
        replacement: 'api_key: ***',
        description: 'API keys'
      },
      {
        pattern: /password["']?\s*[:=]\s*["']?.+?["']?(?=\s|,|}|$)/gi,
        replacement: 'password: ***',
        description: 'Passwords'
      }
    ];
  }

  /**
   * Scrub log message
   */
  scrub(message: string): string {
    let scrubbed = message;

    for (const { pattern, replacement } of this.patterns) {
      scrubbed = scrubbed.replace(pattern, replacement);
    }

    return scrubbed;
  }

  /**
   * Scrub object
   */
  scrubObject(obj: Record<string, unknown>): Record<string, unknown> {
    const scrubbed: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(obj)) {
      if (this.isSensitiveKey(key)) {
        scrubbed[key] = '***';
      } else if (typeof value === 'string') {
        scrubbed[key] = this.scrub(value);
      } else if (typeof value === 'object' && value !== null) {
        scrubbed[key] = this.scrubObject(value as Record<string, unknown>);
      } else {
        scrubbed[key] = value;
      }
    }

    return scrubbed;
  }

  private isSensitiveKey(key: string): boolean {
    const sensitiveKeys = [
      'password', 'secret', 'token', 'apiKey', 'api_key',
      'accessKey', 'access_key', 'secretKey', 'secret_key',
      'ssn', 'creditCard', 'cardNumber', 'cvv'
    ];

    return sensitiveKeys.some(sk =>
      key.toLowerCase().includes(sk.toLowerCase())
    );
  }
}
```

### Error Message Sanitization

```typescript
/**
 * Error message sanitizer
 */
class ErrorSanitizer {
  /**
   * Sanitize error for external display
   */
  sanitize(error: Error, tenantId?: string): {
    message: string;
    code: string;
    details?: Record<string, unknown>;
  } {
    // Log full error internally
    console.error('[Error]', {
      message: error.message,
      stack: error.stack,
      tenantId,
      timestamp: new Date().toISOString()
    });

    // Return generic message externally
    return {
      message: this.getGenericMessage(error),
      code: this.getErrorCode(error)
    };
  }

  private getGenericMessage(error: Error): string {
    // Don't leak internal details
    const errorMessages: Record<string, string> = {
      'PostgresError': 'Database error occurred',
      'ValidationError': 'Invalid input data',
      'AuthenticationError': 'Authentication failed',
      'AuthorizationError': 'Access denied',
      'NotFoundError': 'Resource not found',
      'RateLimitError': 'Too many requests',
      'QuotaError': 'Resource quota exceeded'
    };

    for (const [type, message] of Object.entries(errorMessages)) {
      if (error.name.includes(type)) {
        return message;
      }
    }

    return 'An error occurred';
  }

  private getErrorCode(error: Error): string {
    const errorCodes: Record<string, string> = {
      'PostgresError': 'DATABASE_ERROR',
      'ValidationError': 'INVALID_INPUT',
      'AuthenticationError': 'AUTH_FAILED',
      'AuthorizationError': 'ACCESS_DENIED',
      'NotFoundError': 'NOT_FOUND',
      'RateLimitError': 'RATE_LIMITED',
      'QuotaError': 'QUOTA_EXCEEDED'
    };

    for (const [type, code] of Object.entries(errorCodes)) {
      if (error.name.includes(type)) {
        return code;
      }
    }

    return 'INTERNAL_ERROR';
  }
}
```

---

## Implementation

### Complete Isolation Service

```typescript
/**
 * Complete tenant isolation service
 */
class TenantIsolationService {
  private rlsManager: RLSManager;
  private auditLogger: TenantAuditLogger;
  private encryptionService: TenantEncryptionService;
  private quotaManager: ResourceQuotaManager;
  private rateLimiter: TenantRateLimiter;
  private logScrubber: LogScrubber;
  private errorSanitizer: ErrorSanitizer;

  constructor() {
    this.rlsManager = new RLSManager();
    this.auditLogger = new TenantAuditLogger();
    this.encryptionService = new TenantEncryptionService();
    this.quotaManager = new ResourceQuotaManager();
    this.rateLimiter = new TenantRateLimiter();
    this.logScrubber = new LogScrubber();
    this.errorSanitizer = new ErrorSanitizer();
  }

  /**
   * Initialize isolation for request
   */
  async initializeRequest(
    request: Request,
    tenantId: string
  ): Promise<void> {
    // Set RLS context
    await this.rlsManager.setTenantContext(tenantId);

    // Check rate limit
    const rateLimitResult = await this.rateLimiter.checkLimit(tenantId);
    if (!rateLimitResult.allowed) {
      throw new Error('Rate limit exceeded');
    }

    // Log request
    await this.auditLogger.log({
      tenantId,
      action: 'request_received',
      resource: request.url,
      details: {
        method: request.method,
        headers: this.logScrubber.scrubObject(
          Object.fromEntries(request.headers)
        )
      },
      ipAddress: request.headers.get('x-forwarded-for') || 'unknown',
      userAgent: request.headers.get('user-agent') || 'unknown',
      severity: 'info'
    });
  }

  /**
   * Encrypt tenant-sensitive data
   */
  async encryptData(
    tenantId: string,
    data: string
  ): Promise<string> {
    const encrypted = await this.encryptionService.encrypt(tenantId, data);
    return JSON.stringify(encrypted);
  }

  /**
   * Decrypt tenant-sensitive data
   */
  async decryptData(
    tenantId: string,
    encryptedData: string
  ): Promise<string> {
    const data = JSON.parse(encryptedData);
    return this.encryptionService.decrypt(tenantId, data);
  }

  /**
   * Check resource quota
   */
  async checkQuota(
    tenantId: string,
    resource: keyof ResourceUsage,
    amount = 1
  ): Promise<boolean> {
    return this.quotaManager.canConsume(tenantId, resource);
  }

  /**
   * Handle error with isolation
   */
  async handleError(
    error: Error,
    tenantId: string,
    context: Record<string, unknown>
  ): Promise<{
    message: string;
    code: string;
  }> {
    // Log error
    await this.auditLogger.log({
      tenantId,
      action: 'error',
      resource: context.resource as string || 'unknown',
      details: {
        error: error.message,
        context: this.logScrubber.scrubObject(context)
      },
      ipAddress: context.ipAddress as string || 'unknown',
      userAgent: context.userAgent as string || 'unknown',
      severity: 'error'
    });

    // Return sanitized error
    return this.errorSanitizer.sanitize(error, tenantId);
  }
}
```

---

## Testing Scenarios

### Isolation Tests

```typescript
describe('Tenant Isolation', () => {
  describe('Data Isolation', () => {
    it('should prevent cross-tenant data access', async () => {
      const tenant1Id = 'tenant-1';
      const tenant2Id = 'tenant-2';

      // Create customer for tenant 1
      const repo1 = new CustomerRepository(tenant1Id);
      await repo1.create({
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@tenant1.com'
      });

      // Try to access from tenant 2
      const repo2 = new CustomerRepository(tenant2Id);
      const customers = await repo2.findMany({});

      expect(customers).toHaveLength(0);
    });

    it('should enforce foreign key tenant validation', async () => {
      const tenant1Id = 'tenant-1';
      const tenant2Id = 'tenant-2';

      // Create customer for tenant 1
      const customer = await new CustomerRepository(tenant1Id).create({
        firstName: 'Jane',
        lastName: 'Smith',
        email: 'jane@tenant1.com'
      });

      // Try to create trip for tenant 2 referencing tenant 1's customer
      const tripRepo = new TenantAwareRepository<Trip>(tenant2Id, 'trips');

      await expect(
        tripRepo.create({
          customerId: customer.id,
          destination: 'Paris',
          status: 'draft'
        } as any)
      ).rejects.toThrow('Foreign key violation');
    });
  });

  describe('RLS Isolation', () => {
    it('should enforce RLS policies', async () => {
      const rlsManager = new RLSManager();
      const tenant1Id = 'tenant-1';
      const tenant2Id = 'tenant-2';

      // Create test record
      await db.execute(`
        INSERT INTO customers (id, tenant_id, email)
        VALUES ('test-customer', '${tenant1Id}', 'test@test.com');
      `);

      // Try to access from tenant 2
      await rlsManager.setTenantContext(tenant2Id);
      const result = await db.execute(`
        SELECT * FROM customers WHERE id = 'test-customer';
      `);

      expect(result.rowCount).toBe(0);

      // Clean up
      await rlsManager.clearTenantContext();
      await db.execute(`DELETE FROM customers WHERE id = 'test-customer';`);
    });
  });

  describe('Encryption Isolation', () => {
    it('should not decrypt with different tenant key', async () => {
      const encryptionService = new TenantEncryptionService();

      await encryptionService.generateKey('tenant-1');
      await encryptionService.generateKey('tenant-2');

      const encrypted = await encryptionService.encrypt('tenant-1', 'sensitive data');

      await expect(
        encryptionService.decrypt('tenant-2', JSON.parse(encrypted))
      ).rejects.toThrow();
    });
  });

  describe('Quota Isolation', () => {
    it('should enforce tenant quotas', async () => {
      const quotaManager = new ResourceQuotaManager();

      quotaManager.setQuota('tenant-1', {
        maxCpuPercent: 80,
        maxMemoryMB: 1024,
        maxConnections: 10,
        maxRequestsPerMinute: 100,
        maxStorageGB: 10,
        maxConcurrentJobs: 5
      });

      const canConsume1 = await quotaManager.canConsume('tenant-1', 'connections');
      const canConsume2 = await quotaManager.canConsume('tenant-2', 'connections');

      expect(canConsume1).toBe(true);
      expect(canConsume2).toBe(true); // No quota set = unlimited
    });
  });
});
```

---

## API Specification

### Isolation Management API

```yaml
openapi: 3.0.0
info:
  title: Travel Agency Agent - Isolation API
  version: 1.0.0

paths:
  /api/v1/tenants/{tenantId}/isolation/status:
    get:
      summary: Get tenant isolation status
      parameters:
        - name: tenantId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Isolation status
          content:
            application/json:
              schema:
                type: object
                properties:
                  rlsEnabled:
                    type: boolean
                  encryptionEnabled:
                    type: boolean
                  quotas:
                    type: object
                  rateLimits:
                    type: object

  /api/v1/tenants/{tenantId}/audit-logs:
    get:
      summary: Get tenant audit logs
      parameters:
        - name: tenantId
          in: path
          required: true
          schema:
            type: string
        - name: startDate
          in: query
          schema:
            type: string
            format: date-time
        - name: endDate
          in: query
          schema:
            type: string
            format: date-time
        - name: action
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Audit logs
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AuditLogEntry'

  /api/v1/tenants/{tenantId}/encryption/rotate:
    post:
      summary: Rotate tenant encryption key
      parameters:
        - name: tenantId
          in: path
          required: true
          schema:
            type: string
      responses:
        '202':
          description: Key rotation initiated

components:
  schemas:
    AuditLogEntry:
      type: object
      properties:
        id:
          type: string
        tenantId:
          type: string
        userId:
          type: string
        action:
          type: string
        resource:
          type: string
        resourceId:
          type: string
        details:
          type: object
        ipAddress:
          type: string
        userAgent:
          type: string
        timestamp:
          type: string
          format: date-time
        severity:
          type: string
          enum: [info, warning, error, critical]
```

---

## Metrics and Monitoring

### Isolation Metrics

```typescript
/**
 * Isolation metrics collector
 */
interface IsolationMetrics {
  // Data isolation
  crossTenantAccessAttempts: number;
  rlsViolationCount: number;
  foreignKeyViolationCount: number;

  // Resource isolation
  quotaExceededCount: number;
  rateLimitExceededCount: number;
  storageQuotaExceededCount: number;

  // Encryption
  encryptionOperations: number;
  decryptionOperations: number;
  keyRotations: number;

  // Audit
  auditLogEntries: number;
  criticalEvents: number;

  // Performance
  averageQueryTime: number;
  slowQueriesCount: number;
}

class IsolationMetricsCollector {
  async collectMetrics(tenantId?: string): Promise<IsolationMetrics> {
    const tenantFilter = tenantId
      ? `WHERE tenant_id = '${tenantId}'`
      : '';

    const [
      crossTenantAttempts,
      rlsViolations,
      fkViolations,
      quotaExceeded,
      rateLimitExceeded,
      storageExceeded
    ] = await Promise.all([
      this.getCrossTenantAccessAttempts(tenantFilter),
      this.getRLSViolations(tenantFilter),
      this.getForeignKeyViolations(tenantFilter),
      this.getQuotaExceededCount(tenantFilter),
      this.getRateLimitExceededCount(tenantFilter),
      this.getStorageExceededCount(tenantFilter)
    ]);

    return {
      crossTenantAccessAttempts: crossTenantAttempts,
      rlsViolationCount: rlsViolations,
      foreignKeyViolationCount: fkViolations,
      quotaExceededCount: quotaExceeded,
      rateLimitExceededCount: rateLimitExceeded,
      storageQuotaExceededCount: storageExceeded,
      encryptionOperations: 0,
      decryptionOperations: 0,
      keyRotations: 0,
      auditLogEntries: 0,
      criticalEvents: 0,
      averageQueryTime: 0,
      slowQueriesCount: 0
    };
  }

  private async getCrossTenantAccessAttempts(filter: string): Promise<number> {
    const result = await db.execute(`
      SELECT COUNT(*) as count
      FROM audit_logs
      WHERE action = 'cross_tenant_access_attempt'
      ${filter.replace('WHERE', 'AND')};
    `);
    return parseInt(result.rows[0]?.count || '0');
  }

  private async getRLSViolations(filter: string): Promise<number> {
    // This would be tracked separately
    return 0;
  }

  private async getForeignKeyViolations(filter: string): Promise<number> {
    const result = await db.execute(`
      SELECT COUNT(*) as count
      FROM audit_logs
      WHERE action = 'foreign_key_violation'
      ${filter.replace('WHERE', 'AND')};
    `);
    return parseInt(result.rows[0]?.count || '0');
  }

  private async getQuotaExceededCount(filter: string): Promise<number> {
    const result = await db.execute(`
      SELECT COUNT(*) as count
      FROM audit_logs
      WHERE action = 'quota_exceeded'
      ${filter.replace('WHERE', 'AND')};
    `);
    return parseInt(result.rows[0]?.count || '0');
  }

  private async getRateLimitExceededCount(filter: string): Promise<number> {
    const result = await db.execute(`
      SELECT COUNT(*) as count
      FROM audit_logs
      WHERE action = 'rate_limit_exceeded'
      ${filter.replace('WHERE', 'AND')};
    `);
    return parseInt(result.rows[0]?.count || '0');
  }

  private async getStorageExceededCount(filter: string): Promise<number> {
    const result = await db.execute(`
      SELECT COUNT(*) as count
      FROM audit_logs
      WHERE action = 'storage_quota_exceeded'
      ${filter.replace('WHERE', 'AND')};
    `);
    return parseInt(result.rows[0]?.count || '0');
  }
}
```

---

**End of Document**

**Next:** [Tenant Onboarding Deep Dive](MULTI_TENANCY_03_ONBOARDING.md)
