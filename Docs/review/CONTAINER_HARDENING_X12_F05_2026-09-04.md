# X-12 / F-05 Container Hardening Evidence — 2026-09-04

## Scope and outcome

This is the bounded container-hardening slice for X-12/F-05. The goal is to
make a developer checkout an unsafe build input by default: local secrets,
personal/runtime data, mutable image tags, and root-owned application layers
must not silently enter a production image.

The implementation is source-level and local. It does not claim a built image,
runtime, deployed environment, vulnerability scan, or production readiness.

## Observed baseline (Tier 1)

The live checkout contained approximately **742 MB** under `data/`, including
approximately **604 MB** under `data/runs/` and **69 MB** under
`data/documents/`. The root `.dockerignore` did not exclude dotenv files or
runtime data, while the API Dockerfiles copied `data/` wholesale. The API and
frontend Dockerfiles used mutable `python:3.13-slim`/`node:20-alpine` tags, and
compose used mutable `postgres:16-alpine`/`redis:7.4-alpine` tags.

The original X-12 finding also described `uv run`/lockfile drift and root
execution. The current API Dockerfiles already had `uv.lock`, `uv sync
--frozen --no-dev`, and an app user; this slice retained those improvements and
closed the remaining reproducibility/context/ownership gaps.

## Implemented controls

### Build-context data and secret boundary

- Root `.dockerignore` now excludes `.env`/`.env.*` (including nested files),
  private-key/certificate extensions, and runtime or local state:
  `runs`, `documents`, `audit`, `trips`, `test_trips`, `drafts`, `memory`,
  `product_b_events`, `proposals`, `guard`, `overrides`, `assignments`, `logs`,
  `kdd`, fixtures, evals, shadow data, local team/demo state, and local DB
  files.
- Only the runtime geography datasets (`cities.json`, `cities5000.txt`) and
  checked-in seasonal campaign configuration are re-included from `data/`.
  The application can recreate writable directories, while production compose
  uses SQL and named/external state volumes.
- `frontend/.dockerignore` covers the separate `frontend/` build context,
  including dotenv files, credentials, dependencies, build output, and local
  artifacts.

### Reproducible image inputs

All production Dockerfiles now pin every `FROM` image to a Docker Registry
manifest digest, with tag and digest kept together for intentional refreshes.
The digests were resolved from the official registries on 2026-09-04:

| Image | Digest |
|---|---|
| `python:3.13-slim` | `sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285` |
| `node:20-alpine` | `sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293` |
| `ghcr.io/astral-sh/uv:0.8.14` | `sha256:f3660c56d5b08d6c516360981bedc439f499b9bf37f46a216018da3777a74011` |
| `postgres:16-alpine` | `sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685` |
| `redis:7.4-alpine` | `sha256:ff02b58f971e7d7d156a1267e283fcbbeee91773b6aa36c49dac28ecfe28eadf` |

The digest is a reproducibility input, not a vulnerability verdict. Refreshes
must re-run image inspection and the scanner before promotion.

### Runtime privilege and signal behavior

- API runtime stages create `appuser` before copying files, copy the venv and
  application layers with `--chown=appuser:appuser`, and run as
  `USER appuser:appuser`.
- Frontend runtime stages run as `USER nextjs:nodejs` and retain chowned
  standalone/static layers.
- All four production Dockerfiles declare `STOPSIGNAL SIGTERM`. API commands
  use `exec` so the application receives the signal directly; the Node process
  is launched directly.
- The API healthcheck remains `/ready`, which is the correct traffic-readiness
  contract for a service whose liveness and dependency/migration readiness are
  distinct.

### Stateful dependency exposure

Compose now pins Postgres and Redis images by digest and keeps their ports
internal to the bridge network. Only the API and frontend publish host ports by
default. This reduces accidental exposure of stateful services while keeping
the local service topology intact.

## Verification

| Check | Result | Evidence tier / sensitivity |
|---|---|---|
| `PYTHONPATH=src .venv/bin/pytest -q tests/test_container_hardening.py` | 6 passed | Tier 2 / S1 static regression contract |
| `.venv/bin/ruff check tests/test_container_hardening.py` | pass | Tier 2 / S1 |
| `docker compose config --quiet` with non-secret placeholder environment | pass (`docker compose` parser available) | Tier 1; does not start containers |
| `uv lock --check` | pass | Tier 2 / S1 lock consistency |
| Docker daemon/image build | unavailable: `docker` CLI/daemon is not installed on this host | Unknown; exact next check below |
| Trivy/Grype/Syft image scan | unavailable: no scanner installed and no image exists locally | Unknown; exact next check below |

The policy tests are intentionally static. They prove the source contract but
cannot prove that Docker accepts the syntax, that the image is small, that all
runtime imports work after context exclusions, or that OS packages have no
known vulnerabilities.

## Residual gates and exact next checks

These remain open and should not be converted into a local “closed” claim:

1. **Build proof (Tier 3):** on a host with Docker BuildKit, run
   `docker build --pull=false --platform linux/amd64 -f Dockerfile.spine_api -t waypoint-spine-api:local .`
   and the equivalent root-context frontend build. Also run the nested-context
   build: `docker build --pull=false --platform linux/amd64 -f frontend/Dockerfile -t waypoint-frontend:local frontend`.
2. **Context proof:** inspect the built context/image and assert no dotenv,
   certificate/key, `data/runs`, `data/documents`, audit, trip, fixture, or
   local DB artifacts are present; measure image/context size against the
   pre-change 742 MB checkout state.
3. **Runtime proof (Tier 4):** run the compose stack with explicit deployment
   secrets, then verify `/health` versus `/ready`, migration ordering, API and
   frontend healthchecks, non-root UID/GID (`docker inspect`), graceful
   SIGTERM shutdown, and no accidental Postgres/Redis host listeners.
4. **Vulnerability/provenance proof (Tier 5):** run an approved scanner (for
   example `trivy image --scanners vuln,secret,misconfig`) and record image
   digest, SBOM, CVE policy, scanner version/database timestamp, and exceptions.
5. **Deployment proof:** repeat the same checks for the selected hosted target,
   including secret-manager injection, release migrations, persistent volumes,
   rollback, backup/restore, and multi-replica behavior.

## Decision and rollback

**Decision:** ACCEPT the source-level hardening slice; keep X-12/F-05 **partial**
until build, scan, runtime, and hosted evidence exists. Pinning digests is
preferred over tag-only “version pinning” because a tag can move without a
dependency diff. Excluding all data would break geography/config behavior, so
the narrow allowlist preserves those static inputs while excluding user and
evaluation state.

Rollback is a normal revert of this bounded file set if a verified build proves
that an allowed static input is required at runtime. Do not restore broad
`COPY data/` behavior; instead add the specific missing static input to the
allowlist and add a regression test documenting why it is required.

## Files changed

- `.dockerignore`
- `frontend/.dockerignore`
- `Dockerfile`
- `Dockerfile.spine_api`
- `Dockerfile.frontend`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `tests/test_container_hardening.py`
- this evidence record

No Git staging, commit, push, reset, checkout, stash, clean, deletion, or
external deployment was performed.
