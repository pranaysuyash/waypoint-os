'use client';

import Link from 'next/link';
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

function StatCard({
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
          <span className='text-[11px] font-semibold tracking-widest uppercase text-[#6e7681]'>
            {title}
          </span>
          <AlertTriangle className='h-3.5 w-3.5 text-[#f85149]' />
        </div>
        <span className='text-[11px] text-[#f85149]'>Failed to load</span>
      </div>
    );
  }

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 flex flex-col gap-3 hover:border-[#30363d] transition-colors'>
      <div className='flex items-center justify-between'>
        <span className='text-[11px] font-semibold tracking-widest uppercase text-[#6e7681]'>
          {title}
        </span>
        <div
          className='h-7 w-7 rounded-lg flex items-center justify-center'
          style={{ background: meta.bg }}
        >
          {isLoading ? (
            <div className='w-3 h-3 border-2 border-[#0d1117]/30 border-t-[#0d1117] rounded-full animate-spin' />
          ) : (
            <Icon className='h-3.5 w-3.5' style={{ color: meta.color }} />
          )}
        </div>
      </div>
      <span
        className='text-3xl font-bold tabular-nums'
        style={{ color: meta.color }}
      >
        {isLoading ? '—' : value}
      </span>
      <span className='text-[11px] text-[#484f58] font-mono'>{sub}</span>
    </div>
  );
}

function PipelineBar({
  data,
  isLoading,
  error,
}: {
  data: Array<{ label: string; count: number }> | null;
  isLoading: boolean;
  error: Error | null;
}) {
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
          <span className='text-[11px] font-semibold tracking-widest uppercase text-[#6e7681]'>
            Pipeline
          </span>
          <span className='text-[11px] font-mono text-[#484f58]'>
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

  const total = data.reduce((s, x) => s + x.count, 0);

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
      <div className='flex items-center justify-between mb-3'>
        <span className='text-[11px] font-semibold tracking-widest uppercase text-[#6e7681]'>
          Pipeline
        </span>
        <span className='text-[11px] font-mono text-[#484f58]'>
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
            <span className='text-[12px] font-semibold tabular-nums text-[#e6edf3]'>
              {stage.count}
            </span>
            <span className='text-[10px] text-[#484f58] truncate'>
              {stage.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActivityRow({
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
          <span className='text-[13px] font-medium text-[#e6edf3] truncate'>
            {item.destination}
          </span>
          <span className='text-[11px] text-[#484f58]'>{item.type}</span>
        </div>
        <div className='text-[11px] font-mono text-[#6e7681]'>{item.id}</div>
      </div>
      <div className='flex items-center gap-2 shrink-0'>
        <span
          className='text-[10px] font-mono px-2 py-0.5 rounded-md'
          style={{ color: meta.color, background: meta.bg }}
        >
          {meta.label}
        </span>
        <span className='text-[11px] text-[#484f58]'>{item.age}</span>
        <ChevronRight
          className='h-3 w-3 text-[#30363d] group-hover:text-[#6e7681] transition-colors'
          aria-hidden='true'
        />
      </div>
    </Link>
  );
}

function RecentTrips() {
  const { data: trips, isLoading, error } = useTrips({ limit: 5 });

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
          <div key={i} className='h-14 bg-[#161b22] rounded-lg animate-pulse' />
        ))}
      </div>
    );
  }

  if (!trips || trips.length === 0) {
    return (
      <div className='p-4 text-center text-[12px] text-[#6e7681]'>
        No recent trips
      </div>
    );
  }

  return (
    <div className='p-2 space-y-0.5'>
      {trips.map((trip) => (
        <ActivityRow
          key={trip.id}
          item={{
            id: trip.id,
            destination: trip.destination,
            type: trip.type,
            state: trip.state,
            age: trip.age,
          }}
        />
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

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      <div className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-[15px] font-semibold text-[#e6edf3]'>
            Operations Overview
          </h1>
          <p className='text-[12px] text-[#6e7681] mt-0.5'>
            Travel Agency Agent · decision intelligence
          </p>
        </div>
        <Link
          href='/workbench'
          className='flex items-center gap-1.5 text-[12px] text-[#58a6ff] hover:text-[#79b8ff] transition-colors'
        >
          Open workbench{' '}
          <ArrowRight className='h-3.5 w-3.5' aria-hidden='true' />
        </Link>
      </div>

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
        <div className='lg:col-span-2 rounded-xl border border-[#1c2128] bg-[#0f1115] overflow-hidden'>
          <div className='flex items-center justify-between px-4 py-3 border-b border-[#1c2128]'>
            <div className='flex items-center gap-2'>
              <Activity
                className='h-3.5 w-3.5 text-[#6e7681]'
                aria-hidden='true'
              />
              <span className='text-[11px] font-semibold tracking-widest uppercase text-[#6e7681]'>
                Recent Trips
              </span>
            </div>
            <Link
              href='/inbox'
              className='text-[11px] text-[#58a6ff] hover:text-[#79b8ff] flex items-center gap-1 transition-colors'
            >
              See all <ArrowRight className='h-3 w-3' aria-hidden='true' />
            </Link>
          </div>
          <RecentTrips />
        </div>

        <div className='space-y-4'>
          <PipelineBar
            data={pipeline ?? null}
            isLoading={pipelineLoading}
            error={pipelineError}
          />
          <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
            <span className='text-[11px] font-semibold tracking-widest uppercase text-[#6e7681]'>
              Jump To
            </span>
            <div className='mt-3 space-y-1'>
              {[
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
              ].map((nav) => {
                const Icon = nav.icon;
                return (
                  <Link
                    key={nav.href}
                    href={nav.href}
                    className='flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-[#161b22] transition-colors group'
                  >
                    <div className='h-7 w-7 rounded-lg bg-[#161b22] flex items-center justify-center shrink-0'>
                      <Icon
                        className='h-3.5 w-3.5 text-[#8b949e]'
                        aria-hidden='true'
                      />
                    </div>
                    <div className='flex-1 min-w-0'>
                      <div className='text-[13px] text-[#e6edf3]'>
                        {nav.label}
                      </div>
                      <div
                        className='text-[11px] font-mono'
                        style={{ color: nav.dot }}
                      >
                        {nav.sub}
                      </div>
                    </div>
                    <ChevronRight
                      className='h-3.5 w-3.5 text-[#30363d] group-hover:text-[#6e7681] transition-colors'
                      aria-hidden='true'
                    />
                  </Link>
                );
              })}
            </div>
          </div>
          <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
            <span className='text-[11px] font-semibold tracking-widest uppercase text-[#6e7681]'>
              Decision States
            </span>
            <div className='mt-3 space-y-2'>
              {(
                Object.entries(STATE_META) as [
                  StateKey,
                  (typeof STATE_META)[StateKey],
                ][]
              ).map(([, meta]) => (
                <div key={meta.label} className='flex items-center gap-2'>
                  <span
                    className='h-1.5 w-1.5 rounded-full shrink-0'
                    style={{ background: meta.color }}
                    aria-hidden='true'
                  />
                  <span className='text-[12px] font-mono text-[#6e7681]'>
                    {meta.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
