#!/bin/bash
# =============================================================================
# dev.sh — Start both spine-api and Next.js frontend for local development
#
# Usage:
#   ./dev.sh              # start both services
#   ./dev.sh --api-only   # start only spine-api
#   ./dev.sh --fe-only    # start only frontend
#   ./dev.sh --stop       # stop all services
# =============================================================================

set -e

cd "$(dirname "$0")"

SPINE_API_PID=""
NEXTJS_PID=""

cleanup() {
  echo "Stopping services..."
  [ -n "$SPINE_API_PID" ] && kill $SPINE_API_PID 2>/dev/null || true
  [ -n "$NEXTJS_PID" ] && kill $NEXTJS_PID 2>/dev/null || true
  exit 0
}

trap cleanup SIGINT SIGTERM

start_spine_api() {
  echo "Starting spine-api on http://127.0.0.1:8000 ..."
  if [ "${TRIPSTORE_BACKEND:-file}" = "sql" ]; then
    echo "Running SQL bootstrap preflight for public checker agency ..."
    TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run alembic upgrade head
    TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/bootstrap_public_checker_agency.py
  fi
  uv run uvicorn spine_api.server:app --port 8000 --reload &
  SPINE_API_PID=$!
  echo "spine-api started (PID $SPINE_API_PID)"
}

start_frontend() {
  echo "Starting Next.js frontend on http://localhost:3000 ..."
  cd frontend && npm run dev &
  NEXTJS_PID=$!
  echo "Next.js started (PID $NEXTJS_PID)"
}

case "${1:-}" in
  --api-only)
    start_spine_api
    wait $SPINE_API_PID
    ;;
  --fe-only)
    start_frontend
    wait $NEXTJS_PID
    ;;
  --stop)
    cleanup
    ;;
  *)
    start_spine_api
    sleep 3
    start_frontend
    echo ""
    echo "Services running:"
    echo "  spine-api:  http://127.0.0.1:8000"
    echo "  frontend:   http://localhost:3000"
    echo "  health:     http://127.0.0.1:8000/health"
    echo ""
    echo "Press Ctrl+C to stop both services."
    wait
    ;;
esac
