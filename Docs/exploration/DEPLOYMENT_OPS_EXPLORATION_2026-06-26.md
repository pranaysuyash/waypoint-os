# Deployment & Operations Exploration (#25)

## Status Note

As of 2026-06-30, this exploration remains active. The synthesis is useful as a planning base, but the P0/P1 production gaps documented below are still open and should not be treated as archive material.

**Status**: 🔴 High Priority — blocking production release  
**Topic ID**: 25  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Last Updated**: 2026-06-26  
**Source Review**: [COMPREHENSIVE_REVIEW_V2.md](../COMPREHENSIVE_REVIEW_V2.md), Phase 4B

---

## Quick Summary

The codebase is feature-rich (~2,878 tests, 26 migrations, working frontend + backend) but has **no production-ready deployment path**. Four partial deployment targets exist, none fully working. CI skips 70% of tests (no PostgreSQL service). There is zero error tracking, zero structured logging, and zero backup strategy.

**The app cannot be deployed to a beta user today without significant work.**

---

## Current State Assessment

### 1. CI/CD

| Component | Status | Details |
|-----------|--------|---------|
| **CI workflow** | 🟡 Exists but incomplete | `.github/workflows/ci.yml` runs 3 jobs: docs-quality, backend-lint, backend-tests, frontend-quality |
| **Backend lint** | ✅ Working | Ruff check + F401 gate on src/, spine_api/, tests/ |
| **Backend tests** | ⛔ Skips 10 test files | Excludes ALL tests requiring PostgreSQL (~70% of backend coverage missing) |
| **Frontend quality** | ✅ Working | TypeScript typecheck, ESLint, route-map guard tests |
| **Contract guard** | ⛔ Disabled | `.github/workflows/run-contract-guard.yml.disabled` — never verified end-to-end |

**Key gaps:**
- No PostgreSQL service configured in CI (`backend-tests` job has no `services.postgres`)
- The 10 excluded tests cover pipeline execution, RLS, trip lifecycle, suitability, and orchestration — the most critical business logic
- No container build/publish in CI (no Docker image is built or pushed to any registry)
- No deployment workflow in CI (no deploy step after tests pass)

### 2. Docker & Container

| Component | Status | Details |
|-----------|--------|---------|
| **Backend Dockerfile** | ✅ Working | Multi-stage build (python:3.13-slim), non-root user, healthcheck, uv sync --frozen for dependencies |
| **Frontend Dockerfile** | ✅ Fixed this session | Was using pnpm (pnpm-lock.yaml) but project uses npm (package-lock.json). Fixed: changed `pnpm install --frozen-lockfile` → `npm ci`, `pnpm-lock.yaml*` → `package-lock.json` |
| **docker-compose.yml** | 🟡 Improved this session | Now has 4 services: postgres, migrations (NEW), spine-api, frontend |
| **Migration step** | ✅ Added this session | New `migrations` service runs `alembic upgrade head && bootstrap_public_checker_agency.py` before spine-api starts. Uses `entrypoint: [""]` to clear the Dockerfile's uvicorn ENTRYPOINT so migrations run standalone. |

**Remaining issues:**
- Frontend Dockerfile healthcheck uses `wget` but the image doesn't have `wget` installed — should use `node` or `curl`
- No docker-compose override for development (e.g. hot reload, volume mounts)
- Backend Dockerfile HEALTHCHECK uses `curl` but it's a slim image — `curl` may not be installed in the runtime stage (it's installed in the `base` stage but not in `runtime` which copies from `deps`)

### 3. Deployment Targets

#### 3a. Render (Closest to Working)

**Status**: 🟡 Candidate for canonical target

```yaml
preDeployCommand: uv run alembic upgrade head && uv run python scripts/bootstrap_public_checker_agency.py
startCommand: uvicorn spine_api.server:app --host 0.0.0.0 --port 8000 --workers 4
healthCheckPath: /health
```

**Working:**
- Blueprint format (render.yaml) with build/predeploy/start commands
- Migration + bootstrap on every deploy
- Health check configured

**Gaps:**
- Several env vars marked `sync: false` (require manual config in Render dashboard): `SPINE_API_CORS`, `TRAVELER_SAFE_STRICT`
- No frontend service defined (only spine-api)
- No Redis service (LLM usage guard needs it)
- `starter` plan has limited resources
- No env var for `SPINE_API_URL` (frontend needs to know where backend lives)
- No database backup configuration

#### 3b. Fly.io

**Status**: ❌ Placeholder — not usable

```toml
[build]
image = "ghcr.io/your-org/spine-api:latest"  # PLACEHOLDER
```

**Issues:**
- References a non-existent container image (`your-org` is a placeholder)
- No Docker image is published to any registry
- `release_command` is configured correctly (would run migrations) but image doesn't exist
- VM configured at 512MB / 1 shared CPU — adequate for MVP but untested
- No persistent volume for database (uses Fly Postgres? Unclear)

#### 3c. Docker Compose

**Status**: 🟡 Best for local/CI testing

**Fixed this session:**
- Added `migrations` service with `entrypoint: [""]` so Alembic runs standalone (not through uvicorn)
- spine-api now depends on `migrations: service_completed_successfully`
- Frontend Dockerfile no longer broken (pnpm → npm)

**Still missing:**
- No `docker-compose.override.yml` for development (hot reload, volume mounts)
- No `.env` file auto-loading from `docker-compose.yml` (uses hardcoded dev secrets)
- No Redis service for LLM usage guard
- Frontend healthcheck uses `wget` but alpine may not have it

#### 3d. Procfile

**Status**: 🟢 Stub — used by Render/Fly.io as fallback

No issues. Just wraps the uvicorn command. Used by both Render and Fly.io.

### 4. Monitoring & Observability

| Capability | Status | Details |
|-----------|--------|---------|
| **Error tracking** | ❌ Not configured | No Sentry, no error aggregation. Every backend 500 is silent unless a logger catches it. |
| **OpenTelemetry** | 🟡 Dead code | `opentelemetry-distro`, `-exporter-otlp-proto-grpc`, `-instrumentation-fastapi` all in `pyproject.toml`. `server.py` has full OTel instrumentation wired (`FastAPIInstrumentor.instrument_app(app)`). BUT it only activates if `SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT` is set. No collector is deployed. |
| **Structured logging** | 🟡 Basic logging only | Standard `logging.getLogger()` used throughout (20+ spine_api files). `SensitiveDataFilter` at `spine_api/core/logging_filter.py` scrubs tokens/cookies. But no JSON format, no correlation IDs, no log levels enforced across modules. |
| **Health endpoint** | ✅ Working | `GET /health` with DB check. RLS runtime posture validated on startup. |
| **Backups** | ❌ No strategy | No pg_dump, no WAL archiving, no snapshot strategy. 26 migrations + 2,800+ test records at risk. |

### 5. Database & Migrations

| Area | Status | Details |
|------|--------|---------|
| **Migrations** | ✅ Working | 26 Alembic migration files. `alembic.ini` configured with `prepend_sys_path = . spine_api`. |
| **Auto-schema fix on startup** | 🟡 Safety net | `server.py` has `_ensure_agencies_schema_compatibility()` and `_ensure_memberships_schema_compatibility()` — uses `ALTER TABLE ADD COLUMN IF NOT EXISTS` as defensive guard, not a replacement for Alembic. |
| **Env configuration** | ✅ Documented | `.env.example` covers all critical vars. |
| **Dual-store warning** | ⚠️ Persistent risk | `TRIPSTORE_BACKEND` defaults to file store if unset. If deployments omit this, trips silently vanish. This caused the "missing trips" bug on 2026-05-03. |

### 6. Security Findings (from COMPREHENSIVE_REVIEW_V2)

| ID | Issue | Severity | Status |
|----|-------|----------|--------|
| P0-02 | Static Fernet encryption key fallback | **CRITICAL** | ❌ Not fixed. `encryption.py:22` has hardcoded fallback key. `DATA_PRIVACY_MODE=dogfood` silently uses it. |
| P0-03 | Undefined names causing runtime crashes | HIGH | 🟡 Mostly fixed (previous sessions cleaned F401/F841) |
| — | Default database password in docker-compose | MEDIUM | 🟡 Known dev-only password; must use secrets in production |
| — | No rate limiting on auth endpoints | MEDIUM | 🟡 slowapi dependency exists but rate limits not explicitly configured for auth routes |

---

## Changes Made in This Session (2026-06-26)

### Fixed
1. **frontend/Dockerfile**: pnpm → npm (`pnpm-lock.yaml` → `package-lock.json`, `pnpm install --frozen-lockfile` → `npm ci`, removed `corepack enable` pnpm install step)
2. **docker-compose.yml**: Added `migrations` service that runs `alembic upgrade head && bootstrap_public_checker_agency.py` before spine-api starts. Uses `entrypoint: [""]` to clear the Dockerfile's uvicorn ENTRYPOINT so the migration command runs standalone.

### Identified But Not Yet Fixed
3. **frontend/.env.local**: Set `SPINE_API_URL=http://127.0.0.1:8001` to fix port mismatch (spine API runs on 8001, not 8000 where orbitcover is)
4. **Frontend healthcheck**: Uses `wget` but alpine may not have it installed. Should verify or switch to `node -e` or `curl`.

---

## Prioritized Action Plan

### P0 — Must Fix Before Production

| # | Action | Effort | Depends On |
|---|--------|--------|------------|
| 1 | **Add PostgreSQL service to CI** | 1 hour | — |
| 2 | **Fix static encryption key** | 30 min | — |
| 3 | **Choose canonical deployment target** (Render recommended) | 1 hour | #1, #2 |
| 4 | **Add Sentry error tracking** | 2 hours | #3 |

### P1 — Before Beta

| # | Action | Effort | Depends On |
|---|--------|--------|------------|
| 5 | **Publish Docker image to GHCR** | 1 hour | #1 |
| 6 | **Configure Render production deployment** | 2 hours | #3, #5 |
| 7 | **Add Redis service to docker-compose** | 30 min | — |
| 8 | **Add database backup strategy** (pg_dump cron) | 1 hour | #3 |
| 9 | **Configure env vars via Render secrets** | 1 hour | #3 |
| 10 | **Add structured JSON logging** | 2 hours | — |
| 11 | **Verify frontend healthcheck works in Docker** | 30 min | — |

### P2 — Before Scale

| # | Action | Effort | Depends On |
|---|--------|--------|------------|
| 12 | **Set up OpenTelemetry collector** | 4 hours | #10 |
| 13 | **Add deployment workflow to CI** (auto-deploy on master push) | 2 hours | #5, #6 |
| 14 | **Add production docker-compose overlay** | 1 hour | #7 |
| 15 | **Configure slowapi rate limits for auth** | 1 hour | — |
| 16 | **Add runbooks for common failure modes** | 3 hours | — |

---

## Detailed Steps

### P0-1: Add PostgreSQL Service to CI

Add a `services` block to the `backend-tests` job in `.github/workflows/ci.yml`:

```yaml
backend-tests:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:16-alpine
      env:
        POSTGRES_USER: waypoint
        POSTGRES_PASSWORD: waypoint_dev_password
        POSTGRES_DB: waypoint_os
      ports:
        - 5432:5432
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  steps:
    # ... existing steps ...
    - name: Run all tests (with PostgreSQL)
      run: uv run pytest -q tests/ --ignore=tests/test_vision_extraction.py --ignore=tests/test_extraction_fallback.py
      env:
        DATABASE_URL: postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os
        TRIPSTORE_BACKEND: sql
        PUBLIC_CHECKER_AGENCY_ID: d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b
        JWT_SECRET: ci-test-secret
```

### P0-2: Fix Static Encryption Key

In `src/security/encryption.py`, make the Fernet key a hard requirement in production:

- Remove the hardcoded fallback key `b'v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8='`
- Raise `RuntimeError` if `ENCRYPTION_KEY` is not set and `DATA_PRIVACY_MODE != "dogfood"`
- Add a startup validation check in `server.py`'s lifespan

### P0-3: Choose Canonical Deployment Target

**Recommendation: Render**

**Why:**
- Already has the most complete configuration (buildCommand, preDeployCommand, startCommand, healthCheckPath)
- Supports Blueprint-as-code (render.yaml can be version-controlled)
- Built-in PostgreSQL (add-on, no separate infra)
- Free tier available for MVP
- Node.js + Python runtimes supported for frontend + backend

**Steps:**
1. Create Render Web Service for spine-api
2. Add Render PostgreSQL add-on
3. Configure env vars in Render dashboard (secrets for JWT_SECRET, GEMINI_API_KEY, etc.)
4. Add `DATABASE_URL` from Render PostgreSQL add-on
5. Deploy and verify health check passes
6. Add frontend as a separate Render Static Site or Web Service

### P0-4: Add Sentry

1. `uv add sentry-sdk`
2. Initialize in `spine_api/server.py` lifespan:
   ```python
   import sentry_sdk
   sentry_sdk.init(
       dsn=os.environ["SENTRY_DSN"],
       environment=os.environ.get("ENVIRONMENT", "development"),
       traces_sample_rate=0.25,
   )
   ```
3. Add `@sentry_sdk.monitor` to background pipeline threads
4. Add `SENTRY_DSN` to all deployment configs

---

## Cost Estimates (Monthly, MVP)

| Component | Cost | Notes |
|-----------|------|-------|
| Render Web Service (spine-api) | $7–$25/mo | Starter plan ($7) or Professional ($25) |
| Render PostgreSQL | $7–$15/mo | Mini DB ($7) — adequate for MVP |
| Render Static Site (frontend) | Free | Static site tier |
| Sentry | Free | 5k events/month on developer plan |
| Uptime monitoring (checkly/uptimerobot) | Free | Basic checks |
| **Total MVP** | **~$14–$40/mo** | |

---

## Environment Variables Required for Production

| Variable | Source | Required | Notes |
|----------|--------|----------|-------|
| `JWT_SECRET` | Generate via `secrets.token_urlsafe(32)` | ✅ | Rotate quarterly |
| `DATABASE_URL` | Render PostgreSQL add-on | ✅ | Auto-provided by Render |
| `TRIPSTORE_BACKEND` | Set to `sql` | ✅ | Critical — file store loses data |
| `PUBLIC_CHECKER_AGENCY_ID` | Seed in migration | ✅ | Must exist in agencies table |
| `SPINE_API_CORS` | Frontend URL | ✅ | Set to Render frontend domain |
| `GEMINI_API_KEY` | Google AI Studio | ✅ | Primary LLM provider |
| `OPENAI_API_KEY` | OpenAI dashboard | 🟡 | Fallback LLM provider |
| `SENTRY_DSN` | Sentry project | ✅ | Error tracking |
| `ENVIRONMENT` | Set to `production` | ✅ | Changes behavior of startup mutations |
| `TRAVELER_SAFE_STRICT` | Set to `1` | ✅ | Production safety |
| `SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT` | OTel collector | Optional | Only if APM is configured |

---

## Related Documents

- [COMPREHENSIVE_REVIEW_V2.md](../COMPREHENSIVE_REVIEW_V2.md) — Original findings (Phase 4B)
- [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) — Master exploration index
- [Docs/discussions/logging_observability_2026-04-29.md](../discussions/logging_observability_2026-04-29.md) — Logging architecture research
- [Docs/discussions/monitoring_2026-04-29.md](../discussions/monitoring_2026-04-29.md) — Monitoring research
- [DATA_STRATEGY.md](../research/DATA_STRATEGY.md) — Database schema design
- [.env.example](../../.env.example) — Environment variable reference
- [render.yaml](../../render.yaml) — Render blueprint config
- [fly.toml](../../fly.toml) — Fly.io config (placeholder)

---

*Status: Exploration phase complete. P0 items (CI PostgreSQL, encryption key, deployment target, Sentry) are the gate to production readiness.*
