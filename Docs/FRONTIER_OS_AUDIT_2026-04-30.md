# Frontier OS / FrontierDashboard — Audit & Comparison Report

**Date:** 2026-04-30
**Scope:** Complete audit of all Frontier OS code (frontend + backend), comparison against current production system.

---

## 1. Inventory

### Frontend Source (4 files)

| File | Role | Status |
|------|------|--------|
| `frontend/src/components/workspace/FrontierDashboard.tsx` | Dashboard component (100 lines) | Visual mock with hardcoded defaults |
| `frontend/src/app/(agency)/workbench/page.tsx` | Workbench tab wiring (line 79, 1073-1086) | Tab renders, wires to `store.result_frontier` |
| `frontend/src/stores/workbench.ts` | Zustand store: `result_frontier`, `setResultFrontier` | Field+setter defined, never called |
| `frontend/src/app/(agency)/workbench/SettingsPanel.tsx` | Config toggles (ghost concierge, sentiment, federation, negotiation) | Real UI, wired to store config, never consumed by backend |

### Frontend Types (2 files)

| File | Role | Status |
|------|------|--------|
| `frontend/src/types/generated/spine-api.ts` | `FrontierOrchestrationResult` interface (lines 93-105) | Auto-generated from contract, correct shape |
| `frontend/src/types/spine.ts` | `RunStatusResponse` (lines 60-79) | **Missing `frontier_result` — poll endpoint type lacks it** |
| `frontend/src/lib/api-client.ts` | `Trip` interface (line 288+) | **Missing `frontier_result` — Trip type lacks it** |

### Frontend Tests (1 file)

| File | Role | Status |
|------|------|--------|
| `frontend/src/app/(agency)/workbench/__tests__/page.test.tsx` | Workbench test (line 69) | Mocks `result_frontier: null` | 

### Frontend Hooks (1 file)

| File | Role | Status |
|------|------|--------|
| `frontend/src/hooks/useSpineRun.ts` | Run polling hook | Returns `RunStatusResponse` which has no frontier field |

### Backend Python: API Layer (2 files)

| File | Role | Status |
|------|------|--------|
| `spine_api/contract.py` | `FrontierOrchestrationResult` model (lines 71-82) + field in `SpineRunResponse` (line 128) | Defined in contract, **never populated by server** |
| `spine_api/server.py` | POST /run + GET /runs/{id} handlers | `_execute_spine_pipeline` never extracts `frontier_result` from `SpineResult` to RunLedger; `RunStatusResponse` missing the field |

### Backend Python: Router (1 file)

| File | Role | Status |
|------|------|--------|
| `spine_api/routers/frontier.py` | REST API (POST /ghost/workflows, POST /emotions/log, POST /intelligence/report) | Real CRUD endpoints, **never called by pipeline**, standalone API surface |

### Backend Python: Models (1 file)

| File | Role | Status |
|------|------|--------|
| `spine_api/models/frontier.py` | SQLAlchemy: GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord, LegacyAspiration | Real DB models with check constraints, proper foreign keys, indexes |

### Backend Python: Intake Orchestration (4 files)

| File | Role | Status |
|------|------|--------|
| `src/intake/frontier_orchestrator.py` | `run_frontier_orchestration()` (224 lines) | Real pipeline logic — sentiment heuristic, ghost trigger, intelligence query, specialty detection, negotiation |
| `src/intake/federated_intelligence.py` | `FederatedIntelligenceService` (69 lines) | In-memory mock with 1 hardcoded Singapore visa delay hit |
| `src/intake/specialty_knowledge.py` | `SpecialtyKnowledgeService` (63 lines) | Real — 5 niches with proper checklists/compliance |
| `src/intake/orchestration.py` | `run_spine_once()` — calls `run_frontier_orchestration()` (line 334), puts it in `SpineResult.frontier_result` (line 440) | **Real orchestration, properly wired into SpineResult** |

### Data Fixtures (3 files)

| File | Role |
|------|------|
| `data/fixtures/sc_frontier_318.json` | Frontier scenario fixture |
| `data/fixtures/sc_frontier_319.json` | Frontier scenario fixture |
| `data/fixtures/sc_frontier_320.json` | Frontier scenario fixture |

### Tools (2 files)

| File | Role |
|------|------|
| `tools/generate_frontier_scenarios.py` | Scenario generator |
| `tools/verify_frontier_models.py` | Model verification |

### Docs (10+ files)

| Category | Count |
|----------|-------|
| Frontier research roadmaps (V2–V11) | 10 |
| Frontier specs & strategy | 3 |
| Personas & scenarios | 25 (many with frontier content) |

---

## 2. Runtime Data Flow

### Intended Path

```
src/intake/orchestration.py                  ✅  run_frontier_orchestration() called
    → src/intake/frontier_orchestrator.py    ✅  orchestrator runs all 5 subsystems
    → returns FrontierOrchestrationResult    ✅  
    → SpineResult.frontier_result            ✅  populated (line 440)
    → spine_api/server.py _execute_spine     ❌  NEVER extracts frontier_result from SpineResult
    → RunLedger steps                        ❌  frontier_result never checkpointed
    → GET /runs/{id} RunStatusResponse       ❌  field doesn't exist in response model
    → frontend useSpineRun.ts hook           ❌  returns RunStatusResponse (no frontier)
    → workbench page.tsx useEffect           ❌  doesn't call setResultFrontier
    → Zustand store.result_frontier          ❌  always null
    → FrontierDashboard props                ❌  always uses hardcoded defaults
```

### Broken at 3 Levels

| Level | What's Broken | Severity |
|-------|---------------|----------|
| **Backend server** | `_execute_spine_pipeline` discards `frontier_result` from `SpineResult` after `run_spine_once` returns it | BLOCKING |
| **API contract** | `RunStatusResponse` (both backend + frontend type) lacks `frontier_result` field | BLOCKING |
| **Frontend hydration** | `useHydrateStoreFromTrip` and run completion handler never call `setResultFrontier` | BLOCKING |

---

## 3. Backend Audit

### frontier_orchestrator.py (src/intake/)

**Status:** Real pipeline logic, heuristic prototype
- 5 subsystems all wired: sentiment, ghost concierge, intelligence pool, specialty knowledge, negotiation engine
- `_calculate_sentiment_heuristic()` — keyword-based heuristic with explicit advisory-only warning (line 204)
- Ghost Concierge triggers on `ESCALATE_RECOVERY` or `emergency` mode
- Checker agent redundancy for ghost workflows
- Exception handling on every subsystem (never breaks pipeline)
- **Limitation:** Sentiment is keyword heuristic, not LLM-based

### federated_intelligence.py (src/intake/)

**Status:** In-memory mock
- `_pool` is in-memory list — data lost on restart
- `query_risks()` has 1 hardcoded mock for "Singapore" (visa_processing_delay, severity 3)
- Real structure for incident reporting with source hashing
- **Not production-safe:** No persistent storage, no real federation

### specialty_knowledge.py (src/intake/)

**Status:** Production-grade
- 5 fully defined niches with proper checklists, compliance requirements, safety notes
- Academic Research Logistics (HIGH), Human Remains Repatriation (CRITICAL), Sub-Aquatic (NORMAL), Medical Tourism (HIGH), MICE (NORMAL)
- Keyword-based detection via `identify_niche()`
- Real business value — actually useful for travel agency

### frontier.py DB Models (spine_api/models/)

**Status:** Real SQLAlchemy models
- `GhostWorkflow`: task_type, autonomic_level (0-4), action_payload (JSON), status transitions (pending→executing→completed→failed→escalated), proper check constraints and indexes
- `EmotionalStateLog`: sentiment_score, anxiety_trigger, mitigation_action_id, recovery_time_ms, FK to agencies
- `IntelligencePoolRecord`: incident_type, anonymized_data (JSON), severity (1-5), confidence (0-1), source_agency_hash
- `LegacyAspiration`: goal_title, target_year, fitness_window_age, estimated_cost (Decimal), status transitions
- All models have proper indexes, foreign keys, check constraints. Real production-grade schema design.
- **Limitation:** Not covered by Alembic migrations yet? (Check: referenced in models/__init__.py)

### routers/frontier.py (spike_api/routers/)

**Status:** Real but disconnected
- 4 REST endpoints with proper Pydantic validation
- `POST /ghost/workflows`, `GET /ghost/workflows/{id}`, `POST /emotions/log`, `POST /intelligence/report`
- **Never called by the pipeline.** These are standalone API endpoints.
- Reaches DB directly with async sessions.

### contract.py FrontierOrchestrationResult

**Status:** Defined in contract, properly structured
- Fields: ghost_triggered, ghost_workflow_id, sentiment_score, anxiety_alert, intelligence_hits (list), specialty_knowledge (list), mitigation_applied, requires_manual_audit, audit_reason, negotiation_active, negotiation_logs (list)
- **Only used in `SpineRunResponse` (POST response envelope),** not in `RunStatusResponse` (polling endpoint)
- Frontend auto-generates correct TS types for it

### server.py wiring

**Status:** **THE BROKEN LINK**
- Line 861: calls `run_spine_once()` which returns `SpineResult` with `frontier_result` populated
- Line 874-897: `_checkpoint_result_steps()` only checkpoints packet, validation, decision, strategy — NOT frontier
- Line 966-978: `save_processed_trip` does not include frontier_result
- No code in `_execute_spine_pipeline()` reads `frontier_result` from `SpineResult` or persists it

---

## 4. Frontend Audit

### FrontierDashboard Component

**Status:** Visual mock, 100 lines
- Location: `frontend/src/components/workspace/FrontierDashboard.tsx`
- All props have hardcoded defaults: `packetId="PK-9912"`, `sentiment=0.82`, `isAnxious=false`, `ghostActive=true`, `intelHits=[]`, `logicRationale="Autonomic trigger based on 'visa_delay'..."` 
- 4 sections: Ghost Concierge Status, Sentiment Meter, Intelligence Feed, Trust Anchor
- "No active risks detected in this sector" shown when `intelHits` empty
- `logicRationale` fallback chain: `store.result_frontier?.audit_reason || store.result_decision?.rationale || ''`
- Styled with Tailwind, no CSS module

### Workbench Tab Wiring

**Status:** Tab renders, data path broken
- Tab #7 of 9 in `workspaceTabs` array
- Renders at lines 1073-1085:
```
<FrontierDashboard
  packetId={trip?.id}
  sentiment={store.result_frontier?.sentiment_score ?? 0.82}
  isAnxious={store.result_frontier?.anxiety_alert ?? false}
  ghostActive={store.result_frontier?.ghost_triggered ?? false}
  intelHits={store.result_frontier?.intelligence_hits ?? []}
  logicRationale={store.result_frontier?.audit_reason || store.result_decision?.rationale || ''}
/>
```
- The `??` defaults mean: always shows 0.82 sentiment, not anxious, `ghostActive` depends on which is ambiguous...

Wait — `ghostActive` default is `true` (from component), but the wired prop `store.result_frontier?.ghost_triggered ?? false` would show `false` since store is null. The component overrides with `ghostActive = true` default.

### Store

**Status:** Field and setter defined, never called
- `result_frontier: any | null` at line 86
- `setResultFrontier: (value: any | null) => void` at line 100
- Initialized to `null` at line 208
- Zero call sites in the entire `frontend/src/` directory (confirmed via grep)

### Tests

**Status:** Minimal mock coverage
- `page.test.tsx` mocks `result_frontier: null` at line 69
- No tests for FrontierDashboard component itself
- No tests for frontier data flow

---

## 5. Compare Against Current System

| Capability | Current System | Frontier System | Better? | Why | Recommendation |
|------------|---------------|-----------------|---------|-----|----------------|
| Trip intake | ✅ IntakeTab — real form, draft persistence, validation | ❌ No frontier equivalent | Current | Frontier is an overlay, not an intake | Keep current |
| Packet/details | ✅ PacketTab — field-level view, structured | ❌ No packet equivalent | Current | — | Keep current |
| Decision | ✅ DecisionTab — real decision output from spine | ❌ Ghost trigger only (decision reactive) | Current | Frontier ghost is a reaction to decision, not a replacement | Keep current |
| Strategy | ✅ StrategyTab — full strategy output | ❌ No strategy equivalent | Current | — | Keep current |
| Risk intelligence | ⚠️ SafetyTab — leakage check, no external risk data | ✅ Federated intelligence pool | Frontier | Cross-agency risk data doesn't exist in current system | **Adapt** |
| Sentiment/tone | ❌ No sentiment tracking | ✅ Sentiment meter, anxiety alert | Frontier | Current system has no traveler emotional state | **Adapt** |
| Autonomous workflows | ❌ No ghost concierge | ✅ Ghost Workflow model + trigger logic | Frontier | Real DB model with autonomic levels | **Park** |
| Long-term goals | ❌ No aspiration tracking | ✅ LegacyAspiration model | Frontier | Life-mapping concept | **Park** |
| Negotiation | ⚠️ Basic pricing | ✅ Negotiation engine in frontier_orchestrator | Both | Current has fee calc, frontier has agentic negotiation | Mixed — see notes |
| Specialty knowledge | ❌ Not explicitly surfaced | ✅ 5 niche checklists | Frontier | Real business value for specialized trips | **Adapt** |
| Visual presentation | ✅ Production UI, dark theme, polished | ✅ Bento-grid design, Trust Anchor section, glow effects | Frontier | More visually rich than current safety tab | **Adapt UI** |

### Key Finding: Complementary, Not Competing

The current system and Frontier are NOT duplicates. The current system is a **trip pipeline** (intake → packet → decision → strategy → safety → output). Frontier is a **cross-cutting intelligence layer** that analyzes traveler sentiment, detects autonomous-trigger conditions, queries external risk pools, and logs emotional states.

The overlap is minimal — Frontier could theoretically integrate INTO the current pipeline as a supplement, not a replacement.

---

## 6. What is Better in Frontier — Salvageable Concepts

| Concept | Location | Assessment | Action |
|---------|----------|------------|--------|
| **Federated intelligence pool** | `federated_intelligence.py` + `IntelligencePoolRecord` model | Real architecture, in-memory mock implementation. Valuable for cross-agency risk sharing. The DB model is production-grade. | **Adapt** — Replace in-memory pool with persistent query on DB model |
| **Sentiment/anxiety signals** | `frontier_orchestrator.py` sentiment heuristic + `EmotionalStateLog` model | Heuristic is weak (keyword-based), but the model is real. Valuable for premium/white-glove travel. | **Adapt** — Improve heuristic or replace with LLM call |
| **Specialty knowledge checklists** | `specialty_knowledge.py` | Production-grade. 5 niches with compliance notes. Immediately useful. | **Adapt** — Surface specialty hits in the strategy/safety tabs |
| **Ghost concierge workflows** | `GhostWorkflow` model + trigger in orchestrator | Real model, simple trigger (ESCALATE_RECOVERY). Premature for agency users — autonomic ops will confuse them. | **Park** — Keep model, hide from UI. Enable behind feature flag for internal testing |
| **Legacy aspirations** | `LegacyAspiration` model | Real model, but far-future. Requires traveler profile system that doesn't exist yet. | **Park** — Comes after traveler profiles |
| **Negotiation engine** | Negotiation in `frontier_orchestrator.py` + `negotiation_service` | Already exists, relies on `negotiation_engine.py` | Already integrated — just needs wiring |
| **Trust Anchor / audit language** | FrontierDashboard "Trust Anchor" section | High-quality UX copy. Builds user confidence. | **Adapt** — Copy the trust/audit display pattern into Strategy or Safety tab |
| **Bento-grid visual layout** | FrontierDashboard bento-item pattern | Clean, data-dense layout | **Adapt** — Could be used for a future cross-tab dashboard |
| **Frontier REST API** | `routers/frontier.py` | Proper endpoints, but disconnected | **Keep** — Defined but needs integration |

---

## 7. Local Run / Test Plan

### Backend

```bash
cd /Users/pranay/Projects/travel_agency_agent

# Start with env vars for auth-disabled mode:
SPINE_API_DISABLE_AUTH=1 uvicorn spine_api.server:app --port 8000 --reload
```

### Frontend

```bash
cd /Users/pranay/Projects/travel_agency_agent/frontend
npm run dev
```

### To see Frontier tab:

1. Open `http://localhost:3000/workbench?tab=frontier`
2. The Frontier OS tab renders with default/hardcoded data: sentiment 82%, ghost ACTIVE, "No active risks detected"
3. Check browser DevTools Network tab — no XHR calls for frontier data
4. Check Zustand devtools — `result_frontier` is always `null`

### To prove data path is broken:

1. Add a breakpoint or log in `spine_api/server.py` after `run_spine_once()` returns (line 861-870)
2. Check `result.frontier_result` — it IS populated (non-None)
3. Continue watching — nothing reads it, nothing persists it
4. Frontend stores never receive it

### Expected results today:

- Frontier tab renders and looks nice
- All data shown is fake defaults
- No real intelligence, sentiment, or ghost data flows to the dashboard
- The "Trust Anchor" section shows `logicRationale` from `store.result_decision?.rationale` if one exists from pipeline, otherwise empty string

---

## 8. Risk Assessment

| Risk | Severity | Details |
|------|----------|---------|
| **Fake data presented as real** | HIGH | "No active risks detected" when intelHits empty creates false confidence. Sentiment always shows 82% stable. Ghost always shows ACTIVE. This misleads operators. |
| **Sci-fi terminology confuses agency users** | MEDIUM | "Federated Intelligence Pool", "Federated Node #412", "Ghost Concierge", "Trust Anchor" — these terms are not travel industry standard. Would confuse real travel agents. |
| **Dead backend models accumulate** | LOW | DB models exist but never queried. Tables could be created but remain empty. Wasted schema complexity. |
| **Parallel router creates confusing API surface** | LOW | `spine_api/routers/frontier.py` has standalone endpoints that aren't integrated. Developer confusion about when to use which API. |
| **Data pipeline has 3 breaks** | HIGH | Backend → RunLedger → API → Frontend Store — each break means any fix requires touching 3+ layers. Integration effort is non-trivial. |
| **EmotionalStateLog privacy** | MEDIUM | Model stores `anxiety_trigger` as raw string. Comment in model warns about PII but no enforcement. Risk of storing sensitive traveler data. |
| **IntelligencePoolRecord anonymization** | MEDIUM | `anonymized_data` is JSON with no sanitization layer. Risk of raw data leakage. |

---

## 9. Recommendation

### Verdict: B — Salvage selected concepts, hide Frontier OS tab

**Do NOT integrate Frontier OS as-is.** Do NOT remove it entirely. The right approach is to extract the high-value pieces and park the premature ones.

### Immediate (this sprint):

1. **Mark Frontier tab as experimental** — add a `?experimental=1` flag to the frontier tab, or add a dev-mode banner inside FrontierDashboard: "Frontier OS is an experimental feature under development"
2. **Fix the false confidence issue** — Replace the "No active risks detected" text with "Frontier intelligence not available" when data is null. The current default text implies real security clearance.
3. **Surface specialty knowledge hits** — `specialty_knowledge.py` is real and immediately useful. Wire it into the Strategy tab or Safety tab: when a specialty niche is detected, show the checklist + compliance notes directly.
4. **Fix the data pipeline at the API layer** — This is a ~20-line fix in `spine_api/server.py`: extract `frontier_result` from `SpineResult` and save it to `RunLedger`. Add field to `RunStatusResponse` in both backend and frontend types.

### Next sprint:

5. **Add real sentiment** — Replace keyword heuristic with an LLM call. The model and store are ready.
6. **Build intelligence pool query API** — Wire `IntelligencePoolRecord` queries into the frontier orchestrator so federated intelligence becomes real instead of in-memory mock.
7. **Copy Trust Anchor UI** — The trust/audit display pattern from FrontierDashboard is better than the current opacity. Add a similar section to Strategy tab or Output panel.

### Next quarter:

8. **Ghost Concierge** — Enable behind feature flag for internal testing. Needs operator education and clear documentation.
9. **Legacy Aspirations** — Only after traveler profiles are built.
10. **Full Frontier Dashboard v2** — Build only when the above pieces are real and the data pipeline is proven.

### Keep hidden:

- The `Frontier OS` tab stays in the workbench tab list but shows an "under development" state
- Sci-fi terminology in the UI gets toned down for agency users (replace "Federated Intelligence Pool" with "Risk Intelligence Network", "Ghost Concierge" with "Automated Workflows")
- The standalone `routers/frontier.py` stays but is documented as "internal API — not yet integrated into pipeline"

### Do NOT do:

- ❌ Do not remove backend models — they're well-designed and will be used
- ❌ Do not ship Frontier OS as production UI — the fake data problem is too dangerous
- ❌ Do not invest in federated intelligence without a real data-sharing governance model
- ❌ Do not show "Legacy Aspirations" in the UI until traveler profiles exist

---

## Summary

| Dimension | Verdict |
|-----------|---------|
| **Code quality** | ✅ Backend models + orchestrator are solid. Dashboard is fine as prototype. |
| **Operational safety** | ❌ Fake data creates false confidence. Must be fixed before any production use. |
| **User experience** | 🟡 Visual design is strong, but terminology is wrong for agency users. |
| **Data pipeline** | ❌ Broken at 3 levels. ~1 day of work to fix. |
| **Business value** | 🟡 Specialty knowledge = immediate value. Sentiment/Federation/Ghost = medium-term differentiators. |
| **Recommendation** | **Salvage specialty knowledge + sentiment model + trust UI. Park ghost + aspirations. Hide tab behind dev flag.** |
