# MICE Requirements — Meetings, Incentives, Conferences & Events

> Research document for understanding the MICE market, requirements, and platform needs.

---

## Key Questions

1. **What's the MICE market size in India, and what growth segments should we target?**
2. **How do MICE bookings differ from leisure/corporate bookings in workflow complexity?**
3. **What's the typical RFP-to-booking cycle time, and where do delays accumulate?**
4. **What are the unique payment and billing patterns for MICE (deposits, milestone payments)?**
5. **How do we handle group room blocks, event spaces, and F&B packages as bookable inventory?**
6. **What compliance and liability considerations are specific to MICE?**

---

## Research Areas

### MICE Segment Analysis

**Meetings:** Half-day to multi-day business meetings, typically at hotels or business centers. High volume, moderate complexity.

**Incentives:** Reward trips for top-performing employees or channel partners. Experiential, high-touch, variable complexity.

**Conferences/Conventions:** Large-scale events with hundreds of attendees, multiple sessions, and complex logistics.

**Events/Exhibitions:** Trade shows, product launches, exhibitions requiring specialized venues and setup.

```typescript
interface MICEInquiry {
  inquiryId: string;
  type: MICEType;
  client: MICEClient;
  estimatedAttendees: AttendeeRange;
  dates: DatePreference;
  location: LocationPreference;
  budget: BudgetRange;
  requirements: MICERequirement[];
  status: InquiryStatus;
}

type MICEType =
  | 'meeting'           // Board meeting, team offsite, strategy session
  | 'incentive_trip'    // Employee reward, channel partner incentive
  | 'conference'        // Industry conference, company annual meeting
  | 'exhibition'        // Trade show, product launch, exhibition
  | 'wedding'           // Destination wedding (overlaps with leisure)
  | 'team_building'     // Offsite team activities
  | 'training'          // Corporate training programs
  | 'product_launch';   // Launch events

interface MICEClient {
  companyId: string;
  industry: string;
  companySize: number;
  contactPerson: string;
  decisionMaker: string;
  budgetAuthority: string;
  pastEvents: number;
}

type AttendeeRange =
  | { min: 10; max: 30 }      // Small meeting
  | { min: 30; max: 100 }     // Medium event
  | { min: 100; max: 500 }    // Large conference
  | { min: 500; max: 2000 }   // Major convention
  | { min: 2000; max: null }; // Mega event
```

### RFP Workflow

**Questions:**
- What's the standard RFP format in the MICE industry?
- How many venues typically bid on an RFP?
- What comparison dimensions matter most to planners?

**Data model sketch:**

```typescript
interface MICE_RFP {
  rfpId: string;
  inquiryId: string;
  title: string;
  description: string;
  requirements: RFPSpecification;
  submissions: RFPSubmission[];
  evaluationCriteria: EvaluationCriteria[];
  status: RFPStatus;
  deadline: Date;
}

interface RFPSpecification {
  eventDates: DateRange;
  setupDates: DateRange;
  teardownDates: DateRange;
  attendees: number;
  roomNights: number;
  meetingRooms: MeetingRoomReq[];
  fAndB: FAndBRequirement;
  avEquipment: AVEquipmentReq[];
  accommodation: AccommodationReq;
  transport: TransportReq;
  specialRequirements: string[];
}

interface EvaluationCriteria {
  criterion: string;
  weight: number;
  scoringGuide: string;
}
```

### Budget & Pricing Structure

**MICE pricing is fundamentally different from leisure:**

| Cost Category | Pricing Model | Variables |
|--------------|---------------|-----------|
| Venue hire | Per-event or per-day | Day/half-day, capacity, setup |
| Accommodation | Group rate per night | Room type, block size, nights |
| F&B | Per-person per-meal | Menu tier, dietary needs, service style |
| AV/tech | Per-event package | Equipment list, technicians, setup |
| Transport | Per-vehicle or per-person | Vehicle type, distance, timing |
| Activities | Per-person | Activity type, group size, duration |
| Decor/design | Per-event | Theme, complexity, materials |
| Printing/signage | Per-event | Quantity, materials, complexity |
| Staffing | Per-person per-day | Role, duration, skill level |

**Open questions:**
- How do we model the many-to-many relationships between events and cost items?
- What's the standard markup/commission model for MICE?
- How do we handle client budget ceilings with supplier minimums?

---

## Open Problems

1. **Inventory modeling** — MICE inventory (ballrooms, meeting rooms, event spaces) has fundamentally different availability patterns than hotel rooms. Need a separate inventory model.

2. **Multi-venue events** — A conference may use 3 hotels + a convention center + offsite dinner venue. How to model and book this as a coherent package?

3. **Provisional bookings** — MICE planners often hold space tentatively for weeks while decisions are made. How to manage holds without blocking confirmed bookings?

4. **Bespoke pricing** — Every MICE event is different, making standard rate cards insufficient. Need a quote builder that accommodates customization.

5. **Attendee management** — For large events, individual attendee registration, room assignment, dietary preferences, and travel arrangements become a separate sub-system.

---

## Next Steps

- [ ] Research India MICE market size and growth projections
- [ ] Study standard RFP formats used by event management companies
- [ ] Map pricing models across venue types (hotels, convention centers, standalone)
- [ ] Investigate MICE-specific booking platforms (Cvent, EventsAir) for integration patterns
- [ ] Design MICE inventory model for venues and event spaces
