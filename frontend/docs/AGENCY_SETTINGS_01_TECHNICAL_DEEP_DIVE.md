# Agency Settings — Technical Deep Dive

> Part 1 of 4 in Agency Settings Exploration Series

---

## Document Overview

**Series:** Agency Settings / Configuration
**Part:** 1 — Technical Architecture
**Status:** Complete
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Settings Architecture](#settings-architecture)
3. [Database Schema](#database-schema)
4. [Settings Inheritance](#settings-inheritance)
5. [Configuration Service](#configuration-service)
6. [Branding System](#branding-system)
7. [Team & Permissions](#team--permissions)
8. [API Specification](#api-specification)

---

## System Overview

### What Are Agency Settings?

Agency Settings is a comprehensive configuration system that allows travel agencies to customize their workspace, manage their team, define permissions, and establish their brand identity across all customer-facing communications.

### Settings Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENCY SETTINGS CATEGORIES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   PROFILE       │  │   BRANDING      │  │   TEAM          │            │
│  │                 │  │                 │  │                 │            │
│  │ • Name          │  │ • Logo          │  │ • Members       │            │
│  │ • Contact       │  │ • Colors        │  │ • Roles         │            │
│  │ • Address       │  │ • Fonts         │  │ • Permissions   │            │
│  │ • GST/PAN       │  │ • Email Styles  │  │ • Groups        │            │
│  │ • Business Hrs  │  │ • Templates     │  │ • Onboarding    │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   PREFERENCES   │  │   INTEGRATIONS  │  │   BILLING       │            │
│  │                 │  │                 │  │                 │            │
│  │ • Currency      │  │ • WhatsApp      │  │ • Plan          │            │
│  │ • Timezone      │  │ • Email         │  │ • Payment Mtd   │            │
│  │ • Language      │  │ • SMS           │  │ • Invoices      │            │
│  │ • Date Format   │  │ • Payment Gateway│  │ • Usage         │            │
│  │ • Number Format │  │ • Tally         │  │                 │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   NOTIFICATIONS │  │   AUTOMATION    │  │   SECURITY      │            │
│  │                 │  │                 │  │                 │            │
│  │ • Email Alerts  │  │ • Auto-assign   │  │ • 2FA           │            │
│  │ • Push Notify   │  │ • Auto-response │  │ • SSO           │            │
│  │ • SMS Alerts    │  │ • Escalation    │  │ • Audit Log     │            │
│  │ • Webhooks      │  │ • SLA Rules     │  │ • IP Whitelist  │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Settings Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SETTINGS ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        FRONTEND LAYER                                │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │  │ Settings   │  │ Branding   │  │ Team       │  │ Billing    │   │   │
│  │  │ Panel      │  │ Editor     │  │ Manager    │  │ Section    │   │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘   │   │
│  └────────┼───────────────┼───────────────┼───────────────┼──────────┘   │
│           │              │               │               │               │
│           └──────────────┴───────────────┴───────────────┴───────┐       │
│                                                          │             │
│  ┌───────────────────────────────────────────────────────▼─────────┐     │
│  │                        API LAYER                            │     │
│  │  ┌────────────────────────────────────────────────────────┐      │     │
│  │  │  Settings Routes (Protected by authentication)        │      │     │
│  │  │  - GET    /api/settings                               │      │     │
│  │  │  - PATCH  /api/settings                               │      │     │
│  │  │  - GET    /api/settings/:category                     │      │     │
│  │  │  - POST   /api/settings/branding/logo                 │      │     │
│  │  └────────────────────────────────────────────────────────┘      │     │
│  └───────────────────────────────┬─────────────────────────────────┘     │
│                                  │                                         │
│  ┌───────────────────────────────▼─────────────────────────────────┐     │
│  │                    SETTINGS SERVICE LAYER                        │     │
│  │  ┌────────────────────────────────────────────────────────┐      │     │
│  │  │  SettingsService                                         │      │     │
│  │  │  - getSettings()                                         │      │     │
│  │  │  - updateSettings()                                      │      │     │
│  │  │  - resetToDefaults()                                     │      │     │
│  │  │  - validateSettings()                                    │      │     │
│  │  └────────────────────────────────────────────────────────┘      │     │
│  │  ┌────────────────────────────────────────────────────────┐      │     │
│  │  │  BrandingService                                         │      │     │
│  │  │  - uploadLogo()                                          │      │     │
│  │  │  - generateColorPalette()                                │      │     │
│  │  │  - previewEmailTemplate()                                │      │     │
│  │  └────────────────────────────────────────────────────────┘      │     │
│  │  ┌────────────────────────────────────────────────────────┐      │     │
│  │  │  TeamService                                             │      │     │
│  │  │  - inviteMember()                                        │      │     │
│  │  │  - updateRole()                                          │      │     │
│  │  │  - setPermissions()                                      │      │     │
│  │  └────────────────────────────────────────────────────────┘      │     │
│  └───────────────────────────────┬─────────────────────────────────┘     │
│                                  │                                         │
│  ┌───────────────────────────────▼─────────────────────────────────┐     │
│  │                    DATA LAYER                                  │     │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐      │     │
│  │  │  PostgreSQL    │  │  Redis Cache   │  │  S3 Storage    │      │     │
│  │  │  - agencies    │  │  - Settings    │  │  - Logos       │      │     │
│  │  │  - settings    │  │  - Branding    │  │  - Assets      │      │     │
│  │  │  - users       │  │  - Permissions │  │                │      │     │
│  │  │  - roles       │  │                │  │                │      │     │
│  │  └────────────────┘  └────────────────┘  └────────────────┘      │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
AgencySettings
├── Frontend
│   ├── pages/
│   │   ├── Settings.tsx
│   │   │   ├── General.tsx
│   │   │   ├── Branding.tsx
│   │   │   ├── Team.tsx
│   │   │   ├── Notifications.tsx
│   │   │   ├── Integrations.tsx
│   │   │   ├── Billing.tsx
│   │   │   └── Security.tsx
│   │   └── NotFound.tsx
│   ├── components/
│   │   ├── settings/
│   │   │   ├── SettingsLayout.tsx
│   │   │   ├── SettingsCard.tsx
│   │   │   ├── SettingsSection.tsx
│   │   │   └── SettingsField.tsx
│   │   ├── branding/
│   │   │   ├── LogoUploader.tsx
│   │   │   ├── ColorPicker.tsx
│   │   │   ├── FontSelector.tsx
│   │   │   └── TemplatePreview.tsx
│   │   └── team/
│   │       ├── MemberList.tsx
│   │       ├── RoleSelector.tsx
│   │       ├── PermissionMatrix.tsx
│   │       └── InviteModal.tsx
│   └── hooks/
│       ├── useSettings.ts
│       ├── useBranding.ts
│       └── useTeam.ts
│
├── Backend
│   ├── routes/
│   │   ├── settings.routes.ts
│   │   ├── branding.routes.ts
│   │   ├── team.routes.ts
│   │   └── billing.routes.ts
│   ├── services/
│   │   ├── settings.service.ts
│   │   ├── branding.service.ts
│   │   └── team.service.ts
│   ├── middleware/
│   │   ├── agency-admin.middleware.ts
│   │   └── settings-owner.middleware.ts
│   └── validators/
│       ├── settings.validator.ts
│       └── branding.validator.ts
│
└── Database
    ├── migrations/
    │   ├── XXX_create_agencies_table.sql
    │   ├── XXX_create_settings_table.sql
    │   ├── XXX_create_branding_table.sql
    │   └── XXX_create_roles_permissions_table.sql
    └── seeds/
        └── default_settings.seed.ts
```

---

## Database Schema

### Agencies Table

```sql
-- migrations/XXX_create_agencies_table.sql

CREATE TABLE agencies (
  -- Primary identification
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Profile information
  name VARCHAR(255) NOT NULL,
  legal_name VARCHAR(255), -- Different from display name if needed
  slug VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,

  -- Contact information
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  website VARCHAR(500),

  -- Address
  address_line1 VARCHAR(255),
  address_line2 VARCHAR(255),
  city VARCHAR(100),
  state VARCHAR(100),
  postal_code VARCHAR(20),
  country_code CHAR(2) DEFAULT 'IN',

  -- Business identifiers
  gst_number VARCHAR(15),
  pan_number VARCHAR(10),
  tan_number VARCHAR(10),

  -- Business details
  business_type VARCHAR(50), -- 'sole_proprietorship', 'partnership', 'pvt_ltd', 'llp'
  industry VARCHAR(100), -- 'travel_agency', 'tour_operator', etc.
  year_established INTEGER,

  -- Subscription
  plan_id VARCHAR(50) DEFAULT 'starter',
  plan_status VARCHAR(20) DEFAULT 'active' CHECK (plan_status IN ('active', 'trial', 'suspended', 'cancelled')),
  trial_ends_at TIMESTAMPTZ,
  subscription_renews_at TIMESTAMPTZ,

  -- Usage tracking
  monthly_message_quota INTEGER DEFAULT 1000,
  monthly_message_sent INTEGER DEFAULT 0,
  quota_reset_at TIMESTAMPTZ,

  -- Status
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
  onboarding_completed BOOLEAN DEFAULT false,
  onboarding_step VARCHAR(50),

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ,

  CONSTRAINT valid_slug CHECK (slug ~* '^[a-z0-9-]+$'),
  CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes
CREATE INDEX idx_agencies_slug ON agencies(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_agencies_status ON agencies(status, deleted_at);
CREATE INDEX idx_agencies_plan ON agencies(plan_id, plan_status);

-- Owner relationship (through agency_agents)
CREATE TABLE agency_owners (
  agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  is_primary BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (agency_id, user_id)
);
```

### Settings Table

```sql
-- migrations/XXX_create_settings_table.sql

CREATE TABLE agency_settings (
  -- Primary identification
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,

  -- Category and key
  category VARCHAR(50) NOT NULL,
  key VARCHAR(100) NOT NULL,
  value JSONB NOT NULL,

  -- Type and validation
  value_type VARCHAR(20) NOT NULL CHECK (value_type IN ('string', 'number', 'boolean', 'object', 'array')),
  is_encrypted BOOLEAN DEFAULT false,

  -- Metadata
  description TEXT,
  default_value JSONB,
  validation_rules JSONB,

  -- Access control
  is_public BOOLEAN DEFAULT false, -- Can be accessed without special permissions
  requires_plan VARCHAR(50), -- Minimum plan required (e.g., 'professional')

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_setting UNIQUE(agency_id, category, key)
);

-- Indexes
CREATE INDEX idx_settings_agency_category ON agency_settings(agency_id, category);
CREATE INDEX idx_settings_public ON agency_settings(is_public) WHERE is_public = true;

-- Default settings template
CREATE TABLE default_settings (
  category VARCHAR(50) NOT NULL,
  key VARCHAR(100) NOT NULL,
  value JSONB NOT NULL,
  value_type VARCHAR(20) NOT NULL,
  description TEXT,
  default_value JSONB,
  validation_rules JSONB,
  PRIMARY KEY (category, key)
);
```

### Branding Table

```sql
-- migrations/XXX_create_branding_table.sql

CREATE TABLE agency_branding (
  -- Primary identification
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,

  -- Logo
  logo_url VARCHAR(500),
  logo_dark_url VARCHAR(500), -- For dark mode
  logo_icon_url VARCHAR(500), -- Favicon/app icon
  logo_width INTEGER,
  logo_height INTEGER,

  -- Colors
  primary_color CHAR(7) DEFAULT '#6366F1',
  secondary_color CHAR(7) DEFAULT '#8B5CF6',
  accent_color CHAR(7) DEFAULT '#EC4899',
  background_color CHAR(7) DEFAULT '#FFFFFF',
  text_color CHAR(7) DEFAULT '#111827',

  -- Typography
  font_family VARCHAR(100) DEFAULT 'Inter',
  font_family_heading VARCHAR(100),
  font_size_base INTEGER DEFAULT 16,

  -- Email branding
  email_header_background CHAR(7) DEFAULT '#6366F1',
  email_footer_text TEXT,
  email_signature TEXT,

  -- Document branding
  document_header_logo_url VARCHAR(500),
  document_footer_text TEXT,
  document_watermark_enabled BOOLEAN DEFAULT false,
  document_watermark_text VARCHAR(255),

  -- Custom domain
  custom_domain VARCHAR(255),
  custom_domain_verified BOOLEAN DEFAULT false,
  custom_domain_ssl_until TIMESTAMPTZ,

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_agency_branding UNIQUE(agency_id)
);
```

### Team & Roles Tables

```sql
-- migrations/XXX_create_roles_permissions_table.sql

-- Roles
CREATE TABLE roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  is_system_role BOOLEAN DEFAULT false, -- Built-in roles like Owner, Admin

  -- Role hierarchy
  parent_role_id UUID REFERENCES roles(id),

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_role_name UNIQUE(agency_id, name)
);

-- Permissions
CREATE TABLE permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource VARCHAR(100) NOT NULL, -- 'trips', 'customers', 'messages', etc.
  action VARCHAR(50) NOT NULL, -- 'create', 'read', 'update', 'delete', etc.
  description TEXT,

  CONSTRAINT unique_permission UNIQUE(resource, action)
);

-- Role permissions junction
CREATE TABLE role_permissions (
  role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
  permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
  granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (role_id, permission_id)
);

-- Agency members
CREATE TABLE agency_agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID REFERENCES roles(id) ON DELETE SET NULL,

  -- Profile within agency
  job_title VARCHAR(255),
  department VARCHAR(100),

  -- Status
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pending', 'suspended', 'removed')),
  invited_by UUID REFERENCES users(id),
  invited_at TIMESTAMPTZ,
  joined_at TIMESTAMPTZ,

  -- Last activity
  last_active_at TIMESTAMPTZ,

  -- Notification preferences
  notification_preferences JSONB DEFAULT '{}',

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_agent_in_agency UNIQUE(agency_id, user_id)
);

-- Indexes
CREATE INDEX idx_agents_agency ON agency_agents(agency_id, status);
CREATE INDEX idx_agents_user ON agency_agents(user_id);
CREATE INDEX idx_agents_role ON agency_agents(role_id);
```

---

## Settings Inheritance

### Settings Hierarchy Model

```typescript
// types/settings.types.ts

export interface SettingValue<T = unknown> {
  category: string;
  key: string;
  value: T;
  valueType: ValueType;
  isEncrypted: boolean;
  source: 'default' | 'agency' | 'user';
  overridden: boolean;
}

export enum ValueType {
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  OBJECT = 'object',
  ARRAY = 'array'
}

export interface SettingsHierarchy {
  default: Record<string, unknown>;
  agency: Record<string, unknown>;
  user?: Record<string, unknown>;
}

/**
 * Settings resolution with inheritance
 *
 * Priority: User > Agency > Default
 */
export class SettingsResolver {
  /**
   * Get setting value with inheritance
   */
  async getSetting<T>(
    agencyId: string,
    category: string,
    key: string,
    userId?: string
  ): Promise<SettingValue<T>> {
    // 1. Check user override
    if (userId) {
      const userSetting = await this.getUserSetting(agencyId, userId, category, key);
      if (userSetting) {
        return {
          category,
          key,
          value: userSetting.value as T,
          valueType: userSetting.value_type as ValueType,
          isEncrypted: userSetting.is_encrypted,
          source: 'user',
          overridden: true
        };
      }
    }

    // 2. Check agency setting
    const agencySetting = await this.getAgencySetting(agencyId, category, key);
    if (agencySetting) {
      return {
        category,
        key,
        value: agencySetting.value as T,
        valueType: agencySetting.value_type as ValueType,
        isEncrypted: agencySetting.is_encrypted,
        source: 'agency',
        overridden: false
      };
    }

    // 3. Return default
    const defaultSetting = await this.getDefaultSetting(category, key);
    return {
      category,
      key,
      value: defaultSetting.value as T,
      valueType: defaultSetting.value_type as ValueType,
      isEncrypted: false,
      source: 'default',
      overridden: false
    };
  }

  /**
   * Get all settings for a category
   */
  async getSettings(
    agencyId: string,
    category: string,
    userId?: string
  ): Promise<Record<string, SettingValue>> {
    const defaults = await this.getDefaultSettings(category);
    const agencySettings = await this.getAgencySettings(agencyId, category);
    const userSettings = userId
      ? await this.getUserSettings(agencyId, userId, category)
      : {};

    const result: Record<string, SettingValue> = {};

    // Start with defaults
    for (const [key, setting] of Object.entries(defaults)) {
      result[key] = {
        category,
        key,
        value: setting.value,
        valueType: setting.value_type,
        isEncrypted: false,
        source: 'default',
        overridden: false
      };
    }

    // Override with agency settings
    for (const [key, setting] of Object.entries(agencySettings)) {
      if (result[key]) {
        result[key] = {
          ...result[key],
          value: setting.value,
          isEncrypted: setting.is_encrypted,
          source: 'agency',
          overridden: true
        };
      }
    }

    // Override with user settings
    for (const [key, setting] of Object.entries(userSettings)) {
      if (result[key]) {
        result[key] = {
          ...result[key],
          value: setting.value,
          isEncrypted: setting.is_encrypted,
          source: 'user',
          overridden: true
        };
      }
    }

    return result;
  }

  /**
   * Update agency setting
   */
  async updateAgencySetting(
    agencyId: string,
    category: string,
    key: string,
    value: unknown,
    updatedBy: string
  ): Promise<SettingValue> {
    // Get default for validation
    const defaultSetting = await this.getDefaultSetting(category, key);

    // Validate against rules
    await this.validateSetting(category, key, value, defaultSetting.validation_rules);

    // Upsert setting
    await db.query(`
      INSERT INTO agency_settings (agency_id, category, key, value, value_type, validation_rules)
      VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (agency_id, category, key)
      DO UPDATE SET
        value = EXCLUDED.value,
        value_type = EXCLUDED.value_type,
        updated_at = NOW()
    `, [agencyId, category, key, JSON.stringify(value), defaultSetting.value_type, JSON.stringify(defaultSetting.validation_rules)]);

    // Clear cache
    await this.clearCache(agencyId, category);

    // Audit log
    await this.logSettingChange(agencyId, category, key, value, 'agency', updatedBy);

    return {
      category,
      key,
      value,
      valueType: defaultSetting.value_type as ValueType,
      isEncrypted: false,
      source: 'agency',
      overridden: true
    };
  }

  /**
   * Reset setting to default
   */
  async resetToDefault(
    agencyId: string,
    category: string,
    key: string,
    updatedBy: string
  ): Promise<void> {
    await db.query(`
      DELETE FROM agency_settings
      WHERE agency_id = $1 AND category = $2 AND key = $3
    `, [agencyId, category, key]);

    await this.clearCache(agencyId, category);

    await this.logSettingChange(agencyId, category, key, null, 'reset', updatedBy);
  }

  private async getDefaultSetting(category: string, key: string) {
    const result = await db.query(
      'SELECT * FROM default_settings WHERE category = $1 AND key = $2',
      [category, key]
    );
    return result.rows[0];
  }

  private async getDefaultSettings(category: string) {
    const result = await db.query(
      'SELECT * FROM default_settings WHERE category = $1',
      [category]
    );
    return result.rows.reduce((acc, row) => {
      acc[row.key] = row;
      return acc;
    }, {});
  }

  private async getAgencySetting(agencyId: string, category: string, key: string) {
    const result = await db.query(
      'SELECT * FROM agency_settings WHERE agency_id = $1 AND category = $2 AND key = $3',
      [agencyId, category, key]
    );
    return result.rows[0];
  }

  private async getAgencySettings(agencyId: string, category: string) {
    const result = await db.query(
      'SELECT * FROM agency_settings WHERE agency_id = $1 AND category = $2',
      [agencyId, category]
    );
    return result.rows.reduce((acc, row) => {
      acc[row.key] = row;
      return acc;
    }, {});
  }

  private async getUserSetting(agencyId: string, userId: string, category: string, key: string) {
    const result = await db.query(
      'SELECT * FROM user_settings WHERE agency_id = $1 AND user_id = $2 AND category = $3 AND key = $4',
      [agencyId, userId, category, key]
    );
    return result.rows[0];
  }

  private async getUserSettings(agencyId: string, userId: string, category: string) {
    const result = await db.query(
      'SELECT * FROM user_settings WHERE agency_id = $1 AND user_id = $2 AND category = $3',
      [agencyId, userId, category]
    );
    return result.rows.reduce((acc, row) => {
      acc[row.key] = row;
      return acc;
    }, {});
  }

  private async validateSetting(
    category: string,
    key: string,
    value: unknown,
    rules: unknown
  ): Promise<void> {
    if (!rules) return;

    const validation = rules as ValidationRules;

    // Type validation
    if (validation.type) {
      let isValid = false;
      switch (validation.type) {
        case 'string':
          isValid = typeof value === 'string';
          break;
        case 'number':
          isValid = typeof value === 'number';
          break;
        case 'boolean':
          isValid = typeof value === 'boolean';
          break;
        case 'email':
          isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value as string);
          break;
        case 'url':
          try {
            new URL(value as string);
            isValid = true;
          } catch {
            isValid = false;
          }
          break;
      }

      if (!isValid) {
        throw new Error(`Invalid value type for ${category}.${key}. Expected ${validation.type}`);
      }
    }

    // Range validation
    if (validation.min !== undefined && (typeof value === 'number') && value < validation.min) {
      throw new Error(`${category}.${key} must be at least ${validation.min}`);
    }

    if (validation.max !== undefined && (typeof value === 'number') && value > validation.max) {
      throw new Error(`${category}.${key} must be at most ${validation.max}`);
    }

    // Enum validation
    if (validation.enum && !validation.enum.includes(value)) {
      throw new Error(`${category}.${key} must be one of: ${validation.enum.join(', ')}`);
    }

    // Pattern validation
    if (validation.pattern) {
      const regex = new RegExp(validation.pattern);
      if (!regex.test(value as string)) {
        throw new Error(`${category}.${key} format is invalid`);
      }
    }
  }

  private async clearCache(agencyId: string, category: string): Promise<void> {
    const redis = getRedisClient();
    const key = `settings:${agencyId}:${category}`;
    await redis.del(key);
  }

  private async logSettingChange(
    agencyId: string,
    category: string,
    key: string,
    value: unknown,
    action: string,
    userId: string
  ): Promise<void> {
    await db.query(`
      INSERT INTO audit_log_settings (agency_id, category, setting_key, old_value, new_value, action, user_id)
      SELECT $1, $2, $3, value, $4, $5, $6
      FROM agency_settings
      WHERE agency_id = $1 AND category = $2 AND key = $3
    `, [agencyId, category, key, JSON.stringify(value), action, userId]);
  }
}

interface ValidationRules {
  type?: 'string' | 'number' | 'boolean' | 'email' | 'url' | 'phone';
  min?: number;
  max?: number;
  pattern?: string;
  enum?: unknown[];
  required?: boolean;
}
```

---

## Configuration Service

### Settings Service

```typescript
// services/settings.service.ts

import { SettingsResolver, SettingValue } from './settings-resolver';

export class SettingsService {
  private resolver: SettingsResolver;
  private cache: Map<string, { value: unknown; expiresAt: number }> = new Map();
  private cacheTTL = 60000; // 1 minute

  constructor() {
    this.resolver = new SettingsResolver();
  }

  /**
   * Get setting with caching
   */
  async getSetting<T>(
    agencyId: string,
    category: string,
    key: string,
    userId?: string,
    options?: { skipCache?: boolean }
  ): Promise<T> {
    const cacheKey = `${agencyId}:${category}:${key}:${userId || 'default'}`;

    if (!options?.skipCache) {
      const cached = this.getFromCache<T>(cacheKey);
      if (cached !== null) {
        return cached;
      }
    }

    const setting = await this.resolver.getSetting<T>(agencyId, category, key, userId);
    this.setToCache(cacheKey, setting.value);

    return setting.value;
  }

  /**
   * Get all settings for a category
   */
  async getSettings(
    agencyId: string,
    category: string,
    userId?: string
  ): Promise<Record<string, unknown>> {
    const settings = await this.resolver.getSettings(agencyId, category, userId);

    const result: Record<string, unknown> = {};
    for (const [key, setting] of Object.entries(settings)) {
      result[key] = setting.value;
    }

    return result;
  }

  /**
   * Update setting
   */
  async updateSetting(
    agencyId: string,
    category: string,
    key: string,
    value: unknown,
    userId: string
  ): Promise<SettingValue> {
    const setting = await this.resolver.updateAgencySetting(
      agencyId,
      category,
      key,
      value,
      userId
    );

    // Invalidate cache
    const cacheKey = `${agencyId}:${category}:${key}:default`;
    this.cache.delete(cacheKey);

    return setting;
  }

  /**
   * Bulk update settings
   */
  async updateSettings(
    agencyId: string,
    category: string,
    updates: Record<string, unknown>,
    userId: string
  ): Promise<SettingValue[]> {
    const results: SettingValue[] = [];

    for (const [key, value] of Object.entries(updates)) {
      const result = await this.updateSetting(agencyId, category, key, value, userId);
      results.push(result);
    }

    return results;
  }

  /**
   * Reset setting to default
   */
  async resetSetting(
    agencyId: string,
    category: string,
    key: string,
    userId: string
  ): Promise<void> {
    await this.resolver.resetToDefault(agencyId, category, key, userId);

    // Invalidate cache
    const cacheKey = `${agencyId}:${category}:${key}:default`;
    this.cache.delete(cacheKey);
  }

  /**
   * Get effective settings for frontend
   */
  async getEffectiveSettings(agencyId: string, userId?: string): Promise<EffectiveSettings> {
    const [
      general,
      preferences,
      notifications,
      branding
    ] = await Promise.all([
      this.getSettings(agencyId, 'general', userId),
      this.getSettings(agencyId, 'preferences', userId),
      this.getSettings(agencyId, 'notifications', userId),
      this.getSettings(agencyId, 'branding', userId)
    ]);

    return {
      general: general as GeneralSettings,
      preferences: preferences as PreferenceSettings,
      notifications: notifications as NotificationSettings,
      branding: branding as BrandingSettings
    };
  }

  private getFromCache<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.value as T;
    }
    this.cache.delete(key);
    return null;
  }

  private setToCache(key: string, value: unknown): void {
    this.cache.set(key, {
      value,
      expiresAt: Date.now() + this.cacheTTL
    });
  }
}

// Type definitions for settings categories
export interface GeneralSettings {
  agencyName: string;
  agencyEmail: string;
  agencyPhone: string;
  agencyWebsite: string;
  address: {
    line1: string;
    line2?: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
  gstNumber?: string;
  panNumber?: string;
}

export interface PreferenceSettings {
  currency: string;
  timezone: string;
  language: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  numberFormat: 'indian' | 'international';
  firstDayOfWeek: 0 | 1 | 6; // Sunday, Monday, Saturday
}

export interface NotificationSettings {
  email: {
    newInquiry: boolean;
    bookingConfirmed: boolean;
    paymentReceived: boolean;
    dailySummary: boolean;
  };
  push: {
    enabled: boolean;
    newMessage: boolean;
    tripUpdate: boolean;
  };
  sms: {
    enabled: boolean;
    urgentOnly: boolean;
  };
}

export interface BrandingSettings {
  logoUrl?: string;
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
}

export interface EffectiveSettings {
  general: GeneralSettings;
  preferences: PreferenceSettings;
  notifications: NotificationSettings;
  branding: BrandingSettings;
}
```

---

## Branding System

### Branding Service

```typescript
// services/branding.service.ts

import { S3Client, PutObjectCommand, DeleteObjectCommand } from '@aws-sdk/client-s3';
import sharp from 'sharp';

export class BrandingService {
  private s3: S3Client;
  private bucketName: string;

  constructor() {
    this.s3 = new S3Client({
      region: process.env.AWS_REGION,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
      }
    });
    this.bucketName = process.env.S3_BRANDING_BUCKET!;
  }

  /**
   * Upload agency logo
   */
  async uploadLogo(
    agencyId: string,
    file: Express.Multer.File,
    options: {
      variant?: 'light' | 'dark' | 'icon';
      maxWidth?: number;
    } = {}
  ): Promise<{ url: string; width: number; height: number }> {
    const { variant = 'light', maxWidth = 400 } = options;

    // Process image
    let image = sharp(file.buffer);

    // Get metadata
    const metadata = await image.metadata();

    // Resize if needed
    if (metadata.width && metadata.width > maxWidth) {
      image = image.resize(maxWidth, null, {
        withoutEnlargement: true,
        fit: 'inside'
      });
    }

    // Convert to PNG for transparency support
    const processed = await image.png().toBuffer();

    // Generate S3 key
    const key = `branding/${agencyId}/logo-${variant}-${Date.now()}.png`;

    // Upload to S3
    const command = new PutObjectCommand({
      Bucket: this.bucketName,
      Key: key,
      Body: processed,
      ContentType: 'image/png',
      CacheControl: 'public, max-age=31536000' // 1 year
    });

    await this.s3.send(command);

    // Get public URL
    const url = `https://${this.bucketName}.s3.${process.env.AWS_REGION}.amazonaws.com/${key}`;

    // Update database
    const column = variant === 'dark' ? 'logo_dark_url' : variant === 'icon' ? 'logo_icon_url' : 'logo_url';

    await db.query(`
      INSERT INTO agency_branding (agency_id, ${column}, logo_width, logo_height)
      VALUES ($1, $2, $3, $4)
      ON CONFLICT (agency_id)
      DO UPDATE SET ${column} = EXCLUDED.${column}, logo_width = EXCLUDED.logo_width, logo_height = EXCLUDED.logo_height, updated_at = NOW()
    `, [agencyId, url, metadata.width, metadata.height]);

    // Clear cache
    await this.clearCache(agencyId);

    return { url, width: metadata.width || 0, height: metadata.height || 0 };
  }

  /**
   * Generate color palette from logo
   */
  async generateColorPalette(agencyId: string, logoUrl: string): Promise<ColorPalette> {
    // Download image
    const response = await fetch(logoUrl);
    const buffer = Buffer.from(await response.arrayBuffer());

    // Extract dominant colors using sharp
    const { dominant } = await sharp(buffer)
      .resize(50, 50, { fit: 'cover' })
      .raw()
      .toBuffer({ resolveWithObject: true })
      .then(({ data, info }) => {
        // Simple color extraction
        const colors: Record<string, number> = {};

        for (let i = 0; i < data.length; i += 4) {
          const r = data[i];
          const g = data[i + 1];
          const b = data[i + 2];
          const hex = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
          colors[hex] = (colors[hex] || 0) + 1;
        }

        const sorted = Object.entries(colors).sort((a, b) => b[1] - a[1]);
        return {
          dominant: sorted[0]?.[0] || '#6366F1',
          palette: sorted.slice(0, 5).map(([color]) => color)
        };
      });

    return {
      primary: dominant,
      secondary: this.generateComplementary(dominant),
      accent: this.generateAccent(dominant),
      palette: []
    };
  }

  /**
   * Preview email template with branding
   */
  async previewEmailTemplate(
    agencyId: string,
    templateType: 'booking_confirmation' | 'payment_receipt' | 'itinerary'
  ): Promise<{ html: string; text: string }> {
    const branding = await this.getBranding(agencyId);
    const settings = await this.getSettings(agencyId, 'branding');

    // Load template
    const template = await this.loadEmailTemplate(templateType);

    // Render with branding
    const html = template.render({
      logoUrl: branding.logo_url,
      primaryColor: branding.primary_color,
      agencyName: settings.agencyName,
      agencyEmail: settings.agencyEmail,
      agencyPhone: settings.agencyPhone,
      agencyWebsite: settings.agencyWebsite
    });

    return { html, text: this.stripHtml(html) };
  }

  /**
   * Get agency branding
   */
  async getBranding(agencyId: string): Promise<AgencyBranding> {
    const result = await db.query(
      'SELECT * FROM agency_branding WHERE agency_id = $1',
      [agencyId]
    );

    if (result.rows.length === 0) {
      return this.getDefaultBranding();
    }

    return result.rows[0];
  }

  /**
   * Update branding settings
   */
  async updateBranding(
    agencyId: string,
    updates: Partial<AgencyBranding>,
    userId: string
  ): Promise<AgencyBranding> {
    const allowedFields = [
      'primary_color',
      'secondary_color',
      'accent_color',
      'background_color',
      'text_color',
      'font_family',
      'font_family_heading',
      'font_size_base',
      'email_header_background',
      'email_footer_text',
      'email_signature',
      'document_footer_text',
      'document_watermark_enabled',
      'document_watermark_text'
    ];

    const updatesFiltered: Record<string, unknown> = {};
    const setColumns: string[] = [];
    const values: unknown[] = [agencyId];
    let paramIndex = 2;

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        updatesFiltered[key] = value;
        setColumns.push(`${key} = $${paramIndex++}`);
        values.push(value);
      }
    }

    if (setColumns.length === 0) {
      throw new Error('No valid branding fields to update');
    }

    values.push(userId);

    const result = await db.query(`
      INSERT INTO agency_branding (agency_id)
      VALUES ($1)
      ON CONFLICT (agency_id)
      DO UPDATE SET ${setColumns.join(', ')}, updated_at = NOW()
      RETURNING *
    `, values);

    await this.clearCache(agencyId);

    // Log change
    await this.logBrandingChange(agencyId, updatesFiltered, userId);

    return result.rows[0];
  }

  /**
   * Set custom domain
   */
  async setCustomDomain(
    agencyId: string,
    domain: string,
    userId: string
  ): Promise<{ verificationToken: string; dnsRecords: DNSRecord[] }> {
    const verificationToken = generateToken();

    await db.query(`
      INSERT INTO agency_branding (agency_id, custom_domain, custom_domain_verified)
      VALUES ($1, $2, false)
      ON CONFLICT (agency_id)
      DO UPDATE SET custom_domain = EXCLUDED.custom_domain, custom_domain_verified = false, updated_at = NOW()
    `, [agencyId, domain]);

    const dnsRecords: DNSRecord[] = [
      {
        type: 'CNAME',
        name: domain,
        value: `${process.env.CUSTOM_DOMAIN_TARGET || 'app.travelagency.com'}.`
      },
      {
        type: 'TXT',
        name: `_travelagency-verify.${domain}`,
        value: verificationToken
      }
    ];

    return { verificationToken, dnsRecords };
  }

  /**
   * Verify custom domain ownership
   */
  async verifyCustomDomain(agencyId: string): Promise<boolean> {
    const branding = await this.getBranding(agencyId);

    if (!branding.custom_domain) {
      throw new Error('No custom domain set');
    }

    // Check DNS TXT record
    const resolver = new Resolver();
    const txtRecords = await resolver.resolveTxt(`_travelagency-verify.${branding.custom_domain}`);

    const isVerified = txtRecords.some(record =>
      record.includes(process.env.DOMAIN_VERIFICATION_TOKEN || '')
    );

    if (isVerified) {
      await db.query(
        'UPDATE agency_branding SET custom_domain_verified = true WHERE agency_id = $1',
        [agencyId]
      );

      // Provision SSL certificate
      await this.provisionSSLCertificate(agencyId, branding.custom_domain);
    }

    return isVerified;
  }

  private generateComplementary(hex: string): string {
    // Simple complementary color generation
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    const compR = (255 - r).toString(16).padStart(2, '0');
    const compG = (255 - g).toString(16).padStart(2, '0');
    const compB = (255 - b).toString(16).padStart(2, '0');

    return `#${compR}${compG}${compB}`;
  }

  private generateAccent(hex: string): string {
    // Generate accent by shifting hue
    const hsl = this.hexToHSL(hex);
    hsl.h = (hsl.h + 30) % 360;
    return this.hslToHex(hsl);
  }

  private hexToHSL(hex: string): { h: number; s: number; l: number } {
    let r = parseInt(hex.slice(1, 3), 16) / 255;
    let g = parseInt(hex.slice(3, 5), 16) / 255;
    let b = parseInt(hex.slice(5, 7), 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0;
    let s = 0;
    const l = (max + min) / 2;

    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

      switch (max) {
        case r:
          h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
          break;
        case g:
          h = ((b - r) / d + 2) / 6;
          break;
        case b:
          h = ((r - g) / d + 4) / 6;
          break;
      }
    }

    return { h: h * 360, s: s * 100, l: l * 100 };
  }

  private hslToHex(hsl: { h: number; s: number; l: number }): string {
    const h = hsl.h / 360;
    const s = hsl.s / 100;
    const l = hsl.l / 100;

    let r, g, b;

    if (s === 0) {
      r = g = b = l;
    } else {
      const hue2rgb = (p: number, q: number, t: number) => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return p + (q - p) * 6 * t;
        if (t < 1/2) return q;
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
      };

      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;

      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }

    const toHex = (x: number) => {
      const hex = Math.round(x * 255).toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    };

    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  }

  private getDefaultBranding(): AgencyBranding {
    return {
      id: '',
      agency_id: '',
      primary_color: '#6366F1',
      secondary_color: '#8B5CF6',
      accent_color: '#EC4899',
      background_color: '#FFFFFF',
      text_color: '#111827',
      font_family: 'Inter',
      font_size_base: 16,
      email_header_background: '#6366F1',
      logo_url: null,
      logo_dark_url: null,
      logo_icon_url: null,
      logo_width: null,
      logo_height: null,
      email_footer_text: null,
      email_signature: null,
      document_header_logo_url: null,
      document_footer_text: null,
      document_watermark_enabled: false,
      document_watermark_text: null,
      custom_domain: null,
      custom_domain_verified: false,
      custom_domain_ssl_until: null,
      created_at: new Date(),
      updated_at: new Date()
    };
  }

  private async clearCache(agencyId: string): Promise<void> {
    const redis = getRedisClient();
    await redis.del(`branding:${agencyId}`);
  }

  private async logBrandingChange(
    agencyId: string,
    changes: Record<string, unknown>,
    userId: string
  ): Promise<void> {
    await db.query(`
      INSERT INTO audit_log_branding (agency_id, changes, user_id)
      VALUES ($1, $2, $3)
    `, [agencyId, JSON.stringify(changes), userId]);
  }

  private async provisionSSLCertificate(agencyId: string, domain: string): Promise<void> {
    // Integrate with certificate provider (Let's Encrypt, AWS Certificate Manager, etc.)
    // This is a placeholder for the actual implementation
  }
}

interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  palette: string[];
}

interface AgencyBranding {
  id: string;
  agency_id: string;
  logo_url: string | null;
  logo_dark_url: string | null;
  logo_icon_url: string | null;
  logo_width: number | null;
  logo_height: number | null;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string;
  text_color: string;
  font_family: string;
  font_family_heading: string | null;
  font_size_base: number;
  email_header_background: string;
  email_footer_text: string | null;
  email_signature: string | null;
  document_header_logo_url: string | null;
  document_footer_text: string | null;
  document_watermark_enabled: boolean;
  document_watermark_text: string | null;
  custom_domain: string | null;
  custom_domain_verified: boolean;
  custom_domain_ssl_until: Date | null;
  created_at: Date;
  updated_at: Date;
}

interface DNSRecord {
  type: 'A' | 'CNAME' | 'TXT' | 'MX';
  name: string;
  value: string;
  priority?: number;
}
```

---

## Team & Permissions

### Team Service

```typescript
// services/team.service.ts

export class TeamService {
  /**
   * Invite team member
   */
  async inviteMember(
    agencyId: string,
    inviteData: {
      email: string;
      role: string;
      jobTitle?: string;
      department?: string;
    },
    invitedBy: string
  ): Promise<{ inviteId: string; token: string; expiresAt: Date }> {
    // Check if user already exists
    const existingUser = await db.query(
      'SELECT id FROM users WHERE email = $1',
      [inviteData.email]
    );

    let userId = existingUser.rows[0]?.id;

    // Create user if doesn't exist
    if (!userId) {
      const newUser = await db.query(
        'INSERT INTO users (email, name) VALUES ($1, $2) RETURNING id',
        [inviteData.email, inviteData.email.split('@')[0]]
      );
      userId = newUser.rows[0].id;
    }

    // Check if already member
    const existingMember = await db.query(
      'SELECT id FROM agency_agents WHERE agency_id = $1 AND user_id = $2',
      [agencyId, userId]
    );

    if (existingMember.rows.length > 0) {
      throw new Error('User is already a member of this agency');
    }

    // Get role
    const role = await db.query(
      'SELECT id FROM roles WHERE agency_id = $1 AND name = $2',
      [agencyId, inviteData.role]
    );

    if (role.rows.length === 0) {
      throw new Error(`Role "${inviteData.role}" not found`);
    }

    // Generate invite token
    const token = generateInviteToken();
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

    // Create pending membership
    const result = await db.query(`
      INSERT INTO agency_agents (
        agency_id, user_id, role_id, job_title, department,
        status, invited_by, invited_at
      ) VALUES ($1, $2, $3, $4, $5, 'pending', $6, NOW())
      RETURNING id
    `, [agencyId, userId, role.rows[0].id, inviteData.jobTitle, inviteData.department, invitedBy]);

    const inviteId = result.rows[0].id;

    // Store token
    await db.query(`
      INSERT INTO invite_tokens (id, agency_agent_id, token, expires_at)
      VALUES ($1, $2, $3, $4)
    `, [generateId(), inviteId, hashToken(token), expiresAt]);

    // Send invite email
    await this.sendInviteEmail(inviteData.email, agencyId, token);

    return { inviteId, token, expiresAt };
  }

  /**
   * Accept invitation
   */
  async acceptInvitation(token: string, userId: string): Promise<void> {
    // Find and validate token
    const inviteResult = await db.query(`
      SELECT it.*, aa.agency_id, aa.user_id as invited_user_id
      FROM invite_tokens it
      JOIN agency_agents aa ON aa.id = it.agency_agent_id
      WHERE it.token = $1 AND it.expires_at > NOW() AND it.used_at IS NULL
    `, [hashToken(token)]);

    if (inviteResult.rows.length === 0) {
      throw new Error('Invalid or expired invitation');
    }

    const invite = inviteResult.rows[0];

    // Verify user matches
    if (invite.invited_user_id !== userId) {
      throw new Error('This invitation is for a different user');
    }

    // Activate membership
    await db.query(`
      UPDATE agency_agents
      SET status = 'active', joined_at = NOW()
      WHERE id = $1
    `, [invite.agency_agent_id]);

    // Mark token as used
    await db.query(
      'UPDATE invite_tokens SET used_at = NOW() WHERE id = $1',
      [invite.id]
    );

    // Log activity
    await this.logActivity(invite.agency_id, userId, 'joined_agency');
  }

  /**
   * Update member role
   */
  async updateMemberRole(
    agencyId: string,
    agentId: string,
    newRole: string,
    updatedBy: string
  ): Promise<void> {
    // Check permissions
    const hasPermission = await this.checkPermission(
      agencyId,
      updatedBy,
      'team',
      'update_role'
    );

    if (!hasPermission) {
      throw new Error('Insufficient permissions');
    }

    // Get role
    const role = await db.query(
      'SELECT id FROM roles WHERE agency_id = $1 AND name = $2',
      [agencyId, newRole]
    );

    if (role.rows.length === 0) {
      throw new Error(`Role "${newRole}" not found`);
    }

    // Update role
    await db.query(
      'UPDATE agency_agents SET role_id = $1, updated_at = NOW() WHERE id = $2',
      [role.rows[0].id, agentId]
    );

    // Log activity
    await this.logActivity(agencyId, updatedBy, 'updated_role', {
      targetAgentId: agentId,
      newRole
    });
  }

  /**
   * Remove member
   */
  async removeMember(
    agencyId: string,
    agentId: string,
    removedBy: string
  ): Promise<void> {
    // Check permissions
    const hasPermission = await this.checkPermission(
      agencyId,
      removedBy,
      'team',
      'remove_member'
    );

    if (!hasPermission) {
      throw new Error('Insufficient permissions');
    }

    // Check if trying to remove owner
    const agent = await db.query(
      'SELECT * FROM agency_agents WHERE id = $1',
      [agentId]
    );

    if (agent.rows[0]?.role_id) {
      const role = await db.query(
        'SELECT name FROM roles WHERE id = $1',
        [agent.rows[0].role_id]
      );

      if (role.rows[0]?.name === 'Owner') {
        throw new Error('Cannot remove agency owner');
      }
    }

    // Soft delete
    await db.query(
      "UPDATE agency_agents SET status = 'removed', updated_at = NOW() WHERE id = $1",
      [agentId]
    );

    // Log activity
    await this.logActivity(agencyId, removedBy, 'removed_member', {
      targetAgentId: agentId
    });
  }

  /**
   * Check user permission
   */
  async checkPermission(
    agencyId: string,
    userId: string,
    resource: string,
    action: string
  ): Promise<boolean> {
    const result = await db.query(`
      SELECT EXISTS(
        SELECT 1
        FROM agency_agents aa
        JOIN roles r ON r.id = aa.role_id
        JOIN role_permissions rp ON rp.role_id = r.id
        JOIN permissions p ON p.id = rp.permission_id
        WHERE aa.agency_id = $1
          AND aa.user_id = $2
          AND aa.status = 'active'
          AND p.resource = $3
          AND p.action = $4
      ) OR EXISTS(
        SELECT 1
        FROM agency_owners ao
        WHERE ao.agency_id = $1 AND ao.user_id = $2
      ) as has_permission
    `, [agencyId, userId, resource, action]);

    return result.rows[0].has_permission;
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(
    agencyId: string,
    userId: string
  ): Promise<Permission[]> {
    const result = await db.query(`
      SELECT DISTINCT p.resource, p.action, p.description
      FROM agency_agents aa
      JOIN roles r ON r.id = aa.role_id
      JOIN role_permissions rp ON rp.role_id = r.id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE aa.agency_id = $1
        AND aa.user_id = $2
        AND aa.status = 'active'
      ORDER BY p.resource, p.action
    `, [agencyId, userId]);

    return result.rows;
  }

  /**
   * Create custom role
   */
  async createRole(
    agencyId: string,
    roleData: {
      name: string;
      description?: string;
      permissions: Array<{ resource: string; action: string }>;
    },
    createdBy: string
  ): Promise<Role> {
    // Check permission
    const hasPermission = await this.checkPermission(
      agencyId,
      createdBy,
      'roles',
      'create'
    );

    if (!hasPermission) {
      throw new Error('Insufficient permissions');
    }

    // Create role
    const result = await db.query(`
      INSERT INTO roles (agency_id, name, description)
      VALUES ($1, $2, $3)
      RETURNING *
    `, [agencyId, roleData.name, roleData.description]);

    const role = result.rows[0];

    // Assign permissions
    for (const perm of roleData.permissions) {
      await db.query(`
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT $1, id FROM permissions WHERE resource = $2 AND action = $3
      `, [role.id, perm.resource, perm.action]);
    }

    return role;
  }

  /**
   * Update role permissions
   */
  async updateRolePermissions(
    agencyId: string,
    roleId: string,
    permissions: Array<{ resource: string; action: string }>,
    updatedBy: string
  ): Promise<void> {
    // Check permission
    const hasPermission = await this.checkPermission(
      agencyId,
      updatedBy,
      'roles',
      'update'
    );

    if (!hasPermission) {
      throw new Error('Insufficient permissions');
    }

    // Remove existing permissions
    await db.query(
      'DELETE FROM role_permissions WHERE role_id = $1',
      [roleId]
    );

    // Add new permissions
    for (const perm of permissions) {
      await db.query(`
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT $1, id FROM permissions WHERE resource = $2 AND action = $3
        ON CONFLICT DO NOTHING
      `, [roleId, perm.resource, perm.action]);
    }
  }

  /**
   * Get team members
   */
  async getTeamMembers(
    agencyId: string,
    filters?: {
      status?: string;
      role?: string;
      department?: string;
    }
  ): Promise<TeamMember[]> {
    const conditions: string[] = ['aa.agency_id = $1'];
    const values: unknown[] = [agencyId];
    let paramIndex = 2;

    if (filters?.status) {
      conditions.push(`aa.status = $${paramIndex++}`);
      values.push(filters.status);
    }

    if (filters?.role) {
      conditions.push(`r.name = $${paramIndex++}`);
      values.push(filters.role);
    }

    if (filters?.department) {
      conditions.push(`aa.department = $${paramIndex++}`);
      values.push(filters.department);
    }

    const whereClause = conditions.join(' AND ');

    const result = await db.query(`
      SELECT
        aa.id,
        aa.user_id,
        aa.job_title,
        aa.department,
        aa.status,
        aa.invited_at,
        aa.joined_at,
        aa.last_active_at,
        r.name as role_name,
        u.name,
        u.email,
        u.avatar_url
      FROM agency_agents aa
      JOIN users u ON u.id = aa.user_id
      LEFT JOIN roles r ON r.id = aa.role_id
      WHERE ${whereClause}
      ORDER BY aa.created_at DESC
    `, values);

    return result.rows;
  }

  private async sendInviteEmail(
    email: string,
    agencyId: string,
    token: string
  ): Promise<void> {
    const agency = await db.query(
      'SELECT name FROM agencies WHERE id = $1',
      [agencyId]
    );

    const inviteUrl = `${process.env.APP_URL}/invite/${token}`;

    // Send email using communication service
    // This is a placeholder
  }

  private async logActivity(
    agencyId: string,
    userId: string,
    action: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    await db.query(`
      INSERT INTO audit_log_team (agency_id, user_id, action, metadata)
      VALUES ($1, $2, $3, $4)
    `, [agencyId, userId, action, metadata ? JSON.stringify(metadata) : null]);
  }
}

interface TeamMember {
  id: string;
  user_id: string;
  name: string;
  email: string;
  avatar_url: string;
  job_title: string;
  department: string;
  role_name: string;
  status: string;
  invited_at: Date;
  joined_at: Date;
  last_active_at: Date;
}

interface Permission {
  resource: string;
  action: string;
  description: string;
}

interface Role {
  id: string;
  agency_id: string;
  name: string;
  description: string;
  created_at: Date;
}

function generateInviteToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

function hashToken(token: string): string {
  return crypto.createHash('sha256').update(token).digest('hex');
}

function generateId(): string {
  return crypto.randomUUID();
}
```

---

## API Specification

### Settings Endpoints

#### GET /api/settings

Get all agency settings.

**Response:**
```json
{
  "general": {
    "agencyName": "ABC Travels",
    "agencyEmail": "contact@abctravels.com",
    "agencyPhone": "+91 98765 43210",
    "agencyWebsite": "https://abctravels.com",
    "address": {
      "line1": "123 Main Street",
      "city": "Mumbai",
      "state": "Maharashtra",
      "postalCode": "400001",
      "country": "IN"
    },
    "gstNumber": "27ABCDE1234F1Z5",
    "panNumber": "ABCDE1234F"
  },
  "preferences": {
    "currency": "INR",
    "timezone": "Asia/Kolkata",
    "language": "en",
    "dateFormat": "DD/MM/YYYY",
    "timeFormat": "12h",
    "numberFormat": "indian",
    "firstDayOfWeek": 1
  },
  "notifications": {
    "email": {
      "newInquiry": true,
      "bookingConfirmed": true,
      "paymentReceived": true,
      "dailySummary": false
    },
    "push": {
      "enabled": true,
      "newMessage": true,
      "tripUpdate": true
    },
    "sms": {
      "enabled": false,
      "urgentOnly": true
    }
  },
  "branding": {
    "logoUrl": "https://s3.../logo.png",
    "primaryColor": "#6366F1",
    "secondaryColor": "#8B5CF6",
    "fontFamily": "Inter"
  }
}
```

#### PATCH /api/settings/:category

Update settings in a category.

**Request:**
```json
{
  "agencyPhone": "+91 98765 43210",
  "gstNumber": "27XYZWA5678F1Z5"
}
```

#### POST /api/settings/branding/logo

Upload agency logo.

**Request:** multipart/form-data
- `file`: Image file
- `variant`: 'light' | 'dark' | 'icon' (optional)

**Response:**
```json
{
  "url": "https://s3.../logo.png",
  "width": 400,
  "height": 200
}
```

### Team Endpoints

#### GET /api/team/members

Get team members.

**Query Parameters:**
- `status`: Filter by status
- `role`: Filter by role
- `department`: Filter by department

#### POST /api/team/invite

Invite new team member.

**Request:**
```json
{
  "email": "newmember@example.com",
  "role": "Agent",
  "jobTitle": "Travel Consultant",
  "department": "Leisure"
}
```

**Response:**
```json
{
  "inviteId": "uuid",
  "token": "invite-token",
  "expiresAt": "2026-05-02T10:00:00Z"
}
```

#### PATCH /api/team/members/:agentId/role

Update member role.

**Request:**
```json
{
  "role": "Senior Agent"
}
```

#### DELETE /api/team/members/:agentId

Remove team member.

#### GET /api/team/roles

Get all roles.

#### POST /api/team/roles

Create custom role.

**Request:**
```json
{
  "name": "Custom Agent",
  "description": "Agent with limited permissions",
  "permissions": [
    { "resource": "trips", "action": "read" },
    { "resource": "customers", "action": "read" },
    { "resource": "messages", "action": "create" }
  ]
}
```

#### GET /api/team/permissions

Get current user's permissions.

**Response:**
```json
{
  "permissions": [
    { "resource": "trips", "action": "create", "description": "Create new trips" },
    { "resource": "trips", "action": "read", "description": "View trips" },
    { "resource": "trips", "action": "update", "description": "Update trips" },
    { "resource": "messages", "action": "send", "description": "Send messages" }
  ]
}
```

---

## Summary

The Agency Settings technical architecture provides:

1. **Flexible Configuration System**: Hierarchical settings with default, agency, and user levels
2. **Comprehensive Branding**: Logo management, color theming, custom domains
3. **Team Management**: Role-based access control with granular permissions
4. **Validation & Caching**: Type-safe settings with performance optimization
5. **Audit Logging**: Full change tracking for compliance
6. **Multi-Tenancy Ready**: Isolated settings per agency

---

**Next:** Agency Settings UX/UI Deep Dive (AGENCY_SETTINGS_02) — settings interface design, navigation patterns, and user experience
