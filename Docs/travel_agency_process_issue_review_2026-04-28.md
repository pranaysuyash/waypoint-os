# Travel Agency Process Issue Review - 2026-04-28

## Scope
- Reproduced and investigated timeline 404s for workspace timeline fetches.
- Investigated inconsistent extraction in Singapore call scenario.
- Reviewed duplicate-looking workspace entries and run/trip linkage behavior.

## Reported Symptoms
- `GET /api/trips/<trip_id>/timeline` returned 404 from frontend.
- Timeline/progress UX was inconsistent and some tabs looked empty.
- Multiple new workspace entries appeared after repeated Process Trip attempts.
- Scenario extraction quality errors:
  - destination inferred as `Nov`/`Caller`/`Pace`/`Not`
  - party size inconsistent with explicit `Party: 6 pax ...`

## Root Cause Analysis

### 1) Timeline 404
- File: `frontend/src/lib/route-map.ts`
- Cause:
  - Dynamic route resolution used an ID-shape heuristic (`UUID`/`hex`) to replace path segments with `{id}`.
  - Real trip IDs are shaped like `trip_1cad495b9586`, which do not match the heuristic.
  - Result: `/api/trips/trip_.../timeline` was treated as unmapped and denied by catch-all 404.

### 2) Destination pollution from call-log labels
- File: `src/intake/extractors.py`
- Cause:
  - Destination candidate extraction scanned broad capitalized tokens and allowed geography hits from metadata labels.
  - In mixed narrative + call-log text, labels like `Caller`, `Pace`, `Not` leaked into destination candidates.

### 3) Party-size mismatch despite explicit `6 pax`
- File: `src/intake/extractors.py`
- Cause:
  - Family-composition inference computed a total (e.g., 5) and did not prioritize explicit declared headcount (`6 pax`).

### 4) Multiple entries in dashboard
- Evidence in `data/trips/`:
  - Recent trips have distinct `run_id` values, indicating multiple independent submissions.
  - This is not one run duplicating writes; it is repeated process executions, likely driven by unclear in-flight feedback earlier.

## Changes Implemented

### Frontend
- Updated dynamic route resolution to structural placeholder matching.
- File: `frontend/src/lib/route-map.ts`
- What changed:
  - Removed ID-shape inference matching.
  - Added explicit placeholder matching for route patterns (`{id}`, `{step_name}`) by path structure.
  - Added safe placeholder substitution for backend paths.

- File: `frontend/src/app/workbench/RunProgressPanel.tsx`
- What changed:
  - Current-step rendering now uses real `pipeline_stage_entered` events (not inferred first-pending heuristic).
  - Added explicit intake-only completion copy when run completes before decision stage.

### Backend extraction
- File: `src/intake/extractors.py`
- What changed:
  - Destination extraction now strips known call-log metadata lines before scanning for place names.
  - Added hard filters for call-note label tokens (`caller`, `pace`, `budget`, `interests`, `not`, etc.).
  - Added month-token filter in generic destination match path.
  - Party extraction now prefers explicit headcount (`N pax/people/travelers`) when present.

### Backend run progress lifecycle
- Files:
  - `src/intake/orchestration.py`
  - `spine_api/server.py`
- What changed:
  - `run_spine_once` now emits phase lifecycle callbacks: `entered`, `completed`, `failed`.
  - Server callback handling now consumes lifecycle payloads and emits run events at true phase boundaries.
  - Stage timing now measures `completed - entered` per stage instead of same-tick pseudo-timing.
  - Failure/block events now include `stage_at_failure` / `stage_at_block` context where available.

## Verification Evidence

### Tests
- Frontend:
  - `./node_modules/.bin/vitest run src/lib/__tests__/route-map.test.ts`
  - Result: `7 passed`
- Backend:
  - `uv run pytest -q tests/test_extraction_fixes.py tests/test_orchestration_stage_progress.py tests/test_run_state_unit.py`
  - Result: `138 passed`

### Added/updated regression coverage
- `frontend/src/lib/__tests__/route-map.test.ts`
  - Validates `trip_*` timeline route resolves correctly.
  - Validates placeholder substitution for run step route.
- `tests/test_extraction_fixes.py`
  - Validates explicit `6 pax` overrides inferred family count.
  - Validates month/call-log labels are excluded from destination candidates.
- `tests/test_orchestration_stage_progress.py`
  - Validates stage lifecycle ordering (`entered` before `completed`) for orchestrated run phases.

### Scenario-level spot check
- Input: user-provided Singapore scenario text with mixed narrative + call log.
- Extraction result after fix:
  - destination candidates: `['Singapore']`
  - party size: `6`

### Live run spot check
- Submitted authenticated runs against `/run` and polled `/runs/{id}` + `/runs/{id}/events`.
- Verified event stream now contains true in-flight `pipeline_stage_entered` followed later by `pipeline_stage_completed` for executed stages.

## Remaining Risks / Next Work
- Timeline 404 is fixed at route-mapping level.
- Core UX gap remains:
  - Progress steps are still not fully phase-true from orchestration internals across long runs.
  - Next task should instrument real phase boundaries in orchestration and emit events at actual stage transitions.
