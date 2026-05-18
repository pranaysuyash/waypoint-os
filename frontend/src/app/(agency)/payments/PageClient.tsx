'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, RefreshCw } from 'lucide-react';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { InlineError } from '@/components/error-boundary';
import { usePaymentsQueue } from '@/hooks/usePayments';
import type {
  PaymentQueueParams,
  PaymentQueueItem,
  QueueStatus,
  PaymentStatus,
  RefundStatus,
} from '@/lib/api-client';

const PAGE_SIZE = 25;

const QUEUE_FILTER_OPTIONS: Array<{ value: QueueStatus; label: string }> = [
  { value: 'overdue', label: 'Overdue' },
  { value: 'due_soon', label: 'Due soon' },
  { value: 'due_later', label: 'Due later' },
  { value: 'not_configured', label: 'Not configured' },
  { value: 'refund_in_progress', label: 'Refund in progress' },
  { value: 'paid_complete', label: 'Paid complete' },
  { value: 'unknown', label: 'Unknown' },
];

const PAYMENT_FILTER_OPTIONS: Array<{ value: PaymentStatus; label: string }> = [
  { value: 'not_started', label: 'Not started' },
  { value: 'deposit_paid', label: 'Deposit paid' },
  { value: 'partially_paid', label: 'Partially paid' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'waived', label: 'Waived' },
  { value: 'refunded', label: 'Refunded' },
  { value: 'unknown', label: 'Unknown' },
];

const REFUND_FILTER_OPTIONS: Array<{ value: RefundStatus; label: string }> = [
  { value: 'not_applicable', label: 'Not applicable' },
  { value: 'not_requested', label: 'Not requested' },
  { value: 'pending_review', label: 'Pending review' },
  { value: 'approved', label: 'Approved' },
  { value: 'processing', label: 'Processing' },
  { value: 'paid', label: 'Paid' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'cancelled', label: 'Cancelled' },
];

const DUE_BUCKET_OPTIONS: Array<{
  value: NonNullable<PaymentQueueParams['due_bucket']>;
  label: string;
}> = [
  { value: 'overdue', label: 'Past due' },
  { value: 'due_0_3', label: 'Due in 0–3 days' },
  { value: 'due_4_7', label: 'Due in 4–7 days' },
  { value: 'due_8_14', label: 'Due in 8–14 days' },
  { value: 'none', label: 'No due date' },
];

function formatMoney(value: number | null | undefined, currency: string): string {
  if (value == null) return '—';
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value);
  } catch {
    return `${currency} ${value.toFixed(2)}`;
  }
}

function renderTripLabel(item: PaymentQueueItem): string {
  if (item.trip_name?.trim()) return item.trip_name;
  if (item.destination?.trim()) return `${item.destination} trip`;
  return item.trip_id;
}

function toTitleCase(value: string): string {
  return value
    .split('_')
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

export default function PaymentsPage() {
  const [queueStatus, setQueueStatus] = useState<QueueStatus | ''>('');
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | ''>('');
  const [refundStatus, setRefundStatus] = useState<RefundStatus | ''>('');
  const [dueBucket, setDueBucket] = useState<PaymentQueueParams['due_bucket'] | ''>('');
  const [offset, setOffset] = useState(0);

  const params = useMemo<PaymentQueueParams>(
    () => ({
      limit: PAGE_SIZE,
      offset,
      queue_status: queueStatus || undefined,
      payment_status: paymentStatus || undefined,
      refund_status: refundStatus || undefined,
      due_bucket: dueBucket || undefined,
    }),
    [dueBucket, offset, paymentStatus, queueStatus, refundStatus],
  );

  const { data, isLoading, error, refetch } = usePaymentsQueue(params);

  const summary = data?.summary;
  const pagination = data?.pagination;
  const items = data?.items ?? [];

  const hasActiveFilters = Boolean(queueStatus || paymentStatus || refundStatus || dueBucket);
  const canPrev = (pagination?.offset ?? 0) > 0;
  const canNext = Boolean(pagination?.has_more);

  const resetFilters = () => {
    setQueueStatus('');
    setPaymentStatus('');
    setRefundStatus('');
    setDueBucket('');
    setOffset(0);
  };

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      <BackToOverviewLink />

      <header className='flex items-center justify-between gap-3 flex-wrap pt-1'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Payments</h1>
          <p className='text-ui-sm text-[var(--text-muted)] mt-0.5'>
            Track payment status and due risk across active trips.
          </p>
        </div>

        <button
          type='button'
          onClick={() => refetch()}
          className='inline-flex items-center gap-2 px-3 py-2 rounded-lg text-ui-sm border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[#e6edf3] hover:bg-[#161b22] transition-colors'
        >
          <RefreshCw className={`size-4 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </header>

      <div className='grid grid-cols-2 lg:grid-cols-5 gap-3'>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <p className='text-ui-xs text-[var(--text-tertiary)]'>Total in queue</p>
          <p className='text-ui-xl font-semibold text-[#e6edf3] mt-1'>{summary?.total ?? 0}</p>
        </div>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <p className='text-ui-xs text-[var(--text-tertiary)]'>Overdue</p>
          <p className='text-ui-xl font-semibold text-[#f85149] mt-1'>{summary?.overdue_count ?? 0}</p>
        </div>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <p className='text-ui-xs text-[var(--text-tertiary)]'>Due soon</p>
          <p className='text-ui-xl font-semibold text-[#d29922] mt-1'>{summary?.due_soon_count ?? 0}</p>
        </div>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <p className='text-ui-xs text-[var(--text-tertiary)]'>Not configured</p>
          <p className='text-ui-xl font-semibold text-[#58a6ff] mt-1'>{summary?.not_configured_count ?? 0}</p>
        </div>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <p className='text-ui-xs text-[var(--text-tertiary)]'>Refund in progress</p>
          <p className='text-ui-xl font-semibold text-[#a371f7] mt-1'>{summary?.refund_in_progress_count ?? 0}</p>
        </div>
      </div>

      <section className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 space-y-3'>
        <div className='flex items-center justify-between gap-3 flex-wrap'>
          <h2 className='text-ui-sm font-semibold text-[#e6edf3]'>Payment status filters</h2>
          {hasActiveFilters && (
            <button
              type='button'
              onClick={resetFilters}
              className='text-ui-xs text-[var(--accent-blue)] hover:text-[#79b8ff]'
            >
              Clear filters
            </button>
          )}
        </div>
        <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3'>
          <label className='text-ui-xs text-[var(--text-tertiary)]'>
            Queue status
            <select
              className='mt-1 w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-2 py-2 text-ui-sm text-[#e6edf3]'
              value={queueStatus}
              onChange={(e) => {
                setQueueStatus(e.target.value as QueueStatus | '');
                setOffset(0);
              }}
            >
              <option value=''>All queue statuses</option>
              {QUEUE_FILTER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className='text-ui-xs text-[var(--text-tertiary)]'>
            Payment status
            <select
              className='mt-1 w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-2 py-2 text-ui-sm text-[#e6edf3]'
              value={paymentStatus}
              onChange={(e) => {
                setPaymentStatus(e.target.value as PaymentStatus | '');
                setOffset(0);
              }}
            >
              <option value=''>All payment statuses</option>
              {PAYMENT_FILTER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className='text-ui-xs text-[var(--text-tertiary)]'>
            Refund status
            <select
              className='mt-1 w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-2 py-2 text-ui-sm text-[#e6edf3]'
              value={refundStatus}
              onChange={(e) => {
                setRefundStatus(e.target.value as RefundStatus | '');
                setOffset(0);
              }}
            >
              <option value=''>All refund statuses</option>
              {REFUND_FILTER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className='text-ui-xs text-[var(--text-tertiary)]'>
            Due window
            <select
              className='mt-1 w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-2 py-2 text-ui-sm text-[#e6edf3]'
              value={dueBucket}
              onChange={(e) => {
                setDueBucket(e.target.value as PaymentQueueParams['due_bucket'] | '');
                setOffset(0);
              }}
            >
              <option value=''>All due windows</option>
              {DUE_BUCKET_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className='rounded-xl border border-[#1c2128] bg-[#0f1115] overflow-hidden'>
        <header className='px-4 py-3 border-b border-[#1c2128] flex items-center justify-between'>
          <h2 className='text-ui-sm font-semibold text-[#e6edf3]'>Payments queue</h2>
          <span className='text-ui-xs text-[var(--text-muted)]'>
            {isLoading ? 'Loading…' : `Showing ${pagination?.returned ?? items.length} of ${pagination?.total ?? items.length}`}
          </span>
        </header>

        {error && (
          <div className='p-4'>
            <InlineError message='Failed to load payments queue.' />
          </div>
        )}

        {!error && items.length === 0 && !isLoading && (
          <div className='p-10 text-center space-y-2'>
            <p className='text-ui-sm text-[#e6edf3] font-medium'>No trips match the current filters.</p>
            <p className='text-ui-xs text-[var(--text-muted)]'>
              Try clearing one or more filters to view more payment records.
            </p>
          </div>
        )}

        {!error && (
          <div className='overflow-x-auto'>
            <table className='min-w-full text-ui-sm'>
              <thead className='bg-[#0d1117]'>
                <tr className='text-left text-ui-xs text-[var(--text-tertiary)]'>
                  <th className='px-4 py-2 font-medium'>Trip</th>
                  <th className='px-4 py-2 font-medium'>Queue status</th>
                  <th className='px-4 py-2 font-medium'>Payment status</th>
                  <th className='px-4 py-2 font-medium'>Balance due</th>
                  <th className='px-4 py-2 font-medium'>Due date</th>
                  <th className='px-4 py-2 font-medium'>Refund status</th>
                  <th className='px-4 py-2 font-medium'>Action</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && items.length === 0
                  ? Array.from({ length: 5 }).map((_, index) => (
                      <tr key={`skeleton-${index}`} className='border-t border-[#1c2128]'>
                        <td className='px-4 py-3'>
                          <div className='h-4 w-40 rounded bg-[#161b22] animate-pulse' />
                        </td>
                        <td className='px-4 py-3'>
                          <div className='h-4 w-24 rounded bg-[#161b22] animate-pulse' />
                        </td>
                        <td className='px-4 py-3'>
                          <div className='h-4 w-24 rounded bg-[#161b22] animate-pulse' />
                        </td>
                        <td className='px-4 py-3'>
                          <div className='h-4 w-20 rounded bg-[#161b22] animate-pulse' />
                        </td>
                        <td className='px-4 py-3'>
                          <div className='h-4 w-20 rounded bg-[#161b22] animate-pulse' />
                        </td>
                        <td className='px-4 py-3'>
                          <div className='h-4 w-24 rounded bg-[#161b22] animate-pulse' />
                        </td>
                        <td className='px-4 py-3'>
                          <div className='h-4 w-16 rounded bg-[#161b22] animate-pulse' />
                        </td>
                      </tr>
                    ))
                  : items.map((item) => (
                      <tr key={item.trip_id} className='border-t border-[#1c2128]'>
                        <td className='px-4 py-3 text-[#e6edf3]'>
                          <div className='font-medium'>{renderTripLabel(item)}</div>
                          <div className='text-ui-xs text-[var(--text-muted)]'>{item.destination || 'Destination pending'}</div>
                        </td>
                        <td className='px-4 py-3 text-[var(--text-secondary)]'>{toTitleCase(item.queue_status)}</td>
                        <td className='px-4 py-3 text-[var(--text-secondary)]'>{toTitleCase(item.payment_status)}</td>
                        <td className='px-4 py-3 text-[var(--text-secondary)]'>{formatMoney(item.balance_due, item.currency)}</td>
                        <td className='px-4 py-3 text-[var(--text-secondary)]'>
                          {item.final_payment_due || '—'}
                          {item.queue_status === 'overdue' && (
                            <span className='inline-flex items-center gap-1 ml-2 text-[#f85149] text-ui-xs'>
                              <AlertTriangle className='size-3' /> overdue
                            </span>
                          )}
                        </td>
                        <td className='px-4 py-3 text-[var(--text-secondary)]'>{toTitleCase(item.refund_status)}</td>
                        <td className='px-4 py-3'>
                          <Link
                            href={`/trips/${item.trip_id}/ops`}
                            className='inline-flex items-center gap-1 text-[var(--accent-blue)] hover:text-[#79b8ff]'
                          >
                            Open trip <ArrowRight className='size-3.5' />
                          </Link>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        )}

        <footer className='px-4 py-3 border-t border-[#1c2128] flex items-center justify-between'>
          <span className='text-ui-xs text-[var(--text-muted)]'>
            {pagination
              ? `Offset ${pagination.offset} · Returned ${pagination.returned}`
              : 'Offset 0 · Returned 0'}
          </span>
          <div className='flex items-center gap-2'>
            <button
              type='button'
              disabled={!canPrev}
              onClick={() => setOffset((current) => Math.max(0, current - PAGE_SIZE))}
              className='px-3 py-1.5 rounded-lg border border-[#30363d] text-ui-xs text-[#e6edf3] disabled:opacity-50 disabled:cursor-not-allowed'
            >
              Previous
            </button>
            <button
              type='button'
              disabled={!canNext}
              onClick={() => setOffset((current) => current + PAGE_SIZE)}
              className='px-3 py-1.5 rounded-lg border border-[#30363d] text-ui-xs text-[#e6edf3] disabled:opacity-50 disabled:cursor-not-allowed'
            >
              Next
            </button>
          </div>
        </footer>
      </section>
    </div>
  );
}

