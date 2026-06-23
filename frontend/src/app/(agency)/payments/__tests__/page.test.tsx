import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import PageClient from '../PageClient';

const mockUsePaymentsQueue = vi.fn();

vi.mock('@/hooks/usePayments', () => ({
  usePaymentsQueue: (...args: unknown[]) => mockUsePaymentsQueue(...args),
}));

vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    ...props
  }: {
    children: ReactNode;
    href: string;
  }) => <a href={href} {...props}>{children}</a>,
}));

describe('payments page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePaymentsQueue.mockReturnValue({
      data: {
        summary: {
          total: 2,
          by_queue_status: { overdue: 1, due_soon: 1 },
          overdue_count: 1,
          due_soon_count: 1,
          not_configured_count: 0,
          paid_complete_count: 0,
          refund_in_progress_count: 0,
          due_within_7_days_count: 1,
        },
        pagination: {
          limit: 25,
          offset: 0,
          returned: 2,
          total: 2,
          has_more: false,
        },
        items: [
          {
            trip_id: 'trip-1',
            trip_name: 'Italy Honeymoon',
            destination: 'Italy',
            start_date: '2026-08-11',
            status: 'assigned',
            queue_status: 'overdue',
            payment_status: 'partially_paid',
            refund_status: 'not_applicable',
            agreed_amount: 2000,
            amount_paid: 500,
            balance_due: 1500,
            currency: 'USD',
            final_payment_due: '2026-05-15',
            payment_reference_present: true,
            payment_proof_url_present: true,
            refund_paid_by_agency: false,
            updated_at: '2026-05-18T10:00:00Z',
          },
          {
            trip_id: 'trip-2',
            trip_name: 'Japan Family',
            destination: 'Japan',
            start_date: '2026-09-02',
            status: 'in_progress',
            queue_status: 'due_soon',
            payment_status: 'deposit_paid',
            refund_status: 'not_applicable',
            agreed_amount: 3000,
            amount_paid: 1200,
            balance_due: 1800,
            currency: 'USD',
            final_payment_due: '2026-05-21',
            payment_reference_present: false,
            payment_proof_url_present: false,
            refund_paid_by_agency: false,
            updated_at: '2026-05-18T11:00:00Z',
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it('renders payment status summary and trip actions', () => {
    render(<PageClient />);

    expect(screen.getByRole('heading', { name: 'Payments' })).toBeInTheDocument();
    expect(screen.getByText('Total in queue')).toBeInTheDocument();
    expect(screen.getByText('Italy Honeymoon')).toBeInTheDocument();
    const openTripLinks = screen.getAllByRole('link', { name: /open trip/i });
    expect(openTripLinks).toHaveLength(2);
    expect(openTripLinks[0]).toHaveAttribute('href', '/trips/trip-1/ops');
    expect(openTripLinks[1]).toHaveAttribute('href', '/trips/trip-2/ops');
    expect(screen.getByText('Showing 2 of 2')).toBeInTheDocument();
  });

  it('falls back to destination or trip id when trip name is missing', () => {
    mockUsePaymentsQueue.mockReturnValueOnce({
      data: {
        summary: {
          total: 1,
          by_queue_status: { overdue: 1 },
          overdue_count: 1,
          due_soon_count: 0,
          not_configured_count: 0,
          paid_complete_count: 0,
          refund_in_progress_count: 0,
          due_within_7_days_count: 0,
        },
        pagination: {
          limit: 25,
          offset: 0,
          returned: 1,
          total: 1,
          has_more: false,
        },
        items: [
          {
            trip_id: 'trip-blank',
            trip_name: '',
            destination: '',
            start_date: null,
            status: 'assigned',
            queue_status: 'overdue',
            payment_status: 'overdue',
            refund_status: 'not_applicable',
            agreed_amount: null,
            amount_paid: null,
            balance_due: null,
            currency: 'USD',
            final_payment_due: null,
            payment_reference_present: false,
            payment_proof_url_present: false,
            refund_paid_by_agency: false,
            updated_at: null,
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<PageClient />);

    expect(screen.getByText('trip-blank')).toBeInTheDocument();
    expect(screen.getByText('Destination pending')).toBeInTheDocument();
  });

  it('passes filter params to payments queue hook', () => {
    render(<PageClient />);
    expect(mockUsePaymentsQueue).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 25, offset: 0 }),
    );

    fireEvent.change(screen.getByLabelText('Queue status'), {
      target: { value: 'overdue' },
    });

    expect(mockUsePaymentsQueue).toHaveBeenLastCalledWith(
      expect.objectContaining({ queue_status: 'overdue', offset: 0 }),
    );
  });
});
