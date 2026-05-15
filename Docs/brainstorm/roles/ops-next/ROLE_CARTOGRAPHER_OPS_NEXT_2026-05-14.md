# Brainstorm Role: Cartographer — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-Sentence Thesis

Ops should be a spatially-organized booking execution master record where an operator can, in a single downward reading pass, answer: "what is blocking this trip right now, and what do I do next?"

---

## 2. What the Current Ops Page Gets Right

- **Readiness-as-context, not readiness-as-gate.** The existing design correctly shows readiness signals inline but does not prevent access to any section when readiness is absent. This is the right call — operators in small agencies can't afford locked-out workflows.
- **Customer submission review as a distinct inbox action.** The amber-bordered pending review block surfaces a discrete decision (accept/reject customer-submitted data) rather than merging it silently into the booking details form. That distinction matters for auditability.
- **Extraction confidence at the field level.** The per-field confidence percentages (90%+ green, 70%+ yellow, below red) on document extraction are genuinely useful — operators learn to trust or distrust individual fields rather than the whole document.
- **Separation of booking data source provenance.** The "Customer (verified)" vs "Agent" badge on the booking details section is a meaningful audit trail signal, even if currently understated.
- **BookingExecutionPanel's 7-state machine.** Having not_started / blocked / ready / in_progress / waiting_on_customer / completed / cancelled as distinct, named states reflects real booking work. The state machine is not over-simplified.
- **Collection link as a first-class workflow tool.** Generate / copy / revoke as a complete mini-workflow inside Ops is correct — the link is not a settings detail, it is an active ops action.

---

## 3. What It Gets Wrong

**Wrong reading order.** The current page reads: Readiness → Tiers → Missing fields → Signals → Pending review → Booking details → Collection link → Documents → Execution tasks → Confirmations → Timeline. This is an architectural inventory, not an operator workflow. An operator arriving on this page after a client call needs to know *what action to take right now*, not see a readiness tier breakdown as the first cognitive load.

**Readiness tiers are placed where next-action cues belong.** Readiness is diagnostic context. It answers "am I ready to book?" It is not the answer to "what do I do now?" These are different questions. Right now they are conflated positionally.

**Payments are unanchored.** Payment tracking (agreed amount, paid, balance, status) lives inside the Booking Details card, as a sub-section of traveler data. This makes it invisible at a glance. A trip with overdue payment looks identical structurally to a trip with payment confirmed. The visual hierarchy does not communicate financial risk.

**Documents are a flat list without ownership or purpose context.** A passport uploaded by a customer, a hotel confirmation received from a supplier, and a visa copy uploaded by the agent are rendered as peers in a single `documents.map()` list. An operator scanning the list cannot immediately answer "do I have everything I need for this trip?" They have to mentally classify each item.

**Extraction results render inline inside the document row.** The extraction UI (field list, traveler selector, conflict resolution, apply/reject buttons) currently expands below each document row within the same flat list. For a trip with 3 travelers and 3 documents each, this becomes 9 inline expansion zones in one scrollable column — cognitively fragmented.

**Collection link and Customer Submission are spatially separated.** The collection link generator appears after Booking Details, and the pending submission review appears before Booking Details. They are two phases of the same workflow (send link → customer submits → agent reviews) but are not adjacent or visually grouped.

**The timeline is a passive log at the bottom.** ExecutionTimelinePanel lives at the very end of the page — below everything else. Operators who want to review what happened on a booking task or who made a change must scroll past the entire page. The timeline is a trust instrument, not an appendix.

**No "current moment" anchor.** The page has no header section that tells an operator what is happening right now: what stage is the trip in, when is departure, what is the open blocking issue. Every section starts without that anchor, so the operator must reconstruct context from the aggregate of what they see.

---

## 4. The Top 5 Operator Decisions Ops Must Support

1. **"Is this trip ready to book, and if not, what specifically is missing?"**
   This is the booking readiness question. It drives the main workflow gate. The answer must be immediately visible without scrolling.

2. **"Has the customer given me everything I need, and have I reviewed and accepted it?"**
   Traveler data, documents, and the collection link workflow are all sub-answers to this question. The operator needs a single pass to confirm all required inputs are complete and verified.

3. **"What booking tasks are open right now, and what is blocked?"**
   The 7-state execution board is the active work queue. In a 3-person agency, this is the equivalent of a job board — the operator looks at it to know where to spend the next 30 minutes.

4. **"Am I going to get paid, and when?"**
   Payment status (agreed, paid, balance, overdue) is a financial risk signal. An operator must be able to see payment health without hunting for it inside a traveler card.

5. **"What happened on this trip so that I can explain it to a client, a colleague, or an auditor?"**
   The execution timeline is the answer. It must be accessible — not buried — because operators use it during client calls, handoffs, and dispute resolution.

---

## 5. Ideal Page Layout

The page should be divided into four spatial zones, reading top to bottom. Each zone answers exactly one operator question.

### Zone 1 — Trip Command Strip (always visible, non-scrolling header area)
**Answers: "Where am I and what is the top priority right now?"**

A narrow sticky strip at the top of the Ops page (not the global nav — inside the ops surface itself). Contains:
- Trip name + stage badge (proposal / booking) + departure date countdown ("14 days out")
- Readiness pulse: a single summary indicator showing highest_ready_tier + missing_for_next (collapsed to one line: "Ready for tier 2 — missing: passport_number for adult_2")
- Payment health chip: agreed amount vs. paid amount + status color (green/amber/red) — one chip, always visible
- If pendingData exists: an amber "1 customer submission awaiting review" pill that acts as an anchor link jumping to Zone 2

This strip does NOT expand. It is a one-line-per-concept summary. Its function is orientation. If the operator sees all-green chips and no amber pill, they know the trip is healthy without reading the rest of the page.

### Zone 2 — Data Intake (expandable cards, collapsible as a group)
**Answers: "Do I have all required inputs from the customer?"**

This zone groups three things that are logically one workflow: send → submit → verify.

Sub-section 2A: Customer Collection Link
- Status: active link (expires when) / no active link
- Generate / Copy / Revoke actions
- Position: top of this zone because it is the trigger for everything below

Sub-section 2B: Pending Customer Submission (conditional — only shown when pendingData exists)
- Amber card showing submitted traveler data
- Accept / Reject actions
- Disappears after action (or shows "accepted" tombstone for audit)

Sub-section 2C: Traveler Booking Details (always shown)
- Current traveler table (ID, name, DOB, passport)
- Payer name
- Source badge (Customer verified / Agent)
- Edit button
- This section is the canonical record. It reflects either agent-entered or customer-accepted data.

These three sub-sections are vertically stacked. The reading order is intentional: generate link → await submission → review submission → see canonical record. This is the intake flow.

### Zone 3 — Documents (grouped by traveler, then by type)
**Answers: "Do I have all required documents, and are they verified?"**

Structure change from current flat list to a two-level grouping:

Level 1 header: per-traveler group ("adult_1 — John Smith" / "adult_2 — Priya Verma")
Within each traveler group: document rows organized by document_type (passport, visa, insurance, other)

Level 1 header also: "Trip-level documents" for non-traveler docs (hotel confirmations, flight tickets, supplier confirmations) — these belong to the trip, not a traveler.

Each document row:
- Document type label + filename + size + upload source badge
- Status chip (pending_review / accepted / rejected)
- Actions: Accept / Reject / Download / Delete
- Extract button (per doc) leads to an inline panel BELOW the document row (same as now, but contained inside the traveler group accordion)

Upload button moves to the traveler group header: "Upload for adult_1" with doc type selector inline. This eliminates the global upload control at the top of the section.

The traveler-grouped layout answers the completeness question directly: an operator can see "adult_1: passport (accepted), visa (missing)" at a glance.

### Zone 4 — Execution (tasks + confirmations + timeline as three tabs within this zone)
**Answers: "What work is happening on this trip, what is confirmed, and what is the audit record?"**

Zone 4 is the operational workspace. It is where the agent works after data intake is complete.

Tab 4A — Tasks (BookingExecutionPanel)
- The task board with 7-state state machine
- Group by status bucket: Blocked | In Progress | Waiting on Customer | Ready | Completed
- This is the daily work queue view

Tab 4B — Confirmations (ConfirmationPanel)
- Per-booking confirmation records
- Future: diff against proposed itinerary line items

Tab 4C — Timeline (ExecutionTimelinePanel)
- Actor-typed event log
- Full audit history
- Accessible via tab, not buried at bottom of page

These three panels become tabs because they are all "after the data is collected" surfaces. An operator does not look at Tasks and Timeline simultaneously — they are distinct modes of attention. Tabs reduce scroll debt without hiding functionality.

The tab control sits immediately below Zone 3, visible without scrolling past long document lists.

### Summary of reading order:

```
[ Zone 1: Command Strip — always visible, orientation ]
[ Zone 2: Data Intake — collect → submit → verify ]
  [ 2A: Collection Link ]
  [ 2B: Pending Submission (conditional) ]
  [ 2C: Booking Details (canonical) ]
[ Zone 3: Documents — grouped by traveler ]
  [ adult_1 accordion → docs ]
  [ adult_2 accordion → docs ]
  [ trip-level docs ]
[ Zone 4: Execution — tab bar ]
  [ Tasks | Confirmations | Timeline ]
```

This layout can be read top-to-bottom on a healthy trip in under 30 seconds: strip is green → link sent → data collected → documents complete → tasks all in progress or complete.

---

## 6. What to Build Next

**Specific, concrete, small:**

**Slice 6A — Command Strip (1-2 days)**
Add a non-scrolling summary strip at the top of the Ops page with three pieces of information: (1) highest_ready_tier + first missing field from missing_for_next as a one-line string, (2) payment status chip derived from existing payment_tracking data, (3) conditional "N submission awaiting review" amber anchor link when pendingData is present. No new API calls — all data already fetched by OpsPanel. This is a pure rendering change on top of existing state.

**Slice 6B — Group Collection Link + Pending Submission + Booking Details into one contiguous zone (1 day)**
Reorder the three sections so they appear as 2A → 2B → 2C in DOM order, wrapped in a single "Data Intake" section header. No logic changes. Move the `ops-collection-link` div above `ops-pending-review` above `ops-booking-data`. Add a section label. This makes the intake flow spatially coherent without any behavior change.

**Slice 6C — Traveler-grouped documents (2-3 days)**
Refactor the documents section to render a traveler-keyed accordion structure. Group logic: for each traveler in bookingData.travelers, filter documents where uploaded_by_id matches traveler_id (or add a traveler_id field to BookingDocument). Add a "Trip Documents" group for unowned docs. Move the upload control to the traveler group header. This is the highest-value layout change for multi-traveler trips.

**Slice 6D — Zone 4 tab control (1 day)**
Wrap BookingExecutionPanel, ConfirmationPanel, and ExecutionTimelinePanel in a simple tab component with labels "Tasks / Confirmations / Timeline". Default tab is Tasks. This does not change any panel internals — it only changes how they are presented spatially. Eliminates the current behavior where the timeline is buried below 200+ lines of task and confirmation content.

Total: approximately 5-7 days of focused frontend work for all four slices. Each slice is independently shippable and does not break existing functionality.

---

## 7. What Not to Build Yet

**Supplier deadline linkage to payment dates.** Conceptually correct (knowing that a hotel requires 50% deposit by a specific date should live near the payment tracking row), but it requires a supplier deadline data model that does not exist yet. Do not bolt this onto the current payment_tracking struct — it needs its own entity. Build the spatial container for it in Zone 1 (a "Next deadline" chip) but leave it empty until the data model exists.

**Confirmation diff against proposed itinerary.** This is the right long-term vision (ConfirmationPanel shows what was promised vs. what was confirmed) but it requires the accepted quote / itinerary to be a queryable data structure. Right now the itinerary likely lives in proposal documents or unstructured text. Do not invent a diff surface before the source-of-truth for "what was proposed" is structured.

**Public / client-facing booking status page.** The collection link is already a client-facing surface. Do not extend it into a full client portal on this slice. The client-facing workflow should be designed separately, after the operator-facing Ops surface is coherent.

**Booking tasks auto-generated from the accepted quote.** This is one of the strongest long-term ideas (task list derived from itinerary line items rather than manually created), but it requires the quote/output to have structured line items with supplier identifiers. Currently BookingExecutionPanel tasks are manually created. The structural prerequisite is a structured proposal/itinerary entity. Flag this as the next major architectural investment, but do not attempt it before that entity exists.

**Ops sub-tabs as a permanent navigation structure (full route split).** The Zone 4 tab control described above is a layout choice, not a route change. Do not split /ops into /ops/tasks, /ops/confirmations, /ops/timeline as separate Next.js routes in this slice. The sub-tab approach keeps all data in one component tree and avoids prop-threading or context re-fetching across route changes.

---

## 8. Risks and Failure Modes

**Traveler-document association data gap.** The current BookingDocument type may not carry a traveler_id field. If documents are not linked to travelers in the backend schema, the grouping logic in Slice 6C cannot be implemented without a backend migration. Verify the document schema before committing to the traveler-grouped layout.

**Command Strip state-dependency on bookingData load.** Zone 1 (the strip) depends on readiness, bookingData, and pendingData — three separate async fetches. If any is loading, the strip should show a skeleton rather than partial or incorrect state. The current sequential loading pattern (readiness from trip prop, bookingData from getBookingData, pendingData from getPendingBookingData) means the strip may flash incomplete for several hundred milliseconds on load. This needs explicit loading coordination.

**Tab default causing timeline to become invisible.** If Zone 4 defaults to the Tasks tab, operators who previously relied on scrolling to the timeline to get a quick audit view may not discover the tab. Include a visual indicator (e.g., a badge on the Timeline tab showing "N events") to draw attention to it.

**OpsPanel size and the temptation to extract too aggressively.** The component is 1399 lines. The correct response to this is zone-based extraction (one component per zone), not atomization. If the refactor breaks into too many small components with tangled prop-threading, it will be harder to maintain than the current monolith. Extract by zone (DataIntakeZone, DocumentsZone, ExecutionZone), not by individual sub-section.

**Payment tracking orphaned from supplier deadlines.** If payment tracking is visually elevated into Zone 1 (as a chip) but not connected to any deadline context, operators may misread a "partially paid" status as fine when there is actually a supplier deadline in 3 days. The chip must either show deadline context or not show financial risk coloring until deadline data exists.

**Conflict resolution UX in extraction is deeply nested.** The current extraction conflict UI (conflicts detected → per-field display → overwrite button) lives inside a document row, inside a traveler accordion, inside Zone 3. This is three levels of nesting for a decision that requires operator attention. Consider a modal or a dedicated conflict review panel rather than inline expansion at this depth.

---

## 9. Three Strongest Insights

**Insight 1: Readiness is a diagnostic, not a workflow driver.**
The current page treats readiness as the primary frame for the entire Ops surface — it is the first thing rendered, and the page is implicitly organized around answering "is this ready?" But operators do not arrive on the Ops page to answer that question. They arrive to take an action. Readiness is a tool the operator uses to decide which action to take. Moving it from primary position to a summary chip in the Command Strip is not a demotion — it is a correct reclassification from "primary subject" to "context instrument." This single reframe changes the entire reading order of the page.

**Insight 2: The collection link, pending submission, and booking details are one workflow masquerading as three separate sections.**
Send link → customer fills form → agent reviews submission → canonical booking data is updated. This is a linear workflow with a clear handoff at each step. The current layout breaks it across three separately-rendered sections with unrelated content between them. Collapsing these into one contiguous zone does not add features — it surfaces existing logic that the product already has. The workflow is already implemented; it is just spatially incoherent.

**Insight 3: The timeline is an audit instrument, not a history decoration.**
ExecutionTimelinePanel at the bottom of the page reads as an "also here" feature — something you scroll to if you happen to be curious. But in real agency operations, the timeline is how you explain to a client why their booking took 4 days, or how you hand off a trip to a colleague mid-execution, or how you demonstrate due diligence to a supplier in a dispute. Making it accessible via a tab in Zone 4 is not just a layout improvement — it is a statement that the timeline is a first-class operational tool. Small agencies that use the timeline confidently look like large agencies.

---

## 10. One Surprising Idea

**Give the Zone 1 Command Strip a keyboard shortcut that copies the current trip status as a one-paragraph client-facing summary.**

An operator on a phone call with a client should be able to press `Cmd+Shift+S` (or similar) while looking at the Ops page and have the clipboard filled with: "Hi [client name], your trip is currently in booking stage. We have your traveler details confirmed, all documents received, and 3 of 5 booking tasks are complete. We're waiting on confirmation from [supplier]. Expected completion by [date]." The data for all of this already exists in the page — readiness tier, booking data, document statuses, task states, timeline events. No new API. No new modal. Just a copy-to-clipboard action that synthesizes the page state into natural language. For a 2-person agency fielding 20 client calls a week, this saves 3 minutes per call and eliminates the risk of an agent giving a client an inaccurate status because they were reading from memory rather than the current record.

---

**The thing most people miss about this:**

The Ops page is not primarily a data entry surface — it is a trust instrument. Every section exists to let an operator answer, under pressure, "I know exactly what is happening with this booking and I can prove it." Travelers and payers are not just data rows; they are the people whose trip will either go well or go badly. Documents are not files; they are proof that the agency did its job. The timeline is not a log; it is the agency's legal record. The UX mistake most teams make with an ops surface like this is optimizing for how fast data can be entered. The correct optimization is how clearly the current state can be read — because operators spend far more time reading and acting than entering. A layout that makes reading fast and trustworthy is worth more than one that makes editing marginally more ergonomic.
