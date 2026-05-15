# Roles Index: Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?
**9 roles — quick reference to each agent's thesis, axis, and top 3 insights**

Full synthesis: `Docs/brainstorm/TRIP_WORKSPACE_OPS_MASTER_RECORD_BRAINSTORM_2026-05-14.md`
Implementation plan: `Docs/status/TRIP_WORKSPACE_OPS_NEXT_SLICE_PLAN_2026-05-14.md`
Brainstorm brief: `Docs/brainstorm/OPS_NEXT_BRAINSTORM_BRIEF_2026-05-14.md`

---

## Role 1 — Operator
**File:** `ROLE_OPERATOR_OPS_NEXT_2026-05-14.md`
**Axis:** What does this page feel like to actually use under pressure?

**Thesis:** Ops should be the single place where a 3-person agency can hand a trip to any team member on a Monday morning and have that person know exactly what to do next, what is already confirmed, and what will blow up by Friday if nobody acts.

**Top 3 insights:**
1. The ops page is currently a status dashboard, but operators need a decision surface — every operator action not made explicit in the UI is a thing that gets forgotten on a Friday afternoon.
2. Document trust is the real bottleneck, not document presence — operators need provenance ("this passport was accepted by agent on May 12, confidence 94%, name matches booking data"), not just presence.
3. The confirmation diff is the single highest-leverage quality guard in the system — catching a hotel room type mismatch at confirmation time vs. at check-in is the difference between a phone call and an emergency rebooking.

**What to build next:** `computeNextActions()` pure function → `NextActionsBar` component, seeded with 4 rules (missing DOB, pending document review, deposit overdue, blocked task)

**Surprising idea:** Trip Handoff Brief — one-click printable summary: last 5 timeline events, open tasks, unresolved confirmations, payment status, who is now responsible.

---

## Role 2 — Skeptic
**File:** `ROLE_SKEPTIC_OPS_NEXT_2026-05-14.md`
**Axis:** What is the specific structural risk that makes this page go wrong?

**Thesis:** The current Ops page is a good technical scaffold disguised as a product surface — it faithfully stores data but gives operators no signal about what actually needs to happen right now, and the path to "overbuilt, ignored, or dangerous" is short if the next slices follow the same accumulation logic.

**Top 3 insights:**
1. The Ops page conflates "have the data" with "know what to do with the data" — data and action guidance are not the same thing; every section added without an action model makes the page more informative and less useful.
2. In a small agency, the danger is not missing features — it is silent data corruption — the 409 guard, provenance badge, and extraction conflict warning are the three most important things on the page.
3. The extraction UI's manual traveler-document matching is the most likely source of the first serious operator error — three sequential decisions (which fields, which traveler, overwrite or not) on a 4-traveler trip while handling three other trips simultaneously.

**What to build next:** Blocked-task surface + Next Action header (synthesizes existing state, zero new endpoints); collection link re-expose fix (~15 lines in sessionStorage).

**Surprising idea:** "Changes since your last visit" callout at page open — operators process the delta, not the full state.

---

## Role 3 — Executioner
**File:** `ROLE_EXECUTIONER_OPS_NEXT_2026-05-14.md`
**Axis:** What should be killed, what should be kept, and what specific code bugs are already in flight?

**Thesis:** Ops must become the single, ordered checklist that tells one operator exactly what to do next, and makes every past action auditable without requiring them to read a log.

**Code bugs identified:**
- `extractionSelections`/`extractionConflicts` never cleared on `handleDocDelete` → session-lifetime memory leak
- `handleSave` atomically writes travelers + payment_tracking → unnecessary 409 surface, independent concerns
- `mode='documents'` with 34 guards — all 34+ state vars initialize regardless of mode
- `useReducer` comment at line 176 is wrong: `editing + conflict + saving + error + bookingData` are tightly coupled atomic transitions, not independent slices

**Top 3 insights:**
1. The booking execution lifecycle has two distinct phases that Ops conflates: Phase A (data collection) and Phase B (booking execution). Auto-collapsed completed Phase A sections let operators focus on Phase B.
2. The highest-value AI feature is already built but under-leveraged — extraction pipeline should be a first-class "Data from Documents" workflow card, not a button on a list item.
3. The timeline is the most undervalued section — the only source that answers "how did we get here?" — but rendered as a footnote.

**Kill list:** Sub-tabs, confirmation diff (no structured join key), tasks from quote (unstructured prose), traveler-organized documents (type-grouped is better for operator workflow — sole dissenter on this)

**Surprising idea:** Presence indicator on collection link — "Customer viewed link 4 minutes ago" from token access logs already recorded.

---

## Role 4 — Cartographer
**File:** `ROLE_CARTOGRAPHER_OPS_NEXT_2026-05-14.md`
**Axis:** What is the correct spatial organization of this surface?

**Thesis:** Ops should be a spatially-organized booking execution master record where an operator can, in a single downward reading pass, answer: "what is blocking this trip right now, and what do I do next?"

**Proposed layout (4 zones):**
- Zone 1 — Command Strip (always visible, non-scrolling): trip name, readiness pulse, payment chip, pending submission pill
- Zone 2 — Data Intake: 2A Collection Link → 2B Pending Submission → 2C Booking Details (one contiguous workflow)
- Zone 3 — Documents: grouped by traveler (per-traveler accordion + Trip Documents)
- Zone 4 — Execution: Tasks | Confirmations | Timeline as tabs (sole role to advocate sub-tabs, for these three panels only)

**Top 3 insights:**
1. Readiness is a diagnostic, not a workflow driver — it should be a summary chip in the Command Strip, not the primary page frame.
2. Collection link + pending submission + booking details are one workflow masquerading as three sections — spatially cohering them surfaces existing logic without adding features.
3. The timeline is an audit instrument, not a history decoration — making it accessible via a tab in Zone 4 changes what it signals to the operator.

**Surprising idea:** Cmd+Shift+S copies current trip status as a natural-language paragraph for client calls — no new API, pure state synthesis.

---

## Role 5 — Strategist
**File:** `ROLE_STRATEGIST_OPS_NEXT_2026-05-14.md`
**Axis:** What is the correct long-term product architecture?

**Thesis:** Ops must become the operator's single source of execution truth — where every booking decision, data handoff, payment event, and supplier confirmation is stamped, sequenced, and auditable — so a 3-person agency operates with the institutional memory of a 20-person operation.

**Top 3 insights:**
1. Ops is a state machine, not a form — the real product question is "what state is this trip in, and what are the valid transitions from here?" The Next Action banner is the interface making the state machine visible.
2. Auditability is a product feature, not a compliance artifact — every audit feature is a sales feature; agencies that can reconstruct events win disputes with suppliers and customers.
3. The collection link is the customer relationship touchpoint — it is the moment the agency relationship becomes professional or amateur; treat link management with the UX care of a CRM action.

**Proposed slices:** Next Action Banner (1–2 days) → Payment Status Card extracted from edit form (1 day) → Per-traveler documents (2–3 days) → Confirmation vs. quote diff indicator (3–4 days, deferred) → OpsPanel decomposition (2 days, architectural prerequisite)

**Surprising idea:** Make the Execution Timeline the primary coordination primitive — not the bottom appendix, but the spine that every other section attaches to.

---

## Role 6 — Archivist
**File:** `ROLE_ARCHIVIST_OPS_NEXT_2026-05-14.md`
**Axis:** What does a defensible, legally-sound chain-of-custody record look like?

**Thesis:** Trip Workspace Ops should become the immutable chain-of-custody record for every decision, approval, data change, and money movement made on behalf of a trip — a surface that makes the operator's past actions as legible as their next ones.

**Critical missing pieces:**
- No timestamp/actor on operator decisions (Accept/Reject on submissions, document accept)
- Payment is a flat blob — no per-obligation rows with deadlines linked to suppliers
- No "who was responsible" attribution visible on any action
- Timeline is read-only — cannot annotate events, cannot flag discrepancies

**Top 3 insights:**
1. The gap between data entry and accountability is exactly one timestamp and one actor — every important decision is captured in the backend already; it's just not durably attributed in the UI.
2. Documents without traveler ownership are just files — grouping by traveler changes the question from "what files do I have?" to "is this traveler travel-ready?"
3. Confirmation diff is the most high-stakes missing feature — catching booking errors at confirmation rather than check-in is the difference between a phone call and an emergency.

**Immutability principle:** Operators cannot delete timeline entries. They can only annotate.

**Surprising idea:** Time capsule note — written by operator at booking handoff, locked and surfaced when the trip re-enters view for post-travel review or dispute.

---

## Role 7 — Future Self
**File:** `ROLE_FUTURE_SELF_OPS_NEXT_2026-05-14.md`
**Axis:** With 2 years of hindsight (writing from 2028), what were the right and wrong calls?

**Thesis:** Ops must stop being a collection of independent panels bolted together and become a single, opinionated execution dashboard whose job is to answer one question at every moment: "What stands between this trip and a successful booking, and who needs to act right now?"

**2028 hindsight insights:**
1. The provenance chain from document to booking record became the product's defensible moat — `bookingDataSource` felt like a minor UX nicety in 2026; by 2028 it was the most-cited feature in agency sales conversations.
2. Agencies that scaled from 3 to 12 people did it by making junior staff capable of handling booking execution — not by hiring more senior travel agents. The Next Action card gave junior coordinators a script.
3. Keeping payments as tracking-only in 2026 was the right call — teams that built Stripe integration in 2026 spent Q1 2027 rebuilding it for Razorpay, bank transfer, and corporate card reconciliation.

**What not to build:** Sub-tabs (deferred until month 12+), client portal, automated supplier communication, multi-currency conversion.

**Surprising idea:** Booking task list as an operator execution fingerprint — task completion patterns become a per-operator quality signal for mentorship and early detection of junior coordinator errors.

---

## Role 8 — Champion
**File:** `ROLE_CHAMPION_OPS_NEXT_2026-05-14.md`
**Axis:** What is the maximum value version, and what is the right path to it?

**Thesis:** Trip Workspace Ops should become the single authoritative execution cockpit where a three-person agency can run the full booking lifecycle — data collection, document verification, supplier payment deadlines, task execution, and confirmation auditing — without ever switching to a spreadsheet, a WhatsApp thread, or a supplier portal.

**Top 3 insights:**
1. The extraction pipeline is a competitive moat, not a document feature — upload → AI extract → field-level confidence → human review → selective apply → conflict resolution → audit trail is the feature that lets a 3-person agency move at 10-person speed.
2. The booking task state machine is already half of a project management tool that doesn't need to become one — connecting tasks to accepted quote and readiness assessment closes the feedback loop without building Jira.
3. The timeline is the most underutilized asset on the page — a "since last visit" highlight, actor filter, and severity indicator would make it a proactive daily-check tool at near-zero cost.

**Surprising idea:** Collection link expires on stage advancement, not time — auto-revoke when operator accepts all data and advances to booking stage; creates a natural moment of finality for the customer.

---

## Role 9 — Trickster
**File:** `ROLE_TRICKSTER_OPS_NEXT_2026-05-14.md`
**Axis:** What frame is everyone using that is wrong?

**The metaphor:** The current Ops page is a *chart room* — it contains everything. The WHO Surgical Safety Checklist is an *execution gate*. The Ops page is trying to be both at the same time. That is why it is 1399 lines and growing.

**Thesis:** Trip Workspace Ops should become a time-sequenced execution gate — not a data-management interface — where the operator's single question at any moment is "what must be true before I press the next button, and is it true right now?"

**Proposed layout (flight deck metaphor):**
- Zone 1 — Primary Flight Display: Next Action bar (one sentence, one button)
- Zone 2 — Navigation Display: Data (A), Payments (B), Documents (C), Tasks (D) — four collapsible strips
- Zone 3 — Overhead Panel: Confirmations + Timeline (consulted on demand, not on every scan)

**Top 3 insights:**
1. Readiness is not the top of the page; it is the input to the top of the page — the tier breakdown is a diagnostic that produces a single output: the next action.
2. The document flat list is not an organization problem; it is a traveler model problem — `BookingDocument` has `document_type` but no enforced `traveler_id`; grouping without that change is approximate and will mislead.
3. The 7-status task state machine is the latent core of the product — everything else (data, documents, payments, confirmations) should be framed as preconditions to supplier bookings, not independent sections.

**Surprising idea:** Hand Off button — generates a frozen read-only snapshot at the moment of handoff: last 24h timeline events, next action, deferred decisions, who is now responsible. All data already exists. Button costs almost nothing.

---

## Convergence Summary

| Question | Answer | Roles agreeing |
|----------|--------|----------------|
| Next Action Banner — build it? | YES — highest ROI next build | 9/9 |
| Sub-tabs — build now? | NO — premature; fragments context | 8/9 (Cartographer alone says yes for Zone 4 panels) |
| Traveler-grouped documents? | YES — but requires `traveler_id` on `BookingDocument` first | 8/9 (Executioner prefers type-grouped) |
| Confirmation diff — build now? | NO — no structured itinerary join key | 6/9 (Champion, Archivist, Future Self want it but same dependency) |
| Tasks from accepted quote? | NO — accepted quote is unstructured prose; defer | 5/9 |
| Payment `final_payment_due` field? | YES — simple field addition, high temporal value | 7/9 |
| Separate payment save from traveler save? | YES — decouple `handleSave` | 7/9 |
| `extractionSelections` memory leak — fix? | YES | 9/9 (Executioner explicit; all imply correctness) |
| Timeline annotability + immutability? | YES (near-term) | 6/9 |
| Payment processing integration? | NO — tracking-only constraint is correct | 9/9 |
| Client portal features inside Ops? | NO — separate trust boundary | 9/9 |
