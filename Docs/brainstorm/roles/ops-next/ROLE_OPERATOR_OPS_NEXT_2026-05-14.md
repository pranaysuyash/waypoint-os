# Brainstorm Role: Operator — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-Sentence Thesis

Ops should be the single place where a 3-person agency can hand a trip to any team member on a Monday morning and have that person know exactly what to do next, what is already confirmed, and what will blow up by Friday if nobody acts.

---

## 2. What the Current Ops Page Gets Right

- **Readiness tiers exist and are exposed.** The tier/unmet/met breakdown is the right mental model. An operator genuinely wants to know "am I at flight-booking tier or just hotel tier?"
- **Conflict guard on booking data saves real work.** The 409 optimistic-lock + reload prompt is production-grade. Two agents editing the same trip simultaneously is a realistic risk.
- **Pending customer submission is a first-class review.** The amber-bordered review block with Accept/Reject is the correct UX. Customer data goes nowhere until an agent explicitly accepts it.
- **Documents have a clear acceptance state machine.** `pending_review → accepted/rejected` with extraction is the right workflow skeleton.
- **AI extraction with conflict awareness is a genuine differentiator.** Showing confidence scores per field, per-traveler application, and explicit conflict resolution is genuinely sophisticated — most CRMs don't do this.
- **ExecutionTimeline, BookingExecutionPanel, and ConfirmationPanel are present.** Even if they are at the bottom, the data shapes exist. That is the hardest part.
- **`mode='documents'` escape hatch exists.** Gives a clean way to surface documents in a narrower view without duplicating the component.

---

## 3. What It Gets Wrong

- **There is no "next action" anywhere on this page.** An operator loading Ops at 6pm Friday sees: readiness tiers (which require interpretation), then booking details table, then documents, then tasks, then confirmations, then a timeline. The page describes state. It does not say what the operator should do. That is the most important missing thing.
- **Readiness is at the top but it is the wrong kind of top-of-page content.** "Highest ready tier: tier_3_docs" is informational, not actionable. It answers "how ready am I?" not "what must I do now?" Those are different questions.
- **Payment has no deadline.** The payment tracking block shows agreed amount, amount paid, balance due, and status — but there is no "final payment due" date field. An operator with a 30-day final payment deadline needs that field more than the method/reference combo.
- **Documents are a flat list sorted by upload time.** Three travelers, each with a passport, visa, and insurance doc — that is nine documents in a sequence that has no grouping. An operator scanning for "do I have adult_2's passport?" is doing visual search work that the UI should eliminate.
- **Booking tasks are not generated from the trip.** The BookingExecutionPanel presumably has manual task creation. But the accepted quote contains flights, hotels, and transfers — those are the exact tasks. If an agent accepts a quote with "3 nights Park Hyatt + Emirates EK501" and then has to manually create a "Book hotel" task, the system missed an obvious step.
- **Confirmations exist but there is no diff against the proposal.** If the accepted quote said "Park Hyatt, 3 nights, superior room" and the confirmation comes back "Park Hyatt, 2 nights, deluxe room" — nothing on this page surfaces that discrepancy. That is how an operator causes a complaint.
- **The timeline is passive.** ExecutionTimelinePanel at line 1396 renders at the very bottom. An actor-typed event log that no one scrolls to is decorative, not structural. It should be the spine that everything else is anchored to.
- **The customer collection link UX conflates status with generation.** "Active link exists. Generating a new link will revoke the old one." and then a "Generate New Customer Link" button is too close together. An operator who just wants to know the link status and copy it again is forced through a generate flow they did not intend to start.
- **34+ independent state variables in one component.** This is not a layout problem per se, but it means every section is tightly coupled in one render tree. Adding one new section (e.g., supplier deadline tracking) requires threading new state through an already-large function. The architecture fights future extension.
- **The "canonical workflow" banner inside Documents** ("use this Ops panel for document upload, review, extraction, and apply. The dedicated /documents module remains staged…") is developer context leaking into an operator UI. No operator cares. That banner should be removed.

---

## 4. The Top 5 Operator Decisions Ops Must Support

These are the actual decisions an operator makes while working a trip, in rough frequency order:

**Decision 1: What do I need to do right now on this trip?**
The page must make the next required action unambiguous. Not "what data is missing" — that is readiness. The question is "what human action do I take in the next 15 minutes?" Examples: call the customer to get adult_2's passport, confirm the hotel booking before the hold expires, send the balance payment reminder.

**Decision 2: Is it safe to book supplier X yet?**
This is the readiness question, but framed as a yes/no gating decision. Before calling Emirates to book flights, an operator needs: all traveler passports present and verified, payment status at least deposit_paid, trip dates locked. If any of those are red, the answer is "no, do not book yet."

**Decision 3: Did everything come back from the supplier exactly as quoted?**
After booking, the operator must verify confirmations match the accepted itinerary. Room type, check-in/check-out dates, passenger name spelling, flight number and time. One mismatch here causes a client complaint at destination.

**Decision 4: Is the client current on payments, and when is the next payment due?**
Not just "what is the status" — what is the date by which the agency owes the supplier or the client owes the agency? Payment-without-deadline is financial risk.

**Decision 5: What happened and who did it?**
When a client calls and says "I was told X but my booking says Y," the operator needs to reconstruct the sequence: who accepted which data, when, and from what source. The timeline is the answer — but only if it is easy to reach and comprehensive.

---

## 5. Ideal Page Layout

Section order as it should appear on the page, with rationale for each position:

**[HEADER] Trip status strip — always visible, never collapsed**
Single row: trip name, stage badge, departure date, days-until-departure. Gives every operator instant orientation regardless of scroll position. This should already exist in the Trip Workspace shell, but if it does not, Ops needs it.

**[SECTION 1] Next Actions — highest priority, top of page**
A computed list of actions the operator must take, ordered by urgency. Not a free-text notes field — a system-generated list derived from readiness gaps, payment deadlines, unconfirmed bookings, and pending submissions. Each action has a label ("Collect adult_2 passport"), a category icon (data / payment / booking / document), and optionally an overdue indicator. If there are no blocking actions, show "All clear — N tasks in progress." This section replaces the current readiness-at-top arrangement.

**[SECTION 2] Readiness Gate — collapsed by default if all tiers met, expanded if anything is unmet**
The existing tier breakdown is correct but it should be secondary to the Next Actions list above it. Show "Booking Ready: Tier 3 of 4" as a summary row. Expand to show the tier details and `missing_for_next` fields. The visa concern signal belongs here too, not in a separate Signals block.

**[SECTION 3] Travelers + Documents — side-by-side or per-traveler accordion**
This is the biggest structural change from the current layout. Group by traveler rather than by document type. For each traveler: name, DOB, passport number (with source badge: Agent / Customer-verified / Extracted), and then that traveler's documents as a sub-list with their status chips. An operator scanning for "do I have everything for adult_2?" finds the answer in one visual unit, not by scanning a flat list of nine documents.

The collection link generator belongs here as a sub-action within this section ("Send data collection link to customer") rather than as a standalone section. The current placement makes it feel like a major workflow step; it is actually a sub-step of traveler data collection.

**[SECTION 4] Payment — with deadline field**
Agreed amount, paid, balance due, status — this is already correct. Add: `final_payment_due` date field. Show a countdown if that date is within 14 days: "Final payment due in 7 days." Refund tracking stays here but collapses into a sub-row unless refund_status is not `not_applicable`.

**[SECTION 5] Booking Tasks — generated from the accepted quote, editable**
The BookingExecutionPanel belongs here. Key change: when a quote is accepted, the system should pre-populate tasks from the itinerary items (flight segments, hotel nights, transfers, activities). The operator can add, edit, or cancel tasks — but the starting state should not be an empty board. Tasks show their 7-status state machine clearly: the current status transitions available should be one-click, not buried in a form.

**[SECTION 6] Confirmations — diffed against the proposal**
The ConfirmationPanel belongs here. Add a "diff view" per confirmation: what the accepted itinerary said vs. what the confirmation document states. If dates, names, room types, or flight numbers differ — highlight in amber. If they match exactly — show a green "Matches quote" badge. This is the most underbuilt section in the current panel and the one with the highest consequence for trip quality.

**[SECTION 7] Execution Timeline — always at bottom, but promoted to audit spine**
The ExecutionTimelinePanel stays at the bottom. Its role should shift from "passive log" to "audit record." Every accept/reject action, every booking task status change, every confirmation upload should appear here as a named-actor event. The timeline should also be linkable — a deep link to `#timeline-event-xyz` so an operator can share "look at what happened at 3pm Tuesday."

---

## 6. What to Build Next

Concrete, ordered, each buildable in 1–3 days:

**Slice 1: Next Actions computed header (highest ROI)**
Add a `computeNextActions(trip, bookingData, documents, tasks, payments)` function that returns an ordered list of action items. Wire it to a new `NextActionsBar` component at the top of OpsPanel. Start with four rules: (a) any traveler missing DOB → "Collect DOB for {name}"; (b) any document in `pending_review` → "Review document: {type} for {traveler}"; (c) payment_status is `not_started` or `unknown` and departure < 30 days → "Collect deposit from {payer}"; (d) any task in `blocked` state → "Unblock: {task_name}". Even four rules make the page dramatically more useful.

**Slice 2: `final_payment_due` date on PaymentTracking model + UI**
Add `final_payment_due: string | null` to the `PaymentTracking` type, persist it through the booking data endpoint, and show it in the payment display row. Show a countdown badge if within 14 days. This is one new field but eliminates the most common financial risk oversight.

**Slice 3: Per-traveler document grouping in the Documents section**
Refactor the document list to group by `traveler_id` (or "Unassigned" for docs without a traveler). No backend changes needed — documents already have a traveler_id field (or can be assigned one). This is a pure frontend reorganization of the existing `documents` array.

**Slice 4: Confirmation diff view against accepted quote**
Add a `proposed_value` / `confirmed_value` comparison to the ConfirmationPanel per-booking record. The accepted quote output already contains structured itinerary items. A simple string comparison per field (dates, names, room type, flight number) with amber highlight on mismatch is achievable without AI — just structured comparison. This is the highest-consequence quality guard.

**Slice 5: Remove the developer-context banner from Documents**
Delete the "Canonical workflow: use this Ops panel…" blue info box. It is not operator content. One line removal.

---

## 7. What Not to Build Yet

- **Full sub-tab navigation (Data / Documents / Payments / Tasks / Confirmations).** The sub-tab structure is appealing architecturally but it buries context. On a 15-supplier trip with 4 travelers, an operator needs to see payment status while reviewing a document — tabs force them to context-switch. Keep the single scrollable page until the content genuinely requires tabbing. The natural trigger for sub-tabs is when any single section exceeds one screen's worth of content consistently. Build the sections well first.
- **Client-facing confirmation portal.** The confirmation diff view (Slice 4 above) should remain internal only. A client-facing portal is a separate product surface with its own trust, formatting, and communication requirements.
- **Automated supplier booking integration.** The tasks model exists. The temptation will be to add "Book via API" buttons for GDS/supplier integrations. That is a 6-month initiative, not a next slice. The operator workflow must work without it first.
- **AI-generated next actions from unstructured notes.** Slice 1 proposes rule-based next actions. The temptation is to have an LLM read the intake notes and produce actions. Resist this until the rule-based version is trusted. Operators need to understand why an action appears; "the AI said so" is not an acceptable answer when a $20,000 trip is on the line.
- **Email/WhatsApp send from Ops panel.** The collection link already handles the canonical "send data request to customer" flow. Building full comms from within Ops before the core execution workflow is stable is scope creep.

---

## 8. Risks / Failure Modes

**Risk 1: Next Actions computed incorrectly → operator ignores the feature**
If the Next Actions bar fires a false alarm twice, operators will stop trusting it. The rule logic must be conservative: only surface an action when the system is certain it is required. Better to show nothing than to cry wolf. Ship with four rules, monitor trust before expanding.

**Risk 2: Traveler-grouped documents create an "unassigned" pile**
If documents uploaded before the traveler grouping is built have no `traveler_id`, they fall into an "Unassigned" bucket. That bucket becomes a dumping ground. Mitigate: when displaying unassigned documents, show them at the top with a "Assign to traveler" action rather than at the bottom.

**Risk 3: Confirmation diff produces false positives on name formatting**
"Emirates EK 501" vs "EK501" or "Park Hyatt Dubai" vs "Park Hyatt, Dubai" will produce diffs that are not meaningful mismatches. Naive string comparison will annoy operators with noise. Mitigate: use normalized comparison (strip spaces/punctuation for flight numbers, case-insensitive for names) and add a "Mark as matching" dismiss button.

**Risk 4: `final_payment_due` date field adds input burden**
If every trip requires operators to manually enter a payment deadline, they will skip it on busy days. Mitigate: populate it automatically from the accepted quote if the quote contains payment terms. Fall back to a "Set deadline" prompt in the Next Actions bar if the field is empty and departure is within 30 days.

**Risk 5: OpsPanel growing past 1,399 lines with new sections**
Adding Next Actions, payment deadline, per-traveler grouping, and confirmation diff without refactoring will push the component toward 2,000+ lines. This is a maintainability risk. Mitigate: extract `NextActionsBar`, `TravelerDocumentGroup`, and `ConfirmationDiffRow` as standalone components before or during Slice 1-4 delivery.

**Risk 6: Timeline gets written to but never read**
The ExecutionTimeline is already built but is positioned last. If operators never scroll to it, the audit record is useless. Mitigate: Surface the last 2 timeline events as a "Recent activity" strip in the Next Actions header. This makes the timeline visible without moving it.

---

## 9. Three Strongest Insights

**Insight 1: The ops page is currently a status dashboard, but operators need a decision surface.**
Status tells you what is true. A decision surface tells you what to do. The gap between "all traveler data entered" and "send the link to the customer" is a human action that the current page does not surface. Every operator action that is not made explicit in the UI is a thing that gets forgotten on a Friday afternoon.

**Insight 2: Document trust is the real bottleneck, not document presence.**
It is not enough to know a passport was uploaded. An operator needs to know: is this the right passport (name matches the booking), is it valid beyond the return date, and was it reviewed by a human or just auto-accepted. The current document model has the status field and the extraction confidence — but the UI does not surface "this passport was accepted by agent on May 12, confidence 94%, name matches booking data" in a scannable way. Trust requires provenance, not just presence.

**Insight 3: The confirmation diff is the single highest-leverage quality guard in the entire system.**
Everything before confirmation is preparation. The confirmation is when the supplier commits. If what the supplier confirmed does not match what the client expects, the problem exists — and the earlier it is caught, the cheaper it is to fix. An operator who catches a hotel room type mismatch before travel starts can fix it with a phone call. The same discovery at check-in requires an emergency rebooking. Building the diff view (Slice 4) has asymmetric impact: low build cost, very high operational value.

---

## 10. One Surprising Idea

**The "Trip Handoff Brief" — a one-click printable/shareable ops summary for handing a trip to a colleague or an on-call agent.**

When a senior agent goes on vacation or a client trip is transferred mid-booking, the receiving agent currently has to read through the entire Ops page to get up to speed. Instead: a single "Generate Handoff Brief" button that produces a structured 1-page summary:

- Traveler list with document status per person
- Payment status and next deadline
- Open tasks and their current state
- Last 5 timeline events
- Any unresolved confirmations or conflicts

This is not a client-facing document. It is an internal ops handoff note. It requires no new data — everything already exists in the Trip Workspace. The only new work is the layout rendering.

A 3-person agency with this button can hand off a live trip to a freelance assistant or a partner agency without a 30-minute briefing call. That is the "look like a 20-person operation" feature. Large agencies have operations manuals and handoff meetings. Small agencies have tribal knowledge. The Handoff Brief makes tribal knowledge portable.

---

**The thing most people miss about this:**

The operator's enemy is not missing information — it is missing *sequenced* information. Every piece of data needed to execute a trip correctly already exists somewhere in the system by the time the booking stage is reached: the itinerary, the traveler profiles, the payment terms, the supplier contacts. The ops page already stores almost all of it. What makes a small agency feel like they are barely holding on is that the data exists but the sequence does not. Nobody told the system "step 1 is always verify names match passports, step 2 is always collect deposit before booking, step 3 is always compare confirmations against the quote." Building even a partial sequence — just four rules in a Next Actions bar — transforms the ops page from an archive into a workflow engine. The whole competitive advantage of a well-built system at this scale is not AI features or supplier integrations. It is that the right operator action is obvious at every moment, regardless of who is looking at the screen.
