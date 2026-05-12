"use client";

import { useEffect, useReducer } from "react";
import type { TimelineResponse } from "@/types/spine";
import { STAGE_LABELS, STATUS_LABELS, labelOrTitle } from "@/lib/label-maps";
import {
  getTimelineEventTitle,
  getTimelineStageLabel,
} from "@/lib/timeline-rail";
import { ClientTime } from "@/hooks/useClientDate";

interface TimelineSummaryProps {
  tripId: string;
  timeline?: TimelineResponse | null;
  loading?: boolean;
  error?: string | null;
}

const AVAILABLE_STAGES = ["intake", "packet", "decision", "strategy", "safety"];

type TimelineFetchState =
  | { status: "loading"; timeline: TimelineResponse | null; error: null }
  | { status: "success"; timeline: TimelineResponse; error: null }
  | { status: "error"; timeline: TimelineResponse | null; error: string };

type TimelineFetchAction =
  | { type: "loading" }
  | { type: "loaded"; timeline: TimelineResponse }
  | { type: "failed"; error: string };

function timelineFetchReducer(
  state: TimelineFetchState,
  action: TimelineFetchAction,
): TimelineFetchState {
  switch (action.type) {
    case "loading":
      return { status: "loading", timeline: state.timeline, error: null };
    case "loaded":
      return { status: "success", timeline: action.timeline, error: null };
    case "failed":
      return { status: "error", timeline: state.timeline, error: action.error };
    default:
      return state;
  }
}

export function TimelineSummary({ tripId, timeline: providedTimeline, loading: providedLoading, error: providedError }: TimelineSummaryProps) {
  const [fetchState, dispatch] = useReducer(timelineFetchReducer, {
    status: "loading",
    timeline: null,
    error: null,
  });
  const shouldFetch = providedTimeline === undefined && providedLoading === undefined && providedError === undefined;

  useEffect(() => {
    if (!shouldFetch) return;
    if (!tripId) return;
    const fetchTimeline = async () => {
      try {
        dispatch({ type: "loading" });
        const response = await fetch(`/api/trips/${tripId}/timeline`, {
          credentials: "include",
          cache: "no-store",
        });
        if (!response.ok) throw new Error(`Failed to fetch timeline: ${response.statusText}`);
        const data = await response.json();
        dispatch({ type: "loaded", timeline: data });
      } catch (err) {
        dispatch({ type: "failed", error: err instanceof Error ? err.message : "Failed to load timeline" });
      }
    };
    fetchTimeline();
  }, [tripId, shouldFetch]);

  const resolvedTimeline = shouldFetch ? fetchState.timeline : (providedTimeline ?? null);
  const resolvedLoading = shouldFetch ? fetchState.status === "loading" : Boolean(providedLoading);
  const resolvedError = shouldFetch ? fetchState.error : (providedError ?? null);

  if (resolvedLoading) {
    return (
      <div className="p-4 text-center">
        <p className="text-ui-xs text-text-muted">Loading…</p>
      </div>
    );
  }

  if (resolvedError) {
    return (
      <div className="p-4">
        <p className="text-ui-xs text-accent-red">{resolvedError}</p>
      </div>
    );
  }

  const events = resolvedTimeline?.events ?? [];

  if (events.length === 0) {
    return (
      <div className="p-4 text-center">
        <p className="text-ui-xs font-medium text-text-secondary">No activity yet</p>
        <p className="text-ui-xs text-text-muted mt-2">Activity will appear here when customer details are updated, follow-ups are drafted, options are built, or quotes are approved.</p>
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
              <ClientTime value={lastEvent.timestamp} options={{
                hour: "2-digit",
                minute: "2-digit",
                hour12: true,
              }} />
            </dd>
          </div>
            <div className="flex justify-between items-center">
              <dt className="text-ui-xs text-text-muted">Current stage</dt>
              <dd className="text-ui-xs font-medium text-text-primary">
                {getTimelineStageLabel(lastEvent.stage)}
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

      <div>
        <h4 className="text-ui-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Recent Events</h4>
        <div className="space-y-2">
          {events.slice(-5).reverse().map((event) => (
            <div key={`${event.timestamp}-${event.stage}`} className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] px-3 py-2">
              <p className="text-ui-xs font-medium text-text-primary">{getTimelineEventTitle(event)}</p>
              <p className="mt-1 text-[12px] text-text-secondary">
                {getTimelineStageLabel(event.stage)} · {labelOrTitle(STATUS_LABELS, event.status)}
              </p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
