# Discovery Gap Analysis: Data Persistence & State Architecture

**Date**: 2026-04-16
**Gap Register**: #02 (P0 — foundational, blocks everything)
**Preceded By**: MASTER_GAP_REGISTER_2026-04-16.md
**Scope**: Database, ORM, migrations, state persistence, session management, data lifecycle

---

## 1. Executive Summary

The system has **zero persistence**. Every spine run produces results that vanish when the browser tab closes. No database, no ORM, no migrations, no DATABASE_URL, no database service in docker-compose, no database driver in pyproject.toml.

The DATA_STRATEGY research doc (524 lines) defines 10+ PostgreSQL tables. TECHNICAL_INFRASTRUCTURE recommends PostgreSQL + SQLAlchemy 2.0. The single-tenant MVP strategy defines a simplified schema. None of it is implemented.

The only "persistence" that exists: one `spine-api/persistence.py` file (246 lines) that writes JSON files to disk. And one localStorage usage (theme preferences).

**Bottom line**: Without this gap resolved, every other gap is academic. The system cannot be an operating system if it forgets everything.

---

## 2. Evidence Inventory

### 2.1 What's Documented

| Doc | What It Specifies | Location |
|-----|------------------|----------|
| `DATA_STRATEGY.md` | 10 PostgreSQL tables: customers, agencies, agents, sessions, packets, events, bookings, customer_embeddings, scenario_embeddings, consent_logs. JSONB for CanonicalPacket. pgvector for similarity. Retention policy. GDPR compliance. | Docs/research/ |
| `TECHNICAL_INFRASTRUCTURE.md` | Stack: PostgreSQL + SQLAlchemy 2.0 + Clerk + Render. Conversations table. SKIP LOCKED for job queue. Backup via Render + S3. | Docs/ |
| `SINGLE_TENANT_MVP_STRATEGY.md` | Simplified MVP schema: customers + packets without tenant_id. "No tenant filtering needed." | Docs/ |
| `FEEDBACK_LOOPS_AND_IMPROVEMENT.md` | `CREATE TABLE trip_logs` and `CREATE TABLE error_logs` with full column specs. | Docs/ |
| `UX_WHATSAPP_INTEGRATION_STRATEGY.md` | DB schema for conversation_turns, reminders, message_templates. | Docs/ |
| `LEAD_LIFECYCLE_AND_RETENTION.md` | Lifecycle schema block for CanonicalPacket persistence. | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` | "DATABASE / PERSISTENCE: ENTIRELY ABSENT" — 6/6 severity. | Docs/ |
| `CODEBASE_ANALYSIS_2026-04-12.md` | "No database schema — Can't persist — P0 — 3 days" | Docs/ |
| `specs/canonical_packet.schema.json` | JSON Schema defining all CanonicalPacket fields. The data contract for persistence. | specs/ |

### 2.2 What's Implemented

| Layer | Technology | What It Stores | Limitations |
|-------|-----------|---------------|-------------|
| **spine-api/persistence.py** | JSON file I/O | TripStore (individual trip JSONs in `data/trips/`), AssignmentStore (single `assignments.json`), AuditStore (single `events.json` with 10K rotation) | No concurrency safety, no transactions, no querying, no relations |
| **Frontend: themeStore.ts** | localStorage via Zustand persist | Theme, component variants, density | Only cosmetic state |
| **Frontend: workbench.ts** | URL query params | Workbench stage, mode, scenario | Lost on refresh; no data persistence |
| **geography.py** | Runtime JSON file | accumulated_cities.json | Concurrency issues documented |

**That's it.** Everything else is ephemeral — in-memory Python dataclasses and React useState/hooks.

### 2.3 What's NOT Implemented

- No PostgreSQL, SQLite, or any database
- No SQLAlchemy, psycopg2, asyncpg, or any DB driver
- No Alembic or migration infrastructure
- No `DATABASE_URL` in env config
- No database service in docker-compose.yml
- No database dependencies in pyproject.toml
- No CRUD APIs (trips endpoint is mock data only)
- No customer entity
- No supplier entity (G-01 from vendor gap analysis)
- No session/auth persistence
- No frontend data persistence (workbench results lost on refresh)
- No event store / audit trail persistence
- No file/document storage (S3 references in docs only)

### 2.4 Empty Scaffolded Directories

| Path | Purpose | Status |
|------|---------|--------|
| `src/config/` | DB config, connection strings | Empty |
| `src/schemas/` | ORM models, Pydantic persistence schemas | Empty |
| `src/adapters/` | Data access adapters, repository pattern | Empty |
| `src/agents/` | Multi-agent state management | Empty |
| `src/pipelines/` | Data pipelines, ETL | Empty |
| `src/utils/` | General utilities | Empty |

---

## 3. Gap Taxonomy

### 3.1 Structural Gaps

| Gap ID | Concept | Documented In | Implementation | Blocks |
|--------|---------|---------------|----------------|--------|
| **PS-01** | Database instance | DATA_STRATEGY, TECHNICAL_INFRASTRUCTURE | None — no DB running anywhere | All persistence |
| **PS-02** | ORM / data access layer | TECHNICAL_INFRASTRUCTURE (SQLAlchemy 2.0) | None — no ORM, no drivers in deps | All data access code |
| **PS-03** | Migration framework | Implied by DATA_STRATEGY schema | None — no Alembic, no migrations/ dir | Schema evolution |
| **PS-04** | Customer entity | DATA_STRATEGY L71-78, SINGLE_TENANT L128 | None — no table, no CRUD | #06 (lifecycle), #08 (auth), #11 (post-trip) |
| **PS-05** | Session entity | DATA_STRATEGY L99-107 | None — no conversation persistence | #03 (comms), #06 (lifecycle) |
| **PS-06** | Event store / audit trail | DATA_STRATEGY L132-138, event_log_and_snapshot_model.md | AuditStore (JSON file, 10K rotation) — inadequate for production | #13 (audit trail) |
| **PS-07** | File/document storage | DATA_ARCHITECTURE (S3 references) | None — no S3, no upload endpoint | #10 (document mgmt) |

### 3.2 Computation Gaps

| Gap ID | What Needs Computing | Current State | Blocked By |
|--------|---------------------|---------------|------------|
| **PC-01** | Trip CRUD (create, read, update, delete, list) | Read-only from JSON files; no create from frontend; no update workflow | PS-01, PS-02 |
| **PC-02** | Customer lookup / repeat detection | Keyword-based `is_repeat_customer` from raw text; no `customer_id` DB lookup | PS-04 |
| **PC-03** | Session state recovery | Each spine run is independent; no way to resume a session | PS-05 |
| **PC-04** | Cross-trip analytics | Impossible — no trip history persisted | PS-04, PS-01 |
| **PC-05** | Event replay / time-travel debugging | No event store; no snapshots | PS-06 |

### 3.3 Integration Gaps

| Gap ID | Integration | Designed In | Current State | Blocked By |
|--------|-------------|------------|---------------|------------|
| **PI-01** | Frontend → DB via API | Frontend calls mock data; real trips would come from DB | Mock data hardcoded in Next.js API routes | PS-01, PC-01 |
| **PI-02** | Spine run → trip persistence | `save_processed_trip()` exists in persistence.py | Saves to JSON file; not connected to Frontend listing | PS-01 |
| **PI-03** | Lifecycle state transitions | LEAD_LIFECYCLE 16-state machine | In-memory LifecycleInfo only; no cross-session state | PS-01, PS-04 |
| **PI-04** | Vector similarity search | DATA_STRATEGY pgvector | None — no embeddings, no vector index | PS-01 |

---

## 4. Data Model: What Needs to Be Persisted

Based on cross-referencing all specs, research, and code, these are the minimum viable tables:

```sql
-- Phase 1: Core entities (unblocks gap #02 resolution)

CREATE TABLE agencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    tier TEXT DEFAULT 'solo',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID REFERENCES agencies(id),
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'senior', 'junior', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_active_at TIMESTAMPTZ
);

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID REFERENCES agencies(id),
    phone TEXT,
    email TEXT,
    name TEXT,
    notes TEXT,
    first_seen_at TIMESTAMPTZ DEFAULT now(),
    last_interaction_at TIMESTAMPTZ
);

CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID REFERENCES agencies(id),
    customer_id UUID REFERENCES customers(id),
    agent_id UUID REFERENCES agents(id),
    status TEXT NOT NULL DEFAULT 'NEW_LEAD',
    packet JSONB NOT NULL,
    decision_result JSONB,
    strategy_result JSONB,
    share_token TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID REFERENCES trips(id),
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_trips_agency ON trips(agency_id);
CREATE INDEX idx_trips_customer ON trips(customer_id);
CREATE INDEX idx_trips_agent ON trips(agent_id);
CREATE INDEX idx_trips_status ON trips(status);
CREATE INDEX idx_trips_share_token ON trips(share_token);
CREATE INDEX idx_events_trip ON events(trip_id);
CREATE INDEX idx_events_type ON events(event_type);
```

### Phase 2: When other gaps unblock

- Suppliers table (gap #01)
- Conversation turns (gap #03)
- Documents/attachments (gap #10)
- Bookings (gap #04/#05)
- Embeddings with pgvector (gap #07)
- Consent logs (privacy/compliance)

---

## 5. Dependency Graph

```
PS-01 (Database Instance)
  └── PS-02 (ORM / Data Access)
       ├── PS-04 (Customer Entity) ──> #06 Lifecycle, #08 Auth
       ├── PS-05 (Session Entity) ──> #03 Comms, #06 Lifecycle
       ├── PC-01 (Trip CRUD) ──> #03 Proposal delivery, #04 Financial state
       └── PS-06 (Event Store) ──> #13 Audit Trail

PS-03 (Migration Framework)
  └── Enables schema evolution without data loss

PI-01 (Frontend → DB)
  └── Depends on PS-01 + PS-02 + API routes

PI-03 (Lifecycle Transitions)
  └── Depends on PS-01 + PS-04 (customer persistence)
```

**Critical path**: PS-01 → PS-02 → PS-04/PC-01 → unblocks 12 downstream gaps.

---

## 6. Phase-In Recommendations

### Phase 1: Database Exists (P0, ~3 days)
1. Add PostgreSQL service to docker-compose.yml
2. Add sqlalchemy + asyncpg + alembic to pyproject.toml
3. Add DATABASE_URL to .env.example
4. Create initial migration with 5 core tables (agencies, agents, customers, trips, events)
5. Wire spine-api `save_processed_trip()` to write to DB instead of JSON files

**Acceptance**: `docker-compose up` starts Postgres. `alembic upgrade head` creates tables. Spine run persists to trips table. Frontend reads from `/api/trips` (now real DB data, not mock).

### Phase 2: Customer & Session Persistence (P0, ~2 days)
1. Add customer CRUD API endpoints
2. Wire `customer_id` lookup in NB01 extractors to real DB query
3. Add session recovery: load trip from DB by ID, resume pipeline state
4. Replace `is_repeat_customer` keyword detection with DB-based repeat detection

**Acceptance**: Returning customer with phone number is recognized. Trip can be re-opened after browser close. Lifecycle state persists across sessions.

### Phase 3: Event Store & Audit (P1, ~1 day)
1. Write events to `events` table on every significant action (field change, decision state change, strategy generated)
2. Add basic event query API (`GET /api/trips/{id}/events`)

**Acceptance**: "Who changed the budget?" is answerable via event log.

### Phase 4: File Storage (P1, ~2 days)
1. Add S3/R2 integration for document uploads
2. Add file upload API endpoint
3. Store document references in trips table (JSONB)

**Acceptance**: Passport image can be attached to a trip and retrieved later.

---

## 7. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| Which database? | (a) PostgreSQL, (b) SQLite, (c) Supabase managed | **(a) PostgreSQL** — already spec'd, JSONB support, pgvector for later, production-grade | Confirms DATA_STRATEGY recommendation |
| ORM approach? | (a) SQLAlchemy 2.0 async, (b) raw SQL, (c) Piccolo, (d) Prisma (if Node API) | **(a) SQLAlchemy 2.0 async** — already spec'd, Python ecosystem standard, async support | Confirms TECHNICAL_INFRASTRUCTURE recommendation |
| Start with SQLite? | (a) SQLite for dev speed, migrate to Postgres, (b) Postgres from day 1 | **(b) Postgres from day 1** — avoids migration tax; docker-compose makes it trivial; JSONB behavior differs | Minimizes future migration work |
| Where to host? | (a) Render managed Postgres, (b) Supabase, (c) Neon, (d) Self-hosted in docker | **(a) Render** for production (already spec'd), **(d) docker** for local dev | Confirms TECHNICAL_INFRASTRUCTURE |
| JSONB vs normalized for CanonicalPacket? | (a) Full JSONB, (b) Full normalized, (c) Hybrid | **(c) Hybrid** — normalized for stable queryable fields (customer_id, status, agent_id, created_at), JSONB for evolving packet structure | Already recommended in DATA_STRATEGY |
| Share token generation? | (a) UUID, (b) secrets.token_urlsafe, (c) Hashids | **(b) secrets.token_urlsafe(16)** — already spec'd in MULTI_CHANNEL_STRATEGY | Enables client portal (gap #03) |

---

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Schema design wrong — need migration early | High | Start with Alembic from day 1. Keep schema minimal (5 tables max). Evolve incrementally. |
| JSONB becomes unqueryable mess | Medium | Index key JSONB paths. Extract stable query fields to columns. Review per table. |
| No migration path from JSON file persistence | Low | spine-api/persistence.py is 246 lines. Write migration script to load JSON files into DB. Then deprecate. |
| PostgreSQL too heavy for solo dev | Low | Docker makes Postgres trivial. Render free tier covers dev. |
| Premature optimization — building schema before features | Medium | Only create tables for features that exist. Don't pre-create supplier/bookings tables until those features are started. |

---

## 9. Files Audited

- `Docs/research/DATA_STRATEGY.md` — Full PostgreSQL schema
- `Docs/TECHNICAL_INFRASTRUCTURE.md` — Stack recommendations, conversations table
- `Docs/SINGLE_TENANT_MVP_STRATEGY.md` — Simplified MVP schema
- `Docs/FEEDBACK_LOOPS_AND_IMPROVEMENT.md` — Trip logs, error logs tables
- `Docs/PERSONA_PROCESS_GAP_ANALYSIS_2026-04-16.md` — Persistence severity 6/6
- `Docs/CODEBASE_ANALYSIS_2026-04-12.md` — P0 gap assessment
- `spine-api/persistence.py` — Only persistence implementation (JSON files)
- `docker-compose.yml` — No DB service
- `.env.example` — No DATABASE_URL
- `pyproject.toml` — No DB dependencies
- `frontend/src/stores/themeStore.ts` — Only localStorage usage
- `frontend/src/app/api/trips/route.ts` — Mock data only
- `specs/canonical_packet.schema.json` — Data contract for persistence