# Wave 1 / RQ-06 / EX-06 Execution Outcomes (2026-08-30)

**Scope:** A-01 (un-mute the D6 quality gate), RQ-06 (frontend ground truth), EX-06 (findings lifecycle). Session note: A-14 landed as commit `8ece02e` during this work; the parallel agent had already implemented most of Wave 1 — this session verified it end-to-end rather than duplicating it, per doctrine §5.

---

## 1. A-01 — the honest quality gate is live (verified)

**State found:** the parallel agent's commit `8ece02e` plus unstaged edits had already implemented the audit's five fixes:

| Plan item | Status | Evidence |
|---|---|---|
| 1.1 `budget_health` in `_check_blocks_ci()` | ✅ done (`8ece02e`) | `scripts/verify_d6_gate_snapshot.py` now checks routing/extraction/pipeline/budget health **plus every category** |
| 1.2 `min_accuracy` on budget | ✅ done (unstaged) | `src/evals/audit/manifest.yaml`: `min_accuracy: 0.85` |
| 1.3 honest assertions | ✅ done (`8ece02e`) | `tests/evals/test_d6_gate_snapshot.py` — 43/43 pass, incl. `test_extraction_live_results_blocks_ci_when_below_threshold` asserting `blocks_ci is True` |
| 1.4 snapshot regenerated | ✅ done (unstaged) | `data/evals/d6_audit_gate_snapshot.json` carries real budget numbers |
| 1.5 real results wiring | ⚠️ **partial** | `build_gate_snapshot()` accepts `extraction_live_results` / `pipeline_live_results` / `budget_live_results` params, but **no caller feeds live results yet** — defaults still run fixture baselines (residual, see §4) |

**Executed verification (this session):**
- `pytest tests/evals/test_d6_gate_snapshot.py` → **43 passed**.
- `python scripts/verify_d6_gate_snapshot.py` → **exit 1** with `ci_blockers`: `budget_health.blocks_ci is true (f1=0.2857)` and `category:budget accuracy_below_threshold` — exactly the honest signal the audit demanded. `budget_health` shows F1 0.2857 / recall 0.1667 / `baseline_drifted: true`.
- S2 acceptance from the plan holds: budget category reports `blocks_ci: true` at F1 0.2857 against `min_accuracy: 0.85`.

**Consequence (announced, not a regression):** CI's "D6 gate snapshot guard" step now fails on every run **until budget extraction F1 actually improves or thresholds are re-baselined with documented rationale**. This makes RQ-01 (is deterministic extraction the right ceiling?) the blocking research question — its error-taxonomy work is now the path to green.

## 2. RQ-06 — frontend ground truth (first real numbers)

| Check | Command | Result |
|---|---|---|
| Typecheck | `npm run typecheck` | **PASS (exit 0)** — zero type errors |
| Lint | `npm run lint` | **FAIL** — 4 errors, 17 warnings (detail below) |
| Tests | `npm test -- --run` | **897 tests: 896 passed, 1 failed** (115 files: 114 passed) · 49 unhandled errors · 22.9 min duration |

- **The one failing test:** `src/components/workspace/panels/__tests__/TimelinePanel.test.tsx > renders timeline events` — asserts on "Decision Timeline" while the component is still in `Loading timeline…`; the fetch hasn't resolved before the assertion (async-loading race, likely missing `waitFor`). Related test in the same file needed 18.5s (real timers), so the file is timing-fragile generally.
- **49 unhandled errors:** post-run `Errors  49 errors` in the vitest summary — unexamined; likely unhandled rejections/timeouts from async components under fake timers.
- **Lint errors (4):** `react/no-unescaped-entities` (1), setState-synchronously-in-effect (2), refs-during-render (1) — the latter three are React 19-style correctness errors. Warnings (17) are overwhelmingly `react-hooks/exhaustive-deps`.
- **Assessment impact:** A-16's "no e2e, thresholds unenforced" stands; A-15's "debt undocumented" gets its first hard numbers. Audit Assumption 7 ("frontend tests never executed") is **closed**.

Recorded as new register row **F-17** (see consolidated register).

## 3. EX-06 — findings lifecycle delivered

- **Spec:** `Docs/review/FINDINGS_LIFECYCLE_2026-08-30.md` — 4-state machine (open / closed / deferred), transition rules (closing requires evidence; no-go requires a recorded reason; one row per ID), canonical register designation, proposed D-02 doctrine amendment text for Pranay.
- **Enforcement:** `scripts/check_findings_register.py` (stdlib-only, ruff-clean, CI-ready). Errors on duplicate IDs and open findings stale beyond `--max-age` (default 45d); warns on undated open rows.
- **Validated:** consolidated register → **51 rows (45 open / 6 closed), OK**; `FINDINGS_REGISTER_2026-08-29.md` → 16 rows (9 open / 7 closed), OK. Stale + duplicate failure modes exercised with a synthetic fixture (exit 1 as designed).
- **Dogfooding payoff:** the checker immediately caught a duplicate R-06 row and a false-stale EX-05 (in-row cross-reference date) in the register written earlier today — both fixed; the date-floor heuristic (doc date floors row dates) came out of that.
- **Deferred (coordination):** the one-line CI job for the gate is specified in the spec but not added to `.github/workflows/ci.yml`, which carries the A-14 agent's changes — wire it in the next CI touch.

## 4. Residuals / next actions

1. **CI is now honestly red on the budget gate** — expected state; the path back to green is RQ-01's extraction error taxonomy (tunable / needs-LLM / ambiguous buckets), or a documented threshold re-baseline. Decision needed from Pranay only if he wants a temporary documented downgrade instead.
2. **1.5 residual:** wire a live-results producer into `build_gate_snapshot()` (run the pipeline over current fixtures/output and pass results) so extraction/pipeline gates measure live output, not fixture baselines.
3. **F-17:** fix the TimelinePanel test race + investigate the 49 unhandled vitest errors + clear the 4 lint errors.
4. **Wire the findings-lifecycle CI job** (one line, spec'd) at the next safe CI edit.

## Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
