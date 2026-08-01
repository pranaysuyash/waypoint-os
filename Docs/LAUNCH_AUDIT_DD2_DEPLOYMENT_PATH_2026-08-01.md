# DD-2: Deployment Path — Deep-Dive

**Date**: 2026-08-01 · **Parent**: `Docs/LAUNCH_AUDIT_BASELINE_2026-08-01.md` (B7–B10, H6–H8, H14)
**Evidence tier**: Tier 2 (static + DB queries + CLI auth checks). No deploy was attempted.

---

## Erratum to baseline (recorded per motto §0.12.1 — corrections are appends, not silent edits)

**Baseline H7 is reframed.** The staged +93-line change to `alembic/versions/0cd0399e2c3c_add_assigned_to_id_and_is_test.py` is a **new file** (`new file mode 100644`), not an edit to a committed migration. The real defect is worse in a different way:

> **The migration that the persistent dev DB is currently at (`alembic_version = 0cd0399e2c3c`, verified via psql) is not in git history.** It was created 2026-07-31, applied to the local DB, and never committed. A fresh checkout + `alembic upgrade head` will NOT produce `assigned_to_id`, `is_test`, `trips.destination`, or the `ix_trips_*` indexes that running code depends on. Verified the columns exist in the live DB.

**Action**: commit this migration before anything else deploys (operator approval required — git mutation). The migration itself is well-written (idempotent `_has_column`/`_has_index` guards).

## D1 — The product has never been deployed (confidence: high, Tier 2)

Cumulative evidence:

- `fly.toml:12` `[build] image = "ghcr.io/your-org/spine-api:latest"` — a literal placeholder; `fly deploy` would pull a nonexistent image and never build the local Dockerfile.
- `flyctl` is installed but **not authenticated** (`fly apps list` → "no access token") — no Fly app exists under this operator.
- `deploy.yml` health check URL carries the comment `# Adjust to match production URL` — never adjusted.
- Render path: `render.yaml` provisions **no database**; `DATABASE_URL` undeclared → falls back to the hardcoded **localhost** default with dev password (`spine_api/core/database.py:21-25`), which in any container is guaranteed-broken.

## D2 — Three half-paths, zero complete ones

| Path | State | Verdict |
|---|---|---|
| Fly (`fly.toml` + `deploy.yml` + `Procfile`) | placeholder image; unauthenticated; CD targets `main` but repo only has `master` | Closest to canonical — finish this one |
| Render (`render.yaml`) | no Postgres, localhost DATABASE_URL fallback, native env | Stale — delete or archive with a pointer note |
| docker-compose | correct local-dev stack (sets `TRIPSTORE_BACKEND=sql`, has frontend service) | Keep as local dev only |

Per AGENTS.md anti-duplication doctrine: **one canonical deploy path**. Recommendation: Fly for backend; delete `render.yaml` (archive note in Docs per doc-preservation rule).

## D3 — Dockerfile cannot run its own migrations (baseline B8, CONFIRMED)

- `alembic` IS in `pyproject.toml` deps → binary lands in `.venv/bin` — but `alembic/`, `alembic.ini`, and `scripts/` are **not COPYed** (`Dockerfile:56-59`). fly `release_command` (`fly.toml:15`) and compose `migrations` service (`docker-compose.yml:35-37`) both fail.
- Compose migrations use `uv run alembic …`; `uv` exists only in the `deps` stage, not runtime (`Dockerfile:37-38,53`) → `uv: command not found`.
- `data/` is COPYed wholesale (`Dockerfile:58`) and `.dockerignore` does not exclude it → local builds bake dev trip data (590k-city geography assets presumably intended, dev trips not) into the image.
- Fix (one commit): add `COPY alembic/ ./alembic/`, `COPY alembic.ini ./`, `COPY scripts/ ./scripts/`; switch compose migration command to `.venv/bin/alembic`; add `data/trips/ data/runs/ data/drafts/` to `.dockerignore` while keeping geography assets explicit.

## D4 — The safety-critical env vars are missing from every prod config (baseline B9/H6, CONFIRMED)

Not present in `fly.toml [env]`, `render.yaml envVars`, or Dockerfile ENV:

- `TRIPSTORE_BACKEND=sql` — without it: file store on an **ephemeral container filesystem** → all trips lost on every deploy/restart. This is the 2026-05-03 incident as a guaranteed production recurrence. Code hard-fails if unset only when `ENVIRONMENT=production|staging` (`server.py:204-208`) — but `ENVIRONMENT` is also unset, so the guard never fires.
- `ENVIRONMENT=production` — gates: ENCRYPTION_KEY enforcement, auth-bypass blocking, cookie `Secure` flag, reset-token exposure, rate-limiter posture.
- `DATABASE_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, `DATA_PRIVACY_MODE=production`, LLM keys — none declared even as `sync: false` placeholders, so there is no secrets checklist.

**Fix (one commit)**: add to fly.toml `[env]`: `ENVIRONMENT="production"`, `TRIPSTORE_BACKEND="sql"`, `DATA_PRIVACY_MODE="production"`; document `fly secrets set` list in `.env.example` + DD-2 follow-up. Long-term (cross-links baseline Theme 2): single startup config-assertion module that fails closed.

## D5 — No database is provisioned anywhere

Neither fly.toml (no `fly postgres` attachment) nor render.yaml (`databases:` absent) provisions Postgres. Launch needs: Fly Postgres (or managed PG) + `DATABASE_URL` secret + migration step that actually runs (blocked by D3). The frontend has **no deploy path at all** — no vercel.json, no .vercel, no fly app, no render service for Next.js. docker-compose runs it for local dev only.

## D6 — CD pipeline can't trigger and wouldn't be safe if it did (baseline B10, CONFIRMED)

- `deploy.yml` triggers on `push: branches: [main]`; the repo's only branch is `master` → the workflow has never run.
- No CI gate: deploy does not depend on `ci.yml` passing. A red commit would ship.
- The post-deploy health loop + `flyctl rollback` (deploy.yml:28-56) is a good instinct and should be kept.

**Fix (one commit)**: branch `main` → `master` (or create a `main` release branch — decision needed); add `workflow_run` gate on CI success; keep rollback.

## D7 — Observability is off in every deploy config (baseline H14, restated for the plan)

OTel only activates with `SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT`/`OTEL_EXPORTER_OTLP_ENDPOINT` (`server.py:95-119`) — unset everywhere. No Sentry, no structured logging, no uptime monitor. Minimum for paying users: error tracking (Sentry or equivalent) + uptime check on `/health`. This is a launch-gate item, not a nice-to-have (motto §0.10: observability is delivery).

---

## Canonical launch deploy plan (recommendation)

Commit-sized steps, in dependency order:

1. **Commit the applied migration** `0cd0399e2c3c` (operator git approval). Everything else depends on schema truth being in git.
2. **Dockerfile + .dockerignore fix** (D3).
3. **fly.toml fix**: remove `[build] image` placeholder (let it build the Dockerfile), add env vars (D4), attach Fly Postgres, set secrets.
4. **Delete render.yaml** (archive note) + fix deploy.yml branch + CI gate (D6).
5. **Frontend deploy decision** (operator input needed): Vercel (fastest for Next.js, free tier fine for soft launch) vs Fly (single-vendor). Recommendation: Vercel now, revisit later — do not let vendor purity delay launch.
6. **Error tracking + uptime** before the first paying user (D7).

## Decisions needed from operator

1. Git approval to commit the staged migration + ADR batch (currently uncommitted; migration is schema truth the DB already runs).
2. Canonical platform: Fly backend + Vercel frontend (recommended) vs all-Fly vs finish Render.
3. Branch model: deploy from `master` or create `main`.

## "Anything else?" (motto §0.1.1)

- `fly.toml` sets `PUBLIC_CHECKER_AGENCY_ID` to the **dev test agency** (`d1e3b2b6…`, per AGENTS.md the developer's working agency). Shipping that id as the public-collection agency in prod mixes test data into a customer-facing surface.
- `SPINE_API_WORKERS=4` with file-based draft/run-ledger stores is a multi-writer hazard on one container FS — another push toward Postgres-only persistence (baseline Theme 2).
- Deploy-time verification should include a tenancy smoke check (RLS posture inspector exists: `inspect_rls_runtime_posture`) — add to release_command chain.
- Not verified: actual Docker build (docker daemon available; build deferred — static COPY analysis is conclusive for D3). Whether `uv.lock` is used in CI (ci.yml uses uv — assumed yes, verify in DD-7).

## Status

Findings D1–D7: **verified, unfixed, awaiting operator decisions** (3 listed above). Next: DD-3 (tenancy & auth hardening).
