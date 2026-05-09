"use client";

import { useEffect, useRef, useState } from "react";
import {
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
  AlertTriangle,
  FileText,
  ChevronRight,
  CircleSlash,
} from "lucide-react";
import type { RunStatusResponse } from "@/types/spine";

interface RunProgressPanelProps {
  runId: string | null;
  runState: RunStatusResponse | null;
  error?: Error | null;
  onRetry: () => void;
  onFixDetails?: () => void;
  onViewTrip?: () => void;
}

const steps = [
  { id: "packet", label: "Guest Intake", desc: "Extracting traveler details" },
  { id: "validation", label: "Trip Details", desc: "Checking completeness" },
  { id: "decision", label: "Ready to Quote?", desc: "AI assessment" },
  { id: "strategy", label: "Build Options", desc: "Planning options" },
  { id: "safety", label: "Final Review", desc: "Safety checks" },
];

function elapsedSec(startedAt: string | null): number {
  if (!startedAt) return 0;
  return Math.round((Date.now() - new Date(startedAt).getTime()) / 1000);
}

type StepStatus = "done" | "failed" | "blocked" | "current" | "pending";

function getStepStatuses(
  run: RunStatusResponse
): StepStatus[] {
  const completed = run.steps_completed ?? [];
  const failedStep = run.state === "failed" ? run.stage_at_failure : null;
  const blockedStep = run.state === "blocked" ? "validation" : null;
  const isTerminal = ["completed", "failed", "blocked"].includes(run.state);

  let hitFailure = false;
  let hitBlocked = false;

  return steps.map((step) => {
    if (hitFailure || hitBlocked) return "blocked";

    if (failedStep && step.id === failedStep) {
      hitFailure = true;
      return "failed";
    }

    if (blockedStep && step.id === blockedStep) {
      hitBlocked = true;
      return "failed";
    }

    if (completed.includes(step.id)) return "done";

    if (!isTerminal) {
      const enteredStage = [...(run.events ?? [])]
        .reverse()
        .find((e) => e.event_type === "pipeline_stage_entered" && e.stage_name)
        ?.stage_name;

      if (enteredStage && enteredStage === step.id) return "current";

      if (!enteredStage) {
        const firstPending = steps.findIndex((s) => !completed.includes(s.id));
        const idx = steps.findIndex((s) => s.id === step.id);
        if (idx === firstPending) return "current";
      }
      return "pending";
    }

    return "pending";
  });
}

export function RunProgressPanel({ runId, runState, error, onRetry, onFixDetails, onViewTrip }: RunProgressPanelProps) {
  const durationRef = useRef<HTMLSpanElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (!runState?.started_at) return;
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      if (durationRef.current && runState?.started_at) {
        durationRef.current.textContent = `${elapsedSec(runState.started_at)}s`;
      }
    }, 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [runState?.started_at]);

  if (!runId) return null;

  const isRunning = runState?.state === "running" || runState?.state === "queued";
  const isBlocked = runState?.state === "blocked";
  const isFailed = runState?.state === "failed";
  const isCompleted = runState?.state === "completed";
  const isIntakeOnlyCompletion = isCompleted && !(runState?.steps_completed ?? []).includes("decision");

  // During active processing: show the compact step tracker
  if (isRunning) {
    const stepStatuses = runState ? getStepStatuses(runState) : steps.map((_, i) => i === 0 ? "current" as StepStatus : "pending" as StepStatus);

    return (
      <div className="rounded-xl border border-[#30363d] bg-[#0d1117] overflow-hidden min-w-[260px] shadow-lg">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#30363d]">
          <div className="flex items-center gap-2 text-[#58a6ff] text-ui-sm font-medium">
            <Loader2 className="size-3.5 animate-spin" />
            Processing Trip
          </div>
          <div className="flex items-center gap-1.5 text-ui-xs text-[var(--text-muted)]">
            <Clock className="size-3" />
            <span ref={durationRef}>{runState?.started_at ? elapsedSec(runState.started_at) : '--'}s</span>
          </div>
        </div>
        <div className="p-3 space-y-1">
          {steps.map((step, idx) => {
            const status = stepStatuses[idx];
            return (
              <div
                key={step.id}
                className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-md transition-colors ${
                  status === "current"
                    ? "bg-[#58a6ff]/10 border border-[#58a6ff]/30"
                    : "bg-transparent"
                }`}
              >
                {status === "done" ? (
                  <CheckCircle className="size-3.5 text-[#3fb950] shrink-0" />
                ) : status === "current" ? (
                  <Loader2 className="size-3.5 animate-spin text-[var(--accent-amber)] shrink-0" />
                ) : (
                  <div className="size-3.5 rounded-full border border-[var(--text-tertiary)] shrink-0" />
                )}
                <span
                  className={`text-ui-xs font-medium ${
                    status === "done"
                      ? "text-[#3fb950]"
                      : status === "current"
                        ? "text-[var(--text-primary)]"
                        : "text-[var(--text-muted)]"
                  }`}
                >
                  {step.label}
                </span>
                {status === "current" && (
                  <span className="text-[10px] text-[var(--text-muted)] ml-auto">{step.desc}</span>
                )}
                {status === "done" && (
                  <StepTiming events={runState?.events} stepId={step.id} />
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Blocked: compact result - details are shown in the inline banner
  if (isBlocked) {
    return (
      <div className="rounded-xl border border-[var(--accent-amber)]/30 bg-[#0d1117] overflow-hidden min-w-[240px] shadow-lg">
        <div className="px-4 py-3 space-y-2.5">
          <div className="flex items-center gap-2 text-[var(--accent-amber)] text-ui-sm font-medium">
            <AlertTriangle className="size-4" />
            Trip Details Need Attention
          </div>
          <p className="text-ui-xs text-[var(--text-muted)] leading-relaxed">
            {runState?.block_reason || "Required details are missing before quote options can be built."}
          </p>
          <button
            type="button"
            onClick={onFixDetails || onRetry}
            className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[var(--accent-amber)]/10 border border-[var(--accent-amber)]/30 text-[var(--accent-amber)] text-ui-xs font-medium rounded-md hover:bg-[var(--accent-amber)]/20 transition-colors"
          >
            Fix Missing Details
          </button>
          <button
            type="button"
            onClick={() => setShowDetails(v => !v)}
            className="block w-full text-center text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-muted)] transition-colors"
          >
            {showDetails ? 'Hide' : 'Show'} run details
          </button>
          {showDetails && (
            <div className="text-[10px] font-mono text-[var(--text-tertiary)] pt-1 border-t border-[#30363d] space-y-1">
              <div>Run: {runId.slice(0, 8)}</div>
              {runState?.steps_completed && <div>Completed: {runState.steps_completed.join(', ')}</div>}
              {runState?.total_ms != null && <div>Duration: {runState.total_ms}ms</div>}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Failed: compact retry result
  if (isFailed) {
    const stepStatuses = runState ? getStepStatuses(runState) : steps.map(() => "pending" as StepStatus);
    const failedLabel = runState?.stage_at_failure
      ? steps.find(s => s.id === runState.stage_at_failure)?.label || runState.stage_at_failure
      : "unknown";

    return (
      <div className="rounded-xl border border-[#f85149]/30 bg-[#0d1117] overflow-hidden min-w-[240px] shadow-lg">
        <div className="px-4 py-3 space-y-2.5">
          <div className="flex items-center gap-2 text-[#f85149] text-ui-sm font-medium">
            <XCircle className="size-4" />
            Processing Failed
          </div>
          <p className="text-ui-xs text-[var(--text-muted)] leading-relaxed">
            Failed at {failedLabel} phase{runState?.error_message ? `: ${runState.error_message}` : ''}.
          </p>
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[#da3633]/10 border border-[#da3633]/30 text-[#f85149] text-ui-xs font-medium rounded-md hover:bg-[#da3633]/20 transition-colors"
          >
            <AlertTriangle className="size-3" />
            Retry Processing
          </button>
          <button
            type="button"
            onClick={() => setShowDetails(v => !v)}
            className="block w-full text-center text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-muted)] transition-colors"
          >
            {showDetails ? 'Hide' : 'Show'} run details
          </button>
          {showDetails && (
            <div className="text-[10px] font-mono text-[var(--text-tertiary)] pt-1 border-t border-[#30363d] space-y-1">
              <div>Run: {runId.slice(0, 8)}</div>
              {runState?.error_type && <div>Error: {runState.error_type}</div>}
              {runState?.total_ms != null && <div>Duration: {runState.total_ms}ms</div>}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Completed successfully: compact result
  if (isCompleted) {
    return (
      <div className="rounded-xl border border-[#3fb950]/30 bg-[#0d1117] overflow-hidden min-w-[240px] shadow-lg">
        <div className="px-4 py-3 space-y-2.5">
          <div className="flex items-center gap-2 text-[#3fb950] text-ui-sm font-medium">
            <CheckCircle className="size-4" />
            Processing Complete
          </div>
          {isIntakeOnlyCompletion && (
            <p className="text-ui-xs text-[var(--accent-amber)]">
              Intake saved, but quote-building stages did not run. Add missing details and reprocess.
            </p>
          )}
          {(runState?.trip_id || onViewTrip) && (
            <button
              type="button"
              onClick={onViewTrip || (() => { window.location.href = `/trips/${runState!.trip_id}/intake`; })}
              className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[#238636] text-white text-ui-xs font-medium rounded-md hover:bg-[#2ea043] transition-colors"
            >
              View Trip
              <ChevronRight className="size-3" />
            </button>
          )}
          {!(runState?.trip_id || onViewTrip) && !isIntakeOnlyCompletion && (
            <div className="flex items-center gap-1.5 text-[#3fb950] text-ui-xs">
              <CheckCircle className="size-3.5" />
              Completed
            </div>
          )}
          <button
            type="button"
            onClick={() => setShowDetails(v => !v)}
            className="block w-full text-center text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-muted)] transition-colors"
          >
            {showDetails ? 'Hide' : 'Show'} run details
          </button>
          {showDetails && (
            <div className="text-[10px] font-mono text-[var(--text-tertiary)] pt-1 border-t border-[#30363d] space-y-1">
              <div>Run: {runId.slice(0, 8)}</div>
              {runState?.total_ms != null && <div>Duration: {runState.total_ms}ms</div>}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Fallback for error/timed-out while running
  if (error) {
    return (
      <div className="rounded-xl border border-[#f85149]/30 bg-[#0d1117] overflow-hidden min-w-[240px] shadow-lg">
        <div className="px-4 py-3 space-y-2.5">
          <div className="flex items-center gap-2 text-[#f85149] text-ui-sm font-medium">
            <XCircle className="size-4" />
            Processing Error
          </div>
          <p className="text-ui-xs text-[var(--text-muted)]">{error.message || "Timed out"}</p>
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[#da3633]/10 border border-[#da3633]/30 text-[#f85149] text-ui-xs font-medium rounded-md hover:bg-[#da3633]/20 transition-colors"
          >
            <AlertTriangle className="size-3" />
            Retry Processing
          </button>
        </div>
      </div>
    );
  }

  return null;
}

function StepTiming({
  events,
  stepId,
}: {
  events: RunStatusResponse["events"];
  stepId: string;
}) {
  const evt = events?.find(
    (e) => e.event_type === "pipeline_stage_completed" && e.stage_name === stepId
  );
  if (!evt || typeof evt.execution_ms !== "number") return null;
  return (
    <span className="text-[10px] text-[var(--text-tertiary)] tabular-nums shrink-0">
      {Math.round(evt.execution_ms)}ms
    </span>
  );
}