"use client";

import { useCallback, useEffect, useState } from "react";
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
  XCircle,
  RotateCcw,
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
};

// ── Component ────────────────────────────────────────────────────────────────

interface ExecutionTimelinePanelProps {
  tripId: string;
}

export default function ExecutionTimelinePanel({ tripId }: ExecutionTimelinePanelProps) {
  const [events, setEvents] = useState<ExecutionTimelineEvent[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const fetchTimeline = useCallback(async () => {
    try {
      const cat = activeCategory === "all" ? undefined : activeCategory;
      const res = await getExecutionTimeline(tripId, cat);
      setEvents(res.events);
      setSummary(res.summary);
    } catch {
      setError("Failed to load timeline");
    } finally {
      setLoading(false);
    }
  }, [tripId, activeCategory]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  if (loading) {
    return (
      <div className="bg-elevated border border-border-default rounded-xl p-4">
        <div className="flex items-center gap-2 text-sm text-muted">
          <Loader className="size-4 animate-spin" />
          Loading execution timeline…
        </div>
      </div>
    );
  }

  return (
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

      {/* Error */}
      {error && (
        <div className="text-xs text-red-400 bg-red-900/20 rounded p-2">{error}</div>
      )}

      {/* Events */}
      {events.length === 0 ? (
        <div className="text-xs text-zinc-500 py-2">
          No execution events yet. Generate tasks or add confirmations to see timeline activity.
        </div>
      ) : (
        <div className="space-y-0.5 max-h-64 overflow-y-auto">
          {events.map((event) => (
            <TimelineRow key={`evt-${event.subject_id}-${event.timestamp}`} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Timeline row ─────────────────────────────────────────────────────────────

function TimelineRow({ event }: { event: ExecutionTimelineEvent }) {
  const statusTo = event.status_to;
  const Icon = STATUS_ICON[statusTo] ?? Circle;
  const color = STATUS_COLOR[statusTo] ?? "text-zinc-400";
  const typeLabel = EVENT_TYPE_LABELS[event.event_type] ?? event.event_type;
  const actor = event.actor_type === "system" ? "System" : event.actor_id?.slice(0, 8) ?? "Unknown";

  const ts = event.timestamp
    ? <ClientTime value={event.timestamp} options={{ hour: "2-digit", minute: "2-digit" }} />
    : "";

  return (
    <div className="flex items-center gap-2 px-2 py-1 rounded text-xs">
      <Icon className={`size-3 shrink-0 ${color}`} />
      <span className="text-zinc-200 flex-1 truncate">
        {event.subject_type.replace("booking_", "").replace("_", " ")} {typeLabel.toLowerCase()}
      </span>
      <span className="text-[10px] text-zinc-500">{actor}</span>
      <span className="text-[10px] text-zinc-600">{ts}</span>
    </div>
  );
}
