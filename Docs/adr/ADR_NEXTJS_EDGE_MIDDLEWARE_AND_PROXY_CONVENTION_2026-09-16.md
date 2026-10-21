# ADR: Next.js Edge Middleware and Proxy Architecture

- **Status**: Accepted
- **Date**: 2026-09-16
- **Context**: A-12 / FND-0028 / FND-0207
- **Deciders**: Travel OS Architecture & Security Engineering

---

## 1. Context and Problem Statement

In early 2026, an experimental refactor adopted the proposed Next.js 16 file convention (`src/proxy.ts`) to replace `src/middleware.ts`. However, the repository runs on Next.js `14.2.20`. 

Under Next.js 14, the edge runtime strictly discovers `middleware.ts` (or `src/middleware.ts`). As a result:
1. `src/proxy.ts` became completely inert in production request flows.
2. Edge-level authentication guards and security headers did not execute at the edge boundary.
3. Dependency skew existed in `devDependencies` (e.g. bundle analyzers and eslint configs targeting 16.x while runtime was pinned to 14.2.20).

## 2. Decision

1. **Restore Canonical `src/middleware.ts`**:
   `frontend/src/middleware.ts` is the single authoritative edge entrypoint:
   ```typescript
   export { default, config } from './proxy';
   ```
2. **Preserve Modular `src/proxy.ts` and `src/lib/proxy-core.ts`**:
   Keep the implementation in `proxy.ts` and `proxy-core.ts` for clean unit-testability in Vitest without requiring edge runtime harnesses.
3. **Runtime Alignment**:
   Maintain Next.js `14.2.x` stability. When upgrading to Next.js 16+ in the future, the single export in `src/middleware.ts` can be cleanly refactored without touching proxy-core routing logic.

## 3. Verification & Evidence

- **Edge Middleware Discovery**: Next.js production build emits `○ (Static)  prerendered as static content`, bundling `Middleware 25.2 kB` from `src/middleware.ts`.
- **Vitest Verification**: `npm --prefix frontend test -- src/__tests__/proxy.test.ts src/lib/__tests__/proxy-core.test.ts` passes 18/18 tests.
- **Static Analysis**: `npm --prefix frontend run typecheck` passes with zero errors.
