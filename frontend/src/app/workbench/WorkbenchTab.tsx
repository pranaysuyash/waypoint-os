"use client";

import styles from "./workbench.module.css";

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

export function WorkbenchTab({ activeTab, onTabChange }: WorkbenchTabProps) {
  return (
    <div className={styles.tabs}>
      {TABS.map((tab) => (
        <button
          type="button"
          key={tab.id}
          className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ""}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
