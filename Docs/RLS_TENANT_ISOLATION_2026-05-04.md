# PostgreSQL RLS — Tenant Isolation (Task 5)

**Date**: 2026-05-04  
**Status**: Implemented with mock/unit coverage; live PostgreSQL enforcement gap found 2026-05-11

---

## What Was Built

Defense-in-depth tenant isolation using PostgreSQL Row Level Security.

Even if application code forgets a `WHERE agency_id = :id` clause, the database
enforces that queries only return rows belonging to the current request's agency.

### Files

| File | Purpose |
|------|---------|
| `spine_api/core/rls.py` | ContextVar, `set_rls_agency()`, `apply_rls()`, `get_rls_db()` |
| `spine_api/core/auth.py` | Modified: calls `set_rls_agency()` in `get_current_membership` |
| `alembic/versions/add_rls_tenant_isolation.py` | Migration enabling RLS on trips, memberships, workspace_codes |
| `tests/test_rls.py` | 9 tests: ContextVar isolation, SQL parameterization, dep wiring |
| `tests/test_rls_live_postgres.py` | Live PostgreSQL catalog check plus rollback-only visibility probe |

---

## Architecture

### Request lifecycle

```
HTTP request
  → AuthMiddleware (validates JWT)
  → get_current_user (loads User from DB)
  → get_current_membership (loads Membership, calls set_rls_agency(agency_id))
                                 ↑ ContextVar now holds agency_id
  → get_rls_db (sets transaction-local app.current_agency_id via set_config)
                    ↑ all subsequent DB queries in this transaction are RLS-filtered
  → Route handler
```

### Why ContextVar (not thread-locals)

asyncio tasks share a thread. Thread-locals would bleed between concurrent requests.
`ContextVar` is per-asyncio-task — one per FastAPI request handler.

### Why transaction-local config (not plain SET)

Connections are pooled. `SET` (without LOCAL) persists for the connection lifetime
and would bleed into the next request reusing the same connection.

`set_config('app.current_agency_id', :agency_id, true)` is transaction-scoped, equivalent in scope to `SET LOCAL`, and lets SQLAlchemy keep agency IDs as bound parameters. It expires when the transaction ends, so pooled connections are clean for the next request.

### Why policies use `current_setting('app.current_agency_id', TRUE)`

The second argument `TRUE` means: return NULL (not error) if the setting is not defined.
NULL ≠ any agency_id, so RLS returns no rows. Unauthenticated sessions see nothing, not everything.

---

## Using `get_rls_db` in routes

Routes that touch tenant-scoped tables should use `get_rls_db` instead of `get_db`:

```python
from spine_api.core.rls import get_rls_db

@router.get("/trips")
async def list_trips(
    membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    # db already has transaction-local tenant config in effect — RLS filters automatically
    result = await db.execute(select(Trip))
    ...
```

`get_rls_db` depends on `get_db` and reads the ContextVar set by `get_current_membership`.
If no agency_id is set (e.g. public endpoints), it falls through to a plain session.

---

## Migration

```bash
alembic upgrade f1a2b3c4d5e6
```

Revision: `f1a2b3c4d5e6`, depends on `10a6e1336ba4`.

### Tables protected

- `trips` — primary trip data, highest risk of cross-tenant leak
- `memberships` — user-agency associations
- `workspace_codes` — invite codes must not be visible across tenants

### Tables intentionally excluded

- `agencies` — no `agency_id` column (the agency IS the tenant)
- `users` — global user registry, users exist independently of tenants
- `audit_logs` — already query-scoped; RLS adds no value and hurts observability

### Policies per table

```sql
-- SELECT restricted to current agency
CREATE POLICY waypoint_rls_select ON trips
  FOR SELECT
  USING (agency_id = current_setting('app.current_agency_id', TRUE));

-- INSERT/UPDATE/DELETE restricted to current agency (+ WITH CHECK for writes)
CREATE POLICY waypoint_rls_all ON trips
  FOR ALL
  USING (agency_id = current_setting('app.current_agency_id', TRUE))
  WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE));
```

### Superuser bypass

`ENABLE ROW LEVEL SECURITY` without `FORCE` means table owners and superusers can bypass RLS.
Alembic, pg_dump, psql admin sessions all continue to work normally, but the runtime app
role must not own protected tables if RLS is expected to be an active defense-in-depth layer.

### 2026-05-11 live database verification

Live catalog inspection showed the local app role is `waypoint`, the protected tables are
owned by `waypoint`, and `relforcerowsecurity=false`. A rollback-only probe inserted two
temporary agency/trip pairs, set `app.current_agency_id` to agency A, and the runtime role
still read agency B's trip. That proves the current local database configuration installs
policies but does not enforce them against the actual app role.

The new live test records this as a known `xfail` rather than turning insecure owner bypass
into a passing assertion. The long-term fix should be one of:

- use a separate non-owner runtime DB role while migrations/schema ownership stay with an
  owner/admin role
- or force RLS only after every SQL path touching protected tables sets `app.current_agency_id`

`spine_api/core/rls.py` now exposes `inspect_rls_runtime_posture()` and the
`RlsRuntimePosture` / `RlsTablePosture` contracts so tests, startup checks, and operator
diagnostics can share one canonical definition of "RLS is enforced for the runtime role."
This avoids duplicating ad-hoc catalog logic in each future guardrail.

---

## Tests (9 total, all passing)

| Class | Test | What it proves |
|-------|------|----------------|
| TestRlsContextVar | test_set_and_get | ContextVar round-trip |
| TestRlsContextVar | test_default_is_none | Default is None, not stale value |
| TestRlsContextVar | test_context_isolated_between_tasks | Task A/B can't see each other's agency |
| TestApplyRls | test_issues_transaction_local_setting | transaction-local config + correct param name emitted |
| TestApplyRls | test_uses_parameterized_query | Evil agency_id never interpolated into SQL |
| TestGetRlsDb | test_calls_apply_rls_when_agency_set | apply_rls called when ContextVar is set |
| TestGetRlsDb | test_skips_apply_rls_when_no_agency | apply_rls NOT called for unauthenticated path |
| TestAuthWiresRls | test_get_current_membership_sets_rls_agency | auth calls set_rls_agency as side-effect |
| TestAuthWiresRls | test_...does_not_set_rls_on_missing_membership | 403 path does NOT set agency |
| TestRlsRuntimePosture | test_non_owner_role_with_enabled_rls_has_no_risks | non-owner runtime posture is acceptable |
| TestRlsRuntimePosture | test_owner_role_without_force_rls_is_reported_as_bypass_risk | owner bypass is flagged before production reliance |
| TestRlsRuntimePosture | test_missing_or_disabled_tables_are_reported_as_risks | missing/disabled RLS tables are explicit risks |

---

## Security notes

- **SQL injection**: `apply_rls` uses a bound parameter (`:agency_id`), never f-string interpolation. Verified by test.
- **Cross-request bleed**: transaction-local `set_config(..., true)` expires on transaction end. Pooled connections are clean for the next request.
- **Concurrent request isolation**: ContextVar is per-asyncio-task. Verified by `test_context_isolated_between_tasks`.
- **Defense-in-depth**: Application code still carries its own `WHERE agency_id = :id` clauses. RLS is a second line of defense, not a replacement.

---

## Pending

- Replace the single owner/runtime DB role with distinct owner/admin and runtime roles, or
  prepare a complete `FORCE ROW LEVEL SECURITY` rollout.
- Thread RLS context through every SQL trip read/write path before forcing RLS. The direct
  `TripStore` / `SQLTripStore` paths still open their own sessions and depend mainly on
  application-layer `agency_id` filters.
- Wire `inspect_rls_runtime_posture()` into startup once the current `spine_api/server.py`
  router extraction work settles, with fail-fast behavior in production/staging and warning
  behavior in local development.
- Keep `booking_collection_tokens` in the protected table set; the migration already covers it.
