# E3 — Multi-Worker Idempotency Backend: When Does In-Process Stop Being Honest, and What Is the SQL Adoption Path?

**Date:** 2026-09-02 (explored; live-DB probe re-verified 2026-09-04)
**Type:** EXPLORE (read-only research; no code changed)
**Anchors:** register F-28 (intake-boundary idempotency), PT-08 (`Docs/review/SPINE_AUDIT_NEW_FINDINGS_2026-09-02.md:39`), `Docs/review/FINDINGS_REGISTER_2026-08-31.md:180` (PT-08 = PARTIAL), prior probe `Docs/exploration/MISC_PROBES_N06_N09_D04_F05_2026-09-02.md`
**Key files:** `src/agents/idempotency.py`, `spine_api/models/idempotency.py`, `spine_api/routers/inbound.py`, `spine_api/services/messaging_webhooks.py`, `alembic/versions/add_idempotency_keys_table.py`, `tests/test_idempotency_sql_backend.py`, `tests/test_intake_idempotency.py`

---

## 1. The Question

Intake-boundary dedup shipped this wave on `IdempotencyRegistry.get_instance()` — an in-process, `threading.Lock`-guarded singleton. `src/agents/idempotency.py` also carries a fully built `SqlIdempotencyBackend` behind a pluggable seam. When does the in-process backend stop being an honest duplicate guarantee, and what is the smallest correct path to the SQL backend?

**Headline answer (verified):** the switch already exists and is already flipped in every deploy surface — `SPINE_API_IDEMPOTENCY_BACKEND=sql` is pinned in `docker-compose.yml:31`, `fly.toml:31`, and `render.yaml`. The backend is **not orphaned**. What remains is (a) one stale comment claiming "in-process backend" at both call sites, (b) no startup assertion enforcing the backend↔worker-count contract, (c) unbounded key-table growth with no janitor, and (d) a single-process honesty gap that no backend fixes: registry state is lost on process restart, so a client retry after a crash re-executes a completed intake.

---

## 2. Current State

### 2.1 Registry API surface (`src/agents/idempotency.py`) — verified

| Member | Semantics |
| --- | --- |
| `IdempotencyStatus` | `PENDING` / `COMPLETED` / `FAILED` |
| `IdempotencyRecord` | key, trip_id, action_name, request_hash, status, `fencing_token` (fresh per acquisition, `secrets.token_urlsafe(32)`), created_at, completed_at, response_payload, error_message, ttl_seconds (default 86400) |
| `generate_key(trip_id, action, payload)` (static) | deterministic: `idem:{trip_id}:{action}:{sha256(json(payload, sort_keys))[:16]}` — dedup is per-payload by construction |
| `try_acquire(key, trip_id, action_name, payload, ttl_seconds=86400)` | `(True, record)` = execute; `(False, record)` = replay (COMPLETED) or reject in-flight (PENDING); FAILED falls through to re-acquire (retry allowed) |
| `mark_completed(key, payload, *, fencing_token)` / `mark_failed(key, err, *, fencing_token)` | fenced terminal CAS; returns `False` when the caller's generation was reclaimed; missing token fails closed |
| `get_instance()` (classmethod singleton) | resolves backend from `SPINE_API_IDEMPOTENCY_BACKEND`: `memory` (default) → `None`; `sql` → `SqlIdempotencyBackend()`; `auto` → sql iff `DATABASE_URL` set. Result cached for process lifetime. |

### 2.2 Call-site map — verified

| Call site | Key scope | Action | What a duplicate would do |
| --- | --- | --- | --- |
| `spine_api/routers/inbound.py:56` → `POST /api/v1/inbound/parse` (`inbound.py:109-136, 211, 247`) | `agency:{agency_id}` + full request payload (channel, raw_text, customer fields, agent_notes, strict_leakage) | `inbound_parse` | mint a duplicate trip + duplicate full spine pipeline (LLM spend); COMPLETED → replay same `trip_id`; PENDING → 409 `duplicate_intake_in_flight` |
| `spine_api/services/messaging_webhooks.py:22` → `process_inbound_traveler_message()` (`:68-89, 131, 136`) | `concierge:{to_phone}` + (message_id, channel, phones, body) | `traveler_message` | dispatch a duplicate concierge reply; COMPLETED → replay reply; PENDING → `duplicate_suppressed` |

Related but **separate** idempotency mechanisms (do not confuse with the registry):

- `spine_api/routers/price_lock.py:208-242` — per-trip *in-packet* `applied_idempotency_keys` dict (client-supplied key persisted inside the trip packet). Durable (lives with the trip) but has no concurrency guard and is a different mechanism from `IdempotencyRegistry`.
- `spine_api/services/agent_work_coordinator.py` + `spine_api/services/agent_requeue_jobs.py` — SQL lease/queue tables with their own `idempotency_key` PK / unique index (durable agent-runtime boundary). In-memory counterpart: `src/agents/runtime.py:272` lease table.
- `src/agents/closed_loop_learning.py:330`, `src/agents/operator_refinement_agent.py:81` — deterministic `idempotency_key` strings fed into the coordinator/queue layer above.

**Call-site honesty note:** both registry call sites carry the comment "In-process backend — see IdempotencyRegistry docstring for the multi-worker seam" (`inbound.py:54`, `messaging_webhooks.py:20`). That is now stale: the backend is env-selected, and deploys pin `sql`. Cosmetic but misleading to the next reader.

**Wiring honesty note (verified):** `process_inbound_traveler_message` has **no HTTP caller**. `POST /api/v1/messaging/webhook/{provider}` (`spine_api/routers/messaging.py:124-167`) verifies signatures and logs the event; it never routes to the concierge service. The webhook dedup is therefore currently exercised by tests only — the duplicate-reply risk is real the moment the route is wired, not before.

### 2.3 `SqlIdempotencyBackend` — verified read

- **Table** (`spine_api/models/idempotency.py` / `alembic/versions/add_idempotency_keys_table.py`): `idempotency_keys` with `key String(512) PRIMARY KEY` (the atomic cross-worker fence — one INSERT wins, loser gets IntegrityError and replays), `status`, `fencing_token String(128)`, `trip_id`, `action_name`, `request_hash`, `response_payload JSONB`, `error_message`, `created_at/completed_at (tz-aware)`, `ttl_seconds Integer`. Indexes on trip_id and status. Intentionally not RLS-protected (system-scoped, opaque keys). **Live-DB probe (verified 2026-09-04, read-only):** table exists in `waypoint_os` with 0 rows — the migration has run since the 2026-09-02 probe found it missing.
- **Engine/session:** lazy imports (`spine_api.core.database.engine` / `async_session_maker`); constructor accepts overrides (tests inject aiosqlite). The maker is *called* (`async with session_maker()`) — the session-maker crash bug from review was fixed here.
- **Sync→async bridge:** every public method wraps its coroutine in `spine_api.persistence._run_async_blocking` — the same process-wide background event-loop thread TripStore uses (`persistence.py:1618`). Serialized per process through one loop thread.
- **Acquire path:** INSERT (PK decides winner) → on conflict SELECT → TTL-expired rows reclaimed by **guarded UPDATE** (`WHERE key = :key AND created_at = :created_at`, rowcount==1 wins) → FAILED rows reclaimed by the same guarded UPDATE plus `AND status = 'FAILED'` (the review-cycle-2 fix: two concurrent retries of the same payload cannot both win). Retry budget: 3 recursive attempts, then `RuntimeError`.
- **Terminal path:** CAS `UPDATE ... WHERE key = :key AND status = 'PENDING' AND fencing_token = :token`; unfenced writes rejected.
- **All SQL is SQLAlchemy expression-style with bound parameters — verified: no string-built SQL anywhere in `src/agents/idempotency.py` or the model.**

### 2.4 Backend comparison

| Dimension | In-memory (`memory`, `_backend=None`) | `SqlIdempotencyBackend` |
| --- | --- | --- |
| Cross-worker dedup | None — each uvicorn worker/replica has its own dict | Holds (PK on `key` decides one winner across any process count) |
| Survives process restart | No — all records vanish; post-crash retry of a COMPLETED intake re-executes | Yes — durable rows |
| Replay payload fidelity | Python dict, exact | JSON/JSONB round-trip (both call sites already serialize via `model_dump(mode="json")` / `asdict` — verified JSON-safe) |
| TTL | Passive, per-record, 24h default | Same; reclaim via guarded UPDATE |
| FAILED retry | Allowed under lock | Allowed via guarded FAILED-reclaim (no double-retry) |
| Fencing | `hmac.compare_digest` on token | CAS UPDATE on token + PENDING |
| Payload-mismatch defense | **None** in either: stored `request_hash` is never compared to the presented payload. Safe only because `generate_key` hashes the payload — a caller-supplied colliding key would replay the wrong response (edge, both backends) | Same |
| Request latency cost | ~0 (dict under lock) | New intake: INSERT + commit (~1–2 roundtrips); replay hit: failed INSERT + SELECT; terminal: UPDATE + commit → ~2–4 local-Postgres roundtrips via one bridge thread. **Inferred:** negligible vs the multi-second `run_spine_once` LLM pipeline it guards |
| Memory/growth | Completed entries linger in the dict until that exact key is re-checked post-TTL; slow unbounded growth | Rows persist forever once written — **no janitor/cleanup path exists**; every distinct intake payload adds a permanent row |
| Storage dependency | None | Requires `DATABASE_URL` (asyncpg); lazy `create_all` on first use + alembic migration (both present, idempotent together) |
| Tests | `tests/test_intake_idempotency.py` (8) | `tests/test_idempotency_sql_backend.py` (12; durable semantics on in-memory aiosqlite, never live Postgres) |

### 2.5 Deployment reality — verified

| Surface | Workers | Idempotency backend |
| --- | --- | --- |
| `Dockerfile.spine_api:66` | `--workers ${SPINE_API_WORKERS:-1}` ("one worker is intentional until background supervisors are split out") | — |
| `docker-compose.yml` | inherits default → **1 worker** | **`sql` pinned** (`:31`, with explicit PT-08 comment) |
| `fly.toml` | `SPINE_API_WORKERS = "1"`; but `auto_start_machines = true`, `min_machines_running = 1` → **horizontal scale = multiple machines** | **`sql` pinned** |
| `render.yaml` | `--workers 1` | **`sql` pinned** |
| `.env.example:33` | — | `memory` (dev default) |
| Local `.env` (verified: no `SPINE_API_IDEMPOTENCY_BACKEND` key present) | dev `uvicorn ... --port 8000` per AGENTS.md = 1 worker | unset → **memory** |
| `Docs/review/SECURITY_HONESTY_WAVE_HANDOFF_2026-09-02.md:22` | claims "docker-compose pins sql (workers=4)" | **stale/incorrect** — no `SPINE_API_WORKERS=4` exists anywhere; all surfaces are 1 |

**Redis status (topic check):** Redis **is** in the stack — a compose service (`docker-compose.yml:94-108`, digest-pinned `redis:7.4`), `REDIS_URL` wired to the API, used by rate limiting (`spine_api/core/rate_limiter.py:43`) and usage accounting (`src/llm/usage_store.py` `RedisUsageStore`, P4-03), and required by startup assertion in production (`spine_api/core/startup_assertions.py:127-143`). A Redis idempotency backend is therefore *not* out-of-scope-by-absence; it is simply unnecessary while the SQL backend exists on an already-required Postgres dependency. Note as deliberate non-goal, not a gap.

---

## 3. The Honesty Boundary

Single-process idempotency stops being honest at four distinct boundaries — only the first is about worker count:

### 3.1 Worker/replica count × duplicate-risk matrix

| Deployment shape | Memory backend | SQL backend | Duplicate effects that actually hurt |
| --- | --- | --- | --- |
| 1 worker, 1 replica (today: compose/fly/render/dev) | ✅ Honest for *concurrent* duplicates | ✅ (already pinned) | Only the *restart* gap below |
| N workers, 1 replica (`SPINE_API_WORKERS>1`) | ❌ Broken — N independent dicts; provider retry landing on two workers mints 2 trips | ✅ | Duplicate **trips** (operator-visible, corrupts backlog), duplicate **LLM spend** per minted duplicate (NB01→NB02→NB03 pipeline re-runs), duplicate **concierge replies** (once webhook route wired — customer-visible) |
| 1 worker, M replicas (fly `auto_start_machines`, any LB) | ❌ Broken — same as N workers | ✅ | Same as above |
| Any shape, process restart mid-TTL | ⚠️ Broken — completed key lost; the *same* client retry re-executes | ✅ | Duplicate trip + duplicate LLM spend with zero concurrency involved |

**Severity ranking of duplicate effects (inferred from product reality):**

1. **Duplicate trips** — worst: operator-visible state corruption, customer may get two itineraries; no downstream dedup exists.
2. **Duplicate concierge replies** — customer-visible (double text); currently dormant because the webhook route is unwired.
3. **Double LLM spend** — real cost, no user impact, bounded by retry rate.

**Verified current exposure:** every deploy surface runs `--workers 1`, so *today* the memory backend would not actually produce cross-worker duplicates — but the SQL backend is pinned anyway, which is the correct posture because (a) fly scale-out is one command away, (b) the restart gap is closed, and (c) `TRIPSTORE_BACKEND=sql` already requires DATABASE_URL, so the SQL backend costs nothing new. **The one shape where dishonesty can still slip in: a developer/operator running `uvicorn --workers 4` locally (or overriding `SPINE_API_WORKERS`) with the unset env var → memory backend, silently.** There is no startup assertion coupling worker count or `ENVIRONMENT=production` to the backend choice — the parallel `REDIS_URL` assertion (`startup_assertions.py:127`) is the proven pattern to copy.

Related same-family in-process surfaces (documented for completeness, out of E3 scope): `_TRIP_EVENT_LISTENERS` SSE pub/sub in `inbound.py:65` and the in-memory lease in `src/agents/runtime.py` are also per-process; the durable `agent_work_coordinator`/`agent_requeue_jobs` SQL paths already exist as their cross-worker answers.

### 3.2 Semantics parity check — verified equivalent

The SQL backend preserves the registry contract exactly: same `(bool, record)` tuple, same FAILED-allows-retry, same fencing discipline, same TTL default. Two callers must keep one invariant: **pass the returned `fencing_token` through to `mark_completed`/`mark_failed`** (both call sites already do). The in-memory path additionally mints tokens only via acquisition, matching SQL.

---

## 4. Adoption Path Design — the smallest honest switch

**The switch already exists and is already thrown in all deploy surfaces.** Verified wiring:

- `get_instance()` reads `SPINE_API_IDEMPOTENCY_BACKEND` (`memory` | `sql` | `auto`) once per process; `sql`/`auto`+`DATABASE_URL` construct `SqlIdempotencyBackend()`.
- No code change is needed at either call site — the backend is transparent behind `IdempotencyRegistry`'s interface (that was the point of the seam, and tests `test_backend_selection_*` pin it).
- Table provisioning: alembic migration (ran in compose `migrations` service and fly `release_command`) **and** lazy `create_all(checkfirst=True)` fallback — both present and agree.

What remains, sized smallest-first:

1. **(Docs, ~5 min)** Fix the two stale "In-process backend" comments (`inbound.py:53-55`, `messaging_webhooks.py:19-21`) to say "backend resolved from `SPINE_API_IDEMPOTENCY_BACKEND`; deploys pin `sql`".
2. **(One assertion, ~30 min)** Add `_check_idempotency_backend` to `spine_api/core/startup_assertions.py`: fail fast when `ENVIRONMENT ∈ {production, staging}` (or `SPINE_API_WORKERS > 1`) while the resolved backend is memory. Resolution note: the assertion must read `os.environ[IDEMPOTENCY_BACKEND_ENV]`/`DATABASE_URL` directly rather than poking the cached singleton (import-order safety — `inbound.py` resolves `_IDEMPOTENCY` at import time). Mirrors the existing `REDIS_URL` check.
3. **(Optional flip of the dev default, ~5 min)** Change `.env.example` to `SPINE_API_IDEMPOTENCY_BACKEND=auto` so local dev with `DATABASE_URL` set (which local `.env` already has) quietly gets the durable backend and the restart gap closes in dev too. Keep `memory` as the bare-default for zero-dependency tests.
4. **(Janitor, ~1–2 h, only when intake volume makes it real)** The `idempotency_keys` table grows one row per distinct intake payload forever. Smallest correct cleanup: a periodic (or startup + daily) delete of terminal rows past `created_at + ttl_seconds`, using bound parameters — expression form already in-repo style:

   ```python
   await session.execute(
       delete(IdempotencyKey)
       .where(IdempotencyKey.status.in_(
           [IdempotencyStatus.COMPLETED.value, IdempotencyStatus.FAILED.value]))
       .where(IdempotencyKey.created_at < cutoff)
   )
   ```

   Do **not** delete PENDING rows younger than their TTL (that would release an in-flight lock). An index on `created_at` would be the accompanying migration if volume justifies it.

**Explicitly rejected alternatives (inferred reasoning):** Redis SETNX backend — adds a second durability tier and eviction-TTL semantics (an evicted key = silent dedup loss) for no capability Postgres doesn't already provide; Postgres advisory locks — session-scoped and weaker than a PK row with replay payload; waiting for "real scale" — pointless, the backend is built, tested, and one env var away.

---

## 5. Test Gaps

**SQL backend today: 12 tests** (`tests/test_idempotency_sql_backend.py`) — mapping/selection (5 pure) + durable semantics (7 on aiosqlite StaticPool): acquire/mark/replay, FAILED retry, TTL reclaim, fenced stale-owner rejection, unknown-key noop, cross-instance durability, direct-construction-stays-memory. Intake-boundary behavior: 8 tests (`tests/test_intake_idempotency.py`, in-memory registry + `/parse` + webhook service).

Gaps (all verified by reading the suites):

1. **No true cross-process race test.** SQLite+StaticPool validates control flow, not the Postgres PK-conflict race under two *connections*. The honest cross-worker claim rests on PK semantics + the alembic migration, untested. A live-Postgres integration test (two engines, ThreadPoolExecutor, `assert count(True)==1`) would close it — repo rule bars writing to the live test DB, so this needs a scratch database or a dedicated CI Postgres.
2. **No concurrent-reclaim race test** for the guarded TTL/FAILED UPDATEs (the review-cycle-2 fix has a regression test for *staleness*, but not for two simultaneous reclaims — the rowcount==1 branch is unexercised under contention).
3. **No retry-budget test**: `_retries >= 3 → RuntimeError` path is uncovered.
4. **No end-to-end test with the SQL backend wired into `/parse`** (i.e., env `sql` + sqlite injection through `get_instance` is untested; backend-selection tests construct backends directly).
5. **No payload-mismatch guard test** (see §2.4 — neither backend compares `request_hash`; either add the comparison or document the invariant that keys must come from `generate_key`).
6. **Webhook dedup has no HTTP-level test** — and cannot, until the route is wired to `process_inbound_traveler_message`.
7. **Restart-recovery test for the restart gap** (acquire → new backend instance over same store → replay) exists for the SQL backend (`test_sql_backend_durable_across_instances` — the exact property memory can't give); no equivalent documents that memory *loses* it, so the honesty boundary is asserted nowhere.

---

## 6. Sized Next Tasks

| # | Task | Size | Blocking? |
| --- | --- | --- | --- |
| T1 | Fix stale "in-process backend" comments at both call sites (§4.1) | XS | no |
| T2 | Startup assertion: production/staging or `SPINE_API_WORKERS>1` must not resolve memory backend (§4.2) | S | no — closes the only live dishonesty path |
| T3 | Flip `.env.example` to `auto` (§4.3) | XS | no |
| T4 | SQL-backed end-to-end `/parse` test via `get_instance` (§5.4) | S | pairs with T2 |
| T5 | Scratch-DB cross-process PK-race + concurrent-reclaim + retry-budget tests (§5.1–5.3) | M | needs a non-live test Postgres decision |
| T6 | Idempotency-key janitor + (if needed) `created_at` index migration (§4.4) | M | only when row volume is real |
| T7 | Wire `POST /messaging/webhook/{provider}` inbound-message branch to `process_inbound_traveler_message` (activates the second dedup call site) | M | separate wave; changes webhook behavior |

---

## 7. Decision Needed

1. **Enforcement posture:** should the memory backend be *forbidden* in production/staging via startup assertion (T2, fail-fast — recommended, mirrors the existing `REDIS_URL` gate), or only *warned*? Fail-fast can break a misconfigured deploy that previously "worked"; that is the point, but it is a behavior change.
2. **Dev default:** move `.env.example` (and ideally the code default in `get_instance`) from `memory` to `auto` (T3)? The bare code default `memory` should stay for dependency-free tests; the question is only the documented dev posture.
3. **Test-DB policy:** T5's true cross-process race test requires writing to a *scratch* Postgres, not `waypoint_os` (repo rule: tests must not create rows in the live test DB). Approve a dedicated CI/test database, or accept SQLite control-flow coverage as the standing bar?
4. **Janitor timing:** ship T6 now (small, but touches schema-adjacent code) or defer until `idempotency_keys` row count makes it measurable? (Currently 0 rows — deferral is defensible.)
5. **Stale doc:** `Docs/review/SECURITY_HONESTY_WAVE_HANDOFF_2026-09-02.md:22` claims compose pins "workers=4"; actual surfaces are all 1 worker. Correct the handoff line or leave history untouched per doc-preservation rules?

---

### Verification ledger

- **Verified (file reads):** registry + backend code, model, migration, both call sites, docker-compose.yml, Dockerfile.spine_api, fly.toml, render.yaml, .env.example, startup_assertions (no idempotency check), messaging.py route (webhook unwired), rate_limiter/usage_store Redis usage, both test suites (12 + 8 tests), FINDINGS_REGISTER/audit/handoff PT-08 + F-28 entries.
- **Verified (live, read-only, 2026-09-04):** `waypoint_os` contains `idempotency_keys` (0 rows) and `agent_requeue_jobs`; `agent_work` table absent. Local `.env` sets `DATABASE_URL`/`TRIPSTORE_BACKEND` but not `SPINE_API_IDEMPOTENCY_BACKEND`.
- **Inferred (marked):** SQL roundtrip latency negligible vs LLM pipeline; duplicate-effect severity ranking; Redis-backend rejection rationale.
