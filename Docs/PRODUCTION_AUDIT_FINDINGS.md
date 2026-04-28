# Production Audit Findings — Waypoint OS

**Review Date:** 2026-04-28
**Scope:** Deployment configs, dependencies, environment setup, production readiness
**Rule:** Report only — no code changes, no git commands

---

## 1. Deployment Configuration

### 1.1 HIGH: Dockerfile Has Wrong Module Path

**File:** `Dockerfile:57`
```
COPY spine-api/ ./spine-api/
```

**Problem:** The directory on disk is `spine_api` (underscore), not `spine-api` (hyphen). The COPY command references a non-existent path, causing the Docker build to fail.

**File:** `Dockerfile:79`
```
ENTRYPOINT ["uvicorn", "spine-api.server:app", ...]
```

**Problem:** The uvicorn entry point uses `spine-api.server:app` (hyphen) but the Python module on disk is `spine_api.server` (underscore). Python cannot import a module with hyphens. This will cause a runtime `ModuleNotFoundError`.

**Impact:** The Docker image cannot build or run with the current Dockerfile.

### 1.2 MEDIUM: docker-compose.yml Missing spine-api Service

**File:** `docker-compose.yml` — only defines PostgreSQL, not the spine-api FastAPI service.

**Impact:** `docker compose up` only starts the database. Developers must manually start the server, and there's no documented way to do a single-command full-stack startup.

### 1.3 MEDIUM: Four Deployment Targets Without Canonical

| Config | Platform | Last Updated | Status |
|--------|----------|-------------|--------|
| Dockerfile | Generic Docker | Appears recent | BROKEN (see 1.1) |
| docker-compose.yml | Docker Compose | Recent | INCOMPLETE (no app service) |
| fly.toml | Fly.io | Apr 15 | Uses placeholder image `ghcr.io/your-org/spine-api:latest` |
| render.yaml | Render | Apr 15 | Builds directly from git |
| Procfile | Heroku/Fly/Render | Apr 15 | Wraps uvicorn command |

**Impact:** No single deployment path is documented as canonical. Config drift is likely. The fly.toml references a non-existent container registry path.

### 1.4 MEDIUM: No Database Migration Step in Deploy

- Dockerfile does not run `alembic upgrade head`
- fly.toml has empty `release_command`
- render.yaml has no migration step

**Impact:** Deploying a new version without running migrations will break if the schema has changed.

---

## 2. Security Configuration

### 2.1 HIGH: Static Encryption Key in Source Code

**File:** `src/security/encryption.py:22`
```python
ENCRYPTION_KEY = b'v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8='
```

**Problem:** When `ENCRYPTION_KEY` is not set in the environment (which is the default), a hardcoded key is used. This key is the same across all deployments. Anyone with the source code can decrypt data encrypted in dogfood mode.

**Mitigation:** The code raises `ValueError` in `DATA_PRIVACY_MODE=production` if the key is unset. But `DATA_PRIVACY_MODE` defaults to `dogfood`, which silently uses the static key.

### 2.2 MEDIUM: No Refresh Token Rotation

**File:** `spine_api/core/security.py`

JWT tokens are issued without a refresh token mechanism. Session invalidation requires token expiry. No blacklist/cache mechanism exists to revoke tokens.

### 2.3 LOW: Dev Password in docker-compose.yml

**File:** `docker-compose.yml:7`
```
POSTGRES_PASSWORD: waypoint_dev_password
```

Standard for local development, but flag as a reminder for production.

---

## 3. Environment Variable Coverage

### 3.1 MEDIUM: Required vs Optional Not Documented

The `.env.example` file documents all variables well, but doesn't distinguish:
- Which are required in production vs. optional
- Which are required for local development
- Which have secure defaults vs. must be explicitly set

### 3.2 LOW: Missing Variables in .env.example

Based on code inspection, the following env vars are read but NOT documented in `.env.example`:
- `ENCRYPTION_KEY` (src/security/encryption.py:13)
- `DATA_PRIVACY_MODE` (src/security/privacy_guard.py:32)
- `LLM_GUARD_ENABLED` (src/decision/hybrid_engine.py:29)
- `GEMINI_API_KEY` is documented (good)

---

## 4. Dependency Analysis

### 4.1 LOW: Potentially Unused Production Dependencies

**Based on project structure (Frontend is Next.js, backend is FastAPI):**
- `streamlit>=1.40.0` — Streamlit is a core dependency. The root-level `app.py` suggests there was/will be a Streamlit UI, but the primary frontend is Next.js.
- `rich>=14.3.3` — Rich is used? Verify if it's imported anywhere.

**LLM Dependencies (installed separately via `uv add --group llm`):**
- `transformers>=4.30.0`
- `torch>=2.0.0`
- `sentencepiece>=0.1.99`

These are heavy dependencies (~2-4GB) only needed if running local LLM inference. Good that they're in a separate dependency group.

### 4.2 LOW: Unused Imports (ruff F401)

**File:** `spine_api/notifications.py:12-13`
- `smtplib` imported but unused
- `email.mime.text.MIMEText` imported but unused

---

## 5. Monitoring and Observability

### 5.1 LOW: No Structured Logging

The project uses Python's standard `logging` module. No structured logging (JSON logs, correlation IDs, log levels enforced) is configured.

### 5.2 LOW: No APM or Metrics Export

No application performance monitoring or metrics endpoint configured beyond the `/health` endpoint.

### 5.3 MEDIUM: Print Statements Instead of Logging

Multiple production code paths use `print()` instead of `logging`:
- `src/intake/decision.py:55, 136, 1313` — warning messages
- `src/llm/local_llm.py:107-144` — model loading status

These won't appear in log files or log aggregation systems.

---

## 6. CI/CD

### 6.1 MEDIUM: No CI Pipeline Detected

No GitHub Actions workflows found. No `.github/workflows/` directory. No test runner configuration in CI.

**Impact:** No automated test execution on pull requests or merges.

---

## 7. Summary

| Severity | Count | Items |
|----------|-------|-------|
| HIGH | 2 | Dockerfile wrong module path, static encryption key fallback |
| MEDIUM | 6 | Missing CI, no migrations in deploy, missing spine-api service in docker-compose, 4 deployment targets with drift, no auth rate limiting, print() statements |
| LOW | 5 | Unused deps, unused imports, missing env vars in .example, no structured logging, dev password in compose |

**Critical Path to Launch:**
1. Fix Dockerfile (spine-api -> spine_api)
2. Set DATA_PRIVACY_MODE=production and require ENCRYPTION_KEY env var
3. Choose one deployment target and make it canonical
4. Add database migration step to deployment
5. Set up CI pipeline
