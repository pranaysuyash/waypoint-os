# Workbench Randomized Testing: Draft Flow + Extraction Fixes

Date: 2026-05-11 22:47 IST
Repo: `/Users/pranay/Projects/travel_agency_agent`

## Scope

Randomized live-user testing in Chrome against `http://localhost:3000/workbench?draft=...&tab=...` using the test agency user session.

## Runtime Findings

### 1. Draft creation was failing with backend 500

Evidence:

- Frontend repeatedly logged `POST /api/drafts 500`.
- Backend logged a Pydantic route model error for `routers.drafts.CreateDraftRequest`.
- Root cause: `spine_api/server.py` first attempted top-level `from routers import ...`, which fails under the normal package launch path (`uvicorn spine_api.server:app`) and falls back to dynamic import. That fallback bypassed normal package module registration, so postponed annotations could not be resolved by FastAPI/Pydantic.

Resolution:

- Updated the app shell router imports in `spine_api/server.py` to use package-qualified `from spine_api.routers import ...` imports.
- Verified `POST /api/drafts` returns 200 with a real `draft_id`.

### 2. Blocked inquiry recovery pointed to a non-existent Trip Details tab

Evidence:

- After processing a draft, the UI said `Check the Trip Details tab` and showed `Fix Missing Details`.
- The visible workbench tabs were only `New Inquiry` and `Risk Review`, so the user could not follow the instruction.

Resolution:

- Reintroduced the existing canonical `PacketTab` as `Trip Details` when extracted packet/validation data exists, or when a draft is blocked/failed.
- Blocked/failed runs now route users to `Trip Details` instead of leaving them on `New Inquiry` with no details.

### 3. Runtime extraction misses from the Bali family inquiry

Test input used live:

```text
Family of four wants 6 nights in Bali in July. Two adults, two kids age 6 and 9. Prefer beach resort with kids club, vegetarian food, and one villa or connecting rooms. Budget around INR 4L excluding flights. They can travel any week after July 10. Need something calm, safe, and not too far from the airport.
```

Before:

- `party_size` missing even though child ages were extracted.
- `date_window` missing even though `after July 10` was present.
- `origin_city` incorrectly extracted as `the airport`.
- `trip_purpose` missing despite strong family leisure signals.

After:

- `party_size = 4`
- `party_composition = { adults: 2, children: 2 }`
- `date_window = after july 10`
- `date_start = 2026-07-10`
- `trip_purpose = family leisure`
- `origin_city` remains missing instead of falsely becoming `the airport`

Remaining expected blocker:

- `origin_city` is still required and truly absent from the customer request.

## Verification

Commands run:

```bash
uv run pytest tests/test_extraction_fixes.py -q
cd frontend && npm run -s test -- --run 'src/app/(agency)/workbench/__tests__/page.test.tsx'
cd frontend && npm run -s test -- --run 'src/app/(agency)/workbench/__tests__/page.test.tsx' 'src/app/(agency)/workbench/__tests__/PipelineFlow.test.tsx' 'src/components/workspace/panels/__tests__/IntakePanel.test.tsx'
uv run pytest tests/test_drafts_router_contract.py -q
cd frontend && npm run -s typecheck -- --pretty false
python tools/dev_server_manager.py status --service all
```

Results:

- `tests/test_extraction_fixes.py`: 166 passed.
- Workbench page focused test: 3 passed.
- Workbench/Pipeline/Intake focused frontend suite: 31 passed.
- Draft router contract: 1 passed.
- Frontend typecheck: passed.
- Backend and frontend health: both 200.

Runtime API verification:

- `POST /run` returned 200.
- Polled run `3355c6c3-1c5d-4a55-80d3-c941e6b92817`.
- Final state: `blocked` only because `origin_city` is missing.
- Extracted facts confirmed: date, start date, party size, party composition, and trip purpose are present.

## Files Changed

- `spine_api/server.py`
- `frontend/src/app/(agency)/workbench/PageClient.tsx`
- `src/intake/extractors.py`
- `tests/test_extraction_fixes.py`
- `Docs/status/WORKBENCH_RANDOMIZED_TESTING_DRAFT_FLOW_2026-05-11.md`

## Follow-Ups

- Improve operator recovery copy for the remaining origin blocker: ask “Which city are they departing from?” directly in the Trip Details panel or offer an inline edit.
- Format object-valued extracted facts in `PacketTab`; `Owner Constraints` currently renders as `[object Object]`.
- Consider auto-filling `origin_city` only when a real departure city appears, never from airport transfer/proximity language.

## Update: 2026-05-12 00:38 IST

### Additional Live/Runtime Checks

- Restart/health path rechecked with `python tools/dev_server_manager.py start --service all`; existing backend/frontend processes were healthy (`backend` pid `35566`, `frontend` pid `88042`).
- Chrome/Computer Use inspection verified the overview page is currently internally consistent in the visible summary, cards, planning progress, jump-to links, and planning status: `2` trips in planning, `1618` leads, `3` quotes, `535` system-check items.
- Backend/frontend logs show the sandboxed server start attempt produced `PermissionError` / `listen EPERM`, but the already-running elevated dev processes remained healthy and served requests. Treat those startup errors as environment/sandbox artifacts, not current app runtime failures.

### Completed Follow-Up: Structured Packet Value Rendering

Issue:

- `PacketTab` rendered arrays of structured objects with JavaScript object coercion, e.g. owner constraints could appear as `[object Object]`.
- Root cause: `_formatValue()` handled plain objects with `JSON.stringify()` but handled arrays with `value.join(', ')`, which coerces array items before recursively formatting them.

Resolution:

- Changed `PacketTab` to format arrays recursively.
- Added readable object rendering for common packet structures, including owner constraint records with `{ text, visibility }`.
- Reused the same formatter for summary cards, derived signals, and contradiction values so nested packet data has one consistent display boundary.

Files:

- `frontend/src/app/(agency)/workbench/PacketTab.tsx`
- `frontend/src/app/(agency)/workbench/__tests__/PacketTab.test.tsx`

### Completed Follow-Up: Singular/Plural Validation Reason

Issue:

- Blocked run copy could say `Structural validation failed (1 errors)`.

Resolution:

- Updated `NB01CompletionGate` to pluralize `error`/`errors` correctly at the backend gate source.
- Added regression assertions for both `1 error` and `2 errors`.

Files:

- `src/intake/gates.py`
- `tests/test_validation_split.py`

### Verification Evidence

Commands run on 2026-05-12:

```bash
cd frontend && npm run -s test -- --run 'src/app/(agency)/workbench/__tests__/PacketTab.test.tsx'
uv run pytest tests/test_validation_split.py -q
cd frontend && npm run -s test -- --run 'src/app/(agency)/workbench/__tests__/PacketTab.test.tsx' 'src/app/(agency)/workbench/__tests__/page.test.tsx' 'src/app/(agency)/workbench/__tests__/PipelineFlow.test.tsx' 'src/components/workspace/panels/__tests__/IntakePanel.test.tsx'
cd frontend && npm run -s typecheck -- --pretty false
python tools/dev_server_manager.py status --service all
```

Results:

- `PacketTab.test.tsx`: 1 passed.
- `tests/test_validation_split.py`: 22 passed.
- Focused workbench/frontend suite: 4 files passed, 32 tests passed.
- Frontend typecheck: passed.
- Dev server status: backend and frontend healthy (`200`).

### Remaining Follow-Ups

- Reprocess the live draft in Chrome once the active DevTools focus issue is cleared; direct runtime contract already verifies the extractor path, but a final browser pass should confirm the user sees only the true missing `origin_city` blocker after the latest backend/frontend hot reload.
- Improve the missing-origin recovery UX from generic missing-field text to a direct operator prompt: `Which city will the travelers depart from?`.
- Investigate recurring OpenTelemetry export warnings to `localhost:4317`; they are non-blocking but noisy during dev.

## Update: 2026-05-12 00:53 IST

### Added: Contextual Unknown-Field Prompts in Trip Details

Problem:

- Trip Details listed unknown fields and machine reasons, but operators still had to infer what question to ask the traveler.
- This slowed triage in blocked runs and made `origin_city` recovery less direct.

Solution:

- Added field-specific operator prompts in `PacketTab` for unknowns, rendered in both:
  - blocked-validation `Missing fields` banner list, and
  - full `Unknowns` section.
- Prompt mapping now includes:
  - `origin_city` → `Which city will the travelers depart from?`
  - `date_window` → `What are the exact travel dates or date range?`
  - `destination_candidates` → `Which destination(s) is the traveler considering?`
  - `budget_raw_text` → `What budget range should we plan within?`
  - `trip_purpose` → `What is the purpose of this trip (family holiday, honeymoon, business, etc.)?`
  - `party_size` → `How many travelers are going?`

Files:

- `frontend/src/app/(agency)/workbench/PacketTab.tsx`
- `frontend/src/app/(agency)/workbench/__tests__/PacketTab.test.tsx`

### Parallel Drift Stabilization (Typecheck)

During verification, full frontend typecheck exposed parallel-work drift unrelated to PacketTab logic:

- `DocumentsPage` passed unsupported `fallbackHref` to `BackToOverviewLink`.
- `OpsPanel` had strict-null/shape typing issues around `readiness.signals`.

Stabilization fixes:

- `frontend/src/app/(agency)/documents/PageClient.tsx` → removed unsupported prop and used canonical `BackToOverviewLink` invocation.
- `frontend/src/app/(agency)/workbench/OpsPanel.tsx` → added safe object narrowing for `signals` and null-safe access patterns.

### Verification

Commands run:

```bash
cd frontend && npm run -s test -- --run 'src/app/(agency)/workbench/__tests__/PacketTab.test.tsx' 'src/app/(agency)/workbench/__tests__/page.test.tsx' 'src/app/(agency)/workbench/__tests__/PipelineFlow.test.tsx' 'src/components/workspace/panels/__tests__/IntakePanel.test.tsx'
cd frontend && npm run -s typecheck -- --pretty false
uv run pytest tests/test_validation_split.py -q
python tools/dev_server_manager.py status --service all
```

Results:

- Workbench-focused frontend tests: 33 passed.
- PacketTab regression tests: 2 passed.
- Frontend typecheck: passed.
- Backend validation split tests: 22 passed.
- Dev servers: backend/frontend healthy (`200`).

## Update: 2026-05-12 01:32 IST

### Intake Follow-up Contract Upgrade (Field-Aware Prompts)

Problem:

- `PlanningDetailSection` used a generic `Ask traveler` action with no field context.
- Operators could click follow-up actions, but the draft text did not always capture the exact missing detail question.

First-principles fix:

- Extended canonical `PlanningDetailRow` shape with `travelerPrompt` so each missing detail owns its explicit traveler-facing question.
- Promoted `onAskTraveler` from no-arg to field-aware callback and passed the full row context.
- Displayed the question inline in each planning card (`Ask: ...`) so operators can validate intent before sending.
- Updated follow-up behavior so clicking `Ask traveler` appends a targeted `Specific question: ...` line if it is not already present.
- Kept this additive by extending existing row/section contracts rather than introducing a parallel follow-up system.

Files changed:

- `frontend/src/components/workspace/panels/IntakePanel.tsx`
- `frontend/src/components/workspace/panels/IntakeFieldComponents.tsx`
- `frontend/src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx`

### Verification

Commands:

```bash
cd frontend && npm run -s test -- --run 'src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx' 'src/components/workspace/panels/__tests__/IntakePanel.test.tsx'
cd frontend && npm run -s typecheck -- --pretty false
python tools/dev_server_manager.py status --service all
```

Results:

- Intake field/panel suites: 39 passed.
- Frontend typecheck: passed.
- Dev servers: backend/frontend healthy (`200`).

## Update: 2026-05-12 09:10 IST

### Shared Prompt Contract (Drift-Proofing)

Problem:

- Prompt wording for missing details was duplicated across Intake planning rows and Workbench Trip Details unknown-field rendering.
- This creates long-term drift risk (different prompts for the same missing field) and weakens operator consistency.

Architectural fix:

- Added a shared prompt contract module:
  - `frontend/src/lib/traveler-prompts.ts`
- Canonical APIs:
  - `getTravelerPromptForUnknownField(fieldName)`
  - `getTravelerPromptForPlanningDetail(detailId)`
- Rewired both surfaces to consume the shared contract:
  - `frontend/src/app/(agency)/workbench/PacketTab.tsx`
  - `frontend/src/components/workspace/panels/IntakePanel.tsx`

Quality hardening:

- Added contract tests for prompt lookup behavior:
  - `frontend/src/lib/__tests__/traveler-prompts.test.ts`
- Updated intake field-component test fixtures to align with canonical phrasing.

Why this is better long-term:

- Single source of truth for traveler prompt language.
- Reduced copy drift as more tabs/surfaces consume missing-detail prompts.
- Safer iteration path for future localization/brand voice changes.

### Verification

Commands:

```bash
cd frontend && npm run -s test -- --run 'src/lib/__tests__/traveler-prompts.test.ts' 'src/app/(agency)/workbench/__tests__/PacketTab.test.tsx' 'src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx' 'src/components/workspace/panels/__tests__/IntakePanel.test.tsx'
cd frontend && npm run -s typecheck -- --pretty false
python tools/dev_server_manager.py status --service all
```

Results:

- Targeted frontend suites: 44 passed.
- Frontend typecheck: passed.
- Dev servers: backend/frontend healthy (`200`).

## Update: 2026-05-12 09:26 IST

### Scope
- Eliminated remaining Packet UI drift between Workbench `PacketTab` and shared `PacketPanel` by aligning rendering and issue surfacing behavior.

### Changes
- Updated `frontend/src/components/workspace/panels/PacketPanel.tsx`:
  - Summary cards now use `_formatValue(...)` instead of raw `String(...)` coercion.
  - Added explicit sections for:
    - `Ambiguities` (field + raw value + ambiguity type)
    - `Missing Details` (unknown reason + traveler-facing prompt)
    - `Contradictions` (values + sources)
  - Wired unknown-field prompts to shared contract: `getTravelerPromptForUnknownField(...)`.
  - Kept type-safety aligned with canonical packet contracts (`Ambiguity.raw_value`, `PacketContradiction.values/sources`).
- Stabilized unrelated typecheck regression introduced in parallel edits:
  - Updated `frontend/src/components/workspace/panels/__tests__/ExtractionHistoryPanel.test.tsx` to assert page text without relying on a block-scoped `container` binding in that test case.

### Verification
- `cd frontend && npm run -s test -- --run 'src/components/workspace/panels/__tests__/ExtractionHistoryPanel.test.tsx' 'src/app/(agency)/workbench/__tests__/PacketTab.test.tsx' 'src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx' 'src/components/workspace/panels/__tests__/IntakePanel.test.tsx' 'src/lib/__tests__/traveler-prompts.test.ts'`
  - Result: **5 files, 53 tests passed**.
- `cd frontend && npm run -s typecheck -- --pretty false`
  - Result: **pass**.

### Outcome
- Packet surfaces are now contract-consistent and traveler-prompt-consistent.
- Workbench packet diagnostics expose operator-useful unknown/ambiguity/contradiction context in both tab and panel paths.
