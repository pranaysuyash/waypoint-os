import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import OpsPanel from '../OpsPanel';

const mockStore = {
  result_validation: null as unknown,
};

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
}));

const READINESS_WITH_TIERS = {
  highest_ready_tier: 'quote_ready',
  suggested_next_stage: 'shortlist',
  should_auto_advance_stage: false,
  missing_for_next: ['budget_max'],
  tiers: {
    intake_minimum: {
      tier: 'intake_minimum',
      ready: true,
      met: ['destination_candidates', 'date_window'],
      unmet: [],
    },
    quote_ready: {
      tier: 'quote_ready',
      ready: true,
      met: ['destination_candidates', 'date_window', 'party_size', 'budget_min'],
      unmet: [],
    },
    proposal_ready: {
      tier: 'proposal_ready',
      ready: false,
      met: ['destination_candidates'],
      unmet: ['traveler_bundle', 'fees'],
    },
  },
};

const READINESS_WITH_VISA_SIGNAL = {
  ...READINESS_WITH_TIERS,
  signals: {
    visa_concerns_present: true,
  },
};

const READINESS_WITHOUT_SIGNALS = {
  ...READINESS_WITH_TIERS,
};

describe('OpsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockStore.result_validation = null;
  });

  it('shows empty state when no readiness data', () => {
    render(<OpsPanel trip={null} />);
    expect(screen.getByTestId('ops-panel-empty')).toBeInTheDocument();
  });

  it('shows readiness tiers when data is present', () => {
    mockStore.result_validation = { readiness: READINESS_WITH_TIERS };
    render(<OpsPanel trip={null} />);
    expect(screen.getByTestId('ops-tiers')).toBeInTheDocument();
    expect(screen.getByTestId('ops-tier-intake_minimum')).toBeInTheDocument();
    expect(screen.getByTestId('ops-tier-quote_ready')).toBeInTheDocument();
    expect(screen.getByTestId('ops-tier-proposal_ready')).toBeInTheDocument();
  });

  it('shows visa/passport concern when signals.visa_concerns_present is true', () => {
    mockStore.result_validation = { readiness: READINESS_WITH_VISA_SIGNAL };
    render(<OpsPanel trip={null} />);
    expect(screen.getByTestId('ops-signal-visa-concern')).toBeInTheDocument();
  });

  it('omits signal section when no signals', () => {
    mockStore.result_validation = { readiness: READINESS_WITHOUT_SIGNALS };
    render(<OpsPanel trip={null} />);
    expect(screen.queryByTestId('ops-signals')).not.toBeInTheDocument();
  });

  it('falls back to trip.validation.readiness when store has no validation', () => {
    mockStore.result_validation = null;
    const trip = {
      validation: { readiness: READINESS_WITH_TIERS },
    } as never;
    render(<OpsPanel trip={trip} />);
    expect(screen.getByTestId('ops-tiers')).toBeInTheDocument();
  });
});
