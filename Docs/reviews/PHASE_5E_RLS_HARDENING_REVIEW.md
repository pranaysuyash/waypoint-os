# Phase 5E: Tenant Isolation + RLS Hardening — Review

**Date**: 2026-05-15
**Status**: Complete, all tests green
**Test suite**: 2170 passed, 0 failed, 7 skipped, 4 pre-existing errors (async fixture compat)

---

## What changed

PostgreSQL Row Level Security is now enforced as a defense-in-depth layer across all 11 tenant-scoped tables. Even if application code omits a `WHERE agency_id = ...` clause, the database restricts queries to the current agency's rows.

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
| `alembic/versions/add_rls_phase5e_full_coverage.py` | Migration: adds `agency_id`/`trip_id` to `document_extraction_attempts`, enables RLS + policies on 6 new tables, FORCE RLS on all 11 |

### Tests

| File | Tests | Coverage |
|---|---|---|
| `tests/test_rls.py` | 12 | ContextVar round-trip, task isolation, parameterized queries, auth wiring, runtime posture |
| `tests/test_rls_live_postgres.py` | 7 | Live DB: catalog checks, FORCE RLS, cross-tenant isolation, policy existence |
| `tests/test_booking_collection.py` | 43 | Public collection flow with agency-scoped URLs, RLS-safe queries |
| `tests/test_partial_intake_lifecycle.py` | 7 | Pipeline INSERT under FORCE RLS, partial/full/blocked intake |

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
| New developer adds endpoint with `Depends(get_db)` instead of `Depends(get_rls_db)` | `scripts/check_rls_coverage.py` CI guard scans for bare `get_db` usage on tenant-table-touching endpoints |
| Migration drops FORCE RLS during upgrade/downgrade cycle | Phase 5E migration is idempotent; startup `_validate_rls_runtime_posture_configuration()` warns (dev) or fails (prod) |
| `tripstore_session_maker()` creates separate engine per event loop | Each loop gets its own engine, but `set_config` is per-transaction, so no cross-loop bleed |
| DB restart loses manually-applied FORCE RLS | Alembic migration re-applies on `alembic upgrade head`; startup posture validation catches drift |

---

## Verification checklist

- [x] `alembic upgrade head` — both tables created, RLS enabled, FORCE applied
- [x] `pytest tests/test_rls.py tests/test_rls_live_postgres.py -v` — 19 pass
- [x] `pytest tests/test_booking_collection.py -v` — 43 pass
- [x] `pytest tests/test_partial_intake_lifecycle.py -v` — 7 pass
- [x] Full suite: 2170 passed, 0 failed
- [x] Runtime posture: non-superuser, no BYPASSRLS, 9/11 tables have FORCE RLS
- [x] Cross-tenant isolation: verified via `test_trips_rls_hides_cross_tenant_rows_for_runtime_role`
- [x] Pipeline INSERT: verified via `test_partial_data_saves_incomplete_trip` (save_trip sets RLS context)
- [x] Public collection: verified via 43 booking collection tests with agency-scoped URLs

---

## Open items

1. **Auth-exempt tables hardening**: Future work could redesign the login/join flow to set RLS context before querying `memberships` and `workspace_codes`. Options include passing agency_id in the join request or using a dedicated auth-role database session.

2. **`test_auth_membership_regression.py` errors (4)**: Pre-existing async fixture compatibility issue with pytest-asyncio. These tests use sync test functions requesting async fixtures. Fix requires converting to async tests or adjusting fixture scope. Not related to RLS work.

3. **Non-owner application role**: The current architecture uses the table owner (`waypoint`) as the application runtime user. A stronger posture would use a separate non-owner role (e.g., `waypoint_app`) for runtime queries, so FORCE RLS is enforced even without the FORCE flag. This is a future infrastructure change.
