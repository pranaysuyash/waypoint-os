'use client';

import type { BookingDocument } from '@/lib/api-client';
import type { ReadinessAssessment } from '@/types/spine';

export interface NextAction {
  priority: 'urgent' | 'attention' | 'info';
  message: string;
}

export function computeNextAction(
  pendingData: unknown,
  documents: BookingDocument[],
  readiness: ReadinessAssessment | null | undefined,
): NextAction | null {
  if (pendingData) {
    return {
      priority: 'urgent',
      message: 'Customer has submitted booking data. Review and accept or reject.',
    };
  }

  const pendingReview = documents.filter((d) => d.status === 'pending_review');
  if (pendingReview.length > 0) {
    const count = pendingReview.length;
    return {
      priority: 'attention',
      message: `${count} document${count > 1 ? 's' : ''} awaiting review.`,
    };
  }

  const missing = readiness?.missing_for_next ?? [];
  if (missing.length > 0) {
    return {
      priority: 'info',
      message: `Missing fields blocking next stage: ${missing.join(', ')}.`,
    };
  }

  return null;
}

interface NextActionBannerProps {
  pendingData: unknown;
  documents: BookingDocument[];
  readiness: ReadinessAssessment | null | undefined;
}

const PRIORITY_STYLES: Record<NonNullable<NextAction['priority']>, string> = {
  urgent: 'border-amber-700/60 bg-amber-950/20 text-amber-300',
  attention: 'border-blue-700/60 bg-blue-950/20 text-blue-200',
  info: 'border-[#30363d] bg-[#0d1117] text-[#8b949e]',
};

export default function NextActionBanner({ pendingData, documents, readiness }: NextActionBannerProps) {
  const action = computeNextAction(pendingData, documents, readiness);

  if (!action) {
    return (
      <div
        data-testid="ops-next-action-banner"
        data-priority="none"
        className="rounded-lg border border-[#30363d] bg-[#0d1117] px-4 py-3 text-xs text-[#8b949e]"
      >
        No urgent Ops action detected from available data.
      </div>
    );
  }

  return (
    <div
      data-testid="ops-next-action-banner"
      data-priority={action.priority}
      className={`rounded-lg border px-4 py-3 text-xs ${PRIORITY_STYLES[action.priority]}`}
    >
      {action.message}
    </div>
  );
}
