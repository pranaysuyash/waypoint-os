# Brainstorm Synthesis: Trip Workspace Ops as Booking Execution Master Record
**Date:** 2026-05-14
**Source roles:** 9 — Operator, Skeptic, Executioner, Cartographer, Strategist, Archivist, Future Self, Champion, Trickster
**Role files:** `Docs/brainstorm/roles/ops-next/`
**Subject file:** `frontend/src/app/(agency)/workbench/OpsPanel.tsx` (1399 lines)

---

## Product Thesis

Trip Workspace Ops should become the single execution cockpit where a 3-person agency can open any active trip, understand what to do next in under 3 seconds, and close gaps between "data we have" and "booking we need to make" — without switching to a spreadsheet, WhatsApp thread, or supplier portal.

The current Ops page is an excellent **reference tool**. It is 20% of the way to being a **force multiplier**. Every next product decision should be evaluated against: "Does this make the right operator action more obvious, or does it make the page more complete?"

---

## 1. What All 9 Roles Agree Is Right About the Current Page

These are the genuine strengths — do not accidentally break them:

- **`bookingDataSource` badge** (`agent` / `customer_accepted`) is a trust signal that will become a liability defense layer. Every competitor omits this.
- **409 optimistic-lock on booking data save** is production-grade correctness. Multi-agent overwrites in a 3-person office are realistic; silent loss is unacceptable.
- **Pending customer submission review** (explicit Accept/Reject) is architecturally correct. Customer data does not auto-apply. The amber-bordered review card is visually correct — treat it as a hot item.
- **Document extraction with field-level confidence and conflict detection** is genuinely rare. The `extract → field-select → confidence scores → conflict delta → apply` flow is the competitive moat. Most competitors do "has passport: yes/no."
- **7-status booking task state machine** (`not_started / blocked / ready / in_progress / waiting_on_customer / completed / cancelled`) reflects real booking workflow vocabulary. It is not over-simplified.
- **Stage gate (proposal/booking only)** is correct product discipline.
- **ExtractionHistoryPanel** shows provenance for why a field has a particular value. Do not remove it.
- **`payment_tracking` scoped as status-only** with `tracking_only: true` is honesty, not limitation. Do not add payment processing.

---

## 2. What All 9 Roles Agree Is Wrong

These are the definitive gaps — none is contested:

**Missing: The "What do I do right now?" question**
The page answers "what data do we have?" It does not answer "what must I do in the next 15 minutes to advance this trip?" Readiness tiers, flat document lists, and payment blocks are all status reports. Zero of them are dispatch instructions. A small agency operator opening 12 trips needs triage, not a filing cabinet.

**Readiness is in the wrong position**
Readiness tiers are diagnostic output — the *input* to a next-action decision, not the decision itself. Rendering them first is like showing a patient their full blood panel before telling them whether they need surgery. The tiers belong in a detail view; the derived action belongs at the top.

**Payment has no temporal structure**
`PaymentTracking` has `agreed_amount`, `amount_paid`, `balance_due`, `payment_status` — all present-state fields. There is no `final_payment_due` date. An operator with a 30-day final payment deadline carries that date in their head or in a spreadsheet. This is a financial risk invisible to the system.

**Payment is coupled to traveler data in `handleSave`**
Lines 329–356: a single save writes `travelers + payer + payment_tracking` atomically. These are different operator concerns on different cadences. A 409 on a payment status update blocks a traveler name correction, and vice versa. These must be independent save paths.

**Documents are a flat list with no ownership context**
`documents.map()` at line 1149 renders all documents as peers sorted by upload time. Three travelers, each with a passport, visa, and insurance doc = 9 undifferentiated rows. An operator cannot answer "do I have a valid document for every traveler?" without manual counting.

**Extraction is buried in the wrong place**
The `extract → apply` flow (lines 1294–1369) is nested inline inside a document list row. For a trip with 3 travelers and 3 docs each, this creates 9 inline expansion zones. An operator applying a passport extraction is doing something that merits a dedicated surface, not a sub-control on list item 4 of 9.

**Timeline is passive and positioned last**
`ExecutionTimelinePanel` at line 1396 is the audit spine of the trip record. It is rendered after confirmations, after tasks, at the very bottom of a 1399-line component. Operators who check it during a client dispute have to scroll past everything to find it. The timeline is a first-class trust instrument disguised as an appendix.

**No "done" state**
Nothing tells an operator the trip's ops work is complete. There is no ops-level completion signal, no zero-state congratulation, no "all tasks done" indicator. "Nothing to do here" and "you haven't done anything yet" look identical.

**Developer context leaking into operator UI**
Line 1132–1133: a blue info banner reads "use this Ops panel for document upload, review, extraction, and apply. The dedicated /documents module remains staged…". This is implementation-planning copy in an operator interface. Remove it.

---

## 3. Divergent Tensions — Resolved

### 3A: Traveler-grouped vs. type-grouped documents

**8/9 roles say traveler-grouped.** Operator, Skeptic, Cartographer, Strategist, Archivist, Future Self, Champion, Trickster all converge on organizing documents per traveler.

**Executioner is the sole dissenter.** Reason: many documents (hotel confirmation, group insurance, tour voucher) belong to the trip, not a specific traveler. Type-grouping (all passports together, all confirmations together) avoids the "trip-level orphan" problem and is one `sort()` call away.

**Resolution: traveler-grouped wins, with a required fallback.**
The completeness question ("do I have a passport for every traveler?") is answered per-traveler, not per-type. Type-grouping cannot answer it. But Executioner's concern is architecturally correct: the current `BookingDocument` type has no enforced `traveler_id` field — grouping without it is inference, not fact. The correct implementation path is:

1. Add `traveler_id: string | null` as a first-class field on `BookingDocument` (required for traveler-level documents, null for trip-level)
2. Add the `traveler_id` assignment to the document upload form (currently only asks `document_type`)
3. Render per-traveler groups with a mandatory "Trip Documents" fallback group for null `traveler_id`

Trickster insight: "The reason documents are a flat list is that `BookingDocument` has `document_type` but no enforced `traveler_id`. Documents are trip-level, not traveler-level. Without that model change, any grouping is approximate and will mislead."

### 3B: Zone 4 sub-tabs (Tasks / Confirmations / Timeline)

**1/9 roles say sub-tabs: Cartographer.**
Cartographer's Zone 4 tab structure (Tasks | Confirmations | Timeline) is the most spatially coherent proposal in the set. The reasoning: these are distinct modes of attention, operators don't look at Tasks and Timeline simultaneously, and tabs eliminate scroll debt on a long page.

**8/9 roles say no sub-tabs yet:** Executioner, Trickster, Skeptic, Operator, Champion, Strategist, Future Self, Archivist.
Common reasoning: tabs fragment context; an operator working a booking needs to see task status while reviewing payment status; "critical action is in the Payments tab" gets missed during fast pre-departure checks; build when scroll is genuinely unusable.

**Resolution: No sub-tabs in this slice.** Cartographer's concern is valid for a trip with 15+ components. For a 1–5 person agency's typical 3–6 component trip, scroll + collapsed sections is sufficient. Validate with real trip usage data before adding tabs. Cartographer's Zone 4 structure is the correct target state for a future slice; Skeptic's "tabs are a trap" warning is the guard rail.

### 3C: Confirmation diff against proposed itinerary

**3/9 say build it:** Champion ("single highest-consequence quality guard"), Archivist ("most high-stakes missing feature"), Future Self (2027 hindsight: "the product that won agency deals" had this).

**Executioner kills it explicitly.** Reason: no structured join key between `ConfirmationPanel` records and proposal line items. Proposal output is unstructured (Markdown/prose). Building the diff requires: structured itinerary data model → itinerary-to-confirmation linking model → diff UI. Three separate slices.

Trickster, Strategist, and Cartographer all agree it's the right long-term vision but defer to the same dependency: structured quote/itinerary data.

**Resolution: Kill for this slice.** Executioner is technically correct. The data dependency (structured accepted quote) doesn't exist. Build data model first, defer diff UI. Champion's and Archivist's urgency is correct directionally but the prerequisite work is scoped separately.

### 3D: Tasks auto-generated from accepted quote

**Future Self, Champion, Archivist, Operator** all want tasks pre-populated from itinerary components.

**Executioner kills this:** "Auto-generation of tasks from a structured itinerary quote is valuable in principle. The problem is the same as the confirmation diff: the accepted quote/output is currently unstructured prose. Auto-generated tasks will be low-quality stubs that an operator has to edit anyway. Kill the smart version."

**Resolution: Defer.** Same structural dependency. Manual task creation stays until the proposal output has stable structured line items.

---

## 4. Convergent Page Architecture (Evidence from 8+ Roles)

The following layout is supported by supermajority across all 9 roles. No role opposes any of these structural choices (though sub-tabs and grouping choices have the caveats above).

```
[ PERSISTENT STRIP — always visible ]
  Trip name · Stage badge · Days to departure
  Readiness pulse: one-line summary + first blocker
  Payment health chip: agreed/paid/balance in one chip
  If pendingData: amber anchor "1 submission awaiting review"

[ SECTION 1 — Next Action Banner (THE hero element) ]
  Computed from existing state. One sentence. One button.
  Examples:
    "Customer submitted data 2h ago — [Review Submission]"
    "Missing: adult_2 passport number — [Edit Booking Data]"
    "Task blocked: Book Taj Hotels — [Open Tasks]"
    "Deposit due in 3 days — [Record Payment]"
  All-clear state: "No action needed — all checks passed" (green)
  Sources: pendingData → blocked tasks → readiness missing_for_next → pending_review docs

[ SECTION 2 — Data Intake (three sub-sections, one contiguous workflow) ]
  2A: Collection Link (top — it is the trigger for everything below)
      Status: active link (expires when) / no active link / no link ever generated
      Actions: Generate / Copy / Revoke
      If has_active_token: display the URL (fix the re-expose problem)
  2B: Pending Customer Submission (conditional — only when pendingData exists)
      Amber card with submitted data, Accept/Reject actions
      Compare submitted values vs. current canonical values inline
  2C: Booking Details (canonical record)
      Traveler table (traveler_id, full_name, DOB, passport_number, source badge)
      Payer information
      Edit button

[ SECTION 3 — Payments (standalone card, not inside booking data edit) ]
  Agreed / Paid / Balance Due / Status
  final_payment_due date field (new) — shows countdown if within 14 days
  Refund tracking collapsed unless refund_status != not_applicable
  Separate save path from traveler data

[ SECTION 4 — Documents (grouped by traveler) ]
  Per-traveler accordion: adult_1, adult_2, child_1...
  Each traveler group shows: passport slot, visa slot, insurance slot
  Missing document = red slot indicator visible without expanding
  Upload lives in traveler group header: "Upload for adult_1" + type selector
  Extraction results: expand below the specific document row (within traveler group)
  "Trip Documents" group at bottom for null traveler_id items

[ SECTION 5 — Booking Tasks ]
  Current BookingExecutionPanel content
  Blocked tasks show inline blocker reason
  Future: generated from accepted quote (prerequisite: structured itinerary)

[ SECTION 6 — Confirmations ]
  Current ConfirmationPanel content
  Future: diff against proposed itinerary (prerequisite: structured itinerary)

[ SECTION 7 — Execution Timeline (always last, but accessible) ]
  Current ExecutionTimelinePanel
  Add: last 2 events surfaced in Next Action banner as "Recent activity"
  Add: navigable links from events to the live record they describe
  Future: annotability (notes on events), anomaly detection
```

---

## 5. Code-Level Bugs Identified by Roles

These are concrete, implementation-specific issues from reading `OpsPanel.tsx`:

| Bug | Location | Severity | Description |
|-----|----------|----------|-------------|
| Memory leak | `handleDocDelete` (line 494–507) | Medium | `extractionSelections` and `extractionConflicts` are `Record<string, ...>` keyed by `doc.id`. `handleDocDelete` refreshes `documents` state but never calls `setExtractionSelections` or `setExtractionConflicts`. Stale keys for deleted documents accumulate unbounded in a long-running session. |
| Payment/traveler coupling | `handleSave` (lines 329–356) | Medium-High | Single save writes travelers + payer + payment_tracking atomically. A 409 conflict on payment blocks a traveler name correction. These are independent concerns with different cadences and different actors. |
| mode='documents' dead mode | Line 43, 34+ guards | Low-Medium | `mode='documents'` prop switches rendering via 34 `documentsOnly` guards, but all 34+ state variables and useEffect fetches run regardless of mode. Dead network traffic on every mount in documents mode. Future: remove the mode prop entirely or commit to enabling the /documents module. |
| Collection link re-expose | Lines 1038+ | Medium | When `linkInfo` is null but `has_active_token` is true, the operator is told "Active link exists" with no way to retrieve the URL. Operator who sent a link yesterday cannot verify it without revoking and regenerating. Fix: store last-generated URL in sessionStorage keyed on `tripId + tokenId`. ~15 lines. |
| Developer banner in Documents | Line 1132–1133 | Low | "use this Ops panel for document upload, review, extraction, and apply. The dedicated /documents module remains staged…" is implementation-planning copy visible to operators. Remove it. |
| 34+ independent useState framed as "independent slices" | Line 176 comment | Architectural | The code comment dismisses `useReducer` by saying the vars are "independent slices." They are not: `editing + conflict + saving + error + bookingData + updatedAt` are tightly coupled in atomic transitions (a 409 sets both `conflict` and clears `saving`). Misleading comment that will cause the wrong architectural decision at the next refactor. |

---

## 6. Extraction Pipeline — The Competitive Moat

**Champion's strongest insight:** "The extraction pipeline is a competitive moat, not a document feature. Most travel agency software treats document collection as a checklist ('has passport: yes/no'). The extraction pipeline — upload → AI extract → field-level confidence → human review → selective apply → conflict resolution → audit trail — is qualitatively different from everything else in the market. This is the feature that a 3-person agency uses to move at the speed of a 10-person agency."

**Current problem:** The pipeline is buried. It appears as an inline button on document list item N of M. An operator doesn't know they're in passport extraction for adult_1 specifically without reading the context carefully.

**Direction:** Elevate extraction to a first-class "Data from Documents" workflow card, not an action on a list item. The per-traveler document grouping (Section 4 above) naturally solves this by context-anchoring extraction to the traveler it applies to.

---

## 7. Timeline — The Underutilized Audit Spine

All 9 roles identify `ExecutionTimelinePanel` as the most undervalued section on the page. Specific improvements that are implementation-ready (no new data models):

**Immediate (rendering-only changes):**
- Surface last 2 events as "Recent activity" in the Next Action banner or section header
- Add navigable links from timeline events to the live record they reference (scroll-to anchor, not modal)
- Add collapsed summary: "N events, last activity X" when timeline is not the focus

**Near-term (minor model additions):**
- Operator note annotation on timeline events (append-only; cannot delete events)
- "Since your last visit" highlight using `last_viewed_at` timestamp (one backend endpoint, one derived render)

**Future (requires more work):**
- Anomaly detection layer: tasks `in_progress` > N days with no update, confirmations with unresolved discrepancies, payment overdue flags
- Actor filter: view by operator / customer / system events only
- **Archivist's immutability principle: operators cannot delete timeline entries. They can only annotate.** This must be a backend guarantee.

---

## 8. Surprising Ideas Worth Preserving

These are the Section 10 ideas from across all 9 roles that have asymmetric leverage:

**Executioner — Presence indicator on collection link**
"Customer viewed link 4 minutes ago" or "Customer is on step 2 of 3" derived from token access logs. Eliminates the most common operator support action: "Did the customer receive my link? Should I call them?" Requires no new data entry model — token access is already logged.

**Skeptic — Delta since last session**
On page open, show "Changes since your last visit" callout: "Customer submitted passport data (2h ago) · Task moved to waiting_on_customer (yesterday) · Payment updated to deposit_paid (3 days ago)." Costs one backend endpoint querying timeline events after `last_viewed_at`. Operators process the delta, not the full state — this is how a 3-person agency operates at 20-person throughput.

**Operator / Trickster — Trip Handoff Brief / Hand Off button**
One button that generates a single-screen snapshot: what was done today (last 24h timeline events), what is still open (Next Action), what decisions were deferred (tasks on hold), who is now responsible. All data already exists in OpsPanel. The output is a frozen read-only view stamped with handoff time and agent names. Eliminates institutional memory loss on evening/vacation handoffs.

**Champion — Collection link expires on stage advancement, not time**
Reframes collection link from a security feature (revoke after N days) to a workflow gate (revoke when data collection phase is over). When operator accepts all pending booking data and advances to booking stage, link auto-revokes. Customer sees: "Your travel agency has already locked in your booking details." Creates a natural moment of finality.

**Archivist — Time capsule note**
At booking handoff, operator writes a brief note: "Used supplier X because Y was unavailable. Customer was firm on room type. Watch for Z at check-in." Timestamped, attributed, locked. Surfaced prominently when the trip re-enters view. Preserves reasoning behind decisions otherwise buried in timeline or forgotten.

**Cartographer — Cmd+Shift+S client status summary**
Keyboard shortcut copies current trip status as natural language: "Your trip is in booking stage. We have your traveler details confirmed, all documents received, 3 of 5 tasks complete. Waiting on confirmation from [supplier]." No new API. No modal. Pure state synthesis. Saves 3 minutes per client call.

**Future Self — Operator execution fingerprint**
By 2028, the execution timeline becomes a per-operator execution fingerprint for mentorship and quality recovery. When a junior coordinator's task pattern diverges sharply from the agency's established pattern (tasks marked complete too fast, deadline fields blank), the system flags for senior review. Requires no new data — pattern analysis on timeline events already recorded.

---

## 9. What Not to Build

This list is constructed from cross-role kill analysis. Each item was proposed by at least one role and killed by at least two others with specific rationale.

| Feature | Kill Rationale |
|---------|----------------|
| Sub-tabs (Data / Documents / Payments / Tasks / Confirmations) | 8/9 roles against. Fragments cross-sectional context. Build when a single section exceeds one screen consistently — validate with real trip usage first. |
| Confirmation diff against proposed itinerary | Prerequisite (structured itinerary model) doesn't exist. Three separate slices required before the diff UI. |
| Tasks auto-generated from accepted quote (smart version) | Same dependency as confirmation diff: accepted quote is unstructured prose. Low-quality stubs operators will delete. |
| Payment linked to supplier deadlines | Supplier deadline data doesn't exist in the data model. Build deadline fields on booking tasks first. |
| Payment processing integration | `tracking_only: true` constraint is correct. PCI compliance, reconciliation, refund flows add a separate product surface. |
| Client-facing portal features inside Ops | Separate trust boundary, auth model, UX requirements. Collection link is the correct minimal public-facing surface. |
| AI-generated next actions from unstructured notes | Rule-based Next Action first. Operators need to understand why an action appears before AI-generated suggestions can be trusted. |
| Automated supplier communication (email, WhatsApp) | Requires supplier profile management, templates, delivery audit trails that don't exist. |
| /ops/tasks, /ops/confirmations route splits | Keep all data in one component tree. Sub-tabs as layout choice only, not route split. |
| Inline chat / AI suggestions inside Ops | Wrong surface. Workbench is AI processing. Ops is human execution. Keep the boundary clean. |

---

## 10. Three Strongest Insights Across All Roles

**1. Ops is a gap-closing cockpit, not a data repository**
(Trickster, Operator, Executioner — all converge on this)
Every section of OpsPanel exists because there is a potential gap between what is needed and what exists. The operator's job is not to manage data; it is to close gaps before they become booking failures. The moment you reframe the page from "repository of booking artifacts" to "gap-closing cockpit," every design decision changes: the Next Action header becomes obvious, traveler-grouped documents become obvious, payment deadlines become obvious, the timeline-as-spine becomes obvious.

**2. Auditability is a product feature, not a compliance artifact**
(Strategist, Archivist, Champion, Future Self — all make this case)
The `bookingDataSource` badge, 409 conflict guard, extraction conflict history, and `ExtractionHistoryPanel` are not defensive engineering. They are the product's liability moat. An agency that can show a timestamped, actor-attributed record of "customer submitted data on day 3, agent accepted on day 4, booking confirmed on day 5" wins supplier disputes and survives customer complaints. Future Self 2028 hindsight: "The provenance chain from document to booking record became the product's defensible moat." Every audit feature is a sales feature.

**3. The extraction pipeline is currently a hidden competitive advantage**
(Champion, most explicitly)
The `extract → field-level confidence → human review → selective apply → conflict resolution → audit trail` flow is architecturally sophisticated and operationally valuable. No competitor has it. The current bug: it is buried as a sub-control on a flat document list row. Elevating it — via per-traveler document organization — does not add capability. It surfaces the capability that already exists. The product's most differentiating feature is currently invisible.

---

## 11. Future Self's 2028 Hindsight Summary

Future Self's strongest meta-observation: "The 3-person agencies that grew to 12 did not hire 9 more senior agents. They hired 9 junior coordinators and used the product to constrain what junior staff could do wrong. The booking task state machine, the readiness tiers, and the Next Action card together gave junior coordinators a script: 'the system says do this, so I do this.'"

Every design decision should be tested against: **"Can a 6-month-in coordinator use this without asking a senior agent?"**

- Flat document list with global Extract button: **fails**
- Per-traveler document slots with missing-document indicators: **passes**
- Readiness tier table as first section: **fails**
- Next Action banner with one-sentence instruction: **passes**

---

*Source files: all 9 role outputs in `Docs/brainstorm/roles/ops-next/`, all dated 2026-05-14, written from full reads of `frontend/src/app/(agency)/workbench/OpsPanel.tsx`*
