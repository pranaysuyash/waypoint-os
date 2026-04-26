# Scenario Directory Status

**Date**: 2026-04-26
**Purpose**: Clarify what is in this directory, what is implemented, and what is exploratory.

---

## Scenario Categories in This Directory

| Category | Prefix/Pattern | Count | Pipeline Mapping | Implementation Status |
|---|---|---|---|---|
| **Core 20** (originally mapped) | `P1_*`, `P2_*`, `P3_*`, `S1S2_*` | 6 files | Mapped in `SCENARIOS_TO_PIPELINE_MAPPING.md` | Partially implemented in `src/intake/` and `src/decision/` |
| **Additional scenarios (early expansion)** | `ADDITIONAL_SCENARIOS_21_25.md` and similar | ~21 | Some mapped; see `SCENARIOS_TO_PIPELINE_MAPPING.md` lines 490–517 | Same as core |
| **Additional scenarios (domain expansion)** | `ADDITIONAL_SCENARIOS_[56-329+]_*.md` | ~314 | NOT mapped to pipeline | Not implemented — exploratory research inputs |
| **Frontier / edge-case scenarios** | `OE_*`, `SCENARIOS_315_*`, `SCENARIOS_316_*`, etc. | 8+ | NOT mapped to pipeline | Not implemented — stress-test / edge-case ideas |
| **Deep dives** | `AREA_DEEP_DIVE_*.md` | 16+ | Some referenced; not fully mapped | Not implemented — domain research |
| **Supporting docs** | `README.md`, `INDEX.md`, `EXECUTIVE_SUMMARY.md`, etc. | 8 | N/A | Reference documentation |

---

## What Is Exploratory / Not Implemented

The following domains are documented in scenario files but have ZERO code implementation:

- **Remote work / digital nomad travel** (ADDITIONAL_SCENARIOS_56, _74, _132, _152, _193, _277, _329, and WORK-001 through WORK-006)
- **Adventure sport** (ADDITIONAL_SCENARIOS_153, etc.)
- **Medical tourism** (ADDITIONAL_SCENARIOS_162, etc.)
- **Space / extreme frontier** (AREA_DEEP_DIVE_SPACE_EXTREME_FRONTIER.md)
- **Film production** (AREA_DEEP_DIVE_FILM_PRODUCTION.md)
- And many other domain areas

**Rule for agents**: Before implementing any scenario, verify the current codebase for the relevant extraction fields, decision rules, pipeline stages, and frontend types. If the code does not exist, do not assume it is "almost done" or "just needs wiring" — check explicitly.

---

## Implementation Decision Log

| Date | Decision | Affected Scenarios |
|---|---|---|
| 2026-04-26 | Remote work / digital nomad is **deferred** (not in launch scope) | ADDITIONAL_SCENARIOS_56, _74, _132, _152, _193, _277, _329, AREA_DEEP_DIVE_WORKCATIONS.md |
| 2026-04-26 | Bulk pipeline mapping of 287+ additional scenarios is **deferred** | All ADDITIONAL_SCENARIOS_100+ files |
| 2026-04-26 | `SCENARIO_HANDLING_SPEC.md` subsystem (route analysis, weather risk, activity suitability, StructuredRisk) is **deferred** | Full spec, no current plan |

---

## Quick Start for Agents

| If you need... | Read... |
|---|---|
| Core 20 scenario pipeline mapping | `SCENARIOS_TO_PIPELINE_MAPPING.md` |
| All scenario exploration files | This directory listing (340+ files) |
| What is actually implemented today | Search `src/`, `spine_api/`, `frontend/src/` for the relevant terms |

---

*Status: Updated 2026-04-26. This file is the source of truth for what is implemented vs exploratory in the personas_scenarios directory.*
