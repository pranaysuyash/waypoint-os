# Brainstorm Role: Skeptic — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-Sentence Thesis

The current Ops page is a good technical scaffold disguised as a product surface — it faithfully stores data but gives operators no signal about what actually needs to happen right now, and the path to "overbuilt, ignored, or dangerous" is short if the next slices follow the same accumulation logic.

---

## 2. What the Current Ops Page Gets Right

- **Data provenance is tracked.** The `bookingDataSource` badge (`customer_accepted` vs `agent`) solves a real trust problem: operators need to know whether the passport data came from the traveler or was keyed in by someone who eyeballed a WhatsApp photo. This is genuinely valuable and not obvious.
- **Optimistic-conflict detection exists.** The 409 `updatedAt` guard on `handleSave` is the right instinct. In a 1–5 person agency where two people might touch the same trip, silent overwrites would corrupt data that was legally obtained.
- **Pending review is surfaced prominently.** The amber-bordered customer submission block is correctly treated as a hot item. An operator glancing at Ops knows immediately that customer data is waiting.
- **Documents, extraction, and apply are in one flow.** The round-trip from upload → extract → select fields → apply-to-traveler is coherent. An operator doesn't need to leave the panel to populate traveler data from a passport scan. That is genuinely useful for a small agency.
- **Stage-gate enforcement exists.** Showing Ops only at proposal/booking stage is architecturally correct — the gate prevents operators from acting on booking tasks for a trip that hasn't been accepted yet.
- **Status machine has the right vocabulary.** The 7-state machine (`not_started / blocked / ready / in_progress / waiting_on_customer / completed / cancelled`) reflects real booking workflows. These aren't invented; they match what a supplier-facing ops person actually does.

---

## 3. What It Gets Wrong

**The layout teaches nothing.** Open OpsPanel fresh on a booking-stage trip with 4 travelers and 6 documents. The page renders: readiness tiers at top, then booking data, then collection link, then documents (flat list), then BookingExecutionPanel, then ConfirmationPanel, then ExecutionTimelinePanel — seven distinct UI regions stacked in a single scroll. There is no hierarchy of urgency. Readiness details (tier breakdowns with `met`/`unmet` lists) are visually similar to the payment tracking block, which is visually similar to a document row. Everything is the same weight. An operator cannot tell if the trip is 15 minutes from ready-to-book or three weeks away without reading every section.

**The readiness section is structurally backwards.** It shows `highest_ready_tier` as a small label, then expands into full tier detail, then a missing-fields block, then a signals block. The signal-to-noise ratio is inverted: the most actionable thing (what is specifically blocking the next tier) is buried two blocks below a verbose tier table. A new-hire will read the tier table before they reach the blocking field names.

**Payment tracking is embedded in the wrong data model.** `payment_tracking` lives inside `BookingData` alongside traveler records. In the edit form (line 926–1000), changing a traveler's DOB and updating the payment reference are in the same save operation. This means a conflict on payment (someone else marked it `deposit_paid`) will block you from saving a corrected traveler name, or vice versa. These are independent concerns with different actors and different urgency. Conflating them is a data integrity risk waiting to be triggered.

**Documents are a flat list with no assignment.** The document list (line 1148–1390) shows `[type] · [ext] · [size] · [status]` for every document. On a 4-traveler trip with passports, visas, and insurance docs, this renders as 8–12 rows of identical-looking items. The extraction UI that follows each accepted document is visually identical for every document — there's no orientation cue indicating which document's extraction panel you're in. An operator rushing to process a same-day booking could apply a passport extraction to the wrong traveler. The traveler-selector dropdown (line 1299–1317) requires the operator to correctly identify and match — entirely from memory — which `traveler_id` maps to which person.

**The extraction UI exposes operator error as the happy path.** The "Apply selected" flow requires the operator to: (a) check which fields to include, (b) pick the correct traveler from a bare `traveler_id` + `full_name` dropdown, (c) decide whether to overwrite conflicts. These are three sequential decisions, each requiring recall. The current implementation trusts operators not to make mistakes. In a 1-person agency doing 12 trips simultaneously on a Thursday afternoon, this is where data corruption happens.

**`mode='documents'` is a hidden sub-mode that is not discoverable.** OpsPanel accepts `mode='documents'` (line 44) and suppresses all non-document rendering with `documentsOnly` guards (34 occurrences). This mode exists for a `/documents` module that is deliberately staged-and-disabled (line 1132–1133). This is a feature that was spec'd, partially built, disabled, and left structurally embedded in a 1,399-line component. It will confuse future developers and is an unremovable landmine in the component interface.

**The collection link section solves a UI state problem awkwardly.** When `linkInfo` is null but `linkStatus.has_active_token` is true (line 1038), the operator sees "Active link exists (expires…). Generating a new link will revoke the old one." But they have no way to retrieve or display the existing URL — it was generated in a previous session and not re-exposed. So an operator who already sent a link to the customer, comes back the next day, and wants to verify the link is still valid, is told "there's an active link" with no URL. They have to decide whether to revoke it and generate a new one, which invalidates the link the customer already received. This is a real workflow failure that will happen repeatedly.

**The timeline is a passive afterthought.** `ExecutionTimelinePanel` is rendered last, below confirmations, with no interaction affordances. It will be ignored. Timeline events are actor-typed but the component is never described — from reading the import, there is no indication whether it shows operator edits, system transitions, customer submissions, or all three. Without knowing this, operators won't scroll down to check it. It will accumulate data no one reads.

**There is no "done" state.** Nothing on the current page tells an operator this trip's ops work is complete. The 7-state machine can reach `completed`, but there is no trip-level ops completion signal, no congratulatory zero-state, no "all tasks done" indicator. An operator checking in on a completed booking will scroll all seven sections looking for the thing that still needs action. Nothing is visually distinguished between "nothing to do here, you're done" and "you haven't done anything yet."

---

## 4. The Top 5 Operator Decisions Ops Must Support

These are ranked by frequency and consequence, grounded in what I see in the data model:

1. **"Is this trip ready for me to actually send booking requests to suppliers?"**
   The answer lives in readiness tiers + booking task states + traveler completeness. Currently it requires synthesizing three sections. The operator should be able to see this in one glance.

2. **"Is the customer's data complete enough that I can start booking?"**
   Specifically: do I have all travelers' full names, DOBs, and passport numbers? The current layout requires reading a table and cross-referencing with the readiness `unmet` list. These should be the same view.

3. **"Has the customer paid, and is what they paid consistent with what we agreed?"**
   The payment tracking section has `agreed_amount`, `amount_paid`, and a computed `balance_due`. But there is no alert when `amount_paid < agreed_amount` and a supplier deadline is approaching. Without that link, operators carry this context in their heads or spreadsheets — not here.

4. **"Which booking tasks are currently blocked, and what specifically is blocking them?"**
   BookingExecutionPanel has `blocked` status and presumably a reason field. But an operator does not need to scroll to the tasks section to find this — it should surface in the top of the page when any task is blocked.

5. **"Did the confirmation I received match what the customer was actually promised?"**
   ConfirmationPanel exists. Whether it has a diff mechanism against the accepted quote is unclear from this file (it's an imported component). But this decision — "did the hotel confirmation match what we sold?" — is high-stakes and happens on every booking.

---

## 5. Ideal Page Layout

**Section order with purpose:**

1. **Trip Header / Ops Status Bar** — one line: trip name, stage, a single ops health badge (`Action Required / In Progress / Complete`). Not a section, a persistent anchor. The operator knows where they are.

2. **Next Action Block** — conditional, shown only when something is pending. Exactly one primary action (e.g., "Customer submitted data — Review now" or "2 tasks blocked — See reason" or "Payment overdue"). Not a list of issues; one most-urgent prompt. If nothing is pending: "No action required. All tasks in progress or complete." This replaces the current readiness-empty notice and the scattered urgent states.

3. **Traveler Data + Readiness** — combined into one section. Per-traveler rows showing: name, DOB, passport, completeness indicator (green/amber/red). The readiness tier logic feeds the per-row indicators. Missing fields call out inline next to the traveler they belong to, not in a separate tier table below.

4. **Documents** — organized by traveler, not by flat list. Each traveler has their own document group. An operator processing Adult 1's passport upload sees only Adult 1's documents in that group. The extract/apply flow stays in this section, but the traveler is pre-determined by the group context — removing the manual selection error.

5. **Payment** — a standalone section, not embedded in booking data. Shows agreed / paid / balance due. Links to a supplier deadline if one exists on any booking task. Editable independently from traveler data.

6. **Booking Tasks** — BookingExecutionPanel, unchanged in function. Elevated in position: above confirmations. Blocked tasks are visually prominent with the blocker reason.

7. **Confirmations** — ConfirmationPanel. Shows per-booking confirmations. If diff capability exists, surface it here.

8. **Customer Collection Link** — demoted to a utility section. Operators know where to find it when they need it; it doesn't need high placement after initial link generation.

9. **Timeline** — remains last, but with section-level summary: "N events in the last 7 days." If the summary is non-trivial, operators will scroll in. If it's empty, they won't waste time.

---

## 6. What to Build Next

**Slice: Blocked-Task Surface + Next Action Header**

Concrete implementation:
- Add a `nextAction` derived value to OpsPanel computed from: pending customer data (`pendingData != null`), any blocked booking tasks (query BookingExecutionPanel state or add a count-of-blocked-tasks API response), and payment `overdue` status. Show exactly one `<NextActionBanner>` component at the top of the page — dismissible only after the action is resolved, not arbitrary. This does not require new backend endpoints; it synthesizes existing state.
- Add a `blockedReason` field to the booking task API response if not already present. Surface it inline on blocked tasks. This is the #1 thing operators need to act on a stalled booking without calling the agent who set the task.
- Fix the collection link re-expose problem: store the last-generated URL in a cookie or sessionStorage keyed on `tripId + tokenId`. On reload, if `linkStatus.has_active_token` and the stored URL matches the `token_id`, display it. No new API needed. Cost: ~15 lines.

---

## 7. What Not to Build Yet

**Sub-tabs (Data / Documents / Payments / Tasks / Confirmations):** This is a trap. A 3-person agency does not benefit from tabs — they need everything on one screen to catch the one thing that fell through. Tabs create a situation where a critical action is "in the Payments tab" and gets missed during a fast pre-departure check. Build tabs only when the page is so populated it is genuinely unusable without them, and validate that with real usage data.

**Confirmation diff against proposed itinerary:** Conceptually appealing. In practice, the "proposed itinerary" lives in a Workbench AI-generated output that may be informal, multi-hotel, and written in prose. Building a reliable structural diff against supplier confirmation PDFs requires entity extraction, matching logic, and tolerance handling for name variations, dates, and rate plans. Doing this wrong produces false conflicts. False conflicts destroy operator trust faster than no diff at all. Build it only after the confirmation data model is stable and you have 20+ real confirmations to test against.

**Payment linked to supplier deadlines:** Valid idea; wrong time. The supplier deadline data does not appear to exist in the current data model — it would need to be added to booking tasks. That data needs to be reliably entered first (operators need a habit of setting deadlines on tasks before you can link payment alerts to them). Build deadline fields on booking tasks first, get operators to use them for one quarter, then surface the payment link.

**Traveler-organized documents with automatic extraction routing:** The per-traveler document grouping is the right end-state, but it requires knowing which document belongs to which traveler at upload time — either from the upload form or from extraction. The current upload form only asks for `document_type`, not `traveler_id`. Adding traveler assignment to upload is a 1-field change; making the extraction auto-route to the assigned traveler removes the dangerous manual dropdown. Do the upload-side change first; the extraction auto-route follows naturally.

**Client-facing ops features of any kind:** The collection link is as far as client-facing goes in this slice. Do not add a client-readable confirmation view, a client payment portal, or a client document portal to OpsPanel. These are separate surfaces with different trust boundaries, auth requirements, and design constraints. Building any part of them here contaminates the operator surface.

---

## 8. Risks / Failure Modes

**Payment-traveler coupling will produce data corruption.** When the same save operation handles both traveler records and payment tracking, a 409 conflict on one blocks the other. This will happen at the worst time: a payment update from one agent and a traveler correction from another, on the same trip, minutes before a booking deadline. The current 409 handling (line 347–353) shows a "reload" prompt and discards the in-flight edit. One of those edits will be lost.

**Document extraction + traveler selection is a high-frequency, low-safeguard action.** The "Apply selected" button (line 1346) applies extracted fields to a traveler with no confirmation dialog, no undo, and no audit diff shown before commit. The conflict dialog exists (line 1319) but only fires if the field already has a value. For an empty traveler record (the common new-trip case), an operator can apply the wrong passport's data to the wrong traveler with two clicks and no warning. The only recovery is the timeline, which they won't find until it's too late.

**The `mode='documents'` dead mode is a maintenance trap.** There are 34 `documentsOnly` guards in this component. Every future feature addition must decide: does this appear in documents mode? This creates a conditional explosion that is easy to get wrong. When the `/documents` module is eventually enabled, there will be a divergence in functionality between modes that no one will have tested. Either commit to enabling the documents module or remove the mode parameter and the 34 guards.

**The page is already at 1,399 lines and has no tests at the component level.** Adding sub-tabs, a Next Action header, per-traveler document grouping, and extraction auto-routing to a 1,399-line component will produce a component that is unmaintainable in 6 months. The architectural risk is that every new feature gets added here because "it's already in OpsPanel" — and the file becomes the graveyard of all Ops product ideas.

**Readiness tiers are only as good as the data feeding them.** The current readiness display faithfully shows `tier.met` and `tier.unmet` arrays. If the backend readiness assessment is stale (computed at a previous save, not recomputed on each load), an operator could see "Ready: tier 2" and proceed to booking, only to find the actual data is incomplete. There is no "readiness last computed at" timestamp visible to the operator. This should exist.

**The timeline has no operator affordance for adding context.** Actor-typed events are fine for audit. But operators routinely add notes like "called supplier, confirmed availability, ref #XYZ." Currently this goes in the payment notes field (wrong location), or in booking task notes (if that exists), or in a WhatsApp thread outside the system. The timeline will log system events and nothing the operator actually wants to record. Over time, the timeline will be accurate but contextually hollow.

---

## 9. Three Strongest Insights

**1. The Ops page conflates "have the data" with "know what to do with the data."**
The current page is a good data display. It shows booking data, payment tracking, documents, tasks, confirmations, and timeline. But none of these sections answer the operator's actual question, which is: "what should I do right now to advance this trip?" Data and action guidance are not the same thing. Every section added without an action model makes the page more informative and less useful.

**2. In a small agency, the danger is not missing features — it is silent data corruption.**
The 409 conflict guard, the customer data provenance badge, and the extraction conflict warning are the three most important things currently on this page. Not because they are used often, but because when they fire, the stakes are high (wrong traveler data sent to a supplier, wrong payment amount recorded, booking made against stale customer input). Any new feature that introduces a path to silent data modification — without provenance, without confirmation, without auditability — is more dangerous than the feature is valuable.

**3. The extraction UI's manual traveler-document matching is the most likely source of the first serious operator error.**
This is not hypothetical. The current flow requires an operator to: upload a document (selecting type but not traveler), then extract, then select a traveler by ID from a dropdown, then pick which fields to apply. The probability of a mismatch on a 4-traveler trip where the operator is handling three other trips simultaneously is not low. The fix is trivial: add traveler assignment at upload time and pre-populate the extraction "apply to" field. Not doing this before promoting the extraction feature to primary workflow is accepting a known error path.

---

## 10. One Surprising Idea

**Make OpsPanel show the delta since last session, not the current state.**

Right now, when an operator opens a trip's Ops page, they see the full current state: all traveler data, all documents, all tasks, all payments. This is correct for someone using the page for the first time. But a 3-person agency's operator returns to the same 12 trips every day. What they need is not the full state — they know the full state — they need to see what changed since they last looked.

Show a "Changes since your last visit" callout at the top: "Customer submitted passport data (2 hours ago) · Task 'Book hotel' moved to waiting_on_customer (yesterday) · Payment updated to deposit_paid (3 days ago)." This is a per-user, per-trip diff — not a raw timeline — synthesized from the ExecutionTimeline events since the operator's last session token. It costs one backend endpoint that queries timeline events after a `last_viewed_at` timestamp. The operator processes the delta, not the state. This is how a 3-person agency operates at 20-person throughput: they stop re-reading everything they already know.

---

**The thing most people miss about this:**

The Ops page is designed as if operators open it to fill it in. In practice, operators open it to find out if something went wrong. The difference between those two mental models determines everything about what should be on screen when the page loads — and the current layout, starting with readiness tier tables and booking data read-view, is optimized for the filling-in use case that only happens once per trip, not the checking use case that happens five times a day.
