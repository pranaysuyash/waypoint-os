# The Exploration Frontier

**Date**: Wednesday, April 22, 2026
**Purpose**: A raw, un-filtered repository for ideas, experiments, and "what if" scenarios. This document is a safe space for brainstorming before they are vetted for the Master Roadmap.

---

## 1. Raw Ideas & Experimental Concepts

- **[Architecture] BFF + Modular Monolith Topology**: Current system is neither a pure monolith nor microservices. It is a Next.js BFF plus FastAPI backend modular monolith, with future extraction candidates around workers, integrations, documents, analytics, and public traveler collection. See `Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md`.
- **[Concept] Agent-Role Swapping**: Allow operators to "swap" the persona of an agent dynamically (e.g., "Take your current plan and explain it to a budget-conscious traveler instead of the current luxury profile").
- **[Concept] Automatic 'Next-Action' Nudging**: AI detects when a trip has been idle in a stage for X hours and suggests an "Internal Note" to nudge the process forward.
- **[Concept] Visual State Replay**: Rather than just logs, create a "Video-Game Style Replay" button that iterates through the `TimelinePanel` steps at 0.5s intervals, allowing the operator to see the AI's "thought" progression visually.
- **[Concept & Engineering] KDD v0.1: Fuzzy Feature Vector Clustering (`HDBSCAN` / Gower Distance) & Automated Rule Promotion Loop**: Upgrade the `exact-match-v1` override clustering algorithm (`src/analytics/kdd/clustering.py`) to a density-based fuzzy distance metric over `(flag, action, destination, party_size, duration_days)`. Prevents high-value domain overrides from dropping into the noise floor and implements a closed-loop `POST /kdd/clusters/{id}/promote` endpoint to convert verified operator patterns into automated suitability policy overrides. See `Docs/audit/KDD_OVERRIDE_MINING_AND_FEEDBACK_LOOP_AUDIT_2026-07-13.md`.

---

## 2. Status of Ideas

| Idea | State | Discovery/Next Step |
| :--- | :--- | :--- |
| **BFF + Modular Monolith Topology** | Explored | Adopt as current architecture label; next step is route/service modularization, persistence consolidation, and worker-boundary design. |
| **Agent-Role Swapping** | Raw | Analyze `SessionStrategy` requirements for persona-injection. |
| **Next-Action Nudging** | Raw | Feasibility study: can this be a trigger in the `Orchestrator`? |
| **Visual State Replay** | Experimental | Needs exploration of `PacketPanel` state rehydration (the "Time Travel" feature). |
| **Collaborative Agents** | Raw | Requires multi-agent orchestration infrastructure. |
| **KDD v0.1: Fuzzy Clustering & Rule Promotion** | Explored & Audited | Implement tenant isolation in `spine_api/routers/kdd.py` and benchmark agglomerative Gower clustering across historical overrides (`OverrideStore`). |

---

## 3. How to use this doc:
1. **Dumping**: When you have an idea, add a bullet point here immediately. Don't worry about whether it's "architecturally sound" or "roadmap-ready."
2. **Review**: Periodically (during our sessions), we will review this list. 
3. **Promotion**: If an idea proves valuable, we will flesh it out into a technical directive and move it to the `MASTER_PHASE_ROADMAP.md`.
4. **Pruning**: If an idea loses relevance, move it to the `Archive/` section or delete it.

*This doc is for your curiosity. Keep adding to it.*
