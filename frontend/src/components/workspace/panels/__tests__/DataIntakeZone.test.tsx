import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataIntakeZone from '../DataIntakeZone';

const mockApi = {
  getBookingData: vi.fn(),
  updateBookingData: vi.fn(),
  updatePaymentTracking: vi.fn(),
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
  updatePaymentTracking: (...args: unknown[]) => mockApi.updatePaymentTracking(...args),
  getCollectionLink: (...args: unknown[]) => mockApi.getCollectionLink(...args),
  generateCollectionLink: (...args: unknown[]) => mockApi.generateCollectionLink(...args),
  revokeCollectionLink: (...args: unknown[]) => mockApi.revokeCollectionLink(...args),
  getPendingBookingData: (...args: unknown[]) => mockApi.getPendingBookingData(...args),
  acceptPendingBookingData: (...args: unknown[]) => mockApi.acceptPendingBookingData(...args),
  rejectPendingBookingData: (...args: unknown[]) => mockApi.rejectPendingBookingData(...args),
}));

describe('DataIntakeZone', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: null,
      updated_at: null,
    });
    mockApi.getCollectionLink.mockRejectedValue(new Error('not found'));
    mockApi.getPendingBookingData.mockRejectedValue(new Error('not found'));
  });

  it('shows collection link section at proposal stage', async () => {
    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
    });
  });

  it('shows collection link section at booking stage (canGenerateLink=true)', async () => {
    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-collection-link')).toBeInTheDocument();
    });
  });

  it('hides collection link when canGenerateLink is false', async () => {
    render(<DataIntakeZone tripId="trip_1" canGenerateLink={false} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-booking-data')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('ops-collection-link')).not.toBeInTheDocument();
  });

  it('shows active link hint when GET returns has_active_token', async () => {
    mockApi.getCollectionLink.mockResolvedValue({
      has_active_token: true,
      token_id: 'tok_1',
      expires_at: '2026-05-11T00:00:00Z',
      status: 'active',
      has_pending_submission: false,
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-link-active-hint')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
  });

  it('generates collection link and shows URL', async () => {
    const user = userEvent.setup();
    mockApi.generateCollectionLink.mockResolvedValue({
      token_id: 'tok_1',
      collection_url: 'https://example.com/booking-collection/d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b/abc123',
      expires_at: '2026-05-11T00:00:00Z',
      trip_id: 'trip_1',
      status: 'active',
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

    const btn = await screen.findByTestId('ops-generate-link-btn');
    await user.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId('ops-link-info')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-link-url')).toHaveValue('https://example.com/booking-collection/d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b/abc123');
    expect(screen.getByTestId('ops-copy-link-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-revoke-link-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-regenerate-link-btn')).toBeInTheDocument();
  });

  it('revokes collection link', async () => {
    const user = userEvent.setup();
    mockApi.generateCollectionLink.mockResolvedValue({
      token_id: 'tok_1',
      collection_url: 'https://example.com/booking-collection/d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b/abc123',
      expires_at: '2026-05-11T00:00:00Z',
      trip_id: 'trip_1',
      status: 'active',
    });
    mockApi.revokeCollectionLink.mockResolvedValue({ ok: true });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

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
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
        payer: { name: 'Jane Doe' },
      },
      booking_data_source: null,
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-pending-review')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-accept-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-reject-btn')).toBeInTheDocument();
    expect(screen.getByText('Submitted by customer')).toBeInTheDocument();
  });

  it('accepts pending booking data', async () => {
    const user = userEvent.setup();
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
      },
      booking_data_source: null,
    });
    mockApi.acceptPendingBookingData.mockResolvedValue({ ok: true });
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
      },
      updated_at: '2026-05-04T00:00:00Z',
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

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
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
      },
      booking_data_source: null,
    });
    mockApi.rejectPendingBookingData.mockResolvedValue({ ok: true });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

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
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: null,
      booking_data_source: 'agent',
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-source-badge')).toBeInTheDocument();
    });
    expect(screen.getByText('Agent')).toBeInTheDocument();
  });

  it('shows source badge when booking data was accepted from customer', async () => {
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: null,
      booking_data_source: 'customer_accepted',
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-source-badge')).toBeInTheDocument();
    });
    expect(screen.getByText('Customer (verified)')).toBeInTheDocument();
  });

  it('shows payment tracking without exposing a payment collection workflow', async () => {
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
        payer: { name: 'Jane Doe' },
        payment_tracking: {
          agreed_amount: 120000,
          currency: 'INR',
          amount_paid: 50000,
          balance_due: 70000,
          payment_status: 'partially_paid',
          refund_status: 'not_applicable',
          tracking_only: true,
        },
      },
      updated_at: '2026-05-12T00:00:00Z',
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={false} />);

    expect(await screen.findByTestId('ops-payment-tracking')).toBeInTheDocument();
    expect(screen.getByText('Status-only tracking')).toBeInTheDocument();
    expect(screen.getByText('INR 70,000')).toBeInTheDocument();
    expect(screen.queryByText(/wallet/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pay now/i)).not.toBeInTheDocument();
  });

  it('traveler save does not include payment_tracking in payload', async () => {
    const user = userEvent.setup();
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
        payer: { name: 'Jane Doe' },
      },
      updated_at: '2026-05-12T00:00:00Z',
    });
    mockApi.updateBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: { travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }] },
      updated_at: '2026-05-12T00:01:00Z',
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={false} />);

    await user.click(await screen.findByTestId('ops-edit-btn'));
    await user.click(screen.getByTestId('ops-save-btn'));

    await waitFor(() => {
      expect(mockApi.updateBookingData).toHaveBeenCalled();
    });
    const [, payload] = mockApi.updateBookingData.mock.calls[0];
    expect(payload).not.toHaveProperty('payment_tracking');
  });

  it('calls onPendingDataChange when pending data loads', async () => {
    const onPendingDataChange = vi.fn();
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
      },
      booking_data_source: null,
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={true} onPendingDataChange={onPendingDataChange} />);

    await waitFor(() => {
      expect(onPendingDataChange).toHaveBeenCalledWith(
        expect.objectContaining({ travelers: expect.any(Array) }),
      );
    });
  });

  it('calls onTravelersChange when booking data loads', async () => {
    const onTravelersChange = vi.fn();
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
      },
      updated_at: '2026-05-12T00:00:00Z',
    });

    render(<DataIntakeZone tripId="trip_1" canGenerateLink={false} onTravelersChange={onTravelersChange} />);

    await waitFor(() => {
      expect(onTravelersChange).toHaveBeenCalledWith(
        expect.arrayContaining([expect.objectContaining({ traveler_id: 'adult_1' })]),
      );
    });
  });

  it('calls onPaymentTrackingChange when booking data loads with payment tracking', async () => {
    const onPaymentTrackingChange = vi.fn();
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [{ traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' }],
        payment_tracking: {
          agreed_amount: 120000,
          amount_paid: 50000,
          balance_due: 70000,
          payment_status: 'partially_paid',
          refund_status: 'not_applicable',
          tracking_only: true,
        },
      },
      updated_at: '2026-05-12T00:00:00Z',
    });

    render(
      <DataIntakeZone
        tripId="trip_1"
        canGenerateLink={false}
        onPaymentTrackingChange={onPaymentTrackingChange}
      />,
    );

    await waitFor(() => {
      expect(onPaymentTrackingChange).toHaveBeenCalledWith(
        expect.objectContaining({ payment_status: 'partially_paid' }),
      );
    });
  });
});
