# C-02 — Wire-or-Archive Dossiers for Orphaned & Simulated Assets

**Date:** 2026-09-02 (audit against live working tree; supersedes stale portions of `AGENTIC_FLOW_DEEP_MAP_2026-08-31.md` §2.1/§6 F-A3/F-A4)
**Personas:** PER-0700 Agentic Systems Architect (central test: *first ask whether deterministic workflow is sufficient*) + PER-0882 Model-Routing Optimization Engineer
**Scope:** READ-ONLY. Every claim carries file:line evidence. No code changed, no commits.
**Companion:** `C03_ROUTER_DESIGN_2026-09-02.md`, `C04_SLM_BENCHMARK_PROTOCOL_2026-09-02.md`, `MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` (POST-WAVE REFRESH).

---

## 0. Headline: one dossier is already stale — in the *good* direction

The 2026-08-31 deep map recorded the hybrid decision engine as "BUILT, NOT WIRED" with **zero production callers** (deep map §2.1 item 2, F-A4). **That is no longer true.** The hybrid engine is now wired into the serving decision path, default-ON:

| Evidence | Location |
|---|---|
| Integration header + flag in the serving decision engine | `src/intake/decision.py:28-47` |
| Flag default `"1"` (ON) | `src/intake/decision.py:36`; `src/decision/hybrid_engine.py:829`; `.env.example:65` |
| Serving-path call chain | `decision.py:2166` (`run_gap_and_decision` → `generate_risk_flags`) → `decision.py:1192` → `_generate_risk_flags_with_hybrid_engine` (`decision.py:75-149`) → `engine.decide()` |
| LLM tier reachable when rules miss | `src/decision/hybrid_engine.py:419-477` (Step 3: `_call_llm`) |
| G-08 egress hardening landed around it | `hybrid_engine.py:24,721,731` (`add_prompt_delimiters`); `src/llm/gemini_client.py:151` and `src/llm/openai_client.py:152` (`prepare_egress_payload`) |
| Governed: usage guard, telemetry, health | `hybrid_engine.py:549-586` (per-agency `usage_guard.check_before_call`, feature `hybrid_engine`), `hybrid_engine.py:374-411` (telemetry per decision) |
| **CI deliberately measures the flag-OFF path** | `src/evals/audit/snapshot.py:706-716` forces `USE_HYBRID_DECISION_ENGINE=0` around the mirror-baseline decision lane |

The dossier below therefore **reclassifies** the hybrid engine from "wire-or-archive" to "already wired — needs governance and evaluation," and flags a **new split-brain finding** (§1.6): prod runs hybrid-ON, the CI decision lane runs hybrid-OFF, and the D6 snapshot never grades the hybrid path.

---

## 1. Dossier format

Each dossier: What it does · Code quality/size · Test coverage · Callers today · What wiring it would require · What would make it trustworthy · Value hypothesis · **Verdict + confidence**.

---

## 2. Dossiers

### 2.1 Hybrid decision engine (`src/decision/hybrid_engine.py`, 843 L + `src/decision/rules/` ~1,050 L)

| Dimension | Evidence |
|---|---|
| What it does | Per-decision-type engine: cache (₹0, disk JSON at `data/decision_cache/`, `cache_storage.py:16-40`) → rules (`rules/`: elderly, toddler, composition, visa, budget + explicit `not_applicable` negative rules, `not_applicable.py:9-13`) → LLM (Gemini default, `LLM_PROVIDER`) → static default, with LLM-result caching ("successful LLM decisions become cached rules", deep map; `hybrid_engine.py:426-432`) |
| Quality | Good separation (schema-validated decision types, `SCHEMAS`, metrics, telemetry, health). 26 tests in `tests/test_hybrid_engine.py`. Egress-delimited prompts (G-08 closed: `hybrid_engine.py:721,731`). Guard-fail-open on guard errors is noted (`hybrid_engine.py:585-586`) |
| Test coverage | `test_hybrid_engine.py` 26 tests; guard tests in `test_usage_guard.py`; eval mirror lane deliberately runs it OFF (`snapshot.py:706-716`) |
| Callers today | **Serving path, default-ON** (§0 table). Plus `tools/validation/hybrid_engine_validator.py` |
| Wiring required | None — it is wired. Required instead: **flag policy + parity + observability** (§1.6) |
| Trustworthiness needs | (1) Decide and record the flag's production posture; (2) make the CI decision lane grade the same config prod uses; (3) emit hybrid telemetry (`src/decision/telemetry.py`) fields into `ExecutionEvent` metadata so `routing_health` sees real tier/source/latency/cost; (4) an eval lane proving hybrid risk flags ≥ legacy risk flags on the scenario corpus before the flag stays default-ON |
| Value hypothesis | Advisors get contextual composition/visa/budget risk flags grounded in packet facts (elderly + Maldives class) instead of the hardcoded risky-destinations set at `decision.py:1207-1211`; LLM graduations to cached rules materialize the V02 doctrine ("every repeated LLM judgment is a candidate for graduation", `Docs/V02_GOVERNING_PRINCIPLES.md:24-27`) |
| **Verdict** | **KEEP WIRED — but ratify the flag and close the eval split-brain. Confidence: high (evidence is in-tree).** The PER-0700 test is satisfied *because* rules + negative rules cover the six decision types deterministically first; the LLM is the last resort, and each hit becomes a future rule. |

**§1.6 New finding (H-01, this dossier):** prod default-ON vs CI forced-OFF (`snapshot.py:706-716`) means every D6 snapshot, gate, and alert silently describes the non-hybrid system while production runs the hybrid one. Either set the flag explicitly in prod env (`.env` today has no `USE_HYBRID_DECISION_ENGINE` line) and mirror it in the lane, or default the flag OFF until the hybrid lane has eval evidence. Both are one-line changes; the decision is ratification-class (owner call).

---

### 2.2 Suitability Tier-3 LLM contextual scorer (`src/suitability/llm_scorer.py`, 334 L)

| Dimension | Evidence |
|---|---|
| What it does | Contextual (beyond static catalog) activity suitability scoring with verdict schema, cache, and injectable `llm_client` (`llm_scorer.py:65-71`); Tier-1 static catalog + Tier-2 itinerary coherence remain the serving tiers (`src/suitability/integration.py:235-280`); a Tier-3 *heuristic* pacing flag already exists in the integration (`integration.py:372-376`) |
| Quality | Clean; designed for injection/cache. 5 tests (`tests/test_suitability_tier3.py`) |
| Callers today | **Zero production callers** — `rg LLMContextualScorer` hits only `src/suitability/__init__.py` export + the test file |
| Wiring required | One call site in `integration.py` behind the existing critical-flag escalation, which already forces `STOP_NEEDS_REVIEW` on critical flags (`src/intake/orchestration.py:418-436`) — the LLM would only *add* flags; STOP stays deterministic |
| Trustworthiness needs | Golden fixtures where Tier-3 changes the verdict vs Tier-1/2 (none exist); flag-level P/R vs advisor review; usage-guard + egress integration (copy the hybrid engine's pattern); confidence/authority recorded on flags |
| Value hypothesis | Tier-1 catalog cannot see "73-year-old with recent surgery + 5-activity day in hill country" unless the catalog enumerates it — the long tail is exactly why Tier 3 was designed. Pain: silent under-flagging today; false comfort from Tier-1-only coverage |
| **Verdict** | **WIRE — conditionally, behind the existing escalation, after the C-04/eval core produces a Tier-3 flag-quality lane. Confidence: medium-high.** It is the repo's own deep-map recommendation (F-A10 rationale) and the authority boundary already exists. Do not wire before there is a lane that can fail it. |

---

### 2.3 Ghost concierge engine (`spine_api/services/ghost_concierge.py`, 144 L)

| Dimension | Evidence |
|---|---|
| What it does | `evaluate_flight_telemetry` (`ghost_concierge.py:57`): delay/cancellation classification, connection-cascade risk (MCT math), intervention drafting (`ALERT_AGENT`, `NOTIFY_HOTEL_LATE_CHECKIN`, `SEARCH_FALLBACK_FLIGHTS`, `DRAFT_EU261_CLAIM`, `ghost_concierge.py:47-51`). Pure, self-contained, deterministic |
| Quality | Clean dataclasses + pure function; **2 tests** (`tests/test_ghost_concierge.py`) |
| Callers today | **Zero production callers** — only the test and the scenario generator tool `tools/generate_frontier_scenarios.py`. Meanwhile the live frontier pass *mints fake ghost workflow ids* on `ESCALATE_RECOVERY`/`emergency` (`src/intake/frontier_orchestrator.py:83-86`) and the ghost CRUD router stores id-strings with no executor (deep map F-A3; `spine_api/routers/frontier.py:70-95`) |
| Wiring required | Make it a scanner/executor pair in the production agent runtime: scan (FlightStatusTool / live telemetry, `src/agents/live_tools.py:26` already has the flight-status tool contract) → WorkItems per disrupted trip → execute: `evaluate_flight_telemetry` + interventions. The runtime already provides leases, idempotency, retry/poison states (`runtime.py:581`, `agent_work_coordinator.py:20-60`) |
| Trustworthiness needs | Live flight data contract (env-templated providers exist, `live_tools.py:158-159,412-441`); intervention action classes gated (draft-only until advisor sends); false-positive rate tracked; the fake id-minting trigger at `frontier_orchestrator.py:83-86` deleted when the real path lands (C-01 already requires removing the theater) |
| Value hypothesis | In-trip disruption is the one genuinely time-pressured, open-ended domain where an autonomous monitor pays for itself (traveler stranded vs advisor asleep). The deep map ranked it #3 for justified autonomy (deep map §5.2.3) |
| **Verdict** | **WIRE LATER as an agent-runtime scanner; until then, archive the *trigger*, not the engine. Confidence: high on the disposition split.** Keep `evaluate_flight_telemetry` (it is honest, tested, doctrine-compatible); delete/rebrand the fabricated `ghost_{id}` minting now (that is C-01's cheap-honesty action, already labeled). |

---

### 2.4 The Gemini-wave modules — audit table with dispositions

Status legend: **LIVE** = has a non-router production consumer · **ROUTER-ONLY** = reachable via an API route whose panel is demo surface (C-01/G-01-amp) · **SHADOW** = zero non-test callers. Sizes from `wc -l` on 2026-09-02 tree.

| Module | Size | Test file (count) | Reality | Disposition | Confidence |
|---|---|---|---|---|---|
| `src/logistics/route_geometry.py` | 491 L | `test_route_geometry.py` | **LIVE** — `src/agents/live_tools.py:656` (`haversine_distance`), and via `pipeline_bridge` in the **CI 30-scenario gate** (`tests/evals/test_30_scenario_corpus_gate.py:8`) and journey smoke (`tests/test_journey_smoke_e2e.py`) | **KEEP — already load-bearing for eval + agent tooling.** | High |
| `src/logistics/pipeline_bridge.py` | 175 L | scenario gate + journey smoke | **LIVE in CI lanes** — `RouteAssessmentBridge` is the scenario lane's subject (`test_30_scenario_corpus_gate.py:8`) | **KEEP** — the eval ground truth depends on it | High |
| `src/logistics/{connection_risk,rooming_list,fleet_allocation,timed_entry,accessibility}.py` | 1,268 L | `test_logistics_operations_suite.py` (11) | ROUTER-ONLY (`spine_api/routers/logistics.py:18-32`); real deterministic logic, no live feeds | **PARK as libraries**; wire `connection_risk` into ghost concierge when §2.3 wires (MCT math overlaps) | Med-high |
| `src/intake/mrz_parser_engine.py` | 183 L | `test_document_mrz_extraction.py` (3), `test_passport_mrz.py` | ROUTER-ONLY (`document_extraction.py:14`); genuine ICAO 9303 7-3-1 mod-10 (`mrz_parser_engine.py:70,133`); nothing feeds it scans | **PARK as library** — wire when the vision-document intake path (§2.5) attaches OCR/MRZ text. Highest-quality orphan in the wave | High |
| `src/intake/epistemic_arbiter.py` | 163 L | `test_epistemic_provenance_arbiter.py` (4) | ROUTER-ONLY + proposal compiler (`src/orchestration/proposal_compiler.py`); **not in canonical intake** — and `Slot` already carries `epistemic_status`/`authority_level`/`evidence_refs` (`src/intake/packet_models.py:151-164`) | **ARCHIVE-or-MERGE**: field-by-field comparison shows the arbiter duplicates what the packet already records (supersession rule applies); merge any unique check into packet validation, then remove | Med |
| `src/decision/group_pareto_engine.py` | 161 L | `test_group_pareto_consensus.py` (2) | ROUTER-ONLY (`group_pareto.py:14`); real deterministic math | **PARK**; revisit with the group/coordinator operating mode (`packet_models.py:432-435` `coordinator_group`) if that mode ships | Med |
| `src/yield_arbitrage/*` (engine+models+benchmark) | 360 L | `test_yield_arbitrage_engine.py` (2), `test_yield_arbitrage_real.py`, `test_multi_property_yield_benchmark.py` | **SHADOW engine** ("Simulates real-time multi-channel rate comparison", `rate_parity_engine.py:30`); the `/api/v1/yield` router is self-contained (`spine_api/routers/yield_arbitrage.py:35`); panel↔backend contract mismatch already registered (N-04) | **ARCHIVE** (engine) unless a real bedbank/GDS feed is contracted; fix or delete the panel (N-04) | High |
| `src/telephony/ivr_bypass_bot.py` | 98 L | `test_ivr_bypass_bot.py` (3) | ROUTER-ONLY; self-labeled simulator, invented DTMF trees (`ivr_bypass_bot.py:26-44,61`) | **ARCHIVE** until a real telephony provider exists (the "Production Twilio Adapter" is itself a simulator, GM-02) | High |
| `src/charter/aviation_engine.py` | 357 L | `test_charter_aviation_engine.py` (4) | ROUTER-ONLY; sim, no fleet feed | **PARK** (premium-segment feature; needs a live operator feed to be more than a calculator) | Med |
| `src/fees/settlement_engine.py` | (part of fees/) | `test_financial_settlement_vcc.py` (4) | ROUTER-ONLY; FX/interchange math real, VCC issuance is uuid-seeded pseudo-issuance (`settlement_engine.py:101-133`) | **PARK**; wire only behind a real VCC provider (Stripe Issuing adapter is currently fake, GM-03 — that fake must die first) | High |
| `src/briefing/pre_departure_cadence.py` | 196 L | `test_industry_blindspots_expansion.py` (within 10) | **SHADOW** (zero callers outside tests) | **ARCHIVE-or-WIRE-to-Communicator-agent**: the runtime already has a Communicator agent (deep map §5.1, 18-agent registry); a cadence generator is a natural agent output. Decide with product | Med |
| `src/corporate/policy_engine.py` | 181 L | `test_industry_blindspots_expansion.py` | **SHADOW** | **ARCHIVE** until a corporate-travel segment exists | High |
| `src/documents/visa_workflow.py` | 213 L | `test_industry_blindspots_expansion.py` | **SHADOW** | **ARCHIVE** — visa *risk* already lives in decision rules (`src/decision/rules/visa_timeline.py`, 199 L); two visa subsystems is drift | High |
| `src/financial/payment_mandates.py` | 170 L | `test_extraction_and_mandates_suite.py` (7) | **SHADOW** | **ARCHIVE** (F-04 mandate ledger has no producer or consumer) | High |
| `src/monitoring/perishable_sentinel.py` | 143 L | `test_p1_findings_hardening.py` (6) | **SHADOW** | **ARCHIVE** (no inventory domain in the current product) | High |
| `src/security/retention_enforcer.py` | 147 L | `test_extraction_and_mandates_suite.py` | **SHADOW** — despite GDPR Art-17/DPDP erasure-SLA framing | **WIRE or PROMISE-ONLY**: compliance-shaped shadow code is the worst kind of orphan (implies a control that doesn't run). Either wire to the lifecycle/agent path or demote the docstrings | High |
| `src/agents/dlq_inspector.py` | 124 L | `test_p1_findings_hardening.py` | **SHADOW** — while the runtime genuinely has poison states (`WorkStatus.POISONED`) | **WIRE later** (small, natural ops fit for the runtime) or archive; never leave it implying a live DLQ process | Med |
| `src/accounting/export_bridge.py` | 156 L | `test_industry_blindspots_expansion.py` | **SHADOW** | **ARCHIVE** until an accounting integration is contracted | High |
| `src/intake/epistemic_engine.py` (pre-wave, F-A7) | — | `test_epistemic_engine_deep.py` | **SHADOW** (self + test only) | **ARCHIVE** — superseded in practice by `Slot` provenance fields (`packet_models.py:151-164`) + audit snapshots | High |
| `spine_api/providers/{amadeus_enterprise,stripe_issuing,twilio_telephony}_adapter.py` | — | `test_production_provider_adapters.py` | SHADOW; simulators named "Production…"; fake webhook HMAC (`stripe_issuing_adapter.py:84-90`) | **RENAME/move + delete fake security control** (GM-02/GM-03 — restated as C-02 action because they are the most dangerous orphans: they *impersonate* the directory where real clients will live) | High |

---

### 2.5 Vision document extraction — the reference pattern (not a dossier; the template)

Wired, human-gated, default-`noop`: `spine_api/services/extraction_service.py:117` (`EXTRACTION_PROVIDER` default `"noop"`), invoked only from trip-documents upload/retry routes (`spine_api/routers/trip_documents.py:492,527`), with schema validation, per-field confidence, cost tracking, provider fallback chain, and review states `applied/rejected/pending_review` (`extraction_service.py:63-65,271,527`). **Every wiring below should copy this shape** — model proposes, deterministic validation + human/authority decides, provenance recorded.

---

## 3. Decision framework applied (PER-0700)

1. **Is deterministic workflow sufficient?** For risk-flag composition (hybrid rules), visa risk, MRZ text parsing, route geometry, MCT math, Pareto consensus — yes, and those parts stay deterministic. LLM is justified only where interpretation of open-ended human text or genuinely open-world context is required (NB01 colloquial extraction first; suitability context second; disruption monitoring is deterministic-per-observation but time-critical).
2. **Authority never moves:** gates (NB01/NB02), leakage policy, autonomy policy, persistence stay deterministic forever; any wired scorer only adds flags/advisories (the critical-flag escalation pattern at `orchestration.py:418-436` is the template).
3. **Wire only what evaluation can judge** (synthesis §4.2): no wiring without a lane that can fail it — hence every "WIRE" verdict above carries a precondition, not a date.

## 4. Consolidated disposition register

| Asset | Verdict | Precondition / first action |
|---|---|---|
| Hybrid decision engine | KEEP WIRED | Ratify `USE_HYBRID_DECISION_ENGINE` prod posture; close CI↔prod split-brain (H-01); feed telemetry into routing_health |
| Suitability Tier-3 | WIRE (gated) | Tier-3 flag-quality lane from eval core; wire behind existing critical-flag escalation |
| Ghost concierge engine | WIRE LATER | As agent-runtime scanner; delete the fake trigger at `frontier_orchestrator.py:83-86` now |
| Logistics route_geometry + pipeline_bridge | KEEP (already live) | None — protect as eval-lane dependency |
| MRZ parser | PARK as library | Attach to vision-doc intake when OCR path exists |
| Epistemic arbiter / epistemic_engine | ARCHIVE-or-MERGE | Field-by-field supersession comparison vs `Slot` provenance first |
| Group Pareto | PARK | Revisit with `coordinator_group` mode |
| Yield arbitrage engine | ARCHIVE | Fix/delete YieldArbitragePanel (N-04) |
| IVR bypass, charter, settlement, payment mandates, perishable sentinel, corporate policy, visa_workflow, accounting export | ARCHIVE | Keep tests with archived code; archive note in each module docstring |
| Pre-departure cadence | ARCHIVE-or-WIRE to Communicator agent | Product decision |
| Retention enforcer | WIRE or demote copy | Compliance-shaped shadow is unsafe; either wire to lifecycle or annotate honestly |
| DLQ inspector | WIRE later or archive | Small ops fit for runtime poison states |
| "Production" provider adapters | RENAME + delete fake HMAC | GM-02/GM-03 hotfix class |

## 5. Open questions (ratification-class)

1. **H-01 (new):** should `USE_HYBRID_DECISION_ENGINE` be explicit OFF in prod until a hybrid-specific eval lane passes, or explicit ON with the CI lane switched to parity? (Recommend: explicit ON with parity lane, since the integration is guard- and egress-hardened — but this flips a default and is the owner's call.)
2. **Retention enforcer:** wire now (small) or annotate as not-operating? Leaving compliance copy on unwired code is the G-13-class record risk.
3. **Archives:** archive location preference (in-repo `Archive/` vs docstring `@deprecated` in place)? Doc deletion is prohibited by repo rules; archival with pointers is the default.
4. **Pre-departure cadence:** product call — Communicator-agent output or dead code?
5. Does any live integration expect `spine_api/providers/` to be the real-client home (so the simulators must move *before* the first real client lands)?
6. Confirm `tools/generate_frontier_scenarios.py` is a sanctioned consumer of ghost concierge (it is the only non-test caller); if the engine is later wired into the runtime, this tool should be retired or aligned.
