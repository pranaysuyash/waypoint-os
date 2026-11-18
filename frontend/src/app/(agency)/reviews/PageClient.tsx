'use client';

import { useState, useCallback, memo } from 'react';
import Link from 'next/link';
import {
  CheckCircle,
  XCircle,
  RefreshCw,
  AlertTriangle,
  Clock,
  User,
  Wallet,
  MapPin,
  ChevronRight,
  MoreHorizontal,
} from 'lucide-react';
import { useReviews } from '@/hooks/useGovernance';
import { useUnifiedState } from '@/hooks/useUnifiedState';
import { getTripRoute } from '@/lib/routes';
import { StatusBadge } from '@/components/ui/status-badge';
import { formatLeadTitle } from '@/lib/lead-display';
import { titleCase } from '@/lib/label-maps';
import { CURRENCY_CONFIG, formatBudgetWithCode, formatMoneyCompact, type SupportedCurrency } from '@/lib/currency';
import type { TripReview, ReviewStatus, RiskFlag } from '@/types/governance';

const REVIEW_STATUS_MAP = {
  pending:         { label: 'Pending Review',   color: '#d29922', icon: Clock },
  revision_needed: { label: 'Revision Needed',  color: '#e36f2f', icon: RefreshCw },
  approved:        { label: 'Approved',         color: '#3fb950', icon: CheckCircle },
  rejected:        { label: 'Rejected',         color: '#f85149', icon: XCircle },
  escalated:       { label: 'Escalated',        color: '#a371f7', icon: AlertTriangle },
};

const DAY_MS = 1000 * 60 * 60 * 24;

function hasKnownDestination(value?: string | null): boolean {
  const cleaned = value?.trim();
  if (!cleaned) return false;
  return !['tbd', 'to confirm', 'unknown', 'not set', 'n/a', '-'].includes(cleaned.toLowerCase());
}

function getReviewTitle(review: TripReview): string {
  if (!hasKnownDestination(review.destination)) return 'Trip details incomplete';
  return formatLeadTitle(review.destination, review.tripType);
}

function getDaysWaiting(submittedAt: string, referenceNow: number) {
  return Math.floor((referenceNow - new Date(submittedAt).getTime()) / DAY_MS);
}

function toSupportedCurrency(currency: string): SupportedCurrency {
  const normalized = currency.trim().toUpperCase();
  return normalized in CURRENCY_CONFIG ? (normalized as SupportedCurrency) : 'USD';
}

function humanizeReviewReason(reason?: string | null): string {
  const cleaned = reason?.trim();
  if (!cleaned) return 'Flagged for owner review';
  return cleaned
    .replace(/Decision state STOP_NEEDS_REVIEW requires owner review/gi, 'Policy hold: requires owner review')
    .replace(/\bSTOP_NEEDS_REVIEW\b/g, 'policy hold');
}

const RiskFlagBadge = memo(function RiskFlagBadge({ flag }: { flag: RiskFlag }) {
  /* one colour per flag so identical flags are identical and distinct flags are distinct */
  const config: Record<RiskFlag, { label: string; color: string; bg: string }> = {
    high_value:        { label: 'High Value', color: '#e36f2f', bg: 'rgba(227,111,47,0.12)' },
    unusual_destination:{ label: 'Unusual',   color: '#a371f7', bg: 'rgba(163,113,247,0.12)' },
    tight_deadline:    { label: 'Tight',     color: '#d29922', bg: 'rgba(210,153,34,0.12)' },
    complex_itinerary: { label: 'Complex',   color: '#58a6ff', bg: 'rgba(88,166,255,0.12)' },
    visa_required:     { label: 'Visa',      color: '#58a6ff', bg: 'rgba(88,166,255,0.12)' },
    supplier_delay:    { label: 'Supplier',  color: '#d29922', bg: 'rgba(210,153,34,0.12)' },
  };

  const c = config[flag];
  return (
    <span className='inline-block px-1.5 py-0.5 text-ui-xs rounded-md font-medium'
      style={{ color: c.color, background: c.bg }}
    >
      {c.label}
    </span>
  );
});

const ReviewCard = memo(function ReviewCard({
  review,
  referenceNow,
  isSelected = false,
  onToggleSelect,
  onApprove,
  onReject,
  onRequestChanges,
}: {
  review: TripReview;
  referenceNow: number;
  isSelected?: boolean;
  onToggleSelect?: (id: string, selected: boolean) => void;
  onApprove: (id: string, notes?: string) => void;
  onReject: (id: string, notes?: string) => void;
  onRequestChanges: (id: string, notes?: string) => void;
}) {
  const [showActions, setShowActions] = useState(false);
  const [reason, setReason] = useState('');
  const daysWaiting = getDaysWaiting(review.submittedAt, referenceNow);
  const isCriticalPriority =
    Boolean(review.isEscalated) ||
    review.slaStatus === 'breached' ||
    review.riskFlags.includes('high_value') ||
    review.riskFlags.includes('complex_itinerary');
  const hasHighAge = review.status === 'pending' && daysWaiting > 7;

  return (
    <div
      className={`rounded-xl border p-4 transition-all hover:border-[#30363d] ${
        isCriticalPriority ? 'border-[#f85149]/35 bg-[#f85149]/[0.04]' : 'border-[#1c2128] bg-[#0f1115]'
      }`}
    >
      <div className='flex items-start justify-between gap-4'>
        <div className='flex items-start gap-3 flex-1 min-w-0'>
          {onToggleSelect && (
            <input
              type='checkbox'
              id={`select-review-${review.id}`}
              name={`select-review-${review.id}`}
              aria-label={`Select quote ${review.tripReference || review.id}`}
              checked={isSelected}
              onChange={(e) => onToggleSelect(review.id, e.target.checked)}
              className='mt-1 size-4 rounded border-[#30363d] bg-[#0d1117] text-[#58a6ff] focus:ring-0 focus:ring-offset-0 cursor-pointer shrink-0'
            />
          )}
          <div className='flex-1 min-w-0'>
            <div className='flex items-center gap-2 mb-1'>
              {isCriticalPriority && <AlertTriangle className='size-4 text-[#f85149] shrink-0' />}
              <span className='text-ui-sm text-[#8b949e] font-mono'>{review.tripReference}</span>
              <StatusBadge status={review.status} map={REVIEW_STATUS_MAP} />
            </div>
            
            <h3 className='text-ui-base font-semibold text-[#e6edf3] mb-1'>
              {getReviewTitle(review)}
            </h3>
            {!hasKnownDestination(review.destination) && (review.tripReference || review.agentName) && (
              <p className='text-ui-xs text-[#58a6ff] font-medium mb-1'>
                {[review.tripReference ? `Ref ${review.tripReference}` : null, review.agentName && review.agentName !== 'Unassigned' ? `Assigned: ${review.agentName}` : null].filter(Boolean).join(' · ')}
              </p>
            )}
          
          <div className='flex flex-wrap items-center gap-4 text-ui-xs text-[#8b949e] mb-2'>
            <span className='flex items-center gap-1'>
              <MapPin className='size-3' /> {titleCase(review.tripType)}
            </span>
            <span className='flex items-center gap-1'>
              <User className='size-3' /> {review.partySize} pax
            </span>
            <span className='flex items-center gap-1'>
              <Wallet className='size-3' />
              {review.value > 0
                ? formatBudgetWithCode(review.value, toSupportedCurrency(review.currency))
                : 'Budget to confirm'}
            </span>
            <span className={`flex items-center gap-1 ${hasHighAge ? 'text-[#d29922]' : ''}`}>
              <Clock className='size-3' /> {daysWaiting}d waiting
            </span>
          </div>
          
          <p className='text-ui-sm text-[#8b949e] mb-2'>
            <span className='text-[#e6edf3]'>Reason for review:</span> {humanizeReviewReason(review.reason)}
          </p>
          
          {review.agentNotes && (
            <blockquote className='text-ui-sm text-[#8b949e] border-l-2 border-[#30363d] pl-3 italic'>
              &ldquo;{review.agentNotes}&rdquo;
              <span className='text-ui-xs text-[#484f58] not-italic ml-2'>- {review.agentName}</span>
            </blockquote>
          )}

          {/* Decision history (FND-0270): the last recorded decision is visible
              on the card itself, not only on the trip page. */}
          {(review.reviewedBy || review.reviewedAt) && (
            <p className='text-ui-xs text-[#484f58] mt-2'>
              Last decision:{' '}
              {review.status ? <span className='text-[#8b949e] capitalize'>{review.status.replace('_', ' ')}</span> : null}
              {review.reviewedBy ? <> by <span className='text-[#8b949e]'>{review.reviewedBy}</span></> : null}
              {review.reviewedAt ? <> at <span className='text-[#8b949e]'>{new Date(review.reviewedAt).toLocaleString()}</span></> : null}
            </p>
          )}
          {review.ownerNotes && (
            <p className='text-ui-xs text-[#8b949e] mt-1'>
              <span className='text-[#484f58]'>Owner notes:</span> {review.ownerNotes}
            </p>
          )}
          
          {review.riskFlags.length > 0 && (
            <div className='flex items-center gap-2 mt-2'>
              <span className='text-ui-xs text-[#8b949e]'>Risk flags:</span>
              {review.riskFlags.map((flag, flagIndex) => (
                <RiskFlagBadge key={`${flag}-${flagIndex}`} flag={flag} />
              ))}
            </div>
          )}
          </div>
        </div>
        
        <div className='flex flex-col gap-2'>
          {!showActions ? (
            <button
              onClick={() => setShowActions(true)}
              className='px-3 py-1.5 bg-[#58a6ff] text-[#0d1117] rounded-lg text-ui-sm font-medium hover:bg-[#6eb5ff] transition-colors'
            >
              Review
            </button>
          ) : (
            <div className='flex flex-col gap-2'>
              {/* FND-0302: the reason is the artifact — reject/request-changes
                  without one leaves downstream revision intent unrecorded. */}
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder='Reason (required for reject / request changes)'
                rows={2}
                data-testid='review-reason-input'
                className='w-full px-2 py-1.5 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-xs text-[#e6edf3] placeholder:text-[#484f58] focus:outline-none focus:border-[#58a6ff]'
              />
              
              <button
                onClick={() => {
                  onApprove(review.id, reason.trim() || undefined);
                  setShowActions(false);
                  setReason('');
                }}
                className='flex items-center gap-1 px-3 py-1.5 bg-[#3fb950] text-white rounded-lg text-ui-sm font-medium hover:bg-[#4bc95b] transition-colors'
              >
                <CheckCircle className='size-3.5' /> Approve
              </button>
              
              <button
                disabled={!reason.trim()}
                onClick={() => {
                  onRequestChanges(review.id, reason.trim());
                  setShowActions(false);
                  setReason('');
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-ui-sm font-medium transition-colors ${reason.trim() ? 'bg-[#d29922] text-white hover:bg-[#e3a532]' : 'bg-[#d29922]/40 text-white/60 cursor-not-allowed'}`}
              >
                <RefreshCw className='size-3.5' /> Request Changes
              </button>
              
              <button
                disabled={!reason.trim()}
                onClick={() => {
                  onReject(review.id, reason.trim());
                  setShowActions(false);
                  setReason('');
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-ui-sm font-medium transition-colors ${reason.trim() ? 'bg-[#f85149] text-white hover:bg-[#ff6b6b]' : 'bg-[#f85149]/40 text-white/60 cursor-not-allowed'}`}
              >
                <XCircle className='size-3.5' /> Reject
              </button>
              
              <button
                onClick={() => setShowActions(false)}
                className='px-3 py-1.5 text-[#8b949e] text-ui-sm hover:text-[#e6edf3] transition-colors'
              >
                Cancel
              </button>
            </div>
          )}
          
          {review.tripId && (
            <Link
              href={getTripRoute(review.tripId, 'output')}
              className='flex items-center justify-center gap-1 text-ui-xs text-[#58a6ff] hover:text-[#79b8ff] transition-colors'
            >
              View Quote <ChevronRight className='size-3' />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
});

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function OwnerReviewsPage() {
  const [statusFilter, setStatusFilter] = useState<ReviewStatus | 'all'>('all');
  const [visibleLimit, setVisibleLimit] = useState(25);
  const [referenceNow] = useState(() => Date.now());
  const { data: reviews, isLoading, error, refetch, submitAction, bulkAction } = useReviews();
  const { state: unifiedState } = useUnifiedState();
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedReviews, setSelectedReviews] = useState<Set<string>>(new Set());
  const [bulkActionType, setBulkActionType] = useState<'approve' | 'reject' | 'request_changes' | null>(null);
  const [bulkNotes, setBulkNotes] = useState('');
  const [bulkFeedback, setBulkFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Filter reviews (page-local — acceptable per SSOT rule)
  const filteredReviews = reviews.filter((r) => {
    if (statusFilter === 'all') return true;
    return r.status === statusFilter;
  });

  // Sort by urgency (days waiting desc, then value desc)
  const sortedReviews = filteredReviews.toSorted((a, b) => {
    const daysA = getDaysWaiting(a.submittedAt, referenceNow);
    const daysB = getDaysWaiting(b.submittedAt, referenceNow);
    if (daysA !== daysB) return daysB - daysA;
    return b.value - a.value;
  });

  const [actionError, setActionError] = useState<string | null>(null);

  const handleAction = useCallback(async (id: string, action: 'approve' | 'reject' | 'request_changes', notes: string = '') => {
    setIsProcessing(true);
    setActionError(null);
    try {
      const internalAction = action === 'approve' ? 'approve' : action === 'reject' ? 'reject' : 'request_changes';
      // FND-0302: only approvals may fall back to a default note; rejections
      // and revision requests carry an operator-written reason (backend 400s
      // otherwise, so the FE never silently fabricates one).
      await submitAction({
        reviewId: id,
        action: internalAction as any,
        notes: notes || (action === 'approve' ? 'Owner approved via dashboard.' : '')
      });
      await refetch();
    } catch (err) {
      console.error(`Failed to ${action} review:`, err);
      setActionError(`Failed to ${action.replace('_', ' ')} review${err instanceof Error ? `: ${err.message}` : ''}.`);
    } finally {
      setIsProcessing(false);
    }
  }, [submitAction, refetch]);

  const handleApprove = (id: string, notes?: string) => handleAction(id, 'approve', notes ?? '');
  const handleReject = (id: string, notes?: string) => handleAction(id, 'reject', notes ?? '');
  const handleRequestChanges = (id: string, notes?: string) => handleAction(id, 'request_changes', notes ?? '');

  const handleToggleSelect = useCallback((id: string, selected: boolean) => {
    setSelectedReviews((prev) => {
      const next = new Set(prev);
      if (selected) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedReviews(new Set());
  }, []);

  const handleSelectAllVisible = useCallback(() => {
    const ids = sortedReviews.slice(0, visibleLimit).map((r) => r.id);
    setSelectedReviews(new Set(ids));
  }, [sortedReviews, visibleLimit]);

  const handleExecuteBulkAction = useCallback(async () => {
    if (!bulkActionType || selectedReviews.size === 0) return;
    setIsProcessing(true);
    setBulkFeedback(null);
    setActionError(null);
    try {
      const ids = Array.from(selectedReviews);
      const requests = ids.map((id) => ({
        reviewId: id,
        action: bulkActionType as any,
        notes: bulkNotes.trim() || (bulkActionType === 'approve' ? 'Bulk approved by owner via dashboard.' : 'Bulk review action'),
      }));
      const res = await bulkAction(requests);
      setBulkFeedback({
        type: 'success',
        message: `Successfully processed ${res?.processed ?? ids.length} quotes (${bulkActionType.replace('_', ' ')}).`,
      });
      setSelectedReviews(new Set());
      setBulkActionType(null);
      setBulkNotes('');
      await refetch();
    } catch (err) {
      console.error('Bulk review action failed:', err);
      setBulkFeedback({
        type: 'error',
        message: err instanceof Error ? err.message : 'Bulk review action failed. Please try again.',
      });
    } finally {
      setIsProcessing(false);
    }
  }, [bulkActionType, selectedReviews, bulkNotes, bulkAction, refetch]);

  if (error) {
    return (
      <div className='p-12 text-center'>
        <div className='inline-flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20'>
          <AlertTriangle className='size-5' />
          <span>Error loading reviews: {error.message}</span>
        </div>
        <button 
          onClick={() => refetch()}
          className='block mx-auto mt-4 text-[#58a6ff] hover:underline'
        >
          Try again
        </button>
      </div>
    );
  }

  // Summary card counts from unified state (SSOT for dashboard-level stats)
  const reviewCounts = unifiedState?.review_counts ?? {};
  const pendingCount = unifiedState?.pending_review_count ?? reviewCounts['pending'] ?? 0;
  const approvedCount = reviewCounts['approved'] ?? 0;
  const escalatedCount = reviewCounts['escalated'] ?? 0;
  const valueByCurrency: Record<string, number> = (() => {
    const fromUnified = unifiedState?.pending_review_value_by_currency;
    if (fromUnified && Object.keys(fromUnified).length > 0) {
      return fromUnified;
    }
    const aggregated: Record<string, number> = {};
    for (const r of reviews) {
      if (r.status === 'pending' && r.value > 0) {
        const cur = toSupportedCurrency(r.currency);
        aggregated[cur] = (aggregated[cur] ?? 0) + r.value;
      }
    }
    if (Object.keys(aggregated).length === 0 && (unifiedState?.total_pending_review_value ?? 0) > 0) {
      const cur = toSupportedCurrency(unifiedState?.primary_review_currency ?? 'INR');
      aggregated[cur] = unifiedState!.total_pending_review_value!;
    }
    return aggregated;
  })();
  const currencyEntries = Object.entries(valueByCurrency).filter(([, amount]) => amount > 0);
  const primaryEntry = currencyEntries.sort((a, b) => b[1] - a[1])[0];
  const totalValueDisplay = primaryEntry
    ? formatMoneyCompact(primaryEntry[1], toSupportedCurrency(primaryEntry[0]))
    : 'To confirm';
  const totalValueSubtitle =
    currencyEntries.length > 1
      ? `+${currencyEntries.length - 1} other ${currencyEntries.length - 1 === 1 ? 'currency' : 'currencies'}`
      : primaryEntry
        ? primaryEntry[0]
        : 'Budgets awaiting entry';
  const hasSummaryBacklog = pendingCount > 0 && reviews.length === 0;
  const hasMoreLoadedReviewsThanVisible = statusFilter === 'all' && reviews.length > 0 && pendingCount > reviews.length;
  const visibleReviews = sortedReviews.slice(0, visibleLimit);
  const remainingReviewsCount = Math.max(0, sortedReviews.length - visibleReviews.length);

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      {/* Header */}
      <header className='flex flex-wrap items-center justify-between gap-3 pt-1'>
        <div>
          <h1 className='text-ui-2xl font-semibold text-[#e6edf3]'>Quote Review</h1>
          <p className='text-ui-base text-[#8b949e] mt-0.5'>
            Quotes waiting for approval before sending to travelers.
          </p>
        </div>
        
        <div className='flex items-center gap-3'>
          <button 
            onClick={() => refetch()}
            className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#8b949e] rounded-lg text-ui-sm hover:text-[#e6edf3] transition-colors'
          >
            <RefreshCw className={`size-4 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          
        </div>
      </header>

      {actionError && (
        <div className='mb-4 flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20' data-testid='review-action-error' role='alert'>
          <AlertTriangle className='size-4' />
          <span className='text-ui-sm'>{actionError}</span>
          <button onClick={() => setActionError(null)} className='ml-auto text-ui-xs text-[#8b949e] hover:text-[#e6edf3]'>Dismiss</button>
        </div>
      )}

      {bulkFeedback && (
        <div
          role='alert'
          className={`flex items-center justify-between p-3 rounded-lg border text-ui-sm ${
            bulkFeedback.type === 'success'
              ? 'bg-[#3fb950]/10 border-[#3fb950]/30 text-[#3fb950]'
              : 'bg-[#f85149]/10 border-[#f85149]/30 text-[#f85149]'
          }`}
        >
          <span>{bulkFeedback.message}</span>
          <button
            onClick={() => setBulkFeedback(null)}
            className='text-ui-xs underline hover:no-underline ml-3'
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Stats */}
      <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e]'>Pending Quotes</span>
          <div className='text-ui-2xl font-bold text-[#e6edf3] tabular-nums mt-1'>{pendingCount.toLocaleString('en-IN')}</div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e] font-inter'>Total Value in Progress</span>
          <div className='text-ui-2xl font-bold text-[#e6edf3] tabular-nums mt-1'>
            {totalValueDisplay}
          </div>
          <div className='text-ui-xs text-[#8b949e] mt-0.5'>{totalValueSubtitle}</div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e]'>Approved Quotes</span>
          <div className='text-ui-2xl font-bold text-[#3fb950] tabular-nums mt-1'>{approvedCount.toLocaleString('en-IN')}</div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e]'>Escalated</span>
          <div className='text-ui-2xl font-bold text-[#58a6ff] tabular-nums mt-1'>{escalatedCount.toLocaleString('en-IN')}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className='flex flex-wrap items-center gap-2 border-b border-[#1c2128] pb-3'>
        {[
          { key: 'all', label: 'All', count: reviews.length },
          { key: 'pending', label: 'Pending', count: pendingCount },
          { key: 'approved', label: 'Approved', count: approvedCount },
          { key: 'rejected', label: 'Rejected', count: reviewCounts['rejected'] ?? 0 },
          { key: 'revision_needed', label: 'Revision Needed', count: reviewCounts['revision_needed'] ?? 0 },
          { key: 'escalated', label: 'Escalated', count: escalatedCount },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setStatusFilter(tab.key as ReviewStatus | 'all');
              setVisibleLimit(25);
            }}
            className={`px-4 py-2 rounded-lg text-ui-sm font-medium transition-colors ${
              statusFilter === tab.key
                ? 'bg-[#161b22] text-[#e6edf3]'
                : 'text-[#8b949e] hover:text-[#e6edf3]'
            }`}
          >
            {tab.label}
            <span className='ml-2 text-ui-xs tabular-nums text-[#8b949e]'>{tab.count.toLocaleString('en-IN')}</span>
          </button>
        ))}
      </div>

      {/* Bulk Actions Toolbar */}
      {selectedReviews.size > 0 && (
        <div className='flex flex-wrap items-center justify-between gap-3 p-3 bg-[#161b22] rounded-xl border border-[#30363d]'>
          <div className='flex items-center gap-3'>
            <span className='text-ui-sm text-[#e6edf3] font-medium'>
              <strong>{selectedReviews.size}</strong> {selectedReviews.size === 1 ? 'quote' : 'quotes'} selected
            </span>
            <button
              type='button'
              onClick={handleSelectAllVisible}
              className='text-ui-xs text-[#58a6ff] hover:underline'
            >
              Select all visible ({visibleReviews.length})
            </button>
            <button
              type='button'
              onClick={handleClearSelection}
              className='text-ui-xs text-[#8b949e] hover:text-[#e6edf3]'
            >
              Clear
            </button>
          </div>
          <div className='flex items-center gap-2 flex-wrap'>
            <button
              type='button'
              onClick={() => {
                setBulkActionType('approve');
                setBulkNotes('Bulk approved by owner via dashboard.');
              }}
              className='flex items-center gap-1.5 px-3 py-1.5 bg-[#3fb950] text-white rounded-lg text-ui-sm font-medium hover:bg-[#4bc95b] transition-colors'
            >
              <CheckCircle className='size-3.5' /> Bulk Approve
            </button>
            <button
              type='button'
              onClick={() => {
                setBulkActionType('request_changes');
                setBulkNotes('');
              }}
              className='flex items-center gap-1.5 px-3 py-1.5 bg-[#d29922] text-white rounded-lg text-ui-sm font-medium hover:bg-[#e3a532] transition-colors'
            >
              <RefreshCw className='size-3.5' /> Bulk Request Changes
            </button>
            <button
              type='button'
              onClick={() => {
                setBulkActionType('reject');
                setBulkNotes('');
              }}
              className='flex items-center gap-1.5 px-3 py-1.5 bg-[#f85149] text-white rounded-lg text-ui-sm font-medium hover:bg-[#ff6b6b] transition-colors'
            >
              <XCircle className='size-3.5' /> Bulk Reject
            </button>
          </div>
        </div>
      )}

      {/* Review Queue */}
      <div className='space-y-3'>
        {hasMoreLoadedReviewsThanVisible && (
          <div className='rounded-xl border border-[#d29922]/25 bg-[#d29922]/10 px-4 py-3 text-ui-sm text-[#d29922]'>
            Showing {reviews.length.toLocaleString('en-IN')} loaded quotes while the summary reports {pendingCount.toLocaleString('en-IN')} pending quotes.
            Refresh if you expect the queue to have grown since the last load.
          </div>
        )}
        {isLoading && reviews.length === 0 ? (
          <div className='flex flex-col items-center justify-center py-20 gap-4 text-[#8b949e]'>
            <div className='size-8 border-2 border-[#58a6ff]/30 border-t-[#58a6ff] rounded-full animate-spin' />
            <p>Loading review queue…</p>
          </div>
        ) : sortedReviews.length === 0 ? (
          <div className='text-center py-12 text-[#8b949e]'>
            <p>No quotes to review</p>
            {hasSummaryBacklog ? (
              <p className='text-ui-xs mt-2 max-w-md mx-auto'>
                Summary counts show {pendingCount.toLocaleString('en-IN')} pending quotes, but no detailed review cards are loaded in this view yet.
                Refresh if you expect new approvals to have arrived.
              </p>
            ) : (
              <p className='text-ui-xs mt-2'>Trips will appear here after options are prepared and ready for approval.</p>
            )}
          </div>
        ) : (
          <>
            {visibleReviews.map((review, index) => (
              <ReviewCard
                key={review.id || `review-${index}`}
                review={review}
                referenceNow={referenceNow}
                isSelected={selectedReviews.has(review.id)}
                onToggleSelect={handleToggleSelect}
                onApprove={handleApprove}
                onReject={handleReject}
                onRequestChanges={handleRequestChanges}
              />
            ))}
            {remainingReviewsCount > 0 && (
              <div className='flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#1c2128] bg-[#0f1115] px-4 py-3 text-ui-sm text-[#8b949e]'>
                <span>
                  Showing {visibleReviews.length.toLocaleString('en-IN')} of {sortedReviews.length.toLocaleString('en-IN')} quotes
                </span>
                <div className='flex items-center gap-2'>
                  <button
                    type='button'
                    onClick={() => setVisibleLimit((prev) => prev + 25)}
                    className='rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-1.5 text-ui-xs font-medium text-[#58a6ff] hover:bg-[#1c2431]'
                  >
                    Show {Math.min(25, remainingReviewsCount)} more
                  </button>
                  <button
                    type='button'
                    onClick={() => setVisibleLimit(sortedReviews.length)}
                    className='rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-1.5 text-ui-xs font-medium text-[#8b949e] hover:text-[#e6edf3]'
                  >
                    Show all ({sortedReviews.length.toLocaleString('en-IN')})
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Bulk Action Confirmation Modal */}
      {bulkActionType && (
        <div className='fixed inset-0 bg-[#0d1117]/80 backdrop-blur-sm flex items-center justify-center z-50 p-4'>
          <div className='bg-[#161b22] border border-[#30363d] rounded-2xl max-w-md w-full p-5 shadow-2xl space-y-4'>
            <h3 className='text-ui-base font-semibold text-[#e6edf3] capitalize'>
              Bulk {bulkActionType.replace('_', ' ')} ({selectedReviews.size} {selectedReviews.size === 1 ? 'quote' : 'quotes'})
            </h3>
            <p className='text-ui-sm text-[#8b949e]'>
              {bulkActionType === 'approve'
                ? 'Confirm bulk approval for the selected quotes.'
                : 'Please provide a reason for the selected quotes (required):'}
            </p>
            <textarea
              value={bulkNotes}
              onChange={(e) => setBulkNotes(e.target.value)}
              placeholder='Supervisor audit note / feedback…'
              rows={3}
              className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] placeholder:text-[#484f58] focus:outline-none focus:border-[#58a6ff]'
            />
            <div className='flex items-center justify-end gap-2 pt-2'>
              <button
                type='button'
                onClick={() => {
                  setBulkActionType(null);
                  setBulkNotes('');
                }}
                className='px-3 py-1.5 text-ui-sm text-[#8b949e] hover:text-[#e6edf3]'
              >
                Cancel
              </button>
              <button
                type='button'
                disabled={bulkActionType !== 'approve' && !bulkNotes.trim()}
                onClick={handleExecuteBulkAction}
                className={`px-4 py-1.5 rounded-lg text-ui-sm font-medium text-white transition-colors ${
                  bulkActionType === 'approve'
                    ? 'bg-[#3fb950] hover:bg-[#4bc95b]'
                    : bulkActionType === 'reject'
                      ? 'bg-[#f85149] hover:bg-[#ff6b6b]'
                      : 'bg-[#d29922] hover:bg-[#e3a532]'
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                Confirm {bulkActionType.replace('_', ' ')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Processing Overlay */}
      {isProcessing && (
        <div className='fixed inset-0 bg-[#0d1117]/80 flex items-center justify-center z-50'>
          <div className='flex items-center gap-3 text-[#e6edf3] font-inter'>
            <div className='size-6 border-2 border-[#58a6ff]/30 border-t-[#58a6ff] rounded-full animate-spin' />
            Processing decision…
          </div>
        </div>
      )}
    </div>
  );
}
