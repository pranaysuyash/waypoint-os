'use client';

import { useWorkbenchStore } from '@/stores/workbench';
import type { Trip } from '@/lib/api-client';
import type { ReadinessAssessment } from '@/types/spine';

interface OpsPanelProps {
  trip?: Trip | null;
}

export default function OpsPanel({ trip }: OpsPanelProps) {
  const { result_validation } = useWorkbenchStore();

  const readiness: ReadinessAssessment | undefined =
    (result_validation as { readiness?: ReadinessAssessment } | null)?.readiness ??
    (trip?.validation as { readiness?: ReadinessAssessment } | null)?.readiness;

  if (!readiness) {
    return (
      <div data-testid="ops-panel-empty" className="text-sm text-[#8b949e]">
        No readiness data available. Run the pipeline to generate a readiness assessment.
      </div>
    );
  }

  const tiers = readiness.tiers ?? {};
  const tierEntries = Object.entries(tiers);
  const signals = readiness.signals;

  return (
    <div data-testid="ops-panel" className="space-y-6">
      {/* Highest tier summary */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-[#8b949e]">Highest ready tier:</span>
        <span
          data-testid="ops-highest-tier"
          className="text-sm font-medium text-[#e6edf3]"
        >
          {readiness.highest_ready_tier ?? 'none'}
        </span>
      </div>

      {/* Tier details */}
      {tierEntries.length > 0 && (
        <div data-testid="ops-tiers" className="space-y-4">
          <h3 className="text-sm font-medium text-[#e6edf3]">Booking Readiness Tiers</h3>
          {tierEntries.map(([name, tier]) => (
            <div
              key={name}
              data-testid={`ops-tier-${name}`}
              className="border border-[#30363d] rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-[#e6edf3]">
                  {name.replace(/_/g, ' ')}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    tier.ready
                      ? 'bg-emerald-900/50 text-emerald-400'
                      : 'bg-red-900/50 text-red-400'
                  }`}
                >
                  {tier.ready ? 'Ready' : 'Not ready'}
                </span>
              </div>
              {tier.met.length > 0 && (
                <div className="mb-1">
                  <span className="text-xs text-[#8b949e]">Met: </span>
                  <span className="text-xs text-emerald-400">{tier.met.join(', ')}</span>
                </div>
              )}
              {tier.unmet.length > 0 && (
                <div>
                  <span className="text-xs text-[#8b949e]">Missing: </span>
                  <span className="text-xs text-red-400">{tier.unmet.join(', ')}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Missing for next stage */}
      {readiness.missing_for_next.length > 0 && (
        <div data-testid="ops-missing" className="border border-[#30363d] rounded-lg p-4">
          <span className="text-xs text-[#8b949e]">Fields blocking next tier: </span>
          <span className="text-xs text-amber-400">
            {readiness.missing_for_next.join(', ')}
          </span>
        </div>
      )}

      {/* Auxiliary signals */}
      {signals && Object.keys(signals).length > 0 && (
        <div data-testid="ops-signals" className="border border-[#30363d] rounded-lg p-4">
          <h4 className="text-sm font-medium text-[#e6edf3] mb-2">Signals</h4>
          {signals.visa_concerns_present === true && (
            <div
              data-testid="ops-signal-visa-concern"
              className="flex items-center gap-2 text-sm"
            >
              <span className="text-amber-400">Visa/Passport concern detected</span>
              <span className="text-xs text-[#8b949e]">
                Traveler input mentions visa or passport topics. Review may be needed.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
