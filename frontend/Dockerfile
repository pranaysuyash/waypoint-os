# =============================================================================
# Dockerfile — frontend (Next.js)
# =============================================================================
# Multi-stage build for the Next.js frontend. Uses npm for dependency
# management and produces a minimal production image.
#
# Build:
#   docker build -t waypoint-frontend -f frontend/Dockerfile ./frontend
#
# Run:
#   docker run -p 3000:3000 \
#     -e SPINE_API_URL=http://host.docker.internal:8000 \
#     waypoint-frontend
# =============================================================================

# ---- Stage 1: Dependencies ----
FROM node:20-alpine AS deps

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Install dependencies (frozen lockfile for reproducible builds)
RUN npm ci

# ---- Stage 2: Build ----
FROM node:20-alpine AS builder

WORKDIR /app

# Copy installed deps from previous stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Build Next.js app
RUN npm run build

# ---- Stage 3: Production runtime ----
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built output from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
