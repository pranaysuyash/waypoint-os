"use client";

import { useWorkbenchStore } from "@/stores/workbench";
import type { StrategyOutput } from "@/types/spine";
import Link from "next/link";

interface StrategyPanelProps {
  tripId: string;
}

export function StrategyPanel({ tripId }: StrategyPanelProps) {
  const { result_strategy, debug_raw_json, setDebugRawJson } = useWorkbenchStore();
  const strategy = result_strategy as StrategyOutput | null;

  if (!strategy) {
    return (
      <div className="p-6 text-center">
        <h2 className="text-ui-xl font-semibold text-text-primary">Ready to build trip options</h2>
        <p className="text-ui-sm text-text-muted mt-2">Required trip details are complete. Option generation will appear here once the options builder is connected.</p>
        <div className="mt-4 text-ui-xs text-text-muted">
          Recommended details missing: trip priorities / must-haves.
        </div>
        <div className="mt-6 flex flex-wrap gap-3 justify-center">
          <span
            className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-3 py-2 text-ui-sm font-medium text-text-muted opacity-50 cursor-not-allowed"
          >
            Options builder not connected yet
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Session Goal</h3>
        <div className="bg-sidebar rounded-lg border border-highlight p-4 text-ui-sm text-text-secondary">
          {strategy.session_goal || "-"}
        </div>
      </section>

      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Suggested Opening</h3>
        <div className="bg-sidebar rounded-lg border border-highlight p-4 text-ui-sm text-text-secondary italic">
          "{strategy.suggested_opening || "-"}"
        </div>
      </section>

      {strategy.priority_sequence && strategy.priority_sequence.length > 0 && (
        <section>
          <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Priority Sequence</h3>
          <ol className="list-decimal list-inside space-y-2 bg-sidebar rounded-lg border border-highlight p-4 text-ui-sm text-text-secondary">
            {strategy.priority_sequence.map((item, i) => (
              <li key={`priority-${item.slice(0, 20)}-${i}`}>{item}</li>
            ))}
          </ol>
        </section>
      )}

      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
          Tone: {strategy.suggested_tone || "-"}
        </h3>
        {strategy.tonal_guardrails && strategy.tonal_guardrails.length > 0 && (
          <ul className="bg-sidebar rounded-lg border border-highlight p-4 space-y-2 text-ui-sm text-text-secondary">
            {strategy.tonal_guardrails.map((guardrail, i) => (
              <li key={`guard-${guardrail.slice(0, 20)}-${i}`} className="flex items-start gap-2">
                <span className="text-accent-blue mt-0.5">•</span>
                {guardrail}
              </li>
            ))}
          </ul>
        )}
      </section>

      {strategy.assumptions && strategy.assumptions.length > 0 && (
        <section>
          <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-text-muted mb-3">Assumptions</h3>
          <ul className="bg-sidebar rounded-lg border border-highlight p-4 space-y-2 text-ui-sm text-text-secondary">
            {strategy.assumptions.map((assumption, i) => (
              <li key={`assume-${assumption.slice(0, 20)}-${i}`} className="flex items-start gap-2">
                <span className="text-accent-amber mt-0.5">?</span>
                {assumption}
              </li>
            ))}
          </ul>
        </section>
      )}

      <button
        type="button"
        className="text-ui-xs text-accent-blue hover:text-accent-blue underline"
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>

      {debug_raw_json && (
        <pre className="bg-sidebar p-4 rounded text-ui-xs font-mono text-text-muted overflow-x-auto">
          {JSON.stringify({ strategy }, null, 2)}
        </pre>
      )}
    </div>
  );
}
