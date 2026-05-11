"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { Trip } from "@/lib/api-client";
import type { TimelineEvent, TimelineResponse, SuitabilityFlag, OverrideData } from "@/types/spine";
import { STAGE_LABELS, STATUS_LABELS, labelOrTitle } from "@/lib/label-maps";
import { SuitabilitySignal } from "./SuitabilitySignal";
import { OverrideTimelineEvent } from "./OverrideTimelineEvent";

interface TimelinePanelProps {
  trip?: Trip | null;
  tripId?: string;
  onStageFilter?: (stage: string | null) => void;
}

const STAGE_COLORS: Record<string, { bg: string; badge: string; dot: string }> = {
  intake: { bg: "bg-[rgba(var(--accent-blue-rgb)/0.06)]", badge: "bg-[rgba(var(--accent-blue-rgb)/0.12)] text-accent-blue", dot: "bg-accent-blue" },
  packet: { bg: "bg-[rgba(var(--accent-amber-rgb)/0.06)]", badge: "bg-[rgba(var(--accent-amber-rgb)/0.12)] text-accent-amber", dot: "bg-accent-amber" },
  decision: { bg: "bg-[rgba(var(--accent-green-rgb)/0.06)]", badge: "bg-[rgba(var(--accent-green-rgb)/0.12)] text-accent-green", dot: "bg-accent-green" },
  strategy: { bg: "bg-[rgba(var(--accent-purple-rgb)/0.06)]", badge: "bg-[rgba(var(--accent-purple-rgb)/0.12)] text-accent-purple", dot: "bg-accent-purple" },
  safety: { bg: "bg-[rgba(var(--accent-red-rgb)/0.06)]", badge: "bg-[rgba(var(--accent-red-rgb)/0.12)] text-accent-red", dot: "bg-accent-red" },
};

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
}

function TimelineEventCard({
  event,
  isLast,
}: {
  event: TimelineEvent;
  isLast: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const colors = STAGE_COLORS[event.stage] || STAGE_COLORS.intake;
  const detailsId = `timeline-details-${event.timestamp}-${event.stage}`;

  return (
    <div className="relative" role="listitem">
      {!isLast && (
        <div className="absolute left-5 top-12 w-0.5 h-8 bg-border-default" />
      )}

      <div className={`flex gap-4 ${colors.bg} p-4 rounded-lg border border-border-default`}>
        {/* Timeline dot */}
        <div className="flex-shrink-0">
          <div className={`size-3 rounded-full ${colors.dot} mt-1`} />
        </div>

        {/* Event content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-ui-xs font-semibold px-2 py-1 rounded ${colors.badge}`}>
                {labelOrTitle(STAGE_LABELS, event.stage)}
              </span>
              <span className="text-ui-sm font-medium text-text-secondary">
                {labelOrTitle(STATUS_LABELS, event.status)}
              </span>
            </div>
            <span className="text-ui-xs text-text-muted whitespace-nowrap">
              {formatTimestamp(event.timestamp)}
            </span>
          </div>

          {/* Optional details */}
          {(event.decision || event.reason) && (
            <div className="mt-2 flex items-start gap-2">
              <div className="flex-1">
                {event.decision && (
                  <p className="text-ui-xs text-text-muted">
                    <span className="font-semibold">Decision:</span> {event.decision}
                  </p>
                )}
                {event.reason && (
                  <p className="text-ui-xs text-text-muted mt-1">
                    <span className="font-semibold">Reason:</span> {event.reason}
                  </p>
                )}
                {event.actor && (
                  <p className="text-ui-xs text-text-muted mt-1">
                    <span className="font-semibold">By:</span> {event.actor}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Expandable JSON */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            aria-expanded={isExpanded}
            aria-controls={detailsId}
            className="mt-2 flex items-center gap-1 text-ui-xs text-text-muted hover:text-text-secondary transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="size-3" />
            ) : (
              <ChevronRight className="size-3" />
            )}
            <span>Show Details</span>
          </button>

          {isExpanded && (
            <div
              id={detailsId}
              className="mt-2 p-2 bg-elevated rounded border border-border-default overflow-x-auto"
            >
              <pre className="text-ui-xs text-text-muted font-mono">
                {JSON.stringify(event, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const AVAILABLE_STAGES = ["intake", "packet", "decision", "strategy", "safety"];

export function TimelinePanel({ trip: propTrip, tripId: propTripId, onStageFilter }: TimelinePanelProps) {
  // Derive tripId directly from props so the effect re-runs when the trip changes
  const tripId = propTripId || propTrip?.id;
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [suitabilityFlags, setSuitabilityFlags] = useState<SuitabilityFlag[]>([]);
  const [overrides, setOverrides] = useState<OverrideData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  const handleStageFilter = (stage: string | null) => {
    setSelectedStage(stage);
    onStageFilter?.(stage);
  };

  const fetchAll = useCallback(async () => {
    if (!tripId) return;

    try {
      setIsLoading(true);
      setError(null);

      // Fetch timeline
      const timelineUrl = selectedStage
        ? `/api/trips/${tripId}/timeline?stage=${selectedStage}`
        : `/api/trips/${tripId}/timeline`;
      const timelineResponse = await fetch(timelineUrl, {
        credentials: "include",
        cache: "no-store",
      });
      if (!timelineResponse.ok) {
        throw new Error(`Failed to fetch timeline: ${timelineResponse.statusText}`);
      }
      const timelineData = await timelineResponse.json();
      setTimeline(timelineData);

      // Fetch suitability flags
      try {
        const suitabilityUrl = `/api/trips/${tripId}/suitability`;
        const suitabilityResponse = await fetch(suitabilityUrl, {
          credentials: "include",
          cache: "no-store",
        });
        if (suitabilityResponse.ok) {
          const suitabilityData = await suitabilityResponse.json();
          setSuitabilityFlags(suitabilityData.suitability_flags || []);
        }
      } catch (_err) {
        // Silently fail if suitability endpoint not available
      }

      // Fetch overrides
      try {
        const overridesUrl = `/api/trips/${tripId}/overrides`;
        const overridesResponse = await fetch(overridesUrl, {
          credentials: "include",
          cache: "no-store",
        });
        if (overridesResponse.ok) {
          const overridesData = await overridesResponse.json();
          setOverrides(overridesData.overrides || []);
        }
      } catch (_err) {
        // Silently fail if overrides endpoint not available
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load timeline");
    } finally {
      setIsLoading(false);
    }
  }, [tripId, selectedStage]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const events = timeline?.events ?? [];

  // Merge timeline events with override events, sorted by timestamp
  // Override events: show them regardless of stage filter because they don't
  // have a stage field that maps to the timeline stage filter. They represent
  // operator actions that are relevant context regardless of which stage is selected.
  const mergedItems: Array<{ type: "event" | "override"; data: TimelineEvent | OverrideData; timestamp: string }> = [
    ...events.map((e) => ({ type: "event" as const, data: e, timestamp: e.timestamp })),
    ...overrides.map((o) => ({ type: "override" as const, data: o, timestamp: o.created_at })),
  ];
  mergedItems.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  const totalCount = mergedItems.length;

  return isLoading ? (
    <div className="p-6 text-center">
      <p className="text-ui-sm text-text-muted">Loading timeline…</p>
    </div>
  ) : error ? (
    <div className="p-6">
      <div className="rounded-lg border border-[rgba(var(--accent-red-rgb)/0.3)] bg-[rgba(var(--accent-red-rgb)/0.06)] p-4">
        <p className="text-ui-sm text-accent-red">{error}</p>
        <button
          onClick={() => fetchAll()}
          className="mt-3 text-ui-sm px-3 py-1.5 rounded-md bg-accent-red text-text-on-accent hover:opacity-90 transition-opacity"
        >
          Retry
        </button>
      </div>
    </div>
  ) : events.length === 0 && suitabilityFlags.length === 0 && overrides.length === 0 ? (
    <div className="p-6 text-center">
      <p className="text-ui-sm font-medium text-text-primary">No activity yet</p>
      <p className="text-ui-xs text-text-muted mt-2">Activity will appear when customer details are updated, follow-ups are drafted, options are built, or quotes are approved.</p>
    </div>
  ) : (
    <div className="p-6" data-testid="timeline-panel">
      <div className="space-y-4">
        {/* Suitability Flags Section */}
        {suitabilityFlags.length > 0 && (
          <div className="mb-6">
            <h3 className="text-md font-semibold text-text-primary mb-3">
              Suitability Assessment
            </h3>
            <SuitabilitySignal 
              flags={suitabilityFlags.map((flag) => ({
                flag_type: flag.name,
                severity: flag.tier as "low" | "medium" | "high" | "critical",
                reason: flag.reason || "",
                confidence: flag.confidence / 100, // Convert 0-100 to 0-1
              }))}
              tripId={tripId}
            />
          </div>
        )}

        <div>
          <h2 className="text-ui-lg font-semibold text-text-primary mb-3">
            Decision Timeline
          </h2>
          
          {/* Stage Filter */}
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              onClick={() => handleStageFilter(null)}
              aria-pressed={selectedStage === null}
              className={`px-3 py-1.5 text-ui-sm rounded-md font-medium transition-colors ${
                selectedStage === null
                  ? "bg-accent-blue text-text-on-accent"
                  : "bg-elevated text-text-muted hover:bg-highlight hover:text-text-primary"
              }`}
            >
              All
            </button>
            {AVAILABLE_STAGES.map((stage) => (
              <button
                key={stage}
                onClick={() => handleStageFilter(stage)}
                aria-pressed={selectedStage === stage}
                className={`px-3 py-1.5 text-ui-sm rounded-md font-medium transition-colors ${
                  selectedStage === stage
                    ? `${STAGE_COLORS[stage]?.badge} opacity-100`
                    : "bg-elevated text-text-muted hover:bg-highlight hover:text-text-primary"
                }`}
              >
                {labelOrTitle(STAGE_LABELS, stage)}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Events + Overrides */}
        <div className="space-y-3" role="list" aria-label="Timeline events">
          {mergedItems.map((item, index) => {
            if (item.type === "override") {
              const override = item.data as OverrideData;
              return (
                <div key={`override-${override.override_id || override.created_at}`} role="listitem">
                  <OverrideTimelineEvent event={override} />
                </div>
              );
            }
            const event = item.data as TimelineEvent;
            return (
              <TimelineEventCard
                key={`event-${event.timestamp}-${event.stage}`}
                event={event}
                isLast={index === totalCount - 1}
              />
            );
          })}
        </div>
      </div>

      {/* Summary stats */}
      {events.length > 0 && (
        <div className="mt-6 p-4 bg-surface rounded-lg border border-border-default">
          <p className="text-ui-xs text-text-muted">
            <span className="font-semibold">{events.length} events</span> {selectedStage ? `in ${labelOrTitle(STAGE_LABELS, selectedStage)}` : ''} captured in this timeline
          </p>
        </div>
      )}
    </div>
  );
}
