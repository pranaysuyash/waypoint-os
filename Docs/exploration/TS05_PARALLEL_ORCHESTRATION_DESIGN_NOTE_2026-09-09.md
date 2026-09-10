# TS-05 — Pipeline Parallel Orchestration & Speculative Execution (design note, PARKED)

**Status:** design note — parked by recommendation (2026-09-09). Revisit when external provider tools land (B6/B7).
**Source:** training-session register TS-05; tutor's rule: *parallelize independent work when the expected latency benefit exceeds the expected cost of wasted work* — as a function of latency, API/monetary cost, gate-failure probability, wasted-work consequence, downstream reusability, and UX.
**Doctrine:** Architecture 1.1 (failure is design; no speculative complexity without a forcing load).

---

## 1. Current state (Observed)

- `run_spine_once` (`src/intake/orchestration.py:181-614`) is **strictly sequential**: Phase 1 extraction → Phase 2 validation → NB01 → Phase 3 decision → 3.5 suitability → NB02 → 3.2 frontier → Phase 4 strategy → 4.5 fees → 4.6 plan candidate → Phase 5 bundle → 7 sanitized view → 9.6 readiness → 10 fixture compare. Early-return on gate ESCALATE/DEGRADE (already a short-circuit, in the tutor's sense).
- No fan-out anywhere in the pipeline: `asyncio.gather` exists only in the stress simulator (`src/benchmarking/stress_simulator.py:164`); `create_task` only in the agent-lease heartbeat (`src/orchestration/agent_lease.py:528`).
- `MULTI_AGENT_RUNTIME_ROADMAP.md` Layer 3 (durable orchestration: SQL leases, job queue/outbox, dead letters) covers *durability*, a different axis than intra-request parallelism.

## 2. Why parked (honest cost/benefit)

Today's pipeline is local-deterministic + one LLM extraction call. The independent-work candidates are: suitability (3.5) vs strategy (4) vs frontier (3.2) — all sub-second local CPU. Parallelizing them buys milliseconds and adds cancellation complexity, ordering nondeterminism (the fixture-compare phase depends on stable ordering), and harder failure attribution (which phase observability attributes, PA-19). **The tutor's own rule says don't.**

The value arrives with external providers: entry-requirement check (visa lead time) as a cheap early gate, with speculative flight/Disney/hotel feasibility running concurrently, cancel-on-gate-fail — exactly the tutor's "entry check 2s vs 3min" tradeoff table.

## 3. The design checklist (when unparked)

When a live provider lane lands, evaluate each candidate fan-out against the tutor's factors, and record the decision:

| Factor | Question |
|---|---|
| Latency delta | How much wall-clock does serialization cost us? |
| API/monetary cost | What does the speculative work cost if the gate fails? |
| Gate-failure probability | How often does the early gate kill the trip? |
| Wasted-work consequence | Are side effects created (no — searches only) or just spend? |
| Downstream reusability | Are speculative results cacheable for the retry after gate-fix? |
| UX | Does the customer see feasibility signal sooner? |

**Design shape (Proposed, not built):** a bounded fan-out step inside `run_spine_once` — a single `asyncio.TaskGroup` around provider-read calls, with an overall deadline; gate results awaited first and used to cancel siblings (`TaskGroup` cancellation is cooperative and standard). Deterministic phases stay sequential; only provider I/O fans out. Ordering for fixture-compare must be re-established by sorting, not by completion order.

**Explicitly out of scope:** no actor framework, no workflow engine, no new queue system — Layer 3 of the runtime roadmap already owns durability; this note owns only intra-request concurrency.

## 4. Trigger to revisit

B6/B7 produces a live provider adapter whose median latency exceeds ~2s, or the WhatsApp corridor (C5) makes intake wall-clock a UX-visible number. Until then this note is the complete deliverable.
