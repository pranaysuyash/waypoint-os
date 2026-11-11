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
import { hasCustomerName, readCustomerName } from '@/lib/lead-display';

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
  variant?: 'default' | 'compact' | 'overview' | 'workspace';
  similarTripCount?: number;
}

export const PlanningTripCard = memo(function PlanningTripCard({ trip, variant = 'default', similarTripCount = 1 }: PlanningTripCardProps) {
  const summary = getPlanningListSummary(trip);
  const progressItems = getPlanningStageProgressItems(trip).slice(1);
  const freshness = getTripFreshnessLabel(trip);
  const fc = freshnessColors[freshness.tone] ?? freshnessColors.neutral;
  const meta = PLANNING_LIST_STATE_META[summary.statusTone] ?? PLANNING_LIST_STATE_META.blue;
  const isCompact = variant === 'compact' || variant === 'overview';
  const isOverview = variant === 'overview';
  const isWorkspace = variant === 'workspace' || variant === 'default';

  const rawOverviewNextAction = isOverview
    ? summary.nextAction.replace(/^Next:\s*/i, '').trim()
    : summary.nextAction;
  const overviewNextAction = rawOverviewNextAction
    ? rawOverviewNextAction.charAt(0).toUpperCase() + rawOverviewNextAction.slice(1)
    : rawOverviewNextAction;

  return (
    <div
      className='group block rounded-2xl border p-4 sm:p-5 transition-colors'
      style={{
        background: 'var(--bg-surface)',
        borderColor: meta.border,
      }}
    >
      {/* Header: trip name + status */}
      <div className='flex flex-wrap items-center justify-between gap-2 pb-3 mb-3' style={{ borderBottom: '1px solid var(--border-default)' }}>
        <div className='flex items-center gap-2 min-w-0'>
          <span className={`${isCompact ? 'text-[14px]' : 'text-[15px]'} font-semibold`} style={{ color: 'var(--text-primary)' }}>
            {summary.title}
          </span>
          {similarTripCount > 1 ? (
            <span
              className='inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium tabular-nums'
              style={{
                color: 'var(--text-tertiary)',
                borderColor: 'var(--border-default)',
                background: 'var(--bg-elevated)',
              }}
              title={`${similarTripCount} trips share this same overview pattern`}
            >
              {similarTripCount.toLocaleString('en-IN')} matching trips
            </span>
          ) : null}
        </div>
        <span className='text-[12px] font-medium' style={{ color: meta.fg }}>
          {summary.statusLabel}
        </span>
      </div>

      <div className='space-y-3'>
        {/* Ref + metadata + freshness */}
        <div className='flex flex-wrap items-start justify-between gap-2'>
          <div className='min-w-0 space-y-1'>
            <div className='flex flex-wrap items-center gap-2'>
              <span className='inline-flex items-center text-[11px] font-mono px-2 py-0.5 rounded-full shrink-0' style={{ color: 'var(--text-muted)', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>
                Ref {summary.inquiryReference}
              </span>
              <span className='text-[12px]' style={{ color: 'var(--text-muted)' }}>
                {summary.assignmentLabel}
              </span>
            </div>
            <p className='text-[13px]' style={{ color: 'var(--text-secondary)' }}>
              {[trip.contactName, summary.subtitle].filter(Boolean).join(' · ')}{summary.budgetLabel !== 'Budget missing' ? ` · ${summary.budgetLabel}` : ''}
            </p>
          </div>
          <span
            className='shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium'
            style={{ color: fc.fg, background: fc.bg, border: `1px solid ${fc.border}` }}
            title={freshness.detail}
          >
            {freshness.label}
          </span>
        </div>

        {/* Contact & missing details as clean hairline rows (no nested cards-inside-cards) */}
        {(!hasCustomerName(trip.rawInput, trip.agentNotes, trip.contactName) || summary.missingBadges.length > 0) && (
          <div className='pt-2.5 space-y-2' style={{ borderTop: '1px solid var(--border-default)' }}>
            {!hasCustomerName(trip.rawInput, trip.agentNotes, trip.contactName) && (
              <div className='flex flex-wrap items-center justify-between gap-2 text-[12px]'>
                <span style={{ color: 'var(--text-muted)' }}>Contact name missing</span>
                <Link
                  href={`/trips/${trip.id}/intake?repair=customerName`}
                  className='inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[12px] font-medium hover:underline'
                  style={{ color: 'var(--accent-blue)' }}
                >
                  Add contact name
                </Link>
              </div>
            )}

            {summary.missingBadges.length > 0 && (
              <div className='flex flex-wrap items-center gap-1.5'>
                <span className='text-[12px] font-medium mr-1' style={{ color: 'var(--accent-amber)' }}>
                  Missing trip details:
                </span>
                {summary.missingBadges.slice(0, isOverview ? 3 : 2).map((badge) => {
                  const param = fieldParam[badge];
                  const fieldName = badge.replace(/ missing$/i, '').toLowerCase();
                  return (
                    <Link
                      key={badge}
                      href={`/trips/${trip.id}/intake?repair=${param}`}
                      className='inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[12px] font-medium transition-opacity hover:opacity-80'
                      style={{ color: '#d29922', background: 'rgba(210,153,34,0.10)', border: '1px solid rgba(210,153,34,0.22)' }}
                    >
                      Add {fieldName}
                    </Link>
                  );
                })}
                {isOverview && summary.missingBadges.length > 3 ? (
                  <span
                    className='inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium'
                    style={{ color: 'var(--text-muted)', background: 'var(--bg-elevated)' }}
                    title={`${summary.missingBadges.length - 3} more missing fields`}
                  >
                    +{summary.missingBadges.length - 3} more
                  </span>
                ) : null}
              </div>
            )}
          </div>
        )}

        {/* Stage/progress */}
        {isWorkspace && (
          <div className='flex flex-wrap items-center gap-1.5 pt-1 text-[12px]'>
            <span className='font-semibold' style={{ color: 'var(--text-secondary)' }}>Stage:</span>
            <span className='font-semibold' style={{ color: 'var(--accent-blue)' }}>{summary.stage}</span>
            {progressItems.length > 0 ? (
              <>
                <span style={{ color: 'var(--text-muted)' }}>·</span>
                <span style={{ color: 'var(--text-secondary)' }}>
                  {progressItems.map((item, i) => (
                    <span key={item.label}>
                      {i > 0 ? ' · ' : ''}
                      <span style={{ color: item.color }}>{item.label}</span>
                    </span>
                  ))}
                </span>
              </>
            ) : null}
          </div>
        )}

        {/* Next step + primary action inline footer */}
        <div className='flex flex-wrap items-center justify-between gap-3 pt-2.5' style={{ borderTop: '1px solid var(--border-default)' }}>
          <p className='text-[13px] min-w-0 flex-1' style={{ color: 'var(--text-secondary)' }}>
            {overviewNextAction}
          </p>
          <Link
            href={summary.action.href}
            className='inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium shrink-0 transition-colors'
            style={{ color: 'var(--accent-blue)', background: 'rgba(88,166,255,0.08)', border: '1px solid rgba(88,166,255,0.25)' }}
          >
            {summary.action.label}
            <ChevronRight className='size-4' aria-hidden='true' />
          </Link>
        </div>
      </div>
    </div>
  );
});
