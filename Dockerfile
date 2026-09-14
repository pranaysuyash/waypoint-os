# =============================================================================
# Dockerfile — spine_api (Python module) / spine-api (service name)
# =============================================================================
# Multi-stage build for the FastAPI spine service.
#
# Build:
#   docker build -t spine-api --platform linux/amd64 .
#
# Run:
#   docker run -p 8000:8000 \
#     -e SPINE_API_CORS="https://your-frontend.com" \
#     -e TRAVELER_SAFE_STRICT=0 \
#     spine-api
#
# Production tip: Use --platform linux/amd64 on Apple Silicon (darwin) to avoid
# compatibility issues with the Python extension modules (uvloop, httptools).

# Digest pins are intentional; update the tag and digest together in a
# reviewed dependency-refresh change. Digest resolved from Docker Hub on
# 2026-09-04 (multi-architecture manifest).
FROM python:3.13-slim@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285 AS base

WORKDIR /app

# Install the small runtime utilities used by healthchecks and TLS validation.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Dependency installer — pin to lock file for reproducible builds
# =============================================================================

FROM base AS deps

COPY pyproject.toml uv.lock ./

# Install a pinned uv binary for reproducible dependency resolution.
COPY --from=ghcr.io/astral-sh/uv:0.8.14@sha256:f3660c56d5b08d6c516360981bedc439f499b9bf37f46a216018da3777a74011 /uv /bin/uv

# Sync dependencies into a venv (faster than pip, respects lock file)
RUN uv sync --frozen --no-dev --no-install-project

# =============================================================================
# Production image
# =============================================================================

FROM base AS runtime

WORKDIR /app

# Create the runtime identity before copying files so no application layer is
# owned by root. The process remains least-privileged after startup.
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Copy installed venv from deps stage
COPY --from=deps --chown=appuser:appuser /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser spine_api/ ./spine_api/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Non-root user for security
USER appuser:appuser

# Let the process receive the normal termination signal directly. The command
# uses exec below, so no shell remains as a signal-swallowing PID 1.
STOPSIGNAL SIGTERM

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ready || exit 1

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    SPINE_API_HOST=0.0.0.0 \
    SPINE_API_PORT=8000 \
    SPINE_API_WORKERS=1 \
    SPINE_API_RELOAD=0 \
    TRAVELER_SAFE_STRICT=1 \
    USE_HYBRID_DECISION_ENGINE=0

CMD ["sh", "-c", "exec uvicorn spine_api.server:app --host 0.0.0.0 --port ${SPINE_API_PORT:-8000} --workers ${SPINE_API_WORKERS:-1}"]
