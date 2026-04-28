'use client';

import { Percent, Clock, Calendar, MessageSquare, Mic } from 'lucide-react';
import type { AgencySettings } from '@/hooks/useAgencySettings';

interface OperationalTabProps {
  draft: AgencySettings;
  onChange: (updater: (prev: AgencySettings) => AgencySettings) => void;
}

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'AUD', 'CAD', 'SGD', 'AED'];
const BRAND_TONES = ['professional', 'friendly', 'casual', 'direct', 'cautious', 'measured', 'confident'];
const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
const DAY_LABELS: Record<string, string> = {
  mon: 'Mon', tue: 'Tue', wed: 'Wed', thu: 'Thu', fri: 'Fri', sat: 'Sat', sun: 'Sun',
};
const CHANNELS = ['whatsapp', 'email', 'phone', 'sms'];

export function OperationalTab({ draft, onChange }: OperationalTabProps) {
  const op = draft.operational;

  const toggleDay = (day: string) => {
    onChange((prev) => {
      const days = prev.operational.operating_days;
      if (days.includes(day)) {
        prev.operational.operating_days = days.filter((d) => d !== day);
      } else {
        prev.operational.operating_days = [...days, day];
      }
      return prev;
    });
  };

  const toggleChannel = (channel: string) => {
    onChange((prev) => {
      const channels = prev.operational.preferred_channels;
      if (channels.includes(channel)) {
        prev.operational.preferred_channels = channels.filter((c) => c !== channel);
      } else {
        prev.operational.preferred_channels = [...channels, channel];
      }
      return prev;
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-semibold text-[#e6edf3]">Operations</h2>
        <p className="text-xs text-[#8b949e] mt-1">
          Business rules that affect budget feasibility, AI tone, and communication.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Margin */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-[#8b949e]">
            <Percent className="w-3.5 h-3.5" />
            Target Margin (%)
          </label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={0}
              max={100}
              value={op.target_margin_pct}
              onChange={(e) =>
                onChange((prev) => {
                  prev.operational.target_margin_pct = parseFloat(e.target.value);
                  return prev;
                })
              }
              className="flex-1 accent-[#58a6ff]"
            />
            <span className="text-sm font-mono text-[#e6edf3] w-12 text-right">
              {op.target_margin_pct}%
            </span>
          </div>
          <p className="text-[11px] text-[#8b949e]">
            Used in budget feasibility scoring. Higher margins mean stricter budget checks.
          </p>
        </div>

        {/* Currency */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-[#8b949e]">
            <Percent className="w-3.5 h-3.5" />
            Default Currency
          </label>
          <select
            value={op.default_currency}
            onChange={(e) =>
              onChange((prev) => {
                prev.operational.default_currency = e.target.value;
                return prev;
              })
            }
            className="w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none"
          >
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* Operating Hours */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-[#8b949e]">
            <Clock className="w-3.5 h-3.5" />
            Operating Hours
          </label>
          <div className="flex items-center gap-2">
            <input
              type="time"
              value={op.operating_hours.start}
              onChange={(e) =>
                onChange((prev) => {
                  prev.operational.operating_hours.start = e.target.value;
                  return prev;
                })
              }
              className="px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]"
            />
            <span className="text-[#8b949e]">to</span>
            <input
              type="time"
              value={op.operating_hours.end}
              onChange={(e) =>
                onChange((prev) => {
                  prev.operational.operating_hours.end = e.target.value;
                  return prev;
                })
              }
              className="px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]"
            />
          </div>
        </div>

        {/* Brand Tone */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-[#8b949e]">
            <Mic className="w-3.5 h-3.5" />
            AI Brand Tone
          </label>
          <select
            value={op.brand_tone}
            onChange={(e) =>
              onChange((prev) => {
                prev.operational.brand_tone = e.target.value;
                return prev;
              })
            }
            className="w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none"
          >
            {BRAND_TONES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-[#8b949e]">
            How the AI sounds when generating traveler-facing messages and options.
          </p>
        </div>
      </div>

      {/* Operating Days */}
      <div className="space-y-2">
        <label className="flex items-center gap-1.5 text-xs font-medium text-[#8b949e]">
          <Calendar className="w-3.5 h-3.5" />
          Operating Days
        </label>
        <div className="flex flex-wrap gap-2">
          {DAYS.map((day) => {
            const isActive = op.operating_days.includes(day);
            return (
              <button
                key={day}
                onClick={() => toggleDay(day)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-[#58a6ff]/20 text-[#58a6ff] border border-[#58a6ff]/40'
                    : 'bg-[#161b22] text-[#8b949e] border border-[#30363d] hover:text-[#c9d1d9]'
                }`}
              >
                {DAY_LABELS[day]}
              </button>
            );
          })}
        </div>
      </div>

      {/* Preferred Channels */}
      <div className="space-y-2">
        <label className="flex items-center gap-1.5 text-xs font-medium text-[#8b949e]">
          <MessageSquare className="w-3.5 h-3.5" />
          Preferred Communication Channels
        </label>
        <div className="flex flex-wrap gap-2">
          {CHANNELS.map((channel) => {
            const isActive = op.preferred_channels.includes(channel);
            return (
              <button
                key={channel}
                onClick={() => toggleChannel(channel)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
                  isActive
                    ? 'bg-[#58a6ff]/20 text-[#58a6ff] border border-[#58a6ff]/40'
                    : 'bg-[#161b22] text-[#8b949e] border border-[#30363d] hover:text-[#c9d1d9]'
                }`}
              >
                {channel}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
