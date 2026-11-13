'use client';

/**
 * /trips - Active trips listing.
 *
 * Domain boundary (explicit, not ad-hoc):
 *   Inbox  = intake queue. Trips that haven't been acted on yet (state: 'blue').
 *   Workspace = execution queue. Trips that are actively being worked (state: 'green' | 'amber' | 'red').
 *
 * The workspace-status list now lives in `lib/trip-domain.ts` and is reused
 * by the trips and pipeline API routes. If client-side filtering returns here,
 * it should import that shared helper instead of redefining the statuses.
 */

import Link from 'next/link';
import { memo, useMemo, useState, useCallback, useEffect } from 'react';
import {
  Briefcase,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  LayoutGrid,
  Search,
  Table2,
  X,
} from 'lucide-react';
import { useTrips } from '@/hooks/useTrips';
import { InlineError } from '@/components/error-boundary';
import type { Trip } from '@/lib/api-client';
import { PlanningTripCard } from '@/components/workspace/PlanningTripCard';
import { getPlanningListSummary, getPlanningStageLabel } from '@/lib/planning-list-display';
import { getPlanningBriefStatus, hasPlanningBriefBlocker } from '@/lib/planning-status';
import { groupTripsByOverviewSignature } from '@/lib/trip-grouping';
import { isTripEscalated } from '@/lib/trip-lifecycle';
import { WORKSPACE_TRIP_STATUS_LIST } from '@/lib/trip-domain';
import { WorkspaceTable, type SortField, type SortDirection } from './WorkspaceTable';

const PAGE_SIZE = 24;

const WORKSPACE_STATUS_LABELS: Record<string, string> = {
  assigned: 'Assigned',
  in_progress: 'In progress',
  ready_to_quote: 'Ready to quote',
  ready_to_book: 'Ready to book',
  blocked: 'Blocked',
  active: 'In trip',
};

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
          href='/inquiries/new'
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

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense } from 'react';

export default function WorkspacesPage() {
  return (
    <Suspense fallback={<div className='p-6 text-[#8b949e]'>Loading trips in planning…</div>}>
      <WorkspacesPageWithSearchParams />
    </Suspense>
  );
}

function WorkspacesPageWithSearchParams() {
  const { push } = useRouter();
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);

  const initialQuery = getSearchParam('q') ?? '';
  const [searchInput, setSearchInput] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery.trim());

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchInput.trim());
    }, 250);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const rawStatusParam = getSearchParam('status');
  const activeStatus =
    rawStatusParam && WORKSPACE_TRIP_STATUS_LIST.includes(rawStatusParam as never) ? rawStatusParam : 'all';

  const parsedPage = Number.parseInt(getSearchParam('page') ?? '1', 10);
  const currentPage = Number.isFinite(parsedPage) && parsedPage >= 1 ? parsedPage : 1;
  const offset = (currentPage - 1) * PAGE_SIZE;

  const isUnfilteredAll = activeStatus === 'all' && !debouncedQuery;
  const {
    data: workspaceTrips,
    total,
    statusCounts,
    isLoading,
    error,
    refetch,
  } = useTrips({
    view: 'workspace',
    status: activeStatus !== 'all' ? activeStatus : undefined,
    limit: PAGE_SIZE,
    offset,
    q: debouncedQuery || undefined,
  });

  // Only fetch lightweight baseline counts when a filter/search is active so default
  // unfiltered /trips issues a single request and filtered tabs retain full counts.
  const { total: baselineTotalRaw, statusCounts: baselineStatusCountsRaw } = useTrips({
    view: 'workspace',
    limit: 1,
    enabled: !isUnfilteredAll,
  });

  const resolvedTotal = total || workspaceTrips.length;
  const workspaceTotalCount = isUnfilteredAll ? resolvedTotal : baselineTotalRaw || resolvedTotal;
  const tabCounts: Record<string, number> = isUnfilteredAll
    ? (statusCounts ?? {})
    : baselineStatusCountsRaw && Object.keys(baselineStatusCountsRaw).length > 0
      ? baselineStatusCountsRaw
      : (statusCounts ?? {});

  // URL state persistence with localStorage fallback
  const urlView = getSearchParam('view') as 'card' | 'table' | null;
  const [viewMode, setViewModeState] = useState<'card' | 'table'>(() => urlView || getSavedView());

  const [sortField, setSortField] = useState<SortField>(
    () => (getSearchParam('sort') as SortField) || 'stage',
  );
  const [sortDirection, setSortDirection] = useState<SortDirection>(
    () => (getSearchParam('dir') as SortDirection) || 'asc',
  );

  const updateParams = useCallback((updates: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, value]) => {
      if (value === null || value === '') params.delete(key);
      else params.set(key, value);
    });
    const nextQuery = params.toString();
    push(nextQuery ? `?${nextQuery}` : '?');
  }, [push, searchParams]);

  const setViewMode = useCallback((v: 'card' | 'table') => {
    setViewModeState(v);
    saveView(v);
    updateParams({ view: v });
  }, [updateParams]);

  const handleStatusChange = useCallback((nextStatus: string) => {
    updateParams({
      status: nextStatus === 'all' ? null : nextStatus,
      page: null,
    });
  }, [updateParams]);

  const handlePageChange = useCallback((nextPage: number) => {
    updateParams({ page: nextPage <= 1 ? null : String(nextPage) });
  }, [updateParams]);

  const handleSearchChange = useCallback((value: string) => {
    setSearchInput(value);
    updateParams({ q: value.trim() ? value : null, page: null });
  }, [updateParams]);

  const clearAllFilters = useCallback(() => {
    setSearchInput('');
    setDebouncedQuery('');
    updateParams({ q: null, status: null, filter: null, page: null });
  }, [updateParams]);

  const needsDetailsCount = useMemo(
    () => workspaceTrips.filter((trip) => hasPlanningBriefBlocker(trip)).length,
    [workspaceTrips],
  );

  // Escalated queue (register N-4): client-side slice over the active page.
  const escalatedTrips = useMemo(
    () => workspaceTrips.filter(isTripEscalated),
    [workspaceTrips],
  );
  const showEscalatedOnly = getSearchParam('filter') === 'escalated';
  const toggleEscalatedOnly = useCallback(() => {
    updateParams({ filter: showEscalatedOnly ? null : 'escalated' });
  }, [showEscalatedOnly, updateParams]);

  const sortedTrips = useMemo(
    () => sortTrips(workspaceTrips, sortField, sortDirection),
    [workspaceTrips, sortField, sortDirection],
  );
  const visibleTrips = useMemo(
    () => (showEscalatedOnly ? sortedTrips.filter(isTripEscalated) : sortedTrips),
    [sortedTrips, showEscalatedOnly],
  );
  const groupedTrips = useMemo(
    () => groupTripsByOverviewSignature(visibleTrips),
    [visibleTrips],
  );
  const isCardGrouped = groupedTrips.length < visibleTrips.length;
  const totalPages = Math.max(1, Math.ceil(resolvedTotal / PAGE_SIZE));
  const hasActiveFilter = Boolean(debouncedQuery || activeStatus !== 'all' || showEscalatedOnly);
  const pageStart = resolvedTotal === 0 ? 0 : Math.min(offset + 1, resolvedTotal);
  const pageEnd = Math.min(offset + workspaceTrips.length, resolvedTotal);

  const handleSort = useCallback((field: SortField) => {
    setSortField((current) => {
      const nextDir: SortDirection = current === field && sortDirection === 'asc' ? 'desc' : 'asc';
      setSortDirection(nextDir);
      updateParams({ sort: field, dir: nextDir });
      return field;
    });
  }, [sortDirection, updateParams]);

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      {/* Header */}
      <header className='flex items-center justify-between pt-1 flex-wrap gap-3'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Trips in Planning</h1>
          <p className='text-ui-sm text-[var(--text-muted)] mt-0.5'>
            Trips your team is actively working on
          </p>
        </div>
        <div className='flex items-center gap-3 flex-wrap'>
          {needsDetailsCount > 0 && (
            <span
              className='flex items-center gap-1.5 text-ui-sm text-[#d29922]'
              title={`${needsDetailsCount} of ${workspaceTrips.length} trips shown on this page still need required brief details`}
            >
              <AlertTriangle className='size-3.5' aria-hidden='true' />
              {needsDetailsCount} of {workspaceTrips.length} on page need details
            </span>
          )}
          {escalatedTrips.length > 0 && (
            <button
              type='button'
              onClick={toggleEscalatedOnly}
              aria-pressed={showEscalatedOnly}
              className='flex items-center gap-1.5 text-ui-sm px-2 py-0.5 rounded-md font-medium'
              style={{
                color: showEscalatedOnly ? '#0d1117' : '#f85149',
                background: showEscalatedOnly ? '#f85149' : 'rgba(248,81,73,0.08)',
                border: '1px solid rgba(248,81,73,0.22)',
              }}
            >
              <AlertTriangle className='size-3.5' aria-hidden='true' />
              {escalatedTrips.length} escalated
            </button>
          )}
          <span className='text-ui-sm font-medium text-[#e6edf3] tabular-nums' data-testid='trips-total-count'>
            {isLoading && workspaceTotalCount === 0
              ? 'Loading…'
              : `${workspaceTotalCount.toLocaleString('en-IN')} in planning`}
          </span>
          <ViewToggle view={viewMode} onChange={setViewMode} />
        </div>
      </header>

      {/* Search + Stage Filter Bar */}
      <div className='flex flex-col lg:flex-row lg:items-center justify-between gap-3 rounded-xl border border-[#1c2128] bg-[#0f1115] p-3'>
        <div className='relative flex-1 max-w-md'>
          <Search className='size-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none' aria-hidden='true' />
          <input
            type='search'
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder='Search destination, client, or ref…'
            aria-label='Search trips in planning'
            className='w-full bg-[#0a0d11] border border-[#1c2128] rounded-lg pl-8 pr-8 py-1.5 text-ui-sm text-[#e6edf3] placeholder:text-[var(--text-muted)] focus:border-[#58a6ff] focus:outline-none'
          />
          {searchInput && (
            <button
              type='button'
              onClick={() => handleSearchChange('')}
              aria-label='Clear search'
              className='absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[#e6edf3]'
            >
              <X className='size-3.5' />
            </button>
          )}
        </div>

        <div className='flex items-center gap-1.5 flex-wrap' role='group' aria-label='Filter by planning status'>
          <button
            type='button'
            onClick={() => handleStatusChange('all')}
            aria-pressed={activeStatus === 'all'}
            className={`px-2.5 py-1 rounded-md text-ui-xs font-medium transition-colors tabular-nums ${
              activeStatus === 'all'
                ? 'bg-[#161b22] text-[#e6edf3] border border-[#30363d]'
                : 'text-[var(--text-muted)] hover:text-[#e6edf3] border border-transparent'
            }`}
          >
            All ({workspaceTotalCount.toLocaleString('en-IN')})
          </button>
          {WORKSPACE_TRIP_STATUS_LIST.map((st) => {
            const count = tabCounts[st] ?? 0;
            if (count === 0 && activeStatus !== st) return null;
            const isSelected = activeStatus === st;
            return (
              <button
                key={st}
                type='button'
                onClick={() => handleStatusChange(st)}
                aria-pressed={isSelected}
                className={`px-2.5 py-1 rounded-md text-ui-xs font-medium transition-colors tabular-nums ${
                  isSelected
                    ? 'bg-[#161b22] text-[#58a6ff] border border-[#58a6ff]/40'
                    : 'text-[var(--text-muted)] hover:text-[#e6edf3] border border-transparent'
                }`}
              >
                {WORKSPACE_STATUS_LABELS[st] ?? st} ({count.toLocaleString('en-IN')})
              </button>
            );
          })}
        </div>
      </div>

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
          {['trips-skeleton-1', 'trips-skeleton-2', 'trips-skeleton-3'].map((skeletonKey) => (
            <div
              key={skeletonKey}
              className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 space-y-3'
            >
              <div className='h-4 bg-[#161b22] rounded w-1/2 animate-pulse' />
              <div className='h-3 bg-[#161b22] rounded w-1/3 animate-pulse' />
            </div>
          ))}
        </div>
      )}

      {/* Filtered empty state */}
      {!error && !isLoading && visibleTrips.length === 0 && hasActiveFilter && (
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-10 text-center space-y-3'>
          <p className='text-[#e6edf3] font-medium'>No matching trips in planning</p>
          <p className='text-ui-sm text-[var(--text-muted)]'>
            Try clearing your search query or switching status filter.
          </p>
          <button
            type='button'
            onClick={clearAllFilters}
            className='px-4 py-2 bg-[#161b22] border border-[#30363d] text-[#e6edf3] rounded-lg text-ui-sm font-medium hover:bg-[#21262d] transition-colors'
          >
            Clear filters
          </button>
        </div>
      )}

      {/* True Empty workspace state */}
      {!error && !isLoading && visibleTrips.length === 0 && !hasActiveFilter && <EmptyWorkspace />}

      {/* Content */}
      {!error && visibleTrips.length > 0 && (
        <>
          {viewMode === 'card' ? (
            <div className='space-y-4'>
              {isCardGrouped ? (
                <p className='text-ui-sm text-[var(--text-muted)]'>
                  {resolvedTotal > visibleTrips.length
                    ? `Showing ${groupedTrips.length.toLocaleString('en-IN')} grouped cards from ${visibleTrips.length.toLocaleString('en-IN')} trips on this page (${resolvedTotal.toLocaleString('en-IN')} total).`
                    : `Showing ${groupedTrips.length.toLocaleString('en-IN')} grouped cards from ${visibleTrips.length.toLocaleString('en-IN')} trips.`}
                </p>
              ) : null}
              {groupedTrips.length === 1 ? (
                <div className='grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4 items-start'>
                  <PlanningTripCard trip={groupedTrips[0]!.primaryTrip} variant='workspace' similarTripCount={groupedTrips[0]!.count} />
                  <SingleTripNextStepPanel trip={groupedTrips[0]!.primaryTrip} />
                </div>
              ) : (
                <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
                  {groupedTrips.map((group) => (
                    <PlanningTripCard key={group.key} trip={group.primaryTrip} variant='workspace' similarTripCount={group.count} />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <WorkspaceTable
              trips={visibleTrips}
              sortField={sortField}
              sortDirection={sortDirection}
              onSort={handleSort}
            />
          )}

          {/* Pagination */}
          {resolvedTotal > PAGE_SIZE && (
            <div className='flex items-center justify-between gap-3 pt-2 border-t border-[#1c2128] text-ui-sm text-[var(--text-muted)]'>
              <span className='tabular-nums'>
                Showing {pageStart.toLocaleString('en-IN')}–{pageEnd.toLocaleString('en-IN')} of{' '}
                {resolvedTotal.toLocaleString('en-IN')} {hasActiveFilter ? 'matching' : 'planning'} trips
              </span>
              <div className='flex items-center gap-2'>
                <button
                  type='button'
                  disabled={currentPage <= 1}
                  onClick={() => handlePageChange(currentPage - 1)}
                  className='inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#1c2128] bg-[#0f1115] text-[#e6edf3] text-ui-xs font-medium hover:bg-[#161b22] disabled:opacity-40 disabled:pointer-events-none'
                >
                  <ChevronLeft className='size-3.5' aria-hidden='true' />
                  Previous
                </button>
                <span className='text-ui-xs tabular-nums px-2'>
                  Page {currentPage.toLocaleString('en-IN')} of {totalPages.toLocaleString('en-IN')}
                </span>
                <button
                  type='button'
                  disabled={currentPage >= totalPages}
                  onClick={() => handlePageChange(currentPage + 1)}
                  className='inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#1c2128] bg-[#0f1115] text-[#e6edf3] text-ui-xs font-medium hover:bg-[#161b22] disabled:opacity-40 disabled:pointer-events-none'
                >
                  Next
                  <ChevronRight className='size-3.5' aria-hidden='true' />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
