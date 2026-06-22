import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import OwnerReviewsPage from '../page';

let reviewsMockData: any[] = [];

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
    state: {
      review_counts: {},
      pending_review_count: 0,
      total_pending_review_value: 0,
    },
  }),
}));

describe('OwnerReviewsPage', () => {
  it('renders a page-level return link back to overview', () => {
    reviewsMockData = [];
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
});
