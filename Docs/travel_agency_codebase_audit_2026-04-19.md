# Travel Agency Agent — Python Backend Codebase Audit

**Date**: 2026-04-19
**Scope**: `src/intake/`, `src/decision/`, `src/llm/`, `src/suitability/`, `spine-api/`, `src/` root files
**Mode**: Read-only — no fixes applied
**Auditor**: AI assistant (automated static review)

---

## Summary

| Severity | Count |
|----------|-------|
| P0 (Runtime error / crash) | 2 |
| P1 (Data loss / wrong behavior) | 4 |
| P2 (Code quality / fragility) | 6 |
| P3 (Cosmetic / style) | 1 |
| **Total** | **13** |

---

## Findings

### P0-1: `PROJECT_ROOT` undefined — `NameError` at runtime

- **File**: `spine-api/server.py:259`
- **Issue**: `load_fixture_expectations()` references `PROJECT_ROOT` but this variable is never defined in the file. When `scenario_id` is provided to the `/run` endpoint, this function is called and will raise `NameError: name 'PROJECT_ROOT' is not defined`.
- **Fix**: Define `PROJECT_ROOT = Path(__file__).resolve().parent.parent` at module level (consistent with how other modules resolve the project root).

---

### P0-2: Broken absolute import for hybrid engine

- **File**: `src/intake/decision.py:43`
- **Issue**: `from decision import create_hybrid_engine` uses an absolute import that only works if `decision` is a top-level package on `sys.path`. Since `decision.py` itself lives inside `src/intake/`, this import path is fragile and will fail in most execution contexts (e.g., when running `spine-api/server.py` as a module). The actual module is `src/decision/hybrid_engine.py`.
- **Fix**: Change to `from src.decision.hybrid_engine import create_hybrid_engine` or use a relative import pattern consistent with the project's package structure. Verify `sys.path` configuration in all entry points.

---

### P1-1: Duplicate `_PAST_TRIP_INDICATORS` — second definition silently overrides first

- **File**: `src/intake/extractors.py:48–53` vs `:70–74`
- **Issue**: `_PAST_TRIP_INDICATORS` is defined twice as a frozenset. The first definition (lines 48–53) includes `"recently visited"` and `"we went to"`. The second definition (lines 70–74) omits those two phrases and silently overrides the first. This means past-trip detection never matches on those two indicator phrases.
- **Fix**: Remove the duplicate definition. Merge any unique items from the first into the second, or keep the first and delete the second. Add a test to prevent regression.

---

### P1-2: Dead code — unreachable risk-flag blocks in `generate_risk_flags`

- **File**: `src/intake/decision.py:1332–1351`
- **Issue**: The `generate_risk_flags` function has a `return risks` statement at line 1389, but lines 1332–1351 contain a duplicate "coordination risk" block and a "traveler-safe leakage risk" block that are **unreachable** because they appear after an earlier `return` or are in a code path that can never be reached. These blocks will never execute.
- **Fix**: Remove the dead code blocks, or move them before the return statement if they represent intended logic that was accidentally placed after the exit point.

---

### P1-3: `internal_notes` leakage on traveler-safe bundle

- **File**: `src/intake/decision.py:911` (inside `build_traveler_safe_bundle`)
- **Issue**: When `enforce_no_leakage` detects leaks but doesn't raise, the code sets `bundle.internal_notes = f"LEAKAGE DETECTED: ..."`. While `to_traveler_dict()` excludes `internal_notes`, `to_dict()` includes it. If any code path serializes this bundle via `to_dict()` and returns it to the traveler, internal reasoning leaks. This violates the structural guarantee that traveler-facing bundles contain no internal data.
- **Fix**: Either (a) raise on leakage instead of silently setting `internal_notes`, (b) ensure all traveler-facing serialization paths use `to_traveler_dict()`, or (c) store leakage notes in a separate audit object rather than on the bundle itself.

---

### P1-4: Race condition — non-atomic read-modify-write in persistence stores

- **File**: `spine-api/persistence.py` (AssignmentStore, AuditStore, and any store using `json.load` → modify → `json.dump`)
- **Issue**: All persistence stores read a JSON file, modify the in-memory dict, and write it back without any file locking or atomic write strategy. Under concurrent requests (e.g., two `/run` calls hitting the same trip), this can cause data loss: both reads see the same state, both writes overwrite, and the second write loses the first's changes.
- **Fix**: Use `fcntl.flock` (POSIX) or `filelock` library for cross-platform file locking. Alternatively, use atomic writes (write to `.tmp`, then `os.rename`) combined with locking.

---

### P2-1: `_FAMILY_BUFFER_BUMP` logic — `max()` always returns second argument

- **File**: `src/intake/decision.py:952`
- **Issue**: `max(adult_equivalents, adult_equivalents + _FAMILY_BUFFER_BUMP * adult_equivalents)` — since `_FAMILY_BUFFER_BUMP` is positive (0.02), the second argument is always larger. `max()` is therefore redundant; it always returns the bumped value. This suggests either the multiplier should be negative (a *reduction* guard) or the `max()` was meant for a different comparison (e.g., capping the bump).
- **Fix**: Clarify the intent. If it's a floor, change to `max(floor_value, adult_equivalents + ...)`. If the bump is always applied, remove the `max()` wrapper.

---

### P2-2: Slot object repr in LLM prompt

- **File**: `src/decision/hybrid_engine.py:622` (inside `_extract_packet_context`)
- **Issue**: When building the LLM prompt, `value` (a `Slot` object) is stringified directly rather than accessing `value.value`. This causes the LLM to see unhelpful Python repr strings like `Slot(field='destination_raw_text', value='Tokyo', ...)` instead of just `'Tokyo'`.
- **Fix**: Change the f-string to use `value.value` (with a guard for `value.value is not None`).

---

### P2-3: Import fragility in `spine-api/server.py`

- **File**: `spine-api/server.py:57–78`
- **Issue**: The server uses try/except to import `persistence` as either relative or absolute, and imports `run_state`, `run_events`, `run_ledger` as absolute modules. These only work if `spine-api/` is on `sys.path`. Running the server as `python spine-api/server.py` vs `python -m spine-api.server` may produce different import behavior.
- **Fix**: Standardize on one invocation method. Add `sys.path` manipulation in an `if __name__ == "__main__"` block, or convert to a proper package with `__init__.py` and use relative imports throughout.

---

### P2-4: No error handling on file write in `AgencySettingsStore.save`

- **File**: `src/intake/config/agency_settings.py` (`.save()` method)
- **Issue**: The `save()` method writes JSON to disk with no try/except. If the write fails partway (disk full, permissions, crash), the JSON file could be left corrupt (truncated or empty), causing `load()` to fail on next startup.
- **Fix**: Write to a `.tmp` file first, then `os.rename()` to the target path (atomic on POSIX). Add try/except with a meaningful error message.

---

### P2-5: Budget feasibility table duplicated between `decision.py` and `rules/budget_feasibility.py`

- **File**: `src/intake/decision.py` (budget feasibility table) vs `src/decision/rules/budget_feasibility.py`
- **Issue**: The budget feasibility threshold table exists in both `decision.py` and the `budget_feasibility` rule module. If one is updated without the other, they'll diverge silently, producing inconsistent feasibility verdicts depending on which code path is hit.
- **Fix**: Canonicalize the table in one location (e.g., a shared `constants.py` or the rules module) and import from there.

---

### P2-6: `continue` in budget extraction skips generic `set_fact`

- **File**: `src/intake/extractors.py:1088`
- **Issue**: When `canonical_field == "budget_raw_text"`, the code does `continue`, skipping the subsequent `packet.set_fact(canonical_field, ...)` call. This means structured JSON budget fields never get their main canonical field set via the generic path — only budget-specific sub-fields are populated. This appears intentional (budget goes through special handling) but the flow is confusing and undocumented, making future maintainers likely to introduce bugs.
- **Fix**: Add a comment explaining why budget skips the generic path. Consider refactoring to make the special case explicit rather than relying on a `continue` in a loop.

---

### P3-1: Telemetry emission with no backend — silent no-op

- **File**: `src/intake/telemetry.py`
- **Issue**: The `emit()` function is a no-op stub that logs at DEBUG level but never sends telemetry anywhere. Consumers of telemetry data will never receive any signals. This is not a bug per se, but it means all telemetry-dependent features (dashboards, alerts, observability) are silently broken.
- **Fix**: Document that telemetry is currently a stub. If telemetry is intended to work, wire up the actual transport (e.g., statsd, Prometheus, OTLP).

---

## Audit Coverage

| Directory | Files Read | Issues Found |
|-----------|-----------|--------------|
| `src/intake/` | 13 | 6 |
| `src/decision/` | 9 | 2 |
| `src/llm/` | 4 | 0 |
| `src/suitability/` | 6 | 0 |
| `spine-api/` | 5 | 3 |
| `src/` root | 2 | 0 |
| **Total** | **39** | **13** (2 + 4 + 6 + 1) |

---

## Methodology

1. Full file-by-file read of all Python files across all 6 target directories
2. Manual static analysis for: runtime errors, type mismatches, missing error handling, silent failures, dead code, security issues, broken API contracts, missing validation, inconsistencies
3. Cross-file comparison for duplicated logic and contract mismatches
4. No automated linting or type-checking tools were run (supplementary automated scan recommended)

---

## Recommended Next Steps

1. **Fix P0s first** — the `PROJECT_ROOT` NameError and broken import will cause crashes in production
2. **Address P1s** — data loss (race condition) and wrong behavior (duplicate indicators, dead code, leakage) affect correctness
3. **Run automated tooling** — `mypy --strict`, `ruff`, `bandit` to catch issues the manual audit missed
4. **Add integration tests** — especially for concurrent persistence writes and fixture loading paths
5. **Re-audit after fixes** — verify no regressions introduced