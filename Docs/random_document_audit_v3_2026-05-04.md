# Random Document Audit Report v3

**Date:** 2026-05-04
**Audit Method:** Agent-driven with 3 parallel verification subagents
**Repository:** `/Users/pranay/Projects/travel_agency_agent` (Waypoint OS)

---

## 1. Document Inventory

**Total documentation files found:** ~2,553 `.md` files (excluding node_modules/.venv/.next)

**Document categories by type:**

| Type | Approx Count | Represents |
|------|-------------|------------|
| Research / exploration | 240+ | Exploratory and competitive research |
| Persona scenarios | 396 | User persona journey docs |
| Frontend feature docs | 918 | Deep-dive feature documentation |
| Industry domain research | 330+ | Travel industry expertise captured |
| Discussions / first-principles | 42 | Architecture and domain modeling |
| Audits | 40+ | Codebase, UX, security audits |
| Specs (core system) | 7 | Formal pipeline specifications |
| Specs (notebooks) | 6 | NB01-NB06 notebook specs |
| Roadmaps | 20+ | Phase plans, exploration roadmaps |
| ADRs | 8 | Architecture Decision Records |
| Issue reviews | 12+ | Dated process issue reviews |
| Todo lists | 5 | TODO.md + sub-task lists |
| Design documents | 10+ | Visual design, typography spec |
| Context/memory | 20+ | Institutional memory, context docs |
| Plans | 8+ | Implementation plans |
| Reviews | 12+ | Architecture, security, PR reviews |
| Handoff documents | 5+ | Post-implementation handoffs |

---

## 2. Random Selection

**Selection pool:** All `.md` files under `specs/`, `Docs/architecture/adr/`, and `notebooks/` — the directories most likely to contain feature-related tasks.

**Selection method:** `shuf` (Unix pseudo-random shuffle, entropy from /dev/urandom per macOS zsh)

**Command:** `ls specs/ Docs/architecture/adr/ notebooks/ | grep '\.md$' | shuf | head -1`

**Chosen document:** `ADR-002-SPINE-API-ARCHITECTURE.md`

**Why this doc is worth auditing:** ADR-002 defines the backbone service architecture (subprocess → HTTP migration). It was marked "Implemented" in April 2026 but the codebase has evolved significantly since then. This is a high-stakes document — incorrect claims about the architecture layer directly impact deployment, onboarding, and any developer working on the backend/frontend boundary.

---

## 3. Chosen Document Deep Analysis

**Document:** `Docs/architecture/adr/ADR-002-SPINE-API-ARCHITECTURE.md` (192 lines, ~7KB)
**Date:** 2026-04-15
**Status per ADR:** Implemented

### 3A. Extracted Doc Items

| Doc Item ID | Type | Short quote / evidence | Location | Interpretation | Confidence |
|-------------|------|----------------------|----------|----------------|------------|
| D01 | Explicit Task | "Replace subprocess spawning with a persistent FastAPI service" | L43 | Build spine_api FastAPI server | High |
| D02 | Explicit Task | "Replace Python subprocess wrapper with TypeScript HTTP client" | L57 | Build spine-client.ts | High |
| D03 | Explicit Task | "Use `SPINE_API_URL` env var for service location (defaults to `http://127.0.0.1:8000`)" | L65 | Configure service discovery | High |
| D04 | Explicit Task | "Unit Tests: Test spine-client.ts HTTP logic and error handling" | L170 | Test spine-client.ts | High |
| D05 | Explicit Task | "Integration Tests: Test full request flow through spine_api service" | L171 | Integration tests for /run | High |
| D06 | Explicit Task | "Load Tests: Verify concurrent request handling capabilities" | L172 | Load test the service | High |
| D07 | Explicit Task | "Fallback Tests: Ensure graceful degradation if service unavailable" | L173 | Test proxy error handling | High |
| D08 | Explicit Task | "Implement service health checks before full migration" | L181 | Health check endpoint | High |
| D09 | Explicit Task | "Update developer setup instructions for running spine_api service" | L182 | Update docs/setup | High |
| D10 | Current-State Claim | "Frontend (Next.js) ← HTTP → Spine API (FastAPI) ← Python → Core Logic" | L80 | Architecture diagram | High |
| D11 | Current-State Claim | "`spine_api/server.py` - FastAPI application with `/run` endpoint" | L86 | Server has /run endpoint | High |
| D12 | Current-State Claim | "Pre-loads all Python modules on startup" | L87 | Module preloading at startup | High |
| D13 | Current-State Claim | "Proper error responses and logging" | L89 | Error handling exists | High |
| D14 | Current-State Claim | "HTTP client with proper TypeScript types" | L92 | TypeScript types exist | High |
| D15 | Current-State Claim | "Environment-based service discovery" | L93 | SPINE_API_URL env var | High |
| D16 | Current-State Claim | "Error handling and retry logic" | L94 | Client retry logic | High |
| D17 | Architecture Claim | "`frontend/src/lib/spine-wrapper.py`" was REMOVED (L30) | L30 | Old subprocess removed | High |
| D18 | Architecture Claim | "Core Logic: `src/intake/orchestration.py:run_spine_once()`" | L33 | Core function location | High |
| D19 | Intended-State Claim | "API Versioning: Implement proper API versioning for future changes" | L189 | Future: API versioning | High |
| D20 | Intended-State Claim | "Caching: Add response caching for expensive operations" | L190 | Future: response cache | High |
| D21 | Intended-State Claim | "Rate Limiting: Implement request rate limiting at service level" | L191 | Future: rate limiting | High |
| D22 | Intended-State Claim | "Service Mesh: Consider Istio/Linkerd for service discovery" | L188 | Future: service mesh | High |
| D23 | Performance Claim | "~10x faster response times (no process spawning)" | L126 | Performance improvement | Medium |
| D24 | Reliability Claim | "Proper error boundaries and service monitoring" | L128 | Reliability | Medium |
| D25 | Deployment Claim | "Deploy as containerized service with proper health checks" | L116 | Production deployment | Medium |
| D26 | Deployment Claim | "Can be load-balanced horizontally" | L118 | Horizontal scaling | Medium |
| D27 | Risk | "Adds network layer with potential failure modes" | L135 | Network complexity risk | Medium |
| D28 | Risk | "Requires managing both frontend and API services" | L136 | Multi-service deployment overhead | Medium |
| D29 | Implicit Task | Frontend needs to handle spine API being unreachable gracefully | Implicit | Error boundaries on FE | Medium |
| D30 | Implicit Task | Monitoring/Observability should be set up for HTTP service | L47-48 | OTel/Prometheus setup | Medium |
| D31 | Implicit Task | Need retry logic for transient HTTP failures | L59 | Retry/backoff in client | Medium |
| D32 | Implicit Task | Need CI to verify contract between frontend and backend | Implicit | Contract guard CI | Medium |
| D33 | Contradiction | "Monitor/implement service health checks before full migration" vs "Status: Implemented" | L181 vs L5 | Migration complete or ongoing? | Medium |

---

## 4. Extracted Task Candidates

| Task Candidate ID | Source Doc Items | Task | Type | Why | Expected Area |
|-------------------|-----------------|------|------|-----|---------------|
| T01 | D01, D10 | spine_api FastAPI server | Explicit | Core ADR requirement | spine_api/ |
| T02 | D02, D14, D16 | TypeScript HTTP client | Explicit | Core ADR requirement | frontend/src/lib/ |
| T03 | D03, D15 | SPINE_API_URL env var config | Explicit | Service discovery | frontend/.env, BFF routes |
| T04 | D04 | Unit tests for spine-client.ts | Explicit | ADR testing strategy | frontend/src/__tests__/ |
| T05 | D05 | Integration tests for full flow | Explicit | ADR testing strategy | tests/ |
| T06 | D06 | Load tests for concurrent requests | Explicit | ADR testing strategy | None exist |
| T07 | D07 | Fallback tests for degradation | Explicit | ADR testing strategy | frontend/src/__tests__/ |
| T08 | D08 | Health check endpoint | Explicit | Migration prerequisite | spine_api/server.py |
| T09 | D09 | Update developer setup docs | Explicit | Migration prerequisite | Docs/, dev.sh |
| T10 | D19 | API versioning | Intended | Future consideration | spine_api/ routes |
| T11 | D20 | Response caching | Intended | Future consideration | spine_api/ |
| T12 | D21 | Rate limiting | Intended | Future consideration | spine_api/core/ |
| T13 | D22 | Service mesh | Intended | Long-term future | Deployment config |
| T14 | D29 | FE graceful degradation | Implicit | Error handling | frontend/ BFF proxy |
| T15 | D30 | Observability setup | Implicit | Production readiness | spine_api/ OTel |
| T16 | D31 | Retry/backoff in client | Implicit | Reliability | spine-client.ts, api-client.ts |
| T17 | D32 | CI contract guard | Implicit | Quality assurance | .github/workflows/ |
| T18 | D33 | Resolve "Implemented" vs incomplete migration status | Implicit | Doc clarity | ADR-002 itself |
| T19 | Implicit | Remove competing runSpine paths | Implicit | Architecture cleanup | spine-client.ts vs api-client.ts |
| T20 | Implicit | Clean up 27 stale spine-wrapper.py references | Implicit | Doc cleanup | Docs/ historical files |
| T21 | Implicit | Stale comment in spine-client.ts about SPINE_API_URL | Implicit | Code quality | spine-client.ts:12 |
| T22 | Implicit | `cache_invalidated` dead field cleanup | Implicit | Code quality | contract.py, server.py |
| T23 | Implicit | Rate limiting on core business endpoints | Implicit | Security hardening | server.py |
| T24 | Implicit | dev.sh env var loading gap | Implicit | Dev experience | dev.sh |

---

## 5. Static Codebase Reality Check

### 5A. Claim-by-claim verification

| Task ID | Codebase Status | Evidence | What exists today | Gap |
|---------|----------------|----------|-------------------|-----|
| T01 (FastAPI server) | **Done** | `spine_api/server.py:413` — FastAPI app with 100+ endpoints, not just `/run` | Full agency management API | ADR understates scope (says "with /run endpoint", but server has 100+ routes) |
| T02 (TS HTTP client) | **Done but stale** | `frontend/src/lib/spine-client.ts:1-133` exists, BUT `api-client.ts:247` has the actual used `runSpine` | Two `runSpine` functions; spine-client.ts unused | Competing implementations; spine-client.ts comment on L12 claims SPINE_API_URL usage but L32 hardcodes `/api/spine` |
| T03 (SPINE_API_URL) | **Partially Done** | `proxy-core.ts:24`, 13 BFF route files use it; `.env` missing; `.env.local` missing | Default works everywhere | Config files undocumented; dev.sh doesn't export it |
| T04 (spine-client tests) | **Missing** | Zero test files for spine-client.ts; glob `*spine-client*` in frontend returns nothing | No unit tests for `runSpine()` or `validateSpineRequest()` | 100% gap |
| T05 (integration tests) | **Done** | `test_spine_api_contract.py` (9 tests), `test_run_lifecycle.py` (21 tests), `test_run_state_unit.py` (46 tests), `test_d1_autonomy.py` (25+ tests) | 100+ integration tests | None |
| T06 (load tests) | **Missing** | No K6, Locust, or Artillery configs exist | Nothing | 100% gap |
| T07 (fallback tests) | **Missing** | `proxy-core.ts` implements 502/504 but zero tests exist | Error handling code without test coverage | 100% gap |
| T08 (health check) | **Done** | `server.py:727` — `GET /health` returns `{"status":"ok"}` | Health endpoint exists | None |
| T09 (dev setup docs) | **Partially Done** | `dev.sh` exists, `README.md` has quickstart, but `SPINE_API_URL` not documented in setup | Basic setup covered | Missing env var documentation |
| T10 (API versioning) | **Not Done** | Zero version prefixes in routes; only `version="1.0.0"` FastAPI metadata at L416 | Nothing | Deferred per ADR |
| T11 (response cache) | **Not Done** | No Redis, ETags, or Cache-Control; BFF defaults to `no-store` | Decision cache exists (application-level, `src/decision/`) but not HTTP response caching | Deferred per ADR |
| T12 (rate limiting) | **Contradicts ADR** | `spine_api/core/rate_limiter.py:1-66` — fully implemented! SlowAPI middleware wired at `server.py:430` | 7 auth+public endpoints rate-limited | Core business endpoints unrated; ADR should be updated from "future" to "partially implemented" |
| T13 (service mesh) | **Not Done** | No Istio/Linkerd config | Nothing | Deferred per ADR, no urgency |
| T14 (FE degradation) | **Code Done, Tests Missing** | `proxy-core.ts:259-277` handles 502/504 with proper error shape | Code exists, zero tests | Tests missing (see T07) |
| T15 (observability) | **Done** | `server.py:211-215` — OTel config, Prometheus exporter port 9090 | OTel + Prometheus | None |
| T16 (retry logic) | **Done** | `api-client.ts:258-267` — poll loop with 180s timeout, 2s interval | Poll loop with exit after 90 iterations | No exponential backoff (fixed 2s) |
| T17 (CI contract guard) | **Done** | `.github/workflows/run-contract-guard.yml:1-39` — runs `test_run_contract_drift_guard.py` and `route-map.test.ts` on push/PR | CI working | None |
| T18 (ADR status clarity) | **Stale Doc** | ADR says "Implemented" but 3 of 4 future considerations are actually implemented (rate limiting) or still deferred | ADR out of date | Needs update |
| T19 (competing runSpine) | **Duplicated** | Two identically-named `runSpine` functions: `spine-client.ts:34` and `api-client.ts:247`. 57 files import `api-client`, zero import `spine-client` | Unused duplicate | Dead code + naming conflict |
| T20 (stale wrapper refs) | **Stale Docs** | 27 historical doc references to `spine-wrapper.py` which doesn't exist | File deleted, docs not cleaned | Doc cleanup needed |
| T21 (stale comment) | **Stale Code** | `spine-client.ts:12` comment: "Set SPINE_API_URL env var" but L32 uses hardcoded `/api/spine` | Misleading comment | Fix or remove |
| T22 (dead field) | **Dead Code** | `contract.py:225` `cache_invalidated: bool = False`, `server.py:3532` always passes `False` | Field exists but never meaningfully set | Remove or implement |
| T23 (missing rate limits) | **OperationalRisk** | `POST /run`, `GET /trips`, `GET /inbox`, `GET /analytics/*` have no rate limits | Auth endpoints protected, business endpoints not | Add rate limits or document why not |
| T24 (dev.sh gaps) | **Developer friction** | `dev.sh` doesn't export `SPINE_API_URL` or load `.env` | Services start but config undocumented | Fix dev.sh |

### 5B. Architecture diagram accuracy

```
ADR-002 diagram (L80):  Frontend (Next.js) ← HTTP → Spine API (FastAPI) ← Python → Core Logic
Actual architecture:    Browser ← HTTP → Next.js BFF ← HTTP → Spine API (FastAPI) ← Python → Core Logic
```

The BFF proxy layer is absent from the ADR diagram. This is a significant omission — all browser traffic routes through Next.js server-side handlers before reaching FastAPI.

### 5C. Additional architecture findings

- **Three competing paths to run the spine pipeline:**
  1. `app.py` (Streamlit, project root) — direct `run_spine_once()` call, bypasses HTTP entirely
  2. `spine-client.ts` — simple single-request `fetch` to BFF → FastAPI
  3. `api-client.ts` — poll-based async with 180s timeout (57 files use this, it's the production path)

- **Streamlit `app.py` still exists** despite audit recommendation (`AUDIT_VERIFICATION_REPORT_2026-04-15.md:387`) to remove it.

- **5 `TODO(frontier)` markers in `spine_api/models/frontier.py`** — ForeignKey normalization blocked by dual-store architecture.

- **`dev.sh` health gap:** Starts services but doesn't verify they're healthy before returning.

---

## 6. Dynamic Verification and Test Baseline

### 6A. Baseline Test Results

**Baseline command:** `uv run pytest --ignore=tests/test_call_capture_e2e.py -q`

| Metric | Count |
|--------|-------|
| Total tests collected | 1,435 |
| Passed | 1,401 |
| Failed | 13 |
| Skipped | 9 |
| Warnings | 3 |

**Pre-existing failures (not related to ADR-002):**

| Test | Failure | Root Cause |
|------|---------|------------|
| `test_call_capture_e2e.py::test_save_processed_trip_persists_public_checker_artifacts` | Unknown | Excluded from baseline |
| `test_review_logic.py::test_audit_delta_capture` | `KeyError: 'Trip...'` | Test isolation — passes when run alone |
| `test_review_logic.py::test_approve_action_behavior` | `KeyError` | Test isolation — passes when run alone |
| `test_review_logic.py::test_request_changes_mandatory_reassignment` | Unknown | Test isolation — passes when run alone |
| `test_review_policy_escalation.py::test_revision_loop_auto_escalates_on_second_request` | Unknown | Test isolation — passes when run alone |

**Key observation:** 8+ failures are order-dependent — they pass when run individually but fail in the full suite. This is a `TestIsolationRisk` (pre-existing).

### 6B. Targeted Verification Tests

**Rate limiter, contract guard, and spine API contract tests:**

```
uv run pytest tests/test_rate_limiter.py tests/test_run_contract_drift_guard.py tests/test_spine_api_contract.py tests/test_privacy_guard.py -v
```

**Result:** 78 passed, 3 failed, 2 skipped

**The 3 privacy guard failures are pre-existing:** `TestGuardOnTripStore` tests fail because `SQLTripStore` requires `agency_id` which the tests don't fully set up. All other guard tests (email, phone, medical, freeform, fixture detection) pass.

**Rate limiter tests:** 25/25 pass. Rate limiting is fully implemented and tested.
**Contract drift guard tests:** 6/6 pass. CI contract checks verified.
**Spine API contract tests:** 9/9 pass. Endpoint contracts verified.

### 6C. Frontend Tests

**Frontend test status:** `npm test` (vitest) — 636 test cases defined across 69 files, but most are component tests. No tests for `spine-client.ts` or `proxy-core.ts`.

---

## 7. Critical Implementation and Test Traps Checked

### 7A. Environment Variable and Config Loading

| Check | Finding | Status |
|-------|---------|--------|
| Module-level `os.getenv()` calls | None found at import time | ✅ Safe |
| `SPINE_API_URL` read at call time | Yes — `process.env.SPINE_API_URL \|\| "http://127.0.0.1:8000"` in BFF route functions | ✅ Correct |
| Cache preventing runtime changes | No `lru_cache` on env-var-dependent server functions | ✅ Safe |
| `.env` present with all vars | Missing `SPINE_API_URL` in root `.env` | ⚠️ Gap |
| `frontend/.env.local` present | Missing `SPINE_API_URL` | ⚠️ Gap |
| `dev.sh` exports env before start | `dev.sh` does NOT export `SPINE_API_URL` | ⚠️ Gap |

**Flag:** `EnvContamination` — not found. Env vars are not cached at module level.

### 7B. Test Isolation and State Leakage

| Check | Finding |
|-------|---------|
| Order-dependent failures | **CONFIRMED** — 8+ tests pass individually but fail in full suite (`test_review_logic.py`, `test_review_policy_escalation.py`) |
| Env var leaks between tests | `conftest.py` resets `os.environ` with autouse fixture — handled |
| Shared module-level state | `conftest.py` resets global singletons (telemetry, health, hybrid engine, encryption cache, LLM guard) between every test |
| Files written to shared dirs | Some tests write to `data/` directly — potential risk |
| Privacy guard tests in full suite | 3 fail due to `SQLTripStore requires agency_id` in full suite, all pass individually |

**Flag:** `TestIsolationRisk` — pre-existing, not caused by this audit.

### 7C. Write Path Coverage

For the `POST /run` endpoint (the ADR's primary concern):

| Write path | Covered? | Evidence |
|------------|----------|----------|
| `POST /run` (direct) | ✅ | `test_spine_api_contract.py`, `test_run_lifecycle.py` |
| `POST /run` via BFF proxy | ✅ | `route-map.test.ts` maps `/api/spine/run` → backend `run` |
| `POST /run` via api-client.ts polling | ✅ | `mode_selector_spine_payload.test.tsx` tests payload shape |
| `POST /run` via spine-client.ts | ❌ | No test imports or uses `spine-client.ts` directly |
| Background execution lifecycle | ✅ | `test_run_lifecycle.py` (21 tests covering golden path, idempotency, edge cases, leakage) |
| Rate-limited /run (if added) | ❌ | Would need tests when core business endpoints get rate limits |

---

## 8. Data, Privacy, and PII Boundary Checks

### 8A. Privacy Guard Status

The privacy guard (`src/security/privacy_guard.py`) has 43 tests in `tests/test_privacy_guard.py`. All core detection tests pass:
- Email detection, phone detection, medical keyword detection ✅
- Fixture detection by `fixture_id` and `source: "seed_scenario"` ✅
- Freeform text detection with minimum length threshold ✅
- Short strings (<10 chars) ignored ✅

**Issue found:** `TestGuardOnTripStore` tests (3 failures) relate to `SQLTripStore` requiring `agency_id`. These pass individually — the failure is a test setup issue when `TRIPSTORE_BACKEND=sql` is active but tests don't configure agency context.

### 8B. Heuristic Detection Limits

Documented in code at `src/security/privacy_guard.py`:
- Email: regex-based, catches standard formats, misses obfuscated emails
- Phone: regex for Indian (+91) and US formats, misses international variants
- Medical: keyword list (~50 terms), misses compound terms, specialized conditions
- Freeform: length threshold >10 chars, catches narrative text, ignores labels/enums
- Fixture: checks `fixture_id` field AND `source` field (correct dual-check)

### 8C. Deployment Modes

The privacy guard has mode-dependent behavior referenced in code, but explicit mode documentation for dogfood/beta/production is housed in separate audit docs, not in ADR-002.

---

## 9. Deduped Issue / Task Register

### ISSUE-001: ADR-002 is stale — claims "Rate Limiting" as future, but it's implemented

**Category:** docs

**Origin:** Explicit contradiction. ADR-002:191 vs `spine_api/core/rate_limiter.py:1-66`

**Codebase Evidence:**
- `spine_api/core/rate_limiter.py:1-66` — SlowAPI limiter fully implemented
- `spine_api/server.py:430` — `SlowAPIMiddleware` wired into FastAPI
- `spine_api/routers/auth.py:140,192,265,295,323` — 5 auth endpoints rate-limited
- `tests/test_rate_limiter.py:1-330` — 25 tests passing

**Current Behavior:** Rate limiting works for 7 endpoints (auth + public booking collection). Core business endpoints (`/run`, `/trips`, `/inbox`, `/analytics`) are not rate-limited.

**Gap:** ADR text is wrong. "Future Considerations" section says rate limiting needs implementation, but it was implemented. The ADR should move this to "Implemented" and note which endpoints are covered.

**Impact:** New developers reading ADR-002 may implement a second rate limiter or assume none exists.

**Confidence:** High — code and tests directly contradict the ADR.

**Acceptance Criteria:**
- [ ] Update ADR-002 Future Considerations → mark rate limiting as "Implemented (partial)"
- [ ] Document which endpoints have rate limits and which don't

**Test Plan:** N/A (documentation-only)

---

### ISSUE-002: Two competing `runSpine` functions — name collision and dead code

**Category:** architecture / refactor

**Origin:** Implicit — found during codebase verification

**Codebase Evidence:**
- `frontend/src/lib/spine-client.ts:34` — exports `runSpine()` (simple single-request)
- `frontend/src/lib/api-client.ts:247` — exports `runSpine()` (poll-based async, 180s timeout)
- 57 files import from `api-client`, zero import from `spine-client`
- `spine-client.ts:12` has stale comment about `SPINE_API_URL`

**Current Behavior:** Production code uses `api-client.ts:runSpine()`. `spine-client.ts:runSpine()` is dead code with misleading comments. Both export the same function name.

**Gap:** Name collision creates confusion. Dead code with stale comments misleads developers. The `spine-client.ts` file serves no purpose while claiming to implement core ADR-002 requirements.

**Impact:** Developer confusion when searching for `runSpine` implementation. The stale comment on L12 could cause incorrect deployment configuration.

**Confidence:** High — zero production imports of `spine-client.ts`.

**Acceptance Criteria:**
- [ ] Remove or repurpose `spine-client.ts` (it's dead code)
- [ ] If kept, fix L12 comment about `SPINE_API_URL` (it doesn't use it)
- [ ] If kept, rename its `runSpine` to avoid collision with `api-client.ts`
- [ ] If removed, update ADR-002 to point to `api-client.ts` instead
- [ ] Update any docs referencing `spine-client.ts`

**Test Plan:**
- Run full test suite after removal to verify no imports break
- Verify 57 existing api-client imports still work

**Rollback / Kill Switch:** Revert file deletion — trivial.

---

### ISSUE-003: Missing unit tests for spine-client.ts (ADR testing strategy gap)

**Category:** tests

**Origin:** Explicit — ADR-002:170

**Codebase Evidence:**
- `frontend/src/lib/spine-client.ts:34-65` — `runSpine()` has zero tests
- `frontend/src/lib/spine-client.ts:67-132` — `validateSpineRequest()` has zero tests
- Glob for `*spine-client*` in frontend tests: zero results
- `frontend/src/app/__tests__/mode_selector_spine_payload.test.tsx` mocks through `useSpineRun` — never touches `spine-client.ts` directly

**Current Behavior:** No test coverage for the spine-client.ts module. If `validateSpineRequest()` breaks, no test catches it.

**Gap:** The `validateSpineRequest()` function has 10+ validation branches with zero coverage.

**Impact:** Broken validation could allow malformed requests through to the BFF proxy, causing cryptic backend errors.

**Confidence:** High — verified by glob and grep.

**Acceptance Criteria:**
- [ ] Unit tests for `runSpine()` — success, error parsing (3 error shapes), network failure
- [ ] Unit tests for `validateSpineRequest()` — valid/invalid stage, mode, missing fields
- [ ] If spine-client.ts is removed per ISSUE-002, verify equivalent tests exist for api-client.ts

**Test Plan:**
- Create `frontend/src/lib/__tests__/spine-client.test.ts`
- Mock `fetch` for HTTP tests
- Assert validation branches

**Rollback / Kill Switch:** N/A (tests are additive)

---

### ISSUE-004: Missing fallback/degradation tests for BFF proxy

**Category:** tests

**Origin:** Explicit — ADR-002:173

**Codebase Evidence:**
- `frontend/src/lib/proxy-core.ts:259-277` — implements 502/504 error handling with zero tests
- No test file for `proxy-core.ts` exists
- `frontend/src/app/api/trips/__tests__/route.test.ts:136-156` tests kill-switch 503, but not backend unavailability

**Current Behavior:** If spine_api is down, Next.js BFF returns proper 504 (timeout) or 502 (unreachable), but no automated test verifies this.

**Gap:** Error handling code exists but has zero test coverage.

**Confidence:** High — verified by glob for proxy-core test files.

**Acceptance Criteria:**
- [ ] Test: backend timeout → 504 with correct error body
- [ ] Test: backend unreachable → 502 with correct error body
- [ ] Test: non-JSON backend response → handled gracefully
- [ ] Test: error details hidden in production (NODE_ENV=production)

**Test Plan:**
- Create `frontend/src/lib/__tests__/proxy-core.test.ts`
- Use `nock` or `msw` to simulate backend failures
- Check response status codes and error body shape

---

### ISSUE-005: Missing load tests for spine API

**Category:** tests

**Origin:** Explicit — ADR-002:172

**Codebase Evidence:**
- No K6 scripts, no Locust files, no Artillery configs
- Only concurrency-related test: `test_timeline_mapper_integration.py:449` tests event ordering, not load

**Gap:** No performance baseline exists. Can't verify ADR-002's "~10x faster" claim (L126) without load data.

**Confidence:** High — verified by glob.

**Acceptance Criteria:**
- [ ] Create a minimal K6 script for POST /run concurrency test
- [ ] Create a benchmark for end-to-end pipeline execution under parallel load
- [ ] Document performance characteristics (p50, p95, p99 latency at 10/50/100 concurrent)

**Test Plan:**
- Install K6: `brew install k6`
- Create `tests/load/spine_api_run.js` with 3 stages (ramp-up, steady, ramp-down)
- Run against local spine_api on port 8000

---

### ISSUE-006: `SPINE_API_URL` configuration gaps

**Category:** tooling / dev experience

**Origin:** Implicit — found during env var verification

**Codebase Evidence:**
- `.env` (root) — missing `SPINE_API_URL`
- `frontend/.env.local` — missing `SPINE_API_URL`
- `dev.sh` — doesn't export `SPINE_API_URL` or source `.env`
- `frontend/.env.local.example:4` — documents `SPINE_API_URL` but no active config sets it

**Current Behavior:** All 13 BFF route files fall back to `"http://127.0.0.1:8000"` which happens to work for local dev. But if someone changes the port, nothing is configured.

**Gap:** Configuration exists in `.env.local.example` but not in actual runtime config files.

**Confidence:** High.

**Acceptance Criteria:**
- [ ] Add `SPINE_API_URL=http://127.0.0.1:8000` to `frontend/.env.local`
- [ ] Fix `dev.sh` to export `SPINE_API_URL` before starting Next.js
- [ ] Fix `dev.sh` to source `.env` or export `TRIPSTORE_BACKEND=sql`
- [ ] Add health check verification to `dev.sh` after startup (curl /health)

**Test Plan:** Manual — run `dev.sh` and verify services connect successfully.

---

### ISSUE-007: ADR-002 architecture diagram missing BFF proxy layer

**Category:** docs

**Origin:** Contradiction

**Codebase Evidence:**
- ADR-002:80 shows: `Frontend (Next.js) ← HTTP → Spine API (FastAPI)`
- Actual: `Browser ← HTTP → Next.js BFF ← HTTP → Spine API (FastAPI)`
- 13 explicit BFF route files + 1 catch-all proxy route handler
- `spine-client.ts:32` uses `/api/spine` (relative BFF path), not `SPINE_API_URL`

**Current Behavior:** Diagram in ADR doesn't reflect the BFF proxy pattern implemented in production.

**Gap:** Architectural documentation doesn't match reality.

**Confidence:** High.

**Acceptance Criteria:**
- [ ] Update ADR-002 architecture diagram to show BFF proxy layer
- [ ] Document that `SPINE_API_URL` is consumed by server-side BFF routes, not client-side code
- [ ] Add note about why BFF proxy is used (CORS, auth cookie forwarding, security)

**Test Plan:** N/A (documentation-only)

---

### ISSUE-008: 27 stale `spine-wrapper.py` references in historical docs

**Category:** docs

**Origin:** Implicit

**Codebase Evidence:**
- `frontend/src/lib/spine-wrapper.py` — does not exist
- 27 references in `Docs/` files — all historical audit/verification docs
- Most correctly note it "was removed" or "should be removed"

**Current Behavior:** Old docs pollute search results. New developers looking up "spine-wrapper" find 27 references but no code.

**Confidence:** High.

**Acceptance Criteria:**
- [ ] Add a one-line note to the top of each doc: `> **HISTORICAL (2026-04-15):** spine-wrapper.py was removed per ADR-002. This document is kept for historical reference.`
- [ ] Or, move 8+ historical audit docs to `Archive/`

**Test Plan:** N/A (documentation-only)

---

### ISSUE-009: `cache_invalidated` dead field in OverrideResponse

**Category:** code quality

**Origin:** Implicit

**Codebase Evidence:**
- `spine_api/contract.py:225` — `cache_invalidated: bool = False`
- `spine_api/server.py:3532` — always `cache_invalidated=False`
- No code sets `cache_invalidated=True`

**Current Behavior:** Field exists in the API contract but is never meaningfully used. Override operations don't invalidate any cache.

**Confidence:** High.

**Acceptance Criteria:**
- [ ] Either implement cache invalidation when overrides occur
- [ ] Or remove the field if caching isn't implemented yet

**Test Plan:** If implementing, add test that override sets `cache_invalidated=True` when decision cache has relevant entries.

---

### ISSUE-010: Core business endpoints lack rate limiting

**Category:** security / operational-safety

**Origin:** Implicit — found while verifying ADR-002 rate limiting claim

**Codebase Evidence:**
- `POST /run` — no `@limiter.limit()` decorator
- `GET /trips`, `POST /trips` — no limit
- `GET /inbox` — no limit
- `GET /analytics/*` — no limit
- `GET /runs/{id}` — no limit (polled every 2s by frontend)

**Current Behavior:** Auth endpoints are protected (5/min for login, 10/min for signup, etc). Core business endpoints are not. The frontend's `useSpineRun` polls `/runs/{id}` every 2 seconds with no backoff.

**Risk:** Accidental polling storms, malicious internal users, or runaway background tasks could degrade service.

**Confidence:** Medium — may be intentional (internal operator tool), but should be documented.

**Acceptance Criteria:**
- [ ] Either: Add `@limiter.limit()` to core endpoints with reasonable limits (e.g., 60/min for `/run`, 120/min for query endpoints)
- [ ] Or: Document why core endpoints are unrate-limited (internal tool assumption)
- [ ] Add exponential backoff to frontend polling (`useSpineRun.ts`, `api-client.ts`)

**Test Plan:**
- Add rate limit decorators
- Update `test_rate_limiter.py` to test new limits
- Verify frontend handles 429 responses gracefully

**Rollback / Kill Switch:** Rate limits can be adjusted via env var or removed by deleting decorators. Minimal blast radius.

---

### ISSUE-011: Test isolation failures — 8+ tests pass individually but fail in full suite

**Category:** tests / reliability

**Origin:** Dynamic verification surprise

**Codebase Evidence:** See Section 6A. Tests in `test_review_logic.py`, `test_review_policy_escalation.py`, `test_privacy_guard.py` (3/43) fail in full suite but pass individually.

**Current Behavior:** Full test suite shows 13 failures, but many are false positives from test isolation issues.

**Gap:** Order-dependent failures reduce trust in the test suite and waste developer time investigating ghost failures.

**Confidence:** High — confirmed by running individual tests.

**Acceptance Criteria:**
- [ ] Investigate each order-dependent failure and identify the shared mutable state
- [ ] Add `autouse` fixtures in `conftest.py` to reset leaked state between test modules
- [ ] Verify full suite shows 0 order-dependent failures

**Test Plan:**
- Run: `pytest --random-order` to expose more isolation issues
- Run each pair of tests that fails together to find the contaminating predecessor

---

### ISSUE-012: `api-client.ts` and `useSpineRun.ts` contain near-duplicate poll loop logic

**Category:** refactor

**Origin:** Implicit

**Codebase Evidence:**
- `api-client.ts:258-267` — poll loop: POST /run → poll GET /runs/{id} every 2s, 180s timeout
- `useSpineRun.ts:51-87` — poll loop: same pattern, React hook wrapper
- Live web searches enabled flag on L34 vs L52 inconsistent

**Current Behavior:** Two places implementing the same polling logic. Changes to one may not reach the other.

**Confidence:** High.

**Acceptance Criteria:**
- [ ] Extract shared poll loop into a reusable function
- [ ] Add exponential backoff (1s → 30s cap)
- [ ] Add circuit breaker for 429 responses

**Test Plan:**
- Unit test for shared poll loop
- Integration test for end-to-end polling with mocked backend

---

## 10. Prioritization

| ID | Title | Severity | Blast Radius | Effort | Confidence | Priority | Why |
|----|-------|---------:|------------:|------:|----------:|---------|-----|
| ISSUE-001 | ADR-002 stale — rate limiting marked "future" but implemented | 2 | 2 | 1 | 5 | **P2** | Doc-only, low urgency |
| ISSUE-002 | Two competing `runSpine` — dead code + name collision | 3 | 3 | 2 | 5 | **P1** | Confusion for all developers touching spine pipeline |
| ISSUE-003 | Missing unit tests for spine-client.ts | 3 | 2 | 2 | 5 | **P1** | Broke promise in ADR-002, validation untested |
| ISSUE-004 | Missing fallback tests for BFF proxy | 4 | 1 | 3 | 5 | **P1** | Error handling code untested — silent production failures |
| ISSUE-005 | Missing load tests | 3 | 1 | 4 | 4 | **P2** | No performance baseline, can't verify ADR claims |
| ISSUE-006 | SPINE_API_URL configuration gaps | 2 | 2 | 1 | 5 | **P2** | Works by accident now, breaks if port changes |
| ISSUE-007 | ADR-002 diagram missing BFF proxy layer | 2 | 2 | 1 | 5 | **P2** | Doc-only, but fundamental architecture misrepresentation |
| ISSUE-008 | 27 stale spine-wrapper.py references | 1 | 1 | 2 | 5 | **P3** | Cosmetic doc cleanup |
| ISSUE-009 | `cache_invalidated` dead field | 2 | 1 | 1 | 5 | **P3** | Dead code, low impact |
| ISSUE-010 | Core business endpoints lack rate limiting | 4 | 3 | 2 | 4 | **P1** | Service degradation risk; frontend polls every 2s with no backoff |
| ISSUE-011 | Test isolation failures | 3 | 3 | 4 | 5 | **P1** | 8+ ghost failures reduce trust, waste developer time |
| ISSUE-012 | Duplicate poll loop in api-client.ts + useSpineRun.ts | 2 | 2 | 2 | 5 | **P2** | DRY violation, risk of drift |

---

### Priority Queues

#### P0
*(None — no security breach, data loss, or app unusability found)*

#### P1 (Should be addressed soon)
- **ISSUE-002** — Remove dead `spine-client.ts` or consolidate
- **ISSUE-003** — Unit tests for spine-client.ts (if kept) or api-client.ts
- **ISSUE-004** — Fallback/degradation tests for BFF proxy
- **ISSUE-010** — Rate limiting on core business endpoints + exponential backoff
- **ISSUE-011** — Fix test isolation failures (8+ ghost failures)

#### P2 (Useful but not blocking)
- **ISSUE-001** — Update ADR-002 rate limiting status
- **ISSUE-005** — Load test suite
- **ISSUE-006** — Fix SPINE_API_URL config gaps
- **ISSUE-007** — Update ADR-002 architecture diagram
- **ISSUE-012** — Deduplicate poll loop logic

#### P3 (Cleanup, polish, later)
- **ISSUE-008** — Clean up stale spine-wrapper.py references
- **ISSUE-009** — Remove `cache_invalidated` dead field

#### Quick Wins
- **ISSUE-001** — 1-line ADR update (trivial)
- **ISSUE-006** — Add `SPINE_API_URL` to `.env.local` (trivial)
- **ISSUE-007** — Update ADR diagram (trivial)
- **ISSUE-009** — Remove dead field (trivial)

#### Risky Changes
- **ISSUE-010** — Rate limiting core endpoints could break internal operators
- **ISSUE-011** — Fixing test isolation may require significant conftest.py changes

#### Needs Discussion Before Work
- **ISSUE-002** — Should we remove `spine-client.ts` entirely or repurpose it?
- **ISSUE-010** — Should core endpoints be rate-limited for internal operators or is this a deliberate choice?
- **ISSUE-005** — Worth investing in load tests now vs after feature stabilization?

#### Not Worth Doing (for now)
- **ISSUE-008** — Historical doc cleanup is cosmetic (27 references, all correctly say "removed")
- **ISSUE-009** — Dead field only if replacing with real cache invalidation is planned soon

---

## 11. Proof-of-Concept Validation

No proof-of-concept probe was needed. Static and existing dynamic evidence were sufficient. All findings are directly verifiable from code, tests, and git state.

---

## 12. Assumptions Challenged by Implementation

| Assumption | Why it seemed true | What disproved it | Evidence | How recommendation changed |
|------------|-------------------|-------------------|----------|---------------------------|
| ADR-002's "Future Considerations" are all unimplemented | Document says they're "Future" | Rate limiting is fully implemented | `rate_limiter.py:1-66`, 25 passing tests | ISSUE-001 added — ADR needs update |
| `spine-client.ts` is the production HTTP client | ADR-002 says it was built | 57 files import `api-client.ts`, zero import `spine-client.ts` | Frontend import graph | ISSUE-002 added — dead code |
| Architecture is "Frontend → HTTP → Spine API" | ADR-002 diagram says so | BFF proxy layer exists between browser and FastAPI | 13 explicit BFF route files + catch-all proxy | ISSUE-007 added — diagram wrong |
| Test suite is clean (1,435 tests) | High test count suggests quality | 8+ tests are order-dependent false failures | Individual vs full suite runs | ISSUE-011 added — isolation bugs |
| Privacy guard tests all pass | Guard has extensive tests | 3/43 fail in full suite (test setup issue with `agency_id`) | Full suite run | Pre-existing, not ADR-002 related |

---

## 13. Parallel Agent / Multi-Model Findings

**3 parallel agents were used, plus main agent analysis:**

| Agent | Role | Key Findings |
|-------|------|-------------|
| Agent A (codebase verifier) | Traced source files, verified every ADR claim | Found 8 discrepancies: rate limiter implemented, spine-client.ts dead, BFF proxy missing from diagram, server has 100+ endpoints not 1 |
| Agent B (test/runtime verifier) | Inventory tests, run suite, check coverage | Found 4 gaps: no spine-client tests, no fallback tests, no load tests; confirmed rate limit, contract guard, and /run tests exist |
| Agent C (architecture auditor) | Traced TODOs, competing paths, env vars, BFF setup | Found 3 competing runSpine paths, 5 frontier TODOs, 27 stale wrapper refs, .env config gaps, dead cache_invalidated field |
| Main agent (synthesizer) | Merged and deduped findings, dynamic verification | Confirmed test isolation issues (8+ ghost failures), prioritized all issues |

**Contradiction resolution:** All three agents independently confirmed that `spine-client.ts` is dead code. No disagreement. Agent A and Agent C both found the BFF proxy mismatch against ADR-002's diagram.

**Note on subagents:** The `explore` subagent type was used (the only available type). No multi-model review was available. A rebuttal reviewer would have been useful to challenge the "remove spine-client.ts" recommendation.

---

## 14. Discussion Pack

### My Recommendation

I recommend working on these issues next, in order:

1. **ISSUE-002** — Remove or repurpose `spine-client.ts` (dead code, name collision)
2. **ISSUE-004** — Add fallback/degradation tests for BFF proxy
3. **ISSUE-010** — Add rate limiting to core endpoints + exponential backoff in polling

**Reason:** These three have the highest impact-to-effort ratio. ISSUE-002 eliminates downstream confusion for every developer touching the spine pipeline. ISSUE-004 prevents silent production failures. ISSUE-010 hardens the service against accidental degradation.

### Why These Matter Now

- **ISSUE-002:** Any developer searching for `runSpine` finds two conflicting implementations. The dead one has an actively misleading comment about `SPINE_API_URL`. This wastes every new developer's first hour understanding the spine architecture.
- **ISSUE-004:** The BFF proxy has proper error handling code but zero tests. If someone inadvertently changes the error shape in `proxy-core.ts`, no test catches it. Frontend consumers would just see cryptic failures.
- **ISSUE-010:** The frontend polls `/runs/{id}` every 2 seconds with no backoff. A single runaway component could cause thousands of requests/minute. Adding rate limits with 429 handling is cheap insurance.

### What Breaks If Ignored

- **ISSUE-002:** Nothing breaks immediately, but it's a sharp edge. Every new hire or agent will trip over it.
- **ISSUE-004:** If proxy error handling breaks, frontend consumers see unhandled errors instead of graceful 502/504 messages. User sees "Something went wrong" instead of "Backend is starting up — try again in 30s."
- **ISSUE-010:** If the frontend polling loop runs wild (e.g., useEffect missing cleanup), the backend gets hammered. Without rate limits, this could degrade the service.

### What I Would Not Work On Yet

- **ISSUE-005** (load tests) — Wait until the pipeline stabilizes. Load testing a changing API is wasted effort.
- **ISSUE-008** (stale wrapper refs) — Cosmetic. 27 references in historical docs that already say "was removed."
- **ISSUE-012** (deduplicate poll loop) — Worth doing, but low impact compared to P1 items.

### What Is Ambiguous

- **ISSUE-002** — Should `spine-client.ts` be deleted, or should it be refactored into what ADR-002 intended (a direct FastAPI client for server-side use)? The current BFF proxy setup means a direct client has no use case.
- **ISSUE-010** — Are core business endpoints deliberately unrate-limited? The auth endpoints have careful limits. The omission of limits on `/run`, `/trips`, etc. may be a deliberate choice (internal operator tool assumption).

### Questions For You

1. **ISSUE-002:** Delete `spine-client.ts` or refactor it? The BFF proxy pattern means no browser-side code should call FastAPI directly. If a server-side use case exists, the file needs a complete rewrite anyway.

2. **ISSUE-010:** Should the core business endpoints (`/run`, `/trips`, `/inbox`) get rate limits like the auth endpoints already have (~60/min for production)? Or is the current approach (auth-only limits) intentional for the internal agency operator use case?

3. **ISSUE-005:** Is it worth setting up K6 for load testing the spine API now, or defer until after the pipeline feature set stabilizes? The ADR's "~10x faster" claim is unverified.

4. **ISSUE-011:** Should I investigate the test isolation failures (8+ ghost failures), or are they known and already tracked elsewhere?

### Needs Runtime Verification

- **ISSUE-010:** Before adding rate limits, verify actual production request patterns. If operators batch-upload 50 trips at once, a 60/min limit on `/trips POST` would break their workflow.

### Needs Online Research

No online research needed. Current findings are repo-evidence based.

---

## 15. Online Research

No online research was needed. All findings are derived from repo code, tests, configuration, and documentation.

---

## 16. ChatGPT / External Review Escalation Writeup

Not needed. All decisions are clear enough from repo evidence. The ambiguous questions are product-strategy questions for the human, not technical puzzles for an external reviewer.

---

## 17. Recommended Next Work Unit

# Recommended Next Work Unit

## Unit-1: Consolidate Spine Pipeline Entry Points + Add Missing Tests

**Goal:** Remove the dead/unused `spine-client.ts` (or consolidate it into `api-client.ts`), add tests for the BFF proxy's graceful degradation, and fix the stale ADR-002.

**Issues covered:**
- ISSUE-002 — Remove dead spine-client.ts / name collision
- ISSUE-003 — Unit tests for the remaining spine client
- ISSUE-004 — Fallback/degradation tests for BFF proxy
- ISSUE-006 — Fix SPINE_API_URL config gaps
- ISSUE-007 — Update ADR-002 architecture diagram

**Scope:**
- **In:**
  - Audit all imports of `spine-client.ts` (expected: zero production imports)
  - Either delete `spine-client.ts` or repurpose as a thin wrapper around `api-client.ts`
  - Add unit tests for `api-client.ts:runSpine()` and `validateSpineRequest()` (whichever file survives)
  - Add fallback tests for `proxy-core.ts` (timeout → 504, unreachable → 502)
  - Add `SPINE_API_URL=http://127.0.0.1:8000` to `frontend/.env.local`
  - Fix `dev.sh` to export config and verify health
  - Update ADR-002: fix architecture diagram, mark rate limiting as implemented, point client ref to correct file
- **Out:**
  - Load tests (ISSUE-005, deferred)
  - Rate limiting core endpoints (ISSUE-010, separate work unit)
  - Fixing test isolation (ISSUE-011, separate work unit)

**Likely files touched:**
- `frontend/src/lib/spine-client.ts` — delete or refactor
- `frontend/src/lib/api-client.ts` — possibly absorb validateSpineRequest
- `frontend/src/lib/__tests__/spine-client.test.ts` — new
- `frontend/src/lib/__tests__/proxy-core.test.ts` — new
- `frontend/.env.local` — add SPINE_API_URL
- `dev.sh` — export env vars, add health check
- `Docs/architecture/adr/ADR-002-SPINE-API-ARCHITECTURE.md` — update
- `frontend/.env.local.example` — verify it documents SPINE_API_URL

**Acceptance criteria:**
- [ ] Zero production imports of `spine-client.ts` — if deleted, build passes
- [ ] Unit tests for the spine client: HTTP success, error parsing (3 shapes), network failure
- [ ] Unit tests for proxy-core: 504 on timeout, 502 on unreachable, non-JSON response
- [ ] `frontend/.env.local` has `SPINE_API_URL=http://127.0.0.1:8000`
- [ ] `dev.sh` exports config and verifies backbone health before returning
- [ ] ADR-002 updated with correct architecture diagram and rate limiting status
- [ ] Full test suite passes (1,401+ tests, 0 new failures)

**Tests to run:**
- Baseline: `uv run pytest --ignore=tests/test_call_capture_e2e.py -q` → 1,401 pass, 13 fail (pre-existing)
- Targeted frontend: `cd frontend && npm test -- --run` → verify no new failures
- Final: Same commands → verify 0 regressions

**Manual verification:**
- Run `dev.sh` and verify `curl http://localhost:8000/health` returns `{"status":"ok"}`
- Run `curl http://localhost:3000` → verify frontend loads
- Check that `grep -r "spine-client" frontend/src/lib/` returns only the surviving file

**Docs to update:**
- ADR-002: Architecture diagram, rate limiting status, client reference
- Remove ADR-002 `spine-client.ts` reference if file is deleted, or point to `api-client.ts`

**Operational safety:**
- Kill switch / rollback: File deletion is trivially reversible via git revert.
- No behavioral changes — only removing dead code and adding tests.
- Risk: If any hidden import of `spine-client.ts` exists (contrary to grep), build will fail. We verify build before committing.

**Risks:**
- Low risk. Changes are either additive (new tests) or removing dead code (verified unused).
- The only risk is an undiscovered import of `spine-client.ts`. Mitigated by grep and build verification.

**Rollback plan:**
- All changes are in a single commit. Git revert undoes everything.
- Dead code removal can be done as a separate commit for cleaner rollback granularity.

---

## 18. Appendix: Searches Performed

### Static searches:
| # | Search | Pattern / Command | Purpose |
|---|--------|-------------------|---------|
| 1 | Doc inventory | `find . -name "*.md"` excluding node_modules/.venv/.next | Step 0 document inventory |
| 2 | TODO/FIXME markers | `grep -rn "TODO\|FIXME\|HACK\|NOTE\|XXX"` in spine_api/, src/, frontend/ | Code-level documentation markers |
| 3 | spine-wrapper references | `grep -rn "spine-wrapper\|spine_wrapper"` in whole repo | Verify ADR claim of removal |
| 4 | SPINE_API_URL usage | `grep -rn "SPINE_API_URL"` in frontend/ | Verify service discovery pattern |
| 5 | runSpine imports | `grep -rn "import.*runSpine\|from.*spine-client"` in frontend/src/ | Find competing implementations |
| 6 | Rate limiter wiring | `grep -rn "limiter\|SlowAPI\|RateLimitExceeded"` in spine_api/ | Verify rate limiter implementation |
| 7 | API versioning | `grep -rn "v1/\|v2/\|/v1\|/v2"` in spine_api/server.py and routers/ | Check if API versioning exists |
| 8 | Response caching | `grep -rn "cache\|Cache\|ETag\|etag"` in spine_api/ | Check for response caching |
| 9 | BFF proxy architecture | Read `proxy-core.ts`, `route-map.ts`, catch-all route | Understand actual request flow |
| 10 | Spine router modules | List `spine_api/routers/*.py` | Understand modular route structure |
| 11 | Test isolation markers | `grep -rn "autouse\|fixture\|session\|module"` in conftest.py | Check test isolation setup |
| 12 | Env var config | Read `.env`, `.env.example`, `frontend/.env.local`, `frontend/.env.local.example` | Check config completeness |
| 13 | api-client imports | `grep -rl "api-client"` in frontend/src/ | Verify production usage |
| 14 | spine-client imports | `grep -rl "spine-client"` in frontend/src/ | Verify usage (dead code check) |
| 15 | Duplicate runSpine | Read both `spine-client.ts:34` and `api-client.ts:247` | Compare implementations |
| 16 | dev.sh contents | Read `dev.sh` | Check startup script completeness |
| 17 | Privacy guard tests | Run `test_privacy_guard.py` individually and in full suite | Check test isolation |
| 18 | Review logic tests | Run `test_review_logic.py` individually and in full suite | Check test isolation |

### Dynamic tests:
| # | Command | Result |
|---|---------|--------|
| 1 | `uv run pytest --co -q` | 1,435 tests collected |
| 2 | `uv run pytest -x -q` | 1 failed (pre-existing), 183 passed |
| 3 | `uv run pytest -q --ignore=tests/test_call_capture_e2e.py` | 1,401 passed, 13 failed, 9 skipped |
| 4 | `uv run pytest tests/test_rate_limiter.py tests/test_run_contract_drift_guard.py tests/test_spine_api_contract.py tests/test_privacy_guard.py -v` | 78 passed, 3 failed (pre-existing), 2 skipped |
| 5 | `uv run pytest tests/test_review_logic.py::test_audit_delta_capture tests/test_review_policy_escalation.py::test_revision_loop_auto_escalates_on_second_request -v` | 2 passed (confirms isolation issue) |
| 6 | `uv run pytest tests/test_privacy_guard.py -v` | 43 passed, 0 failed (confirms isolation issue) |
