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

/**
 * Maps workspace stage → nearest workbench tab equivalent.
 * Used by the compat-redirect layer during Wave 1L.
 * 'output' maps to 'strategy' (traveller-safe bundle lives there pre-Wave 3).
 */
export const WORKSPACE_TO_WORKBENCH_TAB: Record<WorkspaceStage, WorkbenchTab> = {
  intake: 'intake',
  packet: 'packet',
  decision: 'decision',
  strategy: 'strategy',
  output: 'strategy',   // closest pre-Wave-3 equivalent
  safety: 'safety',
};

/**
 * Canonical trip URL.
 * Always use this — never write /workspace/${id}/stage inline.
 */
export function getTripRoute(
  tripId: string,
  stage: WorkspaceStage = 'intake',
): string {
  return `/workspace/${tripId}/${stage}`;
}

/**
 * Workbench compat URL for the migration redirect layer.
 * Used internally by workspace stage pages during Wave 1L.
 * Do not call this from UI code — call getTripRoute() instead.
 *
 * @internal Remove when Wave 2+3 workspace pages reach parity.
 */
export function _getWorkbenchCompatRoute(
  tripId: string,
  stage: WorkspaceStage = 'intake',
): string {
  const tab = WORKSPACE_TO_WORKBENCH_TAB[stage];
  return `/workbench?trip=${tripId}&tab=${tab}`;
}
