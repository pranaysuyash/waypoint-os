# Brainstorm Role: Strategist — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-Sentence Thesis

Ops must become the operator's single source of execution truth — the place where every booking decision, data handoff, payment event, and supplier confirmation is stamped, sequenced, and auditable — so a 3-person agency operates with the institutional memory of a 20-person operation.

---

## 2. What the Current Ops Page Gets Right

The existing OpsPanel.tsx (1,399 lines, all in one component) demonstrates genuine product instinct in several areas:

**The readiness tier model is architecturally correct.** Exposing `highest_ready_tier`, tier-level met/unmet lists, and `missing_for_next` fields means the system can answer the operator's real question — "can I actually book this?" — rather than just storing data. This is the right abstraction. It avoids the trap of checklist-only tools (TravelJoy) that tell you what to collect but not whether you're done collecting it.

**Source attribution on booking data is meaningful.** The `bookingDataSource` badge (agent vs. customer_accepted) is a trust signal, not just a label. It answers the compliance question "who entered this?" before anyone asks it. Most competitors omit this entirely.

**The 7-status booking task state machine is production-grade.** `not_started / blocked / ready / in_progress / waiting_on_customer / completed / cancelled` maps directly to real agency workflow. The `waiting_on_customer` status in particular is something spreadsheet users track in their heads — externalizing it reduces dropped balls.

**Extraction with field-level conflict handling is a real differentiator.** The ability to extract structured data from uploaded documents, show per-field confidence scores, let the agent cherry-pick fields to apply, and surface exact field-level conflicts (existing value vs. extracted value) is a feature that takes competitors 2+ years to build if they think to build it at all.

**Optimistic conflict detection on booking data saves.** The 409-based conflict guard (with reload prompt) is the right behavior for a multi-agent environment. This prevents silent data loss when two ops staff work the same trip.

**The timeline panel as actor-typed event log is audit-ready.** Separating events by actor type is not a cosmetic choice — it is the foundation for compliance reporting, dispute resolution, and eventually liability documentation.

---

## 3. What It Gets Wrong

**The page has no opinionated orientation.** When an operator opens Ops for an in-progress booking trip, they see: no-readiness notice (or readiness tiers), then pending submission review, then booking details, then collection link, then documents, then tasks, then confirmations, then timeline. This is accretion order, not decision priority. The page answers the question "what data do we have?" rather than "what do I do next?"

**Payment tracking is buried inside booking data editing.** Payment status (agreed amount, amount paid, balance due, refund status) is arguably the most time-sensitive financial signal in any active booking. Right now it lives inside the booking data edit form, rendered as a collapsible sub-section. An operator managing 12 active trips should be able to scan payment status at a glance from the trip list or the top of Ops — not dig into an edit flow.

**Documents are a flat list with no contextual organization.** A passport and a hotel confirmation are both `BookingDocument` objects rendered in the same `space-y-2` list. There is no grouping by traveler, no grouping by supplier, no distinction between identity documents (needed for booking) and confirmation documents (produced by booking). When a trip has 4 travelers and 6 suppliers, this list has 20+ items with no navigable structure.

**Booking tasks have no declared origin.** The `BookingExecutionPanel` renders tasks but does not connect them to the accepted quote or itinerary. An operator cannot tell whether a task was generated from the proposal, created manually, or carried over from a template. This forecloses the ability to audit "we booked what we proposed."

**Confirmations are not diffed against the proposal.** The `ConfirmationPanel` records supplier confirmation details per booking, but there is no comparison to what was promised in the accepted quote. A hotel booked at INR 4,200/night when the quote said 3,800/night is invisible unless someone manually checks. This is the most common source of margin erosion in small agencies.

**The collection link UX conflates generating and sharing.** Generating a new link revokes the old one, which is correct security behavior. But the UX presents this as a single "Generate New Customer Link" button with a warning note, rather than clearly modeling the link lifecycle (active / revoked / expired / pending submission). An operator who generates a second link while a customer is filling out the first form has caused a bad customer experience — the system should warn more loudly.

**The timeline is passive.** `ExecutionTimelinePanel` logs events as they happen. It does not flag anomalies, does not highlight SLA violations (e.g., "waiting_on_customer for 3 days"), and does not surface time-sensitive sequences (e.g., "payment deposit due in 2 days, supplier deadline tomorrow"). It is a black box history, not an operational radar.

**OpsPanel is 1,399 lines as a single component.** This is not a cosmetic problem. It means the entire page re-renders on any state change anywhere. More importantly, it means every new feature must be threaded into a component that already manages 34+ independent state slices. The architectural ceiling of this approach will be hit in the next 3 features.

---

## 4. The Top 5 Operator Decisions Ops Must Support

These are the real decisions an operator makes during the booking phase. Ops must make each one fast, confident, and auditable.

**Decision 1: "Is this trip ready to book with the supplier right now?"**
This is the daily question. The operator needs to know — before calling the hotel or airline — whether they have all required data. Currently, the readiness tier system answers this correctly at a data level, but the page does not present it as a primary orientation point. This decision should take 3 seconds.

**Decision 2: "What do I do next on this trip, and by when?"**
This is the sequencing question. The operator has 8 trips open. For each one they need the single next action, who is waiting, and whether anything is overdue. Currently, this requires reading through tasks, pending submissions, document statuses, and timeline events across multiple sections. This decision currently takes 2–3 minutes of scanning.

**Decision 3: "Has the customer paid what they agreed to, and is there a balance due?"**
This is the cash question. Payment status affects whether to issue documents, whether to confirm with the supplier, and whether to chase the customer. Currently, the operator must open the booking data edit view to see payment amounts and status. A glanceable payment status widget at the top of Ops would eliminate a multi-click flow for the most frequent financial check.

**Decision 4: "Do the supplier confirmations match what we quoted?"**
This is the margin integrity question. Operators rarely audit this systematically — they rely on memory. An automated diff between accepted quote line items and received confirmation details would surface discrepancies automatically. This is currently completely absent.

**Decision 5: "If something goes wrong, who did what and when?"**
This is the accountability question, which matters both for internal accountability (which agent changed this field?) and for supplier disputes ("we confirmed on May 10, here is the record"). The timeline audit log supports this, but it is currently passive and buried at the bottom of a very long page.

---

## 5. Ideal Page Layout

The ideal Ops layout is oriented around current state and next action, not data collection sections. Here is the recommended section order and what each shows:

**[A] Next Action Banner (top, always visible)**
A single computed statement: the most urgent action and who owns it.
Examples: "Waiting for customer to submit data (link sent 2 days ago)" / "3 booking tasks ready — no blockers" / "Confirmation for Taj Hotels has not been entered" / "Payment deposit overdue by 1 day"
This is not a settings field — it is a computed readout derived from all other Ops state. One banner. One thing.

**[B] Booking Readiness Strip (below banner)**
A compact horizontal strip: three tier pills (Tier 1 / Tier 2 / Tier 3) each showing ready/not-ready. Clicking a pill expands to show met/unmet fields. This replaces the current full readiness tier card layout and takes ~1/4 the vertical space. Missing-for-next fields appear inline if any tier is not ready.

**[C] Payment Status Card (full width, below readiness)**
Agreed amount / amount paid / balance due / payment status — readable without entering edit mode. Edit button opens inline form. Refund section only appears if refund_status is not `not_applicable`. Supplier deadline integration (when built) attaches here.

**[D] Pending Customer Submission Banner (conditional, amber highlight)**
Appears only when `pendingData` exists. Shows submitted traveler rows with Accept/Reject. Disappears once actioned. Currently rendered in the right place conceptually, but visually equivalent to all other sections — it should be visually elevated (amber border, top-of-content placement, not buried after readiness).

**[E] Traveler Data + Documents (combined, per-traveler organization)**
Each traveler gets one row: name, DOB, passport status, collection link status (has submitted / not yet), and their own documents (passport, visa) as inline attachments. This replaces both the flat traveler table and the flat document list. When a traveler row is expanded, document upload, extraction, and apply actions appear in context. Identity documents live with the traveler they belong to.

**[F] Supplier Documents + Confirmations (combined)**
Documents of type `hotel_confirmation`, `flight_ticket`, `insurance`, and `other` grouped by supplier/component. Each supplier row shows: booked component, confirmation reference, doc attachment, and (when diffing is built) a delta indicator against the accepted quote line item. This is where "we quoted X, supplier confirmed Y" becomes visible.

**[G] Booking Execution Tasks**
Current `BookingExecutionPanel` content. Task cards with status, assignee-type, and blocking reason. Eventually, tasks are generated from accepted quote segments (each supplier = one task set). For now, they remain manually managed.

**[H] Execution Timeline (collapsed by default, expandable)**
The current `ExecutionTimelinePanel` content. Collapsed to a "N events, last activity: X" summary row by default. Expanding shows the full actor-typed log. This preserves auditability without dominating the page layout for trips that are actively executing.

**[I] Collection Link Management (moved to utility section or drawer)**
The collection link generator is an operational utility, not a section. It should be accessible via a button in the traveler data section (inline with the specific traveler or via a trip-level "Send data collection link" action), not a standalone top-level card.

---

## 6. What to Build Next

These are concrete, sequenced, buildable slices. Each is independent of the others.

**Slice 1: Next Action Banner (highest leverage, 1–2 days)**
Implement a `computeNextAction(trip, bookingData, tasks, documents, confirmations)` pure function that returns `{ priority: 'high' | 'medium', actor: 'agent' | 'customer' | 'supplier', message: string, daysOverdue?: number }`. Render it as a single full-width banner at the top of Ops. No new API endpoints needed — all inputs already load on mount. This is the single change that most immediately answers the operator's orientation question.

**Slice 2: Payment Status Card (extracted from edit form, 1 day)**
Extract the payment display block from the inline booking data editor into a standalone read-only card. Payment status, agreed/paid/balance, and refund status should be readable without clicking "Edit." Edit button opens the existing form. Zero functional change — this is a layout and component extraction task.

**Slice 3: Per-traveler document organization (2–3 days)**
Group the documents list by traveler when `doc.traveler_id` is set, with a fallback "Trip Documents" group for non-traveler-linked docs. The traveler row shows the traveler data inline. Document actions (accept, reject, extract, apply) remain identical. The change is grouping and rendering, not API shape.

**Slice 4: Confirmation vs. quote diff indicator (3–4 days)**
Add a `quoted_value` field to ConfirmationPanel records (or a separate comparison record). When a confirmation is entered, compare the confirmed price/dates/room type against the accepted quote's corresponding line item. Show a delta badge on the supplier row: green (matches), amber (minor variance <5%), red (significant variance or mismatch). This requires extending the confirmation data model and potentially reading the accepted proposal output from the trip record.

**Slice 5: OpsPanel component decomposition (2 days, architectural prerequisite)**
Extract the 34+ state slices into 5–6 focused hooks: `useBookingData`, `useCollectionLink`, `usePendingData`, `useDocuments`, `useExtractions`. Each hook encapsulates its own fetch, mutation, and error state. OpsPanel becomes a layout composition of focused sub-components. This is not a user-visible feature, but it is the prerequisite for every subsequent feature without introducing new performance problems.

---

## 7. What Not to Build Yet

**Client-facing views inside Ops.** The collection link public page is correctly separated. Do not add a "preview what the customer sees" toggle, a customer-facing payment portal link, or any shared-link generation for anything other than the existing traveler data collection form. Client-facing surfaces require their own UX, auth, and data-scoping review — they are a separate product layer.

**Automated supplier communication.** Email drafts to hotels, automated booking confirmations, WhatsApp integration — these are compelling eventually, but they require supplier profile management, communication templates, and delivery audit trails that do not exist yet. Building communication before the data layer is solid produces debt immediately.

**Multi-trip dashboard / batch operations.** A view across all trips showing payment statuses, overdue tasks, and readiness at a portfolio level is extremely valuable for a 10-person agency. But it requires the per-trip Ops data to be reliable and complete first. Build depth before breadth.

**Public booking status page for travelers.** "Your booking is confirmed" pages are a nice retention touch. They require a public auth layer, trip-level exposure controls, and design that will not reuse internal Ops components. Too early given current surface area.

**AI-generated task lists from quote.** Eventually booking tasks should be generated automatically from the accepted quote structure (one task set per supplier, pre-populated with confirmation requirements). This is high-value but requires the quote/output data model to be stable and queryable. Do not build the generator until the source data is reliable.

**Payment processing integration.** Razorpay, Stripe, bank transfer reconciliation — none of this should be touched until the status-tracking model is battle-tested. Payment tracking is explicitly marked `tracking_only: true` in the current model, and that constraint should be preserved.

---

## 8. Risks / Failure Modes

**Risk 1: Next Action becomes a false authority.**
If `computeNextAction` makes wrong inferences — e.g., showing "Waiting on customer" when the agent already has the data but hasn't marked the task done — operators will stop trusting it within a week and start ignoring it. This is worse than not having it, because it adds noise to the top of the page. Mitigation: start with a narrow set of confidently-derivable signals (pending submission exists, task in waiting_on_customer state, document in pending_review) before adding heuristics.

**Risk 2: Per-traveler document grouping breaks for edge cases.**
Documents uploaded without a traveler association (e.g., a group insurance document, a visa covering all travelers) will fall into a "Trip Documents" group that has no clear owner. If this group becomes a dumping ground, the per-traveler organization advantage is lost. Mitigation: require document-to-entity assignment at upload time, with an explicit "applies to all travelers" option.

**Risk 3: Confirmation diff creates friction without trust.**
If the quote data model is imprecise (ranges, approximate costs, "from" pricing), every confirmation will show a "variance" badge even when the booking is correct. This creates alert fatigue. Mitigation: only diff fields that have exact, confirmed values in the accepted quote; skip fields marked as estimates or ranges.

**Risk 4: Component decomposition breaks existing tests.**
The current test suite targets OpsPanel data-testid attributes directly. Decomposing into sub-components without updating tests will produce false failures. Mitigation: preserve all data-testid values on their existing DOM nodes during decomposition; update snapshot fixtures once.

**Risk 5: Page length creates scroll blindness.**
Adding a Next Action banner at the top helps orientation, but if the page remains 8+ full sections long, operators will still miss items at the bottom (timeline, confirmations). Mitigation: collapsed-by-default sections (timeline, collection link management) reduce length for the common case; implement section-level expand/collapse before adding more sections.

**Risk 6: Sub-tabs fragment the audit trail.**
If Ops is divided into separate tabs (Data / Documents / Payments / Tasks / Confirmations), operators working quickly will leave a tab without seeing a blocking issue on another tab. The audit trail becomes harder to read holistically. Mitigation: if tabs are introduced, maintain a cross-tab "needs attention" count badge per tab so unresolved items surface regardless of which tab is active.

---

## 9. Three Strongest Insights

**Insight 1: Ops is a state machine, not a form.**
Every section of Ops (data collection, documents, payments, tasks, confirmations) is a node in a trip-level state machine. The real product question is not "what data do we store?" but "what state is this trip in, and what are the valid transitions from here?" The Next Action banner is not a feature — it is the interface making the state machine visible. Competitors build form-heavy tools. Waypoint OS should build state-transition tools. The difference is whether operators are filling in boxes or navigating a process.

**Insight 2: Auditability is a product feature, not just a compliance artifact.**
Small agencies lose disputes — with suppliers, with customers, with payment processors — because they cannot prove what happened when. The execution timeline, source attribution badges, extraction conflict history, and 409 conflict guards are not defensive engineering. They are the product's liability moat. An agency that can produce a timestamped, actor-attributed record of "customer submitted data on day 3, agent accepted on day 4, booking confirmed on day 5" is operating at a professional tier that spreadsheets and most SaaS tools cannot match. Every audit feature is a sales feature.

**Insight 3: The collection link is the customer relationship touchpoint.**
The link generation UI is currently treated as an internal plumbing utility — generate, copy, revoke, done. But from the customer's perspective, the moment they receive that link is the moment the agency relationship becomes professional or amateur. The link experience (when it expires, how many times it can be submitted, what happens after submission, whether the agency acknowledges receipt) is as important as anything else on the page. The operator who generates a link is making a customer promise. Ops should treat link management with the UX care of a CRM action, not a developer utility.

---

## 10. One Surprising Idea

**The Execution Timeline should be the primary coordination primitive, not the bottom appendix.**

Right now, the timeline is the last section — a post-hoc log that nobody checks until something goes wrong. Flip the mental model: make the timeline the spine of the Ops page, and have every other section (readiness, data, documents, tasks, confirmations) render as cards that "attach to" the timeline rather than stand-alone panels.

Concretely: each booking task, document upload, payment update, and confirmation entry is a timeline event with a type. The operator sees a chronological view of what has happened and what is next. "Customer submitted data (3 hours ago) → Agent accepted (2 hours ago) → Passport extraction applied (2 hours ago) → Book Taj Hotels [READY]" tells a complete story in 4 lines.

This reframe changes the product narrative from "a data collection tool with a timeline at the bottom" to "an operations log with editing capabilities" — which is exactly how senior travel consultants mentally model an active booking. The audit trail is not a feature of the tool; it is the tool.

Competitors will never discover this because they are building from the checklist metaphor outward. Waypoint OS has the data model to do it today because the timeline is already actor-typed and the 7-status state machine is already event-generating.

---

**The thing most people miss about this:**

The value of Ops is not what it stores — it is what it makes unnecessary to remember. A 3-person agency that uses spreadsheets is not slow because the spreadsheet is slow; it is slow because each agent carries a mental model of every active trip that must be reconstructed from scratch each time they open it. Every section of Ops that reduces reconstruction time — the Next Action banner, the readiness strip, the payment card, the source badge, the conflict guard — is worth more than the feature itself, because its real output is agency-wide working memory that no individual agent needs to maintain. The "20-person operation" effect is not about adding staff features; it is about externalizing the cognitive load that currently lives in three people's heads.
