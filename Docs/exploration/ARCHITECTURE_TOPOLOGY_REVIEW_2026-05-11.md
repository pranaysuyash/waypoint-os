# Architecture Topology Review

**Date:** 2026-05-11  
**Status:** Exploration note  
**Question:** Is the current system a monolith, microservices, or something else, and should Waypoint OS move to a different topology?

---

## Short Answer

Waypoint OS is currently a **modular monorepo with a BFF plus a backend modular monolith**.

It is not a classic single-process monolith because the browser-facing application and backend run as separate processes:

```text
Browser
  -> Next.js app and BFF routes on :3000
  -> FastAPI spine_api on :8000
  -> in-process domain modules under src/
  -> PostgreSQL plus remaining file-backed stores
```

It is also not microservices. There is one primary backend deployable, one primary frontend deployable, no service-owned databases, no brokered inter-service event bus, and no independently deployable domain services. Most boundaries are module boundaries, not runtime/service boundaries.

The best label is:

> **BFF + modular monolith, with a few early distributed-system pressures.**

This is the right broad topology for the current stage. The wrong move would be premature microservices. The right move is to make the modular monolith more explicit: route ownership, domain services, async job boundaries, persistence ownership, and integration adapters.

---

## Evidence From The Codebase

### Runtime Topology

- [frontend/README.md](../../frontend/README.md) describes the intended runtime as `Browser -> Next.js -> spine_api FastAPI -> run_spine_once`.
- [spine_api/server.py](../../spine_api/server.py) defines one FastAPI app and includes routers for auth, workspace, frontier, audit, assignments, run status, health, dashboard, followups, team, product analytics, booking tasks, and confirmations.
- [frontend/src/lib/proxy-core.ts](../../frontend/src/lib/proxy-core.ts) is a generic BFF proxy from Next.js API routes to FastAPI.
- [frontend/src/lib/route-map.ts](../../frontend/src/lib/route-map.ts) is a deny-by-default route registry for BFF-to-backend mapping.
- [docker-compose.yml](../../docker-compose.yml) only defines PostgreSQL as infrastructure; it does not define separate domain services.

### Backend Shape

- [spine_api/server.py](../../spine_api/server.py) is still a large route/application module, about 4,500 lines at review time.
- The backend already has modular extraction points:
  - [spine_api/routers/](../../spine_api/routers/) for some route groups.
  - [spine_api/services/](../../spine_api/services/) for domain/application services.
  - [spine_api/models/](../../spine_api/models/) for SQLAlchemy models.
  - [spine_api/contract.py](../../spine_api/contract.py) for API contracts.
- The core trip pipeline remains in-process:
  - [src/intake/orchestration.py](../../src/intake/orchestration.py) exposes `run_spine_once()`.
  - [spine_api/services/pipeline_execution_service.py](../../spine_api/services/pipeline_execution_service.py) wraps that pipeline, checkpoints steps, emits run events, and persists results.

### Persistence Shape

- [spine_api/core/database.py](../../spine_api/core/database.py) defines the async SQLAlchemy engine/session for PostgreSQL.
- [spine_api/core/rls.py](../../spine_api/core/rls.py) implements PostgreSQL RLS context for tenant isolation.
- [spine_api/persistence.py](../../spine_api/persistence.py) still contains a dual persistence facade:
  - `FileTripStore`
  - `SQLTripStore`
  - `TripStore` facade selected by `TRIPSTORE_BACKEND`
- [Docs/TRIP_STATE_CONTRACT.md](../TRIP_STATE_CONTRACT.md) states the current contract: flat trip state in one trips table with encrypted JSON compartments, with exit criteria for splitting private state or booking state later.

### Async And Agent Pressure

- `/run` accepts a request and starts pipeline work in a daemon thread in [spine_api/server.py](../../spine_api/server.py).
- [spine_api/run_ledger.py](../../spine_api/run_ledger.py), [spine_api/run_events.py](../../spine_api/run_events.py), and [spine_api/routers/run_status.py](../../spine_api/routers/run_status.py) provide execution-state tracking.
- [src/agents/runtime.py](../../src/agents/runtime.py) and [src/agents/recovery_agent.py](../../src/agents/recovery_agent.py) show early background-agent runtime concepts.

These are not microservices yet, but they are the areas most likely to need durable queues, workers, and stronger process boundaries.

---

## What We Have Today

### 1. Frontend/BFF Layer

The Next.js app is both UI and BFF. It owns:

- authenticated browser experience,
- API route mapping,
- cookie/header forwarding,
- frontend-local scenario routes,
- some response adapters and fallback shaping.

This is useful. It keeps browser auth and frontend routing close to the UI while hiding the internal FastAPI origin.

Risk: there are both catch-all mapped proxy routes and explicit hand-authored API routes. That is not inherently wrong, but it can drift unless route ownership is documented and tests enforce parity.

### 2. FastAPI Application Layer

FastAPI is the main backend application. It owns:

- auth and workspace membership,
- trip lifecycle,
- run submission/status,
- inbox/projections,
- team and assignments,
- booking collection,
- documents and extraction,
- analytics and settings,
- public checker,
- background agent controls.

This is a classic modular-monolith responsibility set. The issue is not that these live in one backend process. The issue is that some of them still live in one very large `server.py`.

### 3. Domain Pipeline Layer

The `src/` tree is the core product brain:

- intake,
- validation,
- decision,
- strategy,
- safety,
- suitability,
- extraction,
- LLM clients,
- public checker,
- analytics/policy rules.

This layer is mostly in-process library code, called by FastAPI. That is good for latency, debugging, and contract control while the product surface is still evolving.

### 4. Persistence Layer

The product has moved toward PostgreSQL, but it is not yet cleanly one-store:

- tenant/auth/workspace/document/task models are SQL-backed,
- trip state has `SQLTripStore`,
- legacy/file-backed stores and facades still exist,
- `TRIPSTORE_BACKEND` is an important runtime switch and has already caused split-brain risk.

From an architecture standpoint, the persistence layer is the highest-leverage cleanup before any service extraction.

### 5. Observability And Workflow State

The product has run-ledger, audit, timeline, execution events, and OpenTelemetry traces. That is the right direction. The current question is whether those streams become:

- internal module APIs only,
- durable events in Postgres,
- or a brokered event bus.

At this stage, Postgres-backed durable events are likely enough. A full broker can wait.

---

## What This Is Not

### Not A Pure Monolith

Because the UI/BFF and backend are separate runtimes, and the backend already has domain/service/contract boundaries.

### Not Microservices

Because there is no independent deployability or service-owned data boundary. The domain modules do not communicate over network APIs; they are imported and called in-process.

### Not Serverless-First

Long-running pipeline execution, background agents, Postgres sessions, document extraction, and local/dev process assumptions point away from pure serverless as the primary backend model.

### Not Event-Driven Yet

The system has events, ledgers, and audit records, but they are not yet the backbone of inter-service communication.

---

## Should We Move To Something Different?

### Recommendation

Do **not** move to microservices now.

Do move toward a more explicit **modular monolith with service-ready boundaries**:

```text
Next.js UI/BFF
  -> FastAPI application shell
     -> Route modules
     -> Application services
     -> Domain modules
     -> Persistence repositories
     -> Durable run/event tables
     -> Optional worker process for long-running jobs
```

This preserves speed and architectural coherence while preventing the backend from becoming a ball of routes and global stores.

### Why This Fits The Business

Waypoint OS is still discovering the exact operational workflow for boutique agencies: inbox, intake, readiness, proposal, booking data, documents, confirmations, routing, analytics, and agent automation. Microservices punish that kind of discovery because every domain boundary becomes operational overhead.

The current product needs:

- fast iteration on the operator workflow,
- strong API/data contracts,
- tenant isolation,
- reliable run execution,
- document/booking data safety,
- integration adapters for real-world travel ops.

None of those require microservices first. They require clean ownership boundaries first.

---

## Where A Different Topology May Make Sense Later

### Good Candidates For Future Extraction

1. **Worker / Job Execution**
   - Pipeline runs, document extraction, OCR, LLM work, and recovery agents can move behind a durable queue.
   - This can start as a separate worker process in the same repo before becoming a service.

2. **Integration Connectors**
   - WhatsApp, email, GDS/flight APIs, hotel APIs, payments, CRM sync.
   - These are high-failure, rate-limited, credential-sensitive boundaries.
   - They benefit from adapter isolation and retry policies.

3. **Document Processing**
   - Upload storage, extraction attempts, OCR, PDF/image parsing, virus scanning, and signed URLs can become a bounded subsystem.
   - It can remain one deployable until volume/security requires extraction.

4. **Analytics / Reporting**
   - Once metrics are derived from durable events, analytics can be served from projections/materialized views.
   - This is a good read-model boundary, not necessarily an early microservice.

5. **Public Traveler Collection**
   - Public unauthenticated surfaces have different security/rate-limit needs.
   - They may eventually justify a separate edge/public API, but current tokenized endpoints can remain in FastAPI.

### Poor Candidates For Early Extraction

1. **Core intake/decision/strategy pipeline**
   - This is the product brain and is still evolving.
   - Keep in-process until contracts, latency, and data boundaries stabilize.

2. **Trip state**
   - Split storage before split services.
   - Service extraction before persistence consolidation would amplify the existing split-brain risk.

3. **Auth/workspace membership**
   - Keep centralized while tenant/RLS semantics are still being hardened.

---

## Topology Options Considered

| Option                                   | Verdict                 | Why                                                                 |
| ---------------------------------------- | ----------------------- | ------------------------------------------------------------------- |
| Keep current shape exactly               | Reject                  | `server.py`, dual stores, and route-map drift will compound.        |
| Big backend rewrite                      | Reject                  | High risk, low product value right now.                             |
| Full microservices                       | Reject for now          | Operational overhead before domain boundaries are stable.           |
| Serverless-first                         | Reject for core backend | Long-running jobs and stateful execution do not fit cleanly.        |
| Modular monolith + BFF + worker boundary | Accept                  | Best balance of speed, correctness, and future extraction.          |
| Event-driven modular monolith            | Accept as direction     | Use durable events/projections internally before broker extraction. |

---

## Proposed Target Architecture

```text
Browser
  |
  v
Next.js App + BFF
  - UI routes
  - authenticated API proxy
  - frontend-local scenario fixtures
  - response adapters only when needed
  |
  v
FastAPI Application Shell
  - auth/workspace middleware
  - route registry
  - request/response contracts
  |
  v
Application Services
  - TripLifecycleService
  - RunSubmissionService
  - InboxProjectionService
  - BookingCollectionService
  - DocumentService
  - AssignmentService
  - SettingsService
  |
  v
Domain Modules
  - intake/orchestration
  - decision
  - suitability
  - safety
  - strategy
  - extraction
  |
  v
Persistence
  - PostgreSQL as source of truth
  - RLS for tenant isolation
  - encrypted JSON compartments where appropriate
  - durable run/audit/execution-event tables
  |
  v
Optional Worker Process
  - pipeline execution
  - document extraction
  - external connector retries
  - recovery agents
```

The target is still one repo and probably two or three deployables:

1. `frontend` Next.js
2. `spine_api` FastAPI
3. optional `spine_worker` process

That is not microservices. It is a modular product platform with clean process boundaries where they matter.

---

## Practical Migration Path

### Phase 0 — Name The Architecture

Document the current architecture as:

> **Waypoint OS uses a BFF + backend modular monolith architecture. The backend is organized around route modules, application services, domain pipeline modules, and PostgreSQL-backed persistence. Long-running and integration-heavy work may move to a worker process before any microservice extraction.**

This prevents future agents from forcing false choices between "monolith" and "microservices."

### Phase 1 — Finish Backend Modularity

Goal: reduce `spine_api/server.py` into an application shell.

Move remaining large endpoint clusters into routers and services:

- trips lifecycle,
- inbox,
- analytics,
- settings,
- documents/extraction,
- public checker,
- drafts.

Do not create duplicate route files for the same resource/action. Extend canonical routes per [AGENTS.md](../../AGENTS.md).

### Phase 2 — Consolidate Persistence Ownership

Goal: make PostgreSQL the only real source of truth for production-like flows.

Actions:

- keep `TRIPSTORE_BACKEND=sql` pinned,
- remove runtime ambiguity once all tests and fixtures support SQL,
- move run ledger/audit/event state toward SQL-backed durable tables where needed,
- keep encrypted JSON compartments until reporting/access-control requirements force splits.

### Phase 3 — Introduce A Worker Boundary

Goal: isolate long-running work without jumping to microservices.

Start with a same-repo worker process:

- accepts jobs from a Postgres-backed queue or a lightweight queue package,
- writes run status/events to the same durable store,
- handles pipeline runs, extraction retries, and connector retries.

This solves the real problem: long-running work should not depend on daemon threads inside the web process.

### Phase 4 — Adapterize External Integrations

Goal: protect the core from unreliable partner systems.

Create stable adapter contracts for:

- WhatsApp/email/SMS,
- document storage,
- flight/hotel/GDS APIs,
- CRM sync,
- payment gateways.

Adapters can stay in-process until rate limits, credentials, compliance, or uptime demands justify extraction.

### Phase 5 — Extract Only Proven Boundaries

A module graduates to an independent service only when it has:

- a stable public contract,
- independent scaling needs,
- independent failure domain,
- clear data ownership,
- operational monitoring,
- a reason to deploy separately.

Without those, extraction is ceremony.

---

## Architecture Guardrails

1. **One canonical route per resource/action.** Route extraction is good; duplicate route variants are not.
2. **Contracts before consumers.** Backend Pydantic contracts and frontend types must match runtime responses.
3. **Postgres before microservices.** Resolve persistence ambiguity before splitting deployables.
4. **Events before event bus.** Make durable business/run events reliable before adding a broker.
5. **Worker before service mesh.** Move long-running jobs out of the web process before extracting domain services.
6. **Adapters at the edge.** Keep partner/integration complexity outside core trip-state and decision modules.
7. **Domain modules stay boring.** The product brain should remain testable library code as long as possible.

---

## Open Questions

1. Should run ledger and audit store become SQL-backed now, or only when multi-worker execution is introduced?
2. Should public traveler collection stay inside the main FastAPI app until launch, or split earlier for security/rate-limit isolation?
3. Should the BFF route registry become the single canonical frontend route map, replacing hand-authored direct proxy routes over time?
4. Which integration is the first real forcing function: WhatsApp, email, CRM, document storage, or travel inventory?
5. What is the minimum worker infrastructure: Postgres queue, Redis/RQ, Celery, Dramatiq, or another package?

---

## Decision

**Current architecture:** BFF + backend modular monolith in a monorepo.  
**Near-term target:** Cleaner modular monolith plus optional worker process.  
**Do not do now:** Microservices, service mesh, broker-first event architecture, or a large rewrite.  
**Do next:** route/service modularization, persistence consolidation, and worker-boundary design.
