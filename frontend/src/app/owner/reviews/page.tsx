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
import type { TripReview, ReviewStatus, RiskFlag } from '@/types/governance';

// ============================================================================
// MOCK DATA - Replace with real API calls
// ============================================================================

const MOCK_REVIEWS: TripReview[] = [
  {
    id: 'rev-001',
    tripId: 'trip-001',
    tripReference: 'TRP-2026-MSC-0422',
    destination: 'Moscow, Russia',
    tripType: 'Solo Adventure',
    partySize: 1,
    dateWindow: 'Jun 10–20, 2026',
    value: 12400,
    currency: 'USD',
    agentId: 'agent-001',
    agentName: 'Sarah Chen',
    submittedAt: '2026-04-14T10:30:00Z',
    status: 'pending',
    reason: 'High-value trip to destination requiring special visas',
    agentNotes: 'Client has visa concerns, needs guidance on documentation requirements. Has traveled extensively before.',
    riskFlags: ['high_value', 'unusual_destination', 'visa_required'],
  },
  {
    id: 'rev-002',
    tripId: 'trip-002',
    tripReference: 'TRP-2026-AND-0420',
    destination: 'Andaman Islands',
    tripType: 'Honeymoon',
    partySize: 2,
    dateWindow: 'May 15–22, 2026',
    value: 8200,
    currency: 'USD',
    agentId: 'agent-002',
    agentName: 'Mike Johnson',
    submittedAt: '2026-04-12T14:15:00Z',
    status: 'pending',
    reason: 'Supplier quote pending for 48+ hours',
    agentNotes: 'Waiting on Andaman resort confirmation. Client flexible on dates.',
    riskFlags: ['supplier_delay'],
  },
  {
    id: 'rev-003',
    tripId: 'trip-003',
    tripReference: 'TRP-2026-EMR-0418',
    destination: 'Dubai, UAE',
    tripType: 'Corporate Retreat',
    partySize: 8,
    dateWindow: 'Jul 3–7, 2026',
    value: 15600,
    currency: 'USD',
    agentId: 'agent-001',
    agentName: 'Sarah Chen',
    submittedAt: '2026-04-10T09:00:00Z',
    status: 'pending',
    reason: 'Group size exceeds standard approval threshold',
    agentNotes: 'Corporate client, needs meeting facilities + leisure activities. Budget approved by client.',
    riskFlags: ['high_value', 'complex_itinerary'],
  },
  {
    id: 'rev-004',
    tripId: 'trip-004',
    tripReference: 'TRP-2026-PAR-0415',
    destination: 'Paris, France',
    tripType: 'Anniversary',
    partySize: 2,
    dateWindow: 'Oct 14–21, 2026',
    value: 9500,
    currency: 'USD',
    agentId: 'agent-003',
    agentName: 'Alex Kim',
    submittedAt: '2026-04-08T16:45:00Z',
    status: 'pending',
    reason: 'Client requested owner involvement for luxury upgrades',
    agentNotes: 'Repeat client, wants to confirm luxury package details directly.',
    riskFlags: [],
  },
  {
    id: 'rev-005',
    tripId: 'trip-005',
    tripReference: 'TRP-2026-NYC-0410',
    destination: 'New York, USA',
    tripType: 'Family Vacation',
    partySize: 5,
    dateWindow: 'Dec 20–28, 2026',
    value: 18700,
    currency: 'USD',
    agentId: 'agent-002',
    agentName: 'Mike Johnson',
    submittedAt: '2026-04-05T11:20:00Z',
    status: 'pending',
    reason: 'High-value booking during peak holiday season',
    agentNotes: 'Christmas week, premium pricing. Client aware of costs.',
    riskFlags: ['high_value', 'tight_deadline'],
  },
];

// ============================================================================
// COMPONENTS
// ============================================================================

const StatusBadge = memo(function StatusBadge({ status }: { status: ReviewStatus }) {
  const styles = {
    pending: { bg: 'rgba(210,153,34,0.12)', color: '#d29922', label: 'Pending Review' },
    approved: { bg: 'rgba(63,185,80,0.12)', color: '#3fb950', label: 'Approved' },
    rejected: { bg: 'rgba(248,81,73,0.12)', color: '#f85149', label: 'Rejected' },
    escalated: { bg: 'rgba(88,166,255,0.12)', color: '#58a6ff', label: 'Escalated' },
  };
  
  const style = styles[status];
  
  return (
    <span
      className='inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium'
      style={{ background: style.bg, color: style.color }}
    >
      {status === 'pending' && <Clock className='w-3 h-3' />}
      {status === 'approved' && <CheckCircle className='w-3 h-3' />}
      {status === 'rejected' && <XCircle className='w-3 h-3' />}
      {status === 'escalated' && <AlertTriangle className='w-3 h-3' />}
      {style.label}
    </span>
  );
});

const RiskFlagBadge = memo(function RiskFlagBadge({ flag }: { flag: RiskFlag }) {
  const labels: Record<RiskFlag, string> = {
    high_value: 'High Value',
    unusual_destination: 'Unusual',
    tight_deadline: 'Tight Deadline',
    complex_itinerary: 'Complex',
    visa_required: 'Visa Required',
    supplier_delay: 'Supplier Delay',
  };
  
  return (
    <span className='inline-block px-1.5 py-0.5 bg-[#f85149]/10 text-[#f85149] text-xs rounded'>
      {labels[flag]}
    </span>
  );
});

const ReviewCard = memo(function ReviewCard({
  review,
  onApprove,
  onReject,
  onRequestChanges,
}: {
  review: TripReview;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onRequestChanges: (id: string) => void;
}) {
  const [showActions, setShowActions] = useState(false);
  
  const daysWaiting = Math.floor(
    (Date.now() - new Date(review.submittedAt).getTime()) / (1000 * 60 * 60 * 24)
  );
  
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
            {isUrgent && <AlertTriangle className='w-4 h-4 text-[#f85149] shrink-0' />}
            <span className='text-sm text-[#8b949e] font-mono'>{review.tripReference}</span>
            <StatusBadge status={review.status} />
          </div>
          
          <h3 className='text-base font-semibold text-[#e6edf3] mb-1'>
            {review.destination}
          </h3>
          
          <div className='flex items-center gap-4 text-xs text-[#8b949e] mb-2'>
            <span className='flex items-center gap-1'>
              <MapPin className='w-3 h-3' /> {review.tripType}
            </span>
            <span className='flex items-center gap-1'>
              <User className='w-3 h-3' /> {review.partySize} pax
            </span>
            <span className='flex items-center gap-1'>
              <DollarSign className='w-3 h-3' /> 
              ${review.value.toLocaleString()}
            </span>
            <span className='flex items-center gap-1'>
              <Clock className='w-3 h-3' /> {daysWaiting}d waiting
            </span>
          </div>
          
          <p className='text-sm text-[#8b949e] mb-2'>
            <span className='text-[#e6edf3]'>Reason for review:</span> {review.reason}
          </p>
          
          {review.agentNotes && (
            <blockquote className='text-sm text-[#8b949e] border-l-2 border-[#30363d] pl-3 italic'>
              "{review.agentNotes}"
              <span className='text-xs text-[#484f58] not-italic ml-2'>— {review.agentName}</span>
            </blockquote>
          )}
          
          {review.riskFlags.length > 0 && (
            <div className='flex items-center gap-2 mt-2'>
              <span className='text-xs text-[#8b949e]'>Risk flags:</span>
              {review.riskFlags.map((flag) => (
                <RiskFlagBadge key={flag} flag={flag} />
              ))}
            </div>
          )}
        </div>
        
        <div className='flex flex-col gap-2'>
          {!showActions ? (
            <button
              onClick={() => setShowActions(true)}
              className='px-3 py-1.5 bg-[#58a6ff] text-[#0d1117] rounded-lg text-sm font-medium hover:bg-[#6eb5ff] transition-colors'
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
                className='flex items-center gap-1 px-3 py-1.5 bg-[#3fb950] text-white rounded-lg text-sm font-medium hover:bg-[#4bc95b] transition-colors'
              >
                <CheckCircle className='w-3.5 h-3.5' /> Approve
              </button>
              
              <button
                onClick={() => {
                  onRequestChanges(review.id);
                  setShowActions(false);
                }}
                className='flex items-center gap-1 px-3 py-1.5 bg-[#d29922] text-white rounded-lg text-sm font-medium hover:bg-[#e3a532] transition-colors'
              >
                <RefreshCw className='w-3.5 h-3.5' /> Request Changes
              </button>
              
              <button
                onClick={() => {
                  onReject(review.id);
                  setShowActions(false);
                }}
                className='flex items-center gap-1 px-3 py-1.5 bg-[#f85149] text-white rounded-lg text-sm font-medium hover:bg-[#ff6b6b] transition-colors'
              >
                <XCircle className='w-3.5 h-3.5' /> Reject
              </button>
              
              <button
                onClick={() => setShowActions(false)}
                className='px-3 py-1.5 text-[#8b949e] text-sm hover:text-[#e6edf3] transition-colors'
              >
                Cancel
              </button>
            </div>
          )}
          
          <Link
            href={`/workbench?trip=${review.tripId}`}
            className='flex items-center justify-center gap-1 text-xs text-[#58a6ff] hover:text-[#79b8ff] transition-colors'
          >
            View Details <ChevronRight className='w-3 h-3' />
          </Link>
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
  const [selectedReviews, setSelectedReviews] = useState<Set<string>>(new Set());
  const [reviews, setReviews] = useState(MOCK_REVIEWS);
  const [isProcessing, setIsProcessing] = useState(false);

  // Filter reviews
  const filteredReviews = reviews.filter((r) => {
    if (statusFilter === 'all') return true;
    return r.status === statusFilter;
  });

  // Sort by urgency (days waiting desc, then value desc)
  const sortedReviews = [...filteredReviews].sort((a, b) => {
    const daysA = Math.floor((Date.now() - new Date(a.submittedAt).getTime()) / (1000 * 60 * 60 * 24));
    const daysB = Math.floor((Date.now() - new Date(b.submittedAt).getTime()) / (1000 * 60 * 60 * 24));
    if (daysA !== daysB) return daysB - daysA;
    return b.value - a.value;
  });

  const handleApprove = useCallback((id: string) => {
    setIsProcessing(true);
    // Simulate API call
    setTimeout(() => {
      setReviews((prev) =
        prev.map((r) =
          r.id === id ? { ...r, status: 'approved', reviewedAt: new Date().toISOString() } : r
        )
      );
      setIsProcessing(false);
    }, 500);
  }, []);

  const handleReject = useCallback((id: string) => {
    setIsProcessing(true);
    setTimeout(() => {
      setReviews((prev) =
        prev.map((r) =
          r.id === id ? { ...r, status: 'rejected', reviewedAt: new Date().toISOString() } : r
        )
      );
      setIsProcessing(false);
    }, 500);
  }, []);

  const handleRequestChanges = useCallback((id: string) => {
    setIsProcessing(true);
    setTimeout(() => {
      setReviews((prev) =
        prev.map((r) =
          r.id === id ? { ...r, status: 'escalated', reviewedAt: new Date().toISOString() } : r
        )
      );
      setIsProcessing(false);
    }, 500);
  }, []);

  const stats = {
    pending: reviews.filter((r) => r.status === 'pending').length,
    approved: reviews.filter((r) => r.status === 'approved').length,
    rejected: reviews.filter((r) => r.status === 'rejected').length,
    escalated: reviews.filter((r) => r.status === 'escalated').length,
    totalValue: reviews
      .filter((r) => r.status === 'pending')
      .reduce((sum, r) => sum + r.value, 0),
  };

  return (
    <div className='p-5 max-w-[1400px] mx-auto space-y-5'>
      {/* Header */}
      <header className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-2xl font-semibold text-[#e6edf3]'>Reviews & Approvals</h1>
          <p className='text-base text-[#8b949e] mt-0.5'>
            Approve high-value trips and manage escalations
          </p>
        </div>
        
        <div className='flex items-center gap-3'>
          <button className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#8b949e] rounded-lg text-sm hover:text-[#e6edf3] transition-colors'>
            <Filter className='w-4 h-4' /> Filters
          </button>
          
          <button className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#8b949e] rounded-lg text-sm hover:text-[#e6edf3] transition-colors'>
            <MoreHorizontal className='w-4 h-4' /> Bulk Actions
          </button>
        </div>
      </header>

      {/* Stats */}
      <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <span className='text-sm text-[#8b949e]'>Pending Review</span>
          <div className='text-2xl font-bold text-[#e6edf3] mt-1'>{stats.pending}</div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <span className='text-sm text-[#8b949e]'>Pipeline Value</span>
          <div className='text-2xl font-bold text-[#e6edf3] mt-1'>
            ${(stats.totalValue / 1000).toFixed(1)}k
          </div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <span className='text-sm text-[#8b949e]'>Approved (30d)</span>
          <div className='text-2xl font-bold text-[#3fb950] mt-1'>{stats.approved}</div>
        </div>
        
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
          <span className='text-sm text-[#8b949e]'>Escalated</span>
          <div className='text-2xl font-bold text-[#58a6ff] mt-1'>{stats.escalated}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className='flex items-center gap-2 border-b border-[#1c2128] pb-3'>
        {[
          { key: 'all', label: 'All', count: reviews.length },
          { key: 'pending', label: 'Pending', count: stats.pending },
          { key: 'approved', label: 'Approved', count: stats.approved },
          { key: 'escalated', label: 'Escalated', count: stats.escalated },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setStatusFilter(tab.key as ReviewStatus | 'all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === tab.key
                ? 'bg-[#161b22] text-[#e6edf3]'
                : 'text-[#8b949e] hover:text-[#e6edf3]'
            }`}
          >
            {tab.label}
            <span className='ml-2 text-xs text-[#484f58]'>{tab.count}</span>
          </button>
        ))}
      </div>

      {/* Review Queue */}
      <div className='space-y-3'>
        {sortedReviews.length === 0 ? (
          <div className='text-center py-12 text-[#8b949e]'>
            <p>No reviews match this filter.</p>
          </div>
        ) : (
          sortedReviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
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
          <div className='flex items-center gap-3 text-[#e6edf3]'>
            <div className='w-6 h-6 border-2 border-[#58a6ff]/30 border-t-[#58a6ff] rounded-full' />
            Processing...
          </div>
        </div>
      )}
    </div>
  );
}
