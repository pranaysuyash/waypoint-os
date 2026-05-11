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
