# F-08 Locking Semantics Audit — 2026-09-04

**Status:** Open — audit complete; implementation intentionally deferred until
semantic ownership is assigned for the shared startup/server surfaces.

**Finding:** `spine_api/core/locking.py` silently falls back from PostgreSQL
transaction-scoped advisory locking to a process-local `asyncio.Lock` whenever
the database is absent, uninspectable, or non-PostgreSQL. The fallback cannot
coordinate Uvicorn workers, containers, hosts, or replicas. In addition, no
production mutation route currently invokes the primitive, and the transaction
boundary required by `pg_try_advisory_xact_lock` is not documented or tested.

## Verified evidence

- `spine_api/core/locking.py:56-130` implements PostgreSQL advisory locking
  plus the implicit process-local fallback.
- `spine_api/core/locking.py:25-27` stores fallback locks in a process-local
  registry.
- Repository call-site search found only the locking tests; no production trip
  mutation imports or invokes `trip_advisory_lock`.
- `spine_api/core/startup_assertions.py:46-59,110-124,214-225` rejects missing
  or SQLite configuration in strict environments but does not require the
  actual SQLAlchemy dialect to be PostgreSQL and has no locking assertion.
- `spine_api/server.py:1157-1159,1224-1229` defines strict environments and
  runs startup assertions during lifespan.
- Deployment manifests currently describe one worker, but that is not proof
  that the lock path is active or safe for future multi-worker deployment.

## Read-only verification receipt

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
.venv/bin/pytest -q -p no:cacheprovider \
tests/test_trip_locking.py \
tests/test_startup_assertions.py \
tests/test_server_startup_invariants.py
```

Result: **62 passed in 6.84s**.

This is Tier 2/S1 evidence for the current test contracts only. The locking
tests exercise the in-process fallback; they do not prove distributed
PostgreSQL behavior, boot rejection, or transaction lifetime.

## Doctrine-aligned disposition

**Do not close F-08.** A safe first slice may add an explicit locking-mode
policy and strict-environment startup rejection for unsupported dialects, while
keeping development/test fallback observable as `process_local`. It must not
claim that trip mutations are protected until the lock is wired to a canonical
mutation path and its transaction ownership is proven.

The long-term design is additive and layered:

```text
durable lease row + monotonically increasing fence token
        +
transaction-scoped PostgreSQL advisory lock where needed
        +
conditional fenced writes on every worker mutation
```

Advisory locking is a concurrency guard, not a replacement for durable lease
state, attempt history, fencing, crash reconciliation, operator inspection,
or replay/terminal state.

## Owned follow-up package

1. Define one canonical locking-mode policy (`postgres_advisory` or explicit
   `process_local`).
2. Derive the strict-mode requirement from the actual SQLAlchemy engine
   dialect, not only a URL substring; fail closed on unsupported dialect,
   probe error, or timeout.
3. Document transaction ownership and prohibit commits inside a protected
   advisory-lock scope unless the API explicitly supports that boundary.
4. Add negative tests for MySQL, SQLite, `None`, uninspectable binds, and
   development fallback; add a PostgreSQL two-session contention test.
5. Trace the lock to a real trip mutation and prove fenced writes, rollback,
   release, and timeout behavior.
6. Re-run in a multi-worker/container topology before any launch promotion.

## Ownership boundary

The implementation necessarily touches `spine_api/core/startup_assertions.py`,
`spine_api/server.py`, `spine_api/core/database.py`, deployment manifests, and
shared startup tests that already contain concurrent work. No code or Git
mutation is authorized by this audit record; assign an exact semantic owner and
release snapshot before editing those surfaces.
