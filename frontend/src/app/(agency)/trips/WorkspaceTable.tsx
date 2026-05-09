'use client';

/**
 * WorkspaceTable - Dense table view for scanning trips quickly.
 *
 * Accessibility: native <table> with proper scope attributes.
 * Responsive: horizontal scroll on narrow viewports.
 */

import Link from 'next/link';
import { memo } from 'react';
import { ChevronRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import type { Trip } from '@/lib/api-client';
import {
  getPlanningListSummary,
  PLANNING_LIST_STATE_META,
} from '@/lib/planning-list-display';

export type SortField = 'stage' | 'destination' | 'age' | 'type';
export type SortDirection = 'asc' | 'desc';

interface WorkspaceTableProps {
  trips: Trip[];
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
}

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
      className="flex items-center gap-1 text-left text-ui-xs font-semibold text-[#8b949e] uppercase tracking-wider hover:text-[#e6edf3] transition-colors"
      aria-label={`Sort by ${label} ${isActive ? (direction === 'asc' ? 'ascending' : 'descending') : ''}`}
    >
      {label}
      {isActive ? (
        direction === 'asc' ? (
          <ArrowUp className="size-3 text-[#58a6ff]" aria-hidden="true" />
        ) : (
          <ArrowDown className="size-3 text-[#58a6ff]" aria-hidden="true" />
        )
      ) : (
        <ArrowUpDown className="size-3 text-[#484f58]" aria-hidden="true" />
      )}
    </button>
  );
}

const TripRow = memo(function TripRow({ trip }: { trip: Trip }) {
  const summary = getPlanningListSummary(trip);
  const meta = PLANNING_LIST_STATE_META[summary.statusTone] ?? PLANNING_LIST_STATE_META.blue;
  const missingSummary = summary.missingFields.length > 0 ? summary.missingFields.join(', ') : 'None';

  return (
    <tr className="border-b border-[#1c2128] hover:bg-[#0f1115] transition-colors">
      <td className="py-2.5 px-3">
        <Link
          href={summary.action.href}
          className="block text-[#e6edf3] hover:text-[#58a6ff] transition-colors"
        >
          <span className="block text-ui-sm font-medium truncate max-w-[260px]">{summary.title}</span>
          <span className="mt-1 block text-[12px] text-[#8b949e] truncate max-w-[320px]">{summary.subtitle}</span>
          <span className="mt-1 block text-[10px] text-[#6e7681]">Inquiry Ref: {summary.inquiryReference}</span>
        </Link>
      </td>
      <td className="py-2.5 px-3">
        <div className="flex flex-wrap gap-1.5">
          <span
            className="inline-flex items-center text-ui-xs font-semibold px-2 py-0.5 rounded-md uppercase tracking-wide"
            style={{ color: meta.fg, background: meta.bg, border: `1px solid ${meta.border}` }}
          >
            {summary.statusLabel}
          </span>
          <span
            className="inline-flex items-center text-ui-xs font-semibold px-2 py-0.5 rounded-md uppercase tracking-wide"
            style={{
              color: '#c9d1d9',
              background: 'rgba(201,209,217,0.08)',
              border: '1px solid rgba(201,209,217,0.16)',
            }}
          >
            {summary.assignmentLabel}
          </span>
        </div>
      </td>
      <td className="py-2.5 px-3">
        <span className="text-ui-xs text-[#8b949e]">{missingSummary}</span>
      </td>
      <td className="py-2.5 px-3">
        <div className="space-y-1">
          <span className="block text-ui-xs text-[#8b949e]">{summary.recencyLabel}</span>
          <span className="block text-[12px] text-[#c9d1d9]">{summary.nextAction}</span>
        </div>
      </td>
      <td className="py-2.5 px-3 text-right">
        <Link
          href={summary.action.href}
          className="inline-flex items-center text-ui-xs text-[#58a6ff] hover:text-[#79b8ff] transition-colors"
        >
          {summary.action.label}
          <ChevronRight className="size-3 ml-0.5" aria-hidden="true" />
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
                <SortHeader field="destination" label="Trip" activeField={sortField} direction={sortDirection} onSort={onSort} />
              </th>
              <th scope="col" className="py-2.5 px-3" aria-sort={sortField === 'stage' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <SortHeader field="stage" label="Stage" activeField={sortField} direction={sortDirection} onSort={onSort} />
              </th>
              <th scope="col" className="py-2.5 px-3">
                <span className="text-ui-xs font-semibold text-[#8b949e] uppercase tracking-wider">Missing</span>
              </th>
              <th scope="col" className="py-2.5 px-3" aria-sort={sortField === 'age' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}>
                <SortHeader field="age" label="Updated" activeField={sortField} direction={sortDirection} onSort={onSort} />
              </th>
              <th scope="col" className="py-2.5 px-3 text-right">
                <span className="text-ui-xs font-semibold text-[#8b949e] uppercase tracking-wider">Action</span>
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
