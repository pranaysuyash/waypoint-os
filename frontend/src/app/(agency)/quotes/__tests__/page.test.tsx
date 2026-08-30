// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import QuotesPageClient from '../PageClient';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/quotes',
  useSearchParams: () => new URLSearchParams('tripId=trip_123'),
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrips: () => ({
    data: [
      {
        id: 'trip_123',
        destination: 'Cape Town',
        type: 'luxury',
        origin: 'London',
        budget: ',500',
        dateWindow: 'November 2026',
        tripPurpose: 'vacation',
        party: 2,
        validation: { is_valid: true, errors: [], warnings: [] },
        decision: {
          decision_state: 'PROPOSAL_READY',
          hard_blockers: [],
          soft_blockers: [],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          branch_options: [],
          rationale: {},
          confidence: {},
          commercial_decision: 'RECOMMEND_UPGRADE',
          budget_breakdown: null,
        },
      },
    ],
    isLoading: false,
  }),
  useTrip: (id: string | null) => ({
    data: id
      ? {
          id,
          destination: 'Cape Town',
          party: 2,
          budget: ',500',
          status: 'PROPOSAL_READY',
        }
      : null,
  }),
}));

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

describe('QuotesPageClient', () => {
  it('renders the quotes studio with multi-tier comparison matrix', () => {
    render(<QuotesPageClient />);

    expect(screen.getByText('Quotes & Commercial Proposals')).toBeInTheDocument();
    expect(screen.getByText('Multi-Tier Quote Comparison Matrix')).toBeInTheDocument();
    expect(screen.getByText('Signature Curator')).toBeInTheDocument();
    expect(screen.getByText('Essential Saver')).toBeInTheDocument();
    expect(screen.getByText('Ultra Prestige Suite')).toBeInTheDocument();
    expect(screen.getByText(/Live Margin & Fee Modeling/i)).toBeInTheDocument();
    expect(screen.getByText(/Copy Interactive Web Link/i)).toBeInTheDocument();
  });
});
