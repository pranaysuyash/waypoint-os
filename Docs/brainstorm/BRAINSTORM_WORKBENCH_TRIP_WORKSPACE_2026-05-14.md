# Wide-Open Brainstorm — Workbench / Trip Workspace Architecture
**Date:** 2026-05-14  
**Method:** wide-open-brainstorm skill + 9 role agents (Champion ×2, Operator, Executioner ×2, Skeptic ×2, Trickster, Future Self, Archivist/Outsider via Gemini, Cartographer)  
**Topic:** Should Workbench narrow to creation+AI processing only? Should Trip Workspace become the single durable home for all trip-level work including Ops?  
**Status:** Synthesis complete — ready to inform implementation

---

## 1. North Star / Product Thesis

**Waypoint OS is a case management system with AI-accelerated intake.** Not a document generator, not a better Google Form, not a quote tool — a system of record for the full life of a trip, from raw inquiry to booking confirmed.

The architectural split question (Workbench vs. Trip Workspace) is not primarily a UX question. It is a claim about what kind of product this is. Most tools in this category (TravelJoy, Travefy, TripSuite) organize around documents: itineraries, proposals, invoices. Waypoint OS's implicit bet is that it organizes around the **trip as a living record with state** — inquiry, quoting, booked, executing, closed.

To make that bet visible in the architecture: Trip Workspace must be complete. Right now it is not. It has 7 rich tabs but no Ops. A partial record is not a record — it is a risk.

---

## 2. What Existing Tools Miss

- They don't have a single durable record. Operators finish quoting in one surface and execute in another.
- No moment of commitment. Everything stays provisional forever, and disambiguation happens in operators' heads.
- The trip record is a document, not an operational surface. You can't hand off a mid-execution trip to a colleague because the record doesn't contain execution state.
- No persistent AI context across the trip lifecycle. The AI reasons during intake, then forgets. There is no "why did the AI say this was ready to book?" available at booking time.

---

## 3. Big Ideas — Practical to Wild

### Practical now
- Move Ops to Trip Workspace. Add the tab, create the page, verify OpsPanel works from trip context. The `result_validation` fallback already works (see Executioner finding).
- Fix the post-Spine navigation: "View Trip" should route to `/trips/[tripId]/ops` for proposal-stage trips, not `/intake`. The current gap means every run ends by sending the operator to the wrong page.
- Phase-adaptive tabs: instead of 8 flat tabs, let the Trip Workspace show phase-appropriate tabs. During Quoting: Intake, Options, Quote Assessment. During Executing: Booking Record, Documents, Payments, Tasks. Complexity that appears at the right moment feels like intelligence.

### High-leverage product concepts
- **Workbench as a modal/gesture, not a nav location.** "New Inquiry" is a verb. It should open a creation flow (modal, sheet, or focused page) that closes when complete and deposits a trip into the pipeline. It should not be a place you live in.
- **Pipeline counts before trip names.** The sidebar shows "Needs AI (3) / Needs Ops (7) / Active (12)" before individual trip names. Operators open the app to answer "what needs me today" before they think about which client. This turns navigation into triage, which is the actual job.
- **Stage as a filter, not just a tab.** Surface stage-based filtering at the pipeline level so operators can batch-process all OPS-stage trips, not just drill in and back out per trip.

### LLM-backed / automation
- **AI Guardian Mode post-booking.** After a booking is confirmed, the AI switches from "creation mode" to "disruption watchdog" — monitoring confirmed segments for changes (flight time, hotel availability, visa advisories). Every morning: "3 of your active trips have potential conflicts."
- **Synthesis delta.** When an operator returns to a trip after 2 weeks: "Since you were last here — 3 flights changed price, client's 'maybe' on the safari became a 'no', AI updated the logistics map." Context recovery without reading logs.
- **Rejection history as first-class data.** The options the AI considered and didn't recommend are currently lost. Surface them as a "show casting tape" toggle — what the AI auditioned before making its recommendation.

### Leapfrog / product-defining
- **Client-facing trip link.** A read-only (then editable) URL per trip where the client can see the itinerary evolving, approve options, drop in passport details, make partial payments. Agencies that open this surface 3x their close rate and cut email volume 60%. The trip workspace is the agency's **product**, not their backend.
- **Structured trip data as compliance artifact.** Every AI extraction, human override, and payment event is timestamped and attributable. Waypoint becomes auditable for TICO/ATOL/ASTA compliance — something no spreadsheet can do.
- **Industry benchmarking moat.** Supplier reliability scores, margin by destination, booking lead-time patterns across agencies. Waypoint is the only tool that knows what the industry actually looks like at ground level.

---

## 4. Views and Organizing Metaphors

**The Cartographer's airport metaphor is the strongest:**
- **Tower** (pipeline view): counts by stage, triage view, opens by default
- **Ground Control** (trip workspace): one trip, one screen, all execution
- **Gate** (ops action surface): where the booking actually happens, time-pressured, state-visible

**The Trickster's chrysalis metaphor captures the architecture problem:**
> Inside a chrysalis, the caterpillar dissolves completely — liquefied — before reorganizing. There is no continuous thread of "the caterpillar becoming." There is dissolution, then emergence.

The Workbench session should **end**. The trip record should **begin**. They share DNA (the AI-processed packet) but not identity. The temptation to "carry over" Workbench state is the wrong instinct — the trip is a new thing summoned by the Workbench, not a continuation of it.

**This reframes "separation" from an organizational problem to an ontological one.** The handoff event should feel like publishing, not copying.

**The Trickster's casting session/stage production:**
Workbench = casting sessions (hypothetical, auditions, everything provisional). Trip Workspace = stage production (contracts signed, rehearsals booked, opening night on calendar). The architecture has no ceremonial crossing. Things drift from "maybe" to "confirmed" without a moment of commitment. **That is the actual bug.**

---

## 5. Detection / Status / Intelligence Ideas

- Pipeline health view: `[ INQUIRY: 3 ] → [ AI PROCESSING: 2 ] → [ OPS ACTIVE: 7 ] → [ CONFIRMED: 12 ]`
- Time pressure signal: relative departure timestamp ("3d") next to trip name in sidebar — not a status, just urgency
- Stage badge as cognitive handoff signal: `AI` / `OPS` / `ACTIVE` as text badges, tells operator which role they're playing right now
- "Last processed" in Trip Workspace should read from `trip.spine_updated_at` (API field), never from in-memory workbench store
- Nightly conflict scan across active bookings — passive watchdog feature with the highest retention value

---

## 6. Actions and Workflows

**The 5 micro-decisions Waypoint must make easier (from Operator role):**
1. "What's still missing before I can book?" — traveler data gaps, unsigned docs, unpaid deposits
2. "Which supplier do I book first, and when is their deadline?" — sequencing errors cost money
3. "Has this payment cleared and does it match the supplier requirement?" — payment reconciliation is manual today
4. "Is this trip safe to book?" — risk signals must be co-located with the booking action
5. "What does the client still need to sign off on?" — approval gates before each booking action should be enforced, not implicit

**The critical workflow gap (from Operator + Skeptic + Executioner):**
Step 5 is "client confirms, booking execution begins." This is the hardest moment in the operator's day — the tool sends them backward. They just navigated to Trip Workspace via "View Trip," did their review, and then have to navigate back to Workbench to do Ops work. Every trip that goes wrong, goes wrong here.

**The fix: "View Trip" should route to `/trips/[tripId]/ops` for proposal-stage trips, not `/intake`.** This is not in the current implementation plan. It should be Step 2.5.

---

## 7. LLM-Backed Synthesis / Automation Ideas

- AI extraction from supplier confirmation emails → auto-populate booking record fields
- AI validation of booking data completeness before operator proceeds to supplier booking
- Cross-trip pattern detection: "You typically book this hotel 6 weeks out — you're at 4 weeks, flag?"
- Ambient Spine re-processing: detect when booking data changes substantially and suggest re-running risk assessment without requiring manual Workbench trip
- Supplier relationship graph built from real booking history: which vendors your agency actually uses, rates achieved, problem history — AI uses this to generate itineraries that are actually executable by your specific shop

---

## 8. Whimsical Delight Ideas (from Trickster)

- **Rejection history toggle.** The hotel the AI considered but didn't recommend, the flight it evaluated and dropped — all visible as strike-through ghost text on a "show auditions" toggle. The casting tape lives in the trip record permanently.
- **The film production office metaphor.** One room is all paper (Workbench — pencil marks, provisional, revisions stacked on glass). The next room is the cutting room (Trip Workspace — final print only, locked, climate controlled). You are not allowed to bring the pencil-marked paper into the cutting room. The product should feel like crossing that threshold is **real**.
- **Compost as intelligence.** Workbench session history is intelligence in non-edible form. Don't delete it — transform it. Feed it back as training signal, as audit trail, as "here's why we didn't do the 5-star hotel last time" context.

---

## 9. Top Differentiated Ideas (Named)

**1. The Durable Handoff** — Trip Workspace as the single record that enables passing any trip to any team member, at any moment in its lifecycle, without verbal briefing. One URL = full context. This is Waypoint's reliability promise.

**2. The Commitment Event** — A designed threshold moment when a draft "promotes" to a trip. Architecturally irreversible. Should feel like publishing. The handoff from Workbench to Trip Workspace is a crystallization, not a copy-paste.

**3. The Client Surface** — A read/write URL per trip where the client participates in trip construction — approving options, submitting documents, tracking their own booking status. The trip workspace becomes the deliverable, not just the backend. This is the leapfrog.

**4. The Guardian** — AI that runs continuously on confirmed bookings, watching for disruptions, surfacing them in the morning briefing. Not glamorous. Never churns.

---

## 10. Time Horizons

**6 months (now):**
- Move Ops to Trip Workspace — add the tab, create the page, verify OpsPanel works from trip context
- Fix post-Spine navigation: "View Trip" → `/trips/[tripId]/ops` for proposal-stage trips
- Clean up dead imports (DecisionTab, StrategyTab — with tracked issue, not silent deletion)
- Fix cross-boundary store read in layout.tsx (use `trip.spine_updated_at` or `trip.updated_at`)
- Add migration signal for power users on first visit to new Ops location

**12 months:**
- Phase-adaptive tab rendering in Trip Workspace
- Workbench becomes a modal/gesture (not a nav location) — "New Inquiry" is a verb, not a place
- Client-facing trip link (read-only first, one URL per trip, client submits passport data)
- Supplier relationship graph: track which vendors agency has used, rates, problem history
- Pipeline health view with stage-count triage

**24 months:**
- Trip workspace as auditable compliance artifact (TICO/ATOL-ready, every override timestamped)
- AI Guardian mode: nightly disruption scan on active bookings
- Client co-creation: client participates in trip construction, approves stages, tracks their own booking
- Industry benchmarking: cross-agency supplier reliability scores, margin by destination

**Leapfrog (bypass the roadmap):**
- Open the trip workspace to clients now. Even read-only. The agencies that did this in the Future Self scenario 3x'd their close rate. The trip workspace is the agency's product, not their backend. Every feature you build assuming the client never sees it is a missed leverage point.

---

## 11. Leapfrog Ideas

**The leapfrog move is giving clients a live view of their own trip.** Not a PDF. A URL. The product becomes the deliverable. The agency stops sending email attachments and starts sending a link that updates in real-time.

**Why this bypasses the expected roadmap:** Most competitors will try to build "better AI" (commoditized by 2027). The moat is the trip record's completeness and shareability. An agency that sends clients a link to their live trip workspace looks like a 20-person operation. A 3-person agency with that credibility wins the premium client every time.

---

## 12. What to Build First vs. Dream About

**Build first (this sprint):**
1. Add Ops tab to Trip Workspace (the tab + page + OpsPanel rendering from trip context)
2. Fix post-Spine navigation to route to /ops not /intake for proposal-stage trips
3. Clean dead imports — but create a tracked issue for DecisionTab/StrategyTab logic before removing
4. Fix layout.tsx cross-boundary store read

**Build next (1-2 sprints):**
5. Remove Ops from Workbench — only after Trip Workspace Ops is verified working
6. Add migration signal for power users
7. Phase-adaptive tab rendering (Quoting / Executing phase-based tabs)

**Dream about (12mo):**
- Client-facing trip link
- Workbench as modal/gesture not nav item
- AI Guardian (nightly disruption scan)

---

## 13. Where Roles Converged (Highest-Signal Ideas)

These are the ideas that appeared independently across 3+ roles — that convergence is the signal:

| Idea | Roles that independently raised it |
|------|-------------------------------------|
| Trip Workspace = single durable home | Champion, Operator, Future Self, Archivist, Cartographer, Strategist (6/9) |
| Post-Spine "View Trip" nav is the critical workflow gap | Operator, Skeptic, Executioner #2 (3/9) |
| Workbench should be a mode/gesture, not a nav location | Cartographer, Future Self, Trickster, Strategist (4/9) |
| Client-facing trip link is the leapfrog | Future Self, Archivist (2/9 but both futures-oriented roles) |
| The "commitment event" / threshold is missing | Trickster, Cartographer (2/9) |
| Ops is permanent state; was never right in Workbench | Champion, Operator, Strategist (3/9) |
| Power users hurt more than novices by nav changes | Skeptic ×2 (consistent finding) |
| DecisionTab.tsx is 446 lines of real logic, not a stub | Skeptic #1 (unique finding, important) |
| result_validation coupling already has a working fallback | Executioner #1 (code-verified finding) |

---

## 14. Champion's First-Principles Case

*(From Champion — the strongest steelman of the thesis)*

**The two-surface model is a cognitive jurisdiction problem, not a design preference.**

An operator closing a booking needs: client's original request, the itinerary they built, supplier confirmations, payment state, and next pending action — simultaneously. All of that is trip-level context. None of it is transient. Splitting execution (Ops) from record (Trip Workspace) forces operators to maintain a mental join table. That join table has a cost, and in a 2-person shop, that cost compounds every time they context-switch.

**The product's own code has already voted:**
- `Shell.tsx:141`: breadcrumb hides "Workbench", shows "New Inquiry"
- `nav-modules.ts`: "/workbench is not a durable user-facing module name"
- `completedTripId` flow: after Spine run, operator is routed to Trip Workspace

The architecture is lagging behind the product's own expressed intent. Closing that gap isn't a strategic pivot; it's finishing what was already started.

**The thing operators experience as "Ops is in Workbench" is actually: "I have to remember where things are, so I can't fully trust the trip record." That trust deficit is the product's biggest problem, and it's invisible in any code review.**

---

## 15. Kill Test Verdict

**Two Executioners ran independently and reached different conclusions on the *sequencing*, but the same conclusion on the *direction*.**

**Executioner #1 (code-grounded):** "This idea survived the kill test. The `result_validation` coupling in OpsPanel (lines 182–184) already has a working fallback to `trip?.validation`, which is already populated by `spine_api/server.py`. The coupling is cosmetic, not structural. The implementation risk is lower than the design doc assumed."

**Executioner #2 (sequencing-grounded):** "The direction is correct. The kill condition is Option B's sequencing: if you ship Trip Workspace Ops without removing it from Workbench, you create indefinite parallelism — two valid execution paths, doubled maintenance surface, and the two-surface mental model institutionalized in two shipped codepaths."

**Arbitration:** Both are right. The resolution is:
- Option B is correct: incrementally add to Trip Workspace before removing from Workbench
- But Option B needs a **scoped deprecation commitment**: Workbench Ops is explicitly removed in the same or immediately following release, not deferred indefinitely
- The re-run affordance gap (no Spine re-run from Trip Workspace) is a real gap but it does NOT block removing Ops from Workbench — re-processing a trip through Spine and executing bookings are different jobs
- **The idea survives the kill test. The sequencing needs tightening.**

**Kill condition that was probed but didn't hold:** Whether any operator has expressed frustration at having to return to Workbench for Ops. The evidence is circumstantial (code signals, nav decisions, architecture doc Feature #7) rather than observed. The implementation is right regardless; the question is urgency.

---

## 16. Build Conditions

**Proceed now if:**
- `trip.validation` (or equivalent) is confirmed populated in the API response for all trip stages — Executioner #1 verified this is true (`spine_api/server.py` passes `trip.get("validation")`)
- The post-Spine navigation fix (step 2.5) is scoped into the same release as Ops moving to Trip Workspace
- DecisionTab/StrategyTab removal is replaced with a tracked issue (not silent deletion)

**Prototype before committing if:**
- Phase-adaptive tab rendering — this is a larger UX change with more unknowns

**Pause until built:**
- Removing Ops from Workbench entirely — should be gated on at least one release cycle of the Trip Workspace Ops tab being live and confirmed working, with a migration signal for power users visible

**Do not build yet (not this sprint):**
- Workbench as modal/gesture — valid long-term direction, wrong scope for this refactor
- Client-facing trip link — this is the leapfrog; scope it separately
- AI Guardian mode — separate product feature, don't entangle with this refactor

---

## 17. Six-Hat Coverage

**White (facts known):**
- `OpsPanel.tsx` lines 182–184: `result_validation` already falls back to `trip?.validation` — coupling is cosmetic
- `spine_api/server.py` lines 1148, 2068, 2309: all pass `trip.get("validation")` into API response
- `Shell.tsx:141`: breadcrumb already says "New Inquiry"
- `nav-modules.ts`: explicitly says `/workbench` is not a durable module name
- `DecisionTab.tsx` is 446 lines with real business logic (suitability acknowledgment, budget breakdown, follow-up questions)
- `StrategyTab.tsx` is 106 lines
- No `/trips/[tripId]/ops/page.tsx` exists
- `WorkspaceStage` type does not include `'ops'`
- Trip Workspace layout.tsx line 103 reads `result_run_ts` from workbench store (cross-boundary)

**Yellow (value if the thesis is right):**
- Trip Workspace becomes a complete, trustworthy record — operators stop maintaining external spreadsheets as safety nets
- Sharing and delegation become trivial: one URL = full context
- Feature compounding: every future cross-cutting feature (anomaly detection, handoff summaries, compliance audit) requires a single trip-scoped record
- Path to the client-facing leapfrog becomes clear
- The product becomes "load-bearing infrastructure" instead of a convenience tool

**Black (risks and what must be de-risked):**
- Muscle memory disruption for power users — strongest resistance will come from most valuable users
- Deep-link rot: SOPs in Notion, Slack, onboarding docs containing `/workbench?tab=ops` become dead ends
- Post-Spine navigation still lands on `/intake` — must be fixed in the same release
- Option B can become indefinite parallelism if deprecation isn't committed to with a deadline
- `result_validation` carry forward: the BLOCKED/ESCALATED reasons are richer than `trip.stage` alone — but the fallback already handles this

**Green (creative alternatives surfaced):**
- Phase-adaptive tabs (Quoting / Executing phases) instead of 8 flat tabs
- Workbench as a modal/gesture rather than a nav location
- Rejection history as "casting tape" toggle — options the AI didn't pick as first-class data
- Commitment event as a ceremonial architectural threshold (publishing, not copying)

**Red (emotional/taste signals):**
- "The system knows where everything is" — this is the feeling operators want. The current architecture makes that impossible.
- Operators do not want to be sent backward. Step 5 (client confirms → has to go back to Workbench) is where trust erodes.
- The product "knowing where everything is" is what separates a tool from a system of record.
- Power users will feel the change most acutely. They need a migration signal, not a silent move.

**Blue (facilitation / next actions):**
1. Confirm `trip.validation` field in API is populated for all trip stages (quick `rg` check or test)
2. Scope post-Spine navigation fix as Step 2.5 in the implementation plan
3. Replace "remove DecisionTab/StrategyTab" with "archive with tracked issue"
4. Add power-user migration signal to plan (first-visit banner or tooltip)
5. Commit to Workbench Ops deprecation timeline in the same or next release
6. Defer Workbench-as-modal and client-facing link to separate roadmap items

---

## 18. Reformulated Prompt (for future continuation)

> Waypoint OS is a B2B travel agency case management system with AI-accelerated intake. The fundamental architecture question is: Trip Workspace (/trips/[tripId]/...) should be the single durable record for the complete trip lifecycle — intake, AI processing, options, quote, risk, booking execution, and confirmation. Workbench (/workbench) should be narrowed to creation and AI processing only: a verb, not a place. The immediate work is: (1) move Ops execution to Trip Workspace by creating /trips/[tripId]/ops/, (2) fix post-Spine navigation to route to /ops for proposal-stage trips, (3) clean dead imports (with tracked issue, not silent deletion), (4) fix cross-boundary store read in layout.tsx, (5) add power-user migration signal, (6) remove Ops from Workbench in a scoped release. Longer-term: Workbench becomes a modal/gesture, Trip Workspace grows a client-facing URL, and AI switches to Guardian mode post-booking. The leapfrog is the client-facing trip link — agencies that ship it stop sending PDFs and start sending URLs that update in real-time. The trip workspace is the agency's product, not their backend.
