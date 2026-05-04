# Agent Graph + Global Admin Exploration (First-Principles) — 2026-05-04

## Why this doc exists
You asked for deep exploration, not a shallow "yes". This document is the decision packet for:
1. In-app node/graph view of agent runtime (who is working on what).
2. Human approvals from the same surface.
3. Full-platform admin view across all workspaces/clients.

It is intentionally backend-first and architecture-first.

## Current backend truth (as of 2026-05-04)
- Runtime primitives exist:
  - `src/agents/runtime.py`: `AgentRegistry`, `AgentSupervisor`, `InMemoryWorkCoordinator`, product agents.
  - `src/agents/recovery_agent.py`: separate recovery loop.
  - `src/agents/events.py`: canonical event envelope.
- Runtime API surfaces exist:
  - `GET /agents/runtime`
  - `POST /agents/runtime/run-once`
  - `GET /agents/runtime/events`
  - `GET /trips/{trip_id}/agent-events`
- Auth model is agency-scoped in JWT (`agency_id`, `role`) and membership-centric (`spine_api/models/tenant.py`, `spine_api/routers/auth.py`).

Implication: graph visualization can be built now from existing event/runtime surfaces; approval-control and global-admin require new backend contracts.

---

## Part A — Agent Graph + Approvals

## A1. First-principles goals
A graph/control surface should satisfy five invariants:
1. Truthful: it reflects canonical runtime state, not frontend-invented state.
2. Actionable: operator can intervene safely where automation risk is high.
3. Auditable: every intervention and decision is logged with identity + reason.
4. Bounded: approvals gate only defined high-risk actions, not all actions.
5. Non-fragile: UI failure cannot silently permit blocked execution.

## A2. Minimum viable mental model
- Graph entity types:
  - System node: `agent_supervisor`
  - Agent nodes: product agents + `recovery_agent`
  - Work item nodes: optional (trip-scoped action instances)
- Edge semantics:
  - `agent_decision` (execute/skip)
  - `agent_action` (success)
  - `agent_retry` (transient failure)
  - `agent_escalated` (terminal budget exhausted)
  - `agent_failed` (scan/runtime failure)

Use `correlation_id` and `idempotency_key` as first-class graph IDs.

## A3. What exists vs what is missing
Exists:
- Event stream needed for graph reconstruction.
- Runtime introspection endpoint and run-once endpoint.

Missing for approval:
- Explicit pending-approval state in runtime contract.
- Approval object/entity and persistence.
- Approval APIs and policy engine.
- Resume/reject execution transitions.

## A4. Approval architecture options

### Option 1: Inline synchronous approval (reject)
- Agent waits in request path until human approves.
- Reject because: blocks runtime loop, brittle, bad operator latency coupling.

### Option 2: Event-only soft approval (weak)
- Agent emits "needs approval" but action still runs.
- Reject because: fake control; violates safety invariant.

### Option 3: Durable approval gate (recommended)
- Agent emits `pending_approval` and writes approval record.
- Work item status transitions to `WAITING_APPROVAL`.
- No execution until explicit approve API call.
- Approve -> resumes execution with preserved `idempotency_key`.
- Reject -> transitions to `ESCALATED` or `MANUAL_REQUIRED`.
- Best fit for safety + audit + operator control.

## A5. Proposed backend contract (approval gate)

### New runtime status values
- `waiting_approval`
- `approved`
- `rejected`

### New event types
- `agent_pending_approval`
- `agent_approved`
- `agent_rejected`

### New persistence model
`agent_approvals` (SQL preferred)
- `id`
- `trip_id`
- `agent_name`
- `action`
- `idempotency_key`
- `correlation_id`
- `risk_reason`
- `requested_by_agent_at`
- `status` (`pending|approved|rejected|expired`)
- `approved_by_user_id` / `rejected_by_user_id`
- `decision_reason`
- `decided_at`
- `expires_at`

### New APIs (canonical)
- `GET /agents/runtime/approvals?status=pending&trip_id=&agent_name=`
- `POST /agents/runtime/approvals/{approval_id}/approve`
- `POST /agents/runtime/approvals/{approval_id}/reject`

No duplicate route families; keep under `/agents/runtime/*`.

## A6. Policy: which actions require approval?
Default gating policy (v1):
- Any action that can materially change customer-facing or compliance-sensitive state.
- Start with:
  - quality escalation overrides
  - document-readiness risk downgrades
  - destination intelligence actions marked high-risk uncertainty
  - recovery actions that could requeue repeatedly beyond threshold

Policy store:
- static config first (in-repo), then move to agency-configurable policy later.

## A7. Failure-mode analysis (important)
- Approval API unavailable:
  - keep work in `pending`; do not auto-execute.
- Duplicate approvals/race:
  - idempotent decision endpoint using approval status check + optimistic lock.
- Expired approvals:
  - auto-transition to `expired` then `manual_required`.
- Operator rejects after action already executed:
  - must be impossible by design; execution reads authoritative approval state before action.

---

## Part B — Global Admin View (all workspaces/clients)

## B1. First-principles goals
1. Global visibility for platform operations.
2. No tenant data leakage into normal agency users.
3. Explicit super-admin scope and audit trail for every cross-tenant read/action.
4. Safe gradual rollout: read-only first, controlled writes later.

## B2. Current model constraints
- JWT is agency-scoped (`agency_id`, `role`).
- Current routes enforce agency ownership semantics.

Implication: global admin cannot be implemented safely by bypassing existing checks ad hoc. It needs explicit auth scope and separate guardrails.

## B3. Role model options

### Option 1: Reuse agency `owner` role for global admin (reject)
- Violates tenant isolation and principle of least privilege.

### Option 2: Separate platform-admin identity + scope (recommended)
- Add platform role claim: `platform_role` (`none|support|ops_admin|super_admin`).
- Platform routes check platform role first, then allow read across agencies.
- All accesses audited with target tenant IDs.

## B4. Admin API surface (backend-first)
Read-only v1:
- `GET /platform/admin/agencies`
- `GET /platform/admin/agencies/{agency_id}`
- `GET /platform/admin/agencies/{agency_id}/members`
- `GET /platform/admin/agencies/{agency_id}/trips?status=&stage=&limit=`
- `GET /platform/admin/runtime/overview` (cross-tenant runtime health)

Controlled write v2:
- `POST /platform/admin/agencies/{agency_id}/suspend`
- `POST /platform/admin/agencies/{agency_id}/reactivate`
- `POST /platform/admin/agencies/{agency_id}/limits`

Each write requires:
- reason
- second confirmation token (or equivalent dual-step guard)
- immutable audit record

## B5. Data model additions
Potential table: `platform_admin_audit`
- actor, platform_role, action, target_agency_id, target_entity, payload_hash, reason, timestamp

Potential table: `agency_operational_snapshot` (optional optimization)
- pre-aggregated metrics: active trips, backlog age, escalations, runtime error counts.

## B6. Security and compliance boundaries
- Never return raw PII by default in global list endpoints.
- Field-level projection by platform role (`support` sees less than `super_admin`).
- Rate-limit and monitor admin endpoints separately.

---

## Part C — Recommended execution sequence

## Phase 0: Contracting (no UI)
- Finalize runtime approval contracts and platform-admin auth scope.
- Produce OpenAPI spec updates + event schema updates.

## Phase 1: Backend approvals
- Implement approval status/state machine + APIs + audit events.
- Add tests: pending/approve/reject/race/expiry/idempotency.

## Phase 2: Backend platform-admin read-only
- Implement platform role auth guard + read-only aggregated APIs.
- Add strict tenant isolation tests.

## Phase 3: Graph UI wiring
- UI consumes existing runtime endpoints and approval endpoints.
- Read-first graph; then enable approve/reject controls.

## Phase 4: Controlled admin writes
- Add constrained write actions with dual-confirm and audit.

---

## Part D — What we should decide together (to-fro)
1. Approval gating strictness:
- strict default (deny until approved) vs selective by policy map.
2. Platform admin rollout:
- support-only read scope first vs full super-admin read scope.
3. Audit depth:
- standard audit only vs immutable append-only ledger for admin/approval events.
4. Multi-worker timeline:
- keep in-memory coordinator short-term vs prioritize DB-backed coordinator before approvals.

---

## Proposed decision baseline (my recommendation)
1. Use durable approval gate (Option 3) with strict deny-until-approved for flagged actions.
2. Launch global admin as read-only first with separate `platform_role` scope.
3. Implement DB-backed approval records before UI controls.
4. Keep runtime graph derived from canonical event stream; no separate graph store initially.

This gives safety and operator trust without introducing duplicate orchestration paths.

## Backlog linkage
These exploration tracks are now listed in `Docs/exploration/backlog.md` under:
- `Agent Runtime Control Plane`
- `Platform Admin Control Plane (All Workspaces/Clients)`
