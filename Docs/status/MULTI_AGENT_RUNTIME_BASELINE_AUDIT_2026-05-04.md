# Multi-Agent Runtime Baseline Audit

- Date: 2026-05-04
- Scope: backend-only audit across `src/`, `spine_api/`, `tests/`, and `Docs/`
- Goal source: `~/Downloads/goal.xml`

## Executive Status

The repo had a strong deterministic spine pipeline and one partially wired backend product agent (`RecoveryAgent`), but did not yet have a canonical product-agent registry, supervisor lifecycle, single-owner execution boundary, retry/poison semantics, or runtime-level introspection. This pass adds those missing runtime primitives in canonical backend paths and reconciles the highest-signal documentation claims against the real implementation.

## Architecture Map

| Layer | Current Artifact | Status | Evidence |
| --- | --- | --- | --- |
| Deterministic spine pipeline | `src/intake/orchestration.py`, `spine_api/server.py` `/run` + `/runs/*` | Confirmed | Existing Wave A lifecycle routes remain canonical. |
| Product-agent event envelope | `src/agents/events.py` | Confirmed | `AgentEvent` now carries agent name, event type, trip/run IDs, correlation ID, timestamp, payload. |
| Product-agent runtime | `src/agents/runtime.py` | Confirmed | New static `AgentRegistry`, `AgentSupervisor`, `InMemoryWorkCoordinator`, `FollowUpAgent`, `QualityEscalationAgent`. |
| Recovery agent | `src/agents/recovery_agent.py` | Confirmed with constraint | Runs from server lifespan; now supports dict trip records from `TripStore`. Requeue remains disabled until a canonical async job queue exists. |
| Persistence and audit | `spine_api/persistence.py` | Confirmed | `AuditStore.get_agent_events_for_trip()` and `AuditStore.get_agent_events()` query canonical `agent_event` records. |
| HTTP introspection | `spine_api/server.py` | Confirmed | `/agents/runtime`, `/agents/runtime/run-once`, `/agents/runtime/events`, `/trips/{trip_id}/agent-events`. |

## Route Ownership Map

| Resource / Action | Canonical Route | Owner Layer | Duplicate Route Check |
| --- | --- | --- | --- |
| Run lifecycle | `/run`, `/runs`, `/runs/{run_id}`, `/runs/{run_id}/steps/{step}`, `/runs/{run_id}/events` | Spine lifecycle | Existing routes reused; no duplicate run route added. |
| Trip-scoped agent events | `/trips/{trip_id}/agent-events` | Trip observability | Single trip-scoped event surface. |
| Runtime registry + health | `/agents/runtime` | Product-agent runtime | New resource; no existing equivalent found. |
| Runtime manual pass | `/agents/runtime/run-once` | Product-agent runtime | New admin/test action under same runtime resource. |
| Runtime event query | `/agents/runtime/events` | Product-agent runtime | New aggregate query under same runtime resource. |

## Lifecycle / State Map

| State / Boundary | Implementation | Evidence |
| --- | --- | --- |
| Startup | `lifespan()` starts watchdog, `RecoveryAgent`, `AgentSupervisor`, zombie reaper | `spine_api/server.py` lifecycle wiring. |
| Shutdown | `lifespan()` stops reaper, supervisor, recovery agent, watchdog | `spine_api/server.py` lifecycle wiring. |
| Work discovery | Each product agent implements `scan(trip_repo)` | `src/agents/runtime.py`. |
| Single-owner execution | `InMemoryWorkCoordinator.acquire()` leases by idempotency key | `tests/test_agent_runtime.py::test_ownership_collision_prevention_and_idempotent_reentry`. |
| Idempotent completion | Completed idempotency keys are skipped on re-entry | Same test and scenario artifact. |
| Retry | Failed updates become `retry_pending` until retry budget | `tests/test_agent_runtime.py::test_transient_dependency_failure_retries_then_succeeds`. |
| Poison / fail-closed | Exhausted retry budget marks work `poisoned` and emits `agent_escalated` | `tests/test_agent_runtime.py::test_terminal_failure_poisons_and_escalates_after_retry_budget`. |

## Current Agent Inventory

| Agent | Runtime Status | Trigger Contract | Output Contract |
| --- | --- | --- | --- |
| `recovery_agent` | Lifespan-managed, outside supervisor loop | Trips stuck beyond configured stage thresholds | Requeue when runner exists; otherwise escalate review status; emit audit events. |
| `follow_up_agent` | Registered and supervised | Open trip has overdue `follow_up_due_date` | Mark `status=needs_followup`, `follow_up_status=due`, agent metadata. |
| `quality_escalation_agent` | Registered and supervised | Escalated/blocked decision state, hard blockers, or high/critical suitability flags | Mark `review_status=escalated`, write escalation reason, agent metadata. |

## Observability Surfaces

| Surface | Purpose | Evidence |
| --- | --- | --- |
| `AgentEvent` envelope | Structured event payload with correlation ID | `src/agents/events.py`. |
| `AuditStore` agent queries | Query event history by trip, agent name, or correlation ID | `spine_api/persistence.py`. |
| `/trips/{trip_id}/agent-events` | Trip-specific operator/debug view | `tests/test_agent_events_api.py`. |
| `/agents/runtime/events` | Cross-trip runtime event stream | `tests/test_agent_events_api.py`. |
| Scenario evidence artifact | Human-readable drill output with timestamps and results | `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`. |

## External Reference Check

| Reference | Relevance | Result |
| --- | --- | --- |
| FastAPI lifespan events documentation: https://fastapi.tiangolo.com/fa/advanced/events/ | Confirms startup/shutdown resources can be managed through the `lifespan` parameter and context manager. | Supports wiring `AgentSupervisor.start()` before `yield` and `AgentSupervisor.stop()` after `yield` in `spine_api/server.py`. |
| Python `threading.RLock` documentation: https://docs.python.org/3/library/threading.html | Confirms `RLock` is a reentrant synchronization primitive and supports context-manager use. | Supports the single-process `InMemoryWorkCoordinator` lock boundary; does not imply distributed safety, so distributed leases remain a hardening gap. |

## Doc Claim Reconciliation

| Source Claim | Verdict | Evidence / Notes |
| --- | --- | --- |
| `Docs/MULTI_AGENT_INFRASTRUCTURE_ASSESSMENT_2026-04-22.md` says the product lacks orchestration, lifecycle, registry, retries, observability. | Confirmed before this pass; partially closed now | New runtime closes static registry, lifecycle, retry/fail-closed, health/introspection, and structured events. Inter-agent communication, durable distributed leases, versioning, and external tooling remain production-hardening gaps. |
| `Docs/DETAILED_AGENT_MAP.md` catalogs many aspirational travel agents. | Confirmed as aspirational | Only three backend product agents are executable now: recovery, follow-up, quality escalation. The larger catalog remains a product roadmap, not implementation truth. |
| `Docs/INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` prioritizes QualityGate/Retention/Sales/Inbox-style agents. | Confirmed; implementation now maps to subset | `quality_escalation_agent` is the first QualityGate-style executable agent; `follow_up_agent` covers a Retention/Sales follow-up automation slice. |
| `Docs/WAVE_B_AGENTIC_AUTOMATION_IDEAS_2026-04-18.md` describes Scout, QA, Committee, and Copilot concepts. | Stale as implementation claim, valid as roadmap | Those agents remain design ideas; no Scout/Committee/Copilot runtime was implemented in this pass. |
| `Docs/BACKEND_WAVE_A_AGENTIC_FLOW_2026-04-18.md` says Wave A provides run lifecycle and event ledgers. | Confirmed | Existing `/runs/*` lifecycle routes are preserved; product-agent runtime is additive and does not fork the spine pipeline. |
| `Docs/ROADMAP_PHASE_3_AUTONOMY.md` calls for self-healing autonomy. | Confirmed and extended | `RecoveryAgent` existed; this pass keeps it and adds supervised follow-up and quality escalation automation. |

## Known Constraints

- The work coordinator is in-memory. It proves single-process ownership/idempotency but must move to SQL/advisory locks or a queue backend before multi-worker production scaling.
- `RecoveryAgent` requeue is still not connected to a canonical async job queue; it escalates when no runner is configured.
- Product agents operate on existing trip fields only; no frontend implementation was added.
- Tests report pass output, then the local pytest process can remain alive under the shared TestClient/server lifecycle. The process was killed after pass output was captured.
