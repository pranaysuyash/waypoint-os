/**
 * Pure state helpers for the workbench route: URL-parameter contracts
 * (stage / operating mode / tab), draft trip-id extraction, and the
 * pipeline-stage derivation. No React imports — everything here is
 * testable without a renderer.
 *
 * Extracted verbatim from PageClient.tsx (council decision
 * Docs/architecture/WORKBENCH_MODULARIZATION_COUNCIL_DECISION_2026-09-12.md,
 * slice T1.1). Bodies are intentionally byte-identical to their origin.
 */
import type { SpineStage, OperatingMode } from '@/types/spine';
import type { Trip } from '@/lib/api-client';
import type { WorkbenchStore } from '@/stores/workbench';
import type { PipelineStageId } from './PipelineFlow';

// Safely parse structured JSON - returns null on invalid rather than throwing.
export function safeParseJson(raw: string): Record<string, unknown> | null {
  if (!raw.trim()) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export const workspaceTabs = [
  { id: 'intake', label: 'New Inquiry' },
  { id: 'packet', label: 'Trip Details' },
  { id: 'safety', label: 'Risk Review' },
  { id: 'council', label: 'Persona Council' },
  { id: 'frontier', label: 'Frontier OS' },
] as const;

export type WorkspaceTabId = (typeof workspaceTabs)[number]['id'];

const VALID_SPINE_STAGES = [
  'discovery',
  'shortlist',
  'proposal',
  'booking',
] as const satisfies readonly SpineStage[];

const VALID_SPINE_STAGES_SET = new Set<string>(VALID_SPINE_STAGES);
export function toSpineStage(value: string | null): SpineStage | null {
  if (value && VALID_SPINE_STAGES_SET.has(value)) {
    return value as SpineStage;
  }
  return null;
}

const VALID_OPERATING_MODES = [
  'normal_intake',
  'audit',
  'emergency',
  'follow_up',
  'cancellation',
  'post_trip',
  'coordinator_group',
  'owner_review',
] as const satisfies readonly OperatingMode[];

const VALID_OPERATING_MODES_SET = new Set<string>(VALID_OPERATING_MODES);
export function toOperatingMode(value: string | null): OperatingMode | null {
  if (value && VALID_OPERATING_MODES_SET.has(value)) {
    return value as OperatingMode;
  }
  return null;
}

const WORKSPACE_TAB_IDS_SET = new Set<string>(workspaceTabs.map((t) => t.id));
export function toWorkspaceTabId(value: string | null): WorkspaceTabId | null {
  if (value && WORKSPACE_TAB_IDS_SET.has(value)) {
    return value as WorkspaceTabId;
  }
  return null;
}

export function extractCompletedTripIdFromDraft(draft: Record<string, unknown> | null | undefined): string | null {
  if (!draft || typeof draft !== "object") return null;

  const promotedTripId = draft.promoted_trip_id;
  if (typeof promotedTripId === "string" && promotedTripId.trim()) {
    return promotedTripId.trim();
  }

  const runSnapshots = Array.isArray(draft.run_snapshots) ? draft.run_snapshots : [];
  for (let index = runSnapshots.length - 1; index >= 0; index -= 1) {
    const snapshotEntry = runSnapshots[index];
    if (!snapshotEntry || typeof snapshotEntry !== "object") continue;

    const record = snapshotEntry as Record<string, unknown>;
    const snapshot = record.snapshot;
    if (!snapshot || typeof snapshot !== "object") continue;

    const tripId = (snapshot as Record<string, unknown>).trip_id;
    if (typeof tripId === "string" && tripId.trim()) {
      return tripId.trim();
    }
  }

  return null;
}

/**
 * Derives the pipeline stage from actual trip/store state.
 * PipelineFlow shows processing progress (intake → packet → decision → strategy → safety),
 * not which tab the user clicked.
 * Output and Feedback are workspace sections, not core pipeline stages.
 * Frontier OS is surfaced in its own workbench tab when frontier output exists.
 */
export function getPipelineStageForWorkbench(
  trip: Trip | null | undefined,
  store: WorkbenchStore,
): PipelineStageId {
  if (store.result_safety || trip?.safety) return 'safety';
  if (store.result_strategy || trip?.strategy) return 'strategy';
  if (store.result_decision || trip?.decision) return 'decision';
  if (store.result_packet || trip?.packet) return 'packet';
  return 'intake';
}

// IMP-05 (DEMO-06): shared styling for the blocked-banner "Review Missing Fields"
// control, which renders as a Link to the editable repair surface when a trip
// exists and as a tab-switch button when only a draft exists (pre-persistence).
export const REVIEW_MISSING_FIELDS_CONTROL_CLASSES =
  'px-3 py-1.5 bg-[#f85149]/10 border border-[#f85149]/30 text-[#f85149] text-ui-xs font-medium rounded-md hover:bg-[#f85149]/20 transition-colors';
