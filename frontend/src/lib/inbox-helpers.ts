/**
 * Inbox Helpers
 *
 * Shared utilities for the inbox intelligence layer:
 * - SLA contextual computation
 * - Filter serialization / deserialization
 * - Sort behavior definitions
 * - Search matching
 * - View profile constants
 */

import type { InboxTrip, InboxFilters, TripPriority } from '@/types/governance';

// ============================================================================
// CONSTANTS
// ============================================================================

/** Threshold for showing micro-labels to new users */
export const MICRO_LABEL_THRESHOLD = 3;

/** View profiles for role-based card rendering */
export type ViewProfile = 'operations' | 'teamLead' | 'finance' | 'fulfillment';

export const VIEW_PROFILES: ViewProfile[] = [
  'operations',
  'teamLead',
  'finance',
  'fulfillment',
];

export const VIEW_PROFILE_LABELS: Record<ViewProfile, string> = {
  operations: 'Operations',
  teamLead: 'Team Lead',
  finance: 'Finance',
  fulfillment: 'Fulfillment',
};

/** Canonical sort options */
const SORT_OPTIONS = [
  { key: 'priority', label: 'Priority', defaultDirection: 'desc' as const },
  { key: 'urgency', label: 'Urgency', defaultDirection: 'desc' as const },
  { key: 'importance', label: 'Importance', defaultDirection: 'desc' as const },
  { key: 'sla', label: 'SLA Status', defaultDirection: 'asc' as const },
  { key: 'value', label: 'Value', defaultDirection: 'desc' as const },
  { key: 'destination', label: 'Destination', defaultDirection: 'asc' as const },
  { key: 'party', label: 'Party Size', defaultDirection: 'desc' as const },
  { key: 'dates', label: 'Dates', defaultDirection: 'asc' as const },
] as const;

export type SortKey = (typeof SORT_OPTIONS)[number]['key'];
export type SortDirection = 'asc' | 'desc';

// ============================================================================
// SLA COMPUTATION
// ============================================================================

export interface StageSLAConfig {
  stage: string;
  slaHours: number;
}

/**
 * Compute contextual SLA percentage.
 *
 * Formula: (daysInCurrentStage * 24) / slaHours * 100
 *
 * Example:
 *   - Intake (24h SLA), 6 days = 600%
 *   - Booking (336h SLA), 6 days = ~43%
 *
 * @param daysInCurrentStage - days the trip has been in current stage
 * @param slaHours - expected hours in this stage
 * @returns percentage string (e.g. "600%", "43%")
 */
export function computeSLAPercentage(
  daysInCurrentStage: number,
  slaHours: number,
): string {
  if (!slaHours || slaHours <= 0) return 'N/A';
  const percentage = (daysInCurrentStage * 24) / slaHours * 100;
  return percentage >= 100
    ? `${Math.round(percentage)}%`
    : `${Math.round(percentage)}%`;
}

/**
 * Build a contextual SLA display string.
 *
 * @example "6d · 600% of SLA" or "6d · 43% of SLA"
 */
export function formatContextualSLA(
  daysInCurrentStage: number,
  slaHours: number,
): string {
  const percentage = computeSLAPercentage(daysInCurrentStage, slaHours);
  return `${daysInCurrentStage}d · ${percentage} of SLA`;
}

/**
 * Fallback SLA hours per stage when backend config is unavailable.
 * These are conservative defaults and should be overridden by
 * PipelineStage.slaHours when available.
 */
export const DEFAULT_STAGE_SLA_HOURS: Record<string, number> = {
  intake: 24,
  details: 72,
  options: 72,
  review: 48,
  booking: 336, // 14 days
  completed: 168, // 7 days
};

/**
 * Get SLA hours for a stage, with fallback to defaults.
 */
export function getSLAHoursForStage(
  stage: string,
  stageConfigs?: StageSLAConfig[],
): number {
  if (stageConfigs) {
    const config = stageConfigs.find((c) => c.stage === stage);
    if (config?.slaHours) return config.slaHours;
  }
  return DEFAULT_STAGE_SLA_HOURS[stage] || 168; // 7 days default
}

// ============================================================================
// FILTER SERIALIZATION
// ============================================================================

/**
 * Serialize InboxFilters to URL query params.
 */
export function serializeFilters(filters: InboxFilters): string {
  const params = new URLSearchParams();

  if (filters.priority?.length)
    params.set('priority', filters.priority.join(','));
  if (filters.stage?.length) params.set('stage', filters.stage.join(','));
  if (filters.assignedTo?.length)
    params.set('assignedTo', filters.assignedTo.join(','));
  if (filters.slaStatus?.length)
    params.set('slaStatus', filters.slaStatus.join(','));
  if (filters.minValue !== undefined)
    params.set('minValue', filters.minValue.toString());
  if (filters.maxValue !== undefined)
    params.set('maxValue', filters.maxValue.toString());
  if (filters.dateRange?.from)
    params.set('dateFrom', filters.dateRange.from);
  if (filters.dateRange?.to) params.set('dateTo', filters.dateRange.to);

  return params.toString();
}

/**
 * Deserialize URL query params to InboxFilters.
 */
export function deserializeFilters(queryString: string): InboxFilters {
  const params = new URLSearchParams(queryString);
  const filters: InboxFilters = {};

  const priority = params.get('priority');
  if (priority) filters.priority = priority.split(',') as TripPriority[];

  const stage = params.get('stage');
  if (stage) filters.stage = stage.split(',');

  const assignedTo = params.get('assignedTo');
  if (assignedTo) filters.assignedTo = assignedTo.split(',');

  const slaStatus = params.get('slaStatus');
  if (slaStatus)
    filters.slaStatus = slaStatus.split(',') as (
      | 'on_track'
      | 'at_risk'
      | 'breached'
    )[];

  const minValue = params.get('minValue');
  if (minValue) filters.minValue = parseFloat(minValue);

  const maxValue = params.get('maxValue');
  if (maxValue) filters.maxValue = parseFloat(maxValue);

  const dateFrom = params.get('dateFrom');
  const dateTo = params.get('dateTo');
  if (dateFrom || dateTo) {
    filters.dateRange = {
      from: dateFrom || '',
      to: dateTo || '',
    };
  }

  return filters;
}

// ============================================================================
// SORT HELPERS
// ============================================================================

const priorityOrder: Record<TripPriority, number> = {
  low: 0,
  medium: 1,
  high: 2,
  critical: 3,
};

const slaOrder: Record<string, number> = {
  breached: 0,
  at_risk: 1,
  on_track: 2,
};

/**
 * Compare two trips for sorting.
 */
export function compareTrips(
  a: InboxTrip,
  b: InboxTrip,
  sortBy: SortKey,
  direction: SortDirection,
): number {
  const dir = direction === 'asc' ? 1 : -1;

  switch (sortBy) {
    case 'priority': {
      const pa = priorityOrder[a.priority];
      const pb = priorityOrder[b.priority];
      if (pa !== pb) return (pa - pb) * dir;
      // Secondary: SLA status
      return (slaOrder[a.slaStatus] - slaOrder[b.slaStatus]) * dir;
    }
    case 'destination':
      return a.destination.localeCompare(b.destination) * dir;
    case 'value':
      return (a.value - b.value) * dir;
    case 'party':
      return (a.partySize - b.partySize) * dir;
    case 'dates':
      return a.dateWindow.localeCompare(b.dateWindow) * dir;
    case 'sla': {
      return (slaOrder[a.slaStatus] - slaOrder[b.slaStatus]) * dir;
    }
    default:
      return 0;
  }
}

// ============================================================================
// SEARCH MATCHING
// ============================================================================

/**
 * Check if a trip matches a search query.
 *
 * Expanded to include customerName and assignedToName.
 */
export function tripMatchesQuery(trip: InboxTrip, query: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase().trim();
  if (!q) return true;

  const searchable: string[] = [];
  for (const field of [trip.destination, trip.id, trip.tripType, trip.customerName, trip.assignedToName]) {
    if (field) searchable.push(field.toLowerCase());
  }

  return searchable.some((field) => field.includes(q));
}

// ============================================================================
// VIEW PROFILE PERSISTENCE
// ============================================================================

const VIEW_PROFILE_KEY = 'inbox_view_profile';

/**
 * Get the saved view profile from localStorage.
 * Returns undefined if not set or invalid.
 */
export function getSavedViewProfile(): ViewProfile | undefined {
  if (typeof window === 'undefined') return undefined;
  try {
    const raw = localStorage.getItem(VIEW_PROFILE_KEY);
    if (!raw) return undefined;
    if (VIEW_PROFILES.includes(raw as ViewProfile)) {
      return raw as ViewProfile;
    }
  } catch {
    // localStorage unavailable (private browsing, quota exceeded)
  }
  return undefined;
}

/**
 * Save the view profile to localStorage.
 */
export function saveViewProfile(profile: ViewProfile): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(VIEW_PROFILE_KEY, profile);
  } catch {
    // localStorage unavailable
  }
}

/**
 * Map URL role param to view profile.
 */
export function roleToViewProfile(role: string): ViewProfile {
  switch (role) {
    case 'mgr':
      return 'teamLead';
    case 'finance':
      return 'finance';
    case 'fulfillment':
      return 'fulfillment';
    case 'ops':
    default:
      return 'operations';
  }
}

/**
 * Map view profile to URL role param.
 */
export function viewProfileToRole(profile: ViewProfile): string {
  switch (profile) {
    case 'teamLead':
      return 'mgr';
    case 'finance':
      return 'finance';
    case 'fulfillment':
      return 'fulfillment';
    case 'operations':
    default:
      return 'ops';
  }
}

// ============================================================================
// VIEW PROFILE HELPERS
// ============================================================================

export type MetricField =
  | 'partySize'
  | 'dateWindow'
  | 'value'
  | 'daysInCurrentStage'
  | 'assignedToName'
  | 'slaStatus'
  | 'priority'
  | 'stage';

const METRIC_ROW_CONFIG: Record<ViewProfile, MetricField[]> = {
  operations: ['partySize', 'dateWindow', 'value', 'daysInCurrentStage'],
  teamLead: ['assignedToName', 'slaStatus', 'daysInCurrentStage', 'priority'],
  finance: ['value', 'stage', 'dateWindow', 'priority'],
  fulfillment: ['dateWindow', 'assignedToName', 'stage', 'partySize'],
};

/**
 * Get the ordered metric fields for a view profile.
 */
export function getMetricsForProfile(profile: ViewProfile): MetricField[] {
  return METRIC_ROW_CONFIG[profile];
}

// ============================================================================
// MICRO-LABELS
// ============================================================================

const VISIT_COUNT_KEY = 'inbox_visit_count';

export function getInboxVisitCount(): number {
  if (typeof window === 'undefined') return 0;
  try {
    const raw = localStorage.getItem(VISIT_COUNT_KEY);
    return raw ? parseInt(raw, 10) : 0;
  } catch {
    return 0;
  }
}

export function incrementInboxVisitCount(): void {
  if (typeof window === 'undefined') return;
  try {
    const count = getInboxVisitCount();
    localStorage.setItem(VISIT_COUNT_KEY, (count + 1).toString());
  } catch {
    // localStorage unavailable
  }
}

export function shouldShowMicroLabels(): boolean {
  return getInboxVisitCount() < MICRO_LABEL_THRESHOLD;
}

// ============================================================================
// BADGE LABELS (for progressive disclosure)
// ============================================================================

const MICRO_LABELS: Record<string, string> = {
  // Priority
  critical: 'needs human review',
  high: 'high attention',
  medium: 'standard priority',
  low: 'low priority',
  // Stage
  intake: 'just arrived',
  details: 'gathering info',
  options: 'awaiting selection',
  review: 'needs review',
  booking: 'confirming reservations',
  completed: 'wrapping up',
  // SLA
  on_track: 'within SLA',
  at_risk: 'approaching limit',
  breached: 'overdue',
};

/**
 * Get micro-label for a badge value.
 */
export function getMicroLabel(value: string): string | undefined {
  return MICRO_LABELS[value];
}
