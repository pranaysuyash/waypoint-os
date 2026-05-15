# Brainstorm Role: Future Self — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-sentence thesis

Ops must stop being a collection of independent panels bolted together and become a single, opinionated execution dashboard whose job is to answer one question at every moment: *"What stands between this trip and a successful booking, and who needs to act right now?"*

---

## 2. What the current Ops page gets right

- **Complete data coverage.** Every operative concept is present: traveler identity, payment, documents with AI extraction, booking tasks, confirmations, and a timestamped event log. The team resisted the urge to ship half the surface and revisit; everything that needs to exist is already modeled.
- **Separation of customer-submitted vs. agent-entered data.** The `bookingDataSource` badge and the pending-submission review flow are genuinely good product decisions. By 2028, that provenance trail becomes central to dispute resolution and supplier-facing accountability.
- **AI extraction with conflict handling.** The document extraction + conflict resolution loop (`extractionConflicts`, overwrite confirmation) is the right design. Most tools just overwrite or silently skip. The explicit operator confirmation step builds the audit history that later becomes the legal protection layer.
- **Stage gate discipline.** Blocking Ops from non-booking stages forces the product to stay honest about what "booking ready" means. Agencies that used tools without stage gates consistently had booking data scattered in emails by 2027.
- **Flat booking data model.** `BookingTraveler` with `traveler_id`, `full_name`, `date_of_birth`, `passport_number` is correct as a keyed entity. The IDs (`adult_1`, `child_1`) turn out to be the stable join key across documents, tasks, and confirmations once the data model matures.

---

## 3. What it gets wrong

- **No opinionated ordering of operator attention.** Opening Ops in May 2026 presents: readiness tier summary, missing fields, signals, pending customer submission, booking details, collection link, documents, tasks, confirmations, timeline. There is no signal that distinguishes "you must act on this now" from "this is informational." An agent with four active trips and two customer submissions due today cannot triage from this layout.
- **Readiness tiers are diagnostic, not prescriptive.** Showing "Not ready — missing: passport_number, date_of_birth" is correct but passive. The operator already knows something is missing; they need the system to tell them whether to chase the customer, block the booking task, or accept partial data for a soft-booking flow.
- **Documents are orphaned from travelers.** The document list is a flat queue of files. There is no answer to "do I have a passport for every traveler?" until an operator manually counts. By 2027, every competitor had reorganized documents per-traveler because the mental model of agency ops is per-person, not per-file.
- **Payment has no temporal structure.** The payment tracking block captures agreed amount, paid amount, status, and refund status — all present-state fields. There is no concept of *when* money is due relative to supplier deadlines. The payment tracking field `payment_status: 'overdue'` is set manually. The system cannot proactively surface "final payment due in 4 days" because nothing in the data model knows the supplier's deadline.
- **Booking tasks are manually created.** `BookingExecutionPanel` is a task list, but the tasks are not derived from the accepted itinerary. A luxury villa itinerary with 8 components has the same blank task list as a single-leg flight. Operators re-enter the same task shapes on every trip. This was the single most-cited time sink in the 2027 user research.
- **Confirmations have no comparison baseline.** `ConfirmationPanel` stores per-booking confirmation records but has no reference point. By mid-2027 the product that won agency deals was the one that said "your hotel confirmation shows 2 nights but your itinerary says 3 — resolve before travel."
- **Timeline is passive.** `ExecutionTimelinePanel` is an event log. It records what happened. It does not surface deviations: a task that was "in_progress" for 11 days with no update, a confirmation that arrived for a booking nobody marked complete, a refund that was approved 30 days ago but never paid. Passive logs are for auditors; operators need active anomaly detection.
- **The panel renders everything all at once.** 1399 lines of a single React component that fetches booking data, collection links, pending submissions, documents, extractions, tasks, confirmations, and the timeline in parallel. This creates a page that takes 4–6 API calls on mount, mixes concerns, and will become unmaintainable by month 8 of active development. The lack of sub-tabs is a technical debt time bomb disguised as a design decision.

---

## 4. The top 5 operator decisions Ops must support

These are the decisions that happen on every trip, multiple times, under time pressure:

1. **"Is this trip ready to execute, and if not, what do I do next?"** — This is the primary question. The operator opens Ops and needs an answer in under 3 seconds without scrolling.

2. **"Has the customer given me everything I need, and have I verified it?"** — Document completeness per traveler, pending submissions awaiting review, and data conflicts from extraction all converge here. The decision is binary: proceed or chase.

3. **"What bookings do I need to make today, and in what order?"** — Booking tasks with supplier deadlines and payment cutoffs need to be sequenced. The decision is: act now, schedule for later, or block because a dependency is unmet.

4. **"Is the money situation clean?"** — Do I have confirmed receipt? Is the customer balance overdue? Is there a supplier final payment due before I can issue tickets? Payment and supplier deadlines are the same decision surface, not two separate data entry forms.

5. **"Has anything gone wrong since I last looked at this trip?"** — This is the "something changed" scan. A new customer document uploaded, a task marked failed, a confirmation with mismatched dates, an overdue balance. This should surface as a count and a list, not require reading the entire timeline.

---

## 5. Ideal page layout

This is the section order and content for an Ops surface that actually answers the top 5 operator decisions.

### Header row — always visible
**Trip title + stage badge + "X actions required" count**
The count is the sum of: pending customer submissions, documents pending review, tasks overdue or blocked, confirmations with detected discrepancies, and payment overdue flags. Tapping the count jumps to the first unresolved item.

### Section 1 — Next Action (replaces readiness as hero element)
A single card with one primary action and, beneath it, a ranked list of secondary items. The primary action is the system's best answer to "what should I do right now" based on the trip's state.

Examples:
- "Review customer submission — submitted 2h ago" (amber, if pending submission exists)
- "Generate collection link — no data collected yet" (neutral, if no booking data and no link)
- "Confirm hotel Santorini — supplier deadline in 3 days" (red, if deadline is near)
- "Collect passport for traveler child_1 — document missing" (red, if readiness tier blocked)

The readiness tiers collapse into this surface as contributors to the action priority ranking, not as a separate display block.

### Section 2 — Traveler Dossiers (replaces flat booking data + flat document list)
One card per traveler. Each card shows:
- Identity fields: name, DOB, passport number, source badge (agent / customer-verified)
- Document slots: passport slot (uploaded / pending / missing), visa slot (if applicable), insurance slot
- Extraction status per document: accepted, pending review, or conflict
- Quick actions: Edit, Request from customer

This layout answers "is this traveler complete?" in a glance. Documents stop being a separate flat list and become sub-items of the person they belong to. A 3-traveler trip at a glance shows 3 cards, each with colored status indicators.

### Section 3 — Payments & Supplier Deadlines (collapses current payment tracking + adds timeline)
Two sub-rows:

**Customer payment:** agreed amount, amount paid, balance due, status, next due date (new field), method, reference, proof. The balance-due field and next-due-date field together generate the "overdue" or "due in N days" status automatically rather than relying on manual status updates.

**Supplier payments (per booking):** For each booking task that has a supplier and a cost, show the supplier name, amount, deadline date, and payment status. This is a new data surface that does not exist in May 2026 but is the natural extension of `BookingExecutionPanel` once tasks are generated from the itinerary.

### Section 4 — Booking Tasks (generated from accepted itinerary)
The task list starts populated. When a trip accepts a quote or moves to booking stage, the system generates a task set from the itinerary components: hotels × nights, flights, transfers, activities. Each task has:
- Component name (from itinerary)
- Booking status (7-state machine: unstarted / queued / in_progress / awaiting_confirmation / confirmed / failed / cancelled)
- Supplier deadline (date field — this feeds Section 3)
- Assigned to (agent name or unassigned)
- Link to the confirmation record (once received)

The operator edits tasks, marks them complete, and links confirmations. But they never start from a blank list.

### Section 5 — Confirmations (diffed against itinerary)
Per-booking confirmation cards, each showing:
- What was booked (from the itinerary / task)
- What the confirmation says (structured fields extracted from the confirmation document)
- Discrepancy flags: dates, names, nights, amounts that differ from the itinerary component
- Status: clean / discrepancy detected / under review / resolved

This transforms ConfirmationPanel from a record-keeping tool into a quality-control surface.

### Section 6 — Active Anomalies (replaces passive timeline as primary operator surface)
A list of system-detected issues ordered by urgency:
- Tasks overdue (in_progress > N days with no update)
- Confirmations with discrepancies not yet resolved
- Payment overdue (balance due date passed)
- Documents uploaded by customer not yet reviewed (beyond 24h)
- Traveler data conflicts from extraction not yet resolved

Each anomaly links to the relevant item in sections above. This is the first thing a returning operator checks.

### Section 7 — Audit Timeline (formerly ExecutionTimelinePanel, now secondary)
Full chronological event log, collapsed by default. Accessible but not the primary surface. Contains every system and operator action for compliance and dispute reference. The log is the spine; the anomaly surface in Section 6 is the derived signal layer on top of it.

### Persistent bottom bar — Customer Data Collection
The collection link generator and pending submission review stay persistent but compact. A pill shows link status (active / none) and pending submission count. Expanding shows the current functionality. This removes it from the main flow without removing the capability.

---

## 6. What to build next

These are concrete, sequenced slices ordered by operator impact per build day.

### Slice A — Next Action header (1–2 days)
Add a `NextActionCard` component at the top of Ops. Logic: evaluate pending submission → pending documents → readiness blocking fields → nearst task deadline. Display the highest-priority item as a primary CTA with a short list of secondary items beneath. No new backend needed — derives from data already fetched.

This is the highest-leverage single change. Every operator who opens Ops immediately understands what to do. Measurable outcome: time-to-first-action drops from "scroll and orient" to "read one card."

### Slice B — Traveler-organized document view (2–3 days)
Add a `traveler_id` foreign key to `BookingDocument` (already has it as `traveler_id` in the data model or can be added via document metadata). Group the document list by traveler. Show per-traveler document completeness. If `bookingData.travelers` has 2 travelers and only 1 has a passport document, the second traveler card shows a "Passport — missing" slot in red.

This requires: a grouping utility function, a new `TravelerDocumentCard` component, and possibly a metadata field on `BookingDocument` if `traveler_id` is not already stored. No backend route duplication needed — the existing document endpoints serve the data.

### Slice C — Booking task generation from itinerary (3–4 days)
When a trip enters booking stage, the system should create a default task set from the accepted proposal's itinerary components. Read the itinerary data from `trip.proposal` or the accepted quote. Parse hotel stays, flight legs, and major services into `BookingTask` records with auto-populated component name and a blank deadline field. The operator fills in supplier deadlines; the system handles the rest.

This requires: a backend endpoint or trigger that reads the accepted proposal and calls the booking task creation API; a frontend UX that shows "tasks generated from itinerary" vs. "manually added." The 7-state machine in `BookingExecutionPanel` stays unchanged.

### Slice D — Payment due-date field and overdue detection (1 day)
Add `next_due_date` (ISO date string, nullable) to `PaymentTracking`. Render it in the payment tracking display. Add a derived status: if `next_due_date` is in the past and `payment_status` is not `paid` or `waived`, auto-badge the block as overdue in red. Feed this into the Next Action ranking (Slice A).

---

## 7. What not to build yet

- **Client-facing portal.** The collection link + form is the right edge for now. A full client portal with trip viewing, itinerary display, and interactive confirmations is a 2027 product line. Building it before the internal ops surface is solid will create an unmaintained public surface and a fragmented data model.
- **Sub-tabs navigation.** The temptation to split Ops into Data / Documents / Payments / Tasks / Confirmations sub-tabs is real and will feel like a win. Resist it until the single-surface Next Action + traveler-grouped view has been validated. Tabs fragment operator attention and create the illusion of organization without solving the underlying "what do I do next" problem. Add tabs at month 12 when the surface is large enough that scroll navigation genuinely breaks.
- **Automated supplier communication.** Do not build email generation, supplier API integrations, or automated booking flows until the data model for tasks and confirmations is stable. Automation on top of fragile data creates more mistakes than it saves time.
- **Multi-currency conversion.** The `currency` field is already there. Conversion rates, multi-currency invoicing, and reconciliation are accounting products. Track currency as metadata; do not build rate fetching or conversion into Ops.
- **Notification system.** Anomaly detection in Section 6 of the ideal layout should be on-page first. Push notifications, email summaries, and Slack/WhatsApp integration are the right 12-month features but require notification infrastructure that does not yet exist. Do not couple the anomaly detection logic to a notification pipeline; build detection as a derived UI layer first.

---

## 8. Risks and failure modes

**The "one more field" trap.** `PaymentTrackingDraft` already has 14 fields. `BookingTraveler` has 4 today. Every sprint will have someone ask "can we add X?" The risk is an Ops surface that becomes a data entry form for every edge case a single client ever requested. Counter: define the canonical fields that 80% of trips need and make everything else a `notes` field or a structured extension.

**Confirmation diffing creates false positives.** If the confirmation diff logic is naive (string matching on hotel names, date formats), operators will distrust it within 2 weeks of launch. The diff must normalize dates, handle alternate hotel name spellings, and allow operators to "accept as matching" when the system flags a non-issue. Ship the diff behind a "review flagged items" expandable, not as a blocking banner.

**Task generation from itinerary creates busywork.** If the auto-generated tasks are too granular (one task per hotel night), operators will delete them all and revert to manual entry. The correct granularity is one task per bookable component: one flight booking, one hotel stay (regardless of nights), one transfer. Get this wrong and Slice C creates more friction than it removes.

**The timeline becomes the source of truth for disputes but isn't treated as immutable.** `ExecutionTimelinePanel` is an event log, but if it is editable or if log entries can be deleted via document deletion, it loses its value as an audit spine. Every write to the timeline should be append-only with actor + timestamp. This is a backend guarantee, not a UI concern, but the UI must not allow operators to believe they can retroactively clean the log.

**Sub-tab pressure before product-market fit.** The pattern in this category is: ship tabbed navigation as an "organization improvement," operators stop seeing the cross-sectional anomalies that the flat view surfaced, and the product loses its diagnostic character. Deferring tabs requires disciplined stakeholder management through month 6–12 of growth.

---

## 9. Three strongest insights with 2028 hindsight

### Insight 1: The provenance chain from document to booking record became the product's defensible moat

In May 2026, `bookingDataSource` (`agent` vs. `customer_accepted`) felt like a minor UX nicety. By 2028 it was the most-cited feature in agency sales conversations. When a traveler disputed a passport number error and the agency could show a timestamped record — "this data was submitted by the customer through the collection link on this date and accepted by operator X at this time" — the dispute resolution time dropped from weeks to hours. The extraction conflict log (`extractionConflicts`) turned out to have the same value: agencies that had AI-extracted data with operator confirmation records were indemnified in two supplier disputes where agencies without it were not. Auditability at the field level, not just the document level, was the defensible moat nobody saw coming.

### Insight 2: The agencies that scaled from 3 to 12 people did it by making junior staff capable of handling booking execution, not by hiring more senior travel agents

The 3-person agencies that grew to 12 did not hire 9 more senior agents. They hired 9 junior coordinators and used the product to constrain what junior staff could do wrong. The booking task state machine, the readiness tiers, and the Next Action card together gave junior coordinators a script: "the system says do this, so I do this." Agencies that did not have that constraint relied on senior agent judgment for every step, could not delegate, and stayed small. The implication for product: every design decision should be evaluated against the question "can a 6-month-in coordinator use this without asking a senior agent?" The flat document list with a global Extract button fails this test. Per-traveler document slots with clear missing-document indicators pass it.

### Insight 3: The most important architectural decision was keeping payments as tracking-only in 2026

The temptation in 2026 was to build a real payments layer: Stripe integration, invoice generation, automated receipts. The teams that resisted and kept it tracking-only won on two dimensions. First, they shipped faster and had a working, tested surface with no integration maintenance debt. Second, they preserved the architecture to plug in whichever payments infrastructure each agency already used. By 2027 the market had fragmented into agencies using Razorpay, agencies using manual bank transfer with WhatsApp proof photos, agencies using corporate card reconciliation, and agencies using partial payment through booking.com. The tracking-only model accommodated all of these without a database migration. The teams that built a payments integration in 2026 spent Q1 2027 rebuilding it.

---

## 10. One surprising idea

**The booking task list should be auditable as an operator's "handwriting" sample.**

By 2028, the agencies with the best reputation for execution had something in common: their task completion patterns were consistent. A senior agent's tasks were completed in a recognizable sequence, with consistent time spacing, consistent note formats, and a recognizable error correction style. Waypoint OS can surface this as a per-operator execution fingerprint — not for surveillance, but for mentorship and quality recovery. When a junior coordinator's task pattern diverges sharply from the agency's established pattern (tasks marked complete too fast with no notes, deadline fields left blank, confirmations linked without review), the system can flag it for a senior agent review rather than waiting for the client to complain. This turns the execution timeline from a passive log into an active quality layer, and it requires no new data — just pattern analysis on the events that the timeline already records.

---

**The thing most people miss about this:** The bottleneck in a 3-person travel agency is never time — it is cognitive load. Every task switch costs more than the task itself. The teams that designed Ops as a "complete record you can look things up in" built a reference tool. The teams that designed it as a "what do I do next" surface built a force multiplier. The current Ops page, as of May 2026, is 80% of the way to being the best reference tool in the category. It is 20% of the way to being a force multiplier. The next 12 months of product decisions will determine which one it becomes.
