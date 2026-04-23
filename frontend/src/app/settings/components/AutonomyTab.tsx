'use client';

import { Shield, Lock, AlertTriangle, BookOpen, Zap, GitBranch, MessageCircle, FileText, Ban } from 'lucide-react';
import type { AgencySettings } from '@/hooks/useAgencySettings';

interface AutonomyTabProps {
  draft: AgencySettings;
  onChange: (updater: (prev: AgencySettings) => AgencySettings) => void;
}

const GATE_OPTIONS: Array<{ value: 'auto' | 'review' | 'block'; label: string; color: string }> = [
  { value: 'auto', label: 'Auto', color: 'bg-[#3fb950] text-white' },
  { value: 'review', label: 'Review', color: 'bg-[#d29922] text-white' },
  { value: 'block', label: 'Block', color: 'bg-[#f85149] text-white' },
];

const DECISION_STATES: Array<{
  key: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  locked?: boolean;
}> = [
  {
    key: 'ASK_FOLLOWUP',
    label: 'Ask Follow-up',
    description: 'AI needs more information from the traveler',
    icon: MessageCircle,
  },
  {
    key: 'PROCEED_INTERNAL_DRAFT',
    label: 'Internal Draft',
    description: 'Generate a draft for internal review only',
    icon: FileText,
  },
  {
    key: 'PROCEED_TRAVELER_SAFE',
    label: 'Traveler-Safe Output',
    description: 'Generate output safe to send to the traveler',
    icon: Zap,
  },
  {
    key: 'BRANCH_OPTIONS',
    label: 'Branch Options',
    description: 'Present multiple options for the traveler to choose',
    icon: GitBranch,
  },
  {
    key: 'STOP_NEEDS_REVIEW',
    label: 'Needs Review',
    description: 'Critical issue detected — requires human attention',
    icon: Ban,
    locked: true,
  },
] as const;

export function AutonomyTab({ draft, onChange }: AutonomyTabProps) {
  const autonomy = draft.autonomy;

  const setGate = (state: string, action: 'auto' | 'review' | 'block') => {
    if (state === 'STOP_NEEDS_REVIEW') return; // Safety invariant
    onChange((prev) => {
      prev.autonomy.approval_gates[state] = action;
      return prev;
    });
  };

  const toggleFlag = (key: 'auto_proceed_with_warnings' | 'learn_from_overrides') => {
    onChange((prev) => {
      prev.autonomy[key] = !prev.autonomy[key];
      return prev;
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-semibold text-[#e6edf3]">Autonomy & AI Policy</h2>
        <p className="text-xs text-[#8b949e] mt-1">
          Control how much autonomy the AI has at each decision point. This is the D1 policy contract.
        </p>
      </div>

      {/* Approval Gates Table */}
      <div className="rounded-lg border border-[#30363d] overflow-hidden">
        <div className="bg-[#161b22] px-4 py-2.5 border-b border-[#30363d]">
          <h3 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wide flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" />
            Approval Gates
          </h3>
        </div>
        <div className="divide-y divide-[#30363d]">
          {DECISION_STATES.map((item) => {
            const Icon = item.icon;
            const currentValue = autonomy.approval_gates[item.key] as 'auto' | 'review' | 'block';

            return (
              <div
                key={item.key}
                className={`flex items-center justify-between px-4 py-3 ${
                  item.locked ? 'bg-[#f85149]/5' : ''
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      item.locked
                        ? 'bg-[#f85149]/20 text-[#f85149]'
                        : 'bg-[#21262d] text-[#8b949e]'
                    }`}
                  >
                    {item.locked ? <Lock className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[#e6edf3]">{item.label}</p>
                    <p className="text-[11px] text-[#8b949e]">{item.description}</p>
                  </div>
                </div>

                {item.locked ? (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#f85149]/20 text-[#f85149] text-xs font-medium border border-[#f85149]/30">
                    <Lock className="w-3 h-3" />
                    Always Block
                  </div>
                ) : (
                  <div className="flex items-center gap-1 shrink-0">
                    {GATE_OPTIONS.map((opt) => {
                      const isActive = currentValue === opt.value;
                      return (
                        <button
                          key={opt.value}
                          onClick={() => setGate(item.key, opt.value)}
                          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                            isActive
                              ? opt.color
                              : 'bg-[#21262d] text-[#8b949e] hover:text-[#c9d1d9]'
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Mode Overrides */}
      <div className="rounded-lg border border-[#30363d] p-4 space-y-3">
        <h3 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wide">
          Mode Overrides
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-3 space-y-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-[#f85149]" />
              <span className="text-sm font-medium text-[#e6edf3]">Emergency Mode</span>
            </div>
            <p className="text-[11px] text-[#8b949e]">
              Forces <span className="text-[#f85149] font-medium">block</span> on traveler-safe output.
              Never auto-proceed during emergencies.
            </p>
            <div className="text-[11px] text-[#58a6ff] bg-[#58a6ff]/10 px-2 py-1 rounded inline-block">
              Active override: PROCEED_TRAVELER_SAFE → block
            </div>
          </div>

          <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-3 space-y-2">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[#d29922]" />
              <span className="text-sm font-medium text-[#e6edf3]">Audit Mode</span>
            </div>
            <p className="text-[11px] text-[#8b949e]">
              Forces <span className="text-[#d29922] font-medium">review</span> on internal drafts.
              Audits always require human review.
            </p>
            <div className="text-[11px] text-[#58a6ff] bg-[#58a6ff]/10 px-2 py-1 rounded inline-block">
              Active override: PROCEED_INTERNAL_DRAFT → review
            </div>
          </div>
        </div>
        <p className="text-[11px] text-[#8b949e]">
          These are hardcoded safety overrides. They cannot be disabled.
        </p>
      </div>

      {/* Flags */}
      <div className="rounded-lg border border-[#30363d] p-4 space-y-3">
        <h3 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wide">
          Advanced Flags
        </h3>

        <label className="flex items-start gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={autonomy.auto_proceed_with_warnings}
            onChange={() => toggleFlag('auto_proceed_with_warnings')}
            className="sr-only"
          />
          <div
            className={`w-9 h-5 rounded-full transition-colors relative shrink-0 mt-0.5 ${
              autonomy.auto_proceed_with_warnings ? 'bg-[#58a6ff]' : 'bg-[#30363d]'
            }`}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                autonomy.auto_proceed_with_warnings ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-sm text-[#e6edf3]">Auto-proceed with warnings</p>
            <p className="text-[11px] text-[#8b949e]">
              If enabled, the AI will auto-proceed even when suitability warnings exist.
              Otherwise, any warning triggers the review gate.
            </p>
          </div>
        </label>

        <label className="flex items-start gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={autonomy.learn_from_overrides}
            onChange={() => toggleFlag('learn_from_overrides')}
            className="sr-only"
          />
          <div
            className={`w-9 h-5 rounded-full transition-colors relative shrink-0 mt-0.5 ${
              autonomy.learn_from_overrides ? 'bg-[#58a6ff]' : 'bg-[#30363d]'
            }`}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                autonomy.learn_from_overrides ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-sm text-[#e6edf3]">Learn from overrides</p>
            <p className="text-[11px] text-[#8b949e]">
              When enabled, agent overrides feed back into the system to improve future
              recommendations. (Requires D5 learning loop to be active.)
            </p>
          </div>
        </label>
      </div>

      {/* D1 ADR reference */}
      <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-4">
        <p className="text-[11px] text-[#8b949e] leading-relaxed">
          <span className="text-[#58a6ff] font-medium">Architecture Decision D1:</span>{' '}
          The autonomy gradient is the gate between NB02 judgment and NB03 execution.
          It preserves the raw NB02 verdict while adding a policy-controlled layer that
          determines whether the system acts automatically, queues for review, or blocks.
          Safety invariant: <span className="text-[#f85149] font-medium">STOP_NEEDS_REVIEW</span> is always "block".
        </p>
      </div>
    </div>
  );
}
