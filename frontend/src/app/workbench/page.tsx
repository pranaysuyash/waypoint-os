"use client";

import { useState } from "react";
import { WorkbenchTab } from "./WorkbenchTab";
import { IntakeTab } from "./IntakeTab";
import { PacketTab } from "./PacketTab";
import { DecisionTab } from "./DecisionTab";
import { StrategyTab } from "./StrategyTab";
import { SafetyTab } from "./SafetyTab";
import type { WorkbenchTabId } from "./WorkbenchTab";
import styles from "./workbench.module.css";

export default function WorkbenchPage() {
  const [activeTab, setActiveTab] = useState<WorkbenchTabId>("intake");

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Workbench</h1>
      </div>
      <WorkbenchTab activeTab={activeTab} onTabChange={setActiveTab} />
      <div className={styles.content}>
        {activeTab === "intake" && <IntakeTab />}
        {activeTab === "packet" && <PacketTab />}
        {activeTab === "decision" && <DecisionTab />}
        {activeTab === "strategy" && <StrategyTab />}
        {activeTab === "safety" && <SafetyTab />}
      </div>
    </div>
  );
}
