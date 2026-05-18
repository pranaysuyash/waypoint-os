# COMING SOON READINESS CONTRACT 01: BOOKINGS

Date: 2026-05-17
Mode: Plan-only (no product code changes)
Primary reference: motto.md (status/architecture/context review first)

## 0) Scope and evidence baseline

This contract is drafted after re-validating current implementation and docs.

Evidence anchors reviewed in this pass:
- `motto.md`
- `frontend/src/lib/nav-modules.ts`
- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx`
- `frontend/src/components/workspace/panels/BookingExecutionPanel.tsx`
- `frontend/src/components/workspace/panels/ConfirmationPanel.tsx`
- `frontend/src/components/workspace/panels/PaymentTrackingCard.tsx`
- `frontend/src/lib/api-client.ts`
- `spine_api/routers/booking_tasks.py`
- `spine_api/services/booking_task_service.py`
- `spine_api/routers/confirmations.py`
- `spine_api/services/confirmation_service.py`
- `spine_api/models/tenant.py`
- `Docs/review/COMING_SOON_FEATURES_STATUS_ARCHITECTURE_REVIEW_2026-05-17.md`
- `Docs/review/EXTERNAL_REVIEW_BRIEF_COMING_SOON_READINESS_2026-05-17.md`

Working-tree context (read-only):
- `git status --short --branch` -> `master...origin/master` with parallel local edits present.

## 1) ChatGPT feedback adjudication (accepted vs adjusted)

Accepted as-is:
1. Do not enable coming-soon nav modules yet.
2. Draft Bookings readiness contract before any `/bookings` surface build.
3. Preserve distinction between global queue surface and trip-context execution surface.
4. Enforce rollback gates before nav enablement.
5. Treat external review as critique, not authority.

Accepted with adjustments to match current runtime reality:
1. Proposed state machine labels in external feedback are directionally useful, but current backend canonical statuses are already defined and enforced (`TASK_STATUSES`, `VALID_TRANSITIONS`).
2. Proposed API shape must account for current trip-scoped endpoints (`/api/booking-tasks/{trip_id}/...`) and avoid fake “global module” ownership before data/permission model is explicit.
3. Proposed “version-aware” mutation is valid as a gate, but current booking-task model has no explicit optimistic-version field; this is a gap, not a completed capability.

Rejected for now:
1. Any implication that top-level `/bookings` should be enabled before lifecycle + ownership + parity gates are proven.
2. Any surface-first rollout that duplicates trip ops state logic.

## 2) Bookings ownership statement (mandatory architecture sentence)

Bookings owns booking-task lifecycle and cross-trip operational triage.
Bookings references trips, confirmations, payment-tracking state, supplier metadata, and quote context.
Bookings must never directly mutate quote snapshots or payment ledger truth without domain-validating service boundaries.

## 3) Product contract

Bookings is the cross-trip operational command center for booking work.

Bookings must answer:
- What booking tasks need action now?
- What tasks are blocked and why?
- What deadlines are at risk?
- What confirmation dependencies are unresolved?

Bookings is not:
- quote composition/versioning module
- supplier CRM module
- payment ledger module
- replacement for trip-level execution context

## 4) Surface contract: global queue vs trip execution

Required split:
- `/bookings` (global): queue, prioritization, triage, ownership assignment.
- `/trips/:tripId/ops` (trip): detailed execution, evidence handling, context-specific resolution.

Single source of truth:
- Same booking task entity must power both surfaces.
- No duplicated local-only task state between surfaces.

## 5) Route contract (v1 target)

Current reality:
- Nav contains disabled `/bookings` (`enabled: false`).
- No route found for `/bookings` under `frontend/src/app`.

V1 required routes before enablement:
- `/bookings`
- `/bookings/:bookingTaskId`
- `/bookings?status=...`
- `/bookings?tripId=...`

Optional later:
- `/bookings/deadlines`
- `/bookings/suppliers/:supplierId`

## 6) Domain/state contract (current canonical + planned extension)

Current canonical backend statuses (`spine_api/models/tenant.py`):
- `not_started`, `blocked`, `ready`, `in_progress`, `waiting_on_customer`, `completed`, `cancelled`

Current canonical transitions:
- `not_started -> ready|blocked|cancelled`
- `blocked -> ready|cancelled`
- `ready -> in_progress|blocked|cancelled`
- `in_progress -> completed|waiting_on_customer|cancelled`
- `waiting_on_customer -> in_progress|cancelled`
- `completed` terminal
- `cancelled` terminal

Contract decision:
- V1 must preserve these canonical statuses/transitions.
- Any richer status model (for example, split blocked types) is Phase-2+ and requires explicit migration contract.

## 7) API contract (current vs required for module enablement)

Current API (trip-scoped):
- `GET /api/booking-tasks/{trip_id}`
- `POST /api/booking-tasks/{trip_id}`
- `POST /api/booking-tasks/{trip_id}/generate`
- `PATCH /api/booking-tasks/{trip_id}/{task_id}`
- `POST /api/booking-tasks/{trip_id}/{task_id}/complete`
- `POST /api/booking-tasks/{trip_id}/{task_id}/cancel`

Related confirmation API:
- `GET/POST/PATCH /api/trips/{trip_id}/confirmations...`
- state transitions: `record|verify|void`

Module-enablement API gates:
1. Define canonical global-query contract for `/bookings` without duplicating task ownership.
2. Agency scoping must remain server-derived (no client-asserted tenant).
3. Every status mutation must emit audit timeline event.
4. Blocker reason must be explicit and queryable.
5. Conflict-safe mutation strategy must be defined for booking tasks (gap today: no explicit optimistic-version field on booking_task model).
6. `/bookings` may introduce a global queue read/query model, but all writes must resolve back to the canonical booking-task mutation path and state machine.

Canonical blocker classes for Bookings v1:
- `customer_input_required`
- `customer_approval_required`
- `payment_required`
- `supplier_response_required`
- `supplier_unavailable`
- `confirmation_missing`
- `document_missing`
- `operator_review_required`
- `system_error`
- `other_with_note_required`

Validation rule:
- `other_with_note_required` is only valid when a non-empty human-readable note is provided.

## 8) Data ownership boundaries with adjacent modules

Bookings owns:
- booking task records
- booking task status transitions
- task-level blocker reason/refs
- queue-level prioritization metadata

Bookings references:
- Trips: trip context and stage
- Confirmations: evidence/progress state
- Payments: blocking/reconciliation signals (currently embedded in booking_data.payment_tracking)
- Suppliers: identity and policy references (not full supplier management)
- Quotes: read-only commercial context links

Bookings must not own:
- Quote snapshot mutation
- Direct payment posting/settlement logic
- Supplier master-data lifecycle

## 9) UI acceptance contract (v1)

Minimum queue sections:
- Needs action
- Blocked
- Waiting on customer
- In progress
- Completed recently
- Deadlines at risk

Each task row minimum fields:
- Trip
- Task title/type
- Status
- Blocker reason
- Deadline
- Owner
- Next action hint
- Confirmation/evidence state summary

Mandatory actions in `/bookings` v1:
- open trip ops
- assign owner
- change status with reason (transition-valid)
- add note
- mark blocker class
- retry/reconcile task

Deferred risky actions:
- any external auto-booking
- direct payment charge/release
- irreversible customer-facing automations

Queue freshness and stale-data behavior:
1. After mutation, queue state must be refreshed by either:
   - refetching from server, or
   - replacing local row state with returned canonical server entity.
2. UI must not assume a transition succeeded before server confirmation.
3. If refresh fails post-mutation, UI must show explicit stale-data warning and provide retry.

Empty queue acceptance:
1. Empty `/bookings` is a valid success state.
2. Empty state must provide actionable guidance (for example, where to create/prepare tasks).
3. No seeded/mock runtime data is allowed in production queue surfaces.

## 10) Security/privacy/compliance contract

1. Tenant isolation: enforced from auth membership context.
2. No private confirmation fields in timeline metadata.
3. Confirmation detail decryption only in detail endpoints, not list endpoints.
4. Event metadata allowlist/forbidden patterns remain enforced.
5. Any cross-module reference (task->confirmation->document) must validate trip/agency ownership.

## 11) Observability contract

Required events (minimum):
- `task_created`
- `task_blocked`
- `task_ready`
- `task_started`
- `task_waiting`
- `task_completed`
- `task_cancelled`
- confirmation lifecycle events tied to task context

Required operational metrics:
- open tasks by status
- blocked task count + blocker classes
- tasks overdue
- mean time not_started->completed
- mean time blocked->ready
- tasks by owner
- confirmation-pending linked tasks

## 12) Test contract (enablement gate)

Must pass before `/bookings` nav enablement:
1. nav gate test: disabled->enabled only when route + gate conditions exist.
2. route rendering tests: loading/empty/error/hydrated queue.
3. agency isolation tests for list + mutation.
4. transition validity tests for all allowed/forbidden edges.
5. blocked-task completion guard tests.
6. trip-ops and bookings parity tests for same canonical task state.
7. audit event emission tests for all task status mutations.
8. confirmation linkage tests (no detached evidence refs).
9. conflict behavior tests for concurrent mutation semantics (requires explicit conflict contract).

## 13) Rollout and rollback gates

Enablement preconditions:
1. `/bookings` route exists and is production-safe.
2. global queue query contract defined and verified.
3. parity with trip ops task state proven.
4. security/privacy checks pass.
5. core test matrix passes.

Immediate rollback triggers:
- cross-tenant visibility bug
- state divergence between `/bookings` and trip ops
- invalid transition accepted by UI/API path
- evidence/confirmation linkage break
- persistent route crashes

Rollback action:
- set `/bookings` nav back to disabled
- retain data and APIs
- publish gate-failure note and defect list

## 14) Top risks (ranked)

1. Duplicate ownership between global queue and trip ops.
2. Payment/blocker semantics inconsistent across booking surfaces.
3. Confirmation evidence detached from booking task.
4. Missing conflict semantics for concurrent task edits.
5. Surface-first route enablement before contract completion.
6. Drift between docs and runtime status machine.
7. Supplier context modeled ad hoc inside task notes/blocker refs.
8. Observability blind spots for blocked->ready cycle time.
9. Over-abstraction before 2+ modules share proven patterns.
10. Test coverage focused on slices but missing cross-surface parity.

## 15) Explicit non-goals for Bookings v1

1. Build full supplier CRM.
2. Build full payment ledger.
3. Change canonical task statuses/transitions.
4. Introduce broad abstraction layer for all coming-soon modules.
5. Enable `/bookings` nav without passing all gates above.

## 16) Open questions blocking implementation

1. Conflict model: do we add optimistic versioning to `booking_tasks` now or define server-side last-write + event compensation semantics?
2. Global queue query shape: new endpoint family vs composition layer over existing trip-scoped endpoints?
3. Ownership granularity: do tasks require assignee identity from membership table with role constraints?
4. Supplier linkage: minimal supplier reference contract before Suppliers module exists?
5. Payment dependency semantics: source-of-truth boundaries when payment tracking remains embedded in booking_data and `payment_required` blocker is set.

## 17) Implementation sequencing (required order)

1. Add/verify global read/query contract for booking tasks.
2. Add explicit conflict semantics (optimistic versioning or explicit server-side last-write contract).
3. Implement and enforce canonical blocker classes.
4. Add test gates: agency isolation, transitions, parity, audit emission, conflict behavior.
5. Build `/bookings` read-only queue surface.
6. Add safe mutations through canonical booking-task write path.
7. Enable nav only after all rollout/test/security gates pass.

## 18) Next artifact decision

Recommended next doc (before code):
- `Docs/review/MODULE_READINESS_CONTRACT_TEMPLATE.md`

Then derive:
- `COMING_SOON_READINESS_CONTRACT_02_PAYMENTS_2026-05-17.md`
- `COMING_SOON_READINESS_CONTRACT_03_QUOTES_2026-05-17.md`
- `COMING_SOON_READINESS_CONTRACT_04_SUPPLIERS_2026-05-17.md`
- `COMING_SOON_READINESS_CONTRACT_05_KNOWLEDGE_BASE_2026-05-17.md`

## 19) Stop condition

This document is planning-only.
No product code changes are included.
Await approval before implementation or nav state changes.
