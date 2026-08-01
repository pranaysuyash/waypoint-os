# ADR: AI Workforce Governance Registry

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS AI Workforce Governance & Agent Scoping

---

## Context

As specialized AI worker agents (Intake Parser, Strategy Specialist, Autonomic Ghost Concierge) execute multi-step tasks across agency workflows, un-scoped agent actions create liability and cost overruns.

---

## Decision

Implemented the AI Workforce Governance Registry in `src/governance/registry.py`:

1. **Agent Registration Contract (`AgentRegistration`)**:
   - Registers agent roles with defined tiers (`DETERMINISTIC_GATED`, `AUTONOMOUS_BOUNDED`, `HUMAN_APPROVAL_REQUIRED`), allowed action scopes, and budget impact limits.
2. **Runtime Action Validation (`validate_action`)**:
   - Enforces that no AI worker can perform unauthorized actions or exceed budget impact limits without triggering human approval gates.

---

## Consequences

- Strict governance and capability boundaries for all AI worker agents.
- Complete alignment with `AI_WORKFORCE_REGISTRY_CONTRACT.md`.
