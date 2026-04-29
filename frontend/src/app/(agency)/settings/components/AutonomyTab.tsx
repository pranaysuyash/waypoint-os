'use client';

import { Shield, Lock, AlertTriangle, BookOpen, Zap, GitBranch, MessageCircle, FileText, Ban } from 'lucide-react';
import type { AgencySettings } from '@/hooks/useAgencySettings';

interface AutonomyTabProps {
  draft: AgencySettings;
  onChange: (updater: (prev: AgencySettings) => AgencySettings) => void;
}

const GATE_OPTIONS: Array<{ value: 'auto' | 'review' | 'block'; label: string; color: string }> = [
  { value: 'auto', label: 'Auto', color: 'bg-[var(--accent-green)] text-white' },
  { value: 'review', label: 'Review', color: 'bg-[var(--accent-amber)] text-white' },
  { value: 'block', label: 'Block', color: 'bg-[var(--accent-red)] text-white' },
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
        <h2 className="text-[var(--ui-text-sm)] font-semibold text-[var(--text-primary)]">Autonomy & AI Policy</h2>
        <p className="text-[var(--ui-text-xs)] text-[var(--text-secondary)] mt-1">
          Control how much autonomy the AI has at each decision point.
        </p>
      </div>

      {/* Approval Gates Table */}
      <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
        <div className="bg-[var(--bg-elevated)] px-4 py-2.5 border-b border-[var(--border-default)]">
          <h3 className="text-[var(--ui-text-xs)] font-semibold text-[var(--text-secondary)] uppercase tracking-wide flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" />
            Approval Gates
          </h3>
        </div>
        <div className="divide-y divide-[var(--border-default)]">
          {DECISION_STATES.map((item) => {
            const Icon = item.icon;
            const currentValue = autonomy.approval_gates[item.key] as 'auto' | 'review' | 'block';

            return (
              <div
                key={item.key}
                className={`flex items-center justify-between px-4 py-3 ${
                  item.locked ? 'bg-[var(--accent-red)/0.05]' : ''
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      item.locked
                        ? 'bg-[var(--accent-red)/0.2] text-[var(--accent-red)]'
                        : 'bg-[var(--bg-count-badge)] text-[var(--text-secondary)]'
                    }`}
                  >
                    {item.locked ? <Lock className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]">{item.label}</p>
                    <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">{item.description}</p>
                  </div>
                </div>

                {item.locked ? (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--accent-red)/0.2] text-[var(--accent-red)] text-[var(--ui-text-xs)] font-medium border border-[var(--accent-red)/0.3]">
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
                          className={`px-3 py-1.5 rounded-md text-[var(--ui-text-xs)] font-medium transition-all ${
                            isActive
                              ? opt.color
                              : 'bg-[var(--bg-count-badge)] text-[var(--text-secondary)] hover:text-[var(--text-rationale)]'
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
      <div className="rounded-lg border border-[var(--border-default)] p-4 space-y-3">
        <h3 className="text-[var(--ui-text-xs)] font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
          Mode Overrides
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] p-3 space-y-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-[var(--accent-red)]" />
              <span className="text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]">Emergency Mode</span>
            </div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Forces <span className="text-[var(--accent-red)] font-medium">block</span> on traveler-safe output.
              Never auto-proceed during emergencies.
            </p>
            <div className="text-[var(--ui-text-sm)] text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 px-2 py-1 rounded inline-block">
              Active override: Traveler-Safe Output will always require approval
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] p-3 space-y-2">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[var(--accent-amber)]" />
              <span className="text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]">Audit Mode</span>
            </div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Forces <span className="text-[var(--accent-amber)] font-medium">review</span> on internal drafts.
              Audits always require human review.
            </p>
            <div className="text-[var(--ui-text-sm)] text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 px-2 py-1 rounded inline-block">
              Active override: Internal Drafts will always require review
            </div>
          </div>
        </div>
        <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
          These are hardcoded safety overrides. They cannot be disabled.
        </p>
      </div>

      {/* Flags */}
      <div className="rounded-lg border border-[var(--border-default)] p-4 space-y-3">
        <h3 className="text-[var(--ui-text-xs)] font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
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
              autonomy.auto_proceed_with_warnings ? 'bg-[var(--accent-blue)]' : 'bg-[var(--border-default)]'
            }`}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                autonomy.auto_proceed_with_warnings ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-primary)]">Auto-proceed with warnings</p>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
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
              autonomy.learn_from_overrides ? 'bg-[var(--accent-blue)]' : 'bg-[var(--border-default)]'
            }`}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                autonomy.learn_from_overrides ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-primary)]">Learn from overrides</p>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              When enabled, agent overrides feed back into the system to improve future
              recommendations. (Requires the learning feature to be enabled in settings.)
            </p>
          </div>
        </label>
      </div>

      {/* Autonomy policy note */}
      <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] p-4">
        <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)] leading-relaxed">
          <span className="text-[var(--accent-blue)] font-medium">How it works:</span>{' '}
          The autonomy settings control how much the AI can act on its own at each stage.
          Each decision type can be set to run automatically, queue for your review, or block
          until manually handled. For safety, trips flagged as{' '}
          <span className="text-[var(--accent-red)] font-medium">Needs Review</span> always require
          your manual approval before proceeding.
        </p>
      </div>
    </div>
  );
}
