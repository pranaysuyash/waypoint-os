# Decision Log

**Purpose**: Durable record of meaningful architecture, product, integration, model, data-pipeline, payment, customer-facing, and operational decisions.

**Format per entry**: decision, date, context, options considered, chosen path, tradeoffs, status.

---

## D-001: Deployment Target — Render

**Date**: 2026-06-23  
**Context**: Three configs (Docker Compose, Fly.io, Render) existed simultaneously with incomplete Dockerfile. Needed single canonical target.  
**Options**: Render ($25/mo starter), Fly.io, bare VPS, Docker Compose-only  
**Decision**: Render starter plan ($25/mo)  
**Rationale**: Single platform, native Python + Node support, managed PostgreSQL, free SSL/CDN, lowest operational overhead for solo-founder  
**Tradeoffs**: More expensive per-unit than VPS; no native Redis; vendor lock-in  
**Status**: ✅ Active — Dockerfile fixed, CI pipeline created

---

## D-002: CI/CD Pipeline — GitHub Actions

**Date**: 2026-06-23  
**Context**: No CI pipeline existed. Code routinely merged with failing tests and lint violations.  
**Options**: GitHub Actions (free), GitLab CI, CircleCI, self-hosted  
**Decision**: GitHub Actions with 4 jobs: docs → ruff lint → backend tests → frontend quality  
**Rationale**: Free tier sufficient, co-located with repo, standard for monorepo  
**Tradeoffs**: 2,000 min/mo limit may constrain future expansion  
**Status**: ✅ Active — pipeline configured and running

---

## D-003: Docker Architecture — Single Image, Build Once

**Date**: 2026-06-23  
**Context**: Dockerfile was broken (wrong dir name `spine-api` instead of `spine_api`), no multi-stage build  
**Options**: Monolithic Dockerfile, multi-stage build, distroless base  
**Decision**: 3-stage build (base → deps → runtime) with `python:3.13-slim`  
**Rationale**: Reproducible builds via lock file, small runtime image, non-root user  
**Tradeoffs**: Larger than distroless; Python base image needs security updates  
**Status**: ✅ Active — Dockerfile fixed and working

---

## D-004: Database — SQLAlchemy 2.0 + PostgreSQL (Primary)

**Date**: 2026-05-03 (resolved 2026-05-12)  
**Context**: TripStore facade supported both JSON file store and PostgreSQL. The dual-store architecture caused a "missing trips" production bug when TRIPSTORE_BACKEND env var was absent.  
**Options**: PostgreSQL-only, file store-only, dual store with clear default  
**Decision**: Dual-store with TRIPSTORE_BACKEND=sql pinned as default; both backends support multi-status filtering and offset/limit pagination  
**Rationale**: file store useful for testing; SQL is production standard. Long-term migration to PostgreSQL-only planned.  
**Status**: ✅ Active — pinned in `.env`. Dual-store remains but marked for deprecation.

---

## D-005: Frontend Framework — Next.js 14 (App Router)

**Date**: 2026-04  
**Context**: Frontend needs to serve both agency operators and potentially travelers  
**Options**: Next.js App Router, Next.js Pages Router, Vite+SPA, Streamlit (legacy)  
**Decision**: Next.js 14 App Router with TypeScript, Tailwind CSS  
**Rationale**: Server components for auth, BFF API routes co-located, optimal for complex app routing  
**Tradeoffs**: Complexity vs SPA; server components add learning curve  
**Status**: ✅ Active — legacy Streamlit workbench retired

---

## D-006: Python Package Manager — uv

**Date**: 2026-04  
**Context**: Needed fast, reproducible Python dependency management  
**Options**: pip, pip-tools, poetry, pdm, uv  
**Decision**: uv for both development and Docker builds  
**Rationale**: 10-100x faster than pip, lock file support, works well with Docker multi-stage builds  
**Tradeoffs**: Relatively new tool, smaller ecosystem  
**Status**: ✅ Active — pinned in Dockerfile and dev workflow

---

## D-007: Pipeline Architecture — BFF + Modular Monolith

**Date**: 2026-05  
**Context**: Needed to decide between microservices, serverless, and monolith for the AI pipeline  
**Options**: Full microservices, BFF + modular monolith, serverless functions  
**Decision**: BFF (Next.js API routes) + FastAPI modular monolith in monorepo  
**Rationale**: Pragmatic for solo-founder; AI pipeline benefits from in-process orchestration; BFF keeps frontend concerns separate from AI logic  
**Tradeoffs**: Monolith limits independent scaling; all services share same deployment risk  
**Status**: ✅ Active

---

## D-008: LLM Provider Strategy — Multi-Provider

**Date**: 2026-04  
**Context**: Extraction pipeline needs reliable, cost-effective LLM access  
**Options**: OpenAI-only, Gemini-only, Claude-only, multi-provider with fallback  
**Decision**: Multi-provider — Gemini 2.0 Flash (primary extraction), OpenAI GPT-4o (fallback), Claude (safety/checker)  
**Rationale**: Cost optimization (Gemini cheaper for extraction), reliability via fallback, quality via specialized model selection  
**Tradeoffs**: Multiple API integrations; inconsistent output formats require normalization layer  
**Status**: ✅ Active — fallback chain implemented

---

## D-009: CI Quality Gate — Zero-New-Violations (Not Zero Total)

**Date**: 2026-06-23  
**Context**: 200+ existing ruff violations made a "zero total" gate impossible without massive cleanup pass  
**Options**: Zero total violations, zero new violations, percentage threshold  
**Decision**: CI gate will check zero NEW violations; existing technical debt tracked separately  
**Rationale**: Pragmatic — prevents regressions without blocking fixes for pre-existing issues  
**Status**: 🟡 Pending — gate not yet implemented in CI

---

## D-010: Intake Data Scope — No Full People Management

**Date**: 2026-06-26  
**Context**: Pipeline Stage Data Scope Review defined data boundaries per stage  
**Decision**: Intake stage captures only trip intent (destination, dates, budget, party size, purpose). Full people management (passenger profiles, identities, documents) lives in Booking stage.  
**Rationale**: Keeps intake fast and focused; prevents premature PII collection; full people management is a later-stage concern  
**Tradeoffs**: Some fields (traveler names, ages) feel natural to capture early but are deferred  
**Status**: ✅ Documented — see `Docs/research/PIPELINE_STAGE_DATA_SCOPE_REVIEW.md`

---

## D-011: Testing Strategy — 5-Layer Pyramid for AI

**Date**: 2026-06-26  
**Context**: Traditional testing pyramid inadequate for probabilistic AI outputs  
**Options**: Standard unit/integration/e2e pyramid, AI-specific pyramid, hybrid  
**Decision**: 5-layer pyramid: Unit → Contract → Probabilistic Evals → LLM-as-Judge → E2E Pipeline  
**Rationale**: Separates deterministic code from probabilistic AI behavior; LLM-as-Judge layer catches semantic regressions that unit tests miss  
**Status**: ✅ Documented — see `Docs/research/TESTING_QA_STRATEGY.md`

---

## D-012: Directory Naming Convention — Language-Conforming

**Date**: 2026-05 (updated 2026-06)  
**Context**: `spine-api/` (hyphen) vs `spine_api` (underscore) required a symlink because Python imports need underscores  
**Decision**: Directory names must match language convention: underscores for Python, hyphens/camelCase for JS/TS. No symlinks.  
**Rationale**: Prevents import confusion; pre-launch product has no backward compat concerns  
**Status**: ✅ Completed — symlink removed, directory renamed, all references updated

---
