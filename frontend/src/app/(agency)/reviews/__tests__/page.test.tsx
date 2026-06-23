import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import OwnerReviewsPage from '../page';

let reviewsMockData: any[] = [];
let unifiedStateMock = {
  review_counts: {},
  pending_review_count: 0,
  total_pending_review_value: 0,
};

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/useGovernance', () => ({
  useReviews: () => ({
    data: reviewsMockData,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    submitAction: vi.fn(),
  }),
}));

vi.mock('@/hooks/useUnifiedState', () => ({
  useUnifiedState: () => ({
    state: unifiedStateMock,
  }),
}));

describe('OwnerReviewsPage', () => {
  beforeEach(() => {
    reviewsMockData = [];
    unifiedStateMock = {
      review_counts: {},
      pending_review_count: 0,
      total_pending_review_value: 0,
    };
  });

  it('renders a page-level return link back to overview', () => {
    render(<OwnerReviewsPage />);

    expect(screen.getByRole('link', { name: /back to overview/i })).toHaveAttribute('href', '/overview');
  });

  it('does not surface unknown destination wording in a review card', () => {
    reviewsMockData = [{
      id: 'review-1',
      tripId: 'trip-1',
      tripReference: 'TRIP-1',
      destination: 'Unknown',
      tripType: 'leisure',
      partySize: 2,
      dateWindow: 'June 2026',
      value: 1500,
      currency: 'USD',
      agentId: 'agent-1',
      agentName: 'Agent',
      submittedAt: '2026-06-01T00:00:00Z',
      status: 'pending',
      reason: 'Needs review',
      riskFlags: [],
    }];

    render(<OwnerReviewsPage />);

    expect(screen.getByText('Trip details incomplete')).toBeInTheDocument();
    expect(screen.queryByText(/Unknown leisure/i)).not.toBeInTheDocument();
  });

  it('renders review value using the review currency code for global agencies', () => {
    reviewsMockData = [{
      id: 'review-2',
      tripId: 'trip-2',
      tripReference: 'TRIP-2',
      destination: 'Zanzibar',
      tripType: 'leisure',
      partySize: 4,
      dateWindow: 'August 2026',
      value: 2500000,
      currency: 'NGN',
      agentId: 'agent-2',
      agentName: 'Agent',
      submittedAt: '2026-06-01T00:00:00Z',
      status: 'pending',
      reason: 'Needs review',
      riskFlags: [],
    }];

    render(<OwnerReviewsPage />);

    expect(screen.getByText(/₦2,500,000 NGN/i)).toBeInTheDocument();
    expect(screen.queryByText(/\$2,500,000/)).not.toBeInTheDocument();
  });

  it('explains when summary backlog exists but detailed review cards are empty', () => {
    unifiedStateMock = {
      review_counts: { pending: 22 },
      pending_review_count: 22,
      total_pending_review_value: 0,
    };

    render(<OwnerReviewsPage />);

    expect(screen.getByText(/summary counts show 22 pending quotes/i)).toBeInTheDocument();
    expect(screen.getByText(/no detailed review cards are loaded/i)).toBeInTheDocument();
  });

  it('explains when the loaded review list is smaller than the summary backlog', () => {
    reviewsMockData = [
      {
        id: 'review-1',
        tripId: 'trip-1',
        tripReference: 'TRIP-1',
        destination: 'Bali',
        tripType: 'leisure',
        partySize: 2,
        dateWindow: 'July 2026',
        value: 1500,
        currency: 'USD',
        agentId: 'agent-1',
        agentName: 'Agent',
        submittedAt: '2026-06-01T00:00:00Z',
        status: 'pending',
        reason: 'Needs review',
        riskFlags: [],
      },
    ];
    unifiedStateMock = {
      review_counts: { pending: 47 },
      pending_review_count: 47,
      total_pending_review_value: 0,
    };

    render(<OwnerReviewsPage />);

    expect(screen.getByText(/showing 1 loaded quotes while the summary reports 47 pending quotes/i)).toBeInTheDocument();
    expect(screen.getByText(/refresh if you expect the queue to have grown/i)).toBeInTheDocument();
  });
});
