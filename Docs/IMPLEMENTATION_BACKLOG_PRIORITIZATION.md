# Implementation Backlog & Prioritization

**Date**: Wednesday, April 22, 2026
**Status**: Strategic Planning

This document consolidates all planned features, UX improvements, and architectural gaps identified across current explorations (Front-end, Decision Engine, Analytics, and Traceability).

---

## 1. Prioritization Matrix

| ID | Feature / Component | Category | Priority | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **P0-01** | **Suitability Audit (Intake)** | Decision Logic | Critical | Prevents un-suitable trips from being created; Fixes "Elderly Pilgrimage" scenario. |
| **P0-02** | **Decision Timeline Log** | Traceability | Critical | Solves "State Blindness"; provides an immutable audit trail. |
| **P1-01** | **Provenance Sidebar** | UX / Transparency | High | Critical for agentic trust; surfaces the "Why" behind AI evidence. |
| **P1-02** | **Performance-to-Packet Drill-Down** | Analytics | High | Enables operational QA; converts charts into actionable insight paths. |
| **P2-01** | **Settings Dashboard** | Ops/Config | Medium | Provides UI for agency owners to control Autonomy gates without JSON/API. |
| **P2-02** | **Contextual Knowledge Panel** | UX / Intelligence | Medium | Surfacing agency playbooks dynamically; reduces operator error. |
| **P2-03** | **Scenario Replay Mode** | Dev / QA | Medium | Allows developers/QA to seed the store with `data/fixtures/` for audit. |
| **P3-01** | **Customer History Sidebar** | UX / Personalization | Low | Longitudinal context; nice-to-have for advanced agent performance. |

---

## 2. Implementation Details

### Critical Foundation (P0)
- **Suitability Audit**: Before a trip lands in the `Workspace`, the `Intake` phase must run an explicit check against suitability rules. Risks identified here must be "Hard Blockers" for operator review.
- **Decision Timeline**: Implement a JSONL-based logger in `src/intake/orchestration.py`. Every `SpineResult` transition must be logged to `data/logs/trips/[tripId].jsonl` with timestamps, stage, and state changes.

### Traceability & Audit (P1)
- **Provenance Sidebar**: Requires adding `evidenceRef` pointers to the JSON output of the backend `Packet`.
- **Analytics Drill-down**: Phase A involves linking `TeamPerformanceChart` agent rows to a dedicated `/owner/insights/[agentId]` route.

### Config & Context (P2)
- **Settings Dashboard**: Build the UI to consume the `/api/settings` endpoint. Focus on Autonomy Policy visualization first.
- **Scenario Replay**: Create a "Debug Header" in the workspace that allows manual injection of fixture files.

---

## 3. Guiding Philosophy for Implementation
- **Additive**: Do not refactor existing structures. Extend the current `Spine` to log events.
- **Traceable**: Every action must be logged and linkable to source evidence.
- **Actionable**: No analytics/dashboards should be built without a clear, corresponding operational action.

---

## 4. Next Steps
1.  **Finalize Priorities**: Review the matrix above. Do we agree on the P0-P1 order?
2.  **Define Next Action**: Once prioritized, I will generate an implementation plan for the top item (e.g., the Suitability Audit).

*Note: This is a living document. As we proceed, we will mark items as complete and add new requirements.*
