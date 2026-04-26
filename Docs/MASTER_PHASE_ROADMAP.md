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
| **Phase 3** | Agentic Autonomy | Pending | Self-healing agents, compliance blocks, prompt tuning. |
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
| **P3-01** | **Self-Healing Agent (`recovery_agent.py`)** | Backend | P1-01, P1-03 |
| **P3-02** | **Compliance Hard-Gates** | Backend | P1-05 |
| **P3-03** | **Prompt Tuning Agent (Feedback Loop)** | Backend | P1-04 |
| **P3-04** | **Scenario Replay Engine (QA Tool)** | Dev/QA | Phase 1 |

---

## 4. Phase 4: LLM Cost & Per-Agency Controls (Active — Dogfood Only)

**Production status**: Guard is DOGFOOD-ONLY (single-process, in-memory). See `Docs/LLM_USAGE_GUARD_AND_AGENCY_CONTROLS_2026-04-26.md`.

**Next required work**: P4-03 (Redis-backed guard storage) — required before production enforcement.

| ID | Task | Status | Owner | Dependencies | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P4-01** | **LLM Usage Guard (`LLMUsageGuard`)** | ✅ Done | Backend | None | Functional, single-process |
| **P4-02** | **Per-Agency LLM Guard Config** | ✅ Done | Backend | P4-01 | `LLMGuardSettings` in SQLite |
| **P4-03** | **Redis-Backed Guard Storage** | **Pending — P0** | Backend | P4-01 | Required for production |
| **P4-04** | **Per-Model Rate Limits** | Pending | Backend | P4-03 | After Redis storage |
| **P4-05** | **Alert Delivery (email/webhook)** | Pending | Backend | P4-03 | After Redis storage |
| **P4-06** | **Guard State API Endpoint** | Pending | Backend | P4-03 | After Redis storage |
| **P4-07** | **`AiAgentSettings` Dataclass** | Blocked | Backend | P4-03 | Platform feature, not next |
| **P4-08** | **`SupportSettings` Dataclass** | Blocked | Backend | P4-03 | Platform feature, not next |
| **P4-09** | **`CommSettings` Dataclass** | Blocked | Backend | P4-03 | Platform feature, not next |
| **P4-10** | **`AgencyTier` (Starter/Pro/Enterprise)** | Blocked | Backend | P4-03 | Platform feature, not next |
| **P4-11** | **Admin UI for Agency Settings** | Blocked | Frontend | P4-03 | Platform feature, not next |

> **P4-07 through P4-11 are explicitly deferred** until Redis storage ships. They need real usage patterns, auth completion, and tenant isolation.

See `Docs/LLM_USAGE_GUARD_AND_AGENCY_CONTROLS_2026-04-26.md` for full details.

---

## 4. Execution Rules (Mandatory)
- **SSOT First**: All UI components *must* derive data from `useUnifiedState()`. No manual client-side sums.
- **Fail Loudly**: If data integrity is compromised, UI *must* render a critical error.
- **Traceability**: All agentic actions (especially self-healing) *must* be logged to the `AuditStore`.
- **Review Protocol**: Minimum 2-cycle review for schema changes (Cycle 1: Logic, Cycle 2: Fallbacks/Defensive).

---

## 5. Verification Gateways
- **Mathematical Integrity**: `tests/test_integrity.py` must pass for every build.
- **Coverage**: All P1 tasks require explicit test coverage for the `AuditStore` logging.
- **Handoff**: Every task completion must produce a structured handoff document following the `IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`.

*Note: This roadmap is the source of truth for all current and future work. Any new task must be mapped to this structure before implementation begins.*
