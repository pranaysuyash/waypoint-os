# Customer Relationship Management 01: Profiles

> Customer data collection, profiles, and preferences

---

## Document Overview

**Focus:** Customer profile management
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Data Collection
- What customer data do we collect?
- How do we capture preferences?
- What about travel companions?
- How do we handle family accounts?

### Profile Structure
- How are profiles organized?
- What are the key data points?
- How do we handle multiple travelers?
- What about corporate profiles?

### Privacy & Consent
- What permissions do we need?
- How do we handle data requests?
- What about GDPR compliance?
- How do we secure data?

### Profile Enrichment
- How do we enhance profiles?
- What external data sources?
- How do we infer preferences?
- What about social data?

---

## Research Areas

### A. Customer Data

**Core Data:**

| Field | Required | Purpose | Research Needed |
|-------|----------|---------|-----------------|
| **Name** | Yes | Identification | ? |
| **Email** | Yes | Communication | ? |
| **Phone** | Yes | Urgent contact | ? |
| **Date of birth** | No | Personalization | ? |
| **Address** | No | Documents | ? |
| **ID proof** | Sometimes | Bookings | ? |

**Travel Preferences:**

| Category | Data Points | Research Needed |
|----------|-------------|-----------------|
| **Destinations** | Favorite, visited, wishlist | ? |
| **Accommodation** | Type, amenities, brands | ? |
| **Dining** | Cuisine, restrictions | ? |
| **Activities** | Interests, past activities | ? |
| **Transport** | Preferences, seat types | ? |
| **Service** | Communication style | ? |

**Companion Data:**

| Type | Data | Research Needed |
|------|------|-----------------|
| **Family** | Names, ages, relationships | ? |
| **Friends** | Names, preferences | ? |
| **Colleagues** | Corporate context | ? |
| **Groups** | Travel together patterns | ? |

### B. Profile Types

**Individual Profile:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Single traveler** | Personal account | ? |
| **Own bookings** | My trips | ? |
| **Personal preferences** | My choices | ? |
| **Payment methods** | My cards | ? |

**Family Profile:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Primary account** | Main contact | ? |
| **Family members** | Linked profiles | ? |
| **Shared bookings** | Family trips | ? |
| **Collective preferences** | Family choices | ? |

**Corporate Profile:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Company account** | Business entity | ? |
| **Employees** | Linked travelers | ? |
| **Travel policies** | Company rules | ? |
| **Billing** | Centralized payment | ? |

### C. Privacy & Consent

**Consent Types:**

| Consent | Required | Purpose | Research Needed |
|---------|----------|---------|-----------------|
| **Marketing** | Opt-in | Promotions | ? |
| **Analytics** | Opt-out | Usage tracking | ? |
| **Data sharing** | Opt-in | Partner offers | ? |
| **Profiling** | Opt-out | Personalization | ? |

**Data Rights:**

| Right | Implementation | Research Needed |
|-------|----------------|-----------------|
| **Access** | Self-service export | ? |
| **Correction** | Editable profile | ? |
| **Deletion** | Right to be forgotten | ? |
| **Portability** | Data export | ? |
| **Objection** | Processing limits | ? |

**Security Measures:**

| Measure | Purpose | Research Needed |
|---------|---------|-----------------|
| **Encryption** | Data at rest | ? |
| **Access control** | Role-based | ? |
| **Audit log** | Track access | ? |
| **Anonymization** | Privacy protection | ? |

### D. Profile Enrichment

**Inferred Preferences:**

| Source | Inference | Research Needed |
|--------|-----------|-----------------|
| **Booking history** | Preferred destinations | ? |
| **Spending** | Budget range | ? |
| **Seasonality** | Travel timing | ? |
| **Accommodation type** | Hotel preferences | ? |

**External Data:**

| Source | Data | Research Needed |
|--------|------|-----------------|
| **Social media** | Interests, lifestyle | ? |
| **Public records** | Demographics | ? |
| **Travel APIs** | Status, loyalty | ? |
| **Data providers** | Enriched profiles | ? |

**Social Profiles:**

| Platform | Value | Research Needed |
|----------|-------|-----------------|
| **LinkedIn** | Professional context | ? |
| **Facebook** | Interests, family | ? |
| **Instagram** | Travel style | ? |
| **TripAdvisor** | Reviews, preferences | ? |

---

## Data Model Sketch

```typescript
interface CustomerProfile {
  customerId: string;
  agencyId: string;

  // Basic info
  name: PersonName;
  email: string;
  phone: string;
  phoneVerified: boolean;

  // Demographics
  dateOfBirth?: Date;
  gender?: Gender;
  nationality?: string;
  languages: string[];

  // Address
  address?: PostalAddress;

  // IDs
  governmentIds?: GovernmentId[];

  // Profile type
  type: CustomerType;
  familyId?: string;
  companyId?: string;

  // Preferences
  preferences: CustomerPreferences;

  // Travelers (linked)
  linkedTravelers: LinkedTraveler[];

  // Status
  status: CustomerStatus;
  createdAt: Date;
  updatedAt: Date;

  // Privacy
  consent: ConsentRecord[];
}

interface PersonName {
  title?: string;
  first: string;
  middle?: string;
  last: string;
  suffix?: string;
}

interface GovernmentId {
  type: 'passport' | 'aadhaar' | 'driving_license' | 'other';
  number: string; // Encrypted
  country: string;
  expiryDate?: Date;
  verified: boolean;
}

type CustomerType = 'individual' | 'family_head' | 'employee';

interface CustomerPreferences {
  // Travel style
  travelStyle?: TravelStyle[];
  tripTypes?: TripType[];

  // Destinations
  favoriteDestinations?: string[];
  visitedDestinations?: string[];
  wishlist?: string[];

  // Accommodation
  accommodationTypes?: string[];
  hotelBrands?: string[];
  roomPreferences?: RoomPreference[];

  // Dining
  cuisines?: string[];
  dietaryRestrictions?: string[];

  // Activities
  activityInterests?: string[];

  // Transport
  seatPreference?: SeatPreference;
  mealPreference?: MealPreference;

  // Communication
  preferredLanguage?: string;
  communicationChannel?: CommunicationChannel;
  contactFrequency?: ContactFrequency;

  // Service
  specialRequests?: string[];
}

interface LinkedTraveler {
  travelerId: string;
  relationship: Relationship;
  name: string;
  dateOfBirth?: Date;
  permissions: TravelerPermissions;
}

type Relationship =
  | 'spouse'
  | 'child'
  | 'parent'
  | 'sibling'
  | 'friend'
  | 'colleague'
  | 'other';

interface TravelerPermissions {
  canBook: boolean;
  canViewBookings: boolean;
  canMakePayments: boolean;
}

interface FamilyProfile {
  familyId: string;
  agencyId: string;
  name: string;

  // Members
  primaryCustomerId: string;
  members: FamilyMember[];

  // Preferences
  collectivePreferences?: CustomerPreferences;

  // Travel together
  traveledTogether: number;
}

interface FamilyMember {
  customerId: string;
  role: FamilyRole;
  joinedAt: Date;
}

type FamilyRole = 'head' | 'spouse' | 'child' | 'other';

interface CorporateProfile {
  companyId: string;
  agencyId: string;

  // Company info
  name: string;
  industry?: string;
  size?: CompanySize;
  address: PostalAddress;

  // Contacts
  primaryContact: ContactInfo;
  billingContact: ContactInfo;

  // Policies
  travelPolicy?: TravelPolicy;

  // Employees
  employees: CorporateEmployee[];

  // Commercial
  creditLimit?: number;
  paymentTerms?: PaymentTerms;
}

interface CorporateEmployee {
  customerId: string;
  employeeId: string;
  department?: string;
  role?: string;
  managerId?: string;

  // Policy overrides
  policyOverrides?: PolicyOverride[];

  // Travel
  traveledCount: number;
  spentThisYear: number;
}

interface ConsentRecord {
  consentId: string;
  type: ConsentType;
  granted: boolean;
  grantedAt?: Date;
  withdrawnAt?: Date;
  source: 'web' | 'mobile' | 'paper';
  version: string;
}

type ConsentType =
  | 'marketing_email'
  | 'marketing_sms'
  | 'analytics'
  | 'data_sharing'
  | 'profiling';
```

---

## Open Problems

### 1. Data Quality
**Challenge:** Outdated or incorrect information

**Options:** Verification, self-service updates, periodic refresh

### 2. Profile Merging
**Challenge:** Duplicate profiles

**Options:** Auto-merge, ML matching, manual review

### 3. Privacy Balance
**Challenge:** Personalization vs. privacy

**Options:** Consent management, transparency, user control

### 4. Family Complexity
**Challenge:** Diverse family structures

**Options:** Flexible relationships, multiple connections, custom labels

### 5. Corporate Complexity
**Challenge:** Hierarchy, policies, approvals

**Options:** Clear data model, policy engine, approval workflows

---

## Next Steps

1. Define profile schema
2. Build profile management UI
3. Implement consent system
4. Create data enrichment pipeline

---

**Status:** Research Phase — Profile patterns unknown

**Last Updated:** 2026-04-27
