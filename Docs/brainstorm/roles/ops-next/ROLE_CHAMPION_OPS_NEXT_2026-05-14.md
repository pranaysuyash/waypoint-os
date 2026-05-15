# Brainstorm Role: Champion — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-Sentence Thesis

Trip Workspace Ops should become the single authoritative execution cockpit where a three-person agency can run the full booking lifecycle — data collection, document verification, supplier payment deadlines, task execution, and confirmation auditing — without ever switching to a spreadsheet, a WhatsApp thread, or a supplier portal tab.

---

## 2. What the Current Ops Page Gets Right

- **The 7-status booking task state machine is a serious foundation.** `not_started → blocked → ready → in_progress → waiting_on_customer → completed → cancelled` is real booking execution vocabulary. Agencies actually live in this space; most tools pretend it's a toggle.
- **Document extraction with field-level confidence scoring and conflict handling is genuinely rare.** The `extractDocument → applyExtraction` pipeline with per-field checkboxes and overwrite confirmation is not a toy feature — it's the workflow that currently takes a travel agent 15 minutes per passport and makes it a 30-second review.
- **The customer submission intake flow is well-designed.** A pending submission sits in amber/review until explicitly accepted or rejected. This is the correct pattern: operator-in-control, customer-as-supplier-of-data.
- **Payment tracking is honest about its own scope** — the "Status-only tracking" badge is a truthful signal that prevents operators from treating it as an accounting system. That honesty builds trust faster than overselling.
- **The stage gate is the right call.** Showing Ops only for `proposal` and `booking` stages protects operators from a noisy page during intake/discovery.
- **The `conflict` detection on booking data save** (HTTP 409 → reload prompt) is production-grade concurrency handling that most internal tools omit entirely.

---

## 3. What It Gets Wrong

- **No "What do I do right now?" signal.** The page opens with readiness tiers first, then booking data, then documents, then tasks, then confirmations, then timeline — all equal-weight vertical scroll. A 3-person agency with 12 active trips has no triage signal. The page is a filing cabinet, not a cockpit.
- **Readiness assessment is a set of tier labels without actionable intent.** "Tier: booking_ready / Not ready / Missing: passport_number" tells the operator what is missing but not who should fix it, by what means, and by when. It reads like a compiler error with no line number.
- **Documents are a flat undifferentiated list.** Five documents from three travelers — a passport for adult_1, a visa for adult_2, an insurance certificate that applies to the whole group — render as five identically-styled rows. There is no way to see at a glance "adult_1 is document-complete; adult_2 is not."
- **Payments have no temporal context.** The payment tracking block shows agreed, paid, balance, status — but there is no connection to supplier deadlines. The operator who has collected 70% of the agreed amount but owes a hotel a final payment in 3 days has no warning in this view.
- **Booking tasks are manually created from scratch.** The 7-status state machine is powerful but the tasks themselves have no relationship to the accepted quote. When an operator moves a trip to `booking` stage there should be a pre-populated task list derived from the trip's components (flight, hotel, transfer, visa). Today every task is a blank slate.
- **Confirmations are not diffed against the proposed itinerary.** A confirmation record exists in isolation. The operator cannot see at a glance whether the confirmed hotel matches what was in the proposal (room type, dates, board basis). This is the single most expensive category of post-booking errors.
- **The timeline is a passive append-only log.** ExecutionTimelinePanel renders events but offers no filtering, no actor-scoped view, no "what happened since I last looked" highlight. For a trip with 40+ events it becomes unusable.
- **The extraction UX has a traveler-selection problem.** The traveler dropdown in the extraction apply panel is populated from `bookingData.travelers` — which may be empty if booking data has not been entered yet. An operator trying to extract a passport before entering traveler IDs is stuck.
- **The collection link section and the booking data section are visually equivalent.** They are both flat bordered boxes. The link generator is a means to an end (collecting data), not a peer concept to payment tracking. This grouping is the page architecture reflecting implementation order rather than operator mental model.
- **34+ independent state slices in one component.** This is already acknowledged in a code comment. It means every incremental feature adds to a maintenance burden that will eventually make the component unmaintainable without decomposition.

---

## 4. The Top 5 Operator Decisions Ops Must Support

**Decision 1: "Is this trip ready to book right now, and if not, exactly what is blocking me?"**

The most frequent, highest-stakes decision an operator makes on any active trip. Currently the readiness tiers answer "what tier are you at" but not "here is the one action that moves you forward." The page needs a single authoritative readiness verdict with a concrete blocker list and an attributed owner for each blocker (operator-owned vs. customer-owned vs. supplier-owned).

**Decision 2: "Have I collected and verified everything from the customer before I go to suppliers?"**

This is the pre-booking data-completeness check. The operator needs to see: all travelers → data status (complete/incomplete) → document status (uploaded/verified/extracted). Today this requires scanning the traveler table, then scrolling to a flat document list, then mentally cross-referencing. A traveler-centric view collapses this into one scan.

**Decision 3: "Which supplier payments are coming due and am I at risk of missing a deadline?"**

No tool in the current stack connects payment status to supplier deadlines. Operators manage this in spreadsheets or memory. This is a top-3 cause of margin erosion (late payment surcharges) and supplier relationship damage in small agencies.

**Decision 4: "Has everything been confirmed correctly, and does the confirmation match what I sold?"**

Post-booking verification is currently manual: the operator reads the confirmation email and compares it to the proposal document. A diff view — confirmed hotel name vs. proposed hotel name, confirmed dates vs. proposed dates, confirmed room type vs. proposed room type — would cut this review time by 80% and catch errors before the traveler notices.

**Decision 5: "What did we commit to, who actioned it, and when — if something goes wrong?"**

The audit spine question. When a booking goes wrong (supplier cancels, confirmation details mismatch, customer claims they never received the link) the operator needs to reconstruct the chain of events in under 60 seconds. The current timeline has the data but not the interrogability.

---

## 5. Ideal Page Layout

The page should open in a "command mode" and the operator should be able to read the trip's operational health in 5 seconds without scrolling.

**Section 1 — Next Action Banner (sticky top, dismissable per trip)**

A single computed banner: "1 action needed" or "Awaiting customer: passport from adult_2" or "Ready to book — 0 blockers." This banner is not a readiness display; it is a dispatch instruction. It derives from the combination of readiness assessment + task states + document states + pending submissions. When everything is clear the banner turns green and says "All clear — proceed to booking." When the banner is green for the first time, it is a moment of agency-wide relief and trust.

**Section 2 — Travelers (data + documents, co-located per traveler)**

Each traveler gets a card: name, DOB, passport number, and directly beneath it the documents assigned to that traveler (passport scan status, visa status, extracted fields). The group-level documents (insurance, itinerary) get a separate group-level row at the bottom. This collapses two separate sections (booking data + documents) into one per-entity view. The collection link generator lives as a small action inside this section — it is a data-collection mechanism, not a peer section.

**Section 3 — Payments + Deadlines**

Agreed amount, amount paid, balance, payment status — but now linked to supplier components. Each booking task that represents a supplier booking should carry an optional `payment_due_date` and `supplier_ref`. The payments section renders a deadline calendar: "Hotel final payment — INR 45,000 — due 2026-05-18 — 4 days." Red if overdue. Amber if within 7 days. This is not accounting software; it is a deadline visibility board.

**Section 4 — Booking Tasks (generated from quote, manually augmentable)**

The 7-status state machine remains. But when a trip enters `booking` stage, a task scaffold is generated from the accepted quote's component list: one task per bookable component (flight, hotel, transfer, visa application, travel insurance). These are pre-populated with component name, traveler scope, and supplier if known. Operators can add, remove, and reorder. The task list is the execution checklist; an operator with 3 people can assign tasks by owner (even if owner is just "me") and see at a glance what is in-progress vs. blocked vs. done.

**Section 5 — Confirmations + Diff**

Each confirmation record is displayed alongside the corresponding proposed component from the quote. Side-by-side or inline diff: "Proposed: Le Méridien, Deluxe King, 3 nights, CP. Confirmed: Le Méridien, Superior Room, 3 nights, EP." Mismatches are flagged in amber. The operator resolves each mismatch explicitly (accept diff / escalate). This creates a verified-confirmation record that is the legal and operational handoff to the traveler.

**Section 6 — Execution Timeline (active audit spine)**

The timeline gets a filter bar: by actor type (agent, customer, system), by event category (data-change, document, payment, booking-task, confirmation), and a "since my last visit" toggle that highlights new events since the operator's last session. High-severity events (overwrite-confirmed, confirmation-mismatch-resolved, link-revoked) get a persistent marker that cannot be scrolled past without acknowledgment. This turns the passive log into an active accountability record.

---

## 6. What to Build Next

**Slice: Traveler-centric document grouping (1–2 days, high value, low risk)**

Restructure the flat document list into per-traveler sections. Each traveler row shows their documents inline. Documents without a `traveler_id` association go to a "Trip-level documents" section. This requires only a client-side grouping change — no new API endpoints, no new state. It makes the page scannable by eye and directly addresses the pre-booking completeness check decision. The existing document fetch and upload flows remain unchanged; only the render structure changes.

Implementation path:
1. Add an optional `traveler_id` field to `BookingDocument` (or use existing metadata).
2. Group `documents` array by `traveler_id` in the render function.
3. Render per-traveler document sub-sections inside or adjacent to the traveler rows.
4. Move the collection link generator from its standalone section into the traveler data section header as a secondary action.

**Slice: Next Action Banner computation (2–3 days)**

Add a pure-function `computeNextAction(trip, bookingData, documents, pendingData, tasks)` that returns a typed `NextAction` object: `{ severity: 'blocking' | 'attention' | 'clear', message: string, ownerType: 'operator' | 'customer' | 'supplier' | null }`. Render this as the top banner. Logic:
- `pendingData` not null → "Review customer submission" (blocking, operator)
- Any readiness `missing_for_next` field that is `traveler_id`-attributed and has no accepted document → "Customer document needed: passport for adult_2" (blocking, customer)
- Any task in `blocked` state → "Booking task blocked: [task name]" (blocking, operator)
- Any readiness `missing_for_next` that is an operator-fillable field → "Add [field] before booking" (blocking, operator)
- All clear → "Ready to proceed" (clear)

This is computed client-side from existing data already loaded on the page. No new API endpoints required for the first version.

---

## 7. What Not to Build Yet

**Automated payment gateway integration.** Payment tracking in the current system is intentionally "status-only." Adding actual payment processing (Razorpay, Stripe, etc.) turns this into a financial product with PCI compliance, reconciliation, refund flows, and regulatory surface area. The deadline visibility board is the right next step; actual payment rails are a separate product decision.

**Client-facing portal features.** The collection link generator is the correct and minimal public-facing surface. Any expansion of the customer-facing experience (real-time trip status page, customer document upload portal, approval notifications) belongs in a separate product track with its own auth, design, and UX considerations. Building client-facing UI inside Ops creates a permanently entangled scope problem.

**AI-generated booking task content.** Auto-generating task descriptions from the accepted quote is valuable but requires the quote output format to be stable and machine-readable. If the proposal output is still a markdown/rich text blob, parsing it for structured components will produce unreliable results. The task scaffold should be generated from structured quote data, not NLP extraction. Build the structured quote data layer first.

**Full accounting / P&L per trip.** The operators who need this are 10–20 person agencies. For 1–5 person agencies the payment tracking balance view is sufficient. Adding cost-of-goods tracking, margin calculation, and commission splits now will slow down the core booking execution surface without being used.

**Sub-tabs navigation (Data / Documents / Payments / Tasks / Confirmations).** This is a natural endpoint architecture but is premature as the first reorganization step. Sub-tabs add navigation overhead; a well-ordered single scroll is more usable for trips with fewer than 15 components. Sub-tabs become right when the page exceeds cognitive load on a real trip — which means testing with real trips first, not designing for an imagined complexity.

---

## 8. Risks and Failure Modes

**Risk 1: Traveler-document linkage breaks if traveler_id is inconsistent.**
The extraction traveler selector already exposes this: if booking data is not entered before documents are uploaded, the traveler_id association is broken. Any traveler-centric reorganization must handle the case where documents exist but traveler_id is null or unmatched. The fallback "unassigned documents" section is not optional — it is the safety net.

**Risk 2: The Next Action Banner becomes a liability if it fires false positives.**
A banner that says "Ready to book" when something is actually missing destroys operator trust permanently. The computation must be conservative: if in doubt, surface the blocker, not the all-clear. Over-warning is recoverable; false all-clears cause real-world booking errors.

**Risk 3: Task scaffold from quote requires stable structured output that does not yet exist.**
If the accepted quote is a rich text blob, auto-populating tasks from it is NLP extraction — which will miss components, misparse suppliers, and produce wrong task names. This feature must be gated on structured quote data availability. Launching it prematurely will cause operators to distrust auto-generated content and stop using the task feature entirely.

**Risk 4: Confirmation diff requires a stable proposed-itinerary data model.**
Diffing confirmed vs. proposed requires both to be structured. If the proposal is stored as a PDF or markdown document, extracting the structured components for comparison requires another document extraction pipeline. The risk is that the diff surface is built before the data layer supports it, resulting in a half-functional feature that shows partial diffs and creates more confusion than it resolves.

**Risk 5: The 34-state-slice component will resist decomposition under time pressure.**
Every feature addition to OpsPanel that does not come with a corresponding decomposition step increases the cost of the next one. The correct investment is to extract BookingDataSection, DocumentSection, PaymentSection, and TaskSection as isolated sub-components — each with their own state — before the next major feature is added. Delaying this creates a compounding debt that eventually forces a full rewrite.

**Risk 6: Ops acquires too much surface area and becomes a second Workbench.**
The original sin of the Workbench was that it tried to be everything. Trip Workspace Ops must stay disciplined: it is the execution record for a trip that has reached proposal or booking stage. It is not a communication tool, not a CRM, not a quoting surface, not an itinerary builder. Every new feature proposal should be tested against this: "Is this part of executing a booking, or is it a different job?"

---

## 9. Three Strongest Insights

**Insight 1: The extraction pipeline is a competitive moat, not a document feature.**
Most travel agency software treats document collection as a checklist ("has passport: yes/no"). The extraction pipeline — upload → AI extract → field-level confidence → human review → selective apply → conflict resolution → audit trail — is qualitatively different from everything else in the market. This is the feature that a three-person agency uses to move at the speed of a ten-person agency. It should be the centerpiece of the Ops page, not a sub-action buried in a flat document list.

**Insight 2: The booking task state machine is already half of a project management tool that doesn't need to become one.**
The 7-status machine (`blocked`, `waiting_on_customer`, `in_progress`, `completed`) is a precise vocabulary for travel operations. The insight is that it does not need Jira-style boards, swimlanes, or workload views to be powerful. What it needs is to be seeded from the accepted quote and connected to the readiness assessment — so that the task list and the readiness verdict point at the same truth. Those two things alone close the feedback loop that currently requires three separate tools.

**Insight 3: The timeline is currently the most underutilized asset on the page.**
The ExecutionTimelinePanel has everything: actor, event type, timestamp, structured payload. It is the only feature that answers "what actually happened on this trip" with evidence. But it renders as a passive scroll with no interrogability. The operators who work with it today use it reactively — only when something goes wrong and they need to reconstruct. If it had a "since last visit" highlight, an actor filter, and a severity indicator for high-stakes events, it would become a proactive daily-check tool. The cost to get there is low (pure rendering logic); the value is high (reduces the "what happened?" communication overhead between team members).

---

## 10. One Surprising Idea

**The collection link should expire based on trip-stage transitions, not just time.**

Currently the collection link has a time-based expiry. But the operationally correct expiry condition is stage advancement: when the operator accepts all pending booking data and moves the trip to `booking`, the collection link should auto-revoke. Not because of a timer, but because the data collection phase is over. A customer who clicks a stale link after the trip has moved to booking stage should see a message: "Your travel agency has already locked in your booking details. Contact [agency name] if anything needs to change."

This is surprising because it reframes the collection link from a security feature (revoke after N days) to a workflow gate (revoke when the job is done). It also creates a natural moment of finality for the customer — which reduces the "can I still change my passport number?" calls that cost small agencies real time. The implementation is a backend trigger on stage transition; the UX writes itself.

---

**The thing most people miss about this:**

The entire Ops page is actually an evidence ledger, not a form. Every action — accepting a customer submission, applying a document extraction, marking a task complete, resolving a confirmation diff — creates an irrevocable audit entry. The product's real value is not the editing surface; it is the accumulated proof that the operator did their job correctly. When a booking goes wrong (and in travel, something always eventually goes wrong), the operator who can pull up a timestamped record showing exactly when the passport was verified, who accepted the customer's data, and when the hotel confirmation was reviewed and matched — that operator wins the dispute with the customer and survives the supplier complaint. The OPS page is a litigation shield disguised as a booking checklist. Build it like one.
