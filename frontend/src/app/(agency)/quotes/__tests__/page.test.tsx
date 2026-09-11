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
  });
});

describe('QuotesPageClient honesty (FND-0260)', () => {
  it('badges the page as sample data and explains nothing is persisted or sent', () => {
    render(<QuotesPageClient />);

    // Canonical GM-01 sample-data badge next to the page title.
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');

    // The illustrative-model banner explains exactly what is fake.
    const banner = screen.getByTestId('quotes-sample-banner');
    expect(banner).toHaveTextContent('Illustrative pricing model — not real quotes');
    expect(banner).toHaveTextContent('No quote has been created, persisted, or sent to a client');

    // No quote lifecycle is fabricated: statuses render as draft, not sent/reviewed.
    expect(screen.queryByText(/^sent$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^under review$/i)).not.toBeInTheDocument();
  });

  it('never offers a copyable client link for an unpersisted quote', () => {
    render(<QuotesPageClient />);

    // The dead-domain share affordance is gone; the link buttons are disabled.
    expect(document.body.innerHTML).not.toContain('waypoint.agency');
    const shareButtons = screen.getAllByTestId('quotes-share-disabled');
    expect(shareButtons.length).toBeGreaterThan(0);
    for (const button of shareButtons) {
      expect(button).toBeDisabled();
    }
    expect(screen.getByTestId('quotes-client-link-disabled')).toBeDisabled();
    expect(
      screen.getByText('Client Web Link — unavailable for illustrative quotes'),
    ).toBeInTheDocument();
  });
});
