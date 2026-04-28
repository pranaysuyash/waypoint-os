# Calendar & Scheduling — Master Index

> Exploration of calendar integration, customer scheduling, resource management, and calendar UX.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Integration & Architecture](CALENDAR_01_INTEGRATION.md) | Calendar data model, multi-timezone, external calendar sync, availability |
| 02 | [Customer Scheduling](CALENDAR_02_CUSTOMER_SCHEDULING.md) | Meeting types, travel timeline, scheduling automation, meeting templates |
| 03 | [Resource Scheduling](CALENDAR_03_RESOURCE.md) | Resource booking, conflict detection, capacity planning, supplier scheduling |
| 04 | [UX & Visualization](CALENDAR_04_UX.md) | Calendar views, multi-timezone display, drag-and-drop, mobile UX |

---

## Key Themes

- **Timezone-first design** — Every calendar event stores its timezone. The UI shows local time alongside the viewer's timezone, never assuming one.
- **Travel timeline as calendar** — The trip itinerary IS a calendar. Customers subscribe via .ics feed and see travel events alongside their regular schedule.
- **Smart scheduling** — Agent-customer meetings are auto-suggested based on availability, trip stage, and scheduling rules. No manual back-and-forth.
- **Resource awareness** — Shared resources (meeting rooms, vehicles, specialist time) are scheduled with conflict detection and buffer times.
- **Mobile-native** — Agents use the calendar heavily on mobile during field work. Quick actions and offline access are essential.

## Integration Points

- **Trip Builder** — Itinerary dates flow into the calendar as travel events
- **Task Management** — Task due dates appear on the calendar; meetings create tasks
- **Notification System** — Calendar reminders use the notification pipeline
- **Customer Portal** — Customers access their trip calendar and schedule meetings
- **Collaboration** — Shared calendar events show participant availability
- **Mobile Experience** — Calendar is a primary mobile feature with offline support
