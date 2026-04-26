# LLM Usage Guard & Per-Agency Controls — Implementation & Research

**Date**: 2026-04-26
**Status**: Foundation implemented; production classification: **DOGFOOD-ONLY** (single-process, in-memory)

---

## 1. Production Safety Classification

**Current classification: DOGFOOD-ONLY**

The guard is functional and correct within a single Python process. It MUST NOT be relied upon as production enforcement across multiple workers, backend instances, or server reloads.

**Why**: In-memory singleton state (`_instance = None`) resets on process restart and is not shared across workers. Each uvicorn worker gets its own guard instance.

**Required before production use**: Redis-backed or database-backed guard storage.

---

## 2. What Was Implemented

### LLM Usage Guard (`src/llm/usage_guard.py`)

A lightweight gate that answers: **Can this LLM call proceed right now?**

**Core class**: `LLMUsageGuard`

**Two operations**:
- `check_before_call(model, estimated_cost, feature)` → `LLMUsageDecision`
- `record_call(model, estimated_cost, feature, success)`

**Decision object** (`LLMUsageDecision`):
```python
allowed: bool
reason: str | None
warnings: list[str]
block_reason: str | None  # "rate_limit_exceeded" | "budget_exceeded"
current_daily_cost: float
projected_daily_cost: float
daily_budget: float | None
current_hourly_calls: int
hourly_limit: int | None
```

**Rate limiting**: Rolling one-hour window. Blocked calls NOT counted as usage.

**Budget**: Daily budget with configurable warning thresholds (default: 50%, 80%, 100%).
- `warn` mode: Allow over-budget calls, log warning
- `block` mode: Reject over-budget calls

**Config** (environment variables):
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_GUARD_ENABLED` | bool | `1` | Kill switch — disables guard enforcement without removing code |
| `LLM_MAX_CALLS_PER_HOUR` | int | None | Hourly call limit |
| `LLM_DAILY_BUDGET` | float | None | Daily budget in INR |
| `LLM_BUDGET_MODE` | str | `warn` | `warn` or `block` |
| `LLM_BUDGET_WARNING_THRESHOLDS` | str | `0.5,0.8,1.0` | Threshold fractions |

**Kill switch behavior**: `LLM_GUARD_ENABLED=0` disables guard entirely — all LLM calls proceed without checking or recording.

**Files**:
- `src/llm/usage_guard.py` — guard implementation
- `tests/test_usage_guard.py` — 21 unit tests
- `src/intake/config/agency_settings.py` — `LLMGuardSettings` dataclass added
- `src/decision/hybrid_engine.py` — guard integrated into `_call_llm()`
- `tests/test_hybrid_engine.py` — 6 hybrid engine integration tests

---

## 3. Runtime Behavior

### Guard Integration Point

`hybrid_engine.py:_call_llm()` at line 540:

```
estimate cost → guard.check_before_call() → [blocked? return None]
→ call LLM → guard.record_call(success=True/False)
```

### When Blocked

1. Guard returns `allowed=False` with `block_reason`
2. Structured log emitted: `llm_usage_guard.blocked` with all decision metadata
3. `health_checker.record_llm_failure("usage_guard_blocked: {block_reason}")` called
4. `_call_llm()` returns `None`
5. `decide()` falls through to `default_fallback` — **existing fallback behavior preserved**

### Failure Semantics

**Fail-open**: If the guard raises an exception, the call is allowed and the exception is logged as a warning.

Rationale: Guard failures should not crash the decision engine. Availability takes precedence over cost control. If cost enforcement is critical, set `LLM_BUDGET_MODE=block` and monitor guard health.

### Cost Accounting Assumptions

**Current behavior**:
- Budget check uses **estimated cost before the call** (pre-token count from `count_tokens`)
- Actual cost tracking uses **estimated cost after the call** (same method, slightly better estimate)
- Both use `llm_client.estimate_cost(prompt_tokens, completion_tokens)`
- This means: budget is based on rough estimates, not actual provider billing

**Implication**: Daily budget may not match actual spend exactly. This is acceptable for guardrails; for accurate billing, actual provider logs are required.

---

## 4. LLM Call Path Coverage

| Path | Goes through guard? | Notes |
|------|---------------------|-------|
| `hybrid_engine._call_llm()` | ✅ Yes | Guard applied here |
| `intake.decision.engine.decide()` | ✅ Yes | Uses `hybrid_engine.decide()` |
| `tools/validation.structured_validator` | ✅ Yes | Uses `hybrid_engine.decide()` |
| `tools/validation.hybrid_engine_validator` | ✅ Yes | Uses `hybrid_engine.decide()` |
| `llm/__init__.py` factory functions | ❌ No | These are client factory functions, not call sites |

The `llm/__init__.py` factory functions (`create_llm_client`, `get_default_client`) do not invoke the guard — they only create client instances. All actual LLM call sites go through `hybrid_engine._call_llm()`.

---

## 5. SQLite Settings Behavior

**Schema migration**: `LLMGuardSettings` is a new field added to `AgencySettings`. The SQLite table has no schema migration — it uses `CREATE TABLE IF NOT EXISTS`. Existing rows without `llm_guard` will be deserialized using `AgencySettings.from_dict()`.

**Missing settings behavior**: If `llm_guard` is missing from stored settings:
1. `AgencySettings.from_dict()` ignores unknown keys
2. `llm_guard` uses its dataclass default: `enabled=True`, no limits
3. Safe defaults — guard is enabled but no limits enforced unless configured

**For new agencies**: `AgencySettingsStore.load()` seeds defaults (including `llm_guard`) on first load.

---

## 6. Per-Agency Controls Already Implemented

Each agency has its own `AgencySettings` (stored in SQLite at `data/settings/agency_settings.db`).

| Control | Field | Purpose |
|---------|-------|---------|
| LLM guard | `llm_guard: LLMGuardSettings` | Rate limits, budget caps, warn/block |
| Operating hours | `operating_hours_start/end` | When agent is active |
| Preferred channels | `preferred_channels` | whatsapp, email |
| Brand tone | `brand_tone` | professional/friendly |
| Target margin | `target_margin_pct` | Pricing guidance |
| Auto-negotiation | `enable_auto_negotiation` | Whether to haggle |
| Checker agent | `enable_checker_agent` | Whether secondary review fires |
| Autonomy policy | `autonomy: AgencyAutonomyPolicy` | Per-decision-state approve/review/block gates |
| Override learning | `autonomy.learn_from_overrides` | Whether overrides become cached rules |

---

## 7. Remaining Risks

### P0 — Must Fix Before Production Enforcement

| Risk | Description | Fix |
|------|-------------|-----|
| **In-memory state** | Guard state resets on process restart. Not shared across workers. | Implement Redis or SQLite-backed guard storage |
| **No distributed rate limiting** | Each worker has independent counters | Redis sorted set for rolling window |
| **No persistence of guard state** | Budget tracking lost on restart | Persist to SQLite/Redis daily |

### P1 — Should Fix

| Risk | Description | Fix |
|------|-------------|-----|
| **Estimated vs actual cost** | Budget based on estimates, not actual provider billing | Add actual cost callback or reconciliation |
| **No per-model limits** | All models share one hourly limit | Add `max_calls_per_hour_per_model` config |
| **Guard state not exposed** | No API endpoint to query current guard state | Add `/api/usage-guard/status` endpoint |

### P2 — Future Work

| Item | Priority | Reason |
|------|----------|--------|
| Redis-backed guard storage | P1 | Required for multi-worker production |
| Alert delivery (email/webhook) | P2 | Not needed for guard to function |
| Monthly budget tracking | P2 | Daily is sufficient for now |
| Guard state API | P1 | Useful for monitoring dashboards |

---

## 8. Next Allowed Work

The following are explicitly **NOT allowed** until Redis/production guard storage is implemented:

- ❌ `AiAgentSettings` dataclass
- ❌ `AgencyTier` (Starter/Pro/Enterprise)
- ❌ `SupportSettings` dataclass
- ❌ `CommSettings` dataclass
- ❌ Admin UI for agency settings
- ❌ Alert delivery
- ❌ Monthly budget tracking
- ❌ Monetization/tier controls

These are platform-control features that need real usage patterns, auth completion, and tenant isolation before they make sense.

**Next required work**: Redis-backed guard storage — see `ISSUE-P0-REDIS-STORAGE` below.

---

## 9. Testing Evidence

```
tests/test_usage_guard.py           21 passed
tests/test_hybrid_engine.py         24 passed (including 6 new guard integration tests)
tests/test_llm_clients.py            8 passed, 11 skipped
tests/test_agency_settings.py        6 passed
─────────────────────────────────────────────────────
Total:                             59 passed, 11 skipped
```

Integration tests added:
- `test_guard_allows_call_proceeds_normally` — allowed call goes through
- `test_guard_block_threshold_prevents_llm_call` — budget block → default fallback
- `test_guard_block_rate_limit_prevents_llm_call` — rate limit block → default fallback
- `test_guard_disabled_allows_llm_without_guard` — killswitch allows all
- `test_guard_record_failure_on_llm_exception` — exception → default fallback
- `test_guard_killswitch_stops_enforcement` — `LLM_GUARD_ENABLED=0` bypasses guard

---

## 10. Rollback Plan

If `LLMUsageGuard` needs to be removed:
1. Delete `src/llm/usage_guard.py`
2. Set `LLM_GUARD_ENABLED=0` to disable without code change
3. Remove `LLM_GUARD_ENABLED` import and usage from `hybrid_engine.py`
4. Remove `LLMGuardSettings` from `agency_settings.py` (optional, backward compat via dataclass defaults)
5. Run tests — all should pass without guard

---

## 11. Classification of Current Guard

| Property | Value | Notes |
|----------|-------|-------|
| **Production-safe** | No | Single-process only |
| **Dogfood-safe** | Yes | Works within one process |
| **Storage** | In-memory | Resets on restart |
| **Multi-worker safe** | No | Each worker has own state |
| **Kill switch** | Yes | `LLM_GUARD_ENABLED=0` |
| **Fail behavior** | Fail-open | Guard exception → allow call |
| **LLM path coverage** | Full | All `hybrid_engine` LLM calls |
| **Settings fallback** | Safe defaults | No limits unless configured |

---

*Last updated: 2026-04-26 — post-closure-pass*
