# Master Action Plan — Dependency-Ordered

**Date**: 2026-05-02 | **Status**: Active Baseline

**Source**: Consolidated from `BASELINE_AUDIT_CODEBASE`, `BASELINE_FEATURE_COMPLETENESS_AUDIT`, `BASELINE_DOCUMENTATION_HEALTH`, and `BASELINE_INDEPENDENT_ASSESSMENT`.

---

## Phase A: Immediate Documentation Fixes (Now — ~1 hour)

| # | Action | Effort |
|---|--------|--------|
| A1 | Update `FROZEN_SPINE_STATUS.md` test count to 1,104 | 5 min |
| A2 | Add status header to `AUDIT_AND_INTELLIGENCE_ENGINE.md`: "⚠️ PLANNING — Not implemented" | 5 min |
| A3 | Delete `IMPLEMENTATION_PLAN_D001_D003_2026-04-23.md` (handoff instructed) | 5 min |
| A4 | Update `IMPLEMENTATION_BACKLOG_PRIORITIZATION.md` — mark P0-01 done | 5 min |
| A5 | Resolve Streamlit zombie: delete `app.py` or update docs to acknowledge it | 30 min |

---

## Phase B: Documentation Cleanup (This Week — ~4 days)

| # | Action | Effort |
|---|--------|--------|
| B1 | Add status headers to vision-only docs | 30 min |
| B2 | Update `INDEX.md` — fix superseded links, add D6 entry, add new baseline docs | 30 min |
| B3 | Resolve `PHASE_B_MERGE_CONTRACT` — create or mark DEFERRED | 30 min |
| B4 | Standardize doc headers: Date, Status (Planning/Active/Complete/Stale), Owner, Verified At | 1 day |
| B5 | Create `Docs/README.md` as doc map | 1 day |
| B6 | Archive clearly obsolete docs to `archives/` | 1 day |
| B7 | Verify streamlit/rich usage, remove dead deps | 30 min |

---

## Phase C: Critical Code Refactors (Next 2 Weeks — ~16-18 days)

Monolithic files blocking all new feature work:

| # | Action | Effort |
|---|--------|--------|
| C1 | **Decompose `server.py`** into routers (trips/runs/timeline/dashboard/suitability/followups/analytics) + extract OTel to `core/observability.py` | 3-4 days |
| C2 | **Split `extractors.py`** into domain modules (date/destination/budget/composition/preference) + define BaseExtractor protocol | 3-4 days |
| C3 | **Split `decision.py`** into gap_detector / feasibility_engine / confidence_engine / decision_router | 3-4 days |
| C4 | Add snapshot/clone to `CanonicalPacket` | 1 day |
| C5 | Wire events to persistent store (not in-memory) | 2 days |
| C6 | Add pipeline timeout | 1 day |
| C7 | Rename `DecisionResult` collision (hybrid_engine → HybridDecisionResult) | 0.5 day |
| C8 | Resolve `ValidationReport` contract drift in frontend types | 0.5 day |
| C9 | Validate LLM responses against schema before caching | 1 day |

---

## Phase D: Missing Primitives (Weeks 3-4 — ~21-25 days)

Thesis-critical features:

| # | Action | Effort |
|---|--------|--------|
| D1 | **Implement per-person utility scoring** — utility % per activity per participant | 2-3 days |
| D2 | **Implement wasted spend calculation** — cost × (1 - utility) per participant | 1 day |
| D3 | **Implement rendered itinerary option output** — structured ItineraryOption model with days/costs/suitability/trade-offs | 5-7 days |
| D4 | **Implement template filling in strategy** — openings reference actual packet data | 2 days |
| D5 | Source adapter protocol + PDF extraction adapter (unlocks D2 audit mode) | 3-4 days |
| D6 | Build numeric feasibility model (replace hardcoded 20-destination table) | 3-4 days |
| D7 | Make activity catalog loadable from DB (agency-configurable) | 2 days |
| D8 | Make validation thresholds agency-configurable | 2 days |
| D9 | Add NB03 output quality gate | 2 days |

---

## Phase E: Hardening (Weeks 5-6 — ~16 days)

| # | Action | Effort |
|---|--------|--------|
| E1 | Migrate agency settings from SQLite to PostgreSQL | 2 days |
| E2 | Add settings audit trail | 1 day |
| E3 | Add feature flag system (per-agency enable/disable) | 2 days |
| E4 | Move LLM prompts to template files | 2 days |
| E5 | Add structured data leakage scanning | 1 day |
| E6 | Add `SourcingPolicy` abstraction (even without supplier data) | 2 days |
| E7 | Add hard/soft constraint classification | 2 days |
| E8 | Make pipeline composition configurable | 2 days |
| E9 | Implement idempotent pipeline execution | 2 days |

---

## Phase F: Features on Clean Foundation (Weeks 7-10 — ~32-43 days)

| # | Action | Effort |
|---|--------|--------|
| F1 | D2: Trip Audit mode end-to-end (PDF extraction → audit → fit score → output) | 5-7 days |
| F2 | Dynamic question router (iterative, priority-driven) | 3-4 days |
| F3 | Mode-specific NB03 builders (audit builder, emergency builder) | 4-5 days |
| F4 | WhatsApp/email output delivery channels | 4-5 days |
| F5 | Consumer presentation_profile (D2 consumer surface) | 2 days |
| F6 | D5: Override feedback bus (capture → storage → pattern detection) | 4-5 days |
| F7 | D4 Tier 3: LLM contextual suitability scorer (behind deterministic tiers) | 3-4 days |
| F8 | D6: Eval harness scaffold (manifest runner, golden paths, category gating) | 3-4 days |
| F9 | Revision graph / diff model (snapshots → diff → rationale timeline) | 3-4 days |
| F10 | Operator override protocol with full audit trail | 3-4 days |

---

## Phase G: Scale & Operations (Weeks 11+ — Future)

| # | Action |
|---|--------|
| G1 | Visa requirement database + checklist generator |
| G2 | Financial state tracking (quote → collected → confirmed) |
| G3 | Traveler portal (basic) |
| G4 | Analytics dashboards (owner view) |
| G5 | Booking coordination (readiness checklist, confirmation parser) |
| G6 | In-trip operations dashboard |
| G7 | Post-trip memory + preference learning |
| G8 | Production hardening (Redis, rate limiting, CI/CD) |
| G9 | Agency marketplace / network effects (Phase Z — post-revenue) |

---

## Grand Total

| Phase | Work | Calendar |
|-------|------|----------|
| A: Immediate fixes | 5 items | ~1 hour |
| B: Doc cleanup | 7 items | ~4 days |
| C: Critical refactors | 9 items | ~16-18 days |
| D: Missing primitives | 9 items | ~21-25 days |
| E: Hardening | 9 items | ~16 days |
| F: Features | 10 items | ~32-43 days |
| **Total** | **49 items** | **~89-106 working days (~4-5 months)** |

---

## What This Plan Assumes

1. **Phases are sequential** — each unlocks the next. C (refactors) before D (features on clean code). D before F (features on clean foundation).
2. **Scope is single developer** — calendar estimates are for one person. Could parallelize some Phase C items.
3. **Docker is not a blocker** — local dev uses `uv run uvicorn`. Dockerfile is a 15-min fix when needed for Render/Fly.
4. **Pilot agency is the forcing function** — Phase D (output rendering) is what a pilot agency needs to see.

## What Changes When a Pilot Agency Signs

1. Phase C (refactors) remains mandatory — can't add features to monoliths.
2. Phase D (rendered output) becomes urgent — agency needs to see itineraries, not text blobs.
3. Phase F (D2 audit mode) becomes the GTM wedge — lead gen depends on it.
4. Phase G (operations) gets deprioritized — booking coordination matters after booking happens.

---

*Cross-reference with `BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` for which features unlock which value props.*