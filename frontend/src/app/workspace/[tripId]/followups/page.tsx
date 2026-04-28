'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { Filter, AlertCircle, Loader2 } from 'lucide-react';
import FollowUpCard from '@/components/workspace/cards/FollowUpCard';
import { COLORS } from '@/lib/tokens';

interface FollowUp {
  trip_id: string;
  traveler_name: string;
  agent_name: string;
  due_date: string;
  status: 'pending' | 'completed' | 'snoozed';
  trip_status: string;
  days_until_due: number;
}

type FilterType = 'all' | 'due_today' | 'overdue' | 'upcoming';
type StatusType = 'all' | 'pending' | 'completed' | 'snoozed';

export default function FollowupsPage() {
  const params = useParams();
  const tripId = params?.tripId as string;

  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [statusFilter, setStatusFilter] = useState<StatusType>('all');
  const [sortBy, setSortBy] = useState<'due_date' | 'days_until_due'>('due_date');

  // Fetch followups from backend
  const fetchFollowups = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const filterParam = filterType === 'all' ? '' : `&filter=${filterType}`;
      const statusParam = statusFilter === 'all' ? '' : `&status=${statusFilter}`;

      const response = await fetch(
        `/api/followups/dashboard?${filterParam}${statusParam}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch followups: ${response.statusText}`);
      }

      const data = await response.json();
      setFollowups(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [filterType, statusFilter]);

  // Re-fetch when filters change
  useEffect(() => {
    fetchFollowups();
  }, [fetchFollowups]);

  // Handle complete action
  const handleComplete = useCallback(async (followupTripId: string) => {
    try {
      const response = await fetch(`/api/followups/${followupTripId}/mark-complete`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error('Failed to mark complete');
      }

      // Refresh the list
      await fetchFollowups();
    } catch (err) {
      console.error('Error marking complete:', err);
    }
  }, [fetchFollowups]);

  // Handle snooze action
  const handleSnooze = useCallback(
    async (followupTripId: string, days: number) => {
      try {
        const response = await fetch(
          `/api/followups/${followupTripId}/snooze?days=${days}`,
          {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to snooze');
        }

        // Refresh the list
        await fetchFollowups();
      } catch (err) {
        console.error('Error snoozing:', err);
      }
    },
    [fetchFollowups]
  );

  // Handle reschedule action
  const handleReschedule = useCallback(
    async (followupTripId: string, newDate: string) => {
      try {
        const response = await fetch(`/api/followups/${followupTripId}/reschedule`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_date: newDate }),
        });

        if (!response.ok) {
          throw new Error('Failed to reschedule');
        }

        // Refresh the list
        await fetchFollowups();
      } catch (err) {
        console.error('Error rescheduling:', err);
      }
    },
    [fetchFollowups]
  );

  // Sort followups
  const sortedFollowups = [...followups].sort((a, b) => {
    if (sortBy === 'due_date') {
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
    } else {
      return a.days_until_due - b.days_until_due;
    }
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold" style={{ color: COLORS.textPrimary }}>
            Follow-up Reminders
          </h1>
          {followups.length > 0 && (
            <span
              className="text-sm font-medium px-3 py-1 rounded"
              style={{ color: COLORS.textSecondary, background: COLORS.bgDefault }}
            >
              {followups.length} follow-up{followups.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <p style={{ color: COLORS.textSecondary }}>
          Manage follow-up reminders for promised calls and communications.
        </p>
      </div>

      {/* Filters & Sorting */}
      <div className="flex flex-col gap-4 p-4 rounded-lg border" style={{ borderColor: COLORS.borderDefault }}>
        <div className="flex items-center gap-2 mb-2">
          <Filter className="w-4 h-4" style={{ color: COLORS.textMuted }} />
          <h3 className="text-sm font-semibold" style={{ color: COLORS.textPrimary }}>
            Filters
          </h3>
        </div>

        {/* Filter Buttons */}
        <div className="flex flex-wrap gap-2">
          {(['all', 'due_today', 'overdue', 'upcoming'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setFilterType(filter)}
              className="px-3 py-2 rounded text-xs font-medium transition-colors border"
              style={{
                color: filterType === filter ? '#fff' : COLORS.textSecondary,
                background:
                  filterType === filter
                    ? COLORS.accentBlue
                    : COLORS.bgDefault,
                borderColor:
                  filterType === filter
                    ? COLORS.accentBlue
                    : COLORS.borderDefault,
              }}
            >
              {filter === 'all'
                ? 'All'
                : filter === 'due_today'
                ? 'Due Today'
                : filter === 'overdue'
                ? 'Overdue'
                : 'Upcoming'}
            </button>
          ))}
        </div>

        {/* Status Filter */}
        <div>
          <label className="text-xs font-medium" style={{ color: COLORS.textMuted }}>
            Status:
          </label>
          <div className="flex flex-wrap gap-2 mt-1">
            {(['all', 'pending', 'completed', 'snoozed'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className="px-3 py-1 rounded text-xs font-medium transition-colors border"
                style={{
                  color:
                    statusFilter === status
                      ? '#fff'
                      : COLORS.textSecondary,
                  background:
                    statusFilter === status
                      ? COLORS.accentBlue
                      : 'transparent',
                  borderColor:
                    statusFilter === status
                      ? COLORS.accentBlue
                      : COLORS.borderDefault,
                }}
              >
                {status === 'all'
                  ? 'All'
                  : status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Sort Options */}
        <div>
          <label className="text-xs font-medium" style={{ color: COLORS.textMuted }}>
            Sort by:
          </label>
          <div className="flex gap-2 mt-1">
            {(['due_date', 'days_until_due'] as const).map((sort) => (
              <button
                key={sort}
                onClick={() => setSortBy(sort)}
                className="px-3 py-1 rounded text-xs font-medium transition-colors border"
                style={{
                  color:
                    sortBy === sort
                      ? '#fff'
                      : COLORS.textSecondary,
                  background:
                    sortBy === sort
                      ? COLORS.accentBlue
                      : 'transparent',
                  borderColor:
                    sortBy === sort
                      ? COLORS.accentBlue
                      : COLORS.borderDefault,
                }}
              >
                {sort === 'due_date'
                  ? 'Date'
                  : 'Days Until Due'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin" style={{ color: COLORS.textMuted }} />
          <span className="ml-2" style={{ color: COLORS.textSecondary }}>
            Loading follow-ups...
          </span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div
          className="p-4 rounded-lg border flex items-start gap-3"
          style={{
            borderColor: COLORS.accentRed,
            background: 'rgba(248,81,73,0.08)',
          }}
        >
          <AlertCircle
            className="w-5 h-5 shrink-0 mt-0.5"
            style={{ color: COLORS.accentRed }}
          />
          <div>
            <p className="text-sm font-medium" style={{ color: COLORS.accentRed }}>
              Error loading follow-ups
            </p>
            <p className="text-xs mt-1" style={{ color: COLORS.textSecondary }}>
              {error}
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && followups.length === 0 && (
        <div
          className="p-8 rounded-lg border text-center"
          style={{
            borderColor: COLORS.borderDefault,
            background: COLORS.bgElevated,
          }}
        >
          <p style={{ color: COLORS.textSecondary }}>
            No follow-ups scheduled.
          </p>
        </div>
      )}

      {/* Follow-ups Grid */}
      {!loading && !error && sortedFollowups.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedFollowups.map((followup) => (
            <FollowUpCard
              key={followup.trip_id}
              tripId={followup.trip_id}
              travelerName={followup.traveler_name}
              agentName={followup.agent_name}
              dueDate={followup.due_date}
              status={followup.status}
              daysUntilDue={followup.days_until_due}
              onComplete={handleComplete}
              onSnooze={handleSnooze}
              onReschedule={handleReschedule}
            />
          ))}
        </div>
      )}
    </div>
  );
}
