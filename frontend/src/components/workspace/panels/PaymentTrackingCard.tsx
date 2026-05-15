'use client';

import type { PaymentTracking } from '@/lib/api-client';

function formatLabel(value: string): string {
  return value.replaceAll('_', ' ');
}

function formatMoney(amount?: number | null, currency = 'INR'): string {
  if (amount == null || Number.isNaN(amount)) return '-';
  return `${currency} ${amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

interface PaymentTrackingCardProps {
  paymentTracking: PaymentTracking;
}

export default function PaymentTrackingCard({ paymentTracking }: PaymentTrackingCardProps) {
  const currency = paymentTracking.currency || 'INR';

  return (
    <div
      data-testid="ops-payment-tracking"
      className="mt-3 border border-[#30363d] rounded p-3 text-xs"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-[#e6edf3]">Payment & refund tracking</span>
        <span className="rounded bg-blue-950/40 px-2 py-0.5 text-blue-300">Status-only tracking</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-[#8b949e] sm:grid-cols-4">
        <div>
          <div>Agreed</div>
          <div className="text-[#e6edf3]">
            {formatMoney(paymentTracking.agreed_amount, currency)}
          </div>
        </div>
        <div>
          <div>Paid</div>
          <div className="text-[#e6edf3]">
            {formatMoney(paymentTracking.amount_paid, currency)}
          </div>
        </div>
        <div>
          <div>Balance due</div>
          <div className="text-[#e6edf3]">
            {formatMoney(paymentTracking.balance_due, currency)}
          </div>
        </div>
        <div>
          <div>Status</div>
          <div className="text-[#e6edf3]">{formatLabel(paymentTracking.payment_status || 'unknown')}</div>
        </div>
      </div>
      <div className="mt-2 text-[#8b949e]">
        Refund: <span className="text-[#e6edf3]">{formatLabel(paymentTracking.refund_status || 'not_applicable')}</span>
      </div>
    </div>
  );
}
