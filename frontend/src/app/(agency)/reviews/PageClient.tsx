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
  DollarSign,
  MapPin,
  ChevronRight,
  Filter,
  MoreHorizontal,
} from 'lucide-react';
import { useReviews } from '@/hooks/useGovernance';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { getTripRoute } from '@/lib/routes';
import { StatusBadge } from '@/components/ui/status-badge';
import type { TripReview, ReviewStatus, RiskFlag } from '@/types/governance';

const REVIEW_STATUS_MAP = {
  pending:         { label: 'Pending Review',   color: '#d29922', icon: Clock },
  revision_needed: { label: 'Revision Needed',  color: '#e36f2f', icon: RefreshCw },
  approved:        { label: 'Approved',         color: '#3fb950', icon: CheckCircle },
  rejected:        { label: 'Rejected',         color: '#f85149', icon: XCircle },
  escalated:       { label: 'Escalated',        color: '#a371f7', icon: AlertTriangle },
};

const DAY_MS = 1000 * 60 * 60 * 24;

function getDaysWaiting(submittedAt: string, referenceNow: number) {
  return Math.floor((referenceNow - new Date(submittedAt).getTime()) / DAY_MS);
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
  onApprove,
  onReject,
  onRequestChanges,
}: {
  review: TripReview;
  referenceNow: number;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onRequestChanges: (id: string) => void;
}) {
  const [showActions, setShowActions] = useState(false);
  const daysWaiting = getDaysWaiting(review.submittedAt, referenceNow);
  
  const isUrgent = daysWaiting > 2 || review.riskFlags.includes('high_value');
  
  return (
    <div
      className={`rounded-xl border p-4 transition-all hover:border-[#30363d] ${
        isUrgent ? 'border-[#f85149]/30 bg-[#f85149]/5' : 'border-[#1c2128] bg-[#0f1115]'
      }`}
    >
      <div className='flex items-start justify-between gap-4'>
        <div className='flex-1 min-w-0'>
          <div className='flex items-center gap-2 mb-1'>
            {isUrgent && <AlertTriangle className='size-4 text-[#f85149] shrink-0' />}
            <span className='text-ui-sm text-[#8b949e] font-mono'>{review.tripReference}</span>
            <StatusBadge status={review.status} map={REVIEW_STATUS_MAP} />
          </div>
          
          <h3 className='text-ui-base font-semibold text-[#e6edf3] mb-1'>
            {review.destination}
          </h3>
          
          <div className='flex items-center gap-4 text-ui-xs text-[#8b949e] mb-2'>
            <span className='flex items-center gap-1'>
              <MapPin className='size-3' /> {review.tripType}
            </span>
            <span className='flex items-center gap-1'>
              <User className='size-3' /> {review.partySize} pax
            </span>
            <span className='flex items-center gap-1'>
              <DollarSign className='size-3' /> 
              ${review.value.toLocaleString()}
            </span>
            <span className='flex items-center gap-1'>
              <Clock className='size-3' /> {daysWaiting}d waiting
            </span>
          </div>
          
          <p className='text-ui-sm text-[#8b949e] mb-2'>
            <span className='text-[#e6edf3]'>Reason for review:</span> {review.reason}
          </p>
          
          {review.agentNotes && (
            <blockquote className='text-ui-sm text-[#8b949e] border-l-2 border-[#30363d] pl-3 italic'>
              &ldquo;{review.agentNotes}&rdquo;
              <span className='text-ui-xs text-[#484f58] not-italic ml-2'>- {review.agentName}</span>
            </blockquote>
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
              <button
                onClick={() => {
                  onApprove(review.id);
                  setShowActions(false);
                }}
                className='flex items-center gap-1 px-3 py-1.5 bg-[#3fb950] text-white rounded-lg text-ui-sm font-medium hover:bg-[#4bc95b] transition-colors'
              >
                <CheckCircle className='size-3.5' /> Approve
              </button>
              
              <button
                onClick={() => {
                  onRequestChanges(review.id);
                  setShowActions(false);
                }}
                className='flex items-center gap-1 px-3 py-1.5 bg-[#d29922] text-white rounded-lg text-ui-sm font-medium hover:bg-[#e3a532] transition-colors'
              >
                <RefreshCw className='size-3.5' /> Request Changes
              </button>
              
              <button
                onClick={() => {
                  onReject(review.id);
                  setShowActions(false);
                }}
                className='flex items-center gap-1 px-3 py-1.5 bg-[#f85149] text-white rounded-lg text-ui-sm font-medium hover:bg-[#ff6b6b] transition-colors'
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
              href={getTripRoute(review.tripId)}
              className='flex items-center justify-center gap-1 text-ui-xs text-[#58a6ff] hover:text-[#79b8ff] transition-colors'
            >
              View Details <ChevronRight className='size-3' />
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
  const [referenceNow] = useState(() => Date.now());
  const { data: reviews, isLoading, error, refetch, submitAction } = useReviews();
  const [isProcessing, setIsProcessing] = useState(false);

  // Filter reviews
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

  const handleAction = useCallback(async (id: string, action: 'approve' | 'reject' | 'request_changes', notes: string = '') => {
    setIsProcessing(true);
    try {
      const internalAction = action === 'approve' ? 'approve' : action === 'reject' ? 'reject' : 'request_changes';
      await submitAction({
        reviewId: id,
        action: internalAction as any,
        notes: notes || `Owner ${action} action submitted via dashboard.`
      });
      await refetch();
    } catch (err) {
      console.error(`Failed to ${action} review:`, err);
      alert(`Error: Failed to process ${action}. Please try again.`);
    } finally {
      setIsProcessing(false);
    }
  }, [submitAction, refetch]);

  const handleApprove = (id: string) => handleAction(id, 'approve');
  const handleReject = (id: string) => handleAction(id, 'reject');
  const handleRequestChanges = (id: string) => handleAction(id, 'request_changes');

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

  const pendingCount = reviews.filter((r) => r.status === 'pending').length;
  const approvedCount = reviews.filter((r) => r.status === 'approved').length;
  const rejectedCount = reviews.filter((r) => r.status === 'rejected').length;
  const escalatedCount = reviews.filter((r) => r.status === 'escalated').length;
  const totalValue = reviews
    .filter((r) => r.status === 'pending')
    .reduce((sum, r) => sum + r.value, 0);

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      <BackToOverviewLink />
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
          
          <button className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#8b949e] rounded-lg text-ui-sm hover:text-[#e6edf3] transition-colors'>
            <Filter className='size-4' /> Filters
          </button>
        </div>
      </header>

      {/* Stats */}
      <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e]'>Pending Quotes</span>
          <div className='text-ui-2xl font-bold text-[#e6edf3] mt-1'>{pendingCount}</div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e] font-inter'>Total Value in Progress</span>
          <div className='text-ui-2xl font-bold text-[#e6edf3] mt-1'>
            ${(totalValue / 1000).toFixed(1)}k
          </div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e]'>Approved Quotes</span>
          <div className='text-ui-2xl font-bold text-[#3fb950] mt-1'>{approvedCount}</div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 font-inter'>
          <span className='text-ui-sm text-[#8b949e]'>Escalated</span>
          <div className='text-ui-2xl font-bold text-[#58a6ff] mt-1'>{escalatedCount}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className='flex items-center gap-2 border-b border-[#1c2128] pb-3'>
        {[
          { key: 'all', label: 'All', count: reviews.length },
          { key: 'pending', label: 'Pending', count: pendingCount },
          { key: 'approved', label: 'Approved', count: approvedCount },
          { key: 'escalated', label: 'Escalated', count: escalatedCount },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setStatusFilter(tab.key as ReviewStatus | 'all')}
            className={`px-4 py-2 rounded-lg text-ui-sm font-medium transition-colors ${
              statusFilter === tab.key
                ? 'bg-[#161b22] text-[#e6edf3]'
                : 'text-[#8b949e] hover:text-[#e6edf3]'
            }`}
          >
            {tab.label}
            <span className='ml-2 text-ui-xs text-[#484f58]'>{tab.count}</span>
          </button>
        ))}
      </div>

      {/* Review Queue */}
      <div className='space-y-3'>
        {isLoading && reviews.length === 0 ? (
          <div className='flex flex-col items-center justify-center py-20 gap-4 text-[#8b949e]'>
            <div className='size-8 border-2 border-[#58a6ff]/30 border-t-[#58a6ff] rounded-full animate-spin' />
            <p>Loading review queue…</p>
          </div>
        ) : sortedReviews.length === 0 ? (
          <div className='text-center py-12 text-[#8b949e]'>
            <p>No quotes to review</p>
            <p className='text-ui-xs mt-2'>Trips will appear here after options are prepared and ready for approval.</p>
          </div>
        ) : (
          sortedReviews.map((review, index) => (
            <ReviewCard
              key={review.id || `review-${index}`}
              review={review}
              referenceNow={referenceNow}
              onApprove={handleApprove}
              onReject={handleReject}
              onRequestChanges={handleRequestChanges}
            />
          ))
        )}
      </div>

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
