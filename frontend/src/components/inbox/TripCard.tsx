'use client';

import { memo } from 'react';
import Link from 'next/link';
import { CheckSquare, Square, ChevronRight, Flag, UserX } from 'lucide-react';
import { Card } from '@/components/ui/card';
import type { InboxTrip } from '@/types/governance';
import type { ViewProfile, MetricField } from '@/lib/inbox-helpers';
import {
  formatContextualSLA,
  getMicroLabel,
  getMetricsForProfile,
  shouldShowMicroLabels,
  DEFAULT_STAGE_SLA_HOURS,
} from '@/lib/inbox-helpers';

// ──────────────────────────────────────────────────────────────────────────────
// Color tokens mapping
// ──────────────────────────────────────────────────────────────────────────────

const PRIORITY_BAR: Record<string, string> = {
  critical: '#f85149',
  high: '#d29922',
  medium: '#58a6ff',
  low: '#8b949e',
};

const SLA_BADGE: Record<string, { bg: string; text: string; border: string }> = {
  on_track:  { bg: 'rgba(63,185,80,0.12)',  text: '#3fb950', border: 'rgba(63,185,80,0.28)' },
  at_risk: { bg: 'rgba(210,153,34,0.12)', text: '#d29922', border: 'rgba(210,153,34,0.28)' },
  breached:  { bg: 'rgba(248,81,73,0.12)',  text: '#f85149', border: 'rgba(248,81,73,0.28)' },
};

const STAGE_BG: Record<string, { bg: string; text: string; border: string }> = {
  intake:   { bg: 'rgba(88,166,255,0.12)', text: '#58a6ff', border: 'rgba(88,166,255,0.28)' },
  details:  { bg: 'rgba(163,113,247,0.12)', text: '#a371f7', border: 'rgba(163,113,247,0.28)' },
  options:  { bg: 'rgba(210,153,34,0.12)', text: '#d29922', border: 'rgba(210,153,34,0.28)' },
  review:   { bg: 'rgba(255,146,72,0.12)', text: '#ff9248', border: 'rgba(255,146,72,0.28)' },
  booking:  { bg: 'rgba(63,185,80,0.12)',  text: '#3fb950', border: 'rgba(63,185,80,0.28)' },
  completed:{ bg: 'rgba(139,148,158,0.12)', text: '#8b949e', border: 'rgba(139,148,158,0.28)' },
};

const ASSIGNED_BG: Record<string, { bg: string; text: string; border: string }> = {
  assigned:  { bg: 'rgba(63,185,80,0.10)', text: '#3fb950', border: 'rgba(63,185,80,0.20)' },
  unassigned:{ bg: 'rgba(88,166,255,0.10)', text: '#58a6ff', border: 'rgba(88,166,255,0.20)' },
};

// ──────────────────────────────────────────────────────────────────────────────
// Metric field formatters
// ──────────────────────────────────────────────────────────────────────────────

const METRIC_FORMATTERS: Record<MetricField, (trip: InboxTrip) => string> = {
  partySize: (t) => `${t.partySize} pax`,
  dateWindow: (t) => (t.dateWindow || 'Dates TBD'),
  value: (t) => {
    if (!t.value || t.value <= 0) return 'Value TBD';
    return t.value >= 1000 ? `$${(t.value / 1000).toFixed(1)}k` : `$${t.value}`;
  },
  daysInCurrentStage: (t) => `${t.daysInCurrentStage}d`,
  assignedToName: (t) => t.assignedToName || (t.assignedTo ? 'Assigned' : 'Unassigned'),
  slaStatus: (t) => t.slaStatus.replace('_', ' '),
  priority: (t) => t.priority.charAt(0).toUpperCase() + t.priority.slice(1),
  stage: (t) => t.stage,
};

// ──────────────────────────────────────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────────────────────────────────────

function TripCardMetrics({ trip, profile }: { trip: InboxTrip; profile: ViewProfile }) {
  const fields = getMetricsForProfile(profile);
  return (
    <div
      data-testid="trip-card-metrics"
      className="flex items-center gap-2 text-[11px] mt-2 flex-wrap"
      style={{ color: 'var(--text-muted)' }}
    >
      {fields.map((field, i) => (
        <span key={field} className="flex items-center gap-1.5">
          {i > 0 && <span style={{ color: 'var(--text-secondary)' }}>·</span>}
          <span>{METRIC_FORMATTERS[field](trip)}</span>
        </span>
      ))}
    </div>
  );
}

function FlagBadge({ flag, showLabel }: { flag: string; showLabel: boolean }) {
  const label = showLabel ? getMicroLabel(flag) : undefined;
  return (
    <span
      data-testid="trip-flag-badge"
      className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium"
      style={{
        background: 'rgba(210,153,34,0.10)',
        color: '#d29922',
        border: '1px solid rgba(210,153,34,0.20)',
      }}
    >
      {label || flag}
    </span>
  );
}

function FlagBadgeRow({ trip, showMicroLabels }: { trip: InboxTrip; showMicroLabels: boolean }) {
  if (!trip.flags?.length) return null;
  return (
    <div data-testid="trip-card-flags" className="flex items-center gap-1.5 mt-2 flex-wrap">
      {trip.flags.map((flag, index) => (
        <FlagBadge key={`${flag}-${index}`} flag={flag} showLabel={showMicroLabels} />
      ))}
    </div>
  );
}

function TripCardSLA({ trip }: { trip: InboxTrip }) {
  const slaHours = DEFAULT_STAGE_SLA_HOURS[trip.stage] || 168;
  const contextualText = `${trip.daysInCurrentStage}d · ${formatContextualSLA(trip.daysInCurrentStage, slaHours)}`;
  const style = SLA_BADGE[trip.slaStatus] || SLA_BADGE.on_track;

  return (
    <span
      data-testid="trip-card-sla"
      className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{
        color: style.text,
        background: style.bg,
        border: `1px solid ${style.border}`,
      }}
    >
      {contextualText}
    </span>
  );
}

function TripCardAssignment({ trip }: { trip: InboxTrip }) {
  if (trip.assignedToName) {
    const style = ASSIGNED_BG.assigned;
    return (
      <span
        data-testid="trip-card-assigned"
        className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium"
        style={{
          color: style.text,
          background: style.bg,
          border: `1px solid ${style.border}`,
        }}
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <circle cx="12" cy="8" r="4"/>
          <path d="M20 21a8 8 0 0 0-16 0"/>
        </svg>
        {trip.assignedToName}
      </span>
    );
  }

  const style = ASSIGNED_BG.unassigned;
  return (
    <span
      data-testid="trip-card-unassigned"
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium"
      style={{
        color: style.text,
        background: style.bg,
        border: `1px solid ${style.border}`,
      }}
    >
      <UserX className="w-3.5 h-3.5" />
      Unassigned
    </span>
  );
}

function TripCardStageBadge({ stage }: { stage: string }) {
  const style = STAGE_BG[stage] || STAGE_BG.intake;
  return (
    <span
      data-testid="trip-card-stage"
      className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{
        color: style.text,
        background: style.bg,
        border: `1px solid ${style.border}`,
      }}
    >
      {stage}
    </span>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Main
// ──────────────────────────────────────────────────────────────────────────────

export interface TripCardProps {
  trip: InboxTrip;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  viewProfile?: ViewProfile;
}

export const TripCard = memo(function TripCard({
  trip,
  isSelected,
  onSelect,
  viewProfile = 'operations',
}: TripCardProps) {
  const accentColor = PRIORITY_BAR[trip.priority] || PRIORITY_BAR.medium;
  const showMicroLabels = shouldShowMicroLabels();

  const reviewHref = `/trips/${trip.id}/intake`;
  const title = `${trip.destination} ${trip.tripType.toLowerCase()}`.trim();

  return (
    <Card
      className="group relative overflow-hidden transition-colors"
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
      {/* Accent bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[3px]"
        style={{ background: accentColor }}
        aria-hidden="true"
      />

      {/* Checkbox hover-reveal */}
      <button
        type="button"
        role="checkbox"
        aria-checked={isSelected}
        aria-label={`Select ${trip.destination}`}
        onClick={(e) => { e.stopPropagation(); onSelect(trip.id, !isSelected); }}
        className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10"
      >
        {isSelected ? (
          <CheckSquare className="w-4 h-4" style={{ color: 'var(--accent-blue)' }} />
        ) : (
          <Square className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
        )}
      </button>

      <div className="p-4 pl-5 min-w-0">
        {/* Row 1: Primary Context */}
        <div className="flex items-start justify-between gap-3 pr-6">
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-2">
              <span
                data-testid="trip-card-destination"
                className="text-[15px] font-semibold truncate leading-tight"
                style={{ color: 'var(--text-primary)' }}
                title={title}
              >
                {title}
              </span>
            </div>
            <span
              data-testid="trip-card-customer"
              className="text-[11px] mt-0.5 truncate"
              style={{ color: 'var(--text-secondary)' }}
            >
              {trip.customerName || 'Customer name unavailable'}
            </span>
          </div>
          <TripCardStageBadge stage={trip.stage} />
        </div>

        {/* Row 2: Metrics (role-dependent) */}
        <TripCardMetrics trip={trip} profile={viewProfile} />

        {/* Row 3: Status */}
        <div
          data-testid="trip-card-status"
          className="flex items-center gap-2 mt-2.5 flex-wrap"
        >
          <TripCardSLA trip={trip} />
          <TripCardAssignment trip={trip} />
        </div>

        {/* Flags */}
        <FlagBadgeRow trip={trip} showMicroLabels={showMicroLabels} />

        {/* Row 4: Footer */}
        <div
          className="mt-3 pt-3 flex items-center justify-between"
          style={{ borderTop: '1px solid var(--border-default)' }}
        >
          <span
            data-testid="trip-card-id"
            className="text-[10px] tabular-nums truncate max-w-[140px]"
            style={{ color: 'var(--text-placeholder)' }}
            title={trip.id}
          >
            {trip.id}
          </span>
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Link
              href={reviewHref}
              data-testid="trip-card-view-link"
              className="inline-flex items-center gap-1 text-[11px] font-medium transition-colors"
              style={{ color: 'var(--accent-blue)' }}
            >
              View
              <ChevronRight className="h-3.5 w-3.5" style={{ color: 'var(--accent-blue)' }} />
            </Link>
          </div>
        </div>
      </div>
    </Card>
  );
});

export default TripCard;