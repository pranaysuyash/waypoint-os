#!/usr/bin/env bash
# run_backend_tests.sh — run backend tests with CI-identical environment.
#
# Why this exists: the 2026-08-29 Persona Council audit reported "358 failed /
# 19 errors" by running pytest without the env vars CI sets. With CI-identical
# env the suite is green (3206 passed / 10 skipped on 2026-08-30). Missing env
# makes DB-backed tests fail in ways that look like product regressions.
# Always run the suite through this script (or CI) and cite the numbers.
#
# Usage:
#   scripts/run_backend_tests.sh                        # full suite (CI parity)
#   scripts/run_backend_tests.sh tests/test_run_lifecycle.py -x   # any pytest args
#
# Env overrides are respected: if DATABASE_URL / TRIPSTORE_BACKEND /
# JWT_SECRET / PUBLIC_CHECKER_AGENCY_ID are already set, they are kept.
#
# IMPORTANT (2026-08-30): if the dev server is running on :8000, the
# integration tests execute against it mid-suite and contend with the shared
# database — this manufactures phantom failures (observed: three consecutive
# full-suite runs produced three different failure sets, 13 failures and a
# 25-minute runtime with the server up vs 0-1 failures in ~70s with it down;
# every failing test passes in isolation). For a citable baseline, stop the
# dev server first. The script warns when it detects one.

set -euo pipefail
cd "$(dirname "$0")/.."

if curl -s -o /dev/null --max-time 2 http://127.0.0.1:8000/health; then
    echo "WARNING: dev server detected on :8000 — integration tests will run" >&2
    echo "against it and results are likely polluted (see header). Stop it for" >&2
    echo "a citable baseline." >&2
fi

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os}"
export TRIPSTORE_BACKEND="${TRIPSTORE_BACKEND:-sql}"
export JWT_SECRET="${JWT_SECRET:-test-jwt-secret-for-ci-only-32bytes!}"
export PUBLIC_CHECKER_AGENCY_ID="${PUBLIC_CHECKER_AGENCY_ID:-d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b}"

# CI parity: these two files require an OPENAI_API_KEY (optional deps) and are
# excluded from the CI run — mirror that locally so counts are comparable.
DEFAULT_ARGS=(tests/ --ignore=tests/test_vision_extraction.py --ignore=tests/test_extraction_fallback.py)

if [ "$#" -eq 0 ]; then
    exec .venv/bin/python -m pytest -q "${DEFAULT_ARGS[@]}"
else
    exec .venv/bin/python -m pytest -q "$@"
fi
