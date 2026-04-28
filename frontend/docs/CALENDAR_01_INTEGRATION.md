# Calendar & Scheduling — Integration & Architecture

> Research document for calendar integration, travel timeline sync, and scheduling infrastructure.

---

## Key Questions

1. **What calendar systems need to integrate with the platform?**
2. **How do we sync travel dates with agent and customer calendars?**
3. **What's the calendar data model for multi-timezone travel?**
4. **How do we handle calendar conflicts and availability?**
5. **What's the architecture for real-time calendar updates?**

---

## Research Areas

### Calendar Data Model

```typescript
interface TravelCalendar {
  calendarId: string;
  ownerId: string;
  ownerType: 'agent' | 'customer' | 'team';
  events: CalendarEvent[];
  subscriptions: CalendarSubscription[];
  timezone: string;
}

interface CalendarEvent {
  eventId: string;
  title: string;
  description?: string;
  eventType: CalendarEventType;
  startDateTime: DateTimeWithZone;
  endDateTime: DateTimeWithZone;
  isAllDay: boolean;
  recurrence?: RecurrenceRule;
  location?: EventLocation;
  reminders: EventReminder[];
  linkedTripId?: string;
  linkedTaskId?: string;
  attendees: EventAttendee[];
  status: EventStatus;
  source: EventSource;
}

type CalendarEventType =
  | 'travel_departure'                // Flight/train departure
  | 'travel_arrival'                  // Arrival at destination
  | 'hotel_check_in'                  // Hotel check-in
  | 'hotel_check_out'                 // Hotel check-out
  | 'activity'                        // Tour, excursion, meeting
  | 'transfer'                        // Airport transfer, car pickup
  | 'customer_meeting'                // Agent-customer meeting
  | 'internal_meeting'                // Team meeting, standup
  | 'supplier_deadline'               // Booking deadline, payment due
  | 'travel_document_deadline'        // Visa application deadline
  | 'payment_due'                     // Payment deadline
  | 'reminder'                        // Custom reminder
  | 'blackout'                        // Holiday, maintenance window
  | 'on_call';                        // Agent on-call shift

interface DateTimeWithZone {
  utc: string;                       // ISO 8601 UTC timestamp
  local: string;                     // Local time at the event location
  timezone: string;                  // IANA timezone (e.g., "Asia/Kolkata")
  offset: string;                    // UTC offset (e.g., "+05:30")
}

// Multi-timezone handling:
// Trip: Delhi → Singapore → Bali → Delhi
// Delhi: +05:30 IST
// Singapore: +08:00 SGT
// Bali: +08:00 WITA
// Each calendar event stores timezone at the event location
// Agent calendar shows events in agent's timezone
// Customer calendar shows events in event's local timezone
```

### Calendar Integration

```typescript
interface CalendarSubscription {
  subscriptionId: string;
  provider: CalendarProvider;
  externalCalendarId: string;
  syncDirection: 'read' | 'write' | 'bidirectional';
  syncInterval: number;              // Minutes
  lastSyncAt: Date;
  status: 'active' | 'error' | 'paused';
}

type CalendarProvider =
  | 'google_calendar'
  | 'outlook_office365'
  | 'apple_calendar'
  | 'ical'
  | 'custom';

// Integration patterns:
// Google Calendar:
//   - OAuth2 for authorization
//   - Calendar API for CRUD operations
//   - Push notifications for real-time sync (webhook)
//   - Travel events created as Google Calendar events
//
// Outlook/Office 365:
//   - Microsoft Graph API
//   - OAuth2 + Azure AD
//   - Webhook subscriptions for change notifications
//
// Apple Calendar:
//   - CalDAV protocol
//   - .ics file export for read-only sync
//
// iCal (universal):
//   - .ics feed URL for subscribe-only sync
//   - Standard format all calendar apps support

// Sync rules:
// 1. Travel events created in platform → Push to external calendars
// 2. External calendar changes → Detect conflicts, don't auto-modify travel events
// 3. Agent meetings in external calendar → Show as "busy" in platform scheduling
// 4. Customer meetings → Sync both directions
// 5. Conflict resolution: Platform is source of truth for travel events
```

### Availability Management

```typescript
interface AgentAvailability {
  agentId: string;
  schedule: AvailabilitySchedule[];
  blockedTime: BlockedTime[];
  travelCapacity: TravelCapacity;
}

interface AvailabilitySchedule {
  dayOfWeek: number;
  startTime: string;                 // "09:00"
  endTime: string;                   // "18:00"
  timezone: string;
  isAvailable: boolean;
}

interface BlockedTime {
  blockId: string;
  startDateTime: Date;
  endDateTime: Date;
  reason: string;
  type: 'meeting' | 'personal' | 'travel' | 'training' | 'leave';
  source: 'platform' | 'external_calendar';
}

interface TravelCapacity {
  maxConcurrentTrips: number;
  currentTrips: number;
  upcomingDepartures: number;
  onSiteDates: DateRange[];
}

// Availability-aware scheduling:
// When scheduling a customer meeting:
// 1. Check agent's regular schedule
// 2. Check external calendar conflicts
// 3. Check current trip load
// 4. Check if agent is traveling (on-site with customer)
// 5. Suggest available slots
// 6. Customer picks a slot → Auto-create calendar event
```

---

## Open Problems

1. **Timezone fatigue** — Agents managing trips across 5+ timezones can get confused. Need clear timezone indicators and automatic conversion in the UI.

2. **Calendar sync reliability** — External calendar sync can fail silently. Need sync health monitoring and alerting.

3. **Recurring event complexity** — A weekly customer check-in across a trip that spans timezone changes. How does the recurring event adjust?

4. **Privacy boundaries** — Agents' personal calendar events should not be visible to the platform. Need selective sync (only business hours / meeting types).

5. **Offline access** — Agents need calendar access when offline (at airport, in transit). Need offline-capable calendar with sync-on-reconnect.

---

## Next Steps

- [ ] Design calendar data model with multi-timezone support
- [ ] Evaluate calendar integration APIs (Google Calendar, Outlook, CalDAV)
- [ ] Build availability management for agent scheduling
- [ ] Design .ics feed generation for customer trip calendars
- [ ] Study calendar UX patterns (Google Calendar, Calendly, Doodle)
