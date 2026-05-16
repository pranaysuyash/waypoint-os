import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PaymentTrackingCard from '../PaymentTrackingCard';
import type { PaymentTracking } from '@/lib/api-client';

const mockApi = {
  updatePaymentTracking: vi.fn(),
};

vi.mock('@/lib/api-client', () => ({
  updatePaymentTracking: (...args: unknown[]) => mockApi.updatePaymentTracking(...args),
}));

const BASE_TRACKING: PaymentTracking = {
  agreed_amount: 120000,
  currency: 'INR',
  amount_paid: 50000,
  balance_due: 70000,
  payment_status: 'partially_paid',
  refund_status: 'not_applicable',
  tracking_only: true,
};

function renderCard(overrides: Partial<PaymentTracking> = {}, onPaymentSaved?: () => void) {
  return render(
    <PaymentTrackingCard
      paymentTracking={{ ...BASE_TRACKING, ...overrides }}
      tripId="trip_1"
      updatedAt="2026-05-15T00:00:00Z"
      onPaymentSaved={onPaymentSaved}
    />,
  );
}

describe('PaymentTrackingCard — view mode', () => {
  it('renders the card with testid', () => {
    renderCard();
    expect(screen.getByTestId('ops-payment-tracking')).toBeInTheDocument();
  });

  it('shows agreed/paid/balance/status', () => {
    renderCard();
    expect(screen.getByText('INR 1,20,000')).toBeInTheDocument();
    expect(screen.getByText('INR 50,000')).toBeInTheDocument();
    expect(screen.getByText('INR 70,000')).toBeInTheDocument();
    expect(screen.getByText('partially paid')).toBeInTheDocument();
  });

  it('shows Edit Payment button', () => {
    renderCard();
    expect(screen.getByTestId('ops-payment-edit-btn')).toBeInTheDocument();
  });

  it('shows final_payment_due badge when present', () => {
    renderCard({ final_payment_due: '2099-12-31' });
    expect(screen.getByTestId('ops-payment-due-badge')).toBeInTheDocument();
  });

  it('does not show due badge when final_payment_due absent', () => {
    renderCard({ final_payment_due: null });
    expect(screen.queryByTestId('ops-payment-due-badge')).not.toBeInTheDocument();
  });

  it('shows overdue badge for past date', () => {
    renderCard({ final_payment_due: '2020-01-01' });
    expect(screen.getByTestId('ops-payment-due-badge').textContent).toMatch(/overdue/i);
  });

  it('shows amber badge for date 4-7 days away', () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const d = new Date(today);
    d.setDate(d.getDate() + 5);
    renderCard({ final_payment_due: d.toISOString().slice(0, 10) });
    const badge = screen.getByTestId('ops-payment-due-badge');
    expect(badge.textContent).toMatch(/due in/i);
    expect(badge.className).toMatch(/amber/);
  });
});

describe('PaymentTrackingCard — edit mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('switches to edit mode on Edit Payment click', async () => {
    const user = userEvent.setup();
    renderCard();
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    expect(screen.getByTestId('ops-payment-save-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-payment-cancel-btn')).toBeInTheDocument();
  });

  it('cancel returns to view mode without saving', async () => {
    const user = userEvent.setup();
    renderCard();
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    await user.click(screen.getByTestId('ops-payment-cancel-btn'));
    expect(screen.getByTestId('ops-payment-edit-btn')).toBeInTheDocument();
    expect(mockApi.updatePaymentTracking).not.toHaveBeenCalled();
  });

  it('save calls updatePaymentTracking with correct tripId', async () => {
    const user = userEvent.setup();
    mockApi.updatePaymentTracking.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [],
        payment_tracking: { ...BASE_TRACKING },
      },
      updated_at: '2026-05-15T00:01:00Z',
    });

    renderCard();
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    await user.click(screen.getByTestId('ops-payment-save-btn'));

    await waitFor(() => {
      expect(mockApi.updatePaymentTracking).toHaveBeenCalledWith(
        'trip_1',
        expect.any(Object),
        '2026-05-15T00:00:00Z',
      );
    });
  });

  it('save returns to view mode on success', async () => {
    const user = userEvent.setup();
    mockApi.updatePaymentTracking.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: { travelers: [], payment_tracking: { ...BASE_TRACKING } },
      updated_at: '2026-05-15T00:01:00Z',
    });

    renderCard();
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    await user.click(screen.getByTestId('ops-payment-save-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('ops-payment-edit-btn')).toBeInTheDocument();
    });
  });

  it('calls onPaymentSaved callback after successful save', async () => {
    const onPaymentSaved = vi.fn();
    mockApi.updatePaymentTracking.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [],
        payment_tracking: { ...BASE_TRACKING, payment_status: 'paid' },
      },
      updated_at: '2026-05-15T00:01:00Z',
    });

    const user = userEvent.setup();
    render(
      <PaymentTrackingCard
        paymentTracking={BASE_TRACKING}
        tripId="trip_1"
        updatedAt="2026-05-15T00:00:00Z"
        onPaymentSaved={onPaymentSaved}
      />,
    );
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    await user.click(screen.getByTestId('ops-payment-save-btn'));

    await waitFor(() => {
      expect(onPaymentSaved).toHaveBeenCalledWith(
        expect.objectContaining({ payment_status: 'paid' }),
        '2026-05-15T00:01:00Z',
      );
    });
  });

  it('shows conflict display on 409 response', async () => {
    const user = userEvent.setup();
    mockApi.updatePaymentTracking.mockRejectedValue({ status: 409 });

    renderCard();
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    await user.click(screen.getByTestId('ops-payment-save-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('ops-payment-conflict')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-payment-conflict-reload')).toBeInTheDocument();
  });

  it('conflict reload button returns to view mode', async () => {
    const user = userEvent.setup();
    mockApi.updatePaymentTracking.mockRejectedValue({ status: 409 });

    renderCard();
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    await user.click(screen.getByTestId('ops-payment-save-btn'));

    const reloadBtn = await screen.findByTestId('ops-payment-conflict-reload');
    await user.click(reloadBtn);

    expect(screen.getByTestId('ops-payment-edit-btn')).toBeInTheDocument();
    expect(screen.queryByTestId('ops-payment-conflict')).not.toBeInTheDocument();
  });

  it('shows final_payment_due input in edit mode', async () => {
    const user = userEvent.setup();
    renderCard({ final_payment_due: '2026-06-15' });
    await user.click(screen.getByTestId('ops-payment-edit-btn'));
    const input = screen.getByTestId('ops-payment-due-input') as HTMLInputElement;
    expect(input.value).toBe('2026-06-15');
  });

  it('sends final_payment_due in save payload', async () => {
    const user = userEvent.setup();
    mockApi.updatePaymentTracking.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: { travelers: [], payment_tracking: { ...BASE_TRACKING } },
      updated_at: '2026-05-15T00:01:00Z',
    });

    renderCard();
    await user.click(screen.getByTestId('ops-payment-edit-btn'));

    const dueInput = screen.getByTestId('ops-payment-due-input');
    await user.type(dueInput, '2026-06-30');
    await user.click(screen.getByTestId('ops-payment-save-btn'));

    await waitFor(() => {
      expect(mockApi.updatePaymentTracking).toHaveBeenCalledWith(
        'trip_1',
        expect.objectContaining({ final_payment_due: '2026-06-30' }),
        expect.any(String),
      );
    });
  });
});
