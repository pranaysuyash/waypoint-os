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

## Better next exploration

The next highest-value exploration is browser-level operator QA of the same flow with a real backend and frontend server: create a trip from the capture panel, process it, poll the run, land on Trip Details, and confirm priorities/date flexibility are visible in the operator workspace. That should be done after the current parallel frontend changes settle, because `IntakePanel.tsx` and related frontend generated types are currently modified by other work in the tree.

## Verification

Run:

```bash
uv run pytest tests/test_intake_pipeline_hardening.py tests/test_extraction_fixes.py::TestPrioritiesFlexibilityInPipeline -q
```

Expected: all selected tests pass.
