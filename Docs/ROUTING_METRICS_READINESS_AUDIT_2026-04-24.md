# Routing Metrics Readiness Audit

**Date**: 2026-04-24
**Status**: Audit
**Scope**: Current-state audit of which routing, workload, and operator signals are trustworthy enough to support deterministic assignment, ranked suggestions, or learned routing.
**Related docs**:

- `AUTO_ASSIGNMENT_AND_LEARNED_ROUTING_EXPLORATION_2026-04-24.md`
- `ASSIGNMENT_SIGNAL_TAXONOMY_SPEC_2026-04-24.md`
- `SETTINGS_ASSIGNMENTS_LEARNED_ROUTING_ADDENDUM_2026-04-24.md`
- `ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`
- `SETTINGS_ROUTE_SUBROUTE_UX_CONTRACT_2026-04-23.md`

---

## Executive Summary

Waypoint is not ready for learned auto-assignment yet.

It is partially ready for deterministic routing inputs, and it is close to being ready for transparent suggestion mode if the signal set is intentionally narrow.

### Current Verdict

- **Ready now for deterministic routing**: active membership, basic role gating, manually-entered capacity, current assignment count.
- **Partial / caution**: customer satisfaction, active/completed trip counts, role vocabulary consistency, workload endpoint compatibility.
- **Not ready**: response time, conversion rate, specialization, continuity memory, review backlog per operator, canonical routing-slot telemetry, learned performance scoring.

### Key Blockers

1. Team metrics use simulated values for important fields.
2. The analytics team endpoint has a structural key mismatch and is not trustworthy as a routing foundation.
3. Assignment storage still models one assignee slot rather than the canonical routing state.
4. The frontend and backend still expose conflicting role vocabularies and workload data shapes.
5. Specialization/skills data is not yet modeled as a canonical backend contract.

---

## Evidence Reviewed

- `spine-api/server.py`
- `spine-api/persistence.py`
- `spine-api/contract.py`
- `spine-api/core/auth.py`
- `src/analytics/metrics.py`
- `src/analytics/review.py`
- `frontend/src/types/governance.ts`
- `frontend/src/hooks/useGovernance.ts`
- `frontend/src/app/api/team/workload/route.ts`

---

## Readiness Scale

- `Ready` — safe to use for deterministic routing today.
- `Partial` — usable only with explicit caveats and narrow scope.
- `Blocked` — should not be used for routing decisions yet.

---

## Audit Findings

## 1. Role Eligibility

**Verdict**: Partial

What exists:

- backend auth permissions already define `owner`, `admin`, `senior_agent`, `junior_agent`, `viewer` in `spine-api/core/auth.py`

Why not fully ready:

- frontend governance types still use `owner | manager | agent | viewer` in `frontend/src/types/governance.ts`
- team member APIs use a generic `role: string` in `spine-api/contract.py`

Implication:

- backend authorization is ahead of the frontend type contract, so routing policy can reason about canonical roles conceptually, but the UI/data contract is not fully converged.

## 2. Member Active Status

**Verdict**: Ready

What exists:

- `TeamStore` persists `active` on members in `spine-api/persistence.py`
- `/api/team/members` and `/api/team/workload` can filter active members

Implication:

- `member_active` is a trustworthy eligibility signal for deterministic routing.

## 3. Capacity

**Verdict**: Ready for basic deterministic use

What exists:

- team member contract includes `capacity` in `spine-api/contract.py`
- `TeamStore` persists capacity
- `/api/team/workload` computes `assigned` and `available` from stored capacity and assignment count

Limitations:

- this is only a flat integer capacity, not a nuanced queue or stage-sensitive capacity model

Implication:

- `capacity_available` can be used as a first-pass gate or penalty signal.

## 4. Assignment Count / Current Load

**Verdict**: Partial

What exists:

- `AssignmentStore` tracks one assignment per trip in `spine-api/persistence.py`
- `/api/team/workload` counts how many assignments point at a member id

Why partial:

- this only measures a single `agent_id`
- it does not represent `primary_assignee`, `reviewer`, `escalation_owner`, or `watchers`
- it cannot distinguish light work from complex work

Implication:

- load count is usable for coarse balancing in ranked suggestions, but not as a complete routing truth.

## 5. Specialization / Skills

**Verdict**: Blocked

What exists:

- frontend `TeamMember` type has optional `expertise?: string[]` in `frontend/src/types/governance.ts`

Why blocked:

- backend `TeamMember` contract in `spine-api/contract.py` has no expertise or specialization field
- invite/update APIs do not establish a canonical skills schema
- routing cannot rely on a frontend-only optional field

Implication:

- destination and trip-type fit cannot be used as trustworthy live routing signals yet.

## 6. Continuity Signals

**Verdict**: Blocked

What exists:

- current trip assignment exists

Why blocked:

- no canonical traveler-to-operator relationship layer
- no household/account ownership model
- no repeat-traveler routing memory contract

Implication:

- continuity can preserve existing trip ownership, but returning-traveler continuity is not yet modeled strongly enough for routing.

## 7. Team Metrics Endpoint Integrity

**Verdict**: Blocked

What exists:

- `/analytics/team` calls `compute_team_metrics` from `spine-api/server.py`

Why blocked:

- `get_analytics_team` passes assignment records from `AssignmentStore._load_assignments().values()`
- `compute_team_metrics` initializes operator rows from `user.get("user_id")` and `user.get("name")`
- assignment records actually store `agent_id` and `agent_name`

Implication:

- the endpoint is structurally mismatched and should not be trusted as a routing input until corrected.

## 8. Response Time

**Verdict**: Blocked

What exists:

- `avgResponseTime` is emitted by `compute_team_metrics`

Why blocked:

- value is simulated using `random.uniform(...)` in `src/analytics/metrics.py`

Implication:

- response-time-based ranking or learning would be fictitious today.

## 9. Conversion Rate

**Verdict**: Blocked

What exists:

- `conversionRate` is emitted by `compute_team_metrics`

Why blocked:

- value is simulated using `random.uniform(...)`

Implication:

- conversion-based assignment would be actively misleading today.

## 10. Customer Satisfaction

**Verdict**: Partial

What exists:

- `compute_team_metrics` attempts to derive feedback ratings from trip packet feedback or analytics latest feedback

Why partial:

- signal depends on feedback being present
- if no ratings exist, the code defaults to `4.5`, which is not an observed value
- the endpoint itself is also blocked by the structural mismatch described above

Implication:

- CSAT may become useful later, but should not drive routing now.

## 11. Workload Distribution Frontend Compatibility

**Verdict**: Partial

What exists:

- backend `/api/team/workload` returns items with `member_id`, `name`, `role`, `capacity`, `assigned`, `available`
- frontend `useWorkloadDistribution` passes the result through directly

Why partial:

- frontend `WorkloadDistribution` type expects `userId`, `currentLoad`, `loadPercentage`, `status`, and `trips`
- the Next.js proxy route in `frontend/src/app/api/team/workload/route.ts` does not normalize the shape

Implication:

- the route exists, but the contract is not fully aligned for governance-grade workload UX.

## 12. Review Backlog / Escalation Backlog

**Verdict**: Blocked

What exists:

- review actions and escalation logic exist in `src/analytics/review.py`

Why blocked:

- no canonical per-operator review backlog metric
- no canonical per-operator escalation ownership load
- escalation currently mutates `assigned_to` in some flows, which muddies ownership semantics

Implication:

- backlog-aware routing cannot be trusted until canonical routing-slot telemetry exists.

## 13. SLA Pressure Per Operator

**Verdict**: Partial

What exists:

- SLA concepts exist in analytics and dashboard aggregation

Why partial:

- no clean per-operator routing pressure metric is exposed for assignment policy
- current state is more trip-centric than operator-centric

Implication:

- SLA pressure may be surfaced for review, but should not yet act as a ranking penalty without a dedicated metric contract.

## 14. Auditability Of Assignment Decisions

**Verdict**: Partial

What exists:

- `trip_assigned`, `trip_unassigned`, `team_member_created`, and related generic events in `spine-api/persistence.py`

Why partial:

- no recommendation-generated event
- no recommendation accepted/overridden event
- no auto-applied assignment event
- no signal-breakdown payload

Implication:

- manual assignment is auditable at a basic level, but learned routing is not yet audit-ready.

---

## Overall Readiness By Delivery Phase

## Phase A: Deterministic Eligibility

**Verdict**: Feasible now

Safe signals:

- active membership
- basic role gating
- flat capacity
- current assignment count

Conditions:

- keep the model narrow
- do not assume specialization or continuity memory exists

## Phase B: Ranked Suggestions

**Verdict**: Feasible soon, but only with narrow signal scope

Safe-ish signals after light hardening:

- deterministic eligibility
- coarse load balancing
- current-trip continuity

Required fixes first:

- align role vocabulary across frontend/backend governance types
- normalize workload endpoint contract for frontend use
- stop treating simulated metrics as real team-quality signals

## Phase C: Learning-Assisted Ranking

**Verdict**: Not ready

Blocked by:

- simulated metrics
- broken team analytics contract
- no cohort model
- no specialization model
- no trustworthy continuity memory
- no recommendation audit trail

## Phase D: Low-Risk Auto-Assignment

**Verdict**: Not ready

Blocked by all Phase C issues plus:

- lack of canonical routing slot telemetry
- lack of explainable recommendation payloads
- incomplete audit event taxonomy for routing intelligence

---

## Recommended Next Fixes Before Any Learned Routing Build

1. Converge frontend governance role vocabulary with backend canonical roles.
2. Add a canonical backend skills/specialization profile for team members.
3. Fix `/analytics/team` so it uses a real operator roster instead of mismatched assignment-record keys.
4. Replace simulated response and conversion metrics with measured event-derived values or remove them from routing-facing surfaces.
5. Align `/api/team/workload` with the frontend contract or define a canonical governance workload DTO.
6. Extend assignment telemetry to canonical routing slots instead of a single assignee field.
7. Add recommendation-level audit events before introducing suggestion mode.

---

## Final Recommendation

Treat the current system as ready for only a thin deterministic routing layer.

Do not use current team analytics, simulated response/conversion metrics, or frontend-only expertise fields as routing intelligence inputs. Use this audit as the readiness gate before enabling any learned routing behavior under `/settings/assignments`.
