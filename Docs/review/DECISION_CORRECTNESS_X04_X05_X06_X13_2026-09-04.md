# Decision Correctness Wave — X-04, X-05, X-06, X-13

**Date:** 2026-09-04\
**Scope:** canonical intake decision engine and its 30-scenario evaluation corpus\
**Owner:** decision-layer implementation lane\
**Status:** implemented and locally verified; release/promotion remains bounded by the independent-evaluation gates

## Outcome

The canonical decision path now:

1. escalates critical contradictions and the explicitly high-priority
   `party_conflict`/`origin_conflict` actions instead of silently dropping them;
2. treats `budget_raw_text` and `budget_min` as one logical OR-group;
3. rejects blank strings, whitespace-only strings, and empty collections as
   blocker fills; and
4. aligns the six stale/inconsistent scenario fixtures with the current v0.2
   contract (`visa_status`, traveler-safe soft context, and destination-conflict
   routing).

This is a local correctness result, not provider, browser, hosted, or release
proof.

## Evidence-led findings and decisions

| ID | Observed defect | Chosen implementation | Falsifier / boundary |
|---|---|---|---|
| X-04 | `CONTRADICTION_ACTIONS` declared `party_conflict` and `origin_conflict` as high-priority ASK actions, but Phase 7 collected only critical actions. | Make critical actions universally actionable and explicitly route the two high-priority conflict types to `ASK_FOLLOWUP`; a STOP action wins over ASK in mixed packets. | Add a new high-priority conflict type without updating the explicit escalation set: it will not escalate until policy ownership is deliberately added. This prevents stage-gated feasibility from changing accidentally. |
| X-05 | Discovery listed `budget_raw_text` and `budget_min` independently, so normalized-only structured/CRM packets were demoted to internal draft. | Evaluate the two fields atomically and emit one canonical `budget_min` blocker only when neither representation is usable. | A future consumer that requires raw provenance must check `budget_raw_text` directly; the decision MVB does not erase provenance, it only avoids double-counting it. |
| X-06 | `field_fills_blocker()` rejected only `None`; empty/blank values could satisfy hard blockers. | Add decision-boundary validation for blank strings and empty `Collection` values, while preserving valid non-empty values and authority checks. | Numeric/domain-invalid non-empty values (for example, party size `0`) remain a separate domain-validation task. |
| X-13 | Six corpus expectations/fixtures had drifted from the current decision contract. | Correct C1/F2/F3 soft-context fixtures, D3 booking blocker count, D4 `visa_status`, and F1 destination-conflict state. | Corpus remains synthetic and the broader eval promotion still requires independent producers/holdouts per `EVAL_GATES_E01_E05_2026-09-03.md`. |

### Why budget feasibility was not made an immediate escalation

The action table labels `budget_feasibility` as high priority, but the current
stage policy intentionally represents discovery/shortlist infeasibility as a
soft blocker and proposal/booking infeasibility as a hard blocker. The existing
budget-vs-luxury behavior and tests rely on that staged contract. X-04 names
party/origin conflicts as the high-priority escalation gap; therefore this wave
does not collapse stage-gated budget feasibility into an immediate ASK. A future
policy change must be explicit and separately tested.

## Files changed

- `src/intake/decision.py`
  - added `BUDGET_SOFT_BLOCKER_GROUP` evaluation;
  - hardened `field_fills_blocker()` against empty values;
  - made critical and named high-priority conflict actions reachable;
  - retained STOP-over-ASK precedence and existing result contracts.
- `data/fixtures/test_scenarios.py`
  - corrected the six X-13 fixture/expectation errors.
- `tests/test_decision_policy_conformance.py`
  - added regression coverage for party/origin escalation, OR-group behavior,
    blank/empty values, canonical missing-budget output, and STOP precedence.
- `tests/test_comprehensive_v02.py`
  - updated the expected logical soft-blocker count from four field names to
    three dimensions after the budget OR-group correction.

## Verification receipt

Commands were run against the shared working tree without staging, committing,
pushing, resetting, checking out, stashing, or cleaning:

```text
PYTHONPATH=src .venv/bin/pytest -q \
  tests/test_decision_policy_conformance.py \
  tests/evals/test_30_scenario_corpus_gate.py \
  tests/test_comprehensive_v02.py tests/test_nb02_v02.py \
  tests/test_nb03_v02.py tests/test_realworld_scenarios_v02.py \
  tests/test_api_contract_v02.py
146 passed in 2.45s

PYTHONPATH=src .venv/bin/python - <<'PY'
from src.evals.audit.rules.scenarios import load_scenario_fixtures, run_scenario_eval
print(run_scenario_eval(load_scenario_fixtures()).summary())
PY
{
  'total_fixtures': 30,
  'decision_state_accuracy': 1.0,
  'hard_blocker_accuracy': 1.0,
  'contradiction_accuracy': 1.0,
  'fixture_accuracy': 1.0,
  'fixtures_passing': 30,
  'fixtures_failing': 0,
}

.venv/bin/ruff check \
  src/intake/decision.py data/fixtures/test_scenarios.py \
  tests/test_decision_policy_conformance.py tests/test_comprehensive_v02.py
All checks passed!

git diff --check -- <four files above>
pass
```

The scenario probe emits pre-existing optional-hybrid warnings because
`google-genai` is not installed; the deterministic scenario result still
completed 30/30. Those warnings are not silently promoted to production proof.

**Evidence level:** Tier 2 targeted/in-process verification; defect-sensitive
regressions are S2 by counterfactual reproduction documented in
`Docs/exploration/N01_SCENARIO_TRIAGE_2026-09-02.md`. The 30/30 corpus result is
not independent-source evidence and remains subject to the eval shadow gate.

## Remaining related work

- Triage and fix the separate extraction defects X-01/X-02/X-03/X-07/X-08;
  this wave intentionally leaves parser ownership untouched.
- Decide whether the low-confidence threshold in the final decision branch
  should be made reachable; N-01 records it as a latent/dead gate, but changing
  it would alter the authored `basic_minimal_safe` semantics and is not part of
  X-04/X-05/X-06/X-13.
- Add independent producers, runnable raw document inputs, private holdouts,
  and a falsifying mutation lane before promoting the 30-scenario score to a
  release gate.
