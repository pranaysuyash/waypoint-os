'use client';

import type { BookingDocument, PaymentTracking } from '@/lib/api-client';
import type { ReadinessAssessment } from '@/types/spine';

export interface NextAction {
  priority: 'urgent' | 'attention' | 'info';
  message: string;
}

function daysUntilPayment(dateStr: string): number {
  const due = new Date(dateStr + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - today.getTime()) / 86400000);
}

export function computeNextAction(
  pendingData: unknown,
  documents: BookingDocument[],
  readiness: ReadinessAssessment | null | undefined,
  paymentTracking?: PaymentTracking | null,
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

  const terminalPaymentStatuses = ['paid', 'waived', 'refunded'];
  if (
    paymentTracking?.final_payment_due &&
    !terminalPaymentStatuses.includes(paymentTracking?.payment_status ?? '')
  ) {
    const days = daysUntilPayment(paymentTracking.final_payment_due);
    if (days < 0) {
      const n = Math.abs(days);
      return {
        priority: 'urgent',
        message: `Final payment is overdue by ${n} day${n !== 1 ? 's' : ''}.`,
      };
    }
    if (days <= 3) {
      return {
        priority: 'attention',
        message: `Final payment due in ${days} day${days !== 1 ? 's' : ''}.`,
      };
    }
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
  paymentTracking?: PaymentTracking | null;
}

const PRIORITY_STYLES: Record<NonNullable<NextAction['priority']>, string> = {
  urgent: 'border-amber-700/60 bg-amber-950/20 text-amber-300',
  attention: 'border-blue-700/60 bg-blue-950/20 text-blue-200',
  info: 'border-[#30363d] bg-[#0d1117] text-[#8b949e]',
};

export default function NextActionBanner({ pendingData, documents, readiness, paymentTracking }: NextActionBannerProps) {
  const action = computeNextAction(pendingData, documents, readiness, paymentTracking);

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
