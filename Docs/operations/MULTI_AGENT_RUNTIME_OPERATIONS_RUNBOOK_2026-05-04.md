# Multi-Agent Runtime Operations Runbook

- Date: 2026-05-04
- Scope: backend product-agent runtime

## Runtime Surfaces

| Operation | Command / Route | Expected Result |
| --- | --- | --- |
| Health/introspection | `GET /agents/runtime` | Registry definitions, supervisor health, recovery status. |
| Manual runtime pass | `POST /agents/runtime/run-once` | One scan/execute pass across registered agents. |
| Manual single-agent pass | `POST /agents/runtime/run-once?agent_name=front_door_agent` | Runs one registered agent only. |
| Runtime events | `GET /agents/runtime/events?limit=100` | Recent canonical `agent_event` records. |
| Trip events | `GET /trips/{trip_id}/agent-events` | Agent event history for a trip after agency access check. |
| Scenario drill | `uv run python tools/run_multi_agent_runtime_scenarios.py` | Writes `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`. |

## Local LLM Test Key Handling

- Local-only OpenAI credentials are available in `frontend/.env.local` for tests that explicitly need them.
- Do not print, copy, or commit secret values into docs, fixtures, logs, or scenario artifacts.
- Backend test commands should load only the needed environment variable into the process, then redact command output if an SDK prints configuration.
- `frontend/.nv.local` was checked and does not exist.

## Registered Operational Agents

| Agent | Purpose | Authority Boundary |
| --- | --- | --- |
| `front_door_agent` | Classify fresh/incomplete inquiries, identify missing basics, draft acknowledgment, set lead priority. | Draft/recommend/metadata only; no customer send and no assignment mutation. |
| `sales_activation_agent` | Schedule stage-aware follow-up when an open lead is idle beyond SLA and has no pending follow-up. | May create follow-up task fields; does not send messages. |
| `document_readiness_agent` | Build passport, visa, insurance, and transit readiness checklists with evidence metadata. | May block readiness metadata and escalate must-confirm items; no legal finality. |
| `follow_up_agent` | Mark overdue follow-up tasks as due. | May update follow-up status; does not contact customer. |
| `quality_escalation_agent` | Escalate blocked/high-risk trips for human review. | May set review escalation metadata; cannot approve/suppress risk. |

## Planned Agent Families

The runtime roadmap is expanded in `Docs/status/MULTI_AGENT_RUNTIME_EXPANDED_AGENT_PLAN_2026-05-04.md`.

Planned families:

- live intelligence/tool-calling agents for weather, destination safety, flight status, ticket prices, and advisories;
- document/compliance agents for visa, passport, insurance, transit, and expiry checks;
- stage-specific agents for feasibility, shortlist, proposal readiness, booking readiness, in-trip pulse, and post-trip retention;
- supplier/GDS agents for quote revalidation, schema normalization, PNR shadow checks, and supplier intelligence.

## Tool Evidence Contract

`src/agents/tool_contracts.py` defines the common evidence shape for live/tool-calling agents:

- `ToolFreshnessPolicy`: max age and fail-closed behavior.
- `ToolEvidence`: source, fetched timestamp, raw reference, confidence.
- `ToolResult`: tool name, normalized query, normalized data, evidence, expiry, freshness check.

Any weather, flight, ticket, visa, safety, supplier, or GDS agent must normalize provider output into this contract before updating trip metadata.

## SLOs

| SLO | Target | Current Signal |
| --- | --- | --- |
| Supervisor liveness | `running=true` during backend uptime | `/agents/runtime` |
| Agent pass freshness | `last_pass_at` within `AGENT_SUPERVISOR_INTERVAL_S * 2` | `/agents/runtime` |
| Poisoned work | 0 active poisoned items in normal operation | `/agents/runtime` coordinator snapshot |
| Retry backlog | No item stuck in retry beyond retry budget | `/agents/runtime/events` and coordinator snapshot |
| Audit write availability | Agent actions emit decision/action/retry/escalated events | `AuditStore` JSONL and event routes |

## Alert Thresholds

| Alert | Threshold | Triage |
| --- | --- | --- |
| Supervisor stopped | `running=false` while API healthy | Check backend logs, restart API process, inspect lifespan startup errors. |
| Stale pass | `last_pass_at` older than 2 intervals | Check thread health, long-running scans, TripStore latency. |
| Poisoned work present | Any `poisoned > 0` for more than one pass | Query `/agents/runtime/events`, inspect trip update failures, clear root cause before replay. |
| Missing audit events | Runtime pass returns results but no `agent_event` records | Check `AuditStore.log_event`, file permissions, privacy guard errors. |
| Unexpected retry surge | More than 5 retry events in 10 minutes | Check TripStore backend, DB connectivity, validation failures on updates. |

## Triage Steps

1. Call `GET /agents/runtime` and record `registered_agents`, `running`, `last_pass_at`, and coordinator snapshot.
2. Query `GET /agents/runtime/events?limit=100` and group by `agent_name`, `event_type`, and `correlation_id`.
3. For a trip-specific incident, query `GET /trips/{trip_id}/agent-events`.
4. Run `uv run python tools/run_multi_agent_runtime_scenarios.py` to separate runtime logic defects from environment/TripStore defects.
5. Run targeted tests:
   - `uv run pytest tests/test_agent_runtime.py tests/test_agent_events_api.py tests/test_recovery_agent.py -q`
   - `uv run python -m py_compile src/agents/events.py src/agents/recovery_agent.py src/agents/runtime.py spine_api/persistence.py spine_api/server.py tools/run_multi_agent_runtime_scenarios.py`

## Production-Hardening Gaps

- Replace in-memory leases with SQL-backed leases or queue-native visibility timeouts before multi-worker deployment.
- Connect `RecoveryAgent` requeue to the canonical async run queue once that queue exists.
- Add metrics export for event counts, poisoned work, pass duration, and update latency.
- Add role-scoped admin permissions for runtime run-once endpoints before exposing to non-owner users.
