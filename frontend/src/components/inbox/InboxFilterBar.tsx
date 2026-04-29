/**
 * InboxFilterBar
 *
 * Composable filter bar with standard filters, presets, and role switcher.
 */

'use client';

import { memo } from 'react';
import { LayoutGrid, Shield } from 'lucide-react';
import { FilterPill } from './FilterPill';

export type FilterKey = 'all' | 'at_risk' | 'critical' | 'unassigned';
export type RoleKey = 'ops' | 'mgr';

export interface FilterConfig {
  key: FilterKey;
  label: string;
  count: number;
}

export interface PresetConfig {
  key: string;
  label: string;
  count: number;
  icon?: React.ReactNode;
}

export interface InboxFilterBarProps {
  activeFilter: FilterKey;
  onFilterChange: (filter: FilterKey) => void;
  activeRole: RoleKey;
  onRoleChange: (role: RoleKey) => void;
  filters: FilterConfig[];
  presets: PresetConfig[];
  className?: string;
}

export const InboxFilterBar = memo(function InboxFilterBar({
  activeFilter,
  onFilterChange,
  activeRole,
  onRoleChange,
  filters,
  presets,
  className,
}: InboxFilterBarProps) {
  return (
    <div className={className}>
      {/* Role Switcher (as filter pills) */}
      <div className="flex items-center gap-1 mb-2">
        <span className="text-[var(--ui-text-xs)] uppercase text-text-placeholder font-medium mr-1">View:</span>
        <FilterPill
          label="Ops"
          isActive={activeRole === 'ops'}
          onClick={() => onRoleChange('ops')}
          variant="role"
          icon={<LayoutGrid className="w-3 h-3 inline" />}
        />
        <FilterPill
          label="Lead"
          isActive={activeRole === 'mgr'}
          onClick={() => onRoleChange('mgr')}
          variant="role"
          icon={<Shield className="w-3 h-3 inline" />}
        />
      </div>

      {/* Presets */}
      {presets.length > 0 && (
        <div className="flex items-center gap-1 mb-2">
          <span className="text-[var(--ui-text-xs)] uppercase text-text-placeholder font-medium mr-1">Quick:</span>
          {presets.map((preset) => (
            <FilterPill
              key={preset.key}
              label={preset.label}
              count={preset.count}
              isActive={activeFilter === preset.key as FilterKey}
              onClick={() => onFilterChange(preset.key as FilterKey)}
              icon={preset.icon}
            />
          ))}
        </div>
      )}

      {/* Standard Filters */}
      <div className="flex items-center gap-1" role="tablist">
        <span className="text-[var(--ui-text-xs)] uppercase text-text-placeholder font-medium mr-1">Filter:</span>
        {filters.map((filter) => (
          <FilterPill
            key={filter.key}
            label={filter.label}
            count={filter.count}
            isActive={activeFilter === filter.key}
            onClick={() => onFilterChange(filter.key)}
          />
        ))}
      </div>
    </div>
  );
});

export default InboxFilterBar;
