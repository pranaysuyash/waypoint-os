/**
 * Centralized trip route generation.
 *
 * All code that navigates to trip-inbox cards, overview rows,
 * owner reviews, etc. must use these helpers instead of inline strings.
 * This prevents route drift as the workspace surface matures.
 *
 * Ops lives in Trip Workspace (/trips/{id}/ops) — not in Workbench.
 * Post-Spine navigation uses getPostRunTripRoute() to route based on
 * validation status and trip stage.
 */

/** Trip stage identifiers (matches /trips/[tripId]/ folder names). */
export type WorkspaceStage =
  | 'intake'
  | 'packet'
  | 'decision'
  | 'strategy'
  | 'output'
  | 'safety'
  | 'suitability'
  | 'timeline'
  | 'ops';

/** Workbench tab identifiers (matches tab search-param values in /workbench). */
export type WorkbenchTab = 'intake' | 'packet' | 'decision' | 'strategy' | 'safety';

const _warnedTripIds = new Set<string>();

export function getTripRoute(
  tripId: string | undefined | null,
  stage: WorkspaceStage = 'intake',
): string {
  if (!tripId) {
    // Deduped warning - only log once per falsy value to prevent console spam
    const key = String(tripId);
    if (!_warnedTripIds.has(key)) {
      _warnedTripIds.add(key);
      console.warn('[routes] getTripRoute called with falsy tripId - falling back to /trips');
    }
    return '/trips';
  }
  return `/trips/${tripId}/${stage}`;
}

/**
 * Determines where "View Trip" should navigate after a Spine run completes.
 *
 * Priority order:
 * 1. BLOCKED/ESCALATED validation → /packet (operator must see reasons first)
 * 2. proposal/booking stage → /ops (durable booking operations home)
 * 3. Fallback → /intake
 */
export function getPostRunTripRoute(params: {
  tripId: string;
  tripStage?: string | null;
  validationStatus?: string | null;
}): string {
  if (params.validationStatus === 'BLOCKED' || params.validationStatus === 'ESCALATED') {
    return getTripRoute(params.tripId, 'packet');
  }
  if (params.tripStage === 'proposal' || params.tripStage === 'booking') {
    return getTripRoute(params.tripId, 'ops');
  }
  return getTripRoute(params.tripId, 'intake');
}
