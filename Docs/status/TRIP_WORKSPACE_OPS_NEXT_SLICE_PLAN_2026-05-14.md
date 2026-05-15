# Trip Workspace Ops — Next Slice Implementation Plan
**Date:** 2026-05-14
**Status:** Ready to implement — synthesized from 9-role brainstorm
**Branch:** master
**Brainstorm source:** `Docs/brainstorm/TRIP_WORKSPACE_OPS_MASTER_RECORD_BRAINSTORM_2026-05-14.md`
**Role files:** `Docs/brainstorm/roles/ops-next/`

---

## One-Sentence Product Goal

Transform OpsPanel from a status dashboard into a decision surface by adding a `NextActionBanner` at the top that tells the operator exactly what to do next — computed from state already loaded on the page, requiring zero new API endpoints.

---

## Priority Order for Next Slices

| Slice | Name | Effort | Dependencies | Rationale |
|-------|------|--------|--------------|-----------|
| **S1** | Next Action Banner | 2–4 hours | None | 9/9 roles agree; highest behavioral change per engineering hour. |
| **S2** | Fix collection link re-expose | ~1 hour | None | 1-line sessionStorage fix; fixes a real operator workflow failure. |
| **S3** | Remove developer banner from Documents | 15 min | None | One delete. No operator should see this. |
| **S4** | Fix `extractionSelections` memory leak | 1–2 hours | None | Correctness fix; stale keys accumulate on document delete. |
| **S5** | Separate payment save from traveler save | 2–3 days | None | Decouples unrelated concerns; eliminates unnecessary 409 surface. |
| **S6** | `final_payment_due` field on PaymentTracking | 1–2 days | S5 | Adds temporal context to payment; feeds into S1 banner rules. |
| **S7** | Add `traveler_id` to BookingDocument model + upload form | 2–3 days | Backend model change | Prerequisite for traveler-grouped documents. |
| **S8** | Per-traveler document grouping | 2–3 days | S7 | 8/9 roles converge on this; requires S7 first. |
| **S9** | OpsPanel component decomposition | 2–3 days | None (independent) | Prerequisite for not making the file unmaintainable. Do before the page grows further. |

---

## Slice 1 — Next Action Banner (Do First)

### Why this first

Every one of the 9 roles named this as the highest-leverage next build. Implementation:
- Zero new API endpoints
- Zero new data models
- Computed from state already fetched: `readiness`, `pendingData`, `documents`, `bookingData`, and `tasks` from `BookingExecutionPanel`
- Estimated effort: 2–4 hours for the core version; 1 day for a polished version with all edge cases

### What it does

A single banner at the very top of OpsPanel (above readiness tiers, above everything). One sentence. One button. Examples:

| State | Banner text | Button |
|-------|-------------|--------|
| `pendingData` exists | "Customer submitted data 2 hours ago — review now" | `[Review Submission]` → scrolls to pending review card |
| Any task in `blocked` state | "Booking task blocked: Book Taj Hotels — needs attention" | `[Open Tasks]` → scrolls to BookingExecutionPanel |
| Any document in `pending_review` | "Document pending review: passport for adult_2" | `[Review Document]` → scrolls to document row |
| `readiness?.missing_for_next` has entries | "Missing before next tier: passport_number for adult_2" | `[Edit Booking Data]` → opens booking data edit form |
| Nothing blocking | "No action needed — all checks passed" | none (green state) |

### Priority ordering of rules

Evaluate in this order; show only the highest-priority item:

1. `pendingData !== null` → pending customer submission (highest urgency, operator action needed immediately)
2. Any task with `status === 'blocked'` (operator or supplier action stalled)
3. Any document with `status === 'pending_review'` (operator review needed)
4. `readiness?.missing_for_next` is non-empty (data collection incomplete)
5. All clear (green state)

### Implementation plan

**New file: `frontend/src/app/(agency)/workbench/NextActionBanner.tsx`**

```typescript
// Pure function — no API calls, no side effects
export function computeNextAction(params: {
  pendingData: PendingBookingData | null;
  tasks: BookingTask[];          // from BookingExecutionPanel state
  documents: BookingDocument[];
  readiness: TripReadiness | null;
  paymentTracking: PaymentTrackingDraft | null;
}): NextAction

type NextAction = {
  severity: 'blocking' | 'attention' | 'clear';
  message: string;
  actionLabel: string | null;
  scrollTarget: string | null;  // data-testid of target element to scroll to
}

// Component: reads NextAction, renders one banner row
export function NextActionBanner({ action }: { action: NextAction }): JSX.Element
```

**Changes to `OpsPanel.tsx`:**
1. Import `NextActionBanner` and `computeNextAction`
2. Call `computeNextAction(...)` at render time (pure derived value, no useEffect)
3. Render `<NextActionBanner action={nextAction} />` as the first element inside the OpsPanel return, above the readiness section
4. Add `data-testid` anchors to the scroll targets if not already present

**No backend changes.** All inputs (`pendingData`, `documents`, `readiness`) are already fetched.

### Conservative rule authoring

Executioner's warning: "If the banner computes from cached state and the operator acts on the suggestion but the state has not refreshed, the banner will show a stale action." Champion's warning: "A banner that says 'Ready to book' when something is actually missing destroys operator trust permanently."

Rules to live by:
- **When in doubt, surface the blocker, not the all-clear.** A false positive (unnecessary prompt) is recoverable. A false all-clear causes real booking errors.
- Start with 4–5 high-confidence rules. Do not add heuristics or LLM-derived suggestions to the first version.
- Never derive the all-clear state from absence of data — derive it from presence of positive signals (e.g., all tasks `completed`, `readiness?.highest_ready_tier === 'booking_ready'`).

### Acceptance criteria

- [ ] Opening OpsPanel on a trip with `pendingData` shows the pending review banner immediately (without scrolling)
- [ ] Opening OpsPanel on a trip with a blocked task shows the blocked task banner
- [ ] Opening OpsPanel on a completed trip with all tasks done shows the green all-clear banner
- [ ] Banner is not shown during loading state (shows skeleton or nothing)
- [ ] Clicking a banner button scrolls to the correct section
- [ ] `computeNextAction` is a pure function with 100% test coverage on the priority rules
- [ ] No new API calls on OpsPanel mount

---

## Slice 2 — Fix Collection Link Re-Expose (~1 hour)

### The bug

When `linkInfo` is null (not fetched or expired from server) but `has_active_token` is true, the operator sees:

> "Active link exists (expires…). Generating a new link will revoke the old one."

With no way to see or copy the URL. An operator who sent a link yesterday and wants to verify it must either revoke-and-regenerate (which invalidates the customer's link) or do nothing and hope.

### Fix

Store the last-generated URL in `sessionStorage` keyed on `tripId + tokenId`. On mount, if `linkStatus.has_active_token` is true and `sessionStorage` has a matching entry, display the URL.

```typescript
// On generate success:
sessionStorage.setItem(`collection-link-${tripId}-${tokenId}`, url);

// On mount (after linkStatus fetch):
if (linkStatus.has_active_token && !linkInfo?.url) {
  const stored = sessionStorage.getItem(`collection-link-${tripId}-${tokenId}`);
  if (stored) setDisplayUrl(stored);
}

// On revoke:
sessionStorage.removeItem(`collection-link-${tripId}-${tokenId}`);
```

~15 lines. No new API. No new backend changes.

### Acceptance criteria

- [ ] Operator who generated a link yesterday, refreshes the page, and returns to the same trip sees the existing URL displayed (not just "Active link exists")
- [ ] Revoking the link clears the stored URL
- [ ] Generating a new link stores the new URL and clears the old one

---

## Slice 3 — Remove Developer Banner (15 min)

**Location:** `OpsPanel.tsx` lines 1132–1133 (approx)

The blue info box: `"use this Ops panel for document upload, review, extraction, and apply. The dedicated /documents module remains staged…"` is implementation-planning copy. No operator needs to know the /documents module is staged.

**Change:** Delete the JSX block. No other changes.

**Acceptance criteria:**
- [ ] Banner is gone from the rendered Documents section
- [ ] No regression in document upload/review/extract functionality

---

## Slice 4 — Fix `extractionSelections` Memory Leak (1–2 hours)

### The bug

`handleDocDelete` at lines 494–507 calls `fetchDocuments()` which updates `documents` state. But `extractionSelections` and `extractionConflicts` are `Record<string, ...>` keyed by `doc.id`. After delete, the stale keys for the deleted document remain in both records indefinitely. In a long session with repeated upload/delete cycles, these grow unbounded.

### Fix

In `handleDocDelete`, after the delete API call succeeds, clear the stale keys:

```typescript
// After fetchDocuments() in handleDocDelete:
setExtractionSelections(prev => {
  const next = { ...prev };
  delete next[docId];
  return next;
});
setExtractionConflicts(prev => {
  const next = { ...prev };
  delete next[docId];
  return next;
});
```

### Acceptance criteria

- [ ] After deleting a document, its `doc.id` key is absent from both `extractionSelections` and `extractionConflicts`
- [ ] Unit test: mock `handleDocDelete` flow and assert both state records are clean after delete

---

## Slice 5 — Separate Payment Save from Traveler Data Save (2–3 days)

### The problem

`handleSave` at lines 329–356 writes `travelers + payer + payment_tracking` in a single atomic call. These are separate operator concerns:

- **Traveler data** is collected once early (passport, DOB, names) — typically set once, occasionally corrected
- **Payment tracking** evolves across the booking lifecycle (deposit_pending → deposit_paid → balance_due → paid) — updated frequently, by different agents, at different times

Coupling them causes:
1. A 409 conflict on payment status blocks a traveler name correction
2. An operator correcting a traveler's DOB accidentally overwrites a payment status update made by a colleague minutes before

### Implementation

Extract `PaymentTrackingCard` as a standalone component with its own `handlePaymentSave` function. The backend call signature does not change — `updateBookingData` still accepts the full `BookingData` object. The frontend stops coupling the two save flows.

```typescript
// New component: PaymentTrackingCard.tsx
// Props: initialPayment: PaymentTrackingDraft, tripId: string, bookingDataId: string
// Own state: editPayment, savingPayment, paymentConflict
// Own save handler: calls updateBookingData with ONLY the payment_tracking field updated
//   (passes current bookingData.travelers unchanged)
```

**OpsPanel changes:**
1. Import `PaymentTrackingCard`
2. Remove payment tracking state vars from OpsPanel into the card
3. Remove payment tracking fields from the main booking data edit form
4. Render `<PaymentTrackingCard />` as a separate section (Section 3 in the target layout)

### Acceptance criteria

- [ ] Editing a traveler's DOB does not require re-entering or touching payment tracking fields
- [ ] Saving payment status does not re-save traveler records
- [ ] 409 on payment save does not prevent traveler data save (and vice versa)
- [ ] Existing tests for booking data save continue to pass

---

## Slice 6 — `final_payment_due` Field (1–2 days, depends on S5)

### New field

Add `final_payment_due: string | null` (ISO date string) to:
1. `PaymentTrackingDraft` type (frontend)
2. `payment_tracking` model/schema (backend)
3. `PaymentTrackingCard` UI (new input: date picker, optional)

### Derived display

In `PaymentTrackingCard`, compute `daysUntilDue = differenceInCalendarDays(final_payment_due, today)`:
- `daysUntilDue <= 0` → overdue badge (red)
- `0 < daysUntilDue <= 7` → "Final payment due in N days" amber badge
- `7 < daysUntilDue <= 14` → "Final payment due in N days" neutral badge
- `> 14` → no countdown (just show the date)

### Feed into Next Action Banner (S1)

Add a rule to `computeNextAction`:
- If `final_payment_due` exists and `daysUntilDue <= 3` and `payment_status !== 'paid'` → "Final payment due in N days — [Record Payment]"

### Acceptance criteria

- [ ] Field is optional — existing trips without it continue to work
- [ ] Countdown badge appears when `final_payment_due` is within 14 days
- [ ] Overdue state shows red when past due date
- [ ] S1 Next Action banner includes payment overdue rule

---

## Slice 7 — Add `traveler_id` to BookingDocument (2–3 days, backend model change)

### Why this is a prerequisite for traveler-grouped documents

Trickster: "The reason documents are a flat list is that `BookingDocument` has `document_type` but no enforced `traveler_id`. Documents are trip-level, not traveler-level. Without that model change, any grouping is approximate and will mislead operators."

### Changes required

**Backend:**
1. Add `traveler_id: Optional[str]` to `BookingDocument` model (nullable — trip-level documents have no traveler)
2. Add `traveler_id` to the document upload endpoint request body
3. No migration required if the field is nullable with default null

**Frontend:**
1. Add `traveler_id?: string | null` to `BookingDocument` TypeScript type
2. Add a traveler selector to the document upload form (dropdown from `bookingData.travelers`, with "Applies to all travelers" / "Trip-level" option that sends null)
3. No change to the document list rendering in this slice — rendering change is S8

### Acceptance criteria

- [ ] Upload form has traveler selector
- [ ] Uploaded documents with `traveler_id` have it stored and returned from the documents API
- [ ] Existing documents without `traveler_id` continue to work (null = trip-level)
- [ ] `traveler_id` appears in document detail views
- [ ] Extraction apply flow pre-populates the traveler dropdown from `doc.traveler_id` when it's set

---

## Slice 8 — Per-Traveler Document Grouping (2–3 days, depends on S7)

### Render change

Replace `documents.map()` at line 1149 with a grouped render:

```typescript
const travelerGroups = groupBy(documents, d => d.traveler_id ?? '__trip__');
// Render: one accordion per traveler (from bookingData.travelers)
// Plus one "Trip Documents" accordion for traveler_id === null
```

Each traveler accordion header shows:
- Traveler name and ID
- Completeness indicator: "passport ✓, visa ✗, insurance ✓" (derived from doc types present in group)

Missing document slots:
- For each expected doc type (passport required for all travelers, visa if applicable), show a red "Missing" slot with an "Upload" button if no document of that type is in the traveler's group

Upload button moves from the global section header into each traveler group header.

### Acceptance criteria

- [ ] Three travelers → three accordions + one "Trip Documents" group
- [ ] Missing passport for traveler 2 shows a red "Missing" slot in traveler 2's group
- [ ] Upload from traveler 1's group pre-fills `traveler_id` = traveler 1's ID
- [ ] Extraction apply dropdown pre-populates from the group's traveler when `doc.traveler_id` is set
- [ ] Documents without `traveler_id` appear in "Trip Documents" group, not lost

---

## Slice 9 — OpsPanel Component Decomposition (2–3 days, independent)

### The problem

OpsPanel.tsx is 1399 lines. Adding S1–S8 without decomposition will push it toward 2000+ lines. Every new feature must thread state through a component that already manages 34+ independent state slices.

### Decomposition plan

Extract by zone (do NOT atomize into dozens of tiny components):

| Zone component | Extracted from |
|----------------|----------------|
| `DataIntakeZone.tsx` | Collection link + pending submission + booking details sections |
| `DocumentsZone.tsx` | Document list (or per-traveler grouped version from S8) |
| `PaymentTrackingCard.tsx` | Payment tracking sub-section (also done in S5) |
| `NextActionBanner.tsx` | New component from S1 |

**OpsPanel.tsx becomes an orchestrator:** it fetches all data and passes it to zone components. Zone components manage their own UI state (expanded/collapsed, editing).

**Important:** Preserve all `data-testid` attributes on their existing DOM nodes during decomposition. The snapshot and integration tests target these — do not rename or move them.

### Acceptance criteria

- [ ] All existing tests pass without modification
- [ ] OpsPanel.tsx drops below 600 lines after decomposition
- [ ] Each zone component is independently importable and testable
- [ ] No behavioral regressions (verified by running the full test suite)

---

## No-Removal Rules

These things must not be deleted, weakened, or "simplified" during any of the above slices:

| Thing | Why |
|-------|-----|
| 409 conflict guard on booking data save | Multi-agent correctness. Silent overwrites in a 3-person office are a real risk. |
| `bookingDataSource` badge | Trust/provenance signal. Will become a liability defense feature. |
| Pending submission Accept/Reject flow | Customer data must not auto-apply. Operator in the loop is required. |
| `ExtractionHistoryPanel` | Provenance for extracted fields. Do not remove. |
| Field-level confidence in extraction | Per-field trust scores are the differentiated feature. |
| Stage gate (proposal/booking only) | Correct product discipline. Do not show Ops for pre-proposal trips. |
| Timeline append-only behavior | Immutability is a backend guarantee. UI must not provide delete affordances on timeline entries. |

---

## Tests to Write

In addition to acceptance criteria per slice:

**Unit tests:**
- `computeNextAction` pure function — test all priority rules in isolation, including edge cases (null pendingData + no tasks + no missing fields = green all-clear)
- `groupDocumentsByTraveler` utility function — test orphaned docs, null traveler_id, empty traveler list
- Payment countdown logic — overdue, 3-day, 14-day, > 14-day cases

**Integration tests:**
- OpsPanel mount with pending submission → NextActionBanner shows pending review
- OpsPanel mount with blocked task → NextActionBanner shows blocked task
- Document delete → `extractionSelections` and `extractionConflicts` clean up correctly
- Payment save does not re-save traveler records (after S5)
- Upload with traveler selector → document stored with correct `traveler_id`

**Snapshot tests:**
- Update `tests/fixtures/server_openapi_paths_snapshot.json` and `tests/fixtures/server_route_snapshot.json` when S7 backend changes land
- Update `tests/test_booking_data.py` when payment field is added (S6)

---

## Files Likely Touched

| File | Slice(s) | Change type |
|------|----------|-------------|
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | S1–S9 | Multiple changes; decomposition in S9 |
| `frontend/src/app/(agency)/workbench/NextActionBanner.tsx` | S1 | New file |
| `frontend/src/app/(agency)/workbench/PaymentTrackingCard.tsx` | S5 | New file |
| `frontend/src/app/(agency)/workbench/DataIntakeZone.tsx` | S9 | New file |
| `frontend/src/app/(agency)/workbench/DocumentsZone.tsx` | S8, S9 | New file |
| `frontend/src/types/booking.ts` (or equivalent) | S6, S7 | Add `final_payment_due`, `traveler_id` fields |
| `spine_api/persistence.py` | S6, S7 | Add new fields to persistence layer |
| `spine_api/server.py` | S7 | Add `traveler_id` to document upload endpoint |
| `tests/test_booking_data.py` | S6 | Add payment deadline field tests |
| `tests/fixtures/server_openapi_paths_snapshot.json` | S7 | Update with new document endpoint field |
| `tests/fixtures/server_route_snapshot.json` | S7 | Update with new endpoint shape |

---

## What Stays Unchanged

- `BookingExecutionPanel` — function unchanged. Visual position may change (elevated in S9 decomposition).
- `ConfirmationPanel` — unchanged. Confirmation diff is deferred.
- `ExecutionTimelinePanel` — unchanged in this slice. Navigable links and annotation are near-term follow-ups.
- All 7 booking task statuses — the state machine is correct as-is.
- The `tracking_only: true` constraint on payment — do not add payment processing.
- The stage gate (proposal/booking only) — do not change.

---

## Open Questions

1. **Does `BookingDocument` already have a `traveler_id` field in the backend schema?** If yes, S7 is frontend-only work. If no, it requires a backend schema addition. Verify in `spine_api/persistence.py` before scoping S7.

2. **Does `BookingExecutionPanel` expose its task list (including `blocked` tasks) to OpsPanel, or does it fetch independently?** S1 (Next Action Banner) needs access to blocked tasks. If `BookingExecutionPanel` fetches its own tasks in isolation, OpsPanel needs a shared tasks fetch or a callback prop.

3. **What is the exact shape of `readiness?.missing_for_next`?** S1 rule 4 (missing readiness fields) needs to know if `missing_for_next` contains traveler-attributed field names (e.g., `{ traveler_id: 'adult_2', field: 'passport_number' }`) or just field name strings. Check the readiness API response schema.

4. **Is `final_payment_due` the right name?** Some roles call it `next_due_date`, some `payment_due_date`. Should align with the existing `PaymentTracking` field naming convention.

---

*Plan derived from: `Docs/brainstorm/TRIP_WORKSPACE_OPS_MASTER_RECORD_BRAINSTORM_2026-05-14.md` and all 9 role files in `Docs/brainstorm/roles/ops-next/`.*
