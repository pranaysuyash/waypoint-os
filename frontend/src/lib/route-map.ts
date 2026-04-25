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

const BACKEND_ROUTE_ENTRIES: Array<[string, string]> = [
  // ── Settings ───────────────────────────────────────────────
  ["settings", "api/settings"],
  ["settings/pipeline", "api/settings/pipeline"],
  ["settings/approvals", "api/settings/approvals"],
  ["settings/autonomy", "api/settings/autonomy"],
  ["settings/operational", "api/settings/operational"],

  // ── Insights / Analytics ─────────────────────────────────────
  ["stats", "api/dashboard/stats"],
  ["insights/summary", "analytics/summary"],
  ["insights/pipeline", "analytics/pipeline"],
  ["insights/team", "analytics/team"],
  ["insights/revenue", "analytics/revenue"],
  ["insights/bottlenecks", "analytics/bottlenecks"],
  ["insights/escalations", "analytics/escalations"],
  ["insights/funnel", "analytics/funnel"],
  ["insights/alerts", "analytics/alerts"],
  ["insights/export", "analytics/export"],

  // ── Team ─────────────────────────────────────────────────────
  ["team/members", "api/team/members"],
  ["team/invite", "api/team/invite"],
  ["team/workload", "api/team/workload"],

  // ── Inbox ────────────────────────────────────────────────────
  ["inbox/bulk", "inbox/bulk"],
  ["inbox/stats", "inbox/stats"],

  // ── Audit ────────────────────────────────────────────────────
  ["audit", "audit"],

  // ── Scenarios are frontend-local; do not map them through this proxy.

  // ── System ───────────────────────────────────────────────────
  ["system/unified-state", "api/system/unified-state"],

  // ── Core resources ───────────────────────────────────────────
  ["spine/run", "run"],
  ["assignments", "assignments"],
  ["items", "items"],
  ["health", "health"],

  // ── Review / Override resources ──────────────────────────────
  ["reviews/bulk-action", "analytics/reviews/bulk-action"],
  ["overrides", "overrides"],

  // ── Dynamic patterns (last segment is an ID) ─────────────────
  ["trips/{id}/timeline", "api/trips/{id}/timeline"],
  ["trips/{id}/assign", "trips/{id}/assign"],
  ["trips/{id}/unassign", "trips/{id}/unassign"],
  ["trips/{id}/snooze", "trips/{id}/snooze"],
  ["trips/{id}/reassign", "trips/{id}/reassign"],
  ["trips/{id}/review/action", "trips/{id}/review/action"],
  ["trips/{id}/suitability/acknowledge", "trips/{id}/suitability/acknowledge"],
  ["trips/{id}/override", "trips/{id}/override"],
  ["trips/{id}/overrides", "trips/{id}/overrides"],

  ["runs/{id}", "runs/{id}"],
  ["runs/{id}/events", "runs/{id}/events"],
  ["runs/{id}/steps/{step_name}", "runs/{id}/steps/{step_name}"],

  ["overrides/{id}", "overrides/{id}"],

  ["reviews/{id}", "analytics/reviews/{id}"],

  ["insights/alerts/{id}/dismiss", "analytics/alerts/{id}/dismiss"],

  ["team/members/{id}", "api/team/members/{id}"],
  ["team/members/{id}/workload", "api/team/members/{id}/workload"],

  ["audit/trip/{id}", "audit"],

  ["analytics/agent/{id}/drill-down", "analytics/agent/{id}/drill-down"],
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
    let result = mapped;
    for (const id of ids) {
      result = result.replace("{id}", id);
    }
    return result;
  }

  // 3. Fallback: unknown → deny-by-default 404 in the catch-all route.
  return null;
}
