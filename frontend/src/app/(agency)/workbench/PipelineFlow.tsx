'use client';

import { ProgressSteps } from '@/components/ui/progress-steps';

export const PIPELINE_STAGES = [
  { id: 'intake', label: 'New Inquiry', shortLabel: 'Inquiry' },
  { id: 'packet', label: 'Trip Details', shortLabel: 'Details' },
  { id: 'decision', label: 'Ready to Quote?', shortLabel: 'Quote?' },
  { id: 'strategy', label: 'Build Options', shortLabel: 'Options' },
  { id: 'safety', label: 'Final Review', shortLabel: 'Review' },
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
  const isValid = PIPELINE_STAGES.some((s) => s.id === currentStage);
  if (!isValid) {
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
      <ProgressSteps
        steps={PIPELINE_STAGES}
        currentId={currentStage}
        size='md'
        navAriaLabel='Pipeline progress'
        getAriaLabel={(step, status) => `${step.label}: ${status}`}
      />
    </div>
  );
}
