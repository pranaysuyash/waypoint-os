/**
 * Centralized trip route generation.
 *
 * All code that navigates to a trip—inbox cards, overview rows,
 * owner reviews, etc.—must use these helpers instead of inline strings.
 * This prevents route drift as the workspace surface matures (Wave 2+).
 *
 * Migration notes
 * ---------------
 * Phase 1L (current): getTripRoute() returns the canonical trips URL.
 *   Trip stage pages temporarily redirect to the workbench compat layer.
 *   This preserves functionality while the URL surface is finalized.
 *
 * Phase 2+ (after trips layout + panels land):
 *   Remove the redirects in /trips/[tripId]/<stage>/page.tsx.
 *   getTripRoute() continues to work unchanged.
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
  | 'timeline';

/** Workbench tab identifiers (matches tab search-param values in /workbench). */
export type WorkbenchTab = 'intake' | 'packet' | 'decision' | 'strategy' | 'safety';

const _warnedTripIds = new Set<string>();

export function getTripRoute(
  tripId: string | undefined | null,
  stage: WorkspaceStage = 'intake',
): string {
  if (!tripId) {
    // Deduped warning — only log once per falsy value to prevent console spam
    const key = String(tripId);
    if (!_warnedTripIds.has(key)) {
      _warnedTripIds.add(key);
      console.warn('[routes] getTripRoute called with falsy tripId — falling back to /trips');
    }
    return '/trips';
  }
  return `/trips/${tripId}/${stage}`;
}
