# Gemini Issue Review

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
