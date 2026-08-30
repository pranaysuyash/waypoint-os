// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import BookingsPageClient from '../PageClient';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/bookings',
  useSearchParams: () => new URLSearchParams('tripId=trip_456'),
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrips: () => ({
    data: [
      {
        id: 'trip_456',
        destination: 'South Africa',
        type: 'luxury',
        origin: 'Mumbai',
        budget: '$7,200',
        dateWindow: 'Nov 2026',
        tripPurpose: 'vacation',
        party: 2,
        validation: { is_valid: true, errors: [], warnings: [] },
        decision: {
          decision_state: 'CONFIRMED',
          hard_blockers: [],
          soft_blockers: [],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          branch_options: [],
          rationale: {},
          confidence: {},
          commercial_decision: 'CONFIRMED',
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
          destination: 'South Africa',
          dateWindow: 'Nov 2026',
          party: 2,
          budget: '$7,200',
          state: 'Confirmed',
        }
      : null,
  }),
}));

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

describe('BookingsPageClient', () => {
  it('renders the bookings command hub and opens auto-extract modal', () => {
    render(<BookingsPageClient />);

    expect(screen.getByText('Bookings & Fulfillment Command')).toBeInTheDocument();
    expect(screen.getByText('Confirmed Supplier Bookings & PNR Ledger')).toBeInTheDocument();
    expect(screen.getByText(/Auto-Extract Booking Voucher/i)).toBeInTheDocument();

    const extractBtn = screen.getByText(/Auto-Extract Booking Voucher/i);
    fireEvent.click(extractBtn);

    expect(screen.getByText(/Auto-Extract Voucher & PNR/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Booking Reference: AF79KZ/i)).toBeInTheDocument();
  });
});
