'use client';

import { useState, useCallback, memo, useMemo } from 'react';
import Link from 'next/link';
import {
  Briefcase,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  Clock,
  Users,
  Calendar,
  Wallet,
  AlertTriangle,
  CheckSquare,
  Square,
  UserPlus,
  MoreHorizontal,
  Download,
  Filter,
  Search,
  Flag,
  ArrowUpDown,
} from 'lucide-react';
import { useTrips } from '@/hooks/useTrips';
import { getTripRoute } from '@/lib/routes';
import { InlineLoading } from '@/components/ui/loading';
import { InlineError } from '@/components/error-boundary';
import type { TeamMember } from '@/types/governance';

// ============================================================================
// MOCK TEAM DATA - Replace with real API
// ============================================================================

const TEAM_MEMBERS: TeamMember[] = [
  { id: 'agent-001', name: 'Sarah Chen', email: 'sarah@agency.com', role: 'agent', isActive: true, joinedAt: '2026-01-15', capacity: 15, currentAssignments: 12 },
  { id: 'agent-002', name: 'Mike Johnson', email: 'mike@agency.com', role: 'agent', isActive: true, joinedAt: '2026-02-01', capacity: 15, currentAssignments: 16 },
  { id: 'agent-003', name: 'Alex Kim', email: 'alex@agency.com', role: 'agent', isActive: true, joinedAt: '2026-03-10', capacity: 10, currentAssignments: 8 },
  { id: 'unassigned', name: 'Unassigned', email: '', role: 'agent', isActive: true, joinedAt: '', capacity: 0, currentAssignments: 3 },
];

// ============================================================================
// TYPES
// ============================================================================

type StateKey = 'green' | 'amber' | 'red' | 'blue';
type PriorityKey = 'low' | 'medium' | 'high' | 'critical';
type SLAStatus = 'on_track' | 'at_risk' | 'breached';
type SortKey = 'priority' | 'destination' | 'value' | 'party' | 'dates' | 'state' | 'age' | 'sla';
type SortDirection = 'asc' | 'desc';

interface TripItem {
  id: string;
  destination: string;
  type: string;
  party: number;
  dateWindow: string;
  state: StateKey;
  age: string;
  action: string;
  overdue?: boolean;
  assignedTo?: string;
  assignedToName?: string;
  priority: PriorityKey;
  slaStatus: SLAStatus;
  daysInStage: number;
  value?: number;
}

// ============================================================================
// STATE CONFIGURATION
// ============================================================================

const STATE_META: Record<
  StateKey,
  { color: string; bg: string; border: string; label: string }
> = {
  green: {
    color: '#3fb950',
    bg: 'rgba(63,185,80,0.12)',
    border: 'rgba(63,185,80,0.25)',
    label: 'Ready',
  },
  amber: {
    color: '#d29922',
    bg: 'rgba(210,153,34,0.12)',
    border: 'rgba(210,153,34,0.25)',
    label: 'In Progress',
  },
  red: {
    color: '#f85149',
    bg: 'rgba(248,81,73,0.12)',
    border: 'rgba(248,81,73,0.25)',
    label: 'Needs Review',
  },
  blue: {
    color: '#58a6ff',
    bg: 'rgba(88,166,255,0.12)',
    border: 'rgba(88,166,255,0.25)',
    label: 'Awaiting Info',
  },
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
  state: { label: 'State', icon: CheckSquare },
  age: { label: 'Age', icon: Clock },
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
  trip: TripItem;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
}) {
  const meta = STATE_META[trip.state];
  
  return (
    <div
      className='group relative rounded-xl border bg-[#0f1115] p-4 transition-all hover:border-[#30363d]'
      style={{ borderColor: trip.slaStatus === 'breached' ? '#f85149' : '#1c2128' }}
    >
      {/* Selection Checkbox */}
      <button
        type='button'
        onClick={(e) => {
          e.stopPropagation();
          onSelect(trip.id, !isSelected);
        }}
        className='absolute top-3 left-3 opacity-0 group-hover:opacity-100 transition-opacity'
      >
        {isSelected ? (
          <CheckSquare className='w-4 h-4 text-[#58a6ff]' />
        ) : (
          <Square className='w-4 h-4 text-[#484f58]' />
        )}
      </button>

      <Link href={getTripRoute(trip.id)} className='block pl-6'>
        <div className='flex items-start justify-between gap-3 mb-2'>
          <div className='flex items-center gap-2 min-w-0'>
            <span className='text-[14px] font-semibold text-[#e6edf3] truncate' title={trip.destination}>
              {trip.destination}
            </span>
            <span className='text-xs text-[#8b949e]'>{trip.type}</span>
          </div>
          <div className='flex items-center gap-1'>
            <PriorityBadge priority={trip.priority} />
            <span
              className='shrink-0 text-xs font-mono font-semibold px-2 py-0.5 rounded-md whitespace-nowrap'
              style={{ color: meta.color, background: meta.bg }}
            >
              {meta.label}
            </span>
          </div>
        </div>

        <div className='flex items-center gap-4 text-xs text-[#8b949e] mb-2'>
          <span className='flex items-center gap-1'>
            <Users className='h-3 w-3' aria-hidden='true' /> {trip.party} pax
          </span>
          <span className='flex items-center gap-1'>
            <Calendar className='h-3 w-3' aria-hidden='true' /> {trip.dateWindow}
          </span>
          <span className='flex items-center gap-1 font-mono text-[#484f58]'>
            <Clock className='h-3 w-3' aria-hidden='true' /> {trip.age}
          </span>
          {trip.value && (
            <span className='font-mono text-[#58a6ff]'>
              ${(trip.value / 1000).toFixed(1)}k
            </span>
          )}
        </div>

        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-2'>
            <Briefcase className='h-3 w-3 text-[#484f58]' aria-hidden='true' />
            <span className='text-xs text-[#8b949e]'>{trip.action}</span>
          </div>
          <div className='flex items-center gap-2'>
            {trip.assignedToName ? (
              <span className='text-xs text-[#8b949e]'>
                👤 {trip.assignedToName}
              </span>
            ) : (
              <span className='text-xs text-[#d29922]'>
                👤 Unassigned
              </span>
            )}
            <SLABadge status={trip.slaStatus} daysInStage={trip.daysInStage} />
          </div>
        </div>

        <div className='text-xs font-mono text-[#484f58] mt-2'>{trip.id}</div>
      </Link>
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
}: {
  selectedCount: number;
  onClearSelection: () => void;
  onAssign: () => void;
  onExport: () => void;
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
              {TEAM_MEMBERS.filter(m => m.id !== 'unassigned').map((member) => (
                <button
                  key={member.id}
                  onClick={() => {
                    onAssign();
                    setShowAssignDropdown(false);
                  }}
                  className='w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-[#e6edf3] hover:bg-[#161b22] first:rounded-t-lg last:rounded-b-lg'
                >
                  <div className='h-6 w-6 rounded-full bg-[#58a6ff]/20 flex items-center justify-center text-[#58a6ff] text-xs font-bold'>
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <div>{member.name}</div>
                    <div className='text-xs text-[#8b949e]'>
                      {member.currentAssignments}/{member.capacity} trips
                    </div>
                  </div>
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
  const [activeFilter, setActiveFilter] = useState<'all' | 'pending' | 'review' | 'unassigned'>('all');
  const [selectedTrips, setSelectedTrips] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('priority');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [showSortDropdown, setShowSortDropdown] = useState(false);
  const { data: trips, isLoading, error, refetch } = useTrips();

  // Convert API trips with enhanced fields
  const tripItems: TripItem[] = useMemo(() => {
    return trips.map((trip, index) => {
      // Simulate assignment (in real app, comes from API)
      const assignments = ['agent-001', 'agent-002', 'agent-003', undefined];
      const assignedTo = assignments[index % 4];
      const assignedMember = assignedTo ? TEAM_MEMBERS.find(m => m.id === assignedTo) : undefined;
      
      // Simulate priority based on value/overdue
      const priorities: PriorityKey[] = ['low', 'medium', 'high', 'critical'];
      const priority = trip.overdue ? 'critical' : priorities[index % 4];
      
      // Simulate SLA status
      const daysInStage = Math.floor(Math.random() * 5) + 1;
      const slaStatus: SLAStatus = daysInStage > 3 ? 'breached' : daysInStage > 2 ? 'at_risk' : 'on_track';
      
      return {
        id: trip.id,
        destination: trip.destination,
        type: trip.type,
        state: trip.state,
        age: trip.age,
        party: 2 + (index % 6),
        dateWindow: ['Jun 10-20', 'Jul 3-7', 'Aug 15-22', 'Sep 5-12'][index % 4],
        action: ['Needs supplier quote', 'Awaiting client confirmation', 'Ready to book', 'Draft itinerary'][index % 4],
        overdue: trip.overdue || slaStatus === 'breached',
        assignedTo,
        assignedToName: assignedMember?.name,
        priority,
        slaStatus,
        daysInStage,
        value: 5000 + (index * 2500),
      };
    });
  }, [trips]);

  // Filter counts
  const filterCounts = useMemo(() => ({
    all: tripItems.length,
    pending: tripItems.filter((t) => t.state === 'amber' || t.state === 'blue').length,
    review: tripItems.filter((t) => t.state === 'red').length,
    unassigned: tripItems.filter((t) => !t.assignedTo).length,
  }), [tripItems]);

  // Filter and search
  const filtered = useMemo(() => {
    let result = tripItems;

    // Apply status filter
    if (activeFilter === 'pending') {
      result = result.filter((t) => t.state === 'amber' || t.state === 'blue');
    } else if (activeFilter === 'review') {
      result = result.filter((t) => t.state === 'red');
    } else if (activeFilter === 'unassigned') {
      result = result.filter((t) => !t.assignedTo);
    }

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((t) =>
        t.destination.toLowerCase().includes(query) ||
        t.id.toLowerCase().includes(query) ||
        t.type.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    const dir = sortDirection === 'asc' ? 1 : -1;
    return result.sort((a, b) => {
      switch (sortBy) {
        case 'priority': {
          const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
          const pa = priorityOrder[a.priority];
          const pb = priorityOrder[b.priority];
          if (pa !== pb) return (pa - pb) * dir;
          // Tie-break by SLA
          const slaOrder = { breached: 0, at_risk: 1, on_track: 2 };
          return (slaOrder[a.slaStatus] - slaOrder[b.slaStatus]) * dir;
        }
        case 'destination':
          return a.destination.localeCompare(b.destination) * dir;
        case 'value':
          return ((a.value || 0) - (b.value || 0)) * dir;
        case 'party':
          return (a.party - b.party) * dir;
        case 'dates':
          return a.dateWindow.localeCompare(b.dateWindow) * dir;
        case 'state': {
          const stateOrder = { red: 0, amber: 1, blue: 2, green: 3 };
          return (stateOrder[a.state] - stateOrder[b.state]) * dir;
        }
        case 'age':
          return a.age.localeCompare(b.age) * dir;
        case 'sla': {
          const slaOrder = { breached: 0, at_risk: 1, on_track: 2 };
          return (slaOrder[a.slaStatus] - slaOrder[b.slaStatus]) * dir;
        }
        default:
          return 0;
      }
    });
  }, [tripItems, activeFilter, searchQuery, sortBy, sortDirection]);

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

  const handleAssign = useCallback(() => {
    // Simulate assignment
    alert(`Assigning ${selectedTrips.size} trips...`);
    handleClearSelection();
  }, [selectedTrips.size, handleClearSelection]);

  const handleExport = useCallback(() => {
    alert(`Exporting ${selectedTrips.size} trips...`);
  }, [selectedTrips.size]);

  // Error state
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
          <InlineError message='Failed to load trips' />
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
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
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
              onChange={(e) => setSearchQuery(e.target.value)}
              className='w-full pl-9 pr-3 py-2 bg-[#161b22] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]'
            />
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
                        onClick={() => setSortDirection('asc')}
                        className={`p-1 rounded transition-colors ${
                          sortDirection === 'asc'
                            ? 'bg-[#58a6ff] text-[#0d1117]'
                            : 'text-[#8b949e] hover:text-[#e6edf3]'
                        }`}
                      >
                        <ChevronUp className='w-4 h-4' />
                      </button>
                      <button
                        onClick={() => setSortDirection('desc')}
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
                          setSortBy(key);
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
            {isLoading ? 'Loading...' : `${tripItems.length} trips total`}
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
        />
      )}

      {/* Filters */}
      <div className='flex items-center gap-1' role='tablist'>
        {[
          { key: 'all', label: 'All' },
          { key: 'pending', label: 'Pending' },
          { key: 'review', label: 'Needs Review' },
          { key: 'unassigned', label: 'Unassigned' },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setActiveFilter(f.key as typeof activeFilter)}
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
      {isLoading && tripItems.length === 0 ? (
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
                  onClick={() => setSearchQuery('')}
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
