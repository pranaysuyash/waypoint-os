# Architectural Update: Middleware to Proxy Migration

**Date:** 2026-04-24  
**Context:** Next.js 16.2.4

## What Changed
The file `frontend/src/middleware.ts` was deleted and its logic migrated to `frontend/src/proxy.ts`.

## Why It Changed
1.  **Framework Requirements:** Next.js 16 introduced `proxy.ts` as the new Network Boundary standard. Keeping both files caused a startup conflict where the dev server refused to render pages, resulting in infinite loading loops or empty responses.
2.  **Route Whitelisting:** The new landing page (`/v2`) and the Itinerary Checker (`/itinerary-checker`) needed to be added to the `PUBLIC_PAGES` whitelist to allow unauthenticated access.

## Functional Preservation
The following original behaviors from `middleware.ts` were ported verbatim to `proxy.ts`:
- **Auth Guard:** Still checks for the `access_token` httpOnly cookie.
- **Redirects:** Preserves the `?next=[path]` query parameter pattern for unauthenticated redirects to `/login`.
- **Whitelists:** Preserves all `/api/`, `/_next/`, and `/static/` pass-through rules.

## Comparison & Verification
- **Original:** `middleware(req)` in `middleware.ts`
- **New:** `proxy(req)` in `proxy.ts`
- **Port:** 3000 (Default restored)
- **Status:** Unified, cache cleared, server ready for clean restart.
