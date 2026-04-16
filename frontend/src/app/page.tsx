'use client';

import Link from 'next/link';
import { memo, useMemo, useCallback } from 'react';
import {
  Briefcase,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Inbox,
  Activity,
  ChevronRight,
} from 'lucide-react';
import { useTrips, useTripStats, usePipeline } from '@/hooks/useTrips';
import { InlineLoading } from '@/components/ui/loading';
import { InlineError } from '@/components/error-boundary';

type StateKey = 'green' | 'amber' | 'red' | 'blue';

const STATE_META: Record<
  StateKey,
  { color: string; bg: string; label: string }
> = {
  green: {
    color: '#3fb950',
    bg: 'rgba(63,185,80,0.12)',
    label: 'PROCEED_SAFE',
  },
  amber: {
    color: '#d29922',
    bg: 'rgba(210,153,34,0.12)',
    label: 'BRANCH / DRAFT',
  },
  red: { color: '#f85149', bg: 'rgba(248,81,73,0.12)', label: 'STOP_REVIEW' },
  blue: {
    color: '#58a6ff',
    bg: 'rgba(88,166,255,0.12)',
    label: 'ASK_FOLLOWUP',
  },
};

const StatCard = memo(function StatCard({
  title,
  value,
  sub,
  icon: Icon,
  state,
  isLoading,
  error,
}: {
  title: string;
  value: string | number;
  sub: string;
  icon: React.FC<{ className?: string; style?: React.CSSProperties }>;
  state: StateKey;
  isLoading?: boolean;
  error?: Error | null;
}) {
  const meta = STATE_META[state];

  if (error) {
    return (
      <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 flex flex-col gap-3'>
        <div className='flex items-center justify-between'>
          <span className='text-sm font-semibold tracking-widest uppercase text-[#8b949e]'>
            {title}
          </span>
          <AlertTriangle className='h-4 w-4 text-[#f85149]' />
        </div>
        <span className='text-sm text-[#f85149]'>Failed to load</span>
      </div>
    );
  }

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 flex flex-col gap-3 hover:border-[#30363d] transition-colors'>
      <div className='flex items-center justify-between'>
        <span className='text-sm font-semibold tracking-widest uppercase text-[#8b949e]'>
          {title}
        </span>
        <div
          className='h-8 w-8 rounded-lg flex items-center justify-center'
          style={{ background: meta.bg }}
        >
          {isLoading ? (
            <div className='w-4 h-4 border-2 border-[#0d1117]/30 border-t-[#0d1117] rounded-full animate-spin' />
          ) : (
            <Icon className='h-4 w-4' style={{ color: meta.color }} />
          )}
        </div>
      </div>
      <span
        className='text-3xl font-bold tabular-nums'
        style={{ color: meta.color }}
      >
        {isLoading ? '—' : value}
      </span>
      <span className='text-sm text-[#8b949e] font-mono'>{sub}</span>
    </div>
  );
});

const PipelineBar = memo(function PipelineBar({
  data,
  isLoading,
  error,
}: {
  data: Array<{ label: string; count: number }> | null;
  isLoading: boolean;
  error: Error | null;
}) {
  const total = useMemo(() => {
    if (!data) return 0;
    return data.reduce((s, x) => s + x.count, 0);
  }, [data]);

  if (error) {
    return (
      <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
        <InlineError message='Failed to load pipeline data' />
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
        <div className='flex items-center justify-between mb-3'>
          <h2 className='text-sm font-semibold tracking-widest uppercase text-[#8b949e]'>
            Pipeline
          </h2>
          <span className='text-sm font-mono text-[#8b949e]'>
            Loading...
          </span>
        </div>
        <div className='h-2 bg-[#161b22] rounded-full overflow-hidden'>
          <div
            className='h-full bg-[#58a6ff] animate-pulse'
            style={{ width: '30%' }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
      <div className='flex items-center justify-between mb-3'>
        <h2 className='text-sm font-semibold tracking-widest uppercase text-[#8b949e]'>
          Pipeline
        </h2>
        <span className='text-sm font-mono text-[#8b949e]'>
          {total} total
        </span>
      </div>
      <div className='flex h-2 rounded-full overflow-hidden gap-px'>
        {data.map((stage) => (
          <div
            key={stage.label}
            className='h-full'
            style={{
              width: `${(stage.count / total) * 100}%`,
              background: '#58a6ff',
              opacity: 0.35 + (stage.count / total) * 0.65,
            }}
            title={`${stage.label}: ${stage.count}`}
          />
        ))}
      </div>
      <div className='flex justify-between mt-2.5'>
        {data.map((stage) => (
          <div
            key={stage.label}
            className='flex flex-col items-center gap-0.5 min-w-0'
          >
            <span className='text-sm font-semibold tabular-nums text-[#e6edf3]'>
              {stage.count}
            </span>
            <span className='text-sm text-[#8b949e] truncate'>
              {stage.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
});

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
  const meta = STATE_META[item.state];
  return (
    <Link
      href={`/workbench?trip=${item.id}`}
      className='flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-[#161b22] transition-colors group'
    >
      <span
        className='inline-block h-1.5 w-1.5 rounded-full shrink-0'
        style={{ background: meta.color }}
        aria-hidden='true'
      />
      <div className='flex-1 min-w-0'>
        <div className='flex items-center gap-2'>
          <span className='text-base font-medium text-[#e6edf3] truncate'>
            {item.destination}
          </span>
          <span className='text-sm text-[#8b949e]'>{item.type}</span>
        </div>
        <div className='text-sm font-mono text-[#8b949e]'>{item.id}</div>
      </div>
      <div className='flex items-center gap-2 shrink-0'>
        <span
          className='text-sm font-mono px-2 py-0.5 rounded-md'
          style={{ color: meta.color, background: meta.bg }}
        >
          {meta.label}
        </span>
        <span className='text-sm text-[#8b949e]'>{item.age}</span>
        <ChevronRight
          className='h-4 w-4 text-[#30363d] group-hover:text-[#8b949e] transition-colors'
          aria-hidden='true'
        />
      </div>
    </Link>
  );
});

function RecentTrips() {
  const { data: trips, isLoading, error } = useTrips({ limit: 5 });

  const tripItems = useMemo(() => {
    if (!trips || trips.length === 0) return null;

    return trips.map((trip) => ({
      id: trip.id,
      destination: trip.destination,
      type: trip.type,
      state: trip.state,
      age: trip.age,
    }));
  }, [trips]);

  if (error) {
    return (
      <div className='p-4'>
        <InlineError message='Failed to load recent trips' />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className='p-4 space-y-2'>
        {[1, 2, 3].map((i) => (
          <div key={i} className='h-16 bg-[#161b22] rounded-lg animate-pulse' />
        ))}
      </div>
    );
  }

  if (!tripItems) {
    return (
      <div className='p-4 text-center text-base text-[#8b949e]'>
        No recent trips
      </div>
    );
  }

  return (
    <div className='p-2 space-y-0.5'>
      {tripItems.map((item) => (
        <ActivityRow key={item.id} item={item} />
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useTripStats();
  const {
    data: pipeline,
    isLoading: pipelineLoading,
    error: pipelineError,
  } = usePipeline();

  // Memoize navigation items to prevent recreation on every render
  const navItems = useMemo(
    () => [
      {
        href: '/inbox',
        label: 'Inbox queue',
        sub: '5 pending',
        icon: Inbox,
        dot: '#d29922',
      },
      {
        href: '/workbench',
        label: 'Workbench',
        sub: 'analyze trip',
        icon: Briefcase,
        dot: '#58a6ff',
      },
      {
        href: '/owner/reviews',
        label: 'Reviews',
        sub: '2 awaiting',
        icon: CheckCircle2,
        dot: '#f85149',
      },
    ],
    []
  );

  // Memoize state meta entries for decision states
  const stateEntries = useMemo(
    () => Object.entries(STATE_META) as [StateKey, (typeof STATE_META)[StateKey]][],
    []
  );

  return (
    <main className='p-5 max-w-[1400px] mx-auto space-y-5'>
      <header className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-2xl font-semibold text-[#e6edf3]'>
            Operations Overview
          </h1>
          <p className='text-base text-[#a8b3c1] mt-0.5'>
            Waypoint OS · decision intelligence
          </p>
        </div>
        <Link
          href='/workbench'
          className='flex items-center gap-1.5 text-base text-[#58a6ff] hover:text-[#79b8ff] transition-colors'
        >
          Open workbench{' '}
          <ArrowRight className='h-4 w-4' aria-hidden='true' />
        </Link>
      </header>

      <div className='grid grid-cols-2 lg:grid-cols-4 gap-3'>
        <StatCard
          title='Active Trips'
          value={stats?.active ?? '—'}
          sub={stats ? '+3 this week' : 'Loading...'}
          icon={Briefcase}
          state='blue'
          isLoading={statsLoading}
          error={statsError}
        />
        <StatCard
          title='Pending Review'
          value={stats?.pendingReview ?? '—'}
          sub={stats ? '2 overdue' : 'Loading...'}
          icon={Clock}
          state='amber'
          isLoading={statsLoading}
          error={statsError}
        />
        <StatCard
          title='Ready to Book'
          value={stats?.readyToBook ?? '—'}
          sub={stats ? '+1 today' : 'Loading...'}
          icon={CheckCircle2}
          state='green'
          isLoading={statsLoading}
          error={statsError}
        />
        <StatCard
          title='Needs Attention'
          value={stats?.needsAttention ?? '—'}
          sub='action required'
          icon={AlertTriangle}
          state='red'
          isLoading={statsLoading}
          error={statsError}
        />
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
        <section className='lg:col-span-2 rounded-xl border border-[#1c2128] bg-[#0f1115] overflow-hidden'>
          <header className='flex items-center justify-between px-4 py-3 border-b border-[#1c2128]'>
            <div className='flex items-center gap-2'>
              <Activity
                className='h-4 w-4 text-[#8b949e]'
                aria-hidden='true'
              />
              <h2 className='text-sm font-semibold tracking-widest uppercase text-[#8b949e]'>
                Recent Trips
              </h2>
            </div>
            <Link
              href='/inbox'
              className='text-sm text-[#58a6ff] hover:text-[#79b8ff] flex items-center gap-1 transition-colors'
            >
              See all <ArrowRight className='h-4 w-4' aria-hidden='true' />
            </Link>
          </header>
          <RecentTrips />
        </section>

        <aside className='space-y-4'>
          <PipelineBar
            data={pipeline ?? null}
            isLoading={pipelineLoading}
            error={pipelineError}
          />
          <nav className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4' aria-label='Quick navigation'>
            <h2 className='text-sm font-semibold tracking-widest uppercase text-[#8b949e] mb-3'>
              Jump To
            </h2>
            <ul className='space-y-1'>
              {navItems.map((nav) => {
                const Icon = nav.icon;
                return (
                  <li key={nav.href}>
                    <Link
                      href={nav.href}
                      className='flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-[#161b22] transition-colors group'
                    >
                      <div className='h-8 w-8 rounded-lg bg-[#161b22] flex items-center justify-center shrink-0'>
                        <Icon
                          className='h-4 w-4 text-[#a8b3c1]'
                          aria-hidden='true'
                        />
                      </div>
                      <div className='flex-1 min-w-0'>
                        <div className='text-base text-[#e6edf3]'>
                          {nav.label}
                        </div>
                        <div
                          className='text-sm font-mono'
                          style={{ color: nav.dot }}
                        >
                          {nav.sub}
                        </div>
                      </div>
                      <ChevronRight
                        className='h-4 w-4 text-[#30363d] group-hover:text-[#8b949e] transition-colors'
                        aria-hidden='true'
                      />
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
          <section className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
            <h2 className='text-sm font-semibold tracking-widest uppercase text-[#8b949e]'>
              Decision States
            </h2>
            <div className='mt-3 space-y-2'>
              {stateEntries.map(([, meta]) => (
                <div key={meta.label} className='flex items-center gap-2'>
                  <span
                    className='h-1.5 w-1.5 rounded-full shrink-0'
                    style={{ background: meta.color }}
                    aria-hidden='true'
                  />
                  <span className='text-sm font-mono text-[#8b949e]'>
                    {meta.label}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
