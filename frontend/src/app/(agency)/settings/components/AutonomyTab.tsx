'use client';

import { useId } from 'react';
import { Shield, Lock, AlertTriangle, BookOpen, Zap, GitBranch, MessageCircle, FileText, Ban } from 'lucide-react';
import type { AgencySettings } from '@/hooks/useAgencySettings';

interface AutonomyTabProps {
  draft: AgencySettings;
  onChange: (updater: (prev: AgencySettings) => AgencySettings) => void;
}

const GATE_OPTIONS: Array<{ value: 'auto' | 'review' | 'block'; label: string; color: string }> = [
  { value: 'auto', label: 'Auto-Prepare', color: 'bg-[var(--accent-green)] text-white' },
  { value: 'review', label: 'Review first', color: 'bg-[var(--accent-amber)] text-white' },
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
    label: 'Customer Follow-up',
    description: 'Waypoint prepares a request for missing traveler details.',
    icon: MessageCircle,
  },
  {
    key: 'PROCEED_INTERNAL_DRAFT',
    label: 'Internal Drafts',
    description: 'Prepare drafts for your team to review.',
    icon: FileText,
  },
  {
    key: 'PROCEED_TRAVELER_SAFE',
    label: 'Customer-Ready Messages',
    description: 'Prepare messages that may be sent to the traveler.',
    icon: Zap,
  },
  {
    key: 'BRANCH_OPTIONS',
    label: 'Trip Options',
    description: 'Prepare multiple trip options for comparison.',
    icon: GitBranch,
  },
  {
    key: 'STOP_NEEDS_REVIEW',
    label: 'Critical Issues',
    description: 'Serious risk, missing approval, or policy issue found.',
    icon: Ban,
    locked: true,
  },
] as const;

const REPROCESS_STAGES: Array<{ key: string; label: string; description: string }> = [
  { key: "discovery", label: "Discovery", description: "Re-evaluate intake facts while requirements are still moving." },
  { key: "shortlist", label: "Shortlist", description: "Re-score options when user constraints or risk profile changes." },
  { key: "proposal", label: "Proposal", description: "Refresh pricing and suitability before customer-facing proposals." },
  { key: "booking", label: "Booking", description: "Re-check execution risks before final confirmations." },
];

export function AutonomyTab({ draft, onChange }: AutonomyTabProps) {
  const autonomy = draft.autonomy;
  const flagWarningsId = useId();
  const flagLearnId = useId();
  const flagAutoReprocessId = useId();
  const flagReassessId = useId();
  const reprocessBaseId = useId();

  const setGate = (state: string, action: 'auto' | 'review' | 'block') => {
    if (state === 'STOP_NEEDS_REVIEW') return; // Safety invariant
    onChange((prev) => {
      prev.autonomy.approval_gates[state] = action;
      return prev;
    });
  };

  const toggleFlag = (key: 'auto_proceed_with_warnings' | 'learn_from_overrides' | 'auto_reprocess_on_edit' | 'allow_explicit_reassess') => {
    onChange((prev) => {
      prev.autonomy[key] = !prev.autonomy[key];
      return prev;
    });
  };

  const toggleReprocessStage = (stage: string) => {
    onChange((prev) => {
      const current = prev.autonomy.auto_reprocess_stages?.[stage] ?? true;
      prev.autonomy.auto_reprocess_stages = {
        ...(prev.autonomy.auto_reprocess_stages || {}),
        [stage]: !current,
      };
      return prev;
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-[var(--ui-text-xl)] font-semibold text-[var(--text-primary)]">Approval Rules</h2>
        <p className="text-[var(--ui-text-xs)] text-[var(--text-secondary)] mt-1">
          Choose when Waypoint can prepare work automatically and when your team must review it first.
        </p>
      </div>

      {/* Workflow Approvals Table */}
      <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
        <div className="bg-[var(--bg-elevated)] px-4 py-2.5 border-b border-[var(--border-default)]">
          <h3 className="text-[var(--ui-text-xs)] font-semibold text-[var(--text-secondary)] uppercase tracking-wide flex items-center gap-1.5">
            <Shield className="size-3.5" />
            Workflow Approvals
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
                    className={`size-8 rounded-lg flex items-center justify-center shrink-0 ${
                      item.locked
                        ? 'bg-[var(--accent-red)/0.2] text-[var(--accent-red)]'
                        : 'bg-[var(--bg-count-badge)] text-[var(--text-secondary)]'
                    }`}
                  >
                    {item.locked ? <Lock className="size-4" /> : <Icon className="size-4" />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]">{item.label}</p>
                    <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">{item.description}</p>
                  </div>
                </div>

                {item.locked ? (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--accent-red)/0.2] text-[var(--accent-red)] text-[var(--ui-text-xs)] font-medium border border-[var(--accent-red)/0.3]">
                    <Lock className="size-3" />
                    Always requires review
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
                              : 'bg-[var(--bg-count-badge)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
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
          Safety Overrides
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] p-3 space-y-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-[var(--accent-red)]" />
              <span className="text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]">Emergency Handling</span>
            </div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Customer-ready messages always require approval during emergencies.
            </p>
            <div className="text-[var(--ui-text-sm)] text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 px-2 py-1 rounded inline-block">
              Active: Customer messages require approval during emergencies
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] p-3 space-y-2">
            <div className="flex items-center gap-2">
              <BookOpen className="size-4 text-[var(--accent-amber)]" />
              <span className="text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)]">Audit Handling</span>
            </div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Internal drafts always require team review during audits.
            </p>
            <div className="text-[var(--ui-text-sm)] text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 px-2 py-1 rounded inline-block">
              Active: Internal drafts require review during audits
            </div>
          </div>
        </div>
        <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
          These safety rules are always enforced.
        </p>
      </div>

      {/* Flags */}
      <div className="rounded-lg border border-[var(--border-default)] p-4 space-y-3">
        <h3 className="text-[var(--ui-text-xs)] font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
          Advanced Flags
        </h3>

        <label htmlFor={flagWarningsId} className="flex items-start gap-3 cursor-pointer group">
          <input
            id={flagWarningsId}
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
              className={`absolute top-0.5 size-4 bg-white rounded-full transition-transform ${
                autonomy.auto_proceed_with_warnings ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-primary)]">Allow low-risk warnings</p>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Waypoint may continue only when warnings are informational, not blocking.
            </p>
          </div>
        </label>

        <label htmlFor={flagLearnId} className="flex items-start gap-3 cursor-pointer group">
          <input
            id={flagLearnId}
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
              className={`absolute top-0.5 size-4 bg-white rounded-full transition-transform ${
                autonomy.learn_from_overrides ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-primary)]">Learn from team corrections</p>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Use approved team corrections to improve future recommendations.
              Only reviewed corrections are used. Customer-facing messages are not sent automatically because of this setting.
            </p>
          </div>
        </label>

        <label htmlFor={flagAutoReprocessId} className="flex items-start gap-3 cursor-pointer group">
          <input
            id={flagAutoReprocessId}
            type="checkbox"
            checked={autonomy.auto_reprocess_on_edit}
            onChange={() => toggleFlag('auto_reprocess_on_edit')}
            className="sr-only"
          />
          <div
            className={`w-9 h-5 rounded-full transition-colors relative shrink-0 mt-0.5 ${
              autonomy.auto_reprocess_on_edit ? 'bg-[var(--accent-blue)]' : 'bg-[var(--border-default)]'
            }`}
          >
            <div
              className={`absolute top-0.5 size-4 bg-white rounded-full transition-transform ${
                autonomy.auto_reprocess_on_edit ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-primary)]">Auto re-run after meaningful edits</p>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Automatically re-run decisioning when an operator updates critical trip inputs.
            </p>
          </div>
        </label>

        <label htmlFor={flagReassessId} className="flex items-start gap-3 cursor-pointer group">
          <input
            id={flagReassessId}
            type="checkbox"
            checked={autonomy.allow_explicit_reassess}
            onChange={() => toggleFlag('allow_explicit_reassess')}
            className="sr-only"
          />
          <div
            className={`w-9 h-5 rounded-full transition-colors relative shrink-0 mt-0.5 ${
              autonomy.allow_explicit_reassess ? 'bg-[var(--accent-blue)]' : 'bg-[var(--border-default)]'
            }`}
          >
            <div
              className={`absolute top-0.5 size-4 bg-white rounded-full transition-transform ${
                autonomy.allow_explicit_reassess ? 'left-[18px]' : 'left-0.5'
              }`}
            />
          </div>
          <div>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-primary)]">Allow manual reassessment</p>
            <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">
              Lets operators explicitly trigger a full re-evaluation when context changes.
            </p>
          </div>
        </label>
      </div>

      <div className="rounded-lg border border-[var(--border-default)] p-4 space-y-3">
        <h3 className="text-[var(--ui-text-xs)] font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
          Auto Reprocess By Stage
        </h3>
        <div className="space-y-2">
          {REPROCESS_STAGES.map((stage) => {
            const enabled = autonomy.auto_reprocess_stages?.[stage.key] ?? true;
            return (
              <label key={stage.key} htmlFor={reprocessBaseId + '-' + stage.key} className="flex items-start gap-3 cursor-pointer group rounded-md border border-[var(--border-default)] p-3">
                <input
                  id={reprocessBaseId + '-' + stage.key}
                  type="checkbox"
                  checked={enabled}
                  onChange={() => toggleReprocessStage(stage.key)}
                  className="mt-1"
                />
                <div>
                  <p className="text-[var(--ui-text-sm)] text-[var(--text-primary)]">{stage.label}</p>
                  <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)]">{stage.description}</p>
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Approval rules note */}
      <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-elevated)] p-4">
        <p className="text-[var(--ui-text-sm)] text-[var(--text-secondary)] leading-relaxed">
          <span className="text-[var(--accent-blue)] font-medium">How it works:</span>{' '}
          Approval rules decide when Waypoint can prepare work automatically and when your team must review it first. Customer-ready messages, emergencies, audits, and critical issues should stay under human approval.
        </p>
      </div>
    </div>
  );
}
