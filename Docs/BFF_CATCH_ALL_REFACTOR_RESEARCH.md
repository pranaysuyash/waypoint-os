# Next.js BFF Catch-All Proxy Architecture Review

**Date:** 2026-04-25
**Scope:** `frontend/src/app/api/*` route refactoring
**Goal:** Define the architecturally correct pattern for coexistence of shared catch-all proxy and explicit BFF transform routes.

---

## 1. Executive Summary

The refactor broke the app because it introduced a **catch-all proxy at `/api/spine/[...path]`** but the frontend callers still invoke **`/api/trips`, `/api/inbox`, `/api/settings`, etc.** These are entirely separate URL namespaces. Next.js App Router matches filesystem routes exactly — a request to `/api/trips` will never reach `/api/spine/[...path]`.

**The architecturally correct fix is:** Move the catch-all to `/api/[...path]/route.ts`, extract a shared proxy utility (`proxy-core.ts`) that both the catch-all and explicit routes import, keep explicit routes only where BFF logic (transform, cache, fallback) is required, and delete redundant pure-passthrough routes. The frontend callers should **not** be changed.

This is the **"Explicit Override + Shared Proxy Core"** pattern. It is a standard BFF architecture supported natively by Next.js App Router filesystem routing semantics.

---

## 2. Root Cause Analysis

### 2.1 What the Refactor Did Wrong

| Decision | Why It Broke |
|----------|-------------|
| Catch-all placed at `/api/spine/[...path]` | Frontend calls `/api/trips`, not `/api/spine/trips`. The catch-all lives in a completely separate URL namespace. |
| Passthrough routes deleted | Every call hitting `/api/*` (except explicit surviving routes) now returns 404 because nothing handles that path. |
| Frontend callers not updated | Even if the intent was to change the API contract, 60+ client-side references (`api-client.ts`, `governance-api.ts`, hooks, pages) still point to `/api/*`. |
| No shared proxy utility | Surviving explicit routes duplicate the same fetch logic, auth header forwarding, error handling, and response building. |

### 2.2 Next.js App Router Routing Semantics (Critical)

Next.js App Router uses **filesystem-based deterministic matching**:

1. **Static routes** win over dynamic segments.
2. **Dynamic segments** (`[id]`) win over catch-all segments (`[...path]`).
3. **Catch-all segments** match everything below their path that isn't matched more specifically.

This means:

| Route File | URL | Matches? | Wins over catch-all? |
|-----------|-----|----------|---------------------|
| `app/api/trips/route.ts` | `GET /api/trips` | ✅ Yes | ✅ Yes — explicit `
| `app/api/trips/[id]/route.ts` | `GET /api/trips/123` | ✅ Yes | ✅ Yes — more specific |
| `app/api/trips/[id]/review/action/route.ts` | `POST /api/trips/123/review/action` | ✅ Yes | ✅ Yes — deepest specific |
| `app/api/[...path]/route.ts` | `GET /api/health` | ✅ Yes | ❌ No — only if no explicit route |
| `app/api/[...path]/route.ts` | `GET /api/settings/pipeline` | ✅ Yes | ❌ No — only if no explicit route |

**Key insight:** If you place a catch-all at `app/api/[...path]/route.ts`, it becomes the **default handler for every `/api/*` call** that doesn't have an explicit route file. Explicit routes automatically override it. This is exactly the behavior you want for "passthrough by default, override where needed."

---

## 3. Recommended Architecture Pattern

### 3.1 Pattern Name: Explicit Override + Shared Proxy Core

```
src/app/api/
├── [...path]/route.ts          ← Catch-all proxy (default passthrough)
├── trips/route.ts              ← Explicit: BFF transform (list + filter)
├── trips/[id]/route.ts         ← Explicit: BFF transform (single trip + PATCH mapping)
├── inbox/route.ts              ← Explicit: BFF transform (inbox format + SLA logic)
├── stats/route.ts              ← Explicit: BFF transform (dashboard shape normalization)
├── reviews/route.ts            ← Explicit: BFF transform (status mapping + filtering)
├── spine/run/route.ts          ← Explicit: special handling (if needed)
├── health/route.ts             ← Explicit: local response (no backend call)
├── version/route.ts            ← Explicit: local response (no backend call)
└── auth/*                      ← Explicit: auth flows (cookie handling)
```

**Deleted:** All pure passthrough routes like `settings/route.ts`, `settings/pipeline/route.ts`, `insights/summary/route.ts`, `team/members/route.ts`, etc. — the catch-all handles these.

### 3.2 Shared Proxy Core (`lib/proxy-core.ts`)

Both the catch-all and explicit routes import from a single shared utility. This eliminates duplication and guarantees uniform behavior.

**Responsibilities of the core:**
- Build backend URL (with path mapping)
- Forward auth headers/cookies
- Forward request body
- Handle non-OK responses consistently
- Forward Set-Cookie headers from backend
- Apply configurable response transforms
- Provide error fallback / retry logic
- Set cache-control headers

### 3.3 Route Mapping Registry (`lib/route-map.ts`)

A declarative config that maps frontend URL paths to backend URL paths. Used by the catch-all. Explicit routes know their own backend path and don't need this.

```typescript
export const BACKEND_ROUTE_MAP: Record<string, string> = {
  'settings': 'api/settings',
  'settings/pipeline': 'api/settings/pipeline',
  'settings/approvals': 'api/settings/approvals',
  'settings/autonomy': 'api/settings/autonomy',
  'settings/operational': 'api/settings/operational',
  'reviews': 'analytics/reviews',
  'reviews/bulk-action': 'analytics/reviews/bulk-action',
  'pipeline': 'analytics/pipeline',
  'insights/summary': 'analytics/summary',
  'insights/pipeline': 'analytics/pipeline',
  'insights/team': 'analytics/team',
  'insights/revenue': 'analytics/revenue',
  'insights/escalations': 'analytics/escalations',
  'insights/funnel': 'analytics/funnel',
  'insights/bottlenecks': 'analytics/bottlenecks',
  'insights/export': 'analytics/export',
  'insights/alerts': 'analytics/alerts',
  'insights/alerts/{id}/dismiss': 'analytics/alerts/{id}/dismiss',
  'team/members': 'api/team/members',
  'team/members/{id}': 'api/team/members/{id}',
  'team/invite': 'api/team/invite',
  'team/workload': 'api/team/workload',
  'inbox/assign': 'inbox/assign',
  'inbox/reassign': 'trips/reassign',
  'inbox/bulk': 'inbox/bulk',
  'inbox/stats': 'inbox/stats',
  'audit': 'audit',
  'audit/trip/{tripId}': 'audit/trip/{tripId}',
  'overrides/{id}': 'overrides/{id}',
  'scenarios': 'api/scenarios',
  'scenarios/alpha': 'api/scenarios/alpha',
  'assignments': 'assignments',
  'items': 'items',
  'runs': 'runs',
  'health': 'health',
};
```

**Note:** Dynamic segments in the map use `{id}` or `{tripId}` placeholders. The catch-all resolves path segments numerically and substitutes them.

---

## 4. Decision Framework: Explicit Route vs Catch-All

Use this table for every route in `app/api/`:

| Criterion | Explicit Route | Catch-All |
|-----------|---------------|-----------|
| **Data transformation / schema mapping** | ✅ Yes — BFF owns the contract | ❌ No — raw backend response |
| **Business logic / filtering** | ✅ Yes — e.g., server-side `view=workspace` filter | ❌ No |
| **Status/value remapping** | ✅ Yes — e.g., `statusMap`, `stageMap`, `calculateAge` | ❌ No |
| **Backend path ≠ frontend path** | Either (explicit knows its own path; catch-all uses map) | ✅ Yes (via registry) |
| **Custom caching strategy** | ✅ Yes — explicit `Cache-Control` | ⚠️ Default only |
| **Error fallback / stale-while-revalidate** | ✅ Yes — custom fallback shapes | ⚠️ Generic 502/500 |
| **Request body rewriting** | ✅ Yes — e.g., `state` → `status` inverse map | ❌ No |
| **Pure passthrough** | ❌ No — redundant, maintenance burden | ✅ Yes — perfect fit |
| **No auth transform needed** | ❌ No — use catch-all | ✅ Yes |
| **Local-only response (no backend call)** | ✅ Yes — e.g., `/api/version`, `/api/health` | ❌ N/A |

**Rule of thumb:**
- If the route contains a `transform*` function, `map*`, custom filtering, or field remapping → **Keep as explicit route**.
- If the route only fetches from backend and returns the raw JSON → **Delete it; catch-all handles it**.
- If the route doesn't call the backend at all → **Keep as explicit local route**.

### 4.1 Application to Current Codebase

| Route | Action | Rationale |
|-------|--------|-----------|
| `/api/trips` | **Keep explicit** | `transformTrip`, `statusMap`, `calculateAge`, `view=workspace` filter |
| `/api/trips/[id]` | **Keep explicit** | `transformTrip`, `PATCH` body rewriting (`state` → `status`), 404 handling |
| `/api/inbox` | **Keep explicit** | `transformTripToInboxFormat`, SLA calculation, priority scoring, flags |
| `/api/stats` | **Keep explicit** | Shape normalization (`pipeline` + `summary` wrapper) |
| `/api/reviews` | **Keep explicit** | `transformReviewToFrontendFormat`, `STATUS_MAP`, status filter |
| `/api/health` | **Keep explicit** | Local response (or proxy to `/health` — does no transform) |
| `/api/version` | **Keep explicit** | Local response, no backend call |
| `/api/auth/*` | **Keep explicit** | Cookie handling is auth-specific |
| `/api/settings/*` | **Delete → catch-all** | Pure passthrough, no transform |
| `/api/insights/*` | **Delete → catch-all** | Pure passthrough (except if transform is added later) |
| `/api/team/*` | **Delete → catch-all** | Pure passthrough |
| `/api/pipeline` | **Delete → catch-all** | Pure passthrough |
| `/api/audit/*` | **Delete → catch-all** | Pure passthrough |
| `/api/scenarios/*` | **Delete → catch-all** | Pure passthrough |
| `/api/runs/*` | **Delete → catch-all** | Pure passthrough |
| `/api/overrides/*` | **Delete → catch-all** | Pure passthrough |
| `/api/assignments` | **Delete → catch-all** | Pure passthrough |
| `/api/items` | **Delete → catch-all** | Pure passthrough |
| `/api/trips/[id]/review/action` | **Delete → catch-all** | Pure passthrough (forwards to `/trips/{id}/review/action`) |
| `/api/trips/[id]/unassign` | **Delete → catch-all** | Pure passthrough |
| `/api/trips/[id]/suitability/acknowledge` | **Delete → catch-all** | Pure passthrough |
| `/api/trips/[id]/overrides` | **Delete → catch-all** | Pure passthrough |
| `/api/inbox/assign` | **Delete → catch-all** | Pure passthrough |
| `/api/inbox/reassign` | **Delete → catch-all** | Pure passthrough |
| `/api/inbox/bulk` | **Delete → catch-all** | Pure passthrough |
| `/api/inbox/stats` | **Delete → catch-all** | Pure passthrough |
| `/api/inbox/[tripId]/snooze` | **Delete → catch-all** | Pure passthrough |

---

## 5. Implementation Reference

### 5.1 Shared Proxy Core (`lib/proxy-core.ts`)

```typescript
/**
 * proxy-core.ts
 * Shared proxy utility for all BFF routes.
 * Used by both the catch-all fallback and explicit BFF routes.
 */
import { NextRequest, NextResponse } from "next/server";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export interface ProxyOptions {
  /** Target path on the backend (without leading slash) */
  backendPath: string;
  /** Override method (defaults to incoming request method) */
  method?: string;
  /** Query params to strip before forwarding */
  stripParams?: string[];
  /** Custom headers to forward in addition to defaults */
  extraHeaders?: Record<string, string>;
  /** Transform backend response before returning */
  transformResponse?: (data: unknown, req: NextRequest) => unknown;
  /** Custom error fallback response */
  errorFallback?: (error: unknown, req: NextRequest) => NextResponse;
  /** Cache-Control header value */
  cacheControl?: string;
}

function forwardAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  const cookie = req.headers.get("cookie");
  if (cookie) headers["cookie"] = cookie;
  return headers;
}

function buildBackendUrl(
  req: NextRequest,
  backendPath: string,
  stripParams?: string[]
): string {
  const url = new URL(req.url);
  const forwardParams = new URLSearchParams(url.searchParams.toString());
  if (stripParams) {
    for (const p of stripParams) forwardParams.delete(p);
  }
  const query = forwardParams.toString();
  return `${SPINE_API_URL}/${backendPath}${query ? `?${query}` : ""}`;
}

async function buildFetchOptions(
  req: NextRequest,
  opts: ProxyOptions
): Promise<RequestInit> {
  const headers = new Headers(forwardAuthHeaders(req));
  if (opts.extraHeaders) {
    for (const [k, v] of Object.entries(opts.extraHeaders)) {
      headers.set(k, v);
    }
  }

  const fetchOptions: RequestInit = {
    method: opts.method || req.method,
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      const body = await req.text();
      if (body) fetchOptions.body = body;
    } catch {
      // no body
    }
  }

  return fetchOptions;
}

function buildResponseHeaders(
  backendResponse: Response,
  cacheControl?: string
): Headers {
  const headers = new Headers();
  const ct = backendResponse.headers.get("content-type");
  if (ct) headers.set("content-type", ct);
  for (const cookie of backendResponse.headers.getSetCookie()) {
    headers.append("set-cookie", cookie);
  }
    if (cacheControl) headers.set("Cache-Control", cacheControl);
  return headers;
}

export async function proxyRequest(
  req: NextRequest,
  opts: ProxyOptions
): Promise<NextResponse> {
  try {
    const targetUrl = buildBackendUrl(req, opts.backendPath, opts.stripParams);
    const fetchOptions = await buildFetchOptions(req, opts);

    const backendResponse = await fetch(targetUrl, fetchOptions);

    const responseHeaders = buildResponseHeaders(backendResponse, opts.cacheControl);

    // If transformResponse is provided, parse JSON and transform
    if (opts.transformResponse) {
      const data = await backendResponse.json().catch(() => null);
      const transformed = opts.transformResponse(data, req);
      return NextResponse.json(transformed, {
        status: backendResponse.status,
        headers: responseHeaders,
      });
    }

    // Otherwise stream the raw body through
    const body = await backendResponse.text();
    return new NextResponse(body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    if (opts.errorFallback) {
      return opts.errorFallback(error, req);
    }
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error(`Proxy error [${opts.backendPath}]:`, error);
    return NextResponse.json(
      { ok: false, error: `Proxy error: ${message}` },
      { status: 502 }
    );
  }
}
```

### 5.2 Catch-All Route (`app/api/[...path]/route.ts`)

```typescript
/**
 * Catch-all proxy: /api/[...path] → FastAPI spine_api
 *
 * This is the DEFAULT handler for all /api/* calls not matched by explicit routes.
 * Next.js guarantees that explicit routes win over this catch-all.
 */
import { NextRequest, NextResponse } from "next/server";
import { proxyRequest } from "@/lib/proxy-core";
import { BACKEND_ROUTE_MAP } from "@/lib/route-map";

function resolveBackendPath(segments: string[]): string {
  // Try exact match first
  const exactKey = segments.join("/");
  if (BACKEND_ROUTE_MAP[exactKey]) {
    return BACKEND_ROUTE_MAP[exactKey];
  }

  // Try pattern match with dynamic segments (simplified: replace last numeric segment with {id})
  if (segments.length >= 2) {
    const last = segments[segments.length - 1];
    if (/^[0-9a-fA-F-]+$/.test(last)) {
      const patternKey = [...segments.slice(0, -1), "{id}"].join("/");
      if (BACKEND_ROUTE_MAP[patternKey]) {
        const mapped = BACKEND_ROUTE_MAP[patternKey];
        return mapped.replace("{id}", last);
      }
    }
  }

  // Fallback: passthrough with same path
  return segments.join("/");
}

function handler(method: string) {
  return async (
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
  ) => {
    const { path } = await params;
    const backendPath = resolveBackendPath(path);
    return proxyRequest(request, { backendPath, method });
  };
}

export const GET = handler("GET");
export const POST = handler("POST");
export const PUT = handler("PUT");
export const PATCH = handler("PATCH");
export const DELETE = handler("DELETE");
```

### 5.3 Explicit BFF Route Example (`app/api/trips/route.ts`)

```typescript
/**
 * Explicit BFF route: /api/trips
 *
 * This overrides the catch-all because Next.js matches
 * app/api/trips/route.ts before app/api/[...path]/route.ts
 */
import { NextRequest, NextResponse } from "next/server";
import { proxyRequest } from "@/lib/proxy-core";

const statusMap: Record<string, "green" | "amber" | "red" | "blue"> = {
  new: "blue",
  assigned: "amber",
  in_progress: "amber",
  completed: "green",
  cancelled: "red",
};

function transformTrip(spineTrip: any): any {
  // ... existing transform logic ...
  return {
    id: spineTrip.id,
    state: statusMap[spineTrip.status] || spineTrip.status || "blue",
    // ... etc
  };
}

export async function GET(request: NextRequest) {
  const view = request.nextUrl.searchParams.get("view");

  // Use shared proxy core for the upstream fetch
  const backendResponse = await proxyRequest(request, {
    backendPath: "trips",
    stripParams: ["view"],
    // We handle transform manually below, so no transformResponse here
  });

  // Manually transform because we need to inspect the response before returning
  // (proxyRequest returns a NextResponse; for manual transform we need the raw data)
  // ALTERNATIVE: refactor proxyRequest to optionally return raw data
}
```

**Important:** The explicit route pattern above shows a tension. The shared `proxyRequest` returns a `NextResponse`, but explicit routes need to parse the JSON, transform it, then build their own response. There are two valid approaches:

**Approach A: proxyRequest returns raw data (recommended for explicit routes)**

Add a `raw` option to `proxyRequest` that returns `{ status, headers, data }` instead of `NextResponse`, letting the caller build the response.

**Approach B: explicit routes do their own fetch (current codebase pattern)**

Keep explicit routes using `fetch()` directly (as they do now) but extract auth headers and error handling into `proxy-core.ts` helpers. This is less DRY but simpler and matches the current codebase style.

**Recommendation:** Use **Approach A** with a dual-mode `proxyRequest`:

```typescript
export async function proxyRequest(req: NextRequest, opts: ProxyOptions & { raw: true }): Promise<{ status: number; headers: Headers; data: unknown }>;
export async function proxyRequest(req: NextRequest, opts: ProxyOptions): Promise<NextResponse>;
```

This lets explicit routes do:

```typescript
const { data } = await proxyRequest(request, { backendPath: "trips", raw: true });
const transformed = data.items.map(transformTrip);
return NextResponse.json({ items: transformed, total: transformed.length });
```

---

## 6. Answers to Your Specific Questions

### Q1: Should there be a shared proxy utility that explicit routes call into?

**YES.** This is the primary fix. A `lib/proxy-core.ts` eliminates:
- Duplicated `SPINE_API_URL` env reading
- Duplicated auth header forwarding
- Duplicated error handling / 502 response building
- Duplicated Set-Cookie forwarding
- Inconsistent cache-control behavior

### Q2: Should the frontend callers be updated to call `/api/spine/*` directly?

**NO.** Never. The BFF layer IS the API contract. Frontend code should remain agnostic of backend path structure. Changing frontend callers:
- Breaks the abstraction
- Creates tight coupling between frontend and backend URL structure
- Requires 60+ client code changes
- Makes future backend migrations harder

The catch-all should live at `/api/[...path]`, not `/api/spine/[...path]`.

### Q3: Should there be explicit route files that use the catch-all internally?

**NO.** In Next.js App Router, you cannot "delegate" from one route handler to another route handler. Route handlers are endpoint functions that return `Response`. The catch-all is just another route file.

Explicit routes should import a shared utility function (`proxyRequest`) — the same function the catch-all uses. The catch-all is one consumer of the utility; explicit routes are another.

### Q4: Is there a Next.js/Express pattern for route composition where explicit routes handle what they need to, then delegate to a proxy for upstream?

**Not in Next.js App Router.** Express has `next()` and middleware chains. Next.js App Router does NOT support middleware on API routes. The composition pattern here is **module-level function sharing**, not request-level middleware delegation.

The equivalent pattern in Next.js is:
```
Shared utility module (lib/proxy-core.ts)
    ↑                    ↑
Catch-all route    Explicit route
(app/api/[...path])  (app/api/trips)
```

Both call `proxyRequest()`. The catch-all passes the path it received; the explicit route passes the path it knows.

---

## 7. Path Mapping Strategy

### 7.1 Where Path Mapping Lives

Route mapping (frontend → backend) should be **data-driven, not hardcoded in each route file**.

| Approach | Location | Pros | Cons |
|----------|----------|------|------|
| Registry object | `lib/route-map.ts` | Centralized, easy to audit, testable | Needs to be kept in sync with backend |
| Per-route constant | Each `route.ts` file | Self-documenting | Scattered, duplicates known backend paths |
| Backend introspection | Call `/openapi.json` at build time | Always accurate | Complex, requires build-step fetching |

**Recommendation:** Use a **registry object** (`lib/route-map.ts`) consumed by the catch-all. Explicit routes hardcode their own backend path (which they already do). Audit the registry against backend OpenAPI spec periodically.

### 7.2 How Explicit Routes Handle Divergent Paths

Explicit routes already know their backend path. They don't need the registry. Examples from the codebase:

- `/api/stats` → `/api/dashboard/stats` (hardcoded in `stats/route.ts`)
- `/api/pipeline` → `/analytics/pipeline` (hardcoded in `pipeline/route.ts`)
- `/api/reviews` → `/analytics/reviews` (hardcoded in `reviews/route.ts`)
- `/api/insights/summary` → `/analytics/summary` (hardcoded in `insights/summary/route.ts`)

These explicit routes stay as they are (or are simplified by importing proxy helpers). The catch-all handles everything else via the registry.

---

## 8. Migration Steps (Ordered)

1. **Create `lib/proxy-core.ts`** — Extract shared proxy logic from the current `app/api/spine/[...path]/route.ts`.
2. **Create `lib/route-map.ts`** — Add all frontend→backend mappings for pure passthrough routes.
3. **Create `app/api/[...path]/route.ts`** — New catch-all that uses `proxy-core.ts` + `route-map.ts`.
4. **Delete `app/api/spine/[...path]/route.ts`** — The old catch-all is obsolete.
5. **Audit each explicit route** — Replace inline `fetch()` with `proxyRequest(raw: true)` where it reduces boilerplate. Keep transform logic.
6. **Delete pure passthrough routes** — Any route that just proxies and returns raw data is now handled by the catch-all.
7. **Run full test suite** — Verify all `/api/*` calls still work.
8. **Update `AGENTS.md`** — Document the new pattern: "Explicit routes win. Catch-all is default. Always add transform logic to explicit routes. Never duplicate proxy boilerplate."

---

## 9. Verification Checklist

After implementation, verify:

- [ ] `GET /api/trips` still returns transformed trip list (explicit route wins)
- [ ] `GET /api/settings` works (catch-all + route map)
- [ ] `GET /api/settings/pipeline` works (catch-all + route map)
- [ ] `GET /api/insights/summary` works (catch-all + route map)
- [ ] `GET /api/health` works (explicit local route)
- [ ] `GET /api/version` works (explicit local route)
- [ ] `POST /api/auth/login` works (explicit auth route)
- [ ] `GET /api/trips/123` returns transformed single trip (explicit route wins)
- [ ] A request to an unmapped route (e.g., `/api/new-endpoint`) still proxies through (catch-all fallback)
- [ ] Set-Cookie headers from backend are forwarded through both explicit and catch-all paths
- [ ] No 404s for any previously-working `/api/*` endpoint

---

## 10. Why This Is the Architecturally Correct Answer

| Principle | How This Pattern Delivers |
|-----------|---------------------------|
| **Don't Repeat Yourself** | Shared `proxy-core.ts` eliminates ~20 identical fetch/error-handling blocks |
| **Single Source of Truth** | Route mapping lives in one registry; BFF transforms live in explicit files |
| **Open/Closed** | New backend endpoints automatically work via catch-all; BFF transforms are added explicitly without modifying catch-all |
| **Stable Contracts** | Frontend URL structure (`/api/*`) never changes; backend can migrate freely |
| **Next.js Native** | Uses filesystem routing semantics exactly as designed — no hacks, no rewrites |
| **Operational Safety** | Explicit routes are visible in the filesystem; catch-all behavior is data-driven and auditable |

---

*End of document.*
