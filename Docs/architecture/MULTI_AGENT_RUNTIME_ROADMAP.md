# Multi-Agent Runtime Roadmap

## Product Thesis

Waypoint OS should have a deterministic spine as its trusted judgment core, with
an agent runtime that starts explicit/auditable and evolves toward modular,
contract-first, observable, safely extensible product agents.

## Non-negotiable Principles

- Deterministic spine stays pure — agents use the spine, agents do not pollute the spine
- Agent state, retries, queues, and communications live outside the spine
- Typed contracts for every agent interaction
- Observability from day one
- Feature flags and additive rollout
- Test coverage before production deployment

## Current Implemented Runtime

See `Docs/status/MULTI_AGENT_RUNTIME_IMPLEMENTATION_TRACKER_2026-05-14.md`.

## Valid Roadmap Agents

These are product-agent capabilities that remain valid long-term direction:

### Communicator Agent
Blocked state → clarification drafts for operator review/send. Should not mutate
canonical state directly without operator action.

### Scout Agent
Proactive info retrieval for visa, weather, safety, and availability. Requires
strong tool provenance and freshness policies.

### QA Agent
Analyze pipeline failures, propose test fixtures and regression tests. Should
create drafts only, not auto-merge.

### Committee System
Budget Optimizer + Experience Maximizer + Trip Architect for tiered proposal
generation. Useful after proposal readiness scaffolding is mature.

### Operator Copilot
Natural-language intervention on canonical packet. Parse operator intent, show
diff, re-run pipeline. High value but needs strong mutation contracts.

## Evolution Phases

```text
Layer 0: Deterministic spine — NB01/NB02/NB03, rules + LLM, gates (built)
Layer 1: Product-agent runtime — contracts, static registry, supervisor (built)
Layer 2: Governed agent modules — split runtime.py, per-agent config (next)
Layer 3: Durable orchestration — SQL leases, job queue/outbox, dead letters (next)
Layer 4: Product intelligence — Communicator, Scout, Committee, QA (future)
Layer 5: Advanced extension — governed dynamic registration (speculative)
```

## Superseded Implementation Assumptions

These were described as "Phase 1 Foundation" in earlier docs but are no longer
the planned approach:

- `orchestrator.py` as mandatory first file
- `base_agent.py` as mandatory first file
- Dynamic discovery as near-term registry mechanism
- Message bus before durable work coordination exists
- Agent memory before clear state model exists
- Resource isolation before job execution model exists
