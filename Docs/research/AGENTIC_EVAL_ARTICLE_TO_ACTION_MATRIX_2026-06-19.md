# Agentic Eval Article-to-Action Matrix (2026-06-19)

Purpose:

1. Turn the attached article learnings into project-level executable rules.
2. Show where this repo currently lives for I/O, prompts, routing, fallback, and review signals.
3. Define the next implementation slice that converts logs into measurable product changes.

This is the practical follow-up from your request to make these learnings reusable as rules/skills.

## What those article series says (high signal)

- A final score is useful only if it can become a **next action**.
- Missing/failing data must be traced to the right failure layer (model, prompt, parser, schema, dictionary/normalization, routing, fallback, review).
- Routing, fallback, and review are part of product behavior, not plumbing.
- Evaluation should always carry workflow context:
  - input artifact / workflow unit
  - workflow type
  - provider + model
  - prompt/schema/routing/dictionary/normalization versions
  - fallback trigger and outcome
  - review trigger and outcome
  - escalation outcome
  - latency and cost
- Cost/latency/review burden decisions must be measured alongside accuracy.
- Repeated failures should only become fixes through explicit thresholds plus rerun gates.

## What is already in place (actual code and tests)

- Canonical evidence export path:
  - `src/evals/agentic_feedback.py` now builds `CanonicalAgenticEvidenceRecord`.
  - Includes path-level keys, version fields, escalation outcome, final acceptance status, latency, and cost.
- Repeat-failure work item shaping:
  - `aggregate_eval_records` enriches repeated signatures into work items with:
    - layer, severity, proposed change, regression risk, rerun subset, keep/revert gates, owner.
- Review-path visibility:
  - Review escalation outcomes are joined from `AuditStore` review actions (`src/evals/agentic_feedback.py`).
- Trip-scoped API contract:
  - `GET /api/trips/{trip_id}/agentic-eval`
    - inputs: workflow + optional `workflow_unit_id`, thresholds
    - outputs: canonical evidence list + repeated-failure work items + routing metrics.
- Frontend contract:
  - API client contract test proves `workflow_unit_id` propagation into review actions and eval responses.
- Runtime safety and contract tests:
  - `tests/evals/test_agentic_feedback.py`, `tests/evals/test_agentic_eval_endpoint.py` now include repeated-failure, routing outcome, workflow-unit filtering, and contract coverage.

## What is still missing vs the doctrine

1. One-system evidence source
   - Evaluations still depend on multiple tables/files/feeds, not a single canonical eval view.
2. Full workflow surface
   - Coverage is strongest for extraction/confirmation flows; other workflows are partially instrumented.
3. Promotion enforcement
  - We can produce work items; we are not yet enforcing keep/revert/rollout gates in operator tooling.
4. Decision counterfactuals
   - We still need explicit side-by-side baseline-vs-alternative metrics for routing/fallback edits before change.

## I/O map for current loop

- Inputs:
  - `ExecutionEvent` records (`trip_id`, event metadata, actor/source, timestamps)
  - `AuditStore` review actions (`review_workflow_unit_id`, `escalation_outcome`)
  - Route params (`workflow`, `workflow_unit_id`, windows, thresholds)
- Transform:
  - Filter execution candidates by workflow
  - Join review outcomes by workflow unit
  - Aggregate repeated signatures and rolling route metrics
- Outputs:
  - `agentic-eval` response shape:
    - `canonical_evidence_records[]`
    - `work_items[]` with layer + fix recommendation + rerun/keep/revert fields
    - `routing_metrics` summary + path-level counts/latency/cost

## Project-level rules/skills now in force

- Shared Projects-level rulebook: `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md`
- Reusable skill: `/Users/pranay/Projects/skills/agentic-eval-loop/SKILL.md`
- Repo implementation artifact this slice: `Docs/research/AGENTIC_EVAL_CANONICAL_ROADMAP_2026-06-19.md`

Both should be used by future agents in this project and any project with AI workflow routing/fallback/review behavior.

## Next immediate build slice (in order)

1. Add a canonical eval export endpoint/view that joins events + review outcomes + cost/latency in one payload.
2. Add explicit false-escalation / missed-escalation counters for all major routing transitions.
3. Add work-item persistence API so repeated patterns create backlog entries with owners.
4. Add rollout mode metadata (`draft`, `shadow`, `measured`, `gating`, `default`) on rule/prompt/schema changes.
5. Add operator-facing dashboard for top repeated signatures and rerun outcomes.
