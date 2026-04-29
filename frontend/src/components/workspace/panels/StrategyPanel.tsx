"use client";

import { useWorkbenchStore } from "@/stores/workbench";
import type { StrategyOutput } from "@/types/spine";

interface StrategyPanelProps {
  tripId: string;
}

export function StrategyPanel({ tripId }: StrategyPanelProps) {
  const { result_strategy, debug_raw_json, setDebugRawJson } = useWorkbenchStore();
  const strategy = result_strategy as StrategyOutput | null;

  if (!strategy) {
    return (
      <div className="p-4 text-ui-sm text-gray-500 italic">
        No options data for trip {tripId}. Process a trip from the "New Inquiry" section first.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Session Goal</h3>
        <div className="bg-sidebar rounded-lg border border-highlight p-4 text-ui-sm text-gray-300">
          {strategy.session_goal || "—"}
        </div>
      </section>

      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Suggested Opening</h3>
        <div className="bg-sidebar rounded-lg border border-highlight p-4 text-ui-sm text-gray-300 italic">
          "{strategy.suggested_opening || "—"}"
        </div>
      </section>

      {strategy.priority_sequence && strategy.priority_sequence.length > 0 && (
        <section>
          <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Priority Sequence</h3>
          <ol className="list-decimal list-inside space-y-2 bg-sidebar rounded-lg border border-highlight p-4 text-ui-sm text-gray-300">
            {strategy.priority_sequence.map((item, i) => (
              <li key={`priority-${item.slice(0, 20)}-${i}`}>{item}</li>
            ))}
          </ol>
        </section>
      )}

      <section>
        <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
          Tone: {strategy.suggested_tone || "—"}
        </h3>
        {strategy.tonal_guardrails && strategy.tonal_guardrails.length > 0 && (
          <ul className="bg-sidebar rounded-lg border border-highlight p-4 space-y-2 text-ui-sm text-gray-300">
            {strategy.tonal_guardrails.map((guardrail, i) => (
              <li key={`guard-${guardrail.slice(0, 20)}-${i}`} className="flex items-start gap-2">
                <span className="text-blue-400 mt-0.5">•</span>
                {guardrail}
              </li>
            ))}
          </ul>
        )}
      </section>

      {strategy.assumptions && strategy.assumptions.length > 0 && (
        <section>
          <h3 className="text-ui-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Assumptions</h3>
          <ul className="bg-sidebar rounded-lg border border-highlight p-4 space-y-2 text-ui-sm text-gray-300">
            {strategy.assumptions.map((assumption, i) => (
              <li key={`assume-${assumption.slice(0, 20)}-${i}`} className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">?</span>
                {assumption}
              </li>
            ))}
          </ul>
        </section>
      )}

      <button
        type="button"
        className="text-ui-xs text-blue-400 hover:text-blue-300 underline"
        onClick={() => setDebugRawJson(!debug_raw_json)}
      >
        {debug_raw_json ? "Hide" : "Show"} Technical Data
      </button>

      {debug_raw_json && (
        <pre className="bg-sidebar p-4 rounded text-ui-xs font-mono text-gray-400 overflow-x-auto">
          {JSON.stringify({ strategy }, null, 2)}
        </pre>
      )}
    </div>
  );
}
