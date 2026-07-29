# Deployment & Operations — Research Document

**Topic**: #25 (Exploration Topics Master Index)
**Status**: Active — Comprehensive analysis complete
**Last Updated**: 2026-06-25

---

## Purpose

Resolve the critical production infrastructure gaps identified in the comprehensive architecture review. The Dockerfile is broken, there is no CI pipeline, deployment targets are spread across four platforms with no canonical choice, and there is no monitoring or structured logging. This is the single biggest operational risk for moving to production with real agencies.

---

## Current State Assessment

### Architecture Overview

The application is a **two-service architecture**:

| Service | Stack | Purpose |
|---------|-------|---------|
| **spine_api** (backend) | Python 3.13 + FastAPI + Uvicorn | API server, business logic, LLM orchestration, database access |
| **frontend** (Next.js) | React 19 + Next.js 16 + pnpm | UI + BFF proxy layer (auth token management, route mapping, trip transforms) |

The frontend acts as a **BFF (Backend for Frontend)** — it proxies API requests to spine_api after handling auth cookies and session management. Both services run alongside a **PostgreSQL 16** database.

### Existing Deployment Artifacts (Status)

| Artifact | Status | Issues |
|----------|--------|--------|
| `Dockerfile` | ❌ **BROKEN** | References `spine-api/` (hyphen) directory that doesn't exist — actual dir is `spine_api/` (underscore). Only builds backend, not frontend. Multi-stage but no caching optimization. |
| `docker-compose.yml` | ⚠️ **Incomplete** | Only defines PostgreSQL. Missing spine_api and frontend services, networking config, health check coordination. |
| `fly.toml` | ⚠️ **Stale** | References placeholder image `ghcr.io/your-org/spine-api:latest`. Includes migration bootstrap command. VM: 512mb/1 shared CPU. Public checker agency ID hardcoded. |
| `render.yaml` | ⚠️ **Stale** | Contains build/predeploy/start commands but CORS and TRAVELER_SAFE_STRICT vars are `sync: false` (must be set manually in dashboard). |
| `Procfile` | ✅ **Works** | Simple web process definition for uvicorn. |
| `.env.example` | ✅ **Complete** | Documents all 20+ env vars across 7 sections. Good reference. |
| `dev.sh` | ✅ **Works** | Local dev orchestration with SQL migrations and bootstrap preflight. |
| GitHub Actions | ⚠️ **Partial** | Only `run-contract-guard.yml` exists — runs markdown lint, backend contract guard tests, and frontend route-map tests. No test/lint/typecheck CI. |

### Deployment Flow Diagram

```
┌─────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Browser   │ ───> │  Next.js App     │ ───> │  FastAPI spine   │
│             │      │  (port 3000)     │      │  (port 8000)     │
│             │      │  BFF Proxy       │      │  + Alembic       │
│             │      │  Auth Cookies    │      │  + PostgreSQL    │
└─────────────┘      └──────────────────┘      └──────────────────┘
                              │                          │
                              │  Session Mgmt            │  Persistence
                              v                          v
                      ┌──────────────────┐      ┌──────────────────┐
                      │  spine_api       │      │  PostgreSQL 16   │
                      │  Auth Headers    │      │  (port 5432)     │
                      └──────────────────┘      └──────────────────┘
```

**Key insight:** Both services must be deployed **separately** but configured to talk to each other. The frontend points to `SPINE_API_URL` (env var) to reach the backend. The backend requires `SPINE_API_CORS` to include the frontend origin.

### Critical Issues (from COMPREHENSIVE_REVIEW_V2.md)

The architecture review identified these P0-P1 issues directly affecting deployment:

| ID | Issue | Severity | Status |
|----|-------|----------|--------|
| P0-01 | Dockerfile references `spine-api/` instead of `spine_api/` | **P0** — Container won't build | ❌ Unfixed |
| P0-02 | Static encryption key fallback in `encryption.py:22` | **P0** — Security risk in any deployment | ❌ Unfixed |
| P0-03 | Undefined names in auth_service.py, integration.py | **P0** — Runtime 500s on certain paths | ❌ Unfixed |
| P1-01 | No CI pipeline for test/lint/typecheck | **P1** — No quality gate before deploy | ❌ Unfixed |
| P1-05 | No database migration step in any deployment target | **P1** — Schema changes break deployments | ❌ Unfixed |
| P3-07 | 4 deployment targets with no canonical choice | **P3** — Fragmented effort, unclear best path | ❌ Unfixed |

---

## Key Questions

### Deployment Target

- What is the single canonical deployment target? (Fly.io, Render, Docker-compose-hosted, VPS, or cloud provider?)
- Should we consolidate to one platform or maintain multiple deployment configurations?
- What's the cost profile for each option at small scale (1-10 agencies)?
- Does the platform support the full architecture (Next.js + FastAPI + PostgreSQL)?

### Frontend Deployment

- Does the frontend deploy as a standalone Next.js app (e.g., Vercel) or alongside the backend?
- How do we handle the BFF proxy relationship in production? Same domain? Subdomain? Separate origins with CORS?
- What about Next.js Server-Side Rendering — does it need to reach the backend at request time?
- Should we consider static export if the backend can handle all SSR?

### CI/CD Pipeline

- What stages should the CI pipeline have? (test → lint → typecheck → build → deploy)
- Which tests should gate a deployment? Unit? Integration? E2E? Contract?
- Should we use GitHub Actions, or use the platform's native CI (Fly.io, Render, Vercel)?
- How do we handle database migrations in the deployment pipeline? (Alembic auto-migrate vs manual approval)
- What's the rollback strategy for a failed deployment?

### Monitoring & Observability

- What error tracking should be in place before beta users? (Sentry, Rollbar, custom?)
- How do we implement structured logging? (JSON logs, correlation IDs, log levels)
- What uptime monitoring is needed? (Health check endpoint exists, but no external monitoring)
- Do we need APM for performance tracking?

### Operations

- What's the backup strategy for PostgreSQL (automated dumps, WAL archiving, PITR)?
- How are secrets managed across environments? (GitHub secrets, platform secrets, vault?)
- How do we handle feature flags for gradual rollout?
- What's the incident response process? (Alerting, runbooks, escalation)
- How do we manage environment configuration? (dev, staging, production parity)

---

## Research Areas

### 1. Deployment Target Evaluation

#### Fly.io
**Pros:** Built-in Docker support, auto-scaling, global regions, Postgres via Fly.io managed DB, simple `fly.toml` config, free tier for small apps.
**Cons:** Container-based (need proper Dockerfile), cold starts on auto-stop, no native Next.js support (must run as custom node app), need separate Postgres cluster.

**Current config:** `fly.toml` exists with 512mb/1-cpu VM, health check, release command for schema migrations. References placeholder image — no CI build pipeline.

**Verdict:** Viable if we fix the Dockerfile and set up a proper build pipeline. Best for the backend. Frontend may be better on Vercel.

#### Render
**Pros:** Simple GitHub-connected deploys, native support for Python web services + Node.js + PostgreSQL, preview environments on PRs, free tier.
**Cons:** Cold starts on free tier, limited regions (only Oregon/Frankfurt/Singapore), no edge compute, scaling less flexible than Fly.io.

**Current config:** `render.yaml` exists with build/predeploy/start commands. Some env vars marked `sync: false` (must be set manually).

**Verdict:** Best for quick setup with minimal DevOps overhead. The pre-existing config makes it the path of least resistance.

#### Vercel (for frontend) + separate backend
**Pros:** Native Next.js support (SSR, ISR, Edge Functions), free tier for small projects, preview deployments, global CDN, automatic HTTPS.
**Cons:** Backend still needs separate hosting (Vercel serverless functions are not suitable for long-lived FastAPI connections). Two deployment targets to manage.

**Verdict:** Ideal for the Next.js frontend if we accept managing two deployment targets. The BFF proxy needs the backend to be reachable.

#### Docker-compose on VPS
**Pros:** Full control, single deployment config, fixed cost, no per-request pricing.
**Cons:** Requires VPS management (security updates, backups, networking), no auto-scaling, higher upfront setup effort.

**Verdict:** Good future option for agencies who want on-premise deployment, but overkill for initial beta.

### 2. Dockerfile Redesign

The current Dockerfile must be rewritten to:
1. **Fix the path**: `spine-api/` → `spine_api/` throughout
2. **Add frontend build**: Either build the Next.js frontend in a separate stage, or assume frontend is deployed separately
3. **Optimize caching**: Layer ordering for maximum Docker layer cache hits (dependencies → source code)
4. **Reduce image size**: Use slim Python image, multi-stage build, clean apt cache
5. **Non-root user**: Already implemented (appuser)

**Frontend consideration:** If frontend is deployed to Vercel, the Dockerfile only needs to build the backend. If we want a single monolithic deployment (e.g., Docker-compose with both services), we need a second Dockerfile for the frontend or a combined build.

### 3. CI/CD Pipeline Design

**Recommended stages (ordered, with gates):**

```
PR → [lint → typecheck → unit tests → integration tests] → 
Merge to main → [build → contract tests → staging deploy → E2E tests] → 
Production deploy (manual gate)
```

**Existing contract guard** (`.github/workflows/run-contract-guard.yml`):
- Runs markdown lint
- Runs backend contract guard tests
- Runs D6 gate snapshot verification
- Runs frontend route-map guard tests

**Missing from CI:**
- Python lint (ruff check)
- Python typecheck (pyright/mypy)
- Full pytest suite
- Frontend lint (ESLint)
- Frontend typecheck (tsc --noEmit)
- Build verification (Docker build / next build)
- Deployment automation

### 4. Database Migration Strategy

**Current state:** Alembic configured at `/alembic/` with staged migrations. `dev.sh` runs `alembic upgrade head` + `bootstrap_public_checker_agency.py` startup preflight.

**Gaps:**
- No migration step in any deployment config
- No migration rollback strategy
- No migration testing (can we test upgrades/downgrades?)
- No data migration validation

**Recommended approach:**
1. Add migration step to deployment pipeline (release command in Fly.io, preDeployCommand in Render)
2. Each migration should be reversible (`downgrade()` function)
3. Run migrations as a pre-deploy step (not at app startup) to avoid race conditions with multiple workers
4. Test migrations against a copy of production data before deploying

### 5. Monitoring & Observability Stack

**Current state:**
- `/health` endpoint exists in spine_api (basic)
- No structured logging
- No error tracking
- No APM
- OpenTelemetry dependencies exist in `pyproject.toml` but not configured

**Recommended minimal stack for beta:**
1. **Sentry** for error tracking (free tier covers small teams)
2. **Structured JSON logging** — format logs as JSON for log aggregation
3. **Health check** — already exists, add dependency checks (DB connectivity, LLM provider reachability)
4. **Uptime monitoring** — free tier of BetterUptime, Pingdom, or similar
5. **Application metrics** — use OpenTelemetry (already in deps) with a lightweight collector or direct export

### 6. Secrets Management

**Current state:** All secrets in `.env` file locally. `.env.example` documents required vars. GitHub Actions uses repository secrets for contract guard runs.

**Recommended approach:**
1. Platform-native secrets: Fly.io secrets / Render env vars / Vercel env vars
2. GitHub Actions secrets for CI-passed values
3. No secrets in code or Docker images
4. Document required secrets per environment in a deployment checklist
5. Rotate secrets on a schedule (quarterly for beta, monthly for production)

### 7. Frontend Backend Communication in Production

The BFF proxy pattern means the frontend must be able to reach the backend at request time for SSR:

```
User request → Next.js SSR → fetches from spine_api (server-side) → renders HTML → sends to browser
```

**Deployment options:**
1. **Same origin (recommended):** Backend under `/api/*` on the same domain as frontend. Requires Next.js rewrites or reverse proxy (nginx/Caddy).
2. **Subdomain:** frontend.example.com + api.example.com. CORS required on backend.
3. **Separate domains:** Different origins. Full CORS setup needed.

**Option 1 (same origin)** is cleanest for production:
- Nginx/Caddy reverse proxy: `/api/*` → backend, `/*` → Next.js
- No CORS issues
- Simple cookie domain management
- Single TLS certificate

Or with Next.js rewrites in `next.config.ts`:
- `/api/*` routes get proxied to `SPINE_API_URL` on the server side
- Browser talks only to Next.js
- Auth cookies are same-domain

---

## Actionable Plan

### Phase 1: Fix Critical Blockers (High Priority)

| Step | What | Files | Verification |
|------|------|-------|-------------|
| 1.1 | Fix Dockerfile path (spine-api → spine_api) | `Dockerfile` lines 57, 79 | `docker build --platform linux/amd64 -t spine-api .` |
| 1.2 | Fix encryption key fallback | `spine_api/security/encryption.py:22` | Remove hardcoded key, require ENCRYPTION_KEY env var in production | 
| 1.3 | Fix undefined names causing runtime crashes | auth_service.py, integration.py | Run code paths, verify no 500s |
| 1.4 | Add full docker-compose services | `docker-compose.yml` | Add spine_api + frontend services, networking, health checks |
| 1.5 | Add full CI pipeline | `.github/workflows/` | Lint → typecheck → test → build gates |

### Phase 2: Build CI/CD (Medium Priority)

| Step | What | Details |
|------|------|---------|
| 2.1 | Add Python lint job | `ruff check src/ spine_api/ tests/` |
| 2.2 | Add full pytest job | `uv run pytest -q` (add PostgreSQL service in CI) |
| 2.3 | Add frontend typecheck | `cd frontend && npx tsc --noEmit` |
| 2.4 | Add frontend lint | `cd frontend && npm run lint` |
| 2.5 | Add Docker build job | Build spine-api image, verify it starts |
| 2.6 | Add deployment workflow | Auto-deploy on main branch pushes (Fly.io or Render) |

### Phase 3: Choose Canonical Deploy Target (Medium Priority)

| Step | Action | Rationale |
|------|--------|-----------|
| 3.1 | Evaluate: Render for both services | Path of least resistance — existing config, native Python + Node |
| 3.2 | Evaluate: Fly.io backend + Vercel frontend | Better scalability, but two targets to manage |
| 3.3 | ✅ **DECIDED: Render for both services** | See full evaluation below |

**✅ FINAL DECISION (2026-06-25): Render for both services**

**Rationale:**

1. **Architecture fit**: Render natively supports both Python (FastAPI) and Node.js (Next.js) in the same workspace with private networking. No Docker overhead.

2. **Existing config**: `render.yaml` is already in the repo with build/predeploy/start commands. Only needs env vars filled in.

3. **Single platform**: One dashboard, one billing, one deploy workflow. Reduces DevOps cognitive load.

4. **Managed PostgreSQL**: Built-in with automated backups and point-in-time recovery (paid plans).

5. **Pre-deploy migrations**: `preDeployCommand` runs `alembic upgrade head` + `bootstrap_public_checker_agency.py` before every deploy.

6. **GitHub auto-deploy**: Connect repo → every push to main deploys automatically. Also supports preview environments on PRs (Starter plan+).

7. **Cost**: Pro plan at $25/mo flat + compute costs. Predictable and affordable for beta with real agencies.

8. **Private networking**: Backend and frontend communicate over Render's internal network. No public exposure for the backend.

9. **Migration path**: If Render proves insufficient, the backend can move to Fly.io (Docker-native, background workers, multi-region) and the frontend to Vercel (best-in-class Next.js). The architecture is already containerized with Dockerfiles.

**Prerequisites for Render deploy:**
1. Fill `SPINE_API_CORS` and `TRAVELER_SAFE_STRICT` env vars in Render dashboard
2. Create a managed PostgreSQL database in Render
3. Set `DATABASE_URL` env var to the internal Postgres connection string
4. Create a second Web Service for the frontend (Next.js, Node environment)
5. Set `SPINE_API_URL` on the frontend service to the backend's internal URL
6. Configure custom domain(s) with DNS
7. Generate a secure `JWT_SECRET` and set it as a secret env var

**Left as future options:**
- **Fly.io**: When background workers (agent runtime recovery, scheduled tasks) become critical and Docker-native deployment is needed
- **Vercel**: When frontend preview deployments and edge distribution become essential
- **Docker-compose on VPS**: When agencies need on-premise deployment for data residency

### Phase 4: Monitoring & Observability (Medium Priority)

| Step | What | Details |
|------|------|---------|
| 4.1 | Add Sentry | `sentry-sdk` to deps, initialize in server.py |
| 4.2 | Add structured logging | JSON formatter for all log output |
| 4.3 | Add uptime monitoring | Free tier of BetterUptime or similar |
| 4.4 | Add readiness/liveness probes | Health check endpoint with dependency status |

### Phase 5: Operations & Runbooks (Lower Priority)

| Step | What | Details |
|------|------|---------|
| 5.1 | Database backup plan | Automated pg_dump, retention policy, restore testing |
| 5.2 | Deployment runbook | Document deploy/rollback procedure step by step |
| 5.3 | Incident response runbook | Define severity levels, alert response, escalation path |
| 5.4 | Secrets rotation policy | Schedule and procedure for key rotation |
| 5.5 | Feature flag strategy | Environment-based toggles for gradual rollout |

---

## Existing Reference Material

- [COMPREHENSIVE_REVIEW_V2.md](../COMPREHENSIVE_REVIEW_V2.md) — Architecture review with deployment gap analysis (P0-P3 issues)
- [IMPROVE_ARCHITECTURE_FINDINGS.md](../IMPROVE_ARCHITECTURE_FINDINGS.md) — Module-level architecture recommendations
- [AUTH_IDENTITY_SYSTEM_AUDIT_2026-04-24.md](../AUTH_IDENTITY_SYSTEM_AUDIT_2026-04-24.md) — Auth infrastructure audit
- Dockerfile (project root) — Currently broken, needs rewrite (Phase 1)
- docker-compose.yml — Only defines PostgreSQL, needs full services (Phase 1)
- fly.toml — Fly.io config, references placeholder image
- render.yaml — Render blueprint config
- `frontend/src/app/api/[...path]/route.ts` — BFF proxy architecture
- `frontend/src/lib/route-map.ts` — Backend route mapping
- [DR_SPEC_GRACEFUL_DEGRADATION.md](DR_SPEC_GRACEFUL_DEGRADATION.md) — Graceful degradation research
- [DR_SPEC_SYSTEM_SHADOWING.md](DR_SPEC_SYSTEM_SHADOWING.md) — System shadowing research
- [DEVOPS_DEEP_DIVE_MASTER_INDEX.md](../frontend/docs/DEVOPS_DEEP_DIVE_MASTER_INDEX.md) — Frontend-side DevOps architecture doc
- [DEVOPS_04_SCALING_DEEP_DIVE.md](../frontend/docs/DEVOPS_04_SCALING_DEEP_DIVE.md) — Scaling deep dive

---

## Deliverables

- ✅ Current state assessment (this document)
- [ ] Canonical deployment architecture decision (Phase 3)
- [ ] Fixed Dockerfile with multi-stage build (Phase 1)
- [ ] Complete docker-compose.yml with all services (Phase 1)
- [ ] CI pipeline with quality gates (Phase 2)
- [ ] Production monitoring and alerting setup (Phase 4)
- [ ] Database migration automation (Phase 1/2)
- [ ] Production runbooks (deploy, rollback, recovery, incident response) (Phase 5)
- [ ] Staging environment (Phase 2/3)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-25 | **Canonical deploy target: Render for both services** | See decision evaluation below |
