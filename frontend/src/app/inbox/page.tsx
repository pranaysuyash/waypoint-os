'use client';

import { useState, useCallback, memo, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Briefcase,
  ChevronDown,
  ChevronUp,
  Clock,
  Users,
  Calendar,
  Wallet,
  AlertTriangle,
  CheckSquare,
  Square,
  UserPlus,
  Search,
  Flag,
  ArrowUpDown,
  Download,
} from 'lucide-react';
import { useInboxTrips } from '@/hooks/useGovernance';
import { getTripRoute } from '@/lib/routes';
import { InlineError } from '@/components/error-boundary';
import type { InboxTrip, TripPriority } from '@/types/governance';

type PriorityKey = TripPriority;
type SLAStatus = 'on_track' | 'at_risk' | 'breached';
type SortKey = 'priority' | 'destination' | 'value' | 'party' | 'dates' | 'sla';
type SortDirection = 'asc' | 'desc';

// ============================================================================
// STATE CONFIGURATION
// ============================================================================

const STAGE_LABELS: Record<string, { color: string; bg: string; label: string }> = {
  intake: { color: '#58a6ff', bg: 'rgba(88,166,255,0.12)', label: 'Intake' },
  details: { color: '#d29922', bg: 'rgba(210,153,34,0.12)', label: 'Details' },
  options: { color: '#58a6ff', bg: 'rgba(88,166,255,0.12)', label: 'Options' },
  review: { color: '#f85149', bg: 'rgba(248,81,73,0.12)', label: 'Review' },
  booking: { color: '#3fb950', bg: 'rgba(63,185,80,0.12)', label: 'Booking' },
};

const PRIORITY_META: Record<
  PriorityKey,
  { color: string; label: string; icon: React.ComponentType<{ className?: string }> }
> = {
  low: { color: '#8b949e', label: 'Low', icon: Flag },
  medium: { color: '#58a6ff', label: 'Medium', icon: Flag },
  high: { color: '#d29922', label: 'High', icon: Flag },
  critical: { color: '#f85149', label: 'Critical', icon: AlertTriangle },
};

const SORT_OPTIONS: Record<SortKey, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  priority: { label: 'Priority', icon: Flag },
  destination: { label: 'Destination', icon: Briefcase },
  value: { label: 'Value', icon: Wallet },
  party: { label: 'Party Size', icon: Users },
  dates: { label: 'Dates', icon: Calendar },
  sla: { label: 'SLA Status', icon: AlertTriangle },
};

// ============================================================================
// COMPONENTS
// ============================================================================

const PriorityBadge = memo(function PriorityBadge({ priority }: { priority: PriorityKey }) {
  const meta = PRIORITY_META[priority];
  const Icon = meta.icon;
  
  return (
    <span
      className='inline-flex items-center gap-1 text-xs'
      style={{ color: meta.color }}
    >
      <Icon className='w-3 h-3' />
      {meta.label}
    </span>
  );
});

const SLABadge = memo(function SLABadge({ status, daysInStage }: { status: SLAStatus; daysInStage: number }) {
  const styles = {
    on_track: { color: '#3fb950', bg: 'rgba(63,185,80,0.1)', label: 'On Track' },
    at_risk: { color: '#d29922', bg: 'rgba(210,153,34,0.1)', label: `${daysInStage}d` },
    breached: { color: '#f85149', bg: 'rgba(248,81,73,0.1)', label: `${daysInStage}d overdue` },
  };
  
  const style = styles[status];
  
  return (
    <span
      className='inline-block px-1.5 py-0.5 rounded text-xs font-medium'
      style={{ color: style.color, background: style.bg }}
    >
      {style.label}
    </span>
  );
});

const TripCard = memo(function TripCard({
  trip,
  isSelected,
  onSelect,
}: {
  trip: InboxTrip;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
}) {
  const stageMeta = STAGE_LABELS[trip.stage] || STAGE_LABELS.intake;
  const slaColor = trip.slaStatus === 'breached' ? '#f85149' : trip.slaStatus === 'at_risk' ? '#d29922' : '#3fb950';

  return (
    <div
      className='group relative rounded-xl border bg-[#0f1115] transition-all hover:border-[#30363d] overflow-hidden flex'
      style={{ borderColor: trip.slaStatus === 'breached' ? 'rgba(248,81,73,0.4)' : '#1c2128' }}
    >
      {/* SLA Accent Bar */}
      <div 
        className='w-1.5 shrink-0 h-full' 
        style={{ background: slaColor, opacity: isSelected ? 1 : 0.6 }} 
      />

      <div className='p-4 flex-1'>
        {/* Selection Checkbox (moved to better position) */}
        <button
          type='button'
          onClick={(e) => {
            e.stopPropagation();
            onSelect(trip.id, !isSelected);
          }}
          className='absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity'
        >
          {isSelected ? (
            <CheckSquare className='w-4 h-4 text-[#58a6ff]' />
          ) : (
            <Square className='w-4 h-4 text-[#484f58]' />
          )}
        </button>

        <Link href={getTripRoute(trip.id)} className='block'>
          <div className='flex items-start justify-between gap-3 mb-1'>
            <div className='flex flex-col min-w-0'>
              <span className='text-[14px] font-semibold text-[#e6edf3] truncate leading-tight' title={trip.destination}>
                {trip.destination}
              </span>
              <span className='text-[10px] uppercase tracking-wider text-[#484f58] font-bold mt-0.5'>
                {trip.tripType} · {trip.id.split('_')[1]}
              </span>
            </div>
            <div className='flex items-center gap-1 shrink-0'>
              <PriorityBadge priority={trip.priority} />
            </div>
          </div>

          <div className='flex items-center gap-3 text-[11px] text-[#8b949e] my-3 py-2 border-y border-[#1c2128]/50'>
            <div className='flex flex-col gap-0.5'>
              <span className='text-[10px] text-[#484f58] uppercase font-medium'>Pax</span>
              <span className='text-[#e6edf3] font-medium'>{trip.partySize}</span>
            </div>
            <div className='w-px h-6 bg-[#1c2128]' />
            <div className='flex flex-col gap-0.5'>
              <span className='text-[10px] text-[#484f58] uppercase font-medium'>Budget</span>
              <span className='text-[#58a6ff] font-mono font-medium'>${(trip.value / 1000).toFixed(1)}k</span>
            </div>
            <div className='w-px h-6 bg-[#1c2128]' />
            <div className='flex flex-col gap-0.5 flex-1'>
              <span className='text-[10px] text-[#484f58] uppercase font-medium'>Dates</span>
              <span className='text-[#e6edf3] truncate'>{trip.dateWindow}</span>
            </div>
          </div>

          <div className='flex items-center justify-between mt-2'>
            <div className='flex items-center gap-2'>
              <span
                className='text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-tight'
                style={{ color: stageMeta.color, background: stageMeta.bg }}
              >
                {stageMeta.label}
              </span>
              <span className='text-[11px] text-[#484f58] font-mono'>{trip.daysInCurrentStage}d</span>
            </div>
            
            <div className='flex items-center gap-2'>
              {trip.assignedToName ? (
                <div className='flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#161b22] border border-[#30363d]'>
                  <span className='text-[10px] text-[#8b949e]'>
                    {trip.assignedToName}
                  </span>
                </div>
              ) : (
                <span className='text-[10px] text-[#d29922] font-bold uppercase italic'>
                  Unassigned
                </span>
              )}
              <SLABadge status={trip.slaStatus} daysInStage={trip.daysInCurrentStage} />
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
});

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
        <span className='text-sm text-[#e6edf3]'>
          <strong>{selectedCount}</strong> trips selected
        </span>
        <button
          onClick={onClearSelection}
          className='text-xs text-[#8b949e] hover:text-[#e6edf3]'
        >
          Clear
        </button>
      </div>

      <div className='flex items-center gap-2'>
        <div className='relative'>
          <button
            onClick={() => setShowAssignDropdown(!showAssignDropdown)}
            className='flex items-center gap-1.5 px-3 py-1.5 bg-[#58a6ff] text-[#0d1117] rounded-lg text-sm font-medium hover:bg-[#6eb5ff] transition-colors'
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
                  className='w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-[#e6edf3] hover:bg-[#161b22] first:rounded-t-lg last:rounded-b-lg'
                >
                  <div className='h-6 w-6 rounded-full bg-[#58a6ff]/20 flex items-center justify-center text-[#58a6ff] text-xs font-bold'>
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
          className='flex items-center gap-1.5 px-3 py-1.5 bg-[#161b22] text-[#8b949e] rounded-lg text-sm hover:text-[#e6edf3] transition-colors'
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
  const activeFilter = (searchParams.get('filter') as any) || 'all';
  const sortBy = (searchParams.get('sort') as SortKey) || 'priority';
  const sortDirection = (searchParams.get('dir') as SortDirection) || 'desc';
  const searchQuery = searchParams.get('q') || '';
  const currentRole = (searchParams.get('role') as 'ops' | 'mgr') || 'ops';

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

  const filterCounts = useMemo(() => ({
    all: inboxTrips.length,
    pending: inboxTrips.filter((t) => t.slaStatus === 'at_risk').length,
    review: inboxTrips.filter((t) => t.slaStatus === 'breached' || t.priority === 'critical').length,
    unassigned: inboxTrips.filter((t) => !t.assignedTo).length,
  }), [inboxTrips]);

  const filtered = useMemo(() => {
    let result = [...inboxTrips];

    if (activeFilter === 'pending') {
      result = result.filter((t) => t.slaStatus === 'at_risk');
    } else if (activeFilter === 'review') {
      result = result.filter((t) => t.slaStatus === 'breached' || t.priority === 'critical');
    } else if (activeFilter === 'unassigned') {
      result = result.filter((t) => !t.assignedTo);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((t) =>
        t.destination.toLowerCase().includes(query) ||
        t.id.toLowerCase().includes(query) ||
        t.tripType.toLowerCase().includes(query)
      );
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
        <div className='flex items-center justify-between pt-1'>
          <div>
            <h1 className='text-xl font-semibold text-[#e6edf3]'>Inbox</h1>
            <p className='text-sm text-[#8b949e] mt-0.5'>Trip queue · sorted by urgency</p>
          </div>
        </div>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-8 text-center'>
          <InlineError message='Failed to load inbox' />
          <button
            type='button'
            onClick={() => refetch()}
            className='mt-4 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg text-sm font-medium hover:bg-[#6eb5ff] transition-colors'
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className='p-5 pb-4 max-w-[1400px] mx-auto space-y-5'>
      {/* Header */}
      <header className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-xl font-semibold text-[#e6edf3]'>Inbox</h1>
          <p className='text-sm text-[#8b949e] mt-0.5'>Trip queue · sorted by urgency</p>
        </div>
        
        <div className='flex items-center gap-3 flex-wrap'>
          <div className='relative flex-1 min-w-[180px] max-w-64'>
            <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b949e]' />
            <input
              type='text'
              placeholder='Search trips...'
              value={searchQuery}
              onChange={(e) => updateParams({ q: e.target.value || null })}
              className='w-full pl-9 pr-3 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]'
            />
          </div>

          {/* Role Toggle */}
          <div className='flex items-center bg-[#161b22] border border-[#30363d] rounded-lg p-1'>
            <button
              onClick={() => updateParams({ role: 'ops' })}
              className={`px-3 py-1 rounded-md text-[10px] font-bold uppercase transition-all ${
                currentRole === 'ops' ? 'bg-[#58a6ff] text-[#0d1117]' : 'text-[#8b949e]'
              }`}
            >
              Ops
            </button>
            <button
              onClick={() => updateParams({ role: 'mgr' })}
              className={`px-3 py-1 rounded-md text-[10px] font-bold uppercase transition-all ${
                currentRole === 'mgr' ? 'bg-[#58a6ff] text-[#0d1117]' : 'text-[#8b949e]'
              }`}
            >
              Mgr
            </button>
          </div>

          <div className='relative'>
            <button
              onClick={() => setShowSortDropdown(!showSortDropdown)}
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] hover:border-[#484f58] transition-colors'
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
                    <span className='text-xs text-[#8b949e] font-medium'>Direction</span>
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
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left text-sm rounded-md transition-colors ${
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

          <span className='text-sm text-[#8b949e]'>
            {isLoading ? 'Loading...' : `${inboxTrips.length} trips total`}
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
      <div className='flex items-center gap-1' role='tablist'>
        {[
          { key: 'all', label: 'All' },
          { key: 'pending', label: 'At Risk' },
          { key: 'review', label: 'Critical' },
          { key: 'unassigned', label: 'Unassigned' },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => updateParams({ filter: f.key })}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeFilter === f.key
                ? 'bg-[#161b22] text-[#e6edf3] border-l-2 border-[#58a6ff]'
                : 'text-[#8b949e] hover:text-[#e6edf3]'
            }`}
          >
            {f.label}
            <span className={`tabular-nums px-1.5 py-0.5 rounded-md text-xs ${
              activeFilter === f.key
                ? 'bg-[rgba(88,166,255,0.15)] text-[#58a6ff]'
                : 'bg-[#161b22] text-[#484f58]'
            }`}>
              {filterCounts[f.key as keyof typeof filterCounts]}
            </span>
          </button>
        ))}
      </div>

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
            />
          ))}
          {filtered.length === 0 && !isLoading && (
            <div className='col-span-full py-12 text-center'>
              <p className='text-[#8b949e]'>No trips match this filter.</p>
              {searchQuery && (
                <button
                  onClick={() => updateParams({ q: null })}
                  className='mt-2 text-sm text-[#58a6ff] hover:text-[#79b8ff]'
                >
                  Clear search
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
