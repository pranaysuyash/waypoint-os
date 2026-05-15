# Brainstorm Role: Executioner — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-Sentence Thesis

Ops must become the single, ordered checklist that tells one operator exactly what to do next, and makes every past action auditable without requiring them to read a log.

---

## 2. What the Current Ops Page Gets Right

**The data model is sound.** Traveler records, payment tracking, document lifecycle (upload → pending_review → accepted/rejected → extract → apply), booking task state machine (7 statuses), confirmation records (draft → recorded → verified/voided), and the typed execution timeline are all doing real work. None of these need to be rethought — they just need to be surfaced better.

**The 409 conflict guard on booking data saves operators from silent overwrites.** This is a correctness investment that will matter at scale when two tabs or two agents touch the same trip. Most products don't build this; it's here and it's right.

**Document extraction with conflict detection is genuinely hard and genuinely built.** The extract → field-select → apply → conflict-override flow handles a real problem (passport data differs from what the customer typed) with a real workflow. Operators who use it will trust it. Competitors don't have it.

**The stage gate (proposal/booking only) is correct product thinking.** Ops sections that make no sense before a proposal is accepted should not be visible. The gate is properly placed.

**ExtractionHistoryPanel shows provenance.** Knowing *why* a field has a particular value (which document, which extraction, which operator action) is the foundation of a trustworthy audit trail. It exists. Most products don't bother.

**Payment tracking is scoped correctly as status-only.** The "Status-only tracking" label and the `tracking_only: true` flag are explicit about what this is. It doesn't pretend to be a payment processor. That's honesty, not limitation.

---

## 3. What It Gets Wrong

**There is no concept of "what to do next."** The page opens with a readiness tier display (opaque letter codes, met/unmet lists) that tells an operator the system state but never translates it into an action. A small agency operator does not want to interpret tier logic — they want to be told: "Send the collection link. You are missing DOB for adult_2."

**Readiness tiers are displayed as raw data structures, not as operator guidance.** `tier.met.join(', ')` and `tier.unmet.join(', ')` render raw field names like `date_of_birth`, `passport_number`. These are internal identifiers. An operator sees "date_of_birth" and must infer what to do. This is systems UI, not product UI.

**The extraction UI is embedded inside the document list row.** The apply-extraction workflow (traveler selector, field checkboxes, conflict resolution, overwrite confirmation) is rendered inline in a flat document list item. This creates a deeply nested, contextually confusing interaction: the operator is in a document row but is actually editing booking data. The two concerns — document management and data population — are conflated by the current layout.

**Payment tracking and traveler booking data live in the same edit form.** The `handleSave` function writes travelers + payer + payment_tracking together. These are different operator concerns on different cadences: traveler data is collected once early; payment tracking evolves across the booking lifecycle. Coupling them to a single save creates confusion about what changed and when.

**`documentsOnly` mode prop is a fake abstraction.** The `mode` prop switches between `'full'` and `'documents'`, gating entire sections with `{!documentsOnly && ...}`. This is not a genuine product distinction — it's a layout workaround. The 34+ state variables all initialize regardless of mode. This means loading, fetching, and error state for booking data, collection links, and pending data all run even when the panel is in `'documents'` mode. Dead network traffic on every render in that mode.

**`extractionSelections` state is keyed by `doc.id` but never cleared when a document is deleted.** `handleDocDelete` calls `fetchDocuments()` which updates `documents` state but does not call `setExtractionSelections`. Stale selection state for deleted documents accumulates in memory across the session. Minor, but this is a correctness leak.

**The collection link and pending submission sections are not visually connected.** They are logically the same workflow (send link → customer submits → review pending → accept/reject) but appear as two separate bordered cards with no visible connection between them. An operator who generates a link does not have a visual signal that "pending submission review" is the downstream consequence of that action.

**BookingExecutionPanel, ConfirmationPanel, and ExecutionTimelinePanel are bolted on at the bottom.** Three separate `useEffect` + `useState` fetch cycles, three separate error states, rendered sequentially after the main OpsPanel content. They are decoupled components with no visual hierarchy signaling their relationship to the rest of Ops. The page has no spine.

**The timeline is completely passive.** `ExecutionTimelinePanel` renders `task_created`, `document_uploaded`, `confirmation_verified`, etc. with actor filters and category filters. It's a good audit log. It is not a decision-support surface. There is no connection between a timeline event and the current state of the record it refers to. Clicking a `task_completed` event does not show you which task it was. The log and the live record live in separate boxes with no hyperlink between them.

**34+ independent `useState` calls in one component is not just a linter warning.** The comment at line 176 dismisses the `useReducer` suggestion by saying the vars are "independent slices." They are not independent — `editing` + `conflict` + `saving` + `error` + `bookingData` + `updatedAt` are tightly coupled. A 409 conflict response sets both `conflict` and clears `saving`. A save success sets `bookingData`, `updatedAt`, `bookingDataSource`, and clears `editing`. These are atomic state transitions described by 5 separate `setState` calls in sequence. This is the definition of a case for `useReducer`. The comment suppresses the warning without addressing the substance.

---

## 4. The Top 5 Operator Decisions Ops Must Support

1. **"Is this trip ready to book, and if not, what one thing do I need to collect next?"**
   This is the most frequent question. It is asked on every trip, every day, by every operator. The current readiness tier display does not answer it. It shows system state. Operators need a decision, not a status code.

2. **"Has the customer submitted their data, and is it correct enough to proceed?"**
   The pending submission review section handles this but buries it mid-page and does not contextually connect it to the existing booking data for comparison. Operators should be able to see what changed, not just what was submitted.

3. **"What bookings am I actually executing right now, and what is blocked?"**
   BookingExecutionPanel provides this but lives at the bottom of a long page, after all the data-collection UI. The operator who is deep in the booking execution phase (not data collection phase) has to scroll past irrelevant-to-them sections to reach it.

4. **"Do I have all documents I need, and have I confirmed the bookings with suppliers?"**
   Documents and confirmations are currently in separate sections with no cross-reference. An operator booking a flight needs the passport accepted AND a flight confirmation recorded. These are linked facts that are never shown together.

5. **"What happened on this trip, and who did it?"**
   The timeline supports this but is passive. Operators need to trust the audit trail enough to use it defensively — when a customer disputes a change, or when an agency owner reviews a junior operator's work. That requires the timeline to be prominently accessible, not hidden at the bottom.

---

## 5. Ideal Page Layout

The page should have a single descending priority order: **what needs action now → what is in progress → what is complete and needs no attention**. This mirrors how operators actually work a trip.

**Section 1 — Next Action Banner (sticky, conditional)**
Shown only when there is something requiring operator action. Computed from: missing readiness fields + pending customer submission + blocked booking tasks + pending document reviews. One sentence. One button. Examples: "Collect DOB for adult_2 — send data link" / "Customer submitted data — review and accept" / "Flight booking task is blocked — needs attention." Disappears when there is nothing blocking. This is not a new data source — it is a computed digest of data already fetched.

**Section 2 — Booking Data + Collection Workflow (collapsed by default once complete)**
Traveler table, payer, collection link generation, and pending submission review in a single cohesive card. These are the same workflow; they should live together. The collection link status indicator (active / expired / no link) and the pending review banner should be inline with the traveler data, not in separate cards. When all traveler data is accepted and complete, this section auto-collapses with a green "Complete" indicator.

**Section 3 — Payment Status (one card, never collapsed)**
Separate from traveler data. Agreed amount, amount paid, balance due, status. Edit is separate from the traveler data edit. Payment status changes on a different cadence (deposit → partially paid → paid → refunded) and should not be coupled to traveler form saves.

**Section 4 — Documents (grouped by type, not flat list)**
Passport documents together, visa documents together, confirmation documents together, other together. Each group shows: count, accepted count, pending count. This is a one-line change to the existing rendering logic (sort/group by `document_type` before mapping). Extraction results should open in a side drawer or expanded card, not inline in the list row.

**Section 5 — Booking Tasks (the execution checklist)**
Currently BookingExecutionPanel, unchanged in function, moved up in visual priority relative to where it sits now. At proposal stage: shows task generation prompt if no tasks exist. At booking stage: shows the active task list with status. Blocked tasks show red. Ready tasks show green with a one-click "Mark in progress" button. This is the most action-dense section for an operator who is actively executing.

**Section 6 — Confirmations**
Currently ConfirmationPanel, unchanged. Recorded/verified confirmations for each booked supplier. One addition: each confirmation should reference whether a corresponding booking task exists (cross-link). This gives the operator a quick answer to "did I actually book this or just record that I did?"

**Section 7 — Timeline (always present, always at the bottom)**
Currently ExecutionTimelinePanel. The only change: each timeline event should be a link that scrolls to the relevant live record (task, confirmation, document). The log becomes navigable rather than read-only.

---

## 6. What to Build Next

**Specific recommendation: The Next Action Banner.**

Rationale for not killing it: This requires zero new API endpoints and zero new data models. Every piece of information it needs is already fetched: `readiness?.missing_for_next`, `pendingData`, `tasks` from BookingExecutionPanel, `documents` with `pending_review` status. The computation is a priority-ordered `if` chain: pending customer submission first (most urgent), then blocked tasks, then missing readiness fields, then pending document reviews. One utility function, one banner component, one conditional render at the top of OpsPanel. Estimated implementation: 2–3 hours.

This is the highest behavioral-change-per-engineering-hour item in the entire backlog. An operator who opens a trip and immediately knows what to do next is 30% faster. Nothing else on the list comes close to that ratio.

**Why it survives the kill test:** It does not require data that doesn't exist. It does not create a new editable surface. It does not duplicate anything. It does not require backend changes. It is pure UI synthesis of existing state. And it directly changes operator behavior on every trip they open.

Secondary recommendation: **Separate payment tracking from the traveler data edit form.** Extract `editPaymentTracking` state into a standalone `PaymentTrackingCard` component with its own save handler. The backend call signature does not need to change — `updateBookingData` accepts the full `BookingData` object. The frontend just stops coupling two different operator workflows to a single save button. This is a refactor with a functional payoff: payment status can now be updated without re-entering traveler data, and the 409 conflict on payment status no longer threatens traveler data saves.

---

## 7. What Not to Build Yet

**Sub-tabs (Data / Documents / Payments / Tasks / Confirmations)**
Kill rationale: Sub-tabs solve a navigation problem that does not yet exist at 1–20 person agency scale. When a trip has 3 documents, 4 tasks, and 1 confirmation, tabs create overhead without benefit. The operator now has to click between tabs to get a complete picture of a trip they could see on one scrollable page. Sub-tabs make sense when a single section has enough content to warrant isolation — that threshold is not reached in the typical booking. Build when a specific section exceeds one screen height with regularity. That is not today.

**Confirmations diffed against the proposed itinerary**
Kill rationale: This requires a canonical structured itinerary data model — supplier name, service dates, quantities, prices — to exist in the trip record. Looking at the current `ConfirmationPanel`, confirmations have `supplier_name`, `confirmation_type`, `confirmation_number`, `notes` free text. The itinerary on the proposal side is unstructured (likely a Markdown/prose output). There is no structured join key between a confirmation and a proposal line item. To build this diff you would first need to structure the itinerary output, then add an itinerary-to-confirmation linking model, then build the diff UI. That is 3 separate product slices. Kill it for now. Revisit when the itinerary is structured.

**Payments linked to supplier deadlines**
Kill rationale: Supplier deadline data does not exist in the system. There is no `SupplierDeadline` model, no deadline fields in booking tasks, no payment schedule concept. To implement deadline-linked payments you need: supplier deadline records, a linking model between deadlines and payment milestones, notification/alert logic, and the UI. This is a standalone feature requiring new data model, new API surface, new backend logic. For a 1–20 person agency that tracks supplier deadlines in their head or a spreadsheet, the implementation cost is not justified by the behavioral change — they already know their supplier deadlines. Kill until there is clear demand signal from operators that the system should own this.

**Documents organized by traveler**
Kill rationale: Sounds logical but falls apart in practice. Many documents (insurance policy, hotel confirmation, tour voucher) belong to the trip, not a specific traveler. A passport belongs to one traveler. A hotel booking confirmation belongs to all travelers. Organizing by traveler creates an awkward "trip-level" bucket that immediately becomes the default catch-all. Grouping by `document_type` (which already exists on every document) is both simpler and more useful for the operator's actual workflow (finding all passports, finding all confirmations). Type-grouped rendering is one sort call away. Traveler-grouped rendering requires new metadata and creates the trip-level orphan problem.

**Booking tasks generated from the accepted quote/output**
Kill rationale (partial): Auto-generation of tasks from a structured itinerary quote is genuinely valuable in principle. The problem is the same as the confirmation diff: the accepted quote/output is currently unstructured prose. There is no machine-readable mapping from "4 nights at Hotel X, 2 adults" to "task: book Hotel X, quantity: 2 adults, dates: X–Y." `generateBookingTasks` already exists and presumably takes some trigger — but without a structured quote, it generates generic tasks rather than itinerary-specific tasks. This means auto-generated tasks are low-quality stubs that an operator has to edit anyway. Kill the smart version; the current manual/generate flow is fine until the quote output is structured.

**The active audit spine (promoting the timeline to decision-support)**
Kill rationale: The timeline as an active decision surface — where you can take action on a record by clicking a timeline event — is compelling but expensive. It requires bidirectional linking between timeline events and their source records, plus interactive state management from within the timeline. The passive log is already implemented and working. Adding navigable links from events to records (scroll-to, not modal-based) is the right incremental step. Full bidirectional actioning from the timeline is over-scoped for this slice.

---

## 8. Risks and Failure Modes

**Risk: The Next Action Banner becomes stale or wrong.** If the banner computes from cached state and the operator acts on the suggestion but the state has not refreshed, the banner will show a stale action. This is especially dangerous for pending submission review — if the customer revokes their submission between the operator loading the page and clicking the banner action. Mitigation: the banner should be computed from live state only, not persisted, and the underlying action handlers already handle 404/409 gracefully.

**Risk: The `documentsOnly` mode prop proliferates.** If the `/documents` module referenced in the canonical path hint ever launches, and it reuses `OpsPanel` in `documents` mode, the 34+ state variables that initialize regardless of mode will create silent performance waste in what is meant to be a focused document view. The mode prop is a code smell pointing at a component that does too many things. This will become expensive when the component grows further.

**Risk: Operators treat the timeline as a compliance record and get burned.** The timeline shows actor-typed events with timestamps. If an agency owner presents timeline data to a customer as proof of what happened, they need to trust it completely. Any gap — a task completed manually without a timeline entry, a document deleted without an event — destroys that trust permanently. The risk is not in the UI but in the backend event emission coverage. This should be audited before the timeline is promoted as an audit spine.

**Risk: Extraction state memory leak on document delete grows silently.** `extractionSelections` and `extractionConflicts` are both `Record<string, ...>` keyed by `doc.id`. `handleDocDelete` removes the document from `documents` state but leaves orphaned keys in both records. In a long-running session where documents are repeatedly uploaded and deleted, these records grow unbounded. Not a crash risk, but a correctness and memory risk.

**Risk: The page gets slower as more sections are added.** Each new panel (BookingExecutionPanel, ConfirmationPanel, ExecutionTimelinePanel) adds at least one independent `useEffect` fetch on mount. OpsPanel currently triggers 5–6 separate API calls on load. Adding sections without a loading strategy (lazy load on scroll, or a single batch endpoint) means every trip open becomes slower as the product matures.

**Risk: The "Next Action" concept creates false confidence.** If the banner says "Nothing blocking" and the operator ships the trip, but a non-modeled risk exists (visa requirement not caught, supplier has a cutoff the system doesn't know about), the banner's silence is read as clearance. The banner must never present completeness — only the single most urgent actionable item from modeled signals.

---

## 9. Three Strongest Insights

**Insight 1: The booking execution lifecycle has two distinct phases that Ops conflates into one page.** Phase A is data collection (traveler info, documents, payment status, collection links). Phase B is booking execution (tasks, confirmations, supplier communication). Most operators on a given trip are fully in one phase or the other. The current page renders both phases equally, at full fidelity, all the time. The right product move is not sub-tabs — it is an intelligently auto-collapsed layout where completed Phase A sections shrink to summary badges so the operator can focus on Phase B without scrolling past resolved work.

**Insight 2: The highest-value AI feature is already built but under-leveraged.** Document extraction with confidence scoring and conflict detection is technically sophisticated and operationally valuable. But it is buried inside a flat document list as a secondary button on a document row. The operator who uploads a passport and extracts it is doing something that saves 5 minutes of manual data entry per traveler per trip. That workflow deserves first-class placement, not inline nesting. Surface it as a first-class "Data from Documents" workflow card, not an action on a list item.

**Insight 3: The timeline is currently the most undervalued section on the page.** Every other section shows current state. Only the timeline shows *how* that state was reached — who changed what, when, and via which mechanism (agent, customer, system). For a 1–20 person agency handling a dispute, a refund request, or an ops review, the timeline is the only source of truth about sequence of events. It is rendered last and treated as a footnote. It should be treated as the accountability spine of the trip record.

---

## 10. One Surprising Idea

**The collection link should show the operator in real time when the customer is filling out the form.**

Right now, the operator generates a link, shares it, and then discovers the result only when `pendingData` is populated (which requires a page reload or polling). The customer could be halfway through filling out their passport details and the operator has no signal.

A presence indicator — even just "Customer viewed link 4 minutes ago" or "Customer is on step 2 of 3" derived from token access logs — would let operators know when to follow up (no activity 24 hours after link sent) versus when to wait (customer active right now). This requires no new data entry model. Token access is already logged by the collection link backend. It just needs to be surfaced.

This single UX signal would eliminate the most common operator support action: "Did the customer receive my link? Should I call them?"

---

**The thing most people miss about this:**

Ops is not a data entry form that happens to have a task list attached. It is an execution record — a durable document of what was agreed, collected, executed, and confirmed for a specific trip. The difference matters architecturally: a form optimizes for input; a record optimizes for trust, auditability, and recovery when things go wrong. The current OpsPanel builds the right data model for a record but presents it with the interaction patterns of a form. Every design decision about layout, section ordering, and feature priority should start from the question "what makes this record trustworthy and actionable?" — not "what fields does the operator need to fill in?"
