# Test-Database Isolation — FND-0366 Root-Cause Architecture

**Date:** 2026-10-24
**Status:** Implemented (this document records the design, decisions, and verification)
**Findings:** FND-0366 (P0, two confirmed incidents: 2026-10-23 and 2026-10-24)
**Owner context:** Ratified by Pranay via the standing implementation mandate
("first principles, for the long term").

---

## 1. Problem — first principles

The catastrophe was never "a bad DELETE existed." The root cause is structural:
**test processes and the developer's working environment share one mutable
Postgres database** (`waypoint_os`, the canonical test agency
`d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`). Any test or script with the power to
run a scoped `DELETE` against that database had the *capability* to destroy
state whose loss breaks the working environment, and the only things between
capability and catastrophe were convention ("test data must be additive") and
— after the first incident — a regex tripwire scoped to pytest.

Capability eventually gets exercised. Twice:

| Incident | Date | Evidence (same signature both times) |
| --- | --- | --- |
| #1 | 2026-10-23 | `trips` 45,944 → 0; `customer_memory_profiles` 4 → 0; auth tables intact (users/agencies/memberships survived) |
| #2 | 2026-10-24 (found at session start, noted on FND-0366 via CLI) | `trips` 47,486 → 0; `customer_memory_profiles` → 0; auth tables intact (users=1,360, agencies=1,358, memberships=1,360) |

Incident #2 happened **outside this session's pytest runs**, which is precisely
the residual the statement tripwire (`tests/_data_safety_guard.py`) cannot see:
it is installed from `conftest.py` and therefore guards only pytest processes.
The deleter remains unidentified (registered on FND-0366, actor `zcode-spine`).

**The invariant to enforce:** no test process should be able to issue a
destructive statement against state whose loss anyone would notice.

## 2. The invariant → architecture

### Layer 1 — Ephemeral per-run databases (the structural fix)

Every pytest session provisions its own database:

```
waypoint_test_run_<unix_epoch>_<rand8>
```

created from a template database and **dropped at session end** (atexit +
best-effort; SIGKILL-orphans are swept by epoch age on the next session).

### Layer 2 — Canonical-URL refusal at engine creation (the guarantee)

`tests/_test_db_provision.py` monkeypatches `sqlalchemy.create_engine` and
`sqlalchemy.ext.asyncio.create_async_engine` (test process only) so that any
engine whose URL targets the canonical database **by name** raises
`CanonicalTestDatabaseViolationError` at construction. Even if future code
bypasses the `DATABASE_URL` constant and hardcodes a canonical URL, it fails
loudly instead of silently reading/writing the working environment.

Combined with Layer 1, the canonical database is unreachable by test processes
*at every layer*: env override (the process's `DATABASE_URL` points at the run
DB before any `spine_api` module imports), constant (both engine creators in
the backend derive from that constant), and engine construction (name-based
refusal).

### Layer 3 — Statement tripwire + self-check (demoted to defense-in-depth)

`tests/_data_safety_guard.py` (FND-0366, 2026-10-23) stays unchanged: it still
aborts canonical-agency `DELETE`/`TRUNCATE` statements and unfiltered
protected-table deletes *inside* pytest, and its `run_selfcheck()` still runs
at every session start so a guard regression is a session error. Its role
changes from primary defense to loud teacher (names the culprit with file:line)
— and it now also protects the template, since the template contains the
canonical agency's seeded rows and the same discipline ("never delete canonical
rows, anywhere") keeps test semantics identical across environments.

## 3. Key design decision — schema-sync template, not a data copy

The template (`waypoint_test_template`) is built from **schema + auth
bootstrap**, never from a data copy of `waypoint_os`:

- `alembic upgrade head` (40 migrations) into a fresh template database
- `scripts/bootstrap_public_checker_agency.py` seeds the canonical agency row
- a `waypoint_test_template_meta` table stores a stamp (hash of
  `alembic/versions/*.py` names/sizes/mtimes + `alembic/env.py`) so the next
  session detects schema drift and rebuilds automatically

**Why not `pg_dump`/`TEMPLATE waypoint_os`?**

1. `CREATE DATABASE ... TEMPLATE waypoint_os` fails while the canonical DB has
   active connections — and the dev server legitimately keeps connections open.
2. A data copy would read the canonical corpus on every template build —
   coupling test infrastructure to the working environment's contents, the
   exact coupling this architecture removes.
3. **CI is the existence proof that the suite does not need the corpus:** CI
   runs the full suite green against a freshly-migrated, bootstrap-seeded,
   otherwise-empty database every push. Local runs on a CI-shaped database are
   not a downgrade — they are the CI parity that
   `scripts/run_backend_tests.sh` has been chasing since 2026-08-30.
4. Zero canonical reads also means the provisioning path can *never* damage the
   canonical database — it never opens a connection to it at all.

**Why conftest-level env override works:** `spine_api/core/env.py`
`load_project_env()` explicitly does not override variables already present in
`os.environ`, and `spine_api/core/database.py` reads `DATABASE_URL` once at
first import — which happens after `conftest.py` (pytest imports conftest
before any test module). Exactly two modules in the backend create engines
(`spine_api/core/database.py`, `spine_api/persistence.py`), and both derive
from that one constant. One override covers everything.

## 4. Privilege matrix

| Actor | Privileges | Used for |
| --- | --- | --- |
| `waypoint` (the `DATABASE_URL` role) | normal DML/DLL on databases it owns; **needs CREATEDB** for run-DB creation | suite connections, run-DB ownership |
| Local admin (trust auth, `postgres`) | superuser | one-time idempotent `ALTER ROLE ... CREATEDB` when the URL role lacks it; provisioning refuses to try anything but a local-socket-equivalent trust fallback |
| CI service role | superuser by definition (`POSTGRES_USER` of the docker image) | same flow, no grant needed |

The provisioner never guesses passwords over TCP. If no admin path exists, it
fails loudly with the exact `ALTER ROLE` statement to run, rather than
silently falling back to shared-DB mode (which would silently recreate the
hazard — forbidden).

## 5. Concurrency

- Template build and template→run copy are serialized with Postgres advisory
  locks (fixed keys), so parallel pytest sessions (e.g. two agent sessions
  running suites simultaneously) never race `CREATE DATABASE ... TEMPLATE`
  (Postgres refuses concurrent copies from one template).
- Run DBs are name-spaced by epoch + random suffix; stale databases
  (> 6 h old, identified by the epoch in the name) are swept at session start.
  The sweep only ever touches the `waypoint_test_run_*` namespace — canonical
  and template names are structurally outside it.

## 6. Opt-out and failure modes

- `WAYPOINT_EPHEMERAL_DB=0` — restore the legacy shared-DB behavior
  (debugging the canonical DB itself). Documented escape hatch, never set in CI.
- Postgres unreachable → provisioning skips with a loud warning and the
  pre-existing `require_postgres` skip machinery works unchanged (preserves the
  no-PG dev loop).
- Template build failure (alembic/bootstrap subprocess error) → session aborts
  with the subprocess output — fail closed, never silently degrade to
  shared-DB mode.

## 7. Real-world consequences (stated plainly)

1. **The developer dashboard starts from zero** (the second wipe already made
   this true) and suites will **never repopulate it again**. The old
   "self-healing corpus" behavior — suites re-seeding the working environment —
   was the bug wearing a friendly face. If a browsable corpus is wanted for
   dev-server use, that is now a deliberate operator action (the additive seed
   scripts still exist for exactly that), not a side effect of running tests.
2. `Docs/KNOWN_TEST_DATA_ACCUMULATION.md` describes a behavior that no longer
   exists; it is preserved as history with a pointer to this document
   (documentation-preservation rule).
3. Parallel sessions stop corrupting each other's data mid-gate — the
   "contested moving tree" suite-run interference loses its data dimension.
4. CI needs **no changes**: the same provisioning flow runs against the CI
   service database (whose role is superuser) and reaches the same end state.

## 8. Verification (evidence)

- Provisioner unit tests: `tests/test_test_db_provision.py` — **10/10 green**
  (template idempotency + stamp-drift rebuild, run-DB roundtrip, namespace
  safety of drop/sweep, URL rewrite, engine-guard refuse/allow/restore).
- **RLS surfacing (initially misread as FND-0369, CLOSED-INVALID-PREMISE):**
  the run DB denied conftest's raw-SQL auth seeding, which first looked like
  "canonical drifted, FORCE RLS absent, isolation inert." Full verification
  overturned that: all tenant tables on canonical are FORCE-protected;
  `memberships`/`payment_mandates`/`workspace_codes` are force=False **by
  design** — app startup strips FORCE from `RLS_FORCE_EXEMPT_TABLES`
  (login/join/payment query before agency context exists). The run-DB denial
  was an ordering artifact: fresh run DBs carry FORCE from alembic until the
  app's exemption pass runs in-session. The shipped fix stands regardless:
  conftest seed blocks set the app's own GUC
  (`set_config('app.current_agency_id', ...)`) so seeding complies with the
  RLS contract at any point in the exemption lifecycle. Probe evidence
  (rolled-back transactions, zero persistence): template no-GUC insert
  RLS-denied; with-GUC passes RLS. Slice after fix: **25/25 green** (smoke,
  trips POST/follow-up, privacy parity, RAG mount, drafts contract,
  provisioner).
- **Canonical housekeeping (executed 2026-10-24, doctrine-applied judgment
  per owner mandate):** canonical was one migration behind head. Backed up
  first (`Docs/backups/waypoint_os_pre_bc_component_identity_2026-10-24.sql.gz`,
  31 tables / 99,149 rows via asyncpg COPY), then applied
  `bc_component_identity` (additive booking-confirmation identity migration —
  read in full before applying: guarded column add, index create-before-drop,
  zero destructive statements). Verified: `alembic_version = bc_component_identity`,
  `uq_bc_component_active` present, zero data change.
- **Teardown under pytest:** atexit is unreliable during pytest interpreter
  shutdown (verified: every clean-exit session leaked its run DB); the drop
  now runs in `pytest_unconfigure` — verified by before/after orphan counts.
  atexit remains as the non-pytest fallback. SIGKILLed sessions (Bash
  timeouts, parallel-session kills) leave orphans by design; the 6-hour epoch
  sweep reaps them.
- Full backend gate + **canonical-unchanged proof** (row counts of every
  canonical table captured before and after the gate must be identical):
  recorded in the session log of 2026-10-24 (`/tmp/full_suite_isolation_gate.log`).

## 9. Residuals and honest limits

- The engine-construction guard is a test-process monkeypatch. A *non-pytest*
  process run by an operator with the canonical URL can still touch canonical
  data — by design that is out of scope for test infrastructure; the backup
  recommendation in §Layer-3 and the dedicated-role option (owner DECIDE)
  address the operator surface.
- The deleter behind both wipes remains unidentified. With this architecture
  the unidentified deleter can no longer reach the working environment from any
  test path; accountability work (tripwire catching it in-pytest, or operator
  action) continues on FND-0366, which stays OPEN.
- Owner DECIDE (listed, not decided): whether to additionally enforce a
  dedicated least-privilege test role with `CONNECT` revoked on the canonical
  database at the protocol level. This requires choosing/storing a separate
  role credential and is deferred as an operator decision; the current design
  already makes canonical unreachable from test processes without it.
