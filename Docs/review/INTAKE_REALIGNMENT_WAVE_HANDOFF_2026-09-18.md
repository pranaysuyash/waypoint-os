# Intake Realignment Wave Handoff — 2026-09-18

**Trigger:** Random repository document audit (seed 20260918) selected
`Docs/FIRST_PRINCIPLES_GAP_ASSESSMENT_2026-04-14.md`; owner approved full
implementation of the resulting register. Uncommitted — all work below is in
the working tree for owner review. No commits were made.

**Findings:** FND-0296…FND-0300 opened and closed same session with evidence.
**Explorations:** E14/E15 docs + `Docs/EXPLORATION_TOPICS.md` topics 34/35.

## What was implemented

### T-01 — Decision policy spec realigned (FND-0298)
- `specs/decision_policy.md` rewritten v0.2 → **v0.3**: removed the confidence
  fallback clause (runtime removed it N01 2026-09-02 §2.2), documented
  stage-gated budget feasibility, `HIGH_PRIORITY_ESCALATION_TYPES`, and
  STOP-over-ASK precedence; dated change log added.
- `specs/runtime_contract_version_matrix_2026-05-12.md` decision-policy row updated.
- `tests/test_decision_policy_conformance.py`: +2 invariant pins
  (low-confidence traveler-safe; stage-gated budget blocker) → 13 tests.

### T-02 — branch_options through the run-status contract (FND-0297)
- `spine_api/contract.py`: `branch_options` field on `RunStatusResponse`.
- `spine_api/routers/run_status.py`: read + pass-through (covers both
  decision-step read paths).
- `frontend/src/types/spine.ts`: mirror field.
- `frontend/src/hooks/useWorkbenchRunSync.ts`: hardcoded `[]` replaced with
  normalized mapping.
- Tests: `test_run_contract_drift_guard.py` field pin; `tests/test_spine_api_contract.py`
  green; `tests/test_d1_autonomy.py` (direct constructions) green.

### T-03 — Options surface mounted (DecisionPanel port)
- `frontend/src/components/workspace/panels/DecisionPanel.tsx`: new Branch
  Options section (string + scored route-structure shapes, `data-testid="branch-options"`).
- `frontend/src/components/workspace/panels/__tests__/DecisionPanel.branch_options.test.tsx`: 3 cases.
- **Superseded mid-wave, in the good direction:** the parallel launch-readiness
  tranche (Supersession T2) deleted `workbench/DecisionTab.tsx`, ported its
  remaining sections into DecisionPanel, and added a `decision` workbench tab
  (`workbench-state.ts:28`) rendering DecisionPanel (`PageClient.tsx:854-855`).
  The Branch Options section therefore went live in the workbench during this
  wave — both edit sets verified coexisting (22/22 FE suites, typecheck clean
  on the combined tree).

### T-04 — general_conflict silent drop fixed (FND-0296)
- `src/intake/decision.py` Phase 7: medium-priority ASK actions now actionable
  (honors the declared action table).
- **Collision caught by the scenario pack:** the synthetic `budget_feasibility`
  contradiction classified as `general_conflict` (no field-map entry) and would
  have leaked past its stage-gating. Fixed with
  `"budget_feasibility": "budget_feasibility"` in `CONTRADICTION_FIELD_MAP` —
  the ACTIONS row was previously unreachable via classification.
- Test: `test_general_conflict_emits_followup_question`.

### T-05 — Decision-state + friction metrics (gap-assessment P2-2 residuals)
- `spine_api/metrics_registry.py`: `spine_decisions_total{decision_state}` (5
  states pre-seeded) + `spine_follow_up_questions_total`; helpers
  `inc_decision_outcome` / `inc_follow_up_questions`.
- `spine_api/services/pipeline_execution_service.py`: recorded once per run at
  the decision-step checkpoint (single point where a decision payload exists on
  every terminal path); module-level import prevents silent NameError behind
  the defensive except.
- Tests: 3 new in `tests/test_metrics_registry.py` (10/10).

### T-06 — Season-tier feasibility implemented (supersession verdict: NOT dead code)
- Investigation: the constants were an unwired April TODO documented in
  `Docs/CORE_INSIGHT_AND_HARDCODED_INVENTORY_2026-04-16.md` (P0 "per-destination
  costs + seasonality"); every sibling constant in the block is wired; no
  other subsystem covers intake feasibility (margin_optimizer takes a
  client-supplied bool defaulting False; campaign subsystem is marketing-only).
- Implementation supersedes the flat-constant design per the audit doc's own
  criticism: `_DESTINATION_SEASON_TIERS` (19 destinations, off-peak baseline
  1.0, monsoon months = off, consistent with `live_checks.py`), month resolved
  from `date_start`/`date_end` ISO facts with word-boundary month-name
  fallback (earliest-in-text wins), applied before margin; `season` +
  `season_multiplier` returned in the feasibility payload; `margin_risk`
  message notes peak season; unknown destination/month → 1.0 (byte-for-byte
  old behavior).
- Tests: `tests/test_budget_seasonality.py` (8 cases incl. regression pin,
  word-boundary safety, no-inflation guarantee).

### Overflow hardening (FND-0300, found by E-01 experiment)
- `src/intake/normalizer.py` `parse_budget`: all four `int(float(...))` paths
  guarded (finite + 10^15 sanity bound → graceful None), regression tests in
  `tests/test_extraction_fixes.py::TestParseBudgetOverflowHardening`.

### E-03 — Schema drift guard (FND-0299)
- Genuine drift found and fixed: `assumptions` + `metadata` (emitted by
  `to_dict()` since the F-37 slice) added to `specs/canonical_packet.schema.json`.
- `tests/test_canonical_packet_schema_drift.py`: pins schema == to_dict() keys
  + header version marker.

## Verification

- **Full backend suite (canonical runner, post-realignment recheck with the
  :8000 dev server down): 5,079 passed, 56 skipped, 0 failed in 4m24s** —
  on the combined tree (this wave + the 196-entry parallel tranche).
- Earlier same-wave targeted batches: 601 passed / 2 skipped across the 18
  touched-surface test files; FE DecisionPanel suites 22/22;
  `npm run typecheck` clean (re-verified after the parallel T2 edits landed).
- Findings store validated: 576 events / 306 findings / 0 warnings.

## Deferred / decisions for owner

- **D-1 (RESOLVED 2026-09-18, post-wave):** the parallel tranche mounted the
  workbench Decision tab rendering DecisionPanel — the preferred long-term
  path happened on its own; no action left.
- **D-2:** `spine-api.ts` regeneration (dirty generated file) — regenerate after
  the parallel tranche commits to avoid mixing. The live workbench path uses
  the handwritten `spine.ts` mirror (updated this wave), so the serving fix is
  complete regardless; regeneration is contract hygiene.
- **D-3:** `hypothesis` dev-dependency adoption (E14).
- **D-4:** Tiered-option budget producer (E15) — revisit only on operator demand.
- **D-5:** Archive the gap-assessment doc with a per-item disposition table +
  fix the handoff-checklist backlink (`Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md:38`).

## Post-tranche recheck (2026-09-18, executed)

The parallel tranche grew 61 → 196 dirty entries during this wave. Re-checked:
- No new commits (head still `f51bb232`); all wave edits verified present.
- `decision.py` diff now 191 insertions — shared with parallel work; combined
  tree green (see Verification).
- DecisionTab supersession landed (above); `themeStore.ts:32` still carries a
  stale `DecisionTab` string (cosmetic, parallel-owned).
- Findings store validated clean after interleaved parallel writes
  (576 events / 306 findings / 0 warnings); FND-0296…0300 all closed.
