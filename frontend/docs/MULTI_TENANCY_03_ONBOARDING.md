# Tenant Onboarding — Technical Deep Dive

> Comprehensive guide to tenant provisioning and onboarding for the Travel Agency Agent platform

---

## Document Metadata

**Series:** Multi-tenancy Patterns
**Document:** 3 of 4 (Onboarding)
**Last Updated:** 2026-04-26
**Status:** ✅ Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Provisioning Workflows](#provisioning-workflows)
3. [Database Schema Provisioning](#database-schema-provisioning)
4. [Configuration Initialization](#configuration-initialization)
5. [User Account Creation](#user-account-creation)
6. [Branding Customization](#branding-customization)
7. [Domain Mapping](#domain-mapping)
8. [SSL Certificate Management](#ssl-certificate-management)
9. [Data Migration](#data-migration)
10. [Implementation](#implementation)
11. [Testing Scenarios](#testing-scenarios)
12. [API Specification](#api-specification)
13. [Metrics and Monitoring](#metrics-and-monitoring)

---

## Overview

Tenant onboarding is the process of creating and configuring a new tenant's environment. This includes provisioning infrastructure, initializing configuration, creating user accounts, and setting up branding.

### Onboarding Stages

1. **Validation** - Verify input data and availability
2. **Provisioning** - Create infrastructure resources
3. **Configuration** - Apply tenant-specific settings
4. **Users** - Create admin user account
5. **Branding** - Set up visual identity
6. **Domain** - Configure custom domain (optional)
7. **Verification** - Test tenant setup
8. **Notification** - Send welcome email

### Success Criteria

- Tenant can log in within 5 minutes
- All data properly isolated
- Branding correctly applied
- Domain accessible (if configured)
- No impact on existing tenants

---

## Provisioning Workflows

### Onboarding State Machine

```typescript
/**
 * Tenant onboarding states
 */
enum OnboardingState {
  VALIDATING = 'validating',
  PROVISIONING = 'provisioning',
  CONFIGURING = 'configuring',
  BRAND_SETUP = 'brand_setup',
  DOMAIN_SETUP = 'domain_setup',
  VERIFYING = 'verifying',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ROLLBACK = 'rollback'
}

/**
 * Onboarding workflow definition
 */
interface OnboardingWorkflow {
  tenantId: string;
  state: OnboardingState;
  steps: OnboardingStep[];
  currentStep: number;
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

interface OnboardingStep {
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
  retryCount: number;
}
```

### Provisioning Orchestrator

```typescript
/**
 * Tenant provisioning orchestrator
 */
class TenantProvisioningOrchestrator {
  private workflows: Map<string, OnboardingWorkflow>;

  constructor() {
    this.workflows = new Map();
  }

  /**
   * Start provisioning for new tenant
   */
  async startProvisioning(input: TenantProvisioningInput): Promise<string> {
    const workflowId = generateId();

    // Validate input
    await this.validateInput(input);

    // Create workflow
    const workflow: OnboardingWorkflow = {
      tenantId: input.tenantId,
      state: OnboardingState.VALIDATING,
      steps: this.getProvisioningSteps(),
      currentStep: 0,
      startedAt: new Date()
    };

    this.workflows.set(workflowId, workflow);

    // Start provisioning asynchronously
    this.executeWorkflow(workflowId).catch(error => {
      console.error('Provisioning workflow failed:', error);
    });

    return workflowId;
  }

  /**
   * Execute provisioning workflow
   */
  private async executeWorkflow(workflowId: string): Promise<void> {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) throw new Error('Workflow not found');

    try {
      for (let i = 0; i < workflow.steps.length; i++) {
        workflow.currentStep = i;
        const step = workflow.steps[i];

        step.status = 'in_progress';
        step.startedAt = new Date();

        try {
          await this.executeStep(workflow.tenantId, step.name);
          step.status = 'completed';
          step.completedAt = new Date();
        } catch (error) {
          step.status = 'failed';
          step.error = error instanceof Error ? error.message : 'Unknown error';
          step.retryCount++;

          if (step.retryCount < 3) {
            // Retry step
            step.status = 'pending';
            i--; // Retry same step
            await this.sleep(5000 * step.retryCount); // Exponential backoff
          } else {
            // Max retries exceeded, initiate rollback
            workflow.state = OnboardingState.FAILED;
            await this.rollback(workflowId);
            return;
          }
        }
      }

      workflow.state = OnboardingState.COMPLETED;
      workflow.completedAt = new Date();

    } catch (error) {
      workflow.state = OnboardingState.FAILED;
      workflow.error = error instanceof Error ? error.message : 'Unknown error';
      await this.rollback(workflowId);
    }
  }

  /**
   * Execute individual provisioning step
   */
  private async executeStep(tenantId: string, stepName: string): Promise<void> {
    const stepHandlers: Record<string, () => Promise<void>> = {
      'validate_subdomain': () => this.validateSubdomain(tenantId),
      'create_tenant_record': () => this.createTenantRecord(tenantId),
      'provision_database': () => this.provisionDatabase(tenantId),
      'apply_configuration': () => this.applyConfiguration(tenantId),
      'create_admin_user': () => this.createAdminUser(tenantId),
      'setup_branding': () => this.setupBranding(tenantId),
      'configure_domain': () => this.configureDomain(tenantId),
      'provision_ssl': () => this.provisionSSL(tenantId),
      'seed_data': () => this.seedData(tenantId),
      'verify_setup': () => this.verifySetup(tenantId),
      'send_welcome_email': () => this.sendWelcomeEmail(tenantId)
    };

    const handler = stepHandlers[stepName];
    if (!handler) {
      throw new Error(`Unknown step: ${stepName}`);
    }

    await handler();
  }

  /**
   * Rollback failed provisioning
   */
  private async rollback(workflowId: string): Promise<void> {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) return;

    workflow.state = OnboardingState.ROLLBACK;

    // Rollback in reverse order
    for (let i = workflow.currentStep; i >= 0; i--) {
      const step = workflow.steps[i];
      if (step.status === 'completed') {
        try {
          await this.rollbackStep(workflow.tenantId, step.name);
          step.status = 'pending';
        } catch (error) {
          console.error(`Rollback failed for step ${step.name}:`, error);
        }
      }
    }

    // Mark tenant as failed
    await db.update(tenants)
      .set({ status: 'provisioning_failed' })
      .where(eq(tenants.id, workflow.tenantId));
  }

  /**
   * Get provisioning steps
   */
  private getProvisioningSteps(): OnboardingStep[] {
    return [
      { name: 'validate_subdomain', status: 'pending', retryCount: 0 },
      { name: 'create_tenant_record', status: 'pending', retryCount: 0 },
      { name: 'provision_database', status: 'pending', retryCount: 0 },
      { name: 'apply_configuration', status: 'pending', retryCount: 0 },
      { name: 'create_admin_user', status: 'pending', retryCount: 0 },
      { name: 'setup_branding', status: 'pending', retryCount: 0 },
      { name: 'configure_domain', status: 'pending', retryCount: 0 }, // Optional
      { name: 'provision_ssl', status: 'pending', retryCount: 0 },     // Optional
      { name: 'seed_data', status: 'pending', retryCount: 0 },
      { name: 'verify_setup', status: 'pending', retryCount: 0 },
      { name: 'send_welcome_email', status: 'pending', retryCount: 0 }
    ];
  }

  private async validateInput(input: TenantProvisioningInput): Promise<void> {
    // Validate subdomain format
    if (!/^[a-z0-9-]+$/.test(input.subdomain)) {
      throw new Error('Subdomain must contain only lowercase letters, numbers, and hyphens');
    }

    // Validate email
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.adminEmail)) {
      throw new Error('Invalid email address');
    }

    // Check subdomain availability
    const existing = await db.query.tenants.findFirst({
      where: eq(tenants.subdomain, input.subdomain.toLowerCase())
    });

    if (existing) {
      throw new Error('Subdomain already taken');
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Step implementations (detailed in subsequent sections)
  private async validateSubdomain(tenantId: string): Promise<void> { /* ... */ }
  private async createTenantRecord(tenantId: string): Promise<void> { /* ... */ }
  private async provisionDatabase(tenantId: string): Promise<void> { /* ... */ }
  private async applyConfiguration(tenantId: string): Promise<void> { /* ... */ }
  private async createAdminUser(tenantId: string): Promise<void> { /* ... */ }
  private async setupBranding(tenantId: string): Promise<void> { /* ... */ }
  private async configureDomain(tenantId: string): Promise<void> { /* ... */ }
  private async provisionSSL(tenantId: string): Promise<void> { /* ... */ }
  private async seedData(tenantId: string): Promise<void> { /* ... */ }
  private async verifySetup(tenantId: string): Promise<void> { /* ... */ }
  private async sendWelcomeEmail(tenantId: string): Promise<void> { /* ... */ }

  private async rollbackStep(tenantId: string, stepName: string): Promise<void> {
    // Rollback implementation
  }

  /**
   * Get workflow status
   */
  getWorkflowStatus(workflowId: string): OnboardingWorkflow | undefined {
    return this.workflows.get(workflowId);
  }
}

interface TenantProvisioningInput {
  tenantId: string;
  name: string;
  subdomain: string;
  tier: TenantTier;
  adminEmail: string;
  adminName: string;
  customDomain?: string;
  branding?: {
    logo?: string;
    primaryColor?: string;
  };
}
```

---

## Database Schema Provisioning

### Schema Creation

```typescript
/**
 * Database schema provisioner
 */
class DatabaseSchemaProvisioner {
  /**
   * Create schema for tenant
   */
  async createTenantSchema(tenantId: string, tier: TenantTier): Promise<void> {
    const config = tierConfigs[tier];

    switch (config.multiTenancyModel) {
      case MultiTenancyModel.SCHEMA_PER_TENANT:
        await this.createDedicatedSchema(tenantId);
        break;

      case MultiTenancyModel.DATABASE_PER_TENANT:
        await this.createDedicatedDatabase(tenantId);
        break;

      case MultiTenancyModel.SHARED_SCHEMA:
        // No special schema needed
        break;
    }
  }

  /**
   * Create dedicated schema for tenant
   */
  private async createDedicatedSchema(tenantId: string): Promise<void> {
    const schemaName = `tenant_${tenantId.replace(/-/g, '_')}`;

    await db.transaction(async (tx) => {
      // Create schema
      await tx.execute(`CREATE SCHEMA IF NOT EXISTS ${schemaName};`);

      // Create tables in schema
      await this.createTables(tx, schemaName);

      // Enable RLS
      await this.enableRLS(tx, schemaName);

      // Grant permissions
      await this.grantPermissions(tx, schemaName);
    });
  }

  /**
   * Create tables in tenant schema
   */
  private async createTables(tx: any, schemaName: string): Promise<void> {
    const tables = [
      {
        name: 'customers',
        definition: `
          CREATE TABLE ${schemaName}.customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL DEFAULT '${schemaName.replace('tenant_', '').replace(/_/g, '-')}',
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            phone VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
          );
        `
      },
      {
        name: 'trips',
        definition: `
          CREATE TABLE ${schemaName}.trips (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            customer_id UUID NOT NULL REFERENCES ${schemaName}.customers(id),
            status VARCHAR(50) NOT NULL,
            destination VARCHAR(255) NOT NULL,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
          );
        `
      },
      // ... other tables
    ];

    for (const table of tables) {
      await tx.execute(table.definition);
    }
  }

  /**
   * Enable Row-Level Security
   */
  private async enableRLS(tx: any, schemaName: string): Promise<void> {
    const tables = ['customers', 'trips', 'bookings', 'quotes'];

    for (const table of tables) {
      await tx.execute(`ALTER TABLE ${schemaName}.${table} ENABLE ROW LEVEL SECURITY;`);

      await tx.execute(`
        CREATE POLICY ${table}_tenant_isolation ON ${schemaName}.${table}
        FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
      `);
    }
  }

  /**
   * Grant permissions to application user
   */
  private async grantPermissions(tx: any, schemaName: string): Promise<void> {
    const appUser = process.env.DB_USER || 'app_user';

    await tx.execute(`GRANT USAGE ON SCHEMA ${schemaName} TO ${appUser};`);
    await tx.execute(`GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ${schemaName} TO ${appUser};`);
    await tx.execute(`ALTER DEFAULT PRIVILEGES IN SCHEMA ${schemaName} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${appUser};`);
  }

  /**
   * Create dedicated database for tenant
   */
  private async createDedicatedDatabase(tenantId: string): Promise<void> {
    const dbName = `tenant_${tenantId.replace(/-/g, '_')}`;

    await db.transaction(async (tx) => {
      // Create database
      await tx.execute(`CREATE DATABASE ${dbName};`);

      // Connect to new database and create schema
      await tx.execute(`
        \c ${dbName};

        -- Run full schema migration
        -- This would use your migration tool
      `);
    });
  }

  /**
   * Drop tenant schema/database
   */
  async dropTenantSchema(tenantId: string, tier: TenantTier): Promise<void> {
    const config = tierConfigs[tier];

    switch (config.multiTenancyModel) {
      case MultiTenancyModel.SCHEMA_PER_TENANT:
        const schemaName = `tenant_${tenantId.replace(/-/g, '_')}`;
        await db.execute(`DROP SCHEMA IF EXISTS ${schemaName} CASCADE;`);
        break;

      case MultiTenancyModel.DATABASE_PER_TENANT:
        const dbName = `tenant_${tenantId.replace(/-/g, '_')}`;
        await db.execute(`DROP DATABASE IF EXISTS ${dbName};`);
        break;

      case MultiTenancyModel.SHARED_SCHEMA:
        // Just delete tenant's data
        await this.deleteTenantData(tenantId);
        break;
    }
  }

  /**
   * Delete all data for tenant from shared schema
   */
  private async deleteTenantData(tenantId: string): Promise<void> {
    const tables = ['customers', 'trips', 'bookings', 'quotes', 'suppliers', 'users'];

    for (const table of tables) {
      await db.execute(`DELETE FROM ${table} WHERE tenant_id = '${tenantId}';`);
    }
  }
}
```

### Data Seeding

```typescript
/**
 * Tenant data seeder
 */
class TenantDataSeeder {
  /**
   * Seed initial data for tenant
   */
  async seedTenantData(tenantId: string): Promise<void> {
    await db.transaction(async (tx) => {
      // Seed tags
      await this.seedTags(tenantId, tx);

      // Seed email templates
      await this.seedEmailTemplates(tenantId, tx);

      // Seed default suppliers
      await this.seedSuppliers(tenantId, tx);

      // Seed communication channels
      await this.seedCommunicationChannels(tenantId, tx);
    });
  }

  /**
   * Seed default tags
   */
  private async seedTags(tenantId: string, tx: any): Promise<void> {
    const defaultTags = [
      { name: 'Hot Lead', color: '#EF4444', icon: 'flame' },
      { name: 'Follow Up', color: '#F59E0B', icon: 'clock' },
      { name: 'Closed', color: '#10B981', icon: 'check' },
      { name: 'VIP', color: '#8B5CF6', icon: 'star' },
      { name: 'New Inquiry', color: '#3B82F6', icon: 'sparkles' }
    ];

    for (const tag of defaultTags) {
      await tx.insert(tags).values({
        id: generateId(),
        tenantId,
        ...tag,
        createdAt: new Date()
      });
    }
  }

  /**
   * Seed email templates
   */
  private async seedEmailTemplates(tenantId: string, tx: any): Promise<void> {
    const templates = [
      {
        name: 'Welcome Email',
        subject: 'Welcome to {{agency_name}}!',
        body: 'Dear {{customer_name}}, welcome to our travel agency...',
        type: 'welcome'
      },
      {
        name: 'Quote Ready',
        subject: 'Your travel quote is ready',
        body: 'Your quote for {{destination}} is ready to view...',
        type: 'quote'
      },
      {
        name: 'Booking Confirmation',
        subject: 'Booking Confirmed - {{reference}}',
        body: 'Your booking has been confirmed...',
        type: 'booking'
      }
    ];

    for (const template of templates) {
      await tx.insert(emailTemplates).values({
        id: generateId(),
        tenantId,
        ...template,
        createdAt: new Date()
      });
    }
  }

  /**
   * Seed default suppliers
   */
  private async seedSuppliers(tenantId: string, tx: any): Promise<void> {
    // Would typically come from a global supplier catalog
    const suppliers = [
      {
        name: 'Global Airlines',
        type: 'airline',
        code: 'GA'
      },
      {
        name: 'Hotel Partners Inc',
        type: 'hotel',
        code: 'HPI'
      }
    ];

    for (const supplier of suppliers) {
      await tx.insert(suppliers).values({
        id: generateId(),
        tenantId,
        ...supplier,
        createdAt: new Date()
      });
    }
  }

  /**
   * Seed communication channels
   */
  private async seedCommunicationChannels(tenantId: string, tx: any): Promise<void> {
    const channels = [
      { type: 'email', name: 'Email', enabled: true, default: true },
      { type: 'whatsapp', name: 'WhatsApp', enabled: false, default: false },
      { type: 'sms', name: 'SMS', enabled: false, default: false }
    ];

    for (const channel of channels) {
      await tx.insert(communicationChannels).values({
        id: generateId(),
        tenantId,
        ...channel,
        createdAt: new Date()
      });
    }
  }
}
```

---

## Configuration Initialization

### Configuration Template Application

```typescript
/**
 * Tenant configuration initializer
 */
class TenantConfigurationInitializer {
  /**
   * Initialize tenant configuration
   */
  async initializeConfiguration(
    tenantId: string,
    tier: TenantTier,
    options?: {
      branding?: Partial<BrandingConfig>;
      settings?: Partial<SettingsConfig>;
    }
  ): Promise<void> {
    const template = configurationTemplates[tier];
    const manager = new TenantConfigurationManager();

    // Apply base template
    for (const [key, config] of Object.entries(template.configs)) {
      await manager.set(tenantId, key, config.value, {
        type: config.type,
        category: config.category,
        isEncrypted: config.isEncrypted,
        isPublic: config.isPublic
      });
    }

    // Apply custom overrides
    if (options?.branding) {
      await this.applyBrandingConfig(tenantId, options.branding);
    }

    if (options?.settings) {
      await this.applySettingsConfig(tenantId, options.settings);
    }
  }

  /**
   * Apply branding configuration
   */
  private async applyBrandingConfig(
    tenantId: string,
    branding: Partial<BrandingConfig>
  ): Promise<void> {
    const manager = new TenantConfigurationManager();

    if (branding.name) {
      await manager.set(tenantId, 'branding.name', branding.name);
    }
    if (branding.logo) {
      await manager.set(tenantId, 'branding.logo', branding.logo);
    }
    if (branding.primaryColor) {
      await manager.set(tenantId, 'branding.primaryColor', branding.primaryColor);
    }
    if (branding.favicon) {
      await manager.set(tenantId, 'branding.favicon', branding.favicon);
    }
  }

  /**
   * Apply settings configuration
   */
  private async applySettingsConfig(
    tenantId: string,
    settings: Partial<SettingsConfig>
  ): Promise<void> {
    const manager = new TenantConfigurationManager();

    if (settings.timezone) {
      await manager.set(tenantId, 'settings.timezone', settings.timezone);
    }
    if (settings.currency) {
      await manager.set(tenantId, 'settings.currency', settings.currency);
    }
    if (settings.locale) {
      await manager.set(tenantId, 'settings.locale', settings.locale);
    }
  }
}

interface BrandingConfig {
  name: string;
  logo: string;
  primaryColor: string;
  favicon: string;
}

interface SettingsConfig {
  timezone: string;
  currency: string;
  locale: string;
  dateFormat: string;
}
```

---

## User Account Creation

### Admin User Provisioning

```typescript
/**
 * User provisioner for tenant
 */
class TenantUserProvisioner {
  /**
   * Create admin user for tenant
   */
  async createAdminUser(
    tenantId: string,
    input: {
      email: string;
      name: string;
      password?: string;
    }
  ): Promise<User> {
    // Generate temporary password if not provided
    const temporaryPassword = input.password ||
      this.generateTemporaryPassword();

    // Hash password
    const passwordHash = await hashPassword(temporaryPassword);

    // Create user
    const user = await db.insert(users).values({
      id: generateId(),
      tenantId,
      email: input.email,
      name: input.name,
      passwordHash,
      role: 'admin',
      isActive: true,
      mustChangePassword: !input.password, // Force change if temp password
      createdAt: new Date()
    }).returning().then(rows => rows[0]);

    // Create password reset token for first login
    if (!input.password) {
      await this.createPasswordResetToken(user.id);
    }

    // Send welcome email with temporary password
    await this.sendWelcomeEmail(user, temporaryPassword);

    return user;
  }

  /**
   * Create additional users for tenant
   */
  async createUser(
    tenantId: string,
    input: {
      email: string;
      name: string;
      role: 'admin' | 'agent' | 'viewer';
      sendInvite?: boolean;
    }
  ): Promise<User> {
    const inviteToken = this.generateInviteToken();

    const user = await db.insert(users).values({
      id: generateId(),
      tenantId,
      email: input.email,
      name: input.name,
      passwordHash: '', // No password until they accept invite
      role: input.role,
      isActive: false, // Inactive until invite accepted
      inviteToken,
      inviteExpiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      createdAt: new Date()
    }).returning().then(rows => rows[0]);

    if (input.sendInvite) {
      await this.sendInviteEmail(user);
    }

    return user;
  }

  /**
   * Generate temporary password
   */
  private generateTemporaryPassword(): string {
    const length = 16;
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    let password = '';

    for (let i = 0; i < length; i++) {
      password += charset.charAt(Math.floor(Math.random() * charset.length));
    }

    return password;
  }

  /**
   * Generate invite token
   */
  private generateInviteToken(): string {
    return crypto.randomBytes(32).toString('hex');
  }

  /**
   * Create password reset token
   */
  private async createPasswordResetToken(userId: string): Promise<void> {
    const token = crypto.randomBytes(32).toString('hex');

    await db.insert(passwordResetTokens).values({
      id: generateId(),
      userId,
      token,
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
      createdAt: new Date()
    });
  }

  /**
   * Send welcome email
   */
  private async sendWelcomeEmail(
    user: User,
    temporaryPassword: string
  ): Promise<void> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, user.tenantId)
    });

    const loginUrl = `https://${tenant.subdomain}.travelagent.com/login`;

    await emailService.send({
      to: user.email,
      subject: `Welcome to ${tenant.name}`,
      template: 'welcome',
      data: {
        userName: user.name,
        agencyName: tenant.name,
        temporaryPassword,
        loginUrl
      }
    });
  }

  /**
   * Send invite email
   */
  private async sendInviteEmail(user: User): Promise<void> {
    const tenant = await db.query.tenants.findFirst({
      where: eq(tenants.id, user.tenantId)
    });

    const inviteUrl = `https://${tenant.subdomain}.travelagent.com/accept-invite?token=${user.inviteToken}`;

    await emailService.send({
      to: user.email,
      subject: `Invitation to join ${tenant.name}`,
      template: 'invite',
      data: {
        userName: user.name,
        agencyName: tenant.name,
        inviteUrl,
        expiresAt: user.inviteExpiresAt
      }
    });
  }
}
```

---

## Branding Customization

### Branding Manager

```typescript
/**
 * Branding configuration
 */
interface BrandingAssets {
  logo?: {
    light: string;  // URL to light mode logo
    dark: string;   // URL to dark mode logo
    favicon: string;
  };
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  typography: {
    fontFamily: string;
    headingFont: string;
    bodyFont: string;
  };
  customCSS?: string;
}

/**
 * Branding manager
 */
class BrandingManager {
  private storage: AssetStorage;

  constructor() {
    this.storage = new AssetStorage();
  }

  /**
   * Apply branding to tenant
   */
  async applyBranding(
    tenantId: string,
    branding: Partial<BrandingAssets>
  ): Promise<void> {
    // Upload assets if provided
    if (branding.logo) {
      await this.uploadLogoAssets(tenantId, branding.logo);
    }

    // Save color scheme
    if (branding.colors) {
      await this.saveColorScheme(tenantId, branding.colors);
    }

    // Save typography
    if (branding.typography) {
      await this.saveTypography(tenantId, branding.typography);
    }

    // Save custom CSS
    if (branding.customCSS) {
      await this.saveCustomCSS(tenantId, branding.customCSS);
    }

    // Invalidate branding cache
    await this.invalidateCache(tenantId);
  }

  /**
   * Upload logo assets
   */
  private async uploadLogoAssets(
    tenantId: string,
    logo: { light?: string; dark?: string; favicon?: string }
  ): Promise<void> {
    const basePath = `tenants/${tenantId}/branding`;

    if (logo.light) {
      const lightUrl = await this.storage.upload(
        `${basePath}/logo-light.svg`,
        Buffer.from(log.light),
        { contentType: 'image/svg+xml' }
      );
      await this.saveBrandingConfig(tenantId, 'logo.light', lightUrl);
    }

    if (logo.dark) {
      const darkUrl = await this.storage.upload(
        `${basePath}/logo-dark.svg`,
        Buffer.from(logo.dark),
        { contentType: 'image/svg+xml' }
      );
      await this.saveBrandingConfig(tenantId, 'logo.dark', darkUrl);
    }

    if (logo.favicon) {
      const faviconUrl = await this.storage.upload(
        `${basePath}/favicon.ico`,
        Buffer.from(logo.favicon),
        { contentType: 'image/x-icon' }
      );
      await this.saveBrandingConfig(tenantId, 'logo.favicon', faviconUrl);
    }
  }

  /**
   * Save color scheme
   */
  private async saveColorScheme(
    tenantId: string,
    colors: BrandingAssets['colors']
  ): Promise<void> {
    const manager = new TenantConfigurationManager();

    await manager.set(tenantId, 'branding.colors.primary', colors.primary);
    await manager.set(tenantId, 'branding.colors.secondary', colors.secondary);
    await manager.set(tenantId, 'branding.colors.accent', colors.accent);
    await manager.set(tenantId, 'branding.colors.background', colors.background);
    await manager.set(tenantId, 'branding.colors.text', colors.text);
  }

  /**
   * Save typography
   */
  private async saveTypography(
    tenantId: string,
    typography: BrandingAssets['typography']
  ): Promise<void> {
    const manager = new TenantConfigurationManager();

    await manager.set(tenantId, 'branding.typography.fontFamily', typography.fontFamily);
    await manager.set(tenantId, 'branding.typography.headingFont', typography.headingFont);
    await manager.set(tenantId, 'branding.typography.bodyFont', typography.bodyFont);
  }

  /**
   * Save custom CSS
   */
  private async saveCustomCSS(
    tenantId: string,
    css: string
  ): Promise<void> {
    // Validate CSS
    if (!this.validateCSS(css)) {
      throw new Error('Invalid CSS');
    }

    // Minify CSS
    const minified = this.minifyCSS(css);

    // Save to storage
    const url = await this.storage.upload(
      `tenants/${tenantId}/branding/custom.css`,
      Buffer.from(minified),
      { contentType: 'text/css' }
    );

    const manager = new TenantConfigurationManager();
    await manager.set(tenantId, 'branding.customCSS', url);
  }

  /**
   * Get branding for tenant
   */
  async getBranding(tenantId: string): Promise<BrandingAssets> {
    const manager = new TenantConfigurationManager();

    const colors = {
      primary: await manager.get(tenantId, 'branding.colors.primary', '#3B82F6'),
      secondary: await manager.get(tenantId, 'branding.colors.secondary', '#6366F1'),
      accent: await manager.get(tenantId, 'branding.colors.accent', '#8B5CF6'),
      background: await manager.get(tenantId, 'branding.colors.background', '#FFFFFF'),
      text: await manager.get(tenantId, 'branding.colors.text', '#1F2937')
    };

    const typography = {
      fontFamily: await manager.get(tenantId, 'branding.typography.fontFamily', 'Inter'),
      headingFont: await manager.get(tenantId, 'branding.typography.headingFont', 'Inter'),
      bodyFont: await manager.get(tenantId, 'branding.typography.bodyFont', 'Inter')
    };

    const logo = {
      light: await manager.get(tenantId, 'branding.logo.light'),
      dark: await manager.get(tenantId, 'branding.logo.dark'),
      favicon: await manager.get(tenantId, 'branding.logo.favicon')
    };

    const customCSS = await manager.get(tenantId, 'branding.customCSS');

    return { colors, typography, logo, customCSS };
  }

  /**
   * Validate CSS
   */
  private validateCSS(css: string): boolean {
    // Basic validation - could use a proper CSS parser
    const forbiddenPatterns = [
      /javascript:/i,
      /<script/i,
      /expression\(/i,
      /@import/i
    ];

    return !forbiddenPatterns.some(pattern => pattern.test(css));
  }

  /**
   * Minify CSS
   */
  private minifyCSS(css: string): string {
    return css
      .replace(/\/\*[\s\S]*?\*\//g, '') // Remove comments
      .replace(/\s+/g, ' ')              // Collapse whitespace
      .replace(/\s*([\{\}\:\;])\s*/g, '$1') // Remove space around special chars
      .trim();
  }

  /**
   * Invalidate branding cache
   */
  private async invalidateCache(tenantId: string): Promise<void> {
    await cache.del(`branding:${tenantId}`);
  }

  private async saveBrandingConfig(
    tenantId: string,
    key: string,
    value: string
  ): Promise<void> {
    const manager = new TenantConfigurationManager();
    await manager.set(tenantId, `branding.${key}`, value, {
      isPublic: true
    });
  }
}
```

---

## Domain Mapping

### Custom Domain Configuration

```typescript
/**
 * Custom domain manager
 */
class CustomDomainManager {
  private dnsProvider: DNSProvider;
  private loadBalancer: LoadBalancerClient;

  constructor() {
    this.dnsProvider = new DNSProvider();
    this.loadBalancer = new LoadBalancerClient();
  }

  /**
   * Add custom domain to tenant
   */
  async addCustomDomain(
    tenantId: string,
    domain: string,
    options?: {
      autoConfigureSSL?: boolean;
      skipDNSCheck?: boolean;
    }
  ): Promise<TenantDomain> {
    // Normalize domain
    const normalizedDomain = domain.toLowerCase().replace(/^https?:\/\//, '');

    // Validate domain format
    if (!this.isValidDomain(normalizedDomain)) {
      throw new Error('Invalid domain format');
    }

    // Check domain availability
    const existing = await db.query.tenantDomains.findFirst({
      where: eq(tenantDomains.domain, normalizedDomain)
    });

    if (existing) {
      throw new Error('Domain already in use');
    }

    // Create domain record
    const tenantDomain = await db.insert(tenantDomains).values({
      id: generateId(),
      tenantId,
      domain: normalizedDomain,
      status: 'pending_verification',
      targetHost: `${tenantId}.travelagent.internal`,
      createdAt: new Date()
    }).returning().then(rows => rows[0]);

    // Configure DNS
    await this.configureDNS(normalizedDomain);

    // Configure load balancer
    await this.configureLoadBalancer(tenantId, normalizedDomain);

    // Verify DNS (unless skipped)
    if (!options?.skipDNSCheck) {
      await this.verifyDNS(tenantDomain.id);
    }

    // Provision SSL certificate
    if (options?.autoConfigureSSL !== false) {
      await this.provisionSSLCertificate(tenantDomain.id);
    }

    return tenantDomain;
  }

  /**
   * Configure DNS for domain
   */
  private async configureDNS(domain: string): Promise<void> {
    const targetHost = process.env.LOAD_BALANCER_HOST || 'lb.travelagent.com';
    const targetIp = process.env.LOAD_BALANCER_IP;

    // Create CNAME record
    await this.dnsProvider.createRecord({
      name: domain,
      type: 'CNAME',
      value: targetHost,
      ttl: 300
    });

    // Alternatively, create A record
    if (targetIp) {
      await this.dnsProvider.createRecord({
        name: domain,
        type: 'A',
        value: targetIp,
        ttl: 300
      });
    }
  }

  /**
   * Configure load balancer routing
   */
  private async configureLoadBalancer(
    tenantId: string,
    domain: string
  ): Promise<void> {
    await this.loadBalancer.addRule({
      priority: Math.floor(Math.random() * 10000),
      conditions: [
        { field: 'host-header', value: domain }
      ],
      actions: [
        {
          type: 'forward',
          config: {
            targetGroup: tenantId
          }
        }
      ]
    });
  }

  /**
   * Verify DNS configuration
   */
  private async verifyDNS(domainId: string): Promise<void> {
    const domain = await db.query.tenantDomains.findFirst({
      where: eq(tenantDomains.id, domainId)
    });

    if (!domain) throw new Error('Domain not found');

    const maxAttempts = 30;
    const delay = 10000; // 10 seconds

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const resolved = await dns.resolve(domain.domain);

        // Check if DNS points to our infrastructure
        const isValid = resolved.some(record =>
          record === process.env.LOAD_BALANCER_HOST ||
          record === process.env.LOAD_BALANCER_IP
        );

        if (isValid) {
          await db.update(tenantDomains)
            .set({
              status: 'verified',
              verifiedAt: new Date()
            })
            .where(eq(tenantDomains.id, domainId));

          return;
        }
      } catch (error) {
        // DNS not ready yet
      }

      await this.sleep(delay);
    }

    throw new Error('DNS verification timeout');
  }

  /**
   * Remove custom domain
   */
  async removeCustomDomain(domainId: string): Promise<void> {
    const domain = await db.query.tenantDomains.findFirst({
      where: eq(tenantDomains.id, domainId)
    });

    if (!domain) throw new Error('Domain not found');

    // Remove from load balancer
    await this.loadBalancer.removeRule({
      field: 'host-header',
      value: domain.domain
    });

    // Remove DNS records
    await this.dnsProvider.removeRecord(domain.domain);

    // Revoke SSL certificate
    await this.revokeSSLCertificate(domainId);

    // Delete database record
    await db.delete(tenantDomains)
      .where(eq(tenantDomains.id, domainId));
  }

  /**
   * Validate domain format
   */
  private isValidDomain(domain: string): boolean {
    const domainRegex = /^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$/;
    return domainRegex.test(domain);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

## SSL Certificate Management

### SSL Certificate Provisioner

```typescript
/**
 * SSL certificate manager using Let's Encrypt
 */
class SSLCertificateManager {
  private acmeClient: ACMEClient;
  private storage: CertificateStorage;

  constructor() {
    this.acmeClient = new ACMEClient({
      directoryUrl: process.env.ACME_DIRECTORY || 'https://acme-v02.api.letsencrypt.org/directory'
    });
    this.storage = new CertificateStorage();
  }

  /**
   * Provision SSL certificate for domain
   */
  async provisionCertificate(domainId: string): Promise<Certificate> {
    const domain = await db.query.tenantDomains.findFirst({
      where: eq(tenantDomains.id, domainId)
    });

    if (!domain) throw new Error('Domain not found');
    if (domain.status !== 'verified') {
      throw new Error('Domain must be verified before provisioning SSL');
    }

    await db.update(tenantDomains)
      .set({ sslStatus: 'provisioning' })
      .where(eq(tenantDomains.id, domainId));

    try {
      // Create ACME account
      const account = await this.acmeClient.createAccount({
        termsOfServiceAgreed: true
      });

      // Create order
      const order = await this.acmeClient.createOrder({
        identifiers: [{ type: 'dns', value: domain.domain }]
      });

      // Get authorization challenges
      const authorizations = await this.acmeClient.getAuthorizations(order);

      // Complete challenges
      for (const auth of authorizations) {
        const challenge = auth.challenges.find(c => c.type === 'http-01');
        if (!challenge) continue;

        // Provision challenge response
        await this.provisionChallengeResponse(challenge);

        // Validate challenge
        await this.acmeClient.validateChallenge(challenge);

        // Wait for validation
        await this.waitForValidation(auth);
      }

      // Finalize order
      const keypair = await this.generateKeyPair();
      await this.acmeClient.finalizeOrder(order, {
        csr: await this.generateCSR(domain.domain, keypair)
      });

      // Get certificate
      const certificate = await this.acmeClient.getCertificate(order);

      // Save certificate
      const saved = await this.storage.save({
        domainId,
        domain: domain.domain,
        certificate,
        privateKey: keypair.privateKey,
        expiresAt: this.getExpirationDate(certificate)
      });

      // Update database
      await db.update(tenantDomains)
        .set({
          sslStatus: 'active',
          sslExpiresAt: saved.expiresAt
        })
        .where(eq(tenantDomains.id, domainId));

      // Clean up challenge response
      await this.cleanupChallengeResponse(challenge);

      return saved;

    } catch (error) {
      await db.update(tenantDomains)
        .set({ sslStatus: 'failed' })
        .where(eq(tenantDomains.id, domainId));
      throw error;
    }
  }

  /**
   * Provision HTTP-01 challenge response
   */
  private async provisionChallengeResponse(challenge: Challenge): Promise<void> {
    const token = challenge.token;
    const keyAuthorization = await this.acmeClient.getKeyAuthorization(challenge);

    // Store challenge response at well-known path
    await challengeStorage.put(`/.well-known/acme-challenge/${token}`, keyAuthorization);
  }

  /**
   * Wait for challenge validation
   */
  private async waitForValidation(authorization: Authorization): Promise<void> {
    const maxAttempts = 60;
    const delay = 1000;

    for (let i = 0; i < maxAttempts; i++) {
      const auth = await this.acmeClient.getAuthorization(authorization);

      if (auth.status === 'valid') return;
      if (auth.status === 'invalid') {
        throw new Error('Challenge validation failed');
      }

      await this.sleep(delay);
    }

    throw new Error('Validation timeout');
  }

  /**
   * Renew certificate before expiration
   */
  async renewCertificate(domainId: string): Promise<Certificate> {
    const domain = await db.query.tenantDomains.findFirst({
      where: eq(tenantDomains.id, domainId)
    });

    if (!domain) throw new Error('Domain not found');

    // Check if renewal is needed (within 30 days of expiration)
    const renewalThreshold = 30 * 24 * 60 * 60 * 1000;
    if (domain.sslExpiresAt &&
        domain.sslExpiresAt.getTime() - Date.now() > renewalThreshold) {
      // Certificate still valid, no renewal needed
      return this.storage.load(domainId);
    }

    // Provision new certificate
    return this.provisionCertificate(domainId);
  }

  /**
   * Revoke certificate
   */
  async revokeCertificate(domainId: string): Promise<void> {
    const cert = await this.storage.load(domainId);
    if (!cert) return;

    await this.acmeClient.revokeCertificate(cert.certificate);

    await this.storage.delete(domainId);

    await db.update(tenantDomains)
      .set({ sslStatus: 'revoked' })
      .where(eq(tenantDomains.id, domainId));
  }

  /**
   * Get expiration date from certificate
   */
  private getExpirationDate(certificate: string): Date {
    const cert = new crypto.X509Certificate(certificate);
    return new Date(cert.validTo);
  }

  /**
   * Generate key pair
   */
  private async generateKeyPair(): Promise<{ publicKey: string; privateKey: string }> {
    return new Promise((resolve, reject) => {
      crypto.generateKeyPair('rsa', {
        modulusLength: 2048
      }, (err, publicKey, privateKey) => {
        if (err) reject(err);
        else resolve({
          publicKey: publicKey.export({ type: 'spki', format: 'pem' }).toString(),
          privateKey: privateKey.export({ type: 'pkcs8', format: 'pem' }).toString()
        });
      });
    });
  }

  /**
   * Generate Certificate Signing Request
   */
  private async generateCSR(domain: string, keypair: { publicKey: string; privateKey: string }): Promise<string> {
    // CSR generation implementation
    return '';
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

## Data Migration

### Tenant Import/Export

```typescript
/**
 * Tenant data exporter
 */
class TenantDataExporter {
  /**
   * Export all tenant data
   */
  async exportTenant(tenantId: string): Promise<string> {
    const data = {
      version: '1.0',
      exportedAt: new Date().toISOString(),
      tenantId,
      data: {
        customers: await this.exportTable(tenantId, 'customers'),
        trips: await this.exportTable(tenantId, 'trips'),
        bookings: await this.exportTable(tenantId, 'bookings'),
        quotes: await this.exportTable(tenantId, 'quotes'),
        tags: await this.exportTable(tenantId, 'tags'),
        configurations: await this.exportConfigurations(tenantId)
      }
    };

    const jsonString = JSON.stringify(data, null, 2);
    const exportPath = `/exports/${tenantId}/${Date.now()}.json`;

    await storage.put(exportPath, Buffer.from(jsonString));

    return exportPath;
  }

  /**
   * Export table data
   */
  private async exportTable(tenantId: string, tableName: string): Promise<any[]> {
    await RLSManager.setTenantContext(tenantId);

    return db.query[tableName].findMany();
  }

  /**
   * Export configurations
   */
  private async exportConfigurations(tenantId: string): Promise<Record<string, unknown>> {
    const configs = await db.query.tenantConfig.findMany({
      where: eq(tenantConfig.tenantId, tenantId)
    });

    return configs.reduce((acc, config) => {
      acc[config.key] = config.value;
      return acc;
    }, {} as Record<string, unknown>);
  }
}

/**
 * Tenant data importer
 */
class TenantDataImporter {
  /**
   * Import data to tenant
   */
  async importTenant(
    tenantId: string,
    exportPath: string,
    options?: {
      overwrite?: boolean;
      skipValidation?: boolean;
    }
  ): Promise<void> {
    // Load export data
    const data = await this.loadExportData(exportPath);

    // Validate data
    if (!options?.skipValidation) {
      await this.validateImportData(data);
    }

    await db.transaction(async (tx) => {
      await RLSManager.setTenantContext(tenantId);

      // Import in order of dependencies
      await this.importTable(tenantId, 'tags', data.data.tags, tx);
      await this.importTable(tenantId, 'customers', data.data.customers, tx);
      await this.importTable(tenantId, 'trips', data.data.trips, tx);
      await this.importTable(tenantId, 'bookings', data.data.bookings, tx);
      await this.importTable(tenantId, 'quotes', data.data.quotes, tx);

      // Import configurations
      await this.importConfigurations(tenantId, data.data.configurations, tx);
    });
  }

  /**
   * Import table data
   */
  private async importTable(
    tenantId: string,
    tableName: string,
    records: any[],
    tx: any
  ): Promise<void> {
    for (const record of records) {
      // Override tenant_id
      const data = {
        ...record,
        tenant_id: tenantId,
        id: record.id || generateId()
      };

      await tx.insert(tableName).values(data)
        .onConflictDoNothing()
        .onConflictDoUpdate({
          target: [`${tableName}.id`],
          set: data
        });
    }
  }

  /**
   * Import configurations
   */
  private async importConfigurations(
    tenantId: string,
    configs: Record<string, unknown>,
    tx: any
  ): Promise<void> {
    for (const [key, value] of Object.entries(configs)) {
      await tx.insert(tenantConfig).values({
        id: generateId(),
        tenantId,
        key,
        value,
        type: inferType(value),
        category: inferCategory(key),
        isEncrypted: isSensitiveKey(key),
        isPublic: !isSensitiveKey(key),
        updatedAt: new Date(),
        updatedBy: 'import'
      }).onConflictDoUpdate({
        target: [tenantConfig.tenantId, tenantConfig.key],
        set: {
          value,
          updatedAt: new Date(),
          updatedBy: 'import'
        }
      });
    }
  }

  /**
   * Load export data
   */
  private async loadExportData(exportPath: string): Promise<any> {
    const buffer = await storage.get(exportPath);
    return JSON.parse(buffer.toString());
  }

  /**
   * Validate import data
   */
  private async validateImportData(data: any): Promise<void> {
    if (!data.version) {
      throw new Error('Invalid export format: missing version');
    }

    if (!data.data) {
      throw new Error('Invalid export format: missing data');
    }

    // Validate schema
    const requiredTables = ['customers', 'trips'];
    for (const table of requiredTables) {
      if (!Array.isArray(data.data[table])) {
        throw new Error(`Invalid export format: ${table} is not an array`);
      }
    }
  }
}
```

---

## Implementation

### Complete Onboarding Service

```typescript
/**
 * Complete tenant onboarding service
 */
class TenantOnboardingService {
  private orchestrator: TenantProvisioningOrchestrator;
  private schemaProvisioner: DatabaseSchemaProvisioner;
  private configInitializer: TenantConfigurationInitializer;
  private userProvisioner: TenantUserProvisioner;
  private brandingManager: BrandingManager;
  private domainManager: CustomDomainManager;
  private sslManager: SSLCertificateManager;
  private dataSeeder: TenantDataSeeder;

  constructor() {
    this.orchestrator = new TenantProvisioningOrchestrator();
    this.schemaProvisioner = new DatabaseSchemaProvisioner();
    this.configInitializer = new TenantConfigurationInitializer();
    this.userProvisioner = new TenantUserProvisioner();
    this.brandingManager = new BrandingManager();
    this.domainManager = new CustomDomainManager();
    this.sslManager = new SSLCertificateManager();
    this.dataSeeder = new TenantDataSeeder();
  }

  /**
   * Onboard new tenant
   */
  async onboardTenant(input: TenantProvisioningInput): Promise<{
    workflowId: string;
    tenant: Tenant;
  }> {
    // Create tenant record
    const tenant = await db.insert(tenants).values({
      id: input.tenantId,
      name: input.name,
      subdomain: input.subdomain.toLowerCase(),
      tier: input.tier,
      multiTenancyModel: tierConfigs[input.tier].multiTenancyModel,
      status: 'provisioning',
      createdAt: new Date()
    }).returning().then(rows => rows[0]);

    // Start provisioning workflow
    const workflowId = await this.orchestrator.startProvisioning(input);

    return { workflowId, tenant };
  }

  /**
   * Get onboarding status
   */
  getOnboardingStatus(workflowId: string): OnboardingWorkflow | undefined {
    return this.orchestrator.getWorkflowStatus(workflowId);
  }
}
```

---

## Testing Scenarios

```typescript
describe('Tenant Onboarding', () => {
  describe('Provisioning Workflow', () => {
    it('should complete provisioning successfully', async () => {
      const service = new TenantOnboardingService();

      const { workflowId, tenant } = await service.onboardTenant({
        tenantId: generateId(),
        name: 'Test Agency',
        subdomain: `test-${Date.now()}`,
        tier: TenantTier.STARTUP,
        adminEmail: 'admin@test.com',
        adminName: 'Admin User'
      });

      // Wait for completion
      await waitForWorkflow(workflowId, 60000);

      const status = service.getOnboardingStatus(workflowId);
      expect(status?.state).toBe(OnboardingState.COMPLETED);
    });

    it('should rollback on failure', async () => {
      // Test failure scenario
    });
  });

  describe('Domain Configuration', () => {
    it('should configure custom domain', async () => {
      const manager = new CustomDomainManager();

      const domain = await manager.addCustomDomain(
        'tenant-123',
        'test.example.com',
        { skipDNSCheck: true, autoConfigureSSL: false }
      );

      expect(domain.status).toBe('pending_verification');
    });
  });

  describe('SSL Provisioning', () => {
    it('should provision SSL certificate', async () => {
      const manager = new SSLCertificateManager();

      // Mock ACME client
      // Test certificate provisioning
    });
  });
});
```

---

## API Specification

```yaml
paths:
  /api/v1/tenants:
    post:
      summary: Create and onboard new tenant
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TenantProvisioningInput'
      responses:
        '202':
          description: Onboarding started
          content:
            application/json:
              schema:
                type: object
                properties:
                  workflowId:
                    type: string
                  tenant:
                    $ref: '#/components/schemas/Tenant'

  /api/v1/onboarding/{workflowId}:
    get:
      summary: Get onboarding status
      responses:
        '200':
          description: Onboarding status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OnboardingWorkflow'

  /api/v1/tenants/{tenantId}/branding:
    put:
      summary: Update tenant branding
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BrandingAssets'
      responses:
        '200':
          description: Branding updated

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
                autoConfigureSSL:
                  type: boolean
      responses:
        '202':
          description: Domain configuration started

components:
  schemas:
    TenantProvisioningInput:
      type: object
      required: [name, subdomain, tier, adminEmail, adminName]
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
        customDomain:
          type: string
        branding:
          $ref: '#/components/schemas/BrandingAssets'

    BrandingAssets:
      type: object
      properties:
        logo:
          type: object
          properties:
            light:
              type: string
            dark:
              type: string
            favicon:
              type: string
        colors:
          type: object
          properties:
            primary:
              type: string
            secondary:
              type: string
        typography:
          type: object
          properties:
            fontFamily:
              type: string
```

---

## Metrics and Monitoring

```typescript
interface OnboardingMetrics {
  totalOnboarded: number;
  onboardingInProgress: number;
  averageProvisioningTime: number;
  provisioningSuccessRate: number;
  failuresByReason: Record<string, number>;
  sslCertificatesIssued: number;
  customDomainsConfigured: number;
}
```

---

**End of Document**

**Next:** [Tenant Operations Deep Dive](MULTI_TENANCY_04_OPERATIONS.md)
