/**
 * FilterPill
 *
 * Composable filter pill for inbox filter bar.
 * Supports active/inactive states, counts, and icons.
 */

'use client';

import { memo } from 'react';
import { cn } from '@/lib/utils';
import { COLORS } from '@/lib/tokens';

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
          'px-3 py-1 rounded-md text-[10px] font-bold uppercase transition-all',
          isActive
            ? 'bg-[#58a6ff] text-[#0d1117]'
            : 'text-[#8b949e] hover:text-[#e6edf3]',
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
        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors',
        isActive
          ? 'bg-[#161b22] text-[#e6edf3] border-l-2 border-[#58a6ff]'
          : 'text-[#8b949e] hover:text-[#e6edf3]',
        className
      )}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{label}</span>
      {count !== undefined && (
        <span
          className={cn(
            'tabular-nums px-1.5 py-0.5 rounded-md text-xs',
            isActive
              ? 'bg-[rgba(88,166,255,0.15)] text-[#58a6ff]'
              : 'bg-[#161b22] text-[#484f58]'
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
});

export default FilterPill;
