# Issue Review

Date: 2026-04-14 IST

## Issue Identified
Running full test discovery with `pytest -q` fails during notebook test collection.

### Error Summary
- `TypeError: exec() arg 1 must be a string, bytes or code object`
- Affected files:
  - `notebooks/test_02_comprehensive.py`
  - `notebooks/test_scenarios_realworld.py`

### Observed Cause
Notebook loader executes `cell['source']` directly, but in parsed notebook JSON this value appears as a list of lines rather than a single string.

### Evidence
- Full run: `pytest -q` -> collection errors (2 errors)
- Core suite: `pytest -q tests` -> `41 passed`

## Impact Assessment
- Main code test suite under `tests/` is healthy.
- Notebook-linked tests currently block full-repo `pytest` collection.
- This issue predates current context-ingestion changes and is unrelated to docs/tools updates.

## Suggested Fix Direction
- In both notebook test loaders, normalize source before exec:
  - if list -> `"".join(cell['source'])`
  - else use string directly
- Re-run:
  - `pytest -q` (full)
  - targeted notebook tests for regression confirmation

## Status
- Marked for review.
- Not auto-fixed in this step to keep current scope limited to context ingestion.

## Update: 2026-04-14 (Execution Pass)

### Notebook Loader Normalization
- Implemented in:
  - `notebooks/test_02_comprehensive.py`
  - `notebooks/test_scenarios_realworld.py`
- Fix applied:
  - `cell["source"]` list values are joined before `exec(...)`
- Result:
  - prior `TypeError: exec() arg 1 must be a string...` is resolved.

## Additional Issue Identified (2026-04-14)
### Decision Policy Documentation Drift
- `specs/decision_policy.md` appears version-lagged vs current runtime decision behavior and status set in `src/intake/decision.py`.

### Risk
- Team may implement against stale policy assumptions.
- Increases chance of wrong gating behavior in follow-up vs proceed transitions.

### Recommended Review
- Align doc version and decision-state definitions with actual runtime contract.
- Add a small policy conformance test to detect future drift.

### Status
- Marked for review.

### Update
- Addressed:
  - `specs/decision_policy.md` aligned to v0.2 runtime behavior.
  - Added policy guard test: `tests/test_decision_policy_conformance.py`.
- Verification:
  - `uv run python -m pytest tests/test_decision_policy_conformance.py -q` -> `5 passed`

## New Issue Identified (2026-04-14)
### Legacy Notebook Scenario Contract Drift

#### Symptom
Notebook scenario scripts execute but fail many assertions against v0.2 runtime API/behavior.

#### Evidence
- `PYTHONPATH=src uv run python notebooks/test_02_comprehensive.py`
  - pass/fail summary indicates many expectations tied to deprecated interfaces.
- `PYTHONPATH=src uv run python notebooks/test_scenarios_realworld.py`
  - partial passes with several legacy expectation failures and deprecated parameter usage.

#### Root Cause
- Scripts were written against older NB02 contracts (older field names, signatures like `current_stage`/`mvb_config`, legacy alias expectations, and older decision-state assumptions).
- Runtime now follows v0.2 canonical field model and stricter decision contract.

#### Impact
- Does not block core release test suite (`uv run python -m pytest tests -q` -> `46 passed`).
- Creates noise/failure in notebook exploratory validation scripts.

#### Recommended Next Step
- Explicitly choose one path:
  1. **Migrate** notebook scripts to v0.2 contracts and keep them as non-core checks.
  2. **Archive/label legacy** and remove them from expected validation flow.

#### Status
- Marked for review.

## New Issue Identified (2026-04-14)
### E2E Expected-Decision Drift (existing_plus_new = 3/4)

#### Symptom
End-to-end scenario validation reports `Expected-decision checks: 3/4 passed`.

#### Evidence
- Command:
  - `python tools/e2e_scenario_runner.py --set existing_plus_new --md-out Docs/reports/e2e_existing_plus_new_2026-04-14.md --json-out Docs/reports/e2e_existing_plus_new_2026-04-14.json`
- Report:
  - `Docs/reports/e2e_existing_plus_new_2026-04-14.md`
- Root mismatch found in expectation set:
  - `S03 Dreamer Luxury vs Budget` expected a legacy decision state `BRANCH_OPTIONS` no longer used by runtime v0.2.

#### Likely Cause
- E2E expectation map had a stale expected decision from pre-v0.2 behavior.

#### Impact
- Core unit/conformance suite remains green (`24 passed` for targeted tests).
- E2E expectation credibility is reduced until fixture-vs-policy alignment is clarified.

#### Recommended Next Step
1. Inspect expected-decision map in `tools/e2e_scenario_runner.py`.
2. Replace legacy state expectation with current contract-aligned expected state.

#### Status
- Resolved.

#### Resolution Applied
- Updated `tools/e2e_scenario_runner.py`:
  - `S03` expected decision: `BRANCH_OPTIONS` -> `ASK_FOLLOWUP`
- Re-ran E2E:
  - `python tools/e2e_scenario_runner.py --set existing_plus_new --md-out Docs/reports/e2e_existing_plus_new_2026-04-14.md --json-out Docs/reports/e2e_existing_plus_new_2026-04-14.json`
  - Result: `Expected-decision checks: 4/4 passed`

## New Issue Identified (2026-04-14)
### Visa/VOA/Document Requirement Contract is Fragmented (Not Canonical)

#### Context
Discussion review requested to verify whether visa/document-requirement thinking already exists in repo and whether it is implementation-ready.

Environment date checked before documenting:
- `2026-04-14 10:35:53 IST`

#### Evidence (Current State)
- Code has partial handling:
  - `src/intake/extractors.py` -> `_extract_passport_visa(...)` (keyword/regex-level extraction).
  - `src/intake/decision.py` -> booking-stage checks using `passport_status` / `visa_status`.
- Docs include multiple references across PM/UX/scenario files, but not one canonical runtime contract.

#### Problem
- Logic is distributed across docs and implementation with no single deterministic visa/doc policy spec.
- No strict parser contract yet for:
  - `visa_on_arrival` vs `e-visa` vs embassy visa,
  - transit visa semantics,
  - processing-time-to-travel risk calculations.
- Critical traveler attributes for visa decisions are not enforced as a complete required set.
- OCR provenance (line/box source evidence) is not yet represented as a strict decision input for visa/doc checks.

#### Impact
- Increased risk of inconsistent handling across scenarios.
- Potential false proceed or delayed escalation for high-risk visa/document cases.
- Harder to validate behavior with deterministic test coverage.

#### Recommended Fix Direction
1. Add canonical visa/doc requirement contract (single source of truth doc + schema hooks).
2. Implement deterministic parser-first module for visa/doc constraints.
3. Extend schema + confidence gate to enforce:
   - critical-field completeness,
   - confidence thresholds,
   - evidence spans/provenance for OCR-derived claims.
4. Add scenario tests specifically for:
   - visa-on-arrival eligibility,
   - transit visa requirements,
   - processing-time risk near travel dates.

#### Status
- Marked for review.
- Implementation pending.

## New Issue Identified (2026-04-14)
### Full `pytest` collection fails with notebook import path error (`ModuleNotFoundError: intake`)

#### Symptom
Running `pytest -q` from project root fails during collection of notebook-linked tests.

#### Evidence
- Command:
  - `pytest -q`
- Error:
  - `ModuleNotFoundError: No module named 'intake'`
- Affected files:
  - `notebooks/test_02_comprehensive.py`
  - `notebooks/test_scenarios_realworld.py`

#### Likely Cause
Notebook test loader currently relies on relative path insertion that is brittle under root-level test collection context.

#### Impact
- Full test discovery fails even when non-notebook test modules may be healthy.
- Slows CI confidence if full `pytest` is expected as standard.

#### Recommended Next Step
1. Normalize import path strategy for notebook tests (explicit, root-safe resolution).
2. Re-run full suite:
   - `pytest -q`
3. Keep notebook tests clearly marked as core vs exploratory if needed.

#### Status
- Marked for review.
- Not fixed in this documentation pass.
