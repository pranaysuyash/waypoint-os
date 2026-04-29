'use client';

import { cn } from '@/lib/utils';
import { CheckCircle2 } from 'lucide-react';

export const PIPELINE_STAGES = [
  { id: 'intake', label: '1', fullLabel: 'New Inquiry', shortLabel: 'Inquiry' },
  { id: 'packet', label: '2', fullLabel: 'Trip Details', shortLabel: 'Details' },
  { id: 'decision', label: '3', fullLabel: 'Ready to Quote?', shortLabel: 'Quote?' },
  { id: 'strategy', label: '4', fullLabel: 'Build Options', shortLabel: 'Options' },
  { id: 'safety', label: '5', fullLabel: 'Final Review', shortLabel: 'Review' },
] as const;

export type PipelineStageId = (typeof PIPELINE_STAGES)[number]['id'];

export function toPipelineStageId(value: string): PipelineStageId | null {
  const stage = PIPELINE_STAGES.find((s) => s.id === value);
  return stage?.id ?? null;
}

interface PipelineFlowProps {
  currentStage: PipelineStageId;
}

export function PipelineFlow({ currentStage }: PipelineFlowProps) {
  const currentIndex = PIPELINE_STAGES.findIndex((s) => s.id === currentStage);

  if (currentIndex === -1) {
    console.error(`PipelineFlow: Unknown stage "${currentStage}"`);
    return null;
  }

  return (
    <div
      className='px-6 py-3'
      style={{
        borderBottom: '1px solid var(--border-default)',
        background: 'var(--bg-surface)',
      }}
    >
      <nav aria-label='Pipeline progress'>
        <ol className='flex items-center max-w-5xl mx-auto list-none p-0 m-0'>
          {PIPELINE_STAGES.map((stage, index) => {
            const isActive = index === currentIndex;
            const isCompleted = index < currentIndex;
            const isPending = index > currentIndex;

            const statusLabel = isCompleted
              ? 'completed'
              : isActive
                ? 'current'
                : 'pending';

            return (
              <li
                key={stage.id}
                className='flex items-center flex-1 min-w-0'
                aria-current={isActive ? 'step' : undefined}
                aria-label={`${stage.fullLabel}: ${statusLabel}`}
              >
                <div className='relative flex flex-col items-center min-w-0'>
                  {/* Stage indicator */}
                  <div
                    className={cn(
                      'w-8 h-8 rounded-sm flex items-center justify-center font-mono text-xs font-semibold transition-colors shrink-0 border',
                    )}
                    style={
                      isCompleted
                        ? {
                            background: 'rgba(63, 185, 80, 0.08)',
                            borderColor: 'var(--accent-green)',
                            color: 'var(--accent-green)',
                          }
                        : isActive
                          ? {
                              background: 'var(--accent-blue)',
                              borderColor: 'var(--accent-blue)',
                              color: 'var(--text-on-accent)',
                            }
                          : {
                              background: 'var(--bg-elevated)',
                              borderColor: 'var(--border-default)',
                              color: 'var(--text-muted)',
                            }
                    }
                  >
                    {isCompleted ? (
                      <CheckCircle2 className='w-4 h-4' aria-hidden='true' />
                    ) : (
                      stage.label
                    )}
                  </div>

                  {/* Label */}
                  <p
                    className={cn(
                      'mt-1 text-xs font-medium text-center truncate w-full px-1',
                    )}
                    style={{ color: isActive ? 'var(--text-primary)' : 'var(--text-muted)' }}
                  >
                    <span className='hidden lg:inline'>{stage.fullLabel}</span>
                    <span className='lg:hidden'>{stage.shortLabel}</span>
                  </p>

                  {/* Active dot */}
                  {isActive && (
                    <div
                      className='absolute -bottom-1 w-1.5 h-1.5 rounded-full animate-pulse-dot'
                      style={{ background: 'var(--accent-blue)' }}
                      aria-hidden='true'
                    />
                  )}
                </div>

                {/* Connector line */}
                {index < PIPELINE_STAGES.length - 1 && (
                  <div
                    className='flex-1 min-w-[16px] max-w-[60px] h-px mx-2 shrink'
                    style={{
                      background: isCompleted ? 'var(--accent-green)' : 'var(--border-default)',
                    }}
                    aria-hidden='true'
                  />
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
}
