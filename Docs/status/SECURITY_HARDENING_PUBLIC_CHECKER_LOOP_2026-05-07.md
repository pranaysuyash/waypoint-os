# Security Hardening Loop — Public Checker (2026-05-07)

## Confirmed vulnerabilities fixed
1) Unauthenticated export/delete surfaces
- Fixed by requiring `get_current_agency` + `get_current_user` on:
  - `GET /api/public-checker/{trip_id}`
  - `GET /api/public-checker/{trip_id}/export`
  - `DELETE /api/public-checker/{trip_id}`

2) Unsafe trip-id/path handling in file-backed stores
- Added strict trip-id validator in `spine_api/persistence.py`.
- Enforced validation in file trip CRUD, artifact store, and override store paths.

3) Internal error detail leakage on public checker submit path
- `_run_public_checker_submission` now returns generic HTTP 500 detail.
- Internal stack details remain server-side only.

4) Public events abuse surface (rate + size)
- Added rate limits:
  - run: `12/minute`
  - events: `30/minute`
- Added endpoint payload cap: `PUBLIC_CHECKER_EVENT_MAX_BYTES = 16KiB`.
- Added event store bounds (`MAX_EVENT_BYTES`, `MAX_PROPERTIES`, `MAX_ID_LENGTH`).

5) Oversized artifact archive risk
- Added hard cap: `PublicCheckerArtifactStore.MAX_ARCHIVE_BYTES = 10MiB`.
- Rejects oversized uploads pre-write.

## Tests added/updated
- `tests/test_public_checker_path_safety.py`
- `tests/test_product_b_events.py`
- Existing public-checker e2e coverage re-run in targeted scope.

## Verification evidence
Targeted suite:
- `uv run pytest -q -p no:cacheprovider tests/test_product_b_events.py tests/test_public_checker_path_safety.py tests/test_call_capture_e2e.py -k "public_checker"`
- Result: `12 passed, 16 deselected`

Route/startup invariants:
- `uv run pytest -q -p no:cacheprovider tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py`
- Result: `7 passed`

Focused static analysis:
- `uv run bandit -q -f json spine_api/server.py spine_api/persistence.py spine_api/product_b_events.py scripts/bootstrap_public_checker_agency.py`
- Result: no HIGH/MEDIUM issues; only LOW findings (subprocess advisory + broad except patterns).

## Residual risk verdict
- High confidence in the hardened public-checker scope.
- Not absolute/100% certainty across the whole repository due environment instability during full-suite run:
  - full `pytest` was attempted and produced many unrelated failures under host disk pressure (`Errno 28 No space left on device`).
- This is an operational constraint, not evidence of exploitable regression in the audited surfaces.

## Next loop (recommended)
- Restore stable disk headroom.
- Re-run full suite once environment is stable.
- Optionally add anti-bot challenge (edge-level) for public run/events endpoints.
