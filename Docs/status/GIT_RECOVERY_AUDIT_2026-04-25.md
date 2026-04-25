# Git Recovery Audit — 2026-04-25

Generated: 2026-04-25 16:10:36 IST

## Scope

Audit recent reset/stash activity after concern that an implementation agent stashed or reset code. Recovery policy: additive, better, comprehensive; no destructive git operations; no wholesale stash apply.

## Git Findings

- Current branch: `master`, ahead of `origin/master` by 3 commits at audit time.
- Active stash: `stash@{2026-04-25 15:32:48 +0530}: On master: pre-design-review-wip`.
- Reflog reset events:
  - `2026-04-25 15:59:08 +0530`: `reset: moving to HEAD` (no commit movement).
  - `2026-04-25 15:36:47 +0530`: `reset: moving to HEAD` (no commit movement).
  - `2026-04-25 15:32:49 +0530`: `reset: moving to HEAD` (no commit movement).
  - `2026-04-25 00:48:55 +0530`: `reset: moving to HEAD~1`, moved off `e03ae7e` back to `470cea9`.

## Lost Commit Check

Recoverable commit: `e03ae7e feat(frontend): PipelineFlow Palantir-style upgrade`.

Touched files:

- `frontend/src/app/globals.css`
- `frontend/src/app/workbench/PipelineFlow.tsx`

Prior recovery notes show the useful visual changes from `e03ae7e` were already restored into the working tree/index. No additional merge from that commit was needed during this audit.

Doc check: `e03ae7e` touched no files under `Docs/` or `frontend/docs/`, so there were no documentation files to recover from that reset-lost commit.

## Stash Check

Stash base: `8047d04 Final proxy-core.ts cleanup (ChatGPT round 3)`.

Actual stash delta against its parent touched only four files:

- `frontend/src/app/api/[...path]/route.ts`
- `frontend/src/lib/route-map.ts`
- `spine_api/server.py`
- `src/decision/hybrid_engine.py`

Doc check: the active stash touched no files under `Docs/` or `frontend/docs/`, so there were no documentation files to recover from `stash@{2026-04-25 15:32:48 +0530}`.

Decision by file:

| File | Decision | Rationale |
| --- | --- | --- |
| `frontend/src/app/api/[...path]/route.ts` | Already present | Current `HEAD` already denies unknown catch-all routes with 404. No merge needed. |
| `frontend/src/lib/route-map.ts` | Partially merged with architectural filter | Stash tried adding catch-all mappings for routes that are frontend-local or explicit. Those were rejected. The missing `spine/run -> run` mapping was accepted because the old explicit `app/api/spine/run/route.ts` had been deleted and current catch-all architecture requires an explicit backend route-map entry. |
| `spine_api/server.py` | Merged | Added traveler-safe serialization comment. Behavior already preferred `to_traveler_dict`; comment documents why. |
| `src/decision/hybrid_engine.py` | Merged | Stash fixed stale `decision.*` imports to `src.decision.*`. Smoke test proved this moved built-in rule registration from 0 rules to 18 rules. |

## Additional Consistency Fix

The staged audit closure test expected `BUDGET_FEASIBILITY_TABLE` to be canonical in `src.decision.rules`, but the current code still had a duplicate table in `src/intake/decision.py`.

Applied fix:

- Export `BUDGET_FEASIBILITY_TABLE` from `src/decision/rules/__init__.py`.
- Alias `src/intake/decision.py` to the canonical rules table instead of keeping a duplicate object.

## Verification

- `python` smoke: `HybridDecisionEngine(enable_rules=True)` registered 18 built-in rules.
- `python` smoke: `src.intake.decision.BUDGET_FEASIBILITY_TABLE is src.decision.rules.BUDGET_FEASIBILITY_TABLE` returned `True`.
- `cd frontend && npx vitest run src/lib/__tests__/route-map.test.ts`: `3 passed`.
- `PYTHONPATH=. uv run pytest -q tests/test_audit_closure_2026_04_24.py`: `12 passed`.
- `cd frontend && npx tsc --noEmit`: passed.
- `git diff --check`: passed.

## Not Applied

No wholesale stash apply was performed. The route-map entries from the stash were not applied because they would make frontend-local or explicit routes appear backend-backed in the catch-all registry, which conflicts with the project rule to keep one clear route per resource/action.

Regression fragments explicitly kept out:

- No duplicate explicit API routes were restored from the stale stash shape.
- No deleted documentation/test/file removals from broad stash comparisons were applied.
- No fallback passthrough behavior was restored in the catch-all proxy.
- No route-map entries were added for frontend-local routes such as `/api/version` or `/api/scenarios`.
- The only route-map entry recovered from the stash was `/api/spine/run -> /run`, because the old explicit route was deleted and this mapping is required for the current single catch-all architecture.

Current documentation status: `git diff --diff-filter=D --name-status -- Docs frontend/docs` and `git diff --cached --diff-filter=D --name-status -- Docs frontend/docs` returned no deleted documentation files. Current doc changes are additions/modifications, not deletions.

## Process Guardrail Added

Added `AGENTS.md` section `Stash / Reset / Recovery Discipline (Critical)` so future agents cannot use stash/reset as irresponsible workflow shortcuts. The rule requires read-only inspection first, per-file decisions, no wholesale stash apply without current-turn user authorization, and rejection of any fragment that reintroduces duplicate routes, stale imports, deleted docs, removed tests, downgraded validation, or behavior current commits already fixed.

Added an explicit documentation-preservation rule in `AGENTS.md`: no historical, planning, review, research, scenario, status, or worklog documentation should be lost. Obsolete or moved docs must be archived or replaced with pointers, and doc deletions discovered during stash/reset recovery are rejected by default.

Added an explicit code-quality interpretation rule in `AGENTS.md`: all new, revised, or recovered code must be additive, better, and comprehensive against the current codebase. "Additive" preserves useful intent and capability; it does not require keeping legacy, duplicate, broken, stale, or lower-quality code. Worse legacy paths should be removed only after the Supersession Workflow proves the canonical replacement covers their behavior and intent.
