'use client';

import { useState, useCallback, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Briefcase,
  ChevronDown,
  ChevronUp,
  Users,
  Calendar,
  Wallet,
  AlertTriangle,
  UserPlus,
  Search,
  Flag,
  ArrowUpDown,
  Download,
} from 'lucide-react';
import { useInboxTrips } from '@/hooks/useGovernance';
import { InlineError } from '@/components/error-boundary';
import { tripMatchesQuery } from '@/lib/inbox-helpers';
import { TripCard } from '@/components/inbox/TripCard';
import { InboxFilterBar, type FilterKey } from '@/components/inbox/InboxFilterBar';
import { InboxEmptyState } from '@/components/inbox/InboxEmptyState';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import type { InboxTrip } from '@/types/governance';
type SortKey = 'priority' | 'destination' | 'value' | 'party' | 'dates' | 'sla';
type SortDirection = 'asc' | 'desc';

function leadCountLabel(count: number): string {
  return `${count} ${count === 1 ? 'lead' : 'leads'} total`;
}

const SORT_OPTIONS: Record<SortKey, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  priority: { label: 'Priority', icon: Flag },
  destination: { label: 'Destination', icon: Briefcase },
  value: { label: 'Value', icon: Wallet },
  party: { label: 'Party Size', icon: Users },
  dates: { label: 'Dates', icon: Calendar },
  sla: { label: 'SLA Status', icon: AlertTriangle },
};

// ============================================================================
// BULK ACTIONS TOOLBAR
// ============================================================================

function BulkActionsToolbar({
  selectedCount,
  onClearSelection,
  onAssign,
  onExport,
  agents,
}: {
  selectedCount: number;
  onClearSelection: () => void;
  onAssign: (agentId: string) => void;
  onExport: () => void;
  agents: { id: string; name: string }[];
}) {
  const [showAssignDropdown, setShowAssignDropdown] = useState(false);

  return (
    <div className='flex items-center justify-between py-2 px-3 bg-[#161b22] rounded-lg border border-[#30363d]'>
      <div className='flex items-center gap-3'>
        <span className='text-ui-sm text-[#e6edf3]'>
          <strong>{selectedCount}</strong> trips selected
        </span>
        <button
          onClick={onClearSelection}
          className='text-ui-xs text-[#8b949e] hover:text-[#e6edf3]'
        >
          Clear
        </button>
      </div>

      <div className='flex items-center gap-2'>
        <div className='relative'>
          <button
            onClick={() => setShowAssignDropdown(!showAssignDropdown)}
            className='flex items-center gap-1.5 px-3 py-1.5 bg-[#58a6ff] text-[#0d1117] rounded-lg text-ui-sm font-medium hover:bg-[#6eb5ff] transition-colors'
          >
            <UserPlus className='w-4 h-4' />
            Assign to...
          </button>
          
          {showAssignDropdown && (
            <div className='absolute top-full right-0 mt-1 w-48 bg-[#0f1115] border border-[#30363d] rounded-lg shadow-xl z-10'>
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => {
                    onAssign(agent.id);
                    setShowAssignDropdown(false);
                  }}
                  className='w-full flex items-center gap-2 px-3 py-2 text-left text-ui-sm text-[#e6edf3] hover:bg-[#161b22] first:rounded-t-lg last:rounded-b-lg'
                >
                  <div className='h-6 w-6 rounded-full bg-[#58a6ff]/20 flex items-center justify-center text-[#58a6ff] text-ui-xs font-bold'>
                    {agent.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>{agent.name}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={onExport}
          className='flex items-center gap-1.5 px-3 py-1.5 bg-[#161b22] text-[#8b949e] rounded-lg text-ui-sm hover:text-[#e6edf3] transition-colors'
        >
          <Download className='w-4 h-4' />
          Export
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function InboxPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URL Persistence Sync
  const activeFilter = (searchParams.get('filter') as FilterKey) || 'all';
  const sortBy = (searchParams.get('sort') as SortKey) || 'priority';
  const sortDirection = (searchParams.get('dir') as SortDirection) || 'desc';
  const searchQuery = searchParams.get('q') || '';

  const updateParams = useCallback((updates: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, value]) => {
      if (value === null) params.delete(key);
      else params.set(key, value);
    });
    router.push(`?${params.toString()}`);
  }, [router, searchParams]);

  const [selectedTrips, setSelectedTrips] = useState<Set<string>>(new Set());
  const [showSortDropdown, setShowSortDropdown] = useState(false);
  
  const { data: inboxTrips, isLoading, error, refetch, assignTrips } = useInboxTrips();

  const agents = useMemo(() => {
    const seen = new Map<string, string>();
    for (const t of inboxTrips) {
      if (t.assignedTo && t.assignedToName && !seen.has(t.assignedTo)) {
        seen.set(t.assignedTo, t.assignedToName);
      }
    }
    return Array.from(seen.entries()).map(([id, name]) => ({ id, name }));
  }, [inboxTrips]);

  // ============================================================================
  // FILTER CONFIGURATION
  // ============================================================================

  const filterConfigs = useMemo(() => [
    { key: 'all' as FilterKey, label: 'All leads' },
    { key: 'at_risk' as FilterKey, label: 'At Risk' },
    { key: 'incomplete' as FilterKey, label: 'Needs details' },
    { key: 'unassigned' as FilterKey, label: 'Unassigned' },
  ], []);

  const filterCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: inboxTrips.length,
      at_risk: inboxTrips.filter((t) => t.slaStatus === 'at_risk').length,
      incomplete: inboxTrips.filter((t) =>
        t.flags.includes('incomplete') ||
        t.flags.includes('needs_clarification') ||
        t.flags.includes('details_unclear')
      ).length,
      unassigned: inboxTrips.filter((t) => !t.assignedTo).length,
    };

    return counts;
  }, [inboxTrips]);

  const filtered = useMemo(() => {
    let result = [...inboxTrips];

    // Standard filters
    if (activeFilter === 'at_risk') {
      result = result.filter((t) => t.slaStatus === 'at_risk');
    } else if (activeFilter === 'incomplete') {
      result = result.filter((t) =>
        t.flags.includes('incomplete') ||
        t.flags.includes('needs_clarification') ||
        t.flags.includes('details_unclear')
      );
    } else if (activeFilter === 'unassigned') {
      result = result.filter((t) => !t.assignedTo);
    }

    if (searchQuery) {
      result = result.filter((t) => tripMatchesQuery(t, searchQuery));
    }

    const dir = sortDirection === 'asc' ? 1 : -1;
    return result.sort((a, b) => {
      switch (sortBy) {
        case 'priority': {
          const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
          const pa = priorityOrder[a.priority];
          const pb = priorityOrder[b.priority];
          if (pa !== pb) return (pa - pb) * dir;
          const slaOrder = { breached: 0, at_risk: 1, on_track: 2 };
          return (slaOrder[a.slaStatus] - slaOrder[b.slaStatus]) * dir;
        }
        case 'destination':
          return a.destination.localeCompare(b.destination) * dir;
        case 'value':
          return (a.value - b.value) * dir;
        case 'party':
          return (a.partySize - b.partySize) * dir;
        case 'dates':
          return a.dateWindow.localeCompare(b.dateWindow) * dir;
        case 'sla': {
          const slaOrder = { breached: 0, at_risk: 1, on_track: 2 };
          return (slaOrder[a.slaStatus] - slaOrder[b.slaStatus]) * dir;
        }
        default:
          return 0;
      }
    });
  }, [inboxTrips, activeFilter, searchQuery, sortBy, sortDirection]);

  const handleSelect = useCallback((id: string, selected: boolean) => {
    setSelectedTrips((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedTrips(new Set());
  }, []);

  const handleAssign = useCallback((agentId: string) => {
    assignTrips({ tripIds: Array.from(selectedTrips), assignTo: agentId, notifyAssignee: true });
    handleClearSelection();
  }, [selectedTrips, handleClearSelection, assignTrips]);

  const handleExport = useCallback(() => {
    const selected = inboxTrips.filter((t) => selectedTrips.has(t.id));
    const csv = [
      'ID,Destination,Priority,SLA,Agent',
      ...selected.map((t) => `${t.id},${t.destination},${t.priority},${t.slaStatus},${t.assignedToName || 'Unassigned'}`),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inbox-export-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [selectedTrips, inboxTrips]);

  if (error) {
    return (
      <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
        <BackToOverviewLink />
        <div className='flex items-center justify-between pt-1'>
          <div>
            <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Lead Inbox</h1>
            <p className='text-ui-sm text-[#8b949e] mt-0.5'>New customer inquiries sorted by urgency.</p>
          </div>
        </div>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-8 text-center'>
          <InlineError message='Failed to load inbox' />
          <button
            type='button'
            onClick={() => refetch()}
            className='mt-4 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg text-ui-sm font-medium hover:bg-[#6eb5ff] transition-colors'
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className='p-5 pb-4 max-w-[1400px] mx-auto space-y-5'>
      <BackToOverviewLink />
      {/* Header */}
      <header className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Lead Inbox</h1>
          <p className='text-ui-sm text-[#8b949e] mt-0.5'>New customer inquiries sorted by urgency.</p>
        </div>
        
        <div className='flex items-center gap-3 flex-wrap'>
          <div className='relative flex-1 min-w-[180px] max-w-64'>
            <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b949e]' />
            <input
              type='text'
              placeholder='Search by customer, destination, or lead ref...'
              value={searchQuery}
              onChange={(e) => updateParams({ q: e.target.value || null })}
              className='w-full pl-9 pr-3 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]'
            />
          </div>

          <div className='relative'>
            <button
              onClick={() => setShowSortDropdown(!showSortDropdown)}
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] hover:border-[#484f58] transition-colors'
            >
              <ArrowUpDown className='w-4 h-4 text-[#8b949e]' />
              <span>Sort by {SORT_OPTIONS[sortBy].label}</span>
              {sortDirection === 'asc' ? (
                <ChevronUp className='w-4 h-4 text-[#8b949e]' />
              ) : (
                <ChevronDown className='w-4 h-4 text-[#8b949e]' />
              )}
            </button>

            {showSortDropdown && (
              <div className='absolute top-full right-0 mt-1 w-56 bg-[#0f1115] border border-[#30363d] rounded-lg shadow-xl z-10'>
                <div className='p-2 border-b border-[#30363d]'>
                  <div className='flex items-center justify-between px-2 py-1'>
                    <span className='text-ui-xs text-[#8b949e] font-medium'>Direction</span>
                    <div className='flex items-center gap-1'>
                      <button
                        onClick={() => updateParams({ dir: 'asc' })}
                        className={`p-1 rounded transition-colors ${
                          sortDirection === 'asc'
                            ? 'bg-[#58a6ff] text-[#0d1117]'
                            : 'text-[#8b949e] hover:text-[#e6edf3]'
                        }`}
                      >
                        <ChevronUp className='w-4 h-4' />
                      </button>
                      <button
                        onClick={() => updateParams({ dir: 'desc' })}
                        className={`p-1 rounded transition-colors ${
                          sortDirection === 'desc'
                            ? 'bg-[#58a6ff] text-[#0d1117]'
                            : 'text-[#8b949e] hover:text-[#e6edf3]'
                        }`}
                      >
                        <ChevronDown className='w-4 h-4' />
                      </button>
                    </div>
                  </div>
                </div>
                <div className='p-1'>
                  {(Object.keys(SORT_OPTIONS) as SortKey[]).map((key) => {
                    const option = SORT_OPTIONS[key];
                    const Icon = option.icon;
                    return (
                      <button
                        key={key}
                        onClick={() => {
                          updateParams({ sort: key });
                          setShowSortDropdown(false);
                        }}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left text-ui-sm rounded-md transition-colors ${
                          sortBy === key
                            ? 'bg-[#58a6ff] text-[#0d1117]'
                            : 'text-[#e6edf3] hover:bg-[#161b22]'
                        }`}
                      >
                        <Icon className='w-4 h-4' />
                        <span>{option.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <span className='text-ui-sm text-[#8b949e]'>
            {isLoading ? 'Loading...' : leadCountLabel(inboxTrips.length)}
          </span>
        </div>
      </header>

      {/* Bulk Actions Toolbar */}
      {selectedTrips.size > 0 && (
        <BulkActionsToolbar
          selectedCount={selectedTrips.size}
          onClearSelection={handleClearSelection}
          onAssign={handleAssign}
          onExport={handleExport}
          agents={agents}
        />
      )}

      {/* Filters */}
      <InboxFilterBar
        activeFilter={activeFilter}
        onFilterChange={(filter) => updateParams({ filter })}
        filters={filterConfigs.map((f) => ({ ...f, count: filterCounts[f.key] || 0 }))}
      />

      {/* Trip Grid */}
      {isLoading && inboxTrips.length === 0 ? (
        <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 space-y-3'
            >
              <div className='h-4 bg-[#161b22] rounded w-1/2' />
              <div className='h-3 bg-[#161b22] rounded w-1/3' />
              <div className='h-3 bg-[#161b22] rounded w-2/3' />
            </div>
          ))}
        </div>
      ) : (
        <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
          {filtered.map((trip) => (
            <TripCard
              key={trip.id}
              trip={trip}
              isSelected={selectedTrips.has(trip.id)}
              onSelect={handleSelect}
              viewProfile='operations'
            />
          ))}
          {filtered.length === 0 && !isLoading && (
            <InboxEmptyState
              hasSearch={!!searchQuery}
              activeFilter={activeFilter}
              onClearSearch={() => updateParams({ q: null })}
              onClearFilter={() => updateParams({ filter: null })}
            />
          )}
        </div>
      )}
    </div>
  );
}
