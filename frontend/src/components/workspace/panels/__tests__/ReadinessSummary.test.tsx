import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ReadinessSummary from '../ReadinessSummary';
import type { ReadinessAssessment } from '@/types/spine';

const FULL_READINESS: ReadinessAssessment = {
  highest_ready_tier: 'proposal_ready',
  suggested_next_stage: 'booking',
  should_auto_advance_stage: false,
  missing_for_next: [],
  tiers: {
    intake_minimum: {
      tier: 'intake_minimum',
      ready: true,
      met: ['destination_candidates', 'date_window'],
      unmet: [],
    },
    proposal_ready: {
      tier: 'proposal_ready',
      ready: false,
      met: ['destination_candidates'],
      unmet: ['budget_range', 'traveler_count'],
    },
  },
};

describe('ReadinessSummary', () => {
  it('shows empty notice when readiness is null', () => {
    render(<ReadinessSummary readiness={null} />);
    expect(screen.getByTestId('ops-readiness-empty')).toBeInTheDocument();
    expect(screen.getByText(/No readiness assessment available yet/)).toBeInTheDocument();
  });

  it('shows empty notice when readiness is undefined', () => {
    render(<ReadinessSummary readiness={undefined} />);
    expect(screen.getByTestId('ops-readiness-empty')).toBeInTheDocument();
  });

  it('does not show empty notice when readiness is present', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    expect(screen.queryByTestId('ops-readiness-empty')).not.toBeInTheDocument();
  });

  it('shows highest ready tier label', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    expect(screen.getByTestId('ops-highest-tier')).toBeInTheDocument();
    expect(screen.getByTestId('ops-highest-tier').textContent).toBe('proposal_ready');
  });

  it('shows tier details section when tiers present', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    expect(screen.getByTestId('ops-tiers')).toBeInTheDocument();
    expect(screen.getByTestId('ops-tier-intake_minimum')).toBeInTheDocument();
    expect(screen.getByTestId('ops-tier-proposal_ready')).toBeInTheDocument();
  });

  it('shows Ready badge for a ready tier', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    const intakeTier = screen.getByTestId('ops-tier-intake_minimum');
    expect(intakeTier.textContent).toContain('Ready');
  });

  it('shows Not ready badge for an unready tier', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    const proposalTier = screen.getByTestId('ops-tier-proposal_ready');
    expect(proposalTier.textContent).toContain('Not ready');
  });

  it('shows met and unmet fields within tier', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    const proposalTier = screen.getByTestId('ops-tier-proposal_ready');
    expect(proposalTier.textContent).toContain('budget_range');
    expect(proposalTier.textContent).toContain('traveler_count');
  });

  it('hides tiers section when no tiers', () => {
    const noTiers: ReadinessAssessment = { ...FULL_READINESS, tiers: {} };
    render(<ReadinessSummary readiness={noTiers} />);
    expect(screen.queryByTestId('ops-tiers')).not.toBeInTheDocument();
  });

  it('shows missing_for_next section when fields present', () => {
    const withMissing: ReadinessAssessment = {
      ...FULL_READINESS,
      missing_for_next: ['passport_number', 'date_of_birth'],
    };
    render(<ReadinessSummary readiness={withMissing} />);
    const missing = screen.getByTestId('ops-missing');
    expect(missing).toBeInTheDocument();
    expect(missing.textContent).toContain('passport_number');
    expect(missing.textContent).toContain('date_of_birth');
  });

  it('hides missing section when missing_for_next is empty', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    expect(screen.queryByTestId('ops-missing')).not.toBeInTheDocument();
  });

  it('shows visa/passport signal when visa_concerns_present is true', () => {
    const withVisa: ReadinessAssessment = {
      ...FULL_READINESS,
      signals: { visa_concerns_present: true },
    };
    render(<ReadinessSummary readiness={withVisa} />);
    expect(screen.getByTestId('ops-signals')).toBeInTheDocument();
    expect(screen.getByTestId('ops-signal-visa-concern')).toBeInTheDocument();
    expect(screen.getByText(/Visa\/Passport concern detected/)).toBeInTheDocument();
  });

  it('hides signals section when no signals', () => {
    render(<ReadinessSummary readiness={FULL_READINESS} />);
    expect(screen.queryByTestId('ops-signals')).not.toBeInTheDocument();
  });

  it('hides signals section when signals is empty object', () => {
    const emptySignals: ReadinessAssessment = { ...FULL_READINESS, signals: {} };
    render(<ReadinessSummary readiness={emptySignals} />);
    expect(screen.queryByTestId('ops-signals')).not.toBeInTheDocument();
  });

  it('hides visa signal when visa_concerns_present is false', () => {
    const noVisa: ReadinessAssessment = {
      ...FULL_READINESS,
      signals: { visa_concerns_present: false },
    };
    render(<ReadinessSummary readiness={noVisa} />);
    expect(screen.getByTestId('ops-signals')).toBeInTheDocument();
    expect(screen.queryByTestId('ops-signal-visa-concern')).not.toBeInTheDocument();
  });
});
