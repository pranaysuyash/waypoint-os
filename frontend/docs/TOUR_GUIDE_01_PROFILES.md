# Tour Guide & Escort Management — Guide Profiles & Qualifications

> Research document for guide profile management, certification tracking, skill matrices, availability calendars, and guide ratings.

---

## Key Questions

1. **How do we manage comprehensive guide profiles with certifications and skills?**
2. **What license and certification tracking is required for Indian tour guides?**
3. **How do we build a skill matrix for intelligent guide-trip matching?**
4. **How do availability calendars prevent double-booking?**

---

## Research Areas

### Guide Profile Model

```typescript
interface TourGuide {
  id: string;
  agency_id: string;
  user_id: string;                     // linked auth account

  // Identity
  full_name: string;
  display_name: string;
  email: string;
  phone: string;
  whatsapp: string | null;
  photo_url: string | null;
  bio: string;

  // Demographics
  date_of_birth: string | null;
  gender: "MALE" | "FEMALE" | "OTHER" | null;
  nationality: string;
  languages: LanguageSkill[];

  // Professional
  employee_type: "FULL_TIME" | "PART_TIME" | "FREELANCE" | "CONTRACT";
  years_experience: number;
  specializations: GuideSpecialization[];
  certifications: GuideCertification[];
  destinations_expertise: DestinationExpertise[];

  // Availability
  status: "AVAILABLE" | "ON_TOUR" | "ON_LEAVE" | "INACTIVE";
  availability_calendar: AvailabilityEntry[];
  home_base: string;                   // city

  // Performance
  rating: number;                      // 1-5
  total_tours: number;
  total_customers_hosted: number;
  metrics: GuidePerformanceMetrics;

  // Financial
  daily_rate: Money | null;
  commission_rate: number | null;

  // Emergency
  emergency_contact: ContactPerson;
  blood_group: string | null;
  medical_conditions: string[];

  created_at: string;
  updated_at: string;
}

interface LanguageSkill {
  language: string;                    // "English", "Hindi", "Tamil"
  proficiency: "NATIVE" | "FLUENT" | "CONVERSATIONAL" | "BASIC";
  can_translate: boolean;
  certified: boolean;
}

type GuideSpecialization =
  | "CITY_TOUR" | "HERITAGE" | "ADVENTURE" | "WILDLIFE"
  | "RELIGIOUS" | "CULINARY" | "PHOTOGRAPHY" | "NATURE"
  | "CULTURAL" | "MEDICAL_WELLNESS" | "HONEYMOON" | "FAMILY"
  | "CORPORATE" | "MICE" | "ECO_TOURISM" | "LUXURY";

interface DestinationExpertise {
  destination: string;                 // "Rajasthan", "Kerala", "Singapore"
  level: "BEGINNER" | "INTERMEDIATE" | "ADVANCED" | "EXPERT";
  tours_conducted: number;
  last_tour_date: string | null;
  local_contacts: number;              // vendor/restaurant contacts
}
```

### Certification Tracking

```typescript
interface GuideCertification {
  id: string;
  name: string;
  issuer: string;
  category: CertCategory;
  certificate_number: string;
  issue_date: string;
  expiry_date: string | null;
  verification_url: string | null;
  document_url: string | null;
  status: "ACTIVE" | "EXPIRED" | "PENDING_RENEWAL" | "REVOKED";
}

type CertCategory =
  | "TOURISM_BOARD"      // state/national tourism board
  | "FIRST_AID"          // first aid/CPR
  | "LANGUAGE"           // language proficiency test
  | "SPECIALIZATION"     // adventure, wildlife, heritage
  | "DRIVING"            // commercial driving license
  | "FOOD_SAFETY"        // food handling certificate
  | "SAFETY"             // safety and emergency procedures
  | "ACCESSIBILITY"      // disability awareness
  | "CULTURAL";          // cultural sensitivity training

// ── Indian Tourism Board Certifications ──
// ┌─────────────────────────────────────────┐
// │  Certification                 | Issuer   │
// │  ─────────────────────────────────────── │
// │  Regional Level Guide          | State    │
// │  (e.g., Kerala TG)             | Tourism  │
// │                                | Board    │
// │  National Level Guide          | Ministry │
// │  (Incredible India certified)  | of Tourism│
// │                                           │
// │  State-specific:                           │
// │  - Rajasthan: RTDC certified              │
// │  - Kerala: KTDC certified                 │
// │  - Goa: GTDC certified                    │
// │  - Delhi: Delhi Tourism certified         │
// │                                           │
// │  Renewal: Every 3-5 years                 │
// │  Required: First aid, language test       │
// │  Background check mandatory               │
// └───────────────────────────────────────────┘
```

### Skill Matrix & Matching Score

```typescript
// ── Guide-Trip Matching Algorithm ──
interface GuideTripMatch {
  guide_id: string;
  trip_id: string;
  overall_score: number;               // 0-100

  scores: {
    destination_expertise: number;      // 0-100
    language_match: number;             // 0-100
    specialization_match: number;       // 0-100
    availability: number;              // 0-100
    cost_fit: number;                  // 0-100
    past_performance: number;          // 0-100
    customer_preference: number;       // 0-100 (repeat customer)
  };

  weights: {
    destination_expertise: 0.25;
    language_match: 0.15;
    specialization_match: 0.15;
    availability: 0.20;
    cost_fit: 0.10;
    past_performance: 0.10;
    customer_preference: 0.05;
  };
}

// ┌─────────────────────────────────────────┐
// │  Skill Matrix Heat Map                   │
// │                                           │
// │  Guide    │ Raj │ Ker │ Goa │ Sin │ Bali │
// │  ─────────────────────────────────────── │
// │  Ravi     │ 95  │ 80  │ 60  │ 90  │ 45  │
// │  Priya    │ 40  │ 95  │ 70  │ 50  │ 80  │
// │  Amit     │ 70  │ 60  │ 90  │ 85  │ 90  │
// │  Sita     │ 85  │ 70  │ 50  │ 30  │ 60  │
// │                                           │
// │  Legend: 90+ = Expert, 70-89 = Advanced  │
// │          50-69 = Intermediate, <50 = Nov  │
// └───────────────────────────────────────────┘
```

### Availability Calendar

```typescript
interface AvailabilityEntry {
  date: string;                        // ISO date
  status: "AVAILABLE" | "ON_TOUR" | "ON_LEAVE" | "BLOCKED";
  tour_id: string | null;
  notes: string | null;
}

// ── Availability calendar view ──
// ┌─────────────────────────────────────────┐
// │  April 2026 — Ravi (Rajasthan Expert)    │
// │                                           │
// │  Mon Tue Wed Thu Fri Sat Sun             │
// │           1   2   3   4   5              │
// │           ✅  ✅  🔴  🔴  ✅              │
// │  6   7   8   9  10  11  12              │
// │  ✅  ✅  ✅  ✅  🟡  🟡  ✅              │
// │  13  14  15  16  17  18  19              │
// │  🔴  🔴  🔴  ✅  ✅  ✅  ✅              │
// │                                           │
// │  ✅ Available  🔴 On Tour  🟡 Hold       │
// │                                           │
// │  Tours:                                    │
// │  Apr 3-4: Jaipur City Tour (TP-101)      │
// │  Apr 10-11: Udaipur Weekend (TP-205)     │
// │  Apr 13-15: Jodhpur Heritage (TP-312)    │
// └───────────────────────────────────────────┘

// Conflict detection:
// ┌─────────────────────────────────────────┐
// │  New Assignment Check:                    │
// │  Guide: Ravi                              │
// │  Requested: Apr 10-12                     │
// │                                           │
// │  ❌ CONFLICT: TP-205 (Apr 10-11)         │
// │  Suggestion: Priya (score: 78)            │
// │            or Amit (score: 72)            │
// └───────────────────────────────────────────┘
```

---

## Open Problems

1. **Freelance guide reliability** — Freelance guides may cancel last-minute for better-paying gigs. Need backup guides and penalty clauses in contracts.

2. **Certification verification** — Tourism board databases are not digitized in many Indian states. Manual verification is slow and error-prone.

3. **Language proficiency subjectivity** — Self-reported language skills are unreliable. Need standardized language assessment or certification requirements.

4. **Seasonal availability** — Guide availability is highly seasonal (peak during Diwali, summer, Christmas). Calendar management must handle seasonal patterns.

---

## Next Steps

- [ ] Build guide profile CRUD with certification document upload
- [ ] Implement skill matrix scoring algorithm
- [ ] Create availability calendar with conflict detection
- [ ] Design certification expiry tracking and renewal alerts
- [ ] Study Indian tourism board certification databases for integration
