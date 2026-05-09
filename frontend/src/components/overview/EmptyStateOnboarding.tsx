'use client';

/**
 * EmptyStateOnboarding - first-run guide shown on /overview when the workspace
 * has no trips AND no inbox leads. Three sequential steps lead the owner from
 * a fresh workspace to the first trip in planning.
 *
 * Shown when: planningTripsTotal === 0 && leadInboxTotal === 0 && !isLoading
 * Hidden when: any trip or lead exists (planning has started - not first-run).
 *
 * Step 1 links to /settings?tab=people (WorkspaceCodePanel from Task 1) so the
 * owner can immediately copy and share an invite link.
 */

import Link from 'next/link';
import { ArrowRight, Users, Send, Inbox, CheckCircle2 } from 'lucide-react';

interface OnboardingStep {
  icon: React.FC<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  description: string;
  href: string;
}

const STEPS: OnboardingStep[] = [
  {
    icon: Users,
    label: 'Invite your team',
    description: 'Share an invitation link so agents can join your workspace.',
    href: '/settings?tab=people',
  },
  {
    icon: Send,
    label: 'Add your first inquiry',
    description: "Paste a customer note and Waypoint organizes the details and flags what's missing.",
    href: '/workbench?draft=new&tab=intake',
  },
  {
    icon: Inbox,
    label: 'Review in Lead Inbox',
    description: 'Once processed, the trip appears in your inbox ready for planning.',
    href: '/inbox',
  },
];

export function EmptyStateOnboarding() {
  return (
    <div className="flex flex-col items-center py-10 px-4">
      <div
        className="size-12 rounded-xl flex items-center justify-center mb-5"
        style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}
      >
        <CheckCircle2 className="size-6" style={{ color: 'var(--accent-blue)' }} />
      </div>

      <h2
        className="text-[15px] font-semibold mb-1 text-center"
        style={{ color: 'var(--text-primary)' }}
      >
        Welcome to Waypoint
      </h2>
      <p
        className="text-[13px] text-center max-w-[340px] leading-relaxed mb-8"
        style={{ color: 'var(--text-secondary)' }}
      >
        Your workspace is ready. Here&apos;s how to get started.
      </p>

      <ol className="w-full max-w-[420px] space-y-2">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          return (
            <li key={step.label}>
              <Link
                href={step.href}
                className="flex items-center gap-4 p-4 rounded-xl border transition-colors group"
                style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLAnchorElement;
                  el.style.borderColor = 'var(--border-hover)';
                  el.style.background = 'var(--bg-elevated)';
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLAnchorElement;
                  el.style.borderColor = 'var(--border-default)';
                  el.style.background = 'var(--bg-surface)';
                }}
              >
                <div
                  className="size-7 rounded-full flex items-center justify-center shrink-0 text-[12px] font-bold"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-tertiary)',
                  }}
                >
                  {idx + 1}
                </div>

                <div
                  className="size-8 rounded-lg flex items-center justify-center shrink-0"
                  style={{
                    background: 'rgba(88,166,255,0.10)',
                    border: '1px solid rgba(88,166,255,0.20)',
                  }}
                >
                  <Icon className="size-4" style={{ color: 'var(--accent-blue)' }} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>
                    {step.label}
                  </div>
                  <div className="text-[12px] mt-0.5 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                    {step.description}
                  </div>
                </div>

                <ArrowRight
                  className="size-4 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ color: 'var(--text-muted)' }}
                />
              </Link>
            </li>
          );
        })}
      </ol>

      <p className="mt-6 text-[12px] text-center" style={{ color: 'var(--text-tertiary)' }}>
        This guide disappears once your first trip is in planning.
      </p>
    </div>
  );
}
