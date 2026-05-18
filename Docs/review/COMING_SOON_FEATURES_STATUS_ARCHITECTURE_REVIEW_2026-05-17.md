# Coming-Soon Features: Status + Architecture + Context Review

Date: 2026-05-17
Scope: Read-only status/architecture/context review for coming-soon features (no product code changes)

## Executive verdict

Coming-soon features are planned in navigation and extensively documented, but not yet implemented as canonical top-level modules.

Current nav-declared coming-soon modules:
- Quotes
- Bookings
- Payments
- Suppliers
- Knowledge Base

Source of truth:
- `frontend/src/lib/nav-modules.ts`:
  - `/quotes` enabled: false
  - `/bookings` enabled: false
  - `/payments` enabled: false
  - `/suppliers` enabled: false
  - `/knowledge` enabled: false
- `frontend/src/components/layouts/Shell.tsx` shows these as disabled `Planned` buttons and triggers “coming soon” toast.

## What is planned vs what exists now

## 1) Quotes

Planned:
- Nav module exists as disabled (`/quotes`).
- Feature inventory marks quote module work as SPEC.

Implemented now:
- Quote Review exists (`/reviews`) and is active.
- No `/quotes` route/page found under `frontend/src/app`.
- No canonical quote builder/versioning surface exposed as top-level module.

Evidence:
- `frontend/src/app/(agency)/reviews/page.tsx`
- `frontend/src/app/(agency)/reviews/PageClient.tsx`
- `Docs/status/FEATURE_LIST_V2_2026-05-12.md` (disabled planned modules row + quote engine as SPEC)
- `Docs/status/LEFT_SIDEBAR_NAV_CONTEXT_REVIEW_2026-05-12.md`

## 2) Bookings

Planned:
- Nav module exists as disabled (`/bookings`).
- Documentation stack for booking engine is extensive.

Implemented now (partial and contextual, not full module):
- Backend booking task lifecycle endpoints/services exist.
- Backend confirmations endpoints/services exist.
- Frontend booking execution/confirmation/timeline panels exist inside trip ops route.
- No top-level `/bookings` route/page found.

Evidence:
- Backend:
  - `spine_api/routers/booking_tasks.py`
  - `spine_api/services/booking_task_service.py`
  - `spine_api/routers/confirmations.py`
  - `spine_api/services/confirmation_service.py`
- Frontend:
  - `frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx`
  - `frontend/src/components/workspace/panels/BookingExecutionPanel.tsx`
  - `frontend/src/components/workspace/panels/ConfirmationPanel.tsx`
  - `frontend/src/components/workspace/panels/ExecutionTimelinePanel.tsx`

## 3) Payments

Planned:
- Nav module exists as disabled (`/payments`).
- Payment deep-dive docs exist.

Implemented now (partial and embedded, not full module):
- Payment tracking model + update endpoint exist on booking-data path.
- Payment tracking UI exists inside ops panel.
- No top-level `/payments` route/page found.

Evidence:
- Backend:
  - `spine_api/server.py` (`/trips/{trip_id}/booking-data/payment` patch endpoint + payment model fields)
- Frontend:
  - `frontend/src/components/workspace/panels/PaymentTrackingCard.tsx`
  - `frontend/src/lib/api-client.ts` payment-tracking calls
- Docs:
  - `frontend/docs/PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md`

## 4) Suppliers

Planned:
- Nav module exists as disabled (`/suppliers`).
- Supplier portal/spec docs exist.

Implemented now:
- No canonical top-level suppliers route/page found.
- No clearly scoped supplier management runtime module surfaced in frontend app routes.

Evidence:
- `frontend/src/lib/nav-modules.ts`
- `frontend/docs/SUPPLIER_PORTAL_01_INTERFACE.md`
- `frontend/docs/SUPPLIER_PORTAL_MASTER_INDEX.md`

## 5) Knowledge Base

Planned:
- Nav module exists as disabled (`/knowledge`).
- Knowledge base docs/index exist.

Implemented now:
- No top-level `/knowledge` route/page found.
- Backend has domain knowledge helper (`src/intake/specialty_knowledge.py`), but not an exposed Knowledge Base product module.

Evidence:
- `frontend/src/lib/nav-modules.ts`
- `frontend/docs/KNOWLEDGE_BASE_MASTER_INDEX.md`
- `src/intake/specialty_knowledge.py`

## Exploration/research map coverage for coming-soon areas

Primary map:
- `/Users/pranay/Projects/exploration_maps/travel_agency_agent/EXPLORATION_MAP.md`

Relevant entries include:
- `C2. Booking & Supplier Integration` (stated partial)
- `C2. Payments & Finance` (stated partial)
- `R. Booking Lifecycle` (explicitly called out as critical and under-researched in map narrative)
- `AD. Travel Knowledge Domains`

Fresh codebase-vs-map audit generated now:
- `Docs/review/EXPLORATION_MAP_CODEBASE_AUDIT_2026-05-17.json`
- Summary:
  - total_features: 83
  - go: 14
  - fix: 45
  - maybe: 8
  - nogo: 16
  - status_drift: 43

Coming-soon-adjacent rows from this audit:
- `C2. Booking & Supplier Integration`: stated PARTIAL, actual PARTIAL, verdict FIX (gap analysis needed)
- `C2. Payments & Finance`: stated PARTIAL, actual NOT_STARTED, status drift
- `R. Booking Lifecycle`: stated NOT_STARTED, actual PARTIAL, status drift
- `AD. Travel Knowledge Domains`: stated/actual NOT_STARTED

## Existing status docs that already describe the same gap

- `Docs/status/LEFT_SIDEBAR_NAV_CONTEXT_REVIEW_2026-05-12.md`
  - Explicitly states Quotes/Bookings/Payments/Suppliers/Knowledge Base are planned/disabled.
  - Recommends readiness contracts before enablement.
- `Docs/status/FEATURE_LIST_V2_2026-05-12.md`
  - Marks disabled planned nav modules as SPEC.

## Architecture and ownership observations (root-cause level)

1) IA contract exists; module contract missing
- Navigation cleanly encodes intended product shape (`nav-modules.ts`), but each coming-soon module lacks canonical runtime contract (route + API + data model + acceptance criteria).

2) Partial capability already exists but is embedded in trip-level ops
- Booking/confirmation/payment capabilities exist as workflow slices under trip operations.
- Missing piece is elevation into first-class module ownership surfaces.

3) Documentation volume is high; implementation linkage is weak
- Many deep-dive docs exist for booking/payment/supplier/knowledge domains.
- Fewer docs map directly to executable route/API contracts and rollout gates.

4) Drift risk is active
- Exploration map audit shows high status drift count (43), indicating docs and implementation are diverging in multiple areas.

## Instruction/config/workflow review performed (as requested)

Reviewed project and home-level agent/config context including:

- Project:
  - `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
  - `/Users/pranay/Projects/AGENTS.md`
  - `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`
  - `/Users/pranay/Projects/travel_agency_agent/frontend/AGENTS.md`
  - `/Users/pranay/Projects/travel_agency_agent/frontend/CLAUDE.md`
  - `/Users/pranay/Projects/travel_agency_agent/frontend/docs/AGENT_SYS_03_PARALLEL_AGENTS.md`
  - `/Users/pranay/Projects/travel_agency_agent/.github/workflows/run-contract-guard.yml`
  - `workflows.html`, `data/workflows.json`

- Home-level (multi-agent ecosystem, including Claude/Qwen/Codex/Copilot):
  - `/Users/pranay/AGENTS.md`
  - `/Users/pranay/.claude/CLAUDE.md`
  - `/Users/pranay/.codex/AGENTS.md`
  - `/Users/pranay/.codex/config.toml`
  - `/Users/pranay/.qwen/settings.json`
  - `/Users/pranay/.copilot/settings.json`
  - `/Users/pranay/.copilot/skills/affordances/SKILL.md`

Referenced skills repositories/paths validated:
- `/Users/pranay/.claude/skills`
- `/Users/pranay/.agents/skills`
- `/Users/pranay/.hermes/skills`
- `/Users/pranay/Projects/skills`
- `/Users/pranay/Projects/external-skills`
- `/Users/pranay/Projects/openai-skills`
- `/Users/pranay/.codex/skills`

## Runtime verification evidence

Read-only git status:
- Branch: `master...origin/master`
- Parallel edits are present in working tree (multiple modified/untracked files).

Tests run for this review:
- Frontend nav planned-state tests:
  - `npm -C frontend run test -- src/lib/__tests__/nav-modules.test.ts`
  - Result: 2/2 passed.
- Frontend ops capability tests (partial coming-soon surfaces):
  - `PaymentTrackingCard`, `BookingExecutionPanel`, `ConfirmationPanel`
  - Result: 43/43 passed.
- Backend booking/payment-adjacent service tests:
  - `tests/test_booking_task_service.py`
  - `tests/test_confirmation_service.py`
  - `tests/test_booking_data.py`
  - Result: 107/107 passed.

## Risks and pattern-level issues discovered

- Pattern: planned module labels without corresponding canonical route contracts.
- Pattern: feature capability exists in embedded panels but not in top-level ownership surfaces.
- Pattern: status drift between exploration/research docs and current implementation state.
- Pattern: readiness contract recommendation exists in docs but appears not yet institutionalized as enforceable gate artifacts per module.

## Recommended next non-coding decision package

Before enabling any coming-soon module, define one readiness contract per module with hard gates:

For each of Quotes, Bookings, Payments, Suppliers, Knowledge Base:
- Canonical route(s) and navigation behavior
- Canonical backend endpoint contract(s)
- Source-of-truth data model(s)
- State machine/lifecycle ownership
- Security/privacy/compliance constraints
- Operator UX acceptance criteria
- Observability metrics and failure alerts
- Regression test matrix
- Rollout/rollback plan

This avoids shipping another “surface-first, contract-later” slice and keeps the architecture coherent.

## Notes

- No destructive git operations were performed.
- No product code was modified in this review pass.
- One review artifact was generated in-project for traceability:
  - `Docs/review/EXPLORATION_MAP_CODEBASE_AUDIT_2026-05-17.json`
