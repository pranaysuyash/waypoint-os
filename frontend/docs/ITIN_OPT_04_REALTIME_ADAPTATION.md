# Travel Itinerary Optimization — Real-Time Adaptation

> Research document for real-time itinerary adjustment, disruption handling, dynamic re-routing, same-day booking integration, and post-disruption recovery.

---

## Key Questions

1. **How do we handle disruptions during an active trip?**
2. **How do we dynamically re-route when conditions change?**
3. **How do we find and book replacement activities in real-time?**
4. **How do we recover itineraries after disruptions?**

---

## Research Areas

### Real-Time Itinerary Engine

```typescript
interface RealtimeItineraryEngine {
  detectDisruption(trip: ActiveTrip, signals: DisruptionSignal[]): Disruption | null;
  generateAlternatives(disruption: Disruption): ItineraryAlternative[];
  applyAlternative(trip: ActiveTrip, alternative: ItineraryAlternative): UpdatedItinerary;
  notifyStakeholders(update: ItineraryUpdate): NotificationResult;
}

interface ActiveTrip {
  trip_id: string;
  booking_id: string;
  current_day: number;
  current_location: GeoLocation;
  itinerary: ItineraryDay[];
  travelers: ActiveTraveler[];
  assigned_agent: string;
  assigned_guide: string | null;
}

// ── Disruption detection sources ──
// ┌─────────────────────────────────────────────────────┐
// │  Signal Source         | Disruption Type              │
// │  ─────────────────────────────────────────────────── │
// │  Flight tracking API   | Delay, cancellation          │
// │  Weather API           | Storm, heavy rain, fog       │
// │  Hotel PMS             | Overbooking, maintenance     │
// │  Traffic API           | Road closures, congestion    │
// │  News feeds            | Strikes, political unrest    │
// │  Guide report          | Safety concern, vendor issue │
// │  Customer request      | Illness, preference change   │
// │  Government advisory   | Travel ban, curfew           │
// └─────────────────────────────────────────────────────┘
```

### Disruption Handling Workflow

```typescript
interface DisruptionHandler {
  assess(disruption: Disruption): DisruptionAssessment;
  respond(assessment: DisruptionAssessment): DisruptionResponse;
}

interface DisruptionAssessment {
  disruption: Disruption;
  impact: {
    affected_days: number[];
    affected_activities: string[];
    affected_bookings: string[];
    financial_impact: Money;
    traveler_impact: string;
    time_lost_hours: number;
  };
  severity: "MINOR" | "MODERATE" | "MAJOR" | "CRITICAL";
  requires_customer_decision: boolean;
  auto_resolvable: boolean;
}

interface DisruptionResponse {
  original_plan: ItineraryDay[];
  modified_plan: ItineraryDay[];
  changes: ItineraryChange[];
  cost_delta: Money;                    // additional cost (+/-)
  time_delta_hours: number;
  quality_impact: "IMPROVED" | "MAINTAINED" | "MINOR_DECREASE" | "SIGNIFICANT_DECREASE";
  customer_approval_required: boolean;
}

interface ItineraryChange {
  day: number;
  type: "ACTIVITY_REPLACED" | "TIMING_SHIFTED" | "ROUTE_CHANGED" | "REST_DAY_INSERTED" | "DAY_SWAPPED";
  original: string;
  replacement: string;
  reason: string;
}

// ── Disruption response flow ──
// ┌─────────────────────────────────────────────────────┐
// │  DISRUPTION: Flight DEL→SIN delayed 6 hours          │
// │                                                       │
// │  Assessment:                                          │
// │  - Day 1 itinerary: 3 activities affected            │
// │  - Financial impact: ₹0 (airline rebooked)           │
// │  - Time lost: 6 hours                                │
// │  - Severity: MODERATE                                │
// │                                                       │
// │  Auto-resolved changes:                               │
// │  1. ✅ Marina Bay Sands moved Day 1 PM → Day 2 AM   │
// │  2. ✅ Gardens by the Bay moved Day 1 → Day 2 PM    │
// │  3. ❌ Sentosa needs customer decision               │
// │                                                       │
// │  Options presented to customer (WhatsApp):            │
// │  A) Skip Sentosa, keep relaxed schedule              │
// │  B) Combine Sentosa + Gardens on Day 2 (busy day)    │
// │  C) Add Day 6, include everything (₹8,000 extra)    │
// │                                                       │
// │  Customer selected: B                                │
// │  Itinerary updated automatically                     │
// └─────────────────────────────────────────────────────┘
```

### Dynamic Re-Routing Engine

```typescript
interface DynamicRouter {
  reroute(current: ActiveTrip, disruption: Disruption): RerouteOption[];
  findNearbyAlternatives(location: GeoLocation, activity_type: string, budget: Money): NearbyAlternative[];
}

interface RerouteOption {
  description: string;
  new_route: RouteSegment[];
  cost_delta: Money;
  time_delta_minutes: number;
  quality_score: number;
  available_immediately: boolean;
}

interface NearbyAlternative {
  name: string;
  type: string;
  distance_km: number;
  travel_time_minutes: number;
  cost: Money;
  rating: number;
  open_now: boolean;
  booking_available: boolean;
  booking_url: string | null;
}

// ── Nearby alternative example ──
// ┌─────────────────────────────────────────────────────┐
// │  ACTIVITY CANCELLED: Singapore Zoo (closed for maint)│
// │  Location: Mandai, Singapore                          │
// │  Budget: ₹3,000 for 2 pax                           │
// │                                                       │
// │  Alternatives found:                                  │
// │  ┌──────────────────┬──────┬─────┬───────┬────────┐ │
// │  │ Alternative      │ Dist │Time │ Cost  │ Rating │ │
// │  ├──────────────────┼──────┼─────┼───────┼────────┤ │
// │  │ River Wonders    │ 0km  │ 0m  │ ₹2,000│ 4.5    │ │
// │  │ Night Safari     │ 0km  │ 0m  │ ₹2,500│ 4.7 ★ │ │
// │  │ Bird Paradise    │ 0km  │ 0m  │ ₹1,800│ 4.3    │ │
// │  │ Sungei Buloh     │ 12km │ 20m │ Free  │ 4.1    │ │
// │  │ Botanic Gardens  │ 15km │ 25m │ Free  │ 4.6    │ │
// │  └──────────────────┴──────┴─────┴───────┴────────┘ │
// │  ★ = Recommended (highest rating + available)        │
// └─────────────────────────────────────────────────────┘
```

### Same-Day Booking Integration

```typescript
interface SameDayBookingEngine {
  searchAvailability(query: SameDayQuery): SameDayAvailability[];
  instantBook(option: SameDayAvailability): BookingConfirmation;
}

interface SameDayQuery {
  destination: string;
  activity_type: string;
  date: string;
  pax: number;
  budget_max: Money;
  time_window: TimeWindow;
}

interface SameDayAvailability {
  vendor_id: string;
  activity: string;
  time_slots: TimeSlot[];
  price: Money;
  instant_confirmation: boolean;
  cancellation_policy: string;
}

interface TimeSlot {
  start: string;
  end: string;
  available: boolean;
  remaining_slots: number;
}

// ── Same-day booking partners ──
// ┌─────────────────────────────────────────┐
// │  Activity Type  | Integration            │
// │  ─────────────────────────────────────── │
// │  Attractions    | Klook, GetYourGuide    │
// │  Restaurants    | Zomato, EazyDiner      │
// │  Transport      | Grab, Gojek, Uber      │
// │  Activities     | Viator, TripAdvisor   │
// │  Spa/Wellness   | Fresha, Zenrez         │
// │  Events         | BookMyShow, Eventbrite │
// └───────────────────────────────────────────┘
```

### Post-Disruption Recovery

```typescript
interface PostDisruptionRecovery {
  recoverItinerary(trip: ActiveTrip, disruption_log: DisruptionLog[]): RecoveredItinerary;
  calculateCompensation(disruptions: DisruptionLog[]): CompensationOffer;
}

interface RecoveredItinerary {
  trip_id: string;
  original_plan: ItineraryDay[];
  recovered_plan: ItineraryDay[];
  unrecoverable_items: string[];
  additional_cost: Money;
  customer_satisfaction_prediction: number;
}

interface CompensationOffer {
  disruption_id: string;
  type: "FULL_REFUND" | "PARTIAL_REFUND" | "CREDIT" | "FREE_UPGRADE" | "VOUCHER" | "FUTURE_DISCOUNT";
  value: Money;
  reason: string;
  auto_applied: boolean;
}

// ── Recovery workflow ──
// ┌─────────────────────────────────────────┐
// │  Trip Recovery Checklist                   │
// │                                           │
// │  □ All disrupted activities rescheduled? │
// │  □ All vendor bookings reconfirmed?      │
// │  □ Transport rearranged?                 │
// │  □ Hotel dates adjusted?                 │
// │  □ Customer notified of changes?         │
// │  □ Guide briefed on new itinerary?       │
// │  □ Insurance claim filed (if applicable)?│
// │  □ Compensation offered?                 │
// │  □ Agent updated in workspace?           │
// │  □ Post-trip apology message queued?     │
// └───────────────────────────────────────────┘
```

---

## Open Problems

1. **Multi-disruption cascading** — A flight delay may cause a hotel booking loss, which causes an activity cancellation. Cascading disruption resolution is exponentially complex.

2. **Customer communication timing** — Notifying customers too early (before alternatives are ready) causes anxiety. Too late makes them feel uninformed. Need a "processing update" followed by "here's the fix" pattern.

3. **Vendor cooperation** — Same-day rebooking depends on vendor flexibility. Many vendors don't support instant rebooking or charge premium rates for same-day changes.

4. **Insurance claim automation** — Travel insurance claims for disruptions require documentation that's hard to collect automatically. Need integrated claim filing with pre-filled data.

---

## Next Steps

- [ ] Build real-time disruption detection from multiple signal sources
- [ ] Implement dynamic re-routing engine with nearby alternative search
- [ ] Create same-day booking integration with activity aggregators
- [ ] Design post-disruption recovery automation with compensation engine
- [ ] Build multi-disruption cascade resolution algorithm
