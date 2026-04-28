"use client";

import { useEffect, useRef } from "react";
import {
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
  AlertTriangle,
  FileText,
  ChevronRight,
} from "lucide-react";
import type { RunStatusResponse, RunEvent } from "@/types/spine";
import { STAGE_LABELS, labelOrTitle } from "@/lib/label-maps";

interface RunProgressPanelProps {
  runId: string | null;
  runState: RunStatusResponse | null;
  error?: Error | null;
  onRetry: () => void;
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

function getStepStatus(
  stepId: string,
  run: RunStatusResponse
): "done" | "failed" | "current" | "pending" {
  const done = run.steps_completed?.includes(stepId);
  if (done) return "done";
  const failed = run.state === "failed" && run.stage_at_failure === stepId;
  if (failed) return "failed";
  if (run.state !== "running") return "pending";

  const enteredStage = [...(run.events ?? [])]
    .reverse()
    .find((e) => e.event_type === "pipeline_stage_entered" && e.stage_name)?.stage_name;

  if (enteredStage && enteredStage === stepId) return "current";

  // Fallback for older runs with no entered events logged.
  if (!enteredStage) {
    const firstPending = steps.findIndex((s) => !run.steps_completed?.includes(s.id));
    const idx = steps.findIndex((s) => s.id === stepId);
    if (idx === firstPending) return "current";
  }
  return "pending";
}

export function RunProgressPanel({ runId, runState, error, onRetry, onViewTrip }: RunProgressPanelProps) {
  const durationRef = useRef<HTMLSpanElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

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
  const isIntakeOnlyCompletion = runState
    ? runState.state === "completed" &&
      !(runState.steps_completed ?? []).includes("decision")
    : false;

  return (
    <div className="rounded-xl border border-[#30363d] bg-[#0d1117] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#30363d]">
        <div className="flex items-center gap-2 text-[#58a6ff] text-sm font-mono">
          <FileText className="w-3.5 h-3.5" />
          <span className="truncate max-w-[120px]">{runId.slice(0, 8)}</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[#8b949e]">
          <Clock className="w-3 h-3" />
          <span ref={durationRef}>{runState?.started_at ? elapsedSec(runState.started_at) : '--'}s</span>
        </div>
      </div>

       {/* Steps */}
       <div className="p-3 space-y-1">
         {steps.map((step, idx) => {
           const status = !runState
             ? (idx === 0 ? "current" : "pending")
             : getStepStatus(step.id, runState);
          return (
            <div
              key={step.id}
              className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md transition-colors ${
                status === "current"
                  ? "bg-[#58a6ff]/10 border border-[#58a6ff]/30"
                  : status === "done"
                  ? "bg-transparent"
                  : "bg-transparent opacity-70"
              }`}
            >
              {status === "done" ? (
                <CheckCircle className="w-4 h-4 text-[#3fb950] shrink-0" />
              ) : status === "failed" ? (
                <XCircle className="w-4 h-4 text-[#f85149] shrink-0" />
              ) : status === "current" ? (
                <Loader2 className="w-4 h-4 animate-spin text-[#d29922] shrink-0" />
              ) : (
                <div className="w-4 h-4 rounded-full border border-[#484f58] shrink-0" />
              )}

              <div className="flex-1 min-w-0">
                <div
                  className={`text-xs font-medium ${
                    status === "done"
                      ? "text-[#3fb950]"
                      : status === "failed"
                      ? "text-[#f85149]"
                      : status === "current"
                      ? "text-[#e6edf3]"
                      : "text-[#8b949e]"
                  }`}
                >
                  {step.label}
                </div>
                {status === "current" && (
                  <div className="text-[10px] text-[#8b949e] mt-0.5">{step.desc}</div>
                )}
              </div>

              {/* Show event timing per step from events */}
              {status === "done" && runState && (
                <StepTiming events={runState.events} stepId={step.id} />
              )}
            </div>
          );
        })}
      </div>

      {/* Footer state */}
      <div className="px-4 py-2.5 border-t border-[#30363d] bg-[#161b22]">
        {!runState && (
          <p className="text-[#8b949e] text-xs">Queued...</p>
        )}

        {runState?.state === "completed" && (runState.trip_id || onViewTrip) && (
          <button
            type='button'
            onClick={onViewTrip || (() => { window.location.href = `/workspace/${runState!.trip_id}/intake`; })}
            className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[#238636] text-white text-xs font-medium rounded-md hover:bg-[#2ea043] transition-colors"
          >
            View Trip
            <ChevronRight className="w-3 h-3" />
          </button>
        )}

        {isIntakeOnlyCompletion && (
          <p className="mt-2 text-[11px] text-[#d29922]">
            Intake saved, but quote-building stages did not run. Add missing details and reprocess.
          </p>
        )}

        {runState?.state === "completed" && !runState?.trip_id && !onViewTrip && (
          <div className="flex items-center gap-1.5 text-[#3fb950] text-xs">
            <CheckCircle className="w-3.5 h-3.5" />
            Completed
          </div>
        )}

        {runState?.state === "failed" && (
          <div className="space-y-2">
            <p className="text-[#f85149] text-xs">
              Failed at {runState.stage_at_failure ? labelOrTitle(STAGE_LABELS, runState.stage_at_failure) : "unknown"} phase
            </p>
            {runState.error_message && (
              <p className="text-[10px] text-[#8b949e] line-clamp-2">{runState.error_message}</p>
            )}
            <button
              type='button'
              onClick={onRetry}
              className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[#da3633]/10 border border-[#da3633]/30 text-[#f85149] text-xs rounded-md hover:bg-[#da3633]/20 transition-colors"
            >
              <AlertTriangle className="w-3 h-3" />
              Retry
            </button>
          </div>
        )}

        {runState?.state === "blocked" && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-[#d29922] text-xs font-medium">
              <AlertTriangle className="w-3.5 h-3.5" />
              Needs More Information
            </div>
            <p className="text-[#a8b3c1] text-xs leading-relaxed">
              {runState.block_reason || "Some details are needed before we can build your itinerary."}
            </p>
            <button
              type='button'
              onClick={onRetry}
              className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[#d29922]/10 border border-[#d29922]/30 text-[#d29922] text-xs rounded-md hover:bg-[#d29922]/20 transition-colors"
            >
              Try Again with More Details
            </button>
          </div>
        )}

        {error && runState?.state === "running" && (
          <div className="space-y-2">
            <p className="text-[#f85149] text-xs">{error.message || "Timed out"}</p>
            <button
              type='button'
              onClick={onRetry}
              className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 bg-[#da3633]/10 border border-[#da3633]/30 text-[#f85149] text-xs rounded-md hover:bg-[#da3633]/20 transition-colors"
            >
              <AlertTriangle className="w-3 h-3" />
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function StepTiming({
  events,
  stepId,
}: {
  events: RunEvent[] | undefined;
  stepId: string;
}) {
  const evt = events?.find(
    (e) => e.event_type === "pipeline_stage_completed" && e.stage_name === stepId
  );
  if (!evt || typeof evt.execution_ms !== "number") return null;
  return (
    <span className="text-[10px] text-[#484f58] tabular-nums shrink-0">
      {Math.round(evt.execution_ms)}ms
    </span>
  );
}
