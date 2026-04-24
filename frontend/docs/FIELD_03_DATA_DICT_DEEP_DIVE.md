# FIELD_03_DATA_DICT_DEEP_DIVE

> Part 3 of SmartCombobox & Field Editing Deep Dive
>
> **Previous:** [FIELD_02_UX_UI_DEEP_DIVE](./FIELD_02_UX_UI_DEEP_DIVE.md)
>
> **Next:** [FIELD_04_CHANGE_TRACKING_DEEP_DIVE](./FIELD_04_CHANGE_TRACKING_DEEP_DIVE.md)

---

## Field Type Reference & Data Dictionary

This document provides a complete reference of all field types used across the application, including their data structures, validation rules, and usage patterns.

---

## Table of Contents

1. [Field Type Overview](#1-field-type-overview)
2. [Customer Fields](#2-customer-fields)
3. [Trip Fields](#3-trip-fields)
4. [Booking Fields](#4-booking-fields)
5. [Supplier Fields](#5-supplier-fields)
6. [Agency Fields](#6-agency-fields)
7. [System Fields](#7-system-fields)

---

## 1. Field Type Overview

### 1.1 Field Type Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FIELD TYPE TAXONOMY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIMITIVE TYPES                                                            │
│  ────────────────                                                           │
│  ├── text           Free-form text input                                    │
│  ├── number         Numeric value (integer or decimal)                      │
│  ├── email          Email address                                           │
│  ├── tel            Phone number                                            │
│  ├── url            Web URL                                                │
│  ├── textarea       Multi-line text                                        │
│  ├── boolean        True/false checkbox                                     │
│  └── date           Date value                                             │
│                                                                             │
│  SELECTION TYPES                                                            │
│  ────────────────                                                           │
│  ├── select         Single choice from dropdown                             │
│  ├── multiselect    Multiple choices from dropdown                          │
│  ├── combobox       Searchable single select                                │
│  ├── radio          Single choice from radio buttons                        │
│  ├── checkbox       Multiple choices from checkboxes                       │
│  └── toggle         On/off switch                                          │
│                                                                             │
│  COMPOSITE TYPES                                                            │
│  ────────────────                                                           │
│  ├── daterange      Start and end date                                     │
│  ├── currency       Amount with currency code                              │
│  ├── percentage     Percentage value                                       │
│  ├── duration       Time duration                                          │
│  ├── location       Place with coordinates                                 │
│  └── person         Person name with contact info                          │
│                                                                             │
│  COLLECTION TYPES                                                           │
│  ────────────────                                                           │
│  ├── array          Repeated field items                                    │
│  ├── object         Nested field group                                     │
│  └── reference      Reference to another entity                            │
│                                                                             │
│  SPECIAL TYPES                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ file           File upload                                               │   │
│  │ image          Image upload with preview                               │   │
│  │ color          Color picker                                             │   │
│  │ rating         Star/numeric rating                                     │   │
│  │ rich           Rich text editor                                        │   │
│  │ code           Code input                                               │   │
│  │ password       Password input with visibility toggle                    │   │
│  └── signature      Drawn signature                                         │   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Field Definition Schema

```typescript
/**
 * Complete field definition
 */
interface FieldDefinition {
  /** Unique field identifier */
  id: string;

  /** Display name */
  name: string;

  /** Field type */
  type: FieldType;

  /** Data type */
  dataType: DataType;

  /** Is field required */
  required: boolean;

  /** Default value */
  defaultValue?: any;

  /** Validation rules */
  validation?: FieldValidation;

  /** UI configuration */
  ui?: FieldUIConfig;

  /** API configuration */
  api?: FieldAPIConfig;

  /** Field group/category */
  group?: string;

  /** Display order */
  order?: number;

  /** Field description */
  description?: string;

  /** Help text */
  helpText?: string;

  /** Dependency rules */
  dependencies?: FieldDependency[];
}

/**
 * Data types for field values
 */
enum DataType {
  STRING = 'string',
  NUMBER = 'number',
  INTEGER = 'integer',
  BOOLEAN = 'boolean',
  DATE = 'date',
  DATETIME = 'datetime',
  TIME = 'time',
  ARRAY = 'array',
  OBJECT = 'object',
  NULL = 'null'
}

/**
 * Field validation rules
 */
interface FieldValidation {
  /** Minimum length (for strings/arrays) */
  minLength?: number;

  /** Maximum length (for strings/arrays) */
  maxLength?: number;

  /** Minimum value (for numbers) */
  min?: number;

  /** Maximum value (for numbers) */
  max?: number;

  /** Pattern (regex) */
  pattern?: string;

  /** Allowed values */
  allowedValues?: any[];

  /** Custom validator function */
  custom?: (value: any) => boolean | Promise<boolean>;

  /** Async validation */
  async?: {
    /** Endpoint to validate against */
    endpoint: string;

    /** Response field indicating validity */
    validField: string;

    /** Response field for error message */
    errorField?: string;
  };
}

/**
 * Field UI configuration
 */
interface FieldUIConfig {
  /** Placeholder text */
  placeholder?: string;

  /** Input width */
  width?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';

  /** Display mode */
  mode?: 'input' | 'read-only' | 'hidden';

  /** Component variant */
  variant?: string;

  /** Icon prefix */
  prefix?: string;

  /** Icon suffix */
  suffix?: string;

  /** Show character count */
  showCount?: boolean;

  /** Auto-focus */
  autoFocus?: boolean;

  /** Custom component */
  component?: string;
}
```

---

## 2. Customer Fields

### 2.1 Customer Identity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER IDENTITY FIELDS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIMARY IDENTIFIER                                                        │
│  ────────────────────────                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.id                                               │   │
│  │ Name: Customer ID                                                   │   │
│  │ Type: text (auto-generated)                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Format: CUS-{YYYYMMDD}-{XXXX}                                       │   │
│  │ Example: CUS-20240124-0001                                          │   │
│  │ UI: Read-only                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NAME                                                                       │
│  ──────────────────                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.firstName                                        │   │
│  │ Name: First Name                                                    │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: minLength=2, maxLength=50                               │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.lastName                                         │   │
│  │ Name: Last Name                                                     │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: minLength=2, maxLength=50                               │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  EMAIL                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.email                                            │   │
│  │ Name: Email Address                                                 │   │
│  │ Type: email                                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: email format, unique                                    │   │
│  │ Async: Check uniqueness against existing customers                  │   │
│  │ UI: Width=md, prefix=📧                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PHONE                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.phone                                            │   │
│  │ Name: Phone Number                                                  │   │
│  │ Type: tel                                                           │   │
│  │ Required: No                                                        │   │
│  │ Validation: phone format (E.164)                                    │   │
│  │ UI: Width=md, prefix=📱, country code selector                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATE OF BIRTH                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.dateOfBirth                                      │   │
│  │ Name: Date of Birth                                                 │   │
│  │ Type: date                                                          │   │
│  │ Required: No                                                        │   │
│  │ Validation: max=today, min=-120 years                               │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  GENDER                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.gender                                           │   │
│  │ Name: Gender                                                        │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options:                                                             │   │
│  │   • male (Male)                                                      │   │
│  │   • female (Female)                                                  │   │
│  │   • other (Other)                                                    │   │
│  │   • prefer_not_to_say (Prefer not to say)                           │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NATIONALITY                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.nationality                                      │   │
│  │ Name: Nationality                                                   │   │
│  │ Type: combobox (searchable)                                         │   │
│  │ Required: No                                                        │   │
│  │ Options: ISO 3166-1 alpha-2 country codes                           │   │
│  │ UI: Width=md, show flag, show country name                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Customer Address

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER ADDRESS FIELDS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ADDRESS LINE 1                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.address.line1                                    │   │
│  │ Name: Street Address                                                │   │
│  │ Type: textarea                                                      │   │
│  │ Required: Yes (if address provided)                                 │   │
│  │ Validation: minLength=5, maxLength=100                              │   │
│  │ UI: Width=full, rows=2                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ADDRESS LINE 2                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.address.line2                                    │   │
│  │ Name: Apartment, Suite, Unit                                        │   │
│  │ Type: text                                                          │   │
│  │ Required: No                                                        │   │
│  │ Validation: maxLength=50                                           │   │
│  │ UI: Width=full, placeholder="Optional"                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CITY                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.address.city                                     │   │
│  │ Name: City                                                          │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes (if address provided)                                 │   │
│  │ Validation: minLength=2, maxLength=50                               │   │
│  │ UI: Width=lg                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATE/PROVINCE                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.address.state                                    │   │
│  │ Name: State/Province                                                │   │
│  │ Type: combobox (depends on country)                                 │   │
│  │ Required: Yes (if applicable for country)                           │   │
│  │ Options: Loaded based on selected country                           │   │
│  │ UI: Width=lg                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  POSTAL CODE                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.address.postalCode                               │   │
│  │ Name: Postal/ZIP Code                                               │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes (if applicable for country)                           │   │
│  │ Validation: Pattern based on country                                │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  COUNTRY                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.address.country                                  │   │
│  │ Name: Country                                                       │   │
│  │ Type: combobox (searchable)                                         │   │
│  │ Required: Yes (if address provided)                                 │   │
│  │ Options: ISO 3166-1 alpha-2 country codes                           │   │
│  │ UI: Width=lg, show flag                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ADDRESS TYPE                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.address.type                                     │   │
│  │ Name: Address Type                                                  │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options: home, work, billing, shipping, other                       │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Customer Documents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER DOCUMENT FIELDS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PASSPORT NUMBER                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.passport.number                         │   │
│  │ Name: Passport Number                                               │   │
│  │ Type: text                                                          │   │
│  │ Required: No (required for international travel)                    │   │
│  │ Validation: pattern based on country                                │   │
│  │ UI: Width=lg, uppercase                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PASSPORT EXPIRY                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.passport.expiry                         │   │
│  │ Name: Passport Expiry Date                                          │   │
│  │ Type: date                                                          │   │
│  │ Required: No (required with passport)                               │   │
│  │ Validation: min=today+6months                                       │   │
│  │ UI: Width=sm                                                        │   │
│  │ Warning: Show warning if <6 months from travel date                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PASSPORT ISSUING COUNTRY                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.passport.issuingCountry                 │   │
│  │ Name: Issuing Country                                               │   │
│  │ Type: combobox (searchable)                                         │   │
│  │ Required: No (required with passport)                               │   │
│  │ Options: ISO 3166-1 alpha-2 country codes                           │   │
│  │ UI: Width=md, show flag                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PASSPORT FRONT IMAGE                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.passport.frontImage                     │   │
│  │ Name: Passport Photo (Front)                                        │   │
│  │ Type: image                                                         │   │
│  │ Required: No                                                        │   │
│  │ Validation: maxFileSize=5MB, allowedTypes=[jpg,jpeg,png,pdf]        │   │
│  │ UI: Show preview, crop overlay                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VISA NUMBER                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.visa.number                              │   │
│  │ Name: Visa Number                                                   │   │
│  │ Type: text                                                          │   │
│  │ Required: No                                                        │   │
│  │ Validation: alphanumeric, minLength=8, maxLength=20                 │   │
│  │ UI: Width=lg                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VISA DESTINATION                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.visa.destination                         │   │
│  │ Name: Visa For Country                                              │   │
│  │ Type: combobox (searchable)                                         │   │
│  │ Required: No (required with visa number)                            │   │
│  │ Options: ISO 3166-1 alpha-2 country codes                           │   │
│  │ UI: Width=md, show flag                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VISA EXPIRY                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.visa.expiry                              │   │
│  │ Name: Visa Expiry Date                                              │   │
│  │ Type: date                                                          │   │
│  │ Required: No (required with visa number)                            │   │
│  │ Validation: min=today                                               │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ID PROOF TYPE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.idProof.type                             │   │
│  │ Name: ID Proof Type                                                  │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options:                                                             │   │
│  │   • driving_license (Driving License)                               │   │
│  │   • national_id (National ID Card)                                  │   │
│  │   • aadhaar (Aadhaar Card - India)                                  │   │
│  │   • voter_id (Voter ID Card)                                        │   │
│  │   • other (Other)                                                   │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ID PROOF NUMBER                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.documents.idProof.number                           │   │
│  │ Name: ID Proof Number                                               │   │
│  │ Type: text                                                          │   │
│  │ Required: No (required with type)                                   │   │
│  │ Validation: pattern based on type                                    │   │
│  │ UI: Width=lg                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Customer Preferences

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER PREFERENCE FIELDS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PREFERRED LANGUAGE                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.preferences.language                              │   │
│  │ Name: Preferred Communication Language                               │   │
│  │ Type: combobox (searchable)                                          │   │
│  │ Required: No                                                        │   │
│  │ Default: en                                                          │   │
│  │ Options: ISO 639-1 language codes                                    │   │
│  │ UI: Width=md, show native language name                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PREFERRED CURRENCY                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.preferences.currency                              │   │
│  │ Name: Preferred Currency                                            │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Default: USD                                                        │   │
│  │ Options: Supported agency currencies                                │   │
│  │ UI: Width=sm, show currency symbol                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PREFERRED CONTACT METHOD                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.preferences.contactMethod                         │   │
│  │ Name: Preferred Contact Method                                      │   │
│  │ Type: radio                                                         │   │
│  │ Required: No                                                        │   │
│  │ Default: email                                                      │   │
│  │ Options:                                                             │   │
│  │   • email (Email)                                                   │   │
│  │   • phone (Phone Call)                                              │   │
│  │   • whatsapp (WhatsApp)                                             │   │
│  │   • sms (SMS)                                                       │   │
│  │ UI: Inline                                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MARKETING CONSENTS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.preferences.consents.marketing                    │   │
│  │ Name: Marketing Communications                                      │   │
│  │ Type: checkbox group                                                │   │
│  │ Required: No                                                        │   │
│  │ Options:                                                             │   │
│  │   • email_newsletter (Email newsletter)                             │   │
│  │   • email_offers (Special offers via email)                         │   │
│  │   • sms_offers (Special offers via SMS)                             │   │
│  │   • phone_marketing (Phone calls for marketing)                     │   │
│  │ UI: Vertical layout                                                 │   │
│  │ Legal: GDPR/compliance checkbox required                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MEAL PREFERENCE                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.preferences.meal                                  │   │
│  │ Name: Meal Preference                                               │   │
│  │ Type: multiselect                                                   │   │
│  │ Required: No                                                        │   │
│  │ Options:                                                             │   │
│  │   • vegetarian (Vegetarian)                                         │   │
│  │   • vegan (Vegan)                                                   │   │
│  │   • halal (Halal)                                                   │   │
│  │   • kosher (Kosher)                                                 │   │
│  │   • gluten_free (Gluten-free)                                       │   │
│  │   • no_restriction (No restriction)                                 │   │
│  │ UI: Tag-based selection                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SEAT PREFERENCE                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: customer.preferences.seat                                  │   │
│  │ Name: Seat Preference (Flights)                                     │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options:                                                             │   │
│  │   • window (Window)                                                 │   │
│  │   • aisle (Aisle)                                                   │   │
│  │   • middle (Middle)                                                 │   │
│  │   • no_preference (No preference)                                   │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Trip Fields

### 3.1 Trip Identity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TRIP IDENTITY FIELDS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRIP ID                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.id                                                    │   │
│  │ Name: Trip ID                                                       │   │
│  │ Type: text (auto-generated)                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Format: TRP-{YYYYMMDD}-{XXXX}                                       │   │
│  │ Example: TRP-20240124-0001                                          │   │
│  │ UI: Read-only, copyable                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRIP NAME                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.name                                                 │   │
│  │ Name: Trip Name                                                     │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: minLength=3, maxLength=100                              │   │
│  │ UI: Width=full, placeholder="Summer vacation 2024"                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRIP TYPE                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.type                                                 │   │
│  │ Name: Trip Type                                                     │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • leisure (Leisure / Vacation)                                    │   │
│  │   • business (Business Trip)                                        │   │
│  │   • bleisure (Bleisure - Business + Leisure)                        │   │
│  │   • family (Family Trip)                                            │   │
│  │   • honeymoon (Honeymoon)                                           │   │
│  │   • group (Group Tour)                                              │   │
│  │   • adventure (Adventure Travel)                                    │   │
│  │   • other (Other)                                                   │   │
│  │ UI: Width=md, show icon                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRIP STATUS                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.status                                               │   │
│  │ Name: Trip Status                                                   │   │
│  │ Type: select (auto-managed)                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • inquiry (Inquiry)                                               │   │
│  │   • quoted (Quoted)                                                 │   │
│  │   • confirmed (Confirmed)                                           │   │
│  │   • deposit_paid (Deposit Paid)                                     │   │
│  │   • fully_paid (Fully Paid)                                         │   │
│  │   • booked (Booked)                                                 │   │
│  │   │ documents_sent (Documents Sent)                                 │   │
│  │   • in_progress (In Progress)                                       │   │
│  │   • completed (Completed)                                           │   │
│  │   • cancelled (Cancelled)                                           │   │
│  │ UI: Status pill with color                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRIP SOURCE                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.source                                               │   │
│  │ Name: Lead Source                                                   │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • website (Website)                                               │   │
│  │   • instagram (Instagram)                                           │   │
│  │   • facebook (Facebook)                                             │   │
│  │   • whatsapp (WhatsApp)                                             │   │
│  │   • email (Email Inquiry)                                           │   │
│  │   • phone (Phone Call)                                              │   │
│  │   • referral (Referral)                                             │   │
│  │   • repeat (Repeat Customer)                                        │   │
│  │   • other (Other)                                                   │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Travel Dates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRAVEL DATE FIELDS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRAVEL DATE TYPE                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.dates.type                                            │   │
│  │ Name: Date Selection Type                                           │   │
│  │ Type: radio                                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Default: flexible                                                   │   │
│  │ Options:                                                             │   │
│  │   • exact (Exact dates)                                              │   │
│  │   • flexible (Flexible - +/- days)                                  │   │
│  │   • approx (Approximate - month/year)                                │   │
│  │   • open (Open dates)                                               │   │
│  │ UI: Inline, shows conditional fields                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DEPARTURE DATE                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.dates.departure                                      │   │
│  │ Name: Departure Date                                                │   │
│  │ Type: date                                                          │   │
│  │ Required: Yes (if type=exact or flexible)                           │   │
│  │ Validation: min=today                                               │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RETURN DATE                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.dates.return                                          │   │
│  │ Name: Return Date                                                   │   │
│  │ Type: date                                                          │   │
│  │ Required: No (one-way trips)                                        │   │
│  │ Validation: min=departure date                                      │   │
│  │ UI: Width=sm                                                        │   │
│  │ UI Note: Show "One-way trip" checkbox to disable                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FLEXIBILITY                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.dates.flexibility                                    │   │
│  │ Name: Date Flexibility                                              │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options:                                                             │   │
│  │   • 0 (Exact dates only)                                            │   │
│  │   • 1 (±1 day)                                                      │   │
│  │   • 2 (±2 days)                                                     │   │
│  │   • 3 (±3 days)                                                     │   │
│  │   • 7 (±1 week)                                                     │   │
│  │   • 14 (±2 weeks)                                                   │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DURATION                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.dates.duration                                        │   │
│  │ Name: Trip Duration                                                 │   │
│  │ Type: duration                                                      │   │
│  │ Required: No (calculated from dates)                                │   │
│  │ Format: X days Y nights                                             │   │
│  │ UI: Read-only, calculated                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  APPROXIMATE MONTH                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.dates.approxMonth                                     │   │
│  │ Name: Preferred Month                                               │   │
│  │ Type: month                                                         │   │
│  │ Required: Yes (if type=approx)                                      │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  APPROXIMATE YEAR                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.dates.approxYear                                      │   │
│  │ Name: Preferred Year                                                │   │
│  │ Type: number (year)                                                 │   │
│  │ Required: Yes (if type=approx)                                      │   │
│  │ Validation: min=current year, max=current year+5                    │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Travelers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             TRAVELER FIELDS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRAVELERS (Array)                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers                                             │   │
│  │ Name: Travelers                                                     │   │
│  │ Type: array of objects                                              │   │
│  │ Required: Yes (at least 1)                                          │   │
│  │ Min items: 1                                                        │   │
│  │ Max items: 50                                                       │   │
│  │ UI: Card-based, reorderable, add/remove                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER TYPE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].type                                      │   │
│  │ Name: Traveler Type                                                 │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • adult (Adult)                                                   │   │
│  │   • child (Child)                                                   │   │
│  │   • infant (Infant)                                                 │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER TITLE                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].title                                     │   │
│  │ Name: Title                                                         │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options: mr, mrs, ms, dr, prof                                      │   │
│  │ UI: Width=xs                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER FIRST NAME                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].firstName                                 │   │
│  │ Name: First Name                                                    │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: minLength=2, maxLength=50                               │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER LAST NAME                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].lastName                                  │   │
│  │ Name: Last Name                                                     │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: minLength=2, maxLength=50                               │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER DATE OF BIRTH                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].dateOfBirth                               │   │
│  │ Name: Date of Birth                                                 │   │
│  │ Type: date                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: max=today                                               │   │
│  │ UI: Width=sm                                                        │   │
│  │ Auto-calculates age                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER AGE (Calculated)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].age                                       │   │
│  │ Name: Age                                                           │   │
│  │ Type: number (read-only, calculated)                                │   │
│  │ UI: Width=xs                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER PASSPORT NUMBER                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].passport.number                           │   │
│  │ Name: Passport Number                                               │   │
│  │ Type: text                                                          │   │
│  │ Required: No (required for international)                           │   │
│  │ Validation: pattern by country                                     │   │
│  │ UI: Width=md, uppercase                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER PASSPORT EXPIRY                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].passport.expiry                           │   │
│  │ Name: Passport Expiry                                              │   │
│  │ Type: date                                                          │   │
│  │ Required: No (required with passport)                              │   │
│  │ Validation: min=today+6months                                       │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER NATIONALITY                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].nationality                               │   │
│  │ Name: Nationality                                                   │   │
│  │ Type: combobox (searchable)                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Options: ISO 3166-1 alpha-2 country codes                           │   │
│  │ UI: Width=md, show flag                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRAVELER MEAL PREFERENCE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.travelers[].mealPreference                            │   │
│  │ Name: Meal Preference                                               │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options: (same as customer preferences)                            │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Destination & Budget

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DESTINATION & BUDGET FIELDS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DESTINATIONS (Array)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.destinations                                          │   │
│  │ Name: Destinations                                                  │   │
│  │ Type: array of references                                            │   │
│  │ Required: Yes (at least 1)                                          │   │
│  │ Min items: 1                                                        │   │
│  │ Max items: 10                                                       │   │
│  │ UI: Combobox with tag display, add/remove                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PRIMARY DESTINATION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.destinations.primary                                 │   │
│  │ Name: Primary Destination                                           │   │
│  │ Type: reference (destination)                                       │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Combobox with rich options (flag, type, description)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DESTINATION TYPE                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.destinations[].type                                  │   │
│  │ Name: Destination Type                                              │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • city (City)                                                     │   │
│  │   • beach (Beach/Coastal)                                           │   │
│  │   • mountain (Mountain/Hill Station)                                │   │
│  │   • nature (Nature/Wildlife)                                        │   │
│  │   • historic (Historic Site)                                        │   │
│  │   • adventure (Adventure Destination)                               │   │
│  │   • pilgrimage (Pilgrimage Site)                                    │   │
│  │   • other (Other)                                                   │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BUDGET AMOUNT                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.budget.amount                                         │   │
│  │ Name: Total Budget                                                  │   │
│  │ Type: currency                                                      │   │
│  │ Required: No                                                        │   │
│  │ Validation: min=0                                                   │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BUDGET CURRENCY                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.budget.currency                                       │   │
│  │ Name: Budget Currency                                               │   │
│  │ Type: select                                                        │   │
│  │ Required: No (default from customer pref)                           │   │
│  │ Options: Agency supported currencies                                │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BUDGET PER PERSON                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.budget.perPerson                                      │   │
│  │ Name: Budget Per Person                                             │   │
│  │ Type: currency                                                      │   │
│  │ Required: No                                                        │   │
│  │ Validation: min=0                                                   │   │
│  │ UI: Width=md, calculated from total / travelers                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BUDGET FLEXIBILITY                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: trip.budget.flexibility                                    │   │
│  │ Name: Budget Flexibility                                            │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options:                                                             │   │
│  │   • fixed (Fixed - must not exceed)                                 │   │
│  │   • approximate (Approximate - can exceed slightly)                 │   │
│  │   flexible (Flexible - willing to go higher for better options)     │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Booking Fields

### 4.1 Flight Booking

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FLIGHT BOOKING FIELDS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BOOKING REFERENCE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.pnr                                        │   │
│  │ Name: PNR (Booking Reference)                                       │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: alphanumeric, minLength=5, maxLength=10, uppercase       │   │
│  │ UI: Width=sm, uppercase                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AIRLINE                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.airline                                    │   │
│  │ Name: Airline                                                       │   │
│  │ Type: combobox (searchable)                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Options: IATA airline codes                                        │   │
│  │ UI: Width=md, show airline logo                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FLIGHT NUMBER                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.flightNumber                               │   │
│  │ Name: Flight Number                                                 │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: alphanumeric, uppercase                                 │   │
│  │ UI: Width=sm, uppercase                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DEPARTURE AIRPORT                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.departure.airport                          │   │
│  │ Name: From Airport                                                  │   │
│  │ Type: combobox (searchable by code/city)                            │   │
│  │ Required: Yes                                                       │   │
│  │ Options: IATA airport codes                                         │   │
│  │ UI: Width=lg, show code + city                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DEPARTURE TERMINAL                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.departure.terminal                         │   │
│  │ Name: Terminal                                                       │   │
│  │ Type: text                                                          │   │
│  │ Required: No                                                        │   │
│  │ UI: Width=xs                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DEPARTURE TIME                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.departure.time                             │   │
│  │ Name: Departure Time                                               │   │
│  │ Type: datetime                                                      │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ARRIVAL AIRPORT                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.arrival.airport                            │   │
│  │ Name: To Airport                                                    │   │
│  │ Type: combobox (searchable by code/city)                            │   │
│  │ Required: Yes                                                       │   │
│  │ Options: IATA airport codes                                         │   │
│  │ UI: Width=lg, show code + city                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ARRIVAL TERMINAL                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.arrival.terminal                           │   │
│  │ Name: Terminal                                                       │   │
│  │ Type: text                                                          │   │
│  │ Required: No                                                        │   │
│  │ UI: Width=xs                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ARRIVAL TIME                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.arrival.time                               │   │
│  │ Name: Arrival Time                                                  │   │
│  │ Type: datetime                                                      │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Width=md                                                        │   │
│  │ Note: Auto-calculates local time at destination                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CLASS OF SERVICE                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.class                                      │   │
│  │ Name: Class of Service                                              │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • economy (Economy)                                               │   │
│  │   • premium_economy (Premium Economy)                                │   │
│  │   • business (Business Class)                                       │   │
│  │   • first (First Class)                                             │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BAGGAGE ALLOWANCE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.baggage                                     │   │
│  │ Name: Checked Baggage                                               │   │
│  │ Type: select                                                        │   │
│  │ Required: No                                                        │   │
│  │ Options: (depends on airline/class)                                 │   │
│  │   • none (None)                                                     │   │
│  │   • 15kg (15 kg)                                                    │   │
│  │   • 20kg (20 kg)                                                    │   │
│  │   • 23kg (23 kg)                                                    │   │
│  │   • 25kg (25 kg)                                                    │   │
│  │   • 30kg (30 kg)                                                    │   │
│  │   • 2pc (2 pieces)                                                  │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SEAT ASSIGNMENTS (Array)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.seats                                       │   │
│  │ Name: Seat Assignments                                              │   │
│  │ Type: array of objects                                             │   │
│  │ Required: No                                                        │   │
│  │ UI: Seat map picker per traveler                                    │   │
│  │ Structure: { travelerId, seatNumber, class }                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MEAL PREFERENCES (Array)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.flight.meals                                       │   │
│  │ Name: Meal Preferences                                              │   │
│  │ Type: array of objects                                             │   │
│  │ Required: No                                                        │   │
│  │ Structure: { travelerId, mealType }                                 │   │
│  │ UI: Per traveler dropdown                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Accommodation Booking

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ACCOMMODATION BOOKING FIELDS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROPERTY REFERENCE                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.propertyId                           │   │
│  │ Name: Property                                                      │   │
│  │ Type: reference (property)                                          │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Combobox with property details (name, rating, amenities)        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CONFIRMATION NUMBER                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.confirmationNumber                  │   │
│  │ Name: Confirmation Number                                           │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: alphanumeric, maxLength=20                              │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROOM TYPE                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.roomType                             │   │
│  │ Name: Room Type                                                     │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options: (from property)                                           │   │
│  │   • standard (Standard Room)                                        │   │
│  │   • deluxe (Deluxe Room)                                            │   │
│  │   • suite (Suite)                                                   │   │
│  │   • studio (Studio)                                                 │   │
│  │   • villa (Villa)                                                   │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BOARD BASIS                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.boardBasis                           │   │
│  │ Name: Meal Plan                                                     │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • room_only (Room Only)                                           │   │
│  │   • breakfast (Breakfast Only)                                      │   │
│  │   • half_board (Breakfast + Dinner)                                │   │
│  │   • full_board (Breakfast + Lunch + Dinner)                        │   │
│  │   • all_inclusive (All Inclusive)                                   │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHECK-IN DATE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.checkIn                               │   │
│  │ Name: Check-in Date                                                 │   │
│  │ Type: date                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHECK-OUT DATE                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.checkOut                             │   │
│  │ Name: Check-out Date                                                │   │
│  │ Type: date                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: min=checkIn+1 night                                     │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NUMBER OF ROOMS                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.rooms                                 │   │
│  │ Name: Number of Rooms                                               │   │
│  │ Type: number                                                        │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: min=1, max=10                                            │   │
│  │ UI: Width=xs, spinner                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NUMBER OF NIGHTS (Calculated)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.nights                                │   │
│  │ Name: Nights                                                        │   │
│  │ Type: number (read-only)                                            │   │
│  │ UI: Width=xs                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  GUEST ASSIGNMENTS (Array)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.guests                                │   │
│  │ Name: Room Assignments                                              │   │
│  │ Type: array of objects                                             │   │
│  │ Required: No                                                        │   │
│  │ Structure: { roomIndex, travelerIds[] }                             │   │
│  │ UI: Drag-drop traveler to room                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SPECIAL REQUESTS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.accommodation.specialRequests                       │   │
│  │ Name: Special Requests                                              │   │
│  │ Type: textarea                                                      │   │
│  │ Required: No                                                        │   │
│  │ Validation: maxLength=500                                           │   │
│  │ UI: Width=full, rows=3                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Activity/Experience Booking

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACTIVITY BOOKING FIELDS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ACTIVITY REFERENCE                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.activityId                                │   │
│  │ Name: Activity                                                      │   │
│  │ Type: reference (activity)                                          │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Combobox with activity details                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BOOKING REFERENCE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.referenceNumber                          │   │
│  │ Name: Booking Reference                                             │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: alphanumeric, maxLength=20                              │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACTIVITY DATE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.date                                     │   │
│  │ Name: Date                                                          │   │
│  │ Type: date                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACTIVITY TIME                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.time                                     │   │
│  │ Name: Time                                                          │   │
│  │ Type: time                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DURATION                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.duration                                 │   │
│  │ Name: Duration                                                      │   │
│  │ Type: duration                                                      │   │
│  │ Required: No (from activity definition)                             │   │
│  │ UI: Read-only                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PARTICIPANTS (Array)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.participants                             │   │
│  │ Name: Participants                                                  │   │
│  │ Type: array of references (travelers)                              │   │
│  │ Required: Yes (at least 1)                                          │   │
│  │ UI: Multiselect from trip travelers                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PICKUP LOCATION                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.pickup.location                           │   │
│  │ Name: Pickup Location                                               │   │
│  │ Type: text                                                          │   │
│  │ Required: No (depends on activity)                                  │   │
│  │ Validation: maxLength=200                                           │   │
│  │ UI: Width=full, placeholder="Hotel lobby, etc."                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PICKUP TIME                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: booking.activity.pickup.time                               │   │
│  │ Name: Pickup Time                                                   │   │
│  │ Type: time                                                          │   │
│  │ Required: No (depends on activity)                                  │   │
│  │ UI: Width=sm                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Supplier Fields

### 5.1 Supplier Identity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUPPLIER IDENTITY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SUPPLIER ID                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.id                                                │   │
│  │ Name: Supplier ID                                                   │   │
│  │ Type: text (auto-generated)                                         │   │
│  │ Required: Yes                                                       │   │
│  │ Format: SUP-{YYYYMMDD}-{XXXX}                                       │   │
│  │ Example: SUP-20240124-0001                                          │   │
│  │ UI: Read-only                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SUPPLIER NAME                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.name                                              │   │
│  │ Name: Supplier Name                                                │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: minLength=3, maxLength=100                              │   │
│  │ UI: Width=lg                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SUPPLIER TYPE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.type                                              │   │
│  │ Name: Supplier Type                                                 │   │
│  │ Type: multiselect                                                   │   │
│  │ Required: Yes                                                       │   │
│  │ Options:                                                             │   │
│  │   • airline (Airline)                                               │   │
│  │   • hotel (Hotel/Accommodation)                                      │   │
│  │   • tour_operator (Tour Operator)                                    │   │
│  │   • dmc (DMC - Destination Management Company)                      │   │
│  │   • transport (Transport Provider)                                   │   │
│  │   • activity (Activity Provider)                                     │   │
│  │   • cruise (Cruise Line)                                            │   │
│  │   • insurance (Insurance Provider)                                   │   │
│  │   • visa (Visa Processing Service)                                   │   │
│  │   • other (Other)                                                   │   │
│  │ UI: Tag-based selection                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SUPPLIER CODE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.code                                              │   │
│  │ Name: Supplier Code (Internal)                                      │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                       │   │
│  │ Validation: alphanumeric, uppercase, minLength=2, maxLength=10      │   │
│  │ UI: Width=sm, uppercase                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IATA CODE (for airlines)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.iataCode                                          │   │
│  │ Name: IATA Code                                                     │   │
│  │ Type: text                                                          │   │
│  │ Required: No (required for airlines)                                │   │
│  │ Validation: pattern=^[A-Z0-9]{2,3}$, uppercase                     │   │
│  │ UI: Width=xs, uppercase                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Supplier Contact

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SUPPLIER CONTACT FIELDS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CONTACT PERSON                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.contact.name                                       │   │
│  │ Name: Contact Person                                                │   │
│  │ Type: text                                                          │   │
│  │ Required: No                                                        │   │
│  │ Validation: minLength=3, maxLength=100                              │   │
│  │ UI: Width=lg                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CONTACT EMAIL                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.contact.email                                     │   │
│  │ Name: Email                                                         │   │
│  │ Type: email                                                         │   │
│  │ Required: No                                                        │   │
│  │ Validation: email format                                            │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CONTACT PHONE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.contact.phone                                     │   │
│  │ Name: Phone                                                         │   │
│  │ Type: tel                                                           │   │
│  │ Required: No                                                        │   │
│  │ Validation: phone format                                            │   │
│  │ UI: Width=md                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WEBSITE                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.contact.website                                   │   │
│  │ Name: Website                                                       │   │
│  │ Type: url                                                           │   │
│  │ Required: No                                                        │   │
│  │ UI: Width=lg, show as link                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PORTAL URL                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: supplier.contact.portalUrl                                 │   │
│  │ Name: Booking Portal URL                                            │   │
│  │ Type: url                                                           │   │
│  │ Required: No                                                        │   │
│  │ UI: Width=lg, show as link with "Open Portal" button                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Agency Fields

### 6.1 Agency Identity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENCY IDENTITY FIELDS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AGENCY ID                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.id                                                   │   │
│  │ Name: Agency ID                                                      │   │
│  │ Type: text (auto-generated)                                          │   │
│  │ Required: Yes                                                        │   │
│  │ Format: AGY-{YYYYMMDD}-{XXXX}                                        │   │
│  │ UI: Read-only                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AGENCY NAME                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.name                                                 │   │
│  │ Name: Agency Name                                                   │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                        │   │
│  │ Validation: minLength=3, maxLength=100                               │   │
│  │ UI: Width=lg                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LEGAL NAME                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.legalName                                            │   │
│  │ Name: Legal Name (for contracts)                                     │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                        │   │
│  │ Validation: minLength=3, maxLength=200                               │   │
│  │ UI: Width=full                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BUSINESS TYPE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.businessType                                         │   │
│  │ Name: Business Type                                                 │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                        │   │
│  │ Options:                                                             │   │
│  │   • proprietorship (Sole Proprietorship)                             │   │
│  │   • partnership (Partnership)                                        │   │
│  │   • llc (LLC)                                                        │   │
│  │   • corporation (Corporation)                                        │   │
│  │   • other (Other)                                                    │   │
│  │ UI: Width=md                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TAX ID                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.taxId                                                │   │
│  │ Name: Tax ID / GSTIN                                                │   │
│  │ Type: text                                                          │   │
│  │ Required: Yes                                                        │   │
│  │ Validation: pattern by country                                      │   │
│  │ UI: Width=lg                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Agency Branding

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENCY BRANDING FIELDS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOGO                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.branding.logo                                        │   │
│  │ Name: Agency Logo                                                   │   │
│  │ Type: image                                                          │   │
│  │ Required: No                                                        │   │
│  │ Validation: maxFileSize=2MB, square recommended                       │   │
│  │ UI: Show preview, crop to square                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PRIMARY COLOR                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.branding.primaryColor                               │   │
│  │ Name: Primary Color                                                 │   │
│  │ Type: color                                                         │   │
│  │ Required: No                                                        │   │
│  │ Default: #3B82F6 (blue-500)                                         │   │
│  │ UI: Color picker with hex input                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SECONDARY COLOR                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.branding.secondaryColor                             │   │
│  │ Name: Secondary Color                                               │   │
│  │ Type: color                                                         │   │
│  │ Required: No                                                        │   │
│  │ Default: #10B981 (emerald-500)                                       │   │
│  │ UI: Color picker with hex input                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TAGLINE                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.branding.tagline                                     │   │
│  │ Name: Tagline                                                        │   │
│  │ Type: text                                                          │   │
│  │ Required: No                                                        │   │
│  │ Validation: maxLength=100                                           │   │
│  │ UI: Width=lg                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  EMAIL HEADER LOGO                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: agency.branding.emailHeaderLogo                            │   │
│  │ Name: Email Header Logo (wide)                                      │   │
│  │ Type: image                                                          │   │
│  │ Required: No                                                        │   │
│  │ Validation: maxFileSize=2MB, landscape recommended                  │   │
│  │ UI: Show preview, dimensions guidance                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. System Fields

### 7.1 Audit Fields

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AUDIT FIELDS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  All entities include these standard audit fields:                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.createdAt                                               │   │
│  │ Name: Created At                                                    │   │
│  │ Type: datetime (auto-generated)                                     │   │
│  │ Required: Yes                                                        │   │
│  │ UI: Read-only, show in human-readable format                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.createdBy                                               │   │
│  │ Name: Created By                                                    │   │
│  │ Type: reference (user)                                              │   │
│  │ Required: Yes (auto-populated)                                      │   │
│  │ UI: Read-only, show user name                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.updatedAt                                               │   │
│  │ Name: Updated At                                                    │   │
│  │ Type: datetime (auto-updated)                                       │   │
│  │ Required: Yes                                                        │   │
│  │ UI: Read-only, show in human-readable format                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.updatedBy                                               │   │
│  │ Name: Updated By                                                    │   │
│  │ Type: reference (user)                                              │   │
│  │ Required: Yes (auto-populated)                                      │   │
│  │ UI: Read-only, show user name                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.deletedAt                                               │   │
│  │ Name: Deleted At (soft delete)                                      │   │
│  │ Type: datetime                                                      │   │
│  │ Required: No                                                        │   │
│  │ UI: Hidden unless set                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.version                                                 │   │
│  │ Name: Version (optimistic locking)                                  │   │
│  │ Type: number (auto-incremented)                                     │   │
│  │ Required: Yes                                                        │   │
│  │ UI: Hidden                                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Status Fields

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STATUS FIELDS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.status                                                  │   │
│  │ Name: Status                                                        │   │
│  │ Type: select                                                        │   │
│  │ Required: Yes                                                        │   │
│  │ Common options:                                                      │   │
│  │   • draft (Draft)                                                   │   │
│  │   • active (Active)                                                 │   │
│  │   • inactive (Inactive)                                             │   │
│  │   • archived (Archived)                                             │   │
│  │   • deleted (Deleted)                                               │   │
│  │ UI: Status pill with color coding                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field ID: *.published                                              │   │
│  │ Name: Published                                                     │   │
│  │ Type: boolean                                                       │   │
│  │ Required: No (default: false)                                       │   │
│  │ UI: Toggle switch                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

This data dictionary provides:

- **Complete field type taxonomy** — primitive, selection, composite, collection, special types
- **Customer fields** — identity, address, documents, preferences
- **Trip fields** — identity, dates, travelers, destinations, budget
- **Booking fields** — flights, accommodations, activities
- **Supplier fields** — identity, contact information
- **Agency fields** — identity, branding
- **System fields** — audit trails, status tracking

---

**Next:** [FIELD_04_CHANGE_TRACKING_DEEP_DIVE](./FIELD_04_CHANGE_TRACKING_DEEP_DIVE.md) — Change tracking implementation and audit trails
