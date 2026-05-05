# Agent Intelligence Graph

This graph turns the repo's research, feedback, graph, and learning docs into a living navigation layer.

## Core Concepts
- `concept:autoresearch` - Autoresearch Loop
- `concept:feedback` - Feedback / Learning Loop
- `concept:governance` - Governance / Routing
- `concept:graph` - Graph / Lineage Memory
- `concept:live` - Live Intelligence

## Seed Docs
- `Docs/AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md` - Agent Feedback Loop: Suitability Overrides — Full Specification | themes: feedback_learning, live_intelligence, agent_governance
  - supports -> `concept:feedback`
  - anchors -> `concept:governance`
  - supports -> `concept:governance`
  - supports -> `concept:live`
- `Docs/research/AGENT_GRAPH_AND_GLOBAL_ADMIN_EXPLORATION_2026-05-04.md` - Agent Graph + Global Admin Exploration (First-Principles) — 2026-05-04 | themes: feedback_learning, graph_memory, live_intelligence, agent_governance
  - supports -> `concept:feedback`
  - supports -> `concept:governance`
  - supports -> `concept:graph`
  - supports -> `concept:live`
- `Docs/AI_WORKFORCE_REGISTRY_CONTRACT_2026-04-22.md` - AI Workforce Registry Contract | themes: feedback_learning, live_intelligence, agent_governance
  - supports -> `concept:feedback`
  - supports -> `concept:governance`
  - supports -> `concept:live`
- `Docs/ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md` - Architecture Decision: D5 — Override Learning (Feedback Bus) | themes: feedback_learning, live_intelligence, agent_governance
  - supports -> `concept:feedback`
  - supports -> `concept:governance`
  - supports -> `concept:live`
- `Docs/CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` - Cross-Project Agentic Pattern Exchange — WaypointOS ↔ AdShot | themes: feedback_learning, graph_memory, agent_governance
  - supports -> `concept:feedback`
  - supports -> `concept:governance`
  - supports -> `concept:graph`
- `Docs/product_features/SEMANTIC_TASTE_GRAPH_DISCOVERY.md` - Feature: Semantic Taste Graph Discovery | themes: graph_memory, live_intelligence, agent_governance
  - supports -> `concept:governance`
  - anchors -> `concept:graph`
  - supports -> `concept:graph`
  - supports -> `concept:live`
- `Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md` - Feedback Loops and Improvement | themes: feedback_learning, live_intelligence
  - anchors -> `concept:feedback`
  - supports -> `concept:feedback`
  - supports -> `concept:live`
- `Docs/research/FLW_SPEC_FEEDBACK_LEARNING.md` - Flow Spec: Agentic Feedback-Learning (FLW-003) | themes: feedback_learning
  - supports -> `concept:feedback`
- `Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md` - Live Intel Toolcalling Exploration — 2026-05-05 | themes: live_intelligence, agent_governance
  - supports -> `concept:governance`
  - anchors -> `concept:live`
  - supports -> `concept:live`
- `Docs/ROUTING_STRATEGY.md` - Routing and Optimization Architecture | themes: autoresearch, feedback_learning, agent_governance
  - supports -> `concept:autoresearch`
  - supports -> `concept:feedback`
  - supports -> `concept:governance`
- `Docs/TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md` - Technical Scaffold and Autoresearch Optimization | themes: autoresearch, feedback_learning, agent_governance
  - anchors -> `concept:autoresearch`
  - supports -> `concept:autoresearch`
  - supports -> `concept:feedback`
  - supports -> `concept:governance`
- `Docs/EXPLORATION_FRONTIER.md` - The Exploration Frontier | themes: agent_governance
  - supports -> `concept:governance`
- `Docs/INDEX.md` - Validation and Testing (2026-04-17) | themes: autoresearch, feedback_learning, graph_memory, live_intelligence, agent_governance
  - supports -> `concept:autoresearch`
  - supports -> `concept:feedback`
  - supports -> `concept:governance`
  - supports -> `concept:graph`
  - supports -> `concept:live`

## Operating Model
- Live path stays deterministic and bounded.
- Autoresearch is offline only: mutate, evaluate, persist only if evidence improves.
- Feedback loops convert overrides, outcomes, and recurring corrections into future policy.
- Graph memory links docs, decisions, and learning signals so the next agent can start from a better map.

## Suggested Reading Order
1. `Docs/INDEX.md`
2. `Docs/TECHNICAL_SCAFFOLD_AND_AUTORESEARCH.md`
3. `Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md`
4. `Docs/product_features/SEMANTIC_TASTE_GRAPH_DISCOVERY.md`
5. `Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md`
6. `Docs/CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md`
