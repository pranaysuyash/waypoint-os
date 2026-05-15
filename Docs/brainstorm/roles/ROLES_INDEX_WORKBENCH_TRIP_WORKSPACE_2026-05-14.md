# Roles Index: Workbench / Trip Workspace Architecture Split
**Date:** 2026-05-14 (~16:00)
**Topic:** Should Workbench narrow to creation+AI processing? Should Trip Workspace own Ops?
**9 roles — quick reference to each agent's thesis, axis, and top insights**

Full synthesis: `Docs/brainstorm/BRAINSTORM_WORKBENCH_TRIP_WORKSPACE_2026-05-14.md`
Brainstorm brief: `Docs/brainstorm/WORKBENCH_TRIP_WORKSPACE_BRAINSTORM_BRIEF_2026-05-14.md`

**Decision:** YES — move Ops to Trip Workspace. Option B. Sever Workbench coupling. Commit to deprecation in same or next release.

---

## Role 1 — Operator
**File:** `ROLE_OPERATOR_2026-05-14.md`
**Axis:** What does the current split feel like to use under pressure?

**Thesis:** The trip lifecycle has one natural home — Trip Workspace. Workbench is a runway, not a destination. The hardest moment in the operator's day is Step 5: the client says yes, execution begins, and the tool sends you backward.

**Workflow map:** 7 steps from Inquiry to Confirmation. The critical break is Step 5 — "Client confirms, booking execution begins" — where the operator must navigate away from Trip Workspace back into Workbench to reach Ops.

**Top 3 insights:**
1. The current model treats Ops as a creation activity — it isn't. Ops is record-keeping and coordination. It belongs in the durable record.
2. Once a trip leaves Spine, it should live entirely in Trip Workspace. Workbench is a runway.
3. The hardest moment is Step 5. That backward navigation is where trips go wrong.

**The thing most people miss:** The operator's anxiety isn't about features — it's about not knowing what they forgot. The product's real job is to surface the one thing the operator would have missed at 6pm on a Friday.

---

## Role 2 — Skeptic
**File:** `ROLE_SKEPTIC_2026-05-14.md`
**Note:** Two independent agents ran; composite documented.
**Axis:** What is the specific structural risk that makes this refactor create new problems?

**Top risks found:**
1. "View Trip" navigation lands on `/intake`, not `/ops` — no entry point to Ops in Trip Workspace after refactor; operators who learned "Workbench has an Ops panel" will not know to look for the Ops tab
2. `DecisionTab.tsx` (446 lines) and `StrategyTab.tsx` (106 lines) are not dead code — they are staged/deferred business logic; deleting them based on "not imported" loses 552 lines of non-trivial logic
3. `result_validation` carries BLOCKED/ESCALATED semantics that `trip.stage` alone cannot reproduce (NOTE: this was subsequently invalidated by Executioner #1 — `trip.validation` fallback already works)

**What to cut:** Don't call Option B "zero risk." Defer DecisionTab/StrategyTab deletion until purpose is clear. Commit to Workbench Ops deprecation in the same release (not a "someday" deferred item).

**Strongest skeptical point:** Architectural reorganization hurts power users most — they've automated the old pattern and will be disoriented.

---

## Role 3 — Executioner
**File:** `ROLE_EXECUTIONER_2026-05-14.md`
**Note:** Two independent agents ran; both verdicts documented.
**Axis:** What survives the kill test, what is killed, what code facts change the analysis?

**Executioner #1 — Code-Grounded Kill Test:**
Critical finding: `trip.validation` fallback ALREADY EXISTS in OpsPanel at lines 182–184. The `useWorkbenchStore()` coupling is cosmetic, not structural. The entire "this is hard to decouple" framing is wrong.

Verdict: **The idea survived the kill test.** The coupling concern is addressed.

**Executioner #2 — Sequencing-Grounded Kill Test:**
Critical finding: Option B as staged ("ship Option B now, remove from Workbench someday") guarantees permanent parallelism. Day 1: familiar. Day 30: two valid execution paths. Day 90: Workbench never dies.

Verdict: **Kill Option B's sequencing; keep the direction.** Commit to deprecation now, not later.

**Arbitration:** Both agree on direction. Executioner #1 lowers technical risk (coupling already handled). Executioner #2 raises organizational risk (sequencing creates parallelism). Resolution: Option B with committed Workbench deprecation in same or next release.

---

## Role 4 — Cartographer
**File:** `ROLE_CARTOGRAPHER_2026-05-14.md`
**Note:** Two independent agents ran; composite documented.
**Axis:** What is the correct spatial organization across three altitudes (sidebar → trip list → trip workspace)?

**Navigation model (three altitudes):**
- Altitude 1 — Sidebar: stage-grouped pipeline (LIVE PIPELINE: Trips●3, Lead Inbox●2, Quote Review●1 / RECORDS: Documents, Bookings, Payments / INTELLIGENCE: Insights, Audit)
- Altitude 2 — Trips Dispatch Board: stage badge (WHERE in lifecycle) + attention dot (WHAT it needs from you now) as two separate visual channels. These are orthogonal.
- Altitude 3 — Trip Workspace: smart entry by stage (BOOKING → Ops tab, CONFIRMED → Timeline tab)

**Top 3 insights:**
1. Stage and attention demand are orthogonal — give them separate visual channels. A BOOKING-stage trip can be red (needs action now) or green (executing fine).
2. Counts before names — `Trips (●3)` means "3 need your attention" before you read any trip name.
3. Creation is a mode, not a location — New Inquiry should feel like opening a camera (transient, purposeful, closes when done), not navigating to a room.

**The thing most people miss:** Persistent things get sidebar slots. Moving things get a dispatch board with live state. Putting "Workbench" in the sidebar treats a moving thing as if it persists.

---

## Role 5 — Strategist
**File:** `ROLE_STRATEGIST_2026-05-14.md`
**Axis:** What does the correct long-term product architecture look like, and which current decisions constrain or enable it?

**Product identity thesis:** Most tools organize around documents (itineraries, proposals, invoices). Waypoint OS's implicit bet is it organizes around the trip as a living record with state. This is a fundamentally different product. The architecture must expose that bet loudly.

**Time horizons:**
- 6 months: Move Ops into Trip Workspace. Sever Workbench coupling. Redirect /workbench to /inquiries/new.
- 12 months: Phase-aware tab rendering. Trip record becomes single source of truth.
- 24 months: Auditable compliance record for TICO/ASTA/ATOL. Every AI extraction, human override, and payment event timestamped and attributable.
- Leapfrog: Trip record as structured data enables cross-agency benchmarking — supplier reliability, margin by destination, booking lead-time patterns.

**Top 3 insights:**
1. Retire Workbench as a destination — it is an implementation artifact, not a mental model.
2. Phase-adaptive Trip Workspace tabs — complexity that appears at the right moment feels like intelligence; always-visible complexity feels like clutter.
3. Ops as a compliance artifact, not just a task list — the long-term moat is structured, auditable trip history that agencies cannot reconstruct from email threads.

---

## Role 6 — Archivist/Outsider (Gemini)
**File:** `ROLE_ARCHIVIST_OUTSIDER_GEMINI_2026-05-14.md`
**Note:** Run via Gemini — no codebase access, fresh external perspective.
**Axis:** What does good memory design look like, and what assumptions are we treating as obvious that are actually suspect?

**Archivist thesis:** Trip Workspace must be the Single Source of Truth. Workbench should be a Layer of Interpretation, not a separate room. Every moment information lives in a Workbench draft and not in the Trip Record, it is losing value.

**Outsider challenges:**
- "The Trip is the unit of work" → CHALLENGED: The Relationship is the unit of work. The trip is just a chapter.
- "Agents want a Durable Record" → CHALLENGED: Agents want Zero Liability. The record is for "covering their ass," not just "remembering."
- "Execution is the end of the cycle" → CHALLENGED: Execution is a recursing loop. "Booked" means "waiting for the airline to cancel."

**Top 3 insights:**
1. Workbench as a State, Not a Place — switching between AI Processing and Ops Execution should feel like switching a lens, not walking into a different building.
2. The Draft is Technical Debt — every moment information lives in a Workbench draft it is losing value.
3. Synthesis is the Product — agents' value is verifying the work, not doing it; optimize for Rapid Verification.

---

## Role 7 — Future Self
**File:** `ROLE_FUTURE_SELF_2026-05-14.md`
**Axis:** What does the product look like from 2028, and which 2026 decisions determined the outcome?

**2028 hindsight:** No clear winner among the three predicted options. What actually happened was a collapse and merge — Workbench shrank from a surface into a gesture (a hotkey, a sidebar flash) as AI latency dropped below 400ms. The products that shipped "two surfaces" and kept them equal-weight mostly died in 2026 acquisition rounds.

**Leapfrog move:** The agencies that opened a read-only (then editable) trip portal to clients — where clients could see the itinerary, approve options, drop in passport details — 3x'd their close rate and cut email volume by 60%. The trip workspace became the agency's product, not their backend.

**What kept optionality open:**
- Making Trip Workspace the durable record (products that stored canonical state in a processing artifact couldn't later make the workspace client-facing without a full rewrite)
- Modeling booking execution as operations inside the trip, not as a separate workflow engine

**The thing most people miss:** The independent travel agency's core anxiety isn't efficiency — it's that they'll lose a client to a larger shop that looks more professional. Waypoint OS is a credibility amplifier.

---

## Role 8 — Champion
**File:** `ROLE_CHAMPION_2026-05-14.md`
**Note:** Two independent agents ran; composite documented.
**Axis:** Why is the two-surface model wrong, and what does the single durable home unlock?

**Thesis:** The split is a cognitive jurisdiction problem. When an operator closes a booking, they need to see client request, itinerary, supplier confirmations, payment state, and next action — simultaneously. Splitting execution from record forces the operator to maintain a mental join table.

**The product's own code is voting:** Shell.tsx hides "Workbench" already. Nav doc calls it "New Inquiry." `completedTripId` pushes to Trip Workspace. The architecture is lagging behind the product's own expressed intent.

**Top 3 arguments:**
1. The product already voted — small daily decisions have been slowly renaming this surface to something more honest.
2. Ops is permanent state, not session state — it was never right to put it in Workbench; booking execution is a business record that belongs to the trip.
3. One URL, one truth, one operator workflow — gains: shareability, delegation, bookmarking, feature coherence, reduced cognitive overhead.

**The thing most people miss:** When a tool doesn't have a single authoritative place for a record, operators don't trust any of its places. They keep their own spreadsheets. The tool becomes a convenience, not a system of record.

---

## Role 9 — Trickster
**File:** `ROLE_TRICKSTER_2026-05-14.md`
**Axis:** What frame is everyone using that is wrong?

**The right metaphor: The Chrysalis.** Inside a chrysalis, the caterpillar dissolves completely — liquefied, structureless — before reorganizing. There is no continuous thread of "the caterpillar becoming." This reframes the handoff from an organizational problem into an ontological one: the trip is a new thing that was summoned by the Workbench, not a continuation of it.

**5 architectural metaphors:**
1. Kitchen/Dining Room — opposite emotional contracts; opposite jobs
2. Casting Session/Stage Production — the handoff should feel ceremonial, not accidental; that ceremony is the real bug
3. Compost Heap/Garden — Workbench should be allowed to decay; don't serve dinner from the compost heap
4. Flight Plan/Cockpit — deviations from the AI plan should be explicit, not silent overwrites
5. Chrysalis/Butterfly — the handoff event should be architecturally irreversible; "promoting" should feel like publishing

**Surprising idea:** Show every rejected option as strike-through ghost text in Workbench — every flight that didn't make it, every hotel the AI considered and dropped. Trip Workspace shows only what was "cast." A single "show auditions" toggle surfaces the full casting tape. Rejection history as first-class data.

**The thing most people miss:** The problem isn't that the two surfaces overlap — it's that the system has no moment of commitment. Without a clear threshold event, everything stays hypothetical forever.

---

## Convergence Summary

| Question | Answer | Agreement |
|----------|--------|-----------|
| Should Ops move to Trip Workspace? | YES | 9/9 |
| Is the `useWorkbenchStore` coupling a structural blocker? | NO (fallback exists) | Executioner #1 + code evidence |
| Does Option B risk permanent parallelism? | YES (without deprecation commitment) | Executioner #2 |
| Should Workbench Ops be deprecated in the same or next release? | YES | Executioner #2, Skeptic |
| Should DecisionTab.tsx and StrategyTab.tsx be deleted? | NO — defer, add `// DEFERRED` comment | Skeptic, Strategist |
| Is Workbench the right long-term destination for any trip work? | NO — reduce to creation + AI re-processing | 9/9 |
| What is Waypoint OS's product identity? | Case management system with AI-accelerated intake | Strategist, Champion |
