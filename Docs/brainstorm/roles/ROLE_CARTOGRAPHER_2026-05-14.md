# Brainstorm Role: Cartographer
**Date:** 2026-05-14  
**Topic:** Workbench / Trip Workspace — navigation maps and grouping patterns  
**Agent:** Two independent Cartographer agents ran. Composite of both documented here.

---

## The Metaphors

### Dispatch Board (Cartographer #2)

**A dispatch board.** Shipping terminals, freight operations. Every active thing is on the board. Each row tells you: where it is in the journey (stage), and what it needs from you right now (attention). You don't click in to find out what's happening — you can read it from the board.

The Trips page IS the dispatch board. The sidebar just gets you there.

### Airport Operations Center (Cartographer #1)

An airport has three zones: **Gates** (active departures, time-pressured), **Ground Control** (movement in progress), **Tower** (long-range view). Every trip lives in exactly one zone. The operator walks in and knows where to look.

---

## Navigation Map — Three Altitudes

```
ALTITUDE 1: SIDEBAR (orientation layer — always visible)
─────────────────────────────────────────────────────────
  [ + New Inquiry ]   ← CTA button. An ACTION, not a place. No nav slot.

  LIVE PIPELINE
    Trips          (●3)   ← dispatch board. 3 trips need attention.
    Lead Inbox     (●2)
    Quote Review   (●1)

  RECORDS
    Documents
    Bookings
    Payments

  INTELLIGENCE
    Insights
    Audit

  Settings


ALTITUDE 2: DISPATCH BOARD (Trips page — the scan surface)
─────────────────────────────────────────────────────────
  [STAGE BADGE]  [●DOT]  Trip Name         Dates       Next Action
  BOOKING        ●red    Müller Safari     Jun 3-18    Booking failed — act now
  REVIEW         ●amber  Chen Honeymoon    Jul 12-19   Awaiting review (2d)
  PROCESSING     ●blue   Park Family       Aug 5-20    AI run in progress
  BOOKING        ●green  Torres Anniversary May 28     Executing fine
  CONFIRMED      ●green  Walsh Business    May 30      Monitoring

  Two independent channels:
    Stage badge = where in the lifecycle (INTAKE→PROCESSING→REVIEW→BOOKING→CONFIRMED)
    Attention dot = what it needs right now (●red=now, ●amber=soon, ●blue=in progress, ●green=fine)

  A BOOKING-stage trip can be ●green (fine) or ●red (failed). These are DIFFERENT things.
  Default sort: ●red first.


ALTITUDE 3: TRIP WORKSPACE (individual trip — the record)
─────────────────────────────────────────────────────────
  Click any trip row → land at the right tab for the trip's stage.

  Smart entry (defaultTabForStage):
    INTAKE      → Intake tab
    REVIEW      → Output tab (AI results waiting)
    BOOKING     → Ops tab (booking execution)
    CONFIRMED   → Timeline tab

  Breadcrumb: "Trips > [Trip Name]"  (never "Workbench > [Trip Name]")
```

---

## The Creation Funnel

```
  [ + New Inquiry ] → /workbench?draft=new&tab=intake

  Three tabs only: [1. Intake] → [2. Processing] → [3. Done]

  Done state: "Trip created — View Trip →" links to /trips/{tripId}/ops (proposal stage)
              or /trips/{tripId}/intake (draft stage)

  Workbench ends here. Trip Workspace owns everything after.
```

The URL can stay `/workbench` — no route change needed in the immediate term. What changes is what it renders and what it leads to.

---

## The Creation / Durable Record Split

"New Inquiry" is a **verb** (do this now). Trip Workspace is a **noun** (this thing exists and lives here).

Structurally: the verb lives in a floating action or top-of-sidebar shortcut — always one click, never buried in a section. The nouns live in the Pipeline/Trips section. This prevents operators from hunting through "Command" menus to start work, and prevents confusion about whether Workbench is where trips live.

After AI processing, the trip is "born" into the Pipeline. The operator's relationship with it changes from *creating* to *stewarding*.

---

## Three Strongest Navigation Insights

**1. Stage and attention demand are orthogonal — give them separate visual channels.**

The current status color mixes two questions: "where is this trip?" and "what does it need from me?" Splitting them into a stage badge + attention dot lets operators scan the board and answer both questions without opening anything.

**2. Counts before names.**

Operators open the app to answer "what needs me today" before they think about which client. Show pipeline counts in the sidebar before the trip list. `Trips (●3)` means "3 need your attention" before you ever read a name.

**3. Creation is a mode, not a location.**

Workbench/New Inquiry should feel like opening a camera (transient, purposeful, closes when done) — not navigating to a room. Modal or sheet, not a nav item. This keeps the nav free of "place confusion" — the sidebar only contains things that persist.

---

**The thing most people miss about this:** The navigation problem is actually an information architecture problem about what changes and what doesn't. The sidebar items are "things that persist" (Lead Inbox always exists, Documents always exist). But a trip is "something that moves" — it changes stage, it changes attention state. Persistent things get sidebar slots. Moving things get a dispatch board with live state per row. The moment you put "Workbench" in the sidebar, you're treating a moving thing as if it persists — and operators start looking for work there that isn't there.
