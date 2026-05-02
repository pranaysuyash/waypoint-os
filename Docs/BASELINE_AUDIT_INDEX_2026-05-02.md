# Baseline Audit Index — May 2, 2026

This is the canonical index of all baseline audit documents created on 2026-05-02. These docs collectively form the architectural and feature baseline against which all future implementation work should be measured.

**Previous mega-doc** (`ARCHITECTURE_BASELINE_AUDIT_2026-05-02.md`) has been split into the focused docs below. The old file is retained as `ARCHITECTURE_BASELINE_AUDIT_2026-05-02.md` — [ARCHIVED: superseded by this index and the docs below]

---

## The Baseline Docs

| # | Document | Purpose | Read When |
|---|----------|---------|-----------|
| 1 | `BASELINE_AUDIT_CODEBASE_2026-05-02.md` | Per-component architecture ratings (13 components). Specific issues, severity, fix actions. | Planning refactors, onboarding new devs |
| 2 | `BASELINE_INDEPENDENT_ASSESSMENT_2026-05-02.md` | First-principles architectural analysis. Missing primitives. Design smells. Vision vs code gaps. | Evaluating architectural decisions, avoiding design debt |
| 3 | `BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` | 20 feature areas mapped against vision. Current state, gaps, build sequence. **Overall score: 24.5%** | Prioritizing features, understanding what works vs what doesn't |
| 4 | `BASELINE_DOCUMENTATION_HEALTH_2026-05-02.md` | 44 doc issues found (5 Critical, 9 High, 16 Medium, 14 Low). Root causes and fix actions. | Cleaning up docs, understanding doc reliability |
| 5 | `BASELINE_MASTER_ACTION_PLAN_2026-05-02.md` | Consolidated 49-item dependency-ordered plan across 7 phases (A→G). ~4-5 months total. | Sprint planning, tracking progress |

---

## Quick Reference: Key Numbers

| Metric | Value |
|--------|-------|
| Overall feature completeness | **24.5%** (49/200 across 20 areas) |
| Core pipeline LOC | ~7,278 (intake + decision/hybrid) |
| Total backend LOC | ~10,813 (with spine_api) |
| Test functions | ~1,104 across 71 files |
| Monolithic files needing refactor | 3 (`server.py` 3,535L, `decision.py` 2,240L, `extractors.py` 1,808L) |
| Architecture: Strong components | 2 (gates.py, safety.py) |
| Architecture: Critical components | 1 (server.py) |
| Doc issues found | 44 |
| Total action items | 49 |
| Estimated calendar to completion | ~89-106 working days |

---

## How to Use These Docs

1. **Before any new feature**: Read `BASELINE_FEATURE_COMPLETENESS_AUDIT` — is this feature area ready to be built on? What prerequisites are missing?
2. **Before any refactor**: Read `BASELINE_AUDIT_CODEBASE` — what's the current rating? What specific issues exist?
3. **Before any architectural decision**: Read `BASELINE_INDEPENDENT_ASSESSMENT` — what primitives are missing? What design smells should be avoided?
4. **When updating docs**: Read `BASELINE_DOCUMENTATION_HEALTH` — what patterns caused doc rot before? Follow standardized header format.
5. **For planning**: Read `BASELINE_MASTER_ACTION_PLAN` — what phase are we in? What's next in dependency order?

---

## Maintenance Protocol

1. **These docs are the baseline.** They should be updated when:
   - A component is refactored (update AUDIT_CODEBASE)
   - A feature ships (update FEATURE_COMPLETENESS_AUDIT)
   - An architectural decision is made (update INDEPENDENT_ASSESSMENT)
   - Documentation is cleaned up (update DOCUMENTATION_HEALTH)
   - Phases are completed (update MASTER_ACTION_PLAN)

2. **Header format for all future docs**:
   ```
   # Title
   **Date**: YYYY-MM-DD | **Status**: Planning/Active/Complete/Stale | **Owner**: (name)
   **Last Verified Against Code At**: YYYY-MM-DD
   ```

3. **Single source of truth for metrics**: This index. Test counts, line counts, feature scores — all canonical here. Update here first.

---

*This index — `BASELINE_AUDIT_INDEX_2026-05-02.md` — is the entry point for the May 2, 2026 architecture and feature baseline.*