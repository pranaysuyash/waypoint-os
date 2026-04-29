/**
 * TripCard v2
 *
 * Role-aware, progressively disclosed card for inbox trips.
 * Uses design system tokens and supports contextual SLA display.
 */

'use client';

import { memo } from 'react';
import Link from 'next/link';
import { CheckSquare, Square, Users, Calendar, Wallet, Clock, AlertTriangle, Flag, UserPlus } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { getTripRoute } from '@/lib/routes';
import {
  type ViewProfile,
  getMetricsForProfile,
  formatContextualSLA,
  getSLAHoursForStage,
  getMicroLabel,
  shouldShowMicroLabels,
} from '@/lib/inbox-helpers';
import type { InboxTrip, TripPriority } from '@/types/governance';

// ============================================================================
// PRIORITY COLOR MAPPING
// ============================================================================

const PRIORITY_COLORS: Record<TripPriority, { color: string; bg: string }> = {
  critical: { color: 'var(--accent-red)', bg: 'rgba(var(--accent-red-rgb), 0.1)' },
  high: { color: 'var(--accent-amber)', bg: 'rgba(var(--accent-amber-rgb), 0.1)' },
  medium: { color: 'var(--accent-blue)', bg: 'rgba(var(--accent-blue-rgb), 0.1)' },
  low: { color: 'var(--text-secondary)', bg: 'rgba(var(--text-muted-rgb), 0.05)' },
};

const PRIORITY_ICONS: Record<TripPriority, React.ComponentType<{ className?: string }>> = {
  critical: AlertTriangle,
  high: Flag,
  medium: Flag,
  low: Flag,
};

// ============================================================================
// STAGE LABELS
// ============================================================================

const STAGE_LABELS: Record<string, { color: string; bg: string; label: string }> = {
  intake: { color: 'var(--accent-blue)', bg: 'rgba(var(--accent-blue-rgb), 0.1)', label: 'Intake' },
  details: { color: 'var(--accent-amber)', bg: 'rgba(var(--accent-amber-rgb), 0.1)', label: 'Details' },
  options: { color: 'var(--accent-blue)', bg: 'rgba(var(--accent-blue-rgb), 0.1)', label: 'Options' },
  review: { color: 'var(--accent-red)', bg: 'rgba(var(--accent-red-rgb), 0.1)', label: 'Review' },
  booking: { color: 'var(--accent-green)', bg: 'rgba(var(--accent-green-rgb), 0.1)', label: 'Booking' },
};

// ============================================================================
// SLA STYLES
// ============================================================================

const SLA_STYLES = {
  on_track: { color: 'var(--accent-green)', bg: 'rgba(var(--accent-green-rgb), 0.1)', label: 'On Track' },
  at_risk: { color: 'var(--accent-amber)', bg: 'rgba(var(--accent-amber-rgb), 0.1)', label: 'At Risk' },
  breached: { color: 'var(--accent-red)', bg: 'rgba(var(--accent-red-rgb), 0.1)', label: 'Overdue' },
} as const;

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

const PriorityBadge = memo(function PriorityBadge({
  priority,
  showLabel,
}: {
  priority: TripPriority;
  showLabel?: boolean;
}) {
  const meta = PRIORITY_COLORS[priority];
  const Icon = PRIORITY_ICONS[priority];
  const microLabel = getMicroLabel(priority);

  return (
    <span
      className="inline-flex items-center gap-1 text-[var(--ui-text-xs)] font-medium"
      style={{ color: meta.color }}
    >
      <Icon className="w-3 h-3" />
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
      {showLabel && microLabel && (
        <span className="text-[var(--ui-text-xs)] opacity-70">· {microLabel}</span>
      )}
    </span>
  );
});

const StageBadge = memo(function StageBadge({
  stage,
  showLabel,
}: {
  stage: string;
  showLabel?: boolean;
}) {
  const meta = STAGE_LABELS[stage] || STAGE_LABELS.intake;
  const microLabel = getMicroLabel(stage);

  return (
    <span
      className="inline-flex items-center gap-1 text-[var(--ui-text-xs)] font-bold px-1.5 py-0.5 rounded uppercase tracking-tight"
      style={{ color: meta.color, background: meta.bg }}
    >
      {meta.label}
      {showLabel && microLabel && (
        <span className="opacity-70">· {microLabel}</span>
      )}
    </span>
  );
});

const ContextualSLABadge = memo(function ContextualSLABadge({
  trip,
}: {
  trip: InboxTrip;
}) {
  const style = SLA_STYLES[trip.slaStatus];
  const slaHours = getSLAHoursForStage(trip.stage);
  const contextualText = formatContextualSLA(trip.daysInCurrentStage, slaHours);
  const microLabel = getMicroLabel(trip.slaStatus);
  const showLabels = shouldShowMicroLabels();

  return (
    <span
      className="inline-flex items-center gap-1 text-[var(--ui-text-xs)] font-medium px-1.5 py-0.5 rounded"
      style={{ color: style.color, background: style.bg }}
    >
      {contextualText}
      {showLabels && microLabel && (
        <span className="opacity-70">· {microLabel}</span>
      )}
    </span>
  );
});

// ============================================================================
// METRIC FIELD RENDERERS
// ============================================================================

const METRIC_RENDERERS: Record<
  string,
  (trip: InboxTrip) => { label: string; value: React.ReactNode; icon: React.ReactNode }
> = {
  partySize: (trip) => ({
    label: 'Pax',
    value: trip.partySize,
    icon: <Users className="w-3 h-3" />,
  }),
  dateWindow: (trip) => ({
    label: 'Dates',
    value: trip.dateWindow,
    icon: <Calendar className="w-3 h-3" />,
  }),
  value: (trip) => ({
    label: 'Budget',
    value: `$${(trip.value / 1000).toFixed(1)}k`,
    icon: <Wallet className="w-3 h-3" />,
  }),
  daysInCurrentStage: (trip) => ({
    label: 'Days',
    value: `${trip.daysInCurrentStage}d`,
    icon: <Clock className="w-3 h-3" />,
  }),
  assignedToName: (trip) => ({
    label: 'Agent',
    value: trip.assignedToName || 'Unassigned',
    icon: <Users className="w-3 h-3" />,
  }),
  slaStatus: (trip) => ({
    label: 'SLA',
    value: trip.slaStatus.replace('_', ' '),
    icon: <AlertTriangle className="w-3 h-3" />,
  }),
  priority: (trip) => ({
    label: 'Priority',
    value: trip.priority,
    icon: <Flag className="w-3 h-3" />,
  }),
  priorityScore: (trip) => ({
    label: 'Score',
    value: trip.priorityScore,
    icon: <Flag className="w-3 h-3" />,
  }),
  stage: (trip) => ({
    label: 'Stage',
    value: STAGE_LABELS[trip.stage]?.label || trip.stage,
    icon: <Clock className="w-3 h-3" />,
  }),
};

// ============================================================================
// MAIN TRIP CARD
// ============================================================================

export interface TripCardProps {
  trip: InboxTrip;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  viewProfile?: ViewProfile;
  onAssign?: (tripId: string) => void;
}

export const TripCard = memo(function TripCard({
  trip,
  isSelected,
  onSelect,
  viewProfile = 'operations',
  onAssign,
}: TripCardProps) {
  const priorityMeta = PRIORITY_COLORS[trip.priority];
  const showLabels = shouldShowMicroLabels();
  const metrics = getMetricsForProfile(viewProfile);

  return (
    <Card
      variant="bordered"
      className="group relative overflow-hidden transition-all duration-200 ease-out hover:border-[var(--border-default)]"
      style={{
        borderColor:
          trip.slaStatus === 'breached'
            ? 'rgba(var(--accent-red-rgb), 0.4)'
            : 'var(--bg-canvas)',
        borderTop: `2px solid ${priorityMeta.color}`,
        opacity: isSelected ? 1 : 0.7,
      }}
    >
      <div className="p-4 min-w-0">
        {/* Selection Checkbox */}
        <button
          type="button"
          role="checkbox"
          aria-checked={isSelected}
          aria-label={`Select ${trip.destination}`}
          onClick={(e) => {
            e.stopPropagation();
            onSelect(trip.id, !isSelected);
          }}
          className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10"
        >
           {isSelected ? (
             <CheckSquare className="w-4 h-4 text-[var(--accent-blue)]" />
           ) : (
             <Square className="w-4 h-4 text-[var(--text-muted)]" />
           )}
        </button>

        <Link href={trip.id ? getTripRoute(trip.id) : '/inbox'} className="block">
          {/* Row 1: Primary Context */}
          <div className="flex items-start justify-between gap-3 mb-1 pr-6">
            <div className="flex flex-col min-w-0">
              <span
                className="text-[var(--ui-text-lg)] font-semibold truncate leading-tight"
                style={{ color: 'var(--text-primary)' }}
                title={trip.destination}
              >
                {trip.destination}
              </span>
              <span
                className="text-[var(--ui-text-xs)] uppercase tracking-wider font-bold mt-0.5"
                style={{ color: 'var(--text-muted)' }}
              >
                {trip.tripType}
              </span>
              <span
                className="text-[var(--ui-text-sm)] mt-0.5 truncate"
                style={{ color: 'var(--text-secondary)' }}
              >
                {trip.customerName}
              </span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <StageBadge stage={trip.stage} showLabel={showLabels} />
            </div>
          </div>

          {/* Row 2: Metrics (Role-Dependent) */}
          <div className="flex items-center gap-3 my-3 py-2 border-y border-dashed"
            style={{ borderColor: 'var(--border-default)' }}
          >
            {metrics.map((field, index) => {
              const renderer = METRIC_RENDERERS[field];
              if (!renderer) return null;
              const { label, value, icon } = renderer(trip);
              return (
                <div key={field} className="flex items-center gap-2">
                  {index > 0 && (
                    <div
                      className="w-px h-4"
                      style={{ background: 'var(--border-default)' }}
                    />
                  )}
                  <div className="flex flex-col gap-0.5">
                    <span
                      className="text-[var(--ui-text-xs)] uppercase font-medium"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      {label}
                    </span>
                    <span
                      className="text-[var(--ui-text-xs)] font-medium flex items-center gap-1 tabular-nums"
                      style={{
                        color:
                          field === 'value'
                            ? 'var(--accent-blue)'
                            : field === 'priorityScore'
                            ? 'var(--accent-amber)'
                            : 'var(--text-primary)',
                        fontFamily: field === 'value' ? 'var(--font-mono)' : 'inherit',
                      }}
                    >
                      {icon}
                      {value}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Row 3: Status */}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2 flex-wrap">
              <PriorityBadge priority={trip.priority} showLabel={showLabels} />
              <ContextualSLABadge trip={trip} />
            </div>

            <div className="flex items-center gap-2">
              {trip.assignedToName ? (
                <div
                  className="flex items-center gap-1 px-1.5 py-0.5 rounded border"
                  style={{
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-default)',
                  }}
                >
                  <span
                    className="text-[var(--ui-text-xs)]"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    {trip.assignedToName}
                  </span>
                </div>
              ) : (
                <span
                  className="text-[var(--ui-text-xs)] font-bold uppercase italic"
                  style={{ color: 'var(--accent-amber)' }}
                >
                  Unassigned
                </span>
              )}
            </div>
          </div>

          {/* Flags */}
          {trip.flags && trip.flags.length > 0 && (
            <div className="flex items-center gap-1 mt-2 flex-wrap">
              {trip.flags.map((flag) => (
                <span
                  key={flag}
                  className="text-[10px] px-1 py-0.5 rounded font-mono uppercase"
                  style={{
                    color: 'var(--text-muted)',
                    background: 'rgba(var(--text-muted-rgb), 0.08)',
                  }}
                >
                  {flag.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}

          {/* Footer: Trip ID + Quick Actions */}
          <div
            className="mt-2 pt-2 border-t flex items-center justify-between"
            style={{ borderColor: 'var(--border-default)' }}
          >
            <span
              className="text-[10px] font-mono"
              style={{ color: 'var(--text-muted)' }}
            >
              {trip.id}
            </span>

            {/* Quick Actions (hover-revealed) */}
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-out">
              {onAssign && !trip.assignedToName && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    onAssign(trip.id);
                  }}
                  className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[var(--ui-text-xs)] font-medium transition-colors hover:bg-[rgba(var(--accent-amber-rgb),0.15)]"
                  style={{ color: 'var(--accent-amber)' }}
                >
                  <UserPlus className="w-3 h-3" />
                  Assign
                </button>
              )}
            </div>
          </div>
        </Link>
      </div>
    </Card>
  );
});

export default TripCard;
