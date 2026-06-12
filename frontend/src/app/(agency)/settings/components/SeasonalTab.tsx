'use client';

import { CalendarDays, RefreshCw, SlidersHorizontal, WandSparkles, BarChart2, CircleDashed } from 'lucide-react';
import Link from 'next/link';
import type { AgencySettings } from '@/hooks/useAgencySettings';

interface SeasonalTabProps {
  draft: AgencySettings;
  onChange: (updater: (prev: AgencySettings) => AgencySettings) => void;
}

function toBlocklistValue(list: string[]) {
  return list.filter(Boolean).join('\n');
}

export function SeasonalTab({ draft, onChange }: SeasonalTabProps) {
  const seasonal = draft.seasonal ?? {
    active_seasons_enabled: true,
    default_quarter_window_months: 3,
    channel_mix: {
      organic: 0.35,
      email: 0.25,
      social: 0.2,
      paid: 0.2,
    },
    weather_risk_threshold: 0.45,
    budget_guardrail_multiplier: 1.2,
    micro_seasonality_window_days: 14,
    quarterly_recalibration_enabled: true,
    prelaunch_blocklist: [] as string[],
  };

  const channels = Object.keys(seasonal.channel_mix || {}).length
    ? Object.entries(seasonal.channel_mix || {})
    : [['organic', 0], ['email', 0], ['social', 0], ['paid', 0]];

  const updateChannel = (channel: string, value: number) => {
    onChange((prev) => {
      prev.seasonal = {
        ...prev.seasonal,
        channel_mix: {
          ...(prev.seasonal.channel_mix || {}),
          [channel]: value,
        },
      };
      return prev;
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-ui-sm font-semibold text-[#e6edf3]">Seasonal Campaign Planning</h2>
        <p className="text-ui-xs text-[#8b949e] mt-1">
          Configure how campaigns are launched across seasonal windows, with policy guardrails that stay policy-driven and auditable.
        </p>
      </div>

      <div className="rounded-xl border border-[#30363d] bg-[#0f1115] p-5 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-ui-sm font-semibold text-[#e6edf3]">Seasonal Policy</p>
            <p className="text-ui-xs text-[#8b949e]">Global policy layer that affects campaign discovery and forecast behavior.</p>
          </div>
          <Link
            href="/seasons"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#30363d] text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors"
          >
            <CalendarDays className="size-3.5" />
            Open Campaign Planner
          </Link>
        </div>

        <label className="flex items-start gap-3 cursor-pointer group">
          <span className="sr-only">Enable seasonal workflows</span>
          <input
            type="checkbox"
            checked={seasonal.active_seasons_enabled}
            onChange={() =>
              onChange((prev) => {
                prev.seasonal = {
                  ...prev.seasonal,
                  active_seasons_enabled: !prev.seasonal.active_seasons_enabled,
                };
                return prev;
              })
            }
            className="sr-only"
          />
          <div
            className={`w-9 h-5 rounded-full transition-colors relative shrink-0 mt-0.5 ${
              seasonal.active_seasons_enabled ? 'bg-[#58a6ff]' : 'bg-[#30363d]'
            }`}
          >
            <div
              className={`absolute top-0.5 size-4 bg-white rounded-full transition-transform ${
                seasonal.active_seasons_enabled ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-ui-xs font-medium text-[#e6edf3]">Enable seasonal planning</p>
            <p className="text-ui-xs text-[#8b949e]">Turn off to freeze all seasonal automation while keeping manual workflows unchanged.</p>
          </div>
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-[#30363d] bg-[#0f1115] p-4 space-y-3">
          <p className="flex items-center gap-1.5 text-ui-xs font-semibold text-[#8b949e]">
            <CalendarDays className="size-3.5" />
            Quarter windows
          </p>
          <label className="space-y-2 text-ui-xs text-[#8b949e]">
            <span className="inline-flex justify-between w-full text-ui-xs">
              <span>Default quarter window (months)</span>
              <span className="text-[#e6edf3]">{seasonal.default_quarter_window_months}</span>
            </span>
            <input
              type="range"
              min={1}
              max={24}
              value={seasonal.default_quarter_window_months}
              onChange={(e) =>
                onChange((prev) => {
                  prev.seasonal = {
                    ...prev.seasonal,
                    default_quarter_window_months: Number(e.target.value),
                  };
                  return prev;
                })
              }
              className="w-full accent-[#58a6ff]"
            />
          </label>
          <label className="space-y-2 text-ui-xs text-[#8b949e]">
            <span className="inline-flex justify-between w-full text-ui-xs">
              <span>Micro window (days)</span>
              <span className="text-[#e6edf3]">{seasonal.micro_seasonality_window_days}</span>
            </span>
            <input
              type="range"
              min={1}
              max={365}
              value={seasonal.micro_seasonality_window_days}
              onChange={(e) =>
                onChange((prev) => {
                  prev.seasonal = {
                    ...prev.seasonal,
                    micro_seasonality_window_days: Number(e.target.value),
                  };
                  return prev;
                })
              }
              className="w-full accent-[#58a6ff]"
            />
          </label>
        </div>

        <div className="rounded-xl border border-[#30363d] bg-[#0f1115] p-4 space-y-3">
          <p className="flex items-center gap-1.5 text-ui-xs font-semibold text-[#8b949e]">
            <SlidersHorizontal className="size-3.5" />
            Risk & budget guardrails
          </p>
          <label className="block space-y-1">
            <span className="text-ui-xs text-[#8b949e]">Weather risk threshold</span>
            <input
              type="number"
              step="0.01"
              min={0}
              max={1}
              value={seasonal.weather_risk_threshold}
              onChange={(e) =>
                onChange((prev) => {
                  prev.seasonal.weather_risk_threshold = Number(e.target.value);
                  return prev;
                })
              }
              className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1.5 text-ui-sm text-[#e6edf3]"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-ui-xs text-[#8b949e]">Budget guardrail multiplier</span>
            <input
              type="number"
              step="0.01"
              min={0.1}
              value={seasonal.budget_guardrail_multiplier}
              onChange={(e) =>
                onChange((prev) => {
                  prev.seasonal.budget_guardrail_multiplier = Number(e.target.value);
                  return prev;
                })
              }
              className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1.5 text-ui-sm text-[#e6edf3]"
            />
          </label>
          <label className="flex items-start gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={seasonal.quarterly_recalibration_enabled}
              onChange={() =>
                onChange((prev) => {
                  prev.seasonal = {
                    ...prev.seasonal,
                    quarterly_recalibration_enabled: !prev.seasonal.quarterly_recalibration_enabled,
                  };
                  return prev;
                })
              }
              className="sr-only"
            />
            <div
              className={`w-9 h-5 rounded-full transition-colors relative shrink-0 mt-0.5 ${
                seasonal.quarterly_recalibration_enabled ? 'bg-[#58a6ff]' : 'bg-[#30363d]'
              }`}
            >
              <div
                className={`absolute top-0.5 size-4 bg-white rounded-full transition-transform ${
                  seasonal.quarterly_recalibration_enabled ? 'left-[18px]' : 'left-0.5'
                }`}
              />
            </div>
            <div>
              <p className="text-ui-xs text-[#e6edf3]">Quarterly recalibration enabled</p>
              <p className="text-ui-xs text-[#8b949e]">Recompute recommended campaign health at quarter boundaries.</p>
            </div>
          </label>
        </div>
      </div>

      <div className="rounded-xl border border-[#30363d] bg-[#0f1115] p-4 space-y-3">
        <p className="flex items-center gap-1.5 text-ui-xs font-semibold text-[#8b949e]">
          <BarChart2 className="size-3.5" />
          Channel mix
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {channels.map(([channel, weight]) => (
            <label key={channel} className="space-y-1.5">
              <span className="text-ui-xs text-[#8b949e] capitalize">{channel}</span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={typeof weight === 'number' ? weight : 0}
                  onChange={(e) => updateChannel(channel, Number(e.target.value))}
                  className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1.5 text-ui-sm text-[#e6edf3]"
                />
                <WandSparkles className="size-3.5 text-[#8b949e]" />
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-[#30363d] bg-[#0f1115] p-4 space-y-3">
        <p className="flex items-center gap-1.5 text-ui-xs font-semibold text-[#8b949e]">
          <RefreshCw className="size-3.5" />
          Prelaunch blocklist
        </p>
        <textarea
          value={toBlocklistValue(seasonal.prelaunch_blocklist || [])}
          onChange={(event) =>
            onChange((prev) => {
              prev.seasonal = {
                ...prev.seasonal,
                prelaunch_blocklist: event.target.value
                  .split('\n')
                  .map((entry) => entry.trim())
                  .filter(Boolean),
              };
              return prev;
            })
          }
          rows={4}
          placeholder="budget_violation\ndestination_mismatch\nchannel_underweight"
          className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-2.5 py-2 text-ui-sm text-[#e6edf3]"
        />
        <p className="text-ui-xs text-[#8b949e]">
          Each line is a block reason tag considered during campaign prelaunch checks.
        </p>
        <div className="text-ui-xs rounded-lg border border-[#30363d] bg-[#161b22] p-2.5 text-[#8b949e] flex items-center gap-2">
          <CircleDashed className="size-3.5" />
          Add custom tags conservatively; this list is additive with canonical risk checks.
        </div>
      </div>
    </div>
  );
}
