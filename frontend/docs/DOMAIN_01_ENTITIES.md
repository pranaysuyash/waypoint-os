# Core Domain Model Foundation — Entity Models

> Bridging research: unified data model layer connecting all subsystem research into coherent entity definitions for Pydantic (backend) and TypeScript (frontend).

---

## Key Questions

1. **What are the core entities every subsystem depends on?**
2. **How do Enquiry, Booking, Trip, and Customer relate to each other?**
3. **What fields, states, and relationships define each entity?**
4. **How do existing codebase models (Trip, Agency, User) map to the canonical domain?**

---

## Research Areas

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  Agency   │──→│   User   │──→│HumanAgent │    │  Buyer   │          │
│  │(tenant)   │    │(account) │    │(staff)    │    │(customer)│          │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
│       │                                               │                 │
│       │                                               │                 │
│       ▼                                               ▼                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  Vendor   │──→│ Enquiry  │──→│   Trip   │──→│ Booking  │          │
│  │(supplier) │    │(inquiry) │    │(planning)│    │(reserved)│          │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
│       │                                               │                 │
│       │                                               ▼                 │
│       │                                         ┌──────────┐           │
│       └────────────────────────────────────────→│ Payment  │           │
│                                                 │(finance) │           │
│                                                 └──────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Relationships:
  Agency     1:N  User          (multi-tenant)
  Agency     1:N  HumanAgent    (staff members)
  Agency     1:N  Vendor        (suppliers)
  Buyer      1:N  Enquiry       (customer inquiries)
  Enquiry    1:1  Trip          (inquiry → planning)
  Trip       1:N  Booking       (one trip, multiple bookings)
  Booking    1:N  Payment       (payments per booking)
  Booking    N:1  Vendor        (vendor fulfillment)
  HumanAgent 1:N  Trip          (assigned agent)
```

### Enquiry Entity

```typescript
// ── Backend (Pydantic equivalent) ──
interface Enquiry {
  id: string;                          // UUID
  agency_id: string;                   // tenant
  buyer_id: string;                    // customer reference
  assigned_agent_id: string | null;    // human agent

  type: EnquiryType;
  status: EnquiryStatus;
  priority: EnquiryPriority;
  source: EnquirySource;

  // Core fields
  raw_input: string;                   // original customer message
  parsed_data: EnquiryParsedData;
  destinations: string[];              // ["Singapore", "Bali"]
  travel_dates: DateRange | null;
  budget: BudgetRange | null;
  party_composition: PartyComposition | null;

  // Workflow
  triage_result: TriageResult | null;
  extracted_packet: CanonicalPacketRef | null;
  validation: ValidationResult | null;
  decision: DecisionResult | null;

  // Metadata
  lead_source: string | null;
  tags: string[];
  notes: AgentNote[];
  follow_up_due_date: string | null;   // ISO datetime

  // Timestamps
  created_at: string;                  // ISO datetime
  updated_at: string;
  first_response_at: string | null;
  closed_at: string | null;
}

type EnquiryType = "NEW_TOUR" | "IN_PROGRESS_ISSUE" | "MODIFICATION" | "COMPLAINT" | "REFUND_REQUEST";

type EnquiryStatus =
  | "RAW"           // just received, unparsed
  | "PARSING"       // AI extracting data
  | "TRIAGE"        // being categorized/routed
  | "ASSIGNED"      // assigned to agent
  | "IN_REVIEW"     // agent reviewing
  | "QUOTING"       // preparing quote
  | "SENT"          // quote sent to customer
  | "NEGOTIATING"   // back and forth
  | "WON"           // converted to trip/booking
  | "LOST"          // customer declined
  | "EXPIRED"       // no response, timed out
  | "ESCALATED";    // requires supervisor

type EnquiryPriority = "URGENT" | "HIGH" | "MEDIUM" | "LOW";

type EnquirySource = "WHATSAPP" | "PHONE" | "EMAIL" | "WEBSITE" | "WALK_IN" | "REFERRAL" | "PORTAL";

interface EnquiryParsedData {
  destinations: string[];
  travel_dates: DateRange | null;
  budget: BudgetRange | null;
  traveler_count: number;
  pace_preference: "RELAXED" | "MODERATE" | "PACKED" | null;
  special_requests: string[];
  dietary_requirements: string[];
  accessibility_needs: string[];
}

interface BudgetRange {
  min: number;
  max: number;
  currency: string;                    // "INR"
  per_person: boolean;
}

interface PartyComposition {
  adults: number;
  children: number;
  infants: number;
  seniors: number;
  rooms_needed: number;
  relationships: string[];             // ["couple", "family", "friends"]
}

// ── Enquiry State Machine ──
//
//  RAW ──→ PARSING ──→ TRIAGE ──→ ASSIGNED ──→ IN_REVIEW
//                                                │
//                    ┌───────────────────────────┤
//                    │                           │
//                    ▼                           ▼
//                 QUOTING ──→ SENT ──→ NEGOTIATING ──→ WON
//                    │           │                    │
//                    │           │                    ▼
//                    │           └──→ LOST         Trip created
//                    │           └──→ EXPIRED
//                    └──→ ESCALATED ──→ ASSIGNED
```

### Booking Entity

```typescript
interface Booking {
  id: string;                          // UUID
  agency_id: string;
  trip_id: string;                     // parent trip
  enquiry_id: string;                  // originating enquiry
  buyer_id: string;
  assigned_agent_id: string;

  status: BookingStatus;
  type: BookingType;

  // Components
  components: BookingComponent[];

  // Pricing
  pricing: BookingPricing;

  // Vendors
  vendor_agreements: VendorAgreement[];

  // Timeline
  booking_date: string;
  travel_start_date: string | null;
  travel_end_date: string | null;
  cancellation_deadline: string | null;

  // Documents
  confirmation_docs: DocumentRef[];
  vouchers: VoucherRef[];

  // Metadata
  tags: string[];
  internal_notes: string;
  reference_codes: Record<string, string>;  // PNR, booking ref, etc.

  created_at: string;
  updated_at: string;
}

type BookingStatus =
  | "DRAFT"           // agent building
  | "PENDING"         // awaiting confirmation
  | "CONFIRMED"       // vendor confirmed
  | "PARTIAL"         // some components confirmed
  | "GUARANTEED"      // payment made, guaranteed
  | "TICKETED"        // tickets issued
  | "IN_PROGRESS"     // traveler is traveling
  | "COMPLETED"       // trip finished
  | "CANCELLED"       // cancelled by customer/agent
  | "REFUNDED"        // refund processed
  | "NO_SHOW";        // traveler didn't show

type BookingType = "HOTEL" | "FLIGHT" | "PACKAGE" | "ACTIVITY" | "TRANSPORT" | "INSURANCE" | "VISA" | "COMPOSITE";

interface BookingComponent {
  id: string;
  type: BookingType;
  vendor_id: string;
  status: "PENDING" | "CONFIRMED" | "CANCELLED" | "MODIFIED";
  description: string;
  dates: DateRange;
  quantity: number;
  unit_price: Money;
  total_price: Money;
  reference: string;                   // vendor booking ref
  cancellation_policy: CancellationPolicy | null;
}

interface BookingPricing {
  subtotal: Money;
  taxes: Money;
  fees: Money;
  discounts: Money;
  total: Money;
  paid: Money;
  outstanding: Money;
  margin: Money;
  margin_percentage: number;
}

interface VendorAgreement {
  vendor_id: string;
  component_ids: string[];
  terms: string;
  commission_rate: number;
  payment_terms: string;
}

interface CancellationPolicy {
  free_cancellation_until: string | null;
  penalty_tiers: {
    deadline: string;                  // days before travel
    penalty_percentage: number;
  }[];
  no_show_penalty: number;             // percentage
}

// ── Booking State Machine ──
//
//  DRAFT ──→ PENDING ──→ CONFIRMED ──→ GUARANTEED ──→ TICKETED
//               │                          │
//               ▼                          ▼
//           CANCELLED                  IN_PROGRESS ──→ COMPLETED
//                                               │
//                                               ▼
//                                           REFUNDED
//                                               │
//                                               ▼
//                                           NO_SHOW
```

### Buyer / Customer Entity

```typescript
interface Buyer {
  id: string;
  agency_id: string;

  // Identity
  full_name: string;
  email: string | null;
  phone: string;                       // primary (WhatsApp)
  alternate_phone: string | null;

  // Profile
  date_of_birth: string | null;
  gender: "MALE" | "FEMALE" | "OTHER" | "PREFER_NOT_TO_SAY" | null;
  nationality: string;                 // "Indian"
  languages: string[];                 // ["Hindi", "English"]

  // Address
  address: Address | null;
  city: string | null;
  state: string | null;
  pincode: string | null;

  // Travel profile
  travel_preferences: TravelPreferences;
  loyalty_tier: "BRONZE" | "SILVER" | "GOLD" | "PLATINUM" | "DIAMOND";
  lifetime_value: number;              // INR
  booking_count: number;
  last_booking_date: string | null;

  // Segmentation
  segment: CustomerSegment | null;
  lifecycle_stage: CustomerLifecycleStage;
  tags: string[];

  // KYC
  kyc_status: "PENDING" | "VERIFIED" | "REJECTED" | "NOT_REQUIRED";
  pan_number: string | null;
  gst_number: string | null;           // for corporate

  // Communication
  preferred_channel: "WHATSAPP" | "EMAIL" | "PHONE" | "SMS";
  communication_consent: boolean;
  marketing_consent: boolean;
  do_not_contact: boolean;

  // Relationships
  linked_buyers: string[];             // family/group members
  referral_code: string | null;
  referred_by: string | null;

  // Documents
  passports: PassportRef[];
  visas: VisaRef[];

  created_at: string;
  updated_at: string;
}

type CustomerSegment =
  | "BUDGET" | "MID_RANGE" | "PREMIUM" | "LUXURY"
  | "CORPORATE" | "GROUP" | "HONEYMOON" | "FAMILY"
  | "ADVENTURE" | "RELIGIOUS" | "SENIOR";

type CustomerLifecycleStage =
  | "PROSPECT"        // never booked
  | "FIRST_TIME"      // one booking
  | "REPEAT"          // 2-3 bookings
  | "LOYAL"           // 4+ bookings
  | "ADVOCATE"        // refers others
  | "DORMANT"         // no activity 90+ days
  | "CHURNED";        // no activity 365+ days

interface TravelPreferences {
  pace: "RELAXED" | "MODERATE" | "PACKED";
  interests: string[];                 // ["beach", "adventure", "cultural", "religious"]
  dietary: string[];                   // ["vegetarian", "jain", "vegan"]
  accessibility: string[];
  preferred_airlines: string[];
  preferred_hotel_chains: string[];
  seat_preference: "WINDOW" | "AISLE" | "NO_PREFERENCE" | null;
  meal_preference: string | null;
  budget_range: BudgetRange | null;
}

interface Address {
  line1: string;
  line2: string | null;
  city: string;
  state: string;
  pincode: string;
  country: string;
}
```

### HumanAgent Entity

```typescript
interface HumanAgent {
  id: string;
  user_id: string;                     // linked auth account
  agency_id: string;

  // Identity
  full_name: string;
  email: string;
  phone: string;
  employee_id: string;

  // Role
  role: AgentRole;
  department: string | null;
  reports_to: string | null;           // manager agent id

  // Skills & Expertise
  specializations: string[];           // ["Southeast Asia", "Honeymoon", "Corporate"]
  language_skills: string[];           // ["English", "Hindi", "Tamil"]
  certifications: Certification[];
  destinations_expertise: string[];    // ["Singapore", "Kerala", "Europe"]

  // Workload
  status: AgentStatus;
  current_load: number;                // active trips
  max_load: number;                    // capacity limit
  active_trip_ids: string[];

  // Performance
  performance_tier: "TRAINEE" | "JUNIOR" | "MID" | "SENIOR" | "LEAD" | "MANAGER";
  performance_score: number;           // 0-100
  metrics: AgentMetrics;

  // Schedule
  shift: ShiftInfo | null;
  availability: AvailabilityCalendar;

  // Compensation
  commission_rate: number | null;
  commission_tier: string | null;

  created_at: string;
  updated_at: string;
}

type AgentRole =
  | "AGENT" | "SENIOR_AGENT" | "TEAM_LEAD"
  | "SUPERVISOR" | "MANAGER" | "ADMIN";

type AgentStatus =
  | "ONLINE" | "BUSY" | "AWAY" | "OFFLINE"
  | "ON_LEAVE" | "IN_TRAINING";

interface Certification {
  name: string;                        // "IATA Certified", "Destination Specialist - Kerala"
  issuer: string;
  valid_from: string;
  valid_until: string | null;
  certificate_id: string;
}

interface AgentMetrics {
  total_trips_handled: number;
  avg_response_time_minutes: number;
  conversion_rate: number;             // enquiries → bookings
  customer_satisfaction_score: number; // 1-5
  avg_trip_value: number;              // INR
  revenue_generated: number;           // lifetime INR
  cancellation_rate: number;
  repeat_customer_rate: number;
}

interface ShiftInfo {
  type: "MORNING" | "AFTERNOON" | "EVENING" | "NIGHT" | "FLEXIBLE";
  start_time: string;                  // "09:00"
  end_time: string;                    // "18:00"
  working_days: number[];              // [1,2,3,4,5] = Mon-Fri
}

// ── Skill-based routing ──
// ┌─────────────────────────────────────────┐
// │  Enquiry comes in                        │
// │       │                                  │
// │       ▼                                  │
// │  ┌──────────────┐                       │
// │  │ Extract      │ (destinations, type)  │
// │  │ requirements │                        │
// │  └──────────────┘                       │
// │       │                                  │
// │       ▼                                  │
// │  ┌──────────────┐                       │
// │  │ Match agent  │                       │
// │  │ skills       │                        │
// │  └──────────────┘                       │
// │       │                                  │
// │       ├──→ Expertise match (40%)         │
// │       ├──→ Language match (20%)          │
// │       ├──→ Availability (20%)           │
// │       └──→ Current load (20%)           │
// │       │                                  │
// │       ▼                                  │
// │  ┌──────────────┐                       │
// │  │ Assign to    │                       │
// │  │ best agent   │                        │
// │  └──────────────┘                       │
// └──────────────────────────────────────────┘
```

### Vendor Entity

```typescript
interface Vendor {
  id: string;
  agency_id: string;

  // Identity
  name: string;
  type: VendorType;
  category: VendorCategory;

  // Contact
  primary_contact: ContactPerson;
  secondary_contacts: ContactPerson[];
  support_contacts: ContactPerson[];    // 24/7 support line

  // Business
  registration_number: string | null;   // GST, IATA, etc.
  tax_id: string | null;
  bank_details: BankDetails | null;

  // Service areas
  service_destinations: string[];       // ["Singapore", "Malaysia"]
  service_types: string[];              // ["hotel", "transfer", "activity"]

  // Relationship
  status: VendorStatus;
  onboarding_date: string;
  contract_start: string | null;
  contract_end: string | null;
  tier: "STANDARD" | "PREFERRED" | "PREMIUM" | "EXCLUSIVE";

  // Performance
  performance_score: number;            // 0-100
  metrics: VendorMetrics;

  // Rates
  rate_agreements: RateAgreement[];
  commission_structure: CommissionStructure | null;

  // Compliance
  licenses: License[];
  insurance: InsuranceInfo | null;
  certifications: string[];

  // Integration
  api_endpoint: string | null;
  integration_type: "API" | "EDI" | "MANUAL" | "PORTAL" | "WHATSAPP";
  booking_confirmation_channel: "API" | "EMAIL" | "WHATSAPP" | "PORTAL";

  tags: string[];
  notes: string;

  created_at: string;
  updated_at: string;
}

type VendorType =
  | "HOTEL" | "RESORT" | "HOMESTAY"
  | "AIRLINE" | "GDS"
  | "TOUR_OPERATOR" | "DMC"
  | "TRANSPORT" | "CAR_RENTAL" | "TRANSFER"
  | "ACTIVITY" | "EXPERIENCE"
  | "INSURANCE" | "VISA" | "FOREX"
  | "CRUISE" | "RAIL"
  | "OTHER";

type VendorCategory = "ACCOMMODATION" | "TRANSPORTATION" | "ACTIVITY" | "FINANCIAL" | "GOVERNMENT" | "TECHNOLOGY";

type VendorStatus = "ACTIVE" | "INACTIVE" | "SUSPENDED" | "ONBOARDING" | "TERMINATED";

interface ContactPerson {
  name: string;
  designation: string;
  email: string;
  phone: string;
  whatsapp: string | null;
  is_primary: boolean;
}

interface VendorMetrics {
  total_bookings: number;
  cancellation_rate: number;
  avg_response_time_hours: number;
  on_time_rate: number;                // percentage
  customer_complaint_rate: number;
  price_competitiveness: number;       // 1-10
  quality_score: number;               // 1-10
}

interface RateAgreement {
  id: string;
  product_type: string;
  season: string;                      // "peak", "off", "shoulder"
  valid_from: string;
  valid_until: string;
  rate_type: "NET" | "COMMISSION" | "MARGIN";
  rate_value: number;
  currency: string;
  terms: string;
}

interface CommissionStructure {
  type: "PERCENTAGE" | "FLAT" | "TIERED";
  rates: {
    product_type: string;
    rate: number;
    min_booking_value: number | null;
  }[];
}
```

### Payment Entity

```typescript
interface Payment {
  id: string;
  agency_id: string;
  booking_id: string;
  buyer_id: string;

  type: PaymentType;
  status: PaymentStatus;
  direction: "INBOUND" | "OUTBOUND";

  // Amount
  amount: Money;
  currency: string;

  // Method
  method: PaymentMethod;
  gateway: string | null;
  gateway_reference: string | null;

  // Timing
  due_date: string | null;
  paid_at: string | null;
  refunded_at: string | null;

  // Links
  invoice_id: string | null;
  receipt_id: string | null;
  refund_id: string | null;

  // Audit
  created_by: string;
  notes: string;

  created_at: string;
  updated_at: string;
}

type PaymentType =
  | "ADVANCE" | "PARTIAL" | "FULL" | "BALANCE"
  | "REFUND" | "CANCEL_PENALTY" | "MODIFICATION_FEE"
  | "VENDOR_PAYMENT" | "COMMISSION";

type PaymentStatus =
  | "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"
  | "REFUNDED" | "PARTIALLY_REFUNDED" | "CANCELLED" | "DISPUTED";

type PaymentMethod =
  | "UPI" | "CREDIT_CARD" | "DEBIT_CARD" | "NET_BANKING"
  | "BANK_TRANSFER" | "CASH" | "CHEQUE" | "EMI"
  | "WALLET" | "FOREX_CARD";

interface Money {
  amount: number;                      // in smallest unit (paise for INR)
  currency: string;                    // "INR"
  display: string;                     // "₹12,500"
}
```

---

## Open Problems

1. **Enquiry vs Trip overlap** — The existing codebase uses `Trip` as the central entity, but conceptually Enquiry and Trip are distinct phases. Should Enquiry be a separate model or a state within Trip? The current `Trip.status` field conflates both.

2. **Booking granularity** — A single trip may have 10+ bookings (hotel, flights, transfers, activities). How granular should the BookingComponent model be? Over-normalization hurts query performance; under-normalization makes vendor reconciliation impossible.

3. **Buyer identity fragmentation** — Indian customers often have multiple phone numbers, WhatsApp on different numbers, and share family email addresses. De-duplication is non-trivial and needs fuzzy matching (phone + name + city).

4. **Vendor rate volatility** — Hotel and flight rates change multiple times daily. The RateAgreement model needs versioning and real-time price caching, not just static agreements.

5. **Multi-currency Money type** — Every financial entity needs consistent money handling. Floating-point arithmetic causes rounding errors at scale. Should use integer paise/cents throughout.

---

## Next Steps

- [ ] Map existing SQLAlchemy Trip model fields to canonical Enquiry/Trip/Booking split
- [ ] Design database migration strategy (Trip → Enquiry + Trip + Booking)
- [ ] Define Pydantic models for backend validation layer
- [ ] Create TypeScript equivalents for frontend API client types
- [ ] Build entity relationship migration script with foreign key analysis
