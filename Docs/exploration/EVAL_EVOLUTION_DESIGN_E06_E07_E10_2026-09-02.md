# Eval Evolution Design: E-06 Trajectory, E-07 Production Shadow-Eval + Calibrated Judge, E-10 Warnings-Assertable Gate

**Date:** 2026-09-02 (written 2026-09-03)
**Persona lens:** PER-0897 Agent Evaluation Architect — "What evidence proves this agent reliably achieves the intended task?"
**Parent doc:** `Docs/exploration/EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT_2026-08-31.md` §4 (this deepens Phases 4 and 5 and adds the warnings-assertable gate surface that audit doc's Phase 2 adversarial table assumes but never specifies).
**Scope:** DESIGN + RESEARCH ONLY. Read-only on code; no DB writes; dev server :8000 untouched.

---

## 0. Evidence Baseline — What Exists Today (file:line)

Every design claim below builds on this inventory. Nothing here needs to be invented; the work is wiring + assertion surfaces.

### 0.1 The run ledger (trajectory record, never yet consumed by any eval)

| What | Where |
|---|---|
| Canonical step vocabulary `KNOWN_STEPS = (packet, validation, decision, strategy, safety, output, blocked_result)` | `spine_api/run_ledger.py:49` |
| `RunLedger.create()` → QUEUED meta with `run_id, trip_id, draft_id, stage, operating_mode, agency_id, started_at` | `spine_api/run_ledger.py:84-124` |
| `RunLedger.set_state()` enforcing `assert_can_transition` (invalid transitions raise) | `spine_api/run_ledger.py:127-148` |
| `RunLedger.save_step()` — per-step checkpoint with `checkpointed_at` ISO timestamp | `spine_api/run_ledger.py:151-177` (timestamp at `:171`) |
| Terminal writers: `complete(total_ms)` / `fail(error_type, error_message)` / `block(block_reason)` | `spine_api/run_ledger.py:180-229` |
| `update_meta()` — late-binding `trip_id` after save | `spine_api/run_ledger.py:232-244` |
| Reads: `get_meta` / `get_step` / `get_all_steps` / `list_runs(trip_id, state, limit)` | `spine_api/run_ledger.py:251-314` |
| `timeout_stale_runs(300s)` — queued/running → FAILED sweep | `spine_api/run_ledger.py:317-361` |
| Run state machine: `queued→running\|failed`, `running→completed\|failed\|blocked`, terminals frozen | `spine_api/run_state.py:60-66` |
| **Volume:** 16,034 run directories under `data/runs/` | measured 2026-09-03 via `ls data/runs \| wc -l` |

### 0.2 The ExecutionEvent stream (per-run events.jsonl)

| What | Where |
|---|---|
| Event types: `run_started, pipeline_stage_entered, pipeline_stage_completed, run_completed, run_failed, run_blocked` | `spine_api/run_events.py:68-77` |
| `emit_stage_completed(stage_name, execution_ms)` — **per-stage latency already recorded** | `spine_api/run_events.py:177-189` |
| `get_run_events(run_id)` chronological reader | `spine_api/run_events.py:121-141` |
| Stage checkpoint writer: `_stage_checkpoint` saves step artifacts + emits entered/completed with wall-clock timing; stage failure writes `{stage}_failed` step | `spine_api/services/pipeline_execution_service.py:238-287` |
| Blocked paths write `blocked_result` step (packet/validation/decision/`early_exit_reason`/**`trip_id`**) then `run_ledger.block()` + `emit_run_blocked` | early-exit: `pipeline_execution_service.py:316-414` (`blocked_result` step `:397-404`); validation-invalid: `:467-488` |
| Post-save trip linkage: `run_ledger.update_meta(run_id, trip_id=trip_id_saved)` | `pipeline_execution_service.py:389, 459, 535` |
| Agency-scoped read surface `GET /runs`, `GET /runs/{run_id}` (steps + events) | `spine_api/routers/run_status.py:22-80` |

### 0.3 The product-agent runtime (leases / idempotency / DLQ / retry)

| What | Where |
|---|---|
| `WorkStatus` 7 states incl. `RETRY_PENDING, POISONED, ESCALATED, INTERRUPTED_RECOVERABLE` | `src/agents/runtime.py:41-48` |
| `ExecutionLease` (TTL 60s default, heartbeat, `is_expired`) | `src/agents/runtime.py:52-83` |
| `ExecutionCheckpoint` + `CheckpointStore` (deterministic recovery) | `src/agents/runtime.py:87-127` |
| `ZombieLeaseSweeper.sweep()` — expired-lease reclaim list | `src/agents/runtime.py:131-142` |
| `DeadLetterQueue.quarantine()` + record shape | `src/agents/runtime.py:145-167`; inspector `src/agents/dlq_inspector.py:39` |
| `InMemoryWorkCoordinator` — idempotent re-entry (`idempotent_reentry_completed`), lease-conflict refusal, completed/poisoned sets | `src/agents/runtime.py:263-355` |
| `build_default_registry()` — **19 product agents** (audit doc said 18; actual count is 19, includes `CommunicatorAgent` and `OperatorRefinementAgent`) | `src/agents/runtime.py:3242-3261` |
| `AgentEventType`: `agent_started/decision/action/failed/retry/escalated` envelope | `src/agents/events.py:16-23` |
| Durable idempotency: `SqlIdempotencyBackend` / `IdempotencyRegistry` | `src/agents/idempotency.py:61, 359` |
| SQL coordinator + supervisor wiring (lease_seconds=60) | `spine_api/services/agent_work_coordinator.py:15`; `spine_api/services/agent_runtime_factory.py:236-244` |
| Requeue ports (inline/SQL queue) + RecoveryAgent | `src/agents/requeue.py:96-191`; `agent_runtime_factory.py:219-233` |

### 0.4 Routing metrics + the D6 gate snapshot

| What | Where |
|---|---|
| `build_routing_metrics(events)` — fallback trigger/useful/wasteful rates, review correction, false/missed escalation, latency p50/p95, cost | `src/evals/agentic_feedback.py:508-603` |
| `DEFAULT_ROUTING_HEALTH_THRESHOLDS` (fallback warn 0.30/crit 0.50; escalation warn 0.20/crit 0.40; review-correction warn 0.30/crit 0.50; p50 5s/10s; p95 15s/30s) | `src/evals/agentic_feedback.py:777-790` |
| `check_routing_health(metrics, thresholds)` → `RoutingHealthReport` (healthy/warning/critical + alerts) | `src/evals/agentic_feedback.py:869-940` |
| `aggregate_eval_records(events, min_occurrences=3, window_minutes=1440)` — windowed reducer already written | `src/evals/agentic_feedback.py:943-1021` |
| Trip-scoped service bridge over ExecutionEvents + audit review events | `spine_api/services/agentic_eval_service.py:28-59` |
| **The gap:** D6 snapshot calls `build_routing_metrics([])` — an **empty event list**, so `routing_health` in every snapshot to date is vacuously healthy | `src/evals/audit/snapshot.py:833` |
| Snapshot builder / stable view / drift verify | `snapshot.py:818-922` / `:950-1044` / `scripts/verify_d6_gate_snapshot.py:29-116` |
| Manifest statuses `gating\|shadow\|planned`;`blocks_ci = gating && !meets_thresholds` | `src/evals/audit/manifest.yaml`; `src/evals/audit/gates.py:73-85` |

### 0.5 The unused judge

| What | Where |
|---|---|
| 7 agent rubrics, weighted 0–10 dimensions, pass_threshold 7.0/8.0 | `src/evals/judge/rubrics.py:201-249` |
| `judge_agent_output()` — LLM scoring via `BaseLLMClient.decide` (schema-constrained JSON, temp 0.2) with deterministic heuristic fallback; per-dimension `scoring_method` = `llm\|heuristic\|mixed`; verdict`pass\|needs_review\|fail` (fail band = threshold − 2.0) | `src/evals/judge/scorer.py:340-455` (method classification `:431-436`) |
| `build_judge_report()` — per-agent pass_rate/average/worst/verdict histogram, snapshot-ready | `src/evals/judge/scorer.py:458-503` |
| LLM client contract `decide(prompt, schema, temperature)` / `is_available()` | `src/llm/base.py:13, 40, 63` |
| PII egress hygiene: `strip_pii()` (email/phone/passport/card patterns), `prepare_egress_payload()`, audit log with per-call `pii_redactions` count | `spine_api/core/llm_egress.py:181-191, 220, 150-167` |

### 0.6 Warning codes (E-10's subject)

| What | Where |
|---|---|
| `ValidationIssue` (severity/code/message/field) + `PacketValidationReport.warnings` / `warning_count` | `src/intake/validation.py:72-97` |
| Warning codes emitted: `QUOTE_READY_INCOMPLETE` (:124), `LOW_CONFIDENCE_FACT` (:220), `HIGH_AMBIGUITY` (:229), `MANY_STUBS` (:238), `PARTY_UNDERDETECTED` (:254-262 — fires when `party_size ≤ 1` AND `"group_signals:"` in party notes), `PARTY_UNPARSED_GROUP_PHRASING` (:263-273 — unknowns note prefix `unparsed_group_phrasing`) | `src/intake/validation.py` |
| Journey smoke already asserts ledger validation banner (`is_valid is False` from `blocked_result` step) — the pattern E-10 extends to warnings | `tests/test_journey_smoke.py:268-275` |
| Fixture schemas: `AuditFixture` (pydantic `extra="forbid"`; findings/decision_state only — **no warning assertion surface**), colloquial golden (`expected_extracted_fields`), pipeline golden (`expected_extraction/agents/decision`) | `src/evals/audit/fixtures.py:29-44`; `data/fixtures/extraction/colloquial_golden.json`; `data/fixtures/pipeline/pipeline_golden.json` |

---

## 1. E-06 — Trajectory Evaluation over the Run Ledger

### 1.1 Problem (PER-0897 framing)

Outcome metrics (field F1, decision accuracy) prove the agent reached a good answer. They do **not** prove the agent reached it *the right way*. A run that blocks before decision, invents a strategy before a decision exists, or saves two trips for one inquiry can score perfectly on field F1 while being operationally wrong. The ledger already records the full trajectory for all 16,034 historical runs — stage order, timestamps, per-stage outputs, terminal state and reason — and **no eval consumes it**. Trajectory evaluation converts this record from archaeology into evidence.

### 1.2 Architecture

New module `src/evals/trajectory.py` (extends, does not fork, the audit eval package — same relationship `rules/pipeline.py` has to `snapshot.py`):

```text
src/evals/trajectory.py
    TrajectoryExpectation        # declarative per-fixture contract (dataclass)
    extract_trajectory(run_id)   # ledger meta + get_all_steps + get_run_events → Trajectory object
    assert_trajectory_contract(traj, expectation) -> list[TrajectoryViolation]
    score_trajectory_set(...)    # reduces violations + latency/exit distributions → snapshot section
scripts/run_trajectory_audit.py  # production walker (shadow lane, nightly)
```

The trajectory object is built from three sources that already exist: `RunLedger.get_meta(run_id)`, `RunLedger.get_all_steps(run_id)` (each checkpoint carries `checkpointed_at`, `run_ledger.py:168-177`), and `get_run_events(run_id)` (stage enter/exit with `execution_ms`, `run_events.py:177-189`).

### 1.3 Deterministic trajectory assertions (the contract vocabulary)

**T1 — Stage-sequence correctness.** For every run: the set of checkpointed steps ⊆ `KNOWN_STEPS` (`run_ledger.py:49`) and, ordered by `checkpointed_at`, respects the pipeline DAG:

- `packet` before `validation` before `decision` before `strategy` (the "no strategy-before-decision" rule; ordering is the anti-pattern guard: compare timestamps, never step-list strings).
- `blocked_result` step exists **iff** `meta.state == "blocked"` (`:215-229` is the only `block()` writer; `pipeline_execution_service.py:406, 480, 586` are the only block callers).
- Exactly **one** terminal event (`run_completed` XOR `run_failed` XOR `run_blocked`) in events.jsonl, matching `meta.state`.
- No steps written after the terminal timestamp (a checkpoint post-terminal means the state machine and the step writer disagreed).
- Replay conformance: the sequence of states implied by events must be reachable under `_ALLOWED_TRANSITIONS` (`run_state.py:60-66`) — import and reuse `can_transition`, do not duplicate the table.

**T2 — Blocked-lead contract (ADR_ESCALATE_LEAD_PERSISTENCE regression teeth).** For every `state == blocked` run with `early_exit_reason` in `{"ESCALATE", validation_invalid}`:

- `blocked_result.data["validation"]["is_valid"] is False` (journey smoke already asserts this shape at `tests/test_journey_smoke.py:274-275`).
- `blocked_result.data["trip_id"]` is present (the blocked lead was persisted — `pipeline_execution_service.py:397-404`) **unless** the block was `StrictLeakageViolation` (`:571-598`, where suppression is the correct behavior).
- `meta.trip_id` equals `blocked_result.data["trip_id"]` when both present (the `update_meta` at `:389` ran).

**T3 — Stage-latency budgets.** Reduce `pipeline_stage_completed.execution_ms` per stage. Per-stage budget table lives in a new `src/evals/audit/trajectory_budgets.yaml` (packet ≤ 1500ms, validation ≤ 500ms, decision ≤ 2000ms, strategy ≤ 3000ms, total `meta.total_ms` p95 ≤ 6000ms — initial values to be calibrated from the existing `data/runs/` distribution in a one-off probe before gating). Metrics reported: per-stage p50/p95/max, budget-exceed count. This is the trajectory analogue of `latency_by_candidates` (`agentic_feedback.py:589-594`), but stage-attributed, so *which* stage regressed is visible instead of a single run-level p95.

**T4 — Side-effect / tool correctness (the "one trip per run" rule).** Over a set of runs sharing `meta.draft_id`:

- Exactly one distinct `meta.trip_id` after the first successful save (draft→trip is 1:1; reprocess must `preserve_trip_id` — `pipeline_execution_service.py:51-84, 501-535`).
- Zero orphan drafts: every draft touched by a run reaches a terminal `run_state` matching the run's terminal (`_update_draft_for_terminal_state`, `:15-48`).
- Audit event emitted per save with the run's `agency_id` (spot-assert in CI journeys via AuditStore; in production, counted, not asserted row-by-row).

**T5 — Agent-runtime (19-agent) tool/delegation correctness.** Graded against the coordinator primitives, CI-deterministic via `InMemoryWorkCoordinator` (`runtime.py:263-355`):

- **Idempotency:** submitting a `WorkItem` whose `idempotency_key` already completed returns `idempotent_reentry_completed` and does **not** re-execute the agent callable (`:283-286`).
- **Lease exclusivity:** a second `acquire` on a RUNNING leased key is refused while unexpired (`:289-296`); `ZombieLeaseSweeper.sweep()` reclaims exactly the expired set and no live ones (`:131-142`).
- **Retry/escalation-path scoring:** a synthetic flaky agent that fails N−1 times then succeeds terminates `COMPLETED`; one that always fails terminates `POISONED` and lands exactly one `DeadLetterQueue` record (`:145-167`); escalation path terminates `ESCALATED` — i.e., every retry chain converges to a legal `WorkStatus` and never loops. Score = fraction of synthetic chains converging correctly (target 1.0 — these are deterministic unit-of-work properties, not statistics).
- **Recovery/requeue:** `RecoveryAgent` + `build_requeue_port` (`agent_runtime_factory.py:219-233`) replays an interrupted checkpoint and completes without duplicating side effects (checkpoint from `CheckpointStore`, `:87-127`).

### 1.4 CI-able vs production-shadow split

| Lane | Runs where | Data source | Status |
|---|---|---|---|
| **CI trajectory lane** (deterministic) | pytest, in-process | `journey_env`-style isolation (`tests/test_journey_smoke.py:41-72` monkeypatches `run_ledger.RUNS_DIR` to tmp_path; `TRIPSTORE_BACKEND=file` pinned) | `gating` from day one — these are state-machine properties; flaky = real bug |
| **Production trajectory shadow** | nightly script | 16,034-dir `data/runs/` walk + events reduction | `shadow` → `gating` after 2 clean weeks (see thresholds below) |

**How the journey smoke generalizes:** extract the ledger-assertion fragment of `tests/test_journey_smoke.py` (lines 268-275) into `assert_trajectory_contract(run_id, TrajectoryExpectation(...))`. Each journey fixture then declares expectations declaratively:

```python
TrajectoryExpectation(
    terminal_state="blocked",
    required_steps={"packet", "validation", "blocked_result"},
    forbidden_order=[("strategy", "decision")],
    blocked_carries_trip_id=True,
    expected_warnings=[WarningExpectation(code="MVB_MISSING", field="date_window")],  # E-10 hook
    stage_latency_budget_ms={"packet": 1500, "validation": 500},
)
```

The four CI journeys mirror the audit doc Phase 3 set (clean success, missing-basics ESCALATE, partial_intake, validation_invalid) plus two runtime journeys (flaky-agent retry chain; poisoned→DLQ). Each asserts structure (enums, step sets, orderings, id fields) — never response strings.

### 1.5 Wiring into the D6 snapshot (replace the vacuous placeholder)

`snapshot.py:833` currently passes `[]` to `build_routing_metrics`. The trajectory work supplies the honest replacement: the gate's own pipeline/colloquial fixture runs are executed through `execute_spine_pipeline`'s in-process path with ledger enabled (the journey pattern), and the resulting `ExecutionEvent`-shaped stage events feed `build_routing_metrics(events)` — so `fallback_trigger_rate`, `review_correction_rate`, and latency p50/p95 in `routing_health` finally move when routing policy regresses (the audit doc's Phase 4 second bullet, specified here). A new snapshot section `trajectory_health` carries: `runs_checked`, `sequence_violations`, `blocked_contract_violations`, `stage_latency` (per-stage p50/p95 vs budget), `side_effect_violations`, `status`, `blocks_ci`.

### 1.6 Thresholds / gates

- CI lane: **zero** sequence/blocked-contract/side-effect violations tolerated (`min_pass_rate = 1.0`); latency budgets warn-only for the first month, then p95 budgets gate.
- Production shadow lane gates on: sequence-violation rate ≤ 0.5% of runs in window (ledger writer bugs happen mid-deploy), stale-timeout rate ≤ 1%, blocked-contract violation rate = 0 (that one should be absolute).
- Manifest: new category `trajectory` (`status: shadow` initially, `min_accuracy: 0.995` when flipped).

### 1.7 Failure modes (PER-0897 lens)

| Failure mode | Mitigation designed in |
|---|---|
| **Trajectory eval that only checks outcomes** | T1/T2 assert *how* the terminal was reached, not just which |
| **Single-run testing anti-pattern** | CI lane covers 6 trajectories spanning all 3 terminal states + both retry chains; production lane is a distribution over the 16k-run corpus |
| **String-matching fragility** | All assertions compare enums/step-sets/timestamps/id fields; no substring checks on payloads |
| **Clock-skew false positives** | Stage ordering uses `checkpointed_at` from a single monotonic writer process; tolerances: ordering violations only flagged when gap > 1ms |
| **Eval writes polluting prod data** | CI lane never touches `data/runs/` (tmp_path monkeypatch is already the established pattern, `tests/test_journey_smoke.py:72`); production walker is read-only |
| **Ledger gaps mistaken for violations** | Pre-deploy-window runs without a step that post-dates a deploy commit are excluded via `meta.created_at` vs git-sha annotation (open question 5) |

### 1.8 Effort

**~1.5–2 agent-days**: `trajectory.py` (T1–T4: 0.5d), agent-runtime synthetic chains T5 (0.5d), snapshot wiring + budgets yaml + verify-script extension (0.25d), production walker script (0.25d).

---

## 2. E-07 — Production Shadow-Eval + Calibrated Model-Judge

### 2.1 Problem (PER-0897 + PER-PDEV-0425 framing)

Offline gates grade a curated corpus. Production truth is the 16,034-run ledger, and the two genuinely LLM-graded surfaces (document vision extraction; hybrid decision risk verdicts) have **no live grading at all** — the judge module (`src/evals/judge/`) exists and is unused, and the thresholds in `DEFAULT_ROUTING_HEALTH_THRESHOLDS` (`agentic_feedback.py:777-790`) have never been load-bearing because they are fed an empty list. Meanwhile the single most-cited failure of "model-as-judge" is deploying a judge **without calibration against human labels** — an uncalibrated judge manufactures evidence, which is worse than no evidence (it looks like coverage).

### 2.2 Architecture

```text
scripts/run_production_eval.py          # nightly job (local cron / LaunchAgent — data/runs is machine-local)
    window walk: RunLedger.list_runs(limit≈window) + execution_event_service events
    → aggregate_eval_records(...)        # EXISTS: agentic_feedback.py:943-1021
    → check_routing_health(...)          # EXISTS: thresholds become load-bearing
    → judge_sample(runs, policy)         # NEW (below)
    → write data/evals/production/production_eval_<YYYY-MM-DD>.json
    → append alert entry to Docs worklog + non-zero exit on critical
```

This is the audit doc's Phase 5 nightly job, specified to the sample level. **No DB writes** — the walker only reads `data/runs/` files and queries ExecutionEvents read-only.

### 2.3 Judge lanes (what gets graded)

Two rubric families added to `rubrics.py` alongside the seven existing agent rubrics (same `RubricDimension`/`AgentRubric` types — no new scoring machinery):

1. **Brief groundedness** (input: redacted note + packet brief/summary fields). Dimensions: `no_unsupported_facts` (weight 2.0 — every asserted brief fact traceable to the note), `no_dropped_material_facts` (1.5), `authority_hygiene` (1.0 — derived signals never stated as facts). Pass threshold 7.0.
2. **Extraction completeness** (input: redacted note + extracted fact slots). Dimensions: `field_coverage` (2.0 — all stated facts captured), `value_fidelity` (1.5 — captured values match note semantics), `no_invented_values` (2.0 — hallucination dimension, the DEMO-02 date-invention class). Pass threshold 7.0.

Grading plumbing reuses `judge_agent_output` verbatim: `llm_client.decide(prompt, schema=_DIMENSION_SCORE_SCHEMA, temperature=0.0)` (tighten the existing 0.2 → 0.0 for the shadow lane; `scorer.py:320`), with the `JudgeScore.scoring_method` field (`scorer.py:431-436`) carried through so heuristic-fallback scores are **never** mixed into LLM-scored aggregates — a heuristic fallback score under an LLM lane is reported as `scoring_method: "heuristic"` and counted separately (see failure modes).

### 2.4 Judge-prompt design

- Single-output grading (no pairwise ranking) to avoid position bias; one rubric dimension per `decide()` call, exactly as `_build_dimension_prompt` already structures (`scorer.py:254-297`).
- Structured output only: `{score: 0-10, reasoning}` against the existing `_DIMENSION_SCORE_SCHEMA` (`scorer.py:238-251`); clamp to [0,10] already implemented (`scorer.py:336`).
- The judge sees **structured facts + redacted text**, never raw notes (§2.7).
- Rubric versions are content-hashed into the snapshot (`rubric_hash`) so score drift is attributable to rubric changes vs model drift.

### 2.5 Calibration protocol (the anti-"uncalibrated judge" mechanism)

- **Gold set:** 60 examples (30 groundedness, 30 completeness), stratified pass/fail/edge, human-labeled by Pranay, stored in-repo at `data/fixtures/judge_calibration/` (versioned; never tuned against — same discipline as the holdout policy in audit doc Phase 2).
- **Agreement metric:** raw agreement + **Cohen's κ** on the binary pass/fail projection (and on the 3-band verdict). κ is ~10 lines of pure Python (`κ = (p_o − p_e)/(1 − p_e)`); no new dependency (no scipy/sklearn in `pyproject.toml` today — verified).
- **Gate to influence:** the judge lane reports scores but the lane's `trusted: false` flag stays until **κ ≥ 0.60** (substantial agreement) on the gold set. Recalibration (re-run gold set) is required on any change to rubric text, judge model, or prompt template (hash-tracked).
- **Escalation path:** κ in [0.40, 0.60) → judge output feeds `needs_review` queues only; κ < 0.40 → judge disabled (lane reports `calibration: failed`, zero scores published).
- **Promotion to gating:** after 2 consecutive months of κ ≥ 0.60 AND stable gold-set scores (±0.5), the lane may flip `shadow → gating` in the manifest — a ratification decision, not automatic.

### 2.6 Sampling policy + cost budget

- **Volume basis:** `data/runs/` holds 16,034 runs total; assume ~50–200 runs/day live. Budget: **≤ 120 judge calls/day** (each run × 2 lanes × ~3 dimensions ≈ 6 calls, so ~20 runs/day ≈ 10–20% sample).
- **Stratified sampler:** (a) 100% of blocked/ESCALATED runs in window (small population, highest business stakes); (b) uniform random sample of completed runs to fill the remainder; (c) oversample any run whose `prompt_hash`/`schema_version` metadata (`agentic_feedback.py:240-244`) is new since the last eval day (prompt-change canaries).
- **Dedup cache:** judge results keyed by `(rubric_hash, model, sha256(redacted_input))` — identical re-submissions (draft reprocess) do not re-bill.
- **Cost ceiling enforced in code:** the sampler hard-stops at the daily budget and records `budget_exhausted: true` in the snapshot; an over-budget judge is a defect, not a feature. Estimated cost at 120 calls/day with a small-model judge: low single-digit USD/day ceiling — the *cap* is the design commitment; exact $ depends on model choice (open question 2).

### 2.7 PII hygiene — nothing identifiable leaves the deployment

- **Raw notes never enter a judge prompt.** The lane assembles judge input from: (1) `strip_pii()`-processed note text (`spine_api/core/llm_egress.py:181-191` — emails/phones/passports/cards → typed placeholders), and (2) structured packet facts, which are field values (cities, dates, party sizes, budget bands), not identity fields. Traveler names/bundles are excluded from the projection entirely.
- **Local-egress invariant:** `prepare_egress_payload` + the per-call `pii_redactions` audit count (`llm_egress.py:150-167`) are invoked for every judge call; the daily snapshot reports `total_pii_redactions` and the lane refuses to run if the egress audit log shows a call that bypassed `prepare_egress_payload`.
- **Hard option:** if the judge model must be external (open question 6), the invariant above is the contract; if a self-hosted/local judge is preferred, the same interface (`BaseLLMClient`) admits it without lane changes.

### 2.8 Flow into the D6 snapshot as a NON-gating shadow lane

New snapshot section `judge_shadow` (sibling to `routing_health`/`colloquial_health`, added to `build_gate_snapshot` and `stable_snapshot_view`):

```json
{
  "status": "shadow",
  "blocks_ci": false,                       // structurally impossible while status == "shadow"
  "calibration": {"kappa": 0.63, "gold_set_size": 60, "trusted": true, "rubric_hash": "..."},
  "lanes": {
    "brief_groundedness": {"scored": 14, "pass_rate": 0.86, "avg": 7.9, "scoring_method_mix": {"llm": 14}},
    "extraction_completeness": {"scored": 14, "pass_rate": 0.71, "avg": 7.1, "scoring_method_mix": {"llm": 12, "heuristic": 2}}
  },
  "sampling": {"runs_in_window": 87, "sampled": 20, "budget_calls": 120, "used_calls": 84, "budget_exhausted": false},
  "pii": {"total_redactions": 31, "egress_bypass_events": 0},
  "alerts": [...]
}
```

Nightly production snapshots land under `data/evals/production/` (separate from the CI `d6_audit_gate_snapshot.json`); the CI snapshot carries the judge section only when the judge ran in-CI against the calibration set (small, cheap, keeps calibration honest on every PR).

### 2.9 Failure modes (PER-0897 lens)

| Failure mode | Mitigation |
|---|---|
| **Uncalibrated model-as-judge influencing decisions** | §2.5 κ-gate; `trusted:false` structurally prevents gating (`blocks_ci` hardcoded false while untrusted); recalibration on any rubric/model/prompt hash change |
| **Judge scores silently degrading to heuristic fallback** | `scoring_method_mix` is a first-class snapshot field; a lane whose llm share drops below 90% raises an alert — heuristic scores under an LLM lane are shape-checks, not quality grades |
| **Judge grading the pipeline's own defaults (tautology)** | Judge input is note-vs-output; the deterministic pipeline's facts are inputs to grading, never the reference; gold set provides the external reference |
| **PII egress** | Typed redaction before assembly + audit-count assertion + projection excludes identity fields (§2.7) |
| **Cost run-away** | Hard daily call cap in the sampler; dedup cache; budget telemetry in every snapshot |
| **Judge drift vs model drift conflation** | `rubric_hash` + `model` pinned per snapshot; gold set re-run on change separates the two |
| **Shadow lane becomes shelfware** | Alerting contract: critical routing-health from the same nightly job writes a dated worklog entry + fails the job; the judge lane adds `needs_review` queue entries once trusted |

### 2.10 Effort

**~2.5–3 agent-days**: nightly walker + snapshot writer (0.5d), two rubrics + input-projection/redaction adapter (0.5d), calibration harness (gold-set runner + κ function + trusted-flag logic) (0.5d), sampler with budget/dedup (0.5d), snapshot section + verify-script extension + docs (0.5d). **Excludes** the human labeling of 60 gold examples (Pranay, ~2–3h) — flagged as a blocking dependency for `trusted: true`, not for lane construction.

---

## 3. E-10 — Warnings-Assertable Gate Format

### 3.1 Problem

`PARTY_UNDERDETECTED` and `PARTY_UNPARSED_GROUP_PHRASING` exist as machine-readable codes on `PacketValidationReport.warnings` (`src/intake/validation.py:254-273`) — born from DEMO-02, where a "we are 4 of us" note silently collapsing to `party_size=1` was a P0 real-world failure. But the D6 gate has **no surface to assert a warning**: the colloquial lane compares packet fields only (`_COLLOQUIAL_FIELD_MAP`, `snapshot.py:52-65`), fixtures carry `expected_extracted_fields` with no warnings key, and `AuditFixture` is pydantic `extra="forbid"` with findings-shaped fields only (`fixtures.py:29-44`). Consequently: a regression that *stops emitting* a needed warning, or one that *fires on clean input* (noise → operator alert fatigue), is invisible to every gate. Warnings are data-loss-prevention signals (`validation.py:244-249`); unaudited prevention decays.

### 3.2 Design principle

Warnings get their own graded axis with **separate precision and recall**, because the two failure directions have different business costs:

- **Warning recall miss** (expected warning didn't fire) = silent data loss risk (the original DEMO-02 P0 class).
- **Warning precision miss** (warning fired on input where the fixture asserts none) = alert-noise risk. A warning that fires on clean input **is a false positive, full stop** — it is graded as such, not absorbed into "extra info".

### 3.3 Fixture schema extension (backward compatible)

Additive optional key `expected_warnings` on the golden fixture JSON (colloquial, extraction, and pipeline fixtures — raw JSON loaders tolerate additive keys; `AuditFixture` needs an explicit field because of `extra="forbid"`):

```json
{
  "fixture_id": "colloq_party_group_undercount_001",
  "raw_input": "it's the 6 of us but put me down for now",
  "expected_extracted_fields": { "party_size": 1 },
  "expected_warnings": [
    { "code": "PARTY_UNDERDETECTED", "field": "party_size" },
    { "code": "PARTY_UNPARSED_GROUP_PHRASING", "field": "party_size", "count": 1 }
  ]
}
```

**JSON Schema (the ratified contract):**

```json
{
  "type": "object",
  "properties": {
    "expected_warnings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code":   { "type": "string", "description": "ValidationIssue.code, e.g. PARTY_UNDERDETECTED" },
          "field":  { "type": "string", "description": "Optional ValidationIssue.field to pin the warning to a slot" },
          "count":  { "type": "integer", "minimum": 1, "default": 1,
                      "description": "Expected number of occurrences of (code, field)" }
        },
        "required": ["code"],
        "additionalProperties": false
      }
    }
  }
}
```

**Backward compatibility rule:** `expected_warnings` absent ⇒ the key defaults to `[]` and the fixture asserts **nothing** about warnings — every existing fixture passes unchanged on day one. Loader changes are additive: a default-empty field on the colloquial/pipeline fixture models and one new optional field on `AuditFixture` (keeping `extra="forbid"` intact). Also accepted inside `TrajectoryExpectation` (E-06 §1.4) so journey fixtures can assert warnings on the `validation` ledger step — the same tuple shape, one parser.

### 3.4 Collector capture

New `_collect_live_warning_results()` in `snapshot.py`, mirroring the established live-collector contract (`_collect_live_colloquial_results`, `snapshot.py:166-211`):

1. For each fixture with **either** expected fields **or** expected warnings, run `ExtractionPipeline().extract([SourceEnvelope.from_freeform(raw_input, ...)])` — **once per fixture**, shared with the colloquial collector so the packet is not extracted twice.
2. Run `validate_packet(packet, stage="discovery")` (already the canonical producer of the warnings, `validation.py:100`).
3. Capture the multiset `{(warning.code, warning.field): count}` from `report.warnings` (`validation.py:86`) — this is the fixture's *warning actuals*.
4. Return `{fixture_id: {"fired": {...}, "expected": {...}}}`.

This makes warnings graded **live** — the same honesty contract as the budget/colloquial lanes (no expected-as-actuals fallback for the warnings axis; if the pipeline is unimportable the lane reports `status: unavailable`, not a self-consistent 1.0).

### 3.5 Grading rules

Per fixture, over multisets keyed by `(code, field)`:

- **True positive (TP):** expected `(code, field)` fired with `count_actual ≥ count_expected`.
- **False negative (FN, recall miss):** expected `(code, field)` did not fire (or under-count).
- **False positive (FP, precision miss):** `(code, field)` fired that is not in `expected_warnings` for that fixture — **including** a warning firing on a fixture that declares no `expected_warnings` at all *only if* the fixture opts into strictness (see below).
- **Backward-compat strictness switch:** fixtures without `expected_warnings` do **not** contribute FPs (absent key = "not asserted", per §3.3) — but the lane computes and reports `unasserted_warning_rate` (warnings fired on non-asserting fixtures) so the noise problem is *visible* before strict mode. A small curated `warning_precision_canary` set (10+ known-clean notes) declares `"expected_warnings": []` **explicitly**, asserting zero warnings — these canaries are where FP grading bites from day one.
- Aggregate metrics: `warning_precision = TP / (TP + FP)`, `warning_recall = TP / (TP + FN)`, plus `warning_violations[]` (fixture_id, kind, code, field, expected vs actual) for actionable failure output.

### 3.6 Snapshot section + manifest

New snapshot section `warnings_health` (wired into `build_gate_snapshot`, `stable_snapshot_view`, and the `verify_d6_gate_snapshot.py` blocker check exactly like `colloquial_health` — the verify script's `_check_blocks_ci` pattern at `scripts/verify_d6_gate_snapshot.py:29-83` extends mechanically):

```json
{
  "status": "passing",
  "warning_precision": 1.0,
  "warning_recall": 0.92,
  "fixtures_with_assertions": 14,
  "canary_fixtures": 10,
  "canary_false_positives": 0,
  "unasserted_warning_rate": 0.04,
  "violations": [],
  "live_grading": true,
  "blocks_ci": false
}
```

Manifest addition (`src/evals/audit/manifest.yaml`) — new category using the standard threshold mechanics in `gates.py:28-41`:

```yaml
warnings:
  status: shadow          # flip to gating after 2 weeks green (see open question 1)
  min_precision: 1.00     # zero tolerance: a warning on clean input is a defect
  min_recall: 0.90        # initial bar; raise to 0.95 after canary hardening
  min_accuracy: 0.0       # unused for this category
```

`category_accuracy["warnings"]` feeds the min_accuracy path only if we later want a composite; precision/recall ride the existing `CategoryMetrics` comparison.

### 3.7 Failure modes (PER-0897 lens)

| Failure mode | Mitigation |
|---|---|
| **Fixture authors "asserting" warnings they never verified fire** | Collector is live-only; a wrong expectation surfaces as an FN violation immediately, not as a green lane |
| **Warning assertion rotting into noise-tolerance** | Separate precision axis + explicit `[]` canaries; `unasserted_warning_rate` trend makes creep visible before it's tolerated |
| **Count semantics ambiguity** | `count` defaults to 1; ≥ semantics documented in the schema; mismatch reports expected vs actual explicitly |
| **Breaking existing fixtures** | Absent key = not asserted; zero fixture edits required at introduction (verified against loader shapes: golden fixtures are raw JSON with permissive models; `AuditFixture` gains an optional field) |
| **Warnings graded on a different packet than fields** | Single-extract sharing in the collector (§3.4 step 1) — fields and warnings always come from the same run |

### 3.8 Effort

**~0.5–1 agent-day**: schema + loaders (0.15d), collector (0.15d), grading + snapshot section + manifest + verify-script blocker (0.25d), first 10 canaries + 4-6 asserting fixtures (the PARTY_* DEMO-02 fixtures convert first — their raw_inputs already encode group phrasing) (0.25d).

---

## 4. Combined Effort + Ordering

| Order | Layer | Closes | Effort | Depends on |
|---|---|---|---|---|
| 1 | **E-10** warnings-assertable gate | DEMO-02 warning class unaudited; gives E-06 journeys their warning assertions | 0.5–1 d | — (builds purely on existing loaders + `validate_packet`) |
| 2 | **E-06** trajectory eval | Vacuous `routing_health` (`snapshot.py:833`); ledger never consumed; journey assertions ad-hoc | 1.5–2 d | E-10's `WarningExpectation` type (small, declarative dependency) |
| 3 | **E-07** production shadow-eval + calibrated judge | Thresholds never load-bearing; judge unused; no production-eval plan | 2.5–3 d (+2–3 h human labeling) | E-06's production-walker pattern; E-10 independent but lands in same snapshot schema |
| | **Total** | | **~4.5–6 agent-days** + gold-set labeling | |

Sequencing rationale: E-10 first because it is the smallest change with immediate regression teeth (the DEMO-02 PARTY_* P0 class becomes gate-auditable) and its schema shape is consumed by E-06's journey expectations. E-06 second because it replaces the empty-list placeholder in `routing_health` and produces the walker/runner scaffolding E-07's nightly job reuses. E-07 last per the parent doc's own rule: production eval is only meaningful once the offline gates are trustworthy — and its calibration corpus is the long pole.

---

## 5. Open Questions for Ratification

1. **Warnings gate flip policy:** `warnings` category starts `shadow` — flip to `gating` after N green weeks, or immediately with `min_precision: 1.0 / min_recall: 0.9`? (Recommendation: shadow 2 weeks, then gate; the canary set gates immediately regardless.)
2. **Judge model + cost ceiling:** which `BaseLLMClient` implementation backs the judge (existing provider client? which model?), and is the ≤120 calls/day cap the right ceiling vs a $/day cap?
3. **External judge allowed at all?** If the deployment constraint is "no PII leaves the box" in its strong form, the judge must be local/self-hosted; `strip_pii`-redacted input is the weak-form contract. Which form governs?
4. **Gold-set ownership:** Pranay labels all 60 calibration examples, or a first pass is model-proposed + human-confirmed? Where does the labeling session live (recommend: one sitting; the set is small and stratified)?
5. **Nightly job runtime:** `data/runs/` is machine-local (16,034 dirs, file-backed ledger), so the production eval job must run on the dev machine (LaunchAgent/cron) — acceptable, or does this raise the priority of the ledger's long-term Postgres migration (ties into the dual-store elimination already flagged in AGENTS.md)?
6. **Trajectory CI lane strictness:** gate from day one (recommendation — state-machine properties shouldn't be flaky) or one-release shadow grace?
7. **`blocked_contract` absolutism:** T2 violation rate = 0 is proposed as absolute even in the production shadow lane. Confirm that a deploy-window ledger-writer bug failing the night job is the desired alert behavior (vs warning-only).

---

## Appendix A — Anti-duplication statement

All three layers **extend** existing canonical surfaces rather than forking: E-06 extends `snapshot.py`'s gate + reuses `run_events`/`run_state`/journey patterns; E-07 extends `rubrics.py`/`scorer.py` and consumes `aggregate_eval_records`; E-10 extends the existing golden-fixture schema and the manifest/gates mechanics. No new eval framework, no second snapshot format, no parallel judge.
