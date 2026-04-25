# DATA_GOVERNANCE_01: Data Quality Deep Dive

> Data quality frameworks, validation, monitoring, and remediation

---

## Table of Contents

1. [Overview](#overview)
2. [Data Quality Dimensions](#data-quality-dimensions)
3. [Quality Rules Engine](#quality-rules-engine)
4. [Validation Framework](#validation-framework)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Scoring & Metrics](#scoring--metrics)
7. [Remediation Workflows](#remediation-workflows)
8. [Data Profiling](#data-profiling)
9. [Quality Dashboards](#quality-dashboards)
10. [API Specification](#api-specification)
11. [Testing Scenarios](#testing-scenarios)
12. [Metrics & Monitoring](#metrics--monitoring)

---

## Overview

Data quality is foundational to reliable operations, accurate analytics, and customer trust. This document covers the framework for ensuring data quality across the travel agency platform.

### The Data Quality Challenge

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Quality Issues                     │
├─────────────────────────────────────────────────────────────┤
│  40% of data has at least one error                         │
│  15% of customer records have missing critical fields       │
│  8% of pricing data is outdated                             │
│  5% of bookings have validation warnings                    │
└─────────────────────────────────────────────────────────────┘

Impact:
- Misquoted trips → Customer dissatisfaction
- Invalid payments → Failed transactions
- Outdated inventory → Lost bookings
- Poor analytics → Bad decisions
```

### Quality Gates Strategy

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Entry     │────▶│  Pipeline   │────▶│  Output     │
│   Gate      │     │   Gate      │     │   Gate      │
└─────────────┘     └─────────────┘     └─────────────┘
     │                   │                   │
     ▼                   ▼                   ▼
 Schema Rules      Transform Rules      Output Rules
 Format Checks     Business Rules       Completeness
 Required Fields   Consistency          Accuracy
 Reference Data    Cross-field          Timeliness
```

---

## Data Quality Dimensions

### The Six Dimensions

```typescript
// data-quality/dimensions.ts

export enum DataQualityDimension {
  ACCURACY = 'accuracy',           // Data reflects real-world values
  COMPLETENESS = 'completeness',   // All required data is present
  CONSISTENCY = 'consistency',     // Data is consistent across sources
  TIMELINESS = 'timeliness',       // Data is current and up-to-date
  VALIDITY = 'validity',           // Data conforms to defined rules
  UNIQUENESS = 'uniqueness'        // No duplicate records
}

export interface DataQualityScore {
  dimension: DataQualityDimension;
  score: number; // 0-100
  weight: number; // Importance weighting
  issues: QualityIssue[];
}

export interface QualityIssue {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  dimension: DataQualityDimension;
  field: string;
  value: any;
  expected: any;
  message: string;
  rule: string;
  timestamp: Date;
}

export interface DataQualityReport {
  entity: string;
  entityId: string;
  overallScore: number; // Weighted average 0-100
  dimensionScores: DataQualityScore[];
  issues: QualityIssue[];
  assessedAt: Date;
  assessor: string;
}

// Quality score calculation
export function calculateOverallScore(
  dimensionScores: DataQualityScore[]
): number {
  const totalWeight = dimensionScores.reduce((sum, d) => sum + d.weight, 0);
  const weightedSum = dimensionScores.reduce(
    (sum, d) => sum + (d.score * d.weight),
    0
  );
  return totalWeight > 0 ? weightedSum / totalWeight : 0;
}

// Dimension weights by entity type
export const dimensionWeights: Record<string, Record<DataQualityDimension, number>> = {
  customer: {
    [DataQualityDimension.ACCURACY]: 0.25,
    [DataQualityDimension.COMPLETENESS]: 0.25,
    [DataQualityDimension.CONSISTENCY]: 0.15,
    [DataQualityDimension.TIMELINESS]: 0.15,
    [DataQualityDimension.VALIDITY]: 0.10,
    [DataQualityDimension.UNIQUENESS]: 0.10
  },
  booking: {
    [DataQualityDimension.ACCURACY]: 0.30,
    [DataQualityDimension.COMPLETENESS]: 0.30,
    [DataQualityDimension.CONSISTENCY]: 0.15,
    [DataQualityDimension.TIMELINESS]: 0.10,
    [DataQualityDimension.VALIDITY]: 0.10,
    [DataQualityDimension.UNIQUENESS]: 0.05
  },
  inventory: {
    [DataQualityDimension.ACCURACY]: 0.20,
    [DataQualityDimension.COMPLETENESS]: 0.20,
    [DataQualityDimension.CONSISTENCY]: 0.15,
    [DataQualityDimension.TIMELINESS]: 0.25, // Pricing changes frequently
    [DataQualityDimension.VALIDITY]: 0.15,
    [DataQualityDimension.UNIQUENESS]: 0.05
  },
  payment: {
    [DataQualityDimension.ACCURACY]: 0.35,
    [DataQualityDimension.COMPLETENESS]: 0.30,
    [DataQualityDimension.CONSISTENCY]: 0.20,
    [DataQualityDimension.TIMELINESS]: 0.05,
    [DataQualityDimension.VALIDITY]: 0.10,
    [DataQualityDimension.UNIQUENESS]: 0.00
  }
};
```

---

## Quality Rules Engine

### Rule Definition

```typescript
// data-quality/rules/types.ts

export interface QualityRule {
  id: string;
  name: string;
  description: string;
  dimension: DataQualityDimension;
  entityType: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  enabled: boolean;

  // Rule definition
  type: RuleType;
  config: RuleConfig;

  // Behavior
  action: 'block' | 'warn' | 'log' | 'remediate';
  remediation?: RemediationConfig;

  // Metadata
  category: string;
  tags: string[];
  owner: string;
  version: number;
}

export type RuleType =
  | 'required'           // Field must be present
  | 'format'             // Field must match pattern
  | 'range'              // Numeric value within range
  | 'enum'               // Value in allowed set
  | 'reference'          // Reference data exists
  | 'cross_field'        // Depends on another field
  | 'business_rule'      // Custom business logic
  | 'uniqueness'         // No duplicate values
  | 'lookup'             // Validate against external source
  | 'composite'          // Combination of rules;

export interface RuleConfig {
  // Field targeting
  field?: string;
  fields?: string[];

  // Validation
  pattern?: RegExp;
  min?: number;
  max?: number;
  allowedValues?: any[];
  forbiddenValues?: any[];

  // Cross-field
  dependentField?: string;
  dependencyType?: 'requires' | 'excludes' | 'equals' | 'greater_than' | 'less_than';

  // Reference
  referenceTable?: string;
  referenceField?: string;

  // Custom
  customFunction?: string;
  customScript?: string;

  // Thresholds
  threshold?: number;
  tolerance?: number;
}

export interface RemediationConfig {
  type: 'auto_fix' | 'suggest' | 'escalate';
  action: string;
  params?: Record<string, any>;
}
```

### Rule Library

```typescript
// data-quality/rules/library.ts

export const customerQualityRules: QualityRule[] = [
  {
    id: 'CUST_001',
    name: 'Email Required',
    description: 'Customer email is required for communication',
    dimension: DataQualityDimension.COMPLETENESS,
    entityType: 'customer',
    severity: 'critical',
    enabled: true,
    type: 'required',
    config: { field: 'email' },
    action: 'block',
    category: 'contact',
    tags: ['required', 'contact'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'CUST_002',
    name: 'Email Format',
    description: 'Email must be valid format',
    dimension: DataQualityDimension.VALIDITY,
    entityType: 'customer',
    severity: 'high',
    enabled: true,
    type: 'format',
    config: {
      field: 'email',
      pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    },
    action: 'block',
    category: 'contact',
    tags: ['format', 'email'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'CUST_003',
    name: 'Phone Format',
    description: 'Phone must be valid format with country code',
    dimension: DataQualityDimension.VALIDITY,
    entityType: 'customer',
    severity: 'medium',
    enabled: true,
    type: 'format',
    config: {
      field: 'phone',
      pattern: /^\+?[1-9]\d{1,14}$/
    },
    action: 'warn',
    remediation: {
      type: 'suggest',
      action: 'format_phone',
      params: { format: 'international' }
    },
    category: 'contact',
    tags: ['format', 'phone'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'CUST_004',
    name: 'Date of Birth Not Future',
    description: 'Date of birth cannot be in the future',
    dimension: DataQualityDimension.ACCURACY,
    entityType: 'customer',
    severity: 'high',
    enabled: true,
    type: 'range',
    config: {
      field: 'dateOfBirth',
      max: () => new Date()
    },
    action: 'block',
    category: 'personal',
    tags: ['accuracy', 'dates'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'CUST_005',
    name: 'Passport Expiry',
    description: 'Passport must be valid for travel dates',
    dimension: DataQualityDimension.TIMELINESS,
    entityType: 'customer',
    severity: 'high',
    enabled: true,
    type: 'business_rule',
    config: {
      customFunction: 'validatePassportExpiry',
      customScript: `
        function validatePassportExpiry(record, context) {
          if (!record.passportExpiry) return { valid: true };
          const travelDate = context.travelDate || new Date();
          const minValid = new Date(travelDate);
          minValid.setMonth(minValid.getMonth() + 6);
          return {
            valid: new Date(record.passportExpiry) > minValid,
            message: 'Passport must be valid 6 months after travel date'
          };
        }
      `
    },
    action: 'warn',
    remediation: {
      type: 'suggest',
      action: 'request_updated_passport'
    },
    category: 'travel',
    tags: ['timeliness', 'passport'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'CUST_006',
    name: 'Unique Email',
    description: 'Email must be unique across customers',
    dimension: DataQualityDimension.UNIQUENESS,
    entityType: 'customer',
    severity: 'critical',
    enabled: true,
    type: 'uniqueness',
    config: { field: 'email' },
    action: 'block',
    category: 'identity',
    tags: ['uniqueness', 'email'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'CUST_007',
    name: 'Emergency Contact Required',
    description: 'Emergency contact required for bookings',
    dimension: DataQualityDimension.COMPLETENESS,
    entityType: 'customer',
    severity: 'medium',
    enabled: true,
    type: 'cross_field',
    config: {
      field: 'emergencyContact',
      dependentField: 'hasBookings',
      dependencyType: 'requires'
    },
    action: 'warn',
    category: 'safety',
    tags: ['required', 'safety'],
    owner: 'data-team',
    version: 1
  }
];

export const bookingQualityRules: QualityRule[] = [
  {
    id: 'BOOK_001',
    name: 'Travel Dates Required',
    description: 'Travel start and end dates are required',
    dimension: DataQualityDimension.COMPLETENESS,
    entityType: 'booking',
    severity: 'critical',
    enabled: true,
    type: 'required',
    config: { fields: ['startDate', 'endDate'] },
    action: 'block',
    category: 'dates',
    tags: ['required', 'dates'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'BOOK_002',
    name: 'End After Start',
    description: 'End date must be after start date',
    dimension: DataQualityDimension.ACCURACY,
    entityType: 'booking',
    severity: 'critical',
    enabled: true,
    type: 'cross_field',
    config: {
      field: 'endDate',
      dependentField: 'startDate',
      dependencyType: 'greater_than'
    },
    action: 'block',
    category: 'dates',
    tags: ['accuracy', 'dates'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'BOOK_003',
    name: 'Destination Valid',
    description: 'Destination must exist in destinations catalog',
    dimension: DataQualityDimension.VALIDITY,
    entityType: 'booking',
    severity: 'critical',
    enabled: true,
    type: 'reference',
    config: {
      field: 'destinationId',
      referenceTable: 'destinations',
      referenceField: 'id'
    },
    action: 'block',
    category: 'reference',
    tags: ['reference', 'destination'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'BOOK_004',
    name: 'Guest Count Range',
    description: 'Guest count must be between 1 and 50',
    dimension: DataQualityDimension.VALIDITY,
    entityType: 'booking',
    severity: 'high',
    enabled: true,
    type: 'range',
    config: {
      field: 'guestCount',
      min: 1,
      max: 50
    },
    action: 'block',
    category: 'validation',
    tags: ['range', 'guests'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'BOOK_005',
    name: 'Payment Method Valid',
    description: 'Payment method must be supported',
    dimension: DataQualityDimension.VALIDITY,
    entityType: 'booking',
    severity: 'high',
    enabled: true,
    type: 'enum',
    config: {
      field: 'paymentMethod',
      allowedValues: ['credit_card', 'debit_card', 'upi', 'bank_transfer', 'wallet']
    },
    action: 'block',
    category: 'payment',
    tags: ['enum', 'payment'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'BOOK_006',
    name: 'Budget Positive',
    description: 'Budget must be positive number',
    dimension: DataQualityDimension.ACCURACY,
    entityType: 'booking',
    severity: 'high',
    enabled: true,
    type: 'range',
    config: {
      field: 'budget',
      min: 0,
      threshold: 0 // Strictly greater than 0
    },
    action: 'block',
    category: 'financial',
    tags: ['range', 'budget'],
    owner: 'data-team',
    version: 1
  }
];

export const inventoryQualityRules: QualityRule[] = [
  {
    id: 'INV_001',
    name: 'Price Positive',
    description: 'Price must be positive',
    dimension: DataQualityDimension.ACCURACY,
    entityType: 'inventory',
    severity: 'critical',
    enabled: true,
    type: 'range',
    config: {
      field: 'price',
      min: 0.01
    },
    action: 'block',
    category: 'pricing',
    tags: ['range', 'price'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'INV_002',
    name: 'Price Freshness',
    description: 'Price must be updated within last 24 hours',
    dimension: DataQualityDimension.TIMELINESS,
    entityType: 'inventory',
    severity: 'high',
    enabled: true,
    type: 'business_rule',
    config: {
      customFunction: 'validatePriceFreshness',
      customScript: `
        function validatePriceFreshness(record, context) {
          const maxAge = 24 * 60 * 60 * 1000; // 24 hours
          const age = Date.now() - new Date(record.priceUpdatedAt).getTime();
          return {
            valid: age < maxAge,
            message: 'Price is ' + Math.round(age / 3600000) + ' hours old'
          };
        }
      `
    },
    action: 'warn',
    remediation: {
      type: 'escalate',
      action: 'refresh_price'
    },
    category: 'pricing',
    tags: ['timeliness', 'price'],
    owner: 'data-team',
    version: 1
  },
  {
    id: 'INV_003',
    name: 'Availability Non-negative',
    description: 'Available count cannot be negative',
    dimension: DataQualityDimension.ACCURACY,
    entityType: 'inventory',
    severity: 'high',
    enabled: true,
    type: 'range',
    config: {
      field: 'available',
      min: 0
    },
    action: 'block',
    category: 'inventory',
    tags: ['range', 'availability'],
    owner: 'data-team',
    version: 1
  }
];
```

### Rules Engine

```typescript
// data-quality/rules/engine.ts

export class QualityRulesEngine {
  private rules: Map<string, QualityRule[]> = new Map();

  constructor() {
    this.registerRules('customer', customerQualityRules);
    this.registerRules('booking', bookingQualityRules);
    this.registerRules('inventory', inventoryQualityRules);
  }

  registerRules(entityType: string, rules: QualityRule[]): void {
    this.rules.set(entityType, rules.filter(r => r.enabled));
  }

  async validate(
    entityType: string,
    record: Record<string, any>,
    context?: Record<string, any>
  ): Promise<QualityResult> {
    const rules = this.rules.get(entityType) || [];
    const issues: QualityIssue[] = [];
    const blocked: QualityIssue[] = [];

    for (const rule of rules) {
      const result = await this.evaluateRule(rule, record, context);

      if (!result.valid) {
        const issue: QualityIssue = {
          id: `${rule.id}_${Date.now()}`,
          severity: rule.severity,
          dimension: rule.dimension,
          field: rule.config.field || rule.config.fields?.[0] || 'multiple',
          value: this.getFieldValue(record, rule.config.field),
          expected: this.getExpectedValue(rule),
          message: result.message || rule.description,
          rule: rule.id,
          timestamp: new Date()
        };

        issues.push(issue);

        if (rule.action === 'block') {
          blocked.push(issue);
        }

        // Handle remediation
        if (rule.remediation) {
          await this.handleRemediation(rule, record, issue);
        }
      }
    }

    return {
      valid: blocked.length === 0,
      issues,
      blocked,
      score: this.calculateScore(issues, rules)
    };
  }

  private async evaluateRule(
    rule: QualityRule,
    record: Record<string, any>,
    context?: Record<string, any>
  ): Promise<{ valid: boolean; message?: string }> {
    switch (rule.type) {
      case 'required':
        return this.evaluateRequired(rule, record);
      case 'format':
        return this.evaluateFormat(rule, record);
      case 'range':
        return this.evaluateRange(rule, record);
      case 'enum':
        return this.evaluateEnum(rule, record);
      case 'reference':
        return this.evaluateReference(rule, record);
      case 'cross_field':
        return this.evaluateCrossField(rule, record);
      case 'uniqueness':
        return this.evaluateUniqueness(rule, record);
      case 'business_rule':
        return this.evaluateBusinessRule(rule, record, context);
      default:
        return { valid: true };
    }
  }

  private evaluateRequired(
    rule: QualityRule,
    record: Record<string, any>
  ): { valid: boolean; message?: string } {
    if (rule.config.field) {
      const value = record[rule.config.field];
      const valid = value !== null && value !== undefined && value !== '';
      return {
        valid,
        message: valid ? undefined : `Field ${rule.config.field} is required`
      };
    }

    if (rule.config.fields) {
      const missing = rule.config.fields.filter(
        f => record[f] === null || record[f] === undefined || record[f] === ''
      );
      return {
        valid: missing.length === 0,
        message: missing.length > 0 ? `Missing required fields: ${missing.join(', ')}` : undefined
      };
    }

    return { valid: true };
  }

  private evaluateFormat(
    rule: QualityRule,
    record: Record<string, any>
  ): { valid: boolean; message?: string } {
    const value = record[rule.config.field!];
    if (!value) return { valid: true }; // Let required rule handle missing

    const valid = rule.config.pattern!.test(value);
    return {
      valid,
      message: valid ? undefined : `Field ${rule.config.field} format is invalid`
    };
  }

  private evaluateRange(
    rule: QualityRule,
    record: Record<string, any>
  ): { valid: boolean; message?: string } {
    const value = record[rule.config.field!];
    if (value === null || value === undefined) return { valid: true };

    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return { valid: false, message: 'Value is not a number' };

    if (rule.config.min !== undefined && numValue < rule.config.min) {
      return {
        valid: false,
        message: `Value ${numValue} is less than minimum ${rule.config.min}`
      };
    }

    if (rule.config.max !== undefined && numValue > rule.config.max) {
      return {
        valid: false,
        message: `Value ${numValue} is greater than maximum ${rule.config.max}`
      };
    }

    return { valid: true };
  }

  private evaluateEnum(
    rule: QualityRule,
    record: Record<string, any>
  ): { valid: boolean; message?: string } {
    const value = record[rule.config.field!];
    if (!value) return { valid: true };

    const valid = rule.config.allowedValues!.includes(value);
    return {
      valid,
      message: valid ? undefined : `Value must be one of: ${rule.config.allowedValues!.join(', ')}`
    };
  }

  private async evaluateReference(
    rule: QualityRule,
    record: Record<string, any>
  ): Promise<{ valid: boolean; message?: string }> {
    const value = record[rule.config.field!];
    if (!value) return { valid: true };

    // Check reference exists
    const exists = await this.checkReference(
      rule.config.referenceTable!,
      rule.config.referenceField!,
      value
    );

    return {
      valid: exists,
      message: exists ? undefined : `Referenced ${value} does not exist in ${rule.config.referenceTable}`
    };
  }

  private evaluateCrossField(
    rule: QualityRule,
    record: Record<string, any>
  ): { valid: boolean; message?: string } {
    const fieldValue = record[rule.config.field!];
    const depValue = record[rule.config.dependentField!];

    switch (rule.config.dependencyType) {
      case 'requires':
        if (depValue && !fieldValue) {
          return {
            valid: false,
            message: `${rule.config.field} is required when ${rule.config.dependentField} is set`
          };
        }
        break;

      case 'excludes':
        if (depValue && fieldValue) {
          return {
            valid: false,
            message: `${rule.config.field} cannot be set when ${rule.config.dependentField} is set`
          };
        }
        break;

      case 'greater_than':
        if (fieldValue <= depValue) {
          return {
            valid: false,
            message: `${rule.config.field} must be greater than ${rule.config.dependentField}`
          };
        }
        break;

      case 'less_than':
        if (fieldValue >= depValue) {
          return {
            valid: false,
            message: `${rule.config.field} must be less than ${rule.config.dependentField}`
          };
        }
        break;
    }

    return { valid: true };
  }

  private async evaluateUniqueness(
    rule: QualityRule,
    record: Record<string, any>
  ): Promise<{ valid: boolean; message?: string }> {
    const value = record[rule.config.field!];
    if (!value) return { valid: true };

    const isDuplicate = await this.checkDuplicate(
      rule.entityType,
      rule.config.field!,
      value,
      record.id
    );

    return {
      valid: !isDuplicate,
      message: isDuplicate ? `Duplicate value found for ${rule.config.field}` : undefined
    };
  }

  private evaluateBusinessRule(
    rule: QualityRule,
    record: Record<string, any>,
    context?: Record<string, any>
  ): { valid: boolean; message?: string } {
    // Execute custom business rule function
    try {
      const func = new Function('record', 'context', rule.config.customScript!);
      return func(record, context || {});
    } catch (error) {
      return {
        valid: false,
        message: `Business rule execution failed: ${error}`
      };
    }
  }

  private getFieldValue(record: Record<string, any>, field?: string): any {
    if (!field) return '[multiple fields]';
    return record[field];
  }

  private getExpectedValue(rule: QualityRule): any {
    if (rule.config.allowedValues) return rule.config.allowedValues;
    if (rule.config.pattern) return rule.config.pattern.toString();
    if (rule.config.min !== undefined || rule.config.max !== undefined) {
      return `between ${rule.config.min} and ${rule.config.max}`;
    }
    return '[rule defined]';
  }

  private calculateScore(issues: QualityIssue[], rules: QualityRule[]): number {
    if (rules.length === 0) return 100;

    const severityWeights = { critical: 10, high: 5, medium: 2, low: 1 };
    const maxScore = rules.reduce((sum, r) => sum + severityWeights[r.severity], 0);
    const deductedScore = issues.reduce((sum, i) => sum + severityWeights[i.severity], 0);

    return maxScore > 0 ? Math.max(0, 100 - (deductedScore / maxScore) * 100) : 100;
  }

  private async handleRemediation(
    rule: QualityRule,
    record: Record<string, any>,
    issue: QualityIssue
  ): Promise<void> {
    if (!rule.remediation) return;

    switch (rule.remediation.type) {
      case 'auto_fix':
        await this.autoFix(rule, record, issue);
        break;
      case 'suggest':
        await this.suggestFix(rule, record, issue);
        break;
      case 'escalate':
        await this.escalateIssue(rule, record, issue);
        break;
    }
  }

  private async autoFix(
    rule: QualityRule,
    record: Record<string, any>,
    issue: QualityIssue
  ): Promise<void> {
    // Apply automatic fix based on remediation action
    console.log(`Auto-fixing ${issue.id} with action: ${rule.remediation!.action}`);
  }

  private async suggestFix(
    rule: QualityRule,
    record: Record<string, any>,
    issue: QualityIssue
  ): Promise<void> {
    // Suggest fix to user
    console.log(`Suggesting fix for ${issue.id}: ${rule.remediation!.action}`);
  }

  private async escalateIssue(
    rule: QualityRule,
    record: Record<string, any>,
    issue: QualityIssue
  ): Promise<void> {
    // Escalate to data steward or operations team
    console.log(`Escalating ${issue.id} to ${rule.owner}`);
  }

  private async checkReference(
    table: string,
    field: string,
    value: any
  ): Promise<boolean> {
    // Database lookup for reference validation
    return true;
  }

  private async checkDuplicate(
    entityType: string,
    field: string,
    value: any,
    excludeId?: string
  ): Promise<boolean> {
    // Database lookup for uniqueness check
    return false;
  }
}

export interface QualityResult {
  valid: boolean;
  issues: QualityIssue[];
  blocked: QualityIssue[];
  score: number;
}
```

---

## Validation Framework

### Pipeline Integration

```typescript
// data-quality/validation/pipeline.ts

export class DataQualityPipeline {
  private engine: QualityRulesEngine;

  constructor() {
    this.engine = new QualityRulesEngine();
  }

  async validateAtEntry(
    entityType: string,
    record: Record<string, any>,
    context?: Record<string, any>
  ): Promise<EntryValidationResult> {
    const result = await this.engine.validate(entityType, record, context);

    return {
      canProceed: result.valid,
      shouldBlock: result.blocked.length > 0,
      warnings: result.issues.filter(i => !result.blocked.includes(i)),
      errors: result.blocked,
      score: result.score,
      recommendations: this.generateRecommendations(result.issues)
    };
  }

  async validateInPipeline(
    entityType: string,
    records: Record<string, any>[],
    stage: string
  ): Promise<PipelineValidationResult> {
    const results = await Promise.all(
      records.map(record => this.engine.validate(entityType, record))
    );

    const validCount = results.filter(r => r.valid).length;
    const invalidCount = results.length - validCount;

    return {
      stage,
      totalRecords: results.length,
      validRecords: validCount,
      invalidRecords: invalidCount,
      passRate: (validCount / results.length) * 100,
      issues: results.flatMap(r => r.issues),
      canContinue: invalidCount === 0,
      shouldAlert: invalidCount > results.length * 0.05 // Alert if >5% fail
    };
  }

  async validateAtOutput(
    entityType: string,
    record: Record<string, any>,
    outputType: string
  ): Promise<OutputValidationResult> {
    const result = await this.engine.validate(entityType, record);

    return {
      outputType,
      recordId: record.id,
      qualityScore: result.score,
      issues: result.issues,
      certified: result.score >= 80, // Minimum score for output certification
      certificationLevel: this.getCertificationLevel(result.score),
      timestamp: new Date()
    };
  }

  private generateRecommendations(issues: QualityIssue[]): string[] {
    const recommendations: string[] = [];

    for (const issue of issues) {
      switch (issue.rule) {
        case 'CUST_003':
          recommendations.push('Format phone number with country code (+91...)');
          break;
        case 'CUST_005':
          recommendations.push('Request updated passport from customer');
          break;
        case 'INV_002':
          recommendations.push('Refresh pricing from supplier API');
          break;
        default:
          recommendations.push(`Fix: ${issue.message}`);
      }
    }

    return [...new Set(recommendations)];
  }

  private getCertificationLevel(score: number): 'gold' | 'silver' | 'bronze' | 'none' {
    if (score >= 95) return 'gold';
    if (score >= 85) return 'silver';
    if (score >= 80) return 'bronze';
    return 'none';
  }
}

export interface EntryValidationResult {
  canProceed: boolean;
  shouldBlock: boolean;
  warnings: QualityIssue[];
  errors: QualityIssue[];
  score: number;
  recommendations: string[];
}

export interface PipelineValidationResult {
  stage: string;
  totalRecords: number;
  validRecords: number;
  invalidRecords: number;
  passRate: number;
  issues: QualityIssue[];
  canContinue: boolean;
  shouldAlert: boolean;
}

export interface OutputValidationResult {
  outputType: string;
  recordId: string;
  qualityScore: number;
  issues: QualityIssue[];
  certified: boolean;
  certificationLevel: 'gold' | 'silver' | 'bronze' | 'none';
  timestamp: Date;
}
```

---

## Monitoring & Alerting

### Quality Monitoring Service

```typescript
// data-quality/monitoring/service.ts

export class DataQualityMonitoringService {
  private metrics: Map<string, QualityMetrics> = new Map();
  private thresholds: Map<string, QualityThreshold> = new Map();

  async recordValidation(
    entityType: string,
    result: QualityResult
  ): Promise<void> {
    const key = `${entityType}:${new Date().toISOString().split('T')[0]}`;
    const metrics = this.metrics.get(key) || this.createEmptyMetrics();

    metrics.totalValidations++;
    if (result.valid) metrics.passedValidations++;
    else metrics.failedValidations++;

    metrics.issuesBySeverity = this.aggregateIssues(result.issues, metrics.issuesBySeverity);
    metrics.averageScore =
      (metrics.averageScore * (metrics.totalValidations - 1) + result.score) /
      metrics.totalValidations;

    this.metrics.set(key, metrics);

    await this.checkThresholds(entityType, metrics);
  }

  async getQualityReport(
    entityType: string,
    period: 'hour' | 'day' | 'week' | 'month'
  ): Promise<QualityReport> {
    const now = new Date();
    const startTime = this.getPeriodStart(now, period);
    const endTime = now;

    const periodMetrics = await this.getMetricsForPeriod(entityType, startTime, endTime);

    return {
      entityType,
      period,
      startTime,
      endTime,
      totalValidations: periodMetrics.totalValidations,
      passRate: this.calculatePassRate(periodMetrics),
      averageScore: periodMetrics.averageScore,
      issuesBySeverity: periodMetrics.issuesBySeverity,
      topIssues: this.getTopIssues(periodMetrics),
      trend: this.calculateTrend(entityType, period)
    };
  }

  private async checkThresholds(
    entityType: string,
    metrics: QualityMetrics
  ): Promise<void> {
    const threshold = this.thresholds.get(entityType);

    if (!threshold) return;

    const passRate = metrics.passedValidations / metrics.totalValidations;

    if (passRate < threshold.minPassRate) {
      await this.alert('LOW_PASS_RATE', entityType, {
        actual: passRate,
        threshold: threshold.minPassRate
      });
    }

    if (metrics.averageScore < threshold.minScore) {
      await this.alert('LOW_QUALITY_SCORE', entityType, {
        actual: metrics.averageScore,
        threshold: threshold.minScore
      });
    }

    if (metrics.issuesBySeverity.critical > threshold.maxCriticalIssues) {
      await this.alert('TOO_MANY_CRITICAL', entityType, {
        actual: metrics.issuesBySeverity.critical,
        threshold: threshold.maxCriticalIssues
      });
    }
  }

  private async alert(
    type: string,
    entityType: string,
    details: Record<string, number>
  ): Promise<void> {
    // Send alert to monitoring system
    console.error(`Data Quality Alert [${type}] for ${entityType}:`, details);
  }

  private createEmptyMetrics(): QualityMetrics {
    return {
      totalValidations: 0,
      passedValidations: 0,
      failedValidations: 0,
      averageScore: 0,
      issuesBySeverity: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      }
    };
  }

  private aggregateIssues(
    issues: QualityIssue[],
    current: Record<string, number>
  ): Record<string, number> {
    const aggregated = { ...current };
    for (const issue of issues) {
      aggregated[issue.severity] = (aggregated[issue.severity] || 0) + 1;
    }
    return aggregated;
  }

  private calculatePassRate(metrics: QualityMetrics): number {
    if (metrics.totalValidations === 0) return 100;
    return (metrics.passedValidations / metrics.totalValidations) * 100;
  }

  private getPeriodStart(now: Date, period: string): Date {
    const start = new Date(now);
    switch (period) {
      case 'hour':
        start.setMinutes(0, 0, 0);
        break;
      case 'day':
        start.setHours(0, 0, 0, 0);
        break;
      case 'week':
        start.setDate(start.getDate() - 7);
        break;
      case 'month':
        start.setMonth(start.getMonth() - 1);
        break;
    }
    return start;
  }

  private async getMetricsForPeriod(
    entityType: string,
    start: Date,
    end: Date
  ): Promise<QualityMetrics> {
    // Aggregate metrics for period from storage
    return this.createEmptyMetrics();
  }

  private getTopIssues(metrics: QualityMetrics): IssueCount[] {
    return [];
  }

  private calculateTrend(entityType: string, period: string): 'improving' | 'stable' | 'declining' {
    return 'stable';
  }
}

export interface QualityMetrics {
  totalValidations: number;
  passedValidations: number;
  failedValidations: number;
  averageScore: number;
  issuesBySeverity: Record<string, number>;
}

export interface QualityThreshold {
  minPassRate: number;
  minScore: number;
  maxCriticalIssues: number;
}

export interface QualityReport {
  entityType: string;
  period: string;
  startTime: Date;
  endTime: Date;
  totalValidations: number;
  passRate: number;
  averageScore: number;
  issuesBySeverity: Record<string, number>;
  topIssues: IssueCount[];
  trend: 'improving' | 'stable' | 'declining';
}

export interface IssueCount {
  rule: string;
  count: number;
  severity: string;
}
```

---

## Scoring & Metrics

### Quality Score Calculation

```typescript
// data-quality/scoring/calculator.ts

export class DataQualityScoreCalculator {
  calculateEntityScore(
    entityType: string,
    record: Record<string, any>,
    validationResults: QualityResult
  ): DataQualityScore {
    const weights = dimensionWeights[entityType] || dimensionWeights.customer;

    const dimensionScores: Record<DataQualityDimension, DimensionScore> = {
      [DataQualityDimension.ACCURACY]: this.calculateDimensionScore(
        DataQualityDimension.ACCURACY,
        validationResults,
        weights[DataQualityDimension.ACCURACY]
      ),
      [DataQualityDimension.COMPLETENESS]: this.calculateDimensionScore(
        DataQualityDimension.COMPLETENESS,
        validationResults,
        weights[DataQualityDimension.COMPLETENESS]
      ),
      [DataQualityDimension.CONSISTENCY]: this.calculateDimensionScore(
        DataQualityDimension.CONSISTENCY,
        validationResults,
        weights[DataQualityDimension.CONSISTENCY]
      ),
      [DataQualityDimension.TIMELINESS]: this.calculateDimensionScore(
        DataQualityDimension.TIMELINESS,
        validationResults,
        weights[DataQualityDimension.TIMELINESS]
      ),
      [DataQualityDimension.VALIDITY]: this.calculateDimensionScore(
        DataQualityDimension.VALIDITY,
        validationResults,
        weights[DataQualityDimension.VALIDITY]
      ),
      [DataQualityDimension.UNIQUENESS]: this.calculateDimensionScore(
        DataQualityDimension.UNIQUENESS,
        validationResults,
        weights[DataQualityDimension.UNIQUENESS]
      )
    };

    const overallScore = Object.values(dimensionScores).reduce(
      (sum, d) => sum + d.score * d.weight,
      0
    );

    return {
      overallScore: Math.round(overallScore),
      dimensionScores,
      grade: this.getGrade(overallScore),
      validatedAt: new Date()
    };
  }

  private calculateDimensionScore(
    dimension: DataQualityDimension,
    results: QualityResult,
    weight: number
  ): DimensionScore {
    const dimensionIssues = results.issues.filter(i => i.dimension === dimension);

    if (dimensionIssues.length === 0) {
      return { score: 100, weight, issues: [] };
    }

    const severityWeights = { critical: 25, high: 15, medium: 5, low: 1 };
    const deductions = dimensionIssues.reduce(
      (sum, issue) => sum + severityWeights[issue.severity],
      0
    );

    return {
      score: Math.max(0, 100 - deductions),
      weight,
      issues: dimensionIssues
    };
  }

  private getGrade(score: number): 'A' | 'B' | 'C' | 'D' | 'F' {
    if (score >= 95) return 'A';
    if (score >= 85) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }
}

export interface DataQualityScore {
  overallScore: number;
  dimensionScores: Record<DataQualityDimension, DimensionScore>;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  validatedAt: Date;
}

export interface DimensionScore {
  score: number;
  weight: number;
  issues: QualityIssue[];
}
```

---

## Remediation Workflows

### Remediation Engine

```typescript
// data-quality/remediation/engine.ts

export class DataQualityRemediationEngine {
  async remediate(
    entityType: string,
    recordId: string,
    issues: QualityIssue[]
  ): Promise<RemediationResult> {
    const results: RemediationAction[] = [];

    for (const issue of issues) {
      const action = await this.remediateIssue(entityType, recordId, issue);
      if (action) {
        results.push(action);
      }
    }

    return {
      recordId,
      actions: results,
      success: results.every(r => r.status === 'success'),
      timestamp: new Date()
    };
  }

  private async remediateIssue(
    entityType: string,
    recordId: string,
    issue: QualityIssue
  ): Promise<RemediationAction | null> {
    const remediation = this.getRemediationForIssue(issue);

    if (!remediation) {
      return null;
    }

    switch (remediation.type) {
      case 'auto_fix':
        return this.applyAutoFix(entityType, recordId, issue, remediation);
      case 'suggest':
        return this.generateSuggestion(entityType, recordId, issue, remediation);
      case 'escalate':
        return this.escalateForResolution(entityType, recordId, issue, remediation);
      default:
        return null;
    }
  }

  private getRemediationForIssue(issue: QualityIssue): RemediationConfig | null {
    const remediations: Record<string, RemediationConfig> = {
      'CUST_003': {
        type: 'auto_fix',
        action: 'format_phone',
        params: { format: 'international' }
      },
      'CUST_005': {
        type: 'escalate',
        action: 'request_updated_passport'
      },
      'INV_002': {
        type: 'escalate',
        action: 'refresh_price'
      }
    };

    return remediations[issue.rule] || null;
  }

  private async applyAutoFix(
    entityType: string,
    recordId: string,
    issue: QualityIssue,
    remediation: RemediationConfig
  ): Promise<RemediationAction> {
    try {
      // Apply the automatic fix
      const result = await this.executeFix(entityType, recordId, remediation);

      return {
        issueId: issue.id,
        type: 'auto_fix',
        action: remediation.action,
        status: 'success',
        details: result,
        timestamp: new Date()
      };
    } catch (error) {
      return {
        issueId: issue.id,
        type: 'auto_fix',
        action: remediation.action,
        status: 'failed',
        details: { error: String(error) },
        timestamp: new Date()
      };
    }
  }

  private async generateSuggestion(
    entityType: string,
    recordId: string,
    issue: QualityIssue,
    remediation: RemediationConfig
  ): Promise<RemediationAction> {
    return {
      issueId: issue.id,
      type: 'suggest',
      action: remediation.action,
      status: 'pending',
      details: { suggestion: this.getSuggestionText(issue) },
      timestamp: new Date()
    };
  }

  private async escalateForResolution(
    entityType: string,
    recordId: string,
    issue: QualityIssue,
    remediation: RemediationConfig
  ): Promise<RemediationAction> {
    // Create ticket or notify responsible team
    const ticketId = await this.createTicket(entityType, recordId, issue, remediation);

    return {
      issueId: issue.id,
      type: 'escalate',
      action: remediation.action,
      status: 'pending',
      details: { ticketId },
      timestamp: new Date()
    };
  }

  private async executeFix(
    entityType: string,
    recordId: string,
    remediation: RemediationConfig
  ): Promise<any> {
    // Execute the fix based on action type
    switch (remediation.action) {
      case 'format_phone':
        return this.formatPhone(recordId, remediation.params);
      default:
        return null;
    }
  }

  private async formatPhone(recordId: string, params: any): Promise<any> {
    // Phone formatting logic
    return { formatted: true };
  }

  private getSuggestionText(issue: QualityIssue): string {
    const suggestions: Record<string, string> = {
      'CUST_003': 'Format phone number with country code (e.g., +91 98765 43210)',
      'CUST_005': 'Request customer to provide updated passport document',
      'INV_002': 'Refresh pricing data from supplier API'
    };

    return suggestions[issue.rule] || 'Review and correct the data';
  }

  private async createTicket(
    entityType: string,
    recordId: string,
    issue: QualityIssue,
    remediation: RemediationConfig
  ): Promise<string> {
    // Create support ticket or task
    return `TICKET-${Date.now()}`;
  }
}

export interface RemediationResult {
  recordId: string;
  actions: RemediationAction[];
  success: boolean;
  timestamp: Date;
}

export interface RemediationAction {
  issueId: string;
  type: 'auto_fix' | 'suggest' | 'escalate';
  action: string;
  status: 'success' | 'failed' | 'pending';
  details: any;
  timestamp: Date;
}

export interface RemediationConfig {
  type: 'auto_fix' | 'suggest' | 'escalate';
  action: string;
  params?: Record<string, any>;
}
```

---

## Data Profiling

### Profiling Service

```typescript
// data-quality/profiling/service.ts

export class DataProfilingService {
  async profileTable(tableName: string): Promise<TableProfile> {
    const columns = await this.getColumns(tableName);
    const columnProfiles = await Promise.all(
      columns.map(col => this.profileColumn(tableName, col))
    );

    return {
      tableName,
      rowCount: await this.getRowCount(tableName),
      columns: columnProfiles,
      profiledAt: new Date()
    };
  }

  async profileColumn(
    tableName: string,
    columnName: string
  ): Promise<ColumnProfile> {
    const stats = await this.getColumnStats(tableName, columnName);
    const sample = await this.getSampleValues(tableName, columnName, 100);

    return {
      columnName,
      dataType: stats.dataType,
      nullable: stats.nullable,
      nullCount: stats.nullCount,
      nullPercentage: (stats.nullCount / stats.totalRows) * 100,
      uniqueCount: stats.uniqueCount,
      uniquePercentage: (stats.uniqueCount / stats.totalRows) * 100,
      minValue: stats.minValue,
      maxValue: stats.maxValue,
      averageValue: stats.averageValue,
      mostCommonValues: stats.mostCommonValues,
      patterns: this.detectPatterns(sample),
      sampleValues: sample,
      qualityScore: this.calculateQualityScore(stats),
      recommendations: this.generateRecommendations(stats)
    };
  }

  private detectPatterns(values: any[]): PatternMatch[] {
    const patterns: PatternMatch[] = [];
    const patternCounts = new Map<string, number>();

    for (const value of values) {
      if (value === null || value === undefined) continue;

      const pattern = this.getPattern(value);
      patternCounts.set(pattern, (patternCounts.get(pattern) || 0) + 1);
    }

    for (const [pattern, count] of patternCounts.entries()) {
      if (count / values.length > 0.1) {
        patterns.push({ pattern, percentage: (count / values.length) * 100 });
      }
    }

    return patterns;
  }

  private getPattern(value: any): string {
    if (typeof value === 'number') return 'N';
    if (typeof value === 'boolean') return 'B';
    if (typeof value === 'string') {
      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return 'YYYY-MM-DD (date)';
      if (/^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(value)) return 'email';
      if (/^\+?\d{10,15}$/.test(value)) return 'phone';
      if (/^[A-Z]{6}\d{6}$/.test(value)) return 'passport';
      return 'S';
    }
    return '?';
  }

  private calculateQualityScore(stats: ColumnStats): number {
    let score = 100;

    // Deduct for nulls
    score -= stats.nullPercentage * 0.3;

    // Deduct for low uniqueness (if expected to be unique)
    if (stats.expectedUnique && stats.uniquePercentage < 95) {
      score -= (100 - stats.uniquePercentage) * 0.2;
    }

    // Deduct for format violations
    if (stats.format && stats.formatViolationRate) {
      score -= stats.formatViolationRate * 0.3;
    }

    return Math.max(0, Math.min(100, score));
  }

  private generateRecommendations(stats: ColumnStats): string[] {
    const recommendations: string[] = [];

    if (stats.nullPercentage > 20) {
      recommendations.push(`High null rate (${stats.nullPercentage.toFixed(1)}%). Consider if field should be required.`);
    }

    if (stats.uniquePercentage < 50 && stats.uniqueCount < 100) {
      recommendations.push('Low cardinality. Consider enum type.');
    }

    if (stats.averageValue !== undefined && stats.dataType === 'number') {
      recommendations.push('Numeric field suitable for aggregations.');
    }

    return recommendations;
  }

  private async getColumns(tableName: string): Promise<string[]> {
    // Get column names from schema
    return [];
  }

  private async getRowCount(tableName: string): Promise<number> {
    // Get row count
    return 0;
  }

  private async getColumnStats(tableName: string, columnName: string): Promise<ColumnStats> {
    // Get column statistics from database
    return {
      dataType: 'text',
      nullable: true,
      nullCount: 0,
      totalRows: 0,
      uniqueCount: 0,
      minValue: undefined,
      maxValue: undefined,
      averageValue: undefined,
      mostCommonValues: []
    };
  }

  private async getSampleValues(
    tableName: string,
    columnName: string,
    limit: number
  ): Promise<any[]> {
    // Get sample values
    return [];
  }
}

export interface TableProfile {
  tableName: string;
  rowCount: number;
  columns: ColumnProfile[];
  profiledAt: Date;
}

export interface ColumnProfile {
  columnName: string;
  dataType: string;
  nullable: boolean;
  nullCount: number;
  nullPercentage: number;
  uniqueCount: number;
  uniquePercentage: number;
  minValue?: any;
  maxValue?: any;
  averageValue?: number;
  mostCommonValues: { value: any; count: number }[];
  patterns: PatternMatch[];
  sampleValues: any[];
  qualityScore: number;
  recommendations: string[];
}

export interface PatternMatch {
  pattern: string;
  percentage: number;
}

export interface ColumnStats {
  dataType: string;
  nullable: boolean;
  nullCount: number;
  totalRows: number;
  uniqueCount: number;
  minValue?: any;
  maxValue?: any;
  averageValue?: number;
  mostCommonValues: { value: any; count: number }[];
  expectedUnique?: boolean;
  format?: string;
  formatViolationRate?: number;
}
```

---

## Quality Dashboards

### Dashboard Queries

```typescript
// data-quality/dashboards/queries.ts

export const dashboardQueries = {
  // Overall quality score trend
  overallQualityTrend: `
    SELECT
      DATE_TRUNC('day', assessed_at) as date,
      entity_type,
      AVG(overall_score) as avg_score,
      COUNT(*) as record_count
    FROM data_quality_reports
    WHERE assessed_at >= NOW() - INTERVAL '30 days'
    GROUP BY 1, 2
    ORDER BY 1, 2
  `,

  // Top quality issues
  topIssues: `
    SELECT
      rule,
      dimension,
      severity,
      COUNT(*) as issue_count,
      COUNT(DISTINCT entity_id) as affected_records
    FROM quality_issues
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY 1, 2, 3
    ORDER BY 4 DESC
    LIMIT 20
  `,

  // Quality by dimension
  qualityByDimension: `
    SELECT
      dimension,
      AVG(score) as avg_score,
      MIN(score) as min_score,
      MAX(score) as max_score,
      COUNT(*) as record_count
    FROM dimension_scores
    WHERE assessed_at >= NOW() - INTERVAL '24 hours'
    GROUP BY 1
    ORDER BY 2 ASC
  `,

  // Quality score distribution
  scoreDistribution: `
    SELECT
      CASE
        WHEN overall_score >= 95 THEN 'A (95-100)'
        WHEN overall_score >= 85 THEN 'B (85-94)'
        WHEN overall_score >= 70 THEN 'C (70-84)'
        WHEN overall_score >= 60 THEN 'D (60-69)'
        ELSE 'F (0-59)'
      END as grade,
      COUNT(*) as count,
      ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
    FROM data_quality_reports
    WHERE assessed_at >= NOW() - INTERVAL '24 hours'
    GROUP BY 1
    ORDER BY 1
  `,

  // Entity quality comparison
  entityQualityComparison: `
    SELECT
      entity_type,
      AVG(overall_score) as avg_score,
      COUNT(*) as total_records,
      COUNT(CASE WHEN overall_score >= 90 THEN 1 END) as excellent_count,
      COUNT(CASE WHEN overall_score >= 80 AND overall_score < 90 THEN 1 END) as good_count,
      COUNT(CASE WHEN overall_score < 80 THEN 1 END) as needs_attention_count
    FROM data_quality_reports
    WHERE assessed_at >= NOW() - INTERVAL '24 hours'
    GROUP BY 1
    ORDER BY 2 DESC
  `,

  // Remediation effectiveness
  remediationEffectiveness: `
    SELECT
      remediation_type,
      COUNT(*) as total_issues,
      COUNT(CASE WHEN status = 'success' THEN 1 END) as resolved,
      COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
      COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
      ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600), 2) as avg_hours_to_resolve
    FROM remediation_actions
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY 1
  `
};
```

---

## API Specification

### Data Quality API

```typescript
// api/data-quality/routes.ts

import { z } from 'zod';

// Schemas
const ValidationRequestSchema = z.object({
  entityType: z.enum(['customer', 'booking', 'inventory', 'payment']),
  record: z.record(z.any()),
  context: z.record(z.any()).optional()
});

const QualityReportSchema = z.object({
  entityType: z.string(),
  entityId: z.string(),
  overallScore: z.number(),
  dimensionScores: z.record(z.object({
    score: z.number(),
    weight: z.number(),
    issues: z.array(z.object({
      id: z.string(),
      severity: z.enum(['critical', 'high', 'medium', 'low']),
      field: z.string(),
      message: z.string()
    }))
  })),
  validatedAt: z.date()
});

const QualityIssueSchema = z.object({
  id: z.string(),
  entityType: z.string(),
  entityId: z.string(),
  severity: z.enum(['critical', 'high', 'medium', 'low']),
  dimension: z.enum(['accuracy', 'completeness', 'consistency', 'timeliness', 'validity', 'uniqueness']),
  field: z.string(),
  message: z.string(),
  rule: z.string(),
  status: z.enum(['open', 'in_progress', 'resolved', 'ignored']),
  createdAt: z.date()
});

const RemediationActionSchema = z.object({
  issueId: z.string(),
  type: z.enum(['auto_fix', 'suggest', 'escalate']),
  action: z.string(),
  status: z.enum(['success', 'failed', 'pending']),
  details: z.record(z.any())
});

const ProfileRequestSchema = z.object({
  tables: z.array(z.string())
});

const TableProfileSchema = z.object({
  tableName: z.string(),
  rowCount: z.number(),
  columns: z.array(z.object({
    columnName: z.string(),
    dataType: z.string(),
    nullPercentage: z.number(),
    uniquePercentage: z.number(),
    qualityScore: z.number(),
    recommendations: z.array(z.string())
  }))
});

// Routes
export const dataQualityRoutes = {
  // Validation
  'POST /api/data-quality/validate': {
    summary: 'Validate data record',
    request: ValidationRequestSchema,
    response: z.object({
      valid: z.boolean(),
      score: z.number(),
      issues: z.array(z.any()),
      blocked: z.array(z.any()),
      recommendations: z.array(z.string())
    })
  },

  'POST /api/data-quality/validate-batch': {
    summary: 'Validate multiple records',
    request: z.object({
      entityType: z.string(),
      records: z.array(z.record(z.any()))
    }),
    response: z.object({
      totalRecords: z.number(),
      validRecords: z.number(),
      invalidRecords: z.number(),
      passRate: z.number(),
      issues: z.array(z.any())
    })
  },

  // Quality Reports
  'GET /api/data-quality/reports/:entityType/:entityId': {
    summary: 'Get quality report for entity',
    response: QualityReportSchema
  },

  'GET /api/data-quality/reports': {
    summary: 'List quality reports',
    query: z.object({
      entityType: z.string().optional(),
      minScore: z.number().optional(),
      from: z.string().datetime().optional(),
      to: z.string().datetime().optional()
    }),
    response: z.array(QualityReportSchema)
  },

  // Issues Management
  'GET /api/data-quality/issues': {
    summary: 'List quality issues',
    query: z.object({
      entityType: z.string().optional(),
      severity: z.enum(['critical', 'high', 'medium', 'low']).optional(),
      status: z.enum(['open', 'in_progress', 'resolved', 'ignored']).optional(),
      limit: z.number().default(50)
    }),
    response: z.array(QualityIssueSchema)
  },

  'POST /api/data-quality/issues/:issueId/resolve': {
    summary: 'Mark issue as resolved',
    request: z.object({
      resolution: z.string(),
      resolvedBy: z.string()
    }),
    response: QualityIssueSchema
  },

  'POST /api/data-quality/issues/:issueId/ignore': {
    summary: 'Ignore issue',
    request: z.object({
      reason: z.string(),
      ignoredBy: z.string()
    }),
    response: QualityIssueSchema
  },

  // Remediation
  'POST /api/data-quality/remediate': {
    summary: 'Remediate quality issues',
    request: z.object({
      entityType: z.string(),
      entityId: z.string(),
      issueIds: z.array(z.string())
    }),
    response: z.object({
      entityId: z.string(),
      actions: z.array(RemediationActionSchema),
      success: z.boolean()
    })
  },

  'GET /api/data-quality/remediations/:remediationId': {
    summary: 'Get remediation status',
    response: z.object({
      remediationId: z.string(),
      status: z.enum(['pending', 'in_progress', 'completed', 'failed']),
      actions: z.array(RemediationActionSchema)
    })
  },

  // Profiling
  'POST /api/data-quality/profile': {
    summary: 'Profile database tables',
    request: ProfileRequestSchema,
    response: z.array(TableProfileSchema)
  },

  'GET /api/data-quality/profile/:tableName': {
    summary: 'Get table profile',
    response: TableProfileSchema
  },

  // Metrics
  'GET /api/data-quality/metrics': {
    summary: 'Get quality metrics',
    query: z.object({
      entityType: z.string().optional(),
      period: z.enum(['hour', 'day', 'week', 'month']).default('day')
    }),
    response: z.object({
      period: z.string(),
      totalValidations: z.number(),
      passRate: z.number(),
      averageScore: z.number(),
      issuesBySeverity: z.record(z.number()),
      topIssues: z.array(z.object({
        rule: z.string(),
        count: z.number(),
        severity: z.string()
      }))
    })
  },

  // Rules Management
  'GET /api/data-quality/rules': {
    summary: 'List quality rules',
    query: z.object({
      entityType: z.string().optional(),
      dimension: z.string().optional(),
      enabled: z.boolean().optional()
    }),
    response: z.array(z.object({
      id: z.string(),
      name: z.string(),
      dimension: z.string(),
      entityType: z.string(),
      severity: z.string(),
      enabled: z.boolean()
    }))
  },

  'PUT /api/data-quality/rules/:ruleId': {
    summary: 'Update quality rule',
    request: z.object({
      enabled: z.boolean().optional(),
      severity: z.enum(['critical', 'high', 'medium', 'low']).optional(),
      action: z.enum(['block', 'warn', 'log', 'remediate']).optional()
    }),
    response: z.any()
  }
};
```

---

## Testing Scenarios

### Data Quality Tests

```typescript
// tests/data-quality/scenarios.ts

interface TestScenario {
  name: string;
  description: string;
  test: () => Promise<void>;
}

export const dataQualityTests: TestScenario[] = [
  {
    name: 'Required Field Validation',
    description: 'Verify required fields are enforced',
    test: async () => {
      const engine = new QualityRulesEngine();
      const result = await engine.validate('customer', {
        name: 'John Doe'
        // Missing email (required)
      });

      expect(result.valid).toBe(false);
      expect(result.blocked.some(i => i.rule === 'CUST_001')).toBe(true);
    }
  },

  {
    name: 'Email Format Validation',
    description: 'Verify email format is validated',
    test: async () => {
      const engine = new QualityRulesEngine();
      const result = await engine.validate('customer', {
        email: 'invalid-email'
      });

      expect(result.valid).toBe(false);
      expect(result.issues.some(i => i.rule === 'CUST_002')).toBe(true);
    }
  },

  {
    name: 'Phone Auto-format',
    description: 'Verify phone numbers can be auto-formatted',
    test: async () => {
      const remediation = new DataQualityRemediationEngine();
      const result = await remediation.remediate('customer', 'cust-123', [{
        id: 'issue-1',
        severity: 'medium',
        dimension: DataQualityDimension.VALIDITY,
        field: 'phone',
        message: 'Phone format invalid',
        rule: 'CUST_003',
        timestamp: new Date()
      }]);

      expect(result.actions.some(a => a.type === 'auto_fix')).toBe(true);
    }
  },

  {
    name: 'Cross-field Validation',
    description: 'Verify end date after start date',
    test: async () => {
      const engine = new QualityRulesEngine();
      const result = await engine.validate('booking', {
        startDate: '2026-06-01',
        endDate: '2026-05-01' // Before start date
      });

      expect(result.valid).toBe(false);
      expect(result.issues.some(i => i.rule === 'BOOK_002')).toBe(true);
    }
  },

  {
    name: 'Quality Score Calculation',
    description: 'Verify quality scores are calculated correctly',
    test: async () => {
      const calculator = new DataQualityScoreCalculator();
      const score = calculator.calculateEntityScore('customer', {
        email: 'john@example.com',
        name: 'John Doe'
      }, {
        valid: true,
        issues: [],
        blocked: [],
        score: 95
      });

      expect(score.overallScore).toBeGreaterThan(90);
      expect(score.grade).toBe('A');
    }
  },

  {
    name: 'Data Profiling',
    description: 'Verify table profiling works',
    test: async () => {
      const profiler = new DataProfilingService();
      const profile = await profiler.profileTable('customers');

      expect(profile.rowCount).toBeGreaterThanOrEqual(0);
      expect(profile.columns).toBeDefined();
    }
  }
];
```

---

## Metrics & Monitoring

### Data Quality KPIs

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| **Overall Quality Score** | Average data quality score | > 90 | < 85 |
| **Pass Rate** | % of validations passing | > 95% | < 90% |
| **Critical Issues** | Open critical issues | 0 | > 0 |
| **Time to Remediate** | Average time to fix issues | < 4 hours | > 24 hours |
| **Data Freshness** | Age of stalest data | < 24 hours | > 48 hours |
| **Completeness** | % of required fields filled | 100% | < 95% |
| **Uniqueness** | % of duplicate-free records | 100% | < 99% |

### Dashboard Queries

```promql
# Overall quality score
avg(data_quality_score{entity_type="customer"})

# Validation pass rate
rate(data_quality_validations_total{status="pass"}[5m]) /
rate(data_quality_validations_total[5m])

# Issues by severity
sum by (severity) (data_quality_issues{status="open"})

# Quality score trend
avg_over_time(data_quality_score[1d])

# Top failing rules
topk(10, sum by (rule) (rate(data_quality_violations_total[1h])))
```

---

**Document Version:** 1.0

**Last Updated:** 2026-04-26

**Related Documents:**
- [DATA_GOVERNANCE_MASTER_INDEX.md](./DATA_GOVERNANCE_MASTER_INDEX.md)
- [DATA_GOVERNANCE_02_LINEAGE.md](./DATA_GOVERNANCE_02_LINEAGE.md) - Next document
