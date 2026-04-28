"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { Trip } from "@/lib/api-client";
import type { TimelineEvent, TimelineResponse, SuitabilityFlag } from "@/types/spine";
import { STAGE_LABELS, labelOrTitle } from "@/lib/label-maps";
import { SuitabilitySignal } from "./SuitabilitySignal";

interface TimelinePanelProps {
  trip?: Trip | null;
  tripId?: string;
  onStageFilter?: (stage: string | null) => void;
}

const STAGE_COLORS: Record<string, { bg: string; badge: string; dot: string }> = {
  intake: { bg: "bg-blue-50 dark:bg-blue-950", badge: "bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100", dot: "bg-blue-500" },
  packet: { bg: "bg-orange-50 dark:bg-orange-950", badge: "bg-orange-100 text-orange-900 dark:bg-orange-900 dark:text-orange-100", dot: "bg-orange-500" },
  decision: { bg: "bg-green-50 dark:bg-green-950", badge: "bg-green-100 text-green-900 dark:bg-green-900 dark:text-green-100", dot: "bg-green-500" },
  strategy: { bg: "bg-purple-50 dark:bg-purple-950", badge: "bg-purple-100 text-purple-900 dark:bg-purple-900 dark:text-purple-100", dot: "bg-purple-500" },
  safety: { bg: "bg-red-50 dark:bg-red-950", badge: "bg-red-100 text-red-900 dark:bg-red-900 dark:text-red-100", dot: "bg-red-500" },
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
  index,
}: {
  event: TimelineEvent;
  index: number;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const colors = STAGE_COLORS[event.stage] || STAGE_COLORS.intake;

  return (
    <div className="relative">
      {/* Timeline line (not on last item) */}
      {index < 0 && (
        <div className="absolute left-5 top-12 w-0.5 h-8 bg-gray-300 dark:bg-gray-600" />
      )}

      <div className={`flex gap-4 ${colors.bg} p-4 rounded-lg border border-gray-200 dark:border-gray-700`}>
        {/* Timeline dot */}
        <div className="flex-shrink-0">
          <div className={`w-3 h-3 rounded-full ${colors.dot} mt-1`} />
        </div>

        {/* Event content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-xs font-semibold px-2 py-1 rounded ${colors.badge}`}>
                {labelOrTitle(STAGE_LABELS, event.stage)}
              </span>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {event.status}
              </span>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
              {formatTimestamp(event.timestamp)}
            </span>
          </div>

          {/* Optional details */}
          {(event.decision || event.reason) && (
            <div className="mt-2 flex items-start gap-2">
              <div className="flex-1">
                {event.decision && (
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    <span className="font-semibold">Decision:</span> {event.decision}
                  </p>
                )}
                {event.reason && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    <span className="font-semibold">Reason:</span> {event.reason}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Expandable JSON */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-2 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
            <span>Show Details</span>
          </button>

          {isExpanded && (
            <div className="mt-2 p-2 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
              <pre className="text-xs text-gray-600 dark:text-gray-400 font-mono">
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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  const handleStageFilter = (stage: string | null) => {
    setSelectedStage(stage);
    onStageFilter?.(stage);
  };

  useEffect(() => {
    if (!tripId) return;

    const fetchTimelineAndSuitability = async () => {
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
          // If suitability endpoint doesn't exist yet, just skip it gracefully
        } catch (_err) {
          // Silently fail if suitability endpoint not available
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load timeline");
      } finally {
        setIsLoading(false);
      }
    };

    fetchTimelineAndSuitability();
  }, [tripId, selectedStage]);

  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400">Loading timeline...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950 p-4">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      </div>
    );
  }

  const events = timeline?.events ?? [];

  if (!timeline || (events.length === 0 && suitabilityFlags.length === 0)) {
    return (
      <div className="p-6 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400">No timeline events found</p>
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="timeline-panel">
      <div className="space-y-4">
        {/* Suitability Flags Section */}
        {suitabilityFlags.length > 0 && (
          <div className="mb-6">
            <h3 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">
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
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Decision Timeline
          </h2>
          
          {/* Stage Filter */}
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              onClick={() => handleStageFilter(null)}
              className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                selectedStage === null
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              All
            </button>
            {AVAILABLE_STAGES.map((stage) => (
              <button
                key={stage}
                onClick={() => handleStageFilter(stage)}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  selectedStage === stage
                    ? `${STAGE_COLORS[stage]?.badge} opacity-100`
                    : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
                }`}
              >
                {labelOrTitle(STAGE_LABELS, stage)}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Events */}
        <div className="space-y-3">
          {events.map((event, index) => (
            <TimelineEventCard key={`${event.timestamp}-${index}`} event={event} index={index} />
          ))}
        </div>
      </div>

      {/* Summary stats */}
      {events.length > 0 && (
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-600 dark:text-gray-400">
            <span className="font-semibold">{events.length} events</span> {selectedStage ? `in ${labelOrTitle(STAGE_LABELS, selectedStage)}` : ''} captured in this timeline
          </p>
        </div>
      )}
    </div>
  );
}
