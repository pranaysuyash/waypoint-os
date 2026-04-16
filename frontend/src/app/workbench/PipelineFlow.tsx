"use client";

import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, AlertTriangle, HelpCircle, ChevronRight } from "lucide-react";

interface PipelineFlowProps {
  currentStage: string;
}

const stages = [
  { id: "intake", label: "1", fullLabel: "New Inquiry", description: "Capture customer request" },
  { id: "packet", label: "2", fullLabel: "Trip Details", description: "Extract trip information" },
  { id: "decision", label: "3", fullLabel: "Ready to Quote?", description: "Check if ready to price" },
  { id: "strategy", label: "4", fullLabel: "Build Options", description: "Create travel options" },
  { id: "safety", label: "5", fullLabel: "Final Review", description: "Last check before send" },
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
                    isPending && "bg-[#161b22] border border-[#30363d] text-[#8b949e]"
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
                      "text-sm font-medium",
                      isActive ? "text-[#e6edf3]" : "text-[#8b949e]"
                    )}
                  >
                    {stage.fullLabel}
                  </p>
                  <p className="text-xs text-[#8b949e] mt-0.5">{stage.description}</p>
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
