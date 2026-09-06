// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SuppliersPage from '../PageClient';

vi.mock('@/hooks/useTrips', () => ({
  useTrips: () => ({
    data: [
      {
        id: 'trip_bc27d5cadcae',
        destination: 'Cape Town',
        type: 'business',
        origin: 'Mumbai',
        budget: '$5,000',
        dateWindow: 'October 2026',
        tripPurpose: 'business',
        party: 18,
        validation: { is_valid: true, errors: [], warnings: [] },
        decision: {
          decision_state: 'ASK_FOLLOWUP',
          hard_blockers: [],
          soft_blockers: [],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          branch_options: [],
          rationale: {},
          confidence: {},
          commercial_decision: 'NONE',
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
          agentOperations: {
            supplierRiskLevel: 'medium',
            supplierIntelligenceSnapshot: { suppliers: ['Fast Lodge DMC'] },
          },
        }
      : null,
  }),
}));

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

describe('SuppliersPage', () => {
  it('renders the suppliers shell and trip context', () => {
    render(<SuppliersPage />);

    expect(screen.getByText(/Suppliers & DMC Directory/i)).toBeInTheDocument();
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getByTestId('suppliers-preview-banner')).toHaveTextContent(/not evidence that a supplier contract exists/i);
    expect(screen.getByTestId('suppliers-trip-select')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Cape Town business trip · Updated recently · BC27/i })).toBeInTheDocument();
    expect(screen.getByText(/medium \(not supplier-verified\)/i)).toBeInTheDocument();
    expect(screen.getByText(/stored trip snapshot \(freshness unknown\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Showing 6 sample records/i)).toBeInTheDocument();
    expect(screen.queryByText(/Verified Partners/i)).not.toBeInTheDocument();
  });
});
