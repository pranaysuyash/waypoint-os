# =============================================================================
# Dockerfile — spine-api
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

FROM python:3.13-slim AS base

WORKDIR /app

# Install system build dependencies (needed for uvloop, httptools, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Dependency installer — pin to lock file for reproducible builds
# =============================================================================

FROM base AS deps

COPY pyproject.toml uv.lock ./

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Sync dependencies into a venv (faster than pip, respects lock file)
RUN uv sync --frozen

# =============================================================================
# Production image
# =============================================================================

FROM base AS runtime

WORKDIR /app

# Copy installed venv from deps stage
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY src/ ./src/
COPY spine-api/ ./spine-api/
COPY data/ ./data/
COPY pyproject.toml uv.lock ./

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    SPINE_API_HOST=0.0.0.0 \
    SPINE_API_PORT=8000 \
    SPINE_API_WORKERS=4 \
    SPINE_API_RELOAD=0 \
    TRAVELER_SAFE_STRICT=0

ENTRYPOINT ["uvicorn", "spine-api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]