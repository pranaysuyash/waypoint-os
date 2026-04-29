/**
 * TripCard v3 — One severity signal per card.
 *
 * Hierarchy:
 *   Primary: Destination
 *   Secondary: Type · Customer
 *   Dominant state: ONE combined operational badge (priority + stage + SLA)
 *   Metadata: Agent / SLA / Days / Score (small, gray, not badges)
 *   Tags: secondary flags (smallest, gray)
 *   Footer: Trip ID + actions (faded, group-hover reveals)
 *
 * Rule: priority color appears in exactly ONE place — the dominant state badge.
 * No top border. No separate priority row. No competing red/amber signals.
 */

'use client';

import { memo } from 'react';
import Link from 'next/link';
import { CheckSquare, Square, Users, Calendar, Wallet, Clock, AlertTriangle, Flag, UserPlus, ChevronRight } from 'lucide-react';
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

// ── State grammar: one color encodes the whole card's urgency ────────────

const SEVERITY_RANK: Record<TripPriority, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

function getDominantState(trip: InboxTrip): {
  label: string;
  fg: string;
  bg: string;
  border: string;
} {
  // Breached SLA overrides everything
  if (trip.slaStatus === 'breached') {
    return {
      label: 'Overdue',
      fg: '#f85149',
      bg: 'rgba(248,81,73,0.10)',
      border: 'rgba(248,81,73,0.25)',
    };
  }
  // At-risk SLA is next
  if (trip.slaStatus === 'at_risk') {
    return {
      label: 'At Risk',
      fg: '#d29922',
      bg: 'rgba(210,153,34,0.10)',
      border: 'rgba(210,153,34,0.25)',
    };
  }
  // Otherwise, use priority + stage
  const stageLabels: Record<string, string> = {
    intake: 'Intake',
    details: 'Details Needed',
    options: 'Needs Options',
    review: 'Needs Review',
    booking: 'Ready to Book',
  };
  const colors: Record<TripPriority, { fg: string; bg: string; border: string }> = {
    critical: { fg: '#f85149', bg: 'rgba(248,81,73,0.10)', border: 'rgba(248,81,73,0.25)' },
    high:     { fg: '#d29922', bg: 'rgba(210,153,34,0.10)', border: 'rgba(210,153,34,0.25)' },
    medium:   { fg: '#58a6ff', bg: 'rgba(88,166,255,0.10)', border: 'rgba(88,166,255,0.25)' },
    low:      { fg: '#8b949e', bg: 'rgba(110,118,129,0.06)', border: 'rgba(110,118,129,0.15)' },
  };
  const meta = colors[trip.priority];
  return {
    label: stageLabels[trip.stage] || trip.stage,
    ...meta,
  };
}

// ── Metric renderers ───────────────────────────────────────────────────────

const METRIC_RENDERERS: Record<
  string,
  (trip: InboxTrip) => { label: string; value: React.ReactNode }> = {
  partySize: (t) => ({ label: 'Pax', value: t.partySize }),
  dateWindow: (t) => ({ label: 'Dates', value: t.dateWindow }),
  value: (t) => ({ label: 'Budget', value: `$${(t.value / 1000).toFixed(1)}k` }),
  daysInCurrentStage: (t) => ({ label: 'Days', value: `${t.daysInCurrentStage}d` }),
  assignedToName: (t) => ({ label: 'Agent', value: t.assignedToName || 'Unassigned' }),
  slaStatus: (t) => ({ label: 'SLA', value: t.slaStatus.replace('_', ' ') }),
  priorityScore: (t) => ({ label: 'Score', value: t.priorityScore }),
};

// ── Components ────────────────────────────────────────────────────────────

const StateBadge = memo(function StateBadge({ trip }: { trip: InboxTrip }) {
  const state = getDominantState(trip);
  return (
    <span
      className='inline-flex items-center gap-1.5 text-[11px] font-bold px-2 py-1 rounded-md uppercase tracking-wide shrink-0'
      style={{
        color: state.fg,
        background: state.bg,
        border: `1px solid ${state.border}`,
      }}
    >
      <span
        className='inline-block h-1.5 w-1.5 rounded-full'
        style={{ background: state.fg }}
        aria-hidden='true'
      />
      {state.label}
    </span>
  );
});

// ── Main component ───────────────────────────────────────────────────────

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
  const metrics = getMetricsForProfile(viewProfile);
  const showLabels = shouldShowMicroLabels();

  return (
    <Card
      variant='bordered'
      className='group relative overflow-hidden transition-colors'
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-hover)';
        (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-elevated)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-default)';
        (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-surface)';
      }}
    >
      <div className='p-3.5 min-w-0'>
        {/* Checkbox — hover reveal */}
        <button
          type='button'
          role='checkbox'
          aria-checked={isSelected}
          aria-label={`Select ${trip.destination}`}
          onClick={(e) => { e.stopPropagation(); onSelect(trip.id, !isSelected); }}
          className='absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10'
        >
          {isSelected ? (
            <CheckSquare className='w-4 h-4' style={{ color: 'var(--accent-blue)' }} />
          ) : (
            <Square className='w-4 h-4' style={{ color: 'var(--text-muted)' }} />
          )}
        </button>

        <Link href={trip.id ? getTripRoute(trip.id) : '/inbox'} className='block'>
          {/* ── Row 1: Destination + ONE dominant state badge ── */}
          <div className='flex items-start justify-between gap-3 mb-0.5 pr-6'>
            <div className='flex flex-col min-w-0'>
              <span
                className='text-[14px] font-semibold truncate leading-tight'
                style={{ color: 'var(--text-primary)' }}
                title={trip.destination}
              >
                {trip.destination}
              </span>
            </div>
            <StateBadge trip={trip} />
          </div>

          {/* ── Row 2: Type · Customer (secondary, quiet) ── */}
          <div className='flex items-center gap-1 text-[11px] mt-0.5 mb-2'>
            <span className='uppercase tracking-wider font-bold' style={{ color: 'var(--text-muted)' }}>
              {trip.tripType}
            </span>
            <span style={{ color: 'var(--text-placeholder)' }}>·</span>
            <span style={{ color: 'var(--text-secondary)' }}>{trip.customerName}</span>
          </div>

          {/* ── Row 3: Metadata row (small, gray, no badges) ── */}
          <div className='flex flex-wrap items-center gap-x-3 gap-y-1'>
            {metrics.map((field) => {
              const renderer = METRIC_RENDERERS[field];
              if (!renderer) return null;
              const { label, value } = renderer(trip);
              return (
                <span key={field} className='inline-flex items-center gap-1 text-[11px]' style={{ color: 'var(--text-muted)' }}>
                  <span className='font-medium'>{label}</span>
                  <span className='tabular-nums' style={{ color: 'var(--text-secondary)' }}>{value}</span>
                </span>
              );
            })}
          </div>

          {/* ── Row 4: Tags (secondary, smallest) ── */}
          {trip.flags && trip.flags.length > 0 && (
            <div className='flex items-center gap-1.5 mt-2 flex-wrap'>
              {trip.flags.map((flag) => (
                <span
                  key={flag}
                  className='text-[10px] px-1.5 py-0.5 rounded-sm font-mono uppercase tracking-wide'
                  style={{
                    color: 'var(--text-placeholder)',
                    background: 'rgba(110,118,129,0.06)',
                    border: '1px solid rgba(110,118,129,0.10)',
                  }}
                >
                  {flag.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}

          {/* ── Footer: Trip ID + Actions (faded until hover) ── */}
          <div className='mt-2.5 pt-2 flex items-center justify-between' style={{ borderTop: '1px solid var(--border-default)' }}>
            <span className='text-[10px] font-mono tabular-nums' style={{ color: 'var(--text-placeholder)' }}>
              {trip.id}
            </span>
            <div className='flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity'>
              {onAssign && !trip.assignedToName && (
                <button
                  type='button'
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    onAssign(trip.id);
                  }}
                  className='inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-sm text-[11px] font-medium transition-colors'
                  style={{ color: 'var(--accent-amber)', border: '1px solid rgba(210,153,34,0.20)' }}
                >
                  <UserPlus className='w-3 h-3' />
                  Assign
                </button>
              )}
              <ChevronRight className='h-3.5 w-3.5' style={{ color: 'var(--text-muted)' }} />
            </div>
          </div>
        </Link>
      </div>
    </Card>
  );
});

export default TripCard;
