# Idempotency fencing and live SQL evidence — N-06 / X-11

**Date:** 2026-09-04\
**Status:** implemented and locally/live-DB verified; deployment promotion remains
separate\
**Owners:** idempotency boundary (`src/agents/idempotency.py`) and its canonical
intake/webhook callers\
**Related records:** `Docs/exploration/MISC_PROBES_N06_N09_D04_F05_2026-09-02.md`,
`Docs/review/EXECUTION_STATUS_2026-09-04.md`

## Claim and failure mode

The idempotency row is the source of truth for whether a logical operation may
execute and which response may be replayed. A status-only terminal update is not
enough: after a TTL or `FAILED` reclaim, the old owner and the new owner are
both `PENDING`. A delayed old owner can therefore overwrite the new owner's
result.

The prior probe recorded the defect as:

```text
reclaim acquired True ...
after stale completion ('COMPLETED', {'owner': 'old-stale'}, ...)
```

That is a Tier 2/S2-style reproduction of X-11's stale-owner failure class.

## Chosen design

Each acquisition receives a cryptographically random opaque `fencing_token`.
The token is persisted on `idempotency_keys` and is replaced on every TTL or
`FAILED` reclaim. `mark_completed` and `mark_failed` perform one SQL
compare-and-set update requiring all of:

```text
key = requested key
status = PENDING
fencing_token = caller's acquisition token
```

The update returns `True` only when one row changed. A missing, stale, or
already-terminal token returns `False` and cannot mutate the row. The in-memory
backend follows the same contract, including constant-time token comparison.

The returned `(acquired, record)` contract is retained; owners carry
`record.fencing_token` into terminal calls. The canonical inbound parser and
traveler-message webhook now do this explicitly. Key-only terminal calls fail
closed rather than silently bypassing the fence.

## Files and schema

- `src/agents/idempotency.py` — token generation, propagation, terminal CAS,
  and in-memory parity.
- `spine_api/models/idempotency.py` — non-null `fencing_token` column and
  JSON/JSONB response payload remains unchanged.
- `alembic/versions/add_idempotency_keys_table.py` — fresh installs include the
  required column.
- `alembic/versions/add_idempotency_fencing_token.py` — introspective upgrade
  for databases created before the column existed; legacy rows receive a
  deterministic one-time token before `NOT NULL` enforcement.
- `spine_api/routers/inbound.py` and
  `spine_api/services/messaging_webhooks.py` — owner-token propagation.
- `tests/test_idempotency_sql_backend.py` — isolated SQL semantics and stale
  owner regression.
- `tests/test_intake_idempotency.py` and `tests/test_agent_runtime_deep.py` —
  callers exercise the fenced in-memory API.

## Verification evidence

### Focused regression suite (Tier 2)

```text
.venv/bin/pytest -q tests/test_idempotency_sql_backend.py \
  tests/test_intake_idempotency.py tests/test_agent_runtime_deep.py
25 passed in 7.21s
```

The regression specifically proves: old token completion returns `False`, the
reclaimed row remains `PENDING` with no stale payload, and the new token then
completes it successfully.

```text
.venv/bin/ruff check [changed idempotency/model/caller/test/migration files]
All checks passed!
```

### Live local PostgreSQL (Tier 3; local test database, not production)

The local `waypoint_os` database was at Alembic revision
`add_platform_role_to_users`. The additive migration was applied:

```text
DATABASE_URL=postgresql+asyncpg://...@localhost:5432/waypoint_os \
  .venv/bin/alembic upgrade head
Running upgrade add_platform_role_to_users -> add_idempotency_fencing_token
```

Schema inspection afterward reported:

```text
response_payload | jsonb | YES
fencing_token   | character varying | NO
```

An isolated, uniquely named probe then used one event loop with eight
independent SQLAlchemy sessions/backends to model concurrent workers:

```text
jsonb_storage_type= _PGJSONB
race_winners= 1 race_losers= 7
stored_status= COMPLETED
stored_payload= {'items': [1, 2, 3], 'nested': {'winner': True}}
token_len= 43
```

A second live probe forced TTL reclaim and attempted the stale/new terminal
interleaving:

```text
old_acquired= True
new_acquired= True
tokens_distinct= True
stale_cas= False
status_after_stale= PENDING
winner_cas= True
```

Both probes deleted their uniquely named rows; final SQL inspection reported
`0` rows matching the probe prefix. No production or hosted database claim is
made.

## Important runtime boundary

The first attempted live probe shared one async engine across multiple
short-lived bridge loops and hung under contention. It was terminated and its
single uniquely named `PENDING` row was deleted. The successful probe used the
repository's correct one-loop async integration shape. The separate
loop-affinity fix in `spine_api/core/database.py` remains required for
synchronous bridge callers and must be verified under the selected deployment
topology.

This work proves durable row-level JSONB storage, single-winner acquisition,
and stale-owner fencing against the local PostgreSQL instance. It does not
prove multi-replica network behavior, provider-side idempotency, external
side-effect reconciliation after an unknown timeout, backup/restore, or
hosted release operation. Those remain explicit release tasks.

## Revisit triggers

- Add a migration test against a database that already has old idempotency
  rows, including concurrent migration/read behavior.
- Add metrics and operator alerting for rejected stale/unfenced terminal writes.
- If idempotency rows become tenant-owned, add an explicit tenant boundary and
  RLS review; this table is currently system-scoped by design.
- Before enabling multi-replica provider actions, prove provider request-key
  semantics and unknown-outcome recovery in a provider sandbox or contract
  environment.
