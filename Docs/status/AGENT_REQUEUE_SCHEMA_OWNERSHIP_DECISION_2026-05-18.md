# Agent Requeue Schema Ownership Decision

**Date:** 2026-05-18  
**Status:** Option B implemented — `alembic/versions/add_agent_requeue_jobs.py` (commit `86331ff`)  
**Scope:** `agent_requeue_jobs` table — schema ownership, migration posture, RLS

---

## 1. Current Behaviour

`spine_api/services/agent_requeue_jobs.py` — `RequeueJobStore.ensure_schema()` —
creates the table and its three indexes at runtime using `CREATE TABLE IF NOT EXISTS`
raw SQL. Called from `spine_api/services/agent_runtime_factory.py` during server
startup (line 211).

There is:
- **No Alembic migration** for `agent_requeue_jobs`
- **No SQLAlchemy ORM model** in `spine_api/models/tenant.py`
- **No RLS** (`relrowsecurity=f`, `relforcerowsecurity=f` confirmed in live DB)

The table exists in the live `waypoint_os` database because it was self-bootstrapped
when the server started.

---

## 2. Comparison: `agent_work_leases` (the precedent)

`agent_work_leases` is the direct sibling — same architectural category, same
self-bootstrap pattern inside `agent_work_coordinator.py`. **But it also has an
Alembic migration** (`alembic/versions/add_agent_work_leases.py`). That migration
is the `down_revision` anchor for the entire RLS chain
(`add_rls_tenant_isolation.py` → `add_rls_phase5e_full_coverage.py`).

`agent_work_leases` has no RLS either, for the same reason as `agent_requeue_jobs`
(no `agency_id` column; system-internal table).

`agent_requeue_jobs` was added after the migration chain was written, so it got the
self-bootstrap but the migration was never added. This is the gap.

---

## 3. What Tables Have RLS — And Why These Two Don't

**RLS tenant tables** (11 total, defined in `spine_api/core/rls.py`):

```
trips, memberships, workspace_codes, booking_collection_tokens,
trip_routing_states, booking_documents, document_extractions,
document_extraction_attempts, booking_tasks, booking_confirmations,
execution_events
```

These have `agency_id` columns and are in the user request path. RLS enforces
per-agency isolation at the DB level.

**`agent_requeue_jobs` and `agent_work_leases`** are system coordination tables:

- Written by system processes (recovery agent, worker), not per-request user
  context
- No `agency_id` column — they track work across the system, keyed on `trip_id`
  and `idempotency_key`
- RLS as implemented requires `agency_id` to be present — it would not apply
  without a schema change
- Operationally correct: a recovery worker leasing a job must see it regardless
  of which agency the underlying trip belongs to

**Conclusion on RLS:** Not applicable to these tables in their current form.
Adding `agency_id` and RLS would change semantics (system queue → per-tenant
queue), which is not the intent.

---

## 4. Risks of Current State

| Risk | Severity | Notes |
|------|----------|-------|
| `alembic upgrade head` does NOT create `agent_requeue_jobs` | **Medium** | Fresh deployment via Alembic leaves requeue non-functional until first server start |
| No `down_revision` anchor — can't cleanly migrate away from it | Low | No rollback path if schema needs to change |
| Schema drift between deployments | Medium | If two servers start with different ensure_schema() versions, schema may diverge |
| Not visible to DB introspection / `alembic check` | Low | Doesn't appear in migration history |
| Trip data exposure (no RLS) | Low–Medium | `trip_id` is stored; no agency scoping. Only accessible to application process owner (`waypoint` role), not to row-level queries from other tenants. Currently acceptable, revisit if access model broadens. |

---

## 5. Alternatives

### Option A — Keep self-bootstrap only (status quo)

**What changes:** Nothing.

**Pros:**
- Zero migration work
- Operationally isolated — doesn't affect the Alembic chain

**Cons:**
- Deployment gap: `alembic upgrade head` alone is insufficient; server must be
  started at least once to create the table
- Inconsistent with `agent_work_leases` precedent
- Schema changes require in-code version branching, not migrations

**Suitable if:** Table is truly experimental/ephemeral and expected to be replaced
before scaling to multi-node deployments.

---

### Option B — Add Alembic migration + keep self-bootstrap (recommended)

Mirror the `agent_work_leases` pattern exactly:

1. Add `alembic/versions/add_agent_requeue_jobs.py` that creates the table and
   indexes idempotently (`IF NOT EXISTS` or inspector check).
2. Chain `down_revision` to the last migration in the current head
   (`add_rls_phase5e_full_coverage`).
3. Keep `ensure_schema()` in place as a runtime safety net — belt and suspenders.
4. No ORM model required (raw SQL queries are appropriate for this infrastructure
   table).
5. No RLS added (not applicable; see §3).

**Pros:**
- `alembic upgrade head` creates the table on fresh deployments
- Consistent with the established `agent_work_leases` precedent
- Minimal code change — migration + keep existing service intact
- Reversible with a `downgrade()` function

**Cons:**
- Small migration work (~30 lines)
- Adds one migration file to the chain

---

### Option C — Full SQLAlchemy model + RLS + Alembic

Add a `RequeueJob` ORM model to `tenant.py`, add `agency_id` column, add RLS
policy, add Alembic migration.

**Pros:**
- Full DB governance parity with tenant tables
- `agency_id` enables per-tenant audit isolation

**Cons:**
- Requires semantic change: the table becomes per-tenant, which changes worker
  behaviour (a recovery worker would need agency context to lease jobs)
- More migration work
- Breaks the current `RequeueWorker._lookup_trip` pattern which scans across trips
  from all agencies

**Suitable if:** The recovery system is redesigned to be per-agency rather than
system-wide. Not the right move now.

---

## 6. Recommended Decision

**Option B.** Add an Alembic migration that creates `agent_requeue_jobs`
idempotently. Keep `ensure_schema()` as a runtime guard. No RLS. No ORM model.

**Rationale:**
- `agent_work_leases` is the direct precedent; parity removes a source of
  deployment confusion
- The deployment gap (Alembic doesn't create the table) is a real risk as soon
  as this project has multiple deployment environments or a CI pipeline that runs
  `alembic upgrade head` independently
- The work is ~30 lines. The risk of NOT doing it grows with every deployment

---

## 7. Migration Plan (Option B)

When approved, the migration looks like this:

```python
# alembic/versions/add_agent_requeue_jobs.py
revision = "add_agent_requeue_jobs"
down_revision = "add_rls_phase5e_full_coverage"

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "agent_requeue_jobs" not in inspector.get_table_names():
        op.create_table(
            "agent_requeue_jobs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("idempotency_key", sa.String(500), nullable=False),
            sa.Column("trip_id", sa.String(255), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("mode", sa.String(40), nullable=False, server_default="sql_queue"),
            sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
            sa.Column("leased_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("locked_by", sa.String(120), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
        )
        op.create_index("ix_agent_requeue_jobs_status",
                        "agent_requeue_jobs", ["status"])
        op.create_index("ix_agent_requeue_jobs_trip_id",
                        "agent_requeue_jobs", ["trip_id"])
        op.create_unique_index("uq_agent_requeue_jobs_idempotency",
                               "agent_requeue_jobs", ["idempotency_key"])

def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "agent_requeue_jobs" in inspector.get_table_names():
        op.drop_table("agent_requeue_jobs")
```

`ensure_schema()` in the service stays unchanged — it's the runtime guard.

---

## 8. Tests Needed (if Option B implemented)

- Verify `alembic upgrade head` on a clean DB creates the table
- Verify `alembic downgrade` removes it
- Existing `tests/test_agent_requeue_jobs.py` covers all service behaviour
  (schema idempotency, enqueue, lease, complete, fail, snapshot, worker)
- No new service tests needed — the migration adds no new behaviour

---

## 9. What Not to Change

- `ensure_schema()` in `agent_requeue_jobs.py` — keep as runtime guard
- `ensure_schema()` in `agent_work_coordinator.py` — same pattern, leave alone
- `agent_work_leases` — already has a migration, no change needed
- RLS posture for either agent table — not applicable; do not add `agency_id`
  without a deeper worker redesign
- `tests/test_agent_requeue_jobs.py` — tests pass against live PostgreSQL; no
  changes unless the schema definition changes

---

## 10. Follow-up Questions (out of scope here)

1. Does the deployment runbook require `alembic upgrade head` before starting
   the server? If yes, the deployment gap is actively dangerous now.
2. Should `agent_work_leases` be audited for schema drift between its migration
   and its `ensure_schema()` definition? They appear aligned but haven't been
   formally verified.
3. Longer term: if the recovery agent becomes per-agency, add `agency_id` to
   `agent_requeue_jobs` and revisit RLS at that point.
