# E2 Security & Privacy: Verified State & Action Plan

**Date:** 2026-05-02
**Source:** Codebase audit of exploration map finding E2, corrected for actual state

---

## Context

We ran an exploration map audit that flagged E2. Security & Privacy as P0 PARTIAL with several claimed gaps. Deep codebase verification showed **3 of 7 claimed gaps are already shipped** and **1 is out of scope**. This document captures the verified current state and the remaining real work.

---

## What's Already Built (do not rebuild)

### 1. Auth Middleware — DONE
- **File:** `spine_api/core/middleware.py` (91 lines)
- JWT enforcement on all routes except `/health`, `/docs`, `/openapi.json`, `/redoc`, `/api/auth/*`, `/api/public-checker/*`
- Integrated into the FastAPI app, runs on every request
- **No work needed.**

### 2. RBAC — DONE
- **File:** `spine_api/core/auth.py` (189 lines)
- 5 roles: `owner`, `admin`, `senior_agent`, `junior_agent`, `viewer`
- ~25 permissions in `ROLE_PERMISSIONS` matrix
- `require_permission(permission: str)` dependency factory for route-level enforcement
- `require_auth` convenience dependency
- **No work needed.**

### 3. Multi-Tenant Workspace Isolation — DONE
- **Files:** `spine_api/models/tenant.py` (169 lines), `spine_api/routers/workspace.py` (56 lines), `spine_api/services/workspace_service.py` (91 lines)
- `Agency` (tenant), `User`, `Membership`, `WorkspaceCode`, `PasswordResetToken` models
- `agency_id` embedded in JWT, all queries scoped by it
- Workspace codes control agent onboarding
- Alembic migration: `alembic/versions/eb7a5eede594_init_tenant_schema.py`
- **No work needed.**

### 4. Auth Endpoints — DONE
- **Files:** `spine_api/routers/auth.py` (295 lines), `spine_api/services/auth_service.py` (381 lines)
- Full lifecycle: signup, login, logout, me, refresh, password-reset
- Cookie-only transport (httpOnly, SameSite=Lax, Secure in production)
- No tokens in JSON response bodies (eliminates XSS token theft)
- Password reset tokens stored as SHA-256 hashes
- Unknown email returns same generic message as known email (no enumeration)
- **No work needed.**

### 5. PII Privacy Guard — DONE
- **File:** `src/security/privacy_guard.py` (333 lines)
- Detects: email addresses, phone numbers (Indian + generic 10-digit), medical/health keywords (15 terms), freeform field names (16 fields)
- Three modes: dogfood (block PII), beta (log warnings), production (encryption expected)
- Known fixture bypass for test data
- 32 tests in `tests/test_privacy_guard.py` (336 lines)
- **No work needed.**

### 6. Encryption — DONE
- **File:** `src/security/encryption.py` (44 lines)
- Fernet symmetric encryption (AES-128-CBC via `cryptography.fernet`)
- Production mode raises ValueError if `ENCRYPTION_KEY` env var is not set
- Dev/dogfood mode has hardcoded fallback key (documented as NOT for production)
- **No work needed.**

### 7. PCI DSS — NOT APPLICABLE (out of scope by design)
- The app records pricing entries (what was quoted, what was paid, vendor prices) but does **not** process or store payment card data
- PCI DSS compliance is not required for this product
- **No work needed.**

---

## What Actually Needs Work (4 items)

### Gap 1: Backend Audit Trail (Priority: P1)
**Current state:** Frontend `audit.ts` types exist (187 lines). No backend audit log tables, no migration, no middleware.
**Why it matters:** State-changing API calls have no traceability. Operators can't see who did what, when, or why.
**What to build:**
- `AuditLog` SQLAlchemy model: `id`, `agency_id`, `user_id`, `action`, `resource_type`, `resource_id`, `changes` (JSON), `ip_address`, `user_agent`, `created_at`
- Alembic migration for the table
- FastAPI middleware or dependency that automatically logs all POST/PUT/PATCH/DELETE requests with auth context
- API endpoint: `GET /api/audit` with filtering by `resource_type`, `user_id`, `date_range`
- Timebox: ~4 hours

### Gap 2: PII Handling Per Jurisdiction (Priority: P1)
**Current state:** Privacy guard treats all PII uniformly. No awareness of GDPR (EU), DPDP (India), or US state privacy laws.
**Why it matters:** Agencies operate across jurisdictions with different rules (right to erasure, consent requirements, data residency).
**What to build:**
- Add `jurisdiction` field to `Agency` model (enum: `IN`, `EU`, `US`, `OTHER`)
- Create `src/security/jurisdiction_policy.py`: maps jurisdiction → PII handling rules (retention period, erasure rights, consent requirements, data residency)
- Wire `privacy_guard.py` to check `Agency.jurisdiction` for policy routing
- Timebox: ~2 hours for model + policy; ~4-6 hours for full erasure/rights endpoints

### Gap 3: Rate Limiting on Auth Endpoints (Priority: P1)
**Current state:** Explicit TODOs in `spine_api/routers/auth.py` lines 50-60. No rate limiting anywhere.
**Why it matters:** Brute-force and credential-stuffing attacks on login/signup are unmitigated.
**What to build:**
- Add `slowapi` dependency to `spine_api`
- Configure rate limits: signup (5/min/IP), login (10/min/IP), password-reset (3/min/IP), refresh (30/min/IP)
- Use `slowapi` middleware integrated with existing FastAPI app
- Timebox: ~2 hours

### Gap 4: ABAC / Per-Record Access Control (Priority: P2 — not blocking)
**Current state:** RBAC is role-based. A `junior_agent` can see all trips in their agency, even ones not assigned to them.
**Why it matters:** For larger agencies, agents should only see trips assigned to them.
**What to build:**
- Extend `require_permission()` to accept resource-level checks
- Add `assigned_to` field consideration in trip/customer queries for `junior_agent` role
- This is a nice-to-have for MVP; current RBAC is sufficient for customer discovery interviews
- Timebox: ~6 hours (can defer)

---

## Recommended Execution Order

1. **Rate limiting** (2h) — Quick win, protects auth endpoints immediately
2. **Backend audit trail** (4h) — Enables traceability for all future work
3. **PII jurisdiction tagging** (2-6h) — Required before onboarding agencies in multiple regions
4. **ABAC** (6h, deferrable) — Only needed when agencies have agents who shouldn't see each other's trips

---

## Files to Touch

| File | Action | Gap |
|---|---|---|
| `spine_api/models/audit.py` | **Create** — AuditLog model | Audit trail |
| `alembic/versions/xxx_add_audit_log.py` | **Create** — Migration | Audit trail |
| `spine_api/core/audit.py` | **Create** — Audit middleware/dependency | Audit trail |
| `spine_api/routers/audit.py` | **Create** — GET /api/audit endpoint | Audit trail |
| `spine_api/models/tenant.py` | **Modify** — Add `jurisdiction` field to Agency | PII jurisdiction |
| `src/security/jurisdiction_policy.py` | **Create** — Jurisdiction → PII policy mapping | PII jurisdiction |
| `src/security/privacy_guard.py` | **Modify** — Accept jurisdiction parameter | PII jurisdiction |
| `spine_api/routers/auth.py` | **Modify** — Add slowapi rate limit decorators | Rate limiting |
| `spine_api/core/middleware.py` | **Modify** — Add slowapi middleware | Rate limiting |
| `pyproject.toml` or `requirements.txt` | **Modify** — Add `slowapi` dependency | Rate limiting |

---

## Verification Checklist (run after each gap is addressed)

- [ ] All existing tests still pass (`uv run pytest`)
- [ ] New audit log entries appear for POST/PUT/PATCH/DELETE requests
- [ ] Rate limiting returns 429 when limits exceeded
- [ ] PII guard routes correctly based on agency jurisdiction
- [ ] No regressions in auth flow (signup → login → me → refresh → logout)