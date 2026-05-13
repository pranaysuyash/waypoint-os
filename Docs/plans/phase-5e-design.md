# Phase 5E: Tenant Isolation + RLS Hardening

## Context

Phase 5D closed with a clean baseline except one xfail: `test_trips_rls_hides_cross_tenant_rows_for_runtime_role`. The test marks xfail when the runtime DB role (`waypoint`) owns the protected tables and `FORCE ROW LEVEL SECURITY` is not enabled — PostgreSQL bypasses RLS for table owners.

More critically, six tenant-scoped tables created after the original RLS migration have **no RLS at all**:

```text
booking_documents           — travel documents (passports, visas)
document_extractions        — extracted PII from documents
document_extraction_attempts — per-model extraction attempts
booking_tasks               — booking execution tasks
booking_confirmations       — booking confirmations with encrypted supplier data
execution_events            — audit event ledger
```

These tables all contain tenant-scoped data and hold the most sensitive data in the system. Any route that queries them without an explicit `WHERE agency_id = :id` will return rows from all tenants.

## Trigger

```text
xfail: test_trips_rls_hides_cross_tenant_rows_for_runtime_role
Reason: runtime role 'waypoint' owns tables and FORCE RLS is not enabled
```

## Scope

1. RLS policy coverage for all tenant-scoped tables
2. Add `agency_id` + `trip_id` to `document_extraction_attempts` (schema gap fix)
3. `FORCE ROW LEVEL SECURITY` on all tenant tables (interim hardening)
4. Alembic migration for new policies + schema change
5. Update `RLS_TENANT_TABLES` and startup posture check
6. Live Postgres test hardening (xfail only for unsafe dev config)
7. CI guard: fail if production config allows RLS bypass
8. Migration DML rules documented

## Non-goals

- No new product UI
- No new booking workflow
- No auth redesign
- No customer portal
- No supplier API or payments
- Non-owner runtime role split (future target, not Phase 5E)

---

## 1. Current State

### Tables with RLS enabled (via `add_rls_tenant_isolation.py`)

| Table | RLS | FORCE RLS | In `RLS_TENANT_TABLES` | Policies |
|-------|-----|-----------|------------------------|----------|
| `trips` | Yes | No | Yes | `waypoint_rls_select`, `waypoint_rls_all` |
| `memberships` | Yes | No | Yes | same |
| `workspace_codes` | Yes | No | Yes | same |
| `booking_collection_tokens` | Yes | No | Yes | same |
| `trip_routing_states` | Yes | No | **No** (gap) | same |

### Tables WITHOUT RLS (created after the RLS migration)

| Table | Has `agency_id` | Has `trip_id` | Contains PII |
|-------|-----------------|---------------|-------------|
| `booking_documents` | Yes | Yes | Yes (document metadata, hashes) |
| `document_extractions` | Yes | Yes | Yes (encrypted PII fields) |
| `document_extraction_attempts` | **No** | **No** | Yes (extracted fields, confidence) |
| `booking_tasks` | Yes | Yes | No (task type, status) |
| `booking_confirmations` | Yes | Yes | Yes (encrypted supplier name, confirmation numbers) |
| `execution_events` | Yes | Yes | Low (allowlisted metadata only) |

### Schema gap: `document_extraction_attempts`

`DocumentExtractionAttempt` (tenant.py:337-377) has `extraction_id` FK to `document_extractions` but **no `agency_id` or `trip_id` columns**. A standard `agency_id = current_setting(...)` RLS policy cannot work on this table.

**Resolution**: Add `agency_id` and `trip_id` columns (denormalized from parent), backfill from `document_extractions`, then apply standard RLS policy. See Section 3.

### Intentionally excluded tables

| Table | Has `agency_id` | Reason for exclusion |
|-------|-----------------|---------------------|
| `agencies` | No (is the tenant) | Root tenant table; separate hardening decision. See Section 11. |
| `users` | No | Global user table; users exist across tenants |
| `audit_logs` | **Yes** | Admin/audit surface; query-scoped; separate hardening task. See Section 9. |
| `agent_work_leases` | No (has `trip_id` only) | Operational lease table; scoped by trip_id; low sensitivity |

`audit_logs` has `agency_id` and is tracked in `RLS_EXCLUDED_AGENCY_TABLES` (see Section 9).

### DB role

```text
Connection: postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os
Role: waypoint
Role owns: all tables (created by Alembic running as waypoint)
```

The `waypoint` role owns every table, so without `FORCE RLS`, it bypasses all RLS policies.

### Startup validation

`_validate_rls_runtime_posture_configuration()` runs at startup (server.py:713-753):
- Queries `pg_roles` and `pg_class` for the runtime role's posture
- **Raises** `RuntimeError` in production/staging if RLS is bypassable
- **Warns** in development (continues running)
- Only checks tables in `RLS_TENANT_TABLES` — misses the six unprotected tables

---

## 2. Decision: FORCE RLS as interim hardening

### Phase 5E approach: FORCE ROW LEVEL SECURITY on all tenant tables

```text
Phase 5E (this phase):
  - FORCE ROW LEVEL SECURITY on all tenant-scoped tables
  - No BYPASSRLS granted to waypoint
  - Runtime role (waypoint) owns tables but is subject to RLS via FORCE
  - Startup posture check validates all tables
  - CI guard prevents regressions

Production target (future phase, NOT Phase 5E):
  - Non-owner runtime role (waypoint_app) with SELECT/INSERT/UPDATE/DELETE grants
  - Separate migration/admin role (waypoint_admin) that owns tables
  - FORCE RLS still enabled as defense-in-depth
  - This eliminates table-ownership as an attack vector entirely
```

**Rationale for FORCE RLS as interim**:

1. This is a single-tenant-to-multi-tenant hardening step, not a fresh deployment. Minimizing operational change is important.
2. The existing codebase uses a single `DATABASE_URL` everywhere. Splitting roles requires touching config across dev/staging/production — that is a separate operational phase.
3. FORCE RLS immediately closes the owner-bypass gap. The runtime role cannot bypass RLS even though it owns tables.
4. Table ownership remains operationally risky (a compromised app role that owns tables has DDL power). This is acknowledged and tracked as future work.

**Concrete approach**:

```sql
-- On each tenant-scoped table:
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table> FORCE ROW LEVEL SECURITY;

-- Policies use current_setting('app.current_agency_id', TRUE).
-- NULL → no rows visible. Set correctly → only that agency's rows.
```

### Why not BYPASSRLS for Alembic?

If `waypoint` has `BYPASSRLS`, FORCE RLS is meaningless — `BYPASSRLS` supersedes `FORCE ROW LEVEL SECURITY`. So `waypoint` must NOT have `BYPASSRLS`.

Alembic migrations that are DDL-only (CREATE TABLE, ALTER TABLE, CREATE INDEX, CREATE POLICY) are not subject to RLS — they work without `app.current_agency_id`.

Alembic migrations that include DML on tenant tables (data backfills) must follow the migration DML rules in Section 8.

---

## 3. Schema Fix: `document_extraction_attempts`

### Problem

`DocumentExtractionAttempt` has no `agency_id` or `trip_id`. RLS policy `USING (agency_id = ...)` cannot work.

### Resolution: Add denormalized tenant columns

```sql
-- Migration step 1: Add columns
ALTER TABLE document_extraction_attempts
  ADD COLUMN agency_id VARCHAR(36),
  ADD COLUMN trip_id VARCHAR(36);

-- Migration step 2: Backfill from parent
UPDATE document_extraction_attempts dea
SET agency_id = de.agency_id,
    trip_id = de.trip_id
FROM document_extractions de
WHERE dea.extraction_id = de.id;

-- Migration step 3: Make NOT NULL after backfill
ALTER TABLE document_extraction_attempts
  ALTER COLUMN agency_id SET NOT NULL,
  ALTER COLUMN trip_id SET NOT NULL;

-- Migration step 4: Add FK constraints
ALTER TABLE document_extraction_attempts
  ADD CONSTRAINT fk_dea_agency
    FOREIGN KEY (agency_id) REFERENCES agencies(id) ON DELETE CASCADE,
  ADD CONSTRAINT fk_dea_trip
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE;

-- Migration step 5: Add indexes
CREATE INDEX ix_dea_agency_id ON document_extraction_attempts(agency_id);
CREATE INDEX ix_dea_trip_id ON document_extraction_attempts(trip_id);
```

### Write-path update

`DocumentExtractionAttempt` is created in `extraction_service.py`. The extraction already has `agency_id` and `trip_id` available. Pass them through when creating attempt rows:

```python
# In extraction_service.py, where DocumentExtractionAttempt is created:
attempt = DocumentExtractionAttempt(
    extraction_id=extraction.id,
    agency_id=extraction.agency_id,  # new
    trip_id=extraction.trip_id,      # new
    run_number=...,
    attempt_number=...,
    ...
)
```

### Model update

```python
# In tenant.py, DocumentExtractionAttempt class:
agency_id: Mapped[str] = mapped_column(
    String(36), ForeignKey("agencies.id", ondelete="CASCADE"),
    nullable=False, index=True,
)
trip_id: Mapped[str] = mapped_column(
    String(36), ForeignKey("trips.id", ondelete="CASCADE"),
    nullable=False, index=True,
)
```

---

## 4. Exact RLS Policy Definitions

### Policy SQL for all direct `agency_id` tables

All tenant tables now have a direct `agency_id` column (after the Section 3 fix). The policy shape is:

```sql
-- SELECT policy: restrict reads to current tenant
CREATE POLICY waypoint_rls_select ON <table>
  FOR SELECT
  USING (
    agency_id = current_setting('app.current_agency_id', TRUE)
  );

-- ALL policy: restrict writes + ensure inserted/updated rows belong to current tenant
CREATE POLICY waypoint_rls_all ON <table>
  FOR ALL
  USING (
    agency_id = current_setting('app.current_agency_id', TRUE)
  )
  WITH CHECK (
    agency_id = current_setting('app.current_agency_id', TRUE)
  );
```

### Policy behavior

| Condition | SELECT | INSERT | UPDATE | DELETE |
|-----------|--------|--------|--------|--------|
| `app.current_agency_id` set to valid UUID | Rows for that agency only | Row's `agency_id` must match | Row must be visible + new `agency_id` must match | Row must be visible |
| `app.current_agency_id` NULL or unset | No rows visible | INSERT fails (WITH CHECK) | No rows visible | No rows visible |

`WITH CHECK` failure on INSERT is the correct fail-closed behavior: if `app.current_agency_id` is not set, no tenant data can be written.

### Column type consistency

All `agency_id` columns are `String(36)` / `VARCHAR(36)` storing UUIDs as text. `current_setting('app.current_agency_id', TRUE)` returns text. Plain text comparison works without casting.

### FORCE RLS SQL

```sql
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table> FORCE ROW LEVEL SECURITY;
```

---

## 5. Tables to Protect

### Update `RLS_TENANT_TABLES`

```python
RLS_TENANT_TABLES: tuple[str, ...] = (
    # Original (Phase 5A)
    "trips",
    "memberships",
    "workspace_codes",
    "booking_collection_tokens",
    # Phase 5A migration (had RLS but was missing from RLS_TENANT_TABLES)
    "trip_routing_states",
    # Phase 4-5 tables (currently unprotected)
    "booking_documents",
    "document_extractions",
    "document_extraction_attempts",
    "booking_tasks",
    "booking_confirmations",
    "execution_events",
)
```

### Tables intentionally excluded

| Table | Has `agency_id` | Reason |
|-------|-----------------|--------|
| `agencies` | No | Root tenant table; no `agency_id` column. Future: consider `agencies.id = current_setting(...)`. See Section 11. |
| `users` | No | Global user table; users exist across tenants |
| `audit_logs` | Yes | Tracked in `RLS_EXCLUDED_AGENCY_TABLES`. See Section 9. |
| `agent_work_leases` | No | Has `trip_id` only; no `agency_id`. Scoped by trip ownership. |

---

## 6. Migration Strategy

### New Alembic migration: `add_rls_phase5e_full_coverage.py`

```python
"""
Phase 5E: Full RLS coverage for all tenant-scoped tables.

Adds agency_id + trip_id to document_extraction_attempts (with backfill),
enables RLS + FORCE RLS on all 11 tenant tables, and creates policies.

IMPORTANT: After this migration, all DML on tenant tables is subject to
app.current_agency_id RLS. Future migrations doing tenant-table DML must
follow the rules in MIGRATIONS_AND_RLS.md.
"""

# Step 1: Add agency_id + trip_id to document_extraction_attempts
# Step 2: Backfill from document_extractions
# Step 3: Set NOT NULL + add FK constraints + indexes

# Tables needing RLS enabled for the first time
_NEW_RLS_TABLES = (
    "booking_documents",
    "document_extractions",
    "document_extraction_attempts",
    "booking_tasks",
    "booking_confirmations",
    "execution_events",
)

# Tables needing FORCE RLS (all 11 tenant tables)
_ALL_TENANT_TABLES = (
    "trips",
    "memberships",
    "workspace_codes",
    "booking_collection_tokens",
    "trip_routing_states",
    "booking_documents",
    "document_extractions",
    "document_extraction_attempts",
    "booking_tasks",
    "booking_confirmations",
    "execution_events",
)
```

Migration steps:

1. Add `agency_id` + `trip_id` to `document_extraction_attempts` (nullable first)
2. Backfill from `document_extractions`
3. Set NOT NULL, add FK constraints and indexes
4. For each table in `_NEW_RLS_TABLES`: enable RLS, create `waypoint_rls_select` and `waypoint_rls_all` policies
5. For each table in `_ALL_TENANT_TABLES`: `ALTER TABLE ... FORCE ROW LEVEL SECURITY`
6. Update `RLS_TENANT_TABLES` in code (not in migration — code change)

### Policy naming

Use the same policy names as the original migration:
- `waypoint_rls_select` — SELECT policy
- `waypoint_rls_all` — INSERT/UPDATE/DELETE policy

Both use `current_setting('app.current_agency_id', TRUE)`.

### Migration safety

The migration runs DDL (ALTER TABLE, CREATE POLICY, UPDATE for backfill). The DDL is NOT subject to RLS. The backfill UPDATE is DML and runs BEFORE RLS is enabled on the table, so it is not subject to RLS either.

After FORCE RLS is enabled, any subsequent DML in later migrations must follow Section 8 rules.

---

## 7. Runtime Startup / CI Guard

### Update `_validate_rls_runtime_posture_configuration()`

The startup check already queries `pg_roles` and `pg_class`. After Phase 5E:

1. `RLS_TENANT_TABLES` now includes 11 tables
2. The posture check validates all 11 tables have RLS enabled AND FORCE RLS
3. `risks` property catches missing tables, disabled RLS, and missing FORCE RLS
4. Production/staging: `RuntimeError` on failure
5. Development: warning only

### New CI check: `scripts/check_rls_coverage.py`

Script that:
1. Reads all SQLAlchemy models with `agency_id` columns
2. Reads `RLS_TENANT_TABLES` from `rls.py`
3. Reads `RLS_EXCLUDED_AGENCY_TABLES` from `rls.py`
4. Fails if any model with `agency_id` is in neither `RLS_TENANT_TABLES` nor `RLS_EXCLUDED_AGENCY_TABLES`
5. Fails if any table in `RLS_TENANT_TABLES` lacks RLS in the live DB (when run against a DB)

This prevents future tables from being added without RLS coverage.

---

## 8. Migration DML Rules

### Hard rule: no tenant-table DML without agency context

After FORCE RLS is enabled, any DML on tenant tables in Alembic migrations must use one of three approved strategies:

**Strategy 1: Per-tenant loop** (preferred for data backfills)

```python
# Get all agency IDs
agency_ids = conn.execute(text("SELECT id FROM agencies")).scalars().all()
for agency_id in agency_ids:
    conn.execute(text("SELECT set_config('app.current_agency_id', :id, true)"), {"id": str(agency_id)})
    conn.execute(text("UPDATE ... WHERE agency_id = :id"), {"id": str(agency_id)})
```

**Strategy 2: Temporary FORCE RLS disable/enable** (for bulk operations)

```python
conn.execute(text("ALTER TABLE <table> DISABLE ROW LEVEL SECURITY"))
# ... DML ...
conn.execute(text("ALTER TABLE <table> ENABLE ROW LEVEL SECURITY"))
conn.execute(text("ALTER TABLE <table> FORCE ROW LEVEL SECURITY"))
```

Must re-enable both ENABLE and FORCE in the same migration. Include a comment explaining why.

**Strategy 3: Admin migration role** (future, after role split)

When the non-owner runtime role is introduced, Alembic can use a separate `waypoint_admin` role with `BYPASSRLS`. Not available in Phase 5E.

### Documentation

Create `Docs/MIGRATIONS_AND_RLS.md` with:
1. The three strategies above
2. Which tables are RLS-protected
3. How to test migrations locally
4. The fail-closed behavior (INSERT with no agency_id set = error)

---

## 9. `RLS_EXCLUDED_AGENCY_TABLES`

Tables with `agency_id` that are intentionally excluded from `RLS_TENANT_TABLES`:

```python
RLS_EXCLUDED_AGENCY_TABLES: dict[str, str] = {
    "audit_logs": "admin/audit surface; query-scoped by agency_id in application code; separate hardening task. Low PII risk — action/resource metadata only.",
}
```

### CI guard logic

```python
# In scripts/check_rls_coverage.py:
all_agency_tables = {model.__tablename__ for model in models_with_agency_id}
protected = set(RLS_TENANT_TABLES)
exempted = set(RLS_EXCLUDED_AGENCY_TABLES.keys())

unprotected = all_agency_tables - protected - exempted
if unprotected:
    print(f"ERROR: Tables with agency_id but no RLS: {unprotected}")
    sys.exit(1)
```

### Why `audit_logs` is excluded (for now)

`audit_logs` has `agency_id` but is excluded because:
1. Audit queries span agencies for admin/superadmin views
2. RLS would break cross-agency audit queries that are part of the admin surface
3. The table contains action metadata, not PII
4. Application code already filters by `agency_id`

This is tracked as a separate hardening task. If admin queries are refactored to use a separate connection with `app.current_agency_id` unset, `audit_logs` can be added to `RLS_TENANT_TABLES`.

### Why `agent_work_leases` is not listed

`agent_work_leases` does NOT have `agency_id` (only `trip_id`). It is not flagged by the CI guard because the guard checks for `agency_id` columns. Trip-scoped access control is sufficient for this operational table.

---

## 10. Live Postgres Test Hardening

### Current xfail behavior

`test_trips_rls_hides_cross_tenant_rows_for_runtime_role` dynamically xfails when the runtime role can bypass RLS. After Phase 5E:

- With FORCE RLS enabled and no BYPASSRLS: the test **passes** (cross-tenant rows are hidden)
- With FORCE RLS disabled (unsafe dev config): the test **xfails** with a clear reason

### Updated existing test

```python
@pytest.mark.asyncio
async def test_trips_rls_hides_cross_tenant_rows_for_runtime_role():
    """Cross-tenant rows must not be visible when RLS is properly configured."""
    # ... setup agency_a, agency_b, trip_a, trip_b ...

    if trip_b in visible_ids:
        posture = await inspect_rls_runtime_posture(conn, expected_tables=RLS_TENANT_TABLES)
        if posture.risks:
            pytest.xfail(
                "Live runtime role can bypass tenant RLS: "
                + "; ".join(posture.risks)
            )
        else:
            # RLS is configured correctly but cross-tenant rows are still visible
            # This is a real security issue, not an xfail
            pytest.fail("Cross-tenant row leak despite RLS being properly configured")

    assert visible_ids == [trip_a]
```

### New tests

**`test_all_tenant_tables_have_rls_enabled`**

```python
@pytest.mark.asyncio
async def test_all_tenant_tables_have_rls_enabled():
    """Every table in RLS_TENANT_TABLES must have RLS enabled and forced."""
    test_engine = _make_test_engine()
    try:
        async with test_engine.connect() as conn:
            posture = await inspect_rls_runtime_posture(conn)
        for table in posture.tables:
            assert table.rls_enabled, f"{table.table_name} does not have RLS enabled"
            assert table.force_rls, f"{table.table_name} does not have FORCE RLS"
    finally:
        await test_engine.dispose()
```

**`test_rls_policies_exist_on_all_tenant_tables`**

```python
@pytest.mark.asyncio
async def test_rls_policies_exist_on_all_tenant_tables():
    """Both waypoint_rls_select and waypoint_rls_all must exist on every tenant table."""
    # ... query pg_policies for all RLS_TENANT_TABLES ...
    for table in RLS_TENANT_TABLES:
        assert (table, "waypoint_rls_select") in policies
        assert (table, "waypoint_rls_all") in policies
```

**`test_no_tenant_tables_missing_from_rls_tenant_tables`**

```python
@pytest.mark.asyncio
async def test_no_tenant_tables_missing_from_rls_tenant_tables():
    """Every SQLAlchemy model with agency_id must be in RLS_TENANT_TABLES or RLS_EXCLUDED_AGENCY_TABLES."""
    from spine_api.models.tenant import Base
    from spine_api.core.rls import RLS_TENANT_TABLES, RLS_EXCLUDED_AGENCY_TABLES

    all_tables = set()
    for mapper in Base.registry.mappers:
        table = mapper.local_table
        if table is not None and "agency_id" in table.c:
            all_tables.add(table.name)

    unprotected = all_tables - set(RLS_TENANT_TABLES) - set(RLS_EXCLUDED_AGENCY_TABLES.keys())
    assert not unprotected, f"Tables with agency_id but no RLS: {unprotected}"
```

**`test_cross_tenant_isolation_for_sensitive_tables`**

Cross-tenant visibility test for each of the Phase 4/5 sensitive tables. Tests insert rows for two agencies, sets `app.current_agency_id` to one, and verifies only that agency's rows are visible.

```python
@pytest.mark.asyncio
async def test_cross_tenant_isolation_for_sensitive_tables():
    """
    Cross-tenant rows must be invisible on all Phase 4/5 sensitive tables.
    Tests: booking_documents, document_extractions, document_extraction_attempts,
    booking_tasks, booking_confirmations, execution_events.
    """
    _SENSITIVE_TABLES = (
        "booking_documents",
        "document_extractions",
        "document_extraction_attempts",
        "booking_tasks",
        "booking_confirmations",
        "execution_events",
    )

    probe = uuid4().hex[:12]
    agency_a = f"rls-a-{probe}"
    agency_b = f"rls-b-{probe}"
    trip_a = f"trip-a-{probe}"
    trip_b = f"trip-b-{probe}"
    now = datetime.now(timezone.utc)

    test_engine = _make_test_engine()
    try:
        async with test_engine.connect() as conn:
            posture = await inspect_rls_runtime_posture(conn)
            await conn.rollback()

            if posture.risks:
                pytest.xfail("Runtime role can bypass RLS: " + "; ".join(posture.risks))

            trans = await conn.begin()
            try:
                # Insert agencies and trips (same as trips test)
                # ...

                # For each sensitive table, insert a row for each agency
                # Then set app.current_agency_id = agency_a and verify
                # only agency_a's rows are visible

                for table_name in _SENSITIVE_TABLES:
                    # Insert minimal valid rows for agency_a and agency_b
                    # using table-specific INSERT SQL
                    # ...
                    pass

                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_a},
                )

                for table_name in _SENSITIVE_TABLES:
                    visible = (
                        await conn.execute(
                            text(f"SELECT agency_id FROM {table_name} WHERE trip_id IN (:trip_a, :trip_b)"),
                            {"trip_a": trip_a, "trip_b": trip_b},
                        )
                    ).scalars().all()
                    assert all(v == agency_a for v in visible), (
                        f"{table_name}: cross-tenant row leak: {visible}"
                    )
            finally:
                await trans.rollback()
    finally:
        await test_engine.dispose()
```

Each table needs table-specific INSERT SQL with required columns. The test uses a helper function:

```python
def _insert_sql_for_table(table_name: str, agency_id: str, trip_id: str, row_id: str, now: datetime) -> str:
    """Return INSERT SQL for a minimal valid row in the given table."""
    ...
```

For `document_extraction_attempts`, the test verifies the new `agency_id` column works correctly with RLS — especially important since the column was added and backfilled in this phase.

---

## 11. Future Considerations

### `agencies` root table

`agencies` has no `agency_id` column — the agency IS the tenant. Currently excluded from RLS. If app routes can query all agencies, that may leak tenant metadata.

Future consideration (not Phase 5E):

```sql
-- Potential policy for agencies table:
CREATE POLICY waypoint_rls_agencies ON agencies
  FOR SELECT
  USING (
    id = current_setting('app.current_agency_id', TRUE)
  );
```

This would restrict each session to its own agency. Needs separate review because:
1. Agency creation/signup flows need to INSERT without `app.current_agency_id`
2. Admin/superadmin views need cross-agency visibility
3. Agency slug resolution during auth may need to see multiple agencies

Document this as a separate root-tenant-table decision for a future hardening phase.

### Production target: non-owner runtime role

Phase 5E uses FORCE RLS while the runtime role still owns tables. The production target is:

```text
Runtime role: waypoint_app (does NOT own tables)
  - SELECT, INSERT, UPDATE, DELETE grants on all tenant tables
  - RLS applies automatically (non-owner)
  - FORCE RLS as additional defense-in-depth

Migration/admin role: waypoint_admin (owns tables)
  - CREATE, ALTER, DROP, INDEX on all tables
  - BYPASSRLS for migration DML
  - Used only by Alembic, not by application runtime

Connection strings:
  - DATABASE_URL = waypoint_app (application)
  - DATABASE_URL_ADMIN = waypoint_admin (Alembic)
```

This is NOT part of Phase 5E. It is tracked as a future operational milestone.

---

## 12. Local Dev Handling

### Problem

Local dev uses `docker-compose` with the `waypoint` role owning all tables. After FORCE RLS, the `waypoint` role is subject to RLS policies.

### Solution

Local dev continues to work because `get_rls_db()` sets `app.current_agency_id` before every request. The request context provides the agency_id from the JWT. As long as the JWT is valid and the auth middleware sets the ContextVar, RLS works correctly in local dev.

### Startup warning

The startup check warns in development (does not raise). This is acceptable because:
1. Local dev has a single user/agency
2. RLS is a defense-in-depth layer, not the primary tenant filter
3. Application code already filters by agency_id in every query

### Edge case: no agency_id set

If `app.current_agency_id` is not set (e.g., unauthenticated request), the policy evaluates to `agency_id = NULL`, which returns no rows and blocks INSERT/UPDATE/DELETE (WITH CHECK fails). This is the correct fail-closed behavior.

---

## 13. Files to Modify

### Backend
- `spine_api/core/rls.py` — expand `RLS_TENANT_TABLES` to 11 tables, add `RLS_EXCLUDED_AGENCY_TABLES`
- `spine_api/server.py` — update `_validate_rls_runtime_posture_configuration()` to check all 11 tables including FORCE RLS
- `spine_api/models/tenant.py` — add `agency_id` and `trip_id` columns to `DocumentExtractionAttempt`
- `spine_api/services/extraction_service.py` — pass `agency_id` and `trip_id` when creating `DocumentExtractionAttempt` rows

### Alembic
- `alembic/versions/add_rls_phase5e_full_coverage.py` — add columns + backfill + enable RLS on 6 new tables + FORCE RLS on all 11

### Tests
- `tests/test_rls_live_postgres.py` — add 4 new tests, update existing test for new tables

### Documentation
- `Docs/MIGRATIONS_AND_RLS.md` — migration DML rules and RLS behavior documentation

---

## 14. Files to Create

- `alembic/versions/add_rls_phase5e_full_coverage.py` — migration
- `scripts/check_rls_coverage.py` — CI guard script
- `Docs/MIGRATIONS_AND_RLS.md` — migration DML rules

---

## 15. Test Plan

### `tests/test_rls_live_postgres.py` (~7 tests)

**Existing test updates (2)**:
- `test_rls_catalog_is_enabled_for_tenant_tables` — validates all 11 tables (was 4)
- `test_trips_rls_hides_cross_tenant_rows_for_runtime_role` — xfails only when posture is unsafe, fails if RLS is configured but still leaks

**New tests (5)**:
- `test_all_tenant_tables_have_rls_enabled` — every table in `RLS_TENANT_TABLES` has RLS enabled
- `test_all_tenant_tables_have_force_rls` — every table has FORCE RLS
- `test_rls_policies_exist_on_all_tenant_tables` — `waypoint_rls_select` and `waypoint_rls_all` on every table
- `test_no_tenant_tables_missing_from_rls_tenant_tables` — every SQLAlchemy model with `agency_id` is in `RLS_TENANT_TABLES` or `RLS_EXCLUDED_AGENCY_TABLES`
- `test_cross_tenant_isolation_for_sensitive_tables` — verifies agency_b rows invisible for all 6 Phase 4/5 tables (booking_documents, document_extractions, document_extraction_attempts, booking_tasks, booking_confirmations, execution_events)

### `scripts/check_rls_coverage.py` (CI guard)
- Discovers all models with `agency_id` columns
- Cross-references against `RLS_TENANT_TABLES` and `RLS_EXCLUDED_AGENCY_TABLES`
- Exit 1 if any model is missing from both
- Run in CI as a pre-merge check

---

## 16. Implementation Order

1. Update `RLS_TENANT_TABLES` + add `RLS_EXCLUDED_AGENCY_TABLES` in `rls.py`
2. Add `agency_id` + `trip_id` columns to `DocumentExtractionAttempt` model in `tenant.py`
3. Update `extraction_service.py` to pass `agency_id` and `trip_id` when creating attempts
4. Create Alembic migration `add_rls_phase5e_full_coverage.py`
5. Update `_validate_rls_runtime_posture_configuration()` in `server.py`
6. Update `test_rls_live_postgres.py` with new tests
7. Create `scripts/check_rls_coverage.py`
8. Create `Docs/MIGRATIONS_AND_RLS.md`
9. Run migration against local DB
10. Run full regression suite
11. Verify xfail becomes a pass (or remains xfail if FORCE RLS not yet applied locally)

---

## 17. Verification

1. `alembic upgrade head` — migration applies
2. `uv run pytest tests/test_rls_live_postgres.py -v` — all pass (xfail resolved if DB configured)
3. `uv run pytest tests/ -q` — no regressions
4. `python scripts/check_rls_coverage.py` — exit 0
5. Manual: start server, verify startup log shows "RLS runtime posture validation passed"
6. Manual: without FORCE RLS, verify startup shows warning with all 11 tables listed
7. Manual: verify `document_extraction_attempts` rows have `agency_id` and `trip_id` populated

---

## 18. Rollback

The migration's `downgrade()`:
1. Removes FORCE RLS from all tables
2. Drops policies from the 6 new tables
3. Disables RLS on the 6 new tables
4. Drops indexes, FK constraints, and columns (`agency_id`, `trip_id`) from `document_extraction_attempts`

This returns to the current state.

---

## 19. Summary of review revisions

| # | Review point | Resolution |
|---|-------------|------------|
| 1 | `document_extraction_attempts` has no `agency_id` | Add `agency_id` + `trip_id` columns, backfill from `document_extractions`, update write-path |
| 2 | CI guard conflicts with excluded tables | Add `RLS_EXCLUDED_AGENCY_TABLES` dict; guard checks both protected and exempted |
| 3 | FORCE RLS framed as final posture | Section 2 explicitly marks FORCE RLS as interim; Section 11 documents production target (non-owner role split) |
| 4 | Exact policy SQL | Section 4 provides exact CREATE POLICY statements with USING and WITH CHECK |
| 5 | Migration DML rule | Section 8 defines 3 approved strategies; `MIGRATIONS_AND_RLS.md` documents them |
| 6 | Cross-tenant tests for sensitive tables | Section 10 adds `test_cross_tenant_isolation_for_sensitive_tables` covering all 6 Phase 4/5 tables |
| 7 | `agencies` root table note | Section 11 documents exclusion rationale and future policy consideration |
