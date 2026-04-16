"use client";

import { cn } from "@/lib/utils";
import { useEffect, useRef, useCallback } from "react";

interface TabsProps {
  tabs: { id: string; label: string; count?: number }[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export function Tabs({ tabs, activeTab, onTabChange }: TabsProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation for tabs
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const container = containerRef.current;
      if (!container) return;

      const tabElements = Array.from(
        container.querySelectorAll('[role="tab"]')
      ) as HTMLButtonElement[];
      const currentIndex = tabElements.findIndex(
        (tab) => tab.getAttribute("aria-selected") === "true"
      );

      if (currentIndex === -1) return;

      let nextIndex = currentIndex;

      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          nextIndex = currentIndex > 0 ? currentIndex - 1 : tabElements.length - 1;
          break;
        case "ArrowRight":
          e.preventDefault();
          nextIndex = currentIndex < tabElements.length - 1 ? currentIndex + 1 : 0;
          break;
        case "Home":
          e.preventDefault();
          nextIndex = 0;
          break;
        case "End":
          e.preventDefault();
          nextIndex = tabElements.length - 1;
          break;
        default:
          return;
      }

      tabElements[nextIndex].focus();
      onTabChange(tabs[nextIndex].id);
    },
    [tabs, onTabChange]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("keydown", handleKeyDown);
    return () => container.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div
      ref={containerRef}
      role="tablist"
      className="border-b border-[#30363d]"
      aria-label="Tab navigation"
    >
      <div className="flex">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            id={`tab-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "relative px-4 py-3 text-sm font-medium transition-colors outline-none",
              activeTab === tab.id
                ? "text-[#e6edf3]"
                : "text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22]"
            )}
          >
            <div className="flex items-center gap-2">
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-xs rounded bg-[#21262d] text-[#8b949e]">
                  {tab.count}
                </span>
              )}
            </div>
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#58a6ff]" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
