# Agentic Flow Deep Map — Waypoint OS

**Date**: 2026-08-31
**Persona lens**: PER-0700 Agentic Systems Architect (central question: *where is adaptive agent behavior justified, and what architecture makes that autonomy reliable?*)
**Scope**: READ-ONLY exploration. Every claim carries file:line evidence from the working tree on 2026-08-31.
**Context inputs**: `Docs/ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md`, `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md`, `Docs/exploration/RAG_PIPELINE_ARCHITECTURE_EXPLORATION_2026-07-25.md`, `OPERATING_DOCTRINE.md` (skim), `Docs/V02_GOVERNING_PRINCIPLES.md`.

---

## Headline verdict (read this first)

**The canonical discovery run (`POST /run`) is 100% deterministic today — zero LLM calls execute on the serving path.** Every stage is regex/rules/state-machine code; the "gates" are deterministic policy functions, not model judgments. The LLM infrastructure that exists (vision document extraction, a cache→rule→LLM hybrid decision engine, a Tier-3 LLM suitability scorer, LLM-backed eval judges) is real code but **only the vision-extraction path is wired to production**, and even that is human-review-gated. Meanwhile several UI surfaces ("Persona Council", "Frontier OS") present **simulated/heuristic subsystems behind agentic-looking dashboards** — the exact "success judged by plausible conversation" failure mode PER-0700 warns about. There is, however, a genuinely well-architected **deterministic product-agent runtime** (18 registered agents, SQL leases, idempotency keys, tool sandbox) that *does* run in production and already cites PER-0700 in its own docstrings.

---

## 1) Pipeline Map

### 1.1 Entry and execution model

| Step | Location | Behavior |
|---|---|---|
| `POST /run` | `spine_api/server.py:1789-1817` | Auth'd; creates `uuid4` run_id; `RunLedger.create(...)` (server.py:1796); spawns **daemon thread** `spine-{run_id[:8]}` (server.py:1806-1813) → returns `RunAcceptedResponse(run_id, state="queued")` immediately |
| Thread target | `spine_api/server.py:1713` → `spine_api/services/pipeline_execution_service.py:104` (`execute_spine_pipeline`) | Runs the whole pipeline + persistence; closes inherited lock FDs first (pipeline_execution_service.py:191) |
| Orchestration entry | `src/intake/orchestration.py:181` (`run_spine_once`) | Chains frozen modules; returns one `SpineResult` dataclass (orchestration.py:136-174) |
| OTel | `orchestration.py:36` tracer; spans per phase (253, 285, 292, 385, 412, 439, 462, 492, 525, 536, 561, 595, 289 in service) | Every phase is a span; execution_ms recorded in meta |

### 1.2 Stage table (the serving path, in order)

| # | Stage | File:line | Deterministic / LLM / Hybrid | Inputs → Outputs | Gate between |
|---|---|---|---|---|---|
| 0 | Envelope build | `spine_api/services/pipeline_execution_service.py:233` (`build_envelopes`) | Det | raw_note/owner_note/itinerary_text/structured_json → `SourceEnvelope[]` | consent gate: `retention_consent` → `build_consented_submission` (live_checker_service.py:8-13) |
| 1 | Extraction (NB01) | `orchestration.py:247-280`; engine `src/intake/extractors.py` (`ExtractionPipeline.extract`, 2,847 lines) | **Deterministic** — pure regex/normalization ("honest regex parsing… 30+ fact fields", extractors.py); geography via 590k-city set (`src/intake/geography.py`) | Envelopes → `CanonicalPacket` (facts, derived_signals, hypotheses, contradictions, ambiguities, unknowns) | Feature gate `enable_auto_intake` (orchestration.py:249); tier+settings double-gate `_gate()` at orchestration.py:240-245 |
| 2 | Validation | `orchestration.py:282-289`; `src/intake/validation.py` (`validate_packet`, 294 lines) | Det | Packet → `PacketValidationReport` (`is_valid`, errors, warnings incl. `QUOTE_READY_INCOMPLETE`; `QUOTE_READY` vs `INTAKE_MINIMUM` field sets) | **Gate NB01** (below) |
| 3 | **NB01 Intake Completion Gate** | `src/intake/gates.py:101-153`; consumed `orchestration.py:292-368` | Det | (packet, validation) → `GateResult(verdict, score, reasons)` | Verdicts: **ESCALATE** if `validation.is_valid` is false (score 0.0) → early exit, `STOP_NEEDS_REVIEW`, `early_exit=True` (orchestration.py:297-329). **DEGRADE** if any `QUOTE_READY_INCOMPLETE` warning (score 0.5) → early exit, `ASK_FOLLOWUP`, `partial_intake=True` with follow-up questions generated for missing `origin_city / budget_raw_text / trip_purpose / party_size` (orchestration.py:330-368). **PROCEED** otherwise (score = min(1.0, len(facts)/10) — a "simple heuristic", gates.py:147-153). |
| 4 | Decision (NB02 judgment) | `orchestration.py:382-409`; engine `src/intake/decision.py:1942` (`run_gap_and_decision`, 2,252 lines) | **Deterministic** — 9 documented phases: ambiguity classification, MVB hard/soft blockers, operating-mode routing, budget feasibility vs `BUDGET_FEASIBILITY_TABLE` (imported from `src.decision.rules`, decision.py:516), urgency suppression, contradiction classification, confidence formula (`confidence = avg(fact_weight) + 0.2·avg(hyp_weight) − unknown_penalty`, docstring decision.py:1958-1966), decision-state machine, follow-up/risk generation | Packet (+feasibility table, agency settings) → `DecisionResult` (`decision_state` ∈ {ASK_FOLLOWUP, PROCEED_INTERNAL_DRAFT, PROCEED_TRAVELER_SAFE, BRANCH_OPTIONS, STOP_NEEDS_REVIEW}, blockers, contradictions, rationale, confidence) | — |
| 4.5 | Suitability | `orchestration.py:411-436`; `src/suitability/integration.py:281` (`assess_activity_suitability`) | **Det in serving path** — Tier 1 static catalog scoring (`catalog.py`) + Tier 2 itinerary coherence (integration.py:235-280). Tier 3 `LLMContextualScorer` (`src/suitability/llm_scorer.py:69`) exists but is **not called** in the pipeline (only `src/suitability/__init__.py:43` export + `tests/test_suitability_tier3.py`) | Packet → `suitability_flags`; **CRITICAL flags force `STOP_NEEDS_REVIEW`** + hard blocker `suitability_critical_flags_present` (orchestration.py:418-436) | — |
| 5 | **NB02 Judgment/Autonomy Gate (D1)** | `src/intake/gates.py:156-253` (`NB02JudgmentGate`); consumed `orchestration.py:439-456` | Det (pure policy mapping) | (DecisionResult, AgencySettings.autonomy) → `AutonomyOutcome` (raw_verdict preserved; effective_action ∈ auto/review/block; approval_required; rule_source; overrides) | Rules: base `policy.effective_gate(raw_verdict, mode)` (gates.py:193); mode overrides (gates.py:196-206); **safety invariant: STOP_NEEDS_REVIEW always blocks** (gates.py:208-215); warning override: risk flags + `auto_proceed_with_warnings=False` → auto downgraded to review (gates.py:218-225). **Does not mutate** decision_state (D1 three-layer separation, gates.py:47-68). |
| 6 | Frontier pass | `orchestration.py:459-485`; `src/intake/frontier_orchestrator.py:45` (`run_frontier_orchestration`) | **Det (heuristic/simulated)** — sentiment = keyword heuristic ±0.05/stress-word, explicitly "advisory only" (frontier_orchestrator.py:58-63, 222-245); Ghost Concierge triggered on `ESCALATE_RECOVERY`/`emergency` but only **fabricates a workflow id string** (lines 83-86) — no executor exists on this path; checker-agent audit = deterministic second-pass heuristics (`src/intake/checker_agent.py:29-72`; docstring: "Simulates a 'Checker' agent… would call a different LLM", checker_agent.py:24-26); intelligence pool = in-memory dict (`federated_intelligence.py:53`); specialty niches = keyword match, RAG path unexercised (see §4); negotiation = simulated haggle log rows (`negotiation_engine.py:34-56`) | (packet, decision) → `FrontierOrchestrationResult` (ghost_triggered, sentiment_score, intelligence_hits, specialty_knowledge, negotiation_logs, requires_manual_audit) | Feature gates `enable_frontier_orchestration` (orchestration.py:460), `enable_checker_agent` (frontier_orchestrator.py:89, threshold default 0.9 line 27), `enable_auto_negotiation` (frontier_orchestrator.py:152) |
| 7 | Strategy (NB03) | `orchestration.py:487-522`; `src/intake/strategy.py` (`build_session_strategy`, 1,078 lines) | Det — template/guardrail construction; produces **prompt bundles as artifacts** (no model consumes them in-run) | DecisionResult → `SessionStrategy` (session_goal, priority_sequence, tonal_guardrails, suggested_opening, exit_criteria) | Feature gate `enable_auto_proposal` (orchestration.py:489); disabled → minimal empty strategy (orchestration.py:495-506) |
| 8 | Fees | `orchestration.py:525-526`; `src/fees/calculation.py` (`calculate_trip_fees`) | Det | (packet, decision) → fee dict | — |
| 9 | Plan candidate | `orchestration.py:528-531`; `src/intake/plan_candidate.py` (`build_plan_candidate`, 383 lines) | Det | (packet, decision, strategy, fees) → `PlanCandidate` | — |
| 10 | Output bundles | `orchestration.py:533-556`; strategy.py `build_internal_bundle` / `build_traveler_safe_bundle` | Det | → `PromptBundle` internal + traveler (traveler bundle never receives raw PlanCandidate — safety boundary, orchestration.py:540-546) | — |
| 11 | Sanitization + leakage | `orchestration.py:558-592`; `src/intake/safety.py` (`sanitize_for_traveler`, `check_no_leakage`); regex scan orchestration.py:796-860 | Det — compiled forbidden-term regexes (`_get_forbidden_patterns`, orchestration.py:831-838) | → `SanitizedPacketView`, leakage_result {leaks, is_safe} | `StrictLeakageViolation` → run BLOCKED (service line 571-598) |
| 12 | Readiness | `orchestration.py:594-606`; `src/intake/readiness.py` (`compute_readiness`) | Det | all prior artifacts → readiness scorecard attached to `validation.readiness` | — |
| 13 | Fixture compare (optional) | `orchestration.py:608-617, 867-1024` | Det | scenario fixture → assertion results | eval-only |

### 1.3 Persistence & terminalization (pipeline_execution_service.py)

| Path | File:line | Behavior |
|---|---|---|
| Stage checkpoints | pipeline_execution_service.py:238-287 (`_stage_checkpoint` → `run_ledger.save_step`) + `_checkpoint_result_steps` 140-156 | Every completed stage JSON is written to the ledger mid-run |
| Live-checker finalize | pipeline_execution_service.py:158-184; `spine_api/services/live_checker_service.py` | Deterministic live checks + D6 public-authority overlay (`public_authority.py`); adjusted packet/validation/decision saved as `*_live_adjusted` steps |
| **ESCALATE (early_exit)** | pipeline_execution_service.py:316-414 | Per ADR-2026-08-31-01: persists inquiry as Trip `status="incomplete"` via canonical `save_processed_trip` **unless a preserve target exists** (`target_trip_id` or draft-linked trip — `_resolve_draft_reprocess_target` lines 51-84; "NEVER overwritten", comment lines 329-333). `run_ledger.block()` + `run_blocked` event. Ledger-failure isolated (378-386: loud log, no crash). |
| **DEGRADE (partial_intake)** | pipeline_execution_service.py:416-465 | Saves incomplete trip, completes run |
| Defense-in-depth | pipeline_execution_service.py:467-488 | `validation.is_valid` re-checked post-pipeline → BLOCKED |
| Success | pipeline_execution_service.py:500-569 | `save_processed_trip` → TripStore; `run_ledger.update_meta(trip_id=…)` (535); feedback-reopen trigger (539-543, `src/analytics/review.trigger_feedback_recovery`); `run_ledger.complete()` |
| StrictLeakageViolation | pipeline_execution_service.py:571-598 | BLOCKED terminal (first-class, run_state.py:19-29) |
| Catch-all | pipeline_execution_service.py:600-629 | FAILED terminal; ledger + draft updated |

### 1.4 Complete gate inventory

The repo's gate surface (all deterministic; verdicts PROCEED / DEGRADE / ESCALATE where applicable):

| Gate | Location | Inputs | Verdicts & thresholds |
|---|---|---|---|
| NB01 Intake Completion | gates.py:101-153 | validation report + packet facts | ESCALATE (`is_valid=false`); DEGRADE (`QUOTE_READY_INCOMPLETE`, score 0.5); PROCEED (density heuristic `len(facts)/10`) |
| NB02 Judgment/Autonomy (D1) | gates.py:156-253 + `AgencySettings.autonomy` policy | decision_state, operating_mode, risk_flags | effective_action auto/review/block; STOP_NEEDS_REVIEW invariant always block; mode_overrides map; warning downgrade |
| Suitability critical-flag escalation | orchestration.py:418-436 | suitability_flags severity=="critical" | forces STOP_NEEDS_REVIEW + hard blocker |
| Strict leakage policy | src/intake/safety.py + orchestration.py:558-592 | traveler bundle + sanitized view text | BLOCKED terminal on violation |
| Checker-agent redundancy audit | checker_agent.py:29-72 via frontier_orchestrator.py:89-110 | overall confidence vs `checker_audit_threshold` (default 0.9, frontier_orchestrator.py:27); budget blindness; high-stakes purpose keywords; low-confidence-without-blocker (conf<0.8) | requires_manual_audit true/false (audit-only; does not re-route the run) |
| Proposal-dispatch autonomy gate (Wave-2 surface) | `spine_api/services/autonomy_gates.py:33-60` | package USD, non-refundable deposit, destination risk, unverified supplier count, advisor override | AUTONOMOUS / ADVISOR_REVIEW_REQUIRED / RESTRICTED; hard risk factor: **≥ $10,000 package** (autonomy_gates.py:58-62) |
| Tier/feature gates | `orchestration.py:240-245` (`tier_allows_feature` + `AiAgentSettings.is_enabled`) | agency tier + settings | enable_auto_intake, enable_frontier_orchestration, enable_auto_proposal, enable_auto_negotiation, enable_checker_agent |
| Run state machine | `spine_api/run_state.py:19-58` | — | queued→running→{completed, failed, blocked}; invalid transitions raise |
| Lead-routing state machine (human ops) | `spine_api/services/routing_service.py:1-25` | trip assignment | assign/claim/escalate/reassign/return_for_changes/unassign transitions — **human** routing, not model routing |

---

## 2) LLM & Fallback/Routing reality

### 2.1 Where the LLM actually is (and is not)

**Serving path (`POST /run`): fully deterministic. No LLM invocation executes.** The four LLM subsystems in the codebase:

1. **Vision document extraction — WIRED, human-gated.** `src/extraction/openai_vision_extractor.py`, `gemini_vision_extractor.py`, `vision_client.py` (OpenAI path requires `OPENAI_API_KEY` only when `EXTRACTION_PROVIDER=openai_vision`, vision_client.py:228). Selected by `spine_api/services/extraction_service.py:110-149`; **default provider is `noop`** (extraction_service.py:117: `os.environ.get("EXTRACTION_PROVIDER", "noop")`). Invoked only from the trip-documents upload/retry routes (`spine_api/routers/trip_documents.py:492,574`), with a `ModelChain` provider fallback chain and `MAX_PROVIDER_RETRIES` (model_chain.py via extraction_service.py:13), cost tracking (pricing.py), and human review states (`applied/rejected/pending_review`, extraction_service.py:271-274). This is the *one* place a model output enters trip state — and only after operator approval.
2. **Hybrid decision engine — BUILT, NOT WIRED.** `src/decision/hybrid_engine.py:126` (`HybridDecisionEngine.decide`, line 335): cache (₹0) → rule engine (₹0) → LLM fallback (Gemini primary `src/llm/gemini_client.py:4`, OpenAI fallback `openai_client.py:4`) with result caching "so successful LLM decisions become cached rules". **Zero production callers** — only `src/decision/rules/__init__.py`, `src/decision/__init__.py`, and `tests/test_hybrid_engine.py`. The serving-path decision engine (`src/intake/decision.py`) imports *only* `BUDGET_FEASIBILITY_TABLE` from `src.decision.rules` (decision.py:516) — the rule half without the LLM half.
3. **Suitability Tier-3 LLM scorer — BUILT, NOT WIRED.** `src/suitability/llm_scorer.py` (Tier 3 contextual scorer with cache + llm_client injection, lines 65-71); `src/suitability/integration.py` assesses with Tier 1+2 only (integration.py:235-280).
4. **Eval judge — offline only.** `src/evals/judge/scorer.py:16` uses `src.llm.base.BaseLLMClient` for golden-set scoring, not serving.

Supporting governance that is wired but currently guards nothing in production: per-agency LLM usage guards + alert service initialized at lifespan (`spine_api/server.py:1209-1242`; `src/llm/usage_guard.py`, `alert_service.py`) — budget caps and rate limits for calls that the serving path never makes.

**Explicit admission of simulation, in code:** checker_agent.py:24-26 ("Simulates a 'Checker' agent… In a production system, this would call a different LLM"); frontier_orchestrator.py:58-59 ("In a real system, this would call an LLM-based sentiment analyzer. Current heuristic is advisory only — do not use for production decisions").

### 2.2 `routing_health` / fallback metrics — what they actually measure

- Computed by `build_routing_metrics` in `src/evals/agentic_feedback.py:509-612`, reducing **`ExecutionEvent.event_metadata`** fields: `fallback_trigger_reason`, `fallback_result ∈ {succeeded_after_fallback, exhausted}`, `review_trigger_reason`, `review_outcome`, `escalation_outcome ∈ {false_escalation, missed_escalation, correct_escalation}` (lines 527-548).
- Thresholds: `fallback_trigger_rate` warn 0.3 / critical 0.5; `false_escalation_rate` warn 0.2 / critical 0.4 (agentic_feedback.py:778-781); gate-checked in `src/evals/audit/snapshot.py` and `src/evals/audit/public_authority.py`; snapshot shows `fallback_trigger_rate: 0.0, false_escalation_rate: null` (`data/evals/d6_audit_gate_snapshot.json:282-284`).
- `ExecutionEvent` is a **SQL store** (`spine_api/services/execution_event_service.py:16,161-208`) used for trip timelines.
- Important framing: this is an **evaluation-time reducer over eval/harness events**, not a runtime model-routing service. There is no runtime model router on the serving path to fall back *from*. `spine_api/services/routing_service.py` is unrelated — it is the human lead-assignment state machine (routing_service.py:1-25). So `fallback_trigger_rate`/`false_escalation_rate` today describe the *evaluation harness's* synthetic fallback behavior — the metrics are ahead of the runtime they anticipate.

---

## 3) State & Observability map

| System | Storage | Written by | Read by | Reconstructable? |
|---|---|---|---|---|
| **RunLedger** | `data/runs/{run_id}/meta.json` + `steps/{packet,validation,decision,strategy,safety,output,blocked_result}.json` (KNOWN_STEPS, run_ledger.py:49) | pipeline_execution_service.py checkpoints (per-stage, mid-run, lines 238-287, 140-156) | `/runs/{run_id}` + `/runs/{run_id}/steps/{step}` (`spine_api/routers/run_status.py:42,120`) | **Full artifact replay** of every stage for every run; but checkpointing is observability, not resumability (see F-A5) |
| **Run events** | `data/runs/{run_id}/events.jsonl` append-only (run_events.py:37-47); types: run_started / pipeline_stage_entered / pipeline_stage_completed / run_completed / run_failed / run_blocked (run_events.py:51-59) | run_events.py:85-127 | `/runs/{run_id}/events` JSON list (run_status.py:145-175) — note: **no backend SSE endpoint exists at `/runs/{run_id}/stream`** | Complete run lifecycle trace with timings |
| **Run state machine** | meta.json `state` | run_ledger.py:127-148 (`assert_can_transition`) | — | queued→running→completed/failed/blocked, terminal-only exit |
| **Stale-run reaping** | RunLedger.timeout_stale_runs (run_ledger.py:316-361, 300s) + `_zombie_reaper` (server.py:1201, 1255) | lifespan thread | — | Crashed runs become FAILED after 5 min; no mid-run resume |
| **AuditStore** | `data/audit/events.jsonl` capped (persistence.py:113, 2000-2012) | orchestration.py:84-128 (`_emit_audit_event` → `TripEventLogger.log_stage_transition`, src/analytics/logger.py) on every stage transition with pre/post packet-state snapshots (`_snapshot_packet_state`, orchestration.py:68-81) | Trip timeline `/api/trips/{id}/timeline` + SSE poll-loop `/api/trips/{id}/events/stream` (trip_observability.py:148-189) | Operator-visible "why did the system decide this" trail per trip |
| **DraftStore** | file-based drafts + index (draft_store.py:51-452) | drafts router; pipeline updates run_state + linkage (pipeline_execution_service.py:15-48) | draft repair UI; `_resolve_draft_reprocess_target` | Draft→run→trip lineage; 1:1 draft↔trip (ADR-2026-08-31-01) |
| **TripStore** | dual backend JSON file / PostgreSQL via `TRIPSTORE_BACKEND` (persistence.py; AGENTS.md dual-store warning) | `save_processed_trip` (3 call sites in pipeline_execution_service.py:346, 428, 504) | trips/inbox/dashboard | The system of record; carries packet/validation/decision/strategy/bundles/fees/frontier per trip |
| **ExecutionEvent (SQL)** | Postgres (execution_event_service.py:161-208) | agent/timeline services | trip timeline + agentic eval reducers (agentic_feedback.py) | Per-trip event history incl. review/escalation outcomes |
| **TripEventLogger** | audit store (unified timeline SSOT) | orchestration stage transitions | trip timeline | Stage + reason + decision_type + pre/post state |

**SSE reality (run-level):** the BFF proxy `frontend/src/app/api/stream-events/[runId]/route.ts` (docstring lines 1-27) forwards to `GET {SPINE_API}/runs/{runId}/stream` — **an endpoint that does not exist**; the proxy 404s and the client "degrades to polling". `useSSEStream` (frontend/src/hooks/useSSEStream.ts:9-26) is adaptive-polling by default (`NEXT_PUBLIC_SSE_ENABLED` defaults false; poll 500ms ×4 then 2s, hook lines 79-83, 140). The trip-level SSE endpoint (trip_observability.py:148-189) is real but is itself a 1-second **polling loop over AuditStore** wearing an SSE costume (event_generator lines 158-182), capped at 10 minutes, and its consumer hook `useTripStream` (frontend/src/hooks/useTripStream.ts:38) currently has **no consumers** in the frontend tree.

---

## 4) Memory systems reality

| Layer | Exists | Wired into pipeline? | Wired elsewhere? |
|---|---|---|---|
| **5-Tier agent memory** (`src/memory/`: store, models, eligibility_gate, decay_engine, gdpr_engine, provenance, sanitizer, supersession — working/episodic/semantic/procedural/preference tiers) | Yes, comprehensive (per customer_memory.py:1-13: write eligibility gate, source-hierarchy scoring, provenance lineage, half-life decay, GDPR Art. 17 with crypto certificates, token-budgeted trip hydration) | **No.** `run_spine_once` never reads or writes it. | Yes — REST only: `spine_api/routers/customer_memory.py:34` (`_MEMORY_STORE = MemoryStore()`), ingest + hydrate endpoints (customer_memory.py:240 note: structured facts ingested "into the 5-tier durable MemoryStore") |
| Frontend recall of that memory | — | — | `RepeatTravelerRecallCard.tsx:28` states explicitly: "Real recall wiring (GET /api/v1/customers/memory) is the later Option A" — today the card renders sample-profile data (DEMO-04 finding, `Docs/exploration/DEMO04_SAMPLE_PROFILE_PROVENANCE_2026-08-31.md`) |
| **RAG** (`src/rag/`: store, indexer, retriever, grounding, service; sqlite `data/rag_store.db`; hybrid dense/sparse/graph per `rag/service.py:57`, models.py:75) | Yes | **Partially**: `SpecialtyKnowledgeService.identify_niche` (src/intake/specialty_knowledge.py:55-95) accepts an optional `RAGService`, but the pipeline caller passes none (`frontier_orchestrator.py:135` calls `identify_niche(analysis_text)` with default args) → **always keyword fallback** against the hardcoded `KNOWLEDGE_BASE` (specialty_knowledge.py:14-52). RAG is fully wired via `spine_api/routers/rag.py:32-36` for admin/ingest endpoints. | RAG router; blueprint for the 5-pillar architecture in `Docs/exploration/RAG_PIPELINE_ARCHITECTURE_EXPLORATION_2026-07-25.md` (currently the pipeline matches only pillar-0 keyword stubs) |
| **Institutional memory** (`Docs/context/`, root `memory/` = project thesis/assessment docs) | Yes | No — human-process artifacts, not agent-addressable | Docs only |
| De-facto memory: TripStore | Yes | Yes — every run persists extracted facts onto trips; FrontDoorAgent re-reads them (src/agents/runtime.py:590-597) | Whole product |

---

## 5) Agentic Boundary Assessment (PER-0700 verdict)

### 5.1 What is agentic *today*

Applying the persona's simplicity ladder (deterministic → single model call → structured workflow → model+tools → agent → …):

- **The discovery pipeline is Level 0 — deterministic software with policy gates.** It is *architected like* a well-designed agent substrate (stages, gates, autonomy policy, confidence scoring, sanitization, audit trail) but contains no adaptive component. That is **correct**, not deficient: the NB02 autonomy gate already separates judgment from authority (D1, gates.py:47-68), the safety invariant is enforced in code, and business logic lives entirely in code — no prompt carries business logic, because no prompt is executed at all. This satisfies the persona's highest-priority failure-mode checks ("prompts carrying business logic": pass; "no deterministic contracts": pass).
- **One real agentic subsystem exists: the product-agent runtime** (`src/agents/runtime.py`, ~3,150 lines; registry of 18 agents, `build_default_registry` runtime.py:3150-3178: FrontDoor, SalesActivation, DocumentReadiness, DestinationIntelligence, WeatherPivot, ConstraintFeasibility, ProposalReadiness, BookingReadiness, FlightStatus, TicketPriceWatch, SafetyAlert, GDSSchemaBridge, PNRShadow, SupplierIntelligence, FollowUp, QualityEscalation, ClosedLoopLearning, Communicator, OperatorRefinement). It is deterministic-but-agentic in the *systems* sense: scan→WorkItem→execute with idempotency keys (`front_door_agent:{trip_id}:{marker}`, runtime.py:581), retry policies with poison states (`RetryPolicy(max_attempts=3, backoff=(0,1,5))`, runtime.py:561; WorkStatus.POISONED), SQL single-owner leases with TTL (`agent_work_leases`, agent_work_coordinator.py:20-60; `ExecutionLease` runtime.py:47-58, whose docstring **cites PER-0700 directly**), tool sandboxing with timeouts and tenant concurrency quotas (`src/agents/sandbox.py:10-33`, also citing PER-0700), and live tools with explicit provider contracts (open-meteo, travel.state.gov advisories, env-templated HTTP flight/price/safety providers — `src/agents/live_tools.py:158-159, 356, 412-441`). Supervisor + recovery agent + requeue worker start at lifespan (server.py:1199-1206). This is a textbook "agents over deterministic workflows" topology with bounded authority — the strongest part of the architecture.
- **Two *theatrical* agentic surfaces exist and should be flagged (not praised):** Frontier OS and Persona Council (see F-A1). Ghost workflows are id strings (frontier_orchestrator.py:85) with a CRUD record in `routers/frontier.py:70-95` and **no executor**; `ghost_concierge.evaluate_flight_telemetry` (spine_api/services/ghost_concierge.py:73) — the actually-sensible in-trip disruption engine — has **zero callers**. Negotiation logs are simulated rows (negotiation_engine.py:39-53). Persona Council fires real deterministic engines with hardcoded `trip_id='trip_council_demo'` (PersonaCouncilPanel.tsx:68-168) — demo theater detached from the operator's actual trip.

### 5.2 The justified-autonomy boundary — where adaptive behavior is justified next

Ranked by the persona's "first ask whether deterministic software suffices" test, using observed evidence:

1. **NB01 extraction (colloquial input → structured facts).** The strongest candidate. Evidence: DEMO-02/03 — "do japan", "me and 3 friends"→Party 1 (silent wrong data), "next spring"→no dates (`Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md` §1). Regex has hit its ceiling on exactly the input class the product promises to serve ("the mouth of this funnel is, by design, messy input", ADR-2026-08-31-01 §2.2). This is semantic interpretation of open-ended human text — the persona's canonical justification for a model. The correct shape already exists: the vision-extraction service's schema-validated, confidence-scored, provider-fallback, human-review pattern (`extraction_service.py`, `vision_client.py`) should be the template for a *text* extractor: LLM proposes field values → deterministic validation (`validate_packet`) + NB01 unchanged → confidence + authority recorded on slots. Level 1-2 (advisory/assisted), never auto-trusted.
2. **Suitability Tier-3 contextual scoring.** Already designed for it (llm_scorer.py with cache + verdict schema); wiring it behind the existing critical-flag escalation (orchestration.py:418-436) preserves the authority boundary — the LLM only adds flags; STOP remains deterministic.
3. **Ghost Concierge / in-trip disruption.** The domain (real-time flight telemetry, cascading connections) is genuinely time-pressured and open-ended — but the honest engine (ghost_concierge.py) is unwired, and the fake trigger (frontier_orchestrator.py:83-86) should either be connected to it or removed. Live tools already exist for exactly this (FlightStatusTool, live_tools.py:26).
4. **NOT justified yet:** LLM-based decision_state (NB02) — the 9-phase state machine is auditable, cheap, and its failure modes (wrong state) would silently misroute leads; the hybrid_engine's cache→rule→LLM graduation loop (hybrid_engine.py:4-9) is the right *eventual* pattern (LLM proposals become rules), matching V02 Governing Principle 1 ("Every repeated LLM judgment should be considered a candidate for graduation into a deterministic rule", Docs/V02_GOVERNING_PRINCIPLES.md:24-27). **Must stay deterministic forever:** gates (NB01/NB02), leakage policy, autonomy/approval policy, persistence decisions, pricing/fees — these are the authority layer; models may *inform* them, never *be* them.

### 5.3 Failure-semantics audit (persona checklist)

| Check | Verdict | Evidence |
|---|---|---|
| Termination semantics | Good | Runs are finite, terminal states enforced (run_state.py), stale-run reaping 300s (run_ledger.py:316) |
| Idempotency | Partial | Runs keyed by fresh uuid4 (server.py:1794) so HTTP duplicates are impossible (run_ledger.py:119-123 comment); draft-scoped reprocess is idempotent via preserve targets (pipeline_execution_service.py:51-84, 332-345); **but** plain `POST /run` with the same raw text and no draft_id creates a new trip every time — no content-level dedupe |
| Resumability | Weak | Steps checkpointed for observability, but a crashed run cannot resume mid-stage; it is reaped as FAILED and must be fully re-run (no stage-level replay-from-checkpoint exists anywhere) |
| Hidden side effects | Some | `/run` writes trips (3 branches), updates drafts, emits audit events, can trigger feedback recovery (pipeline_execution_service.py:539-543) — all visible in the ledger/audit trail, so *provenance* is fine, but a "read-only-looking" probe run mutates the trip store; negotiation engine mutates in-memory `active_haggles` (negotiation_engine.py:31-33) with no persistence or owner |
| Failure-class separation | Good | FAILED vs BLOCKED vs ESCALATE vs DEGRADE are distinct, documented states (run_state.py:19-29; gates verdicts; ADR-2026-08-31-01) |
| Verification over confidence | Good where wired | Suitability critical flags, checker audit, strict leakage, defense-in-depth post-validation (pipeline_execution_service.py:467-488) — all environment-checked, none self-reported |
| Eval flywheel | Present but measuring a ghost | D6 routing_health gate + agentic_feedback reducers exist with thresholds and snapshots (§2.2) — infrastructure ahead of any LLM runtime to evaluate |

---

## 6) Findings list

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| **F-A1** | **High** | **Agentic theater on operator-facing surfaces.** Frontier OS renders "ACTIVE" ghost workflows that are fabricated id strings with no executor; negotiation logs are simulated; sentiment is a keyword heuristic labeled advisory-in-code but presented as a live meter. Persona Council drives real engines with hardcoded `trip_council_demo` ids. Risk: success judged by plausible dashboard (persona failure mode), operator trust built on non-existent autonomy. | frontier_orchestrator.py:58-63, 83-86; negotiation_engine.py:39-53; checker_agent.py:24-26; PersonaCouncilPanel.tsx:68,72,118,140,168; FrontierDashboard.tsx:18-24 |
| **F-A2** | **High** | **Telemetry for a ghost system.** `fallback_trigger_rate` / `false_escalation_rate` thresholds, alerts, D6 snapshots and per-agency LLM usage guards are all live — but they measure eval-harness events, because no LLM call path exists in serving. Risk: green dashboards imply governed AI; actually there is no AI to govern. | agentic_feedback.py:509-612, 778-781; server.py:1209-1242; d6_audit_gate_snapshot.json:282-284 |
| **F-A3** | **Medium** | **Ghost Concierge split-brain:** a real deterministic disruption engine (`evaluate_flight_telemetry`) is dead code; the live pipeline trigger only mints ids. Wire the former to the latter or delete the trigger. | ghost_concierge.py:73 (0 callers — repo-wide grep); frontier_orchestrator.py:83-86; routers/frontier.py:70-95 (CRUD-only records) |
| **F-A4** | **Medium** | **Hybrid decision engine + Tier-3 suitability scorer are orphaned.** The cache→rule→LLM graduation architecture (the repo's own stated LLM doctrine) has no production caller; only its rule table is imported. Decide: wire behind NB02 as advisory, or formally park it. | hybrid_engine.py:4-9, 335; decision.py:516 (imports only `BUDGET_FEASIBILITY_TABLE`); llm_scorer.py (tests-only) |
| **F-A5** | **Medium** | **Runs are not resumable.** Daemon-thread execution with artifact checkpointing gives full post-mortems but no mid-stage resume; crash ⇒ 5-minute zombie window then FAILED ⇒ full re-run. Acceptable today (deterministic, seconds-fast), becomes a real gap the moment any slow LLM stage is added. | pipeline_execution_service.py:186+; run_ledger.py:316-361 |
| **F-A6** | **Medium** | **Content-level run idempotency absent.** Same inquiry text re-posted without draft_id yields duplicate trips; the ESCALATE duplicate-protection works only for draft/target-linked runs. | server.py:1794-1800; pipeline_execution_service.py:51-84, 332-345 |
| **F-A7** | **Low** | **`epistemic_engine.py` orphaned** (decay, conflict detection, JSON-LD proof graph) — a provenance design with zero callers; superseded in practice by slot-level authority fields in packet_models + audit snapshots. | src/intake/epistemic_engine.py (repo-wide grep: no external refs) |
| **F-A8** | **Low** | **Dead SSE plumbing:** backend has no `/runs/{runId}/stream`; BFF proxy 404s by design; `useTripStream` hook has no consumers while the trip SSE endpoint it targets is itself a poll-loop. | stream-events/[runId]/route.ts:24-27; useSSEStream.ts:9-26, 79-83; useTripStream.ts (no importers); trip_observability.py:158-182 |
| **F-A9** | **Low** | **RAG bypassed in pipeline:** specialty knowledge always takes keyword fallback because the frontier pass never passes a `rag_service`; RAG store is otherwise endpoint-wired only. | frontier_orchestrator.py:134-135; specialty_knowledge.py:55-95, 100-130 |
| **F-A10** | **Info** | **First justified LLM insertion point is NB01 colloquial extraction**, per DEMO-02/03 evidence — with the vision-extraction service (schema, confidence, provider fallback, human review) as the pattern to copy for text. | DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md §1 DEMO-02/03; extraction_service.py:255-280 |
| **F-A11** | **Info** | **Prompt bundles are product artifacts, not executed prompts** — business logic lives 100% in code (persona check passes); when LLM stages arrive, `PromptBundle` is the natural contract boundary to keep it that way. | orchestration.py:533-556; strategy.py |

---

## 7) Open questions

1. **Product intent for the theatrical surfaces:** is Frontier OS a deliberate demo/taster layer (like the simulated persona demo) or an intended production capability awaiting wiring? The answer determines whether F-A1/F-A3 need removal, wiring, or explicit "SIMULATED" badges (cf. IMP-03's sample-profile gating precedent).
2. **Should the hybrid decision engine be wired as advisory behind NB02 before any NB01 LLM extractor lands** (so LLM graduations to rules flow through one canonical loop), or does the repo want two separate LLM entry points (extraction-only first)?
3. **Is trip-level SSE (trip_observability.py:148) meant to be the live surface**, and if so, should `useTripStream` be consumed by the workbench/inbox, or should run-level SSE be implemented at `GET /runs/{run_id}/stream` to match the existing BFF contract?
4. **Content-level dedupe for unlinked runs:** should `POST /run` compute a submission hash and reuse `preserve_trip_id` semantics, or is duplication accepted because drafts are the intended reprocess vehicle?
5. **When LLM extraction arrives, what is the review posture?** Document vision extraction is human-approved (`pending_review`); should extracted colloquial *text* fields auto-populate (with confidence/authority recorded) or land as suggestions pending operator confirmation — i.e., autonomy Level 1 vs 2?
6. **Ghost concierge executor:** if in-trip disruption is the next agentic wave, does `evaluate_flight_telemetry` become an agent in `src/agents/runtime.py` (scan: flights-near-travel → WorkItems; execute: evaluate + interventions), reusing the lease/idempotency machinery?

---

*Exploration only — no code changed, no commits made. Companion docs: `Docs/ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md` (persistence decision implemented in the traced code), `Docs/exploration/RAG_PIPELINE_ARCHITECTURE_EXPLORATION_2026-07-25.md` (target architecture for §4), `Docs/V02_GOVERNING_PRINCIPLES.md` (deterministic-first doctrine the current pipeline exemplifies).*
