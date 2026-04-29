"use client";

import { useEffect, useState } from "react";
import type { TimelineResponse } from "@/types/spine";
import { STAGE_LABELS, STATUS_LABELS, labelOrTitle } from "@/lib/label-maps";

interface TimelineSummaryProps {
  tripId: string;
}

const AVAILABLE_STAGES = ["intake", "packet", "decision", "strategy", "safety"];

export function TimelineSummary({ tripId }: TimelineSummaryProps) {
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tripId) return;
    const fetchTimeline = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await fetch(`/api/trips/${tripId}/timeline`, {
          credentials: "include",
          cache: "no-store",
        });
        if (!response.ok) throw new Error(`Failed to fetch timeline: ${response.statusText}`);
        const data = await response.json();
        setTimeline(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load timeline");
      } finally {
        setIsLoading(false);
      }
    };
    fetchTimeline();
  }, [tripId]);

  if (isLoading) {
    return (
      <div className="p-4 text-center">
        <p className="text-ui-xs text-text-muted">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <p className="text-ui-xs text-accent-red">{error}</p>
      </div>
    );
  }

  const events = timeline?.events ?? [];

  if (events.length === 0) {
    return (
      <div className="p-4 text-center">
        <p className="text-ui-xs text-text-muted">No events yet</p>
      </div>
    );
  }

  const lastEvent = events[events.length - 1];
  const stageCounts: Record<string, number> = {};
  const statusCounts: Record<string, number> = {};
  for (const event of events) {
    stageCounts[event.stage] = (stageCounts[event.stage] || 0) + 1;
    statusCounts[event.status] = (statusCounts[event.status] || 0) + 1;
  }

  return (
    <div className="p-4 space-y-4" data-testid="timeline-summary">
      <div>
        <h3 className="text-ui-sm font-semibold text-text-primary mb-3">Timeline Summary</h3>
        <dl className="space-y-2">
          <div className="flex justify-between items-center">
            <dt className="text-ui-xs text-text-muted">Events</dt>
            <dd className="text-ui-sm font-medium text-text-primary">{events.length}</dd>
          </div>
          <div className="flex justify-between items-center">
            <dt className="text-ui-xs text-text-muted">Last event</dt>
            <dd className="text-ui-xs text-text-secondary">
              {new Date(lastEvent.timestamp).toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
                hour12: true,
              })}
            </dd>
          </div>
          <div className="flex justify-between items-center">
            <dt className="text-ui-xs text-text-muted">Current stage</dt>
            <dd className="text-ui-xs font-medium text-text-primary">
              {labelOrTitle(STAGE_LABELS, lastEvent.stage)}
            </dd>
          </div>
        </dl>
      </div>

      <div>
        <h4 className="text-ui-xs font-semibold text-text-muted uppercase tracking-wider mb-2">By Stage</h4>
        <div className="space-y-1">
          {AVAILABLE_STAGES.map((stage) => {
            const count = stageCounts[stage] || 0;
            if (count === 0) return null;
            return (
              <div key={stage} className="flex justify-between items-center">
                <span className="text-ui-xs text-text-secondary">{labelOrTitle(STAGE_LABELS, stage)}</span>
                <span className="text-ui-xs font-mono text-text-muted">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
