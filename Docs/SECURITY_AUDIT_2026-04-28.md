# Security Audit Report -- travel_agency_agent

**Date:** 2026-04-28
**Scope:** Full project including `spine_api/`, `frontend/`, `src/`, infra configs

---

## Attack Surface Summary

| Layer | Exposure | Notes |
|-------|----------|-------|
| FastAPI `spine_api` | TCP 8000 | `POST /run`, `GET /trips/*`, `PATCH /trips/*`, `GET /runs/*`, workspace, frontier, auth |
| Postgres (docker) | TCP 5432 | Dev only; default creds in docker-compose |
| Frontend (Next.js) | TCP 3000 | Public routes at `/`, `/login`, `/signup`, `/itinerary-checker` |
| LLM API keys | Env vars | Gemini, OpenAI, HuggingFace -- in `.env.example` |
| File persistence | `data/trips/*.json` | JSON files with encrypted PII fields in SQL mode, plaintext in file mode |

---

## Issues Found

### P0 -- Critical

**P0-01: Hardcoded JWT Signing Secret**
File: `spine_api/core/security.py:17`

```python
JWT_SECRET = os.getenv("JWT_SECRET", "waypoint-dev-secret-change-in-production")
```

The fallback secret is a hardcoded, well-known string. If `JWT_SECRET` is not set in production, anyone can forge valid tokens.

Risk: Token forgery, privilege escalation, account takeover.
Fix: Remove the fallback; crash (raise) at startup if `JWT_SECRET` is unset in production. Validate via lifespan hook.

**P0-02: Hardcoded Encryption Key**
File: `src/security/encryption.py:22`

```python
ENCRYPTION_KEY = b'v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8='
```

Static Fernet key in source code. Used to encrypt all PII database fields (`extracted`, `raw_input`, `contact_email`, `passport`, etc.) when `ENCRYPTION_KEY` env var is unset.

Risk: All PII fields at rest are encrypted with a public, unchanging key. Anyone with repo access can decrypt production data.
Fix: Require `ENCRYPTION_KEY` env var in production (already partially done -- raises if `DATA_PRIVACY_MODE=production`). Extend to beta mode too.

### P1 -- Major

**P1-01: Dockerfile References Wrong Directory Name**
File: `Dockerfile:57`

```dockerfile
COPY spine-api/ ./spine-api/
```

Directory is `spine_api` (underscore). `spine-api` doesn't exist. This `COPY` fails silently (build doesn't fail) but the resulting image is missing the entire spine API.

Risk: Docker image is non-functional.
Fix: `COPY spine_api/ ./spine_api/`

**P1-02: Default Database Credentials in Source**
Files: `spine_api/core/database.py:22-25` and `docker-compose.yml:6-7`

- `docker-compose.yml`: `POSTGRES_PASSWORD: waypoint_dev_password`
- `database.py`: `DATABASE_URL` fallback embeds the same password

Risk: If deployed with these defaults, DB is trivially accessible.
Fix: Require `DATABASE_URL` env var in production; remove password from source default.

**P1-03: Password Reset Token Returned in Response Body**
File: `spine_api/services/auth_service.py:324-327`

```python
return {
    ...
    "reset_token": plain_token,  # Remove in production (use email instead)
}
```

The password-reset token is returned in the API response. Token should only go via email.

Risk: Anyone with network access to the API response can reset passwords.
Fix: Remove from response; only send via email. Comment in code explicitly flags this.

### P2 -- Medium

**P2-01: Refresh Token Reuse (No Rotation)**
File: `spine_api/services/auth_service.py:226-271`

`refresh_access_token()` creates new access + refresh tokens but old refresh tokens remain valid.

Risk: Stolen refresh tokens can be used indefinitely until expiry (7 days).
Fix: Invalidate old refresh tokens on rotation. Store a token family + counter in the DB and reject reuse.

**P2-02: Access Token TTL Mismatch (24h vs 15min)**
- `spine_api/core/security.py:19`: `ACCESS_TOKEN_EXPIRE_HOURS = 24`
- `spine_api/routers/auth.py:42`: Cookie max_age = 15 minutes

The token itself is valid for 24 hours but the cookie expires in 15 minutes. A direct Bearer header auth bypasses the short cookie TTL.

Risk: If a token leaks (logs, XSS of localStorage if client stores it), attacker can use it for 24 hours via `Authorization: Bearer` header.
Fix: Set `ACCESS_TOKEN_EXPIRE_HOURS = 0.25` (or `MINUTES = 15`) to match cookie.

**P2-03: CORS Allows All Methods and Headers**
File: `spine_api/server.py:338-343`

```python
allow_methods=["*"],
allow_headers=["*"],
```

Plus `allow_credentials=True`. While `allow_origins` is a finite list, `*` on methods/headers is unnecessarily permissive.

Risk: Low (origin restricted), but defensive hardening is cheap.
Fix: Restrict methods to `["GET", "POST", "PATCH", "DELETE", "OPTIONS"]` and headers to explicit set.

**P2-04: No Rate Limiting Anywhere**
No rate limiting on any endpoint: `/api/auth/login`, `/api/auth/signup`, `/run`, `/trips`, password reset, etc.

Risk: Brute-force login, enumeration attacks, DoS via expensive LLM decision calls (each `/run` can invoke Gemini/OpenAI API = real dollar cost).
Fix: Add per-IP rate limiting (e.g., slowapi for FastAPI) -- especially on auth and `/run`.

**P2-05: Frontier Router Accepts `agency_id` from Request Body**
File: `spine_api/routers/frontier.py:26-31`

```python
class GhostWorkflowCreate(BaseModel):
    agency_id: str  # from client, not from JWT
```

The user provides `agency_id` in the request body rather than deriving it from the authenticated JWT.

Risk: Users can create ghost workflows / log emotions for any agency.
Fix: Remove `agency_id` from request models; derive from `get_current_agency_id` dependency.

### P3 -- Minor

**P3-01: `patch_trip` Accepts `Dict[str, Any]` (No Validation)**
File: `spine_api/server.py:1231-1285`

```python
@app.patch("/trips/{trip_id}")
def patch_trip(
    trip_id: str,
    updates: Dict[str, Any],
    ...
```

No Pydantic model for allowed fields. Any trip field can be set to any value.

Risk: Unexpected state mutations, data corruption. While agency scoping is enforced, there is no field-level validation.
Fix: Create a `TripUpdateRequest` Pydantic model with explicit optional fields and constraints.

**P3-02: Swagger/OpenAPI Exposed on Public Routes**
File: `spine_api/core/middleware.py:33`

```python
PUBLIC_PATHS: set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}
```

Full API documentation is publicly accessible with no authentication.

Risk: Information disclosure (reveals all endpoints, schemas).
Fix: Restrict `/docs`, `/openapi.json`, `/redoc` in production via auth or disable entirely.

**P3-03: No Security Headers**
No `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, or `Strict-Transport-Security` headers on the FastAPI or Next.js responses.

Risk: Clickjacking, MIME-type sniffing, missing XSS protections.
Fix: Add security headers via FastAPI middleware and Next.js `headers()` in `next.config.ts`.

**P3-04: `.env.example` Duplicates Keys**
File: `.env.example`

`GEMINI_API_KEY` appears at lines 56 and 99. `OPENAI_API_KEY` at lines 68 and 101. Unclear which is authoritative.

Risk: Confusion during setup; operator may set one and miss the other.
Fix: Deduplicate; keep each key once with clear comments.

**P3-05: `_to_dict` Uses `__dict__` Introspection**
File: `spine_api/server.py:560-569`

```python
if hasattr(obj, "__dict__"):
    return {k: _to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
```

Serializes arbitrary Python objects by enumerating `__dict__`. Coupled with the pipeline checkpointing which stores to JSON, this could expose internal attributes.

Risk: Information leakage of internal object state into persistent storage.
Fix: Use dedicated `model_dump()` on Pydantic models only; remove `__dict__` fallback.

---

## Quick Wins (Highest Impact, Lowest Effort)

| # | Fix | File(s) | Effort | Impact |
|---|-----|---------|--------|--------|
| 1 | Remove JWT fallback secret; crash if unset in prod | `spine_api/core/security.py:17` | 5 min | P0 elimination |
| 2 | Require `ENCRYPTION_KEY` env var in beta + prod | `src/security/encryption.py:18` | 5 min | P0 elimination |
| 3 | Fix Dockerfile `spine-api` -> `spine_api` | `Dockerfile:57` | 1 min | Build fix |
| 4 | Deduplicate env vars in `.env.example` | `.env.example` | 2 min | Ops clarity |
| 5 | Restrict CORS methods and headers | `spine_api/server.py:340-341` | 3 min | Defense hardening |
| 6 | Reduce access token TTL to match cookie (15 min) | `spine_api/core/security.py:19` | 2 min | Limits exposure window |
| 7 | Remove `agency_id` from frontier request models | `spine_api/routers/frontier.py` | 10 min | Authorization gap |
| 8 | Add rate limiting to `/run` and `/api/auth/login` | `spine_api/server.py` | 15 min | Prevents brute-force + DoS |
| 9 | Add `Content-Security-Policy` to Next.js config | `frontend/next.config.ts` | 10 min | XSS mitigation |

---

## Overall Security Posture: 5.5 / 10

### Strengths (What's done right)

- httpOnly cookie-based auth (no token in response body for login/signup)
- Excellent log scrubbing filter (`SensitiveDataFilter`)
- Privacy guard blocking real PII in dogfood mode
- `extra="forbid"` on Pydantic request models
- Non-root user in Docker
- `poweredByHeader: false` in Next.js
- Auth middleware checks token + user active state
- DB session scoping by `agency_id` on all trip/run endpoints
- Password reset token hashed (SHA-256) before storage
- Password min length enforced (8 chars)

### Weaknesses (Must fix before launch)

- Two P0 crypto credential issues (JWT secret, encryption key)
- Refresh token reuse vulnerability
- No rate limiting on auth or LLM endpoints
- `patch_trip` accepts arbitrary fields (no model)
- Swagger publicly exposed
- No CSP or security headers
- Dockerfile won't build a working image (wrong dir name)
- Access token TTL mismatch between cookie and JWT claim
