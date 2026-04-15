"use client";

import { useState, useEffect } from "react";
import { useWorkbenchStore } from "@/stores/workbench";
import type { SpineStage, OperatingMode } from "@/types/spine";
import styles from "./workbench.module.css";

interface ScenarioListItem {
  id: string;
  title: string;
}

export function IntakeTab() {
  const {
    input_raw_note,
    input_owner_note,
    input_structured_json,
    input_itinerary_text,
    operating_mode,
    stage,
    scenario_id,
    strict_leakage,
    debug_raw_json,
    result_run_ts,
    setInputRawNote,
    setInputOwnerNote,
    setInputStructuredJson,
    setInputItineraryText,
    setOperatingMode,
    setStage,
    setScenarioId,
    setStrictLeakage,
    setDebugRawJson,
    setResultPacket,
    setResultValidation,
    setResultDecision,
    setResultStrategy,
    setResultInternalBundle,
    setResultTravelerBundle,
    setResultLeakage,
    setResultAssertions,
    setResultRunTs,
  } = useWorkbenchStore();

  const [scenarios, setScenarios] = useState<ScenarioListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/scenarios")
      .then((res) => res.json())
      .then((data) => setScenarios(data.items || []))
      .catch(() => setScenarios([]));
  }, []);

  const handleScenarioChange = async (newScenarioId: string) => {
    setScenarioId(newScenarioId);
    if (!newScenarioId) return;

    try {
      const res = await fetch(`/api/scenarios/${newScenarioId}`);
      const data = await res.json();
      if (data.input) {
        setInputRawNote(data.input.raw_note || "");
        setInputOwnerNote(data.input.owner_note || "");
        setInputStructuredJson(
          data.input.structured_json
            ? JSON.stringify(data.input.structured_json, null, 2)
            : ""
        );
        setInputItineraryText(data.input.itinerary_text || "");
        if (data.input.stage) setStage(data.input.stage as SpineStage);
        if (data.input.mode) setOperatingMode(data.input.mode as OperatingMode);
      }
    } catch {
      // Silently handle error
    }
  };

  const handleStructuredJsonChange = (value: string) => {
    setInputStructuredJson(value);
    if (value.trim()) {
      try {
        JSON.parse(value);
        setJsonError(null);
      } catch {
        setJsonError("Invalid JSON format");
      }
    } else {
      setJsonError(null);
    }
  };

  const handleRunSpine = async () => {
    if (jsonError) return;

    setRunning(true);
    setJsonError(null);

    let structuredJson: Record<string, unknown> | null = null;
    if (input_structured_json.trim()) {
      try {
        structuredJson = JSON.parse(input_structured_json);
      } catch {
        setJsonError("Invalid JSON format");
        setRunning(false);
        return;
      }
    }

    try {
      const res = await fetch("/api/spine/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_note: input_raw_note || null,
          owner_note: input_owner_note || null,
          structured_json: structuredJson,
          itinerary_text: input_itinerary_text || null,
          stage,
          operating_mode,
          strict_leakage,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setJsonError(data.error || "Spine run failed");
        setRunning(false);
        return;
      }

      setResultPacket(data.packet);
      setResultValidation(data.validation);
      setResultDecision(data.decision);
      setResultStrategy(data.strategy);
      setResultInternalBundle(data.internal_bundle);
      setResultTravelerBundle(data.traveler_bundle);
      setResultLeakage(data.leakage);
      setResultAssertions(data.assertions);
      setResultRunTs(data.run_ts);
    } catch (err) {
      setJsonError("Failed to call spine API");
    } finally {
      setRunning(false);
    }
  };

  const stages: SpineStage[] = ["discovery", "shortlist", "proposal", "booking"];
  const modes: { value: OperatingMode; label: string }[] = [
    { value: "normal_intake", label: "Normal Intake" },
    { value: "audit", label: "Audit" },
    { value: "emergency", label: "Emergency" },
    { value: "follow_up", label: "Follow Up" },
    { value: "cancellation", label: "Cancellation" },
    { value: "post_trip", label: "Post Trip" },
    { value: "coordinator_group", label: "Coordinator Group" },
    { value: "owner_review", label: "Owner Review" },
  ];

  return (
    <div>
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Scenario Selection</h2>
        <div className={styles.field}>
          <select
            className={styles.select}
            value={scenario_id}
            onChange={(e) => handleScenarioChange(e.target.value)}
          >
            <option value="">-- Select a scenario --</option>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Input Fields</h2>
        <div className={styles.row}>
          <div className={styles.col}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="raw_note">Raw Note</label>
              <textarea
                id="raw_note"
                className={styles.textarea}
                value={input_raw_note}
                onChange={(e) => setInputRawNote(e.target.value)}
                placeholder="Enter raw incoming note..."
              />
            </div>
          </div>
          <div className={styles.col}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="owner_note">Owner Note</label>
              <textarea
                id="owner_note"
                className={styles.textarea}
                value={input_owner_note}
                onChange={(e) => setInputOwnerNote(e.target.value)}
                placeholder="Enter owner note..."
              />
            </div>
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="structured_json">Structured JSON</label>
          <textarea
            id="structured_json"
            className={styles.textarea}
            value={input_structured_json}
            onChange={(e) => handleStructuredJsonChange(e.target.value)}
            placeholder='{"key": "value"}'
            style={{ minHeight: "150px", fontFamily: "monospace" }}
          />
          {jsonError && <div className={styles.error}>{jsonError}</div>}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="itinerary_text">Itinerary Text</label>
          <textarea
            id="itinerary_text"
            className={styles.textarea}
            value={input_itinerary_text}
            onChange={(e) => setInputItineraryText(e.target.value)}
            placeholder="Enter itinerary text..."
          />
        </div>
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Configuration</h2>
        <div className={styles.row}>
          <div className={styles.col}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="stage">Stage</label>
              <select
                id="stage"
                className={styles.select}
                value={stage}
                onChange={(e) => setStage(e.target.value as SpineStage)}
              >
                {stages.map((s) => (
                  <option key={s} value={s}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className={styles.col}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="operating_mode">Operating Mode</label>
              <select
                id="operating_mode"
                className={styles.select}
                value={operating_mode}
                onChange={(e) => setOperatingMode(e.target.value as OperatingMode)}
              >
                {modes.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className={styles.inlineField}>
          <label className={styles.toggle} htmlFor="strict_leakage">
            <input
              id="strict_leakage"
              type="checkbox"
              className={styles.toggleInput}
              checked={strict_leakage}
              onChange={(e) => setStrictLeakage(e.target.checked)}
            />
            <span className={styles.toggleSwitch}></span>
            <span>Strict Leakage Mode</span>
          </label>
        </div>

        <div className={styles.inlineField}>
          <label className={styles.toggle} htmlFor="debug_raw_json">
            <input
              id="debug_raw_json"
              type="checkbox"
              className={styles.toggleInput}
              checked={debug_raw_json}
              onChange={(e) => setDebugRawJson(e.target.checked)}
            />
            <span className={styles.toggleSwitch}></span>
            <span>Debug Raw JSON</span>
          </label>
        </div>
      </div>

      <div className={styles.buttonRow}>
        <button
          type="button"
          className={styles.button}
          onClick={handleRunSpine}
          disabled={running || !!jsonError}
        >
          {running ? "Running..." : "Run Spine"}
        </button>
        {result_run_ts && (
          <span style={{ alignSelf: "center", color: "var(--color-text-muted)", fontSize: "13px" }}>
            Last run: {new Date(result_run_ts).toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
}
