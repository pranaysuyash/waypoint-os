# Brainstorm Role: Archivist — Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Topic:** What should Trip Workspace Ops become?

---

## 1. One-Sentence Thesis

Trip Workspace Ops should become the immutable chain-of-custody record for every decision, approval, data change, and money movement made on behalf of a trip — a surface that makes the operator's past actions as legible as their next ones.

---

## 2. What the Current Ops Page Gets Right

- **Provenance is tracked at the data layer.** `bookingDataSource` distinguishes `agent`-entered from `customer_accepted` — that is the seed of a real audit trail. The badge rendering in the Booking Details section surfaces this distinction correctly.
- **Conflict detection is explicit.** The optimistic-lock `409` conflict path — with a hard "Reload" gate — prevents silent overwrites. This is correct behavior and should never be weakened.
- **Pending-review is a gatekeeping step.** Customer-submitted data does not auto-apply; an operator must Accept or Reject. That decision point is exactly where accountability lives, and the current implementation correctly forces a human into the loop.
- **Extraction conflicts show the delta.** The `existing_value → extracted_value` diff in the conflict panel is the right primitive. The operator sees what would be overwritten before they authorize it.
- **The 7-status task state machine is real.** `not_started / blocked / ready / in_progress / waiting_on_customer / completed / cancelled` covers the actual lifecycle of a booking action. It is not simplified.
- **ExecutionTimelinePanel already exists.** An actor-typed event log is present. The foundation for a proper audit spine is already installed.

---

## 3. What It Gets Wrong

- **No timestamp on any operator decision.** When the operator clicks Accept on a pending submission, the action disappears. The record that it happened, who did it, and when is swallowed into the backend silently. The UI never surfaces "Accepted by [agent] at [time]."
- **Payment is attached to booking data, not to a supplier or deadline.** `payment_tracking` lives inside `BookingData` as a single flat struct. There is no link from a payment to the supplier invoice it settles, the due date it must hit, or the booking task it unlocks. A single trip might have hotel deposit due on May 20 and airline payment due May 25 — the current model conflates these into one undifferentiated blob.
- **Documents are a flat list sorted by upload order.** Passport for adult_1, passport for adult_2, visa for adult_1, insurance — all in the same bucket. Finding which traveler is still missing a document requires scanning the entire list mentally.
- **Readiness is displayed as a status report, not a decision aid.** The tier breakdown shows what is met and unmet but does not answer the only question that matters: "Can I press go on this booking right now, and if not, what one thing must I fix first?"
- **Confirmations are not diffed against the proposed itinerary.** A booking confirmation arriving with a different hotel room type, flight number, or date is a failure mode. The current ConfirmationPanel records the confirmation but has no mechanism to compare it against what was sold to the customer.
- **The timeline is passive.** ExecutionTimelinePanel receives a `tripId` and renders. There is no mechanism to append a note, mark a discrepancy, attach a reference number, or flag a timeline event as disputed. A read-only log cannot serve as an accountability spine.
- **No concept of "who was responsible."** Traveler data entries, document uploads, task state transitions — nothing carries an `operator_id` or `operator_name` visible on the page. In a multi-person agency, this is catastrophically absent.
- **Extraction history is per-document and buried.** The `ExtractionHistoryPanel` is nested inside the document row. An operator reviewing the trip two weeks later will not naturally discover that a passport extraction was run, partially rejected, then retried — unless they expand every document row.

---

## 4. The Top 5 Operator Decisions Ops Must Support

1. **"Is this trip ready to book?"** — Not a readiness score; a binary authorization. The operator must be able to look at one surface and decide "yes, proceed" or "no, here is what is blocking." This requires that readiness, pending data, missing documents, and overdue payments are synthesized into a single decision point.

2. **"Who approved this data, and when?"** — Every field that affects a booking (traveler identity, payment amount, supplier reference) must carry a visible chain of custody. This becomes the dispute-resolution record when a supplier claims different names were submitted, or a customer disputes an amount charged.

3. **"What is still owed, and by when?"** — Not total payment tracking; deadline-linked payment obligations. Hotel X requires deposit by date Y. Airline Z requires full payment by date W. The operator must see these deadlines alongside current payment status.

4. **"Does the confirmation match what was sold?"** — When a hotel or airline confirmation arrives, the operator must verify it against the accepted proposal. Any delta — room type, date, price, traveler name — is a defect that must be caught and resolved before travel.

5. **"What happened on this trip while I was away?"** — After two weeks of not touching a trip, the operator needs a durable, human-readable activity summary: data collected, documents received, tasks completed, payments made, confirmations received. Not a raw event log — a narrative summary with timestamps and actors.

---

## 5. Ideal Page Layout (Section Order and Content)

### Section 1: Trip Action Header (always visible, sticky)
- Large, contextual call to action: "3 items need your review" or "Ready to book — confirm traveler data before proceeding."
- Inline blockers listed as chips: [Passport missing — adult_2] [Deposit overdue — Hotel Amanemu] [Confirmation not received — IndiGo 6E-204]
- One primary button per highest-priority action.
- Not a status report; a decision surface. Re-evaluates on every data change.

### Section 2: Readiness Gate (collapsed by default when green, expanded when blocking)
- Binary: Ready to Book / Not Ready to Book.
- When not ready: exactly one highest-priority blocking item, with a link/anchor to where it can be resolved.
- When ready: a collapsible summary of what was verified and when.
- The detailed tier breakdown stays here but is secondary.

### Section 3: Traveler Dossiers (one card per traveler, not a flat list)
- Each traveler gets a card: identity fields, documents attached to them, extraction history for their documents, visa/passport signals.
- Missing document is visible at-a-glance per traveler: "adult_2 — passport: not received."
- Agent-collected vs. customer-submitted badge stays per field, not per record.
- Pending customer submission review stays inline, scoped to the affected traveler.

### Section 4: Payment Obligations (linked to suppliers and deadlines)
- One row per payment obligation, not one global blob.
- Each row: supplier name, amount agreed, due date, amount paid, status, payment reference, proof link.
- Deadline proximity surface: overdue rows in red, due within 7 days in amber.
- Payer information shown once at the top of this section, not buried in booking data.
- Refund tracking is a sub-section, not co-equal with active payment obligations.

### Section 5: Booking Tasks (generated, not hand-typed)
- Tasks populate from the accepted quote: one task per bookable supplier component.
- The 7-status machine stays exactly as-is — it is correct.
- Blocked tasks show the specific blocking reason (missing field, document not accepted, payment overdue).
- Completed tasks show the completion timestamp and the operator who completed them.

### Section 6: Confirmations vs. Proposed Itinerary
- For each confirmed booking component, a side-by-side diff: proposed vs. confirmed.
- Green = matches. Amber = minor delta. Red = substantive mismatch requiring operator action.
- Unconfirmed components shown explicitly: "Awaiting confirmation — Hotel Taj, check-in 14 Jun."

### Section 7: Documents (organized by traveler and type)
- Primary grouping: traveler → document type.
- Agency-owned documents (insurance, group visa letter) get their own group outside traveler cards.
- Extraction history surfaces as a summary line per document: "Extracted 14 May — 3 fields applied — 1 field overridden by agent."

### Section 8: Execution Timeline (active audit spine)
- Full event log with actor, timestamp, event type.
- Operator can append a note to any event: "Supplier confirmed verbally before system update."
- Operator can flag a discrepancy on any event: "This confirmation does not match the proposal."
- New note or flag creates a new timeline entry, preserving the immutability of earlier entries.
- Operators cannot delete timeline entries. They can only annotate.

---

## 6. What to Build Next (Specific and Concrete)

**The highest-value next slice: Decision stamp + Timeline annotability.**

Specifically:

1. **Stamp every operator decision in the timeline.** When Accept or Reject is clicked on pending data, when a document is accepted or rejected, when a task moves to `completed` — write a timeline entry that includes `operator_id`, `action`, and `timestamp`. Surface the most recent decision stamp on each affected section header. Cost: low. Accountability value: extremely high.

2. **Restructure the documents section by traveler.** Group documents under traveler cards derived from `bookingData.travelers`. An "agency documents" group handles everything not traveler-specific. Upload UI persists as-is but adds a traveler selector. No backend changes required if documents already carry a traveler reference — just a UI grouping change.

3. **Add a per-payment-obligation row model.** Introduce a `payment_obligations` array alongside `payment_tracking`. Each obligation: `supplier`, `amount`, `due_date`, `status`. The existing flat `payment_tracking` stays as-is for backward compatibility. New rows render as the payments list. Due-date proximity coloring costs zero backend work if the date is stored.

These three changes together move Ops from a data entry form to a legible chain-of-custody surface in one sprint.

---

## 7. What Not to Build Yet

- **Client-facing ops view.** The trip workspace is an internal operator tool. Customer-facing status pages belong to a separate public surface with controlled read projection. Do not add customer-visible toggles or "share this view" features to Ops.
- **Automated booking execution.** The BookingExecutionPanel should not gain "click to book via supplier API" capabilities in this phase. The 7-status machine should be human-driven. Automation belongs in a later release, after the audit trail is solid enough to reconstruct what any automated action did and why.
- **Sub-tab navigation.** Tabs (Data / Documents / Payments / Tasks / Confirmations) are appealing but premature. The Archivist's concern: sub-tabs fragment the audit view. An operator reviewing a disputed trip should see everything in sequence, not have to navigate tabs to reconstruct events. Sub-tabs belong after the content within each section stabilizes, not before.
- **Payment gateway integration.** Linking payment references to external payment processors (Razorpay, Stripe, wire transfer records) is high-value eventually but requires careful data governance. Not this slice.
- **Bulk document upload / multi-file.** Single-file upload with type selection is sufficient. Bulk upload creates edge cases around extraction assignment and conflict resolution that are not worth solving now.

---

## 8. Risks and Failure Modes

- **The timeline becomes a post-hoc rationalization tool.** If operators can add notes freely, some will use notes to explain away decisions made incorrectly rather than to document what actually happened. Mitigation: notes annotate events, they do not replace them. The underlying event is immutable; the note is visibly distinguished from the system-generated record.

- **Traveler grouping breaks when traveler_id is inconsistent.** The document-by-traveler grouping depends on documents carrying the right `traveler_id`. If agents upload documents without selecting a traveler, or if `traveler_id` format drifts between the booking data and the document store, the grouping will fragment. The current extraction flow already shows this risk: the traveler selector dropdown is populated from `bookingData?.travelers`, meaning documents uploaded before booking data exists will have no valid grouping target.

- **Payment obligations without deadlines are noise.** If the `due_date` field is optional and most agencies leave it blank, the deadline-proximity feature becomes invisible. Mitigation: surface an inline nudge on save when `due_date` is absent: "Adding a due date enables overdue alerts."

- **Confirmation diffing requires the proposed itinerary to be structured.** A diff against "the accepted quote" is only possible if the quote is machine-readable. If quotes are PDF attachments or free-text notes, the diff surface cannot work. This is a dependency on upstream proposal structure that should be explicitly documented before building the confirmation diff feature.

- **Operator identity is not established.** The current system does not appear to pass authenticated operator identity down to the OpsPanel in a way that would appear in timeline entries. Before decision stamps can show "Accepted by [agent name]," the auth context must be available and passed through. Verify this before assuming the feature is low-cost.

- **The page grows to 2000 lines.** OpsPanel is already 1399 lines. The proposed additions — dossier grouping, obligation rows, decision stamps — will push it beyond maintainable size without decomposition. The correct path is to extract traveler dossier, payment obligations, and readiness gate into named sub-components before adding new features.

---

## 9. Three Strongest Insights

**Insight 1: The gap between data entry and accountability is exactly one timestamp and one actor.**
OpsPanel already captures every important decision (accept/reject/apply/overwrite). It just doesn't record them durably in a visible, attributed way. The audit trail is not missing — it is present in the backend event log and absent in the UI. Surfacing `operator + action + time` on every gatekeeping decision costs almost nothing and changes the entire character of the page.

**Insight 2: Documents without traveler ownership are just files.**
The current document list is useful for storage and workflow. It is useless for pre-travel verification ("do I have valid documents for every traveler?"). The moment documents are grouped by traveler, the question changes from "what files do I have?" to "is this traveler travel-ready?" — which is the question that actually matters.

**Insight 3: The confirmation diff is the most high-stakes missing feature in the entire Ops surface.**
An operator who manually moves a booking task to `completed` without verifying the confirmation against the itinerary has created a liability gap. Booking errors — wrong name on a ticket, wrong hotel room category, wrong travel date — are often caught only at check-in, when the cost of fixing them is maximum. A confirmation diff running automatically against the accepted proposal would catch these failures at the moment the confirmation arrives. This is the feature that turns Ops from a workflow tracker into a quality control gate.

---

## 10. One Surprising Idea

**A "time capsule note" field on every trip — written by the operator at booking handoff, readable only after travel returns.**

When an operator confirms all booking tasks are complete and the trip is ready to execute, they write a brief note: "Used supplier X because Y was unavailable. Customer was firm on room type. Payment was made 3 days early because supplier requested it. Watch for Y issue at check-in."

This note is timestamped, attributed, locked, and surfaced prominently when the trip comes back into view — either for post-trip review, a refund dispute, or a follow-up booking. It is not an audit log entry. It is an operator writing a letter to their future self about what they were thinking at the moment of handoff.

Small agencies lose institutional knowledge when operators switch, take leave, or handle volume spikes. The time capsule note is the lowest-effort way to preserve the reasoning behind decisions that are otherwise buried in a timeline or simply forgotten.

---

**The thing most people miss about this:**

The audit trail is not for regulators or lawsuits — it is for the operator on a Tuesday morning returning to a trip they last touched two weeks ago and trying to remember whether they accepted that customer submission or whether the customer actually sent the right passport number this time. The primary consumer of every audit record is the operator themselves, acting as their own future investigator. Every decision stamp, every conflict resolution record, every "why I did this" note is written for that Tuesday morning moment. Design the audit trail for routine re-entry, not for rare disputes, and you will accidentally also build something that holds up under rare disputes.
