'use client';

import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

export interface StatusConfig {
  label: string;
  color: string;
  icon: LucideIcon;
}

export type StatusMap = Record<string, StatusConfig>;

export interface StatusBadgeProps {
  status: string;
  map: StatusMap;
  size?: 'sm' | 'md';
  className?: string;
}

const SIZE_CLASSES = {
  sm: 'text-ui-xs px-2 py-0.5',
  md: 'text-ui-sm px-2.5 py-1',
};

export function StatusBadge({
  status,
  map,
  size = 'sm',
  className,
}: StatusBadgeProps) {
  const config = map[status];
  if (!config) return null;

  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md font-semibold',
        SIZE_CLASSES[size],
        className
      )}
      style={{
        color: config.color,
        background: `${config.color}1a`,
        border: `1px solid ${config.color}33`,
      }}
    >
      <Icon className="size-3.5 shrink-0" />
      {config.label}
    </span>
  );
}
