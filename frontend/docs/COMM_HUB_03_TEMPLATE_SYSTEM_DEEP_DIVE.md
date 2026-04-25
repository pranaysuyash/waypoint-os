# Communication Hub — Template System Deep Dive

> Part 3 of 4 in Communication Hub Exploration Series

---

## Document Overview

**Series:** Communication Hub
**Part:** 3 — Template System
**Status:** Complete
**Last Updated:** 2026-04-24

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Template Architecture](#template-architecture)
3. [Variable System](#variable-system)
4. [Template Engine](#template-engine)
5. [Localization](#localization)
6. [Template Management](#template-management)
7. [Preview & Testing](#preview--testing)
8. [Template Categories](#template-categories)

---

## System Overview

### What Are Templates?

Templates are reusable message patterns with placeholders for dynamic content. They enable:

- **Consistency**: Standardized communication across the agency
- **Efficiency**: Send common messages without typing
- **Personalization**: Dynamic content insertion while maintaining structure
- **Compliance**: Approved messaging with regulatory compliance

### Template Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TEMPLATE LIFECYCLE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐          │
│  │  CREATE  │────▶│  APPROVE │────▶│  PUBLISH │────▶│  ACTIVE  │          │
│  └──────────┘     └──────────┘     └──────────┘     └──────────┘          │
│       │                                  │                                 │
│       │                                  ▼                                 │
│       │                           ┌──────────┐                             │
│       └───────────────────────────│ ARCHIVED │                             │
│           (on replacement)         └──────────┘                             │
│                                                                             │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                            │
│  │   DRAFT  │────▶  VERSION  │────▶  HISTORY  │                            │
│  └──────────┘     └──────────┘     └──────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Template Types by Channel

| Channel | Template Support | Unique Features |
|---------|------------------|-----------------|
| **WhatsApp** | ✅ Yes | Media templates, button templates, list templates |
| **Email** | ✅ Yes | HTML support, attachments, dynamic sections |
| **SMS** | ⚠️ Limited | Text only, 160 char limit |
| **In-App** | ✅ Yes | Rich formatting, action buttons |

---

## Template Architecture

### Database Schema

```sql
-- migrations/XXX_create_message_templates_table.sql

CREATE TABLE message_templates (
  -- Primary identification
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,

  -- Template metadata
  name VARCHAR(255) NOT NULL,
  code VARCHAR(100) NOT NULL,
  description TEXT,
  category VARCHAR(100),

  -- Channel specificity
  channel VARCHAR(20) NOT NULL CHECK (channel IN ('whatsapp', 'email', 'sms', 'in_app')),

  -- Content
  subject_template VARCHAR(500),
  content_template TEXT NOT NULL,
  html_template TEXT, -- For email

  -- Localization
  language VARCHAR(10) DEFAULT 'en',
  region VARCHAR(10),

  -- Variable definition
  variables JSONB DEFAULT '[]',
  -- Format: [{"name": "customerName", "type": "string", "required": true, "defaultValue": "", "description": ""}]

  -- Template-specific settings
  settings JSONB DEFAULT '{}',
  -- For WhatsApp: {"templateType": "text", "category": "marketing"}
  -- For Email: {"preheader": "", "senderName": "", "replyTo": ""}

  -- Approval workflow
  status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_approval', 'active', 'archived')),
  approved_by UUID REFERENCES users(id),
  approved_at TIMESTAMPTZ,
  version INTEGER DEFAULT 1,

  -- Usage analytics
  usage_count INTEGER DEFAULT 0,
  last_used_at TIMESTAMPTZ,

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_template_code UNIQUE(agency_id, code, language, version)
);

-- Indexes
CREATE INDEX idx_templates_agency_category ON message_templates(agency_id, category, status);
CREATE INDEX idx_templates_channel_language ON message_templates(channel, language, status);
CREATE INDEX idx_templates_usage ON message_templates(usage_count DESC) WHERE status = 'active';

-- Template versions history
CREATE TABLE message_template_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES message_templates(id) ON DELETE CASCADE,

  version INTEGER NOT NULL,
  content_template TEXT NOT NULL,
  subject_template VARCHAR(500),
  variables JSONB DEFAULT '[]',

  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_version UNIQUE(template_id, version)
);

-- Template usage log
CREATE TABLE message_template_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES message_templates(id) ON DELETE CASCADE,
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,

  variables_used JSONB NOT NULL, -- Snapshot of variables used
  rendered_content TEXT NOT NULL, -- Final rendered content

  used_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_template_usage_template ON message_template_usage(template_id, used_at DESC);
CREATE INDEX idx_template_usage_message ON message_template_usage(message_id);
```

### TypeScript Interfaces

```typescript
// types/template.types.ts

export interface MessageTemplate {
  id: string;
  agencyId: string;
  name: string;
  code: string;
  description?: string;
  category: TemplateCategory;
  channel: Channel;
  subjectTemplate?: string;
  contentTemplate: string;
  htmlTemplate?: string;
  language: string;
  region?: string;
  variables: TemplateVariable[];
  settings: TemplateSettings;
  status: TemplateStatus;
  approvedBy?: string;
  approvedAt?: Date;
  version: number;
  usageCount: number;
  lastUsedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export enum TemplateCategory {
  BOOKING = 'booking',
  PAYMENT = 'payment',
  ITINERARY = 'itinerary',
  CONFIRMATION = 'confirmation',
  REMINDER = 'reminder',
  PROMOTIONAL = 'promotional',
  SUPPORT = 'support',
  DOCUMENT = 'document',
  FEEDBACK = 'feedback',
  CUSTOM = 'custom'
}

export enum TemplateStatus {
  DRAFT = 'draft',
  PENDING_APPROVAL = 'pending_approval',
  ACTIVE = 'active',
  ARCHIVED = 'archived'
}

export enum Channel {
  WHATSAPP = 'whatsapp',
  EMAIL = 'email',
  SMS = 'sms',
  IN_APP = 'in_app'
}

export interface TemplateVariable {
  name: string;
  type: VariableType;
  required: boolean;
  defaultValue?: unknown;
  description?: string;
  validation?: VariableValidation;
}

export enum VariableType {
  STRING = 'string',
  NUMBER = 'number',
  DATE = 'date',
  BOOLEAN = 'boolean',
  ARRAY = 'array',
  OBJECT = 'object',
  URL = 'url',
  EMAIL = 'email',
  PHONE = 'phone',
  CURRENCY = 'currency'
}

export interface VariableValidation {
  min?: number;
  max?: number;
  pattern?: string;
  enum?: unknown[];
  customValidation?: string; // JavaScript expression
}

export interface TemplateSettings {
  // WhatsApp specific
  whatsappTemplateType?: 'text' | 'media' | 'interactive';
  whatsappCategory?: 'marketing' | 'utility' | 'authentication';
  whatsappButtons?: Array<{
    type: 'quick_reply' | 'url';
    text: string;
    url?: string;
  }>;

  // Email specific
  emailPreheader?: string;
  emailSenderName?: string;
  emailReplyTo?: string;
  emailLayout?: 'simple' | 'formatted' | 'custom';

  // Common
  trackOpens?: boolean;
  trackClicks?: boolean;
  allowSchedule?: boolean;
}

export interface TemplateVersion {
  id: string;
  templateId: string;
  version: number;
  contentTemplate: string;
  subjectTemplate?: string;
  variables: TemplateVariable[];
  createdBy: string;
  createdAt: Date;
}

export interface TemplateUsage {
  id: string;
  templateId: string;
  messageId: string;
  variablesUsed: Record<string, unknown>;
  renderedContent: string;
  usedAt: Date;
}

export interface CreateTemplateRequest {
  name: string;
  code: string;
  description?: string;
  category: TemplateCategory;
  channel: Channel;
  subjectTemplate?: string;
  contentTemplate: string;
  htmlTemplate?: string;
  language?: string;
  region?: string;
  variables: TemplateVariable[];
  settings?: TemplateSettings;
}

export interface UpdateTemplateRequest extends Partial<CreateTemplateRequest> {
  version?: number; // For optimistic locking
}

export interface RenderTemplateRequest {
  templateId: string;
  variables: Record<string, unknown>;
  previewMode?: boolean;
}

export interface RenderTemplateResponse {
  subject?: string;
  content: string;
  html?: string;
  missingVariables: string[];
  validationErrors: ValidationError[];
}
```

---

## Variable System

### Variable Types and Validation

```typescript
// services/template-variable.service.ts

export class TemplateVariableService {
  /**
   * Validate variable value against its definition
   */
  validateVariable(
    variable: TemplateVariable,
    value: unknown
  ): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Check required
    if (variable.required && (value === undefined || value === null || value === '')) {
      errors.push(`${variable.name} is required`);
      return { valid: false, errors };
    }

    // Skip validation if not required and no value provided
    if (!variable.required && (value === undefined || value === null)) {
      return { valid: true, errors: [] };
    }

    // Type validation
    switch (variable.type) {
      case VariableType.STRING:
        if (typeof value !== 'string') {
          errors.push(`${variable.name} must be a string`);
        }
        break;

      case VariableType.NUMBER:
        if (typeof value !== 'number' || isNaN(value)) {
          errors.push(`${variable.name} must be a number`);
        }
        break;

      case VariableType.BOOLEAN:
        if (typeof value !== 'boolean') {
          errors.push(`${variable.name} must be a boolean`);
        }
        break;

      case VariableType.DATE:
        if (!(value instanceof Date) && typeof value !== 'string') {
          errors.push(`${variable.name} must be a date`);
        }
        break;

      case VariableType.ARRAY:
        if (!Array.isArray(value)) {
          errors.push(`${variable.name} must be an array`);
        }
        break;

      case VariableType.URL:
        try {
          new URL(value as string);
        } catch {
          errors.push(`${variable.name} must be a valid URL`);
        }
        break;

      case VariableType.EMAIL:
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value as string)) {
          errors.push(`${variable.name} must be a valid email`);
        }
        break;

      case VariableType.PHONE:
        const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
        if (!phoneRegex.test(value as string)) {
          errors.push(`${variable.name} must be a valid phone number`);
        }
        break;

      case VariableType.CURRENCY:
        if (typeof value !== 'number' || value < 0) {
          errors.push(`${variable.name} must be a positive number`);
        }
        break;
    }

    // Additional validation rules
    if (variable.validation) {
      const validationErrors = this.validateWithRules(
        variable.name,
        value,
        variable.validation
      );
      errors.push(...validationErrors);
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate against custom validation rules
   */
  private validateWithRules(
    name: string,
    value: unknown,
    validation: VariableValidation
  ): string[] {
    const errors: string[] = [];

    // Min/max for numbers and strings
    if (validation.min !== undefined) {
      if (typeof value === 'number' && value < validation.min) {
        errors.push(`${name} must be at least ${validation.min}`);
      }
      if (typeof value === 'string' && value.length < validation.min) {
        errors.push(`${name} must be at least ${validation.min} characters`);
      }
      if (Array.isArray(value) && value.length < validation.min) {
        errors.push(`${name} must have at least ${validation.min} items`);
      }
    }

    if (validation.max !== undefined) {
      if (typeof value === 'number' && value > validation.max) {
        errors.push(`${name} must be at most ${validation.max}`);
      }
      if (typeof value === 'string' && value.length > validation.max) {
        errors.push(`${name} must be at most ${validation.max} characters`);
      }
      if (Array.isArray(value) && value.length > validation.max) {
        errors.push(`${name} must have at most ${validation.max} items`);
      }
    }

    // Pattern validation
    if (validation.pattern && typeof value === 'string') {
      const regex = new RegExp(validation.pattern);
      if (!regex.test(value)) {
        errors.push(`${name} format is invalid`);
      }
    }

    // Enum validation
    if (validation.enum && !validation.enum.includes(value)) {
      errors.push(`${name} must be one of: ${validation.enum.join(', ')}`);
    }

    // Custom validation (JavaScript expression)
    if (validation.customValidation) {
      try {
        // Safe evaluation of custom validation
        const isValid = this.evaluateCustomValidation(
          validation.customValidation,
          value
        );
        if (!isValid) {
          errors.push(`${name} failed custom validation`);
        }
      } catch (error) {
        errors.push(`${name} custom validation error: ${error.message}`);
      }
    }

    return errors;
  }

  /**
   * Safely evaluate custom validation expression
   */
  private evaluateCustomValidation(expression: string, value: unknown): boolean {
    // Create a restricted execution context
    const sandbox = {
      value,
      result: false
    };

    // Basic sanitization - only allow specific operations
    const sanitized = expression
      .replace(/[^a-zA-Z0-9_\s\.\(\)\[\]\{\}\+\-\*\/\=\!\&\|\>\<\?\:]/g, '');

    // Use Function constructor with restricted scope
    const fn = new Function('value', `return ${sanitized}`);
    return fn(value);
  }

  /**
   * Get default value for a variable
   */
  getDefaultValue(variable: TemplateVariable): unknown {
    if (variable.defaultValue !== undefined) {
      return variable.defaultValue;
    }

    // Type-based defaults
    switch (variable.type) {
      case VariableType.STRING:
        return '';
      case VariableType.NUMBER:
      case VariableType.CURRENCY:
        return 0;
      case VariableType.BOOLEAN:
        return false;
      case VariableType.ARRAY:
        return [];
      case VariableType.OBJECT:
        return {};
      case VariableType.DATE:
        return new Date();
      default:
        return null;
    }
  }

  /**
   * Extract variables from template content
   */
  extractVariables(content: string): string[] {
    const pattern = /\{\{(\w+)\}\}/g;
    const variables = new Set<string>();
    let match;

    while ((match = pattern.exec(content)) !== null) {
      variables.add(match[1]);
    }

    return Array.from(variables);
  }

  /**
   * Get missing required variables
   */
  getMissingVariables(
    template: MessageTemplate,
    providedVariables: Record<string, unknown>
  ): string[] {
    return template.variables
      .filter(v => v.required && !(v.name in providedVariables))
      .map(v => v.name);
  }
}
```

### Built-in Variable Helpers

```typescript
// services/template-helpers.ts

/**
 * Helper functions available in templates
 */
export const templateHelpers = {
  // String manipulation
  uppercase: (value: string) => value?.toUpperCase(),
  lowercase: (value: string) => value?.toLowerCase(),
  capitalize: (value: string) => value?.charAt(0).toUpperCase() + value?.slice(1),
  titleCase: (value: string) => value?.replace(/\w\S*/g, txt => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()),
  truncate: (value: string, length: number = 50) => value?.length > length ? value.substring(0, length) + '...' : value,

  // Date formatting
  formatDate: (value: Date | string, format: string = 'PPP') => {
    return formatDate(value, format);
  },
  formatTime: (value: Date | string) => format(value, 'HH:mm'),
  formatRelative: (value: Date | string) => formatRelative(value, new Date()),
  addDays: (value: Date | string, days: number) => addDays(new Date(value), days),

  // Number formatting
  formatCurrency: (value: number, currency: string = 'INR') => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency
    }).format(value);
  },
  formatNumber: (value: number, locale: string = 'en-IN') => {
    return new Intl.NumberFormat(locale).format(value);
  },
  formatPercent: (value: number, decimals: number = 1) => `${value.toFixed(decimals)}%`,

  // Array manipulation
  first: (arr: unknown[]) => arr?.[0],
  last: (arr: unknown[]) => arr?.[arr.length - 1],
  join: (arr: unknown[], separator: string = ', ') => arr?.join(separator),

  // Conditional
  if: (condition: boolean, ifTrue: unknown, ifFalse: unknown) => condition ? ifTrue : ifFalse,
  equals: (a: unknown, b: unknown) => a === b,
  and: (...values: unknown[]) => values.every(v => !!v),
  or: (...values: unknown[]) => values.some(v => !!v),

  // Links
  link: (text: string, url: string) => `<a href="${url}">${text}</a>`,
  tel: (phone: string, text?: string) => `<a href="tel:${phone}">${text || phone}</a>`,
  mailto: (email: string, text?: string) => `<a href="mailto:${email}">${text || email}</a>`,

  // Trip specific
  nights: (checkIn: Date | string, checkOut: Date | string) => {
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
  },

  // Customer specific
  displayName: (customer: { firstName?: string; lastName?: string; name?: string }) => {
    if (customer.firstName && customer.lastName) {
      return `${customer.firstName} ${customer.lastName}`;
    }
    return customer.name || '';
  },

  // Document specific
  documentLink: (documentId: string, text: string = 'View Document') => {
    return `<a href="${process.env.APP_URL}/documents/${documentId}">${text}</a>`;
  },

  // Payment specific
  paymentLink: (paymentId: string, text: string = 'Pay Now') => {
    return `<a href="${process.env.APP_URL}/payment/${paymentId}">${text}</a>`;
  }
};

/**
 * Extend template context with helpers
 */
export function extendContextWithContext(
  context: Record<string, unknown>
): Record<string, unknown> {
  return {
    ...context,
    ...templateHelpers,
    // Aliases for convenience
    upper: templateHelpers.uppercase,
    lower: templateHelpers.lowercase,
    cap: templateHelpers.capitalize,
    currency: templateHelpers.formatCurrency,
    date: templateHelpers.formatDate
  };
}
```

---

## Template Engine

### Core Template Engine

```typescript
// services/template-engine.service.ts

import { MessageTemplate, RenderTemplateRequest, RenderTemplateResponse } from '../types/template.types';
import { TemplateVariableService } from './template-variable.service';
import { extendContextWithContext } from './template-helpers';

export class TemplateEngineService {
  private variableService: TemplateVariableService;

  constructor() {
    this.variableService = new TemplateVariableService();
  }

  /**
   * Render template with provided variables
   */
  async render(request: RenderTemplateRequest): Promise<RenderTemplateResponse> {
    // Get template
    const template = await this.getTemplate(request.templateId);
    if (!template) {
      throw new Error('Template not found');
    }

    // Extend context with helpers
    const context = extendContextWithContext(request.variables);

    // Validate variables
    const validationErrors = this.validateAllVariables(template, context);
    const missingVariables = this.variableService.getMissingVariables(
      template,
      request.variables
    );

    // Render content
    const content = this.renderString(template.contentTemplate, context);

    // Render subject if exists
    let subject: string | undefined;
    if (template.subjectTemplate) {
      subject = this.renderString(template.subjectTemplate, context);
    }

    // Render HTML for email
    let html: string | undefined;
    if (template.htmlTemplate) {
      html = this.renderString(template.htmlTemplate, context);
    }

    return {
      subject,
      content,
      html,
      missingVariables,
      validationErrors
    };
  }

  /**
   * Render a template string with context
   */
  renderString(template: string, context: Record<string, unknown>): string {
    // Handle simple variable substitution {{variable}}
    let result = template.replace(/\{\{(\w+)\}\}/g, (_, key) => {
      return this.getNestedValue(context, key) ?? '';
    });

    // Handle function calls {{helperName(arg1, arg2)}}
    result = result.replace(/\{\{(\w+)\(([^)]*)\)\}\}/g, (_, func, args) => {
      const helper = this.getNestedValue(context, func);
      if (typeof helper === 'function') {
        const argList = this.parseArguments(args, context);
        try {
          return String(helper(...argList));
        } catch (error) {
          console.error(`Template helper error: ${func}`, error);
          return '';
        }
      }
      return '';
    });

    // Handle conditionals {{#if condition}}...{{/if}}
    result = this.renderConditionals(result, context);

    // Handle loops {{#each items}}...{{/each}}
    result = this.renderLoops(result, context);

    return result;
  }

  /**
   * Render conditional blocks
   */
  private renderConditionals(
    template: string,
    context: Record<string, unknown>
  ): string {
    const ifPattern = /\{\{#if\s+(\w+)\}\}([\s\S]*?)\{\{\/if\}\}/g;

    return template.replace(ifPattern, (_, condition, content) => {
      const value = this.getNestedValue(context, condition);
      return value ? content : '';
    });
  }

  /**
   * Render loop blocks
   */
  private renderLoops(
    template: string,
    context: Record<string, unknown>
  ): string {
    const eachPattern = /\{\{#each\s+(\w+)\}\}([\s\S]*?)\{\{\/each\}\}/g;

    return template.replace(eachPattern, (_, arrayKey, itemTemplate) => {
      const array = this.getNestedValue(context, arrayKey);

      if (!Array.isArray(array)) {
        return '';
      }

      return array.map((item, index) => {
        let itemResult = itemTemplate;

        // Replace {{this}} with current item
        itemResult = itemResult.replace(/\{\{this\}\}/g, String(item));

        // Replace {{@index}} with current index
        itemResult = itemResult.replace(/\{\{@index\}\}/g, String(index));

        // Allow nested property access {{this.property}}
        itemResult = itemResult.replace(/\{\{this\.(\w+)\}\}/g, (_, prop) => {
          return String(item[prop] ?? '');
        });

        return itemResult;
      }).join('');
    });
  }

  /**
   * Get nested value from context (supports dot notation)
   */
  private getNestedValue(context: Record<string, unknown>, path: string): unknown {
    const parts = path.split('.');
    let value: unknown = context;

    for (const part of parts) {
      if (value && typeof value === 'object' && part in value) {
        value = (value as Record<string, unknown>)[part];
      } else {
        return undefined;
      }
    }

    return value;
  }

  /**
   * Parse function arguments from template
   */
  private parseArguments(
    argsString: string,
    context: Record<string, unknown>
  ): unknown[] {
    if (!argsString.trim()) {
      return [];
    }

    // Simple argument parser (handles strings, numbers, and variables)
    const args: unknown[] = [];
    const pattern = /(['"])(.*?)\1|(\w+)|(\d+(?:\.\d+)?)/g;
    let match;

    while ((match = pattern.exec(argsString)) !== null) {
      if (match[2] !== undefined) {
        // String literal
        args.push(match[2]);
      } else if (match[3] !== undefined) {
        // Variable reference
        args.push(this.getNestedValue(context, match[3]));
      } else if (match[4] !== undefined) {
        // Number literal
        args.push(parseFloat(match[4]));
      }
    }

    return args;
  }

  /**
   * Validate all variables for template
   */
  private validateAllVariables(
    template: MessageTemplate,
    context: Record<string, unknown>
  ): Array<{ variable: string; errors: string[] }> {
    const errors: Array<{ variable: string; errors: string[] }> = [];

    for (const variable of template.variables) {
      const value = this.getNestedValue(context, variable.name);
      const validation = this.variableService.validateVariable(variable, value);

      if (!validation.valid) {
        errors.push({
          variable: variable.name,
          errors: validation.errors
        });
      }
    }

    return errors;
  }

  /**
   * Get template from database
   */
  private async getTemplate(templateId: string): Promise<MessageTemplate | null> {
    const result = await db.query(
      'SELECT * FROM message_templates WHERE id = $1',
      [templateId]
    );

    return result.rows[0] || null;
  }

  /**
   * Preview template with sample data
   */
  async preview(templateId: string): Promise<{
    subject?: string;
    content: string;
    sampleVariables: Record<string, unknown>;
  }> {
    const template = await this.getTemplate(templateId);
    if (!template) {
      throw new Error('Template not found');
    }

    // Generate sample data
    const sampleVariables = this.generateSampleData(template);

    // Render with sample data
    const result = await this.render({
      templateId,
      variables: sampleVariables,
      previewMode: true
    });

    return {
      subject: result.subject,
      content: result.content,
      sampleVariables
    };
  }

  /**
   * Generate sample data for template preview
   */
  private generateSampleData(template: MessageTemplate): Record<string, unknown> {
    const sample: Record<string, unknown> = {};

    for (const variable of template.variables) {
      switch (variable.type) {
        case VariableType.STRING:
          sample[variable.name] = variable.defaultValue || 'Sample Text';
          break;

        case VariableType.NUMBER:
          sample[variable.name] = variable.defaultValue || 100;
          break;

        case VariableType.CURRENCY:
          sample[variable.name] = variable.defaultValue || 25000;
          break;

        case VariableType.DATE:
          sample[variable.name] = variable.defaultValue || new Date();
          break;

        case VariableType.BOOLEAN:
          sample[variable.name] = variable.defaultValue ?? true;
          break;

        case VariableType.ARRAY:
          sample[variable.name] = variable.defaultValue || ['Item 1', 'Item 2'];
          break;

        case VariableType.EMAIL:
          sample[variable.name] = variable.defaultValue || 'john@example.com';
          break;

        case VariableType.PHONE:
          sample[variable.name] = variable.defaultValue || '+91 98765 43210';
          break;

        case VariableType.URL:
          sample[variable.name] = variable.defaultValue || 'https://example.com';
          break;

        default:
          sample[variable.name] = variable.defaultValue || null;
      }
    }

    return sample;
  }
}
```

### WhatsApp Template Special Handler

```typescript
// services/whatsapp-template.service.ts

/**
 * WhatsApp Business API has specific template requirements
 * This service handles WhatsApp-specific template formatting
 */
export class WhatsAppTemplateService {
  /**
   * Convert internal template to WhatsApp format
   */
  toWhatsAppTemplate(template: MessageTemplate): WhatsAppTemplate {
    const components: WhatsAppComponent[] = [];

    // Header component (for media templates)
    if (template.settings.whatsappTemplateType === 'media') {
      components.push({
        type: 'HEADER',
        format: 'TEXT',
        text: this.extractHeaderText(template.contentTemplate)
      });
    }

    // Body component
    components.push({
      type: 'BODY',
      text: this.sanitizeContent(template.contentTemplate)
    });

    // Button components
    if (template.settings.whatsappButtons?.length) {
      for (const button of template.settings.whatsappButtons) {
        if (button.type === 'quick_reply') {
          components.push({
            type: 'BUTTON',
            subType: 'QUICK_REPLY',
            text: button.text
          });
        } else if (button.type === 'url') {
          components.push({
            type: 'BUTTON',
            subType: 'URL',
            text: button.text,
            url: button.url || ''
          });
        }
      }
    }

    return {
      name: template.code,
      category: template.settings.whatsappCategory || 'marketing',
      language: template.language.toUpperCase(),
      components
    };
  }

  /**
   * Sanitize content for WhatsApp (remove unsupported formatting)
   */
  private sanitizeContent(content: string): string {
    // WhatsApp supports basic formatting: *bold*, _italic_, ~strikethrough~, ```monospace```
    return content
      .replace(/\*\*(.+?)\*\*/g, '*$1*') // Convert ** to *
      .replace(/__(.+?)__/g, '_$1_') // Convert __ to _
      .replace(/~~(.+?)~~/g, '~$1~') // Convert ~~ to ~
      .replace(/`{3}([\s\S]+?)`{3}/g, '```$1```'); // Preserve ```
  }

  /**
   * Extract header text from template
   */
  private extractHeaderText(content: string): string {
    const lines = content.split('\n');
    const firstLine = lines[0]?.trim();

    // If first line is short and distinct, use it as header
    if (firstLine && firstLine.length < 60) {
      return firstLine;
    }

    return '';
  }

  /**
   * Format variables for WhatsApp API
   */
  formatVariables(variables: Record<string, unknown>): WhatsAppParameter[] {
    return Object.entries(variables).map(([key, value]) => ({
      type: this.getParameterType(value),
      text: String(value)
    }));
  }

  private getParameterType(value: unknown): 'text' | 'currency' | 'date_time' {
    if (typeof value === 'number') {
      return 'currency';
    }
    if (value instanceof Date) {
      return 'date_time';
    }
    return 'text';
  }
}

interface WhatsAppTemplate {
  name: string;
  category: string;
  language: string;
  components: WhatsAppComponent[];
}

interface WhatsAppComponent {
  type: 'HEADER' | 'BODY' | 'BUTTON' | 'FOOTER';
  format?: 'TEXT' | 'IMAGE' | 'VIDEO' | 'DOCUMENT' | 'LOCATION';
  text?: string;
  subType?: 'QUICK_REPLY' | 'URL';
  url?: string;
}

interface WhatsAppParameter {
  type: 'text' | 'currency' | 'date_time';
  text: string;
}
```

---

## Localization

### Multi-Language Template Support

```typescript
// services/template-localization.service.ts

export class TemplateLocalizationService {
  /**
   * Get template for specific language
   */
  async getTemplateForLanguage(
    templateCode: string,
    language: string,
    agencyId: string
  ): Promise<MessageTemplate | null> {
    // Try to get exact language match
    let result = await db.query(`
      SELECT * FROM message_templates
      WHERE code = $1 AND language = $2 AND agency_id = $3 AND status = 'active'
      ORDER BY version DESC
      LIMIT 1
    `, [templateCode, language, agencyId]);

    // If not found, try fallback to base language (en)
    if (result.rows.length === 0 && language !== 'en') {
      result = await db.query(`
        SELECT * FROM message_templates
        WHERE code = $1 AND language = 'en' AND agency_id = $2 AND status = 'active'
        ORDER BY version DESC
        LIMIT 1
      `, [templateCode, agencyId]);
    }

    return result.rows[0] || null;
  }

  /**
   * Get all available languages for a template
   */
  async getAvailableLanguages(templateCode: string, agencyId: string): Promise<{
    code: string;
    name: string;
    nativeName: string;
  }[]> {
    const result = await db.query(`
      SELECT DISTINCT language
      FROM message_templates
      WHERE code = $1 AND agency_id = $3 AND status = 'active'
    `, [templateCode, agencyId]);

    const languageMap: Record<string, { name: string; nativeName: string }> = {
      'en': { name: 'English', nativeName: 'English' },
      'hi': { name: 'Hindi', nativeName: 'हिंदी' },
      'ta': { name: 'Tamil', nativeName: 'தமிழ்' },
      'te': { name: 'Telugu', nativeName: 'తెలుగు' },
      'kn': { name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
      'ml': { name: 'Malayalam', nativeName: 'മലയാളം' },
      'gu': { name: 'Gujarati', nativeName: 'ગુજરાતી' },
      'mr': { name: 'Marathi', nativeName: 'मराठी' },
      'bn': { name: 'Bengali', nativeName: 'বাংলা' },
      'ar': { name: 'Arabic', nativeName: 'العربية' }
    };

    return result.rows.map(row => ({
      code: row.language,
      ...languageMap[row.language] || { name: row.language, nativeName: row.language }
    }));
  }

  /**
   * Create localized version of template
   */
  async createLocalizedVersion(
    originalTemplateId: string,
    language: string,
    translations: {
      subjectTemplate?: string;
      contentTemplate: string;
      htmlTemplate?: string;
    }
  ): Promise<MessageTemplate> {
    const original = await db.query(
      'SELECT * FROM message_templates WHERE id = $1',
      [originalTemplateId]
    );

    if (original.rows.length === 0) {
      throw new Error('Original template not found');
    }

    const template = original.rows[0];

    const result = await db.query(`
      INSERT INTO message_templates (
        agency_id, name, code, description, category, channel,
        subject_template, content_template, html_template,
        language, region, variables, settings, status
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
      )
      RETURNING *
    `, [
      template.agency_id,
      `${template.name} (${language.toUpperCase()})`,
      template.code,
      template.description,
      template.category,
      template.channel,
      translations.subjectTemplate,
      translations.contentTemplate,
      translations.htmlTemplate,
      language,
      template.region,
      JSON.stringify(template.variables),
      JSON.stringify(template.settings),
      'draft'
    ]);

    return result.rows[0];
  }

  /**
   * Format content for RTL languages
   */
  formatForRTL(content: string, language: string): string {
    const rtlLanguages = ['ar', 'he', 'ur', 'fa'];

    if (rtlLanguages.includes(language)) {
      return `<div dir="rtl">${content}</div>`;
    }

    return content;
  }

  /**
   * Get locale-specific date formatter
   */
  getDateFormatter(language: string): (date: Date) => string {
    const localeMap: Record<string, string> = {
      'en': 'en-IN',
      'hi': 'hi-IN',
      'ta': 'ta-IN',
      'te': 'te-IN',
      'kn': 'kn-IN',
      'ml': 'ml-IN',
      'gu': 'gu-IN',
      'mr': 'mr-IN',
      'bn': 'bn-IN',
      'ar': 'ar-SA'
    };

    const locale = localeMap[language] || 'en-IN';

    return (date: Date) => {
      return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }).format(date);
    };
  }

  /**
   * Get locale-specific currency formatter
   */
  getCurrencyFormatter(language: string): (amount: number) => string {
    const localeMap: Record<string, { locale: string; currency: string }> = {
      'en': { locale: 'en-IN', currency: 'INR' },
      'hi': { locale: 'hi-IN', currency: 'INR' },
      'ar': { locale: 'ar-SA', currency: 'SAR' }
    };

    const config = localeMap[language] || { locale: 'en-IN', currency: 'INR' };

    return (amount: number) => {
      return new Intl.NumberFormat(config.locale, {
        style: 'currency',
        currency: config.currency
      }).format(amount);
    };
  }
}
```

---

## Template Management

### Template CRUD Operations

```typescript
// routes/template.routes.ts

import Router from 'express';
const router = Router();

/**
 * Create new template
 */
router.post('/templates', async (req, res) => {
  const { agencyId } = req.user;
  const templateData: CreateTemplateRequest = req.body;

  try {
    // Validate template code uniqueness
    const existing = await db.query(
      'SELECT id FROM message_templates WHERE code = $1 AND agency_id = $2',
      [templateData.code, agencyId]
    );

    if (existing.rows.length > 0) {
      return res.status(400).json({
        error: 'Template with this code already exists'
      });
    }

    // Validate variables match template content
    const variableService = new TemplateVariableService();
    const contentVars = variableService.extractVariables(templateData.contentTemplate);

    const definedVars = new Set(templateData.variables.map(v => v.name));
    const undefinedVars = contentVars.filter(v => !definedVars.has(v));

    if (undefinedVars.length > 0) {
      return res.status(400).json({
        error: 'Variables used in template but not defined',
        undefinedVariables: undefinedVars
      });
    }

    // Create template
    const result = await db.query(`
      INSERT INTO message_templates (
        agency_id, name, code, description, category, channel,
        subject_template, content_template, html_template,
        language, region, variables, settings, status
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'draft'
      )
      RETURNING *
    `, [
      agencyId,
      templateData.name,
      templateData.code,
      templateData.description,
      templateData.category,
      templateData.channel,
      templateData.subjectTemplate,
      templateData.contentTemplate,
      templateData.htmlTemplate,
      templateData.language || 'en',
      templateData.region,
      JSON.stringify(templateData.variables),
      JSON.stringify(templateData.settings || {})
    ]);

    res.status(201).json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * List templates with filters
 */
router.get('/templates', async (req, res) => {
  const { agencyId } = req.user;
  const {
    category,
    channel,
    status = 'active',
    search,
    limit = 50,
    offset = 0
  } = req.query;

  try {
    const conditions: string[] = ['agency_id = $1', 'status = $2'];
    const params: any[] = [agencyId, status];
    let paramIndex = 3;

    if (category) {
      conditions.push(`category = $${paramIndex++}`);
      params.push(category);
    }

    if (channel) {
      conditions.push(`channel = $${paramIndex++}`);
      params.push(channel);
    }

    if (search) {
      conditions.push(`(name ILIKE $${paramIndex++} OR description ILIKE $${paramIndex++})`);
      params.push(`%${search}%`, `%${search}%`);
    }

    const whereClause = conditions.join(' AND ');

    // Get total count
    const countResult = await db.query(
      `SELECT COUNT(*) FROM message_templates WHERE ${whereClause}`,
      params
    );

    // Get templates
    params.push(limit, offset);
    const templatesResult = await db.query(`
      SELECT *,
        COALESCE(last_used_at, created_at) as last_activity
      FROM message_templates
      WHERE ${whereClause}
      ORDER BY last_activity DESC
      LIMIT $${paramIndex++} OFFSET $${paramIndex++}
    `, params);

    res.json({
      templates: templatesResult.rows,
      total: parseInt(countResult.rows[0].count),
      limit: parseInt(limit as string),
      offset: parseInt(offset as string)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Get template by ID
 */
router.get('/templates/:id', async (req, res) => {
  const { id } = req.params;
  const { agencyId } = req.user;

  try {
    const result = await db.query(
      'SELECT * FROM message_templates WHERE id = $1 AND agency_id = $2',
      [id, agencyId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Template not found' });
    }

    // Get version history
    const versionsResult = await db.query(`
      SELECT * FROM message_template_versions
      WHERE template_id = $1
      ORDER BY version DESC
      LIMIT 5
    `, [id]);

    // Get recent usage
    const usageResult = await db.query(`
      SELECT * FROM message_template_usage
      WHERE template_id = $1
      ORDER BY used_at DESC
      LIMIT 10
    `, [id]);

    res.json({
      template: result.rows[0],
      versions: versionsResult.rows,
      recentUsage: usageResult.rows
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Update template
 */
router.put('/templates/:id', async (req, res) => {
  const { id } = req.params;
  const { agencyId } = req.user;
  const updates: UpdateTemplateRequest = req.body;

  try {
    // Get existing template
    const existing = await db.query(
      'SELECT * FROM message_templates WHERE id = $1 AND agency_id = $2',
      [id, agencyId]
    );

    if (existing.rows.length === 0) {
      return res.status(404).json({ error: 'Template not found' });
    }

    const template = existing.rows[0];

    // Check version for optimistic locking
    if (updates.version !== undefined && updates.version !== template.version) {
      return res.status(409).json({
        error: 'Template has been modified by another user',
        currentVersion: template.version
      });
    }

    // Create version snapshot before update
    await db.query(`
      INSERT INTO message_template_versions (
        template_id, version, content_template, subject_template, variables, created_by
      ) VALUES ($1, $2, $3, $4, $5, $6)
    `, [id, template.version, template.content_template, template.subject_template, template.variables, agencyId]);

    // Update template (increment version)
    const result = await db.query(`
      UPDATE message_templates SET
        name = COALESCE($1, name),
        description = COALESCE($2, description),
        category = COALESCE($3, category),
        subject_template = COALESCE($4, subject_template),
        content_template = COALESCE($5, content_template),
        html_template = COALESCE($6, html_template),
        variables = COALESCE($7, variables),
        settings = COALESCE($8, settings),
        version = version + 1,
        updated_at = NOW()
      WHERE id = $9
      RETURNING *
    `, [
      updates.name,
      updates.description,
      updates.category,
      updates.subjectTemplate,
      updates.contentTemplate,
      updates.htmlTemplate,
      updates.variables ? JSON.stringify(updates.variables) : null,
      updates.settings ? JSON.stringify(updates.settings) : null,
      id
    ]);

    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Delete template (soft delete - archive)
 */
router.delete('/templates/:id', async (req, res) => {
  const { id } = req.params;
  const { agencyId } = req.user;

  try {
    await db.query(
      'UPDATE message_templates SET status = $1 WHERE id = $2 AND agency_id = $3',
      ['archived', id, agencyId]
    );

    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Submit template for approval
 */
router.post('/templates/:id/submit', async (req, res) => {
  const { id } = req.params;
  const { agencyId } = req.user;

  try {
    await db.query(
      'UPDATE message_templates SET status = $1 WHERE id = $2 AND agency_id = $3',
      ['pending_approval', id, agencyId]
    );

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Approve template
 */
router.post('/templates/:id/approve', async (req, res) => {
  const { id } = req.params;
  const { agencyId, userId } = req.user;

  try {
    await db.query(
      `UPDATE message_templates
       SET status = 'active', approved_by = $1, approved_at = NOW()
       WHERE id = $2 AND agency_id = $3`,
      [userId, id, agencyId]
    );

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
```

---

## Preview & Testing

### Template Preview Component

```typescript
// components/templates/TemplatePreview.tsx

interface TemplatePreviewProps {
  templateId: string;
  variables?: Record<string, unknown>;
  mode: 'desktop' | 'mobile';
}

export const TemplatePreview: React.FC<TemplatePreviewProps> = ({
  templateId,
  variables = {},
  mode
}) => {
  const [preview, setPreview] = useState<{
    subject?: string;
    content: string;
    html?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [variableValues, setVariableValues] = useState<Record<string, unknown>>(variables);

  useEffect(() => {
    loadPreview();
  }, [templateId, variableValues]);

  const loadPreview = async () => {
    setLoading(true);

    try {
      const response = await fetch(`/api/templates/${templateId}/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variables: variableValues })
      });

      const data = await response.json();
      setPreview(data);
    } catch (error) {
      console.error('Failed to load preview', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <PreviewSkeleton />;
  }

  if (!preview) {
    return <div>Failed to load preview</div>;
  }

  const isMobile = mode === 'mobile';

  return (
    <div
      className={cn(
        "border rounded-lg overflow-hidden",
        isMobile ? "max-w-sm mx-auto" : "w-full"
      )}
    >
      {/* Preview header */}
      <div className="bg-gray-100 px-4 py-2 border-b flex items-center justify-between">
        <span className="text-sm font-medium">Preview</span>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            icon={<DesktopIcon />}
            onClick={() => setMode('desktop')}
          />
          <Button
            variant="ghost"
            size="sm"
            icon={<PhoneIcon />}
            onClick={() => setMode('mobile')}
          />
        </div>
      </div>

      {/* Message subject */}
      {preview.subject && (
        <div className="px-4 py-2 bg-white border-b font-medium">
          {preview.subject}
        </div>
      )}

      {/* Message content */}
      <div className="p-4 bg-white min-h-[200px] whitespace-pre-wrap">
        {preview.html ? (
          <div dangerouslySetInnerHTML={{ __html: preview.html }} />
        ) : (
          preview.content
        )}
      </div>

      {/* Character count for SMS */}
      {preview.content.length > 0 && (
        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
          {preview.content.length} characters
          {preview.content.length > 160 && (
            <span className="text-orange-500 ml-2">
              ({Math.ceil(preview.content.length / 160)} segments)
            </span>
          )}
        </div>
      )}
    </div>
  );
};
```

### Template Testing Service

```typescript
// services/template-testing.service.ts

export class TemplateTestingService {
  /**
   * Send test message
   */
  async sendTestMessage(
    templateId: string,
    testRecipient: string,
    channel: Channel,
    variables: Record<string, unknown>
  ): Promise<{ success: boolean; messageId?: string; error?: string }> {
    try {
      // Render template
      const engine = new TemplateEngineService();
      const rendered = await engine.render({
        templateId,
        variables
      });

      if (rendered.validationErrors.length > 0) {
        return {
          success: false,
          error: rendered.validationErrors.map(e => e.errors.join(', ')).join('; ')
        };
      }

      // Send test message
      const orchestration = new OrchestrationService();
      const message = await orchestration.sendMessage({
        recipientId: testRecipient,
        recipientType: RecipientType.AGENT, // Send to agent for testing
        channel,
        subject: rendered.subject,
        content: rendered.content,
        messageType: MessageType.TEMPLATE,
        templateId,
        templateVariables: variables,
        metadata: { test: true }
      });

      return {
        success: true,
        messageId: message.id
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Validate template for WhatsApp Business API
   */
  async validateWhatsAppTemplate(template: MessageTemplate): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check template name format
    if (!/^[a-z0-9_]+$/.test(template.code)) {
      errors.push('Template code must be lowercase alphanumeric with underscores only');
    }

    // Check content length
    if (template.contentTemplate.length > 1024) {
      errors.push('Template content exceeds WhatsApp limit of 1024 characters');
    }

    // Check category
    const validCategories = ['marketing', 'utility', 'authentication'];
    if (!validCategories.includes(template.settings.whatsappCategory || '')) {
      errors.push(`Invalid WhatsApp category. Must be one of: ${validCategories.join(', ')}`);
    }

    // Warnings
    if (template.contentTemplate.includes('{{')) {
      warnings.push('Variables detected: Ensure all are registered in WhatsApp Business Manager');
    }

    if (template.contentTemplate.length > 500) {
      warnings.push('Long templates may have reduced delivery rates');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * A/B test template variants
   */
  async createABTest(config: {
    templateAId: string;
    templateBId: string;
    trafficSplit: number; // 0-1, percentage for template A
    sampleSize: number;
    metrics: ('open_rate' | 'click_rate' | 'response_rate')[];
  }): Promise<string> {
    const testId = generateId();

    await db.query(`
      INSERT INTO template_ab_tests (
        id, template_a_id, template_b_id, traffic_split,
        sample_size, metrics, status
      ) VALUES ($1, $2, $3, $4, $5, $6, 'running')
    `, [testId, config.templateAId, config.templateBId, config.trafficSplit, config.sampleSize, config.metrics]);

    return testId;
  }
}
```

---

## Template Categories

### Pre-Built Template Library

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TEMPLATE CATEGORIES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BOOKING                    │  PAYMENT                                     │
│  ┌──────────────────────┐  │  ┌──────────────────────┐                     │
│  │ • Inquiry Received   │  │  │ • Payment Request    │                     │
│  │ • Quote Sent         │  │  │ • Payment Reminder   │                     │
│  │ • Booking Confirmed  │  │  │ • Payment Received   │                     │
│  │ • Booking Modified   │  │  │ • Payment Failed     │                     │
│  │ • Booking Cancelled  │  │  │ • Refund Initiated   │                     │
│  └──────────────────────┘  │  └──────────────────────┘                     │
│                                                                             │
│  ITINERARY                  │  CONFIRMATION                                 │
│  ┌──────────────────────┐  │  ┌──────────────────────┐                     │
│  │ • Itinerary Ready    │  │  │ • Booking Confirm    │                     │
│  │ • Day-wise Schedule  │  │  │ • Flight Confirm     │                     │
│  │ • Activity Updates   │  │  │ • Hotel Confirm      │                     │
│  │ • Transport Details  │  │  │ • Payment Confirm    │                     │
│  └──────────────────────┘  │  └──────────────────────┘                     │
│                                                                             │
│  REMINDER                   │  SUPPORT                                      │
│  ┌──────────────────────┐  │  ┌──────────────────────┐                     │
│  │ • Balance Due        │  │  │ • Ticket Received    │                     │
│  │ • Document Upload    │  │  │ • Query Received     │                     │
│  │ • Travel Date        │  │  │ • Query Resolved     │                     │
│  │ • Payment Pending    │  │  │ • Follow-up Required │                     │
│  └──────────────────────┘  │  └──────────────────────┘                     │
│                                                                             │
│  PROMOTIONAL                │  DOCUMENT                                     │
│  ┌──────────────────────┐  │  ┌──────────────────────┐                     │
│  │ • Special Offer      │  │  │ • Invoice Ready      │                     │
│  │ • Seasonal Promo     │  │  │ • Visa Document      │                     │
│  │ • Last Minute Deal   │  │  │ • Travel Insurance   │                     │
│  │ • Referral Bonus     │  │  │ • E-ticket Ready     │                     │
│  └──────────────────────┘  │  └──────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Example Templates

#### Booking Confirmation (WhatsApp)

```
Template Code: booking_confirmation_whatsapp
Category: booking
Channel: whatsapp

Content:
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✅ *Booking Confirmed*                                                     │
│                                                                             │
│ Hi {{customerName}},                                                        │
│                                                                             │
│ Your trip to {{destination}} has been confirmed! 🎉                        │
│                                                                             │
│ *Booking Details:*                                                          │
│ 📅 {{formatDate(checkIn, 'PPP')}}                                          │
│ ⏰ {{nights}} nights                                                        │
│ 👥 {{adults}} adults {{children > 0 ? '+ ' + children + ' children' : ''}} │
│                                                                             │
│ *Amount Paid:* ₹{{formatCurrency(amountPaid)}}                             │
│                                                                             │
│ View your complete itinerary here:                                          │
│ {{itineraryLink}}                                                          │
│                                                                             │
│ Have a great trip! ✈️                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Variables:
- customerName: string (required)
- destination: string (required)
- checkIn: date (required)
- nights: number (required)
- adults: number (required)
- children: number (default: 0)
- amountPaid: currency (required)
- itineraryLink: url (required)
```

#### Payment Reminder (Email)

```
Template Code: payment_reminder_email
Category: payment
Channel: email

Subject: 🔔 Payment Reminder: {{tripName}}

HTML Content:
┌─────────────────────────────────────────────────────────────────────────────┐
│ <html>                                                                     │
│ <body style="font-family: Arial, sans-serif;">                             │
│   <div style="max-width: 600px; margin: 0 auto;">                          │
│     <h1 style="color: #6366F1;">Payment Reminder</h1>                      │
│     <p>Hi {{customerName}},</p>                                            │
│     <p>This is a friendly reminder that your payment of                   │
│        <strong>₹{{formatCurrency(amountDue)}}</strong> is due by           │
│        {{formatDate(dueDate, 'PPP')}}.</p>                                │
│                                                                             │
│     <div style="background: #F3F4F6; padding: 20px; border-radius: 8px;">  │
│       <h3>Trip Details:</h3>                                               │
│       <ul>                                                                 │
│         <li>Destination: {{destination}}</li>                              │
│         <li>Travel Dates: {{formatDate(checkIn)}} to {{formatDate(checkOut)}}</li>
│         <li>Amount Due: ₹{{formatCurrency(amountDue)}}</li>               │
│       </ul>                                                                │
│     </div>                                                                 │
│                                                                             │
│     <center>                                                               │
│       <a href="{{paymentLink}}"                                            │
│          style="background: #6366F1; color: white; padding: 12px 24px;     │
│                 text-decoration: none; border-radius: 6px; display:        │
│                 inline-block;">Pay Now</a>                                 │
│     </center>                                                              │
│                                                                             │
│     <p style="font-size: 12px; color: #6B7280;">                           │
│       If you've already paid, please disregard this email.                 │
│     </p>                                                                   │
│   </div>                                                                    │
│ </body>                                                                    │
│ </html>                                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

Variables:
- customerName: string (required)
- tripName: string (required)
- amountDue: currency (required)
- dueDate: date (required)
- destination: string (required)
- checkIn: date (required)
- checkOut: date (required)
- paymentLink: url (required)
```

---

## Summary

The Template System provides:

1. **Reusable Message Patterns**: Consistent communication across the agency
2. **Rich Variable System**: Type-safe variables with validation
3. **Multi-Language Support**: Localization for Indian languages
4. **Channel-Specific Formatting**: Optimized for WhatsApp, Email, SMS
5. **Version Control**: Track changes and rollback if needed
6. **Preview & Testing**: Validate before sending to customers
7. **Approval Workflow**: Ensure compliance before activation

---

**Next:** Communication Hub Analytics Deep Dive (COMM_HUB_04) — delivery metrics, response rates, and performance insights
