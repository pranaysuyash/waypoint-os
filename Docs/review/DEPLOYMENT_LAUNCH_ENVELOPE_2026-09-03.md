# Deployment and Launch Envelope — 2026-09-03

**Status:** implemented locally where the repository owns the behavior; external
deployment and operator gates remain open

**Scope owner:** deployment/launch-envelope slice

**Related findings:** LR-B01, LR-B02, LR-B03, LR-B06, LR-B08, LR-B14, LR-B15,
LR-O01, LR-O03, LR-O07, PT-08, A-20

**Canonical evidence rule:** this record describes the current checkout and
the commands run on 2026-09-03. It does not upgrade local static or targeted
test evidence into deployed/production proof.

## Outcome

The deployment envelope now has one explicit, fail-closed model:

1. `ENVIRONMENT`, database credentials, API secrets, proposal signing key,
   CORS origins, and the public-checker agency are explicit inputs in compose.
2. `SPINE_API_DISABLE_AUTH` is parsed as a boolean; only `1`, `true`, `yes`,
   and `on` enable the development/test bypass. Values such as `0` and
   `false` leave authentication enabled.
3. Staging/production require a shared `REDIS_URL`, SQL trip storage, durable
   idempotency, non-placeholder secrets, and an explicit environment.
4. `/health` remains liveness-only. `/ready` checks database connectivity,
   an applied Alembic revision, and Redis when configured/required; it returns
   `503` for an unmet required dependency and does not expose driver errors.
5. Compose runs migrations as a one-shot `migrations` service before the API.
   Production Fly/Render release commands run migrations only and do not seed
   a test/public-checker agency.
6. Both backend production Dockerfiles run as `appuser`, use a pinned uv image
   and frozen lockfile, and default to one Uvicorn worker. One worker is a
   deliberate safety boundary until background supervisors are separated into
   a durable worker service.
7. Compose keeps Postgres and Redis internal by default. Server-side BFF calls
   use `SPINE_API_URL=http://spine_api:8000`; browser-facing public API values
   are supplied as a host-resolvable build argument instead of the internal
   Docker hostname.

## Files changed

- `spine_api/core/startup_assertions.py` — canonical auth-bypass parser,
  production-like Redis requirement, development-credential rejection, and
  32-character secret minimum.
- `spine_api/core/auth.py`, `spine_api/core/middleware.py`, `spine_api/server.py`
  — all runtime auth bypass checks use the canonical parser.
- `spine_api/routers/health.py` — dependency-aware readiness contract.
- `tests/test_startup_assertions.py` — boolean parsing, deployment secret,
  Redis, and middleware regression coverage.
- `tests/test_health_readiness.py` — migration, Redis, failure, and redaction
  readiness coverage.
- `alembic.ini`, `alembic/env.py` — no committed database credential; every
  Alembic invocation requires `DATABASE_URL`.
- `Dockerfile`, `Dockerfile.spine_api` — locked multi-stage backend images,
  non-root user, readiness healthcheck, and one-worker default.
- `Dockerfile.frontend` — browser API values are build arguments for standalone
  Next.js output.
- `docker-compose.yml` — explicit secret/config inputs, migration gate,
  internal data services, readiness healthcheck, and browser/BFF URL split.
- `fly.toml`, `render.yaml`, `Procfile` — one-worker production commands,
  readiness probes, SQL/idempotency settings, and migration-only release step.

## Verification evidence

| Check | Result | Evidence tier / sensitivity |
|---|---|---|
| `docker compose config --quiet` with explicit non-production test values | pass | Tier 1 / S1 |
| `env -u DATABASE_URL .venv/bin/alembic current` | rejected with `DATABASE_URL is required for Alembic` | Tier 2 / S2 (fail-closed regression) |
| `python -m py_compile` on changed Python modules | pass | Tier 1 / S1 |
| `pytest tests/test_startup_assertions.py tests/test_health_readiness.py tests/test_server_startup_invariants.py` (run as `5 + 51` split to avoid a transient test-process timeout) | 56 passed | Tier 2 / S1; the auth boolean tests are regression-sensitive but were not run as a pre-fix failure capture |
| `git diff --check` on deployment slice | pass | Tier 1 / S1 |
| Docker image build/inspect | not established | Docker daemon did not return; the hanging local build/inspect commands were terminated. No image or non-root runtime claim is made. |
| Deployed `/ready`, migration release, external Redis, rollback, restore | unknown | Requires an authorized target environment and operator/provider configuration |

## External/operator gates

These remain deliberately open and cannot be closed by local configuration
alone:

- Set real `DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`, `JWT_SECRET`,
  `PROPOSAL_SIGNING_KEY`, `SPINE_API_CORS`, and an existing production
  `PUBLIC_CHECKER_AGENCY_ID` in the deployment secret manager.
- Confirm whether Fly or Render is the canonical production platform; remove
  the unused deployment manifest after an explicit platform decision, using
  the supersession workflow rather than silent deletion.
- Run the release migration against a disposable production-like database,
  inspect `alembic current`, then run `/ready` with database and Redis failure
  injection.
- Build and scan both backend and frontend images, inspect the effective user,
  command, healthcheck, dependency versions, and filesystem permissions.
- Decide and document the durable worker topology before increasing workers
  above one. The current API process starts supervisor/recovery loops, so
  multi-worker launch needs separate worker ownership and duplicate-run proof.
- Configure backups, restore drill, alert destination, rollback command, and
  owner. Readiness cannot prove backup/restore or operator response.
- Establish a browser-level compose smoke test proving the browser uses the
  host-resolvable API URL while server-side BFF calls use the mesh hostname.

## Alignment assessment

This slice is first-principles aligned because it makes the real trust and
failure boundaries explicit: environment strings are normalized once, schema
state is checked separately from socket reachability, and a release migration
is an explicit lifecycle step rather than an API startup side effect. It is
long-term aligned because the configuration has one canonical runtime contract
and keeps worker scaling behind an architectural decision instead of encoding
duplicate background ownership. It is not a complete launch approval: provider,
deployment, backup, browser, and operator evidence remain separate gates.

## Revisit triggers

- A dedicated worker deployment is introduced: re-evaluate `SPINE_API_WORKERS`,
  idempotency, leases, scheduler ownership, and readiness dependencies.
- The frontend is deployed behind a different origin or CDN: update the
  browser build argument and CORS contract, then run browser smoke.
- Redis becomes optional by design: replace the production assertion only after
  proving equivalent shared rate-limit and usage-budget semantics.
- Alembic migrations become a managed platform feature: retain the explicit
  `DATABASE_URL` requirement and update only the release command ownership.
