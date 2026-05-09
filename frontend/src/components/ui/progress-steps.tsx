'use client';

import { cn } from '@/lib/utils';
import { CheckCircle2 } from 'lucide-react';

export type StepStatus = 'completed' | 'current' | 'pending';

export interface Step {
  id: string;
  label: string;
  shortLabel?: string;
}

export interface ProgressStepsProps {
  steps: readonly Step[];
  currentId: string;
  orientation?: 'horizontal' | 'vertical';
  size?: 'sm' | 'md';
  className?: string;
  navAriaLabel?: string;
  getAriaLabel?: (step: Step, status: StepStatus) => string;
}

export function ProgressSteps({
  steps,
  currentId,
  orientation = 'horizontal',
  size = 'md',
  className,
  navAriaLabel = 'Progress',
  getAriaLabel,
}: ProgressStepsProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentId);

  return (
    <nav
      aria-label={navAriaLabel}
      className={cn(
        orientation === 'horizontal' ? 'flex items-center' : 'flex flex-col',
        className
      )}
    >
      {steps.map((step, index) => {
        const status: StepStatus =
          index < currentIndex
            ? 'completed'
            : index === currentIndex
            ? 'current'
            : 'pending';

        const ariaLabel = getAriaLabel
          ? getAriaLabel(step, status)
          : `${step.label}: ${status}`;

        return (
          <div
            key={step.id}
            aria-current={status === 'current' ? 'step' : undefined}
            aria-label={ariaLabel}
            className={cn(
              'flex items-center',
              orientation === 'horizontal'
                ? 'flex-col gap-1.5'
                : 'flex-row gap-3'
            )}
          >
            <div className="flex items-center">
              <div
                className={cn(
                  'flex items-center justify-center rounded-full transition-colors',
                  size === 'md' ? 'size-8 text-sm' : 'size-6 text-xs',
                  status === 'completed' && 'text-[var(--accent-green)] bg-[rgba(var(--accent-green-rgb),0.12)]',
                  status === 'current' && 'text-white bg-[var(--accent-blue)]',
                  status === 'pending' && 'text-[var(--text-muted)] bg-[var(--bg-elevated)]'
                )}
              >
                {status === 'completed' ? (
                  <CheckCircle2 className={size === 'md' ? 'size-4' : 'size-3'} />
                ) : (
                  <span className="font-semibold">{index + 1}</span>
                )}
              </div>

              {index < steps.length - 1 && (
                <div
                  aria-hidden="true"
                  className={cn(
                    'flex-1 transition-colors',
                    orientation === 'horizontal'
                      ? 'w-8 h-0.5'
                      : 'w-0.5 h-6 ml-auto',
                    status === 'completed'
                      ? 'bg-[var(--accent-green)]'
                      : 'bg-[var(--border-default)]'
                  )}
                />
              )}
            </div>

            {orientation === 'horizontal' && (
              <div className="text-center">
                <p
                  className={cn(
                    'font-medium leading-tight',
                    size === 'md' ? 'text-ui-xs' : 'text-ui-2xs',
                    status === 'current' && 'text-[var(--text-primary)]',
                    status !== 'current' && 'text-[var(--text-muted)]'
                  )}
                >
                  <span className="hidden lg:inline">{step.label}</span>
                  {step.shortLabel && (
                    <span className="lg:hidden">{step.shortLabel}</span>
                  )}
                </p>
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}
