# Feature List V2 — Runtime + Docs + Exploration

Date: 2026-05-12  
Status: Active working inventory (runtime-truth first; docs/specs included)  
Purpose: Canonical feature inventory with explicit status, value, dependencies, and build path.

## Method

1. Read instruction stack and session context:
- `/Users/pranay/AGENTS.md`
- `/Users/pranay/Projects/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/AGENTS.md`

2. Runtime-first evidence:
- backend API/routers: `spine_api/server.py`, `spine_api/routers/*.py`
- frontend route surfaces: `frontend/src/app/**/page.tsx`, `frontend/src/app/api/**/route.ts`
- frontend nav + rollout gates: `frontend/src/lib/nav-modules.ts`
- frontend BFF contract map: `frontend/src/lib/route-map.ts`

3. Spec/exploration evidence:
- `frontend/docs/*_MASTER_INDEX.md`
- `Docs/exploration/backlog.md`
- prior completeness/status docs in `Docs/`

## Status Legend

- `LIVE`: implemented and reachable in current runtime/API/UI contracts.
- `PARTIAL`: implemented in slices but not end-to-end or not fully exposed.
- `GATED`: implemented but intentionally disabled pending gates.
- `SPEC`: documented/planned architecture with no canonical runtime path yet.
- `EXPLORE`: identified as next frontier; not yet committed implementation.

---

## A) Platform + Security + Identity

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Auth signup/login/logout/refresh/me | LIVE | P0 | Secure account/session lifecycle | JWT + cookies + auth router | Harden policy + telemetry + abuse controls | `spine_api/routers/auth.py`, `frontend/src/app/api/auth/*` |
| Password reset + code validation | LIVE | P1 | Account recovery and trust | Email/token flows | Improve UX, expiry messaging, anti-abuse checks | `spine_api/routers/auth.py`, `frontend/src/app/(auth)/*` |
| Join invite flow | LIVE | P1 | Team onboarding without manual ops | Team + auth + membership | Add role templates and invite analytics | `spine_api/routers/auth.py`, `frontend/src/app/(auth)/join/[code]/page.tsx` |
| Multi-tenant isolation model | PARTIAL | P0 | Data isolation and compliance | agency/user membership contracts | Expand RLS coverage audits and invariant tests | `spine_api/core/rls.py`, `spine_api/models/*` |
| Rate limiting/security envelopes | PARTIAL | P0 | Abuse resistance and reliability | auth + middleware | Tighten per-endpoint policies and observability | `tests/test_rate_limiter.py`, router stack |

## B) Core Agency Operating Surfaces

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Overview command center | LIVE | P0 | Daily operational entrypoint | summary services + widgets | Expand health/SLA/owner KPIs | `frontend/src/app/(agency)/overview/page.tsx` |
| Lead inbox | LIVE | P0 | Intake triage and queue control | inbox API + assignment + sort/filter | Optimize for high-volume workflows | `spine_api/routers/inbox.py`, `frontend/src/app/(agency)/inbox/page.tsx` |
| Quote review surface | LIVE | P0 | Human risk control before customer output | review endpoints + risk flags | Add richer diff/justification and review automation | `frontend/src/app/(agency)/reviews/page.tsx`, `spine_api/routers/analytics.py` |
| Trips in planning | LIVE | P0 | Work-in-progress trip lifecycle | trips API + stage model | Improve bulk progression and planner ergonomics | `frontend/src/app/(agency)/trips/page.tsx`, `spine_api/server.py` |
| Workbench shell | LIVE | P0 | End-to-end operator workflow | run pipeline + stage tabs | Continue stage-specific hardening | `frontend/src/app/(agency)/workbench/page.tsx` |
| Audit workspace | LIVE | P1 | Fit/waste/compliance diagnostics | audit router + presentation | Expand report templates + export controls | `frontend/src/app/(agency)/audit/page.tsx`, `spine_api/routers/audit.py` |
| Insights workspace | LIVE | P1 | Ops/perf/revenue intelligence | analytics routers + charts | Add actionability and anomaly detection | `frontend/src/app/(agency)/insights/page.tsx`, `spine_api/routers/analytics.py` |
| Settings workspace | LIVE | P0 | Agency governance controls | settings/team/autonomy APIs | Consolidate policy-as-data model | `frontend/src/app/(agency)/settings/page.tsx`, `spine_api/routers/settings.py` |

## C) Pipeline + Decision + Suitability

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Async run orchestration (`/run`, `/runs/*`) | LIVE | P0 | Non-blocking execution and progress | run ledger + event store | Optimize throughput + retries + timeout policy | `spine_api/server.py`, `spine_api/routers/run_status.py` |
| Stage checkpoint ledger | LIVE | P0 | Recoverability + explainability | run ledger persistence | Add integrity audits and replay diagnostics | `spine_api/run_ledger.py` |
| Pipeline stage events | LIVE | P0 | Timeline/observability trace | run event emitter | Add SLA-linked event quality checks | `spine_api/run_events.py` |
| Decision state generation | LIVE | P0 | Ready/review/block outcomes | intake + validation + decision logic | Tighten contract tests and rationale quality | `src/decision/*`, `spine_api/contract.py` |
| Suitability flags endpoint | LIVE | P0 | Risk-fit visibility for operators | suitability module + trip data | Expand per-person utility and calibration | `spine_api/server.py:/trips/{trip_id}/suitability`, `src/suitability/*` |
| Suitability acknowledge gate | LIVE | P0 | Prevent unsafe approvals | critical-flag gating | Add policy configuration per agency | `spine_api/routers/legacy_ops.py`, frontend review controls tests |
| Reassess trip | LIVE | P1 | Recompute after changed facts | pipeline rerun + history | Add diff-aware reassessment UX | `spine_api/server.py:/trips/{trip_id}/reassess` |
| Live checker enrichment for public checker | PARTIAL | P1 | Adds external risk signals to decisions | live checker service + eval manifest | Expand providers and confidence controls | `spine_api/services/live_checker_service.py` |

## D) Assignment + Follow-up + Team Ops

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Assignment state actions (assign/claim/escalate/reassign/return/unassign) | LIVE | P0 | Work ownership clarity | assignment router + audit | Add policy-driven auto-routing | `spine_api/routers/assignments.py` |
| Legacy assignment routes | PARTIAL | P2 | Backward compatibility | legacy ops router | Deprecate safely after contract parity | `spine_api/routers/legacy_ops.py` |
| Follow-up dashboard | LIVE | P1 | SLA and customer response management | followups router + inbox data | Add predictive follow-up prioritization | `spine_api/routers/followups.py`, frontend followup routes |
| Follow-up actions (complete/snooze/reschedule) | LIVE | P1 | Maintains queue quality | timeline + audit + notifications | Add bulk and policy automation | `spine_api/routers/followups.py` |
| Team members/workload | LIVE | P1 | Staffing and load balancing | team router + membership model | Add staffing recommendations and trend analysis | `spine_api/routers/team.py` |

## E) Drafts + Work Preservation

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Draft CRUD lifecycle | LIVE | P1 | Persistent in-progress work | draft store + API | Migrate toward SQL-backed canonical store | `spine_api/routers/drafts.py`, `spine_api/draft_store.py` |
| Draft events and run linkage | LIVE | P1 | Full trace from draft to run/trip | pipeline execution service + audit | Add richer conflict resolution and merge UX | `spine_api/services/pipeline_execution_service.py` |
| Draft promote-to-trip flow | LIVE | P1 | Converts pre-work into operational trip | draft + trip contracts | Harden promotion checks and rollback semantics | `spine_api/routers/drafts.py` |

## F) Documents + Booking Collection + Extraction

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Booking collection link lifecycle | LIVE | P0 | Secure traveler data collection | token model + public endpoints | Add fraud controls + expiration analytics | `spine_api/server.py:/trips/{trip_id}/collection-link` |
| Pending booking data accept/reject | LIVE | P0 | Human verification before state mutation | pending booking state model | Add policy templates per trip type | `spine_api/server.py:/pending-booking-data*` |
| Public booking-collection surface | LIVE | P0 | Traveler submission UX | token validation + public API | Improve accessibility/mobile completion rate | `frontend/src/app/(public)/booking-collection/[token]/page.tsx` |
| Public booking document upload | LIVE | P0 | Evidence intake from traveler | document storage + token scope | Add inline validation and progress feedback | `spine_api/routers/public_collection.py` |
| Document upload/list/review/delete/download-url | LIVE | P0 | Structured evidence operations | document models + storage signer | Add retention policy and quarantine paths | `spine_api/server.py:/documents*`, `spine_api/services/document_storage.py` |
| Document extraction run/get/retry | LIVE | P1 | Faster structured data capture | extraction service + attempts | Add provider strategy and quality scoring | `spine_api/server.py:/extraction*` |
| Extraction apply/reject with attempts ledger | LIVE | P1 | Controlled mutation with auditability | extraction models + event log | Add field-level confidence UX | `spine_api/models/tenant.py`, extraction endpoints |
| `/documents` top-level module enablement | GATED | P0 | Dedicated operations module UX | rollout gates + contract tests | Complete remaining regression suite gate | `frontend/src/lib/nav-modules.ts` |

## G) Confirmations + Booking Tasks + Execution Timeline

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Booking tasks API | LIVE | P1 | Structured post-quote execution steps | booking task model + router | Add templates by trip archetype | `spine_api/routers/booking_tasks.py` |
| Booking confirmations API | LIVE | P1 | Durable supplier confirmation tracking | confirmation service + private fields | Add reconciliation automation | `spine_api/routers/confirmations.py` |
| Execution event ledger + timeline | LIVE | P1 | Operational chronology and accountability | execution_event_service + timeline endpoints | Expand to full cross-module provenance | `spine_api/services/execution_event_service.py`, `spine_api/routers/trip_observability.py` |

## H) Analytics + Intelligence + Reporting

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Analytics summary/pipeline/team/revenue/bottlenecks | LIVE | P1 | Performance intelligence | analytics models + data aggregation | Add metric contract ownership and alerting ties | `spine_api/routers/analytics.py` |
| Escalations/funnel/alerts | LIVE | P1 | Operational risk and conversion control | analytics events + review system | Add prescribed actions/playbooks | `spine_api/routers/analytics.py` |
| Agent drill-down analytics | LIVE | P1 | Performance diagnosis per operator | analytics + assignments + reviews | Add coaching recommendations | `spine_api/routers/analytics.py:/analytics/agent/{agent_id}/drill-down` |
| Product-B KPI endpoint | LIVE | P2 | Separate tracking for Product-B funnel | analytics product-b route | Define authoritative KPI dictionary | `spine_api/routers/product_b_analytics.py` |
| Analytics export | LIVE | P1 | External reporting + governance | analytics serializer + access control | Add row-level security checks and export policy | `spine_api/routers/analytics.py:/analytics/export` |

## I) System Health + Runtime Control Plane

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Health endpoint | LIVE | P0 | Basic liveness readiness signal | health router + dependencies | Add deep readiness sub-checks | `spine_api/routers/health.py` |
| Unified system state + integrity issues | LIVE | P1 | Platform observability for operators | system dashboard router | Tighten ownership and incident hooks | `spine_api/routers/system_dashboard.py` |
| Agent runtime status/events/run-once | LIVE | P1 | Runtime governance for agent loops | runtime coordinator + event stream | Add permission tiers and runbook links | `spine_api/routers/agent_runtime.py` |
| Frontier endpoints (ghost/emotion/intelligence) | PARTIAL | P2 | Experimental intelligence surfaces | frontier router + models | Clarify production boundary and SLA | `spine_api/routers/frontier.py` |

## J) Frontend BFF Contract and Navigation Governance

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Deny-by-default BFF catch-all routing | LIVE | P0 | Prevents accidental backend surface drift | explicit route map | Keep strict contract tests for all mapped routes | `frontend/src/app/api/[...path]/route.ts`, `frontend/src/lib/route-map.ts` |
| Route-level timeout policy registry | LIVE | P1 | Prevents flaky long-run proxy behavior | route-map config + proxy core | Expand endpoint-specific policies | `frontend/src/lib/route-map.ts` |
| Nav taxonomy as product-module model | LIVE | P1 | Prevents persona-route fragmentation | nav model + shell UI | Keep durable IA contract with tests | `frontend/src/lib/nav-modules.ts` |
| Disabled/planned modules in nav (`quotes`,`bookings`,`payments`,`suppliers`,`knowledge`) | SPEC | P1 | Signals intended operating model | module shells + backend contracts | Implement each on canonical contracts before enablement | `frontend/src/lib/nav-modules.ts` |

## K) Traveler/Public Surfaces

| Feature | Status | Priority | Value | Dependency | Build Path | Evidence |
|---|---|---:|---|---|---|---|
| Itinerary checker UI + public-checker backend | PARTIAL | P1 | Consumer wedge and lead-gen utility | public-checker run + event capture | Harden conversion loop to agency handoff | `frontend/src/app/(traveler)/itinerary-checker/page.tsx`, `/api/public-checker/*` |
| Marketing/landing variants (`/`, `/v2`…`/v5`) | PARTIAL | P2 | Messaging and conversion experimentation | analytics + CTA instrumentation | Consolidate learnings into one canonical funnel | `frontend/src/app/page.tsx`, `frontend/src/app/v*/page.tsx` |

## L) Spec-Heavy Feature Families (Documented, not runtime-canonical yet)

These families are heavily documented in `frontend/docs/*_MASTER_INDEX.md` and `Docs/*`, but not yet represented as full canonical runtime modules:

| Family | Status | Priority | Why it matters | Build Path Anchor |
|---|---|---:|---|---|
| Quote/Output template engine + versioning | SPEC | P1 | Customer-ready artifacts and governance | start from canonical doc contracts; avoid parallel renderer paths |
| Payments and settlement operations | SPEC | P1 | Revenue assurance and booking closure | attach to booking_data + task/confirmation lifecycle |
| Supplier management + reliability intelligence | SPEC | P1 | Execution quality and margin protection | integrate with confirmations + risk events + sourcing |
| Knowledge base/agency memory | SPEC | P2 | Organizational learning and consistency | tie to trip outcomes + overrides + review rationale |
| Traveler portal end-to-end | SPEC | P2 | Customer self-service and transparency | evolve from booking-collection/public-checker surfaces |
| Multi-currency/forex operations | SPEC | P2 | Margin and quote correctness | extend existing currency utilities + pricing contracts |
| Regulatory/compliance suites (privacy, legal templates, audits) | SPEC | P1 | Legal risk containment | policy-as-data engine linked to workflow checkpoints |
| Collaboration/workflow builder modules | SPEC | P2 | Agency-scale automation | leverage existing assignments/followups/events primitives |

## M) New Exploration Candidates (Online-validated; added to backlog)

| Candidate | Status | Priority | Why now | Sources |
|---|---|---:|---|---|
| Timatic-class travel document precheck | EXPLORE | P1 | Prevent downstream visa/document failure | IATA Timatic AutoCheck + IATA developer profile |
| US refund-rights rules engine | EXPLORE | P1 | High legal/commercial impact in disruption flows | US DOT ticket refunds + final rule PDF |
| EU package-travel obligations engine | EXPLORE | P1 | Structured compliance for organizer duties | EC PTD page + Council update |
| Agency credential verification trust layer | EXPLORE | P2 | Safer supplier/agency action automation | IATA CheckACode technical spec |
| Multi-jurisdiction traveler-rights policy engine | EXPLORE | P1 | Reusable compliance substrate across workflows | policy-as-data architecture extension |

---

## Feature Count Snapshot (V2)

- Runtime/API feature surfaces identified: 70+ (LIVE/PARTIAL/GATED)
- Spec-heavy feature families tracked: 8
- New online-validated exploration candidates: 5

## First-Principles Judgment

1. The repository already contains a meaningful operational core; this is not a greenfield app.
2. The next major leverage is not adding random modules; it is completing canonical, contract-tested vertical slices:
- documents/extraction -> dedicated documents module enablement,
- quote/output governance,
- compliance policy-as-data,
- supplier/payment closure loops.
3. Biggest long-term architecture risk is drift between spec docs and runtime truth.  
   Keep this file and nav/route contracts as runtime source-of-truth references.

## Verification Notes

- This update is documentation-only and non-mutating to runtime code paths.
- No destructive git actions were used.

