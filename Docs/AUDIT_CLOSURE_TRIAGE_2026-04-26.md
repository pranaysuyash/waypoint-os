# Original Audit Closure Triage Report

**Date**: 2026-04-26
**Original Audit**: `Docs/BACKEND_CODE_QUALITY_ARCHITECTURE_AUDIT_2026-04-18.md`
**Status**: Triaged — corrected priorities below

---

## 1. Deployment Reality

### How This App Runs

| Config | Value | Source |
|--------|-------|--------|
| Server | uvicorn | `Dockerfile:79`, `Procfile:16` |
| Workers | 4 | `Dockerfile:79` — `--workers 4` |
| Host | 0.0.0.0 | `Dockerfile:79` |
| Port | 8000 | `Dockerfile:79`, `fly.toml:20` |
| Platform | Docker/Fly.io | `Dockerfile`, `fly.toml`, `render.yaml` |

**Critical implication**: `LLMUsageGuard` in-memory singleton is **NOT production-safe** across 4 uvicorn workers.

---

## 2. Audit Closure Table

| # | Issue | Orig Severity | Current Evidence | Runtime Risk | Data Risk | Deploy Dep | Rec | Priority Today |
|---|-------|---------------|------------------|--------------|-----------|------------|-----|----------------|
| 1 | No LLM cost control | P0 | `LLMUsageGuard` implemented, integrated, tested ✅ | Medium (dogfood safe) | Low | LLM_GUARD_ENABLED=1 default | Production-enforce when Redis storage ships | **P0** (needs Redis before production) |
| 2 | `decision.py` 2,240 lines / 34 fns | P0 | Refactored into `src/decision/rules/` (8 files). Main file still 2,240 lines but 1,541 are function bodies | Low — rules extracted, no prod bugs reported | Low | None | Inventory functions, decide if further refactors are justified | **P1** |
| 3 | JSON file persistence | P1 | `spine_api/persistence.py` TripStore, AssignmentStore, AuditStore, OverrideStore, TeamStore, ConfigStore all JSON/JSONL. fcntl+flock + threading.Lock added since audit. SQLite used only for agency_settings | Medium if multi-worker | Medium if PII stored | Multi-worker? If yes, P0 | See persistence analysis below | **P1** |
| 4 | No caching → file-based caching | P1 | `DecisionCacheStorage` (JSON-based) exists in `cache_storage.py`. Used by hybrid_engine. 441 cache references in codebase. Non-Redis | Low for small scale | Low | None | Fine for single-process; Redis only if cache miss latency proven | **P2** |
| 5 | Long lines >120 chars | P2 | 1,758 E501 violations across codebase (88-char default) | None | None | None | Low-priority readability cleanup. Most violations in non-core files | **P3** |
| 6 | No data validation | P2 | `_make_json_serializable()` in persistence.py. Validation in agency_settings via `from_dict()`. API routes use FastAPI/Pydantic for request validation | Low | Medium if untrusted input | API surface | Audit boundaries before adding blanket Pydantic | **P2** |
| 7 | Data encryption | Medium (not in original P0/P1) | No encryption in persistence.py. JSON files written as plaintext | Low if no PII, High if PII stored | High if PII | PII classification needed | See PII analysis below | **P2-P0 conditional** |
| 8 | Monitoring/alerting | Medium (not in P0/P1) | Guard logs warnings at thresholds. No alert delivery. Telemetry exists (`src/intake/telemetry.py`) | Low | Low | None | Guard is logged; telemetry exists. Alert delivery deferred until production | **P2** |

---

## 3. P0 Decision: Guard is Dogfood-Only

### Evidence

| File | Lines | Finding |
|------|-------|---------|
| `Dockerfile` | 79 | `uvicorn ... --workers 4` |
| `Procfile` | 16 | `uvicorn ... --workers 4` |
| `src/llm/usage_guard.py` | 330 | `_instance = None` singleton, no Redis, no SQLite |

**Classification after triage**: **DOGFOOD-ONLY**

- ✅ Functional in single process — rates and budgets are enforced
- ❌ In-memory `_instance = None` — each of 4 uvicorn workers gets its own guard
- ❌ No shared state — rate counters, budget tracking, hourly windows are per-process
- ❌ On restart, state resets — daily budget spent so far is lost

**Impact if deployed to production as-is**:
- Hourly limit of 100 → each worker allows 100 = 400 total (4x limit)
- Daily budget of ₹1,000 → each worker resets to 0 on restart = unlimited spend
- User could restart process to reset budget daily

**Required before production**: Redis-backed guard storage OR SQLite-backed per-agency state

---

## 4. `decision.py` Function Inventory

**Current size**: 2,240 lines, 34 functions, ~1,541 lines of function bodies

### Function Categories

| Lines | Name | Size | Category | Notes |
|-------|------|------|----------|-------|
| 1955-2240 | `run_gap_and_decision` | 286 | **orchestrator** | Main entry, calls everything. Too long but orchestrates flow |
| 1145-1372 | `generate_risk_flags` | 228 | **rule logic** | Could move to `src/decision/rules/risk_flags.py` |
| 948-1122 | `decompose_budget` | 175 | **budget logic** | Could move to `budget_feasibility.py` |
| 1375-1475 | `_build_suitability_profile` | 101 | **suitability logic** | Could move to `src/suitability/` |
| 1654-1735 | `apply_operating_mode` | 82 | **mode logic** | Related to autonomy policy |
| 61-139 | `_generate_risk_flags_with_hybrid_engine` | 79 | **orchestrator** | Already calls hybrid engine; keep or move |
| 829-899 | `check_budget_feasibility` | 71 | **budget logic** | Already has rule file; could be moved |
| 1742-1809 | `calculate_confidence` | 68 | **scoring helper** | Pure function, could move to utils |
| 1897-1949 | `_synthesize_destination_ambiguity` | 53 | **ambiguity logic** | Rule-adjacent |
| 1618-1647 | `decide_commercial_action` | 30 | **business logic** | Rule-adjacent |
| 439-469 | `resolve_field` | 31 | **intake helper** | Intake logic, maybe move |
| 1838-1876 | `generate_budget_question` | 39 | **question helper** | UI generation, maybe move |
| 1522-1547 | `score_window_shopper_risk` | 26 | **scoring helper** | Pure function |
| 1550-1576 | `score_repeat_likelihood` | 27 | **scoring helper** | Pure function |
| 1579-1605 | `score_churn_risk` | 27 | **scoring helper** | Pure function |
| 472-495 | `field_fills_blocker` | 24 | **intake helper** | Intake logic |
| 398-417 | `classify_ambiguity_severity` | 21 | **intake helper** | Intake logic |
| 808-826 | `get_numeric_budget` | 19 | **budget helper** | Pure function <20 lines |
| 912-938 | `_get_composition_modifiers` | 27 | **intake helper** | Pure function |
| 1498-1519 | `score_ghost_risk` | 22 | **scoring helper** | Pure function |
| 36-58 | `_get_hybrid_engine` | 23 | **orchestrator** | Factory, keep |
| Others | (13 more) | <20 each | **helpers** | Fine to stay |

### Refactor Recommendation

The file is oversized but **not a launch blocker**. The rules extraction to `src/decision/rules/` was the right first step.

| Recommendation | Risk | Effort |
|----------------|------|--------|
| Move `generate_risk_flags()` (228 lines) to `src/decision/rules/risk_flags.py` | Medium — widely called | Medium |
| Move `decompose_budget()` (175 lines) to `src/decision/rules/budget_feasibility.py` | Medium — tightly coupled | Medium |
| Move `_build_suitability_profile()` (101 lines) to `src/suitability/` | Low | Small |
| Extract scoring helpers (`score_*`) to `src/intake/scoring.py` | Low | Small |
| Move `calculate_confidence()` (68 lines) to `src/intake/confidence.py` | Low | Small |
| **Keep** `run_gap_and_decision()` as orchestrator | — | — |

**Verdict**: This is **P1 technical debt**, not P0 launch blocker. Refactor only if function clearly belongs elsewhere AND tests exist.

---

## 5. Persistence Risk Analysis

### All JSON/JSONL Stores

| Store | File | What It Stores | PII? | Concurrency | Risk |
|-------|------|---------------|------|-------------|------|
| TripStore | `persistence.py:69-145` | Trips, extracted data, decisions, strategy | Yes (names, destinations, budget) | fcntl flock + threading.Lock ✅ | Medium |
| AssignmentStore | `persistence.py:149-216` | Agent assignments to trips | Yes (agent names) | fcntl flock ✅ | Low |
| AuditStore | `persistence.py:219-275` | Audit events | Yes (user_id, trip_id) | fcntl flock + threading.Lock ✅ | Low |
| OverrideStore | `persistence.py:278-441` | AI decision overrides per trip | No | JSONL append (no lock) | Medium |
| TeamStore | `persistence.py:452-526` | Team member records | Yes (email, phone) | threading.Lock ✅ | Medium |
| ConfigStore | `persistence.py:537-573` | Pipeline stages, approval thresholds | No | threading.Lock ✅ | Low |
| CacheStorage | `cache_storage.py:1-195` | Decision cache (JSONL) | No | fcntl flock ✅ | Low |
| Telemetry | `telemetry.py:1-67` | Telemetry events (JSONL) | No | JSONL append | Low |
| AgencySettings | `agency_settings.py:176-288` | Per-agency config | Yes (email, phone) | SQLite ✅ | Low |

**Key findings**:
- TripStore stores traveler data (budget, party composition, destinations) — **PII risk confirmed**
- JSON files are plaintext on disk — **no encryption**
- Concurrency protections exist (fcntl flock) — **good for single-host**
- With 4 uvicorn workers on same host, fcntl works (shared file locks via OS)
- Across Docker containers or hosts, fcntl won't help — need database

**JSON+locking acceptable for**: demo data, local dogfood, single-host with low concurrency
**NOT acceptable for**: real users, multi-host deployment, compliance requirements

**Verdict**: Persistence is fine for current dogfood stage, but real users need PostgreSQL migration or encryption. **P1** — not P0 unless compliance mandates.

---

## 6. Ruff Line Length

**Total E501 violations**: ~1,758 (excluding alembic, node_modules, .venv)

**Analysis**:
- Most violations are in non-critical files: tests, tools, notebooks
- Default config is 88 chars (PEP-8), not 120 as stated in audit
- If standard is 120, violations are fewer — many are 90-120 range
- Fixing would create noisy diffs across hundreds of files

**Recommendation**: **P3** — run `ruff check --select=E501` in CI but don't fix existing code in bulk. Only fix lines you modify.

---

## 7. Validation at Boundaries

| Boundary | Validation Status | Evidence | Risk |
|----------|-------------------|----------|------|
| API request input | ✅ FastAPI auto-validates via Pydantic models | `spine_api/server.py` — FastAPI route definitions with Pydantic schemas | Low |
| JSON data on load from disk | ❌ No validation | `persistence.py` — `json.load()` directly into `dict`, no schema check | Medium if file corrupted |
| LLM response before use | ⚠️ Estimate: schema enforcement by `self.llm_client.decide(schema=...)` but no explicit validation | `hybrid_engine.py:556` — no post-response validation | Low — client enforces schema shape |
| CanonicalPacket construction | ✅ Dataclass with typed fields | `src/intake/packet_models.py` — `CanonicalPacket` dataclass | Low |
| OverrideStore read | ❌ `json.loads(line)` with try/except skip | `persistence.py:336-341` — skips corrupted lines silently | Medium — data loss on corruption |

**Recommendation**: **P2** — Add validation on disk load for TripStore and OverrideStore. FastAPI input validation is already solid.

---

## 8. Summary: What Is Actually Not Done

### Done
- ✅ LLM cost tracking (usage guard, per-call estimation)
- ✅ Rate limiting (hourly rolling window)
- ✅ Budget checking (daily, warn/block modes)
- ✅ Threshold warnings (50%, 80%, 100%)
- ✅ Kill switch (`LLM_GUARD_ENABLED`)
- ✅ Integration tests
- ✅ Rule extraction from decision.py (8 rule files)

### Partial / Conditional
- 🟡 Guard production safety (functional but in-memory across 4 workers)
- 🟡 decision.py refactoring (rules extracted, main file still large)
- 🟡 JSON persistence (concurrency protections added but still JSON/JSONL)
- 🟡 File-based caching (functional, not Redis)

### Not Done / Unknown
- ❌ Data encryption for PII in JSON files
- ❌ Alert delivery on threshold breach
- ❌ Redis-backed persistence for guard
- ❌ PostgreSQL migration for trip data
- ❌ Monthly budget tracking
- ❌ Ruff line-length cleanup
- ❌ Pydantic validation on disk load

---

## 9. Corrected Priority Order

### P0 (Launch Blockers)

| # | Task | Why | Effort |
|---|------|-----|--------|
| 1 | **Guard Redis/SQLite-backed storage** | 4 uvicorn workers = 4 independent guards. Production deployment is unsafe without shared state | Medium (SQLite faster, Redis better for rate limits) |
| 2 | **Document dogfood-only limitation** | Don't claim production enforcement | Trivial |

### P1 (Important, Not Launch-Blocking)

| # | Task | Why | Effort |
|---|------|-----|--------|
| 3 | decision.py function inventory → refactor | Technical debt. Move `generate_risk_flags`, `decompose_budget`, `_build_suitability_profile` | Medium |
| 4 | PII encryption decision | TripStore has PII in plaintext JSON. If going to real users, this is P0 | Small (decision) / Medium (if implementing) |
| 5 | PostgreSQL migration decision | JSON+locking works for demo/low-concurrency. Real users need DB | Decision: Small / Migration: Medium |

### P2 (Useful but Not Blocking)

| # | Task | Why | Effort |
|---|------|-----|--------|
| 6 | Per-model rate limits for guard | All models share one limit currently | Small |
| 7 | Guard state API endpoint | For monitoring dashboards | Small |
| 8 | Pydantic validation on disk load | Prevent silent data corruption | Medium |
| 9 | Ruff line-length CI check | Prevent new violations | Trivial |

### P3 (Later / Platform Features)

| # | Task | Why | Effort |
|---|------|-----|--------|
| 10 | Monthly budget tracking | Daily budget is fine for now | Small |
| 11 | Alert delivery (email/webhook) | Guard just logs today | Medium |
| 12 | decision.py full cleanup (remaining <20 line functions) | Not worth it unless breaking them out clarifies | Small |
| 13 | AiAgentSettings, AgencyTier, SupportSettings, CommSettings | Platform-control features — need auth + tenant isolation first | Not specified |

---

## 10. Recommended Next Work Unit

**Unit: "Guard Production Closure"**

**Goal**: Make `LLMUsageGuard` production-safe across 4 uvicorn workers.

**Scope in**:
- Add SQLite-backed guard storage (`data/guard/usage_log.db`)
- Store per-hour call timestamps and daily cost per agency
- Replace `_hourly_calls` in-memory list with SQLite query
- Replace `_daily_cost` in-memory float with SQLite aggregate
- Maintain in-memory cache for performance (read from SQLite once, write-through)
- On process restart, rehydrate from SQLite

**Scope out**:
- Redis (simpler but adds dependency; SQLite is acceptable within single host)
- Alert delivery
- Monthly budget
- Per-model limits
- PostgreSQL migration
- Any UI changes

**Likely files**:
- `src/llm/usage_guard.py` — add `_Storage` class wrapping SQLite
- `tests/test_usage_guard.py` — test persistence across restarts

**Acceptance criteria**:
- [ ] Guard state survives process restart (agency A spent ₹500, restart → still ₹500)
- [ ] 2 uvicorn workers share state (call from worker 1, worker 2 sees updated limit)
- [ ] SQLite write uses INSERT/UPDATE with transaction
- [ ] In-memory cache rehydrates on first use
- [ ] All existing tests pass
- [ ] Guard documentation updated (remove dogfood-only warning)

**Why SQLite not Redis**: Single-host deployment (uvicorn 4 workers on one Docker container). SQLite with WAL mode is sufficient and adds no infrastructure dependency. Redis can be added later if multi-host.

---

*Report compiled: 2026-04-26*
*Evidence gathered from: Dockerfile, Procfile, fly.toml, pyproject.toml, ruff, decision.py AST parse, persistence.py grep*
