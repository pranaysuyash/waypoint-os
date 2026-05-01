'use client';

import Link from 'next/link';
import { memo } from 'react';
import { ChevronRight } from 'lucide-react';
import type { Trip } from '@/lib/api-client';
import {
  getPlanningListSummary,
  getPlanningStageProgressItems,
  getTripFreshnessLabel,
  PLANNING_LIST_STATE_META,
} from '@/lib/planning-list-display';

const freshnessColors: Record<string, { fg: string; bg: string; border: string }> = {
  neutral: { fg: '#8b949e', bg: 'rgba(139,148,158,0.10)', border: 'rgba(139,148,158,0.20)' },
  blue: { fg: '#58a6ff', bg: 'rgba(88,166,255,0.10)', border: 'rgba(88,166,255,0.20)' },
  amber: { fg: '#d29922', bg: 'rgba(210,153,34,0.12)', border: 'rgba(210,153,34,0.25)' },
  red: { fg: '#f85149', bg: 'rgba(248,81,73,0.10)', border: 'rgba(248,81,73,0.25)' },
  green: { fg: '#3fb950', bg: 'rgba(63,185,80,0.10)', border: 'rgba(63,185,80,0.25)' },
};

const fieldParam: Record<string, string> = {
  'Budget missing': 'budget',
  'Origin missing': 'origin',
  'Destination missing': 'destination',
  'Travel window missing': 'dateWindow',
  'Traveler count missing': 'party',
};

interface PlanningTripCardProps {
  trip: Trip;
  variant?: 'default' | 'compact';
}

export const PlanningTripCard = memo(function PlanningTripCard({ trip, variant = 'default' }: PlanningTripCardProps) {
  const summary = getPlanningListSummary(trip);
  const freshness = getTripFreshnessLabel(trip);
  const fc = freshnessColors[freshness.tone] ?? freshnessColors.neutral;
  const meta = PLANNING_LIST_STATE_META[summary.statusTone] ?? PLANNING_LIST_STATE_META.blue;
  const isCompact = variant === 'compact';

  return (
    <Link
      href={summary.action.href}
      className='group block rounded-2xl border p-5 transition-all'
      style={{
        background: 'linear-gradient(180deg, rgba(17,20,27,0.98) 0%, rgba(12,16,22,0.98) 100%)',
        borderColor: meta.border,
        boxShadow: '0 18px 44px rgba(0,0,0,0.20)',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.borderColor = meta.border;
        (e.currentTarget as HTMLAnchorElement).style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.borderColor = 'rgba(48,54,61,0.9)';
        (e.currentTarget as HTMLAnchorElement).style.transform = 'translateY(0)';
      }}
    >
      {/* Header: trip name */}
      <div className='-mx-5 -mt-5 mb-4 px-5 py-3 rounded-t-2xl' style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid rgba(48,54,61,0.7)' }}>
        <span className={`${isCompact ? 'text-[14px]' : 'text-[16px]'} font-semibold`} style={{ color: 'var(--text-primary)' }}>
          {summary.title}
        </span>
      </div>
      <div className='space-y-4 px-1'>
        {/* Ref + customer metadata */}
        <div className='grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-2 items-start'>
          <div className='min-w-0'>
            <span className='inline-flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded-full' style={{ color: 'var(--text-muted)', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
              Ref {summary.inquiryReference}
            </span>
            <p className='mt-2 text-[13px]' style={{ color: 'var(--text-secondary)' }}>
              {summary.subtitle}{summary.budgetLabel !== 'Budget missing' ? ` · ${summary.budgetLabel}` : ''}
            </p>
          </div>
          <span
            className='shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium justify-self-end'
            style={{ color: fc.fg, background: fc.bg, border: `1px solid ${fc.border}` }}
            title={freshness.detail}
          >
            {freshness.label}
          </span>
        </div>

        {/* Primary status row: business status first, metadata second */}
        <div className='flex items-center gap-2'>
          <span className='text-[11px] font-semibold uppercase tracking-wide' style={{ color: meta.fg }}>
            {summary.statusLabel}
          </span>
          <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>·</span>
          <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>{summary.assignmentLabel}</span>
        </div>

        {/* Missing details block */}
        {summary.missingBadges.length > 0 && (
          <div className='rounded-xl border px-3.5 py-3' style={{ borderColor: 'rgba(210,153,34,0.25)', background: 'rgba(210,153,34,0.04)' }}>
            <p className='text-[11px] font-semibold uppercase tracking-[0.16em]' style={{ color: 'var(--accent-amber)' }}>
              Missing details
            </p>
            <div className='mt-2 flex flex-wrap items-center gap-x-3 gap-y-1'>
              {summary.missingBadges.slice(0, 2).map((badge) => {
                const param = fieldParam[badge];
                return (
                  <span
                    key={badge}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); window.location.href = param ? `/trips/${trip.id}/intake?field=${param}` : summary.action.href; }}
                    className='cursor-pointer text-[12px] font-medium hover:underline'
                    style={{ color: '#d29922' }}
                  >
                    {badge}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Stage/progress */}
        <div className='flex items-center gap-1.5'>
          <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>Stage:</span>
          <span className='text-[11px] font-semibold' style={{ color: 'var(--accent-blue)' }}>{summary.stage}</span>
          <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>·</span>
          <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>
            {getPlanningStageProgressItems(trip).map((item, i) => (
              <span key={item.label}>
                {i > 0 && <span className='mx-1'>·</span>}
                <span style={{ color: item.color }}>{item.label}</span>
              </span>
            ))}
          </span>
        </div>

        {/* Next step */}
        <div className='rounded-xl border px-3.5 py-3' style={{ borderColor: 'rgba(48,54,61,0.85)', background: 'rgba(255,255,255,0.02)' }}>
          <p className='text-[13px]' style={{ color: 'var(--text-primary)' }}>
            {summary.nextAction}
          </p>
        </div>

        {/* CTA */}
        <div className='flex items-center justify-end gap-3'>
          <span className='inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium' style={{ color: 'var(--accent-blue)', background: 'rgba(88,166,255,0.08)', border: '1px solid rgba(88,166,255,0.25)' }}>
            {summary.action.label}
            <ChevronRight className='h-4 w-4' aria-hidden='true' />
          </span>
        </div>
      </div>
    </Link>
  );
});
