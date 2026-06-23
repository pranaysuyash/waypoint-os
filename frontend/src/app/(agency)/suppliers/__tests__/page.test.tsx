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

    expect(screen.getByText('Suppliers')).toBeInTheDocument();
    expect(screen.getByTestId('suppliers-trip-select')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Cape Town business trip · Updated recently · BC27/i })).toBeInTheDocument();
    expect(screen.getByText(/Current supplier risk: medium/i)).toBeInTheDocument();
    expect(screen.getByText(/supplier intelligence snapshot is available/i)).toBeInTheDocument();
  });
});
