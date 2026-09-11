# Feature List V3 — Runtime Truth Inventory

Date: 2026-09-10
Status: Active working inventory (supersedes FEATURE_LIST_V2_2026-05-12 as the current view; V2 is preserved unchanged as history)
Purpose: Canonical per-domain feature inventory with honest wiring status, priority, and code evidence.
Derived artifacts: `Docs/status/FEATURE_LIST_V3_2026-09-10.json`, `Docs/status/FEATURE_LIST_V3_2026-09-10.csv` (generated from this file by `tools/feature_list_generate.py` — edit this MD, then regenerate; never hand-edit the derived files).
Companion map: [CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03](../architecture/CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md) — flows/loops context for everything listed here (see also its [drift addendum](../architecture/CODEBASE_FEATURES_FLOWS_LOOPS_MAP_DRIFT_2026-09-06.md)).

## Method

1. Four parallel read-only Explore sweeps on 2026-09-03 (agent core `src/`, backend `spine_api/`, frontend `frontend/`, docs/tests/tools), synthesized into the companion map; feature rows re-verified against the tree on 2026-09-10.
2. Wiring-status spot verification (not assumed): hybrid engine default `decision.py:40`, distribution + IROPS `PREVIEW_ONLY` markers, in-memory commission ledgers, sourcing-hierarchy stub, tier-gated frontier flag, simulated-surface labels from the 2026-08-31 agentic deep audit and PER-0100 launch audit.
3. V2 (2026-05-12, 60 features) reviewed for continuity; every V2 LIVE feature re-evidenced or superseded below.
4. **Wiring-evidence rule (2026-09-11, FND-0261):** a `LIVE` row requires a serving-path caller — a mounted router endpoint consumed by the frontend/runtime, or a scheduled runtime caller — not merely module existence. The 2026-09-11 Elena-council audit found rows labeled LIVE on module existence alone; those rows are corrected below (C02, D09, E08, E14, F01, F02, G01, G02, I08) and orphaned implementations are marked `PARTIAL` with the missing caller stated.

## Status Legend

- `LIVE` — implemented and reachable in the current runtime/API/UI with no special gate.
- `PARTIAL` — implemented in slices; known limitation stated in the row.
- `GATED` — implemented but disabled by default (env flag, tier gate, or API key).
- `SIMULATED` — demo/in-memory surface, not live inference (labeled per the honesty wave).
- `STUB` — interface exists, resolver/body intentionally not implemented yet.

Counts (authoritative, generated): 117 features — 94 LIVE, 14 PARTIAL, 6 GATED, 2 SIMULATED, 1 STUB. (Corrected 2026-09-11 per FND-0261: 9 rows moved out of LIVE after serving-path-caller verification.)

---

## A) Platform, Identity & Tenancy

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| A01 | Auth lifecycle (signup, login, logout, refresh, me) | LIVE | P0 | httpOnly-cookie JWT sessions for agencies and staff | `spine_api/routers/auth.py`, `frontend/src/app/(auth)/` |
| A02 | Password reset + workspace-code join/validate | LIVE | P1 | Account recovery and invite-based team onboarding | `spine_api/routers/auth.py`, `spine_api/routers/workspace.py` |
| A03 | Multi-tenant RLS isolation + FORCE posture validation | LIVE | P0 | Per-agency row isolation, fail-closed startup checks on all tenant tables | `spine_api/core/rls.py`, `spine_api/server.py:1175`, `scripts/check_rls_coverage.py` |
| A04 | Workspace/member/role management | LIVE | P1 | Roster, invites, roles, capacity, specializations | `spine_api/routers/team.py`, `spine_api/models/tenant.py` |
| A05 | Agency settings (30 endpoints) | LIVE | P0 | Operational, AI, autonomy, epistemic, comms, seasonal policy-as-data | `spine_api/routers/settings.py`, `frontend/src/app/(agency)/settings/` |
| A06 | Tier-gated feature matrix | LIVE | P1 | Plan tiers override manual feature toggles (e.g. frontier/negotiation locked on starter) | `src/intake/config/agency_settings.py` |
| A07 | Audit trail + tamper-evident hashing | LIVE | P1 | Append-only audit logs, per-trip agent events, SHA-256 chain (Rule 0.15) | `spine_api/routers/audit.py`, `Docs/ADR_RULE_015_DECOUPLING_AND_AUDIT_CHAIN_HASHING_2026-07-29.md` |
| A08 | Fail-closed startup assertions + rate limiting + body caps | LIVE | P0 | Boot-time env/secret/RLS validation; slowapi limits; ASGI body cap | `spine_api/core/startup_assertions.py`, `spine_api/server.py:1362` |
| A09 | OTel observability | LIVE | P1 | OTLP gRPC spans, pipeline instrumentation, env-tunable batching | `spine_api/server.py:93`, `Docs/OTEL_OBSERVABILITY_SETUP_2026-05-01.md` |
| A10 | Human-AI authority boundaries | LIVE | P1 | HMAC capability tokens, trust zones, dual-control signoffs | `spine_api/routers/boundaries.py`, `src/services/boundary_engine.py` |
| A11 | AI workforce governance registry | LIVE | P2 | Per-agent capability scoping, policy validation, execution limits | `src/governance/registry.py` |

## B) Lead Intake & Extraction

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| B01 | Async spine run execution | LIVE | P0 | POST /run returns queued immediately; daemon-thread pipeline, file ledger, first-class blocked state | `spine_api/server.py:1927`, `spine_api/run_ledger.py`, `spine_api/run_state.py` |
| B02 | Multi-channel lead ingestion | LIVE | P0 | Freeform, structured JSON, social DM, voice notes, images | `spine_api/routers/inbound.py`, `spine_api/routers/social_inbound.py`, `spine_api/routers/multimodal.py` |
| B03 | Destination extraction with GeoNames validation | LIVE | P0 | 590k-city validation, origin/destination context heuristics, city sets, past-mention filtering | `src/intake/extractors.py:758`, `src/intake/geography.py` |
| B04 | Colloquial party/budget/date extraction | LIVE | P0 | Hinglish and colloquial composition, lakh/crore budgets, stretch max, date flexibility windows | `src/intake/extractors.py:1090`, `src/intake/extractors.py:1516` |
| B05 | MRZ passport parsing | LIVE | P1 | ICAO 9303 TD3 parsing with checksum verification | `src/intake/mrz.py`, `src/intake/mrz_parser_engine.py` |
| B06 | Vision/document extraction model chain | GATED | P1 | Gemini/OpenAI fallback chain with retry; requires provider API key (excluded from CI runner) | `src/extraction/model_chain.py`, `scripts/run_backend_tests.sh` |
| B07 | Epistemic provenance + conflict arbiter | LIVE | P1 | Field-level provenance, multi-turn contradiction detection, implicit needs, negative exclusions | `src/intake/epistemic_engine.py`, `spine_api/routers/epistemic.py` |
| B08 | Validation tiers (INTAKE_MINIMUM / QUOTE_READY) | LIVE | P0 | Stage-tiered minimum viable booking data; missing minimum escalates but persists the lead | `src/intake/validation.py` |
| B09 | NB01 intake-completion gate | LIVE | P0 | ESCALATE early-exit, DEGRADE partial save with generated follow-up questions | `src/intake/gates.py:101` |
| B10 | Incomplete-lead persistence + never-clobber reprocess | LIVE | P0 | ESCALATE runs persist incomplete leads and never overwrite promoted trips on reprocess | `Docs/ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md`, `spine_api/services/pipeline_execution_service.py` |
| B11 | Draft lifecycle | LIVE | P0 | open/processing/blocked/failed/promoted/merged/discarded, autosave with conflict detection, promote to trip | `spine_api/draft_store.py`, `spine_api/routers/drafts.py` |
| B12 | Optimistic sync + repair deep-link | LIVE | P1 | Optimistic trip state push; repair banner deep-links to field-level intake fixes | `spine_api/routers/inbound.py`, `frontend/src/lib/repair-deep-link.ts` |
| B13 | Public itinerary checker | LIVE | P1 | Anonymous checker with rate limiting, live Open-Meteo enrichment, retention sweep | `spine_api/routers/public_checker.py`, `src/public_checker/live_checks.py` |
| B14 | Voice copilot transcript extraction | LIVE | P2 | Consultation transcripts to structured intake packets | `spine_api/services/voice_copilot.py` |

## C) Decision Engine & Suitability

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| C01 | Gap-and-decision engine (10 phases) | LIVE | P0 | Ambiguity, budget feasibility/decomposition, contradictions, urgency, MVB blockers, question generation | `src/intake/decision.py:1942` |
| C02 | NB02 / D1 autonomy gate | PARTIAL | P0 | Per-agency autonomy policy with hard STOP safety invariant. Shipped: per-decision-state `auto/review/block` gates. NOT shipped: ADR-008 `money_execution_mode` rungs (fully_human/hybrid/fully_autonomous) — ratified 2026-09-09, unimplemented (FND-0261) | `src/intake/config/agency_settings.py:55-115`, `src/intake/gates.py:156`; `Docs/architecture/adr/ADR-008-AGENCY_BOUNDARY_AND_AUTONOMY_RUNGS_2026-09-06.md` |
| C03 | Suitability matrix D4/D6 | LIVE | P0 | Activity catalog scoring, context penalties, confidence clamping, critical flags halt the spine | `src/suitability/scoring.py:128`, `src/suitability/integration.py` |
| C04 | Hybrid rules→cache→LLM decision engine | GATED | P1 | Credential-gated LLM upgrade path with circuit breaker; default off (`USE_HYBRID_DECISION_ENGINE=1` to enable) | `src/intake/decision.py:40`, `src/decision/hybrid_engine.py` |
| C05 | Operator overrides + safety invariants | LIVE | P0 | Suppress/downgrade/acknowledge risk flags; document/visa/leakage flags can never be suppressed | `src/decision/override_learning.py:54` |
| C06 | Override learning + pattern mining | LIVE | P1 | Cross-trip override patterns (min strength 2) applied on every decision run | `src/decision/override_learning.py:376`, `src/decision/pattern_matching.py` |
| C07 | KDD override clustering | LIVE | P2 | Feature extraction, clustering, persisted override clusters + jobs API | `src/analytics/kdd/`, `spine_api/routers/kdd.py` |
| C08 | Commercial lifecycle scoring | LIVE | P1 | Ghost/window-shopper/churn/repeat risk feeding commercial action choice incl. Ghost Concierge recovery | `src/intake/decision.py:1484`, `src/intake/lifecycle.py` |
| C09 | Group consensus + Pareto resolution | LIVE | P1 | Multi-traveler preference harmonization with outlier protection | `src/decision/group_consensus.py`, `src/decision/group_pareto_engine.py` |
| C10 | Counterfactual recovery | LIVE | P2 | Three-way replanning alternatives on disruption or rejection | `src/decision/counterfactual_recovery.py`, `spine_api/services/counterfactual_engine.py` |
| C11 | Journey dependency graph + ripple | LIVE | P2 | BFS dependency traversals, co-terminal transfer ripple propagation | `src/schemas/journey_graph.py`, `spine_api/routers/journey_graph.py` |

## D) Proposal, Content & Traveler Surfaces

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| D01 | Proposal compiler | LIVE | P0 | Epistemic parse, inventory costing, margin optimization, JDG feasibility, shareable proposal | `src/orchestration/proposal_compiler.py:64` |
| D02 | Session strategy + sanitized bundles | LIVE | P0 | Internal vs traveler-safe prompt bundles with forbidden-concept leakage scan | `src/intake/strategy.py:972`, `src/intake/safety.py` |
| D03 | Tiered readiness computation | LIVE | P1 | Proposal/booking readiness tiers; never auto-advances stage | `src/intake/readiness.py:276` |
| D04 | Public proposal portal | LIVE | P0 | Tokenized view, option recalculation, e-signature acceptance with audit | `spine_api/routers/public_proposals.py`, `frontend/src/app/p/[token]/page.tsx` |
| D05 | Trust scorecard | LIVE | P1 | "Why this option" explainability, internal + public proposal routes | `spine_api/routers/trust_scorecard.py` |
| D06 | Booking-data collection links | LIVE | P0 | Single-use SHA-256 hashed tokens; traveler submits data + documents; operator accept/reject | `spine_api/services/collection_service.py`, `spine_api/routers/public_collection.py` |
| D07 | Document upload validation + scanner | LIVE | P1 | Magic-byte validation, streaming size cap, scanner abstraction, extraction attempts | `spine_api/services/document_service.py`, `spine_api/routers/trip_documents.py` |
| D08 | Luxury itinerary PDF / e-voucher compiler | LIVE | P2 | Vector HTML/CSS document generation for itineraries and vouchers | `src/compilers/itinerary_export_engine.py`, `Docs/architecture/ADVANCED_INTERNAL_SYSTEMS_AND_COMPILERS_2026-09-03.md` |
| D09 | Pre-departure briefing cadence | PARTIAL | P2 | Automated D-7 / D-3 / D-1 traveler briefings. ORPHANED (FND-0261): module implemented but has no router, scheduler, or pipeline caller — nothing automates the cadence | `src/briefing/pre_departure_cadence.py` (zero non-test importers) |
| D10 | Persona Council panel | SIMULATED | P1 | Labeled demo council surface; not live inference | `frontend/src/app/(agency)/workbench/PersonaCouncilPanel.tsx`, `Docs/exploration/AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md` |
| D11 | Frontier dashboard panel | SIMULATED | P1 | Labeled demo frontier surface; orchestrator heuristics exist behind tier gates | `frontend/src/components/workspace/FrontierDashboard.tsx`, `src/intake/frontier_orchestrator.py:45` |
| D12 | Time-travel scrubber + invertible history | LIVE | P2 | Undo/redo snapshot stack over trip state with UI scrubber | `src/state/mutation_history_stack.py`, `frontend/src/app/(agency)/workbench/TimeTravelScrubber.tsx` |
| D13 | Traveler companion PWA | LIVE | P2 | Trip card, alerts, documents, emergency radio for travelers | `frontend/src/app/(traveler)/companion/` |
| D14 | Group share + deposit collection | LIVE | P1 | Tokenized passenger share pages, multi-payer split deposits | `frontend/src/app/g/[token]/page.tsx`, `spine_api/routers/group_booking.py` |

## E) Pricing, Money & Suppliers

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| E01 | Risk-adjusted fee engine | LIVE | P1 | Severity-scaled service fee multipliers | `src/fees/calculation.py` |
| E02 | Settlement engine | LIVE | P1 | FX slippage buffers, VCC issuance, staged deposit/balance schedules, sub-agent splits | `src/fees/settlement_engine.py` |
| E03 | Payment queue + tracking | LIVE | P0 | Bucketed payment queue (overdue/due-soon) and per-trip payment records | `spine_api/services/payment_queue_service.py`, `spine_api/server.py:2577` |
| E04 | Commission reconciliation + split settlement | PARTIAL | P1 | Supplier commission and IC split ledgers — in-memory store, not yet durable | `spine_api/services/commission_reconciliation.py`, `spine_api/routers/commission.py` |
| E05 | Sub-agent IC payout portal | PARTIAL | P2 | Advisor commission ledger + payout authorization — in-memory store | `spine_api/routers/subagent_payouts.py` |
| E06 | FX risk sentinel | LIVE | P2 | Dynamic FX exposure and hedging recommendations | `spine_api/routers/fx_sentinel.py` |
| E07 | India tax compliance (TCS 206C(1G) / GST) | LIVE | P1 | Statutory computation with sourcing cost ledger | `src/fees/tax_compliance.py`, `spine_api/routers/tax_compliance.py` |
| E08 | Accounting export bridge | PARTIAL | P2 | Tally XML / QuickBooks JSON invoice export. ORPHANED (FND-0261): module implemented but no endpoint exposes the export | `src/accounting/export_bridge.py` (zero non-test importers) |
| E09 | Negotiation suite (bargaining, fee-waiver, margin optimizer) | LIVE | P1 | Game-theoretic counter rounds, penalty-waiver requests, dynamic take-rate with 10 percent floor | `src/negotiation/bargaining_engine.py:90`, `src/negotiation/margin_optimizer.py` |
| E10 | Price-lock sentinel | LIVE | P1 | 72h quote-window rate-drop audits, optimistic-locked re-lock with per-trip idempotency keys | `spine_api/routers/price_lock.py:196` |
| E11 | Supplier contracts | LIVE | P1 | DMC / preferred-supplier / wholesale contract registry backing price-lock | `spine_api/routers/supplier.py` |
| E12 | Yield arbitrage | LIVE | P2 | Bedbank/GDS/CRS rate-parity scans, multi-property benchmark, re-ticketing | `src/yield_arbitrage/rate_parity_engine.py` |
| E13 | Sourcing hierarchy resolver | STUB | P2 | internal→preferred→network→open_market ladder defined; resolver intentionally not implemented (defaults to open_market) | `src/intake/sourcing_path.py` |
| E14 | Payment mandates ledger | GATED | P2 | Consent-digested payment mandate tracking. Default-off pending ADR-008 ratification (open P0 FND-0185 / AT-15) — not "live with no special gate" (FND-0261) | `src/financial/payment_mandates.py`; `Docs/review/FINDINGS_LIVE.md` FND-0185 |
| E15 | Charter aviation + empty-leg arbitrage | LIVE | P2 | Fleet selection, runway feasibility, FBO/eAPIS filings, empty-leg matching | `src/charter/aviation_engine.py`, `spine_api/routers/charter_aviation.py` |

## F) Distribution & GDS

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| F01 | Sabre sandbox adapter | PARTIAL | P2 | BFM pricing + PNR create/delete shapes via deterministic sandbox adapter. No credentials are ever read; endpoints return `provider_connected: false` with `computation_method: "deterministic sandbox adapter; no network call"` (FND-0261) | `src/distribution/sabre_sandbox_adapter.py`, `spine_api/routers/gds_sandbox.py:33-45` |
| F02 | Amadeus sandbox adapter | PARTIAL | P2 | Offer search + order flow shapes via deterministic sandbox adapter. No credentials are ever read; endpoints return `provider_connected: false` (FND-0261) | `src/distribution/amadeus_sandbox_adapter.py` |
| F03 | NDC 21.3 Offer/Order client | LIVE | P2 | IATA NDC 21.3 offer/order lifecycle | `src/distribution/ndc_client.py` |
| F04 | EDIFACT parser + ATPCO fare rules | LIVE | P2 | Cryptic-command PNR parsing, Cat 16/35 rules, ADM prevention | `src/distribution/edifact_parser.py`, `src/distribution/fare_rules_engine.py` |
| F05 | Distribution API surface | PARTIAL | P2 | GDS/NDC endpoints return PREVIEW_ONLY metadata; no live carrier connection | `spine_api/routers/distribution.py:85` |
| F06 | GDS sandbox workbench panel | LIVE | P2 | Dual-GDS query UI for operators | `frontend/src/app/(agency)/workbench/GDSSandboxPanel.tsx` |

## G) In-Trip, Crisis & Duty of Care

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| G01 | Ghost concierge | PARTIAL | P1 | Flight telemetry to connection-risk detection with proactive recovery actions. ORPHANED (FND-0261): zero serving-path callers — `/ghost/*` routes only insert/read a `GhostWorkflow` row and never invoke the engine | `spine_api/services/ghost_concierge.py` (zero non-test importers) |
| G02 | Disruption radar + rebooking copilot | PARTIAL | P2 | Flight disruption preview alerts + deterministic rebooking options. Router self-describes: "no live feed is connected", every response tagged `DETERMINISTIC_PREVIEW`; rebook refuses to mutate booking state (FND-0261 — G03's honesty applied here) | `spine_api/routers/disruption_radar.py:2,80` |
| G03 | IROPS auto-healer | PARTIAL | P1 | Deterministic recovery-plan preview only; strips operative actions until carrier connectivity lands | `spine_api/routers/irops_healer.py:2` |
| G04 | Crisis ops + evacuation engine | LIVE | P1 | Multi-modal evacuation routing bypassing compromised airspace | `spine_api/routers/crisis_ops.py`, `src/crisis/evacuation_engine.py` |
| G05 | Safety beacons + STEP manifests + ground dispatch | LIVE | P1 | I-am-safe check-ins, consular manifests, driver dispatch with SOS messaging | `src/crisis/safety_beacon.py`, `src/crisis/ground_dispatch.py` |
| G06 | Duty-of-care radar | LIVE | P1 | Crisis declaration, traveler beacons, escalation posture | `src/orchestration/duty_of_care_radar.py` |
| G07 | Passenger rights claims | LIVE | P2 | EU261 / US-DOT claim generation | `src/decision/passenger_rights.py`, `spine_api/routers/passenger_rights.py` |
| G08 | Insurance CFAR sentinel | LIVE | P2 | CFAR window and coverage deadline monitoring | `spine_api/routers/insurance.py` |
| G09 | Loyalty programs | LIVE | P2 | Traveler loyalty account tracking | `spine_api/routers/loyalty.py` |
| G10 | Post-trip feedback / NPS | LIVE | P2 | Post-trip feedback extraction and NPS capture | `spine_api/routers/feedback.py`, `src/intake/extractors.py` post_trip mode |
| G11 | Perishable deadline sentinel | LIVE | P1 | Visa deadlines, ticketing TTLs, CFAR windows, deposit milestones, penalty cutoffs | `src/monitoring/perishable_sentinel.py` |
| G12 | Corporate policy engine | LIVE | P1 | Seniority-tier class rules, per-diem caps, approval chains, duty-of-care grading | `src/corporate/policy_engine.py`, `spine_api/routers/corporate_policy.py` |
| G13 | Stress benchmark | LIVE | P2 | 500+ concurrent IROPS scenario simulation with P99 and VCC throughput | `src/benchmarking/stress_simulator.py`, `spine_api/routers/stress_benchmark.py` |

## H) Memory & CRM

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| H01 | 5-tier traveler memory graph | LIVE | P1 | Working/episodic/semantic/procedural/preference tiers with authority weights, decay, supersession | `src/memory/models.py`, `src/memory/store.py` |
| H02 | Customer memory API | LIVE | P1 | Agent memory and CRM graph endpoints | `spine_api/routers/customer_memory.py` |
| H03 | Repeat-traveler relationship graph | LIVE | P1 | Cross-trip companion/family entities with recall card UI | `src/memory/` semantic tier, `frontend/src/app/(agency)/workbench/RepeatTravelerRecallCard.tsx` |
| H04 | GDPR Article 17 erasure | LIVE | P1 | Cascading erasure with signed forget certificates | `src/memory/gdpr_engine.py` |
| H05 | PII guard + retention enforcer + jurisdiction policy | LIVE | P1 | Regex+SpaCy PII detection, retention SLAs, GDPR/DPDP/US rules | `src/security/privacy_guard.py`, `src/security/retention_enforcer.py` |
| H06 | Memory architect panel | LIVE | P2 | Operator view of memory graph state | `frontend/src/app/(agency)/workbench/MemoryArchitectPanel.tsx` |

## I) Agent Runtime & Ops Reliability

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| I01 | Supervised product-agent fleet | LIVE | P1 | FrontDoor triage, SalesActivation SLA follow-ups, FollowUp, QualityEscalation, DocumentReadiness, DestinationIntelligence, WeatherPivot | `src/agents/runtime.py` |
| I02 | Durable work leases + fencing tokens | LIVE | P1 | SQL-backed leases with monotonic fencing vs split-brain/double-booking | `spine_api/services/agent_work_coordinator.py`, `src/orchestration/agent_lease.py` |
| I03 | Requeue worker + recovery agent + supervisor | LIVE | P1 | 5s requeue loop with SKIP LOCKED leasing, 300s stuck-trip recovery, 300s agent ticks | `spine_api/services/agent_requeue_jobs.py`, `src/agents/recovery_agent.py` |
| I04 | DLQ inspector + step checkpoints | LIVE | P2 | Poison-job inspection with redaction, counterfactual patch and replay, checkpoint/resume | `src/agents/dlq_inspector.py`, `src/agents/checkpoints.py` |
| I05 | Zombie reaper + integrity watchdog | LIVE | P1 | Child-process reaping (5s) and dashboard-sum drift detection (600s) | `spine_api/server.py:1806`, `spine_api/watchdog.py` |
| I06 | Resilience engine | LIVE | P1 | Circuit breakers, degradation hierarchy, failure quarantine, compensation | `src/services/resilience_engine.py`, `spine_api/routers/resilience.py` |
| I07 | Invertible state mutation stack | LIVE | P2 | Undo/redo snapshots over trip state | `src/state/mutation_history_stack.py`, `spine_api/routers/trip_history.py` |
| I08 | Agent intelligence graph builder | PARTIAL | P2 | Living navigation graph over docs/code for agent orientation. Developer tooling only (FND-0261): no CI job, no runtime/API/UI surface — artifact generated on demand | `tools/build_agent_intelligence_graph.py`, `Docs/context/AGENT_INTELLIGENCE_GRAPH.md` |

## J) Evals & CI Quality Gates

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| J01 | D6 audit scaffold + gate snapshot | LIVE | P0 | Fixture runner, precision/recall metrics, gating categories block CI on failure | `src/evals/audit/`, `scripts/verify_d6_gate_snapshot.py` |
| J02 | 30-scenario NB02 decision corpus | LIVE | P0 | Scenarios graded live through run_gap_and_decision in CI | `src/evals/rules/scenarios.py`, `data/fixtures/test_scenarios.py` |
| J03 | Extraction / pipeline / activity eval lanes | LIVE | P1 | Per-field P/R/F1 and activity gates; budget + colloquial currently gating | `src/evals/rules/`, `src/evals/audit/manifest.yaml` |
| J04 | LLM-as-judge scoring | GATED | P2 | Per-agent weighted rubrics via LLM or heuristics; shadow status | `src/evals/judge/scorer.py` |
| J05 | Autoresearch + closed-loop learning | GATED | P2 | Mutate-score-accept prompt/config search and fix-candidate shadow testing; experimental | `src/evals/autoresearch_loop.py`, `src/agents/closed_loop_learning.py` |
| J06 | Findings store v2 + lifecycle CI gate | LIVE | P1 | Append-only findings JSONL, minted IDs, stale-finding validation | `scripts/findings.py`, `Docs/review/FINDINGS_STORE.jsonl` |
| J07 | Route/OpenAPI snapshot parity + journey smoke in CI | LIVE | P1 | Server route fixtures regenerated via snapshot script; journey smoke + findings gate in CI | `scripts/snapshot_server_routes.py`, `.github/workflows/ci.yml` |

## K) Operator & Public Web Surfaces

| ID | Feature | Status | Priority | What it does | Evidence |
|---|---|---|---|---|---|
| K01 | Workbench cockpit | LIVE | P0 | Intake/packet/safety/council/frontier tabs, run progress, pipeline flow, repair banner | `frontend/src/app/(agency)/workbench/PageClient.tsx` |
| K02 | Lead inbox | LIVE | P0 | Priority/SLA projection, filters, assign/snooze, bulk ops | `spine_api/routers/inbox.py`, `frontend/src/app/(agency)/inbox/` |
| K03 | Trip workspace stage tabs | LIVE | P0 | Intake/Details/Options/Quote Assessment/Output/Risk/Ops/Timeline with stage gating | `frontend/src/app/(agency)/trips/[tripId]/layout.tsx`, `frontend/src/lib/planning-status.ts` |
| K04 | Quotes / Bookings / Payments / Reviews surfaces | LIVE | P0 | Commercial review, fulfillment records, payment tracking, approval queue | `frontend/src/app/(agency)/quotes/`, `frontend/src/app/(agency)/bookings/`, `frontend/src/app/(agency)/payments/`, `frontend/src/app/(agency)/reviews/` |
| K05 | Insights + system dashboard | LIVE | P1 | Ops/performance/revenue analytics and system health views | `frontend/src/app/(agency)/insights/`, `spine_api/routers/analytics.py`, `spine_api/routers/system_dashboard.py` |
| K06 | Settings sections | LIVE | P0 | Agency profile, AI/autonomy, team, integrations, security, seasonal | `frontend/src/app/(agency)/settings/` |
| K07 | Auth surfaces | LIVE | P0 | Login, signup, join-by-code, password reset | `frontend/src/app/(auth)/` |
| K08 | Marketing landing v2–v5 + pricing | LIVE | P1 | Landing iterations with v5 current; pricing page | `frontend/src/app/v5/`, `frontend/src/app/pricing/` |
| K09 | Fast capture (intake/fast) | PARTIAL | P1 | Social/DM paste capture direct to backend; flagged fabricated-success in PER-0100 | `frontend/src/app/intake/fast/`, `Docs/review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md` |
| K10 | Corporate offsites landing | PARTIAL | P2 | Offsites funnel page; flagged fabricated-success in PER-0100 | `frontend/src/app/corporate/offsites/` |
| K11 | Scenario lab + dev scenarios | GATED | P2 | Scenario replay/testing UI behind NEXT_PUBLIC_ENABLE_SCENARIO_LAB | `frontend/src/app/(agency)/workbench/ScenarioLab.tsx` |
| K12 | Knowledge base / seasons / suppliers surfaces | LIVE | P2 | KB, seasonal campaigns, supplier roster management | `frontend/src/app/(agency)/knowledge-base/`, `frontend/src/app/(agency)/seasons/`, `frontend/src/app/(agency)/suppliers/` |

---

## Notes for V4

- Re-verify the six GATED rows when their gates flip (hybrid engine, vision chain, judge, autoresearch, scenario lab, payment mandates/FND-0185) — each is a one-line status change plus evidence path.
- Re-wire or retire the orphaned PARTIAL rows (D09 briefings, E08 accounting export, G01 ghost concierge) — each needs one serving-path caller to re-earn LIVE.
- E04/E05 need a durable ledger decision (they are money-path PARTIALs; C02's ADR-008 rungs are the other unimplemented money-path slice).
- F05/G03 unblock when real carrier connectivity lands; keep PREVIEW_ONLY until then.
