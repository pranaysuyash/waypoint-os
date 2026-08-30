# ADHD App Audit — Exploration & Implementation Candidates (2026-08-30)

**Method:** `/adhd` skill run. Phase 1 Diverge: 5 parallel isolated generator agents (regulator, hostile-competitor, logistics, 3am-on-call, remove-the-load-bearing-assumption), each grounded in live repo state, 6 ideas each = 30 candidates. Phase 2 Focus: mechanical scoring (novelty 0.35 + viability 0.40 + fit 0.25, 0–10 each), clustering by underlying angle, trap exclusion, top-3 deepened by 3 parallel FOCUS agents with file-level grounding.

**Ground truth read before generating:** `AGENTS.md`, `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`, `Docs/INDEX.md`, recent git log (IDEA-119…IDEA-124 shipped), `Docs/exploration/` inventory, Persona Council Audit register (R-01…R-16, A-01…A-21; backend suite 358 failed / 2803 passed / 19 errors as of 2026-08-29).

**Baseline exclusions (already implemented/documented, not re-proposed):** ghost concierge, yield arbitrage, price-lock sentinel & re-shopping, commission reconciliation & split settlement, group split deposits, multimodal intake, repeat-traveler memory, suitability tiers 1–4, lead lifecycle, follow-up engine, trust scorecard, proposal web link, omnichannel webhooks, team workflows + signoff gates, edge SLM inference, auto-research tuning, stress suite, audit-chain hashing, RAG grounding, PII guard layers, blind comparison arena, auto-assignment routing, JDG schema, durable agent lease (partial), OTel gap doc, server decomposition plan, styling unification plan.

---

## 1. Wide set (30 ideas, 6 clusters, score chips `[N V F]`)

### Cluster A — Run-loop containment & recoverability (self-healing ops)
The autonomous machinery needs undo, quarantine, and fencing before it needs more autonomy.

| # | Idea | Score |
|---|------|-------|
| O6 | **Invertible re-shopping** — compensating-action record + one-command revert writing its own audit-chain entry | [N9 V7 F9] 8.20 |
| L2 | **Cold-chain spoilage sweep** — one watchdog loop treats every dated artifact (visa validity, quote TTLs, insurance windows, payment deadlines) as perishable inventory with tiered breakage alarms | [N7 V9 F8] 8.05 |
| O2 | **Poison-quarantine drain lane** — inspect/redact/replay surface for `JOB_STATUS_POISONED` jobs, which today silently accumulate and never trigger re-shopping recovery | [N7 V9 F8] 8.05 |
| O5 | Usage guard → autonomous freeze breaker: auto-quiesce a runaway tenant's intake, drain in-flight leases, queue post-incident review | [N7 V8 F8] 7.65 |
| O1 | Kill the run-ledger split brain: dual-write `data/runs/` checkpoints into SQL so any replica can answer "where is run X" after a redeploy | [N6 V8 F9] 7.55 |
| O3 | Locking-parity fail-fast: refuse prod boot unless the pg advisory-lock path is live (`core/locking.py` silently falls back to in-process locks) | [N6 V9 F7] 7.45 |
| O4 | Pin every run to pipeline code version + fence cross-version resume (`agent_work_coordinator.py` hands leases with no version check) | [N8 V7 F7] 7.35 |
| C6 | Spend escrow passed down agent leases: parent-child LLM budget reservations so nested subagent loops can't bypass `usage_guard` | [N8 V7 F8] 7.60 |

### Cluster B — Money & token integrity (double-spend plays)
Every dollar moved and every claim booked needs an idempotent, single-use path.

| # | Idea | Score |
|---|------|-------|
| C1 | **Atomic proposal accept**: token-escrow accept flow — `_PROPOSAL_REGISTRY` has no single-use claim, so a replayed token can re-price and re-accept | [N6 V9 F9] 7.95 |
| R2 | **Bind signoffs to the authenticated JWT subject + artifact-version hash** — `team_workflows.py` stores client-supplied `reviewer_id`; `corporate_policy.py` accepts free-text `approved_by` | [N6 V9 F9] 7.95 |
| R5 | **Payment authorization mandate ledger**: payer consent + amount + counterparty + executor per dollar moved (split deposits, `subagent_payouts.py` ACH), chained into the audit hash | [N7 V8 F9] 7.90 |
| C2 | Margin claim ledger: idempotency + optimistic concurrency on `price_lock.py` re-locks so two concurrent re-locks can't double-book `margin_saved_cents` | [N7 V8 F8] 7.65 |
| R6 | Public token surface hardening: TTL, revocation, PII minimization, consent events for `/p/{token}` views and public collection submissions | [N5 V9 F9] 7.60 |

### Cluster C — Evidence that survives dispute (regulator/forensics plays)
| # | Idea | Score |
|---|------|-------|
| R1 | Cryptographically sign the audit chain + extend coverage to `run_ledger.py` files (currently a tamper-prone split-brain evidence story) | [N6 V8 F9] 7.55 |
| R3 | DSAR execution engine actually enforcing `src/security/jurisdiction_policy.py` (declared retention/erasure, zero enforcement wiring; unencrypted PII step files persist forever) | [N7 V7 F9] 7.50 |
| R4 | Immutable AI-decision explanation dossier: stitch gate results, suitability tier, RAG citations, prompt/model versions into one replayable hashed bundle | [N6 V7 F8] 6.90 |
| C4 | Audit-chain fork/gap detector: monotonic sequence envelopes + writer identity + periodic external anchoring of the head hash | [N8 V7 F7] 7.35 |

### Cluster D — Trust-weighted inputs (poisoning defense)
| # | Idea | Score |
|---|------|-------|
| C3 | **Provenance-tiered memory writes**: channel + verification-status tags on traveler/vendor-sourced preferences, confidence decay, retrieval-time quarantine of unverifiable claims (loyalty tier, allergy overrides) before they reach suitability scoring via `src/memory/retriever.py` | [N9 V7 F8] 7.95 |

### Cluster E — Logistics-native ops primitives (travel-as-inventory)
| # | Idea | Score |
|---|------|-------|
| L6 | OS&D (over/short/damaged) exception codes for defective supplier confirmations, routed to a claims lane instead of retry loops (`confirmation_service.py` treats every mismatch as generic failure) | [N8 V8 F8] 8.00 |
| L3 | Reverse-logistics RMA lane for post-trip refunds/compensation with disposition codes (resell / re-shop / write-off) feeding existing re-shop machinery | [N8 V7 F8] 7.60 |
| L1 | Cross-dock EDIFACT/NDC payloads straight into trip documents, skipping agent re-handling (`src/distribution/` parsers already exist) | [N7 V7 F7] 7.00 |
| L5 | Forward-loaded capacity planning: demand-vs-lease-capacity rollup by departure date, before SLA thresholds fire | [N6 V7 F7] 6.65 |
| L4 | JIT ticketing scheduler (issue at last responsible moment) | [N8 V6 F7] 6.95 — **trap**, see below |

### Cluster F — Assumption-inversion product plays
| # | Idea | Score |
|---|------|-------|
| A2 | Veto-window governance: dispatch autonomously, advisors veto inside a time-boxed window, vetoes feed the override learner | [N9 V6 F8] 7.55 — **conditional trap**, see below |
| A5 | Agent-to-agent negotiation endpoint (traveler's external AI as authenticated first-class client) | [N10 V5 F6] 7.00 — **trap**, see below |
| A4 | Git-like itinerary branch-and-merge with constraint re-validation on merge | [N8 V6 F7] 6.95 |
| A6 | Programmable supplier counterparty: machine-readable RFQ rounds into `bargaining_engine.py` | [N8 V6 F7] 6.95 |
| A3 | Standing travel-intent subscriptions: warm plan shelf, trips materialize on trigger | [N9 V5 F7] 6.90 |
| A1 | Event log as source of truth, DB as disposable projection | [N9 V4 F6] 6.25 — **trap**, see below |

---

## 2. Converge (shortlist + traps)

Shortlist, ranked by weighted score with traps excluded:

1. **O6 — Invertible re-shopping (8.20) ★ non-obvious-but-viable pick.** Nobody proposes "undo" for autonomous money-affecting actions. It directly compounds the just-shipped price-lock sentinel, reuses run_ledger checkpoints + the SHA-256 audit chain, and converts the scariest failure class of the autonomous engine (a bad 3am re-shop) into a transaction.
2. **L2 — Cold-chain spoilage sweep (8.05).** One loop unifies visa expiry, quote TTLs, insurance windows, and payment deadlines — currently scattered across `visa_radar.py`, `price_lock.py`, `insurance.py` with no owner of "expiring inventory" as a class. Expired visas and lapsed insurance are the #1 silent real-world failure in travel ops.
3. **O2 — Poison-quarantine drain lane (8.05).** `JOB_STATUS_POISONED` already exists as a buried status string; this turns it into operator recovery with zero new machinery concepts, and unblocks re-shopping recovery for dead trips today.

**Cluster-level position:** if only one *theme* gets funded, fund **Cluster B (money & token integrity)**. Individually its ideas score 7.6–7.95, but they share one root cause — no idempotency/versioning/identity-binding discipline on anything that moves money or represents consent — and any single exploit there is a real-liability incident, not a bug.

**Traps (excluded from deepening):**
- **A1 event-log-as-SSOT (6.25)** — premature architecture rewrite; huge blast radius; contradicts the Wave 0–6 "finish a canonical path first" doctrine. The real need (crash-rebuildable run state) is served by O1's dual-write without the rewrite.
- **A5 A2A negotiation endpoint (7.00)** — false economy: no real supplier adapter exists (per `LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md`); building a negotiation surface without supply-side connectivity is a demo.
- **L4 JIT ticketing (6.95)** — autonomous deferred issuance has no real fulfillment/PNR path; fare rules alone can't execute it. Revisit after connectivity tier 1 lands.
- **A2 veto-window governance (7.55)** — conflicts with the implemented D1 autonomy gradient + high-value signoff gates. Viable only as an additive per-agency opt-in mode, not a replacement; treat as re-litigating a decided architecture unless positioned that way.

---

## 3. Focus (3 deepened branches)

### Branch 1 — O6: Invertible re-shopping ★

**Sketch.** At commit time, `re_lock_lower_rate` (`spine_api/routers/price_lock.py:184`) snapshots the full pre-state of `strategy.recommended_option` (cost cents, supplier name, price-lock fields) plus a `strategy.version` stamp, and writes a compensating-action record to `data/runs/{trip_id}/price_lock_ops/{op_id}.json` shaped as `{op_id, trip_id, agency_id, status: 'applied', triggered_by, forward: {field-level diffs}, pre_state_snapshot, strategy_version_before, inverse: [field patches], reverted_at: null}`. The `op_id` is stamped into the existing `price_lock_arbitrage_saved` AuditStore event, linking mutation and ledger entry. A new `POST /api/v1/price-lock/{trip_id}/re-lock/{op_id}/revert` endpoint (advisor/owner roles only — never the autonomous engine) loads the record, verifies `strategy.version` still matches `strategy_version_before`, applies the inverse patches, marks `status='reverted'`, and appends a chained `price_lock_re_lock_reverted` event — the revert is a new append-only hash-chained entry, never an edit, so the audit chain stays intact. Traveler-visible state converges automatically because public proposals read `strategy.recommended_option`. The ops directory doubles as a per-trip undo stack consumable by the decision engine and opportunity surfaces.

**Load-bearing risk.** The revert is only sound if you can prove no mutation landed between apply and revert — and the repo has no optimistic concurrency: `re_lock_lower_rate` is a blind read-modify-write of `trip.strategy` with no version field, no idempotency key, and no CAS in `TripStore.save_trip`. A blind inverse patch after an intervening mutation corrupts state and margin accounting. The idea therefore rests on introducing and enforcing a serialized `strategy.version` check as the revert precondition, race-free under TripStore locking.

**First concrete step.** In `spine_api/routers/price_lock.py`, before the `TripStore.save_trip` call (~line 213): capture `prev_rec_option = deepcopy(rec_option)`, increment `strategy['version']`, generate `op_id = f"plock_{uuid4().hex[:12]}"`, and write the compensating record to `data/runs/{trip_id}/price_lock_ops/{op_id}.json`; add `op_id` + `strategy_version_after` to the AuditStore event details (~line 219).

**Child ideas.**
- Idempotency-Key header on `POST /re-lock` keyed to `op_id` — prerequisite scaffolding that makes the compensation record trustworthy.
- Compensation lifecycle gating: auto-transition `applied → frozen` once `price_lock_expires_at` passes or the deposit lands; revert returns 409 with audit reason. Recovery is a transaction only inside the 72-hour window.
- LIFO multi-step undo: `POST /{trip_id}/re-lock/undo?steps=N` walking the ops stack with per-step version checks.
- Saga generalization: extract an `UndoableMutation` helper into `spine_api/core/undo.py`; adopt for `yield_arbitrage.py`, `fx_sentinel.py` — uniform revert surface for every autonomous mutator.
- Traveler-facing rollback UX: proposal-refresh event + advisor note in the audit chain on revert.

### Branch 2 — L2: Cold-chain spoilage sweep

**Sketch.** A `SpoilageWatchdog` in `spine_api/watchdog.py` runs as a second loop in the existing `IntegrityWatchdog` thread (same `start()/stop()` wiring at `server.py:1191/1257`), ~15-minute cadence. The artifact registry is virtual — each sweep re-derives dated artifacts from existing SSOTs: price-lock TTL via the imported `_get_price_lock_expires_at()`, payment deadlines via `payment_queue_service`'s due-bucket convention, passport/visa validity via `visa_radar.py`, insurance coverage windows via `routers/insurance.py` — each yielding `(trip_id, artifact_type, expires_at, hours_to_spoilage)`. Escalation buckets: >72h advisory (dashboard count only), ≤72h notify operator dashboard + fold into the daily operator digest, ≤24h critical (immediate operator email + `task_blocked` event), ≤6h/past spoiled (traveler-owned artifacts like passports also ping traveler notification with its operating-hours gate). Transitions emit through `execution_event_service.emit_event_best_effort` with metadata (`blocker_code='SPOILAGE_RISK'`, artifact_type, expires_at) so the timeline shows the cold-chain trail. Dedupe is per `(artifact_id, tier)`, alerting only on tier transitions; routers stay the pull-time views while the sweep is the push-time notifier.

**Load-bearing risk.** `execution_event_service` enforces a closed vocabulary (`EVENT_CATEGORIES` = task/confirmation/document/extraction in `spine_api/models/tenant.py`, with `ALLOWED_SUBJECT_TYPES`, `ALLOWED_EVENT_SOURCES`, `ALLOWED_EVENT_METADATA_KEYS` frozensets). Nothing like "artifact expired" or the proposed metadata keys is allowed — every emission either fails validation or requires a schema-touched migration of those constants, and timeline consumers assume exactly four categories. Secondary: the watchdog is a daemon thread in one process; multi-worker uvicorn would run duplicate sweeps unless tier-transition state is persisted.

**First concrete step.** In `spine_api/models/tenant.py`, extend constants: add `'spoilage_sweep'` to `ALLOWED_EVENT_SOURCES`, add metadata keys (`artifact_type`, `expires_at`, `hours_to_spoilage`, `spoilage_tier`) to `ALLOWED_EVENT_METADATA_KEYS`; then add `SpoilageWatchdog.check_spoilage()` to `spine_api/watchdog.py` starting with one artifact type (price-lock TTL) emitting one best-effort `task_blocked` event per tier transition.

**Child ideas.**
- Insurance cold-chain: join coverage-end dates against departure dates; emit coverage-gap breakage before the trip starts.
- Breakage-to-action: at critical tier on a quote TTL, auto-invoke `/re-lock` or re-shop — spoilage alarms become margin-recovery actions.
- Traveler passport spoilage ledger: 6-month-rule computation escalated to traveler notification.
- Accountability loop: feed spoilage into `sla_service` and the trust scorecard so letting artifacts spoil penalizes advisor scores.
- Persist `(artifact_id, tier, notified_at)` state; swap the thread for a scheduled job → multi-worker-safe sweeps + spoilage analytics.

### Branch 3 — O2: Poison-quarantine drain lane

**Sketch.** A quarantine inbox API in a new `spine_api/routers/poison_quarantine.py` (or extending `agent_runtime.py`, which already wires `RequeueWorkerService`): `GET /api/v1/agent/quarantine` listing poisoned rows, `GET .../{job_id}` detail, `POST .../{job_id}/replay` and `/dismiss`. Requires a new `list_poisoned()` on `RequeueJobStore` (its `snapshot()` returns only status counts). A poison taxonomy persisted on the job (`poison_code` column) is derived at `fail()` time: `POISON_TRIP_MISSING`, `POISON_NO_RAW_INPUT`, `POISON_WORKER_UNCONFIGURED`, `POISON_MAX_ATTEMPTS`, `POISON_PIPELINE_EXCEPTION`. Replay is gated by `require_permission("ai_workforce:manage")` — Owner/Admin replay, SeniorAgent read-only. Replay resets status/attempts and dedupes via `IdempotencyRegistry` so an already-completed original surfaces as a no-op. Redaction strips PII from stored payload before replay while replaying context from the trip's `raw_input` so the idempotency key stays stable. Every inspect/replay/dismiss writes a `poison.*` audit event extending the RULE_015 hash chain. UI: a `QuarantineTab` in the workbench tabs showing poison_code groups, last_error, age, one-click replay/dismiss.

**Load-bearing risk.** Replay must never mutate the idempotency key while reporting success: redacting the payload changes the hash inside `generate_key()`, and the `uq_agent_requeue_jobs_idempotency` unique index + COMPLETED records mean a naive replay either silently no-ops (operator believes the trip was recovered when the 72-hour price-lock window expires anyway) or bypasses dedup and double-books. The endpoint must pass through and display the `try_acquire` dedup outcome (executed vs cached vs rejected) and refuse redactions that would alter key inputs — otherwise the quarantine lane manufactures false recovery confidence.

**First concrete step.** In `spine_api/services/agent_requeue_jobs.py`, add `list_poisoned(limit=50, trip_id=None)` to `RequeueJobStore` (filter `JOB_STATUS_POISONED`, order by `updated_at DESC`, full rows including idempotency_key/reason/last_error/attempts), then expose `GET /api/v1/agent/quarantine` in `spine_api/routers/agent_runtime.py` behind `require_permission("ai_workforce:manage")` for writes and `require_auth` for reads — the smallest change that makes accumulated poison visible before taxonomy, redaction, and replay.

**Child ideas.**
- Auto-classifier at poison time (alembic migration for `poison_code`) enabling bulk replay of whole root-cause classes.
- Unified quarantine ledger merging `ResilienceEngine.quarantine_intake` incidents with requeue poison into one operator inbox.
- Price-lock replay SLA: join poisoned jobs against `price_lock_expires_at` and auto-escalate when a quarantined trip's re-shop window is closing.
- Dry-run replay mode executing against the redacted snapshot in shadow mode with a predicted-dedup verdict.
- Batch replay with a chained audit rollup (executed vs no-op vs rejected per job) for mass recovery after systemic outages.

---

## 4. Provocation

If none of the above lands: **the repo's deepest un-owned primitive is time itself.** Visa windows, price locks, payment deadlines, insurance coverage, ticketing limits, SLA clocks, and the 72-hour re-shop window are all independent timers scattered across routers and services — there is no single concept of "an obligation with a deadline" in the data model. A first-class `TemporalObligation` primitive (one table, one sweep, one escalation policy) would subsume Cluster E, half of Cluster A, and make the spoilage sweep (L2) a special case rather than a feature. Ask: what breaks if every deadline in the system becomes a row in one table?

## 5. Follow-ups

- Shortlist owner decision: pick 1–3 branches for implementation sequencing (recommend O6 first — it forces the `strategy.version`/idempotency discipline that Cluster B also needs, making C1/C2 cheaper afterward).
- Backend test-suite debt (358 failed / 2803 passed per Persona Council Audit 2026-08-29) is the standing precondition for any of these; new contract surfaces (revert endpoint, quarantine API, event-vocabulary extension) should land with their own tests regardless.
- Cross-reference: `Docs/review/EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md` (research questions with falsifiers) — this audit's Cluster D (C3) overlaps that backlog's suitability-signal-mining thread and should be reconciled before implementing.
