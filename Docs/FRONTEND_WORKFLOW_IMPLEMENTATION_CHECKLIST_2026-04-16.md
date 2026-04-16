---
goal: Frontend Workflow Implementation Checklist (Coverage → Delivery)
version: 1.0
date_created: 2026-04-16
last_updated: 2026-04-16
owner: Frontend Team
status: 'Planned'
tags: [frontend, workflow, implementation, checklist, routes, coverage]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

This checklist converts `Docs/FRONTEND_WORKFLOW_COVERAGE_2026-04-16.md` into an execution-ready implementation plan with route-level acceptance criteria.

---

## 1. Requirements & Constraints

- **REQ-001**: Preserve existing implemented UX on `/`, `/inbox`, and `/workbench` while expanding missing workflow coverage.
- **REQ-002**: Implement trip-scoped workflow under `/workspace/[tripId]/*` with shared layout and secondary navigation.
- **REQ-003**: Build owner routes (`/owner/reviews`, `/owner/insights`) beyond placeholders.
- **REQ-004**: Add missing Surface B modules (proposals, trips-in-progress, booking-readiness, change-recovery, timeline).
- **REQ-005**: Add Surface D traveler-facing routes and flow.
- **REQ-006**: Add Surface E public acquisition routes (itinerary checker + SEO/fix flow).
- **CON-001**: Do not delete or regress existing docs and route contracts.
- **CON-002**: Keep business decision logic in backend/BFF; frontend remains presentation + orchestration only.
- **GUD-001**: Follow design semantics in `DESIGN.md` and state semantics already used in app.
- **GUD-002**: Every route implementation must include explicit loading, empty, and error states.
- **PAT-001**: Prefer reusing existing workbench tab logic in workspace routes over duplicate implementations.

---

## 2. Implementation Steps

### Implementation Phase 1 — Route Foundation and Navigation
- **GOAL-001**: Establish coherent route topology and navigation for operator workflows.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create trip-scoped shell route: `frontend/src/app/workspace/[tripId]/layout.tsx` with secondary nav tabs (intake/packet/decision/strategy/output/safety/activity). |  |  |
| TASK-002 | Update inbox card routing from `/workbench` to `/workspace/[tripId]/intake` while keeping a deliberate path to `/workbench` for internal simulation tooling. |  |  |
| TASK-003 | Add missing internal nav entries in `frontend/src/components/layouts/Shell.tsx` for Workspaces, Proposals, Trips in Progress, Settings. |  |  |
| TASK-004 | Add canonical operator index route `frontend/src/app/workspace/page.tsx` for workspace listing and quick filters. |  |  |

### Implementation Phase 2 — Surface B (Operator App)
- **GOAL-002**: Deliver trip-scoped operator workflow modules.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-005 | Implement `frontend/src/app/workspace/[tripId]/intake/page.tsx` with left(raw input)/center(known+unknown)/right(next actions + traveler-safe draft). |  |  |
| TASK-006 | Implement `frontend/src/app/workspace/[tripId]/packet/page.tsx` by adapting `workbench/PacketTab.tsx` with trip-scoped data loading and action affordances. |  |  |
| TASK-007 | Implement `frontend/src/app/workspace/[tripId]/decision/page.tsx` by adapting `workbench/DecisionTab.tsx` and rendering follow-up workflows. |  |  |
| TASK-008 | Implement `frontend/src/app/workspace/[tripId]/strategy/page.tsx` and `.../safety/page.tsx` with trip-scoped operations and auditability affordances. |  |  |
| TASK-009 | Implement `frontend/src/app/workspace/[tripId]/output/page.tsx` as traveler-safe preview with send-prep and confidence framing. |  |  |
| TASK-010 | Create new Surface B routes: `/proposals`, `/trips-in-progress`, `/booking-readiness`, `/change-recovery`, `/conversation-timeline` with usable list/detail skeletons. |  |  |

### Implementation Phase 3 — Surface C (Owner Console)
- **GOAL-003**: Convert owner pages from placeholders to operational screens.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-011 | Implement `/owner/reviews` queue with filters (risk, value, SLA), decision cards, and action history panel. |  |  |
| TASK-012 | Implement `/owner/insights` dashboard with conversion, turnaround, margin adherence, revision loops, escalation heatmap sections. |  |  |
| TASK-013 | Add owner-specific drill-down routes for exception/escalation and margin policy governance. |  |  |

### Implementation Phase 4 — Surface D (Traveler-Facing)
- **GOAL-004**: Provide traveler-visible workflow routes and interactions.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-014 | Add traveler proposal route(s) with safe copy, milestone timeline, and confidence communication. |  |  |
| TASK-015 | Add clarification response flow and change request flow routes. |  |  |
| TASK-016 | Add traveler status timeline route with event history and next expected milestone. |  |  |

### Implementation Phase 5 — Surface E (Public Acquisition)
- **GOAL-005**: Deliver public acquisition funnel and SEO entry points.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-017 | Implement itinerary checker funnel route(s): upload/paste → checks → score/issues. |  |  |
| TASK-018 | Implement “Fix this plan” conversion flow with lead capture and handoff to internal pipeline. |  |  |
| TASK-019 | Implement SEO landing route structure (destination/problem templates). |  |  |

### Implementation Phase 6 — QA, Accessibility, and Performance Gates
- **GOAL-006**: Verify completeness and non-regression.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-020 | Add route-level unit/integration tests for every new module; ensure loading/error/empty states tested. |  |  |
| TASK-021 | Run accessibility audit on all new routes (focus order, ARIA roles, keyboard nav, contrast). |  |  |
| TASK-022 | Run performance checks for route transitions and primary list/detail pages; remediate regressions. |  |  |
| TASK-023 | Update docs (`Docs/INDEX.md`, route map docs, release notes) after implementation is merged. |  |  |

---

## 3. Route-Level Acceptance Criteria (Canonical Checklist)

### Existing routes to preserve
- **ACR-001 (`/`)**: Dashboard renders stats, pipeline summary, and recent trip activity without regressions.
- **ACR-002 (`/inbox`)**: Filters and trip cards remain functional; clicking a trip opens trip-scoped workspace intake.
- **ACR-003 (`/workbench`)**: Workbench remains available for internal intelligence tooling and simulations.

### Trip-scoped workspace routes
- **ACR-004 (`/workspace/[tripId]/intake`)**: Three-panel intake layout present; supports notes, known/unknown extraction, and recommended next actions.
- **ACR-005 (`/workspace/[tripId]/packet`)**: Renders facts/signals/ambiguities/unknowns/contradictions with raw toggle and provenance cues.
- **ACR-006 (`/workspace/[tripId]/decision`)**: Shows decision state, blockers, rationale, follow-up set, and confidence.
- **ACR-007 (`/workspace/[tripId]/strategy`)**: Displays sequence/branch strategy and constraints for operator execution.
- **ACR-008 (`/workspace/[tripId]/safety`)**: Displays leakage checks, sanitization diff, and pass/fail assertions.
- **ACR-009 (`/workspace/[tripId]/output`)**: Displays traveler-safe preview, confidence framing, and send-prep status.
- **ACR-010 (`/workspace/[tripId]/activity`)**: Displays chronological event timeline for trip actions and system transitions.

### Owner routes
- **ACR-011 (`/owner/reviews`)**: Queue supports sorting/filtering and approval actions with audit trace.
- **ACR-012 (`/owner/insights`)**: Dashboard shows conversion, turnaround, margin adherence, revision loops, and escalations.

### Surface B expansion routes
- **ACR-013 (`/proposals`)**: List/detail proposal workflow exists with status and action controls.
- **ACR-014 (`/trips-in-progress`)**: Active trip board/list exists with stage and risk visibility.
- **ACR-015 (`/booking-readiness`)**: Readiness checks and blockers are visible per trip.
- **ACR-016 (`/change-recovery`)**: Change request and recovery actions are trackable and actionable.
- **ACR-017 (`/conversation-timeline`)**: Conversation events are queryable with source and timestamp visibility.

### Surface D & E routes
- **ACR-018 (Traveler-facing routes)**: Proposal, clarification, timeline, and change flow routes are accessible and coherent.
- **ACR-019 (Itinerary checker)**: Public checker flow works end-to-end with clear result output.
- **ACR-020 (Fix flow/SEO landings)**: Conversion handoff exists and SEO routes render with valid metadata.

---

## 4. Alternatives

- **ALT-001**: Build everything directly in `/workbench` tabs only. **Rejected** because spec requires distinct operator/traveler/public surfaces and clearer IA.
- **ALT-002**: Defer trip-scoped workspace and add owner/public first. **Rejected** because operator workflow is the central dependency chain.
- **ALT-003**: Implement traveler/public first for acquisition optics. **Rejected** due to weak internal fulfillment path risk.

---

## 5. Dependencies

- **DEP-001**: Existing BFF API routes in `frontend/src/app/api/**` for trip/scenario/pipeline/stats.
- **DEP-002**: Existing workbench store (`frontend/src/stores/workbench.ts`) and tab components for reuse.
- **DEP-003**: State and visual semantics from `DESIGN.md` and current shell/app styling.
- **DEP-004**: Product scope reference in `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`.

---

## 6. Files (Planned Target Areas)

- **FILE-001**: `frontend/src/components/layouts/Shell.tsx` (internal nav expansion)
- **FILE-002**: `frontend/src/app/inbox/page.tsx` (trip link behavior)
- **FILE-003**: `frontend/src/app/workspace/[tripId]/layout.tsx` (new)
- **FILE-004**: `frontend/src/app/workspace/[tripId]/intake/page.tsx`
- **FILE-005**: `frontend/src/app/workspace/[tripId]/packet/page.tsx`
- **FILE-006**: `frontend/src/app/workspace/[tripId]/decision/page.tsx`
- **FILE-007**: `frontend/src/app/workspace/[tripId]/strategy/page.tsx`
- **FILE-008**: `frontend/src/app/workspace/[tripId]/safety/page.tsx`
- **FILE-009**: `frontend/src/app/workspace/[tripId]/output/page.tsx`
- **FILE-010**: New route files for proposals/trips-in-progress/booking-readiness/change-recovery/conversation-timeline
- **FILE-011**: New traveler-facing route files
- **FILE-012**: New public funnel/SEO route files
- **FILE-013**: Related tests in `frontend/src/**/__tests__/*`

---

## 7. Testing

- **TEST-001**: Route rendering and state tests for each new/converted page.
- **TEST-002**: Navigation path tests (Inbox → workspace trip route).
- **TEST-003**: Accessibility tests for tabs/nav/page structure.
- **TEST-004**: API integration tests for route data dependencies.
- **TEST-005**: Visual and interaction smoke checks for critical flows.

---

## 8. Risks & Assumptions

- **RISK-001**: Reusing workbench components may leak internal-only semantics into traveler-facing surfaces.
- **RISK-002**: Route proliferation without shared layouts can increase maintenance overhead.
- **RISK-003**: Public acquisition pages may drift from backend readiness if implemented too early.
- **ASSUMPTION-001**: Existing BFF endpoints can support first-pass UI completion without schema-breaking backend work.
- **ASSUMPTION-002**: Workbench logic is stable enough to be adapted into trip-scoped routes.

---

## 9. Related Specifications / Further Reading

- `Docs/FRONTEND_WORKFLOW_COVERAGE_2026-04-16.md`
- `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`
- `DESIGN.md`
