import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import InboxPage from '../page';

const mockUseInboxTrips = vi.fn();

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock('@/hooks/useGovernance', () => ({
  useInboxTrips: () => mockUseInboxTrips(),
}));

describe('InboxPage', () => {
  const baseTrip = {
    id: 'TRIP-123',
    reference: 'SC-901',
    destination: 'Singapore',
    tripType: 'Family',
    partySize: 4,
    dateWindow: 'June 2026',
    value: 220000,
    priority: 'high',
    priorityScore: 90,
    stage: 'intake',
    stageNumber: 1,
    assignedTo: undefined,
    assignedToName: undefined,
    submittedAt: '2026-04-23T08:00:00.000Z',
    lastUpdated: '2026-04-23T08:15:00.000Z',
    daysInCurrentStage: 1,
    slaStatus: 'on_track',
    customerName: 'Sharma Family',
    flags: ['incomplete', 'needs_clarification', 'unassigned'],
  };

  mockUseInboxTrips.mockReturnValue({
    data: [],
    total: 0,
    hasMore: false,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    assignTrips: vi.fn(),
    bulkAction: vi.fn(),
    snoozeTrip: vi.fn(),
  });

  it('renders a page-level return link back to overview', () => {
    render(<InboxPage />);

    expect(screen.getByRole('link', { name: /back to overview/i })).toHaveAttribute('href', '/overview');
  });

  it('uses lead language and exposes an explicit view action', () => {
    mockUseInboxTrips.mockReturnValue({
      data: [baseTrip],
      total: 1,
      hasMore: false,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      assignTrips: vi.fn(),
      bulkAction: vi.fn(),
      snoozeTrip: vi.fn(),
    });

    render(<InboxPage />);

    expect(screen.getByRole('heading', { name: /lead inbox/i })).toBeInTheDocument();
    expect(screen.getByText('New customer inquiries sorted by urgency.')).toBeInTheDocument();
    expect(screen.getByText('1 lead total')).toBeInTheDocument();
    // v2 card asserts: destination shown, metrics row, view link
    expect(screen.getByTestId('trip-card-destination')).toHaveTextContent('Singapore family');
    expect(screen.getByTestId('trip-card-metrics')).toBeInTheDocument();
    expect(screen.getByTestId('trip-card-view-link')).toHaveAttribute(
      'href',
      '/trips/TRIP-123/intake'
    );
  });
});