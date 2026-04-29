# Tour Guide & Escort Management — Assignment & Matching

> Research document for guide-trip matching algorithms, multi-guide planning, emergency substitution, briefing systems, and commission calculation.

---

## Key Questions

1. **How do we match guides to trips based on skills, language, and availability?**
2. **How do we handle multi-guide trips for large groups?**
3. **What happens when a guide becomes unavailable at the last minute?**
4. **How are guide commissions calculated per assignment?**

---

## Research Areas

### Guide Assignment Algorithm

```typescript
interface AssignmentEngine {
  matchGuide(trip: TripRequirement): GuideMatchResult;
  assignGuide(guide_id: string, trip_id: string): Assignment;
  findSubstitute(assignment: Assignment, reason: string): GuideMatchResult;
}

interface TripRequirement {
  trip_id: string;
  destinations: string[];
  specializations: GuideSpecialization[];
  required_languages: string[];
  preferred_languages: string[];
  group_size: number;
  travel_dates: DateRange;
  budget_range: Money | null;
  accessibility_needs: string[];
  customer_preferences: string[];
  previous_guide_id: string | null;    // repeat customer preference
}

interface GuideMatchResult {
  candidates: RankedCandidate[];
  best_match: RankedCandidate;
  fallback_options: RankedCandidate[];
}

interface RankedCandidate {
  guide_id: string;
  guide_name: string;
  score: number;                       // 0-100
  breakdown: {
    destination_expertise: number;
    language_match: number;
    specialization_match: number;
    availability: number;
    cost_fit: number;
    performance_score: number;
    customer_preference: number;
  };
  availability_confirmed: boolean;
  estimated_cost: Money;
  notes: string;
}

// ── Assignment flow ──
// ┌─────────────────────────────────────────┐
// │  Trip Requirements                        │
// │       │                                    │
// │       ▼                                    │
// │  ┌──────────────┐                        │
// │  │ Filter        │                       │
// │  │ Available     │ (date range check)    │
// │  │ guides        │                        │
// │  └──────────────┘                        │
// │       │                                    │
// │       ▼                                    │
// │  ┌──────────────┐                        │
// │  │ Score each    │                       │
// │  │ candidate     │ (weighted algorithm)  │
// │  └──────────────┘                        │
// │       │                                    │
// │       ├── Top 3 candidates ranked          │
// │       │                                    │
// │       ▼                                    │
// │  ┌──────────────┐                        │
// │  │ Send          │                       │
// │  │ assignment    │ (push notification)    │
// │  │ request       │                        │
// │  └──────────────┘                        │
// │       │                                    │
// │       ├── Guide accepts → CONFIRMED        │
// │       ├── Guide declines → NEXT            │
// │       └── No response (30min) → NEXT       │
// └───────────────────────────────────────────┘
```

### Multi-Guide Trip Planning

```typescript
interface MultiGuideAssignment {
  trip_id: string;
  lead_guide: GuideAssignment;
  support_guides: GuideAssignment[];
  assignment_strategy: AssignmentStrategy;
}

interface GuideAssignment {
  guide_id: string;
  role: "LEAD" | "SUPPORT" | "LOCAL" | "SPECIALIST";
  segments: TripSegment[];
  responsibilities: string[];
}

interface TripSegment {
  destination: string;
  dates: DateRange;
  activities: string[];
}

type AssignmentStrategy =
  | "SINGLE_GUIDE"       // one guide for entire trip
  | "DESTINATION_HANDOFF" // different guide per destination
  | "LEAD_PLUS_LOCAL"    // lead guide + local experts at each stop
  | "TEAM_COVER"         // 2+ guides covering the whole trip
  | "SPECIALIST_MIX";    // adventure guide + cultural guide

// ── Multi-guide example: Golden Triangle + Kerala ──
// ┌─────────────────────────────────────────────────┐
// │  Trip: Delhi → Jaipur → Agra → Kochi → Alleppey │
// │  Group: 25 people (corporate retreat)            │
// │                                                   │
// │  Assignment:                                      │
// │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
// │  │ Ravi     │  │ Priya    │  │ Suresh   │       │
// │  │ LEAD     │  │ SUPPORT  │  │ LOCAL    │       │
// │  │ Full trip│  │ Full trip│  │ Kerala   │       │
// │  │ Hindi/En │  │ Hindi/Ta │  │ Malayalam│       │
// │  └──────────┘  └──────────┘  └──────────┘      │
// │                                                   │
// │  Responsibilities:                                │
// │  Ravi: Overall coordination, Delhi/Jaipur/Agra    │
// │  Priya: Group management, Agra/Kerala transition  │
// │  Suresh: Kerala segment, local contacts           │
// │                                                   │
// │  Group ratio: 25 pax = 1 guide per 12.5           │
// │  Recommended: 1 per 15 max for premium trips      │
// └───────────────────────────────────────────────────┘
```

### Emergency Substitution Protocol

```typescript
interface EmergencySubstitution {
  original_assignment: GuideAssignment;
  reason: "ILLNESS" | "FAMILY_EMERGENCY" | "ACCIDENT" | "NO_SHOW"
    | "VISA_ISSUE" | "TRANSPORT_FAILURE" | "PERSONAL";
  timing: "PRE_TRIP" | "DAY_OF" | "MID_TOUR";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

  // Substitution process
  replacement_search: {
    initiated_at: string;
    candidates_contacted: number;
    candidate_ids: string[];
  };
  replacement: GuideAssignment | null;
  handover_document: string | null;
  customer_notification_sent: boolean;
  customer_response: "ACCEPTED" | "CONCERN" | "ESCALATION" | null;
}

// ── Emergency protocol by timing ──
// ┌─────────────────────────────────────────┐
// │  PRE-TRIP (24+ hours before):            │
// │  1. Find best alternative (score > 70)   │
// │  2. Brief replacement guide              │
// │  3. Notify customer (if premium)         │
// │  4. No penalty to original guide         │
// │                                           │
// │  DAY-OF (< 24 hours):                     │
// │  1. Find any available qualified guide    │
// │  2. Express briefing (phone call)        │
// │  3. Notify customer                      │
// │  4. Log incident for guide's record      │
// │                                           │
// │  MID-TOUR (during trip):                  │
// │  1. Find local replacement immediately   │
// │  2. Remote briefing via phone             │
// │  3. Support guide takes over (if team)   │
// │  4. Customer apology + compensation      │
// │  5. Incident report + performance review │
// └───────────────────────────────────────────┘
```

### Guide Briefing System

```typescript
interface GuideBriefing {
  id: string;
  assignment_id: string;
  guide_id: string;
  trip_id: string;

  // Trip overview
  trip_summary: string;
  destinations: string[];
  itinerary: ItineraryDay[];
  group_profile: GroupProfile;

  // Customer details
  customer_preferences: string[];
  dietary_requirements: string[];
  accessibility_needs: string[];
  special_instructions: string[];
  vip_notes: string[];

  // Logistics
  meeting_point: string;
  meeting_time: string;
  emergency_contacts: ContactPerson[];
  vendor_contacts: VendorContact[];
  backup_plans: BackupPlan[];

  // Resources
  destination_guide_url: string | null;
  route_map_url: string | null;
  activity_details_url: string | null;

  // Acknowledgment
  briefing_sent_at: string;
  briefing_acknowledged_at: string | null;
  guide_questions: string[];
}

interface GroupProfile {
  size: number;
  demographics: string;                // "25 corporate executives, 30-45 age"
  language_preference: string;
  pace_preference: string;
  interests: string[];
  previous_travel_experience: string;
}
```

### Commission Calculation

```typescript
interface GuideCommission {
  guide_id: string;
  trip_id: string;

  // Base
  daily_rate: Money;
  tour_days: number;
  base_pay: Money;

  // Bonus
  customer_satisfaction_bonus: Money | null;
  on_time_bonus: Money | null;
  repeat_customer_bonus: Money | null;
  premium_trip_bonus: Money | null;

  // Deductions
  late_arrival_penalty: Money | null;
  complaint_deduction: Money | null;

  // Total
  total_commission: Money;
  payment_status: "PENDING" | "PAID" | "PARTIAL" | "DISPUTED";
  paid_at: string | null;
}
```

---

## Open Problems

1. **Guide preference vs optimization** — Customers may request specific guides by name, but the algorithm may suggest a better-skilled match. Balancing preference with optimization is delicate.

2. **Real-time availability** — Freelance guides may accept assignments from multiple agencies. A guide marked "available" may become unavailable between assignment and trip date.

3. **Briefing quality** — Guide briefings are only as good as the data provided. Incomplete customer preferences lead to mismatched expectations during tours.

4. **Commission fairness** — Freelance vs full-time guides have different cost structures. A single commission model doesn't work across employment types.

---

## Next Steps

- [ ] Build assignment scoring algorithm with configurable weights
- [ ] Implement multi-guide coordination with segment handoffs
- [ ] Create emergency substitution playbook with automated candidate search
- [ ] Design guide briefing auto-generation from trip data
- [ ] Implement tiered commission structure by employment type
