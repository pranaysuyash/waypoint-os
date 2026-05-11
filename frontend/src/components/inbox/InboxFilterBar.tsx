/**
 * InboxFilterBar
 *
 * Single-row lead filters for the agency inbox.
 */

'use client';

import { memo } from 'react';
import { FilterPill } from './FilterPill';

export type FilterKey = 'all' | 'at_risk' | 'incomplete' | 'unassigned';

export interface FilterConfig {
  key: FilterKey;
  label: string;
  count: number;
  tone?: 'neutral' | 'attention' | 'ownership' | 'risk';
  muted?: boolean;
}

export interface InboxFilterBarProps {
  activeFilter: FilterKey;
  onFilterChange: (filter: FilterKey) => void;
  filters: FilterConfig[];
  className?: string;
}

export const InboxFilterBar = memo(function InboxFilterBar({
  activeFilter,
  onFilterChange,
  filters,
  className,
}: InboxFilterBarProps) {
  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-1.5" role="tablist" aria-label="Lead inbox filters">
        {filters.map((filter) => (
          <FilterPill
            key={filter.key}
            label={filter.label}
            count={filter.count}
            isActive={activeFilter === filter.key}
            onClick={() => onFilterChange(filter.key)}
            tone={filter.tone}
            muted={filter.muted}
          />
        ))}
      </div>
    </div>
  );
});

