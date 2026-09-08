# Failure Taxonomy & Recovery-Routing Design (2026-09-07)

> **VOCABULARY SUPERSEDED 2026-09-08:** the seven-class noun set in this doc is superseded by the
> live 8-class `FailureClass` enum (`spine_api/failure_taxonomy.py`). See
> `FAILURE_TAXONOMY_RECONCILIATION_2026-09-08.md` for the ratified crosswalk. The recovery ladders,
> POLICY-routing principle, sweep-race fix, and operator-queue designs below remain valid with the
> crosswalked names.


**Status:** exploration package E-B output (PER-0700). Design for ratification; no code changed.
**Problem (PA-07):** the run system has exactly one failure shape — `run_state=failed` + free-text `error_message` — and one recovery policy — retry 2× then escalate (`recovery_agent.py:245-249`). A provider outage, a poisoned fixture, a state divergence, and a budget-guard trip all recover identically, which is why recovery is class-blind and the ledger cannot answer "why did this fail?" (`run_ledger.py:277-296` records no class; `stage_at_failure` is absent from meta).
**Related defects this design must absorb:** PA-13 (no per-trip in-flight lease → concurrent last-writer-wins), PA-17 (stale-run sweep races live threads → `failed` ledger with a saved trip and a swallowed `complete()`), PA-38 (recovery writes `review_status`, the new queue reads `TripRoutingState`), PA-29 (terminal lease/requeue rows never expire), PA-40 (idempotency CAS wired to only 2 ingress paths).

---

## 1. Taxonomy (seven classes)

| Class | Meaning | Typical detection signal |
|---|---|---|
| `TRANSIENT` | Expected, self-healing environment wobble (network blip, 429, timeout) | exception type/timeouts; circuit-breaker state |
| `PROVIDER` | External dependency degraded or misconfigured (LLM, GDS, carrier) | adapter errors, `provider_connected: false` responses |
| `INPUT` | The work item itself is bad (unparseable fixture, malformed envelope) | validation gates, poison-job markers (DLQ) |
| `STATE` | Divergence between persisted views (ledger vs trip vs lease) | read-back mismatch, sweep/lease conflict (PA-17) |
| `POLICY` | A gate or guard did its job (budget guard, leakage scan, authority denial) | gate verdicts, `AuthorityDenied`, usage guard |
| `VERIFICATION` | Execution "succeeded" but the postcondition failed (PA-05 family) | read-back mismatch, eval assertion failure |
| `AUTHORITY` | Actor lacked permission at execution time | 403/authority events |

Rule: **POLICY failures are not system failures.** A leakage block or authority denial is the system working; they must not page anyone or consume retry budget — they route to the operator queues (`blocked`, escalated queue) with human actions, never to `recovery_agent`.

## 2. Where the class lives (schema sketch — additive)

1. `run_state.py`: add `failure_class: Optional[FailureClass]` beside the existing terminal states (no state-machine change; `failed` stays, it gains a dimension).
2. Ledger `meta.json`: add `failure_class`, `stage_at_failure`, `recoverable: bool` (PA-07's missing `stage_at_failure` lands here).
3. Classification is **one function** (`classify_failure(exc, stage, context) -> FailureClass`) called at the single choke point where exceptions become `failed` (`pipeline_execution_service.py:616-624`), so both the daemon path and future worker paths classify identically. Classification is deterministic rules on exception type + stage + gate context — no LLM.
4. `agent_requeue_jobs` / DLQ rows gain the same `failure_class` column (PA-29's TTL applies to terminal rows regardless of class).

## 3. Recovery routing (replaces class-blind 2×→escalate)

| Class | Immediate | Ladder | Terminal state |
|---|---|---|---|
| TRANSIENT | retry in-process (existing backoff) | 3× → requeue (`SKIP LOCKED` path) | `failed` only after ladder exhausts |
| PROVIDER | fail fast if breaker open | requeue with provider-aware delay; DLQ after N | `failed` + DLQ row |
| INPUT | do not retry | DLQ as poisoned (inspect/redact/replay exists — F-07) | `failed` + DLQ |
| STATE | freeze: no auto-retry (retrying may amplify divergence) | reconciliation job compares ledger/trip/lease → `completed_after_failure` (fixes PA-17's swallowed transition) | `failed` → reconciled, or human |
| POLICY | none | none | `blocked` (first-class already) + operator queue |
| VERIFICATION | none (result is untrustworthy) | re-execute once under a fresh lease | `failed` + audit event; never `completed` without verified persistence |
| AUTHORITY | none | human escalation (403 body already requests it) | `blocked` + escalated queue |

Ladder state lives on the ledger meta (`attempt`, `class`, `next_action`) so recovery decisions survive restarts (the current 2× counter is in-memory and class-blind).

## 4. Sweep safety (PA-17, fold-in)

The stale-run sweep (`timeout_stale_runs`, 300s, poller-driven) may only sweep runs whose lease is **provably absent or expired** — `agent_work_leases` is the liveness oracle, replacing the current time-only heuristic. A run whose thread holds a live lease is never marked `failed` by the sweep. This converts PA-17 from "allow illegal transition" to "don't create the lie."

## 5. Operator surface + metrics

- Escalated queue (shipped, uncommitted) and DLQ inspection become the two human-facing recovery views; both gain `failure_class` filters.
- `/metrics` (PA-10) gains per-class counters: `runs_failed_total{class}`, `recovery_actions_total{class,action}`, `dlq_depth{class}`. This is the cheapest honest observability win in the plan and needs no new infrastructure.
- Cost joins here: PA-20's cost-per-outcome is computed **per failure class** (a TRANSIENT-heavy profile and a VERIFICATION-heavy profile are different businesses).

## 6. Migration / rollout sketch

Additive, no backfill required: new fields default `None` (unclassified — the honest value for historical rows); classification ships at the single choke point; recovery-agent routing ships behind the existing supervisor tick with per-class no-ops until each ladder is enabled. Sequence: (1) classify + ledger fields, (2) POLICY/non-retry split (stops wasted retries immediately), (3) STATE reconciliation, (4) sweep lease-awareness, (5) metrics.

## 7. Open questions for ratification

1. Retry budgets per class (proposed: TRANSIENT 3, PROVIDER 2, VERIFICATION 1, others 0).
2. Does `INPUT` ever route to human, or only DLQ replay? (proposed: DLQ only — humans fix data via the repair surface, not the DLQ).
3. Should POLICY failures emit `ExecutionEvent`s into the eval flywheel? (proposed: yes, they are the highest-signal fixtures — with care for the PA-21 verdict-honesty fix landing first).
