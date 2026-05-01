# Async Run Contract Guardrails (2026-04-28)

## Scope

Implemented the remaining top implementation tasks from the random-doc audit after async `/run` migration:

1. Contract drift guard for `POST /run`.
2. Shared polling helper for backend integration tests.
3. Explicit run-events contract checks.
4. Frontend route-map polling path guard.
5. CI guardrail workflow for backend + frontend contract checks.

## Files Updated

- `.github/workflows/run-contract-guard.yml`
- `tests/helpers/run_polling.py`
- `tests/test_run_contract_drift_guard.py`
- `tests/test_spine_api_contract.py`
- `tests/test_run_lifecycle.py`
- `tests/test_partial_intake_lifecycle.py`
- `frontend/src/lib/__tests__/route-map.test.ts`

## What Changed

- Added shared run polling helpers (`wait_for_terminal`, `get_run_status`, `get_run_events`, `get_run_step`) and reused them across integration suites to prevent duplicated polling semantics.
- Added static drift tests to enforce:
  - `POST /run` uses `RunAcceptedResponse`.
  - accepted shape remains `{ run_id, state }`.
  - synchronous payload fields are not reintroduced into accepted responses.
- Extended route-map tests to cover canonical polling paths:
  - `/api/runs/{id}` -> `runs/{id}`
  - `/api/runs/{id}/events` -> `runs/{id}/events`
- Added CI workflow `run-contract-guard` that runs:
  - `uv run pytest -q tests/test_run_contract_drift_guard.py`
  - `npm test -- --run src/lib/__tests__/route-map.test.ts`

## Verification Commands

Backend:

```bash
source Docs/context/agent-start/STEP1_ENV.sh
uv run pytest -q tests/test_run_contract_drift_guard.py tests/test_spine_api_contract.py tests/test_run_lifecycle.py tests/test_partial_intake_lifecycle.py tests/test_run_state_unit.py
```

Frontend:

```bash
cd frontend
npm test -- --run src/lib/__tests__/route-map.test.ts
```

## Notes

- No durable implementation behavior in `spine_api/server.py` was changed in this pass.
- This pass hardens contracts and verification rails to prevent regression back to synchronous `/run` assumptions.
