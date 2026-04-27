/**
 * Route Mapping Registry
 * 
 * Maps frontend URL path segments (relative to /api/) to backend URL paths
 * (relative to SPINE_API_URL). Used by the catch-all proxy at /api/[...path].
 * 
 * Explicit routes (e.g., app/api/trips/route.ts) handle their own mapping
 * and do NOT use this registry — they know their own backend path directly.
 * 
 * If a path is NOT in this registry, the catch-all returns 404. Add only
 * backend-backed routes here; frontend-local routes should stay explicit.
 */

export interface BackendRouteConfig {
  backendPath: string;
  timeoutMs?: number;
}

const DEFAULT_ROUTE_TIMEOUT_MS = 10_000;
const LONG_RUNNING_COMMAND_TIMEOUT_MS = 60_000;

const BACKEND_ROUTE_ENTRIES: Array<[string, BackendRouteConfig]> = [
  // ── Settings ───────────────────────────────────────────────
  ["settings", { backendPath: "api/settings" }],
  ["settings/pipeline", { backendPath: "api/settings/pipeline" }],
  ["settings/approvals", { backendPath: "api/settings/approvals" }],
  ["settings/autonomy", { backendPath: "api/settings/autonomy" }],
  ["settings/operational", { backendPath: "api/settings/operational" }],

  // ── Insights / Analytics ─────────────────────────────────────
  ["stats", { backendPath: "api/dashboard/stats" }],
  ["insights/summary", { backendPath: "analytics/summary" }],
  ["insights/pipeline", { backendPath: "analytics/pipeline" }],
  ["insights/team", { backendPath: "analytics/team" }],
  ["insights/revenue", { backendPath: "analytics/revenue" }],
  ["insights/bottlenecks", { backendPath: "analytics/bottlenecks" }],
  ["insights/escalations", { backendPath: "analytics/escalations" }],
  ["insights/funnel", { backendPath: "analytics/funnel" }],
  ["insights/alerts", { backendPath: "analytics/alerts" }],
  ["insights/export", { backendPath: "analytics/export" }],

  // ── Team ─────────────────────────────────────────────────────
  ["team/members", { backendPath: "api/team/members" }],
  ["team/invite", { backendPath: "api/team/invite" }],
  ["team/workload", { backendPath: "api/team/workload" }],

  // ── Inbox ────────────────────────────────────────────────────
  ["inbox/bulk", { backendPath: "inbox/bulk" }],
  ["inbox/stats", { backendPath: "inbox/stats" }],

  // ── Audit ────────────────────────────────────────────────────
  ["audit", { backendPath: "audit" }],

  // ── Scenarios are frontend-local; do not map them through this proxy.

  // ── System ───────────────────────────────────────────────────
  ["system/unified-state", { backendPath: "api/system/unified-state" }],

  // ── Core resources ───────────────────────────────────────────
  [
    "spine/run",
    {
      backendPath: "run",
      timeoutMs: LONG_RUNNING_COMMAND_TIMEOUT_MS,
    },
  ],
  ["assignments", { backendPath: "assignments" }],
  ["items", { backendPath: "items" }],
  ["health", { backendPath: "health", timeoutMs: DEFAULT_ROUTE_TIMEOUT_MS }],

  // ── Review / Override resources ──────────────────────────────
  ["reviews/bulk-action", { backendPath: "analytics/reviews/bulk-action" }],
  ["overrides", { backendPath: "overrides" }],

  // ── Dynamic patterns (last segment is an ID) ─────────────────
  ["trips/{id}/timeline", { backendPath: "api/trips/{id}/timeline" }],
  ["trips/{id}/assign", { backendPath: "trips/{id}/assign" }],
  ["trips/{id}/unassign", { backendPath: "trips/{id}/unassign" }],
  ["trips/{id}/snooze", { backendPath: "trips/{id}/snooze" }],
  ["trips/{id}/reassign", { backendPath: "trips/{id}/reassign" }],
  ["trips/{id}/review/action", { backendPath: "trips/{id}/review/action" }],
  [
    "trips/{id}/suitability/acknowledge",
    { backendPath: "trips/{id}/suitability/acknowledge" },
  ],
  ["trips/{id}/override", { backendPath: "trips/{id}/override" }],
  ["trips/{id}/overrides", { backendPath: "trips/{id}/overrides" }],

  ["runs/{id}", { backendPath: "runs/{id}" }],
  ["runs/{id}/events", { backendPath: "runs/{id}/events" }],
  ["runs/{id}/steps/{step_name}", { backendPath: "runs/{id}/steps/{step_name}" }],

  ["overrides/{id}", { backendPath: "overrides/{id}" }],

  ["reviews/{id}", { backendPath: "analytics/reviews/{id}" }],

  ["insights/alerts/{id}/dismiss", { backendPath: "analytics/alerts/{id}/dismiss" }],

  ["team/members/{id}", { backendPath: "api/team/members/{id}" }],
  ["team/members/{id}/workload", { backendPath: "api/team/members/{id}/workload" }],

  ["audit/trip/{id}", { backendPath: "audit" }],

  ["analytics/agent/{id}/drill-down", { backendPath: "analytics/agent/{id}/drill-down" }],
];

const BACKEND_ROUTE_MAP = new Map(BACKEND_ROUTE_ENTRIES);

/**
 * UUID-lookahead regex: matches v4-like UUIDs and hyphen-separated hex IDs.
 * Must be a 36-char UUID string OR a run of at least 20 hex characters.
 */
const ID_LIKE_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function isIdLike(segment: string): boolean {
  return ID_LIKE_RE.test(segment) || /^[0-9a-fA-F]{20,}$/.test(segment);
}

/**
 * Resolve a frontend path to the backend path.
 * 
 * @param segments - URL path segments relative to /api/ (e.g., ["settings", "pipeline"])
 * @returns The backend path to forward to, or null for deny-by-default 404.
 */
export function resolveBackendPath(segments: string[]): string | null {
  return resolveBackendRoute(segments)?.backendPath ?? null;
}

/**
 * Resolve a frontend path to the backend path and route-specific execution
 * policy. Long-running command routes belong here so timeout behavior stays
 * attached to the route contract instead of scattered across duplicate API
 * route files.
 *
 * @param segments - URL path segments relative to /api/ (e.g., ["settings", "pipeline"])
 * @returns The backend route config to forward to, or null for deny-by-default 404.
 */
export function resolveBackendRoute(segments: string[]): BackendRouteConfig | null {
  const exactKey = segments.join("/");

  // 1. Exact static match
  if (BACKEND_ROUTE_MAP.has(exactKey)) {
    return BACKEND_ROUTE_MAP.get(exactKey)!;
  }

  // 2. Pattern match with {id} or {id}/… replacing the LAST ID-like segment
  // Replace every ID-like segment in segments with {id}
  const patternSegments = segments.map((seg) => (isIdLike(seg) ? "{id}" : seg));
  const patternKey = patternSegments.join("/");
  if (BACKEND_ROUTE_MAP.has(patternKey)) {
    const mapped = BACKEND_ROUTE_MAP.get(patternKey)!;
    // Substitute real IDs back into the mapped pattern
    const ids = segments.filter(isIdLike);
    let result = mapped.backendPath;
    for (const id of ids) {
      result = result.replace("{id}", id);
    }
    return {
      ...mapped,
      backendPath: result,
    };
  }

  // 3. Fallback: unknown → deny-by-default 404 in the catch-all route.
  return null;
}
