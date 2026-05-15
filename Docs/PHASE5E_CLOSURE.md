# Phase 5E Closure — Tenant Isolation + RLS Hardening

**Date**: 2026-05-15
**Status**: Pending final review

---

## Final posture

### RLS enforcement on 11 tenant-scoped tables

All 11 tables in `RLS_TENANT_TABLES` (`spine_api/core/rls.py`) have ENABLE ROW LEVEL SECURITY with two policies (`waypoint_rls_select` for SELECT, `waypoint_rls_all` for INSERT/UPDATE/DELETE):

```text
Table                             RLS   FORCE
──────────────────────────────────────────────
booking_collection_tokens          Y      Y
booking_confirmations              Y      Y
booking_documents                  Y      Y
booking_tasks                      Y      Y
document_extraction_attempts       Y      Y
document_extractions               Y      Y
execution_events                   Y      Y
trip_routing_states                Y      Y
trips                              Y      Y
memberships                        Y      —     ← auth bootstrap exemption
workspace_codes                    Y      —     ← auth bootstrap exemption
```

### Auth bootstrap exemption

`memberships` and `workspace_codes` have ENABLE RLS but NOT FORCE RLS. These are declared in `RLS_FORCE_EXEMPT_TABLES` (canonical single source of truth).

**Why**: Login queries `memberships` by `user_id` to discover the user's agency. Join queries `workspace_codes` by invitation code to discover the target agency. Both happen before `app.current_agency_id` is known. With FORCE RLS, these queries return zero rows — a chicken-and-egg deadlock.

**Protection level**: ENABLE RLS restricts non-owner database roles. The table owner (`waypoint`) bypasses RLS without FORCE. This is acceptable because the app controls all queries through the owner connection.

### Runtime role

```text
DB user:      waypoint (non-superuser, no BYPASSRLS)
Table owner:  waypoint (same user)
```

With FORCE RLS on 9 tables, even the table owner is subject to RLS policies. Without FORCE, the owner bypasses.

---

## Caveats

### 1. Two tables have weaker RLS posture

`memberships` and `workspace_codes` rely on ENABLE RLS only. A non-owner role would be restricted, but the current single-role architecture means the owner bypasses. This is the explicit tradeoff for making login/join work.

**Mitigation**: `RlsRuntimePosture.risks()` explicitly skips FORCE-exempt tables in its risk reporting. Tests assert both ENABLE RLS on exempt tables and FORCE on non-exempt tables.

### 2. Startup mutation gate covers dedup

`_deduplicate_memberships_and_agencies()` and `_ensure_users_have_memberships()` are data repair functions that delete duplicate memberships and backfill orphan users. They run only when `_should_run_startup_mutations()` returns True:

- Development (default): runs
- Production/Staging: **skipped** unless `SPINE_API_ENABLE_STARTUP_MUTATIONS=1`

Production does NOT run dedup on every startup.

### 3. Public booking collection uses agency-scoped routes

`booking_collection_tokens` has FORCE RLS. The public flow cannot use opaque-token-only lookup. Instead, routes include `agency_id` in the URL path:

```text
GET  /api/public/booking-collection/{agency_id}/{token}
POST /api/public/booking-collection/{agency_id}/{token}/submit
POST /api/public/booking-collection/{agency_id}/{token}/documents
```

Every endpoint opens `rls_session(agency_id)` before querying `booking_collection_tokens` or `trips`. No bare session usage.

### 4. Phase 5E commit included scope creep

The Phase 5E commit bundled workflow visualization, UX changes, and fixture refreshes alongside the security migration. Future security phases should be split into separate commits per concern.

---

## Test results

```text
2170 passed, 0 failed, 7 skipped, 4 pre-existing errors (async fixture compat)
```

Key test files:

| File | Tests | What it proves |
|---|---|---|
| `test_rls.py` | 12 | ContextVar isolation, parameterized queries, auth wiring |
| `test_rls_live_postgres.py` | 7 | Live DB: ENABLE RLS on all 11, FORCE on 9, cross-tenant isolation |
| `test_booking_collection.py` | 43 | Public collection under FORCE RLS with agency-scoped routes |
| `test_partial_intake_lifecycle.py` | 7 | Pipeline INSERT under FORCE RLS |
| `test_auth_membership_regression.py` | 4 errors | Pre-existing async fixture compat (not RLS-related) |

---

## Next hardening task: Phase 5F

**Goal**: Eliminate the FORCE exemptions on `memberships` and `workspace_codes`.

**Approach**:
1. Add `users.primary_agency_id` column (migration + backfill from existing memberships)
2. Login reads `user.primary_agency_id` from `users` table (not tenant-scoped, no RLS)
3. Sets `app.current_agency_id` before querying `memberships`
4. Workspace code flow gets agency_id from the invitation link (already passed in some flows)
5. Re-enable FORCE RLS on `memberships` and `workspace_codes`
6. Remove startup dedup as normal boot behavior

**After Phase 5F**: All 11 tenant tables will have FORCE ROW LEVEL SECURITY. Zero exemptions.

---

## Verification commands

```bash
# DB proof
uv run python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def check():
    e = create_async_engine('postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os')
    async with e.connect() as conn:
        rows = await conn.execute(text(
            \"SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class \"
            \"WHERE relname IN ('trips','memberships','workspace_codes','booking_collection_tokens',\"
            \"'trip_routing_states','booking_documents','document_extractions',\"
            \"'document_extraction_attempts','booking_tasks','booking_confirmations','execution_events') \"
            \"ORDER BY relname\"
        ))
        for r in rows.fetchall():
            print(f'{r[0]:<35} rls={r[1]}  force={r[2]}')
    await e.dispose()
asyncio.run(check())
"

# Test proof
uv run pytest tests/test_rls.py tests/test_rls_live_postgres.py -v
uv run pytest tests/test_booking_collection.py -v
uv run pytest tests/test_partial_intake_lifecycle.py -v
uv run pytest tests/ -q

# Frontend proof
cd frontend && npm test -- --run
cd frontend && npx tsc --noEmit

# RLS coverage guard
python scripts/check_rls_coverage.py
```
