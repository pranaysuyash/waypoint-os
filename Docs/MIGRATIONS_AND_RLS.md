# Migrations and RLS

Phase 5E enabled FORCE ROW LEVEL SECURITY on all 11 tenant-scoped tables. After this change, all DML (INSERT, UPDATE, DELETE) on these tables is subject to the RLS policy:

```sql
agency_id = current_setting('app.current_agency_id', TRUE)
```

If `app.current_agency_id` is not set, the policy returns no rows for SELECT and blocks INSERT/UPDATE/DELETE (WITH CHECK failure). This is fail-closed behavior.

## Protected tables

```text
trips                          — primary trip data
memberships                    — user-agency associations
workspace_codes                — invite codes
booking_collection_tokens      — UUID tokens linked to trips
trip_routing_states            — trip assignment/handoff history
booking_documents              — travel documents (passports, visas)
document_extractions           — extracted PII from documents
document_extraction_attempts   — per-model extraction attempts
booking_tasks                  — booking execution tasks
booking_confirmations          — booking confirmations with encrypted supplier data
execution_events               — audit event ledger
```

## Exempted tables (have agency_id but no RLS)

```text
audit_logs — admin/audit surface; separate hardening task
```

## DDL is not affected

CREATE TABLE, ALTER TABLE, CREATE INDEX, DROP TABLE, and other DDL statements are not subject to RLS. Alembic migrations that only use DDL work without any special handling.

## DML in migrations: three approved strategies

When a migration needs to INSERT, UPDATE, or DELETE rows on tenant tables, use one of these strategies:

### Strategy 1: Per-tenant loop (preferred for data backfills)

```python
def upgrade() -> None:
    conn = op.get_bind()
    agency_ids = conn.execute(sa.text("SELECT id FROM agencies")).scalars().all()
    for agency_id in agency_ids:
        conn.execute(
            sa.text("SELECT set_config('app.current_agency_id', :id, true)"),
            {"id": str(agency_id)},
        )
        conn.execute(
            sa.text("UPDATE some_table SET ... WHERE agency_id = :id"),
            {"id": str(agency_id)},
        )
```

### Strategy 2: Temporary FORCE RLS disable/enable (for bulk operations)

```python
def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE some_table NO FORCE ROW LEVEL SECURITY"))
    conn.execute(sa.text("ALTER TABLE some_table DISABLE ROW LEVEL SECURITY"))
    # ... DML ...
    conn.execute(sa.text("ALTER TABLE some_table ENABLE ROW LEVEL SECURITY"))
    conn.execute(sa.text("ALTER TABLE some_table FORCE ROW LEVEL SECURITY"))
```

Must re-enable both ENABLE and FORCE in the same migration. Include a comment explaining why the disable is needed.

### Strategy 3: Admin migration role (future, after role split)

When the non-owner runtime role is introduced, Alembic can use a separate `waypoint_admin` role with BYPASSRLS. Not available yet.

## Fail-closed behavior

| Condition | SELECT | INSERT | UPDATE | DELETE |
|-----------|--------|--------|--------|--------|
| `app.current_agency_id` set | Rows for that agency only | Row agency_id must match | Row must be visible + new agency_id must match | Row must be visible |
| `app.current_agency_id` NULL/unset | No rows visible | INSERT fails (WITH CHECK) | No rows visible | No rows visible |

## Testing migrations locally

1. Apply the migration: `alembic upgrade head`
2. Verify RLS posture: `uv run pytest tests/test_rls_live_postgres.py -v`
3. Run full test suite: `uv run pytest tests/ -q`
