'use client';

/**
 * /workspace — Active trip workspaces listing.
 *
 * Domain boundary (explicit, not ad-hoc):
 *   Inbox  = intake queue. Trips that haven't been acted on yet (state: 'blue').
 *   Workspace = execution queue. Trips that are actively being worked (state: 'green' | 'amber' | 'red').
 *
 * The filter constant below is the single authoritative definition.
 * Both this page and any future API filter params should reference it.
 *
 * TODO (Wave 2+): Move this filter to a shared lib/trip-domain.ts once the
 * backend trip model exposes an explicit stage/phase field rather than inferring
 * from decision state. For now, decision state is the best available proxy.
 */

import Link from 'next/link';
import { memo, useMemo } from 'react';
import {
  Briefcase,
  Clock,
  Users,
  Calendar,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';
import { useTrips } from '@/hooks/useTrips';
import { getTripRoute } from '@/lib/routes';
import { InlineLoading } from '@/components/ui/loading';
import { InlineError } from '@/components/error-boundary';;
import type { Trip } from '@/lib/api-client';

// ============================================================================
// DOMAIN BOUNDARY DEFINITION
// Decision states that indicate a trip is actively in the execution queue.
// Change here propagates everywhere — do not hardcode elsewhere.
// ============================================================================

const IN_WORKSPACE_STATES = new Set(['green', 'amber', 'red'] as const);

function isInWorkspace(trip: Trip): boolean {
  return IN_WORKSPACE_STATES.has(trip.state as 'green' | 'amber' | 'red');
}

// ============================================================================
// STATE METADATA
// ============================================================================

const STATE_META: Record<string, { color: string; bg: string; label: string }> = {
  green:  { color: '#3fb950', bg: 'rgba(63,185,80,0.12)',   label: 'Ready' },
  amber:  { color: '#d29922', bg: 'rgba(210,153,34,0.12)',  label: 'In Progress' },
  red:    { color: '#f85149', bg: 'rgba(248,81,73,0.12)',   label: 'Needs Review' },
  blue:   { color: '#58a6ff', bg: 'rgba(88,166,255,0.12)',  label: 'Awaiting Info' },
};

// ============================================================================
// WORKSPACE TRIP CARD
// ============================================================================

const WorkspaceCard = memo(function WorkspaceCard({ trip }: { trip: Trip }) {
  const meta = STATE_META[trip.state] ?? STATE_META.blue;
  const isBlocked = trip.state === 'red';

  return (
    <Link
      href={getTripRoute(trip.id)}
      className={`group block rounded-xl border p-4 transition-all hover:border-[#30363d] ${
        isBlocked
          ? 'border-[#f85149]/30 bg-[#f85149]/5'
          : 'border-[#1c2128] bg-[#0f1115]'
      }`}
    >
      <div className='flex items-start justify-between gap-3 mb-2'>
        <div className='flex items-center gap-2 min-w-0'>
          {isBlocked && (
            <AlertTriangle className='h-3.5 w-3.5 text-[#f85149] shrink-0' aria-hidden='true' />
          )}
          <span className='text-[14px] font-semibold text-[#e6edf3] truncate'>
            {trip.destination}
          </span>
          <span className='text-xs text-[#8b949e]'>{trip.type}</span>
        </div>
        <span
          className='shrink-0 text-xs font-mono font-semibold px-2 py-0.5 rounded-md whitespace-nowrap'
          style={{ color: meta.color, background: meta.bg }}
        >
          {meta.label}
        </span>
      </div>

      <div className='flex items-center gap-4 text-xs text-[#8b949e] mb-3'>
        <span className='flex items-center gap-1'>
          <Clock className='h-3 w-3' aria-hidden='true' /> {trip.age}
        </span>
        <span className='font-mono text-[#484f58]'>{trip.id}</span>
      </div>

      <div className='flex items-center justify-between'>
        <span className='text-xs text-[#8b949e]'>
          {isBlocked ? 'Action required' : 'Open workspace'}
        </span>
        <ChevronRight
          className='h-4 w-4 text-[#30363d] group-hover:text-[#8b949e] transition-colors'
          aria-hidden='true'
        />
      </div>
    </Link>
  );
});

// ============================================================================
// EMPTY STATE
// ============================================================================

function EmptyWorkspace() {
  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-12 text-center'>
      <div className='w-12 h-12 rounded-full bg-[#161b22] flex items-center justify-center mx-auto mb-4'>
        <Briefcase className='w-6 h-6 text-[#484f58]' aria-hidden='true' />
      </div>
      <p className='text-[#e6edf3] font-medium mb-1'>No active workspaces</p>
      <p className='text-sm text-[#8b949e] mb-4'>
        Trips move here once they&apos;ve been engaged.
        New leads start in Inbox.
      </p>
      <Link
        href='/inbox'
        className='inline-flex items-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg text-sm font-medium hover:bg-[#6eb5ff] transition-colors'
      >
        Go to Inbox
        <ChevronRight className='w-4 h-4' aria-hidden='true' />
      </Link>
    </div>
  );
}

// ============================================================================
// PAGE
// ============================================================================

export default function WorkspacesPage() {
  const { data: allTrips, isLoading, error, refetch } = useTrips();

  const workspaceTrips = useMemo(
    () => allTrips.filter(isInWorkspace),
    [allTrips],
  );

  const blockedCount = useMemo(
    () => workspaceTrips.filter((t) => t.state === 'red').length,
    [workspaceTrips],
  );

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      {/* Header */}
      <header className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-xl font-semibold text-[#e6edf3]'>Workspaces</h1>
          <p className='text-sm text-[#8b949e] mt-0.5'>
            Active trips · engaged and in progress
          </p>
        </div>
        <div className='flex items-center gap-4'>
          {blockedCount > 0 && (
            <span className='flex items-center gap-1.5 text-sm text-[#f85149]'>
              <AlertTriangle className='h-3.5 w-3.5' aria-hidden='true' />
              {blockedCount} blocked
            </span>
          )}
          <span className='text-sm text-[#8b949e]'>
            {isLoading ? 'Loading…' : `${workspaceTrips.length} active`}
          </span>
        </div>
      </header>

      {/* Error */}
      {error && (
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-8 text-center'>
          <InlineError message='Failed to load workspaces' />
          <button
            type='button'
            onClick={() => refetch()}
            className='mt-4 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg text-sm font-medium hover:bg-[#6eb5ff] transition-colors'
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && workspaceTrips.length === 0 && (
        <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 space-y-3'
            >
              <div className='h-4 bg-[#161b22] rounded w-1/2 animate-pulse' />
              <div className='h-3 bg-[#161b22] rounded w-1/3 animate-pulse' />
            </div>
          ))}
        </div>
      )}

      {/* Grid */}
      {!error && !isLoading && workspaceTrips.length === 0 && <EmptyWorkspace />}

      {!error && workspaceTrips.length > 0 && (
        <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
          {workspaceTrips.map((trip) => (
            <WorkspaceCard key={trip.id} trip={trip} />
          ))}
        </div>
      )}

      {/* Cross-link to inbox for context */}
      {!error && !isLoading && (
        <div className='flex items-center gap-2 text-sm text-[#484f58]'>
          <span>New leads waiting to be engaged →</span>
          <Link href='/inbox' className='text-[#58a6ff] hover:text-[#79b8ff] transition-colors'>
            Inbox
          </Link>
        </div>
      )}
    </div>
  );
}
