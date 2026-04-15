"use client";

import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, AlertTriangle, HelpCircle, ChevronRight } from "lucide-react";

interface PipelineFlowProps {
  currentStage: string;
}

const stages = [
  { id: "intake", label: "NB01", fullLabel: "Intake", description: "Parse Input" },
  { id: "packet", label: "NB02", fullLabel: "Packet", description: "Extract Facts" },
  { id: "decision", label: "NB03", fullLabel: "Decision", description: "Validate & Decide" },
  { id: "strategy", label: "NB04", fullLabel: "Strategy", description: "Build Bundles" },
  { id: "safety", label: "NB05", fullLabel: "Safety", description: "Final Check" },
];

export function PipelineFlow({ currentStage }: PipelineFlowProps) {
  const currentIndex = stages.findIndex((s) => s.id === currentStage);

  return (
    <div className="px-6 py-4 border-b border-[#30363d] bg-[#0a0c0e]">
      <div className="flex items-center justify-between max-w-5xl mx-auto">
        {stages.map((stage, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;
          const isPending = index > currentIndex;

          return (
            <div key={stage.id} className="flex items-center">
              {/* Stage Node */}
              <div
                className={cn(
                  "relative flex flex-col items-center",
                  isActive && "scale-105"
                )}
              >
                <div
                  className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center font-mono text-sm font-semibold transition-all",
                    isCompleted && "bg-[#3fb950]/10 border border-[#3fb950] text-[#3fb950]",
                    isActive && "bg-[#58a6ff] text-[#0d1117] shadow-lg shadow-[#58a6ff]/20",
                    isPending && "bg-[#161b22] border border-[#30363d] text-[#6e7681]"
                  )}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    stage.label
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p
                    className={cn(
                      "text-xs font-medium",
                      isActive ? "text-[#e6edf3]" : "text-[#8b949e]"
                    )}
                  >
                    {stage.fullLabel}
                  </p>
                  <p className="text-[10px] text-[#6e7681] mt-0.5">{stage.description}</p>
                </div>

                {/* Active Indicator */}
                {isActive && (
                  <div className="absolute -bottom-1 w-2 h-2 rounded-full bg-[#58a6ff] animate-pulse" />
                )}
              </div>

              {/* Connector Line */}
              {index < stages.length - 1 && (
                <div className="flex items-center mx-4">
                  <div
                    className={cn(
                      "w-12 h-0.5 transition-colors",
                      isCompleted ? "bg-[#3fb950]" : "bg-[#30363d]"
                    )}
                  />
                  <ChevronRight
                    className={cn(
                      "w-4 h-4 -ml-1",
                      isCompleted ? "text-[#3fb950]" : "text-[#30363d]"
                    )}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
