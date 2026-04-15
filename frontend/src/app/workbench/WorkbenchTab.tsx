"use client";

import { useEffect, useRef } from "react";
import styles from "./workbench.module.css";
import { handleListNavigation, generateId } from "@/lib/accessibility";

export type WorkbenchTabId = "intake" | "packet" | "decision" | "strategy" | "safety";

interface WorkbenchTabProps {
  activeTab: WorkbenchTabId;
  onTabChange: (tab: WorkbenchTabId) => void;
}

const TABS: { id: WorkbenchTabId; label: string }[] = [
  { id: "intake", label: "Intake" },
  { id: "packet", label: "Packet" },
  { id: "decision", label: "Decision" },
  { id: "strategy", label: "Strategy" },
  { id: "safety", label: "Safety" },
];

// Generate stable IDs for ARIA relationships
const tabListId = "workbench-tablist";
const tabIds = TABS.reduce((acc, tab) => {
  acc[tab.id] = `workbench-tab-${tab.id}`;
  acc[`${tab.id}-panel`] = `workbench-panel-${tab.id}`;
  return acc;
}, {} as Record<string, string>);

export function WorkbenchTab({ activeTab, onTabChange }: WorkbenchTabProps) {
  const focusedIndex = useRef(TABS.findIndex(t => t.id === activeTab));

  // Update focused index when active tab changes externally
  useEffect(() => {
    focusedIndex.current = TABS.findIndex(t => t.id === activeTab);
  }, [activeTab]);

  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    const newIndex = handleListNavigation(event, index, TABS.length, "horizontal");

    if (newIndex !== null) {
      focusedIndex.current = newIndex;
      const newTab = TABS[newIndex];
      onTabChange(newTab.id);
      // Focus the new tab button
      event.currentTarget.parentElement?.children[newIndex]?.querySelector("button")?.focus();
    }
  };

  return (
    <>
      <div
        className={styles.tabs}
        role="tablist"
        aria-label="Workbench tabs"
        id={tabListId}
      >
        {TABS.map((tab, index) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              type="button"
              key={tab.id}
              id={tabIds[tab.id]}
              className={`${styles.tab} ${isActive ? styles.tabActive : ""}`}
              onClick={() => onTabChange(tab.id)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              role="tab"
              aria-selected={isActive}
              aria-controls={tabIds[`${tab.id}-panel`]}
              tabIndex={isActive ? 0 : -1}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      {/* Hidden live region for announcing tab changes */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {TABS.find(t => t.id === activeTab)?.label} tab selected
      </div>
    </>
  );
}

// Export tab panel IDs for use in content
export function getTabPanelId(tabId: WorkbenchTabId): string {
  return tabIds[`${tabId}-panel`];
}

export function getTabButtonId(tabId: WorkbenchTabId): string {
  return tabIds[tabId];
}
