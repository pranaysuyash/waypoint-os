# FIELD_01_TECHNICAL_DEEP_DIVE

> Part 1 of SmartCombobox & Field Editing Deep Dive
>
> **Series:** Field Editing, Autocomplete, Validation & Change Tracking
>
> **Next:** [FIELD_02_UX_UI_DEEP_DIVE](./FIELD_02_UX_UI_DEEP_DIVE.md)

---

## Technical Architecture Overview

The field editing system provides intelligent, validated, and tracked form inputs across the entire application. It powers everything from customer names to complex supplier selections.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [SmartCombobox Engine](#2-smartcombobox-engine)
3. [Validation Framework](#3-validation-framework)
4. [Change Tracking System](#4-change-tracking-system)
5. [Conflict Resolution](#5-conflict-resolution)
6. [Field Type Registry](#6-field-type-registry)
7. [Performance Optimization](#7-performance-optimization)

---

## 1. System Architecture

### 1.1 Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FIELD EDITING ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                         FieldProvider                               │
    │  (Context for field state, validation, change tracking)             │
    └─────────────────────────────┬───────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  FieldSet       │ │  FieldGroup     │ │  FieldArray     │
    │  (Collection)   │ │  (Section)      │ │  (Repeated)     │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             └───────────────────┼───────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │     SmartField         │
                    │  (Base field wrapper)  │
                    └────────────┬───────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  SmartCombobox  │ │  SmartInput     │ │  SmartDate      │
    │  (Select +      │ │  (Text/Number/  │ │  (Date picker)  │
    │   Autocomplete) │ │   Email/Tel)    │ │                 │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FIELD DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    USER INPUT
        │
        ▼
    ┌──────────────┐
    │   onChange   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Normalize   │ ◄── Format/type coercion
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Validate    │ ◄── Schema rules
    └──────┬───────┘
           │
      ┌────┴────┐
      │         │
      ▼         ▼
   ┌─────┐  ┌─────────┐
   │ Valid │  │ Invalid │
   └──┬──┘  └────┬────┘
      │          │
      ▼          ▼
   ┌─────┐  ┌─────────┐
   │Update│  │ Show   │
   │State │  │Error   │
   └──┬──┘  └─────────┘
      │
      ▼
    ┌──────────────┐
    │ Track Change │ ◄── Record delta
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Propagate   │ ◄── Parent context
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Persist     │ ◄── Optimistic updates
    └──────────────┘
```

### 1.3 Core Interfaces

```typescript
/**
 * Base field configuration
 */
interface FieldConfig<T = any> {
  /** Unique field identifier */
  name: string;

  /** Field label */
  label: string;

  /** Field type */
  type: FieldType;

  /** Default value */
  defaultValue?: T;

  /** Is field required */
  required?: boolean;

  /** Validation rules */
  validation?: ValidationRule[];

  /** Field-specific options */
  options?: FieldOptions;

  /** Help text */
  helpText?: string;

  /** Placeholder text */
  placeholder?: string;

  /** Is field disabled */
  disabled?: boolean;

  /** Is field read-only */
  readOnly?: boolean;

  /** Field visibility condition */
  visibleIf?: (values: Record<string, any>) => boolean;

  /** Field value dependencies */
  dependsOn?: string[];

  /** Custom change handler */
  onChange?: (value: T, prevValue: T) => void | Promise<void>;

  /** Debounce delay (ms) for onChange */
  debounceMs?: number;
}

/**
 * Field value state
 */
interface FieldState<T = any> {
  /** Current value */
  value: T;

  /** Previous value */
  prevValue?: T;

  /** Is field dirty (has unsaved changes) */
  dirty: boolean;

  /** Is field touched (has been blurred) */
  touched: boolean;

  /** Validation errors */
  errors: FieldError[];

  /** Is field validating */
  validating: boolean;

  /** Is field disabled */
  disabled: boolean;

  /** Is field focused */
  focused: boolean;
}

/**
 * Supported field types
 */
enum FieldType {
  // Basic inputs
  TEXT = 'text',
  NUMBER = 'number',
  EMAIL = 'email',
  TEL = 'tel',
  URL = 'url',
  TEXTAREA = 'textarea',

  // Selection
  SELECT = 'select',
  MULTISELECT = 'multiselect',
  COMBOBOX = 'combobox',
  CHECKBOX = 'checkbox',
  RADIO = 'radio',
  TOGGLE = 'toggle',

  // Date/Time
  DATE = 'date',
  TIME = 'time',
  DATETIME = 'datetime',
  DATERANGE = 'daterange',

  // Special
  CURRENCY = 'currency',
  PERCENTAGE = 'percentage',
  RATING = 'rating',
  FILE = 'file',
  COLOR = 'color',

  // Complex
  ARRAY = 'array',
  OBJECT = 'object',
  REFERENCE = 'reference'
}
```

---

## 2. SmartCombobox Engine

### 2.1 Combobox Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SMARTCOMBOBOX ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                        SmartCombobox                                │
    │                                                                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
    │  │   Trigger   │  │   Input    │  │  Selected   │                 │
    │  │  (Button)   │  │  (Search)  │  │   Tags      │                 │
    │  └─────────────┘  └─────────────┘  └─────────────┘                 │
    │         │               │                   │                      │
    │         └───────────────┴───────────────────┘                      │
    │                         │                                           │
    │                         ▼                                           │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │                     Dropdown Panel                          │   │
    │  │                                                             │   │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │
    │  │  │   Search    │  │   Filter    │  │  Create New │          │   │
    │  │  │    Input    │  │   Chips    │  │    Option   │          │   │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘          │   │
    │  │                                                             │   │
    │  │  ┌─────────────────────────────────────────────────────┐   │   │
    │  │  │                   Options List                      │   │   │
    │  │  │                                                     │   │   │
    │  │  │  ┌───────────────────────────────────────────────┐ │   │   │
    │  │  │  │ Option 1                     (highlighted)    │ │   │   │
    │  │  │  │ ┌────┐ ┌────────────────┐ ┌────────────────┐  │ │   │   │
    │  │  │  │ │Icon│ │ Primary Text   │ │ Secondary      │  │ │   │   │
    │  │  │  │ └────┘ │                │ │ Text           │  │ │   │   │
    │  │  │  └───────────────────────────────────────────────┘ │   │   │
    │  │  │                                                     │   │   │
    │  │  │  ┌───────────────────────────────────────────────┐ │   │   │
    │  │  │  │ Option 2                                       │ │   │   │
    │  │  │  └───────────────────────────────────────────────┘ │   │   │
    │  │  │                                                     │   │   │
    │  │  │  ┌───────────────────────────────────────────────┐ │   │   │
    │  │  │  │ Option 3                                       │ │   │   │
    │  │  │  └───────────────────────────────────────────────┘ │   │   │
    │  │  │                                                     │   │   │
    │  │  │  ┌───────────────────────────────────────────────┐ │   │   │
    │  │  │  │ Create "New Option" as new entry...           │ │   │   │
    │  │  │  └───────────────────────────────────────────────┘ │   │   │
    │  │  │                                                     │   │   │
    │  │  └─────────────────────────────────────────────────────┘   │   │
    │  │                                                             │   │
    │  │  ┌─────────────────────────────────────────────────────┐   │   │
    │  │  │                   Footer                             │   │   │
    │  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │   │
    │  │  │  │   Select    │  │    Clear    │  │   Load      │  │   │   │
    │  │  │  │    All      │  │   Filter    │ │    More     │  │   │   │
    │  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │   │
    │  │  └─────────────────────────────────────────────────────┘   │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
```

### 2.2 SmartCombobox Configuration

```typescript
/**
 * SmartCombobox specific configuration
 */
interface SmartComboboxConfig<T = any> extends FieldConfig<T | T[]> {
  /** Combobox mode */
  mode: 'single' | 'multiple' | 'tags';

  /** Options source */
  options: ComboboxOptions<T>;

  /** Search configuration */
  search?: ComboboxSearchConfig;

  /** Display configuration */
  display?: ComboboxDisplayConfig;

  /** Creation configuration */
  create?: ComboboxCreateConfig;

  /** Virtual scrolling for large lists */
  virtualScroll?: boolean;

  /** Load more configuration */
  loadMore?: ComboboxLoadMoreConfig;
}

/**
 * Options source
 */
type ComboboxOptions<T> =
  | T[] // Static array
  | { type: 'static'; data: T[] }
  | { type: 'api'; endpoint: string; params?: Record<string, any> }
  | { type: 'function'; loader: () => Promise<T[]> }
  | { type: 'paginated'; loader: (page: number, pageSize: number) => Promise<T[]> };

/**
 * Search configuration
 */
interface ComboboxSearchConfig {
  /** Enable search functionality */
  enabled: boolean;

  /** Minimum characters to trigger search */
  minLength?: number;

  /** Search debounce (ms) */
  debounceMs?: number;

  /** Search fields in option object */
  searchFields?: string[];

  /** Custom search function */
  searchFn?: (query: string, options: any[]) => any[];

  /** Show "no results" message */
  noResultsMessage?: string;

  /** Show "create new" option when no results */
  showCreateOption?: boolean;
}

/**
 * Display configuration
 */
interface ComboboxDisplayConfig {
  /** Field to use as primary label */
  labelField: string;

  /** Field to use as secondary label */
  secondaryLabelField?: string;

  /** Field to use for icon/avatar */
  iconField?: string;

  /** Option template */
  renderOption?: (option: any) => ReactNode;

  /** Selected value template */
  renderValue?: (value: any) => ReactNode;

  /** Group by field */
  groupBy?: string;

  /** Sort options */
  sortBy?: string | ((a: any, b: any) => number);
}

/**
 * Create new option configuration
 */
interface ComboboxCreateConfig {
  /** Allow creating new options */
  allow: boolean;

  /** Label for create option */
  label?: string;

  /** Validate new option before creation */
  validate?: (value: string) => boolean | Promise<boolean>;

  /** Transform new option value */
  transform?: (value: string) => any;

  /** Hook after creation */
  onCreate?: (option: any) => void | Promise<void>;
}

/**
 * Load more configuration
 */
interface ComboboxLoadMoreConfig {
  /** Enable infinite scroll */
  enabled: boolean;

  /** Threshold to trigger load more (pixels from bottom) */
  threshold?: number;

  /** Page size */
  pageSize?: number;

  /** Loading indicator */
  showLoading?: boolean;
}
```

### 2.3 Search & Filtering Engine

```typescript
/**
 * Smart search engine for combobox
 */
class ComboboxSearchEngine {
  private searchIndex: Map<string, Set<any>> = new Map();
  private options: any[] = [];
  private config: ComboboxSearchConfig;

  constructor(config: ComboboxSearchConfig) {
    this.config = {
      enabled: true,
      minLength: 0,
      debounceMs: 200,
      searchFields: ['label', 'value'],
      ...config
    };
  }

  /**
   * Index options for fast search
   */
  indexOptions(options: any[]): void {
    this.options = options;
    this.searchIndex.clear();

    options.forEach(option => {
      this.config.searchFields.forEach(field => {
        const value = this.getNestedValue(option, field);
        if (value) {
          const tokens = this.tokenize(value.toString());
          tokens.forEach(token => {
            if (!this.searchIndex.has(token)) {
              this.searchIndex.set(token, new Set());
            }
            this.searchIndex.get(token)!.add(option);
          });
        }
      });
    });
  }

  /**
   * Search options by query
   */
  search(query: string): any[] {
    if (!query || !this.config.enabled) {
      return this.options;
    }

    const tokens = this.tokenize(query);
    if (tokens.length === 0) {
      return this.options;
    }

    // Use custom search function if provided
    if (this.config.searchFn) {
      return this.config.searchFn(query, this.options);
    }

    // Find options matching all tokens
    const resultSets = tokens.map(token => this.searchIndex.get(token));
    const intersection = this.setIntersection(resultSets.filter(Boolean) as Set<any>[]);

    // Score and sort by relevance
    return this.scoreResults(query, Array.from(intersection));
  }

  /**
   * Tokenize search query
   */
  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '') // Remove accents
      .split(/\s+/)
      .filter(t => t.length > 0);
  }

  /**
   * Get nested value from object
   */
  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((o, key) => o?.[key], obj);
  }

  /**
   * Intersect multiple sets
   */
  private setIntersection<T>(sets: Set<T>[]): Set<T> {
    if (sets.length === 0) return new Set();
    if (sets.length === 1) return sets[0];

    return sets.reduce((acc, set) => {
      return new Set([...acc].filter(x => set.has(x)));
    });
  }

  /**
   * Score results by relevance
   */
  private scoreResults(query: string, results: any[]): any[] {
    const queryLower = query.toLowerCase();

    return results
      .map(option => ({
        option,
        score: this.calculateScore(queryLower, option)
      }))
      .filter(r => r.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(r => r.option);
  }

  /**
   * Calculate relevance score
   */
  private calculateScore(query: string, option: any): number {
    let score = 0;

    this.config.searchFields.forEach(field => {
      const value = this.getNestedValue(option, field);
      if (value) {
        const valueLower = value.toString().toLowerCase();

        // Exact match gets highest score
        if (valueLower === query) {
          score += 100;
        }
        // Starts with query
        else if (valueLower.startsWith(query)) {
          score += 50;
        }
        // Contains query
        else if (valueLower.includes(query)) {
          score += 10;
        }
        // Fuzzy match
        else {
          score += this.fuzzyMatch(query, valueLower);
        }
      }
    });

    return score;
  }

  /**
   * Simple fuzzy match scoring
   */
  private fuzzyMatch(query: string, text: string): number {
    let queryIndex = 0;
    let score = 0;

    for (let i = 0; i < text.length && queryIndex < query.length; i++) {
      if (text[i] === query[queryIndex]) {
        score += 1;
        queryIndex++;
      }
    }

    return queryIndex === query.length ? score / text.length * 5 : 0;
  }
}
```

### 2.4 Virtual Scrolling Implementation

```typescript
/**
 * Virtual scroll hook for combobox
 */
function useComboboxVirtualScroll(options: {
  items: any[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}) {
  const { items, itemHeight, containerHeight, overscan = 3 } = options;

  const [scrollTop, setScrollTop] = useState(0);

  // Calculate visible range
  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.ceil((scrollTop + containerHeight) / itemHeight);

  // Add overscan
  const startIndex = Math.max(0, visibleStart - overscan);
  const endIndex = Math.min(items.length - 1, visibleEnd + overscan);

  // Calculate offset
  const offsetY = startIndex * itemHeight;

  // Visible items
  const visibleItems = items.slice(startIndex, endIndex + 1);

  // Total height
  const totalHeight = items.length * itemHeight;

  return {
    visibleItems,
    totalHeight,
    offsetY,
    onScroll: (e: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(e.currentTarget.scrollTop);
    }
  };
}
```

---

## 3. Validation Framework

### 3.1 Validation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VALIDATION FRAMEWORK                                │
└─────────────────────────────────────────────────────────────────────────────┘

    FIELD VALUE CHANGE
             │
             ▼
    ┌──────────────────┐
    │  Pre-Process     │ ◄── Trim, coerce type
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Sync Validate   │ ◄── Required, format, range
    └────────┬─────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   ┌─────────┐  ┌──────────────┐
   │ Errors? │  │ Async Check  │ ◄── Unique, API, custom
   └────┬────┘  └──────┬───────┘
        │              │
        │      ┌───────┴────────┐
        │      │                │
        │      ▼                ▼
        │  ┌─────────┐    ┌─────────┐
        │  │ Valid   │    │ Errors  │
        │  └────┬────┘    └────┬────┘
        │       │              │
        └───────┴──────────────┘
                │
                ▼
        ┌───────────────┐
        │  Show Errors  │
        │  or Continue  │
        └───────────────┘
```

### 3.2 Validation Rules

```typescript
/**
 * Base validation rule interface
 */
interface ValidationRule {
  /** Rule identifier */
  name: string;

  /** Error message */
  message: string | ((value: any) => string);

  /** Validation function */
  validate: (value: any, context: ValidationContext) => boolean | Promise<boolean>;

  /** Run rule only when condition is met */
  when?: (values: Record<string, any>) => boolean;

  /** Run rule asynchronously */
  async?: boolean;
}

/**
 * Validation context
 */
interface ValidationContext {
  /** All field values in form */
  values: Record<string, any>;

  /** Current field name */
  fieldName: string;

  /** Field configuration */
  field: FieldConfig;

  /** Form metadata */
  meta?: Record<string, any>;
}

/**
 * Built-in validation rules
 */
const VALIDATION_RULES = {
  required: {
    name: 'required',
    message: 'This field is required',
    validate: (value: any) => {
      if (Array.isArray(value)) return value.length > 0;
      if (typeof value === 'boolean') return true; // Checkboxes handled separately
      return value !== null && value !== undefined && value !== '';
    }
  },

  minLength: {
    name: 'minLength',
    message: (min: number) => `Must be at least ${min} characters`,
    validate: (value: string, context: ValidationContext) => {
      const min = context.field.validation?.find(r => r.name === 'minLength')?.args?.[0];
      return !value || value.length >= min;
    }
  },

  maxLength: {
    name: 'maxLength',
    message: (max: number) => `Must be no more than ${max} characters`,
    validate: (value: string, context: ValidationContext) => {
      const max = context.field.validation?.find(r => r.name === 'maxLength')?.args?.[0];
      return !value || value.length <= max;
    }
  },

  pattern: {
    name: 'pattern',
    message: 'Invalid format',
    validate: (value: string, context: ValidationContext) => {
      const pattern = context.field.validation?.find(r => r.name === 'pattern')?.args?.[0];
      if (!pattern) return true;
      return !value || new RegExp(pattern).test(value);
    }
  },

  email: {
    name: 'email',
    message: 'Must be a valid email address',
    validate: (value: string) => {
      if (!value) return true;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value);
    }
  },

  url: {
    name: 'url',
    message: 'Must be a valid URL',
    validate: (value: string) => {
      if (!value) return true;
      try {
        new URL(value);
        return true;
      } catch {
        return false;
      }
    }
  },

  min: {
    name: 'min',
    message: (min: number) => `Must be at least ${min}`,
    validate: (value: number, context: ValidationContext) => {
      const min = context.field.validation?.find(r => r.name === 'min')?.args?.[0];
      return value === null || value === undefined || value >= min;
    }
  },

  max: {
    name: 'max',
    message: (max: number) => `Must be no more than ${max}`,
    validate: (value: number, context: ValidationContext) => {
      const max = context.field.validation?.find(r => r.name === 'max')?.args?.[0];
      return value === null || value === undefined || value <= max;
    }
  },

  range: {
    name: 'range',
    message: (min: number, max: number) => `Must be between ${min} and ${max}`,
    validate: (value: number, context: ValidationContext) => {
      const rule = context.field.validation?.find(r => r.name === 'range');
      const [min, max] = rule?.args || [];
      return value === null || value === undefined || (value >= min && value <= max);
    }
  },

  dateMin: {
    name: 'dateMin',
    message: (date: Date) => `Must be after ${formatDate(date)}`,
    validate: (value: Date, context: ValidationContext) => {
      const min = context.field.validation?.find(r => r.name === 'dateMin')?.args?.[0];
      return !value || !min || value >= new Date(min);
    }
  },

  dateMax: {
    name: 'dateMax',
    message: (date: Date) => `Must be before ${formatDate(date)}`,
    validate: (value: Date, context: ValidationContext) => {
      const max = context.field.validation?.find(r => r.name === 'dateMax')?.args?.[0];
      return !value || !max || value <= new Date(max);
    }
  },

  unique: {
    name: 'unique',
    message: 'This value is already taken',
    async: true,
    validate: async (value: any, context: ValidationContext) => {
      const checker = context.field.validation?.find(r => r.name === 'unique')?.args?.[0];
      if (!checker) return true;
      return await checker(value, context);
    }
  },

  confirmed: {
    name: 'confirmed',
    message: 'Values do not match',
    validate: (value: any, context: ValidationContext) => {
      const confirmField = context.field.validation?.find(r => r.name === 'confirmed')?.args?.[0];
      if (!confirmField) return true;
      return value === context.values[confirmField];
    }
  },

  custom: {
    name: 'custom',
    message: 'Invalid value',
    validate: (value: any, context: ValidationContext) => {
      const fn = context.field.validation?.find(r => r.name === 'custom')?.args?.[0];
      if (!fn) return true;
      return fn(value, context);
    }
  }
};
```

### 3.3 Validation Engine

```typescript
/**
 * Field validation engine
 */
class ValidationEngine {
  private rules: Map<string, ValidationRule> = new Map();

  constructor() {
    // Register built-in rules
    Object.entries(VALIDATION_RULES).forEach(([name, rule]) => {
      this.rules.set(name, rule);
    });
  }

  /**
   * Register a custom validation rule
   */
  registerRule(name: string, rule: ValidationRule): void {
    this.rules.set(name, rule);
  }

  /**
   * Validate a field value
   */
  async validateField(
    value: any,
    field: FieldConfig,
    context: ValidationContext
  ): Promise<FieldError[]> {
    const errors: FieldError[] = [];

    if (!field.validation || field.validation.length === 0) {
      return errors;
    }

    // Separate sync and async rules
    const syncRules = field.validation.filter(r => !r.async);
    const asyncRules = field.validation.filter(r => r.async);

    // Run sync validation first
    for (const rule of syncRules) {
      if (rule.when && !rule.when(context.values)) {
        continue;
      }

      const ruleDef = this.rules.get(rule.name);
      if (!ruleDef) continue;

      const valid = await ruleDef.validate(value, context);
      if (!valid) {
        errors.push({
          field: field.name,
          rule: rule.name,
          message: typeof rule.message === 'function'
            ? rule.message(value)
            : rule.message || ruleDef.message
        });
      }
    }

    // Run async validation if sync validation passed
    if (errors.length === 0 && asyncRules.length > 0) {
      for (const rule of asyncRules) {
        if (rule.when && !rule.when(context.values)) {
          continue;
        }

        const ruleDef = this.rules.get(rule.name);
        if (!ruleDef) continue;

        const valid = await ruleDef.validate(value, context);
        if (!valid) {
          errors.push({
            field: field.name,
            rule: rule.name,
            message: typeof rule.message === 'function'
              ? rule.message(value)
              : rule.message || ruleDef.message
          });
        }
      }
    }

    return errors;
  }

  /**
   * Validate multiple fields
   */
  async validateFields(
    values: Record<string, any>,
    fields: FieldConfig[]
  ): Promise<Record<string, FieldError[]>> {
    const errors: Record<string, FieldError[]> = {};

    // Build dependency graph
    const graph = this.buildDependencyGraph(fields);

    // Topological sort for validation order
    const sortedFields = this.topologicalSort(fields, graph);

    // Validate each field
    for (const field of sortedFields) {
      const context: ValidationContext = {
        values,
        fieldName: field.name,
        field
      };

      const fieldErrors = await this.validateField(
        values[field.name],
        field,
        context
      );

      if (fieldErrors.length > 0) {
        errors[field.name] = fieldErrors;
      }
    }

    return errors;
  }

  /**
   * Build field dependency graph
   */
  private buildDependencyGraph(fields: FieldConfig[]): Map<string, string[]> {
    const graph = new Map<string, string[]>();

    for (const field of fields) {
      const dependencies: string[] = [];

      // Add dependsOn dependencies
      if (field.dependsOn) {
        dependencies.push(...field.dependsOn);
      }

      // Add validation dependencies (e.g., confirmed field)
      if (field.validation) {
        for (const rule of field.validation) {
          if (rule.name === 'confirmed' && rule.args?.[0]) {
            dependencies.push(rule.args[0]);
          }
          if (rule.when) {
            // Extract field names from when condition
            const fieldNames = rule.when.toString().match(/\[['"](.*?)['"]\]/g);
            if (fieldNames) {
              dependencies.push(...fieldNames.map(f => f.replace(/['"\[\]]/g, '')));
            }
          }
        }
      }

      graph.set(field.name, dependencies);
    }

    return graph;
  }

  /**
   * Topological sort for dependency resolution
   */
  private topologicalSort(
    fields: FieldConfig[],
    graph: Map<string, string[]>
  ): FieldConfig[] {
    const sorted: FieldConfig[] = [];
    const visited = new Set<string>();
    const fieldMap = new Map(fields.map(f => [f.name, f]));

    const visit = (fieldName: string) => {
      if (visited.has(fieldName)) return;
      visited.add(fieldName);

      const dependencies = graph.get(fieldName) || [];
      for (const dep of dependencies) {
        if (fieldMap.has(dep)) {
          visit(dep);
        }
      }

      const field = fieldMap.get(fieldName);
      if (field) {
        sorted.push(field);
      }
    };

    for (const field of fields) {
      visit(field.name);
    }

    return sorted;
  }
}

/**
 * Field error interface
 */
interface FieldError {
  field: string;
  rule: string;
  message: string;
}
```

---

## 4. Change Tracking System

### 4.1 Change Tracking Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CHANGE TRACKING SYSTEM                               │
└─────────────────────────────────────────────────────────────────────────────┘

    FIELD VALUE CHANGE
             │
             ▼
    ┌──────────────────┐
    │  Compute Delta   │ ◄── Deep diff
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Create Change   │
    │     Record       │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Add to Stack    │ ◄── Undo/redo support
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Mark Dirty      │ ◄── Form-level dirty state
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Emit Event      │ ◄── onChange callback
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Persist to      │
    │  Backend         │ ◄── Optimistic update
    └──────────────────┘
```

### 4.2 Change Record

```typescript
/**
 * Field change record
 */
interface FieldChange {
  /** Unique change ID */
  id: string;

  /** Field name */
  field: string;

  /** Previous value */
  previous: any;

  /** New value */
  current: any;

  /** Change type */
  type: 'set' | 'push' | 'pull' | 'swap' | 'move';

  /** Timestamp */
  timestamp: Date;

  /** User who made change */
  userId?: string;

  /** Change source */
  source: 'user' | 'api' | 'merge' | 'undo' | 'redo';

  /** Nested path for array/object changes */
  path?: string[];

  /** Index for array operations */
  index?: number;

  /** Additional metadata */
  meta?: Record<string, any>;
}

/**
 * Change stack for undo/redo
 */
interface ChangeStack {
  /** Undo stack */
  undo: FieldChange[];

  /** Redo stack */
  redo: FieldChange[];

  /** Maximum stack size */
  maxSize: number;

  /** Current position */
  position: number;
}

/**
 * Change tracking options
 */
interface ChangeTrackingOptions {
  /** Enable undo/redo */
  enableUndoRedo?: boolean;

  /** Maximum undo stack size */
  maxUndoStack?: number;

  /** Track changes at field level */
  trackFieldChanges?: boolean;

  /** Track deep changes in objects/arrays */
  trackDeepChanges?: boolean;

  /** Callback on change */
  onChange?: (changes: FieldChange[]) => void;

  /** Callback on dirty state change */
  onDirtyChange?: (dirty: boolean) => void;
}
```

### 4.3 Diff Engine

```typescript
/**
 * Deep diff engine for change tracking
 */
class DiffEngine {
  /**
   * Compute diff between two values
   */
  diff(previous: any, current: any, path: string[] = []): FieldChange | null {
    // Same value, no change
    if (previous === current) {
      return null;
    }

    // Both null or undefined
    if (previous == null && current == null) {
      return null;
    }

    // Type change
    if (typeof previous !== typeof current) {
      return this.createChange(path, previous, current, 'set');
    }

    // Array diff
    if (Array.isArray(previous) && Array.isArray(current)) {
      return this.diffArray(previous, current, path);
    }

    // Object diff
    if (this.isPlainObject(previous) && this.isPlainObject(current)) {
      return this.diffObject(previous, current, path);
    }

    // Primitive value change
    return this.createChange(path, previous, current, 'set');
  }

  /**
   * Diff arrays
   */
  private diffArray(
    previous: any[],
    current: any[],
    path: string[]
  ): FieldChange | null {
    // Length change
    if (previous.length !== current.length) {
      return this.createChange(path, previous, current, 'set');
    }

    // Element-wise comparison
    for (let i = 0; i < previous.length; i++) {
      const elementDiff = this.diff(previous[i], current[i], [...path, String(i)]);
      if (elementDiff) {
        return elementDiff;
      }
    }

    return null;
  }

  /**
   * Diff objects
   */
  private diffObject(
    previous: Record<string, any>,
    current: Record<string, any>,
    path: string[]
  ): FieldChange | null {
    const keys = new Set([...Object.keys(previous), ...Object.keys(current)]);

    for (const key of keys) {
      const prevValue = previous[key];
      const currValue = current[key];

      const keyDiff = this.diff(prevValue, currValue, [...path, key]);
      if (keyDiff) {
        return keyDiff;
      }
    }

    return null;
  }

  /**
   * Create change record
   */
  private createChange(
    path: string[],
    previous: any,
    current: any,
    type: FieldChange['type']
  ): FieldChange {
    return {
      id: generateId(),
      field: path[0],
      path,
      previous,
      current,
      type,
      timestamp: new Date(),
      source: 'user'
    };
  }

  /**
   * Check if value is plain object
   */
  private isPlainObject(value: any): boolean {
    return (
      typeof value === 'object' &&
      value !== null &&
      !Array.isArray(value) &&
      !(value instanceof Date) &&
      !(value instanceof RegExp)
    );
  }

  /**
   * Apply a change to a value
   */
  applyChange(value: any, change: FieldChange): any {
    switch (change.type) {
      case 'set':
        return change.current;

      case 'push':
        if (!Array.isArray(value)) return value;
        return [...value, change.current];

      case 'pull':
        if (!Array.isArray(value)) return value;
        return value.filter((v, i) => i !== change.index);

      case 'swap':
        if (!Array.isArray(value)) return value;
        const newArr = [...value];
        [newArr[change.index!], newArr[change.index! + 1]] =
          [newArr[change.index! + 1], newArr[change.index!]];
        return newArr;

      case 'move':
        if (!Array.isArray(value)) return value;
        const movedArr = [...value];
        const [moved] = movedArr.splice(change.index!, 1);
        movedArr.splice(change.index! + 1, 0, moved);
        return movedArr;

      default:
        return value;
    }
  }
}
```

### 4.4 Change Tracker

```typescript
/**
 * Field change tracker
 */
class FieldChangeTracker {
  private stack: ChangeStack = {
    undo: [],
    redo: [],
    maxSize: 50,
    position: -1
  };

  private diffEngine = new DiffEngine();
  private options: ChangeTrackingOptions;
  private dirtyFields = new Set<string>();

  constructor(options: ChangeTrackingOptions = {}) {
    this.options = {
      enableUndoRedo: true,
      maxUndoStack: 50,
      trackFieldChanges: true,
      trackDeepChanges: true,
      ...options
    };
  }

  /**
   * Track a field change
   */
  track(change: FieldChange): void {
    // Add to undo stack
    if (this.options.enableUndoRedo) {
      // Clear redo stack on new change
      this.stack.redo = [];

      // Add to undo stack
      this.stack.undo.push(change);

      // Trim stack if too large
      if (this.stack.undo.length > this.stack.maxSize) {
        this.stack.undo.shift();
      }

      this.stack.position = this.stack.undo.length - 1;
    }

    // Mark field as dirty
    this.dirtyFields.add(change.field);

    // Emit callbacks
    this.options.onChange?.([change]);
    this.options.onDirtyChange?.(true);
  }

  /**
   * Track value change
   */
  trackChange(fieldName: string, previous: any, current: any): void {
    const diff = this.diffEngine.diff(previous, current, [fieldName]);

    if (diff) {
      this.track(diff);
    }
  }

  /**
   * Undo last change
   */
  undo(): FieldChange | null {
    if (!this.options.enableUndoRedo || this.stack.position < 0) {
      return null;
    }

    const change = this.stack.undo[this.stack.position];
    this.stack.redo.push(change);
    this.stack.undo.pop();
    this.stack.position--;

    // Update dirty state
    this.updateDirtyState();

    return change;
  }

  /**
   * Redo last undone change
   */
  redo(): FieldChange | null {
    if (!this.options.enableUndoRedo || this.stack.redo.length === 0) {
      return null;
    }

    const change = this.stack.redo.pop()!;
    this.stack.undo.push(change);
    this.stack.position++;

    // Mark field as dirty
    this.dirtyFields.add(change.field);

    // Emit callbacks
    this.options.onChange?.([change]);
    this.options.onDirtyChange?.(true);

    return change;
  }

  /**
   * Clear all changes (e.g., after save)
   */
  clear(): void {
    this.stack.undo = [];
    this.stack.redo = [];
    this.stack.position = -1;
    this.dirtyFields.clear();

    this.options.onDirtyChange?.(false);
  }

  /**
   * Check if form is dirty
   */
  isDirty(): boolean {
    return this.dirtyFields.size > 0;
  }

  /**
   * Check if specific field is dirty
   */
  isFieldDirty(fieldName: string): boolean {
    return this.dirtyFields.has(fieldName);
  }

  /**
   * Get all changes
   */
  getChanges(): FieldChange[] {
    return [...this.stack.undo];
  }

  /**
   * Get changes for specific field
   */
  getFieldChanges(fieldName: string): FieldChange[] {
    return this.stack.undo.filter(c => c.field === fieldName);
  }

  /**
   * Update dirty state
   */
  private updateDirtyState(): void {
    // Rebuild dirty fields from remaining changes
    this.dirtyFields.clear();

    for (const change of this.stack.undo) {
      this.dirtyFields.add(change.field);
    }

    this.options.onDirtyChange?.(this.dirtyFields.size > 0);
  }
}
```

---

## 5. Conflict Resolution

### 5.1 Conflict Detection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONFLICT RESOLUTION                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    LOCAL CHANGE      SERVER STATE
         │                 │
         ▼                 ▼
    ┌─────────┐       ┌─────────┐
    │ Value A │       │ Value B │
    └────┬────┘       └────┬────┘
         │                 │
         └────────┬────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Compare       │
         │  (Base vs A)   │
         │  (Base vs B)   │
         └────────┬───────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
   ┌──────────┐      ┌──────────┐
   │ Conflict │      │  No      │
   │ Detected │      │ Conflict │
   └────┬─────┘      └────┬─────┘
        │                 │
        ▼                 ▼
   ┌──────────┐      ┌──────────┐
   │ Present  │      │  Merge   │
   │ Options  │      │  Auto    │
   └──────────┘      └──────────┘
```

### 5.2 Resolution Strategies

```typescript
/**
 * Conflict types
 */
enum ConflictType {
  /** Both modified same field */
  SAME_FIELD = 'same_field',

  /** Both modified different fields */
  DIFFERENT_FIELDS = 'different_fields',

  /** One deleted, one modified */
  DELETE_MODIFIED = 'delete_modified',

  /** Both deleted */
  BOTH_DELETED = 'both_deleted',

  /** Array conflicts */
  ARRAY_CONFLICT = 'array_conflict'
}

/**
 * Conflict resolution strategy
 */
enum ResolutionStrategy {
  /** Use local value */
  LOCAL = 'local',

  /** Use server value */
  SERVER = 'server',

  /** Merge both values */
  MERGE = 'merge',

  /** Manual resolution required */
  MANUAL = 'manual'
}

/**
 * Conflict detection result
 */
interface Conflict {
  id: string;
  type: ConflictType;
  field: string;

  /** Base value (last known sync) */
  base: any;

  /** Local value */
  local: any;

  /** Server value */
  server: any;

  /** Detected at */
  detectedAt: Date;

  /** Suggested resolution */
  suggestedStrategy: ResolutionStrategy;

  /** Available strategies */
  availableStrategies: ResolutionStrategy[];
}

/**
 * Conflict resolver
 */
class ConflictResolver {
  /**
   * Detect conflicts between local and server changes
   */
  detect(
    localChanges: FieldChange[],
    serverChanges: FieldChange[],
    baseValues: Record<string, any>
  ): Conflict[] {
    const conflicts: Conflict[] = [];

    // Group changes by field
    const localByField = this.groupByField(localChanges);
    const serverByField = this.groupByField(serverChanges);

    // Check each field
    const allFields = new Set([
      ...Object.keys(localByField),
      ...Object.keys(serverByField)
    ]);

    for (const field of allFields) {
      const localChange = localByField[field];
      const serverChange = serverByField[field];
      const baseValue = baseValues[field];

      if (localChange && serverChange) {
        // Both modified - potential conflict
        const conflict = this.analyzeConflict(
          field,
          baseValue,
          localChange.current,
          serverChange.current
        );

        if (conflict) {
          conflicts.push(conflict);
        }
      }
    }

    return conflicts;
  }

  /**
   * Analyze a potential conflict
   */
  private analyzeConflict(
    field: string,
    base: any,
    local: any,
    server: any
  ): Conflict | null {
    // Check if values are actually different
    if (JSON.stringify(local) === JSON.stringify(server)) {
      return null; // No actual conflict
    }

    // Check if either is same as base
    const localChanged = JSON.stringify(local) !== JSON.stringify(base);
    const serverChanged = JSON.stringify(server) !== JSON.stringify(base);

    if (!localChanged) {
      // Only server changed, auto-resolve to server
      return null;
    }

    if (!serverChanged) {
      // Only local changed, auto-resolve to local
      return null;
    }

    // Both changed - conflict detected
    const type = this.determineConflictType(base, local, server);
    const strategies = this.getAvailableStrategies(type);

    return {
      id: generateId(),
      type,
      field,
      base,
      local,
      server,
      detectedAt: new Date(),
      suggestedStrategy: this.suggestStrategy(type, base, local, server),
      availableStrategies: strategies
    };
  }

  /**
   * Determine conflict type
   */
  private determineConflictType(
    base: any,
    local: any,
    server: any
  ): ConflictType {
    // Check for delete conflicts
    if ((local === null || local === undefined) && (server === null || server === undefined)) {
      return ConflictType.BOTH_DELETED;
    }

    if ((local === null || local === undefined) || (server === null || server === undefined)) {
      return ConflictType.DELETE_MODIFIED;
    }

    // Check for array conflicts
    if (Array.isArray(base) && Array.isArray(local) && Array.isArray(server)) {
      return ConflictType.ARRAY_CONFLICT;
    }

    // Default to same field conflict
    return ConflictType.SAME_FIELD;
  }

  /**
   * Get available resolution strategies for conflict type
   */
  private getAvailableStrategies(type: ConflictType): ResolutionStrategy[] {
    switch (type) {
      case ConflictType.BOTH_DELETED:
        return [ResolutionStrategy.LOCAL, ResolutionStrategy.SERVER];

      case ConflictType.DELETE_MODIFIED:
        return [ResolutionStrategy.LOCAL, ResolutionStrategy.SERVER];

      case ConflictType.ARRAY_CONFLICT:
        return [ResolutionStrategy.LOCAL, ResolutionStrategy.SERVER, ResolutionStrategy.MERGE, ResolutionStrategy.MANUAL];

      default:
        return [ResolutionStrategy.LOCAL, ResolutionStrategy.SERVER, ResolutionStrategy.MANUAL];
    }
  }

  /**
   * Suggest resolution strategy
   */
  private suggestStrategy(
    type: ConflictType,
    base: any,
    local: any,
    server: any
  ): ResolutionStrategy {
    // For delete conflicts, prefer keeping data
    if (type === ConflictType.DELETE_MODIFIED) {
      return local === null || local === undefined
        ? ResolutionStrategy.SERVER
        : ResolutionStrategy.LOCAL;
    }

    // For arrays, try merge
    if (type === ConflictType.ARRAY_CONFLICT) {
      return ResolutionStrategy.MERGE;
    }

    // Default: require manual resolution
    return ResolutionStrategy.MANUAL;
  }

  /**
   * Apply resolution strategy
   */
  applyResolution(conflict: Conflict, strategy: ResolutionStrategy): any {
    switch (strategy) {
      case ResolutionStrategy.LOCAL:
        return conflict.local;

      case ResolutionStrategy.SERVER:
        return conflict.server;

      case ResolutionStrategy.MERGE:
        return this.mergeValues(conflict.base, conflict.local, conflict.server);

      case ResolutionStrategy.MANUAL:
        throw new Error('Manual resolution required');
    }
  }

  /**
   * Merge conflicting values
   */
  private mergeValues(base: any, local: any, server: any): any {
    // Array merge - union with server taking precedence for duplicates
    if (Array.isArray(base) && Array.isArray(local) && Array.isArray(server)) {
      const merged = new Set([...local, ...server]);
      return Array.from(merged);
    }

    // Object merge - recursive
    if (this.isPlainObject(base) && this.isPlainObject(local) && this.isPlainObject(server)) {
      const merged = { ...base };

      // Apply local changes
      for (const key of Object.keys(local)) {
        if (JSON.stringify(local[key]) !== JSON.stringify(base[key])) {
          merged[key] = local[key];
        }
      }

      // Apply server changes (overwrites local)
      for (const key of Object.keys(server)) {
        if (JSON.stringify(server[key]) !== JSON.stringify(base[key])) {
          merged[key] = server[key];
        }
      }

      return merged;
    }

    // Default: server wins
    return server;
  }

  /**
   * Group changes by field
   */
  private groupByField(changes: FieldChange[]): Record<string, FieldChange> {
    const grouped: Record<string, FieldChange> = {};

    for (const change of changes) {
      // Use latest change for each field
      grouped[change.field] = change;
    }

    return grouped;
  }

  /**
   * Check if value is plain object
   */
  private isPlainObject(value: any): boolean {
    return (
      typeof value === 'object' &&
      value !== null &&
      !Array.isArray(value) &&
      !(value instanceof Date)
    );
  }
}
```

---

## 6. Field Type Registry

### 6.1 Field Type Definitions

```typescript
/**
 * Field type registry
 */
class FieldTypeRegistry {
  private types: Map<FieldType, FieldTypeDef> = new Map();

  constructor() {
    this.registerBuiltInTypes();
  }

  /**
   * Register a field type
   */
  register(type: FieldTypeDef): void {
    this.types.set(type.type, type);
  }

  /**
   * Get field type definition
   */
  get(type: FieldType): FieldTypeDef | undefined {
    return this.types.get(type);
  }

  /**
   * Check if type is registered
   */
  has(type: FieldType): boolean {
    return this.types.has(type);
  }

  /**
   * Get all registered types
   */
  getAll(): FieldTypeDef[] {
    return Array.from(this.types.values());
  }

  /**
   * Register built-in field types
   */
  private registerBuiltInTypes(): void {
    // Text input
    this.register({
      type: FieldType.TEXT,
      component: 'SmartInput',
      defaultProps: {
        type: 'text'
      },
      validator: (value: any) => typeof value === 'string',
      normalizer: (value: any) => value?.toString() || ''
    });

    // Number input
    this.register({
      type: FieldType.NUMBER,
      component: 'SmartInput',
      defaultProps: {
        type: 'number'
      },
      validator: (value: any) => typeof value === 'number' || !value,
      normalizer: (value: any) => value === '' ? null : Number(value)
    });

    // Email input
    this.register({
      type: FieldType.EMAIL,
      component: 'SmartInput',
      defaultProps: {
        type: 'email',
        autoCapitalize: 'off',
        autoCorrect: 'off'
      },
      validator: (value: any) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
      normalizer: (value: any) => value?.toLowerCase().trim() || ''
    });

    // Combobox
    this.register({
      type: FieldType.COMBOBOX,
      component: 'SmartCombobox',
      defaultProps: {
        mode: 'single'
      },
      validator: (value: any) => true, // Value depends on options
      normalizer: (value: any) => value
    });

    // Date picker
    this.register({
      type: FieldType.DATE,
      component: 'SmartDatePicker',
      defaultProps: {
        format: 'yyyy-MM-dd'
      },
      validator: (value: any) => !value || value instanceof Date || !isNaN(Date.parse(value)),
      normalizer: (value: any) => value ? new Date(value) : null
    });

    // Currency
    this.register({
      type: FieldType.CURRENCY,
      component: 'SmartCurrencyInput',
      defaultProps: {
        currency: 'USD'
      },
      validator: (value: any) => typeof value === 'number' || !value,
      normalizer: (value: any) => {
        if (typeof value === 'string') {
          return parseFloat(value.replace(/[^\d.-]/g, '')) || 0;
        }
        return value || 0;
      }
    });
  }
}

/**
 * Field type definition
 */
interface FieldTypeDef {
  /** Field type enum */
  type: FieldType;

  /** Component name */
  component: string;

  /** Default props for component */
  defaultProps?: Record<string, any>;

  /** Value validator */
  validator?: (value: any) => boolean;

  /** Value normalizer */
  normalizer?: (value: any) => any;

  /** Default validation rules */
  defaultValidation?: ValidationRule[];
}
```

---

## 7. Performance Optimization

### 7.1 Memoization Strategies

```typescript
/**
 * Memoized field component
 */
function memoField<P extends object>(
  Component: React.ComponentType<P>,
  areEqual?: (prevProps: P, nextProps: P) => boolean
): React.ComponentType<P> {
  return React.memo(Component, areEqual);
}

/**
 * Custom comparison for field props
 */
function compareFieldProps(
  prev: FieldProps<any>,
  next: FieldProps<any>
): boolean {
  return (
    prev.value === next.value &&
    prev.errors === next.errors &&
    prev.disabled === next.disabled &&
    prev.readOnly === next.readOnly &&
    prev.config === next.config
  );
}
```

### 7.2 Debounced Validation

```typescript
/**
 * Debounced validation hook
 */
function useDebouncedValidation(
  value: any,
  validate: (value: any) => FieldError[],
  delay: number = 300
): FieldError[] {
  const [errors, setErrors] = useState<FieldError[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setErrors(validate(value));
    }, delay);

    return () => clearTimeout(timer);
  }, [value, validate, delay]);

  return errors;
}
```

### 7.3 Virtual Scrolling for Large Lists

```typescript
/**
 * Virtual scrolling hook (already covered in section 2.4)
 */
// Re-use useComboboxVirtualScroll
```

---

## Summary

The Field Editing system provides:

- **SmartCombobox** with autocomplete, search, and virtual scrolling
- **Comprehensive validation** with sync and async rules
- **Change tracking** with undo/redo support
- **Conflict resolution** for collaborative editing
- **Field type registry** for extensible input types
- **Performance optimization** with memoization and debouncing

---

**Next:** [FIELD_02_UX_UI_DEEP_DIVE](./FIELD_02_UX_UI_DEEP_DIVE.md) — UX/UI patterns and component specifications
