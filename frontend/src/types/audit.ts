/**
 * Audit trail types for tracking field changes.
 * Maintains a complete history of edits with timestamps and user attribution.
 */

// ============================================================================
// TYPES
// ============================================================================

export type FieldChangeType =
  | 'create'
  | 'update'
  | 'delete'
  | 'restore';

export type TripFieldType =
  | 'destination'
  | 'type'
  | 'party'
  | 'dateWindow'
  | 'budget'
  | 'budgetCurrency'
  | 'customerMessage'
  | 'agentNotes'
  | 'state'
  | 'assignee';

export interface FieldChange {
  id: string;
  tripId: string;
  field: TripFieldType;
  changeType: FieldChangeType;
  previousValue: string | number | null;
  newValue: string | number | null;
  changedBy: string; // User ID or 'system'
  changedByName: string; // Display name
  timestamp: string; // ISO 8601
  reason?: string; // Optional reason for the change
}

export interface AuditLog {
  tripId: string;
  changes: FieldChange[];
  lastModified: string;
  version: number; // Increments with each change
}

// ============================================================================
// FORMATTING
// ============================================================================

export function formatFieldLabel(field: TripFieldType): string {
  const labels: Record<TripFieldType, string> = {
    destination: 'Destination',
    type: 'Trip Type',
    party: 'Party Size',
    dateWindow: 'Date Window',
    budget: 'Budget',
    budgetCurrency: 'Budget Currency',
    customerMessage: 'Customer Message',
    agentNotes: 'Agent Notes',
    state: 'State',
    assignee: 'Assignee',
  };
  return labels[field] || field;
}

export function formatChangeType(changeType: FieldChangeType): string {
  const types: Record<FieldChangeType, string> = {
    create: 'Created',
    update: 'Updated',
    delete: 'Deleted',
    restore: 'Restored',
  };
  return types[changeType] || changeType;
}

export function formatValue(value: string | number | null): string {
  if (value === null) return '—';
  if (typeof value === 'number') return value.toString();
  if (value === '') return '(empty)';
  return value;
}

// ============================================================================
// CHANGE DESCRIPTION
// ============================================================================

export function getChangeDescription(change: FieldChange): string {
  const fieldLabel = formatFieldLabel(change.field);
  const changeType = formatChangeType(change.changeType);

  switch (change.changeType) {
    case 'create':
      return `Set ${fieldLabel} to "${formatValue(change.newValue)}"`;
    case 'update':
      return `Changed ${fieldLabel} from "${formatValue(change.previousValue)}" to "${formatValue(change.newValue)}"`;
    case 'delete':
      return `Removed ${fieldLabel} (was "${formatValue(change.previousValue)}")`;
    case 'restore':
      return `Restored ${fieldLabel} to "${formatValue(change.newValue)}"`;
    default:
      return `${fieldLabel}: ${changeType}`;
  }
}

// ============================================================================
// FILTERING
// ============================================================================

export function filterChangesByField(
  changes: FieldChange[],
  field: TripFieldType
): FieldChange[] {
  return changes.filter(c => c.field === field);
}

export function filterChangesByUser(
  changes: FieldChange[],
  userId: string
): FieldChange[] {
  return changes.filter(c => c.changedBy === userId);
}

export function filterChangesByDateRange(
  changes: FieldChange[],
  startDate: string,
  endDate: string
): FieldChange[] {
  return changes.filter(c => {
    const changeDate = new Date(c.timestamp);
    return changeDate >= new Date(startDate) && changeDate <= new Date(endDate);
  });
}

// ============================================================================
// RECENT CHANGES
// ============================================================================

export function getRecentChanges(
  changes: FieldChange[],
  limit: number = 10
): FieldChange[] {
  return [...changes]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, limit);
}

// ============================================================================
// CHANGE SUMMARY
// ============================================================================

export interface ChangeSummary {
  totalChanges: number;
  changesByField: Record<TripFieldType, number>;
  changesByUser: Record<string, number>;
  lastChangeAt: string | null;
  lastChangeBy: string | null;
}

export function getChangeSummary(changes: FieldChange[]): ChangeSummary {
  const summary: ChangeSummary = {
    totalChanges: changes.length,
    changesByField: {} as Record<TripFieldType, number>,
    changesByUser: {},
    lastChangeAt: null,
    lastChangeBy: null,
  };

  if (changes.length === 0) return summary;

  // Sort by timestamp descending to get most recent
  const sorted = [...changes].sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  summary.lastChangeAt = sorted[0].timestamp;
  summary.lastChangeBy = sorted[0].changedByName;

  // Count by field
  for (const change of changes) {
    summary.changesByField[change.field] = (summary.changesByField[change.field] || 0) + 1;
    summary.changesByUser[change.changedBy] = (summary.changesByUser[change.changedBy] || 0) + 1;
  }

  return summary;
}
