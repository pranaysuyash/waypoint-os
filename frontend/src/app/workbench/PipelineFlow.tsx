"use client";

import { cn } from "@/lib/utils";
import { CheckCircle2 } from "lucide-react";

export const PIPELINE_STAGES = [
  { id: "intake", label: "1", fullLabel: "New Inquiry", description: "Capture customer request", shortLabel: "Inquiry" },
  { id: "packet", label: "2", fullLabel: "Trip Details", description: "Extract trip information", shortLabel: "Details" },
  { id: "decision", label: "3", fullLabel: "Ready to Quote?", description: "Check if ready to price", shortLabel: "Quote?" },
  { id: "strategy", label: "4", fullLabel: "Build Options", description: "Create travel options", shortLabel: "Options" },
  { id: "safety", label: "5", fullLabel: "Final Review", description: "Last check before send", shortLabel: "Review" },
] as const;

export type PipelineStageId = typeof PIPELINE_STAGES[number]["id"];

export function toPipelineStageId(value: string): PipelineStageId | null {
  const stage = PIPELINE_STAGES.find((s) => s.id === value);
  return stage?.id ?? null;
}

interface PipelineFlowProps {
  currentStage: PipelineStageId;
}

export function PipelineFlow({ currentStage }: PipelineFlowProps) {
  const currentIndex = PIPELINE_STAGES.findIndex((s) => s.id === currentStage);

  if (currentIndex === -1) {
    if (process.env.NODE_ENV !== "production") {
      console.error(`PipelineFlow: Unknown pipeline stage "${currentStage}". This is a bug in the caller.`);
    }
    return null;
  }

  return (
    <div className="px-4 lg:px-6 py-3 lg:py-4 border-b border-[#30363d] bg-[#0a0d11] pipeline-container">
      <nav aria-label="Pipeline progress">
        <ol className="flex items-center max-w-5xl mx-auto list-none p-0 m-0">
          {PIPELINE_STAGES.map((stage, index) => {
            const isActive = index === currentIndex;
            const isCompleted = index < currentIndex;
            const isPending = index > currentIndex;

            const statusLabel = isCompleted
              ? "completed"
              : isActive
                ? "current"
                : "pending";

            return (
              <li
                key={stage.id}
                className="flex items-center flex-1 min-w-0"
                aria-current={isActive ? "step" : undefined}
                aria-label={`${stage.fullLabel}: ${stage.description}. Status: ${statusLabel}`}
              >
                <div
                  className={cn(
                    "relative flex flex-col items-center min-w-0",
                    isActive && "scale-105"
                  )}
                >
                  <div
                    className={cn(
                      "w-8 h-8 lg:w-10 lg:h-10 rounded-sm flex items-center justify-center font-mono text-xs lg:text-sm font-semibold transition-all shrink-0",
                      isCompleted && "glow-green bg-[#3fb950]/10 border border-[#3fb950] text-[#3fb950]",
                      isActive && "bg-[#58a6ff] text-[#0d1117] glow-blue",
                      isPending && "bg-[#161b22] border border-[#30363d] text-[#8b949e]"
                    )}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 lg:w-5 lg:h-5" aria-hidden="true" />
                    ) : (
                      stage.label
                    )}
                  </div>
                  <p
                    className={cn(
                      "mt-1.5 text-xs lg:text-sm font-mono font-medium text-center truncate w-full px-0.5",
                      isActive ? "text-[#e6edf3]" : "text-[#8b949e]"
                    )}
                  >
                    <span className="hidden lg:inline">{stage.fullLabel}</span>
                    <span className="lg:hidden">{stage.shortLabel}</span>
                  </p>

                  {isActive && (
                    <div className="absolute -bottom-1 w-2 h-2 rounded-full bg-[#58a6ff] animate-pulse-dot" aria-hidden="true" />
                  )}
                </div>

                {index < PIPELINE_STAGES.length - 1 && (
                  <div
                    className={cn(
                      "flex-1 min-w-[16px] max-w-[60px] h-1 mx-1 lg:mx-2 shrink transition-colors",
                      isCompleted ? "bg-[#3fb950] shadow-[0_0_8px_rgba(63,185,80,0.3)]" : "bg-[#30363d]"
                    )}
                    aria-hidden="true"
                  />
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
}
