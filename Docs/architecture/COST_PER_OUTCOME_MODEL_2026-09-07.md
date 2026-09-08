# Cost-per-Outcome Model & Attribution Schema (2026-09-07)

**Status:** exploration package E-C output (PER-0700). Design for ratification; no code changed.
**Problem (PA-20, PA-34):** spend is metered at call time (`usage_guard` + `usage_events`, `usage_store.py:99-127`) but the records carry **no trip/run/decision correlation**, so the system cannot answer "what did this decision cost?" or "what does a delivered trip cost us vs one that escalated?" — and evals measure accuracy only, with no cost, latency, or human-intervention dimension anywhere (`manifest.yaml`, `metrics.py`).
**Why design before instrumentation:** attribution scattered per-call-site is unmigratable (PA-20's warning); the schema must exist first.

---

## 1. Principle

**Cost is an attribute of a decision, not of a call.** A traveler inquiry becomes money through a chain (extract → decide → compile → verify); the unit of business meaning is the decision (and, one level up, the trip outcome). Calls without a decision ancestor are infra cost (ingest, evals, sweeps) and are attributed to their system component instead — never dropped, never misattributed.

## 2. What gets attributed (the five cost dimensions)

| Dimension | Source | Notes |
|---|---|---|
| Model spend | `usage_events` (tokens × price per model — already metered) | per call |
| Tool/provider spend | adapters' result metadata (`provider_connected`, call counts) | simulated providers cost $0 but must still emit **call counts** so latency/complexity is visible |
| Retry/verification cost | recovery ladder executions (E-B's `recovery_actions_total`) | retries are cost multipliers; VERIFICATION re-runs are the expensive class |
| Latency | stage timings already checkpointed per run | wall-clock + per-stage |
| Human intervention | operator actions already audited (overrides, escalations resolved, repair edits) | each carries a cost-of-minutes estimate, agency-configurable |

## 3. Attribution schema (additive)

1. **Correlation context** — a request-scoped context (run_id, trip_id, decision_id, stage, agency_id) established at `POST /run` and propagated through the pipeline (the OTel span already exists as the carrier; `usage_events` gains nullable columns `run_id`, `trip_id`, `decision_id`, `stage`, `failure_class`).
2. **`decision_id`** — minted once per `run_gap_and_decision` invocation; it is the join key between cost and the audit event that explains the decision (PA-04's unified event stream is the consumer).
3. **Rollups** (materialized view or scheduled aggregate, agency-scoped):
   - `cost_per_decision` (by stage, by model, by failure_class from E-B)
   - `cost_per_outcome` (per trip terminal status: delivered / booked / escalated / abandoned)
   - `cost_per_eval_fixture` — eval lanes record cost alongside accuracy, enabling the autoresearch loop's `0.1·cost` term to read **real** numbers instead of hardcoded ones (PA-11's honesty gap closes with real data).
4. **Tenancy/privacy:** all rollups agency-scoped (RLS via existing `app.current_agency_id`); no traveler PII in cost records — only ids.

## 4. Where it lands (the three consumers)

1. **`/metrics` (PA-10):** `decision_cost_usd` histogram + `spend_total{agency,stage,model}` counters — the real metrics endpoint PA-10 demands, sourced from the same rollups.
2. **Operator UI:** cost rendered next to the persisted decision rationale (the anchor already exists in the audit timeline) — "this decision cost $X, fired rule Y, retried Z times" (PER-0700 Part D #3).
3. **Eval/autoresearch:** composite scoring's cost term reads measured fixture cost (PA-34's missing dimension), making the loop's accept/revert economics real.

## 5. Rollout sketch

Sequence: (1) add correlation columns to `usage_events` + establish context propagation at the run entry point, (2) emit decision_ids, (3) rollup job + `/metrics` gauges, (4) eval-lane cost recording, (5) operator UI. Steps 1–2 are the migration-critical pair; everything after is additive reads. No backfill: pre-correlation spend remains component-attributed infra cost.

## 6. Open questions for ratification

1. Latency as cost: convertible to dollars (via a configured rate) or reported separately? (proposed: separately — dollar conversion of time is policy, not measurement).
2. Human-intervention cost: per-agency configurable rate vs global default? (proposed: global default with agency override, off by default).
3. Do eval-lane runs get their own cost namespace so flywheel experiments never pollute production cost rollups? (proposed: yes, `context.kind = eval|production`).
