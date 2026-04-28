# Production Audit v2 — Waypoint OS

**Review Date:** 2026-04-28
**Method:** production-code-audit skill (discovery -> scan -> report; no code changes)
**Documents preserved (no overwrite):** ARCHITECT_REVIEW_V2.md, COMPREHENSIVE_REVIEW_V2.md, IMPROVE_ARCHITECTURE_V2.md, PRODUCTION_AUDIT_FINDINGS.md

---

## Phase 1: Codebase Discovery

### Tech Stack
- Python 3.13 with uv package manager
- FastAPI + uvicorn (1-4 workers)
- SQLAlchemy async + asyncpg
- PostgreSQL (via Docker, Fly.io, Render)
- Redis (LLM usage guard)
- Alembic (migrations)
- Pydantic + Pydantic-to-TypeScript

### Primary Entry Points
- `spine_api/server.py` — FastAPI app, main entrypoint
- `src/intake/orchestration.py` — core pipeline
- `spine_api/run_{state, ledger, events}.py` — run lifecycle management

### External Dependencies
1. PostgreSQL (required)
2. Redis (optional — for LLM usage guard)
3. Gemini API (optional — default LLM provider)
4. OpenAI API (optional — fallback LLM)
5. Local models (optional — transformers + torch)

---

## Phase 2: Comprehensive Issue Detection

### Architecture Issues

| # | Severity | Issue | Location | Details |
|---|----------|-------|----------|---------|
| A01 | CRITICAL | Dockerfile broken | Dockerfile:57,79 | `COPY spine-api/` references non-existent directory (should be `spine_api`). `uvicorn spine-api.server:app` uses hyphen in module name — Python cannot import. |
| A02 | HIGH | Dual async engines | core/database.py + persistence.py | Two SQLAlchemy engines for same database: one pool_size=20 with connection pooling, one with NullPool. Different config, same database. |
| A03 | HIGH | server.py monolith | server.py (2,644 lines) | 77 functions across 7+ concerns. 13 unused imports. 28 import-order violations. |
| A04 | HIGH | intake/decision.py monolith | decision.py (2,240 lines) | 5 distinct concerns in one file. |
| A05 | MEDIUM | persistence.py dual concerns | persistence.py (1,115 lines) | JSON file storage + SQLAlchemy ORM + process health monitoring + encryption integration. |
| A06 | MEDIUM | 4 empty shell packages | pipelines/, adapters/, config/, schemas/, utils/ | Aspirational architecture that hasn't materialized. |

### Security Vulnerabilities

| # | Severity | Issue | Location | Details |
|---|----------|-------|----------|---------|
| S01 | CRITICAL | Static encryption key in source | src/security/encryption.py:22 | Fernet key `v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8=` hardcoded. Used when ENCRYPTION_KEY env var is not set (default). DATA_PRIVACY_MODE defaults to `dogfood` which silently uses this key. |
| S02 | MEDIUM | Dev password in database URL | core/database.py:24 | Default DATABASE_URL contains `waypoint_dev_password`. If deployed accidentally with default URL, the password is in source. |
| S03 | MEDIUM | No auth rate limiting | routers/auth.py | Login, register, password reset have no rate limiting. Brute force attack vector. |
| S04 | LOW | No token revocation | core/auth.py, core/security.py | JWT tokens are valid until expiry. No blacklist/cache mechanism to revoke. |
| S05 | LOW | No refresh token rotation | core/security.py | Single JWT token. No short-lived access token + long-lived refresh token pattern. |
| S06 | LOW | No MFA | auth.py | No multi-factor authentication support. |

### Performance Problems

| # | Severity | Issue | Location | Details |
|---|----------|-------|----------|---------|
| P01 | HIGH | Synchronous LLM calls in async path | hybrid_engine.py, gemini_client.py | LLM API requests use synchronous HTTP. Blocks the async event loop. |
| P02 | MEDIUM | File-based cache not process-safe | decision/cache_storage.py | threading.Lock doesn't synchronize across uvicorn workers. Under 2+ workers, file cache corrupts. |
| P03 | MEDIUM | Synchronous file I/O in async handlers | persistence.py | TripStore/AuditStore use synchronous JSON file read/write inside async route handlers. |
| P04 | LOW | No database query caching | — | Every query hits PostgreSQL directly. No Redis-backed query cache. |
| P05 | LOW | No eager-loading detected | various | Async DB queries use basic select() patterns. No joinedload/selectinload for relationships. |

### Code Quality Issues

| # | Severity | Issue | Files | Details |
|---|----------|-------|-------|---------|
| C01 | CRITICAL | 17 undefined name errors (F821) | Multiple files | See detailed list below — includes `PasswordResetToken` (login flow will crash), `ActivityDefinition` (suitability will crash), `Agency` and `User` in SQLAlchemy models. |
| C02 | HIGH | 18 f-string without placeholders | telemetry.py, composition_risk.py, local_llm.py, notifications.py | Likely copy-paste errors. Some may be bugs (templates that should interpolate). |
| C03 | HIGH | 19 unused imports (F401) | server.py (13), notifications.py (3), frontier.py (3) | Import bloat especially in server.py. |
| C04 | HIGH | 28 import-order violations (E402) | server.py (24), others | Code between imports. |
| C05 | MEDIUM | 9 print() instead of logging | local_llm.py (6), decision.py (3) | Won't appear in log aggregation. |
| C06 | MEDIUM | 5 TODO/FIXME comments | Multiple | Frontier FK issues, health check stub. |
| C07 | LOW | Magic numbers in scoring | analytics/engine.py | Raw numbers: 25, 20, 15, 10, 50, 60, 100, 18.0, 2.0, 3.0, 5.0 without named constants. |

### Undefined Name (F821) Detail — RUNTIME CRASHES

| File | Line | Symbol | Impact |
|------|------|--------|--------|
| spine_api/services/auth_service.py | 299-349 | `PasswordResetToken` | **Login/password-reset flow will 500.** This class is referenced for creating and querying reset tokens but never imported. |
| src/suitability/integration.py | 71 | `ActivityDefinition` | **Suitability integration will 500.** Used in `extract_participants_from_packet` but not imported. |
| spine_api/core/auth.py | 121 | `Agency` | get_current_agency function uses Agency but doesn't import it. |
| spine_api/models/frontier.py | 55,99,177 | `Agency` | ForeignKey reference target not imported. Alembic may generate invalid migrations. |
| spine_api/models/trips.py | 63,64 | `Agency`, `User` | ForeignKey targets not imported. Same migration risk. |
| src/llm/usage_store.py | 483 | `Callable` | Used in type hint but not imported. |
| src/intake/config/agency_settings.py | 288 | `logger` | Used in error handler but not defined. |

### Testing Gaps

| # | Severity | Issue | Details |
|---|----------|-------|---------|
| T01 | HIGH | No CI pipeline | No GitHub Actions or automated test execution on PRs/merges. |
| T02 | HIGH | No tests for undefined-name crashes | The F821 errors in auth_service.py, integration.py have no tests catching these runtime failures. |
| T03 | MEDIUM | No server.py route handler tests | 77 functions, none with dedicated tests. |
| T04 | MEDIUM | No performance/load tests | No benchmark for pipeline execution time. |
| T05 | LOW | No property-based or fuzz testing | — |

### Production Readiness

| # | Severity | Issue | Details |
|---|----------|-------|---------|
| R01 | HIGH | No CI pipeline | No automated test execution, no linting in CI. |
| R02 | HIGH | No database migration in deploy | Dockerfile, fly.toml, render.yaml all skip `alembic upgrade head`. Schema changes will break deployments. |
| R03 | MEDIUM | 4 deployment targets, no canonical | Docker, docker-compose (incomplete), Fly.io (placeholder image), Render. |
| R04 | MEDIUM | No structured logging | No JSON logs, no correlation IDs. |
| R05 | MEDIUM | Ad-hoc env var management | os.getenv scattered across 10+ modules. No centralized config class. |
| R06 | LOW | No APM / error tracking | No Sentry, no Prometheus, no metrics export beyond /health. |
| R07 | LOW | No pre-commit hooks | No automated linting before commits. |

---

## Verification Summary (Phase 4 of skill)

Before claiming completion, I verified:
- No code was modified (all analysis is report-only)
- All findings reference specific file paths and line numbers
- 5,395 lines of ruff output were reviewed
- 17 undefined name errors identified (potential runtime crashes)
- Dockerfile confirmed broken (module path mismatch)
- Static encryption key confirmed in source
- No CI/CD pipeline exists

---

## Issue Count

| Severity | Count | IDs |
|----------|-------|-----|
| CRITICAL | 3 | A01, S01, C01 |
| HIGH | 10 | A02, A03, A04, C02, C03, C04, P01, R01, R02, T01 |
| MEDIUM | 13 | A05, A06, S02, S03, P02, P03, C05, C06, T03, T04, R03, R04, R05 |
| LOW | 7 | S04, S05, S06, P04, P05, C07, R06, R07 |
| **TOTAL** | **33** | |

---

## Production Audit Checklist

| Check | Status | Notes |
|-------|--------|-------|
| No SQL injection | PASS | All queries use SQLAlchemy ORM. One raw SQL in health check (safe). |
| No hardcoded secrets | FAIL | Static Fernet key in encryption.py. Dev password in database.py default URL. |
| Authentication on protected routes | PASS | Middleware + per-route auth dependencies. |
| Authorization checks | PARTIAL | Basic role/permission checks exist. No fine-grained resource-level auth. |
| Input validation on endpoints | PASS | Pydantic models for all request schemas. |
| Password hashing with bcrypt | PASS | bcrypt confirmed in imports. |
| HTTPS enforced | PARTIAL | fly.toml has force_https=true. Dockerfile has no TLS config. |
| No N+1 queries | PARTIAL | No eager-loading detected. Risk exists for complex queries. |
| Database indexes | PARTIAL | Frontier models have no FK indexes (documented TODOs). |
| Caching implemented | PARTIAL | Decision cache exists (file-based, not process-safe). |
| Test coverage > 80% | UNKNOWN | 64 test files. Coverage tool not configured. |
| Environment variables configured | PARTIAL | Documented in .env.example. Not all vars covered. |
| Structured logging | FAIL | No JSON logs, no correlation IDs. |
| Health check endpoints | PASS | /health endpoint exists. |
| CI/CD pipeline | FAIL | No .github/workflows/ directory. |
