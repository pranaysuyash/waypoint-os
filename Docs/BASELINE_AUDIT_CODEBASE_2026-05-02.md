# Architecture Audit — Codebase Component Ratings

**Date**: 2026-05-02 | **Status**: Active Baseline | **Verified Against Code At**: 2026-05-02

**Purpose**: Rate every core pipeline component against first-principles architecture criteria. Identify specific issues, severity, and fix actions.

**Cross-Reference**: See `BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` for feature-level completeness. See `BASELINE_INDEPENDENT_ASSESSMENT_2026-05-02.md` for design-level analysis.

---

## Components Rated

| Component | Rating | Score | Key Issue |
|-----------|--------|-------|-----------|
| `packet_models.py` | 🟡 Adequate | 8/10 | Missing snapshot/clone, in-memory events only |
| `gates.py` | ✅ Strong | 9/10 | Missing NB03 output gate |
| `validation.py` | 🟡 Adequate | 7/10 | Hardcoded thresholds, no schema contract validation |
| `extractors.py` | 🔴 Concerning | 5/10 | **1,808-line monolith — critical refactor needed** |
| `decision.py` | 🔴 Concerning | 4/10 | **2,240-line monolith — critical refactor needed** |
| `hybrid_engine.py` | ✅ Strong | 8/10 | Needs prompt templating + LLM response validation |
| `suitability/` | 🟡 Adequate | 7/10 | Good architecture, missing utility scoring |
| `strategy.py` | 🟡 Adequate | 6/10 | Good framework, needs template filling + rendered output |
| `safety.py` | ✅ Strong | 9/10 | Correct structural approach, needs broader signal coverage |
| `orchestration.py` | 🟡 Adequate | 7/10 | Correct sequencing, missing timeout + persistent events |
| `agency_settings.py` | 🟡 Adequate | 7/10 | D1-aligned, needs Postgres + audit trail |
| `server.py` | 🔴 **Critical** | 3/10 | **3,535-line monolith — worst problem** |
| `types/spine.ts` | 🟡 Adequate | 6/10 | `ValidationReport` contract drift |

**Summary**: 2 Strong, 7 Adequate, 3 Concerning, 1 Critical.

---

## Detailed Per-Component Analysis

### 1. CanonicalPacket & Slot System (`packet_models.py`) — 🟡 8/10

**Strengths**: Strict facts/derived/hypotheses separation. Provenance on every value (`evidence_refs`, `derived_from`, `maturity`). Correct `operating_mode` placement. SubGroup/OwnerConstraint/Ambiguity as structural types. All dataclasses use `slots=True`. Audit trail via `_emit_event()`.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | `events` list in-memory only — grows unbounded, no persistence, no pruning | **HIGH** |
| 2 | No snapshot/clone — can't diff "packet at T1" vs "packet at T2" | **HIGH** |
| 3 | `decision_state` is `Optional[str]` — should be Literal type | Medium |
| 4 | `feedback` field has no structure — untyped dict | Medium |
| 5 | `to_dict()` uses `asdict()` — fragile for nested types | Medium |
| 6 | `add_contradiction()` legacy code path not cleaned up | Low |

**Actions**: Add `snapshot()` method (P0, 1 day). Wire events to persistent store (P0, 2 days). Make `decision_state` a Literal (P1, 0.5 day). Add `FeedbackEvent` dataclass (P1, 1 day). Clean legacy path (P1, 0.5 day).

---

### 2. Quality Gates (`gates.py`) — ✅ 9/10

**Strengths**: Three-layer autonomy model (Judgment→Policy→Human Action). `raw_verdict` preserved alongside `effective_action`. Full traceability on WHY gate decided. Hard safety invariant (`STOP_NEEDS_REVIEW→block`) enforced in code. Gate does NOT mutate decision state.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | No NB03→Output quality gate | Medium |
| 2 | `PipelineGate` Protocol never used | Low |
| 3 | Data density heuristic is arbitrary | Low |

**Actions**: Add NB03 output gate (P1, 2 days). Remove/implement PipelineGate Protocol (P2).

---

### 3. Validation (`validation.py`) — 🟡 7/10

**Strengths**: `INTAKE_MINIMUM` vs `QUOTE_READY` split. Legacy field detection. Derived-only guards. Typed `ValidationIssue`.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | Thresholds hardcoded — not agency-configurable | Medium |
| 2 | `QUOTE_READY` only 6 fields — too minimal | Medium |
| 3 | No runtime schema validation against `specs/` JSON | Medium |

**Actions**: Load thresholds from AgencySettings (P1, 2 days). Expand QUOTE_READY (P1, 1 day). Add schema contract validation step (P1, 1 day).

---

### 4. Extraction Pipeline (`extractors.py`) — 🔴 5/10

**Strengths**: Geography integration. Stop words / relation words / hint verbs for noise reduction. Stub signals marked honestly.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | **1,808 lines in single file** | **CRITICAL** |
| 2 | No extractor strategy pattern | **HIGH** |
| 3 | No confidence per extraction rule | Medium |

**Actions**: Split into domain modules: `date_extractor.py`, `destination_extractor.py`, `budget_extractor.py`, `composition_extractor.py`, `preference_extractor.py` (P0, 3-4 days). Define BaseExtractor protocol (P0, 1 day).

---

### 5. Decision Engine (`decision.py`) — 🔴 4/10

**Strengths**: Hybrid engine integration. Comprehensive risk flag generation. Contradiction detection.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | **2,240 lines in single file** | **CRITICAL** |
| 2 | Gap detection and decision making not separated | **HIGH** |
| 3 | `DecisionResult` naming collision with hybrid_engine | Medium |
| 4 | Feasibility explainability weak | Medium |

**Actions**: Split into `gap_detector.py` + `feasibility_engine.py` + `confidence_engine.py` + `decision_router.py` (P0, 3-4 days). Rename collision (P1, 0.5 day). Add traceable evidence to feasibility (P1, 2 days).

---

### 6. Hybrid Decision Engine (`hybrid_engine.py`) — ✅ 8/10

**Strengths**: Clean cache→rules→LLM→default flow. Cost tracking per path. Structured schema templates. Safe defaults. Telemetry + health checker + LLM guard integration. Extensible rule registration.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | LLM prompts are hardcoded strings — no template files | Medium |
| 2 | LLM responses not validated against schema before caching | Medium |
| 3 | Module-level globals (`_hybrid_engine_instance`) not thread-safe | Low |
| 4 | `DecisionResult` naming collision with intake/decision.py | Medium |

**Actions**: Validate LLM responses against schema (P0, 1 day). Move prompts to template files (P1, 2 days). Make rule registration data-driven (P1, 2 days). Rename DecisionResult collision (P1, 0.5 day).

---

### 7. Suitability Engine (`suitability/`) — 🟡 7/10

**Strengths**: Clean module separation (models/scoring/context_rules/integration/catalog). TAG_RULES declarative mapping. Most-conservative-tier safety. Intensity scoring per participant type. Pace preference normalization with clamping.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | Static catalog hardcodes 17 activities — won't scale | **HIGH** |
| 2 | `assess_activity_suitability()` truncates to 10 activities | **HIGH** |
| 3 | Per-person utility % not computed (thesis feature) | **CRITICAL** |
| 4 | Wasted spend not calculated (thesis feature) | **CRITICAL** |
| 5 | SuitabilityContext not populated from packet data | Medium |
| 6 | Tier 2 rules only cover 2 specific risks | Medium |

**Actions**: Implement per-person utility scoring (P0, 2-3 days). Implement wasted spend calculation (P0, 1 day). Remove `[:10]` truncation (P0, 0.5 day). Make catalog loadable from DB (P1, 2 days). Populate SuitabilityContext from packet (P1, 1 day).

---

### 8. Strategy & Output (`strategy.py`) — 🟡 6/10

**Strengths**: `QuestionWithIntent` carries purpose metadata. Mode-specific goals/openings for all 8×5 combinations. Tone scaling by confidence + sentiment override. Constraint-first question ordering. `to_traveler_dict()` structural safety.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | Mode logic in if/elif chains — not strategy pattern | Medium |
| 2 | `get_mode_specific_goal()` and `get_mode_specific_opening()` duplicate matrix | Medium |
| 3 | Openings are hardcoded English — no localization, no agency voice | Medium |
| 4 | `PromptBundle` is text-only — no structured option rendering | **CRITICAL** |
| 5 | No template filling from packet data — strategy is generic, not personalized | **HIGH** |

**Actions**: Replace if/elif chains with data-driven matrix (P0, 2 days). Implement template filling (P0, 2 days). Implement rendered option output (P0, 5-7 days). Add localization (P1, 3-4 days).

---

### 9. Safety Sanitization (`safety.py`) — ✅ 9/10

**Strengths**: Structural sanitization (data not available, not hidden). SanitizedPacketView intentionally excludes internal concepts. Separate FORBIDDEN / INTERNAL_ONLY / TRANSFORM_REQUIRED classifications. Visibility-based constraint filtering. Financial language scrubbing. Dual-phase leakage check.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | `traveler_safe_signals` only includes ONE signal | **HIGH** |
| 2 | Forbidden concepts hardcoded — not data-driven | Medium |
| 3 | No structured data leakage scanning | Medium |

**Actions**: Expand traveler_safe_signals (P0, 1 day). Make forbidden concepts data-driven (P1, 0.5 day). Add structured data scanning (P1, 1 day).

---

### 10. Orchestration (`orchestration.py`) — 🟡 7/10

**Strengths**: Clean sequential pipeline. OTel spans. Stage callbacks. Single `SpineResult`. Early exit on gate failures. Fixture compare framework.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | No pipeline timeout | Medium |
| 2 | Audit event pre_state is placeholder ("actual packet delta") | Medium |
| 3 | Fixture compare in production code — should be in evals/ | Low |
| 4 | `_obj_to_dict()` is heuristic serialization — fragile | Medium |

**Actions**: Add pipeline timeout (P1, 1 day). Fix pre_state delta (P1, 1 day). Move fixture compare to evals/ (P1, 0.5 day).

---

### 11. Agency Settings (`agency_settings.py`) — 🟡 7/10

**Strengths**: D1-aligned `AgencyAutonomyPolicy`. `__post_init__` enforces STOP_NEEDS_REVIEW = block. `effective_gate()` with mode override precedence. Legacy migration support. SQLite persistence.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | SQLite vs PostgreSQL — two databases | Medium |
| 2 | No settings audit trail | Medium |
| 3 | No feature flags per agency | Medium |
| 4 | Legacy fields confuse D1 model | Low |

**Actions**: Migrate to PostgreSQL (P1, 2 days). Add settings audit trail (P1, 1 day). Add feature flags (P2, 2 days).

---

### 12. Spine API Server (`server.py`) — 🔴 CRITICAL (3/10)

**Strengths**: Comprehensive REST surface. Auth dependencies. Background task support. OTel instrumentation.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | **3,535 LINES IN SINGLE FILE** | **CRITICAL** |
| 2 | Routes defined inline despite `routers/` directory existing | **CRITICAL** |
| 3 | Concerns mixed: OTel, auth, DB, business logic, routes | **CRITICAL** |
| 4 | JSON persistence still active alongside SQLAlchemy | **HIGH** |
| 5 | Business logic in routes, not service layer | Medium |

**Actions**: Decompose into routers: trips.py, runs.py, timeline.py, dashboard.py, suitability.py, followups.py, analytics.py (P0, 3-4 days). Extract OTel to core/observability.py (P0, 0.5 day). Extract business logic to services/ (P0, 2-3 days).

---

### 13. Frontend Types (`types/spine.ts`) — 🟡 6/10

**Strengths**: Re-exports generated types. Separate frontend-only types. Comprehensive coverage.

**Issues**:
| # | Issue | Severity |
|---|-------|----------|
| 1 | `ValidationReport` has BOTH `is_valid` AND `status` — contract drift | **HIGH** |
| 2 | `SuitabilityFlag` and `SuitabilityFlagData` confusingly similar names | Medium |

**Actions**: Resolve ValidationReport contract drift — verify against real API (P0, 1 day). Rename SuitabilityFlagData → PipelineSuitabilityFlag (P1, 0.5 day).

---

## Cross-Cutting Issues

### Monolith Problem (CRITICAL)
7,583 lines in 3 files that should be 20+: `server.py` (3,535), `decision.py` (2,240), `extractors.py` (1,808). Blocks testability, maintainability, all new feature work.

### Dual Persistence (HIGH)
JSON files AND PostgreSQL used side-by-side. Different consistency models. No unified migration path in code.

### Naming Collision (Medium)
`DecisionResult` exists in both `intake/decision.py` and `decision/hybrid_engine.py` — different types, same name.

### Hardcoded vs Data-Driven (Medium)
Validation thresholds, suitability rules, activity catalog, forbidden terms, LLM prompts, strategy openings — all hardcoded. None agency-configurable.

---

*Cross-reference with `BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` for feature-level state and `BASELINE_MASTER_ACTION_PLAN_2026-05-02.md` for dependency-ordered fix sequence.*