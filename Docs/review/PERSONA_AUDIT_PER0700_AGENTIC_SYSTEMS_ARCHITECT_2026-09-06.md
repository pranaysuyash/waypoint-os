# Persona Audit — PER-0700 Agentic Systems Architect (2026-09-06)

**Status:** complete review artifact (read-only audit; no code changed by this audit)
**Date:** 2026-09-06
**Persona applied:** PER-0700 — Agentic Systems Architect (canonical doc: `~/Desktop/Understanding_Personas_sept6/01 Expanded Personas/07 Agentic AI & Exploration/PER-0700 - Agentic Systems Architect.docx`, reconciled 2026-08-22)
**Method:** five parallel read-only evidence sweeps (agency boundary; state/memory/lifecycle; tool contracts/authority; observability/evaluation; explicit-register consolidation), followed by direct code verification of every P0/P1 claim by the lead auditor.
**Doctrine context:** `OPERATING_DOCTRINE.md` v8.0 (§2 truth taxonomy, §11 engineering, §12 AI output boundary, §13 claim reality) + `REVIEW_DOCTRINE.md` 1.1 method.
**Baseline map verified against live tree:** [CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03](../architecture/CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md) — two of its honesty notes are now stale (see PA-03, PA-35).
**Companion artifacts:** findings register [FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0700_2026-09-06](FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0700_2026-09-06.md) · plan [IMPLEMENTATION_PLAN_PER0700_2026-09-06](IMPLEMENTATION_PLAN_PER0700_2026-09-06.md)

---

## 1. Executive summary

**Central question of the persona:** *Where is adaptive agent behavior justified, and what architecture makes that autonomy reliable enough to operate inside a real product?*

**Answer for this repo:** adaptive/LLM behavior is justified in exactly three places — (a) vision/LLM document extraction at the intake edge, (b) optional contextual suitability scoring, (c) optional hybrid risk-flag reasoning for long-tail rule gaps. The deterministic core (extraction → gates → decision → fees → recovery) correctly occupies ladder rungs 1–6 everywhere else, and the supervised agent fleet is honestly a deterministic cron fleet — which is the *right* rung.

**The verdict:** the architecture occupies almost exactly the justified places, but the boundary is enforced by the wrong mechanism, and the system's presentation outruns its capability in the opposite direction:

1. **Determinism is credential-accidental, not architectural (PA-03, P1).** `USE_HYBRID_DECISION_ENGINE` defaults to `"1"` (`src/intake/decision.py:37`) and is pinned in `fly.toml:29` and `docker-compose.yml:21`. The serving spine is LLM-free today only because no `GEMINI_API_KEY` is present in deployed environments. One env var silently moves the spine from rung 1 to rung 2. The 2026-09-03 map's "100% deterministic serving path" note and register row G-03 ("built, unwired") are both now wrong/contradictory.
2. **The system is under-agentic where it claims value and over-presentational where it has none.** The two deliberately designed optional-LLM components (suitability Tier-3 scorer, memory read-path into decisions) are unwired — memory is a full 5-tier lifecycle machine that nothing in the run path reads (PA-18) — while simulated surfaces keep gaining real-looking capability: the uncommitted tree adds an **unauthenticated public journey-graph route that fabricates a confirmed itinerary** (PA-01, P0) and a **signed share token for synthetic proposal inventory** (PA-25).
3. **Authority machinery exists but is decorative (PA-08).** The governance registry (`max_budget_impact` up to $50k) and the dual-control `AuthorityGateKeeper` are enforced by zero execution paths. Proposal→validation→authorization→execution→verification is collapsed inside one function on the money path, whose completion status is **self-asserted from sandbox adapters** (PA-05) and whose authorization evidence (traveler acceptance) is stored **only in a process-local dict** (PA-02, P0).
4. **The verification layer mostly asserts rather than proves.** The one tamper-evident artifact (audit SHA-256 chain) is never verified outside tests and is silently invalidated by its own compaction (PA-19); `/metrics` is a fake Prometheus endpoint (PA-10); the autoresearch loop grades hardcoded simulations and writes authoritative "accepted" lineage (PA-11); closed-loop fix verdicts are string comparisons, not re-executions (PA-21).

**What is genuinely excellent (keep and extend):** the trip persistence core (status guard + optimistic CAS + pinned backend, `spine_api/persistence.py`), the proposal capability-token system (fail-closed signing, durable revocation), the agent lease/fencing + DLQ machinery, the supervised fleet's explicit per-agent contracts and termination semantics (`src/agents/runtime.py:3233-3260`, `:175-188`), the D6 eval audit lane (live-graded, honest shadow statuses, mirror-authority quarantine — the only subsystem that *proves* what it claims), and the persisted decision rationale with autonomy verdicts (`decision.py:2269-2290`, `orchestration.py:446-457`).

**Doctrine alignment in one line:** code is honest where it is excellent; the boundary, the money path's authority model, and the newest surfaces are where first-principles discipline is being lost — and the newest loss is in uncommitted work sitting in the tree right now.

---

## 2. Method and evidence discipline

| Sweep | Dimension | Tool calls | Key artifacts inspected |
|---|---|---|---|
| S1 | Deterministic-vs-agentic boundary | 59 | `src/intake/*`, `src/decision/*`, `src/agents/*`, ~30 `src/` domain engines, uncommitted diffs |
| S2 | State, memory, lifecycle, idempotency | 64 | run ledger, TripStore, drafts, leases, requeue, memory graph, all background loops, disk usage |
| S3 | Tool contracts + authority | 49 | money path (tokens/locks/VCC/settlement/commission), governance/boundaries, preview boundaries |
| S4 | Observability, provenance, evaluation, cost | 59 | decision rationale persistence, timeline, audit chain, evals manifest, judge, autoresearch, usage guard |
| S5 | Explicit-findings consolidation | 24 | canonical register (145 rows: 91 open/53 closed/1 deferred), LAUNCH_STATUS, master inventory, known-issues ledger |

Every P0/P1 claim was re-verified directly by the lead auditor against the working tree before being recorded (hybrid flag default + deploy pins; public router include at `spine_api/server.py:1468`; `_PROPOSAL_REGISTRY` at `spine_api/routers/public_proposals.py:100`). Truth labels: **Observed** = seen in live file/line this audit; **Inferred** = stated with its assumption; **Unknown** = check named. Evidence tier: Tier 1 (static inspection) throughout, with S5's register counts Tier 1 via the repo's own parser (`scripts/check_findings_register.py`). No Tier 2+ was executed — this is a review, not a test campaign; every "verify at Tier 2/3" requirement is listed in the plan doc.

---

## 3. Agency-ladder position map (S1)

Ladder: 1 deterministic → 2 single model call → 3 structured workflow → 4 model+tools → 5 single agent → 6 agent+deterministic workflows → 7 multi-agent → 8 dynamic organization.

| Component | Rung today | Evidence | Simpler alternative | Verdict |
|---|---|---|---|---|
| `run_spine_once` serving path | 1 by default, **climbs to 2 when `GEMINI_API_KEY` exists** | `src/intake/orchestration.py:181,386` → `decision.py:37` (default `"1"`) → `hybrid_engine.py:594` live `llm_client.decide` | Flip default to `"0"`; make determinism architectural | **ALIGNED-but-leaky (PA-03)** |
| Text extraction | 1 — pure regex/rules | `src/intake/extractors.py:2338` | None needed | ALIGNED |
| Vision/LLM document extraction | 2, outside serving path | `src/extraction/vision_client.py:186,231` | Justified for OCR/semantic parsing | ALIGNED |
| Hybrid decision engine | 3 (cache→rules→LLM) with usage guard | `decision.py:32-73,76-154`; `hybrid_engine.py:520-641,550-577` | It *is* the simpler alternative; needs honest default | UNDER-USED / mis-documented |
| Suitability Tier-3 scorer | 2 with heuristic fallback, **unwired** | `src/suitability/llm_scorer.py:216,234-240`; no import in `integration.py` | Wire deliberately or archive | UNDER-USED (PA-36) |
| Frontier sentiment + CheckerAgent | 1 **simulating** 4 | `frontier_orchestrator.py:58,222-245`; `checker_agent.py:22-26` | Label as heuristic | SIMULATED-AS-LIVE (PA-35) |
| Persona Council | 1 **theater** — hardcoded scores, zero callers | `src/agents/debate_council.py:60-131` | Delete or honest weighted-rubric scorer | OVER-AGENCED (PA-35) |
| ModelCapabilityRouter | 1 classifier impersonating a router, zero callers | `src/orchestration/model_router.py:31-90` | Delete or wire to dispatch | OVER-AGENCED (PA-35) |
| Supervised fleet (19 agents) | 6 — deterministic workflows, zero LLM, full contracts | `runtime.py:3233-3260` registry, `:175-188` contracts, `:281-311` leases, `:145-160` DLQ; live tools real HTTP `live_tools.py:173-174` | They *are* the right rung; only naming overstates | **ALIGNED — strongest area** |
| ~30 domain engines (bargaining, fees, crisis, Pareto, recovery…) | 1 — pure deterministic | e.g. `bargaining_engine.py:1-25`, `counterfactual_recovery.py:1-8` | None | ALIGNED (logic); some surfaces dishonest |
| Amadeus sandbox adapter / empty-leg | 1 — fixtures/feed parser | `amadeus_sandbox_adapter.py:31`, `empty_leg_scraper.py:39,127` | Honest naming only | SIMULATED (labeled at some surfaces) |
| IVR bypass | 1 simulating telephony, API reports success | `ivr_bypass_bot.py:61`, `routers/ivr_bypass.py:38-46` | Gate behind real carrier or return `"simulated"` | SIMULATED-AS-LIVE (PA-28) |
| Proposal compiler | 1, fabricates providers/prices | `proposal_compiler.py:95-103,125-127,162-166` | Source inventory honestly | SIMULATED (PA-25) |
| Public journey graph (uncommitted) | 1 **synthesizing fake itineraries, unauthenticated** | `journey_graph.py:118-237`, `server.py:1468` | Return 404/draft when no graph | **SIMULATED-AS-LIVE (PA-01, P0)** |

**Fleet supervision check (persona task):** every registered agent carries an explicit `AgentDefinition` (trigger/input/output/idempotency/failure) and retry policy; termination is deterministic (attempt budget → `POISONED` → DLQ; `runtime.py:293-303,488-492`); no agent lacks purpose or termination criteria. The fleet's only live external effect is open-meteo/geocoding reads wrapped in freshness checks with fail-closed unknown-risk (`runtime.py:1234-1246,1304-1311`). **Pass.**

---

## 4. State vs memory, lifecycle, idempotency, recovery (S2)

### 4.1 Persistent-state surfaces

| Surface | Lifecycle? | Evidence | Gap |
|---|---|---|---|
| Run ledger `data/runs/{id}/` | Lazy 300s stale sweep; **no GC** | `run_ledger.py:54,409-453`; sweep only in `run_status.py:57-58` | **18,987 dirs / 648MB now**; O(N) scans forever (PA-12) |
| SQL `trips` | Status guard + history cap 50 + CAS version | `persistence.py:51-91,1395,1679-1715` (fail-closed backend pin) | Solid |
| Drafts | Lifecycle states; discard soft | `draft_store.py:69,88-94,328-342` | No expiry of abandoned drafts |
| `agent_work_leases` / `agent_requeue_jobs` | TTL + poison on leases; **terminal rows never expire** | `agent_work_coordinator.py:31-50,95-101`; `agent_requeue_jobs.py:186-194,281-298` | Unbounded growth, hidden by LIMIT 200 (PA-29) |
| Audit chain | 10k cap with tail compaction | `persistence.py:2257-2320,2400-2500` | Compaction breaks its own hash chain; never verified in prod (PA-19) |
| Memory graph (5-tier) | Full lifecycle: half-life decay, tombstones, supersession, GDPR erasure | `src/memory/store.py:135-187`, `gdpr_engine.py`, `eligibility_gate.py` | **Nothing in the run path reads it** (PA-18) |
| Webhook idempotency registry | Durable SQL, fencing tokens, 24h reclaim | `src/agents/idempotency.py:59-66,246-300` | Good |
| Collection tokens | TTL + revoke-on-regenerate | `collection_service.py:29-104` | Single-use not atomic (PA-16) |
| Checkpoints / undo stacks | **None** | `src/agents/checkpoints.py:41-44`; `src/state/mutation_history_stack.py:42-44` | In-memory, unbounded, lost on restart (PA-30, PA-15) |
| Retention enforcer | Declared only | `src/security/retention_enforcer.py:105-111` | Paper compliance (known X-14) |

### 4.2 Loop termination

All supervised daemons (zombie reaper, recovery agent, supervisor, requeue worker, watchdog) are terminable with bounded passes and symmetric lifespan start/stop (`server.py:1286-1300,1352-1358`). The autoresearch loop is iteration-bounded. **One unbounded loop:** inbound SSE `while True` with client-disconnect as the only exit, plus a `_TRIP_EVENT_LISTENERS` dict that is never pruned (`routers/inbound.py:528-561`) (PA-14).

### 4.3 Idempotency and failure classes

- `POST /run` mints a fresh `uuid4` per submission — no client idempotency key, no per-trip in-flight lease; two concurrent runs on one trip are last-writer-wins (`server.py:1982+`, `trip_lifecycle_service.py:121-136`) (PA-13).
- Price-lock idempotency has a TOCTOU window; the optimistic `expected_version` guard is **optional** (`price_lock.py:210-253`) (PA-06).
- Failure recording is class-blind: ledger `fail()` stores raw `type(e).__name__`; `stage_at_failure` exists only in events/draft snapshot, **not** in ledger meta; recovery requeues everything stuck on the same 2×→escalate ladder regardless of cause (`run_ledger.py:277-296`; `pipeline_execution_service.py:616-624`; `recovery_agent.py:245-249`) (PA-07).
- Stale-run sweep races live daemon threads: run marked FAILED, thread later saves the trip, `complete()` raises on the illegal failed→completed transition and is swallowed → ledger says FAILED, trip exists (`run_status.py:57-58`, `pipeline_execution_service.py:561-569`) (PA-17).

### 4.4 Memory read-path (persona question: "what must persist beyond the run?")

**Observed:** the only consumer of `src/memory` outside the module is the customer-memory router (UI ingest/query). Zero calls to `MemoryStore.query_memories`/`MemoryRetriever.retrieve` in any decision, suitability, intake, or orchestration path. The half-life/supersession/GDPR machinery is real but currently influences no run (PA-18; sharpens known F-13).

---

## 5. Tool contracts and authority architecture (S3)

### 5.1 External-effect inventory (money/legal/external)

| Effect | Gate | Idempotent? | Compensable? | Verified-after? | Tier | Evidence |
|---|---|---|---|---|---|---|
| Proposal token issue/verify/revoke | `PROPOSAL_SIGNING_KEY` fail-closed at import+boot | Verify pure; revoke durable | Revocation IS compensation | Reloaded every verify | **real** (crypto) | `public_proposals.py:112-140,212-265`; `startup_assertions.py:182-234` |
| Proposal e-sign accept | Public token + consent checkbox | No | Revoke possible | **No** — process-local | **sim (non-durable)** | `public_proposals.py:100,628-629,698-731` (PA-02) |
| Price re-lock | JWT; optional version/idempotency | TOCTOU | **None** — one-way overwrite | None | **sim rate source mutating real trip** | `price_lock.py:117-127,169-179,198-285`; mounted `server.py:1452` (PA-06) |
| VCC issuance (fulfillment) | JWT + proposal `status=="accepted"` + lease fence | Lease yes, op no | **No void path** | **Self-reported** | **sim** — fabricated PAN even in livemode | `booking_fulfillment.py:77-181`; `stripe_issuing_adapter.py:80-127` (PA-05) |
| GDS PNR/e-ticket | Same | No | No | Self-reported | sandbox-preview | `booking_fulfillment.py:111-116` |
| Settlement VCC | JWT | No | No | n/a | sim, preview-wrapped | `settlement_engine.py:101-132`; `financial_settlement.py:29,121` |
| Advisor payout authorize | **NONE — unauthed mount, no internal dep** | No | No | No | sim (in-memory fake-seeded ledger) | `server.py:1473`; `subagent_payouts.py:37`; `commission_reconciliation.py:13,27-71` (PA-09, PA-23) |
| Corporate policy override | JWT but **self-certifying** (free-text approver, no role/dual-control) | No | No | Audit event only | real durable write | `corporate_policy.py:110-147` (PA-26) |
| Negotiation start/accept | **Unauthed mount** (pure computation, no persistence) | n/a | n/a | n/a | sim, ESCALATE_TO_HUMAN at max rounds | `server.py:1470`; `bargaining_engine.py:96-115` |
| Crisis / distribution | **Unauthed mounts**, preview-only truth declared in code | n/a | n/a | n/a | sandbox-preview (honest) | `server.py:1469,1471`; `crisis_ops.py:25-60`; `distribution.py:22-37` |
| Collection single-use token | HMAC + hashed, TTL | Used-marker not CAS | Revoke endpoint | SQL persisted | real | `public_collection.py:109,146-169`; `collection_service.py:75-168` (PA-16) |
| Messaging webhooks | HMAC-SHA256 fail-closed | Dedup solid | n/a | Signature surfaced | real (scheme) | `messaging.py:34-44,101-116` |
| Confirmations void | JWT + timeline | Yes | Void is the compensation | Timeline | **real — best in repo** | `confirmations.py:270,86,113-114` |

**The money path ships without any `TierMetadata` envelope** — `reality_tier.py` exists and is used by distribution/crisis/settlement, but not by `booking_fulfillment.py` or `proposal_compiler.py`.

### 5.2 Authority map (what happens without a human)

| Action | Autonomy level | Policy object actually consulted | Gap |
|---|---|---|---|
| Pipeline stage auto-advance | L1, default ON | `agency_settings.autonomy` + `auto_advance_stages` (`agency_settings.py:317`); NB02 gate enforces review/block (`gates.py:156-247`) | Working |
| Proposal accept → fulfillment trigger | **L2+ — traveler e-sign is the only authorization** | `AuthorityGateKeeper` dual-control exists but is catalog-only; registry `max_budget_impact` never consulted (`registry.py:72-81`; sole ref `boundaries.py:134`) | **PA-08** |
| Advisor payout | L3-analog, **zero authority** | None | **PA-09/PA-23** |
| Corporate override | L0 form-fill, self-approval | `require_pre_approval` flag exists, unused by approve endpoint | **PA-26** |
| Negotiation auto-ACCEPT | L1 bounded (≤ target), ESCALATE at max rounds | None persisted | Acceptable (decision-support only) |

**Progressive-commitment verdict:** `fulfill_accepted_proposal` executes verification, authorization-check, card issuance, PNR creation, JDG mint, and trip write inside one function with no pause (`booking_fulfillment.py:96-178`). Nothing irreversible currently touches real rails, so this is **latent, not live** — but the moment `stripe_issuing_adapter.py` gains a network call, the system will issue money instruments on a traveler e-sign alone, with the human dual-control machinery unwired and the acceptance record non-durable.

---

## 6. Observability, provenance, verification, evaluation, cost (S4)

### 6.1 Trajectory reconstruction — can an operator reconstruct WHY?

**Yes, but only by leaving the operator surface.** `run_gap_and_decision` persists a rich rationale (blockers, contradictions, confidence scorecard, feasibility) and NB02 appends the autonomy verdict (`raw_verdict, effective_action, approval_required, rule_source, reasons`) inside the decision artifact (`decision.py:2269-2290`; `orchestration.py:446-457`), checkpointed to the run ledger and served on `GET /runs/{id}`. OTel is genuinely configured with an OTLP exporter (`server.py:74-101`).

**Exact break point (PA-01-class P1, PA-04):** in `run_spine_once`, the audit-event emission into the trip timeline fires **only when `stage_callback is None`** (`orchestration.py:270-280,308-320,496-506`) — and production always supplies a `stage_callback` (`pipeline_execution_service.py:300`). The operator-facing trip timeline (`/api/trips/{id}/timeline`) therefore never receives intake/decision/escalation events; its only spine entry is a bare `trip_created`. There is also an id-space mismatch (timeline matches on `details.trip_id`; orchestration emits `packet_id`). Decision evidence lives in a disjoint filesystem store keyed by run_id.

### 6.2 Completion: asserted vs demonstrated

| Claim site | Verified against environment? |
|---|---|
| Spine run success | Partially — trip save required, but no version bump / read-back |
| ESCALATE early-exit lead save | **No** — failure only logged; run still marked blocked; lead can be silently lost (PA-27) |
| `fulfill_accepted_proposal` | **No — self-asserted** `FULFILLED_CONFIRMED` from sandbox adapters; TripStore failure swallowed; VCC issued before any verification (PA-05) |
| QualityEscalationAgent | Yes (acts on returned record) — but it is a router, not a quality judge |
| ClosedLoopLearningAgent | Write verified; **verdict unproven** (string-compare shadow test, never re-executes the pipeline) (PA-21) |

### 6.3 Reviewer value (persona: reviewers must demonstrably detect failures)

| Reviewer | Reality | Verdict |
|---|---|---|
| LLM-as-judge default scorer | Scores output **shape** (field presence, lengths); own tests are its only consumer; no calibration | **Reviewer illusion (PA-22)** |
| RAG groundedness | 0.4×retrieval + 0.6×lexical overlap; honestly disclaimed; echo-vocabulary hallucination passes | Partially honest (PA-33) |
| Closed-loop fix verdicts | `failure_layer == next_fix_layer` string equality; "proceed" asserted, not demonstrated | PA-21 |
| Autoresearch loop | Hardcoded simulated metrics; writes `{"accepted": true}` lineage | Prod-safe, **eval-dishonest (PA-11)** |
| D6 eval audit lanes | Live-graded real engines vs golden fixtures; `category_authority` blocks fixture-mirror self-grading; hybrid config recorded to prevent CI/serving divergence | **Proven — the model citizen** |
| Watchdog | Detects exactly one drift class (dashboard-sum) every 10 min; cannot see decision drift, tampering, cost, stale completions | Narrow but honest (PA-37) |

**Eval honesty today:** `manifest.yaml` — budget + colloquial **gating**; activity/weather/safety/extraction/pipeline/gap_decision **shadow** (gap_decision honestly documented at 0.57 vs 0.95 bar, 13 drifting scenarios); pacing/logistics/documents planned. **Evals measure accuracy only** — cost, latency, and human-intervention rate are unmeasured across all categories (PA-34).

### 6.4 Cost accountability

The usage guard is real and wired (`hybrid_engine.py:550-631`; `usage_store.py:99-127`), but `usage_events` has no trip/run/decision id — the system can answer "what did this agency spend on feature X" but **not "what did this decision cost"** (PA-20). `GET /metrics` claims to be Prometheus and returns a static JSON body (PA-10).

### 6.5 Provenance

Field provenance **is consumed** (authority weights feed confidence and blocker logic, `decision.py:508-525,1770-1776,1986-1990,2184`) and the epistemic JSON-LD proof graph is served and rendered to operators (`epistemic.py:88-105`, `EpistemicPanel.tsx`) — genuine strengths. Memory SHA-256 `verify_integrity` has zero callers (PA-32). The audit hash chain is well-designed, **never verified outside tests**, unanchored, and silently invalidated by its own 10k tail-compaction; `/api/audit` reads a different, unchained store (`persistence.py:2400-2500`; `routers/audit.py`) (PA-19).

---

## 7. First-principles / long-term / doctrine alignment assessment

This section answers the core ask directly. For each implementation area: **1P** = first-principles soundness (does the mechanism match the real problem?), **LT** = long-term viability (will this survive scale, providers, operators?), **DOC** = doctrine alignment (§2 truth, §11 engineering, §12 AI-output boundary, §13 claim reality) and persona-principle alignment.

| # | Area | 1P | LT | DOC | Reasoning (evidence) |
|---|---|---|---|---|---|
| 1 | Deterministic intake spine (extract→gates→decision→fees) | ✅ | ✅ | 🟡 | Rules where rules suffice is the textbook minimum-necessary-agency rung. Doubt: determinism is enforced by credential absence, not architecture (PA-03) — doctrine §12 violated in spirit ("a better model does not repair a broken pipeline"; here a credential silently changes the pipeline). |
| 2 | Supervised agent fleet + leases + DLQ | ✅ | ✅ | ✅ | Explicit per-agent contracts, deterministic termination, fail-closed freshness. Durability thinner than vocabulary (in-memory coordinator/checkpoints fallback, PA-30) is the one LT gap. |
| 3 | Trip persistence core (status guard, CAS, pinned backend) | ✅ | ✅ | ✅ | The strongest data-integrity surface in the repo. |
| 4 | Proposal capability tokens (sign/revoke/verify) | ✅ | ✅ | ✅ | Fail-closed, durable, restart-safe — exactly proposal→authorization separation done right. |
| 5 | Money path (fulfillment → settlement → commission) | ❌ | ❌ | ❌ | Proposal/validation/authorization/execution/verification collapsed in one function; completion self-asserted from sim adapters; acceptance evidence non-durable (PA-02/05); simulated rates permanently mutate the price-of-record (PA-06); nothing links booking totals to settlement/payout downstream. Doctrine §13 (claim reality) is the violated clause. |
| 6 | Authority machinery (governance registry, dual-control) | ❌ | ❌ | ❌ | Objects exist, enforcement is zero (PA-08). "Separation of intelligence and authority" is currently a diagram, not a property. |
| 7 | 5-tier memory graph | ✅ design / ❌ delivery | 🟡 | 🟡 | Full lifecycle machinery (decay/tombstones/GDPR) that no decision reads (PA-18). Memory hoarding without read-path = complexity without value — the persona's "memory accumulation without lifecycle" inverted: lifecycle without consumption. |
| 8 | Eval system | ✅ (D6 lane) / ❌ (judge, autoresearch, closed-loop) | ✅ / ❌ | ✅ / ❌ | The D6 lane proves what it claims (mirror-authority quarantine is genuinely advanced). The judge scores shape, the autoresearch loop grades simulations into "accepted" lineage, closed-loop verdicts are string compares — all violate doctrine §2 (static/synthetic inspection presented as verification). |
| 9 | Observability | 🟡 | 🟡 | 🟡 | Decision rationale persistence is excellent; the operator timeline is structurally blind in production (PA-04), `/metrics` is fake (PA-10), cost is not decision-attributable (PA-20), audit chain self-breaking and unverified (PA-19). |
| 10 | State/lifecycle (ledger, drafts, leases, undo) | 🟡 | ❌ | 🟡 | Trips solid; ledger unbounded + O(N) scans (PA-12), lazy sweep races threads (PA-17), recovery class-blind (PA-07), undo/redo in-memory cross-agency bypassing guards (PA-15). These are the LT killers under real load. |
| 11 | Simulated surfaces (IVR, council, router, compiler, journey graph) | ❌ | ❌ | ❌ | The doctrine §13 boundary is repeatedly crossed at the API layer even where frontend badges exist (`"status":"success"` for a never-placed call, PA-28), and the uncommitted tree regresses it on a public, unauthenticated route (PA-01). |
| 12 | Uncommitted in-flight work (assignments queue, FreshnessCard, price-lock BFF, journey graph, share tokens) | mixed | mixed | ❌ for 2 items | Escalated-queue read-model: aligned. FreshnessCard/price-lock BFF: aligned, canonical stack respected. Journey-graph public synthesis + compiler share-token-for-synthetic-inventory: doctrine violations introduced in the current working tree (PA-01, PA-25). |

**Persona's failure modes caught (from §21):** agentification-for-its-own-sake (Council/router/checker — PA-35) · multi-agent theater (council with zero callers) · memory hoarding inverted (write-only memory, PA-18) · reviewer illusion (judge/closed-loop, PA-21/22) · self-reported completion (fulfillment, PA-05) · hidden authority (registry/dual-control unwired, PA-08) · blind-retry-adjacent (class-blind recovery, PA-07) · coordination races (concurrent same-trip runs, PA-13; collection TOCTOU, PA-16). Not caught: god agent (no), context soup (context is constructed deliberately), infinite loops (all bounded except inbound SSE).

**What "the best" looks like (target state):** the repo is ~80% of the way to a genuinely first-principles agentic architecture. The remaining 20% is mechanical, not creative: (1) make the deterministic/agentic boundary an explicit, documented, default-off opt-in rather than a credential accident; (2) wrap every money/legal surface in the existing `TierMetadata` reality envelope; (3) wire the authority objects that already exist into the two execution paths that matter (fulfillment, payout); (4) give the run ledger a lifecycle and the failure record a taxonomy; (5) join decision evidence into the operator timeline; (6) delete-or-wire the five theater components; (7) point the memory read-path at the two decision slot points. Nothing above requires new architectural invention — every primitive already exists in the codebase.

---

## 8. Consolidated new findings (PA-01…PA-37)

Full register with EXPLORE/IMPLEMENT/DECIDE/RECORD classification, per-finding alignment verdicts, and improvement options: see [FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0700_2026-09-06](FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0700_2026-09-06.md). Summary:

- **P0 (2):** PA-01 public unauthenticated fabricated journey graph (uncommitted); PA-02 proposal acceptance non-durable.
- **P1 (9):** PA-03 credential-dependent determinism; PA-04 production timeline blind to decisions; PA-05 self-asserted fulfillment; PA-06 fabricated price-lock writes; PA-07 no failure taxonomy; PA-08 decorative authority; PA-09 unauthed money-adjacent routers; PA-10 fake `/metrics`; PA-11 simulated autoresearch lineage.
- **P2 (16):** PA-12…PA-28 (ledger GC, run idempotency, SSE bounds, undo/redo, collection CAS, sweep race, memory read-path, audit chain verification, cost attribution, closed-loop verdicts, judge calibration, payout ledger, capability-token fallback secret, compiler share tokens, corporate self-approval, lead-save swallow, IVR success).
- **P3 (9):** PA-29…PA-37 (lease/requeue retention, checkpoint durability, retention enforcer, provenance verification, groundedness, eval dimensions, theater components, Tier-3 scorer, watchdog scope).

## 9. Drift and in-flight work

The working tree carries uncommitted capability (506+/95− across 12 files + 5 untracked): escalated-queue read-model (`assignments.py`, tested), journey-graph hydration incl. the P0 public route, proposal-compiler share tokens, companion-page FreshnessCard + price-lock BFF (both clean), hook re-pins. Per the consolidation sweep, this diff **does not close any documented register row** — it adds capability pending commit authorization (owner gate F-04/EV-11), and two of its items are the audit's P0 (PA-01) and a P2 (PA-25). The 2026-09-05 register-wave remediation (F-30…F-40) is not present as register-row closures in the current diff state; treat EV-09's note (F-30 tests are AST-only) as standing.

## 10. Explicit (already-documented) findings state

Canonical register: `Docs/review/FINDINGS_REGISTER_2026-08-31.md` — **145 rows: 91 open / 53 closed / 1 deferred** (parser-verified today). Owner-gated DECIDE items: C-01 wire-or-archive Frontier/Council; C-03 router ratification; C-04 SLM posture; D-01/D-02/D-03 product contracts; R-09 signup; R-10 business model; F-04 commit-split. Release decision stands: **NO-GO public/paid; CONDITIONAL-GO invite-only pilot** (`Docs/LAUNCH_STATUS.md`). Detailed explicit inventory with action classes: register doc §Part B.

## 11. Uncertainties (truth taxonomy)

- **Observed:** every file:line citation in §3–§6 and all P0/P1 claims (lead-verified).
- **Inferred:** "determinism holds in deployed environments because no GEMINI_API_KEY is set" — assumes `fly.toml`/compose reflect the actual deployment env; the exact env of any live deployment is Unknown (check: runtime env of the deployed app).
- **Inferred:** the 648MB/18,987-dir ledger figure was observed during the sweep and will drift; treat as magnitude, not exact.
- **Unknown (needs Tier 2/3):** whether any non-test caller of the hybrid engine exists outside `generate_risk_flags` (grep found none; not exhaustive across scripts/tools); whether `GEMINI_API_KEY` exists in any deployment secret store; hosted/multi-worker behavior of every finding (all findings are local-tree Tier 1).
- **Contested:** the 2026-09-03 architecture map's honesty note ("serving path 100% deterministic… hybrid orphaned behind default-off flag") vs this audit's PA-03. **This audit's reading is verified against code and supersedes the map note; the map should be amended per PA-03 remediation.**

---

## 12. Addendum — Independent verification pass 2 (2026-09-06, same day)

The three sweeps that initially failed on rate limits (S2, S4, S5) were re-run as fresh independent passes (same dimension prompts, no leading hints) and reconciled against pass 1. Disposition:

### 12.1 Upgrades

| ID | Change | Evidence (pass 2, lead-verified) |
|---|---|---|
| **PA-05: P1 → P0** | Fulfillment is not merely self-asserted — the write path is **broken**. `booking_fulfillment.py:137,149` calls `TripStore.get(trip_id)` / `TripStore.update(trip_id, updates)`; TripStore exposes `get_trip`/`update_trip` (`persistence.py:458,510`) — neither called method exists, the `AttributeError` is swallowed (`:150-151`), and `FULFILLED_CONFIRMED` is returned with the trip record **never updated at all**. Booking confirmation persists nowhere. | Lead-verified by grep + method inventory |
| PA-18 (strengthened) | Not only is memory never read — **forgetting never executes**: `MemoryDecayEngine`, `GdprEngine`, `EligibilityGate` have zero callers; supersession happens only at write; tombstones filtered only if a query arrives. The GDPR-erasure capability is dead code on both paths. | Pass 2 exhaustive grep |
| PA-30 (strengthened) | `CheckpointStore` and `DLQInspector` have **zero external callers** (not just in-memory); `DLQInspector.replay_job` flips status to `REPLAYED_SUCCESSFULLY` and returns a payload **without executing anything** (`dlq_inspector.py:90-92` — lead-verified). | Lead-verified |
| PA-17 (demonstrated) | The sweep race is no longer inferred: a sampled ledger run shows `error_message: "Run timed out after 48310s (max 300s)"` — a run stayed `running` for 13.4 hours until a poll drove the lazy sweep. | Pass 2 observation |
| PA-01 (nuance) | The uncommitted test `test_journey_graph_hydration.py` **pins the fabricated-fallback path** (asserts 200 + synthesized DAG for arbitrary IDs) — the test currently locks in F-41 behavior and must be rewritten, not just the route. Under `SPINE_API_DISABLE_AUTH` the public route additionally honors client `X-Agency-ID` (`core/auth.py:182-185`), widening cross-tenant read exposure. | Pass 2 + S5 refresh |

### 12.2 New findings (pass 2)

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| PA-38 | **Escalation split-brain (affects uncommitted in-flight work):** recovery-agent escalation writes `trips.review_status="escalated"` (`recovery_agent.py:323` → `agent_runtime_adapters.py:31`), but the new escalated-queue endpoint reads `TripRoutingState.status=="escalated"` (`routers/assignments.py:121-122`). Two escalation surfaces that never converge — recovery-escalated trips are invisible in the new queue. | Lead-verified | P2 |
| PA-39 | Draft `promote` bypasses the optimistic-version support its own store provides: `draft_store.py:374-384` patches `promoted_trip_id` with no expected_version and no terminal-status guard — a second promote overwrites the trip linkage (last-writer-wins). | Pass 2 | P3 |
| PA-40 | The durable idempotency CAS machinery (`src/agents/idempotency.py`, fencing tokens, 24h reclaim) is wired to only **two** ingress paths (`routers/inbound.py:43`, `services/messaging_webhooks.py:15`) — POST /run, price-lock, fulfillment, and promote all bypass it. Context for PA-13/PA-02/PA-05. | Pass 2 | P3 (context) |

### 12.3 Corrections to pass-1 findings

- **PA-15 (undo/redo)** — pass 1 said restored state "bypasses status guard/CAS". Pass 2 refinement: undo/redo **never writes TripStore at all** — it returns a state payload for the client to apply (`trip_history.py:30-73`). It therefore cannot corrupt the store, but it also cannot actually restore anything: non-durable, agency-unscoped, and **non-authoritative theater**. Severity unchanged; mechanism corrected.
- **PA-27 (ESCALATE lead-save failure)** — pass 1 said "silently lost". Pass 2: the failure **is logged loudly** and the run is marked BLOCKED; the lead is lost to the traveler but not to the ledger. Corrected wording: *loud but unrecoverable* (no retry/DLQ path).
- **Provenance consumption nuance** — pass 1 reported memory authority weights feeding decision confidence (consumed); pass 2 reports the **epistemic engine's** `ProvenanceSlot`/decayed-confidence has no consumers in decision/gates/proposal-compiler, and `ProvenanceEngine.verify_integrity` has test-only callers. Both are true — they are different subsystems: memory authority weights are consumed; epistemic field provenance is write-only (extends PA-32).

### 12.4 Confirmed unchanged (double-verified)

PA-02, PA-03, PA-04 (with sharper break-point: only the safety-stage event emits unconditionally; `pkt_` vs `trip_` id-space mismatch confirmed), PA-06, PA-07, PA-08 context, PA-10, PA-11 (exact fabricated formulas: `accuracy = 0.94 if rag_top_k >= 5 else 0.88`, `safety = 0.99` — `autoresearch_loop.py:77-88`), PA-12 (648MB/18,987 dirs re-measured), PA-13, PA-14, PA-16, PA-19 (+ confirmed `/api/audit` SQL-vs-JSONL split and trim-breaks-chain), PA-20, PA-21, PA-22, PA-26, PA-29, PA-37.

### 12.5 Register refresh (pass 2, S5)

- Canonical register is now authoritatively **147 rows: 93 open / 53 closed / 1 deferred** (checker-verified); F-41/F-42 were promoted today as register Part 4f. The complete 93-ID open enumeration now exists in the reconciliation record below.
- Per the findings lifecycle (no second status store), **PA-01…PA-40 require additive promotion into `FINDINGS_REGISTER_2026-08-31.md`** — flagged as a Phase-0 gate step; not executed unilaterally because the register is a shared hot file (register-wave lesson: additive append only).
- F-42 adds a detail pass 1 missed: ProposalCompilerPanel's fulfillment-chain UI calls **404 via the BFF route-map** — the panel's fulfill flow is dead wiring, not just dishonest labeling.

**Net effect of pass 2:** the audit's verdicts stand; the money path is worse than first reported (PA-05 P0), memory is deader than first reported (PA-18), and two new in-flight defects (PA-38) and one broken-path confirmation (PA-05) sharpen Phase 0. P0 count is now **three**: PA-01, PA-02, PA-05.

---

## 13. Implementation record — PER-0700 remediation wave (2026-09-06, same day)

Owner directed implementation of the P0 (3) + P1 (7) + P2 (15) findings — 25 total. Executed by three parallel implementation agents with disjoint file ownership (money/authority · API surface · pipeline/ledger) plus lead integration of the cross-cluster seams. **All 25 implemented; every fix S2-verified locally; zero ruff warnings; no commits (owner gate F-04/EV-11 stands).**

### 13.1 Disposition (all 25)

| Finding | Fix shape | Key S2 evidence |
|---|---|---|
| PA-01 (P0) | Fabrication deleted; public route requires signed share token matching trip; scoped-lookup failures → 503; hydration test rewritten to pin abstain-not-synthesize | Old test pinned fabricated 200; new 10-test suite pins 404/abstain/token-mismatch |
| PA-02 (P0) | `accept_proposal` persists `proposal_accepted_at/_by/_acceptance_token/esign_consent` on the trip (+409 no durable trip); fulfillment authority reads the durable field | Registry-only acceptance → rejected (was FULFILLED_CONFIRMED) |
| PA-05 (P0) | `get_trip`/`update_trip` fixed; swallow removed; read-back verification; sim-tier reality metadata on result + router envelope | Store failure now raises; persisted PNR verified on read-back |
| PA-03 | Default `"0"` (engine + factory); fly.toml pin removed; compose `:-0`; enable warning; eval snapshot realigned (unset → "0", `default_enabled: false`) + D6 snapshot regenerated & verified | 143 hybrid/decision tests pass; 266 eval tests pass |
| PA-04 | `pipeline_execution_service._emit_decision_evidence` writes `spine_decision` events with real trip_id (NB01/NB02 verdicts, rule_source, rationale) on success/degrade/escalate | S2 in `test_pa_agentic_remediations.py` (47 tests) |
| PA-06 | Re-lock PREVIEW-ONLY (`effects:[]`, `provider_connected:false`); version + idempotency required (422). Supersedes persistence half of F-01/F-32, guards retained | `test_relock_leaves_trip_byte_identical` — trip deep-equal before/after |
| PA-07 | `spine_api/failure_taxonomy.py` (8 classes); `fail()` persists `failure_class` + `stage_at_failure`; recovery branches class-aware | Taxonomy units + ledger roundtrip + recovery-branch tests |
| PA-08 | `enforce_action_authority()`/`AuthorityDenied` in governance registry; wired into fulfillment (cap → 403 `escalation_required`) and payouts ($2k cap) | 8 tests; over-cap payout leaves ledger untouched |
| PA-09 | `_auth_or_skip` on distribution/negotiation/crisis_ops/subagent_payouts includes | 401-unauthenticated test per router |
| PA-10 | New `spine_api/metrics_registry.py` + real v0.0.4 exposition; run-outcome/failure-class counters wired at every pipeline terminal path | 6 registry tests; `/metrics` renders counters |
| PA-12 | `RunLedger.prune_expired_runs(30d, cap 500)` — terminal-only, never touches unknown dirs; lazy trigger opt-in via `WAYPOINT_RUN_LEDGER_GC=1` | Prune safety/cap/throttle tests on tmp dirs |
| PA-13 | `Idempotency-Key` header → durable CAS registry (replay/409/TTL-reclaim); key + fencing token stashed in run meta; terminal `mark_completed`/`mark_failed` wired | 4 header tests incl. replay |
| PA-14 | SSE 240-cycle budget + `STREAM_LIMIT_REACHED {reconnect:true}` + listener-dict pruning | 6 tests |
| PA-15 | History endpoints agency-scoped (`get_trip_for_agency`, 404 mismatch); stack capped 50 drop-oldest; payload semantics documented | 9 tests |
| PA-16 | `mark_token_used` single CAS `UPDATE … WHERE status='active'`; 410 on loss | Double-consume test: one True, one 410 |
| PA-17 | Checkpoint heartbeat (`heartbeat_at`); sweep skips fresh heartbeats; `complete_after_timeout` reconciles the race | S2 race-reproduction test passes |
| PA-20 | Zero-migration contextvar correlation (`set_usage_context`) into `usage_events.metadata_json`; bound at run start, re-bound post-materialization | Correlation keys asserted (InMemory + SQLite) |
| PA-21 | Verdict labeled `verdict_basis="heuristic_string_match"`, `demonstrated=False` (+ trip fields); consumers grep-verified none treat it as authoritative | Closed-loop tests assert honesty fields |
| PA-23 | uuid payout ids; demo seed gated non-production; ledger reality metadata (`in_memory_preview`, `durable=false`); authority enforced | Prod-env → zero balances; collision test |
| PA-24 | `CAPABILITY_TOKEN_SECRET` fallback removed; fail-closed `_require_capability_secret()` mirrors proposal-key posture | Fail-closed tests; router fixture sets dev env |
| PA-25 | Package carries `reality_tier:"simulated"`; share minting blocked by default (`allow_share_for_simulated=False`); panel rewritten (fabricated TRIP-LIVE-772 chain removed) | Compiler e2e + 116 workbench tests + tsc clean |
| PA-26 | Approver from authenticated principal; owner/admin role enforced (403); `require_pre_approval` → `pending_second_approval` staging (same-principal 409) | 5 new tests; F-30/strategic tests adjusted S2 |
| PA-27 | Lead-save retried once; second failure → FAILED `failure_class="state"` + `LeadPersistenceError` | `test_escalate_lead_save_failure_is_loud_and_failed_not_blocked` (failed-before: blocked-cleanly) |
| PA-28 | `status:"simulated"` + reality metadata + `effects:[]` on IVR dispatch/bridge | 3 router-honesty tests |
| PA-38 | `routing_service.system_escalate` (canonical, any-status, idempotent) + adapter mirror in `set_review_status` (loud on failure) | 6 tests in `test_pa38_escalation_mirror.py` |

### 13.2 Integration seams (lead-implemented)

- Pipeline terminal paths increment real `/metrics` counters and finalize the PA-13 idempotency records (completed/blocked → `mark_completed`; failed → `mark_failed`) using the fencing token stashed in run meta at submission.
- Eval snapshot hybrid default realigned (unset → "0") + D6 snapshot regenerated/verified — closes the CI/serving divergence risk C flagged for X-09.
- Fulfillment router: `AuthorityDenied`/HTTPException pass-through (the broad `except` would have converted the PA-08 403 into a 500) + `FULFILLMENT_TIER_METADATA` response envelope.
- Route + D6 snapshots regenerated; parity tests green; all 266 eval tests pass; register Part 4g promoted (PA-01…PA-40, parser-validated).

### 13.3 Honest boundaries of this wave

- All evidence is **local Tier 1/2** (S2-focused suites + this wave's full-suite run). Hosted, multi-worker, and browser-tier verification remain verify-first — fixed-locally rows therefore stay open-partial in the register per lifecycle convention.
- PA-13's per-trip in-flight lease (keyless concurrent submissions) remains open; PA-20's schema-column correlation needs alembic custody (A-20); PA-23's SQL payout ledger + settlement reconciliation remain open under F-04.
- The run-ledger GC is opt-in (`WAYPOINT_RUN_LEDGER_GC=1`) for data safety; first prune is a documented operator command.
- PA-11/18/19/22/29–37/39/40 were not in the directed scope and remain open (register Part 4g).

### 13.4 Full-suite baseline

Canonical runner `scripts/run_backend_tests.sh`, dev server stopped per F-19: **3,987 passed / 0 failed / 44 skipped** (2026-09-06, 329s). Two failures on the first post-wave run were fixed before the clean baseline: (1) `test_run_contract_drift_guard` — the minimal-contract guard updated for PA-13's deliberate additive `idempotent_replay` field; (2) `test_health_router_behavior` — a **pre-existing committed regression from `096ceba`** (shared-tree drift fix): the router's fail-loud fallback honestly returns `degraded` + `health_probe_error`, while the committed test asserted the fabricated-success contract `"ok"`; the test now pins the truthful contract. Frontend: `tsc --noEmit` clean, 116 workbench tests pass. Route + D6 snapshots regenerated and green (parity 2/2, evals 266/266). Register parser: 188 rows, 0 warnings. `/metrics` requires auth (pre-existing posture at HEAD — scrape auth is an L1 deployment concern, noted not regressed).

---

## 14. Wave-2 record — open halves closed (2026-09-06, owner-directed)

The five open halves of the implemented P0–P2 set were closed in a second same-day wave, plus the live multi-process evidence the first wave lacked:

- **PA-13 (closed)** — per-trip/draft in-flight lease at the single `execute_spine_pipeline` choke point: `trip-run:*` keys via the durable IdempotencyRegistry (30-min crash-reclaim TTL), fenced release in `finally`; conflicts BLOCK the run with an explicit reason instead of racing (recovery never auto-requeues them). S2: 7 lock tests (pre-held lock → blocked-without-executing; release semantics; no-double-lock static guard).
- **PA-08 (closed)** — durable dual-control: `authority_approvals` table (RLS) + `authority_approval_service` (two-person rule: same-person second approval → 409, owner/admin role required → 403, CAS status transitions) + 5 approval endpoints on the boundaries router; over-cap fulfillment/payouts return 403 `approval_required` and proceed ONLY against a ratified approval (`ratified_authority_scope` cap elevation), with the approval id recorded in results/audit.
- **PA-20 (closed)** — real nullable `run_id`/`trip_id` columns on `usage_events` (additive alembic; SQLite store self-heals legacy files; metadata_json retained for pre-migration rows); INSERT/finalize populate them from the run-context.
- **PA-23 (closed except F-04 residuals)** — durable `advisor_payouts` table (RLS, zero-seeded, SQL default in production / memory in tests) + `reconcile_trip_commission` exposed on the payouts router: booking total → expected commission split vs recorded payouts (report-only; auto-repair stays with F-04).
- **PA-12 (executed)** — first prune ran: **11,316 terminal run dirs removed, `data/runs` 648 MB → 286 MB**; two corrupt-meta dirs safely skipped by design; `WAYPOINT_RUN_LEDGER_GC=1` wired into fly.toml (prod), compose dev default stays 0.
- **Migration custody** — one additive revision `pa_wave2_authority_payouts_cost` chained on `add_payment_mandates`; applied to the live dev DB (`alembic current` at head).
- **Live multi-process evidence (Tier 3)** — `tests/test_pa_wave2_live_probe.py`: 4 OS processes contending on live PostgreSQL — idempotency CAS single-winner ✅, work-lease single-winner ✅, collection-token CAS single-consumer ✅, usage correlation columns ✅. Auto-skips without DATABASE_URL; runs in CI against the PG service.
- **Shared-tree drift fixed en route:** unscoped `TripStore.get_trip` in `journey_graph.py`/`counterfactual.py` (CI tenant-isolation gate) → canonical agency-scoped reads; stress-benchmark aligned with the healer's AT-06 abstain contract via explicit `stored_graph=` injection (no fabricated graphs); ruff E402/F821 in `proposal_compiler.py` repaired.

Wave-2 full-suite baseline: recorded in the completion report (canonical runner, dev server stopped).
