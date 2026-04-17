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
    <div className="px-4 lg:px-6 py-3 lg:py-4 border-b border-[#30363d] bg-[#0a0c0e]">
      <div className="flex items-center max-w-5xl mx-auto">
        {stages.map((stage, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;
          const isPending = index > currentIndex;

          return (
            <div key={stage.id} className="flex items-center flex-1 min-w-0">
              <div
                className={cn(
                  "relative flex flex-col items-center flex-1 min-w-0",
                  isActive && "scale-105"
                )}
              >
                <div
                  className={cn(
                    "w-8 h-8 lg:w-10 lg:h-10 rounded-lg flex items-center justify-center font-mono text-xs lg:text-sm font-semibold transition-all shrink-0",
                    isCompleted && "bg-[#3fb950]/10 border border-[#3fb950] text-[#3fb950]",
                    isActive && "bg-[#58a6ff] text-[#0d1117] shadow-lg shadow-[#58a6ff]/20",
                    isPending && "bg-[#161b22] border border-[#30363d] text-[#8b949e]"
                  )}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 lg:w-5 lg:h-5" />
                  ) : (
                    stage.label
                  )}
                </div>
                <p
                  className={cn(
                    "mt-1.5 text-xs lg:text-sm font-medium text-center truncate w-full px-0.5",
                    isActive ? "text-[#e6edf3]" : "text-[#8b949e]"
                  )}
                >
                  <span className="hidden lg:inline">{stage.fullLabel}</span>
                  <span className="lg:hidden">{stage.fullLabel.split(" ")[0]}</span>
                </p>

                {isActive && (
                  <div className="absolute -bottom-1 w-2 h-2 rounded-full bg-[#58a6ff] animate-pulse" />
                )}
              </div>

              {index < stages.length - 1 && (
                <div
                  className={cn(
                    "flex-1 min-w-[16px] max-w-[60px] h-0.5 mx-1 lg:mx-2 shrink transition-colors",
                    isCompleted ? "bg-[#3fb950]" : "bg-[#30363d]"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
