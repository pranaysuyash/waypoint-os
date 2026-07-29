'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { CheckCircle2, ArrowRight, Users, Send, Inbox } from 'lucide-react';

/**
 * EmptyStateOnboarding - first-run guide shown on /overview when the workspace
 * has no trips AND no inbox leads. Three sequential steps lead the owner from
 * a fresh workspace to the first trip in planning.
 *
 * Persists completed steps in localStorage so progress survives page reloads.
 *
 * Shown when: planningTripsTotal === 0 && leadInboxTotal === 0 && !isLoading
 * Hidden when: any trip or lead exists (planning has started - not first-run).
 */

const CHECKLIST_KEY = 'waypoint:onboarding-checklist:v2';

// ── Step definitions ─────────────────────────────────────────────────────

interface OnboardingStep {
  key: string;
  icon: React.FC<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  description: string;
  href: string;
}

const STEPS: OnboardingStep[] = [
  {
    key: 'invite_team',
    icon: Users,
    label: 'Invite your team',
    description: 'Share an invitation link so agents can join your workspace.',
    href: '/settings?tab=people',
  },
  {
    key: 'first_inquiry',
    icon: Send,
    label: 'Add your first inquiry',
    description: "Paste a customer note and Waypoint organizes the details and flags what's missing.",
    href: '/workbench?draft=new&tab=intake',
  },
  {
    key: 'review_inbox',
    icon: Inbox,
    label: 'Review in Lead Inbox',
    description: 'Once processed, the trip appears in your inbox ready for planning.',
    href: '/inbox',
  },
];

// ── localStorage helpers ─────────────────────────────────────────────────

function loadCompletedSteps(): Set<string> {
  if (typeof window === 'undefined') return new Set();
  try {
    const raw = localStorage.getItem(CHECKLIST_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return new Set(parsed);
    return new Set();
  } catch {
    return new Set();
  }
}

function saveCompletedSteps(steps: Set<string>): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(CHECKLIST_KEY, JSON.stringify(Array.from(steps)));
  } catch {
    // localStorage unavailable (private browsing, quota exceeded)
  }
}

// ── Component ────────────────────────────────────────────────────────────

export function EmptyStateOnboarding() {
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(loadCompletedSteps);

  const markCompleted = useCallback((key: string) => {
    setCompletedSteps((prev) => {
      if (prev.has(key)) return prev;
      const next = new Set(prev);
      next.add(key);
      // Save synchronously so completion persists even if navigation happens immediately
      saveCompletedSteps(next);
      return next;
    });
  }, []);

  const allCompleted = STEPS.every((step) => completedSteps.has(step.key));

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
        {allCompleted ? 'All set — you\'re ready to go' : 'Welcome to Waypoint'}
      </h2>
      <p
        className="text-[13px] text-center max-w-[340px] leading-relaxed mb-8"
        style={{ color: 'var(--text-secondary)' }}
      >
        {allCompleted
          ? 'Every onboarding step is complete. Start processing inquiries and building trip plans.'
          : 'Your workspace is ready. Here\'s how to get started.'}
      </p>

      <ol className="w-full max-w-[420px] space-y-2">
        {STEPS.map((step) => {
          const Icon = step.icon;
          const isCompleted = completedSteps.has(step.key);

          return (
            <li key={step.key}>
              <Link
                href={step.href}
                onClick={() => markCompleted(step.key)}
                className="flex items-center gap-4 p-4 rounded-xl border transition-colors group"
                style={{
                  background: 'var(--bg-surface)',
                  borderColor: isCompleted ? 'var(--accent-green)' : 'var(--border-default)',
                }}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLAnchorElement;
                  Object.assign(el.style, { borderColor: 'var(--border-hover)', background: 'var(--bg-elevated)' });
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLAnchorElement;
                  Object.assign(el.style, { borderColor: isCompleted ? 'var(--accent-green)' : 'var(--border-default)', background: 'var(--bg-surface)' });
                }}
                aria-current={isCompleted ? 'step' : undefined}
              >
                {/* Step number badge */}
                <div
                  className="size-7 rounded-full flex items-center justify-center shrink-0 text-[12px] font-bold"
                  style={{
                    background: isCompleted ? 'rgba(63,185,80,0.15)' : 'var(--bg-elevated)',
                    border: `1px solid ${isCompleted ? 'var(--accent-green)' : 'var(--border-default)'}`,
                    color: isCompleted ? 'var(--accent-green)' : 'var(--text-tertiary)',
                  }}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="size-4" />
                  ) : (
                    STEPS.findIndex((s) => s.key === step.key) + 1
                  )}
                </div>

                {/* Icon */}
                <div
                  className="size-8 rounded-lg flex items-center justify-center shrink-0"
                  style={{
                    background: 'rgba(88,166,255,0.10)',
                    border: '1px solid rgba(88,166,255,0.20)',
                  }}
                >
                  <Icon className="size-4" style={{ color: 'var(--accent-blue)' }} />
                </div>

                {/* Text */}
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>
                    {step.label}
                  </div>
                  <div className="text-[12px] mt-0.5 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                    {step.description}
                  </div>
                </div>

                <ArrowRight
                  className="size-4 shrink-0 opacity-[0.3] group-hover:opacity-100 transition-opacity"
                  style={{ color: 'var(--text-muted)' }}
                />
              </Link>
            </li>
          );
        })}
      </ol>

      <p className="mt-6 text-[12px] text-center" style={{ color: 'var(--text-tertiary)' }}>
        {allCompleted
          ? 'This guide stays until your first trip enters planning.'
          : 'This guide disappears once your first trip is in planning.'}
      </p>
    </div>
  );
}
