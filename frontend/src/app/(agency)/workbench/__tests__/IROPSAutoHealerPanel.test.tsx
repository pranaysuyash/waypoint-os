import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import IROPSAutoHealerPanel from '../IROPSAutoHealerPanel';

const previewResponse = {
  status: 'PREVIEW_ONLY',
  reality_tier: 'deterministic_preview',
  simulation: true,
  provider_connected: false,
  external_action: false,
  operational_write: false,
  effects: [],
  healing_plan: {
    incident_id: 'PREVIEW-IROPS-ABC123',
    delayed_node_title: 'BA 178 (LHR -> JFK)',
    delay_minutes: 180,
    ripple_summary: 'Local candidate graph preview; provider impact is unverified.',
    statutory_compensation: {
      amount_eur: null,
      estimated_amount_eur: 600,
      regulation: 'Eligibility requires jurisdiction and itinerary evidence.',
      status: 'UNVERIFIED_LEGAL_ESTIMATE',
    },
    counterfactual_options: [
      {
        tier: 'OPTION_A_MIN_DELAY',
        title: 'Illustrative alternative route',
        arrival_delta_minutes: 45,
        airline: 'Illustrative carrier candidate',
        cabin_class: 'Unverified cabin',
        action: 'REVIEW_ONLY — provider confirmation required',
        status: 'PREVIEW_ONLY',
        provider_connected: false,
        external_reference: null,
      },
    ],
    emergency_lodging_vcc: null,
    waiver_status: 'DRAFT_NOT_SENT',
    analysis_status: 'PREVIEW_ONLY',
    evidence_status: 'UNVERIFIED_LOCAL_INPUT',
    operator_next_step: 'Verify provider availability separately.',
  },
};

describe('IROPSAutoHealerPanel', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('presents the surface and action as preview-only', () => {
    render(<IROPSAutoHealerPanel />);

    expect(screen.getByRole('heading', { name: /irops recovery plan preview/i })).toBeInTheDocument();
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Preview only');
    expect(screen.getByText(/no carrier booking, payment, legal claim, vcc, or supplier message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate recovery preview/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /rebook|endorse|approve|waiver|issue/i })).not.toBeInTheDocument();
  });

  it('renders backend candidates without displaying legal, payment, or execution claims', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => previewResponse,
    } as Response);
    const user = userEvent.setup();

    render(<IROPSAutoHealerPanel />);
    await user.click(screen.getByRole('button', { name: /generate recovery preview/i }));

    await waitFor(() => expect(screen.getByTestId('irops-preview-result')).toBeInTheDocument());
    expect(screen.getByText('PREVIEW_ONLY')).toBeInTheDocument();
    expect(screen.getByText(/compensation eligibility/i)).toBeInTheDocument();
    expect(screen.getByText('Not assessed')).toBeInTheDocument();
    expect(screen.getByText(/lodging \/ payment/i)).toBeInTheDocument();
    expect(screen.getByText('Not issued')).toBeInTheDocument();
    expect(screen.getByText(/illustrative rerouting candidates/i)).toBeInTheDocument();
    expect(screen.getByText('Review only')).toBeInTheDocument();
    expect(screen.queryByText(/€600|cash claim|5424-|pnr|automatic|interline endorsement/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /rebook|endorse|approve|waiver|issue/i })).not.toBeInTheDocument();
  });

  it('keeps network failure in a truthful local preview mode', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('offline'));
    const user = userEvent.setup();

    render(<IROPSAutoHealerPanel />);
    await user.click(screen.getByRole('button', { name: /generate recovery preview/i }));

    await waitFor(() => expect(screen.getByText(/provider preview unavailable/i)).toBeInTheDocument());
    expect(screen.getByTestId('irops-preview-result')).toBeInTheDocument();
    expect(screen.getByText('Not assessed')).toBeInTheDocument();
    expect(screen.getByText('Not issued')).toBeInTheDocument();
    expect(screen.queryByText(/€600|cash claim|5424-|pnr|automatic|interline endorsement/i)).not.toBeInTheDocument();
  });
});
