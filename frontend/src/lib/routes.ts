/**
 * Centralized trip route generation.
 *
 * All code that navigates to a trip—inbox cards, overview rows,
 * owner reviews, etc.—must use these helpers instead of inline strings.
 * This prevents route drift as the workspace surface matures (Wave 2+).
 *
 * Migration notes
 * ---------------
 * Phase 1L (current): getTripRoute() returns the canonical workspace URL.
 *   Workspace stage pages temporarily redirect to the workbench compat layer.
 *   This preserves functionality while the URL surface is finalized.
 *
 * Phase 2+ (after workspace layout + panels land):
 *   Remove the redirects in /workspace/[tripId]/<stage>/page.tsx.
 *   getTripRoute() continues to work unchanged.
 */

/** Workspace stage identifiers (matches /workspace/[tripId]/ folder names). */
export type WorkspaceStage =
  | 'intake'
  | 'packet'
  | 'decision'
  | 'strategy'
  | 'output'
  | 'safety';

/** Workbench tab identifiers (matches tab search-param values in /workbench). */
export type WorkbenchTab = 'intake' | 'packet' | 'decision' | 'strategy' | 'safety';

export function getTripRoute(
  tripId: string,
  stage: WorkspaceStage = 'intake',
): string {
  return `/workspace/${tripId}/${stage}`;
}
