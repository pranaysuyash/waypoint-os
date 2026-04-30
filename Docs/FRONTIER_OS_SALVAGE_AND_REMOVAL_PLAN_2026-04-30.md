# Frontier OS — Salvage & Removal Plan

**Date:** 2026-04-30
**Status:** No implementation. Audit + classification only.
**Independent verification:** All 13 claims from prior audit confirmed with exact file:line evidence.

---

## 1. Independent Verification Summary

| # | Claim | Verdict | Key Evidence |
|---|-------|---------|-------------|
| 1 | FrontierDashboard embedded in workbench | ✅ CONFIRMED | `page.tsx:79` (tab), `:1073-1086` (rendering) |
| 2 | store.result_frontier exists | ✅ CONFIRMED | `workbench.ts:86,:100,:208` |
| 3 | setResultFrontier never called | ✅ CONFIRMED | 2 matches (declaration+impl), **zero call sites** in `frontend/src/` |
| 4 | Backend orchestration creates frontier_result | ✅ CONFIRMED | `orchestration.py:334-343` — calls `run_frontier_orchestration`, populates `decision.rationale["frontier"]` |
| 5 | API/run ledger doesn't expose frontier_result | ✅ CONFIRMED | `server.py:751-763` has no frontier save; `RunStatusResponse` lacks field |
| 6 | FrontierDashboard hardcoded defaults | ✅ CONFIRMED | `FrontierDashboard.tsx:22-28` — all props have defaults |
| 7 | "No active risks detected" fake confidence | ✅ CONFIRMED | `FrontierDashboard.tsx:70` — shown when `intelHits` empty (always) |
| 8 | SettingsPanel toggles not sent with API | ✅ CONFIRMED | `page.tsx:425-435` — no frontier fields; `contract.py:112` extra=forbid |
| 9 | RunStatusResponse lacks frontier_result | ✅ CONFIRMED | `contract.py:138-162`, `spine.ts:60-79` — zero frontier fields |
| 10 | Trip type lacks frontier_result | ✅ CONFIRMED | `api-client.ts:288-362` — zero frontier grep hits |
| 11 | Frontier DB models in __init__.py | ✅ CONFIRMED | `models/__init__.py:9` — all 4 models registered |
| 12 | strategy.py consumes frontier data | ✅ CONFIRMED | `strategy.py:434-439` — reads `decision.rationale.get("frontier", {})` for tone |
| 13 | AgencySettings has frontier config | ✅ CONFIRMED | `agency_settings.py:157-160` — `enable_auto_negotiation`, `negotiation_margin_threshold`, `enable_checker_agent` |
| 14 | Zero test coverage for FrontierDashboard | ✅ CONFIRMED | No test file references `FrontierDashboard` or `setResultFrontier` |
| 15 | Zero backend tests for frontier models/routers | ✅ CONFIRMED | No test files in spine_api reference frontier |
| 16 | No migrations for frontier models | ✅ CONFIRMED | No alembic/migration files reference frontier |
| 17 | FrontierOrchestrationResult NOT re-exported from spine.ts | ✅ CONFIRMED | Only 20 types re-exported; it's not among them |

---

## 2. File Classification

### 2A. Frontend Files

| File | Classification | Rationale |
|------|---------------|-----------|
| `frontend/src/components/workspace/FrontierDashboard.tsx` | **SALVAGE then delete** | Extract bento-grid pattern, Trust Anchor section, sentiment bar design. Then delete the file. |
| `frontend/src/app/(agency)/workbench/page.tsx` | **MODIFY** — remove frontier tab wiring | Delete lines 79 (tab def), 1073-1086 (rendering). Keep line 119 comment noting "Frontier OS" was workspace section. |
| `frontend/src/stores/workbench.ts` | **PARK** — keep store fields, don't use yet | Keep `result_frontier`, `setResultFrontier`, frontier config fields. Useful for future integration. Just don't call them from UI. |
| `frontend/src/app/(agency)/workbench/SettingsPanel.tsx` | **MODIFY** — hide frontier toggles behind dev flag | Ghost concierge, sentiment, federation, negotiation toggles shown only when `?dev=1` |
| `frontend/src/types/generated/spine-api.ts` | **KEEP** — auto-generated, don't touch | Generated from contract.py. FrontierOrchestrationResult must stay. |
| `frontend/src/types/generated/spine_api.ts` | **KEEP** — auto-generated duplicate? | Same as above. Investigate why 2 copies exist. |
| `frontend/src/types/spine.ts` | **MODIFY** — optionally add FrontierOrchestrationResult to re-exports | If we do partial reintegration later. Not needed now. |
| `frontend/src/lib/api-client.ts` | **KEEP** — Trip type is current system's type | No changes needed unless we integrate frontier into Trip |
| `frontend/src/hooks/useSpineRun.ts` | **KEEP** — no changes needed | Returns RunStatusResponse. Won't have frontier data until backend adds it. |
| `frontend/src/app/(agency)/workbench/__tests__/page.test.tsx` | **MODIFY** — remove frontier mock after tab removal | Lines 69, 143, 235 referencing frontier will go when tab does. |

### 2B. Backend Files — API Layer

| File | Classification | Rationale |
|------|---------------|-----------|
| `spine_api/contract.py` | **KEEP** — canonical contract | `FrontierOrchestrationResult` stays. `frontier_result` field on `SpineRunResponse` stays. |
| `spine_api/server.py` | **KEEP** — no removal needed | Frontier router import stays. Nothing broken here. No code to delete. |
| `spine_api/routers/frontier.py` | **PARK** — keep but document as internal experimental | Real endpoints. Don't delete. But mark with `# EXPERIMENTAL: Not yet integrated into pipeline` at top. |

### 2C. Backend Files — Orchestration

| File | Classification | Rationale |
|------|---------------|-----------|
| `src/intake/frontier_orchestrator.py` | **KEEP** — real pipeline logic | Sentiment heuristic, ghost trigger, intel query, specialty detection, negotiation — all real code that runs. Not mock. |
| `src/intake/federated_intelligence.py` | **PARK** — prototype | In-memory mock. Architecture (source hashing, query/incident pattern) is good. Replace with real DB query later. |
| `src/intake/specialty_knowledge.py` | **SALVAGE** — immediately useful | 5 real niches with compliance. Wire into Strategy/Safety tabs as "Special Handling Checklist". |
| `src/intake/negotiation_engine.py` | **KEEP** — already integrated | Called by frontier_orchestrator. Supplier discount logic. Real singleton. |
| `src/intake/strategy.py` | **KEEP** — already reads frontier data | Lines 434-439: reads `decision.rationale["frontier"]` for tone pivoting. Works correctly. |
| `src/intake/orchestration.py` | **KEEP** — already wired | Lines 334-343: calls `run_frontier_orchestration`, populates `decision.rationale["frontier"]`. Works. |
| `src/intake/config/agency_settings.py` | **KEEP** — production config | Already has frontier fields: `enable_auto_negotiation`, `negotiation_margin_threshold`, `enable_checker_agent`, `checker_audit_threshold`. |

### 2D. Backend Files — Models

| File | Classification | Rationale |
|------|---------------|-----------|
| `spine_api/models/frontier.py` | **KEEP** — production-grade schema | GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord, LegacyAspiration — all real models with proper constraints. Don't delete. |
| `spine_api/models/__init__.py` | **KEEP** — model registry | Exports all 4 frontier models for Alembic. Must stay for DB migrations. |

### 2E. Data Fixtures

| File | Classification | Rationale |
|------|---------------|-----------|
| `data/fixtures/sc_frontier_318.json` | **KEEP** — test scenario | Fractional Payment Failure. Useful for testing commercial guard later. |
| `data/fixtures/sc_frontier_319.json` | **KEEP** — test scenario | GDPR/Right to be Forgotten. Useful for compliance testing. |
| `data/fixtures/sc_frontier_320.json` | **KEEP** — test scenario | Hostile Sentiment Pivot. Useful for UX/UI testing. |

### 2F. Tools & Scripts

| File | Classification | Rationale |
|------|---------------|-----------|
| `tools/generate_frontier_scenarios.py` | **KEEP** — useful tool | Generates test fixtures for frontier features. Keep for future use. |
| `tools/verify_frontier_models.py` | **KEEP** — model verification | Simple import check. Keep for CI. |
| `scripts/verify_specialty_knowledge.py` | **KEEP** — useful test | Verifies specialty knowledge entries. Good for future regressions. |

### 2G. Docs (69 files referencing frontier)

| Category | Count | Action |
|----------|-------|--------|
| Research roadmaps (V2-V11) | 10 | Keep — historical vision docs, valuable for future reference |
| Frontier specs & strategy | 3 | Keep — SCHEMA_HARDENING_FRONTIER_MODELS_SPEC.md is a blueprint |
| Personas & scenarios (Frontier) | 25 | Keep — rich source of use cases and UX patterns |
| Industry domain (Frontier) | 14 | Keep — vertical research |
| Product features (Frontier) | 7 | Keep — feature vision docs |
| Architecture reviews mentioning frontier | 19 | Keep — audit trail |
| Other (mention frontier) | 8 | Keep — context preservation |

**No docs should be deleted.** They represent institutional memory and vision.

---

## 3. Compare Against Current Product

| Capability | Current System State | Frontier Vision | Better Source | Recommendation |
|------------|---------------------|-----------------|---------------|----------------|
| **Trip intake** | ✅ IntakeTab — real form, draft persistence, validation | ❌ Not a concern of Frontier (different layer) | Current | Keep current |
| **Trip details (packet)** | ✅ PacketTab — field-level view, validation display | ❌ Not a concern of Frontier | Current | Keep current |
| **Decision / readiness** | ✅ DecisionTab — state, rationale, confidence, budget, fees, suitability | ⚠️ Ghost trigger reacts to ESCALATE_RECOVERY (useful supplement) | Current (supplement with Frontier) | Keep current; add ghost trigger awareness later |
| **Strategy / build** | ✅ StrategyTab — goal, opening, priorities, tone, guardrails | ✅ Tone pivoting from anxiety_alert already consumed in strategy.py:434 - WORKS NOW | Co-functional | Already integrated. No UI changes needed. |
| **Safety / final review** | ✅ SafetyTab — leakage check, bundle review | ⚠️ Specialty knowledge compliance could supplement safety checks | Current (supplement with Frontier) | Surface specialty checklists in SafetyTab |
| **Output delivery** | ✅ OutputPanel — bundle display, review controls, send | ⚠️ Trust Anchor UI pattern improves delivery confidence | Partially Frontier | Copy Trust Anchor pattern into OutputPanel |
| **Risk intelligence** | ❌ Not shown. SafetyTab has leakage only. | ✅ Federated intelligence pool, cross-agency risk sharing | Frontier (idea, not implementation) | PARK — requires industry adoption |
| **Sentiment / anxiety** | ❌ Not shown anywhere in UI | ✅ Sentiment meter + anxiety alert + emotional state log | Frontier (model is real, heuristic is weak) | PARK — replace keyword heuristic with real model before surfacing |
| **Autonomous workflows** | ❌ Only D1 autonomy gate (policy, not execution) | ✅ Ghost Concierge autonomic engine: watch loop, action dispatch, escalation | Frontier (concept is real, code is prototype) | PARK behind feature flag — don't auto-execute yet |
| **Long-term goals** | ❌ Not shown | ✅ Legacy Aspirations: life-mapping, bucket list planning | Frontier (different product category) | PARK — wait for traveler profile system |
| **Negotiation** | ✅ Fee calculation only (P&L) | ✅ Agentic supplier negotiation: group discounts, upgrade requests, budget gaps | Frontier code + Current fees | Already integrated via frontier_orchestrator. Keep both. |
| **Specialty trip handling** | ❌ Not shown | ✅ 5 niche checklists with compliance (specialty_knowledge.py) | Frontier — immediately useful | **SALVAGE NOW** — surface in Strategy/Safety tabs |
| **Audit / trust display** | ⚠️ DecisionTab has rationale.feasibility text | ✅ Trust Anchor section: shield icon, badge, "analyzed X variables", rationale dump | Frontier UI pattern | **SALVAGE NOW** — copy pattern into current tabs |
| **Visual layout** | Linear single-column cards | Bento-grid, multi-column, color-coded status bars | Frontier pattern (not the sci-fi content) | **ADAPT** — borrow bento-grid for info-dense dashboards |
| **Terminology** | Agency-appropriate: "Trip Details", "Ready to Quote?" | Sci-fi: "Ghost Concierge", "Federated Intelligence Pool", "Sector" | Current — always | **NEVER use Frontier terms in production UI.** Translate to agency language. |

### Summary Verdict

Frontier OS is **not a competing product.** It is a cross-cutting intelligence layer that supplements the current pipeline. The overlap is minimal — Frontier adds concepts that don't exist in the current system (sentiment, intelligence pool, autonomy, aspirations). Where they overlap (negotiation, decision rationale), Frontier extends rather than duplicates.

---

## 4. Salvage Plan — What to Integrate & How

### SALVAGE-01: Specialty Knowledge Checklists → Strategy + Safety Tabs

**Data source:** `src/intake/specialty_knowledge.py` — `KNOWLEDGE_BASE` dict with 5 niches

**What:** When a trip matches a specialty niche (e.g., research, medical, human remains), show the checklist and compliance notes in the Strategy and/or Safety tab.

**Target file(s):**
- `frontend/src/app/(agency)/workbench/StrategyTab.tsx` — add a "Special Handling" section
- `frontend/src/app/(agency)/workbench/SafetyTab.tsx` — add compliance notes section

**Data flow:**
- Backend: Already computed. `frontier_orchestrator.py` runs specialty detection (line 117-131).
- Data exists at: `SpineResult.frontier_result.specialty_knowledge` and in `decision.rationale["frontier"]["intelligence_hits"]`
- But specialty_knowledge is NOT written to `decision.rationale["frontier"]` in orchestration.py:337-343
- Fix needed: add specialty_knowledge to the frontier dict in orchestration.py

**UI copy (agency-appropriate):**
- Section header: "Special Handling Checklist"
- Show: niche name, urgency badge (CRITICAL/HIGH/NORMAL), checklist items, compliance notes
- Example: "Academic Research Logistics — HIGH priority. Verify: ATA Carnet, Research Visa, Hazmat Manifest, Cold Chain Protocol"

**Tests required:**
- Unit test: specialty knowledge detection for known keywords
- Integration test: specialty hits appear in strategy/safety tab

**Can be done now:** Yes. Specialty_knowledge.py is real and tested via `scripts/verify_specialty_knowledge.py`.

---

### SALVAGE-02: Trust Anchor UI → Decision + Output + Quote Review

**Data source:** FrontierDashboard.tsx "Trust Anchor" section (lines 80-96)

**What:** A UX pattern that shows "why Waypoint recommends this" — displaying the variables and logic the system considered. Includes a shield icon, "AUTHENTICATED LOGIC" badge, and rationale text.

**Target file(s):**
- `frontend/src/app/(agency)/workbench/DecisionTab.tsx` — add Trust Anchor section below decision state
- `frontend/src/components/workspace/panels/OutputPanel.tsx` — add before "Send to Customer" button

**Data flow:**
- Read from: `store.result_decision?.rationale` (already available in store)
- Additional data: decision confidence, commercial decision, autonomy outcome

**UI copy (agency-appropriate):**
- Section header: "Why This Recommendation" (NOT "Trust Anchor")
- Badge: "SYSTEM ANALYSIS" (NOT "AUTHENTICATED LOGIC")
- Body: "This recommendation is based on traveler requirements, budget analysis, and availability checks. [rationale text here]"
- Toggle: "Show Analysis" / "Hide Analysis" (NOT "Decryption Logic")
- NO hardcoded numbers ("412 variables") — use actual data

**Tests required:**
- Component test: Trust Anchor section renders with rationale data
- Snapshot test: correct display for different decision states

**Can be done now:** Yes. All data is already available in the store.

---

### SALVAGE-03: Bento-Grid Layout Pattern → Future Dashboard Views

**Data source:** FrontierDashboard.tsx bento-grid CSS classes

**What:** The 2-column bento-grid layout is information-dense and visually clear. Reuse the CSS pattern (not the component) for future multi-card dashboard views.

**Target:** NOT immediate. When building a Trip Overview dashboard or Agency Dashboard, use bento-grid pattern.

**Can be done now:** No — layout pattern, not a feature. Document for future.

---

### SALVAGE-04: Sentiment Bar Design → Future, After Real Model

**Data source:** FrontierDashboard.tsx sentiment meter (lines 38-51)

**What:** Color-coded sentiment bar with % and STABLE/ANXIOUS label. Good visual design. BUT the underlying model is a keyword heuristic — not production-ready.

**Target:** Use similar visual pattern when a real sentiment model exists.

**Can be done now:** No. Wait for real sentiment model.

---

### PARK-01: Ghost Concierge Engine

**Why parked:** The autonomic engine concepts (Silent Watch Loop, Action Dispatch, Broken Ghost Protocol, HandoffBrief) are well-designed but:
- Real-world supplier API integration doesn't exist yet
- Autonomic execution without human oversight is too risky for production
- Agency users aren't trained for autonomous workflows

**What to keep:** All backend code, models, and concepts. Just don't surface in UI.

**Feature flag:** `ghost_concierge_enabled: false` in agency settings (already exists as config)

---

### PARK-02: Emotional State Logging

**Why parked:** `EmotionalStateLog` model is real and well-designed. But sentiment detection is keyword-based heuristic (not reliable). Privacy concerns around storing traveler emotional state.

**What to keep:** DB model. Router endpoint. Store config toggle.

**What to defer:** UI display. Real sentiment model. Privacy review.

---

### PARK-03: Federated Intelligence Pool

**Why parked:** Architecture is good (anonymized, cryptographically verified). But:
- Requires industry adoption and coordination
- Chicken-and-egg network effect problem
- Trust/governance model not defined
- Mock implementation (in-memory, 1 hardcoded hit)

**What to keep:** DB model (`IntelligencePoolRecord`). Router endpoint. Concept.

**What to defer:** Real federation. Cross-agency network. UI display.

---

### PARK-04: Legacy Aspirations

**Why parked:** Different product category (life planning, not travel operations). Requires traveler profiles that don't exist yet.

**What to keep:** DB model. Maybe reuse in a future "Traveler Profile" product.

**What to defer:** Everything — far future.

---

## 5. Removal Plan — What to Delete or Hide

### REMOVE-01: FrontierDashboard Component from Workbench

**What:** Remove the Frontier OS tab rendering from the workbench.

**What to delete/modify:**
- `frontend/src/app/(agency)/workbench/page.tsx` line 79: Remove `{ id: 'frontier', label: 'Frontier OS' }` from `workspaceTabs`
- `frontend/src/app/(agency)/workbench/page.tsx` lines 1073-1086: Remove the FrontierDashboard rendering block

**What to keep:** The import statement? Keep it for now — the component file stays (we salvage from it first).

**When:** After SALVAGE-01 and SALVAGE-02 are complete.

---

### REMOVE-02: Remove Fake Confidence Messages

**What:** The component itself has dangerous defaults. Before removing the component, fix the text:
- "No active risks detected in this sector." → "Frontier intelligence is not yet available for this trip."
- "Workflow: GHOST-SEQ-004-X" → Remove hardcoded workflow ID
- "Waypoint OS has analyzed 412 variables..." → Remove hardcoded stat

**When:** Immediately — even before salvage. Fix the file in place.

---

### REMOVE-03: Hide Frontier Config Toggles from SettingsPanel

**What:** The Ghost Concierge, Sentiment, Federated Intelligence, and Auto-Negotiation toggles in SettingsPanel should be hidden or gated behind `?dev=1`.

**What to modify:**
- `frontend/src/app/(agency)/workbench/SettingsPanel.tsx` — wrap frontier toggle sections in dev-mode gate
- Or: leave toggles but mark them with "(Experimental)" labels

**When:** After REMOVE-01. Keep toggles functional for internal testing.

---

### REMOVE-04: Clean Up Dead Store References

**What:** After removing the frontier tab and salvage, check if `result_frontier` is still unused.

**If unused:** Add a comment: `// PARKED: Frontier result field — reserved for future cross-agency intelligence integration`
Do NOT delete the store field — it may be needed later.

**If used by salvage:** Keep it. Wire it properly.

---

### REMOVE-05: Remove `data/fixtures/sc_frontier_*.json` from CI/Test Fixture Load

**What:** These fixtures should not be loaded in production or standard test runs. They're Frontier-specific.

**Keep the files for future testing.** Just exclude from default fixture loading.

---

### DO NOT DELETE

- ❌ Do NOT delete `spine_api/models/frontier.py` — real DB models with proper constraints
- ❌ Do NOT delete `src/intake/frontier_orchestrator.py` — real pipeline logic, already running
- ❌ Do NOT delete `src/intake/specialty_knowledge.py` — real business value
- ❌ Do NOT delete `src/intake/federated_intelligence.py` — good architecture prototype
- ❌ Do NOT delete `spine_api/routers/frontier.py` — real REST endpoints
- ❌ Do NOT delete `spine_api/contract.py` frontier types — canonical contract
- ❌ Do NOT delete `frontend/src/stores/workbench.ts` frontier fields — needed for reintegration
- ❌ Do NOT delete `frontend/src/types/generated/spine-api.ts` frontier types — auto-generated from contract
- ❌ Do NOT delete any docs referencing frontier — institutional memory

---

## 6. Local Test Plan

### Start Environment

```bash
# Terminal 1: Backend
cd /Users/pranay/Projects/travel_agency_agent
SPINE_API_DISABLE_AUTH=1 uv run uvicorn spine_api.server:app --port 8000 --reload

# Terminal 2: Frontend
cd /Users/pranay/Projects/travel_agency_agent/frontend
npm run dev
```

### Verify Current State (Pre-Change)

1. **Open workbench with frontier tab:**
   - URL: `http://localhost:3000/workbench?tab=frontier`
   - Expected: Frontier OS tab renders with "Ghost Concierge ACTIVE", "82% STABLE", "No active risks detected in this sector."

2. **Prove no real data reaches UI:**
   - Open browser DevTools → Network tab
   - Submit a trip: `http://localhost:3000/workbench?tab=intake`
   - Type a message with "urgent visa Singapore" keywords, click Process Trip
   - Polling runs via `GET /api/runs/{id}`
   - Switch to Frontier tab — data unchanged
   - Check Zustand store devtools → `result_frontier` is `null`

3. **Prove backend DOES produce frontier_result:**
   ```bash
   SPINE_API_DISABLE_AUTH=1 uv run python -c "
   from src.intake.orchestration import run_spine_once
   from src.intake.packet_models import SourceEnvelope
   env = SourceEnvelope.from_freeform('urgent family trip to Singapore, visa help needed', 'agency_notes', 'agent')
   result = run_spine_once(envelopes=[env])
   print('### FrontierResult exists:', result.frontier_result is not None)
   fr = result.frontier_result
   if fr:
       print('  sentiment:', fr.sentiment_score)
       print('  ghost_triggered:', fr.ghost_triggered)
       print('  intel_hits:', len(fr.intelligence_hits))
       print('  specialty_knowledge:', len(fr.specialty_knowledge))
   print('### Rationale frontier:', result.decision.rationale.get('frontier'))
   "
   ```
   - Expected: frontier_result non-None, sentiment around 0.4-0.5, intel_hits may have Singapore mock

4. **Prove strategy.py reads frontier data:**
   ```bash
   SPINE_API_DISABLE_AUTH=1 uv run python -c "
   from src.intake.orchestration import run_spine_once
   from src.intake.packet_models import SourceEnvelope
   env = SourceEnvelope.from_freeform('emergency! urgent help needed now', 'agency_notes', 'agent')
   result = run_spine_once(envelopes=[env], operating_mode='emergency')
   print('strategy tone:', result.strategy.suggested_tone if hasattr(result.strategy, 'suggested_tone') else 'N/A')
   print('session_goal:', result.strategy.session_goal)
   "
   ```

### Verify Post-Change (After Implementation)

For each salvage item, verify:
1. Specialty checklists appear in Strategy/Safety tab when keyword-triggered trip is processed
2. Trust Anchor section appears in DecisionTab with real rationale data
3. Frontier tab is no longer in the workbench
4. SettingsPanel no longer shows frontier toggles (or shows them behind dev flag)
5. No test failures in `npm run test`
6. No build errors in `npm run build`

---

## 7. Exploration Areas to Add to Map

From the Frontier OS document corpus (69+ docs, product_features/INDEX.md), the following **genuinely useful exploration areas** should be added to the exploration map. These are distinct from the salvage plan — they represent long-term research directions worth tracking.

### Near-Term (Research Now, Build in 1-3 Months)

| # | Exploration Area | Source Docs | Key Question |
|---|-----------------|-------------|--------------|
| E1 | **Devil's Advocate / Adversarial Trip Audit** | `EXPLORATION_FRONTIERS_2026-04-18`, `product_features/ADVERSARIAL_TRIP_AUDIT_ENGINE` | Can we stress-test every itinerary for failure points before delivery? Mobility issues, weather dependencies, tight connections? |
| E2 | **Commercial Guardrail (Cost-to-Serve)** | `EXPLORATION_FRONTIERS_2026-04-18` | Can we compute real-time profitability per trip and alert before agents waste time on loss-making work? |
| E3 | **Next-Action Nudging** | `EXPLORATION_FRONTIER` | Can we detect idle trips and suggest smart next actions to operators? |
| E4 | **Anonymized Supplier Blacklist** | `product_features/INDEX.md` | Can agencies share bad-supplier data without compromising competitive advantage? |
| E5 | **Visual Intent Extraction** | `EXPLORATION_FRONTIERS_2026-04-18`, `product_features/VISUAL_INTENT_EXTRACTION_ENGINE` | Can vision models extract trip preferences from Instagram/Pinterest shared by clients? Now feasible with VLMs. |
| E6 | **Semantic Taste Graph** | `EXPLORATION_FRONTIERS_2026-04-18`, `product_features/SEMANTIC_TASTE_GRAPH_DISCOVERY` | Can we encode agency aesthetic preferences as searchable criteria? Simplified version: structured preference tags. |

### Mid-Term (Research + Prototype, Build in 3-6 Months)

| # | Exploration Area | Source Docs | Key Question |
|---|-----------------|-------------|--------------|
| E7 | **Ghost Concierge: Autonomic Flight Delay Recovery** | `ADDITIONAL_SCENARIOS_315`, `GHOST_CONCIERGE_AUTONOMIC_ENGINE` | Can we auto-rebook transport when flights are delayed (within autonomy bounds)? Requires supplier API integration. |
| E8 | **Sentiment-Based Escalation Routing** | `ADDITIONAL_SCENARIOS_316`, `EMOTIONAL_ANXIETY_MITIGATION_ENGINE` | Can real sentiment analysis replace the current keyword heuristic? Can we route to human agents when hostility detected? |
| E9 | **Post-Trip Retention & Aspiration Engine** | `POST_TRIP_AFTERGLOW_AND_RETENTION_LOOPS`, `ADDITIONAL_SCENARIOS_322` | Can we use trip history to generate "redemption itineraries" after bad experiences? |
| E10 | **Climate Adaptive Itinerary Engineering** | `product_features/CLIMATE_ADAPTIVE_ITINERARY_ENGINEERING` | Can we proactively reroute trips based on weather forecasts? |
| E11 | **Hyper-Local Last Mile Orchestration** | `product_features/HYPER_LOCAL_LAST_MILE_ORCHESTRATION` | Can we auto-handle SIM cards, rail-to-road transfers, and local coordination? |
| E12 | **Autonomous Supplier Auction & Negotiation** | `product_features/INDEX.md`, `FRONTIER_SCENARIO_STRATEGY_NOTES` Scenario 321 | Can AI negotiate no-show waivers, upgrade requests, and group discounts with suppliers autonomously? |

### Far-Future (Monitor Only, No Build Timeline)

| # | Exploration Area | Source Docs | Key Question |
|---|-----------------|-------------|--------------|
| E13 | **Legacy Milestone Visioning / Life Mapping** | `product_features/LEGACY_MILESTONE_VISIONING_ENGINE`, `spine_api/models/frontier.py` `LegacyAspiration` | Different product category. Requires traveler profile system first. |
| E14 | **Federated Cross-Agency Intelligence Pool** | `ADDITIONAL_SCENARIOS_317`, `product_features/CROSS_AGENCY_INTELLIGENCE_POOLING` | Requires industry network effects. Governance model undefined. |
| E15 | **Multi-Agent Slot Trading / Game Theory** | `RESEARCH_ROADMAP_FRONTIER_EXPANSION_V2` Track 2 | Requires market infrastructure. Academic research problem. |
| E16 | **Ambient Sensory Agency (IoT/Wearables)** | `RESEARCH_ROADMAP_FRONTIER_EXPANSION_V2` Track 3 | Requires hardware integration. Privacy concerns. |
| E17 | **Sovereign Agentic Wallets / Smart Contracts** | `RESEARCH_ROADMAP_FRONTIER_EXPANSION_V2` Track 4 | Requires crypto/blockchain infra. Regulatory unknown. |
| E18 | **Predictive Disruption "The Oracle"** | `RESEARCH_ROADMAP_FRONTIER_EXPANSION_V2` Track 5 | Interesting concept. Alternative data sources untested. |
| E19 | **Recursive Identity Architecture** | `RESEARCH_ROADMAP_FRONTIER_EXPANSION_V2` Track 1 | Situational identity switching. Requires persona system. |
| E20 | **Post-Quantum Identity & Privacy** | `product_features/INDEX.md`, `SCHEMA_HARDENING_FRONTIER_MODELS_SPEC` | NIST PQC not finalized. No travel agency threat model. |
| E21 | **Orbital / Sub-Orbital Logistics** | `product_features/ORBITAL_AND_SUB_ORBITAL_LOGISTICS` | Space tourism not at commercial scale. |
| E22 | **Extreme Environment Risk Modeling** | `product_features/INDEX.md` Domain 9 | Polar, deep-sea, radiation. Ultra-niche. |

### Rejected (Should NOT Be on Exploration Map)

| # | Idea | Reason for Rejection |
|---|------|---------------------|
| R1 | BCI-Speed / Neural Pre-emption (NEURAL-001) | Pure science fiction. No travel agency application in foreseeable future. |
| R2 | Cybernetic Hardware Integrity (CYBER-001) | Not a real market. |
| R3 | Inter-Species Companion Agency (SPECIES-001) | Not a real market. |
| R4 | Macro-Engineering Disruption (MACRO-001) | Space elevators, weather control arrays — planetary-scale infrastructure fiction. |
| R5 | Dream-State Briefing | Not grounded in technology. |

---

## 8. Final Recommendation

### VERDICT: B — Salvage Selected Concepts, Remove Frontier OS Tab

**Do NOT integrate Frontier OS as a tab or parallel product surface.**

### Immediate Actions (This Sprint, No Git Operations)

1. **Fix fake confidence**: In `FrontierDashboard.tsx`, change "No active risks detected in this sector" to "Frontier intelligence not yet available for this trip." (1 line change)

2. **Mark tab as experimental**: Keep the tab but add "Experimental" banner and dev-mode gate in the tab label or component.

3. **SALVAGE-01**: Wire specialty knowledge checklists into StrategyTab/SafetyTab.
   - Backend: already running. Data path working.
   - Frontend: new UI section. ~50 lines.
   - Test: verify with keyword-triggered input.

4. **SALVAGE-02**: Copy Trust Anchor pattern into DecisionTab.
   - All data already available in store.
   - New UI section under decision state. ~60 lines.
   - Rename terminology from "Trust Anchor" to "Why This Recommendation."

### Next Steps (After User Reviews Salvage)

5. **Remove: Frontier tab from workbench** (lines 79, 1073-1086)
6. **Remove: Frontier settings toggles** from SettingsPanel (or gate behind dev flag)
7. **Park: Ghost, Emotion, Federation, Legacy** behind feature flags
8. **Document: Add exploration areas to map**

### Things We Should NOT Do

- ❌ Do NOT wire `frontier_result` into the API just to make the Frontier tab work — fix the tab removal first
- ❌ Do NOT delete backend models or orchestration code — they're running and useful
- ❌ Do NOT ship "Federated Intelligence Pool" or "Ghost Concierge" terminology to agency users
- ❌ Do NOT delete any documentation
- ❌ Do NOT commit or push any changes without explicit user approval

---

## Appendix A — Quick Reference: What Code Exists vs What It Does

| Code | Runs? | Data Real? | UI Shows It? | User Should See It? |
|------|-------|-----------|-------------|---------------------|
| `frontier_orchestrator.py` | ✅ Every pipeline run | ✅ Real (heuristic) | ❌ | Parked behind dev flag |
| `specialty_knowledge.py` | ✅ Every pipeline run | ✅ Real | ❌ | YES — surface in Strategy/Safety |
| `federated_intelligence.py` | ✅ Every pipeline run | ⚠️ Mock (1 hardcoded hit) | ❌ | NO — park until real |
| `negotiation_engine.py` | ✅ Every pipeline run | ✅ Real (simulated) | ❌ | Parked — already in DecisionTab fees |
| `GhostWorkflow` model | ❌ No CRUD | ✅ Schema real | ❌ | NO — park behind dev flag |
| `EmotionalStateLog` model | ❌ No CRUD | ✅ Schema real | ❌ | NO — park until sentiment model |
| `IntelligencePoolRecord` model | ❌ No CRUD | ✅ Schema real | ❌ | NO — park until federation |
| `LegacyAspiration` model | ❌ No CRUD | ✅ Schema real | ❌ | NO — park until traveler profiles |
| `routers/frontier.py` | ✅ Endpoints live | ✅ Real REST | ❌ | Keep but document as internal |

## Appendix B — Terminology Translation Table

| Frontier OS Term | Agency-Appropriate Replacement |
|-----------------|-------------------------------|
| Ghost Concierge | Automated Workflows |
| Federated Intelligence Pool | Risk Intelligence Network |
| Trust Anchor | Why This Recommendation |
| Federated Node #412 | [source name or "Anonymized source"] |
| AUTHENTICATED LOGIC | SYSTEM ANALYSIS |
| Sentiment Meter | Customer Sentiment |
| Ghost Active | [don't show to agency users] |
| Sector | Destination / Region |
| Frontier OS | [don't brand as separate product] |
| Emotional State | Customer Satisfaction |
| Legacy Aspiration | Travel Goals / Bucket List |
