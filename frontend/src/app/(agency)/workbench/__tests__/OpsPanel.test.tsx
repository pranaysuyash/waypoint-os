import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OpsPanel from '../OpsPanel';

const mockStore = {
  result_validation: null as unknown,
};

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
}));

const mockApi = {
  getBookingData: vi.fn(),
  updateBookingData: vi.fn(),
  getCollectionLink: vi.fn(),
  generateCollectionLink: vi.fn(),
  revokeCollectionLink: vi.fn(),
  getPendingBookingData: vi.fn(),
  acceptPendingBookingData: vi.fn(),
  rejectPendingBookingData: vi.fn(),
};

vi.mock('@/lib/api-client', () => ({
  getBookingData: (...args: unknown[]) => mockApi.getBookingData(...args),
  updateBookingData: (...args: unknown[]) => mockApi.updateBookingData(...args),
  getCollectionLink: (...args: unknown[]) => mockApi.getCollectionLink(...args),
  generateCollectionLink: (...args: unknown[]) => mockApi.generateCollectionLink(...args),
  revokeCollectionLink: (...args: unknown[]) => mockApi.revokeCollectionLink(...args),
  getPendingBookingData: (...args: unknown[]) => mockApi.getPendingBookingData(...args),
  acceptPendingBookingData: (...args: unknown[]) => mockApi.acceptPendingBookingData(...args),
  rejectPendingBookingData: (...args: unknown[]) => mockApi.rejectPendingBookingData(...args),
}));

const READINESS = {
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
  },
};

function tripAtStage(stage: string) {
  return { id: 'trip_1', stage, validation: { readiness: READINESS } } as never;
}

describe('OpsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockStore.result_validation = null;
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: null,
      updated_at: null,
      stage: 'proposal',
      readiness: {},
    });
    mockApi.getCollectionLink.mockRejectedValue(new Error('not found'));
    mockApi.getPendingBookingData.mockRejectedValue(new Error('not found'));
  });

  it('shows empty state when no readiness data', () => {
    render(<OpsPanel trip={null} />);
    expect(screen.getByTestId('ops-panel-empty')).toBeInTheDocument();
  });

  it('shows collection link section at proposal stage', async () => {
    mockStore.result_validation = { readiness: READINESS };
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
    });
  });

  it('shows collection link section at booking stage', async () => {
    mockStore.result_validation = { readiness: READINESS };
    render(<OpsPanel trip={tripAtStage('booking')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-collection-link')).toBeInTheDocument();
    });
  });

  it('hides collection link at discovery stage', async () => {
    mockStore.result_validation = { readiness: READINESS };
    render(<OpsPanel trip={tripAtStage('discovery')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-booking-data')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('ops-collection-link')).not.toBeInTheDocument();
  });

  it('shows active link hint when GET returns has_active_token', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getCollectionLink.mockResolvedValue({
      has_active_token: true,
      token_id: 'tok_1',
      expires_at: '2026-05-11T00:00:00Z',
      status: 'active',
      has_pending_submission: false,
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-link-active-hint')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
  });

  it('generates collection link and shows URL', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.generateCollectionLink.mockResolvedValue({
      token_id: 'tok_1',
      collection_url: 'https://example.com/booking-collection/abc123',
      expires_at: '2026-05-11T00:00:00Z',
      trip_id: 'trip_1',
      status: 'active',
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const btn = await screen.findByTestId('ops-generate-link-btn');
    await user.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId('ops-link-info')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-link-url')).toHaveValue('https://example.com/booking-collection/abc123');
    expect(screen.getByTestId('ops-copy-link-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-revoke-link-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-regenerate-link-btn')).toBeInTheDocument();
  });

  it('revokes collection link', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.generateCollectionLink.mockResolvedValue({
      token_id: 'tok_1',
      collection_url: 'https://example.com/booking-collection/abc123',
      expires_at: '2026-05-11T00:00:00Z',
      trip_id: 'trip_1',
      status: 'active',
    });
    mockApi.revokeCollectionLink.mockResolvedValue({ ok: true });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    // Generate first to get URL visible
    await user.click(await screen.findByTestId('ops-generate-link-btn'));
    await screen.findByTestId('ops-revoke-link-btn');

    await user.click(screen.getByTestId('ops-revoke-link-btn'));

    await waitFor(() => {
      expect(mockApi.revokeCollectionLink).toHaveBeenCalledWith('trip_1');
    });
    expect(screen.queryByTestId('ops-link-info')).not.toBeInTheDocument();
    expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
  });

  it('shows pending review section when customer data exists', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
        payer: { name: 'Jane Doe' },
      },
      booking_data_source: null,
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-pending-review')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-accept-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-reject-btn')).toBeInTheDocument();
    expect(screen.getByText('Submitted by customer')).toBeInTheDocument();
  });

  it('accepts pending booking data', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
      },
      booking_data_source: null,
    });
    mockApi.acceptPendingBookingData.mockResolvedValue({ ok: true });
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
      },
      updated_at: '2026-05-04T00:00:00Z',
      stage: 'proposal',
      readiness: {},
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const acceptBtn = await screen.findByTestId('ops-accept-btn');
    await user.click(acceptBtn);

    await waitFor(() => {
      expect(mockApi.acceptPendingBookingData).toHaveBeenCalledWith('trip_1');
    });
    await waitFor(() => {
      expect(screen.queryByTestId('ops-pending-review')).not.toBeInTheDocument();
    });
  });

  it('rejects pending booking data', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
      },
      booking_data_source: null,
    });
    mockApi.rejectPendingBookingData.mockResolvedValue({ ok: true });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const rejectBtn = await screen.findByTestId('ops-reject-btn');
    await user.click(rejectBtn);

    await waitFor(() => {
      expect(mockApi.rejectPendingBookingData).toHaveBeenCalledWith('trip_1');
    });
    await waitFor(() => {
      expect(screen.queryByTestId('ops-pending-review')).not.toBeInTheDocument();
    });
  });

  it('shows source badge when booking data was entered by agent', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: null,
      booking_data_source: 'agent',
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-source-badge')).toBeInTheDocument();
    });
    expect(screen.getByText('Agent')).toBeInTheDocument();
  });

  it('shows source badge when booking data was accepted from customer', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: null,
      booking_data_source: 'customer_accepted',
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-source-badge')).toBeInTheDocument();
    });
    expect(screen.getByText('Customer (verified)')).toBeInTheDocument();
  });

  it('shows visa/passport concern when signal is present', () => {
    mockStore.result_validation = {
      readiness: {
        ...READINESS,
        signals: { visa_concerns_present: true },
      },
    };
    render(<OpsPanel trip={null} />);
    expect(screen.getByTestId('ops-signal-visa-concern')).toBeInTheDocument();
  });
});
