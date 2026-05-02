# Documentation Health Audit

**Date**: 2026-05-02 | **Status**: Active Baseline | **Docs Audited**: ~60 of 421+

**Method**: Three parallel audits of core policy/spec docs (~20), discussion/status/roadmap docs (~15), wave/audit/exploration docs (~25).

---

## Findings Summary

| Severity | Count |
|----------|-------|
| Critical | 5 |
| High | 9 |
| Medium | 16 |
| Low | 14 |
| **Total** | **44** |

---

## CRITICAL (5)

| # | File | Issue |
|---|------|-------|
| C1 | `FROZEN_SPINE_STATUS.md:142` | **"127+ tests passing."** Actual: 1,104. 9x understatement. Treated as frozen spine authority. From April 15. |
| C2 | `AUDIT_AND_INTELLIGENCE_ENGINE.md` | **Reads as working feature spec.** No date, no status. Describes "Wasted Spend Detection," "Fit-Score Framework," "Market Flywheel" — all unimplemented (P2). |
| C3 | `IMPLEMENTATION_BACKLOG_PRIORITIZATION.md:14` | **"P0-01 - Suitability Audit" still listed.** Suitability Tier 1+2 was done by April 18. Backlog from April 22 never updated. |
| C4 | `PHASE_3456_COMPLETION_HANDOFF.md:6,124` | **"960 tests" — math doesn't work.** 251 new + 42 baseline = 293, not 960. With 40 pre-existing failures, "Launch Ready: Yes" is not credible. |
| C5 | `dashboard_homepage_ui_2026-04-29.md:462` | **References non-existent file**: `calendar_availability_2026-04-29.md`. Same in `itinerary_builder`. |

---

## HIGH (9)

| # | File | Issue |
|---|------|-------|
| H1 | Multiple docs | **"No Streamlit path."** But `app.py` (575L) still in repo. Streamlit in `pyproject.toml`. 17+ day contradiction. |
| H2 | `Sourcing_And_Decision_Policy.md:19` | **Uses `PRESENT_BRANCHES`.** Actual state is `BRANCH_OPTIONS`. Direct contradiction. |
| H3 | April 28 audits (7 docs) | **Line counts stale.** All say `server.py` = 2,644L. Actual: 3,535L (+34%). Audits stale when written. |
| H4 | April 27-28 audits | **Test file count inconsistent.** Spread: 53→71 across 5+ docs. Actual: 71. |
| H5 | `FRONTEND_WORKFLOW_CHECKLIST_2026-04-16.md` | **All 23 tasks unchecked, status "Planned."** Frontend is live. Predates Next.js work. |
| H6 | `AGENTIC_PIPELINE_CODE_AUDIT_2026-04-27.md` | **Line number references stale.** `server.py:560` — file grew 900+ lines since. |
| H7 | April 27 audits | **Both claim `src/agents/` is empty.** `recovery_agent.py` exists. |
| H8 | `IMPLEMENTATION_PLAN_D001_D003_2026-04-23.md` | **Should have been deleted.** Handoff explicitly says delete. File still there. |
| H9 | `PHASE2_CALL_CAPTURE.md:214,278` | **(a) BFF route misclassified as backend. (b) "No DB changes needed" — migration exists.** |

---

## MEDIUM (16)

Key themes:
- **Docs-as-plans never graduated** (HYBRID_DECISION_ARCHITECTURE checklist items unchecked but implemented)
- **Proposed architecture never built**: `src/ports/`, `src/frontier/`, `src/analytics/calculations.py`, `PHASE_B_MERGE_CONTRACT.md` — all referenced but don't exist
- **Vision docs without status markers**: `UNIFIED_COMMUNICATION_STRATEGY.md`, `SYSTEM_INTEGRITY_PLAN.md` — describe features with zero implementation
- **INDEX.md**: Links to superseded doc, missing D6 and replacement docs
- **Route references stale**: `/workspace/[tripId]/` → actual is `/(agency)/trips/[tripId]/`
- **Severity inconsistency**: Same issues rated differently across audit docs
- **Component naming drift**: `RecoveryHeader.tsx` in docs vs `FeedbackPanel.tsx` in code — identified but unresolved

---

## LOW (14)

Minor issues: typos (8-segment version string `^7.0.0.0`), self-referencing doc listing itself as artifact, Next.js 14 claimed vs 16 actual, Streamlit/rich flagged as potentially unused (never verified), status docs from April 15 completely obsolete.

---

## Root Causes

1. **Audit Parallelism Without Sync**: 7 April 28 audits written simultaneously against growing code. Different HEAD states.
2. **Docs-as-Plans Never Graduated**: Planning docs with action items — implementation happened, plans never updated.
3. **Streamlit Zombie**: Migration decided April 15. `app.py` still exists May 2. Multiple docs claim "no Streamlit" — contradiction.
4. **No Doc Owner**: No single doc canonical for "what's implemented." 4+ docs attempt coverage — all stale.
5. **Test Count as Vanity Metric**: Cited in 6+ docs as quality evidence. No two agree on the number (53→71 files, 127→1,104 functions).

---

## Recommended Actions

### Immediate (P0)

| Action | Effort |
|--------|--------|
| Update `FROZEN_SPINE_STATUS.md` test count | 5 min |
| Add status header to `AUDIT_AND_INTELLIGENCE_ENGINE.md` | 5 min |
| Delete `IMPLEMENTATION_PLAN_D001_D003_2026-04-23.md` | 5 min |
| Update backlog — mark P0-01 done | 5 min |
| Resolve Streamlit: delete app.py or update docs | 30 min |

### Short-Term (P1)

| Action | Effort |
|--------|--------|
| Add status headers to vision-only docs | 30 min |
| Update INDEX.md — fix links | 30 min |
| Resolve PHASE_B_MERGE_CONTRACT — create or defer | 30 min |
| Standardize doc headers (Date, Status, Owner, Verified At) | 1 day |
| Create Docs/README.md as doc map | 1 day |

### Medium-Term (P2)

| Action | Effort |
|--------|--------|
| Archive obsolete docs to `archives/` | 1 day |
| Establish single truth for test counts | 1 day |

---

*Cross-reference with `BASELINE_AUDIT_CODEBASE_2026-05-02.md` for code issues and `BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` for feature gaps.*