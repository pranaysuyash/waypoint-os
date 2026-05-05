# Inquiry-to-Trip Flow Unification — First-Principles Analysis (2026-05-04)

## Why this analysis
You asked for a long-term, first-principles evaluation of whether the current split between `Lead Inbox` and `Trips in Planning` should be unified into a single trip-card lifecycle (with draft support), plus what that implies for labels/statuses, architecture, and refactoring risk.

This document is code-and-doc grounded, additive, and oriented to one canonical implementation path.

---

## Scope and constraints
- No implementation changes in this pass; analysis only.
- No destructive operations.
- No duplicate route proposals; must preserve canonical backend path.
- Must avoid parallel flow stacks (legacy inbox model + new unified model running as competing truths).

Key governing constraints:
- Single canonical implementation path (no duplicate policy stacks): `Docs/personas_scenarios/LOGICAL_POLICY_DECISIONS_RATIFIED_2026-04-23.md`
- New Inquiry is an action, not a module; `/workbench` is temporary route naming: `frontend/src/lib/nav-modules.ts`
- Existing frontend split is explicit: `Lead Inbox` and `Trips in Planning` pages over same trip entity.

---

## Current system truth (code-verified)

## 1) One core entity exists already: Trip
Backend persistence and APIs are trip-centric, not lead-centric.
- Trip model status/stage defaults: `spine_api/models/trips.py`
- Listing and filtering are status-driven: `spine_api/server.py` (`GET /trips`, `GET /inbox`)
- Inbox endpoint is a projection of trips in inbox statuses: `spine_api/server.py` `_INBOX_STATUSES`

## 2) Frontend has two operational modules over same entity
- Inbox module: `frontend/src/app/(agency)/inbox/page.tsx`
- Trips module: `frontend/src/app/(agency)/trips/page.tsx`
- New Inquiry CTA points to workbench intake: `frontend/src/components/layouts/Shell.tsx`

## 3) Status sets are already split in frontend adapter layer
`frontend/src/lib/bff-trip-adapters.ts` defines:
- `INBOX_STATUSES`: `new`, `incomplete`, `needs_followup`, `awaiting_customer_details`, `snoozed`
- `WORKSPACE_STATUSES`: `assigned`, `in_progress`, `ready_to_quote`, `ready_to_book`, `blocked`

This is effectively a dual-queue model implemented as status partitions of the same record.

## 4) Capture path is non-atomic today
- Capture creates trip: `createTrip` from `CaptureCallPanel`: `frontend/src/components/workspace/panels/CaptureCallPanel.tsx`
- Processing is separate action: `handleProcessTrip`: `frontend/src/components/workspace/panels/IntakePanel.tsx`

This creates "saved-but-unprocessed" leakage.

## 5) Draft lifecycle is real in backend but not yet the primary front door
Draft APIs exist and are substantial:
- `/api/drafts/*` endpoints: `spine_api/server.py`

This enables a proper `Draft Inquiry` stage without inventing a second entity type.

---

## Core first-principles diagnosis

The current split is a UI/module split, not a data-model split.
- Data model truth: one entity (`Trip`) with lifecycle status.
- UI truth: two pages that make this feel like two entities (`Lead` then `Trip`).

That mismatch produces avoidable cognitive and operational cost:
1. Duplicate queue mental models.
2. Extra handoff steps (Inbox -> Trips).
3. Higher chance of orphan states (captured but not processed; assigned but not actioned).

From first principles, the right long-term shape is:
- One canonical object (`Trip`) from first capture onwards.
- One lifecycle model.
- Multiple filtered views (including an "Inbox view").

---

## Flow issues identified (severity ordered)

## Critical
1. Non-atomic intake action (`Save` then separate `Process Trip`).
2. Split module semantics over one record type encourage handoff drop-off.

## High
3. Status language drift across layers (state, status, stage, inbox stage projection).
4. Inbox stage mapping is heuristic (`STATUS_TO_INBOX_STAGE`), not canonical lifecycle stage.

## Medium
5. New Inquiry entry defaults to workbench but not explicit capture-mode fast path.
6. Draft APIs exist but are not yet promoted as first-class inquiry lifecycle stage in UI.

## Low
7. Naming debt: `/workbench` as temporary route label adds conceptual noise.

---

## Proposed canonical lifecycle model (long-term)

## Entity
- Keep one entity: `Trip`.
- Add explicit lifecycle dimension instead of overloading one status field for all meanings.

## Recommended lifecycle phases
1. `draft_inquiry` (autosave/unsent; pre-commit)
2. `new_inquiry` (committed, untriaged)
3. `needs_details` (insufficient intake)
4. `ready_to_process` (sufficient for run)
5. `processing` (run active)
6. `in_planning` (agent workflow active)
7. `blocked` (requires intervention)
8. `completed` (done)
9. `cancelled` (closed)

## Important architectural rule
- "Inbox" is a **view** over lifecycle phases (`new_inquiry`, `needs_details`, `ready_to_process`), not a separate domain object.

This satisfies your suggestion: inbox behavior remains, inbox module duplication can be removed.

---

## Draft stage position (your suggestion)
Your suggestion of a draft stage is architecturally correct and aligns with existing backend capabilities.

Use Draft as:
- pre-commit capture space (autosave),
- not visible in planning queue until promoted/committed,
- recoverable/resumable on mobile and desktop.

This lowers accidental queue pollution and supports phone-first quick capture.

---

## Refactor impact analysis

## Backend impact
1. Introduce canonical lifecycle enum/validator in one place (contract + persistence + transition rules).
2. Keep `/trips` as canonical list endpoint.
3. Convert `/inbox` from a distinct concept into a filtered projection backed by lifecycle filter config.
4. Centralize transitions:
   - enforce allowed transitions,
   - enforce quality gates at transition points,
   - log audit events per transition.

## Frontend impact
1. Replace separate queue semantics with `Trips` primary module + saved filters/views.
2. Keep an "Inbox" view pill preset for operator familiarity.
3. Move to a single card system with contextual actions by phase.
4. Collapse capture action to `Save and Process` primary, `Save Draft` secondary.

## Contract impact
1. Explicitly distinguish:
   - lifecycle phase,
   - pipeline stage (`discovery/shortlist/proposal/booking`),
   - visual severity state.
2. Remove implicit stage derivations from status heuristics over time.

## Analytics/reporting impact
- Existing dashboards referencing status buckets must map to new lifecycle phases.
- Provide compatibility mapping during migration window.

---

## No-parallel-flow migration strategy

To avoid building in parallel:
1. Declare lifecycle schema as source of truth.
2. Keep old statuses as compatibility aliases temporarily.
3. Route both old and new UI views through same canonical filter service.
4. Remove legacy inbox-specific behavior after parity verification.

No duplicate routes. No dual policy stacks.

---

## Suggested status/pill redesign

Canonical pills (human-facing):
- `Draft`
- `New Inquiry`
- `Needs Details`
- `Ready to Process`
- `Processing`
- `In Planning`
- `Blocked`
- `Completed`
- `Cancelled`

Derived saved views:
- `Inbox`: Draft excluded, show `New Inquiry + Needs Details + Ready to Process`
- `Planning`: `Processing + In Planning + Blocked`
- `Done`: `Completed + Cancelled`

---

## Testing evidence from this analysis run

Commands executed:
1. `cd frontend && npm test -- --run src/app/api/trips/__tests__/route.test.ts src/components/workspace/panels/__tests__/IntakePanel.test.tsx src/components/workspace/panels/__tests__/CaptureCallPanel.test.tsx src/components/inbox/__tests__/InboxEmptyState.test.tsx`
2. `uv run pytest -q tests/test_api_trips_post.py tests/test_call_capture_phase2.py tests/test_call_capture_e2e.py`

Results summary:
- Frontend:
  - `route.test.ts` and `InboxEmptyState.test.tsx` passed.
  - `IntakePanel` and `CaptureCallPanel` suites failed due env dependency (`NEXT_PUBLIC_SPINE_API_URL` not set in test context), not flow-logic assertion failure.
- Backend:
  - 37 tests passed, 4 failed.
  - Failures indicate current drift in PATCH/status and artifact persistence expectations in targeted call-capture tests.

Why this matters:
- There is already test-surface instability around inquiry capture paths; lifecycle refactor must include a dedicated contract migration test pack before UI consolidation.

---

## Gaps to close before refactor execution
1. Lifecycle contract source-of-truth file + enum policy.
2. Transition matrix with guard conditions.
3. Compatibility mapping table (old status -> new lifecycle phase).
4. Unified query/filter service for Trips and Inbox presets.
5. Capture atomicity (`Save and Process`) as prerequisite.
6. Draft promotion UX integrated into new inquiry funnel.

---

## Recommended implementation sequence (future execution)

Wave 1 (foundation)
1. Lifecycle enum + transition policy in backend.
2. Canonical filter presets (`inbox`, `planning`, `done`) served from backend.
3. `Save and Process` atomic path.

Wave 2 (UI unification)
1. Single Trips module with view presets.
2. Keep Inbox as a preset label (not separate domain module).
3. Migrate card components to one canonical card with contextual actions.

Wave 3 (deprecation)
1. Deprecate legacy inbox-special routes/logic layers.
2. Remove heuristic status->stage adapter paths after parity.
3. Freeze compatibility alias window and finalize canonical labels.

---

## Open questions requiring explicit decisions
1. Do we keep `/inbox` route as a user-facing alias to `/trips?view=inbox` for continuity?
2. Should draft inquiries be persisted only in `DraftStore` until promotion, or also mirrored as trip stubs?
3. What is the SLA source-of-truth field post-lifecycle refactor (trip analytics vs dedicated SLA state)?
4. What is the exact allowed transition path from `needs_details` back to `ready_to_process` and who can trigger it?

---

## Recommended new goal
Implement **canonical trip lifecycle unification** with draft-first intake and inbox-as-view architecture:
- one entity,
- one lifecycle state machine,
- one canonical list surface,
- zero parallel route/policy stacks,
- atomic inquiry capture (`Save and Process`) with `Save Draft` fallback.

This is the most scalable, future-proof path and aligns with current codebase direction while removing existing operational friction.
