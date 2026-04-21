# Status Assessment — WaypointOS

**Date**: 2026-04-21
**Purpose**: Full codebase audit against documented architecture decisions (D1–D6), cross-project patterns, and gap register. Maps what's implemented, what's decided-but-paper-only, and what's blocked.
**Method**: Directory walk, file inventory, line counts, grep for contract implementations, cross-reference against ADRs and `CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md`.

---

## 1. Codebase Inventory

### Backend (Python) — ~13,000 LoC across `src/`

| Module | Files | Key Contents | Status |
|--------|-------|-------------|--------|
| `src/intake/` | 12 files | `packet_models.py` (430L), `decision.py` (2120L), `orchestration.py` (403L), `extractors.py`, `geography.py`, `normalizer.py`, `safety.py`, `strategy.py`, `validation.py`, `telemetry.py`, `config/agency_settings.py` | ✅ Active — core pipeline |
| `src/decision/` | 10 files | `hybrid_engine.py` (741L), `cache_key.py`, `cache_schema.py`, `cache_storage.py`, `health.py`, `telemetry.py`, `rules/` (7 rule modules) | ✅ Active — hybrid engine + rules |
| `src/suitability/` | 7 files | `catalog.py`, `scoring.py`, `context_rules.py`, `models.py`, `confidence.py`, `integration.py` | ✅ Active — Tier 1+2 implemented |
| `src/llm/` | 5 files | `base.py`, `openai_client.py`, `gemini_client.py`, `local_llm.py`, `agents/` (empty) | ✅ Active — LLM client layer |
| `src/analytics/` | 5 files | `engine.py` (136L), `metrics.py`, `models.py` (74L), `review.py` (123L) | ✅ Active — analytics module |
| `src/agents/` | 0 files | Empty directory | ⬜ Placeholder only |
| `src/config/` | 0 files | Empty directory | ⬜ Placeholder only |
| `src/adapters/` | 0 files | Empty directory | ⬜ Placeholder only |
| `src/pipelines/` | 0 files | Empty directory | ⬜ Placeholder only |
| `src/schemas/` | 0 files | Empty directory | ⬜ Placeholder only |
| `src/utils/` | 0 files | Empty directory | ⬜ Placeholder only |

### Spine API — `spine-api/`

| File | Lines | Purpose |
|------|-------|---------|
| `server.py` | 738 | FastAPI service: `/run`, `/trips`, `/stats`, `/scenarios`, `/settings`, `/insights`, `/reviews` |
| `persistence.py` | — | JSON file-backed trip/assignment/audit store |
| `run_state.py` | — | Run state machine with transition assertions |
| `run_events.py` | — | Event emission: started/completed/failed/blocked/stage transitions |
| `run_ledger.py` | — | Deterministic step ledger for run audit trails |

### Decision Rules — `src/decision/rules/`

| Rule | Purpose |
|------|---------|
| `budget_feasibility.py` | Budget vs. destination cost tables (~20 destinations) |
| `composition_risk.py` | Group composition risk (elderly+toddler combos) |
| `elderly_mobility.py` | Elderly traveler mobility constraints |
| `toddler_pacing.py` | Toddler pacing sensitivity |
| `visa_timeline.py` | Visa timeline risk detection |
| `additional_rules.py` | Supplementary rule pack |
| `not_applicable.py` | N/A classification |

### Frontend (Next.js + TypeScript) — ~13,700 LoC

| Area | Files | Purpose |
|------|-------|---------|
| `app/workspace/` | Trip workspace with `[tripId]` dynamic route | Trip detail view |
| `app/workbench/` | 8 files: DecisionTab, IntakeTab, PacketTab, PipelineFlow, SafetyTab, SettingsPanel, StrategyTab | Developer/operator pipeline inspector |
| `app/inbox/` | 1 file | Trip inbox/triage view |
| `app/owner/insights/` | — | Owner analytics dashboard |
| `app/owner/reviews/` | — | Owner review/approval queue |
| `app/api/` | 7 BFF routes: insights, pipeline, scenarios, spine, stats, trips, version | Backend-for-frontend API layer |
| `components/workspace/panels/` | 6 panels + tests: Decision, Intake, Output, Packet, Safety, Strategy | Workspace panel components |
| `types/spine.ts` | ~174L | Full spine contract types (stages, modes, states, budgets, prompts) |
| `types/governance.ts` | ~315L | Reviews, analytics, team, inbox, audit, settings types |
| `stores/` | workbench.ts, themeStore.ts | Zustand stores |
| `lib/` | spine-client.ts, design-system.ts, accessibility.tsx, url-state.ts | Shared utilities |
| `components/shell/` | Empty | ⬜ Placeholder only |

### Test Suite — `tests/`

28 test files covering:
- NB01/NB02/NB03 contract tests
- Decision policy conformance
- Hybrid engine + decision cache + decision rules
- Suitability scoring
- Follow-up mode, lifecycle/retention
- Geography + geography regression
- Budget decomposition, contradiction data model
- Block 2 spine hardening, block 3 extraction
- API contract, spine API contract
- Run lifecycle, run state
- Agency settings, settings behavioral
- E2E freeze pack, comprehensive v02, realworld scenarios
- LLM clients

**Last known status**: 315 tests passing (pre-session baseline — pytest not verified this session due to environment issue).

### Legacy App

- `app.py` (575L): Streamlit Operator Workbench — historical, superseded by Next.js frontend per `Docs/DISCUSSION_LOG.md` (2026-04-15 entry). Still in repo.

---

## 2. Architecture Decisions: Implemented vs. Paper-Only

### D1–D6 Thesis Deep Dive Decisions

| Decision | Document | Contract Designed? | In Code? | Blocker |
|----------|----------|-------------------|----------|---------|
| **D1**: Autonomy Gradient | `ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md` | ✅ `AgencyAutonomyPolicy` dataclass with per-`decision_state` gates | ❌ Not in `src/` — `AgencySettings` has no autonomy fields | **None** — can implement now on existing `AgencySettings` |
| **D2**: Free Engine Persona | `ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md` | ✅ Shared pipeline spec, empowerment framing | ❌ No audit intake path wired | D6 eval precision gate |
| **D3**: Sourcing Hierarchy | `ARCHITECTURE_DECISION_D3_SOURCING_HIERARCHY_2026-04-18.md` | ✅ `SourcingPolicy` with tier priority, margin floors, category overrides, supplier preferences | ❌ Not in `src/` — no vendor/supplier model exists | **Gap #01** (vendor/cost/sourcing) |
| **D4**: Suitability Depth | `ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` + `D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` | ✅ Three-tier scoring: deterministic → context → LLM | ⚠️ **Tier 1+2 implemented**, Tier 3 (LLM) not built | LLM integration wiring |
| **D5**: Override Learning | `ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md` | ✅ `OverrideEvent` with 3 categories, 2-phase learning, required rationale | ❌ Not in `src/` — no feedback bus, no override storage | **Gap #02** (persistence), **Gap #06** (customer lifecycle) |
| **D6**: Audit Eval Suite | `ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` | ✅ Manifest-driven `planned → shadow → gating` progression | ❌ `src/evals/` does not exist | **None** — can scaffold now |

### Cross-Project Patterns (from `CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md`)

| Pattern | Source | Status in Codebase | Blocker |
|---------|--------|--------------------|---------|
| **Quality Gates** at every pipeline stage | AdShot → WaypointOS | ❌ Not adopted — MVB check is implicit logic in `decision.py`, no typed gate contract | **None** — design decision needed |
| **3-Layer Confidence Scorecard** (data/judgment/commercial) | AdShot → WaypointOS | ❌ Not adopted — `DecisionResult` uses single `confidence_score: float` | **None** — can implement now |
| **Artifact Lineage** (`derived_from` on Slot) | AdShot → WaypointOS | ❌ Not adopted — `Slot` model has no `derived_from` field | **None** — can implement now |
| **Deterministic-First as Governing Principle** | AdShot → WaypointOS | ⚠️ Practiced but not codified — `V02_GOVERNING_PRINCIPLES.md` doesn't state this explicitly | **None** — doc update |
| Cache → Rule Graduation | WaypointOS → AdShot | ✅ Implemented in `src/decision/hybrid_engine.py` | — |
| Override Learning / Feedback Bus | WaypointOS → AdShot | ✅ Designed (D5) — not yet in code | Gap #02 |
| Manifest-Driven Eval Categories | WaypointOS → AdShot | ✅ Designed (D6) — not yet in code | — |
| Per-Tenant Policy Config | WaypointOS → AdShot | ✅ Designed (D1/D3) — not yet in code | — |

### Plugin System

| Item | Status |
|------|--------|
| Draft exploration | ✅ `PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md` |
| Architecture decision | ❌ **Pending** — draft needs formal decision |
| Plugin interfaces in code | ❌ None exist |
| First migration candidate | Identified: suitability Tier 3 (LLM scorer) |

### NB05/NB06 Evaluation Infrastructure

| Item | Status |
|------|--------|
| NB05 Golden Path design | ✅ Designed in `ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` |
| NB06 Shadow Mode design | ✅ Designed in same doc |
| `src/evals/` directory | ❌ Does not exist |
| Golden path fixtures | ❌ Not created |
| Shadow replay framework | ❌ Not created |

---

## 3. Gap Register vs. Implementation Status

All 17 gap deep-dives are **documented complete**. None are **implemented**.

| Gap | Priority | Deep-Dive | Implemented? | Blocks |
|-----|----------|-----------|-------------|--------|
| #01 Vendor/Cost/Sourcing | P0 | ✅ | ❌ | D3, all commercial features |
| #02 Data Persistence | P0 | ✅ | ❌ | D5, everything stateful |
| #03 Communication/Channels | P0 | ✅ | ❌ | Output delivery |
| #04 Financial State Tracking | P0 | ✅ | ❌ | Quote/payment state |
| #05 Cancellation/Refund | P1 | ✅ | ❌ | Cancellation workflow |
| #06 Customer Lifecycle | P1 | ✅ | ❌ | D5 Phase 2, retention |
| #07 LLM/AI Integration | P1 | ✅ | ⚠️ Partial (client layer exists, no orchestration) | Extraction quality |
| #08 Auth/Identity | P1 | ✅ | ❌ | Multi-tenant, roles |
| #09 In-Trip/Emergency | P2 | ✅ | ❌ | Active trip monitoring |
| #10 Document/Visa | P1 | ✅ | ❌ | Visa database |
| #11 Post-Trip/Feedback | P2 | ✅ | ❌ | Supplier scoring |
| #12 Analytics/Reporting | P2 | ✅ | ⚠️ Partial (analytics module scaffolded) | Owner dashboards |
| #13 Audit Trail | P1 | ✅ | ⚠️ Partial (run_events exists, no full audit trail) | Compliance |
| #14 Seasonality | P2 | ✅ | ❌ | Rate accuracy |
| #15 Insurance/TCS/GST | P2 | ✅ | ❌ | Tax compliance |
| #16 Configuration | P2 | ✅ | ⚠️ Partial (AgencySettings exists, limited scope) | Per-agency features |
| #17 Industry Blind Spots | P2-P3 | ✅ | ❌ | 20 items |

---

## 4. What Can Be Implemented NOW (Zero Gap Dependencies)

These items have completed architecture decisions and **no gap blockers**:

### A. 3-Layer Confidence Scorecard
- **Current**: `DecisionResult.confidence_score` is a single `float`
- **Target**: Structured `{data_quality: float, judgment_confidence: float, commercial_confidence: float}`
- **Location**: `src/intake/decision.py` (L212-231 area)
- **Why now**: No persistence needed. Immediately improves debuggability. Feeds into D1 autonomy gates.
- **Cross-ref**: `CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` Pattern #2

### B. Artifact Lineage on Slot
- **Current**: `Slot` in `packet_models.py` has no provenance tracking
- **Target**: Add `derived_from: list[str]` field
- **Location**: `src/intake/packet_models.py`
- **Why now**: Pure data model extension. Compounds with D5 override UX.
- **Cross-ref**: `CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` Pattern #3

### C. Quality Gate Contracts
- **Current**: MVB check is implicit logic inside `decision.py`
- **Target**: Typed `PipelineGate` protocol with `GateVerdict = proceed | retry | escalate | degrade`, formalized as `NB01CompletionGate` and `NB02JudgmentGate`
- **Location**: New protocol, referenced by `orchestration.py`
- **Why now**: No persistence needed. Wraps existing logic in typed contract.
- **Cross-ref**: `CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` Pattern #1

### D. D1 AutonomyPolicy Stub
- **Current**: `AgencySettings` has `target_margin_pct`, `brand_tone`, etc. — no autonomy fields
- **Target**: Add `AgencyAutonomyPolicy` as a field on `AgencySettings` with conservative defaults
- **Location**: `src/intake/config/agency_settings.py`
- **Why now**: Policy-as-config, not code branches. Decision pipeline can reference it immediately.
- **Cross-ref**: `ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`

### E. NB05/NB06 Scaffold
- **Current**: `src/evals/` doesn't exist
- **Target**: Create `src/evals/golden_path/` and `src/evals/shadow/` with base protocols and first fixture
- **Location**: New directory
- **Why now**: Framework only — doesn't need production data.
- **Cross-ref**: `ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md`

### F. Deterministic-First Governing Principle
- **Current**: Practiced but not codified in `V02_GOVERNING_PRINCIPLES.md`
- **Target**: Add explicit principle: "Deterministic rules first. LLM only when the answer requires world knowledge or semantic judgment."
- **Location**: `Docs/V02_GOVERNING_PRINCIPLES.md`
- **Why now**: Pure documentation. Validates existing hybrid engine pattern as standard.
- **Cross-ref**: `CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` Pattern #4

---

## 5. Pending Architecture Decisions

| Item | Draft/Discussion | Status | Next Step |
|------|-----------------|--------|-----------|
| Plugin System | `PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md` | Draft — needs formal ADR | Resolve: registration model, per-agency vs global enablement, relationship to quality gates |
| Customer+Trip Classification | Identified during D1 deep dive | No doc yet | Separate deep dive thread needed |
| D3 Open Questions (OQ-1/2/3) | In D3 ADR | Deferred — pending Gap #01 | Resolve when vendor model is designed |

---

## 6. Empty Directories (Planned Intent, No Code)

| Directory | Likely Purpose | Blocks On |
|-----------|---------------|-----------|
| `src/agents/` | Multi-agent orchestration (V02 NB layer agents) | Architecture decision |
| `src/config/` | Centralized config management | Gap #16 |
| `src/adapters/` | Source adapters (WhatsApp, PDF, URL intake) | Gap #03 |
| `src/pipelines/` | Pipeline composition / plugin execution | Plugin system decision |
| `src/schemas/` | Shared schema definitions | Consolidation decision |
| `src/utils/` | Shared utilities | Organic growth |
| `frontend/src/components/shell/` | App shell / navigation chrome | Frontend wave progression |

---

## 7. Recommended Next Threads (Dependency-Ordered)

### Thread A: Close No-Blocker Architecture Gap
Items A–F from Section 4. Zero gap dependencies, immediate compound value. Implements 4 cross-project patterns from AdShot and stubs 2 architecture decisions into running code.

### Thread B: Plugin System Architecture Decision
Formalize the draft into an ADR. Resolves the path for D4 Tier 3, audit rule plugins, and data-source plugins. Design conversation — no implementation blockers.

### Thread C: Gap #02 Persistence
The single biggest architectural unlock. Everything stateful (D5, Gap #06, Gap #13, analytics) is blocked here. Highest blast radius — should follow A+B so we know exactly what persistence needs to support.

---

*This assessment is point-in-time (2026-04-21). Update when implementation work changes the reality map.*
