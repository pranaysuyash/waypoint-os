"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ClientTime } from '@/hooks/useClientDate';
import {
  CheckCircle,
  Circle,
  Clock,
  Loader,
  Play,
  Ban,
  Zap,
  AlertTriangle,
  ShieldCheck,
  FileText,
  ScanLine,
  Layers,
  XCircle,
  RotateCcw,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import {
  getExecutionTimeline,
  type ExecutionTimelineEvent,
} from "@/lib/api-client";

// ── Constants ────────────────────────────────────────────────────────────────

const CATEGORY_LABELS: Record<string, string> = {
  all: "All",
  task: "Tasks",
  confirmation: "Confirmations",
  document: "Documents",
  extraction: "Extractions",
};

const ACTOR_FILTERS = [
  { key: "all", label: "All actors" },
  { key: "agent", label: "Agent actions" },
  { key: "system", label: "System events" },
] as const;

const EVENT_TYPE_LABELS: Record<string, string> = {
  task_created: "Created",
  task_blocked: "Blocked",
  task_ready: "Ready",
  task_started: "Started",
  task_waiting: "Waiting",
  task_completed: "Completed",
  task_cancelled: "Cancelled",
  confirmation_created: "Created",
  confirmation_updated: "Updated",
  confirmation_recorded: "Recorded",
  confirmation_verified: "Verified",
  confirmation_voided: "Voided",
  document_uploaded: "Uploaded",
  document_accepted: "Accepted",
  document_rejected: "Rejected",
  document_deleted: "Deleted",
  extraction_run_started: "Run started",
  extraction_run_completed: "Run completed",
  extraction_run_failed: "Run failed",
  extraction_applied: "Applied",
  extraction_rejected: "Rejected",
  extraction_attempt_completed: "Attempt completed",
  extraction_attempt_failed: "Attempt failed",
};

const STATUS_ICON: Record<string, typeof Circle> = {
  not_started: Circle,
  blocked: AlertTriangle,
  ready: Zap,
  in_progress: Play,
  waiting_on_customer: Clock,
  completed: CheckCircle,
  cancelled: Ban,
  draft: Circle,
  recorded: FileText,
  verified: ShieldCheck,
  voided: XCircle,
  pending_review: Clock,
  accepted: CheckCircle,
  rejected: XCircle,
  deleted: Ban,
  running: Loader,
  failed: AlertTriangle,
  applied: CheckCircle,
  success: CheckCircle,
};

const STATUS_COLOR: Record<string, string> = {
  not_started: "text-zinc-400",
  blocked: "text-red-400",
  ready: "text-emerald-400",
  in_progress: "text-blue-400",
  waiting_on_customer: "text-amber-400",
  completed: "text-emerald-400",
  cancelled: "text-zinc-500",
  draft: "text-zinc-400",
  recorded: "text-blue-400",
  verified: "text-emerald-400",
  voided: "text-zinc-500",
  pending_review: "text-amber-400",
  accepted: "text-emerald-400",
  rejected: "text-red-400",
  deleted: "text-zinc-500",
  running: "text-blue-400",
  failed: "text-red-400",
  applied: "text-emerald-400",
  success: "text-emerald-400",
};

// ── Metadata display allowlist (defense-in-depth) ────────────────────────────

const METADATA_LABELS: Record<string, string> = {
  task_type: "Task type",
  confirmation_type: "Confirmation type",
  document_type: "Document type",
  provider: "Provider",
  model: "Model",
  blocker_code: "Blocker",
  evidence_ref_count: "Evidence refs",
  size_bytes: "File size",
  mime_type: "MIME type",
  uploaded_by_type: "Uploaded by",
  scan_status: "Scan status",
  review_notes_present: "Has notes",
  storage_delete_status: "Storage status",
  run_count: "Run count",
  attempt_count: "Attempt count",
  overall_confidence: "Confidence",
  field_count: "Fields found",
  latency_ms: "Latency",
  cost_estimate_usd: "Cost",
  error_code: "Error code",
  attempt_number: "Attempt #",
  fallback_rank: "Fallback rank",
  fields_applied_count: "Fields applied",
  allow_overwrite: "Overwrite allowed",
};

const SAFE_METADATA_KEYS = new Set(Object.keys(METADATA_LABELS));

function formatMetadataValue(key: string, value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (key === "size_bytes") return `${(Number(value) / 1024).toFixed(1)} KB`;
  if (key === "latency_ms") return `${value}ms`;
  if (key === "cost_estimate_usd" && value != null) return `$${Number(value).toFixed(4)}`;
  if (key === "overall_confidence" && value != null) return `${Math.round(Number(value) * 100)}%`;
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

// ── Date grouping helper ─────────────────────────────────────────────────────

function formatDateHeader(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

// ── Component ────────────────────────────────────────────────────────────────

interface ExecutionTimelinePanelProps {
  tripId: string;
}

// react-doctor-disable-next-line react-doctor/prefer-useReducer — 5 state vars manage distinct filtering/sorting concerns
export default function ExecutionTimelinePanel({ tripId }: ExecutionTimelinePanelProps) {
  const [events, setEvents] = useState<ExecutionTimelineEvent[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");
  const [activeActor, setActiveActor] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const fetchTimeline = useCallback(async () => {
    try {
      const cat = activeCategory === "all" ? undefined : activeCategory;
      const actor = activeActor === "all" ? undefined : activeActor;
      const res = await getExecutionTimeline(tripId, cat, actor);
      setEvents(res.events);
      setSummary(res.summary);
    } catch {
      setError("Failed to load timeline");
    } finally {
      setLoading(false);
    }
  }, [tripId, activeCategory, activeActor]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const groupedEvents = useMemo(() => {
    const groups: Record<string, ExecutionTimelineEvent[]> = {};
    for (const event of events) {
      const date = event.timestamp.split("T")[0];
      if (!groups[date]) groups[date] = [];
      groups[date].push(event);
    }
    return groups;
  }, [events]);

  return loading ? (
      <div className="bg-elevated border border-border-default rounded-xl p-4">
        <div className="flex items-center gap-2 text-sm text-muted">
          <Loader className="size-4 animate-spin" />
          Loading execution timeline…
        </div>
      </div>
  ) : (
    <div className="bg-elevated border border-border-default rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-[#e6edf3]">Execution Timeline</h4>
        <button
          onClick={fetchTimeline}
          className="p-1 rounded hover:bg-zinc-700 text-zinc-500"
          title="Refresh"
        >
          <RotateCcw className="size-3.5" />
        </button>
      </div>

      {/* Category filter chips */}
      <div className="flex gap-1 flex-wrap">
        {Object.entries(CATEGORY_LABELS).map((entry) => {
          const [key, label] = entry;
          const count = key === "all" ? (summary.total ?? 0) : (summary[key] ?? 0);
          return (
            <button
              key={key}
              onClick={() => setActiveCategory(key)}
              className={`text-[10px] px-2 py-0.5 rounded ${
                activeCategory === key
                  ? "bg-zinc-700 text-zinc-200"
                  : "bg-zinc-800/50 text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {label} ({count})
            </button>
          );
        })}
      </div>

      {/* Actor filter chips */}
      <div className="flex gap-1 flex-wrap">
        {ACTOR_FILTERS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveActor(key)}
            className={`text-[10px] px-2 py-0.5 rounded ${
              activeActor === key
                ? "bg-zinc-700 text-zinc-200"
                : "bg-zinc-800/50 text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="text-xs text-red-400 bg-red-900/20 rounded p-2">{error}</div>
      )}

      {/* Events grouped by date */}
      {events.length === 0 ? (
        <div className="text-xs text-zinc-500 py-2">
          No execution events yet. Generate tasks or add confirmations to see timeline activity.
        </div>
      ) : (
        <div className="space-y-1 max-h-72 overflow-y-auto">
          {Object.entries(groupedEvents).map(([date, dateEvents]) => (
            <div key={date}>
              <div className="text-[10px] text-zinc-500 px-2 py-1">{formatDateHeader(date)}</div>
              {dateEvents.map((event) => (
                <TimelineRow key={`evt-${event.subject_id}-${event.timestamp}`} event={event} />
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Timeline row ─────────────────────────────────────────────────────────────

function TimelineRow({ event }: { event: ExecutionTimelineEvent }) {
  const [expanded, setExpanded] = useState(false);
  const statusTo = event.status_to;
  const Icon = STATUS_ICON[statusTo] ?? Circle;
  const color = STATUS_COLOR[statusTo] ?? "text-zinc-400";
  const typeLabel = EVENT_TYPE_LABELS[event.event_type] ?? event.event_type;
  const actor = event.actor_type === "system" ? "System" : event.actor_id?.slice(0, 8) ?? "Unknown";

  const subjectLabel = event.subject_type
    .replace("booking_", "")
    .replace("document_extraction_attempt", "attempt")
    .replace("document_extraction", "extraction")
    .replace("_", " ");

  const ts = event.timestamp
    ? <ClientTime value={event.timestamp} options={{ hour: "2-digit", minute: "2-digit" }} />
    : "";

  const hasMetadata = event.event_metadata && Object.keys(event.event_metadata).length > 0;

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-2 py-1 rounded text-xs ${hasMetadata ? "cursor-pointer hover:bg-zinc-800/50" : ""}`}
        onClick={() => hasMetadata && setExpanded(!expanded)}
      >
        {hasMetadata && (
          expanded
            ? <ChevronDown className="size-3 shrink-0 text-zinc-600" />
            : <ChevronRight className="size-3 shrink-0 text-zinc-600" />
        )}
        {!hasMetadata && <span className="w-3" />}
        <Icon className={`size-3 shrink-0 ${color}`} />
        <span className="text-zinc-200 flex-1 truncate">
          {subjectLabel} {typeLabel.toLowerCase()}
        </span>
        <span className="text-[10px] text-zinc-500">{actor}</span>
        <span className="text-[10px] text-zinc-600">{ts}</span>
      </div>
      {expanded && event.event_metadata && (
        <div className="ml-6 mt-1 space-y-0.5">
          {Object.entries(event.event_metadata)
            .filter(([key]) => SAFE_METADATA_KEYS.has(key))
            .map(([key, value]) => (
              <div key={key} className="flex gap-2 text-[10px]">
                <span className="text-zinc-500">{METADATA_LABELS[key]}</span>
                <span className="text-zinc-300">{formatMetadataValue(key, value)}</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
