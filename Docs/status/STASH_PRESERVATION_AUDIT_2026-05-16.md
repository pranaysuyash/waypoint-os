# Stash Preservation Audit — 2026-05-16

**Purpose:** Read-only audit of two old stashes before drop decision.  
**Bias:** Nitpick toward preserving anything useful.

---

## stash@{0}

**Label:** `WIP on master: 533d39a Add comprehensive test coverage for various components`  
**Base commit date:** 2026-05-04  
**Scope:** 39 files, 1136 insertions, 483 deletions  
**Broad purpose:** In-progress work session that touched analytics refactor, agent runtime, privacy guard reordering, persistence hardening, run_ledger idempotency, and test suite fixes from a SQL backend migration.

### Potentially Valuable Items

| File | Item | In master? | Recommendation | Reason |
|---|---|---|---|---|
| `src/security/privacy_guard.py` | Email/phone check ordered BEFORE known-fixture bypass | **NO — REGRESSED** | **Preserve as security note** | Stash explicitly checked email/phone first (always blocked even for known fixtures). Master inverted the order: known fixtures return None immediately, skipping email/phone checks. Stash comment: "Always check for unambiguous PII patterns — these should be blocked even if the trip is a known fixture, because someone may be updating a fixture with real contact info." This is a real security regression in master. |
| `tests/test_run_state_unit.py` | `test_double_complete_is_idempotent` | **NO** | **Preserve as backlog note** | Stash had idempotent terminal re-entry (complete/fail on already-terminal run is a no-op). Master removed early-return guards and now `assert_can_transition` raises on terminal re-entry. Stash docstring: "idempotent for watchdog safety" — watchdog may retry complete/fail. If it does, master now raises. Worth noting the risk. |
| `tests/test_run_state_unit.py` | `test_fail_after_complete_is_idempotent` | **NO** | **Preserve as backlog note** | Same — tests a behavioral contract deliberately removed in master. |
| `tests/test_run_state_unit.py` | `test_complete_after_fail_is_idempotent` | **NO** | **Preserve as backlog note** | Same. |
| `tests/test_run_state_unit.py` | `test_block_after_fail_is_idempotent` | **NO** | **Preserve as backlog note** | Same. |
| `Docs/status/AUDIT_DEBT_BACKLOG_2026-05-04.md` | `api-client.ts` IIFE env check issue | Unclear | **Check and merge** | Stash adds: "IIFE at line 831 throws if `NEXT_PUBLIC_SPINE_API_URL` is unset when `window` exists. Manifests as test crashes from env var contamination." May be fixed; may not. Worth checking. |
| `Docs/status/AUDIT_DEBT_BACKLOG_2026-05-04.md` | `_agent_work_coordinator` deferred env var issue | Partially — we just fixed this | **Superseded by runtime deferral refactor** | We committed `964ae82` which deferred the bundle. This stash item is now resolved. |
| `Docs/MASTER_GAP_REGISTER_2026-04-16.md` | 2026-05-04 test-fix history (14 pre-existing failures, root causes, fixes) | Partially — fixes landed | **Already documented in git history** | Useful as historical record but the fixes are in master. Low priority. |
| `src/analytics/metrics.py` | `_extract_budget_value`, `_trip_duration_days` helpers | NO — replaced | **Superseded** | Master replaced with `_dict_payload`/`_trip_analytics` helpers and inline budget logic. `_trip_duration_days` measured `updated_at - created_at` which is processing time, not itinerary duration. Master moved to velocity-based calculation. |
| `src/agents/runtime.py` | `_normalize_list` as instance method | NO — refactored | **Superseded** | Master promotes to module-level function, used by multiple classes. Better design. |
| `spine_api/run_ledger.py` | Idempotent early-returns in complete/fail/block | **NO — deliberately removed** | **Preserved as risk note below** | Behavioral contract change. See security/risk items. |
| All other test files | 25+ test files | Master has MORE tests | **Superseded** | Master's test suite is strictly larger and more current. |
| All generated types | `spine-api.ts`, `spine_api.ts` | Master has more fields | **Superseded** | Generated files. Master is ahead. |
| `AGENTS.md` | Old 5-location skill list | NO — master has 8 locations | **Superseded** | Master version is correct and more complete. |
| `spine_api/core/security.py` | Minor change | Master is ahead | **Superseded** | |
| `spine_api/persistence.py` | Old `_safe_filename` without UUID prefix | Master has path-traversal hardening | **Superseded** | Master is strictly more secure. |
| `frontend/src/lib/bff-trip-adapters.ts` | Old adapter code | Master stripped same code | **Superseded** | |
| `frontend/src/app/(agency)/insights/page.tsx` | Older insights page | Master has updated version | **Superseded** | |

### Delete confidence for stash@{0}
- **Safe to drop:** Yes, **after** preserving two security/risk notes below
- **Confidence:** High
- **Things checked:** privacy_guard check ordering, run_ledger idempotency contract, 4 missing tests, analytics helpers, agents/runtime refactor direction, persistence hardening, test suite sizes, generated types, AGENTS.md versions

---

## stash@{1}

**Label:** `WIP on master: pre-design-review-wip` (base: `8047d04`, 2026-04-25)  
**Scope:** 4 files, 18 insertions, 13 deletions  
**Broad purpose:** Pre-design-review WIP — route-map and BFF proxy in transition, one hybrid_engine simplification, one server.py import addition.

### Potentially Valuable Items

| File | Item | In master? | Recommendation | Reason |
|---|---|---|---|---|
| `frontend/src/lib/route-map.ts` | Array-based `BACKEND_ROUTE_ENTRIES` with explicit route list | **NO — replaced** | **Superseded** | Master has fully rewritten route-map with `resolveBackendRoute` returning `{backendPath, timeoutMs}`. Master is strictly more capable (timeout per route). The old route entries are superseded by the current registry. |
| `frontend/src/app/api/[...path]/route.ts` | Older `resolveBackendPath` call with fallback passthrough and console.warn | **NO — superseded** | **Superseded** | Master enforces 404 for unknown routes. Master is strictly more secure. Stash comment noted "Before production launch, tighten by removing fallback passthrough" — master already did this. |
| `src/decision/hybrid_engine.py` | No `_is_llm_guard_enabled`, no `lru_cache`, no `@dataclass(slots=True)`, no token counting | **NO — older** | **Superseded** | Master has all additions. Stash is an older state. |
| `spine_api/server.py` | Single import addition | **Superseded** | **Superseded** | Master is far ahead. |

### Delete confidence for stash@{1}
- **Safe to drop:** Yes — immediately, no preservation needed
- **Confidence:** High
- **Things checked:** route-map architecture direction, BFF proxy security (passthrough vs 404), hybrid_engine feature additions

---

## Resolution

### 1. Privacy guard ordering regression — FIXED (2026-05-16)

**Status:** Fixed in `src/security/privacy_guard.py`  
**Commit:** see fix commit below  
**What changed:** Email/phone in `raw_input` and `raw_note` fields are now checked unconditionally before the known-fixture bypass. Structured output fields (`traveler_bundle`, `extracted`, `analytics`) are excluded from the pre-check — they are processed results, not raw user input. Full scan applies to non-fixture trips as before.  
**Security guarantee:** A known fixture whose `raw_input` or `raw_note` contains a real email or phone number will now be blocked, even if `_is_known_fixture()` returns True.  
**Tests added:** `TestKnownFixtureWithPII` (4 tests) covering: fixture with real email blocked, fixture with real phone blocked, fixture without PII passes, seed_scenario with real email blocked.  
**Test suite after fix:** 2248 passed, 7 skipped. Only 2 pre-existing snapshot failures (route/openapi parity — unrelated).

### 2. RunLedger idempotency removal — LOGGED AS BACKLOG ITEM

**Status:** Not changed in code. Documented below for follow-up.  
**Risk:** `RunLedger.complete()`, `.fail()`, `.block()` on an already-terminal run now raise via `assert_can_transition` (empty transition set for terminal states). Stash had idempotent early-returns with docstring "idempotent for watchdog safety."  
**Action required:** Verify that `watchdog.py` and `recovery_agent.py` never call `complete()`/`fail()` on a run that may already be in a terminal state. If they can (e.g., after a process restart that replays incomplete work), either:
- Add `try/except InvalidTransitionError` at the call sites, or
- Restore idempotent guard in `run_ledger.py` terminal methods.

**Backlog entry added to:** `Docs/exploration/backlog.md`

---

## Stash drop decision

**stash@{1}** — safe to drop immediately. Fully superseded.  
**stash@{0}** — safe to drop after this audit doc is committed. Both items extracted: privacy fix implemented, RunLedger risk documented.

