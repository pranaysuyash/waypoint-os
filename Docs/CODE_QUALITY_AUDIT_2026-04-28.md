# Code Quality Audit Report -- travel_agency_agent

**Date:** 2026-04-28

---

## Tools Executed & Results

| Tool | Scope | Exit | Errors | Fixable | Notes |
|------|-------|------|--------|---------|-------|
| ruff (lint) | `src/` | 0 | 144 | 74 (52%) | Unused imports dominate |
| ruff (lint) | `tests/` | 0 | 238 | 212 (89%) | Test files have worse hygiene |
| ruff (lint) | all | 0 | 625 | 428 (68%) | 26 files formatted vs 175 would-reformat |
| ruff (format) | all | 1 | -- | -- | 175 files would reformat |
| mypy | all | N/A | -- | -- | Not installed (not in dev deps) |
| pytest | `tests/` | 1 | 40 failed / 962 passed | 13 skipped | 4% failure rate |
| tsc | `frontend/src` | 2 | ~110 TS errors | -- | All in `__tests__/` files (vitest globals not recognized) + 2 real errors |
| vitest | `frontend/` | 1 | 8 failed / 38 passed | -- | 17 failed tests across 8 files |
| shellcheck | -- | N/A | -- | -- | No shell scripts in project |

## Ruff Error Breakdown (All Files)

| Code | Rule | Count | Description |
|------|------|-------|-------------|
| F401 | unused-import | 429 | By far the largest issue |
| E402 | module-import-not-at-top | 60 | sys.path hacks in scripts |
| F541 | f-string-no-placeholders | 56 | `print(f"...")` where f is useless |
| F841 | unused-variable | 32 | Assigned but never read |
| F821 | undefined-name | 17 | Name not defined (mostly notebooks) |
| E722 | bare-except | 12 | `except:` without exception type |
| E401 | multiple-imports-on-one-line | 8 | |
| E712 | true-false-comparison | 4 | `== True` instead of `is True` |
| F811 | redefined-while-unused | 3 | |
| E701 | multiple-statements-on-colon | 2 | |

## Ruff Source-Only (src/) Breakdown

| Code | Count |
|------|-------|
| F401 (unused-import) | 116 |
| F541 (f-string-no-placeholders) | 16 |
| F841 (unused-variable) | 7 |
| F821 (undefined-name) | 3 |
| E402 (module-import-not-at-top) | 2 |

**src/ is relatively clean with 144 errors (mostly unused imports leftover from refactoring).**

## Test Results

**Python (pytest):**
- Failed: 40 | Passed: 962 | Skipped: 13
- 4% failure rate
- Primary failing test areas:
  - `test_run_lifecycle.py` -- 11 failures (golden path, ledger, leakage)
  - `test_spine_api_contract.py` -- 11 failures (canonical contract, strict leakage)
  - `test_privacy_guard.py` -- 2 failures
  - `test_geography.py` -- 1 failure
  - `test_nb01_v02.py` -- 3 failures
  - `test_phase5_notifications.py` -- 1 failure

**TypeScript (vitest):**
- Failed: 8 test files | Passed: 38
- 17 individual test failures
- Primary failing areas:
  - `FollowUpCard.test.tsx` -- uses `jest.mock()` but vitest needs `vi.mock()`
  - `page.test.tsx` -- same jest vs vitest mock incompatibility
  - `TimelinePanel.suitability.test.tsx` -- 5 failures (suitability integration)
  - `ActivityTimeline.test.tsx` -- 3 failures
  - `public_marketing_pages.test.tsx` -- 2 failures
  - `SuitabilitySignal.phase3.test.tsx` -- 2 failures
  - `AuditReport.provenance.test.tsx` -- 2 failures

## Manual Code Quality Findings

### P0 -- Must Fix

1. **40 failing Python tests and 17 failing frontend tests** -- indicates code drift from test expectations. `test_run_lifecycle.py` and `test_spine_api_contract.py` each have ~11 failures suggesting a core pipeline regression.

2. **2 real TypeScript compilation errors** in non-test code:
   - `frontend/src/app/workspace/[tripId]/followups/page.tsx:155,187` -- `bgDefault` property does not exist on the theme type

3. **`except Exception` everywhere** -- 19 instances in `src/llm/` (gemini_client.py, openai_client.py, local_llm.py, usage_store.py). All catch broadly without re-raising or specific error handling. Example: `src/llm/usage_store.py:199`, `src/llm/gemini_client.py:96`, `src/llm/openai_client.py:99`.

### P1 -- Should Fix

4. **Bare `print()` in production code** -- `src/intake/decision.py:55,136,1313` uses `print()` instead of `logging`. The `print(f"Warning: ...")` pattern is not configurable, not structured, and can't be silenced.

5. **Missing mypy** -- not installed despite Python 3.13 with `strict: true` equivalent in TypeScript. The `pyproject.toml` dev deps only have `pytest` and `ruff`.

6. **429 unused imports across the codebase** -- 116 in `src/`, 203 in `tests/`. Heavy import cruft from refactoring (e.g., `tests/test_realworld_scenarios_v02.py:15` imports 5 unused symbols from `typing`).

7. **`src/intake/decision.py` at 2240 lines** -- largest file, likely violates single-responsibility. Combined with `src/intake/extractors.py` (1554 lines), these two files represent ~20% of all Python source code.

8. **Frequent `Dict[str, Any]` in extractors** -- `src/intake/extractors.py` uses `Dict[str, Any]` as return type for ~8 extraction functions (lines 409, 518, 626, 714, 811, 857, 863, 925). These should return typed dataclasses or TypedDicts.

### P2 -- Good to Fix

9. **56 f-strings without placeholders** -- `print(f"Test passed: ...")` pattern. Simple `print("Test passed: ...")` suffices.

10. **17 `undefined-name` errors** -- mostly in notebook tests that reference decision engine internals (`DecisionResult.confidence_score`).

11. **`type: ignore` in `src/intake/normalizer.py:268`** -- only one, but it masks an actual typing issue.

12. **TODO markers** -- `src/decision/health.py:181` has a TODO about LLM health checks. `frontend/src/app/api/trips/route.ts:81` has a TODO about calling the spine pipeline.

13. **Large TypeScript files** -- `frontend/src/app/itinerary-checker/page.tsx` (1036 lines), `IntakePanel.tsx` (912 lines). These page components are too large.

## Good Patterns Observed

| Location | Pattern |
|----------|---------|
| `src/llm/usage_guard.py` | Proper `logging` usage with contextual extra data -- `logger.error("llm_usage_guard.storage_failed", extra={"error": str(exc)})` |
| `src/agents/recovery_agent.py` | Structured module with docstrings, typed dataclasses, proper logger setup, structured `logger.info`/`logger.exception` calls |
| `src/security/encryption.py` | Clean, focused encryption module with logged error handling (`logger.warning`) |
| `src/intake/packet_models.py` | Uses Pydantic/dataclass models with `field()` defaults; typed fields |
| `pyproject.toml` | Has explicit tool config for pytest (testpaths, pythonpath) |
| `frontend/tsconfig.json` | `strict: true`, clean module resolution |

## Problematic Patterns

| File:Line | Issue |
|-----------|-------|
| `src/intake/decision.py:55` | `print(f"Warning: ...")` -- should use `logging.warning()` |
| `src/llm/gemini_client.py:96` | `except Exception as e:` -- too broad, swallows KeyboardInterrupt |
| `src/llm/usage_store.py:327` | `except Exception:` no re-raise or logging |
| `src/intake/extractors.py:409` | Return type `Dict[str, Any]` -- loses all type information |
| `tests/test_realworld_scenarios_v02.py:15-17` | 10 imports from `typing` and `dataclasses`, all unused |
| `tests/test_privacy_guard.py:126` | `pytest.raises(Error) as exc` -- `exc` never used (repeated 8 times) |
| `frontend/src/components/workspace/cards/__tests__/FollowUpCard.test.tsx:4` | Uses `jest.mock()` but vitest needs `vi.mock()` -- entire test file is broken |
| `frontend/src/app/workspace/[tripId]/followups/page.tsx:155` | References `bgDefault` on theme type where it doesn't exist |

## Code Quality Score: 6.5 / 10

**Breakdown:**

| Category | Score | Rationale |
|----------|-------|-----------|
| Code Organization | 7 | Good module structure, but 2240-line decision.py is a monolith |
| Type Safety | 5 | No mypy; heavy `Any` use in extractors; 110 TS errors (mostly test) |
| Testing | 6 | 962 Python tests pass but 40 fail (4%); 38 frontend tests pass but 17 fail |
| Error Handling | 5 | 19 broad `except Exception` in llm/; bare `print()` instead of logging |
| Lint Hygiene | 6 | 625 ruff errors, but 74 fixable in src/; 175 files need formatting |
| No Dead Code | 5 | 429 unused imports; 32 unused variables; import rot is significant |
| Naming Conventions | 8 | Generally clean naming; Python uses underscores correctly |
| Documentation | 7 | Docstrings present in most modules; pyproject.toml well-organized |

The codebase is functional with strong test coverage (962 passing) and reasonable module organization. Major issues: 40 failing tests suggest ongoing refactoring/regression, broad `except Exception` patterns in LLM modules mask real errors, and the unused import rot (429 instances) indicates cleanup debt from iterative development. TypeScript tests are broken at scale (jest vs vitest API mismatch across multiple files).
