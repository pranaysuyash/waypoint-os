# Next.js Frontend Implementation Track (Full Scope, Corrected)

Date: 2026-04-15 10:03:53 IST
Authority:
- `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`

## 0) Truth Sources and Conflict Resolution

Implementation path truth:
- Next.js App Router only.
- No Streamlit runtime path is active for this build track.

Spec usage split:
- Full Product Spec (`FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`) is product truth.
- This file is build sequencing truth.
- Workbench component/checklist docs are behavior and acceptance references only (not stack/runtime choice).

## 1) Stack + Repo Layout (Target)

Stack:
- Next.js App Router
- TypeScript
- Server Actions + Route Handlers (BFF)
- Shared design system/components

Proposed layout:
```text
frontend/
  app/
    (public)/
    app/
      inbox/
      workbench/
      workspace/[tripId]/
      owner/
    traveler/
  components/
    shell/
    cards/
    state/
    decision/
    strategy/
    safety/
    funnel/
  lib/
    api/
    schemas/
    formatters/
    adapters/
  tests/
```

## 2) Route-by-Route Build Track

### Track A: Internal Operator Shell
1. `/app/inbox`
- Goal: queue-first triage
- Includes: trip cards, state badge, suggested next action, urgency chips

2. `/app/workbench`
- Goal: engineering/product introspection in product shell
- Includes: intake panel, packet/decision/strategy/safety tabs, fixture replay

3. `/app/workspace/[tripId]/intake`
- Goal: normal intake handling for operators
- Includes: incoming context, known/unknown, clarify prompts, mode/stage controls

4. `/app/workspace/[tripId]/packet`
- Goal: NB01 human summary + raw toggle

5. `/app/workspace/[tripId]/decision`
- Goal: NB02 explanation-first decisioning view

6. `/app/workspace/[tripId]/strategy`
- Goal: NB03 plan sequence and internal/traveler split

7. `/app/workspace/[tripId]/output`
- Goal: traveler-safe proposal preview and send-prep

8. `/app/workspace/[tripId]/safety`
- Goal: leakage checks + sanitization diff + pass/fail assertions

### Track B: Owner Surfaces
9. `/app/owner/reviews`
- Goal: approval queue for high-risk/high-margin-impact items

10. `/app/owner/insights`
- Goal: conversion, turnaround, margin adherence, revision loops, escalation heatmap

### Track C: Traveler Surface
11. `/trip/[shareToken]`
- Goal: traveler-safe proposal view

12. `/trip/[shareToken]/changes`
- Goal: structured change request flow

13. `/trip/[shareToken]/timeline`
- Goal: progress/state timeline

### Track D: Public Growth Surface
14. `/itinerary-checker`
- Goal: upload/paste funnel entry

15. `/itinerary-checker/result/[sessionId]`
- Goal: score/issues, included-vs-missing, CTA

16. `/destinations/[slug]/itinerary-check`
- Goal: SEO destination intent pages

17. `/problems/[slug]`
- Goal: SEO problem-aware pages

## 3) Component Ownership Map

### Shell + Navigation
- `AppShell`
- `WorkspaceSubnav`
- `ModeSwitch` (Ops/Selling)
Owner: Frontend Platform

### State + Signals
- `StateBadge`
- `ConfidenceBadge`
- `RiskFlagList`
Owner: Decisioning UI

### Intake/Packet
- `IncomingContextPanel`
- `KnownUnknownGrid`
- `PacketSummaryCards`
- `PacketRawToggle`
Owner: Intake UI

### Decision/Strategy
- `DecisionRationaleCard`
- `BlockerList`
- `FollowupQuestionPanel`
- `StrategySequence`
- `BranchPromptList`
Owner: Decision + Strategy UI

### Safety/Compliance
- `LeakagePanel`
- `SanitizationDiffPanel`
- `AssertionResults`
Owner: Safety Boundary UI

### Public Funnel
- `Dropzone`
- `ProcessingChecks`
- `ScoreCard`
- `IssuesList`
- `CoverageMatrix`
- `EmailCapture`
Owner: Growth UI

## 4) API/BFF Contract (Next Route Handlers)

## 4.1 Spine Run
`POST /api/spine/run`

Request:
```json
{
  "raw_note": "string",
  "owner_note": "string | null",
  "structured_json": {},
  "itinerary_text": "string | null",
  "stage": "discovery|shortlist|proposal|booking",
  "operating_mode": "normal_intake|audit|emergency|follow_up|cancellation|post_trip|coordinator_group|owner_review",
  "strict_leakage": true,
  "scenario_id": "string | null"
}
```

Response:
```json
{
  "packet": {},
  "validation": {},
  "decision": {},
  "strategy": {},
  "internal_bundle": {},
  "traveler_bundle": {},
  "leakage": { "ok": true, "items": [] },
  "assertions": [],
  "run_ts": "ISO-8601"
}
```

## 4.2 Scenario List
`GET /api/scenarios`

Response:
```json
{
  "items": [
    { "id": "clean-family-discovery", "title": "Clean family discovery" }
  ]
}
```

## 4.3 Scenario Load
`GET /api/scenarios/[id]`

Response:
```json
{
  "id": "string",
  "input": {},
  "expected": {}
}
```

## 4.4 Fixture Compare
`POST /api/fixtures/compare`

Request:
```json
{ "scenario_id": "string", "actual": {} }
```

Response:
```json
{
  "pass": true,
  "checks": [
    { "name": "decision_state", "pass": true, "expected": "ASK_FOLLOWUP", "actual": "ASK_FOLLOWUP" }
  ]
}
```

## 5) Runtime Integration Rules

- All business logic must remain in shared intake modules.
- One shared orchestrator entrypoint under `src/intake/` should be used by:
  - `/api/spine/run`
  - `/api/fixtures/compare`
  - `/app/workbench`
- BFF must orchestrate existing functions only:
  - `ExtractionPipeline`
  - `validate_packet`
  - `run_gap_and_decision`
  - `build_session_strategy_and_bundle`
  - `build_traveler_safe_bundle` / `build_internal_bundle`
- No decisioning implemented in frontend components.
- Strict leakage mode must hard-fail visibly:
  - traveler preview suppressed/invalidated on leakage
  - assertion panel fails with explicit reason
- No reruns of spine on tab switch for inspection routes.

## 6) Implementation Tickets (Execution Sequence)

### Phase P0: Foundation (Contract-Correct First)
- FE-001: Initialize Next.js frontend workspace and app shell
- FE-002: Add global state semantics and design tokens (state colors locked)
- FE-003: Implement `/api/spine/run` with spine-aligned enums and shared module orchestration
- FE-004: Implement scenario APIs (`/api/scenarios*`)

### Phase P1: Internal Product Core (First Deliverable)
- FE-011: `/app/workbench`
- FE-012: `/app/workspace/[tripId]/intake`
- FE-013: `/app/workspace/[tripId]/packet`
- FE-014: `/app/workspace/[tripId]/decision`
- FE-015: `/app/workspace/[tripId]/strategy`
- FE-016: `/app/workspace/[tripId]/output`
- FE-017: `/app/workspace/[tripId]/safety`

### Phase P2: Inbox + Owner + Traveler
- FE-010: `/app/inbox`
- FE-020: `/app/owner/reviews`
- FE-021: `/app/owner/insights`
- FE-022: `/trip/[shareToken]`
- FE-023: `/trip/[shareToken]/changes`
- FE-024: `/trip/[shareToken]/timeline`

### Phase P3: Public Growth Surface
- FE-030: `/itinerary-checker`
- FE-031: `/itinerary-checker/result/[sessionId]`
- FE-032: `/destinations/[slug]/itinerary-check`
- FE-033: `/problems/[slug]`

## 7) Test Plan

### UI + integration (Playwright)
- App shell render
- Inbox load
- Run spine from intake
- Decision state visibility
- Internal vs traveler-safe separation
- Leakage panel visibility + strict failure case
- Scenario load + fixture compare

### Contract tests
- `POST /api/spine/run` schema assertions
- Scenario API schema assertions
- Fixture compare check semantics

## 8) “Coming Soon” Rules (Allowed)

If a route/module is phased, it may show `Coming soon` only with:
- target capability
- dependency blocker
- expected activation phase

No empty placeholders without context.

## 9) Done Criteria (Program Level)

Program considered complete when:
- all route groups (A/B/C/D) are present in product shell,
- BFF contracts are stable and tested,
- safety boundary is visible and enforceable in UI,
- scenario/fixture replay works end-to-end,
- no frontend business-logic duplication exists.
