# LR-B08/B09 Readiness and Observability Boundary — 2026-09-04

**Persona lens:** PER-0164 — Assumption Auditor. This record separates the
observed HTTP contract, the local remediation, and the deployment/operations
proof that still requires a real environment.

## Finding

Deployment manifests and container health checks name `GET /ready` as the
readiness probe (`render.yaml:19`, `fly.toml:51`, `docker-compose.yml:42`,
`Dockerfile:79`, and `Dockerfile.spine_api:61`). Before this wave,
`spine_api/core/middleware.py` did not list `/ready` in `PUBLIC_PATHS`, so an
unauthenticated probe was intercepted by authentication and returned `401`
instead of reaching `spine_api/routers/health.py`.

Fresh local observations before the fix were:

| Request | Result | Interpretation |
|---|---:|---|
| `GET /health` | 200 | Liveness route reachable |
| `GET /ready` | 401 | **Defect:** deployment readiness contract blocked by auth |
| `GET /metrics` | 401 | Protected/static observability surface; exposure is not assumed |
| `GET /docs` | 200 | Public API documentation |
| `GET /openapi.json` | 200 | Public API schema |

## Remediation implemented

- Added `/ready` to the narrow public-path allowlist, with an inline comment
  explaining that platform health checks must reach the dependency-aware
  handler without user authentication.
- Added `tests/test_readiness_auth_boundary.py` to exercise the ASGI boundary:
  unauthenticated `/ready` must return a readiness-shaped 200/503 response,
  while `/api/workspace` remains protected with 401.
- Changed `.github/workflows/deploy.yml` to call `/ready` and label the step as
  deployment-readiness verification rather than liveness verification.
- Readiness now resolves the single Alembic head from the running artifact's
  own migration graph and compares every `alembic_version` row against it;
  stale, empty, multi-row, multi-head, or unreadable graphs fail closed.

## Verification

- Focused boundary/readiness/auth command:
  `PYTHONPATH=src .venv/bin/pytest -q tests/test_readiness_auth_boundary.py
  tests/test_health_readiness.py tests/test_auth_integration.py -k 'ready or
  public or protected'` → **9 passed, 15 deselected** in 8.72s.
- Targeted Ruff and deployment YAML parsing passed.
- Expanded exact-head coverage (stale, empty, multiple revisions, and graph
  resolution failure) is included in the latest focused command: **13 passed,
  15 deselected**.
- Full backend runner after the remediation:
  `scripts/run_backend_tests.sh` → **3,756 passed, 10 skipped, 0 failed** in
  226.14s, with 8 known Python 3.13 fork deprecation warnings. The runner
  detected the existing `:8000` development server; this is a green
  server-present regression receipt, not a hermetic or hosted deployment gate.
- Exact-head implementation focused command:
  `PYTHONPATH=src .venv/bin/pytest -q tests/test_health_readiness.py
  tests/test_readiness_auth_boundary.py tests/test_auth_integration.py -k
  'ready or public or protected'` → **13 passed, 15 deselected**; targeted
  Ruff passed.
- Post-A-20 model-registration rerun:
  `scripts/run_backend_tests.sh` → **3,760 passed, 10 skipped, 0 failed** in
  304.49s, with the same 8 known Python 3.13 fork deprecation warnings and
  server-present/non-hermetic boundary. The four-test increase is the focused
  metadata-contract coverage now included in the full suite.

## Remaining B08/B09 work

1. Add bounded DB and Redis timeouts and deterministic fault-injection tests
   for dependency-down, timeout, and migration-stale states.
2. Run the readiness probe in compose, Fly, and Render deployment environments
   and capture HTTP receipts, logs, and rollback behavior.
3. Decide the metrics contract before exposure: Prometheus/OpenMetrics versus
   the current static JSON, version source, low-cardinality labels, scrape
   authentication/private-network mechanism, and PII/token/prompt exclusion.
4. Add authenticated or platform-native observability checks only after the
   exposure decision; do not make `/metrics` public by analogy with `/ready`.
5. Verify multi-worker and multi-replica readiness, including migration
   ownership, Redis failure, restart, and alert delivery.

**Disposition:** `/ready` auth-boundary and exact-artifact-head checks
**ACCEPT — locally fixed**; bounded dependency timeouts, fault injection,
deployment/runtime proof, and metrics design **OPEN / EXPLORE**. No claim of
hosted readiness or production observability is made by this document.
