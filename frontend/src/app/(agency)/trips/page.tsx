'use client';

/**
 * /trips - Active trips listing.
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
 * from lifecycle status. For now, `assigned` and `in_progress` are the
 * canonical workspace-entry statuses.
 */

import Link from 'next/link';
import { memo, useMemo, useState, useCallback, useEffect } from 'react';
import {
  Briefcase,
  ChevronRight,
  AlertTriangle,
  LayoutGrid,
  Table2,
} from 'lucide-react';
import { useTrips } from '@/hooks/useTrips';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { InlineError } from '@/components/error-boundary';
import type { Trip } from '@/lib/api-client';
import { PlanningTripCard } from '@/components/workspace/PlanningTripCard';
import { getPlanningListSummary, getPlanningStageLabel } from '@/lib/planning-list-display';
import { getPlanningBriefStatus, hasPlanningBriefBlocker } from '@/lib/planning-status';
import { WorkspaceTable, type SortField, type SortDirection } from './WorkspaceTable';

// ============================================================================
// DOMAIN BOUNDARY DEFINITION
// The "workspace" filter is now applied server-side via /api/trips?view=workspace.
// The canonical workspace filter lives in the trips API route.
// This file does NOT duplicate that definition.
// ============================================================================

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
  const stageRank = (trip: Trip): number => {
    const stage = getPlanningStageLabel(trip);
    const brief = getPlanningBriefStatus(trip);
    const baseRank: Record<string, number> = {
      Intake: 1,
      Details: 2,
      Options: 3,
      'Quote Review': 4,
      Output: 5,
    };

    const rank = baseRank[stage] ?? 99;
    // Keep required-detail blockers grouped at the front of their stage.
    if (brief === 'missing_required_details') return rank - 0.25;
    if (brief === 'missing_recommended_details') return rank + 0.1;
    return rank;
  };

  sorted.sort((a, b) => {
    if (field === 'stage') {
      const aRank = stageRank(a);
      const bRank = stageRank(b);
      if (aRank !== bRank) {
        return direction === 'asc' ? aRank - bRank : bRank - aRank;
      }

      // Tie-breaker: more urgent visual tone first (red -> amber -> blue -> green)
      const urgency: Record<string, number> = { red: 0, amber: 1, blue: 2, green: 3 };
      const aUrgency = urgency[a.state] ?? 9;
      const bUrgency = urgency[b.state] ?? 9;
      if (aUrgency !== bUrgency) {
        return aUrgency - bUrgency;
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

const SingleTripNextStepPanel = memo(function SingleTripNextStepPanel({ trip }: { trip: Trip }) {
  const summary = getPlanningListSummary(trip);

  return (
    <aside
      className='rounded-2xl border p-5 space-y-4'
      style={{
        background: 'rgba(15,17,21,0.92)',
        borderColor: 'rgba(48,54,61,0.9)',
      }}
    >
      <div>
        <p className='text-[12px] font-semibold uppercase tracking-[0.16em]' style={{ color: 'var(--text-tertiary)' }}>
          Next step
        </p>
        <h2 className='mt-2 text-[18px] font-semibold' style={{ color: 'var(--text-primary)' }}>
          {summary.missingFields.length > 0 ? 'Confirm missing customer details.' : 'Continue planning this trip.'}
        </h2>
      </div>

      {summary.missingFields.length > 0 && (
        <div className='rounded-xl border px-4 py-3' style={{ borderColor: 'rgba(48,54,61,0.85)', background: 'rgba(255,255,255,0.02)' }}>
          <p className='text-[12px] font-semibold uppercase tracking-[0.14em]' style={{ color: 'var(--text-tertiary)' }}>
            Missing
          </p>
          <ul className='mt-3 space-y-2 text-[14px]' style={{ color: 'var(--text-primary)' }}>
            {summary.missingFields.map((field) => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        </div>
      )}

      <Link
        href={summary.action.href}
        className='inline-flex items-center gap-1.5 text-[14px] font-medium'
        style={{ color: 'var(--accent-blue)' }}
      >
        {summary.action.label}
        <ChevronRight className='size-4' aria-hidden='true' />
      </Link>
    </aside>
  );
});

// ============================================================================
// EMPTY STATE
// ============================================================================

function EmptyWorkspace() {
  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-12 text-center'>
      <div className='size-12 rounded-full bg-[#161b22] flex items-center justify-center mx-auto mb-4'>
        <Briefcase className='size-6 text-[var(--text-tertiary)]' aria-hidden='true' />
      </div>
      <p className='text-[#e6edf3] font-medium mb-1'>No trips in planning</p>
      <p className='text-ui-sm text-[var(--text-muted)] mb-6'>
        Trips appear here once someone starts planning from Lead Inbox.
      </p>
      <div className='flex items-center justify-center gap-3'>
        <Link
          href='/inbox'
          className='inline-flex items-center gap-2 px-5 py-2.5 bg-[#58a6ff] text-[#0d1117] rounded-lg text-ui-sm font-semibold hover:bg-[#6eb5ff] transition-colors'
        >
          Review Lead Inbox
          <ChevronRight className='size-4' aria-hidden='true' />
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
        <LayoutGrid className='size-3.5' aria-hidden='true' />
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
        <Table2 className='size-3.5' aria-hidden='true' />
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
  const [sortField, setSortField] = useState<SortField>('stage');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Persist view preference
  useEffect(() => {
    saveView(viewMode);
  }, [viewMode]);

  const needsDetailsCount = useMemo(
    () => workspaceTrips.filter((trip) => hasPlanningBriefBlocker(trip)).length,
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
      <BackToOverviewLink />
      {/* Header */}
      <header className='flex items-center justify-between pt-1 flex-wrap gap-3'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Trips in Planning</h1>
          <p className='text-ui-sm text-[var(--text-muted)] mt-0.5'>
            Trips your team is actively working on
          </p>
        </div>
        <div className='flex items-center gap-3'>
          {needsDetailsCount > 0 && (
            <span className='flex items-center gap-1.5 text-ui-sm text-[#d29922]'>
              <AlertTriangle className='size-3.5' aria-hidden='true' />
              {needsDetailsCount} needs details
            </span>
          )}
          <span className='text-ui-sm text-[var(--text-muted)]'>
            {isLoading ? 'Loading…' : `${workspaceTrips.length} in planning`}
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
            sortedTrips.length === 1 ? (
              <div className='grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4 items-start'>
                <PlanningTripCard trip={sortedTrips[0]!} />
                <SingleTripNextStepPanel trip={sortedTrips[0]!} />
              </div>
            ) : (
              <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
                {sortedTrips.map((trip) => (
                  <PlanningTripCard key={trip.id} trip={trip} />
                ))}
              </div>
            )
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
