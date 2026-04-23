'use client';

/**
 * WorkspaceTable — Dense table view for scanning trips quickly.
 *
 * Accessibility: native <table> with proper scope attributes.
 * Responsive: horizontal scroll on narrow viewports.
 */

import Link from 'next/link';
import { memo } from 'react';
import { ChevronRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { getTripRoute } from '@/lib/routes';
import type { Trip } from '@/lib/api-client';

export type SortField = 'state' | 'destination' | 'age' | 'type';
export type SortDirection = 'asc' | 'desc';

interface WorkspaceTableProps {
  trips: Trip[];
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
}

const STATE_META: Record<string, { color: string; bg: string; label: string }> = {
  green:  { color: '#3fb950', bg: 'rgba(63,185,80,0.12)',   label: 'Ready' },
  amber:  { color: '#d29922', bg: 'rgba(210,153,34,0.12)',  label: 'In Progress' },
  red:    { color: '#f85149', bg: 'rgba(248,81,73,0.12)',   label: 'Needs Review' },
  blue:   { color: '#58a6ff', bg: 'rgba(88,166,255,0.12)',  label: 'Awaiting Info' },
};

function SortHeader({
  field,
  label,
  activeField,
  direction,
  onSort,
}: {
  field: SortField;
  label: string;
  activeField: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
}) {
  const isActive = activeField === field;
  return (
    <button
      type="button"
      onClick={() => onSort(field)}
      className="flex items-center gap-1 text-left text-xs font-semibold text-[#8b949e] uppercase tracking-wider hover:text-[#e6edf3] transition-colors"
      aria-label={`Sort by ${label} ${isActive ? (direction === 'asc' ? 'ascending' : 'descending') : ''}`}
    >
      {label}
      {isActive ? (
        direction === 'asc' ? (
          <ArrowUp className="h-3 w-3 text-[#58a6ff]" aria-hidden="true" />
        ) : (
          <ArrowDown className="h-3 w-3 text-[#58a6ff]" aria-hidden="true" />
        )
      ) : (
        <ArrowUpDown className="h-3 w-3 text-[#484f58]" aria-hidden="true" />
      )}
    </button>
  );
}

const TripRow = memo(function TripRow({ trip }: { trip: Trip }) {
  const meta = STATE_META[trip.state] ?? STATE_META.blue;
  const isBlocked = trip.state === 'red';

  return (
    <tr className="border-b border-[#1c2128] hover:bg-[#0f1115] transition-colors">
      <td className="py-2.5 px-3">
        <Link
          href={getTripRoute(trip.id)}
          className="flex items-center gap-2 text-[#e6edf3] hover:text-[#58a6ff] transition-colors"
        >
          <span className="text-sm font-medium truncate max-w-[200px]">{trip.destination}</span>
        </Link>
      </td>
      <td className="py-2.5 px-3">
        <span className="text-xs text-[#8b949e]">{trip.type}</span>
      </td>
      <td className="py-2.5 px-3">
        <span
          className="inline-flex items-center text-xs font-mono font-semibold px-2 py-0.5 rounded-md"
          style={{ color: meta.color, background: meta.bg }}
        >
          {isBlocked && <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current" />}
          {meta.label}
        </span>
      </td>
      <td className="py-2.5 px-3">
        <span className="text-xs text-[#8b949e]">{trip.age}</span>
      </td>
      <td className="py-2.5 px-3">
        <span className="text-xs font-mono text-[#484f58]">{trip.id}</span>
      </td>
      <td className="py-2.5 px-3 text-right">
        <Link
          href={getTripRoute(trip.id)}
          className="inline-flex items-center text-xs text-[#484f58] hover:text-[#8b949e] transition-colors"
        >
          Open
          <ChevronRight className="h-3 w-3 ml-0.5" aria-hidden="true" />
        </Link>
      </td>
    </tr>
  );
});

export const WorkspaceTable = memo(function WorkspaceTable({
  trips,
  sortField,
  sortDirection,
  onSort,
}: WorkspaceTableProps) {
  return (
    <div className="rounded-xl border border-[#1c2128] bg-[#0f1115] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-[#1c2128] bg-[#0a0d11]">
              <th scope="col" className="py-2.5 px-3" aria-sort={sortField === 'destination' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <SortHeader field="destination" label="Destination" activeField={sortField} direction={sortDirection} onSort={onSort} />
              </th>
              <th scope="col" className="py-2.5 px-3" aria-sort={sortField === 'type' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <SortHeader field="type" label="Type" activeField={sortField} direction={sortDirection} onSort={onSort} />
              </th>
              <th scope="col" className="py-2.5 px-3" aria-sort={sortField === 'state' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <SortHeader field="state" label="State" activeField={sortField} direction={sortDirection} onSort={onSort} />
              </th>
              <th scope="col" className="py-2.5 px-3" aria-sort={sortField === 'age' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <SortHeader field="age" label="Age" activeField={sortField} direction={sortDirection} onSort={onSort} />
              </th>
              <th scope="col" className="py-2.5 px-3">
                <span className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider">ID</span>
              </th>
              <th scope="col" className="py-2.5 px-3 text-right">
                <span className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider">Action</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {trips.map((trip) => (
              <TripRow key={trip.id} trip={trip} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});
