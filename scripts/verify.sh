#!/usr/bin/env bash
set -euo pipefail

SKIP_HEALTH=0

for arg in "$@"; do
  case "$arg" in
    --skip-health)
      SKIP_HEALTH=1
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: ./scripts/verify.sh [--skip-health]"
      exit 2
      ;;
  esac
done

echo "[verify] Backend tests"
uv run pytest

echo "[verify] Frontend dependencies"
if [[ ! -d "frontend/node_modules" ]]; then
  (cd frontend && npm ci)
fi

echo "[verify] Frontend lint + typecheck + tests"
(
  cd frontend
  npm run lint
  npm run typecheck
  npm run test -- --run
)

if [[ "$SKIP_HEALTH" -eq 0 ]]; then
  echo "[verify] Backend health"
  curl -fsS http://127.0.0.1:8000/health >/dev/null
fi

echo "[verify] All checks passed"
