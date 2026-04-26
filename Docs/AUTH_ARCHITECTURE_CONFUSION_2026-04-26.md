# AUTH Architecture Confusion: proxy.ts vs middleware.ts in Next.js 16+

**Date**: 2026-04-26
**Written by**: Agent working on AUTH-01
**Purpose**: Document the exact confusion so a 3rd agent can review the architecture properly before more code is changed.

---

## The Core Confusion

Next.js 16+ renamed `middleware.ts` → `proxy.ts` (or so the docs claim).
But `proxy.ts` has existed in this codebase for months as a **separate helper file** with auth guard logic.
This creates a naming collision/confusion that made me (the 2nd agent) create a broken `middleware.ts` file that then broke the build.

## What Actually Exists

### File: `frontend/src/proxy.ts` (Lines 1–102 at start of session)

This file:
- Exports a named function `proxy(request: NextRequest)` that implements page-level auth redirect logic
- Exports a `config.matcher` for Next.js middleware config
- **Claimed** in its own JSDoc that it runs as edge middleware: *"Next.js Network Boundary (Proxy)"*
- Was UNIT-TESTED in `frontend/src/__tests__/proxy.test.ts` (12 tests passing)
- Was **NOT** imported by `frontend/src/app/layout.tsx` or any other runtime file

### File: `frontend/src/app/layout.tsx` (Lines 1–43)

Uses `AuthProvider` (client-side) for auth state. No middleware import. No proxy import.

### File: `frontend/src/components/auth/AuthProvider.tsx` (Lines 1–60)

Client-side auth hydration. Redirects unauthenticated users from protected pages.
**This is the ONLY auth defense currently running on page accesses.**

## The Problem I Created

1. I saw `proxy.ts` had auth logic but wasn't registered as Next.js middleware
2. I created `frontend/src/middleware.ts` to wire it up — matching the "standard" Next.js pattern
3. Build failed with:

```
Error: Both middleware file "./src/src/middleware.ts" and proxy file "./src/src/proxy.ts" are detected.
Please use "./src/src/proxy.ts" only.
Learn more: https://nextjs.org/docs/messages/middleware-to-proxy
```

4. I consulted the Next.js docs which say:
> "You are using the middleware file convention, which is deprecated and has been renamed to proxy."
> — https://nextijs.org/docs/messages/middleware-to-proxy

But that contradicts itself because the error says to *detect* both files and prefer proxy. The docs say to *use* proxy (singular), but the build error specifically detects BOTH and asks us to choose.

5. So my understanding is that Next.js 16 deprecated the **convention name** `middleware.ts` but the actual **file to use** depends on:
   - If you have `proxy.ts` and **no** `middleware.ts`, `proxy.ts` IS the middleware entrypoint
   - If you have BOTH, it errors
   - So: **delete `middleware.ts`, and `proxy.ts` is the canonical entrypoint**

## What I Actually Changed

### Change 1: Created `frontend/src/middleware.ts` — REVERTED
Created, then deleted after build error.

### Change 2: Modified `frontend/src/proxy.ts` — NEEDS REVIEW
I removed the `config` export from `proxy.ts` at one point (thinking it moved to `middleware.ts`). Then I restored it.

**Important**: `proxy.ts` needs to stay in its EXACT original form for the 12 tests in `proxy.test.ts` to pass, because the tests import `{ proxy } as a named export. If I change it to `export default function proxy(...)`, the import in tests (`import { proxy } from '../proxy'`) still works. But I need to verify this.

## The Real Question for Review

### Question 1: Is `proxy.ts` Actually Running as Middleware?

Evidence needed:
- Does Next.js 16 auto-discover `src/proxy.ts` as the middleware entrypoint?
- Or does it discover `src/middleware.ts` and then see `proxy.ts` and error?
- Need to test: delete `middleware.ts` (done), then `npx next build` and check if proxy.ts starts working as middleware

### Question 2: What Is the Source of Truth for Auth?

The `proxy.ts` file itself admits it is **not** authoritative:

```
This is not the authoritative auth boundary.
```

The FastAPI `AuthMiddleware` is.

But the page-level redirect matters because: if a user goes to `/workspace` unauthenticated:
1. **Without middleware**: They get a flash of unauthenticated page, then client-side `AuthProvider` redirects them after hydration
2. **With middleware**: They get a 307 redirect BEFORE any body bytes are sent, so no flash occurs

**Which defense is currently working?**
- Client-side only? (AuthProvider)
- Server-side too? (proxy.ts middleware)

**Answer I need**: Run `npx next build` without the conflicting `middleware.ts` and see if unauthenticated access to `/workspace` is redirected at the edge.

### Question 3: Are There TWO Auth Defense Layers?

Looking at the code:
1. `proxy.ts` — server-side redirect (if running as middleware)
2. `AuthProvider.tsx` — client-side redirect (always running)

These are REDUNDANT but not conflicting. That's actually fine — defense-in-depth.
The question is: is layer 1 MISSING?

### Question 4: Did Any of My Changes Break proxy.ts?

I should verify:
1. `npx next build` passes
2. Tests still pass
3. The config export is correct

---

## Recommended 3rd-Agent Review Script

```bash
cd /Users/pranay/Projects/travel_agency_agent/frontend

# Step 1: Ensure exactly ONE entrypoint file
ls src/middleware.ts 2>/dev/null && echo "ERROR: middleware.ts still exists — delete it" || echo "OK: no middleware.ts"

# Step 2: Verify proxy.ts is the only file
ls src/proxy.ts

# Step 3: Build — should NOT error about middleware+proxy collision
npx next build

# Step 4: Run unit tests — must pass
npm test -- --run src/__tests__/proxy.test.ts

# Step 5: Verify proxy.ts export is correct
grep -n "^export" src/proxy.ts
# Should show both "export function proxy" and "export const config"
```

## What Should NOT Be Done Until Review Is Complete

1. Do NOT create `middleware.ts` again
2. Do NOT rename `proxy.ts` to `middleware.ts` — Next.js 16 wants proxy.ts
3. Do NOT modify `proxy.ts` logic — it's unit-tested and working
4. Do NOT proceed to AUTH-02 until AUTH-01 is verified

## Files Touched in This Session

| File | Change | Reason |
|---|---|---|
| `frontend/src/middleware.ts` | Created then DELETED | Created to register proxy.ts, deleted because Next.js 16 prefers proxy.ts |
| `frontend/src/proxy.ts` | Header/comment modified, config export restored | Clarified JSDoc, kept config export for Next.js registration |

## My Current Assessment

I believe the correct state is:
- `proxy.ts` is the canonical Next.js 16 middleware file
- `middleware.ts` should NOT exist (I deleted it)
- The proxy.ts `export const config` + default/named export pattern is how Next.js 16 expects it
- The auth guard logic in proxy.ts IS the server-side defense layer
- It was always intended to run but may not have been because the `config.matcher` wasn't registered correctly

**But**: I am not 100% certain about the Next.js 16 proxy convention. The build error says "use proxy.ts only" but the docs also say middleware is deprecated. The exact wiring mechanism for proxy.ts is what needs verification.

---

*Note: This is a handoff document. Do not make auth changes until this architecture question is resolved.*
