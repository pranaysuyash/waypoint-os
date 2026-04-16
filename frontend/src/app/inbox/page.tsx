'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Briefcase,
  ChevronRight,
  Clock,
  Users,
  Calendar,
  AlertTriangle,
} from 'lucide-react';

type StateKey = 'green' | 'amber' | 'red' | 'blue';

const STATE_META: Record<
  StateKey,
  { color: string; bg: string; border: string; label: string }
> = {
  green: {
    color: '#3fb950',
    bg: 'rgba(63,185,80,0.12)',
    border: 'rgba(63,185,80,0.25)',
    label: 'PROCEED_SAFE',
  },
  amber: {
    color: '#d29922',
    bg: 'rgba(210,153,34,0.12)',
    border: 'rgba(210,153,34,0.25)',
    label: 'BRANCH / DRAFT',
  },
  red: {
    color: '#f85149',
    bg: 'rgba(248,81,73,0.12)',
    border: 'rgba(248,81,73,0.25)',
    label: 'STOP_REVIEW',
  },
  blue: {
    color: '#58a6ff',
    bg: 'rgba(88,166,255,0.12)',
    border: 'rgba(88,166,255,0.25)',
    label: 'ASK_FOLLOWUP',
  },
};

type TripItem = {
  id: string;
  destination: string;
  type: string;
  party: number;
  dateWindow: string;
  state: StateKey;
  age: string;
  action: string;
  overdue?: boolean;
};

const TRIPS: TripItem[] = [
  {
    id: 'TRP-2026-MSC-0422',
    destination: 'Moscow',
    type: 'Solo',
    party: 1,
    dateWindow: 'Jun 10–20',
    state: 'red',
    age: '2d ago',
    action: 'Requires owner review',
    overdue: true,
  },
  {
    id: 'TRP-2026-AND-0420',
    destination: 'Andaman',
    type: 'Honeymoon',
    party: 2,
    dateWindow: 'May 15–22',
    state: 'amber',
    age: '1d ago',
    action: 'Draft itinerary branch pending',
  },
  {
    id: 'TRP-2026-DXB-0418',
    destination: 'Dubai',
    type: 'Corporate',
    party: 8,
    dateWindow: 'Jul 3–7',
    state: 'blue',
    age: '5h ago',
    action: 'Clarification requested from client',
  },
  {
    id: 'TRP-2026-SGP-0315',
    destination: 'Singapore',
    type: 'Family',
    party: 4,
    dateWindow: 'Aug 1–10',
    state: 'green',
    age: '2h ago',
    action: 'Ready to proceed',
  },
  {
    id: 'TRP-2026-BKK-0401',
    destination: 'Bangkok',
    type: 'Group',
    party: 12,
    dateWindow: 'Sep 5–12',
    state: 'green',
    age: '3d ago',
    action: 'Booking confirmation pending',
  },
  {
    id: 'TRP-2026-PAR-0430',
    destination: 'Paris',
    type: 'Anniversary',
    party: 2,
    dateWindow: 'Oct 14–21',
    state: 'amber',
    age: '4d ago',
    action: 'Visa docs incomplete',
  },
  {
    id: 'TRP-2026-NYC-0512',
    destination: 'New York',
    type: 'Family',
    party: 5,
    dateWindow: 'Dec 20–28',
    state: 'blue',
    age: '6h ago',
    action: 'Budget clarification needed',
  },
];

type FilterKey = 'all' | 'pending' | 'review';

const FILTERS: { key: FilterKey; label: string; count: number }[] = [
  { key: 'all', label: 'All', count: TRIPS.length },
  {
    key: 'pending',
    label: 'Pending',
    count: TRIPS.filter((t) => t.state === 'amber' || t.state === 'blue')
      .length,
  },
  {
    key: 'review',
    label: 'Needs Review',
    count: TRIPS.filter((t) => t.state === 'red').length,
  },
];

function TripCard({ trip }: { trip: TripItem }) {
  const meta = STATE_META[trip.state];
  return (
    <Link
      href='/workbench'
      className='group flex flex-col gap-3 rounded-xl border bg-[#0f1115] p-4 transition-colors hover:border-[#30363d]'
      style={{ borderColor: trip.overdue ? meta.border : '#1c2128' }}
    >
      <div className='flex items-start justify-between gap-3'>
        <div className='flex items-center gap-2 min-w-0'>
          {trip.overdue && (
            <AlertTriangle
              className='h-3.5 w-3.5 shrink-0'
              style={{ color: meta.color }}
            />
          )}
          <span className='text-[14px] font-semibold text-[#e6edf3] truncate'>
            {trip.destination}
          </span>
          <span className='text-xs text-[#6e7681]'>{trip.type}</span>
        </div>
        <span
          className='shrink-0 text-xs font-mono font-semibold px-2 py-0.5 rounded-md whitespace-nowrap'
          style={{ color: meta.color, background: meta.bg }}
        >
          {meta.label}
        </span>
      </div>

      <div className='flex items-center gap-4 text-xs text-[#6e7681]'>
        <span className='flex items-center gap-1'>
          <Users className='h-3 w-3' /> {trip.party} pax
        </span>
        <span className='flex items-center gap-1'>
          <Calendar className='h-3 w-3' /> {trip.dateWindow}
        </span>
        <span className='flex items-center gap-1 font-mono text-[#484f58]'>
          <Clock className='h-3 w-3' /> {trip.age}
        </span>
      </div>

      <div className='flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          <Briefcase className='h-3 w-3 text-[#484f58]' />
          <span className='text-xs text-[#8b949e]'>{trip.action}</span>
        </div>
        <ChevronRight className='h-3.5 w-3.5 text-[#30363d] group-hover:text-[#6e7681] transition-colors shrink-0' />
      </div>

      <div className='text-xs font-mono text-[#484f58]'>{trip.id}</div>
    </Link>
  );
}

export default function InboxPage() {
  const [activeFilter, setActiveFilter] = useState<FilterKey>('all');

  const filtered = TRIPS.filter((t) => {
    if (activeFilter === 'pending')
      return t.state === 'amber' || t.state === 'blue';
    if (activeFilter === 'review') return t.state === 'red';
    return true;
  });

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      <div className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-[15px] font-semibold text-[#e6edf3]'>Inbox</h1>
          <p className='text-[12px] text-[#6e7681] mt-0.5'>
            Trip queue · sorted by urgency
          </p>
        </div>
        <span className='text-xs font-mono text-[#484f58]'>
          {TRIPS.length} trips total
        </span>
      </div>

      <div className='flex items-center gap-1'>
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setActiveFilter(f.key)}
            className='flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors'
            style={
              activeFilter === f.key
                ? {
                    background: '#161b22',
                    color: '#e6edf3',
                    borderLeft: '2px solid #58a6ff',
                  }
                : { color: '#6e7681' }
            }
          >
            {f.label}
            <span
              className='tabular-nums px-1.5 py-0.5 rounded-md text-xs'
              style={
                activeFilter === f.key
                  ? { background: 'rgba(88,166,255,0.15)', color: '#58a6ff' }
                  : { background: '#161b22', color: '#484f58' }
              }
            >
              {f.count}
            </span>
          </button>
        ))}
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
        {filtered.map((trip) => (
          <TripCard key={trip.id} trip={trip} />
        ))}
        {filtered.length === 0 && (
          <div className='col-span-full py-12 text-center text-[13px] text-[#484f58]'>
            No trips match this filter.
          </div>
        )}
      </div>
    </div>
  );
}
