# Override Persistence + State-Contract Parity Fix (2026-05-26)

## What Was Broken (Root Cause)
- Override persistence tests were intermittently polluted by shared on-disk override state when not fully isolated to tmp paths; temporary debug assertions/checks were added during diagnosis and left in place.
- Parity coverage for encrypted private compartments validated helper-level behavior but did not directly assert that both `SQLTripStore.save_trip(...)` and `SQLTripStore.update_trip(...)` persist private fields through the same blob-encrypted storage contract.
- `tests/test_state_contract_parity.py` also had duplicated sentinel assertion execution in one test method (same `_run()` and checks repeated), which added noise and masked intent.

## What Changed
- Removed temporary debug scaffolding from override persistence path:
  - Dropped post-write existence re-check/exception in `OverrideStore.save_override`.
  - Removed debug-only monkeypatch verification + unused imports from `tests/test_override_api.py`.
- Cleaned parity test noise:
  - Removed duplicate sentinel execution block in `TestSQLRawRowSentinel.test_save_path_raw_columns_no_plaintext`.
- Added explicit save/update parity proof for private compartments:
  - New test `test_save_update_use_same_storage_encryption_contract` in `tests/test_state_contract_parity.py` asserts both save and update persist `traveler_bundle`, `internal_bundle`, and `fees` as blob-encrypted payloads (`__encrypted_blob=True`).

## Verification Run
- Command:
  - `./.venv/bin/pytest -q tests/test_override_api.py tests/test_state_contract_parity.py -q`
- Result:
  - `65 passed` (targeted suite green)

## Remaining Risk
- These tests prove storage-contract parity at unit/integration-mock level; they do not fully substitute for a live SQL integration run with real RLS/context and database I/O under concurrent writers.
