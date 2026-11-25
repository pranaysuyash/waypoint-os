'use client';

import { handleHorizontalScrollKey } from '@/lib/horizontal-scroll';

import { Suspense, useCallback, useEffect, useId, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import {
  AlertTriangle,
  ArrowDownUp,
  CheckCircle2,
  Clock,
  CreditCard,
  ExternalLink,
  RefreshCw,
  Search,
} from 'lucide-react';
import { usePaymentsQueue } from '@/hooks/usePayments';
import GroupCollectionPanel from './GroupCollectionPanel';
import type {
  PaymentQueueItem,
  PaymentQueueParams,
  PaymentStatus,
  QueueStatus,
  RefundStatus,
} from '@/lib/api-client';

const PAGE_SIZE = 25;

const QUEUE_STATUS_OPTIONS: Array<{ value: '' | QueueStatus; label: string }> = [
  { value: '', label: 'All queue statuses' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'due_soon', label: 'Due soon (≤ 7 days)' },
  { value: 'due_later', label: 'Due later' },
  { value: 'refund_in_progress', label: 'Refund in progress' },
  { value: 'paid_complete', label: 'Paid complete' },
  { value: 'not_configured', label: 'Not configured' },
  { value: 'unknown', label: 'Unknown' },
];

const PAYMENT_STATUS_OPTIONS: Array<{ value: '' | PaymentStatus; label: string }> = [
  { value: '', label: 'All payment statuses' },
  { value: 'not_started', label: 'Not started' },
  { value: 'deposit_paid', label: 'Deposit paid' },
  { value: 'partially_paid', label: 'Partially paid' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'waived', label: 'Waived' },
  { value: 'refunded', label: 'Refunded' },
  { value: 'unknown', label: 'Unknown' },
];

const REFUND_STATUS_OPTIONS: Array<{ value: '' | RefundStatus; label: string }> = [
  { value: '', label: 'All refund statuses' },
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
  value: '' | NonNullable<PaymentQueueParams['due_bucket']>;
  label: string;
}> = [
  { value: '', label: 'All due windows' },
  { value: 'overdue', label: 'Past due' },
  { value: 'due_0_3', label: 'Due in 0–3 days' },
  { value: 'due_4_7', label: 'Due in 4–7 days' },
  { value: 'due_8_14', label: 'Due in 8–14 days' },
  { value: 'none', label: 'No due date' },
];

function formatMoney(value: number | null | undefined, currency: string): string {
  if (value == null) return '—';
  const code = (currency || 'INR').toUpperCase();
  try {
    if (code === 'INR') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: Number.isInteger(value) ? 0 : 2,
      }).format(value);
    }
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: code }).format(value);
  } catch {
    return `${code} ${value.toFixed(2)}`;
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

function queueBadgeClasses(status: QueueStatus): string {
  switch (status) {
    case 'overdue':
      return 'bg-[#f85149]/15 text-[#ff7b72] border-[#f85149]/40';
    case 'due_soon':
      return 'bg-[#d29922]/15 text-[#e3b341] border-[#d29922]/40';
    case 'due_later':
      return 'bg-[#1f6feb]/15 text-[#58a6ff] border-[#1f6feb]/40';
    case 'refund_in_progress':
      return 'bg-[#a371f7]/15 text-[#bc8cff] border-[#a371f7]/40';
    case 'paid_complete':
      return 'bg-[#238636]/15 text-[#3fb950] border-[#238636]/40';
    default:
      return 'bg-[#21262d] text-[#8b949e] border-[#30363d]';
  }
}

function formatDueRelative(dueDate: string | null | undefined, queueStatus: QueueStatus): string | null {
  if (!dueDate) return null;
  const parsed = new Date(`${dueDate}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.round((parsed.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  if (queueStatus === 'paid_complete') return null;
  if (diffDays < 0) return `${Math.abs(diffDays)}d overdue`;
  if (diffDays === 0) return 'Due today';
  if (diffDays <= 14) return `In ${diffDays}d`;
  return null;
}

export default function PaymentsPage() {
  return (
    <Suspense fallback={<div className='p-6 text-[#8b949e]'>Loading payments queue…</div>}>
      <PaymentsQueueContent />
    </Suspense>
  );
}

function PaymentsQueueContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const baseId = useId();
  const searchParamsString = searchParams.toString();

  // Keep local optimistic overrides bound to the URL string they were mutated against
  // so mocked useSearchParams tests and browser URL navigation both update cleanly with zero effect setState.
  const [overlay, setOverlay] = useState<{
    base: string;
    patch: Record<string, string | null | undefined>;
  }>({ base: searchParamsString, patch: {} });

  const activePatch = useMemo(
    () => (overlay.base === searchParamsString ? overlay.patch : {}),
    [overlay, searchParamsString]
  );

  const readParam = (key: string): string => {
    if (key in activePatch) return activePatch[key] || '';
    return searchParams.get(key) || '';
  };

  const queueStatus = readParam('queue_status') as '' | QueueStatus;
  const paymentStatus = readParam('payment_status') as '' | PaymentStatus;
  const refundStatus = readParam('refund_status') as '' | RefundStatus;
  const dueBucket = readParam('due_bucket') as '' | NonNullable<PaymentQueueParams['due_bucket']>;
  const sortMode = (readParam('sort') === 'recent' ? 'recent' : 'urgent') as 'urgent' | 'recent';
  const configuredOnly = readParam('configured_only') === 'true';
  const urlQuery = readParam('q');
  const parsedOffset = Number.parseInt(readParam('offset') || '0', 10);
  const offset = Number.isFinite(parsedOffset) && parsedOffset >= 0 ? parsedOffset : 0;

  const [searchInput, setSearchInput] = useState(urlQuery);

  const updateParams = useCallback(
    (patch: Record<string, string | null | undefined>) => {
      setOverlay((prev) => ({
        base: searchParamsString,
        patch: { ...(prev.base === searchParamsString ? prev.patch : {}), ...patch },
      }));

      const next = new URLSearchParams(searchParamsString);
      for (const [key, value] of Object.entries(patch)) {
        if (!value) {
          next.delete(key);
        } else {
          next.set(key, value);
        }
      }
      const qs = next.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [pathname, router, searchParamsString]
  );

  useEffect(() => {
    const trimmed = searchInput.trim();
    if (trimmed === urlQuery) return;
    const timer = setTimeout(() => {
      updateParams({ q: trimmed || null, offset: null });
    }, 250);
    return () => clearTimeout(timer);
  }, [searchInput, urlQuery, updateParams]);

  const queryParams = useMemo<PaymentQueueParams>(
    () => ({
      limit: PAGE_SIZE,
      offset,
      queue_status: queueStatus || undefined,
      payment_status: paymentStatus || undefined,
      refund_status: refundStatus || undefined,
      due_bucket: dueBucket || undefined,
      configured_only: configuredOnly || undefined,
      q: urlQuery || undefined,
      sort: sortMode,
    }),
    [offset, queueStatus, paymentStatus, refundStatus, dueBucket, configuredOnly, urlQuery, sortMode]
  );

  const { data, isLoading, error, refetch } = usePaymentsQueue(queryParams);

  const summary = data?.summary;
  const pagination = data?.pagination;
  const items = data?.items ?? [];

  const hasActiveFilters = Boolean(
    queueStatus || paymentStatus || refundStatus || dueBucket || configuredOnly || urlQuery
  );

  const clearAllFilters = () => {
    setSearchInput('');
    updateParams({
      queue_status: null,
      payment_status: null,
      refund_status: null,
      due_bucket: null,
      configured_only: null,
      q: null,
      offset: null,
    });
  };

  const toggleKpiFilter = (targetQueueStatus: '' | QueueStatus) => {
    if (!targetQueueStatus) {
      updateParams({ queue_status: null, configured_only: null, offset: null });
      return;
    }
    const nextValue = queueStatus === targetQueueStatus ? null : targetQueueStatus;
    updateParams({ queue_status: nextValue, offset: null });
  };

  const kpiCards: Array<{
    key: '' | QueueStatus;
    label: string;
    value: number;
    toneClass: string;
    activeRing: string;
    icon: typeof CreditCard;
  }> = [
    {
      key: '',
      label: 'Total in queue',
      value: summary?.total ?? 0,
      toneClass: 'text-[#e6edf3]',
      activeRing: 'border-[#58a6ff] bg-[#161b22]',
      icon: CreditCard,
    },
    {
      key: 'overdue',
      label: 'Overdue',
      value: summary?.overdue_count ?? 0,
      toneClass: 'text-[#ff7b72]',
      activeRing: 'border-[#f85149] bg-[#f85149]/10',
      icon: AlertTriangle,
    },
    {
      key: 'due_soon',
      label: 'Due soon',
      value: summary?.due_soon_count ?? 0,
      toneClass: 'text-[#e3b341]',
      activeRing: 'border-[#d29922] bg-[#d29922]/10',
      icon: Clock,
    },
    {
      key: 'not_configured',
      label: 'Not configured',
      value: summary?.not_configured_count ?? 0,
      toneClass: 'text-[#8b949e]',
      activeRing: 'border-[#8b949e] bg-[#21262d]',
      icon: CreditCard,
    },
    {
      key: 'refund_in_progress',
      label: 'Refund in progress',
      value: summary?.refund_in_progress_count ?? 0,
      toneClass: 'text-[#bc8cff]',
      activeRing: 'border-[#a371f7] bg-[#a371f7]/10',
      icon: RefreshCw,
    },
  ];

  return (
    <div className='p-6 space-y-6'>
      {/* Group collection (FND-0409): per-traveler shares, schedules, reminders */}
      <GroupCollectionPanel />
      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <CreditCard className='size-5 text-[#3fb950]' aria-hidden='true' />
            Payments
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Tenant payment balances, overdue follow-ups, due dates, and refund queue across trips.
          </p>
        </div>

        <div className='flex flex-wrap items-center gap-2'>
          <div className='inline-flex items-center rounded-md border border-[#30363d] bg-[#161b22] p-0.5 text-ui-xs'>
            <button
              type='button'
              onClick={() => updateParams({ sort: null, offset: null })}
              aria-pressed={sortMode === 'urgent'}
              className={`px-2.5 py-1 rounded font-medium flex items-center gap-1.5 transition-colors ${
                sortMode === 'urgent' ? 'bg-[#21262d] text-[#e6edf3]' : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}
            >
              <ArrowDownUp className='size-3.5 text-[#3fb950]' aria-hidden='true' />
              Urgency priority
            </button>
            <button
              type='button'
              onClick={() => updateParams({ sort: 'recent', offset: null })}
              aria-pressed={sortMode === 'recent'}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                sortMode === 'recent' ? 'bg-[#21262d] text-[#e6edf3]' : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}
            >
              Most recent
            </button>
          </div>

          <button
            type='button'
            onClick={() =>
              updateParams({
                configured_only: configuredOnly ? null : 'true',
                offset: null,
              })
            }
            aria-pressed={configuredOnly}
            className={`px-3 py-1.5 rounded-md border text-ui-xs font-medium transition-colors flex items-center gap-1.5 ${
              configuredOnly
                ? 'border-[#3fb950]/50 bg-[#238636]/15 text-[#3fb950]'
                : 'border-[#30363d] bg-[#161b22] text-[#8b949e] hover:text-[#e6edf3]'
            }`}
          >
            <CheckCircle2 className='size-3.5' aria-hidden='true' />
            Hide unconfigured
          </button>

          {hasActiveFilters && (
            <button
              type='button'
              onClick={clearAllFilters}
              className='px-2.5 py-1.5 rounded-md border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-ui-xs text-[#e6edf3] transition-colors'
            >
              Reset filters
            </button>
          )}

          <button
            type='button'
            onClick={() => void refetch()}
            className='inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#30363d] bg-[#161b22] hover:bg-[#21262d] text-ui-xs text-[#e6edf3] transition-colors'
          >
            <RefreshCw className={`size-3.5 ${isLoading ? 'animate-spin' : ''}`} aria-hidden='true' />
            Refresh
          </button>
        </div>
      </div>

      {/* Interactive KPI Cards */}
      <div className='grid grid-cols-2 lg:grid-cols-5 gap-3'>
        {kpiCards.map((card) => {
          const Icon = card.icon;
          const isActive =
            card.key === '' ? !queueStatus && !configuredOnly : queueStatus === card.key;
          return (
            <button
              key={card.label}
              type='button'
              onClick={() => toggleKpiFilter(card.key)}
              aria-pressed={isActive}
              className={`text-left rounded-lg border p-3.5 transition-colors ${
                isActive
                  ? card.activeRing
                  : 'border-[#30363d] bg-[#161b22] hover:border-[#484f58]'
              }`}
            >
              <div className='flex items-center justify-between text-xs text-[#8b949e]'>
                <span>{card.label}</span>
                <Icon className='size-3.5 opacity-80' aria-hidden='true' />
              </div>
              <div className={`mt-1.5 text-xl font-semibold tabular-nums ${card.toneClass}`}>
                {card.value.toLocaleString('en-IN')}
              </div>
            </button>
          );
        })}
      </div>

      {/* Search + Accessible Filters */}
      <div className='rounded-xl border border-[#30363d] bg-[#161b22] p-4 space-y-3'>
        <div className='relative'>
          <Search
            className='size-4 text-[#8b949e] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none'
            aria-hidden='true'
          />
          <input
            id={`${baseId}-search`}
            name='payments_search'
            type='search'
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder='Search by trip name, destination, or trip reference…'
            aria-label='Search payments by trip name, destination, or reference'
            className='w-full bg-[#0d1117] border border-[#30363d] rounded-md pl-9 pr-3 py-2 text-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:border-[#3fb950] outline-none'
          />
        </div>

        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3'>
          <div>
            <label
              htmlFor={`${baseId}-queue-status`}
              className='block text-xs text-[#8b949e] mb-1'
            >
              Queue status
            </label>
            <select
              id={`${baseId}-queue-status`}
              name='queue_status'
              value={queueStatus}
              onChange={(e) => updateParams({ queue_status: e.target.value || null, offset: null })}
              className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:border-[#3fb950] outline-none'
            >
              {QUEUE_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value || 'all'} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor={`${baseId}-payment-status`}
              className='block text-xs text-[#8b949e] mb-1'
            >
              Payment status
            </label>
            <select
              id={`${baseId}-payment-status`}
              name='payment_status'
              value={paymentStatus}
              onChange={(e) => updateParams({ payment_status: e.target.value || null, offset: null })}
              className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:border-[#3fb950] outline-none'
            >
              {PAYMENT_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value || 'all'} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor={`${baseId}-refund-status`}
              className='block text-xs text-[#8b949e] mb-1'
            >
              Refund status
            </label>
            <select
              id={`${baseId}-refund-status`}
              name='refund_status'
              value={refundStatus}
              onChange={(e) => updateParams({ refund_status: e.target.value || null, offset: null })}
              className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:border-[#3fb950] outline-none'
            >
              {REFUND_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value || 'all'} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor={`${baseId}-due-bucket`}
              className='block text-xs text-[#8b949e] mb-1'
            >
              Due window
            </label>
            <select
              id={`${baseId}-due-bucket`}
              name='due_bucket'
              value={dueBucket}
              onChange={(e) => updateParams({ due_bucket: e.target.value || null, offset: null })}
              className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:border-[#3fb950] outline-none'
            >
              {DUE_BUCKET_OPTIONS.map((opt) => (
                <option key={opt.value || 'all'} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Queue Table */}
      <div className='rounded-xl border border-[#30363d] bg-[#161b22] overflow-hidden'>
        {!error && !isLoading && items.length > 0 && (
            <p id={`${baseId}-table-scroll`} className='border-b border-[#30363d] px-4 py-2 text-xs text-[#8b949e] xl:sr-only'>
              Scroll the table to see balances and trip actions.
            </p>
        )}
        {error ? (
          <div className='p-8 text-center space-y-3'>
            <p className='text-sm text-[#ff7b72]'>Failed to load payment queue.</p>
            <button
              type='button'
              onClick={() => void refetch()}
              className='px-3 py-1.5 rounded-md border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-xs text-[#e6edf3]'
            >
              Retry
            </button>
          </div>
        ) : isLoading ? (
          <div className='p-6 space-y-2' aria-label='Loading payment rows'>
            {[0, 1, 2, 3, 4].map((row) => (
              <div key={row} className='h-10 rounded bg-[#0d1117] animate-pulse' />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className='p-8 text-center space-y-2 text-sm text-[#8b949e]'>
            <p>No trips match the active payment filters.</p>
            {hasActiveFilters && (
              <button
                type='button'
                onClick={clearAllFilters}
                className='text-[#58a6ff] hover:underline text-xs'
              >
                Clear all filters
              </button>
            )}
          </div>
        ) : (
          <div
            role='region'
            aria-label='Payment queue table'
            aria-describedby={`${baseId}-table-scroll`}
            onKeyDown={handleHorizontalScrollKey}
            tabIndex={0}
            className='overflow-x-auto focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[#58a6ff]'
          >
            <table className='w-full text-left border-collapse text-sm'>
              <thead>
                <tr className='border-b border-[#30363d] bg-[#0d1117] text-xs uppercase tracking-wider text-[#8b949e]'>
                  <th className='px-4 py-3 font-medium'>Trip</th>
                  <th className='px-4 py-3 font-medium'>Queue Status</th>
                  <th className='px-4 py-3 font-medium'>Payment Status</th>
                  <th className='px-4 py-3 font-medium text-right'>Agreed</th>
                  <th className='px-4 py-3 font-medium text-right'>Paid</th>
                  <th className='px-4 py-3 font-medium text-right'>Balance Due</th>
                  <th className='px-4 py-3 font-medium'>Final Due</th>
                  <th className='px-4 py-3 font-medium'>Refund</th>
                  <th className='px-4 py-3 font-medium text-right'>Workspace</th>
                </tr>
              </thead>
              <tbody className='divide-y divide-[#30363d]'>
                {items.map((item) => {
                  const dueRel = formatDueRelative(item.final_payment_due, item.queue_status);
                  return (
                    <tr key={item.trip_id} className='hover:bg-[#0d1117]/60 transition-colors'>
                      <td className='px-4 py-3'>
                        <div className='font-medium text-[#e6edf3]'>{renderTripLabel(item)}</div>
                        <div className='flex flex-wrap items-center gap-1.5 mt-0.5 text-xs text-[#8b949e]'>
                          <span>{item.destination || 'Destination pending'}</span>
                          {item.payment_reference_present && (
                            <span className='px-1.5 py-0.5 rounded bg-[#21262d] text-[#8b949e]'>
                              Ref recorded
                            </span>
                          )}
                          {item.payment_proof_url_present && (
                            <span className='px-1.5 py-0.5 rounded bg-[#238636]/15 text-[#3fb950]'>
                              Proof attached
                            </span>
                          )}
                        </div>
                      </td>
                      <td className='px-4 py-3'>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium whitespace-nowrap ${queueBadgeClasses(
                            item.queue_status
                          )}`}
                        >
                          {toTitleCase(item.queue_status)}
                        </span>
                      </td>
                      <td className='px-4 py-3 text-[#c9d1d9] whitespace-nowrap'>
                        {toTitleCase(item.payment_status)}
                      </td>
                      <td className='px-4 py-3 text-right tabular-nums text-[#c9d1d9] whitespace-nowrap'>
                        {formatMoney(item.agreed_amount, item.currency)}
                      </td>
                      <td className='px-4 py-3 text-right tabular-nums text-[#3fb950] whitespace-nowrap'>
                        {formatMoney(item.amount_paid, item.currency)}
                      </td>
                      <td className='px-4 py-3 text-right tabular-nums font-medium text-[#e6edf3] whitespace-nowrap'>
                        {formatMoney(item.balance_due, item.currency)}
                      </td>
                      <td className='px-4 py-3 whitespace-nowrap'>
                        <div className='text-[#c9d1d9]'>{item.final_payment_due || '—'}</div>
                        {dueRel && (
                          <div
                            className={`text-xs ${
                              item.queue_status === 'overdue' ? 'text-[#ff7b72]' : 'text-[#e3b341]'
                            }`}
                          >
                            {dueRel}
                          </div>
                        )}
                      </td>
                      <td className='px-4 py-3 text-[#c9d1d9] whitespace-nowrap'>
                        {toTitleCase(item.refund_status)}
                      </td>
                      <td className='px-4 py-3 text-right whitespace-nowrap'>
                        <Link
                          href={`/trips/${item.trip_id}/ops`}
                          className='inline-flex items-center gap-1 text-xs font-medium text-[#58a6ff] hover:underline'
                        >
                          Open trip
                          <ExternalLink className='size-3' aria-hidden='true' />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {pagination && pagination.total > 0 && (
          <div className='border-t border-[#30363d] bg-[#0d1117] px-4 py-3 flex items-center justify-between text-xs text-[#8b949e]'>
            <span>
              Showing {pagination.returned} of {pagination.total}
            </span>
            <div className='flex items-center gap-2'>
              <button
                type='button'
                disabled={offset <= 0}
                onClick={() => updateParams({ offset: String(Math.max(0, offset - PAGE_SIZE)) })}
                className='px-2.5 py-1 rounded border border-[#30363d] bg-[#161b22] text-[#e6edf3] disabled:opacity-40 hover:bg-[#21262d]'
              >
                Previous
              </button>
              <button
                type='button'
                disabled={!pagination.has_more}
                onClick={() => updateParams({ offset: String(offset + PAGE_SIZE) })}
                className='px-2.5 py-1 rounded border border-[#30363d] bg-[#161b22] text-[#e6edf3] disabled:opacity-40 hover:bg-[#21262d]'
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
