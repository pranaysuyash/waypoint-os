# Codebase Features, Flows & Loops Map (2026-09-03)

**Status:** current-state architecture map (read-only exploration, no code changed)
**Date:** 2026-09-03
**Method:** four parallel read-only Explore sweeps — agent core (`src/`), backend API (`spine_api/`), frontend (`frontend/`), and the docs/tests/tools landscape — synthesized here with file-path citations.
**Scope:** features, end-to-end flows, and explicit loops (polling, background workers, retry/flywheel cycles) as the code implements them today. This is a map, not a spec: for product intent see [MASTER_PRODUCT_SPEC](../MASTER_PRODUCT_SPEC.md); for trip state rules see [TRIP_STATE_CONTRACT](../TRIP_STATE_CONTRACT.md).

> **2026-09-06 drift addendum:** [CODEBASE_FEATURES_FLOWS_LOOPS_MAP_DRIFT_2026-09-06.md](CODEBASE_FEATURES_FLOWS_LOOPS_MAP_DRIFT_2026-09-06.md) — commit `096ceba` (585 files: lifecycle read-model, trip-status invariant, field-merge precedence, platform auth, idempotency fencing, strategic expansion verdicts) landed plus working-tree drift; §5 of the addendum lists the corrections that supersede the sections noted here.

---

## 1. System at a glance

Three layers, one spine:

1. **Agent core** (`src/`) — the deterministic travel-intake pipeline `run_spine_once()` plus a supervised background agent fleet and ~30 domain engines (crisis, negotiation, memory, evals, distribution, …).
2. **Spine API** (`spine_api/`) — FastAPI wrapper: ~78 routers / ~500 endpoints, run lifecycle with file ledger, dual-store persistence, tenancy, and ~10 background loops.
3. **Frontend** (`frontend/`) — Next.js App Router operator cockpit + public/traveler surfaces, talking to the API through a BFF proxy with SSE-or-poll run status.

```text
Traveler inquiry (note/voice/social/PDF)
        │
        ▼
spine_api  POST /run ──► daemon thread ──► run_spine_once (src/intake/orchestration.py)
        │                                        extract → validate → NB01 → decision
        │                                        → suitability → NB02/D1 → frontier
        │                                        → strategy → fees → bundles → safety
        ▼                                        → readiness
file run ledger (data/runs/{run_id}/)  ◄── GET /runs/{run_id}  ◄── frontend poll (2s) or SSE
        │
        ▼
trip materialization (SQL, tenant-scoped) ──► draft promote ──► proposal ──► booking
```

Canonical entry points: `src/intake/orchestration.py:181` (`run_spine_once`), `spine_api/server.py:1927` (`POST /run`), `frontend/src/app/(agency)/workbench/PageClient.tsx` (operator cockpit).

---

## 2. Agent core — `src/`

### 2.1 The spine pipeline (`src/intake/orchestration.py`)

`run_spine_once(envelopes, stage, ...)` returns a `SpineResult`. Phase order as implemented:

| # | Phase | Where | Notes |
|---|---|---|---|
| 1 | Extraction | `src/intake/extractors.py:2107` | Regex-only (explicitly "not an LLM") → `CanonicalPacket` |
| 2 | Validation | `src/intake/validation.py:100` | `INTAKE_MINIMUM`, `QUOTE_READY`, numeric-budget modes |
| 3 | Gate NB01 (`intake_completion`) | `src/intake/gates.py:101` | `ESCALATE` → early exit; `DEGRADE` → partial save + follow-up questions |
| 4 | Decision | `src/intake/decision.py:1942` (`run_gap_and_decision`) | 10 sub-phases, see 2.3 |
| 5 | Suitability (3.5) | `src/suitability/integration.py` | `critical` flag forces `STOP_NEEDS_REVIEW` |
| 6 | Gate NB02 / D1 autonomy (`decision_readiness`) | `src/intake/gates.py:156` | `raw_verdict` + `effective_action` = auto/review/block from agency autonomy policy; safety invariant: `STOP_NEEDS_REVIEW` always blocks |
| 7 | Frontier orchestration (3.2) | `src/intake/frontier_orchestrator.py:45` | sentiment heuristic, Ghost Concierge trigger, intelligence pool, specialty RAG, auto-negotiation; feature-gated |
| 8 | Session strategy (4) | `src/intake/strategy.py:450` | goal, question sequence, tone; internal vs traveler-safe bundles |
| 9 | Fees (4.5) + PlanCandidate (4.6) | `src/fees/calculation.py`, `src/intake/plan_candidate.py:243` | risk-adjusted fees |
| 10 | Output bundles + safety | `src/intake/strategy.py:972`, `src/intake/safety.py` | leakage scan of forbidden internal concepts |
| 11 | Readiness (9.6) | `src/intake/readiness.py:276` | tiered proposal/booking readiness; never auto-advances stage |
| 12 | Fixture compare (10, optional) | `src/intake/orchestration.py:873` | eval assertions vs fixtures |

Vocabulary: `PipelineStage` NB01–NB06 and `GateIdentifier` in `src/intake/constants.py`; `DecisionState` = `ASK_FOLLOWUP / PROCEED_INTERNAL_DRAFT / PROCEED_TRAVELER_SAFE / BRANCH_OPTIONS / STOP_NEEDS_REVIEW`; gate verdicts `PROCEED / RETRY / ESCALATE / DEGRADE` (`src/intake/gates.py:26`). Every phase emits audit events (`TripEventLogger.log_stage_transition`) and OTel spans.

### 2.2 Intake & extraction

- `src/intake/extractors.py` (~2.9k lines): destinations (GeoNames-backed, `src/intake/geography.py`, ~590k cities; origin/destination context heuristics; "or/and" city sets; past-trip mention filtering; Hinglish stop-words), dates + flexibility, budget (₹/lakh/crore, ranges, stretch max, per-person "each"), party (colloquial composition, "4 of us", couple=2, decimal toddler ages, "N pax" wins), intent, owner context, sub-groups, passport/visa (stage-gated), MRZ parsing (`src/intake/mrz.py`).
- Derived signals include urgency and `sourcing_path` (`SourcingPathResolver`, `src/intake/extractors.py:2871`).
- Vision/document extraction: `src/extraction/` — Gemini/OpenAI extractors with a fallback `model_chain.py` (service layer retries a provider up to 2× before falling through the chain), `confidence.py`, `pdf_utils.py`.
- Epistemic layer: `src/intake/epistemic_engine.py` / `epistemic_arbiter.py` — field provenance, multi-turn conflict detection, implicit needs, negative exclusions, JSON-LD proof graphs.

### 2.3 Suitability & decision

- Suitability: static activity catalog + `evaluate_activity` (`src/suitability/scoring.py:128`) with most-conservative-tier downgrade; confidence clamped to [0,1] (`src/suitability/confidence.py:12`); unknown pace preference clamps to "balanced" with a warning (`src/suitability/integration.py:34`).
- Decision: `run_gap_and_decision` (`src/intake/decision.py:1942`) — ambiguity classification, budget feasibility/decomposition, MVB hard/soft blockers per stage, operating-mode routing, urgency suppression, contradiction classification (date/document conflicts → `STOP_NEEDS_REVIEW`; budget conflict → `BRANCH_OPTIONS`), confidence clamped to [0,1], invariant checks (blocking ambiguity or infeasible budget can never reach `PROCEED_TRAVELER_SAFE`), question generation incl. budget "stretch" semantics.
- Commercial signals: ghost/window-shopper/repeat/churn risk scoring (`src/intake/decision.py:1484–1565`, state machine in `src/intake/lifecycle.py`) feeding `decide_commercial_action` (`:1604`), incl. `ESCALATE_RECOVERY` → Ghost Concierge.
- Hybrid engine: `USE_HYBRID_DECISION_ENGINE=1` (`src/intake/decision.py:36`) routes risk flags through `src/decision/hybrid_engine.py` (rules → cache → LLM, circuit breaker `src/decision/health.py`). **Default is off — see §8 honesty notes.**
- Override learning (feedback loop): operator overrides applied each run (`src/decision/override_learning.py:54`, wired at `src/intake/decision.py:2168`); `SAFETY_INVARIANT_FLAGS` can never be suppressed; `learn_from_operator_override` + `pattern_matching.py` mine cross-trip pattern overrides (min strength 2).
- Group: `src/decision/group_consensus.py`, `group_pareto_engine.py` (Pareto-optimal preference resolution), `counterfactual_recovery.py`, `passenger_rights.py` (EU261/US-DOT).

### 2.4 Strategy, pricing & money

- Sourcing hierarchy: `src/intake/sourcing_path.py` — `internal_package → preferred_supplier → network → open_market`; resolver is currently a stub (owner constraints → `network`, default `open_market`).
- Fees: `src/fees/calculation.py` (risk-adjusted multipliers 1.0–2.0), `settlement_engine.py` (FX slippage buffers, VCC issuance, deposit/balance schedules, sub-agent commission splits), `currency.py`, `tax_compliance.py` (India TCS 206C(1G)/GST).
- Yield arbitrage: `src/yield_arbitrage/rate_parity_engine.py` (bedbank/GDS/CRS scans, re-ticketing), `multi_property_benchmark.py`.
- Negotiation: `src/negotiation/bargaining_engine.py:90` — game-theoretic loop: ACCEPT (≤3% tolerance) / COUNTER (split-the-difference) / REJECT → `ESCALATE_TO_HUMAN` at max rounds; `fee_waiver_bot.py`; `margin_optimizer.py` (dynamic take-rate, 10% floor).
- Charter: `src/charter/aviation_engine.py`, `empty_leg_scraper.py`.

### 2.5 Crisis, ops & resilience

- `src/crisis/models.py`: `CrisisSeverity`, `EvacuationMode` (air charter / commercial rebook / overland convoy / rail / ferry), `PassengerBeaconStatus`, `GeofenceArea`, `EvacuationManifest`, `GroundTransferDispatch`.
- Engines: `evacuation_engine.py` (multi-modal routing), `safety_beacon.py` ("I Am Safe" check-ins + STEP consular manifests), `ground_dispatch.py`; tied to `src/orchestration/duty_of_care_radar.py`.
- Ops: `src/services/resilience_engine.py` (circuit breakers, quarantine), `src/monitoring/perishable_sentinel.py` (visa/ticketing/insurance/deposit deadlines), `src/agents/dlq_inspector.py` (poison-job inspection + replay), `src/agents/checkpoints.py`, `src/orchestration/agent_lease.py` (monotonic fencing tokens).
- Telephony: `src/telephony/ivr_bypass_bot.py` (DTMF navigation, hold detection, human bridging).
- `src/orchestration/irops_healer.py`: disruption ripple → EU261/US-DOT claims → 3-tier counterfactual rebooking → lodging VCC → fee-waiver disputes. `src/orchestration/proposal_compiler.py:64`: epistemic parse → inventory costing → `MarginOptimizer` → Journey Dependency Graph → constraint feasibility → shareable proposal.

### 2.6 Memory

`src/memory/` — 5-tier graph (`Working / Episodic / Semantic / Procedural / Preference`, `models.py`) with source-authority weights (traveler_direct 1.0 … third_party_web 0.6), SHA-256 provenance hashes, supersession links, tombstones, half-life decay (`A(t)=A0·2^(−days/half_life)`; safety-critical facts infinite). Write curation gate (min confidence 0.75, `eligibility_gate.py`), retrieval with injection sanitization (`retriever.py`), GDPR Article 17 cascading erasure with signed certificates (`gdpr_engine.py`). Cross-trip relationships live in semantic memory.

### 2.7 Evals — the flywheel

- D6 audit scaffold: `src/evals/audit/` — fixture runner, precision/recall metrics, `manifest.yaml` where per-category status `planned/shadow/gating` gates CI (`gates.py:76`); snapshot built/verified via `scripts/generate_d6_gate_snapshot.py` / `verify_d6_gate_snapshot.py` into `data/evals/d6_audit_gate_snapshot.json`.
- Lanes: extraction P/R/F1, the **30-scenario NB02 corpus** (`data/fixtures/test_scenarios.py`) graded **live** through `run_gap_and_decision`, pipeline, activity. Currently gating: `budget`, `colloquial`; `gap_decision` is shadow (honest accuracy 0.57 vs 0.95 bar, documented in the manifest).
- Flywheel: `src/evals/agentic_feedback.py` (distills `ExecutionEvent`s into failure signals) → `src/agents/closed_loop_learning.py` (repeated-failure scan → fix candidate → shadow test → verdict) → `src/evals/autoresearch_loop.py` (baseline → mutate → composite score `0.4·acc + 0.3·safety + 0.2·speed + 0.1·cost` → accept/revert; lineage in `data/audit/autoresearch_experiments.jsonl`). LLM-as-judge: `src/evals/judge/`.

### 2.8 Background agent fleet

`src/agents/runtime.py` (~3.2k lines): lease/idempotency coordination, dead-letter quarantine, zombie-lease sweeper, and product agents — `FrontDoorAgent` (inquiry triage), `SalesActivationAgent` (stage-SLA follow-ups), `FollowUpAgent`, `QualityEscalationAgent`, `DocumentReadinessAgent`, `DestinationIntelligenceAgent` (freshness-gated), `WeatherPivotAgent`, and more below `runtime.py:1398`. Plus `operator_refinement_agent.py` (counterfactual generation on operator rejections), `live_tools.py` (freshness-policied tools with evidence contracts). Governance registry: `src/governance/registry.py` (capability scoping, execution limits).

### 2.9 Other domain modules (one line each)

`src/security/` (regex+SpaCy PII guard, jurisdiction policy, retention enforcer, Fernet encryption) · `src/distribution/` (Sabre/Amadeus sandbox adapters, NDC 21.3 client, EDIFACT parser, ATPCO fare rules) · `src/rag/` (multi-tenant hybrid retrieval + groundedness/citation engine) · `src/briefing/pre_departure_cadence.py` (D-7/D-3/D-1) · `src/corporate/policy_engine.py` (policy caps, approval chains) · `src/logistics/` (route geometry with 2-opt improvement while-loop at `route_geometry.py:350`, rooming lists, connection risk) · `src/analytics/` (owner approval state machine with request_changes → reassign-to-agent feedback edge; KDD override clustering) · `src/services/boundary_engine.py` (HMAC capability tokens, dual-control signoffs) · `src/schemas/journey_graph.py` (BFS dependency traversals) · `src/public_checker/live_checks.py` (isolated Open-Meteo enrichment) · `src/documents/visa_workflow.py` (D-45/D-30/D-15/D-7 milestones) · `src/compilers/itinerary_export_engine.py` · `src/benchmarking/stress_simulator.py` (500+ concurrent IROPS) · `src/llm/` (provider clients, usage guard).

---

## 3. Spine API — `spine_api/`

### 3.1 Server composition (`spine_api/server.py`, ~3.3k lines)

- Middleware order: CORS (`SPINE_API_CORS`) → `AuthMiddleware` (JWT; public allowlist `/health`, docs, `/api/auth/*`, `/api/public/*`, public-checker, proposal-token paths; `SPINE_API_DISABLE_AUTH` bypass, forbidden in prod) → body-size cap → slowapi rate limiting (e.g. public-checker 12/min).
- Lifespan (`server.py:1221`): fail-closed startup assertions (`core/startup_assertions.py`: `DATABASE_URL`, auth-not-disabled, `SECRET_KEY`, `ENVIRONMENT`, `TRIPSTORE_BACKEND`, `REDIS_URL`, public-checker agency, proposal signing key); prod guards (CORS explicit, no `*`/localhost); startup data mutations only in non-prod; **RLS posture validation** (all tenant tables RLS-enabled, FORCE where required); background loop starts (watchdog, agent runtime bundle, zombie reaper) — skipped under `RUNNING_TESTS`.
- 81 router mounts with per-router auth posture made explicit at the include site (`server.py:1463`); a set of endpoints remains inline in `server.py` (`POST /run`, `GET /metrics`, `GET /trips*`, payments queue, booking-data, collection-link, pending-booking-data accept/reject).

### 3.2 Router domains (~78 routers)

| Domain | Routers |
|---|---|
| Auth / workspace / tenancy | `auth`, `workspace`, `team`, `team_workflows`, `audit` |
| Runs / pipeline / runtime | `run_status` (**GET /runs/{id}** poll + stale-run sweep), `agent_runtime`, `agent_lease` (fencing tokens), `assignments`, `kdd`, `settings` (30 ep, biggest), `settings_health`, `legacy_ops` |
| Inbox / drafts / ingestion | `inbox` (read-model projection), `drafts` (CRUD + **promote** draft→trip), `inbound` (parse, optimistic-sync, follow-up prompt, **SSE**), `social_inbound`, `messaging` (+HMAC webhooks), `multimodal`, `customer_memory` |
| Trips / booking | `trip_lifecycle` (**reassess**), `trip_actions`, `trip_history` (undo/redo), `trip_observability` (timeline + SSE), `booking_tasks`, `confirmations`, `group_booking`, `group_pareto`, `trip_documents`, `document_extraction`, `proposal_compiler` |
| Public surfaces | `public_proposals` (token view / calculate / **accept with e-sign consent**), `public_checker` (+ inline run in server), `public_collection` (single-use hashed booking-data tokens), `trust_scorecard` (public route) |
| Money | `financial_ops`, `financial_settlement`, `commission`, `subagent_payouts`, `fx_sentinel`, `tax_compliance`, `price_lock` (72h window audit + re-lock with optimistic locking + per-trip idempotency keys, `price_lock.py:196`), payments queue (inline in server) |
| Crisis / in-trip | `crisis_ops`, `concierge`, `concierge_upsell`, `irops_healer`, `disruption_radar`, `counterfactual`, `duty_of_care_radar`, `visa_radar`, `passenger_rights`, `insurance`, `loyalty`, `feedback` |
| Distribution / supplier | `distribution`, `gds_sandbox`, `supplier` (owns contracts store used by price_lock), `negotiation`, `yield_arbitrage`, `yield_benchmark`, `charter_aviation`, `ivr_bypass`, `journey_graph` |
| Analytics / platform | `analytics`, `product_b_analytics`, `system_dashboard`, `trip_observability`, `resilience`, `boundaries`, `epistemic`, `constraints`, `stress_benchmark`, `rag`, `frontier`, `health`, `integrations`, `extraction`, `followups` |

### 3.3 Run lifecycle

1. **Create** — `POST /run` (`server.py:1927`): auth → `RunLedger.create` (state `queued`) → **daemon thread** runs the pipeline (deliberately not multiprocessing: fd-inheritance/flock deadlocks on fork) → returns `RunAcceptedResponse{run_id, state:"queued"}` immediately.
2. **State machine** — `spine_api/run_state.py`: `queued → running → completed | failed | blocked`. `blocked` is a first-class terminal state for policy/leakage blocks, distinct from system `failed`.
3. **Ledger** — `spine_api/run_ledger.py`: file-based `data/runs/{run_id}/` (`meta.json`, `steps/*.json` checkpoints, `events.jsonl`). **Stale-run sweep** (`timeout_stale_runs(300s)`) runs lazily inside `GET /runs/{run_id}` (`routers/run_status.py:57`) — the polling client drives it.
4. **Execute** — `services/pipeline_execution_service.py`: draft → `running` + audit; stage callbacks checkpoint each stage and emit events; OTel span. Terminal paths:
   - **ESCALATE early-exit** → persists an **incomplete lead** (`trip_status="incomplete"`), ledger `block()`, draft → `blocked`; **never overwrites an existing trip** (draft reprocess target resolution per `Docs/ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md`).
   - **partial intake** → trip saved incomplete, run `completed`.
   - **success** → `save_processed_trip(..., preserve_trip_id=...)` (re-runs update in place), draft → `completed`, feedback-driven recovery trigger if reopened.
   - `StrictLeakageViolation` → blocked; other exceptions → `failed` with `stage_at_failure`.
5. **Idempotency/concurrency** — new uuid4 per POST; SQL work leases (`agent_work_leases`, PK = idempotency key, `SELECT … FOR UPDATE`, 60s TTL, poison after max attempts, `services/agent_work_coordinator.py`); requeue jobs (`agent_requeue_jobs`, unique keys, `FOR UPDATE SKIP LOCKED`, backoff = lease window); price-lock re-lock uses `expected_version` optimistic locking.

### 3.4 Persistence & tenancy

- `spine_api/persistence.py` (~3.4k lines): `TripStore` facade dispatching on `TRIPSTORE_BACKEND` — `FileTripStore` (JSON, fcntl locks) vs `SQLTripStore` (async SQLAlchemy behind a sync bridge). Field-level PII encryption, **status guard on every write** (intake-blocked statuses cannot jump to quote-capable; history capped at 50), optimistic concurrency (`update_trip_if_version`). Tenant scoping via `get_trip_for_agency`. ⚠️ Dual-store is a known split-brain risk — `TRIPSTORE_BACKEND=sql` is pinned in `.env` (see root `AGENTS.md` data-safety rules).
- `spine_api/core/database.py`: async engine (pool 30+20, `pool_pre_ping`); checkout hook invalidates asyncpg connections owned by a foreign event loop. RLS via `app.current_agency_id` per transaction (`core/rls.py`); `memberships`/`workspace_codes` are FORCE-RLS-exempt (login chicken-and-egg).
- Key tables (`spine_api/models/`): `agencies/users/memberships/workspace_codes`, `trips` (intake fields + spine outputs + `booking_data`/`pending_booking_data`/`raw_input`), `agent_work_leases`, `idempotency_keys`, `trip_routing_states`, `audit_logs`, `booking_collection_tokens`, `booking_documents`, `document_extractions`, `booking_tasks`, `booking_confirmations`, `execution_events`, frontier tables.
- Drafts: `spine_api/draft_store.py` — lifecycle `open | processing | blocked | failed | promoted | merged | discarded`, capped per-draft event audit, `promote(draft_id, trip_id)`.

### 3.5 Contract

`spine_api/contract.py` (~1.6k lines, 130+ models). The load-bearing three: `SpineRunRequest` (`raw_note` 100k, `stage`, `operating_mode`, `draft_id`, intake hints, `extra="forbid"`), `RunAcceptedResponse` (async `{run_id, queued}`), and `RunStatusResponse` (poll payload with `decision_state`, `follow_up_questions`, `hard_blockers`/`soft_blockers`, steps, events, frontier result). Frontend types are generated from this contract (`scripts/generate_types.py` → `frontend/src/types/generated/spine-api.ts`).

### 3.6 Notable services

`messaging_webhooks.py` (webhook idempotency per provider `message_id` — retries replay the original reply) · `collection_service.py` (single-use SHA-256-hashed collection tokens, new token revokes prior) · `document_service.py` (magic-byte validation, streaming size cap, scanner abstraction) · `trip_lifecycle_service.py` (reassessment preserves trip id/status; `REASSESS_EDIT_TRIGGER_FIELDS` gate auto-reassess-on-edit) · `ghost_concierge.py` (connection-risk → proactive recovery) · `voice_copilot.py` (transcript → intake packet) · `commission_reconciliation.py` (in-memory IC payout ledgers) · `supplier_yield.py` (multi-supplier quote comparison) · `inbox_projection.py` (canonical inbox read model) · `payment_queue_service.py` (bucketed payment queue).

---

## 4. Frontend — `frontend/`

### 4.1 Surfaces

| Group | Paths | Purpose |
|---|---|---|
| `(agency)` | `overview`, `workbench`, `inbox`, `trips/[tripId]` (stage tabs: Intake / Details / Options / Quote Assessment / Output / Risk Review / Ops / Timeline), `inquiries/new` (alias of workbench), `quotes`, `bookings`, `payments`, `documents`, `reviews`, `audit`, `insights`, `knowledge(-base)`, `seasons`, `suppliers`, `settings` | Authenticated operator app |
| `(auth)` | `login`, `signup`, `join/[code]`, `forgot/reset-password` | httpOnly-cookie sessions |
| `(public)` | `booking-collection/[agencyId]/[token]` | Tokenized traveler data collection |
| `(traveler)` | `companion`, `itinerary-checker` | Traveler PWA; public checker |
| Token routes | `p/[token]` (public proposal accept), `g/[token]` (group deposit share) | Traveler-facing |
| Internal | `proposals/[proposalId]` | Agency-side proposal review |
| Marketing/dev | `/`, `v2..v5`, `pricing`, `corporate/offsites`, `intake/fast`, `api/scenarios/dev` | Landing iterations; dev/demo paths |
| BFF | `frontend/src/app/api/**` | See 4.3 |

### 4.2 Workbench (operational cockpit)

`frontend/src/app/(agency)/workbench/PageClient.tsx` (~1.4k lines), auth-gated. URL-driven tabs: `intake` (New Inquiry), `packet` (Trip Details — shown when a trip/validation exists or draft blocked/failed), `safety` (Risk Review), `council` (Persona Council), `frontier` (Frontier OS). Panels in the same folder: `RunProgressPanel`, `PipelineFlow`, plus ~25 domain panels (Negotiation, ProposalCompiler, Distribution, YieldArbitrage, FinancialSettlement, DutyOfCareRadar, CrisisEvacuation, CharterAviation, DocumentMRZ, GDSSandbox, IROPSAutoHealer, IVRBypass, Epistemic, StressBenchmark, `TimeTravelScrubber`, `JourneyGraphVisualizer`, …).

- **Repair banner**: on invalid validation or `ESCALATED`/`BLOCKED` (no active run) a persistent banner deep-links to `/trips/{tripId}/intake?repair=<field>` (`src/lib/repair-deep-link.ts`).
- **Drafts**: 5s-debounced autosave, 409 → `save_state='conflict'`; `promoteDraft` then route via `getPostRunTripRoute()`. Recovery banner for `feedback_reopen` trips.

### 4.3 State & data

- **BFF proxy**: catch-all `api/[...path]/route.ts` → `src/lib/proxy-core.ts` (forwards cookies to `SPINE_API_URL`, default `http://127.0.0.1:8000`; 120s timeout; route allowlist `src/lib/route-map.ts`, unknown → 404). Explicit routes override for auth, trips, inbox, followups, runs, scenarios, and `api/stream-events/[runId]` (SSE proxy injecting the Authorization header EventSource cannot send).
- **Client HTTP**: `src/lib/api-client.ts` — 30s timeout, default `retry: 2` exponential backoff; on 401 a single deduped `POST /api/auth/refresh` then one retry.
- **State**: TanStack Query (`useTrips` staleTime 30s, `useSpineRun`, `useSSEStream`, `usePayments`, …) + Zustand (`stores/auth.ts`, `stores/workbench.ts`). Types: `src/types/spine.ts` re-exports the generated backend contract.

---

## 5. End-to-end flows (as implemented)

### 5.1 Lead → trip

1. Lead arrives via `POST /api/v1/inbound/parse`, `POST /api/v1/inbox/parse_social` (also `intake/fast` UI), draft creation, or anonymous `POST /api/public-checker/run`.
2. Operator (or API client) calls `POST /run` with `draft_id` → run executes on a daemon thread; draft `open → processing`.
3. Client polls `GET /runs/{run_id}` (2s) or subscribes via SSE. Outcome branches:
   - `ASK_FOLLOWUP` → follow-up questions surfaced; the traveler's reply re-enters the spine as a new envelope (re-entry loop, §6).
   - `ESCALATE` → incomplete lead persisted, never clobbering an existing trip; repair banner in the UI deep-links to fix fields.
   - success → trip materialized (tenant-scoped, status-guarded, id-preserving on re-runs); draft finalized via `POST /api/drafts/{id}/promote`.

### 5.2 Trip reassessment

`POST /trips/{trip_id}/reassess` re-queues the pipeline on an existing trip merging the extracted snapshot with edited fields; auto-reassess-on-edit is gated by `REASSESS_EDIT_TRIGGER_FIELDS`; `feedback_reopen` trips enter a recovery mode with a "Mark Resolved" operator action.

### 5.3 Proposal → booking → money

Proposal compiler produces options → traveler sees `p/[token]` (view, option recalculation, e-sign acceptance; trust scorecard explains the pick) → `price_lock` audits/re-locks supplier rates in the 72h window → `collection-link` issues a single-use token for the traveler to submit booking data + documents (reviewed via pending-booking-data accept/reject) → `booking_tasks` generation/reconciliation → `confirmations` record/verify/void → payment tracking feeds `GET /payments` buckets → settlement/VCC/tax/commission close the money side.

### 5.4 In-trip & post-trip

Ghost concierge + disruption radar + IROPS healer monitor and replan (counterfactual); crisis ops and duty-of-care radar handle emergencies (beacons, STEP manifests, evacuation); passenger-rights/insurance/loyalty/feedback close the loop; perishable sentinel watches deadlines throughout; memory write-path records facts for future trips.

### 5.5 Improvement flywheels

Operator overrides → override learning + KDD clustering; `ExecutionEvent`s → agentic feedback records → closed-loop fix candidates (shadow-tested) → autoresearch loop (scored, accept/revert, lineage logged); eval fixtures → D6 gate snapshot → CI guard.

---

## 6. Consolidated loops & cadences

| Loop | Where | Cadence / mechanism |
|---|---|---|
| Run-status polling | frontend `useSpineRun` | every 2s, terminal at completed/failed/blocked, cap 180s |
| SSE with fallback | frontend `useSSEStream` → BFF `api/stream-events/[runId]` | SSE when enabled; reconnect ≤3 (exp backoff) then poll 500ms×4 → 2s |
| Stale-run sweep | `RunLedger.timeout_stale_runs` via `GET /runs/{run_id}` | runs stuck >300s marked failed; driven by pollers |
| Requeue worker | `services/agent_requeue_jobs.py` | thread, every 5s, ≤5 jobs/pass, `SKIP LOCKED`, poison at max attempts |
| Recovery agent | `src/agents/recovery_agent.py` | every 300s; detects stuck trips, enqueues requeue jobs |
| Agent supervisor | `src/agents/runtime.py:373` | every 300s; ticks the product-agent registry |
| Zombie reaper | `server.py:1806` | thread, every 5s, `waitpid(-1, WNOHANG)` |
| Integrity watchdog | `spine_api/watchdog.py` | every 600s; dashboard-sum drift → operator notification |
| SSE: trip state | `routers/inbound.py` `stream-events/{trip_id}` | asyncio.Queue fan-out, 15s heartbeat |
| SSE: audit timeline | `routers/trip_observability.py` | 1s internal AuditStore poll, cap ~10 min then client reconnects |
| Webhook replay | `services/messaging_webhooks.py` | provider retries deduped per `message_id`; completed results replayed |
| Follow-up re-entry | NB01 `DEGRADE` / `ASK_FOLLOWUP` | traveler reply → new envelope → spine re-run |
| Reassess | `POST /trips/{id}/reassess` + edit-trigger fields | policy-gated re-run preserving trip id/status |
| Bargaining | `src/negotiation/bargaining_engine.py` | ACCEPT/ COUNTER rounds → escalate to human at max |
| Override learning | `src/decision/override_learning.py` | applied every decision run; patterns mined cross-trip |
| Eval flywheel | `src/evals/agentic_feedback.py` → `closed_loop_learning.py` → `autoresearch_loop.py` | event scan → fix candidates → scored accept/revert |
| Draft autosave | workbench `PageClient` | 5s debounce; 409 conflict handling |
| Auth refresh | `src/lib/api-client.ts` | one deduped refresh on 401, then single retry |

---

## 7. Verification surface

- **Tests**: `tests/` — 284 top-level test files + `tests/evals/` (11 eval-gate tests incl. the 30-scenario corpus gate and D6 scaffold). **Canonical runner**: `scripts/run_backend_tests.sh` (CI-identical env, excludes two API-key-dependent files, warns if the dev server occupies :8000 — live-server contention manufactures phantom failures). Last citable CI-identical baseline: **3,206 passed / 10 skipped** (2026-08-30, `Docs/review/A13_TEST_BASELINE_RESOLUTION_2026-08-30.md`).
- **Snapshots**: `tests/fixtures/server_openapi_paths_snapshot.json` + `server_route_snapshot.json`, regenerated via `scripts/snapshot_server_routes.py` (route/OpenAPI parity tests).
- **CI** (`.github/workflows/ci.yml`): docs-quality (markdownlint + lychee), backend-lint (ruff, scoped mypy, F401 / unscoped-trip-access / findings-register gates), backend-tests (postgres service, alembic upgrade, full pytest, D6 gate snapshot guard), frontend-quality (tsc, ESLint, Vitest).
- **Tools** (documented in `tools/README.md`): `runtime_smoke_matrix.py` (authenticated smoke gate), `dev_server_manager.py`, `architecture_route_inventory.py` (backend↔BFF drift), `performance_benchmark_matrix.py`, `e2e_scenario_runner.py`, `eval_runner.py`, `recovery_guard_report.py`, D6 snapshot scripts, and others.
- **Compose/dev**: `docker-compose.yml` (spine_api + one-shot migrations + postgres + redis + frontend; fail-closed `${VAR:?}` env), `dev.sh` (alembic + public-checker agency bootstrap preflight on `:8000`/`:3000`).

## 8. Honesty boundaries — read before trusting any surface

Two audits establish what is live vs simulated; both predate this map and remain the authority on truth-in-advertising for the product:

- [Agentic deep audit synthesis](../exploration/AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md): the serving path through `run_spine_once` is **100% deterministic** (zero LLM calls); the hybrid LLM decision engine exists but is orphaned behind `USE_HYBRID_DECISION_ENGINE=1` (default off); Frontier and Persona Council surfaces are simulated; sim-vs-reality scorecard: 7 of 30 claimed capabilities fully verified.
- [Launch readiness audit PER-0100](../review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md): verdict NO-GO public / CONDITIONAL-GO invite-only pilot; implementation plan at `Docs/review/LAUNCH_IMPLEMENTATION_PLAN_2026-09-02.md`.

Practical implications for anyone extending this codebase:

1. Don't assume an LLM is in the request path — the intake spine is rules/regex; LLM touches are feature-gated or in dedicated engines (`src/extraction/`, hybrid engine, RAG, judge).
2. Persona Council / Frontier panels are demo simulations, not live inference.
3. The dual trip-store is pinned to SQL (`TRIPSTORE_BACKEND=sql`); never run the server without it or trips will silently vanish from the UI.
4. `gap_decision` eval lane is shadow at honest accuracy 0.57 (bar 0.95) — see `src/evals/audit/manifest.yaml` before claiming decision-quality wins.

## 9. Pointers

- Canonical routing: `Docs/README.md` (knowledge-type → directory), `Docs/INDEX.md` (chronological working-doc index).
- Product/thesis: `Docs/MASTER_PRODUCT_SPEC.md`; trip state rules: `Docs/TRIP_STATE_CONTRACT.md`; lead persistence: `Docs/ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md`; server decomposition plan (R-10): `Docs/architecture/SERVER_DECOMPOSITION_PLAN_2026-08-29.md`; tenancy models: `Docs/architecture/TENANCY_ISOLATION_MODELS_LEARNING_2026-08-31.md`; runtime contracts: `specs/`.
- Recent hardening waves: `Docs/review/SECURITY_HONESTY_WAVE_HANDOFF_2026-09-02.md`, `Docs/architecture/SELF_CONTAINED_INTERNAL_ENGINES_HARDENING_2026-09-02.md`, `Docs/architecture/ADVANCED_INTERNAL_SYSTEMS_AND_COMPILERS_2026-09-03.md`.

## 10. Addendum 2026-09-12 — workbench modularization (structure-only)

`frontend/src/app/(agency)/workbench/PageClient.tsx` was decomposed via pure
moves (no feature/flow changes): URL/stage/tab validators and pure helpers →
`workbench-state.ts`; trip→store hydration → `hooks/useHydrateStoreFromTrip`;
run-state merge + draft-status + terminal-tab auto-switch →
`hooks/useWorkbenchRunSync`; draft create/patch/autosave lifecycle →
`hooks/useWorkbenchDraftPersistence` (payload construction consolidated per
FND-0277); transient toast timers → `hooks/useTransientTimers` (FND-0282).
PageClient remains the composition root (1,463 → ~915 lines). Behavior
contracts pinned by `workbench/__tests__/page-characterization.test.tsx`.
Evidence: `Docs/architecture/WORKBENCH_MODULARIZATION_COUNCIL_DECISION_2026-09-12.md`.
