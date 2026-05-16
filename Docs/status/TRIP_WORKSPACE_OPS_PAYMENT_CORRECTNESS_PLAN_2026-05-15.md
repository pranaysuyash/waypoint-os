# Trip Workspace Ops — Slice C: Payment Correctness
**Date:** 2026-05-15  
**Status:** Implemented / verified — merged to master 2026-05-16  
**Branch:** master (commits `2c4d104`, `05c8538`)  
**Context:** Follows S1–S4 + S9 (NextActionBanner, doc cleanup, extraction leak fix, full decomposition arc)  
**Prior art:** `Docs/status/TRIP_WORKSPACE_OPS_NEXT_SLICE_PLAN_2026-05-14.md` (S5–S6 section)  
**Prior art:** `Docs/status/PAYMENT_REFUND_TRACKING_STATUS_2026-05-12.md` (current payment implementation)

---

## 1. Current State

### What exists

`PATCH /trips/{trip_id}/booking-data` accepts a **full `BookingDataModel` blob**:

```json
{
  "booking_data": {
    "travelers": [...],
    "payer": {...},
    "special_requirements": null,
    "booking_notes": null,
    "payment_tracking": {
      "agreed_amount": 120000,
      "amount_paid": 50000,
      "balance_due": 70000,   ← server-computed, ignored on input
      "payment_status": "partially_paid",
      "tracking_only": true   ← server-enforced
    }
  },
  "expected_updated_at": "2026-05-15T06:00:00Z"
}
```

Optimistic lock: **trip-level `updated_at`**. One CAS lock for traveler data and payment data together.

`PaymentTrackingModel` (backend, `spine_api/server.py` lines 1880–1942):
- All numeric amounts validated non-negative
- `balance_due` computed server-side: `max(agreed_amount - amount_paid, 0.0)`
- `tracking_only` forced to `True` on every write (no payment processing)
- `currency` normalized to 3-letter uppercase

**`final_payment_due` does not exist anywhere.**

No dedicated payment endpoint. No sub-field locking.

### What is broken today

1. **Tangled save flows.** `DataIntakeZone.handleSave` serializes `editTravelers + editPayerName + editPaymentTracking` into one `BookingData` object and posts it. An agent fixing a traveler's DOB must also re-submit current payment state, or accidentally revert payment status to the editor's starting snapshot.

2. **Shared optimistic lock.** One agent editing travelers and another editing payment tracking will cause a 409 on the second save. The error message ("Booking data conflict") doesn't distinguish which field caused the conflict — the operator has no clean path to merge.

3. **No `final_payment_due`.** Payment tracking has no temporal anchor. Operators track deadline manually (outside the system), which makes the NextActionBanner unable to give a payment-overdue cue.

---

## 2. Options Considered

### Option A — Dedicated payment PATCH endpoint (recommended)

`PATCH /trips/{trip_id}/booking-data/payment`

- Accepts only `PaymentTrackingModel` + `expected_updated_at`
- Backend reads current booking data, replaces only the `payment_tracking` sub-object, writes back
- Returns the same `BookingDataResponse` envelope
- Same trip-level `updated_at` lock as before (no new lock dimension)
- `DataIntakeZone` gets a `handlePaymentSave` that calls this endpoint
- Main `handleSave` no longer sends `payment_tracking`

**Why recommended:** Semantic clarity — payment ops and booking ops are distinct operator actions. Clean audit log separation. If needed in future, this endpoint can get its own permissions (e.g. a "billing" role). Minimal backend complexity: 20–30 lines.

**Tradeoff:** Two agents editing travelers and payment simultaneously will still conflict at the trip `updated_at` lock. This is acceptable — true simultaneous edits are rare in practice, and the conflict message will now say "payment tracking conflict" specifically. The conflict rate is reduced because traveler edits and payment edits no longer compete for the same button click.

### Option B — Merge-patch fields selector

Add `update_fields?: list[Literal['travelers', 'payer', 'payment_tracking']]` to `BookingDataUpdateRequest`.

- Backend reads current booking, replaces only specified fields
- If `payment_tracking` not in `update_fields`, it is preserved from current storage

**Why not recommended:** Makes the existing endpoint semantically ambiguous. Partial updates with a shared blob require careful read-merge-write in the backend. The "what field caused my conflict?" problem is unresolved. More complex testing surface.

### Option C — Read-before-write at frontend only (insufficient)

Frontend payment save: fetch latest booking data → merge payment changes in memory → PATCH.

- No backend changes
- Still uses the same lock; eliminates "editor snapshots stale payment state" problem
- Does NOT eliminate "traveler edit conflicts with payment edit" problem

**Why insufficient:** The user specifically asked for backend write semantics. Option C is a partial fix.

---

## 3. Recommended Contract — Option A

### New endpoint

```
PATCH /trips/{trip_id}/booking-data/payment
```

**Request:**
```json
{
  "payment_tracking": {
    "agreed_amount": 120000,
    "amount_paid": 60000,
    "payment_status": "partially_paid",
    "final_payment_due": "2026-06-15",
    "currency": "INR"
  },
  "expected_updated_at": "2026-05-15T06:00:00Z"
}
```

**Behavior:**
1. Stage gate: only `proposal`/`booking` (same as main endpoint)
2. Fetch current booking data
3. Replace `booking_data.payment_tracking` with the new value
4. Recompute `balance_due` and force `tracking_only = True` (same model validators as today)
5. Run `compute_readiness` (payment status is currently not a readiness factor; this is a no-op but keeps the recompute invariant)
6. Atomic write with compare-and-set on `expected_updated_at`
7. Audit event: `payment_tracking_updated` (separate from `booking_data_updated`)

**Response:** Same `BookingDataResponse` envelope as the main endpoint.

**409 behavior:** Returns `"message": "Payment tracking conflict"` — distinguishable from traveler data conflict.

### Updated `handleSave` in `DataIntakeZone`

`handleSave` (traveler save) sends `BookingData` with `payment_tracking: null`. Payment state is no longer included in the traveler save payload.

New `handlePaymentSave` calls `PATCH /trips/{trip_id}/booking-data/payment`.

UI: "Edit" button opens traveler/payer form as today. Payment section has its own "Edit Payment" button that opens `PaymentTrackingCard` in edit mode, with its own "Save Payment" / "Cancel" buttons.

---

## 4. `final_payment_due` Field

### Schema addition

**Backend `PaymentTrackingModel`** — add one field:

```python
final_payment_due: Optional[str] = None
```

Validation: if present, must be a valid ISO date (`YYYY-MM-DD`). Use a `@field_validator` that calls `datetime.fromisoformat` — reject if malformed.

**Frontend `PaymentTracking` type** — add:
```typescript
final_payment_due?: string | null;
```

**`PaymentTrackingDraft`** in `DataIntakeZone` — add:
```typescript
final_payment_due: string;  // ISO date string, empty = null
```

### Display in `PaymentTrackingCard`

Compute `daysUntilDue` from today's date (2026-05-15):

| Condition | Display |
|-----------|---------|
| `final_payment_due` absent | nothing |
| `daysUntilDue < 0` | red badge "Overdue by N days" |
| `0 <= daysUntilDue <= 3` | red badge "Due in N days" |
| `4 <= daysUntilDue <= 7` | amber badge "Due in N days" |
| `8 <= daysUntilDue <= 14` | neutral badge "Due in N days" |
| `> 14` | show date only, no badge |

### NextActionBanner rule (addition to `computeNextAction`)

After the `pending_review documents` rule and before the `missing_for_next` rule, insert:

```typescript
// priority: 'urgent' when overdue, 'attention' when ≤ 3 days
const paymentTracking = /* passed as prop from DataIntakeZone via callback */;
if (paymentTracking?.final_payment_due && paymentTracking?.payment_status !== 'paid') {
  const daysUntil = differenceInCalendarDays(parseISO(paymentTracking.final_payment_due), today);
  if (daysUntil < 0) {
    return { priority: 'urgent', message: `Final payment is overdue by ${Math.abs(daysUntil)} day${Math.abs(daysUntil) !== 1 ? 's' : ''}.` };
  }
  if (daysUntil <= 3) {
    return { priority: 'attention', message: `Final payment due in ${daysUntil} day${daysUntil !== 1 ? 's' : ''}.` };
  }
}
```

`paymentTracking` reaches `NextActionBanner` via a new `onPaymentTrackingChange` callback on `DataIntakeZone` — same mirror-state pattern as `opsDocs` and `opsTravelers`.

---

## 5. Optimistic Locking Semantics

No new lock dimension is introduced. Both `PATCH /booking-data` and `PATCH /booking-data/payment` use the trip-level `updated_at` CAS lock.

**Conflict scenario post-Slice C:** Two agents, one editing travelers (using main endpoint) and one editing payment (using new endpoint), will still conflict if both started from the same `updated_at`. The second save loses and gets a 409.

**Why this is acceptable now:** Before Slice C, a payment edit and a traveler edit shared the same form and the same button — any background change conflicted with everything. After Slice C, the two flows are independent. Conflicts are real concurrent edits by different operators, not false conflicts caused by unrelated field coupling.

**Future path to finer-grained locking:** Add a `payment_tracking_version` (monotonic counter) to the booking data blob. `PATCH /booking-data/payment` checks this independently from the trip `updated_at`. This is deferred until there is evidence of multi-agent concurrent payment+traveler editing in production.

---

## 6. `public_collection.py` Guard

`BookingDataModel` in `routers/public_collection.py` uses `extra = "forbid"` and does not include `PaymentTrackingModel`. This ensures customer-submitted booking data cannot contain `payment_tracking` or `final_payment_due`. This guard is unchanged by Slice C.

---

## 7. Frontend UX

`PaymentTrackingCard` becomes an **editable card** with its own edit state:

**View mode** (current `PaymentTrackingCard` display):
- Agreed / Paid / Balance due / Status / Refund (as today)
- Add: `final_payment_due` display with countdown badge
- "Edit Payment" button

**Edit mode** (new):
- All current payment draft fields (agreed amount, amount paid, currency, payment status, payment method, reference, refund status, refund amount, refund method, notes)
- New: `final_payment_due` date input (optional, `type="date"`)
- "Save Payment" button → calls `PATCH /trips/{trip_id}/booking-data/payment`
- "Cancel" button
- Conflict display: "Payment data was updated by another session. [Reload]" — same pattern as traveler conflict today

`DataIntakeZone` removes all payment draft state and the payment section from `handleSave`. It passes `bookingData.payment_tracking` as a prop to `PaymentTrackingCard` and provides `tripId` and `updatedAt`.

`OpsPanel` adds a new mirror: `const [opsPaymentTracking, setOpsPaymentTracking] = useState<PaymentTracking | null>(null)` and passes `setOpsPaymentTracking` as `onPaymentTrackingChange` to `DataIntakeZone`. `NextActionBanner` receives this as a new prop.

---

## 8. Readiness Integration

Payment status is **not** a readiness criterion today (`_check_booking_ready` checks only travelers + payer). This is intentional and unchanged by Slice C.

`final_payment_due` is also not added to readiness. Payment deadlines are tracked for the operator's awareness, not for the AI pipeline's booking-readiness computation.

---

## 9. Migration Risk

| Risk | Mitigation |
|------|-----------|
| Existing trips have `payment_tracking` without `final_payment_due` | Field is `Optional[str] = None` — no migration needed. Null = absent. |
| Existing frontend code reads `PaymentTracking` shape | Adding optional field is backward-compatible — no consumer breaks. |
| `PATCH /booking-data` now sends `payment_tracking: null` | Current trips with payment data: payment is preserved because the new payment endpoint owns it. But first save via traveler form would null out payment tracking. **Fix:** `handleSave` must send `payment_tracking: bookingData?.payment_tracking ?? null` (preserve current value) when not in payment-edit mode. |
| Audit log split | `booking_data_updated` now only logs traveler/payer changes. New `payment_tracking_updated` event for payment. Both audit logs are metadata-only (no PII). |
| OpenAPI snapshot | `tests/fixtures/server_openapi_paths_snapshot.json` and `server_route_snapshot.json` will need updating. |

---

## 10. Implementation Order

1. **Backend**: Add `final_payment_due` field to `PaymentTrackingModel` with validation. Update `test_booking_data.py`.
2. **Backend**: Add `PATCH /trips/{trip_id}/booking-data/payment` endpoint. Update route snapshots.
3. **Frontend types**: Add `final_payment_due` to `PaymentTracking` and `updatePaymentTracking` function to `api-client.ts`.
4. **`PaymentTrackingCard`**: Make editable with own save flow + `final_payment_due` display + countdown badge.
5. **`DataIntakeZone`**: Remove payment draft state and payment section from `handleSave`. Add `onPaymentTrackingChange` callback. Pass `paymentTracking` prop to `PaymentTrackingCard`.
6. **`OpsPanel`**: Add `opsPaymentTracking` mirror state. Pass to `NextActionBanner`.
7. **`NextActionBanner` + `computeNextAction`**: Add payment overdue/due-soon rules.
8. **Tests**: `PaymentTrackingCard.test.tsx` (editable, countdown badge, conflict display). Backend `test_booking_data.py` additions. Frontend `DataIntakeZone.test.tsx` updates.

---

## 11. Open Questions Before Implementation

1. **Should `handleSave` (traveler save) explicitly preserve `payment_tracking`?** Option A: pass `payment_tracking: bookingData?.payment_tracking ?? null` in the payload. Option B: new payment endpoint writes payment tracking, traveler endpoint ignores it entirely (backend only touches `travelers + payer + special_requirements + booking_notes`). Option B requires backend to split the merge instead of frontend — cleaner but more backend work.

2. **`date-fns` or `Temporal` for countdown?** `date-fns` is likely already in the frontend bundle. Check `package.json` before adding.

3. **Should the `final_payment_due` field name use `_due` or `_date`?** Existing fields use `_at` for datetimes. Payment deadlines are dates only (not times). `final_payment_due` (date-only string `YYYY-MM-DD`) is the clearest. Confirm naming is consistent with any existing follow-up date fields (`follow_up_due_date` in server.py).

4. **Concurrency: should `PATCH /booking-data/payment` read-merge-write or expect the full current `payment_tracking` in the request?** Read-merge-write (backend fetches current, replaces only `payment_tracking`) is safer. This means the endpoint only needs the new `payment_tracking` sub-object + `expected_updated_at`.

---

## 8. Implementation Record (added 2026-05-16)

### Decisions confirmed as implemented

| Decision | Outcome |
|---|---|
| Traveler endpoint preserves/ignores `payment_tracking` | Backend reads existing `payment_tracking` from storage and forces it back into the write — client-supplied value discarded |
| Payment endpoint owns `payment_tracking` | `PATCH /booking-data/payment` is the only write path for payment fields |
| `final_payment_due` field added | ISO `YYYY-MM-DD` string, validated via `date.fromisoformat`, optional, `None` by default |
| Terminal statuses suppress due alerts | `paid`, `waived`, `refunded` — `NextActionBanner` emits no payment alert for any of these |
| `balance_due` and `tracking_only` server-authoritative | `compute_balance_due` model_validator always overwrites client-supplied values |
| Conflict Reload fetches fresh data | `onReload` prop wired to `fetchBookingData`; `handleReload` clears state then awaits callback |

### Test coverage shipped
- 998 frontend tests passing (121 test files)
- 47 backend `test_booking_data.py` tests passing
- 8 new `TestPaymentTrackingEndpoint` tests
- 4 new `PaymentTrackingModel` Pydantic validation unit tests
- 20 `PaymentTrackingCard` component tests (view mode, edit mode, save, 409 conflict, reload)
- 9 `NextActionBanner` payment rule tests (overdue urgent, due-soon attention, terminal no-op)
