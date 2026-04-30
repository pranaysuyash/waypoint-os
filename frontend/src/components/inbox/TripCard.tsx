'use client';

import { memo } from 'react';
import Link from 'next/link';
import { CheckSquare, Square, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { formatDateWindowDisplay, formatLeadTitle } from '@/lib/lead-display';
import { getTripRoute } from '@/lib/routes';
import type { ViewProfile } from '@/lib/inbox-helpers';
import type { InboxTrip } from '@/types/governance';

type PillTone = 'attention' | 'healthy' | 'risk' | 'ownership';

function formatBudgetSummary(trip: InboxTrip): string {
  if (!trip.value || trip.value <= 0) return 'Budget missing';
  return `Budget ${trip.value >= 1000 ? `$${(trip.value / 1000).toFixed(1)}k` : `$${trip.value}`}`;
}

function deriveNextAction(trip: InboxTrip): string {
  const hasBudget = trip.value > 0;
  const needsClarification = trip.flags.includes('needs_clarification') || trip.flags.includes('details_unclear');
  if (!hasBudget && needsClarification) return 'Next: confirm budget and trip details.';
  if (!hasBudget) return 'Next: confirm budget before planning.';
  if (needsClarification) return 'Next: review customer details before planning.';
  return 'Next: review the lead before starting planning.';
}

function getPrimaryPills(trip: InboxTrip): Array<{ label: string; tone: PillTone }> {
  const pills: Array<{ label: string; tone: PillTone }> = [];
  const needsDetails =
    trip.flags.includes('incomplete') ||
    trip.flags.includes('needs_clarification') ||
    trip.flags.includes('details_unclear');

  if (needsDetails) {
    pills.push({ label: 'Needs details', tone: 'attention' });
  } else {
    pills.push({ label: 'Ready to plan', tone: 'healthy' });
  }

  if (trip.assignedToName) {
    pills.push({ label: `Assigned to ${trip.assignedToName}`, tone: 'healthy' });
  } else {
    pills.push({ label: 'Unassigned', tone: 'ownership' });
  }

  if (trip.slaStatus === 'breached') {
    pills.push({ label: 'SLA late', tone: 'risk' });
  } else if (trip.slaStatus === 'at_risk') {
    pills.push({ label: 'SLA due soon', tone: 'risk' });
  } else {
    pills.push({ label: 'SLA on track', tone: 'healthy' });
  }

  return pills.slice(0, 3);
}

const PILL_STYLES: Record<PillTone, { text: string; bg: string; border: string }> = {
  attention: { text: '#f2cc60', bg: 'rgba(210,153,34,0.12)', border: 'rgba(210,153,34,0.28)' },
  healthy: { text: '#3fb950', bg: 'rgba(63,185,80,0.12)', border: 'rgba(63,185,80,0.28)' },
  risk: { text: '#ff8b85', bg: 'rgba(248,81,73,0.12)', border: 'rgba(248,81,73,0.28)' },
  ownership: { text: '#a5d6ff', bg: 'rgba(88,166,255,0.12)', border: 'rgba(88,166,255,0.28)' },
};

// ── Main component ───────────────────────────────────────────────────────

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
  viewProfile: _viewProfile = 'operations',
}: TripCardProps) {
  const reviewHref = trip.id ? getTripRoute(trip.id) : '/inbox';
  const displayReference = trip.reference?.trim() ? `Inquiry Ref: ${trip.reference}` : null;
  const primaryPills = getPrimaryPills(trip);
  const title = formatLeadTitle(trip.destination, trip.tripType);
  const subtitle = `${trip.customerName} · ${trip.partySize} pax · ${formatDateWindowDisplay(trip.dateWindow, 'Dates to confirm')}`;
  const budgetSummary = formatBudgetSummary(trip);
  const nextAction = deriveNextAction(trip);

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

        {/* ── Row 1: Lead identity ── */}
        <div className='flex items-start gap-3 mb-1 pr-6'>
          <div className='flex flex-col min-w-0'>
            <span
              className='text-[15px] font-semibold truncate leading-tight'
              style={{ color: 'var(--text-primary)' }}
              title={title}
            >
              {title}
            </span>
            <span className='text-[11px] mt-1 truncate' style={{ color: 'var(--text-secondary)' }}>
              {subtitle}
            </span>
          </div>
        </div>

        {/* ── Row 2: Action status pills ── */}
        <div className='flex items-center gap-1.5 mt-2 flex-wrap'>
          {primaryPills.map((pill) => {
            const style = PILL_STYLES[pill.tone];
            return (
              <span
                key={pill.label}
                className='inline-flex items-center rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide'
                style={{
                  color: style.text,
                  background: style.bg,
                  border: `1px solid ${style.border}`,
                }}
              >
                {pill.label}
              </span>
            );
          })}
        </div>

        {/* ── Row 3: Key fields + next action ── */}
        <div className='mt-3 space-y-2'>
          <div className='text-[11px] font-medium' style={{ color: 'var(--text-secondary)' }}>
            {budgetSummary}
          </div>
          <div className='text-[11px]' style={{ color: 'var(--text-muted)' }}>
            {nextAction}
          </div>
        </div>

        {/* ── Footer: Reference + action ── */}
        <div className='mt-3 pt-3 flex items-center justify-between' style={{ borderTop: '1px solid var(--border-default)' }}>
          <span className='text-[10px] tabular-nums' style={{ color: 'var(--text-placeholder)' }}>
            {displayReference}
          </span>
          <div className='flex items-center gap-2'>
            <Link
              href={reviewHref}
              className='inline-flex items-center gap-1 text-[11px] font-medium transition-colors'
              style={{ color: 'var(--accent-blue)' }}
            >
              Review Lead
              <ChevronRight className='h-3.5 w-3.5' style={{ color: 'var(--accent-blue)' }} />
            </Link>
          </div>
        </div>
      </div>
    </Card>
  );
});

export default TripCard;
