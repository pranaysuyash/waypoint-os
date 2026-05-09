import { useClientTime } from '@/hooks/useClientDate';

/**
 * ActivityTimeline - Display all trip activities grouped by day with provenance.
 *
 * Shows:
 * - Activities grouped by date (Date headers with activities below)
 * - Each activity with source badge (suggested or requested)
 * - Confidence % for suggested activities
 * - Sortable by date (newest/oldest)
 *
 * Used in workspace to give operators full transparency on activity provenance
 * and help them distinguish AI suggestions from traveler requests.
 */

'use client';

import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { ActivityProvenanceBadge, ActivitySource } from './ActivityProvenance';
import { cn } from '@/lib/utils';

export interface Activity {
  id?: string;
  name: string;
  source: ActivitySource;
  confidence?: number;
  timestamp?: string;
  description?: string;
}

export interface ActivityTimelineProps {
  activities: Activity[];
  sortOrder?: 'newest' | 'oldest';
  onSortChange?: (order: 'newest' | 'oldest') => void;
  className?: string;
  showEmpty?: boolean;
}

type GroupedActivities = Record<string, Activity[]>;

/**
 * Parse ISO timestamp to date string for grouping
 */
function getDateFromTimestamp(timestamp?: string): string {
  if (!timestamp) return 'No date';

  try {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid date';

    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return 'Invalid date';
  }
}

/**
 * Group activities by date
 */
function groupActivitiesByDate(activities: Activity[]): GroupedActivities {
  const grouped: GroupedActivities = {};

  activities.forEach((activity) => {
    const dateKey = getDateFromTimestamp(activity.timestamp);
    if (!grouped[dateKey]) {
      grouped[dateKey] = [];
    }
    grouped[dateKey].push(activity);
  });

  return grouped;
}

/**
 * Sort date groups in chronological order
 */
function sortDateGroups(
  grouped: GroupedActivities,
  order: 'newest' | 'oldest'
): [string, Activity[]][] {
  const parseDate = (dateStr: string): Date => {
    if (dateStr === 'No date' || dateStr === 'Invalid date') {
      return new Date(0);
    }
    return new Date(dateStr);
  };

  return Object.entries(grouped).sort(([dateA], [dateB]) => {
    const timeA = parseDate(dateA).getTime();
    const timeB = parseDate(dateB).getTime();

    return order === 'newest' ? timeB - timeA : timeA - timeB;
  });
}

/**
 * ActivityTimeline - Display activities grouped by day with provenance badges
 */
export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
  activities,
  sortOrder = 'newest',
  onSortChange,
  className,
  showEmpty = true,
}) => {
  const [expandedDates, setExpandedDates] = useState<Set<string>>(
    new Set(activities.length > 0 ? [getDateFromTimestamp(activities[0]?.timestamp)] : [])
  );
  const [currentSortOrder, setCurrentSortOrder] = useState<'newest' | 'oldest'>(sortOrder);

  // Group and sort activities
  const grouped = useMemo(() => groupActivitiesByDate(activities), [activities]);
  const sortedDates = useMemo(
    () => sortDateGroups(grouped, currentSortOrder),
    [grouped, currentSortOrder]
  );

  const handleSortChange = (order: 'newest' | 'oldest') => {
    setCurrentSortOrder(order);
    onSortChange?.(order);
  };

  const toggleDateExpanded = (dateKey: string) => {
    const newExpanded = new Set(expandedDates);
    if (newExpanded.has(dateKey)) {
      newExpanded.delete(dateKey);
    } else {
      newExpanded.add(dateKey);
    }
    setExpandedDates(newExpanded);
  };

  if (activities.length === 0) {
    return showEmpty ? (
      <div className={cn('p-4 text-center text-ui-sm text-text-muted', className)}>
        No activities recorded yet.
      </div>
    ) : null;
  }

  return (
    <div className={cn('w-full space-y-4', className)}>
      {/* Sort Controls */}
      <div className="flex items-center gap-2 border-b pb-4">
        <span className="text-ui-xs font-semibold text-text-secondary uppercase">Sort:</span>
        <button
          onClick={() => handleSortChange('newest')}
          className={cn(
            'px-3 py-1 rounded text-ui-xs font-medium transition-colors',
            currentSortOrder === 'newest'
              ? 'bg-[rgba(var(--accent-blue-rgb)/0.18)] text-accent-blue'
              : 'bg-elevated text-text-secondary hover:bg-elevated'
          )}
        >
          Newest First
        </button>
        <button
          onClick={() => handleSortChange('oldest')}
          className={cn(
            'px-3 py-1 rounded text-ui-xs font-medium transition-colors',
            currentSortOrder === 'oldest'
              ? 'bg-[rgba(var(--accent-blue-rgb)/0.18)] text-accent-blue'
              : 'bg-elevated text-text-secondary hover:bg-elevated'
          )}
        >
          Oldest First
        </button>
      </div>

      {/* Date Groups */}
      <div className="space-y-4">
        {sortedDates.map(([dateKey, dateActivities]) => {
          const isExpanded = expandedDates.has(dateKey);
          const suggestedCount = dateActivities.filter((a) => a.source === 'suggested').length;
          const requestedCount = dateActivities.filter((a) => a.source === 'requested').length;

          return (
            <div key={dateKey} className="border rounded-lg overflow-hidden">
              {/* Date Header */}
              <button
                onClick={() => toggleDateExpanded(dateKey)}
                className="w-full px-4 py-3 bg-surface hover:bg-elevated flex items-center justify-between transition-colors"
              >
                <div className="text-left">
                  <h3 className="font-semibold text-text-primary">{dateKey}</h3>
                  <p className="text-ui-xs text-text-secondary mt-1">
                    {suggestedCount > 0 && (
                      <span>
                        🤖 {suggestedCount} suggested{suggestedCount !== 1 ? 's' : ''}
                      </span>
                    )}
                    {suggestedCount > 0 && requestedCount > 0 && <span> • </span>}
                    {requestedCount > 0 && (
                      <span>
                        ✅ {requestedCount} requested
                      </span>
                    )}
                  </p>
                </div>
                {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>

              {/* Activities List */}
              {isExpanded && (
                <div className="divide-y">
                  {dateActivities.map((activity, idx) => (
                    <div
                      key={activity.id || idx}
                      className="px-4 py-3 hover:bg-[rgba(var(--accent-blue-rgb)/0.10)] transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <p className="font-medium text-text-primary">{activity.name}</p>
                          {activity.description && (
                            <p className="text-ui-sm text-text-secondary mt-1">{activity.description}</p>
                          )}
                          {activity.timestamp && (
                            <p className="text-ui-xs text-text-muted mt-1">
                              {useClientTime(activity.timestamp, {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </p>
                          )}
                        </div>
                        <ActivityProvenanceBadge
                          source={activity.source}
                          confidence={activity.confidence}
                          size="sm"
                          className="flex-shrink-0 mt-0.5"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ActivityTimeline;
