# ADR: Frontend SSE Subscription & Real-Time Pipeline State Integration

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Real-time progress updates for Spine pipeline execution in Workbench UI

---

## Context

During Spine pipeline execution, the frontend Workbench previously relied exclusively on client-side interval polling (`useSpineRun`) hitting `GET /api/runs/{run_id}` every 2 seconds.

While functional, fixed interval polling introduces latency jitter for fast pipeline stages and unnecessary network overhead during multi-step execution.

---

## Decision

Implemented `useSSEStream` hook and Next.js BFF proxy route (`/api/stream-events/[runId]`):

### 1. `useSSEStream` Hook (`frontend/src/hooks/useSSEStream.ts`)
- Provides a clean, event-driven API wrapping state stream subscriptions.
- Features adaptive polling fallback (500ms fast start for 4 rounds -> 2s steady) when SSE is disabled or unsupported.
- Listens to typed event types: `state_update`, `stage_entered`, `terminal`, `error`, `heartbeat`.
- Connects automatically when `spineRunId` is initiated in `PageClient.tsx`.

### 2. Next.js BFF Proxy Route (`frontend/src/app/api/stream-events/[runId]/route.ts`)
- Native browser `EventSource` API cannot attach custom request headers (like `Authorization: Bearer <token>`).
- The Next.js BFF proxy reads the JWT from an httpOnly cookie (`spine_auth_token`), injects `Authorization: Bearer <token>`, and proxies the upstream SSE stream from `SPINE_API_BASE/runs/{runId}/stream`.
- Gracefully returns `404` when upstream SSE endpoint is not active, signaling `useSSEStream` to degrade seamlessly to adaptive polling.

---

## Consequences

- Zero breaking changes to `useSpineRun`.
- Immediate UI responsiveness when backend stream events are enabled (`NEXT_PUBLIC_SSE_ENABLED=true`).
- Secure auth token injection without exposing JWT to client JS EventSource parameters.
