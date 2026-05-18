# Review Branch Scope — review/collection-link-reexpose-encrypted-token

**Branch:** `review/collection-link-reexpose-encrypted-token`
**Date:** 2026-05-18
**Status:** Awaiting review sign-off — do not merge to master until approved

---

## This branch is NOT collection-link only

It contains three distinct areas of change batched together. Reviewer preferred splitting (Option A), but Option B (batch with documentation) was chosen to avoid rebase without explicit approval.

---

## Commit map

### `f30dcc9` — sys.path live-server fix + snapshot format repair
- **Problem:** `PATCH /trips/{id}/booking-data/payment` returned 500 in live uvicorn because bare `intake` package was not on `sys.path` at runtime (pytest adds `src/` via pythonpath config; uvicorn did not).
- **Fix:** Insert `PROJECT_ROOT/src` into `sys.path` at server startup.
- **Snapshot change:** `server_openapi_paths_snapshot.json` migrated from full 7200-line OpenAPI blob to compact `{openapi_path_count, paths[]}`. This was fixing a pre-existing fixture/test mismatch: `test_server_openapi_path_parity.py` already asserted `expected["openapi_path_count"]` — the fixture was stale, not the test. Both snapshot tests pass (`test_server_openapi_path_parity.py`, `test_server_route_parity.py`).
- **Scope:** Backend only. No frontend changes.

### `e105153` — package-lock repair + gitignore fix
- **Problem:** A prior commit had gitignored `package-lock.json` and `package.json` with "we use uv" reasoning (Python/JS tooling confusion). This caused npm to displace packages into `.ignored/` directories on clean install.
- **Fix:** Removed bad gitignore rules. Ran clean `npm install`.
- **Side effect:** vitest bumped from `^3.2.4` → `^4.1.4` by npm during dependency resolution. This is a side effect of the clean install, not an intentional upgrade decision. All 19 DataIntakeZone frontend tests pass under vitest 4.
- **Scope:** `.gitignore`, `frontend/package.json`, `frontend/package-lock.json`.

### `7236f53` — Collection Link Re-expose (Option D)
- **What:** Authenticated agency operators can re-view/copy an active booking collection URL after page reload or in another session, without revoking and regenerating the link.
- **Model:** `plain_token_encrypted` (Fernet-encrypted JSON, nullable) added to `booking_collection_tokens`. `token_hash` unchanged. URL assembled at read time from `PUBLIC_COLLECTION_BASE_URL`.
- **Scope:** alembic migration, model, collection_service, server, api-client.ts, DataIntakeZone.tsx, backend tests (7), frontend tests (4).

### `5bc80ee` — Validator hardening + review fixes
- **What:** Replaced blacklist validation in `_safe_collection_plain_token` with whitelist regex `^[A-Za-z0-9_-]{32,128}$`. Removed unused `decrypt_field` import. Updated design doc status. Added `TestSafeCollectionPlainToken` (16 unit tests).
- **Scope:** `server.py`, `collection_service.py`, `test_booking_collection.py`, design doc.

---

## Test results (branch HEAD `5bc80ee`)

| Suite | Result |
|---|---|
| `test_booking_collection.py` (66 tests) | ✅ 66/66 pass |
| `TestSafeCollectionPlainToken` (16 tests) | ✅ 16/16 pass |
| `test_server_openapi_path_parity.py` | ✅ pass |
| `test_server_route_parity.py` | ✅ pass |
| `DataIntakeZone.test.tsx` (19 tests) | ✅ 19/19 pass |

---

## Merge order (if splitting later)

1. `f30dcc9` (sys.path + snapshot) — no dependencies
2. `e105153` (package repair) — no dependencies on #1
3. `7236f53` + `5bc80ee` (collection-link feature) — depends on nothing above, but logically should follow infra fixes

