# Master Execution Roadmap: Travel Agency Agent

**Date**: Wednesday, April 22, 2026
**Scope**: Unified cockpit, system integrity, and agentic autonomy.

---

## 1. Executive Summary
This master roadmap consolidates the transition from fragmented mocks to a mathematically verified, self-healing agentic platform.

| Phase | Focus | Status | Primary Goal |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Foundation & Traceability | Done | Unified backend pipeline, auditable lifecycle. |
| **Phase 2** | System Integrity & Cockpit | Active | Proactive drift detection, SSOT, Inbox intelligence. |
| **Phase 3** | Agentic Autonomy | Partial | Self-healing agents, compliance blocks, prompt tuning. |
| **Phase 4** | LLM Cost & Per-Agency Controls | Partial | LLM usage guard, agency-specific settings, feature gating. |

---

## Future / Deferred Domains

| Domain | Status | Rationale | When It Ships |
| :--- | :--- | :--- | :--- |
| **Digital Nomad / Extended Stay** | Deferred | Not in launch scope. Cross-cuts intake, decision rules, visa logic. | Only after explicit product decision. |

> **Rule**: No scenario file for these domains (e.g. `ADDITIONAL_SCENARIOS_152` and related files) may be treated as an implementation commitment. They are exploratory inputs. Verify codebase before building.

---

## 2. Phase 2: System Integrity & Inbox Intelligence (Active)

| ID | Task | Owner | Dependencies |
| :--- | :--- | :--- | :--- |
| **P1-01** | **Backend Aggregator (SSOT)** | Backend | None |
| **P1-02** | **Frontend SSOT Hook (`useUnifiedState`)** | Frontend | P1-01 |
| **P1-03** | **Integrity Watchdog Service** | Backend | P1-01 |
| **P1-04** | **Inbox V2 (Status Footer & Quick Actions)** | Frontend | P1-02 |
| **P1-05** | **SLA Logic Migration to Aggregator** | Backend | P1-01 |

---

## 3. Phase 3: Agentic Autonomy (Future)

| ID | Task | Owner | Dependencies |
| :--- | :--- | :--- | :--- |
| **P3-01** | **Self-Healing Agent (`recovery_agent.py`)** ✅ Done | Backend | P1-01, P1-03 |
| **P3-02** | **Compliance Hard-Gates** | Backend | P1-05 |
| **P3-03** | **Prompt Tuning Agent (Feedback Loop)** | Backend | P1-04 |
| **P3-04** | **Scenario Replay Engine (QA Tool)** | Dev/QA | Phase 1 |

---

## 4. Phase 4: LLM Cost & Per-Agency Controls (Active — Dogfood Only)

**Production status**: Guard supports Redis-backed storage (activates when `REDIS_URL` is set) and in-memory fallback. See `Docs/LLM_USAGE_GUARD_AND_AGENCY_CONTROLS_2026-04-26.md`.

**Redis storage**: ✅ Done — `RedisUsageStore` with Lua atomic scripts. See `src/llm/usage_store.py:630-770`.

| ID | Task | Status | Owner | Dependencies | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P4-01** | **LLM Usage Guard (`LLMUsageGuard`)** | ✅ Done | Backend | None | Functional, single-process |
| **P4-02** | **Per-Agency LLM Guard Config** | ✅ Done | Backend | P4-01 | `LLMGuardSettings` in SQLite |
| **P4-03** | **Redis-Backed Guard Storage** | ✅ Done | Backend | P4-01 | Activates when `REDIS_URL` is set |
| **P4-04** | **Per-Model Rate Limits** | Pending | Backend | P4-03 | After Redis storage |
| **P4-05** | **Alert Delivery (email/webhook)** | ✅ Done | Backend | P4-03 | `src/llm/alert_service.py` — webhook + email channels, env var config, guard integration |
| **P4-06** | **Guard State API Endpoint** | Pending | Backend | P4-03 | After Redis storage |
| **P4-07** | **`AiAgentSettings` Dataclass** | ✅ Done | Backend+Frontend | P4-03 | Shipped: dataclass, API, Settings UI |
| **P4-08** | **`SupportSettings` Dataclass** | ✅ Done | Backend+Frontend | P4-03 | Shipped: dataclass, API, Settings UI |
| **P4-09** | **`CommSettings` Dataclass** | ✅ Done | Backend+Frontend | P4-03 | Shipped: dataclass, API, Settings UI |
| **P4-10** | **`AgencyTier` (Starter/Pro/Enterprise)** | Pending | Backend | P4-03 | Needs product decision |
| **P4-11** | **Admin UI for Agency Settings** | Pending | Frontend | P4-07–P4-10 | Depends on data models |

> **P4-07 through P4-11**: Dependencies (Redis, auth, tenant isolation) are resolved. Items are now eligible for work pending product decisions. See Addendum (2026-06-18).

See `Docs/LLM_USAGE_GUARD_AND_AGENCY_CONTROLS_2026-04-26.md` for full details.

---

## 4. Execution Rules (Mandatory)
- **SSOT First**: Dashboard-level trip/inbox/review counts must derive from the unified state endpoint or a backend-aggregated summary. Page-level domain-specific data (campaigns, documents, individual trips) may use domain-specific hooks. Client-side `.filter().length` on server-fetched arrays is acceptable for page-local display logic (e.g., filter tab counts) but not for summary cards that appear on multiple pages.
- **Fail Loudly**: If data integrity is compromised, UI *must* render a critical error.
- **Traceability**: All agentic actions (especially self-healing) *must* be logged to the `AuditStore`.
- **Review Protocol**: Minimum 2-cycle review for schema changes (Cycle 1: Logic, Cycle 2: Fallbacks/Defensive).

---

## 5. Verification Gateways
- **Mathematical Integrity**: `tests/test_integrity.py` must pass for every build.
- **Coverage**: All P1 tasks require explicit test coverage for the `AuditStore` logging.
- **Handoff**: Every task completion must produce a structured handoff document following the `IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`.

*Note: This roadmap is the source of truth for all current and future work. Any new task must be mapped to this structure before implementation begins.*

---

## Addendum (2026-06-18): Status Reconciliation Audit

A Random Document Audit (motto_v3) on 2026-06-18 verified every claim in this roadmap against the live codebase. Three factual contradictions and one architectural gap were found. The original text above is preserved for historical record. Corrections are below.

### Corrections to Phase Summary Table

| Phase | Original Status | Corrected Status | Evidence |
| :--- | :--- | :--- | :--- |
| **Phase 3** | Pending | **Partial** | P3-01 (Self-Healing Agent) is fully implemented and tested. See correction below. |
| **Phase 4** | Partial | **Partial (advanced)** | P4-03 (Redis-Backed Guard Storage) is fully implemented. See correction below. |

### P3-01: Self-Healing Agent — DONE

Original status: Pending.

Actual status: ✅ Done.

- `src/agents/recovery_agent.py` — Full implementation (360+ lines): stuck-trip detection, requeue escalation ladder, AuditStore logging, fail-closed design, thread lifecycle, `run_once()` admin endpoint.
- `tests/test_recovery_agent.py` — 5/5 tests passing.
- Integrated into server lifespan: `spine_api/server.py:304-338`, `spine_api/services/agent_runtime_factory.py:230-247`.

### P4-03: Redis-Backed Guard Storage — DONE

Original status: "Pending — P0. Required for production."

Actual status: ✅ Done.

- `src/llm/usage_store.py:630-770` — `RedisUsageStore` class with Lua-script atomic check-and-reserve, key TTLs, fail-closed on storage error.
- `src/llm/usage_guard.py:119-137` — `from_env()` selects `RedisUsageStore` when `REDIS_URL` env var is set; otherwise falls back to `InMemoryUsageStore`.
- `tests/test_usage_guard.py` — 26/26 tests passing.
- Production deployment note: Redis storage activates automatically when `REDIS_URL` is configured. No code change needed.

### P4-07 through P4-11: Dependency Resolved

Original status: "Blocked — explicitly deferred until Redis storage ships."

Corrected status: **Dependency resolved.** P4-03 (Redis) is done. P4-07–P4-11 are now eligible for work pending product decision on tiering/features. None of these dataclasses (`AiAgentSettings`, `SupportSettings`, `CommSettings`, `AgencyTier`) exist in the codebase yet.

### SSOT Rule Adoption Gap

The execution rule "All UI components must derive data from useUnifiedState()" is not fully met. Only 2 frontend consumers exist:

1. `frontend/src/components/layouts/Shell.tsx:160` — `isConsistent` check
2. `frontend/src/app/(agency)/insights/PageClient.tsx:314` — `unifiedState` read

Most dashboard pages compute stats independently. This is an architectural gap that requires a product decision: enforce the rule (migrate remaining consumers) or update the rule to reflect actual architecture.

### Remaining Phase 3 Tasks (Still Pending)

| ID | Task | Verified Status |
| :--- | :--- | :--- |
| **P3-02** | Compliance Hard-Gates | Partial — `AgencyAutonomyPolicy` exists but full hard-gate enforcement unclear |
| **P3-03** | Prompt Tuning Agent (Feedback Loop) | **Not found** — no implementation in codebase |
| **P3-04** | Scenario Replay Engine (QA Tool) | **Not found** — no implementation in codebase |

### Remaining Phase 4 Tasks (Status Verified)

| ID | Task | Verified Status |
| :--- | :--- | :--- |
| **P4-04** | Per-Model Rate Limits | Not implemented — guard has model param but limits are per-agency, not per-model |
| **P4-05** | Alert Delivery (email/webhook) | Not implemented |
| **P4-06** | Guard State API Endpoint | Partial — `LLMUsageGuard.get_state()` method exists; API route not verified |

---

*End of Addendum (2026-06-18)*

---

## Addendum (2026-06-18): P4-07–P4-11 Unblocking Decision

### Decision: Move P4-07–P4-11 to **Pending**

The original roadmap stated P4-07–P4-11 were "explicitly deferred until Redis storage ships" and also needed "real usage patterns, auth completion, and tenant isolation." All three blockers have been verified as resolved.

### Blocker Verification

| Blocker | Original Claim | Verified Status | Evidence |
| :--- | :--- | :--- | :--- |
| **P4-03 Redis storage** | "Required before production enforcement" | ✅ Done | `src/llm/usage_store.py:630-770` — `RedisUsageStore` with Lua atomic scripts. Activates when `REDIS_URL` is set. |
| **Auth completion** | Implied prerequisite | ✅ Done | JWT middleware (`spine_api/core/middleware.py:38`), `get_current_user`, `get_current_agency_id`, `get_current_agency` implemented and used in 20+ routers. |
| **Tenant isolation** | Implied prerequisite | ✅ Done | RLS via Alembic migrations (`alembic/versions/add_rls_tenant_isolation.py`), `spine_api/core/rls.py` with `ContextVar`, all routes use `Depends(get_current_agency)`. |

### What Exists Today

- `AgencySettings` dataclass with `LLMGuardSettings` — `src/intake/config/agency_settings.py:195-219`
- Settings router with operational, autonomy, and seasonal endpoints — `spine_api/routers/settings.py`
- `plan_label` field on `AgencySettings` — lightweight tier label, not a full tier system

### What Does NOT Exist Yet

- `AiAgentSettings` dataclass — **0 matches in codebase**
- `SupportSettings` dataclass — **0 matches in codebase**
- `CommSettings` dataclass — **0 matches in codebase**
- `AgencyTier` enum (Starter/Pro/Enterprise) — **0 matches in codebase**
- Admin UI for agency settings — settings pages exist but no tier/plan management UI

### Updated Status for P4-07–P4-11

| ID | Task | Original Status | New Status | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **P4-07** | `AiAgentSettings` Dataclass | Blocked | **Pending** | All dependencies met. Needs product spec on what agent settings an agency should control. |
| **P4-08** | `SupportSettings` Dataclass | Blocked | **Pending** | All dependencies met. Needs product spec on support channel configuration per agency. |
| **P4-09** | `CommSettings` Dataclass | Blocked | **Pending** | All dependencies met. Needs product spec on communication preferences per agency. |
| **P4-10** | `AgencyTier` (Starter/Pro/Enterprise) | Blocked | **Pending** | All dependencies met. Needs product decision on tiering model and what each tier gates. |
| **P4-11** | Admin UI for Agency Settings | Blocked | **Pending** | All dependencies met. Depends on P4-07–P4-10 for data model. |

### Sequencing Recommendation

P4-07–P4-10 are independent data model tasks. P4-11 (Admin UI) depends on all four. Recommended order:

1. **P4-10 (AgencyTier)** first — defines the tiering model that P4-07–P4-09 may reference
2. **P4-07, P4-08, P4-09** in parallel — independent dataclasses
3. **P4-11 (Admin UI)** last — needs all data models finalized

### Risk Note

These are platform features, not core product features. They enable multi-tenant commercial operations (tiered plans, per-agency feature gating). If the product direction has shifted away from tiered pricing, these items should be re-evaluated or removed rather than implemented speculatively.

---

*End of Addendum (2026-06-18)*
