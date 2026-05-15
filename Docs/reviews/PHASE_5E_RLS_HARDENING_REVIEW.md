# Phase 5E: Tenant Isolation + RLS Hardening — Review

**Date**: 2026-05-15
**Status**: Closed — 9 FORCE RLS + 2 auth-bootstrap FORCE exemptions. Phase 5F removes exemptions.
**Test suite**: Backend 2233 passed, 0 failed, 0 errors. Frontend 957 passed. TypeScript 0 errors.

---

## What changed

PostgreSQL Row Level Security is now enforced as a defense-in-depth layer across all 11 tenant-scoped tables. 9 tables have FORCE ROW LEVEL SECURITY (even the table owner is subject to RLS policies). 2 tables (memberships, workspace_codes) have ENABLE RLS only — they are queried during login/join before agency context is known, making FORCE RLS a chicken-and-egg blocker. These are tracked in `RLS_FORCE_EXEMPT_TABLES` as the canonical exemption list.

### Tables covered (11 total)

| Table | RLS Enabled | FORCE RLS | Notes |
|---|---|---|---|
| trips | Y | Y | Primary data, highest leak risk |
| booking_collection_tokens | Y | Y | UUID tokens linked to trips |
| trip_routing_states | Y | Y | Assignment and handoff history |
| booking_documents | Y | Y | Uploaded customer documents |
| document_extractions | Y | Y | Extracted document fields |
| document_extraction_attempts | Y | Y | Per-attempt extraction metadata |
| booking_tasks | Y | Y | Booking execution checklist |
| booking_confirmations | Y | Y | Supplier confirmation records |
| execution_events | Y | Y | Durable event ledger |
| memberships | Y | - | Auth exempt (see below) |
| workspace_codes | Y | - | Auth exempt (see below) |

### Runtime posture

- DB user: `waypoint` (non-superuser, no BYPASSRLS)
- Table owner: `waypoint` (same user)
- With FORCE RLS, even the table owner is subject to RLS policies
- Each table has 2 policies: `waypoint_rls_select` (SELECT) and `waypoint_rls_all` (INSERT/UPDATE/DELETE)

---

## Architecture

### How RLS context is set

1. **Authenticated requests**: `get_current_user()` extracts the JWT, stores `agency_id` in a ContextVar. `get_current_membership()` calls `set_config('app.current_agency_id', jwt_agency_id, true)` before querying `memberships`. All downstream queries use `get_rls_db()` which reads the ContextVar and issues transaction-local `set_config`.

2. **Public endpoints (no auth)**: Use `rls_session(agency_id)` context manager which explicitly sets `app.current_agency_id` on a session created for that agency. The URL path includes the `agency_id` (e.g., `/api/public/booking-collection/{agency_id}/{token}`).

3. **Background pipeline**: `SQLTripStore.save_trip()` explicitly calls `set_config('app.current_agency_id', agency_id, true)` before INSERT/UPDATE, within the same session/transaction. The `_for_agency` variants of all TripStore methods use `_rls_session_for_agency(agency_id)`.

### Session boundary audit

| Pattern | Count | Purpose |
|---|---|---|
| `rls_session(agency_id)` / `get_rls_db()` | 84 | RLS-aware sessions with `app.current_agency_id` |
| `async_session_maker()` | 7 | Non-tenant paths (health check, audit bridge, middleware, `get_db` base dep) |

The 7 remaining `async_session_maker()` calls are on non-tenant tables or are the base dependency that `get_rls_db()` wraps.

---

## Auth exemption: memberships and workspace_codes

Two tables intentionally keep ENABLE RLS but skip FORCE RLS. The reason is a chicken-and-egg problem in the login/join flow:

1. **memberships**: The login flow (`_ensure_user_membership`) queries memberships by `user_id` to discover the user's agency. At this point, `app.current_agency_id` is not yet known (the user is authenticating to GET a JWT, not using one).

2. **workspace_codes**: The join flow (`validate_join_code`, `join_with_code`) queries workspace codes by invitation code to discover which agency the code belongs to. No agency context exists at this stage.

With FORCE RLS, these queries return zero rows because the RLS policy requires `agency_id = current_setting('app.current_agency_id', TRUE)`. Without the agency_id, the policy blocks all access.

### Why ENABLE RLS is still valuable here

ENABLE RLS (without FORCE) protects against non-owner database roles. The table owner (`waypoint`) bypasses the policy, but any future role (e.g., a read replica user, a reporting role) would be restricted. This is defense-in-depth: the owner bypass is acceptable because the app controls all queries through the owner connection.

### Single source of truth

`RLS_FORCE_EXEMPT_TABLES` in `spine_api/core/rls.py` is the canonical list. Three consumers read from it:
- `_ensure_rls_no_force_on_auth_tables()` in `server.py` (startup enforcement)
- `RlsRuntimePosture.risks()` (startup posture validation, skips exempt tables)
- `test_all_tenant_tables_have_force_rls()` (asserts ENABLE RLS on exempt, FORCE on all others)

---

## Key files changed

### Backend

| File | Changes |
|---|---|
| `spine_api/core/rls.py` | `RLS_FORCE_EXEMPT_TABLES` constant, `rls_session()` context manager, `get_rls_db()` dependency, `RlsRuntimePosture` with exempt-aware risk reporting |
| `spine_api/core/auth.py` | `get_current_membership()` sets `app.current_agency_id` from JWT before querying memberships |
| `spine_api/core/middleware.py` | Request-scoped RLS context cleanup |
| `spine_api/persistence.py` | `SQLTripStore.save_trip()` explicitly sets RLS context before INSERT; `_rls_session_for_agency()` method for all `_for_agency` variants |
| `spine_api/routers/public_collection.py` | All endpoints use `rls_session(agency_id)` and `_for_agency` TripStore methods |
| `spine_api/services/auth_service.py` | `join_with_code()` calls `apply_rls()` before membership INSERT; `_ensure_user_membership()` handles orphan users |
| `spine_api/server.py` | Startup posture validation, `_ensure_rls_no_force_on_auth_tables()` reads from `RLS_FORCE_EXEMPT_TABLES`, re-added missing collection-link endpoints |
| `alembic/versions/add_rls_phase5e_full_coverage.py` | Migration: adds `agency_id`/`trip_id` to `document_extraction_attempts`, enables RLS + policies on 6 new tables, FORCE RLS on all 11 (startup removes FORCE from 2 auth tables) |

### Tests

| File | Tests | Coverage |
|---|---|---|
| `tests/test_rls.py` | 12 | ContextVar round-trip, task isolation, parameterized queries, auth wiring, runtime posture |
| `tests/test_rls_live_postgres.py` | 7 | Live DB: catalog checks, FORCE RLS, cross-tenant isolation, policy existence |
| `tests/test_booking_collection.py` | 43 | Public collection flow with agency-scoped URLs, RLS-safe queries |
| `tests/test_partial_intake_lifecycle.py` | 7 | Pipeline INSERT under FORCE RLS, partial/full/blocked intake |

---

## Public booking collection: RLS proof

`booking_collection_tokens` has FORCE RLS. The public collection flow must set RLS context before any token lookup. The route shape and RLS wiring:

**Route shape**: `/api/public/booking-collection/{agency_id}/{token}`
- GET (form context), POST (submit data), POST (upload document)
- `agency_id` comes from the URL path, not from auth

**RLS wiring per endpoint**:
- `get_public_collection_form` (line 109): `async with rls_session(agency_id) as db:` → `validate_token(db, token)` → `TripStore.get_trip_for_agency(record.trip_id, agency_id)` → `TripStore.get_pending_booking_data_for_agency(record.trip_id, agency_id)`
- `submit_public_booking_data` (line 148): `async with rls_session(agency_id) as db:` → `validate_token(db, token)` → `TripStore.get_trip_for_agency(...)` → `TripStore.update_trip_for_agency(...)` → `mark_token_used(db, record.id)` (within `rls_session`)
- `upload_public_document` (line 189): `async with rls_session(agency_id) as db:` → `validate_token(db, token)` → `TripStore.get_trip_for_agency(...)` → `rls_session(agency_id)` for `upload_document`

Every database operation on `booking_collection_tokens` or `trips` happens inside `rls_session(agency_id)` which sets `app.current_agency_id` before the query. No bare `async_session_maker()` or `get_db()` usage.

**Test coverage**: 43 tests in `test_booking_collection.py` exercise all three public endpoints with the agency-scoped URL format, including token validation, submission, document upload, and stage-gate enforcement.

## Startup dedup behavior

`_deduplicate_memberships_and_agencies()` and `_ensure_users_have_memberships()` are data repair functions that run on startup. They are gated behind `_should_run_startup_mutations()`:

```python
def _should_run_startup_mutations() -> bool:
    if os.environ.get("SPINE_API_ENABLE_STARTUP_MUTATIONS", "").lower() in ("1", "true", "yes"):
        return True
    env = os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development"))
    return env.strip().lower() not in ("production", "staging")
```

- **Development**: mutations run by default (ENVIRONMENT defaults to "development")
- **Production/Staging**: mutations are SKIPPED unless `SPINE_API_ENABLE_STARTUP_MUTATIONS=1` is explicitly set
- The canonical path for production data repair is migrations or maintenance commands, not app startup

This means production does NOT run dedup on every startup. The reviewer's concern is already addressed by the gate.

## Login/refresh idempotency

`_ensure_user_membership()` (called by both `login()` and `refresh_access_token()`):
1. First queries for primary membership by `user_id`
2. Falls back to any membership by `user_id`
3. Only if both queries return None does it create a new agency + membership

With the current posture (ENABLE RLS, no FORCE on `memberships`), the table owner (`waypoint`) bypasses RLS, so existing memberships are always visible. No duplicate creation occurs for users who already have memberships.

Tests verify: `test_existing_user_with_membership_unchanged` and `test_backfill_idempotent`.

---

## Decisions and tradeoffs

### Decision 1: FORCE RLS on all tables, exempt auth tables

**Options considered**:
- Full FORCE RLS on everything (blocked by auth chicken-and-egg)
- No FORCE RLS, rely on ENABLE RLS only (owner bypass defeats the purpose)
- FORCE RLS everywhere, use superuser connections for auth (adds attack surface)
- FORCE RLS with explicit exemptions for auth tables (chosen)

**Tradeoff**: Two tables have a weaker RLS posture. The app connects as the table owner, so ENABLE RLS alone doesn't restrict the app. But non-owner roles are still protected. The exemption is small, well-documented, and consumed from a single constant.

### Decision 2: Transaction-local `set_config` with `true`

`set_config('app.current_agency_id', value, true)` uses the third parameter `true` (transaction-local). This means the setting resets after `COMMIT`, preventing cross-request bleed on pooled connections. The alternative was session-level (`false`) with explicit cleanup, but transaction-local is simpler and safer — no cleanup needed, no risk of stale values.

### Decision 3: `rls_session(agency_id)` for public endpoints

Public endpoints (booking collection, document upload) have no JWT. The agency_id comes from the URL path. `rls_session(agency_id)` creates a session, sets the context, and yields it. This is the same pattern as `get_rls_db()` but explicitly scoped.

### Decision 4: `_for_agency` TripStore variants

The `SQLTripStore` has dual APIs: `get_trip()` (reads ContextVar) and `get_trip_for_agency(trip_id, agency_id)` (explicit). Public endpoints and background tasks use `_for_agency` variants because the ContextVar may not be set. Authenticated endpoints can use either, but `_for_agency` is preferred for clarity.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| New developer adds endpoint with `Depends(get_db)` instead of `Depends(get_rls_db)` | `scripts/check_rls_coverage.py` checks that all SQLAlchemy models with `agency_id` are in `RLS_TENANT_TABLES` or `RLS_EXCLUDED_AGENCY_TABLES`. Endpoint-level session misuse is not yet machine-enforced — relies on code review and the `get_rls_db` / `rls_session` patterns being well-established. |
| Migration drops FORCE RLS during upgrade/downgrade cycle | Phase 5E migration is idempotent; startup `_validate_rls_runtime_posture_configuration()` warns (dev) or fails (prod) |
| `tripstore_session_maker()` creates separate engine per event loop | Each loop gets its own engine, but `set_config` is per-transaction, so no cross-loop bleed |
| DB restart loses manually-applied FORCE RLS | Alembic migration re-applies on `alembic upgrade head`; startup posture validation catches drift |

---

## Verification checklist

- [x] `alembic upgrade head` — both tables created, RLS enabled, FORCE applied
- [x] `pytest tests/test_rls.py tests/test_rls_live_postgres.py -v` — 19 pass
- [x] `pytest tests/test_booking_collection.py -v` — 43 pass
- [x] `pytest tests/test_partial_intake_lifecycle.py -v` — 7 pass
- [x] Full suite: 2233 passed, 0 failed, 0 errors
- [x] Runtime posture: non-superuser, no BYPASSRLS, 9/11 tables have FORCE RLS
- [x] Cross-tenant isolation: verified via `test_trips_rls_hides_cross_tenant_rows_for_runtime_role`
- [x] Pipeline INSERT: verified via `test_partial_data_saves_incomplete_trip` (save_trip sets RLS context)
- [x] Public collection: verified via 43 booking collection tests with agency-scoped URLs

---

## Open items

1. **Auth-exempt tables hardening (Phase 5F)**: Eliminate FORCE exemptions on `memberships` and `workspace_codes` by adding `users.primary_agency_id`, backfilling from existing memberships, and having login read the user's primary agency before querying the memberships table. After Phase 5F, all 11 tables will have FORCE RLS with zero exemptions.

2. **`test_auth_membership_regression.py` fixture fix**: Previously failed with 4 errors due to `@pytest.fixture()` on an async fixture. Fixed by switching to `@pytest_asyncio.fixture()`. All 4 tests now pass: orphan login backfill, orphan refresh backfill, existing user unchanged, backfill idempotency.

3. **Non-owner application role**: The current architecture uses the table owner (`waypoint`) as the application runtime user. A stronger posture would use a separate non-owner role (e.g., `waypoint_app`) for runtime queries, so FORCE RLS is enforced even without the FORCE flag. This is a future infrastructure change.
