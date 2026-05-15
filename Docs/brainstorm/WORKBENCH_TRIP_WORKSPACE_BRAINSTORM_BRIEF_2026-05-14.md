# Brainstorm Brief: Workbench / Trip Workspace Architecture Split
**Date:** 2026-05-14 (~16:00)
**Method:** 9-role multi-agent brainstorm (wide-open-brainstorm skill)
**Status:** Complete — synthesis written, architecture decision made

---

## The Question

**Should Workbench narrow to creation + AI processing only? Should Trip Workspace become the single durable home for all trip-level work including Ops?**

The operational tension: `OpsPanel` (1404 lines) currently lives inside Workbench, which is conceptually a creation tool. Ops is not a creation activity — it is booking execution, document management, payment tracking, and supplier confirmation, all of which are permanently tied to the trip record. The question was whether to move Ops into Trip Workspace.

---

## Context Provided to Agents

**Architecture Plan:** `Docs/WORKBENCH_TRIP_WORKSPACE_ARCHITECTURE_PLAN_2026-05-14.md`

**Key code facts given to agents:**
- `OpsPanel.tsx` at `frontend/src/app/(agency)/workbench/OpsPanel.tsx` — 1404 lines, contains booking execution, document upload/review/extract, task state machine, payment tracking, confirmation panel, execution timeline
- `useWorkbenchStore()` coupling: OpsPanel reads `result_validation` from the Workbench Zustand store for readiness state; this is the main technical coupling to break
- Existing fallback: `trip?.validation` already provides the same readiness signal from the trip API response (lines 182–184 of OpsPanel)
- `Shell.tsx:141` already hides the word "Workbench" from users — the product nav was already renaming this
- `completedTripId` flow: after a Spine run, the operator is pushed to Trip Workspace but Ops is not there — they have to navigate back to Workbench
- `DecisionTab.tsx` (446 lines) and `StrategyTab.tsx` (106 lines) — not currently rendered in the tab list; existence is uncertain (dead code vs. staged/deferred)
- `getPostRunTripRoute()` in `routes.ts` — determines where operators land after Spine completes
- Trip Workspace currently has 7 tabs but no Ops tab

**Three options under consideration:**
- **Option A:** Keep Ops in Workbench, treat Trip Workspace as read-only
- **Option B (favored):** Move Ops to Trip Workspace at `/trips/[tripId]/ops`, sever Workbench coupling, deprecate Workbench Ops in the same or next release
- **Option C:** Redirect all Workbench trips to Trip Workspace immediately

---

## Role Definitions

Nine roles ran. Some roles had two independent agents to provide independent perspectives; composites documented in the files.

| Role | File | Note |
|------|------|-------|
| Operator | `ROLE_OPERATOR_2026-05-14.md` | Single agent — operator workflow map |
| Skeptic | `ROLE_SKEPTIC_2026-05-14.md` | Two agents, composite — found the UX regression and the `result_validation` concern |
| Executioner | `ROLE_EXECUTIONER_2026-05-14.md` | Two agents — Executioner #1 verified the coupling fallback exists; Executioner #2 found the sequencing risk |
| Cartographer | `ROLE_CARTOGRAPHER_2026-05-14.md` | Two agents — dispatch board + airport metaphors, navigation altitude model |
| Strategist | `ROLE_STRATEGIST_2026-05-14.md` | Single agent — product identity, time horizons |
| Archivist/Outsider | `ROLE_ARCHIVIST_OUTSIDER_GEMINI_2026-05-14.md` | Run via Gemini (external LLM, no codebase access) — fresh-eyes challenge |
| Future Self | `ROLE_FUTURE_SELF_2026-05-14.md` | Single agent — 24-month horizon |
| Champion | `ROLE_CHAMPION_2026-05-14.md` | Two agents, composite — cognitive jurisdiction problem |
| Trickster | `ROLE_TRICKSTER_2026-05-14.md` | Single agent — chrysalis metaphor |

---

## Decision Reached

**Option B: Move Ops to Trip Workspace. Sever Workbench coupling. Deprecate Workbench Ops in the same or following release.**

Key facts that determined the decision:
1. The `result_validation` coupling is already handled by `trip?.validation` fallback (Executioner #1 finding) — the blocking technical concern does not exist
2. Option B without a deprecation commitment creates permanent parallelism (Executioner #2 finding) — must commit to removal
3. Waypoint OS is a case management system with AI-accelerated intake, not a document generator — the architecture must reflect this (Strategist)
4. The product had already voted: Shell.tsx hiding "Workbench," nav doc calling it "New Inquiry," `completedTripId` pushing to Trip Workspace (Champion)

**What stays in Workbench:** New inquiry creation, Spine runs, AI re-processing of existing trips.

**Architecture plan:** `Docs/WORKBENCH_TRIP_WORKSPACE_ARCHITECTURE_PLAN_2026-05-14.md`

---

## Relationship to Later Brainstorm

This brainstorm answered: "Should we migrate Ops?" — answered YES.

The 10pm brainstorm on the same date answered: "What should Ops become now that we know it moves?" — see `OPS_NEXT_BRAINSTORM_BRIEF_2026-05-14.md` and `TRIP_WORKSPACE_OPS_MASTER_RECORD_BRAINSTORM_2026-05-14.md`.

---

## Deliverables Written

| File | Description |
|------|-------------|
| `Docs/brainstorm/roles/ROLE_OPERATOR_2026-05-14.md` | Operator workflow map |
| `Docs/brainstorm/roles/ROLE_SKEPTIC_2026-05-14.md` | Skeptic composite — UX regression risks |
| `Docs/brainstorm/roles/ROLE_EXECUTIONER_2026-05-14.md` | Executioner composite — kill test + sequencing risk |
| `Docs/brainstorm/roles/ROLE_CARTOGRAPHER_2026-05-14.md` | Cartographer composite — navigation architecture |
| `Docs/brainstorm/roles/ROLE_STRATEGIST_2026-05-14.md` | Strategist — product identity and time horizons |
| `Docs/brainstorm/roles/ROLE_ARCHIVIST_OUTSIDER_GEMINI_2026-05-14.md` | Archivist/Outsider via Gemini — memory design and "Living Dossier" |
| `Docs/brainstorm/roles/ROLE_FUTURE_SELF_2026-05-14.md` | Future Self — 24-month horizon |
| `Docs/brainstorm/roles/ROLE_CHAMPION_2026-05-14.md` | Champion composite — cognitive jurisdiction case |
| `Docs/brainstorm/roles/ROLE_TRICKSTER_2026-05-14.md` | Trickster — chrysalis metaphor, 5 architectural metaphors |
| `Docs/brainstorm/roles/ROLES_INDEX_WORKBENCH_TRIP_WORKSPACE_2026-05-14.md` | Per-role thesis + insights index |
| `Docs/brainstorm/BRAINSTORM_WORKBENCH_TRIP_WORKSPACE_2026-05-14.md` | Full synthesis |
| `Docs/brainstorm/WORKBENCH_TRIP_WORKSPACE_BRAINSTORM_BRIEF_2026-05-14.md` | This file — the brief |
