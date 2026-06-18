# Agentic Flow And Eval Audit

Date: 2026-06-18
Repo: `/Users/pranay/Projects/travel_agency_agent`
Scope: current agentic runtime, decision telemetry, audit/event surfaces, and evaluation doctrine

## Why this exists

This audit converts a set of user-authored articles on extraction evals, routing rules, fallback policy, and human review into:

1. a current-state audit of the repo's agentic workflow
2. a judgment on what is already strong vs weak
3. a reusable Projects-level ruleset and skill for future agent work across repos

The articles are useful because they do not stop at "which model is best." They consistently push toward:

- evals that produce the next work item
- logs that preserve the full workflow path
- routing rules as product behavior, not hidden plumbing
- explicit measurement of false escalation, missed escalation, review burden, cost, and latency
- field contracts that distinguish raw, normalized, missing, unknown, inferred, and not-applicable states

That is the right direction.

## Executive verdict

The current repo is much stronger on agent contract definition and runtime safety than the older docs suggest, but it is still weaker than the articles require on closed-loop learning and evaluation.

### What is genuinely good

1. The runtime now uses explicit agent contracts instead of vague "AI will do stuff" posture. `src/agents/runtime.py` defines `trigger_contract`, `input_contract`, `output_contract`, `idempotency_contract`, and `failure_contract` on every agent definition, which is exactly the right seam for controllable agentic behavior.
2. The runtime has deterministic ownership and retry boundaries. `src/agents/runtime.py` includes lease-based coordination, idempotency keys, retry budgets, and poisoned work handling.
3. The repo has a durable event model for at least one important surface. `spine_api/services/execution_event_service.py` validates event metadata against allowlists and makes timeline reads derive from events rather than current row state.
4. The autonomy surface is explicit enough to govern. `src/intake/config/agency_settings.py` and `frontend/src/app/(agency)/settings/components/AutonomyTab.tsx` expose approval gates, mode overrides, learning toggles, and reprocessing controls rather than burying them in code.
5. The decision layer already tracks cost/latency/source at a basic level. `src/decision/telemetry.py` captures decision type, source, latency, error, and cost; extraction providers also emit provider/model/latency/cost metadata.
6. The extraction event model already shows the right privacy instinct. `tests/test_extraction_events.py` proves the system intentionally logs safe metadata like provider/model/attempt/fallback rank while forbidding raw extracted fields, filenames, token payloads, and other risky artifacts.

### What is still weak or structurally incomplete

1. The repo has multiple telemetry systems instead of one canonical learning loop.
   - `src/intake/telemetry.py` writes JSONL telemetry
   - `src/decision/telemetry.py` keeps an in-memory singleton window
   - `spine_api/run_events.py` writes append-only JSONL per run
   - `spine_api/run_ledger.py` stores checkpointed steps
   - `spine_api/services/execution_event_service.py` writes SQL execution events
   This is better than no logging, but it fragments the evidence needed for evals.
2. Prompt, schema, routing, dictionary, and review provenance are not treated as one contract surface.
   - Extraction events currently prove provider/model/attempt/fallback metadata.
   - The audit did not find a canonical production record for `prompt_version`, `prompt_hash`, `schema_version`, normalization dictionary version, routing rule version, fallback trigger reason, or review outcome across the full workflow.
3. The repo has observability, but not enough decision-forensics.
   - It tracks that fallback/default/rule/LLM happened.
   - It does not yet consistently answer why fallback triggered, why review triggered, what counterfactual path would have happened, or whether the escalation was later judged correct.
4. `learn_from_overrides` exists as policy, but the learning loop is mostly aspirational.
   - The setting is real in `src/intake/config/agency_settings.py`.
   - The audit did not find a canonical system that converts repeated review corrections into prompt changes, schema fixes, dictionary updates, routing mutations, or review-rule changes.
5. The eval story is still mostly scaffolding and docs, not an executable promotion loop.
   - The repo contains terminology like `golden_path_evaluation` and `shadow_replay`.
   - The current state still looks closer to "evaluation vocabulary exists" than "every repeated failure becomes a tracked, rerunnable work item with owner and rerun gate."
6. Review outcome quality is under-modeled.
   - Human review exists in product language and escalation paths.
   - The repo does not yet expose a canonical metric layer for review acceptance, review correction type, review effort saved, false escalation rate, or missed escalation rate by workflow path.

## Repo-grounded audit

### 1. Runtime contracts are strong

The best current design choice is that the agent runtime is explicit and auditable by construction.

Evidence:

- `src/agents/runtime.py:56-104` defines the shared agent contract and execution result envelope.
- `src/agents/runtime.py:517-787` shows concrete agents with trigger/input/output/idempotency/failure contracts.
- `src/agents/runtime.py:777-820` includes a `QualityEscalationAgent` instead of treating escalation as implicit side-effect.

Why this is good:

- It makes agent behavior inspectable before runtime.
- It creates clean seams for future evals.
- It gives future shared skills a stable contract vocabulary to require across repos.

What is still missing:

- there is no canonical "eval finding -> contract mutation" workflow attached to these agent definitions
- there is no required field for rule version, prompt version, or review policy version in agent outputs

### 2. Autonomy policy is explicit, but learning is not closed-loop

Evidence:

- `src/intake/config/agency_settings.py:28-104` defines approval gates and mode overrides.
- `src/intake/config/agency_settings.py:70-78` includes `learn_from_overrides`, `auto_reprocess_on_edit`, and `allow_explicit_reassess`.
- `frontend/src/app/(agency)/settings/components/AutonomyTab.tsx` exposes those controls in the operator UI.

Why this is good:

- It treats autonomy as policy, not magic.
- It supports different risk postures by mode and decision state.

What is still weak:

- the policy flag says learning is allowed, but not how learning becomes a safe change
- there is no visible canonical path from override evidence to prompt/routing/schema backlog items
- there is no promotion threshold such as "same correction repeated N times across M documents"

### 3. Eventing is serious, but split

Evidence:

- `spine_api/services/execution_event_service.py:1-220` is the strongest event layer in the repo. It validates event category, actor type, source, and metadata keys.
- `spine_api/run_events.py` provides append-only per-run event logs.
- `spine_api/run_ledger.py` stores step checkpoints.
- `src/intake/telemetry.py:1-96` writes lightweight quality telemetry outside the event ledger.
- `src/decision/telemetry.py:19-199` stores in-memory decision metrics.

What is good:

- The repo understands that event contracts matter.
- The SQL execution event service is privacy-aware and structured.
- The run ledger makes step outputs inspectable.

What is bad:

- There is no single evidence plane for agentic evaluation.
- The same workflow can require reading SQL events, JSONL events, checkpoint files, and singleton memory.
- That fragmentation makes it hard to compute false escalation, fallback usefulness, and review burden in one place.

### 4. Decision telemetry exists, but it is not yet an evaluation system

Evidence:

- `src/decision/telemetry.py:19-199` captures decision type, source, latency, cost, and errors.
- `src/extraction/gemini_vision_client.py:137-157` and its OpenAI counterpart add provider/model/latency/token/cost metadata.
- `tests/test_extraction_events.py:40-255` proves the extraction event metadata is deliberate and privacy-aware.

What is good:

- The repo measures more than accuracy.
- The extraction path already records attempt number and fallback rank.

What is missing relative to the articles:

- no canonical `fallback_trigger_reason`
- no canonical `review_trigger_reason`
- no canonical `review_outcome`
- no canonical `accepted_after_fallback`
- no canonical `false_escalation` and `missed_escalation` labels
- no canonical `next_fix_layer`
- no durable per-run provenance for prompt/schema/dictionary/routing versions

### 5. The articles are highly useful, but need one more layer

The articles are strong because they are operational. They already beat most generic eval writing.

Their strongest ideas:

1. Scores are summaries, not the loop.
2. Repeated failures should become work items.
3. The fix layer may be prompt, schema, parser, dictionary, routing, fallback, or review.
4. Routing rules need evals too.
5. Cost, latency, review effort, and fallback frequency belong inside the evaluation.
6. Ground truth must separate extracted vs missing vs unknown vs inferred vs not-applicable.
7. Model rankings are less useful than routing policy.

Where they can be strengthened further:

1. Add a canonical event schema so the logging layer is implementation-ready.
2. Add severity taxonomy:
   - extraction defect
   - unsupported inference
   - schema break
   - unsafe acceptance
   - avoidable review
   - avoidable fallback
3. Add promotion thresholds:
   - when a repeated issue becomes a work item
   - when a work item becomes a routing rule
   - when a routing rule can be retired
4. Add ownership fields:
   - fix owner
   - rerun subset
   - keep/revert condition
5. Add counterfactual review:
   - what would have happened without fallback
   - what would have happened without review
6. Add rollout mode:
   - draft
   - shadow
   - measured
   - gating
   - default

## What should change in this repo

### P0: Create one canonical agentic-eval evidence record

Every meaningful AI workflow path should be able to emit one record shape that answers:

- input artifact or workflow unit
- workflow type
- model/provider
- prompt version/hash
- schema version
- dictionary/normalization version
- routing rule version
- fallback trigger reason
- fallback result
- review trigger reason
- review outcome
- final acceptance status
- cost
- latency
- error labels
- next-fix layer

Without this, the repo will keep having "telemetry" without a durable improvement loop.

### P1: Treat repeated failures as first-class backlog generation

Add a canonical eval-finding format that stores:

- failure signature
- affected layer
- severity
- proposed fix
- rerun subset
- keep/revert threshold

This should live next to the eventual eval harness, not only in docs.

### P1: Measure routing quality directly

The system should be able to label:

- false escalation
- missed escalation
- useful fallback
- wasteful fallback
- correct review
- unnecessary review

At minimum, do this for:

- extraction fallback
- quality escalation
- proposal/booking readiness agents

### P1: Connect override learning to concrete mutation classes

`learn_from_overrides` should not mean "silently adapt."

It should mean:

- repeated review correction -> candidate prompt change
- repeated raw-value loss -> schema split or parser/dictionary fix
- repeated hallucinated field -> tighter routing/review rule
- repeated low-value fallback -> fallback trigger change
- repeated accepted manual correction -> review checklist or dictionary update

### P2: Collapse fragmented telemetry surfaces behind a canonical export

The repo does not have to delete its current ledgers immediately, but it should expose a canonical export that joins:

- execution event
- run ledger meta
- run event path
- decision telemetry
- extraction attempt telemetry
- review result

That joined surface is what eval tooling should consume.

## Shared rules extracted from this audit

The shared Projects-level ruleset created alongside this audit is:

- `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md`

The reusable skill created from this audit is:

- `/Users/pranay/Projects/skills/agentic-eval-loop/SKILL.md`

Those artifacts intentionally encode the strongest lessons from the articles:

- evals must produce work items
- routing rules need evals
- logs must preserve the path, not only the final score
- repeated failures must map to the correct fix layer
- review must be measured as part of the workflow, not treated as an opaque escape hatch

## Suggested next implementation slice

If this repo wants the highest-leverage real implementation next, the best slice is:

1. define one canonical `AgenticEvalRecord`
2. emit it for extraction attempts, fallback attempts, and quality escalation
3. add labels for `fallback_trigger_reason`, `review_trigger_reason`, and `review_outcome`
4. create a simple reducer that groups repeated failures into proposed work items
5. run that reducer on one golden/shadow subset before widening scope

That would move the repo from "good contracts and partial telemetry" to the start of a real eval-to-improvement loop.
