import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import type { ReactNode } from 'react';
import WorkspacesPage from '../page';

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/useTrips', () => ({
  useTrips: vi.fn(),
}));

import { useTrips } from '@/hooks/useTrips';

describe('WorkspacesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useTrips).mockReturnValue({
      data: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as never);
  });

  it('renders a page-level return link back to overview', () => {
    render(<WorkspacesPage />);

    expect(screen.getByRole('link', { name: /back to overview/i })).toHaveAttribute('href', '/overview');
  });

  it('renders trips in planning with the same planning language as overview and intake', () => {
    vi.mocked(useTrips).mockReturnValue({
      data: [
        {
          id: 'trip_4b9e0d894872',
          destination: 'Singapore',
          type: 'Family Leisure',
          state: 'amber',
          age: 'Today',
          party: 5,
          dateWindow: 'dates around 9th to 14th feb',
          origin: 'TBD',
          budget: '$0',
          status: 'assigned',
          rawInput: { fixture_id: 'SC-901' },
          decision: {
            decision_state: 'ASK_FOLLOWUP',
            hard_blockers: [],
            soft_blockers: ['incomplete_intake'],
          },
          validation: {
            warnings: [
              { field: 'budget_raw_text' },
              { field: 'origin_city' },
            ],
          },
          createdAt: '2026-04-29T20:02:40.764703+00:00',
          updatedAt: '2026-04-30T12:23:15.851953+00:00',
        },
      ],
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as never);

    render(<WorkspacesPage />);

    expect(screen.getByRole('heading', { name: 'Trips in Planning' })).toBeInTheDocument();
    expect(screen.getByText('Trips your team is actively working on')).toBeInTheDocument();
    expect(screen.queryByText('Workspaces')).not.toBeInTheDocument();

    const tripCard = screen.getByText('Singapore family trip').closest('a');
    expect(tripCard).not.toBeNull();

    expect(within(tripCard as HTMLElement).getByText('Singapore family trip')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Customer SC-901 · 5 pax · Around Feb 9–14')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Need Customer Details')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Budget missing')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Origin missing')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Assigned')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Next: confirm budget and origin before building options.')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Inquiry Ref: 4B9E')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).getByText('Updated today')).toBeInTheDocument();
    expect(within(tripCard as HTMLElement).queryByText('In Progress')).not.toBeInTheDocument();
    expect(within(tripCard as HTMLElement).queryByText('$0')).not.toBeInTheDocument();
    expect(within(tripCard as HTMLElement).queryByText(/trip_4b9e0d894872/i)).not.toBeInTheDocument();
    expect(within(tripCard as HTMLElement).queryByText(/^Open$/)).not.toBeInTheDocument();

    expect(screen.getByText('Next step')).toBeInTheDocument();
    expect(screen.getByText('Confirm missing customer details.')).toBeInTheDocument();
    expect(screen.getByText('Budget range')).toBeInTheDocument();
    expect(screen.getByText('Origin city')).toBeInTheDocument();
    const missingDetailLinks = screen.getAllByRole('link', { name: /Continue planning|Open missing details/i });
    expect(missingDetailLinks).toHaveLength(2);
    missingDetailLinks.forEach((link) => {
      expect(link).toHaveAttribute('href', '/trips/trip_4b9e0d894872/intake');
    });
  });
});
