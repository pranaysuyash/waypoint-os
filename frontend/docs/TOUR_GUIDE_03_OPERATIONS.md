# Tour Guide & Escort Management — Day-of-Tour Operations

> Research document for real-time guide operations, customer check-in, incident management, tour modifications, and post-tour feedback.

---

## Key Questions

1. **How do we support guides during live tours?**
2. **What check-in and tracking systems ensure traveler safety?**
3. **How do we handle incidents and emergencies during tours?**
4. **What post-tour processes capture feedback and close the loop?**

---

## Research Areas

### Real-Time Tour Operations

```typescript
interface LiveTourSession {
  id: string;
  trip_id: string;
  guide_id: string;
  booking_id: string;

  status: "PRE_START" | "IN_PROGRESS" | "PAUSED" | "COMPLETED" | "EMERGENCY";
  current_day: number;
  current_location: GeoLocation | null;

  // Tracking
  guide_location: GeoLocation | null;
  last_check_in: string | null;
  check_in_interval_minutes: number;

  // Communication
  support_channel_id: string;          // WhatsApp group with ops team
  emergency_channel_active: boolean;

  // Timeline
  started_at: string | null;
  expected_end: string | null;
  actual_end: string | null;
}

interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy_meters: number;
  timestamp: string;
  battery_percentage: number | null;
}

// ── Real-time ops dashboard ──
// ┌─────────────────────────────────────────┐
// │  Live Tours Dashboard                     │
// │                                           │
// │  Active: 12  |  On-time: 9  |  Issues: 3 │
// │                                           │
// │  ─── Tour ──── ── Guide ── ── Status ──  │
// │  TP-101 Jaipur  Ravi     🟢 On Track     │
// │  TP-205 Kochi   Priya    🟢 On Track     │
// │  TP-312 Agra    Amit     🟡 15min late   │
// │  TP-418 Delhi   Sita     🔴 Incident*    │
// │  TP-520 Goa     Raj      🟢 On Track     │
// │                                           │
// │  * TP-418: Customer medical emergency     │
// │    → Ambulance dispatched                 │
// │    → Backup guide en route                │
// │    → Ops team notified                    │
// └───────────────────────────────────────────┘
```

### Customer Check-In System

```typescript
interface CustomerCheckIn {
  id: string;
  tour_session_id: string;
  customer_id: string;

  // Check-in
  type: "MORNING_ASSEMBLY" | "ACTIVITY_START" | "HOTEL_CHECKOUT" | "TRANSPORT_BOARDING" | "ROLL_CALL";
  expected_time: string;
  actual_time: string | null;
  status: "PENDING" | "CHECKED_IN" | "LATE" | "MISSING" | "EXCUSED";

  // Location (for assembly points)
  location: GeoLocation | null;
  qr_code_verified: boolean;

  notes: string;
}

// ── Daily tour flow ──
// ┌─────────────────────────────────────────┐
// │  Day 2 — Jaipur City Tour                │
// │                                           │
// │  08:00  Morning assembly (lobby)          │
// │         ├── QR scan check-in              │
// │         ├── Guide headcount               │
// │         └── Photo for WhatsApp group      │
// │  08:30  Depart for Amber Fort             │
// │  10:00  Amber Fort tour start             │
// │  12:00  Lunch at restaurant               │
// │  14:00  City Palace tour                  │
// │  16:00  Jantar Mantar                     │
// │  17:30  Return to hotel                   │
// │  18:00  Evening roll call                 │
// │  18:30  Guide daily report                │
// │                                           │
// │  Auto-alerts:                             │
// │  - Customer not checked in by 08:15       │
// │  - Group split > 200m apart               │
// │  - Guide stationary > 30 min (non-stop)  │
// └───────────────────────────────────────────┘
```

### Incident Management

```typescript
interface TourIncident {
  id: string;
  tour_session_id: string;
  guide_id: string;

  type: TourIncidentType;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "REPORTED" | "IN_PROGRESS" | "RESOLVED" | "ESCALATED" | "CLOSED";

  description: string;
  affected_customers: string[];
  location: GeoLocation | null;

  // Response
  actions_taken: string[];
  escalation_level: number;
  ops_handler: string | null;
  emergency_services_called: boolean;

  // Timeline
  reported_at: string;
  first_response_at: string | null;
  resolved_at: string | null;
  follow_up_required: boolean;
  follow_up_date: string | null;

  // Documentation
  photos: string[];
  statements: IncidentStatement[];
}

type TourIncidentType =
  | "MEDICAL_EMERGENCY" | "ACCIDENT" | "THEFT"
  | "LOST_TRAVELER" | "VENDOR_NO_SHOW" | "TRANSPORT_BREAKDOWN"
  | "WEATHER_DISRUPTION" | "POLITICAL_UNREST" | "NATURAL_DISASTER"
  | "FOOD_POISONING" | "ALLERGIC_REACTION" | "DISPUTE"
  | "OVERCHARGING" | "SAFETY_CONCERN" | "COMPLAINT";

// ── Incident severity response matrix ──
// ┌─────────────────────────────────────────────────────┐
// │  Severity | Response Time | Who Handles               │
// │  ─────────────────────────────────────────────────── │
// │  LOW      | < 2 hours     | Guide resolves            │
// │           |               | Log incident              │
// │  MEDIUM   | < 30 minutes  | Guide + ops team          │
// │           |               | Customer notified         │
// │  HIGH     | < 10 minutes  | Ops team + supervisor     │
// │           |               | Agent notified            │
// │           |               | Alternative arranged      │
// │  CRITICAL | Immediate     | Emergency protocol        │
// │           |               | Emergency services        │
// │           |               | Agency head notified      │
// │           |               | Insurance activated       │
// └─────────────────────────────────────────────────────┘
```

### Tour Modification Handling

```typescript
interface TourModification {
  id: string;
  tour_session_id: string;
  guide_id: string;

  type: "ROUTE_CHANGE" | "TIMING_ADJUSTMENT" | "ACTIVITY_SUBSTITUTION"
    | "RESTAURANT_CHANGE" | "TRANSPORT_CHANGE" | "HOTEL_CHANGE";
  reason: "WEATHER" | "TRAFFIC" | "CUSTOMER_REQUEST" | "VENDOR_ISSUE"
    | "SAFETY" | "TIME_CONSTRAINT";

  original_plan: string;
  modified_plan: string;
  cost_impact: Money;
  time_impact_minutes: number;
  customer_approved: boolean;

  created_at: string;
}

// ── Common modifications ──
// ┌─────────────────────────────────────────┐
// │  Weather: Indoor alternative for outdoor │
// │  Traffic: Route change, skip 1 activity  │
// │  Fatigue: Remove 1 stop, add rest break  │
// │  Interest: Extend popular stop, skip next│
// │  Closure: Backup destination (pre-planned)│
// └───────────────────────────────────────────┘
```

### Post-Tour Debrief

```typescript
interface PostTourDebrief {
  id: string;
  tour_session_id: string;
  guide_id: string;

  // Completion
  all_customers_returned: boolean;
  on_time_completion: boolean;

  // Guide report
  overall_assessment: "EXCELLENT" | "GOOD" | "SATISFACTORY" | "PROBLEMATIC";
  highlights: string[];
  issues: string[];
  customer_feedback_summary: string;
  vendor_feedback: VendorFeedback[];
  improvement_suggestions: string[];

  // Photos & content
  tour_photos: string[];
  social_media_content: string[];

  // Customer feedback triggers
  feedback_requests_sent: number;
  feedback_responses: number;

  submitted_at: string;
}
```

---

## Open Problems

1. **Location tracking privacy** — Continuous GPS tracking of guides raises privacy concerns. Need clear consent, off-duty tracking disable, and data retention limits.

2. **Internet connectivity** — Remote tourist destinations (Ladakh, rural Rajasthan) may have poor connectivity. Offline-capable check-in and incident reporting is essential.

3. **Incident escalation fatigue** — Not every late customer needs ops team involvement. Smart escalation rules must distinguish between genuine emergencies and minor delays.

4. **Guide autonomy vs standardization** — Over-scripting tours removes the personal touch that makes guides valuable. Need guard rails, not scripts.

---

## Next Steps

- [ ] Build real-time tour tracking with privacy-aware location sharing
- [ ] Implement QR-based customer check-in system
- [ ] Create incident reporting and escalation workflow
- [ ] Design offline-capable tour operations (local storage + sync)
- [ ] Build post-tour auto-debrief questionnaire for guides
