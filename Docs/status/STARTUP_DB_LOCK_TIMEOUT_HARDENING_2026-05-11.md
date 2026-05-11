# Startup DB Lock Timeout Hardening

Date: 2026-05-11
Scope: FastAPI lifespan startup compatibility checks in `spine_api/server.py`

## Context

During `/insights` runtime verification, backend restart temporarily hung before binding `:8000`.
Read-only Postgres inspection showed startup sessions queued behind a stale `idle in transaction`
session holding an `agencies` relation lock. The blocked startup query was the existing additive
compatibility DDL:

```sql
ALTER TABLE agencies
ADD COLUMN IF NOT EXISTS is_test BOOLEAN DEFAULT false
```

This was not data loss and not a duplicate-route issue. The operational problem was that local API
startup could wait indefinitely behind an unrelated stale transaction.

## Decision

Keep the existing compatibility checks, but bound their lock/statement waits transaction-locally.
This preserves the current additive startup behavior while preventing a stale lock from silently
holding the API offline.

Implemented in `spine_api/server.py`:

- `_get_startup_db_timeout(name, default)` resolves env-overridable timeout strings.
- `_apply_startup_db_timeouts(conn)` applies PostgreSQL transaction-local settings:
  - `lock_timeout`, default `5s`
  - `statement_timeout`, default `20s`
- The helper runs at the start of:
  - `_ensure_agencies_schema_compatibility()`
  - `_ensure_memberships_schema_compatibility()`
  - `_validate_public_checker_agency_configuration()`

Because the settings are applied with `set_config(..., true)`, they are scoped to the current
transaction and do not leak into normal request handling.

## Verification

Targeted startup invariant tests:

```bash
.venv/bin/python -m pytest tests/test_server_startup_invariants.py -q
# 9 passed in 21.66s
```

Combined regression check with the `/insights` analytics hardening tests:

```bash
.venv/bin/python -m pytest tests/test_server_startup_invariants.py tests/test_overview_analytics_hardening.py -q
# 11 passed in 9.46s
```

Runtime verification:

```bash
set -a; source .env; set +a; .venv/bin/python tools/dev_server_manager.py restart --service backend
# backend: healthy

curl -sS -o /dev/null -w 'health %{http_code}\n' http://localhost:8000/health
# health 200

curl -sS -o /dev/null -w 'frontend %{http_code}\n' http://localhost:3000
# frontend 200

curl -sS -o /dev/null -w 'summary %{http_code}\n' -b .runtime/insights_cookies.txt \
  'http://localhost:3000/api/insights/summary?range=30d'
# summary 200

curl -sS -o /dev/null -w 'page %{http_code}\n' -b .runtime/insights_cookies.txt \
  http://localhost:3000/insights
# page 200
```

## Follow-Up

- If production startup compatibility checks remain long-term, move them into a dedicated startup/bootstrap module or Alembic migration preflight so `server.py` continues shrinking as router extraction proceeds.
- If lock waits recur, capture `pg_stat_activity` and terminate only stale, non-writing blockers after confirming ownership and age.
