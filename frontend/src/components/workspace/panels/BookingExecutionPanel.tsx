"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle,
  Circle,
  Clock,
  Loader,
  AlertTriangle,
  Play,
  Ban,
  Zap,
  RotateCcw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  listBookingTasks,
  generateBookingTasks,
  completeBookingTask,
  cancelBookingTask,
  updateBookingTask,
  type BookingTask,
  type BookingTaskSummary,
  type GenerateTasksResponse,
} from "@/lib/api-client";

// ── Status helpers ──────────────────────────────────────────────────────────

const STATUS_META: Record<string, { label: string; color: string; icon: typeof Circle }> = {
  not_started: { label: "Not started", color: "text-zinc-400", icon: Circle },
  blocked: { label: "Blocked", color: "text-red-400", icon: AlertTriangle },
  ready: { label: "Ready", color: "text-emerald-400", icon: Zap },
  in_progress: { label: "In progress", color: "text-blue-400", icon: Play },
  waiting_on_customer: { label: "Waiting on customer", color: "text-amber-400", icon: Clock },
  completed: { label: "Completed", color: "text-emerald-400", icon: CheckCircle },
  cancelled: { label: "Cancelled", color: "text-zinc-500", icon: Ban },
};

const PRIORITY_BADGE: Record<string, string> = {
  critical: "bg-red-900/50 text-red-300",
  high: "bg-amber-900/50 text-amber-300",
  medium: "bg-zinc-800 text-zinc-300",
  low: "bg-zinc-800 text-zinc-500",
};

// ── Component ───────────────────────────────────────────────────────────────

interface BookingExecutionPanelProps {
  tripId: string;
  stage?: string;
}

const GENERATE_ALLOWED_STAGES = new Set(["proposal", "booking"]);

// react-doctor-disable-next-line react-doctor/prefer-useReducer — 7 state vars are independent form/UI concerns
export default function BookingExecutionPanel({ tripId, stage }: BookingExecutionPanelProps) {
  const [tasks, setTasks] = useState<BookingTask[]>([]);
  const [summary, setSummary] = useState<BookingTaskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState<GenerateTasksResponse | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await listBookingTasks(tripId);
      setTasks(res.tasks);
      setSummary(res.summary);
    } catch {
      setError("Failed to load booking tasks");
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const canGenerate = stage ? GENERATE_ALLOWED_STAGES.has(stage) : false;

  const handleGenerate = useCallback(async () => {
    if (!canGenerate) return;
    setGenerating(true);
    setError(null);
    setGenResult(null);
    try {
      const res = await generateBookingTasks(tripId);
      setGenResult(res);
      await fetchTasks();
    } catch {
      setError("Failed to generate tasks");
    } finally {
      setGenerating(false);
    }
  }, [tripId, fetchTasks, canGenerate]);

  const handleComplete = useCallback(
    async (taskId: string) => {
      try {
        await completeBookingTask(tripId, taskId);
        await fetchTasks();
      } catch {
        setError("Failed to complete task");
      }
    },
    [tripId, fetchTasks],
  );

  const handleCancel = useCallback(
    async (taskId: string) => {
      try {
        await cancelBookingTask(tripId, taskId);
        await fetchTasks();
      } catch {
        setError("Failed to cancel task");
      }
    },
    [tripId, fetchTasks],
  );

  const handleStatusChange = useCallback(
    async (taskId: string, status: string) => {
      try {
        await updateBookingTask(tripId, taskId, { status });
        await fetchTasks();
      } catch {
        setError("Failed to update task status");
      }
    },
    [tripId, fetchTasks],
  );

  // ── Render ──────────────────────────────────────────────────────────────

  const activeTasks = tasks.filter((t) => t.status !== "completed" && t.status !== "cancelled");
  const completedTasks = tasks.filter((t) => t.status === "completed");
  const blockedCount = tasks.filter((t) => t.status === "blocked").length;
  const readyCount = tasks.filter((t) => t.status === "ready").length;

  return loading ? (
    <div className="bg-elevated border border-border-default rounded-xl p-4">
      <div className="flex items-center gap-2 text-sm text-muted">
        <Loader className="size-4 animate-spin" />
        Loading booking tasks…
      </div>
    </div>
  ) : (
    <div className="bg-elevated border border-border-default rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-medium text-[#e6edf3]">Booking Execution</h4>
          {summary && (
            <span className="text-xs text-zinc-500">
              {summary.completed}/{summary.total} done
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {blockedCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-red-900/50 text-red-400">
              {blockedCount} blocked
            </span>
          )}
          {readyCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-900/50 text-emerald-400">
              {readyCount} ready
            </span>
          )}
          <button
            onClick={handleGenerate}
            disabled={generating || !canGenerate}
            className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-[#1f6feb] text-white hover:bg-[#388bfd] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
              <Loader className="size-3 animate-spin" />
            ) : (
              <RotateCcw className="size-3" />
            )}
            {generating ? "Generating…" : "Generate / Reconcile"}
          </button>
        </div>
      </div>

      {/* Generation result */}
      {genResult && (
        <div className="text-xs text-zinc-400 bg-zinc-800/50 rounded p-2">
          Created {genResult.created.length} / Skipped {genResult.skipped.length}
          {genResult.reconciled.length > 0 &&
            ` / Reconciled ${genResult.reconciled.length}`}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="text-xs text-red-400 bg-red-900/20 rounded p-2">{error}</div>
      )}

      {/* Task list */}
      {activeTasks.length === 0 && completedTasks.length === 0 ? (
        <div className="text-xs text-zinc-500 py-2">
          No booking tasks yet. Click &quot;Generate / Reconcile&quot; to create tasks from trip state.
        </div>
      ) : (
        <div className="space-y-1">
          {activeTasks.map((task) => (
            <TaskRow
              key={task.id}
              task={task}
              onComplete={handleComplete}
              onCancel={handleCancel}
              onStatusChange={handleStatusChange}
            />
          ))}

          {/* Completed tasks (collapsible) */}
          {completedTasks.length > 0 && (
            <>
              <button
                onClick={() => setShowCompleted(!showCompleted)}
                className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 py-1"
              >
                {showCompleted ? (
                  <ChevronUp className="size-3" />
                ) : (
                  <ChevronDown className="size-3" />
                )}
                {completedTasks.length} completed
              </button>
              {showCompleted &&
                completedTasks.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    onComplete={handleComplete}
                    onCancel={handleCancel}
                    onStatusChange={handleStatusChange}
                  />
                ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Task row ────────────────────────────────────────────────────────────────

interface TaskRowProps {
  task: BookingTask;
  onComplete: (taskId: string) => void;
  onCancel: (taskId: string) => void;
  onStatusChange: (taskId: string, status: string) => void;
}

function TaskRow({ task, onComplete, onCancel, onStatusChange }: TaskRowProps) {
  const meta = STATUS_META[task.status] ?? STATUS_META.not_started;
  const Icon = meta.icon;
  const isTerminal = task.status === "completed" || task.status === "cancelled";

  return (
    <div
      className={`flex items-center gap-2 px-2 py-1.5 rounded text-xs ${
        isTerminal ? "opacity-60" : ""
      }`}
    >
      {/* Status icon */}
      <Icon className={`size-3.5 shrink-0 ${meta.color}`} />

      {/* Title */}
      <span className={`flex-1 truncate ${isTerminal ? "line-through text-zinc-500" : "text-zinc-200"}`}>
        {task.title}
      </span>

      {/* Priority badge */}
      <span className={`text-[10px] px-1.5 py-0.5 rounded ${PRIORITY_BADGE[task.priority] ?? PRIORITY_BADGE.medium}`}>
        {task.priority}
      </span>

      {/* Source badge */}
      {task.source !== "agent_created" && (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500">
          auto
        </span>
      )}

      {/* Blocker indicator */}
      {task.blocker_code && (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/40 text-red-400" title={task.blocker_code}>
          {task.blocker_code.replace(/_/g, " ")}
        </span>
      )}

      {/* Actions */}
      {!isTerminal && (
        <div className="flex items-center gap-1">
          {task.status === "ready" && (
            <button
              onClick={() => onStatusChange(task.id, "in_progress")}
              className="p-1 rounded hover:bg-zinc-700 text-blue-400"
              title="Start"
            >
              <Play className="size-3" />
            </button>
          )}
          {task.status === "in_progress" && (
            <button
              onClick={() => onComplete(task.id)}
              className="p-1 rounded hover:bg-zinc-700 text-emerald-400"
              title="Complete"
            >
              <CheckCircle className="size-3" />
            </button>
          )}
          <button
            onClick={() => onCancel(task.id)}
            className="p-1 rounded hover:bg-zinc-700 text-zinc-500"
            title="Cancel"
          >
            <Ban className="size-3" />
          </button>
        </div>
      )}
    </div>
  );
}
