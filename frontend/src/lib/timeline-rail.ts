import { STAGE_LABELS, STATUS_LABELS, labelOrTitle } from "@/lib/label-maps";
import type { TimelineEvent } from "@/types/spine";

const IMPORTANT_TIMELINE_KEYWORDS = [
  "sla",
  "reply",
  "customer reply",
  "quote",
  "status change",
  "override",
  "escalat",
  "booking",
  "payment",
  "document",
];

function normalizeTimelineText(event: TimelineEvent): string {
  return [
    event.stage,
    event.status,
    event.reason,
    event.decision,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function isTimelineStageUnset(stage?: string | null): boolean {
  const normalized = stage?.trim().toLowerCase();
  return !normalized || normalized === "unknown" || normalized === "unset" || normalized === "none" || normalized === "n/a";
}

export function getTimelineStageLabel(stage?: string | null): string {
  if (isTimelineStageUnset(stage)) return "Stage not set";
  return labelOrTitle(STAGE_LABELS, stage ?? "");
}

function getTimelineTriggerLabel(eventCount?: number | null): string {
  if (!eventCount) return "Timeline";
  return `Timeline · ${eventCount} ${eventCount === 1 ? "event" : "events"}`;
}

export function hasImportantTimelineEvent(events?: TimelineEvent[]): boolean {
  return (events ?? []).some((event) => {
    const haystack = normalizeTimelineText(event);
    return IMPORTANT_TIMELINE_KEYWORDS.some((keyword) => haystack.includes(keyword));
  });
}

export function getTimelineEventTitle(event: TimelineEvent): string {
  if (event.reason?.trim()) return event.reason.trim();
  if (event.decision?.trim()) return event.decision.trim();
  return `${labelOrTitle(STATUS_LABELS, event.status)} · ${getTimelineStageLabel(event.stage)}`;
}
