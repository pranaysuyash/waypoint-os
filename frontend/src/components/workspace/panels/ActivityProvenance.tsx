/**
 * ActivityProvenance - Badge component for activity source tracking.
 *
 * Shows whether an activity was:
 * - 🤖 SUGGESTED (by AI) with confidence %
 * - ✅ REQUESTED (by traveler)
 *
 * Color-coded:
 * - Suggested: blue background (AI-powered)
 * - Requested: green background (user-initiated)
 *
 * Used in ActivityTimeline and activity lists to provide operator clarity
 * on activity provenance.
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export type ActivitySource = 'suggested' | 'requested';

export interface ActivityProvenanceProps {
  source: ActivitySource;
  confidence?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * ActivityProvenanceBadge - Renders a badge showing activity source and confidence
 */
export const ActivityProvenanceBadge: React.FC<ActivityProvenanceProps> = ({
  source,
  confidence,
  className,
  size = 'md',
}) => {
  const isSuggested = source === 'suggested';
  const isRequested = source === 'requested';

  // Base styles
  const baseStyles = 'inline-flex items-center gap-1.5 rounded-md font-medium border transition-colors';

  // Size variants
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-ui-xs',
    md: 'px-2.5 py-1 text-ui-sm',
    lg: 'px-3 py-1.5 text-ui-base',
  };

  // Color variants for suggested (AI-powered)
  const suggestedStyles =
    'bg-[rgba(var(--accent-blue-rgb)/0.10)] text-accent-blue border-[rgba(var(--accent-blue-rgb)/0.25)] hover:bg-[rgba(var(--accent-blue-rgb)/0.18)] hover:border-[rgba(var(--accent-blue-rgb)/0.35)]';

  // Color variants for requested (user-initiated)
  const requestedStyles =
    'bg-[rgba(var(--accent-green-rgb)/0.10)] text-accent-green border-[rgba(var(--accent-green-rgb)/0.25)] hover:bg-[rgba(var(--accent-green-rgb)/0.18)] hover:border-[rgba(var(--accent-green-rgb)/0.35)]';

  const variantStyles = isSuggested ? suggestedStyles : requestedStyles;

  // Content
  const emoji = isSuggested ? '🤖' : '✅';
  const label = isSuggested ? 'SUGGESTED' : 'REQUESTED';
  const confidenceText = isSuggested && confidence !== undefined ? ` ${confidence}%` : '';

  return (
    <span
      className={cn(baseStyles, sizeStyles[size], variantStyles, className)}
      role="status"
      aria-label={`Activity ${label}${confidenceText}`}
    >
      <span className="inline-block">{emoji}</span>
      <span className="font-semibold">{label}</span>
      {isSuggested && confidence !== undefined && (
        <span className="font-mono text-ui-xs opacity-85">{confidenceText}</span>
      )}
    </span>
  );
};

/**
 * ActivityProvenanceGroup - Renders provenance badge with additional context
 *
 * Typically used in lists/tables where activity details are shown with source tracking.
 */
export interface ActivityProvenanceGroupProps {
  activityName: string;
  source: ActivitySource;
  confidence?: number;
  timestamp?: string;
  className?: string;
}

export const ActivityProvenanceGroup: React.FC<ActivityProvenanceGroupProps> = ({
  activityName,
  source,
  confidence,
  timestamp,
  className,
}) => {
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <div className="flex items-center gap-2">
        <span className="font-medium text-text-primary">{activityName}</span>
        <ActivityProvenanceBadge source={source} confidence={confidence} size="sm" />
      </div>
      {timestamp && <div className="text-ui-xs text-text-muted">{timestamp}</div>}
    </div>
  );
};

export default ActivityProvenanceBadge;
