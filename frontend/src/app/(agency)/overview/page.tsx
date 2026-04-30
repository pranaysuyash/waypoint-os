'use client';

import Link from 'next/link';
import { memo, useMemo, useState } from 'react';
import {
  ArrowRight,
  AlertTriangle,
  Activity,
  ChevronRight,
  Send,
  MapPin,
} from 'lucide-react';
import { getTripRoute } from '@/lib/routes';
import { InlineError } from '@/components/error-boundary';
import type { Trip } from '@/lib/api-client';
import { useOverviewSummary } from './useOverviewSummary';

// ── Severity grammar: color encodes state, not decoration ──────────────────

type StateKey = 'green' | 'amber' | 'red' | 'blue';

interface StateMeta {
  fg: string;
  bg: string;
  border: string;
  label: string;
}

const STATE_META: Record<StateKey, StateMeta> = {
  green: {
    fg: '#3fb950',
    bg: 'rgba(63,185,80,0.10)',
    border: 'rgba(63,185,80,0.25)',
    label: 'Ready for Booking',
  },
  amber: {
    fg: '#d29922',
    bg: 'rgba(210,153,34,0.10)',
    border: 'rgba(210,153,34,0.25)',
    label: 'Need Trip Options',
  },
  red: {
    fg: '#f85149',
    bg: 'rgba(248,81,73,0.10)',
    border: 'rgba(248,81,73,0.25)',
    label: 'Needs Quote Review',
  },
  blue: {
    fg: '#58a6ff',
    bg: 'rgba(88,166,255,0.10)',
    border: 'rgba(88,166,255,0.25)',
    label: 'Need Customer Details',
  },
};

const INTAKE_HREF = '/workbench?draft=new&tab=intake';

// ── StatCard: metric-first operational instrument ─────────────────────────

const StatCard = memo(function StatCard({
  title,
  value,
  sub,
  ctaLabel,
  icon: Icon,
  state,
  isLoading,
  error,
  href,
}: {
  title: string;
  value: string | number;
  sub: string;
  ctaLabel: string;
  icon: React.FC<{ className?: string; style?: React.CSSProperties }>;
  state: StateKey;
  isLoading?: boolean;
  error?: Error | null;
  href?: string;
}) {
  const meta = STATE_META[state];

  if (error) {
    return (
      <div
        className='relative rounded-xl border p-4 flex flex-col gap-3'
        style={{
          background: 'var(--bg-surface)',
          borderColor: 'var(--border-default)',
          borderLeft: '3px solid var(--accent-red)',
        }}
      >
        <div className='flex items-center justify-between'>
          <span className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>{title}</span>
          <AlertTriangle className='h-4 w-4' style={{ color: 'var(--accent-red)' }} />
        </div>
        <span className='text-[13px] font-medium' style={{ color: 'var(--accent-red)' }}>Failed to load</span>
      </div>
    );
  }

  const displayValue = isLoading && value === '—' ? '—' : value;
  const displaySub = isLoading && sub === 'Loading...' ? 'Loading...' : sub;

  const cardContent = (
    <>
      {/* Row: label + icon badge */}
      <div className='flex items-center justify-between'>
        <span className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>{title}</span>
        <div
          className='h-7 w-7 rounded-md flex items-center justify-center'
          style={{ background: meta.bg, border: `1px solid ${meta.border}` }}
        >
          <Icon className='h-3.5 w-3.5' style={{ color: meta.fg }} />
        </div>
      </div>
      {/* Metric value — the anchor */}
      <span
        className='text-[24px] font-bold tabular-nums leading-none'
        style={{ color: displayValue === '—' ? 'var(--text-muted)' : meta.fg }}
      >
        {displayValue}
      </span>
      {/* Subtext — tertiary */}
      <span className='text-[12px] font-medium' style={{ color: 'var(--text-muted)' }}>{displaySub}</span>
      {href && (
        <div className='flex items-center gap-1 mt-0.5 text-[11px] font-medium' style={{ color: 'var(--accent-blue)' }}>
          {ctaLabel} <ArrowRight className='h-3 w-3' style={{ color: 'var(--accent-blue)' }} />
        </div>
      )}
    </>
  );

  const cardStyles: React.CSSProperties = {
    background: 'var(--bg-surface)',
    borderColor: 'var(--border-default)',
    borderTop: `2px solid ${meta.fg}`,
  };

  const cardClassName = 'relative rounded-xl border p-4 flex flex-col gap-2.5 transition-colors cursor-pointer';

  if (href) {
    return (
      <Link
        href={href}
        className={cardClassName}
        style={cardStyles}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border-hover)';
          (e.currentTarget as HTMLAnchorElement).style.background = 'var(--bg-elevated)';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border-default)';
          (e.currentTarget as HTMLAnchorElement).style.background = 'var(--bg-surface)';
        }}
      >
        {cardContent}
      </Link>
    );
  }

  return (
    <div
      className={cardClassName}
      style={cardStyles}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-hover)';
        (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-elevated)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-default)';
        (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-surface)';
      }}
    >
      {cardContent}
    </div>
  );
});

// ── PipelineBar: compact operational progress module ──────────────────────

const PipelineBar = memo(function PipelineBar({
  data,
  isLoading,
  error,
  leadInboxTotal,
}: {
  data: Array<{ label: string; count: number }> | null;
  isLoading: boolean;
  error: Error | null;
  leadInboxTotal: number;
}) {
  const safeData = data ?? [];
  const total = useMemo(() => {
    return safeData.reduce((s, x) => s + (Number(x.count) || 0), 0);
  }, [safeData]);

  const [isExpanded, setIsExpanded] = useState(false);

  if (error) {
    return (
      <div className='rounded-xl border p-4' style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)', borderLeft: '3px solid var(--accent-red)' }}>
        <InlineError message='Failed to load pipeline data' />
      </div>
    );
  }

  if (isLoading && safeData.length === 0) {
    return (
      <div className='rounded-xl border p-4' style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
        <div className='flex items-center justify-between mb-3'>
          <h2 className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>Planning Progress</h2>
          <span className='text-[12px] font-mono' style={{ color: 'var(--text-tertiary)' }}>Loading...</span>
        </div>
        <div className='h-2 rounded-full overflow-hidden' style={{ background: 'var(--bg-elevated)' }}>
          <div className='h-full' style={{ width: '30%', background: 'var(--accent-blue)' }} />
        </div>
      </div>
    );
  }

  if (safeData.length === 0 || total === 0) {
    const hasLeadsWaiting = leadInboxTotal > 0;
    return (
      <div className='rounded-xl border p-4' style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
        <div className='flex items-center justify-between mb-1'>
          <h2 className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>Planning Progress</h2>
          <span className='text-[13px] font-mono font-medium tabular-nums' style={{ color: 'var(--text-primary)' }}>0</span>
        </div>
        <p className='text-[12px]' style={{ color: 'var(--text-muted)' }}>
          {hasLeadsWaiting
            ? 'A lead is waiting in Lead Inbox and needs review before planning can begin.'
            : 'No trips are being planned yet.'}
        </p>
        <Link
          href={hasLeadsWaiting ? '/inbox' : INTAKE_HREF}
          className='inline-flex items-center gap-1.5 mt-3 text-[12px] font-medium transition-colors'
          style={{ color: 'var(--accent-blue)' }}
        >
          {hasLeadsWaiting ? 'Review Lead' : 'Process New Inquiry'} <ArrowRight className='h-3.5 w-3.5' />
        </Link>
      </div>
    );
  }

  // Collapsed: summary bar
  if (!isExpanded) {
    return (
      <div className='rounded-xl border p-4' style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
        <div className='flex items-center justify-between mb-2'>
          <h2 className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>Planning Progress</h2>
          <button
            onClick={() => setIsExpanded(true)}
            className='text-[11px] font-medium transition-colors'
            style={{ color: 'var(--accent-blue)' }}
          >
            Expand
          </button>
        </div>
        <div className='flex items-center gap-3'>
          <div className='flex-1'>
            <div className='h-2 rounded-full overflow-hidden flex' style={{ background: 'var(--bg-elevated)' }}>
              {safeData.map((stage, i) => (
                <div
                  key={stage.label || `stage-${i}`}
                  className='h-full transition-all'
                  style={{
                    width: `${(stage.count / total) * 100}%`,
                    background: ['#3fb950', '#58a6ff', '#d29922', '#f85149', '#a371f7'][i % 5],
                  }}
                />
              ))}
            </div>
          </div>
          <span className='text-[13px] font-semibold tabular-nums' style={{ color: 'var(--text-primary)' }}>{total}</span>
        </div>
        <p className='text-[11px] mt-1.5' style={{ color: 'var(--text-muted)' }}>
          {safeData.length} stages · Most in{' '}
          {safeData.reduce((m, s) => (s.count > m.count ? s : m)).label}
        </p>
      </div>
    );
  }

  // Expanded: vertical stage list
  return (
    <div className='rounded-xl border p-4' style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
      <div className='flex items-center justify-between mb-3'>
        <h2 className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>Planning Progress</h2>
        <div className='flex items-center gap-2'>
          <span className='text-[12px] font-mono tabular-nums' style={{ color: 'var(--text-tertiary)' }}>{total} total</span>
          <button
            onClick={() => setIsExpanded(false)}
            className='text-[11px] font-medium transition-colors'
            style={{ color: 'var(--text-muted)' }}
          >
            Collapse
          </button>
        </div>
      </div>

      <div className='space-y-2'>
        {safeData.map((stage, i) => {
          const pct = total > 0 ? (stage.count / total) * 100 : 0;
          const color = ['#3fb950', '#58a6ff', '#d29922', '#f85149', '#a371f7'][i % 5];
          return (
            <div key={stage.label} className='group'>
              <div className='flex items-center justify-between mb-1'>
                <span className='text-[12px] font-medium' style={{ color: 'var(--text-primary)' }}>{stage.label}</span>
                <span className='text-[12px] font-mono tabular-nums' style={{ color: 'var(--text-tertiary)' }}>{stage.count}</span>
              </div>
              <div className='h-1.5 rounded-full overflow-hidden' style={{ background: 'var(--bg-elevated)' }}>
                <div
                  className='h-full rounded-full transition-all'
                  style={{ width: `${pct}%`, background: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

// ── ActivityRow: trip as operational decision object ───────────────────────

const ActivityRow = memo(function ActivityRow({
  item,
}: {
  item: {
    id: string;
    destination: string;
    type: string;
    state: StateKey;
    age: string;
  };
}) {
  const meta = STATE_META[item.state] ?? STATE_META.blue;
  return (
    <Link
      href={item.id ? getTripRoute(item.id) : '/inbox'}
      className='flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group'
      style={{
        borderLeft: '2px solid transparent',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.background = 'var(--bg-elevated)';
        (e.currentTarget as HTMLAnchorElement).style.borderLeftColor = meta.fg;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLAnchorElement).style.background = 'transparent';
        (e.currentTarget as HTMLAnchorElement).style.borderLeftColor = 'transparent';
      }}
    >
      <div className='flex-1 min-w-0'>
        <div className='flex items-center gap-2'>
          <span className='text-[13px] font-medium truncate' style={{ color: 'var(--text-primary)' }}>{item.destination}</span>
          <span className='text-[11px] shrink-0' style={{ color: 'var(--text-tertiary)' }}>{item.type}</span>
        </div>
        <div className='text-[11px] font-mono' style={{ color: 'var(--text-muted)' }}>{item.id}</div>
      </div>
      <div className='flex items-center gap-2 shrink-0'>
        <span
          className='text-[11px] font-semibold px-1.5 py-0.5 rounded-sm uppercase tracking-wide'
          style={{
            color: meta.fg,
            background: meta.bg,
            border: `1px solid ${meta.border}`,
          }}
        >
          {meta.label}
        </span>
        <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>{item.age}</span>
        <ChevronRight
          className='h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity'
          style={{ color: 'var(--text-muted)' }}
          aria-hidden='true'
        />
      </div>
    </Link>
  );
});

// ── RecentTrips: empty + populated states ─────────────────────────────────

function RecentTrips({
  trips,
  isLoading,
  error,
  planningTripsTotal,
  leadInboxTotal,
}: {
  trips: Trip[];
  isLoading: boolean;
  error: Error | null;
  planningTripsTotal: number;
  leadInboxTotal: number;
}) {
  const tripItems = useMemo(() => {
    if (trips.length === 0) return [];
    return trips.map((trip) => ({
      id: trip.id,
      destination: trip.destination,
      type: trip.type,
      state: trip.state,
      age: trip.age,
    }));
  }, [trips]);

  const hasLeadsWaiting = planningTripsTotal === 0 && leadInboxTotal > 0;

  if (error) {
    return (
      <div className='p-4'>
        <InlineError message='Failed to load recent trips' />
      </div>
    );
  }

  if (isLoading && trips.length === 0) {
    return (
      <div className='p-4 space-y-2'>
        {[1, 2, 3].map((i) => (
          <div key={i} className='h-14 rounded-lg animate-pulse' style={{ background: 'var(--bg-elevated)' }} />
        ))}
      </div>
    );
  }

  if (tripItems.length === 0) {
    return (
      <div className='p-8 text-center'>
        {/* Empty state: intentional, not accidental */}
        <div
          className='w-14 h-14 rounded-xl flex items-center justify-center mx-auto mb-4'
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
          }}
        >
          <MapPin className='w-6 h-6' style={{ color: 'var(--text-tertiary)' }} />
        </div>
        <p className='text-[14px] font-medium mb-1' style={{ color: 'var(--text-primary)' }}>
          No trips in planning yet
        </p>
        <p className='text-[12px] leading-relaxed max-w-[280px] mx-auto' style={{ color: 'var(--text-secondary)' }}>
          {hasLeadsWaiting
            ? 'A lead is waiting in Lead Inbox. Review it to start planning, and the trip will appear here.'
            : 'Add a customer inquiry and Waypoint will organize the details, flag missing information, and prepare the next planning step.'}
        </p>
        <Link
          href={hasLeadsWaiting ? '/inbox' : INTAKE_HREF}
          className='inline-flex items-center gap-2 mt-5 px-4 py-2 rounded-lg text-[13px] font-medium transition-colors border'
          style={{
            background: 'transparent',
            color: 'var(--text-primary)',
            borderColor: 'var(--border-default)',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border-hover)';
            (e.currentTarget as HTMLAnchorElement).style.background = 'var(--bg-elevated)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border-default)';
            (e.currentTarget as HTMLAnchorElement).style.background = 'transparent';
          }}
        >
          <Send className='w-4 h-4' style={{ color: 'var(--accent-blue)' }} />
          {hasLeadsWaiting ? 'Review Lead' : 'Add New Inquiry'}
          <ArrowRight className='w-3.5 h-3.5' style={{ color: 'var(--text-muted)' }} />
        </Link>
      </div>
    );
  }

  return (
    <div className='p-1.5 space-y-0.5'>
      {tripItems.map((item) => (
        <ActivityRow key={item.id} item={item} />
      ))}
    </div>
  );
}

// ── Page: Operations Overview ───────────────────────────────────────────

export default function OverviewPage() {
  const {
    headerSubtitle,
    metrics,
    navItems,
    pipeline,
    pipelineLoading,
    pipelineError,
    recentTrips,
    recentTripsLoading,
    recentTripsError,
    planningTripsTotal,
    leadInboxTotal,
  } = useOverviewSummary();

  const stateEntries = useMemo(
    () => Object.entries(STATE_META) as [StateKey, StateMeta][],
    []
  );

  return (
    <main className='p-5 max-w-[1400px] mx-auto space-y-5'>
      {/* Header: breadcrumb quiet, title clear, actions secondary */}
      <header className='flex items-center justify-between pt-1'>
        <div>
          <div className='flex items-center gap-2 mb-1'>
            <span className='text-[12px] font-medium' style={{ color: 'var(--text-muted)' }}>Waypoint</span>
            <span style={{ color: 'var(--border-default)' }} aria-hidden='true'>/</span>
            <span className='text-[12px] font-medium' style={{ color: 'var(--text-primary)' }}>Overview</span>
          </div>
           <h1 className='text-[18px] font-semibold tracking-tight' style={{ color: 'var(--text-primary)' }}>
             Operations Overview
           </h1>
           <p className='text-[13px] mt-0.5' style={{ color: 'var(--text-secondary)' }}>
             {headerSubtitle}
           </p>
         </div>
        <Link
          href={INTAKE_HREF}
          className='inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium border transition-colors'
          style={{
            background: 'transparent',
            color: 'var(--text-primary)',
            borderColor: 'var(--border-default)',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--accent-blue)';
            (e.currentTarget as HTMLAnchorElement).style.color = 'var(--accent-blue)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border-default)';
            (e.currentTarget as HTMLAnchorElement).style.color = 'var(--text-primary)';
          }}
        >
          Process New Inquiry
          <ArrowRight className='h-3.5 w-3.5' aria-hidden='true' />
        </Link>
      </header>

      {/* Stat cards: metric-first instruments */}
      <div className='grid grid-cols-2 lg:grid-cols-4 gap-3'>
        {metrics.map((metric) => (
          <StatCard
            key={metric.title}
            title={metric.title}
              value={metric.value}
              sub={metric.sub}
              ctaLabel={metric.ctaLabel}
              icon={metric.icon}
            state={metric.state}
            isLoading={metric.isLoading}
            error={metric.error}
            href={metric.href}
          />
        ))}
      </div>

      {/* Main content: trips + right rail */}
      <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
        {/* Recent trips panel */}
        <section
          className='lg:col-span-2 rounded-xl border overflow-hidden flex flex-col'
          style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
        >
          <header
            className='flex items-center justify-between px-4 py-3'
            style={{ borderBottom: '1px solid var(--border-default)' }}
          >
            <div className='flex items-center gap-2'>
              <Activity className='h-4 w-4' style={{ color: 'var(--text-tertiary)' }} aria-hidden='true' />
              <h2 className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
                Trips in Planning
              </h2>
            </div>
            <Link
              href='/trips'
              className='inline-flex items-center gap-1 text-[12px] font-medium transition-colors'
              style={{ color: 'var(--accent-blue)' }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = 'var(--text-primary)'; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = 'var(--accent-blue)'; }}
            >
               Open trips <ArrowRight className='h-3.5 w-3.5' aria-hidden='true' />
            </Link>
          </header>
          <RecentTrips
            trips={recentTrips}
            isLoading={recentTripsLoading}
            error={recentTripsError}
            planningTripsTotal={planningTripsTotal}
            leadInboxTotal={leadInboxTotal}
          />
        </section>

        {/* Right rail: compact operational modules */}
        <aside className='space-y-4'>
          <PipelineBar
            data={pipeline}
            isLoading={pipelineLoading}
            error={pipelineError}
            leadInboxTotal={leadInboxTotal}
          />

          <nav
            className='rounded-xl border p-4'
            style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
            aria-label='Quick navigation'
          >
            <h2 className='text-[11px] font-semibold uppercase tracking-wider mb-3' style={{ color: 'var(--text-tertiary)' }}>
              Jump To
            </h2>
            <ul className='space-y-1'>
              {navItems.map((nav) => {
                const Icon = nav.icon;
                return (
                  <li key={nav.href}>
                    <Link
                      href={nav.href}
                      className='flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group'
                      style={{ border: '1px solid transparent' }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLAnchorElement).style.background = 'var(--bg-elevated)';
                        (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border-default)';
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLAnchorElement).style.background = 'transparent';
                        (e.currentTarget as HTMLAnchorElement).style.borderColor = 'transparent';
                      }}
                    >
                      <div
                        className='h-8 w-8 rounded-lg flex items-center justify-center shrink-0'
                        style={{
                          background: 'var(--bg-elevated)',
                          border: '1px solid var(--border-default)',
                        }}
                      >
                        <Icon
                          className='h-4 w-4'
                          style={{ color: 'var(--text-tertiary)' }}
                          aria-hidden='true'
                        />
                      </div>
                      <div className='flex-1 min-w-0'>
                        <div className='text-[13px] font-medium' style={{ color: 'var(--text-primary)' }}>{nav.label}</div>
                        <div className='text-[11px] font-mono tabular-nums' style={{ color: nav.subColor }}>
                          {nav.sub}
                        </div>
                      </div>
                      <ChevronRight
                        className='h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity'
                        style={{ color: 'var(--text-muted)' }}
                        aria-hidden='true'
                      />
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <section
            className='rounded-xl border p-4'
            style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
          >
            <h2 className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
              Planning Status
            </h2>
            <div className='mt-3 space-y-2'>
              {stateEntries.map(([, meta]) => (
                <div key={meta.label} className='flex items-center gap-2.5'>
                  <span
                    className='h-2 w-2 rounded-full shrink-0'
                    style={{ background: meta.fg, boxShadow: `0 0 6px ${meta.fg}40` }}
                    aria-hidden='true'
                  />
                  <span className='text-[12px] font-medium' style={{ color: 'var(--text-secondary)' }}>{meta.label}</span>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
