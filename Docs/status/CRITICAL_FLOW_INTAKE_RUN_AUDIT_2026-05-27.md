# Critical Flow Audit: Capture Intake → Process Trip → Operator Visibility

Date: 2026-05-27

## Flow selected

The most critical product flow is the agency operator's intake path:

1. capture messy customer context in the workbench,
2. submit it through `POST /run`,
3. normalize it into canonical packet facts,
4. persist the processed trip,
5. show the operator enough detail to continue planning without retyping or guessing.

This is the product spine. If this flow loses high-signal intake fields, later readiness, packet, decision, and follow-up screens are technically alive but operationally weaker.

## What is done

- `SpineRunRequest` accepts direct structured fields for `trip_priorities` and `date_flexibility`.
- The extractor can infer both fields from raw notes and import both from structured envelopes.
- PATCH `/trips/{trip_id}` syncs both fields into `extracted.facts` for operator edits.
- Frontend capture/intake tests cover structured field submission and edit behavior.

## Gap found

`build_envelopes()` was forwarding only part of the direct `POST /run` structured intake payload into the pipeline. It forwarded `follow_up_due_date`, `pace_preference`, `lead_source`, `activity_provenance`, and `date_year_confidence`, but dropped `trip_priorities` and `date_flexibility` even though the request contract allowed them and the extractor knew how to import them.

Real-world effect: an operator could capture priorities and date flexibility as explicit fields, process the trip, and still have those readiness-critical facts missing from the packet unless the same details also appeared in the raw note.

## Fix applied

- Added `trip_priorities` and `date_flexibility` to the `build_envelopes()` structured field bridge in `spine_api/server.py`.
- Extended `tests/test_intake_pipeline_hardening.py` so the end-to-end request-to-packet path now proves both fields survive `SpineRunRequest` → `build_envelopes()` → `run_spine_once()` → `CanonicalPacket.facts`.
- Added `trip_priorities` and `date_flexibility` to the canonical `TripResponse` so the operator-facing contract no longer buries these readiness-critical values only in `extracted.facts`.
- Updated generated frontend API types and `PacketPanel` fallback rendering so Trip Details shows priorities and date flexibility as normal known details.
- Added focused backend and frontend tests for the new contract/display behavior.

## Better next exploration

The next highest-value exploration is browser-level operator QA of the same flow with a real backend and frontend server on a non-3000/3001/3002 port: create a trip from the capture panel, process it, poll the run, land on Trip Details, and confirm priorities/date flexibility are visible in the operator workspace. This session did not run that UI flow because the local frontend test binary is missing from `frontend/node_modules` (`vitest: command not found`) and the user explicitly asked to skip flows dependent on ports 3000/3001/3002.

## Verification

Run:

```bash
uv run pytest tests/test_intake_pipeline_hardening.py tests/test_extraction_fixes.py::TestPrioritiesFlexibilityInPipeline -q
```

Expected: all selected tests pass.

Additional checks run:

```bash
uv run pytest tests/test_intake_pipeline_hardening.py tests/test_extraction_fixes.py::TestPrioritiesFlexibilityInPipeline tests/test_api_trips_post.py::TestTripFollowUpDueDate::test_get_trip_surfaces_priorities_and_date_flexibility_from_extracted_facts -q
```

Result: `5 passed in 40.65s`.

```bash
uv run pytest tests/test_api_trips_post.py::TestTripFollowUpDueDate::test_get_trip_surfaces_priorities_and_date_flexibility_from_extracted_facts tests/test_intake_pipeline_hardening.py -q
```

Result: `2 passed in 19.29s`.

Frontend check attempted:

```bash
npm run test -- --run src/components/workspace/panels/__tests__/PacketPanel.test.tsx
```

Result: blocked by missing local test binary: `sh: vitest: command not found`.
