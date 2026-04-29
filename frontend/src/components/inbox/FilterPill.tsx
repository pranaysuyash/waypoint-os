/**
 * FilterPill
 *
 * Composable filter pill for inbox filter bar.
 * Supports active/inactive states, counts, and icons.
 */

'use client';

import { memo } from 'react';
import { cn } from '@/lib/utils';

export interface FilterPillProps {
  label: string;
  count?: number;
  isActive?: boolean;
  onClick?: () => void;
  icon?: React.ReactNode;
  className?: string;
  variant?: 'default' | 'role';
}

export const FilterPill = memo(function FilterPill({
  label,
  count,
  isActive = false,
  onClick,
  icon,
  className,
  variant = 'default',
}: FilterPillProps) {
  if (variant === 'role') {
    return (
      <button
        type="button"
        onClick={onClick}
        className={cn(
          'px-3 py-1 rounded-md text-[var(--ui-text-xs)] font-bold uppercase transition-all',
          isActive
            ? 'bg-accent-blue text-text-on-accent'
            : 'text-text-muted hover:text-text-primary',
          className
        )}
      >
        {icon && <span className="mr-1">{icon}</span>}
        {label}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[var(--ui-text-xs)] font-semibold transition-colors',
          isActive
            ? 'bg-elevated text-text-primary'
            : 'text-text-muted hover:text-text-primary',
        className
      )}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{label}</span>
      {count !== undefined && (
        <span
          className={cn(
            'tabular-nums px-1.5 py-0.5 rounded-md text-[var(--ui-text-xs)]',
              isActive
                ? 'bg-[rgba(var(--accent-blue-rgb),0.15)] text-accent-blue'
                : 'bg-elevated text-text-placeholder'
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
});

export default FilterPill;
