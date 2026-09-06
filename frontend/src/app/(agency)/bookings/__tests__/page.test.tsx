// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
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
  it('renders the bookings command hub as an explicitly labelled sample surface', () => {
    render(<BookingsPageClient />);

    expect(screen.getByText('Bookings & Fulfillment Command')).toBeInTheDocument();
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getByText('Sample Booking Records')).toBeInTheDocument();
    expect(screen.getByText('No live GDS/DMC connection')).toBeInTheDocument();
    expect(screen.getByText('Supplier Holds')).toBeInTheDocument();
    expect(screen.getByText('Unavailable')).toBeInTheDocument();
    expect(screen.getByText('Provider Artifacts')).toBeInTheDocument();
    expect(screen.getAllByText('Not connected')).toHaveLength(2);
    expect(screen.getAllByText('Sample / unverified')).toHaveLength(4);

    expect(screen.queryByText('Confirmed Supplier Bookings & PNR Ledger')).not.toBeInTheDocument();
    expect(screen.queryByText('Live GDS & DMC Direct Sync')).not.toBeInTheDocument();
    expect(screen.queryByText('48h Zero-Cost Hold (Expires in 22h)')).not.toBeInTheDocument();
  });

  it('keeps local document parsing unverified and view-only', async () => {
    render(<BookingsPageClient />);

    const extractBtn = screen.getByRole('button', { name: /Preview Booking Document/i });
    fireEvent.click(extractBtn);

    const dialog = screen.getByRole('dialog', { name: 'Preview Booking Document' });
    expect(within(dialog).getByText('Preview Booking Document')).toBeInTheDocument();
    expect(within(dialog).getByPlaceholderText(/Booking Reference: AF79KZ/i)).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Air France PNR' }));
    fireEvent.click(within(dialog).getByRole('button', { name: 'Preview Parsed Details' }));

    expect(await within(dialog).findByText('Local parse preview — not independently verified')).toBeInTheDocument();
    expect(within(dialog).getByText('AF79KZ')).toBeInTheDocument();
    expect(within(dialog).getByText('Source reference (unverified):')).toBeInTheDocument();
    expect(within(dialog).getByText('Illustrative value:')).toBeInTheDocument();
    expect(within(dialog).queryByText(/Extraction Successful/i)).not.toBeInTheDocument();
    expect(within(dialog).queryByText('Record & Add to Ledger')).not.toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Add Sample to This View' }));
    expect(screen.getAllByText('Sample / unverified')).toHaveLength(5);
    expect(screen.getByText('Local browser parse preview')).toBeInTheDocument();
  });
});
