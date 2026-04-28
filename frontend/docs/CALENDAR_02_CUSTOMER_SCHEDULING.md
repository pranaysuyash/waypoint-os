# Calendar & Scheduling — Customer Scheduling

> Research document for customer meeting scheduling, appointment booking, and travel timeline.

---

## Key Questions

1. **How do customers book meetings with agents?**
2. **What scheduling workflows exist across the trip lifecycle?**
3. **How do we handle pre-trip, during-trip, and post-trip scheduling needs?**
4. **What's the customer-facing calendar experience?**
5. **How do automated scheduling reminders reduce no-shows?**

---

## Research Areas

### Customer Meeting Scheduling

```typescript
interface CustomerMeeting {
  meetingId: string;
  tripId: string;
  agentId: string;
  customerId: string;
  meetingType: MeetingType;
  scheduledAt: Date;
  duration: number;                  // Minutes
  channel: MeetingChannel;
  location?: MeetingLocation;
  agenda: string[];
  preparationNotes: string;
  status: MeetingStatus;
  reminders: MeetingReminder[];
  recording?: MeetingRecording;
  followUp?: MeetingFollowUp;
}

type MeetingType =
  | 'initial_consultation'           // First meeting with new customer
  | 'requirements_gathering'         // Understand travel needs
  | 'itinerary_presentation'         // Present proposed itinerary
  | 'itinerary_revision'             // Discuss changes to itinerary
  | 'pricing_discussion'             // Negotiate pricing
  | 'pre_departure_briefing'         // Final meeting before travel
  | 'during_trip_check_in'           // Check-in during travel
  | 'post_trip_feedback'             // Debrief after travel
  | 'issue_resolution'               // Handle problems during trip
  | 'upsell_opportunity'             // Suggest additional services
  | 'renewal_booking';               // Plan next trip

type MeetingChannel =
  | 'phone'
  | 'video_call'
  | 'in_person'
  | 'whatsapp_call'
  | 'whatsapp_chat';

// Scheduling flow:
// 1. Agent or customer requests meeting
// 2. System shows available slots based on agent availability
// 3. Customer selects a slot (or agent proposes times)
// 4. Calendar event created in both calendars
// 5. Reminder sequence: 24h, 2h, 30min before
// 6. Meeting happens
// 7. Agent logs meeting notes and action items
// 8. Follow-up tasks auto-created if needed
```

### Travel Timeline View

```typescript
interface TravelTimeline {
  tripId: string;
  customerCalendarUrl: string;       // .ics feed URL
  events: TravelTimelineEvent[];
  criticalDates: CriticalDate[];
}

interface TravelTimelineEvent {
  eventId: string;
  type: TravelEventType;
  title: string;
  date: DateTimeWithZone;
  duration?: string;
  location?: string;
  documents?: string[];              // Related documents to show
  notes?: string;
  isPast: boolean;
}

type TravelEventType =
  | 'flight_departure'
  | 'flight_arrival'
  | 'hotel_check_in'
  | 'hotel_check_out'
  | 'activity_start'
  | 'activity_end'
  | 'transfer_pickup'
  | 'transfer_dropoff'
  | 'restaurant_reservation'
  | 'visa_appointment'
  | 'insurance_start'
  | 'insurance_end'
  | 'tour_start'
  | 'free_time'
  | 'border_crossing';

interface CriticalDate {
  date: Date;
  label: string;
  type: 'document_deadline' | 'payment_due' | 'cancellation_deadline' | 'booking_deadline';
  actionRequired: string;
  isOverdue: boolean;
}

// Customer calendar features:
// 1. Subscribe to trip calendar (.ics feed)
// 2. Real-time updates when itinerary changes
// 3. Push notifications for upcoming events
// 4. Offline access to itinerary details
// 5. Integration with phone's native calendar
// 6. Weather forecast for event dates/locations
// 7. Local time display alongside home timezone
```

### Scheduling Automation

```typescript
interface SchedulingAutomation {
  rules: SchedulingRule[];
  templates: MeetingTemplate[];
}

interface SchedulingRule {
  ruleId: string;
  trigger: string;
  meetingType: MeetingType;
  timing: SchedulingTiming;
  channel: MeetingChannel;
  assignee: string;
  autoSchedule: boolean;
}

interface SchedulingTiming {
  relativeTo: string;                // Trip milestone or date
  offsetDays: number;
  preferredTime: string;             // "10:00"
  preferredDays: number[];           // 0-6, Sunday-Saturday
}

// Auto-scheduling rules:
// New trip created → Auto-schedule initial consultation within 2 business days
// Itinerary drafted → Auto-schedule presentation meeting within 1 day
// Trip confirmed → Auto-schedule pre-departure briefing 7 days before travel
// Day 1 of travel → Auto-schedule during-trip check-in call
// Trip completed → Auto-schedule feedback call within 3 days
// 30 days post-trip → Auto-suggest renewal booking meeting

interface MeetingTemplate {
  meetingType: MeetingType;
  defaultDuration: number;
  defaultChannel: MeetingChannel;
  agendaTemplate: string[];
  preparationChecklist: string[];
  followUpActions: string[];
}

// Meeting templates:
// Initial consultation (45 min, video call):
//   - Introductions and relationship building
//   - Travel preferences and past experiences
//   - Budget and timeline discussion
//   - Destination ideas and constraints
//   - Next steps and timeline
```

---

## Open Problems

1. **No-show management** — Customers miss scheduled calls. Need rescheduling workflows and no-show tracking for agent productivity.

2. **Timezone negotiation** — Agent in IST, customer in PST. Scheduling tools should show both timezones clearly and suggest overlap windows.

3. **Meeting quality** — A 30-minute call can be productive or wasteful. Need structured agendas and outcome tracking to measure meeting effectiveness.

4. **Spontaneous scheduling** — During-trip issues require immediate calls, not scheduled meetings. Need a separate "urgent call" flow bypassing normal scheduling.

5. **Customer self-scheduling** — Customers want to book meetings without going back and forth. Need a Calendly-style self-booking experience.

---

## Next Steps

- [ ] Design customer meeting scheduling flow with self-booking
- [ ] Build travel timeline view for customer portal
- [ ] Create meeting templates for each meeting type
- [ ] Design .ics feed generation with real-time itinerary updates
- [ ] Study scheduling UX (Calendly, Doodle, Google Appointment Slots)
