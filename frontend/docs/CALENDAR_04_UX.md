# Calendar & Scheduling — UX & Visualization

> Research document for calendar UI patterns, timeline visualization, and scheduling UX.

---

## Key Questions

1. **What calendar view modes best serve agents and customers?**
2. **How do we visualize multi-timezone travel on a calendar?**
3. **What's the drag-and-drop interaction model for rescheduling?**
4. **How do we display scheduling conflicts visually?**
5. **What's the mobile calendar experience for agents in the field?**

---

## Research Areas

### Calendar View Modes

```typescript
type CalendarViewMode =
  | 'day'                    // Single day, hourly slots
  | 'week'                   // 7-day view with time grid
  | 'month'                  // Monthly overview with dots/badges
  | 'timeline'               // Horizontal trip timeline (Gantt-like)
  | 'agenda'                 // List of upcoming events
  | 'schedule'               // Available slots for booking
  | 'map'                    // Events plotted on map by location
  | 'trip_focus';            // All events for a specific trip

// View modes by role:
// Agent workbench:
//   Primary: Timeline view (trip stages + deadlines)
//   Secondary: Week view (meetings + tasks)
//   Tertiary: Day view (today's schedule)
//
// Team lead:
//   Primary: Week view (team schedule overview)
//   Secondary: Timeline view (trip pipeline)
//
// Customer portal:
//   Primary: Trip timeline (travel itinerary visual)
//   Secondary: Agenda view (upcoming events list)
//   Tertiary: Month view (plan around trip dates)

// Calendar layout considerations:
// - Trip events color-coded by trip
// - Deadlines shown as flags/pins
// - Travel days highlighted with flight/hotel icons
// - Conflict indicators (red outlines, warning badges)
// - Current timezone always visible
// - Today marker with scroll-to-current-time
```

### Multi-Timezone Visualization

```typescript
interface TimezoneDisplay {
  primaryTimezone: string;           // Agent's timezone
  tripTimezones: string[];           // Timezones in current trip
  displayMode: TimezoneDisplayMode;
}

type TimezoneDisplayMode =
  | 'local_only'                     // Show event time in event's timezone
  | 'dual'                           // Show local + agent timezone
  | 'timeline_strip'                 // Time ruler with multiple timezone marks
  | 'world_clock'                    // Clock widgets for each timezone
  | 'comparison'                     // Side-by-side timezone comparison;

// UX for timezone display:
// Dual mode: "14:00 SGT | 11:30 IST" shown next to each event
// Timeline strip: Hour ruler showing IST, SGT, WITA simultaneously
// Color coding: Each timezone gets a subtle color tint
// Hover: Full timezone conversion shown on event hover
// Trip header: "Your trip spans 3 timezones: IST (+5:30), SGT (+8:00), WITA (+8:00)"

// Timezone UX principles:
// 1. Never assume timezone — always show explicitly
// 2. Use city names, not abbreviations (SGT, not "UTC+8")
// 3. Show day boundary when events cross midnight
// 4. Flight events show both departure AND arrival timezone
// 5. DST transitions flagged in advance
```

### Drag-and-Drop Rescheduling

```typescript
interface ReschedulingInteraction {
  eventId: string;
  originalTime: Date;
  newTime: Date;
  constraints: ReschedulingConstraint[];
  sideEffects: ReschedulingSideEffect[];
}

interface ReschedulingConstraint {
  type: 'fixed_time'                 // Can't reschedule (flight departure)
       | 'range'                     // Must be within time range
       | 'dependency'                // Must be before/after another event
       | 'minimum_gap';              // Minimum time between events
  message: string;
}

interface ReschedulingSideEffect {
  affectedEventId: string;
  affectedEventTitle: string;
  proposedNewTime: Date;
  requiresConfirmation: boolean;
}

// Drag-and-drop rules:
// Free events (meetings, reminders) → Can be dragged freely
// Constrained events (hotel check-in) → Can only move within check-in window
// Fixed events (flight departure) → Can't be dragged, but can be "linked" to new flight
// Dependent events (transfer after flight) → Moves with parent, or flagged as conflict

// Side effect handling:
// Drag "Hotel A check-in" from Day 2 to Day 3
// → System checks: "Hotel A check-out" should also move
// → Shows side effect: "This will also move Hotel A check-out to Day 4. OK?"
// → If confirmed, both events move
// → If rejected, only check-in moves (flagged as potential issue)

// Visual feedback during drag:
// Green zone: Valid drop targets
// Yellow zone: Possible but with warnings
// Red zone: Invalid (conflict or constraint violation)
// Ghost events: Show where dependent events will move
```

### Mobile Calendar UX

```typescript
interface MobileCalendarConfig {
  defaultView: 'agenda' | 'day' | 'timeline';
  quickActions: MobileQuickAction[];
  offlineSupport: boolean;
  pushNotifications: boolean;
  widgetSupport: boolean;
}

type MobileQuickAction =
  | 'quick_meeting'                   // One-tap schedule meeting
  | 'check_in_call'                   // Mark "called customer" for trip event
  | 'reschedule'                      // Propose new time
  | 'navigate'                        // Open maps to event location
  | 'call_customer'                   // Direct call to customer
  | 'view_trip';                      // Jump to trip details

// Mobile calendar considerations:
// 1. Agenda view is primary (most scannable on small screens)
// 2. Swipe to navigate between days/weeks
// 3. Long-press on event for quick actions
// 4. Haptic feedback for event creation
// 5. Today's events as lock screen widget
// 6. Offline mode shows cached calendar
// 7. Location-based alerts (arrive at airport → show transfer details)
```

---

## Open Problems

1. **Information density** — Calendar needs to show trip name, event type, time, timezone, and location in a small space. Design for scannability without clutter.

2. **Rescheduling cascade** — Changing a flight affects hotel, transfer, and activities. Need clear cascade visualization before confirming changes.

3. **Calendar accessibility** — Color-coded events don't work for colorblind users. Need patterns/icons in addition to colors.

4. **Print calendar** — Some customers want a printed itinerary calendar. Need print-optimized layout with all details.

5. **Calendar sharing** — Sharing trip calendar with a group (family trip). Each member sees their relevant events plus shared events.

---

## Next Steps

- [ ] Design calendar view modes for agent workbench and customer portal
- [ ] Build multi-timezone visualization component
- [ ] Create drag-and-drop rescheduling with cascade preview
- [ ] Design mobile calendar experience with quick actions
- [ ] Study calendar UX patterns (Google Calendar, Fantastical, Notion Calendar)
