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
import { memo, useMemo, useState, useCallback, useEffect } from 'react';
import {
  Briefcase,
  Clock,
  Users,
  Calendar,
  ChevronRight,
  AlertTriangle,
  LayoutGrid,
  Table2,
} from 'lucide-react';
import { useTrips } from '@/hooks/useTrips';
import { getTripRoute } from '@/lib/routes';
import { InlineLoading } from '@/components/ui/loading';
import { InlineError } from '@/components/error-boundary';
import type { Trip } from '@/lib/api-client';
import { WorkspaceTable, type SortField, type SortDirection } from './WorkspaceTable';

// ============================================================================
// DOMAIN BOUNDARY DEFINITION
// The "workspace" filter is now applied server-side via /api/trips?view=workspace.
// The canonical WORKSPACE_STATES set lives in the trips API route.
// This file does NOT duplicate that definition.
// ============================================================================

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
// VIEW PERSISTENCE
// ============================================================================

const VIEW_STORAGE_KEY = 'waypoint:workspace:view';

function getSavedView(): 'card' | 'table' {
  if (typeof window === 'undefined') return 'card';
  try {
    const saved = localStorage.getItem(VIEW_STORAGE_KEY);
    return saved === 'table' ? 'table' : 'card';
  } catch {
    return 'card';
  }
}

function saveView(view: 'card' | 'table') {
  try {
    localStorage.setItem(VIEW_STORAGE_KEY, view);
  } catch {
    /* ignore */
  }
}

// ============================================================================
// SORTING
// ============================================================================

function sortTrips(
  trips: Trip[],
  field: SortField,
  direction: SortDirection,
): Trip[] {
  const sorted = [...trips];

  sorted.sort((a, b) => {
    // Always promote blocked (red) trips to top when sorting by state
    if (field === 'state') {
      const aBlocked = a.state === 'red' ? 1 : 0;
      const bBlocked = b.state === 'red' ? 1 : 0;
      if (aBlocked !== bBlocked) {
        return bBlocked - aBlocked; // blocked (1) always before non-blocked (0)
      }
      // Within same blocked status, sort by state name
      if (a.state !== b.state) {
        return direction === 'asc'
          ? a.state.localeCompare(b.state)
          : b.state.localeCompare(a.state);
      }
    }

    if (field === 'destination') {
      return direction === 'asc'
        ? a.destination.localeCompare(b.destination)
        : b.destination.localeCompare(a.destination);
    }

    if (field === 'type') {
      return direction === 'asc'
        ? a.type.localeCompare(b.type)
        : b.type.localeCompare(a.type);
    }

    if (field === 'age') {
      // Extract numeric portion for comparison (e.g. "2h" vs "1d")
      const aNum = parseInt(a.age, 10) || 0;
      const bNum = parseInt(b.age, 10) || 0;
      return direction === 'asc' ? aNum - bNum : bNum - aNum;
    }

    return 0;
  });

  return sorted;
}

// ============================================================================
// WORKSPACE TRIP CARD
// ============================================================================

const WorkspaceCard = memo(function WorkspaceCard({ trip }: { trip: Trip }) {
  const meta = STATE_META[trip.state] ?? STATE_META.blue;
  const isBlocked = trip.state === 'red';

  return (
    <Link
      href={trip.id ? getTripRoute(trip.id) : '/workspace'}
      className='group block rounded-xl border border-[#1c2128] bg-[#0f1115] transition-all hover:border-[var(--border-default)] hover:bg-[#111418] overflow-hidden'
      style={isBlocked ? { borderColor: 'rgba(248,81,73,0.35)', background: 'rgba(248,81,73,0.04)' } : {}}
    >
      {/* State accent strip — top */}
      <div className='h-[2px] w-full' style={{ background: meta.color, opacity: 0.8 }} />

      <div className='p-4'>
        {/* Row 1: destination + state badge */}
        <div className='flex items-start justify-between gap-3 mb-1'>
          <div className='min-w-0'>
            <div className='flex items-center gap-1.5 mb-0.5'>
              {isBlocked && (
                <AlertTriangle className='h-3 w-3 text-[#f85149] shrink-0' aria-hidden='true' />
              )}
              <span
                className='text-[14px] font-semibold truncate leading-tight'
                style={{ color: '#f0f6fc', fontFamily: "'Outfit', system-ui, sans-serif" }}
              >
                {trip.destination}
              </span>
            </div>
            {trip.type && (
              <span className='text-[var(--ui-text-xs)] font-bold uppercase tracking-widest text-[var(--text-tertiary)]'>
                {trip.type}
              </span>
            )}
          </div>
          <span
            className='shrink-0 text-[var(--ui-text-xs)] font-bold uppercase tracking-wide px-2 py-0.5 rounded-md whitespace-nowrap'
            style={{ color: meta.color, background: meta.bg }}
          >
            {meta.label}
          </span>
        </div>

        {/* Row 2: metrics strip — dashed separator */}
        <div
          className='flex items-center gap-4 py-2 my-2 text-ui-xs'
          style={{ borderTop: '1px dashed rgba(48,54,61,0.6)', borderBottom: '1px dashed rgba(48,54,61,0.6)' }}
        >
          <div className='flex items-center gap-1 text-[var(--text-muted)]'>
            <Clock className='h-3 w-3' aria-hidden='true' />
            <span>{trip.age}</span>
          </div>
          {trip.party && (
            <>
              <div className='w-px h-3 bg-[#21262d]' />
              <div className='flex items-center gap-1 text-[var(--text-muted)]'>
                <Users className='h-3 w-3' aria-hidden='true' />
                <span>{trip.party} pax</span>
              </div>
            </>
          )}
          {trip.dateWindow && (
            <>
              <div className='w-px h-3 bg-[#21262d]' />
              <div className='flex items-center gap-1 text-[var(--text-muted)]'>
                <Calendar className='h-3 w-3' aria-hidden='true' />
                <span className='truncate max-w-[100px]'>{trip.dateWindow}</span>
              </div>
            </>
          )}
          {trip.budget && (
            <>
              <div className='w-px h-3 bg-[#21262d]' />
              <span className='font-mono text-[#58a6ff] font-semibold'>{trip.budget}</span>
            </>
          )}
        </div>

        {/* Row 3: ID + open cue */}
        <div className='flex items-center justify-between'>
          <span className='text-[var(--ui-text-xs)] font-mono text-[var(--border-default)]'>{trip.id}</span>
          <span className='flex items-center gap-1 text-[var(--ui-text-xs)] text-[var(--text-tertiary)] group-hover:text-[var(--text-muted)] transition-colors'>
            {isBlocked ? 'Action required' : 'Open'}
            <ChevronRight className='h-3.5 w-3.5' aria-hidden='true' />
          </span>
        </div>
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
        <Briefcase className='w-6 h-6 text-[var(--text-tertiary)]' aria-hidden='true' />
      </div>
      <p className='text-[#e6edf3] font-medium mb-1'>No active workspaces</p>
      <p className='text-ui-sm text-[var(--text-muted)] mb-6'>
        Trips appear here once you engage a lead from the inbox.
      </p>
      <div className='flex items-center justify-center gap-3'>
        <Link
          href='/inbox'
          className='inline-flex items-center gap-2 px-5 py-2.5 bg-[#58a6ff] text-[#0d1117] rounded-lg text-ui-sm font-semibold hover:bg-[#6eb5ff] transition-colors'
        >
          Browse Inbox
          <ChevronRight className='w-4 h-4' aria-hidden='true' />
        </Link>
        <Link
          href='/workbench'
          className='inline-flex items-center gap-2 px-5 py-2.5 border border-[var(--border-default)] text-[#e6edf3] rounded-lg text-ui-sm font-medium hover:bg-[#161b22] transition-colors'
        >
          New Inquiry
        </Link>
      </div>
    </div>
  );
}

// ============================================================================
// VIEW TOGGLE
// ============================================================================

function ViewToggle({
  view,
  onChange,
}: {
  view: 'card' | 'table';
  onChange: (v: 'card' | 'table') => void;
}) {
  return (
    <div className='flex items-center rounded-md border border-[#1c2128] bg-[#0a0d11] p-0.5'>
      <button
        type='button'
        onClick={() => onChange('card')}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-ui-xs font-medium transition-all ${
          view === 'card'
            ? 'bg-[#161b22] text-[#e6edf3]'
            : 'text-[var(--text-muted)] hover:text-[#e6edf3]'
        }`}
        aria-pressed={view === 'card'}
        aria-label='Card view'
      >
        <LayoutGrid className='h-3.5 w-3.5' aria-hidden='true' />
        <span className='hidden sm:inline'>Cards</span>
      </button>
      <button
        type='button'
        onClick={() => onChange('table')}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-ui-xs font-medium transition-all ${
          view === 'table'
            ? 'bg-[#161b22] text-[#e6edf3]'
            : 'text-[var(--text-muted)] hover:text-[#e6edf3]'
        }`}
        aria-pressed={view === 'table'}
        aria-label='Table view'
      >
        <Table2 className='h-3.5 w-3.5' aria-hidden='true' />
        <span className='hidden sm:inline'>Table</span>
      </button>
    </div>
  );
}

// ============================================================================
// PAGE
// ============================================================================

export default function WorkspacesPage() {
  const { data: workspaceTrips, isLoading, error, refetch } = useTrips({ view: 'workspace' });
  const [viewMode, setViewMode] = useState<'card' | 'table'>(getSavedView);
  const [sortField, setSortField] = useState<SortField>('state');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Persist view preference
  useEffect(() => {
    saveView(viewMode);
  }, [viewMode]);

  const blockedCount = useMemo(
    () => workspaceTrips.filter((t) => t.state === 'red').length,
    [workspaceTrips],
  );

  const sortedTrips = useMemo(
    () => sortTrips(workspaceTrips, sortField, sortDirection),
    [workspaceTrips, sortField, sortDirection],
  );

  const handleSort = useCallback((field: SortField) => {
    setSortField((current) => {
      if (current === field) {
        setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
        return current;
      }
      setSortDirection('asc');
      return field;
    });
  }, []);

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      {/* Header */}
      <header className='flex items-center justify-between pt-1 flex-wrap gap-3'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Workspaces</h1>
          <p className='text-ui-sm text-[var(--text-muted)] mt-0.5'>
            Active trips · engaged and in progress
          </p>
        </div>
        <div className='flex items-center gap-3'>
          {blockedCount > 0 && (
            <span className='flex items-center gap-1.5 text-ui-sm text-[#f85149]'>
              <AlertTriangle className='h-3.5 w-3.5' aria-hidden='true' />
              {blockedCount} blocked
            </span>
          )}
          <span className='text-ui-sm text-[var(--text-muted)]'>
            {isLoading ? 'Loading…' : `${workspaceTrips.length} active`}
          </span>
          <ViewToggle view={viewMode} onChange={setViewMode} />
        </div>
      </header>

      {/* Error */}
      {error && (
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-8 text-center'>
          <InlineError message='Failed to load workspaces' />
          <button
            type='button'
            onClick={() => refetch()}
            className='mt-4 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg text-ui-sm font-medium hover:bg-[#6eb5ff] transition-colors'
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

      {/* Empty state */}
      {!error && !isLoading && workspaceTrips.length === 0 && <EmptyWorkspace />}

      {/* Content */}
      {!error && workspaceTrips.length > 0 && (
        <>
          {viewMode === 'card' ? (
            <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
              {sortedTrips.map((trip) => (
                <WorkspaceCard key={trip.id} trip={trip} />
              ))}
            </div>
          ) : (
            <WorkspaceTable
              trips={sortedTrips}
              sortField={sortField}
              sortDirection={sortDirection}
              onSort={handleSort}
            />
          )}
        </>
      )}

    </div>
  );
}
