# Deliverable Report: Guard Production Closure

**Date**: 2026-04-26
**Phase**: Phase 4 — Guard Production Closure
**Scope**: LLMUsageGuard with atomic check-and-reserve + durable SQLite storage

---

## 1. Status Classification

**Guard is now production-safe for the current 4-worker single-container deployment.**

| Condition | Before | After |
|-----------|--------|-------|
| Storage | In-memory singleton | SQLite + WAL + busy_timeout |
| Cross-worker | Independent (400% overshoot) | Shared via SQLite file locks |
| Survives process restart | No | Yes (DB file on disk) |
| Fails on storage error | Open (call proceeds) | Closed (call blocked, default fallback) |
| Atomic check + reserve | Race condition | Single transaction |
| Budget reconciliation | None | Actual cost after call |
| Multi-container safe | N/A | No (same file required) |

---

## 2. Files Changed

| File | Change |
|------|--------|
| `src/llm/usage_guard.py` | **Rewritten** — `check_before_call()` uses atomic `check_and_reserve`. `record_call()` finalizes with actual cost. Fail-closed on storage error |
| `src/llm/usage_store.py` | **New** — `LLMUsageStore` (SQLite backend) + `InMemoryUsageStore` (test backend). WAL mode, busy_timeout=5000ms, schema init |
| `tests/test_usage_guard.py` | **Rewritten** — 26 tests covering: allow/block/warn, budget/rate limit, concurrency (100 threads), storage failure, reservation finalization |
| `src/intake/config/agency_settings.py` | Added `LLMGuardSettings` dataclass with guard config |
| `src/decision/hybrid_engine.py` | Guard integration: `LLM_GUARD_ENABLED` env check, fail-open on guard exception, fallback to default on block |
| `pyproject.toml` | Added `ruff` dev dependency |
| `Docs/AUDIT_CLOSURE_TRIAGE_2026-04-26.md` | **New** — Full audit triage with corrected priorities |
| `Docs/LLM_USAGE_GUARD_AND_AGENCY_CONTROLS_2026-04-26.md` | Guard implementation and research areas |
| `Docs/MASTER_PHASE_ROADMAP.md` | Updated Phase 4 priorities |

---

## 3. Schema Added

Table: `usage_events` in `data/guard/usage.db`

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| request_id | TEXT | UUID per call |
| agency_id | TEXT | `default` |
| model | TEXT | e.g., `gemini-2.0-flash` |
| feature | TEXT | e.g., `hybrid_engine` |
| created_at | TEXT | ISO timestamp |
| usage_date | TEXT | `YYYY-MM-DD` for daily aggregation |
| status | TEXT | `reserved \| completed \| failed \| blocked \| guard_unavailable` |
| estimated_cost | REAL | Pre-call estimate |
| actual_cost | REAL | Post-call actual |
| block_reason | TEXT | `rate_limit_exceeded \| budget_exceeded \| guard_unavailable` |
| warning_flags | TEXT | `null` or JSON array |
| metadata_json | TEXT | Reserved |

Indexes: `idx_usage_lookup`, `idx_usage_hourly`, `idx_request_id`

---

## 4. Test Results

```
tests/test_usage_guard.py           26 passed
tests/test_hybrid_engine.py         24 passed
tests/test_llm_clients.py            8 passed, 11 skipped
tests/test_agency_settings.py        6 passed
────────────────────────────────────────────────────────────────
Full suite                          728 passed, 13 skipped
```

**New tests added** (concurrency and edge cases):

| Test | What it proves |
|------|----------------|
| `test_race_hundred_calls_single_worker` | 100 concurrent threads: exactly 10 allowed when limit=10 |
| `test_parallel_budget_enforcement` | Budget ₹5.0, 10 threads: exactly 5 allowed |
| `test_reservation_finalization` | Reserved event updates to `completed` with actual cost |
| `test_blocked_call_not_finalized` | Blocked calls have no reservation, don't inflate budget |
| `test_guard_storage_error_fails_closed` | GuardStorageError → blocked with `guard_unavailable` |
| `test_blocks_on_second_call` | Second call with same params blocked (no state manipulation) |

---

## 5. Atomic Check-and-Reserve Behavior

Flow in `LLMUsageStore.check_and_reserve()`:

```sql
BEGIN EXCLUSIVE;
SELECT hourly_calls, daily_cost FROM usage_events WHERE ... AND date = today;
IF hourly_calls >= limit: INSERT blocked; COMMIT; RETURN allowed=False;
IF projected_cost > budget AND mode=block: INSERT blocked; COMMIT; RETURN allowed=False;
INSERT reserved; COMMIT; RETURN allowed=True;
```

Key guarantees:
- All reads + write in one SQLite transaction
- `busy_timeout=5000ms` (5 second lock wait)
- `journal_mode=WAL` (write-ahead logging, read concurrency)
- Fail-closed on any exception: `GuardStorageError` blocked, `default_fallback` used

---

## 6. Budget Accounting

| Stage | Behavior |
|-------|----------|
| Before call | Estimated cost reserved in `estimated_cost` column |
| After call (success) | `actual_cost` updated, status=`completed` |
| After call (failure) | `actual_cost` updated, status=`failed` — cost counts for budget |
| Budget calculation | Only `actual_cost` from `status=completed` events |
| Rate calculation | Counts `status IN ('reserved', 'completed', 'failed')` |

**Design decision**: Blocked calls do NOT count toward budget or rate. Only calls that hit the LLM (or tried to) are tracked.

---

## 7. Kill Switch

Environment variable: `LLM_GUARD_ENABLED`
- `1` (default): Guard active, SQLite storage used
- `0`: Guard inactive, all calls allowed

**When disabled**: No DB operations. No reservations. No logging overhead.

---

## 8. Production Safety for Current Deployment

| Deployment Characteristic | Supported? |
|---------------------------|------------|
| 4 uvicorn workers on single host | ✅ Yes — shared SQLite file |
| Single Docker container | ✅ Yes — `data/guard/usage.db` on container filesystem |
| Persistent volume for `data/` | ✅ Yes — survives restart |
| Ephemeral container / no persistent volume | ❌ No — DB lost on recreation |
| Multiple containers / replicas | ❌ No — each container has independent DB |
| Serverless / Lambda | ❌ No — state between invocations lost |
| Multi-host | ❌ No — needs Redis/PostgreSQL |

**Required for multi-instance production**: Redis-based `LLMUsageStore` implementation.

---

## 9. Remaining Limitations

| # | Limitation | Priority | Fix When |
|---|------------|----------|----------|
| 1 | Single-container only | P1 | Multi-container deployment needed |
| 2 | SQLite file must be on persistent volume | P1 | Container recreation without volume = state loss |
| 3 | No per-model rate limits | P2 | Different LLM models need different limits |
| 4 | Alert delivery (email/webhook) | P2 | Blocked calls logged only; no proactive alerts |
| 5 | Monthly budget tracking | P2 | Only daily tracked |
| 6 | Admin UI for guard settings | P3 | Platform feature — deferred |
| 7 | `decision.py` refactor | P3 | Technical debt; not launch-blocker |
| 8 | PostgreSQL migration for trip data | P1-P0 | If real user/PII data enters JSON stores |
| 9 | Data encryption for PII JSON files | P1-P0 | If real user data stored |
| 10 | `ruff --select=E501` fixes | P3 | 1,758 violations; noise, not priority |

---

## 10. Next Recommended Work Unit

**Unit: "Guard Multi-Instance Storage"** (only when needed)

Scope:
- Implement `RedisUsageStore` as alternative backend
- Add `GUARD_STORE_BACKEND` env var (`sqlite`/`redis`)
- Redis uses sorted sets for time-series + atomic `ZADD` + `ZRANGEBYSCORE`
- Keep `SQLiteUsageStore` as default for single-host
- Add `healthcheck` endpoint for guard DB connectivity

Not before:
- Multi-container deployment is confirmed
- Persistent volume config is uncertain
- Redis infrastructure exists

---

## 11. Rollback Plan

If everything must be removed:
1. Delete `src/llm/usage_store.py`
2. Revert `src/llm/usage_guard.py` to pre-closure version
3. Remove guard integration from `hybrid_engine.py`
4. Delete `data/guard/usage.db`
5. Remove `LLMGuardSettings` from `agency_settings.py` (safe to keep, backward-compatible)
6. `LLM_GUARD_ENABLED=0` disables guard without code changes

---

*Last updated: 2026-04-26*
*Full suite: 728 passed, 13 skipped*
