# Lead Management 01: Capture

> Lead sources, intake forms, and data collection

---

## Document Overview

**Focus:** Lead capture mechanisms
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Lead Sources
- Where do leads come from?
- How do we track sources?
- What about multi-source attribution?
- How do we handle offline sources?

### Capture Methods
- How do we capture leads?
- What forms do we need?
- How do we handle social media?
- What about phone inquiries?

### Data Collection
- What information do we collect?
- How much is too much?
- What about progressive profiling?
- How do we validate data?

### Integration
- How do leads enter the system?
- What about third-party sources?
- How do we handle bulk imports?
- What about API access?

---

## Research Areas

### A. Lead Sources

**Digital Channels:**

| Source | Description | Research Needed |
|--------|-------------|-----------------|
| **Website form** | Direct inquiry | ? |
| **Landing page** | Campaign-specific | ? |
| **Social media** | Facebook, Instagram | ? |
| **Email** | Direct inquiries | ? |
| **Chat/WhatsApp** | Conversational | ? |
| **Google Ads** | Paid search | ? |

**Offline Channels:**

| Source | Description | Research Needed |
|--------|-------------|-----------------|
| **Phone call** | Direct call | ? |
| **Walk-in** | Office visit | ? |
| **Referral** | Customer referral | ? |
| **Events** | Travel expos, etc. | ? |
| **Partners** | Agency partners | ? |

**Partner Sources:**

| Source | Description | Research Needed |
|--------|-------------|-----------------|
| **Affiliate referrals** | Partner-sourced | ? |
| **Channel partners** | B2B partners | ? |
| **White label** | Co-branded | ? |

### B. Capture Forms

**Standard Inquiry Form:**

| Field | Required | Purpose | Research Needed |
|-------|----------|---------|-----------------|
| **Name** | Yes | Identification | ? |
| **Email** | Yes | Communication | ? |
| **Phone** | Yes | Follow-up | ? |
| **Destination** | Yes | Trip planning | ? |
| **Travel dates** | No | Planning | ? |
| **Budget** | No | Qualification | ? |
| **Travelers** | No | Planning | ? |
| **Message** | No | Details | ? |

**Progressive Profiling:**

| Stage | Fields Collected | Research Needed |
|-------|-----------------|-----------------|
| **Initial** | Name, email, destination | ? |
| **Follow-up** | Dates, travelers, budget | ? |
| **Qualification** | Preferences, history | ? |
| **Booking** | Full details | ? |

**Contextual Capture:**

| Context | Adaptations | Research Needed |
|---------|-------------|-----------------|
| **Mobile** | Fewer fields, autofill | ? |
| **Desktop** | Full form | ? |
| **Chat** | Conversational | ? |
| **Social** | Pre-filled data | ? |

### C. Data Validation

**Validation Rules:**

| Field | Validation | Research Needed |
|-------|------------|-----------------|
| **Email** | Format, exists | ? |
| **Phone** | Format, valid | ? |
| **Dates** | Future, reasonable | ? |
| **Budget** | Numeric, range | ? |
| **Destination** | Valid location | ? |

**Real-time Validation:**

| Method | Description | Research Needed |
|--------|-------------|-----------------|
| **Client-side** | Immediate feedback | ? |
| **API validation** | Email/phone verification | ? |
| **Duplicate check** | Existing lead? | ? |
| **Spam check** | Bot detection | ? |

**Data Enrichment:**

| Source | Data Added | Research Needed |
|--------|------------|-----------------|
| **IP geolocation** | Location | ? |
| **Email domain** | Company, type | ? |
| **Social profiles** | Public info | ? |
| **UTM parameters** | Campaign source | ? |

### D. Integration Points

**Website Integration:**

| Method | Implementation | Research Needed |
|--------|----------------|-----------------|
| **Embedded form** | JavaScript widget | ? |
| **Popup/modal** | Triggered form | ? |
| **Landing page** | Dedicated page | ? |
| **API** | Direct submission | ? |

**Social Media:**

| Platform | Integration | Research Needed |
|----------|-------------|-----------------|
| **Facebook Lead Ads** | Auto-import | ? |
| **Instagram** | DM automation | ? |
| **Google Ads** | Form extensions | ? |
| **WhatsApp** | Chat to lead | ? |

**Third-Party Tools:**

| Tool | Integration | Research Needed |
|------|-------------|-----------------|
| **CRM** | Two-way sync | ? |
| **Marketing automation** | Lead import | ? |
| **Analytics** | Source tracking | ? |
| **Call tracking** | Phone to lead | ? |

---

## Data Model Sketch

```typescript
interface Lead {
  leadId: string;
  agencyId: string;

  // Source
  source: LeadSource;
  sourceDetails: SourceDetails;
  campaign?: string;

  // Contact
  contact: LeadContact;

  // Trip interest
  trip: TripInterest;

  // Qualification
  status: LeadStatus;
  score?: number;
  priority: LeadPriority;

  // Assignment
  assignedTo?: string; // Agent ID
  assignedAt?: Date;

  // Timing
  capturedAt: Date;
  firstContactedAt?: Date;
  convertedAt?: Date;

  // Metadata
  utmParameters?: UTMParameters;
  referrer?: string;
  device?: DeviceInfo;
}

interface LeadContact {
  name: {
    first: string;
    middle?: string;
    last: string;
  };
  email: string;
  phone: string;
  phoneVerified?: boolean;

  // Optional
  company?: string;
  title?: string;
  socialProfiles?: SocialProfile[];
}

interface TripInterest {
  destination?: string;
  destinations?: string[];
  departureDate?: Date;
  returnDate?: Date;
  flexibility?: string;

  travelers?: {
    adults: number;
    children?: number;
    infants?: number;
  };

  budget?: BudgetRange;
  preferences?: string[];
  tripType?: TripType;

  message?: string;
}

interface SourceDetails {
  channel: string;
  subChannel?: string;
  referrer?: string;
  keywords?: string;

  // Partner source
  partnerId?: string;
  partnerCommission?: number;

  // Offline source
  sourceAgent?: string;
  location?: string;
}

type LeadSource =
  | 'website_form'
  | 'landing_page'
  | 'social_media'
  | 'email'
  | 'chat'
  | 'phone'
  | 'walk_in'
  | 'referral'
  | 'event'
  | 'partner'
  | 'other';

type LeadStatus =
  | 'new'
  | 'contacted'
  | 'engaged'
  | 'qualified'
  | 'proposal'
  | 'negotiation'
  | 'converted'
  | 'lost'
  | 'unqualified';

type LeadPriority =
  | 'hot'
  | 'warm'
  | 'cold';

interface UTMParameters {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
}

interface DeviceInfo {
  type: 'desktop' | 'mobile' | 'tablet';
  os?: string;
  browser?: string;
}

interface LeadCaptureForm {
  formId: string;
  name: string;
  type: FormType;

  // Fields
  fields: FormField[];
  requiredFields: string[];

  // Behavior
  submitAction: SubmitAction;
  successMessage?: string;
  redirectUrl?: string;

  // Integration
  webhookUrl?: string;
  integration?: FormIntegration;
}

type FormType =
  | 'inline'
  | 'popup'
  | 'slide_in'
  | 'full_page';

interface FormField {
  fieldId: string;
  name: string;
  type: FieldType;
  label: string;
  placeholder?: string;
  required: boolean;
  validation?: ValidationRule;
  options?: string[]; // For select/radio
}

type FieldType =
  | 'text'
  | 'email'
  | 'phone'
  | 'number'
  | 'date'
  | 'select'
  | 'multiselect'
  | 'textarea'
  | 'checkbox'
  | 'radio';
```

---

## Open Problems

### 1. Form Friction
**Challenge:** More fields = fewer submissions

**Options:** Progressive profiling, smart defaults, minimize

### 2. Data Quality
**Challenge:** Bad contact information

**Options:** Validation, verification, social login

### 3. Source Attribution
**Challenge:** Multi-touch journeys

**Options:** Last touch, first touch, multi-touch attribution

### 4. Spam Prevention
**Challenge:** Bot submissions

**Options:** CAPTCHA, rate limiting, honeypot fields

### 5. Mobile Experience
**Challenge:** Forms are hard on mobile

**Options:** Optimized layouts, autofill, chat interface

---

## Next Steps

1. Design capture forms
2. Build submission pipeline
3. Implement validation
4. Create source tracking

---

**Status:** Research Phase — Capture patterns unknown

**Last Updated:** 2026-04-27
