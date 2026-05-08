'use client';

import { memo } from 'react';
import { cn } from '@/lib/utils';

export type PillTone = 'neutral' | 'attention' | 'ownership' | 'risk';

export interface PillProps {
  label: string;
  count?: number;
  isActive?: boolean;
  onClick?: () => void;
  icon?: React.ReactNode;
  className?: string;
  variant?: 'default' | 'role';
  tone?: PillTone;
  muted?: boolean;
}

export const Pill = memo(function Pill({
  label,
  count,
  isActive = false,
  onClick,
  icon,
  className,
  variant = 'default',
  tone = 'neutral',
  muted = false,
}: PillProps) {
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

  const toneClasses: Record<PillTone, { idle: string; active: string; count: string }> = {
    neutral: {
      idle: 'text-text-muted hover:text-text-primary',
      active: 'bg-elevated text-text-primary',
      count: 'bg-elevated text-text-placeholder',
    },
    attention: {
      idle: 'text-[#d29922] hover:text-[#f2cc60] border border-[rgba(210,153,34,0.16)]',
      active: 'bg-[rgba(210,153,34,0.12)] text-[#f2cc60] border border-[rgba(210,153,34,0.28)]',
      count: 'bg-[rgba(210,153,34,0.12)] text-[#f2cc60]',
    },
    ownership: {
      idle: 'text-[#7ab9ff] hover:text-[#a5d6ff] border border-[rgba(88,166,255,0.16)]',
      active: 'bg-[rgba(88,166,255,0.12)] text-[#a5d6ff] border border-[rgba(88,166,255,0.28)]',
      count: 'bg-[rgba(88,166,255,0.12)] text-[#a5d6ff]',
    },
    risk: {
      idle: 'text-[#f85149] hover:text-[#ff8b85] border border-[rgba(248,81,73,0.18)]',
      active: 'bg-[rgba(248,81,73,0.12)] text-[#ff8b85] border border-[rgba(248,81,73,0.3)]',
      count: 'bg-[rgba(248,81,73,0.12)] text-[#ff8b85]',
    },
  };

  const toneMeta = toneClasses[tone];
  const idleClass = muted
    ? 'text-text-muted border border-[var(--border-default)] hover:text-text-primary'
    : toneMeta.idle;
  const activeClass = muted
    ? 'bg-elevated text-text-primary border border-[var(--border-default)]'
    : toneMeta.active;
  const countClass = muted ? 'bg-elevated text-text-placeholder' : toneMeta.count;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[var(--ui-text-xs)] font-semibold transition-colors border border-transparent',
        isActive ? activeClass : idleClass,
        className
      )}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{label}</span>
      {count !== undefined && (
        <span
          className={cn(
            'tabular-nums px-1.5 py-0.5 rounded-md text-[var(--ui-text-xs)]',
            isActive ? countClass : 'bg-elevated text-text-placeholder'
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
});
