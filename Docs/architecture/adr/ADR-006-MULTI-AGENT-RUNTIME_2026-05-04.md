# ADR-006: Canonical Backend Multi-Agent Runtime

- Date: 2026-05-04
- Status: Accepted

## Context

The product needs executable backend product agents, but the repo previously had only deterministic spine lifecycle primitives and a standalone `RecoveryAgent`. Prior docs described a much larger multi-agent architecture, but most of it was aspirational.

## Decision

Implement a static, in-repo product-agent runtime under `src/agents/runtime.py` and wire it into the existing FastAPI lifespan in `spine_api/server.py`.

The runtime consists of:

- `AgentDefinition` contracts for trigger, input, output, idempotency, retry, and failure behavior.
- `AgentRegistry` with explicit in-repo registration only.
- `AgentSupervisor` for startup/shutdown, scan/execute passes, health, and event emission.
- `InMemoryWorkCoordinator` for single-owner leases, idempotent completion, retry, and poison/fail-closed behavior.
- Two executable product agents beyond `RecoveryAgent`: `follow_up_agent` and `quality_escalation_agent`.

## Rationale

This keeps the deterministic spine pipeline canonical and adds product-agent autonomy around it instead of forking a second pipeline. Static registration is deliberately narrower than dynamic plugin loading because the current product needs auditable, predictable backend agents before open-ended extension points.

The lifecycle wiring follows FastAPI's documented lifespan pattern for startup/shutdown resources. The current lease boundary uses Python `threading.RLock` for single-process synchronization; this is intentionally documented as insufficient for distributed multi-worker ownership.

## Consequences

- Operators and tests can inspect runtime health through `/agents/runtime`.
- Product-agent audit history is queryable through `/agents/runtime/events` and `/trips/{trip_id}/agent-events`.
- The current coordinator is correct for single-process backend runtime but is not a distributed lock. Production multi-worker deployment needs SQL-backed leases or a queue.

## Supersession / Route Safety

No existing API route was duplicated. New agent surfaces live under the new `/agents/runtime` resource, while trip-scoped events use the existing trip resource namespace.
