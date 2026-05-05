import { afterEach, describe, it, expect, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import type { ReactNode } from 'react';
import OverviewPage from '../page';

const ROUTES = {
  workspaces: '/trips',
  inbox: '/inbox',
  approvals: '/reviews',
  integrity: '/workbench?panel=integrity',
  intake: '/workbench?draft=new&tab=intake',
} as const;

const baseSummary = {
  headerSubtitle: '2 trips in planning · 5 leads · 1 quote to review',
  metrics: [
      {
        title: 'Trips in Planning',
        value: 2,
        sub: '2 trips being planned',
        ctaLabel: 'Open trips',
        href: '/trips',
      state: 'blue',
      icon: () => null,
      isLoading: false,
      error: null,
    },
      {
        title: 'Lead Inbox',
        value: 5,
        sub: '5 new leads to review',
        ctaLabel: 'Review leads',
        href: '/inbox',
      state: 'amber',
      icon: () => null,
      isLoading: false,
      error: null,
    },
      {
        title: 'Quote Review',
        value: 1,
        sub: '1 quote to review',
        ctaLabel: 'Review quotes',
        href: '/reviews',
      state: 'green',
      icon: () => null,
      isLoading: false,
      error: null,
    },
      {
        title: 'System Check',
        value: 3,
        sub: '3 routing issues',
        ctaLabel: 'Check status',
        href: ROUTES.integrity,
      state: 'red',
      icon: () => null,
      isLoading: false,
      error: null,
    },
  ],
  navItems: [
    {
      href: '/inbox',
      label: 'Lead Inbox',
        sub: '5 new leads to review',
      subColor: 'var(--accent-amber)',
      icon: () => null,
    },
    {
      href: '/trips',
      label: 'Trips in Planning',
        sub: '2 trips being planned',
      subColor: 'var(--accent-blue)',
      icon: () => null,
    },
    {
      href: '/reviews',
      label: 'Quote Review',
        sub: '1 quote to review',
      subColor: 'var(--accent-green)',
      icon: () => null,
    },
    {
      href: ROUTES.integrity,
        label: 'System Check',
        sub: '3 routing issues',
      subColor: 'var(--accent-red)',
      icon: () => null,
    },
  ],
  pipeline: [
    { label: 'Assigned', count: 1 },
  ],
  pipelineLoading: false,
  pipelineError: null,
  recentTrips: [
    {
      id: 'trip_4b9e0d894872',
      destination: 'Singapore',
      type: 'family',
      state: 'amber',
      age: 'Today',
      createdAt: '2026-04-30T00:00:00Z',
      updatedAt: '2026-04-30T00:00:00Z',
      party: 5,
      dateWindow: 'dates around 9th to 14th feb',
      origin: 'TBD',
      budget: '$0',
      status: 'assigned',
      rawInput: {
        fixture_id: 'SC-901',
      },
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
    },
  ],
  recentTripsLoading: false,
  recentTripsError: null,
  planningTripsTotal: 2,
  leadInboxTotal: 5,
};

const mockUseOverviewSummary = vi.fn(() => baseSummary);

vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    ...props
  }: {
    children: ReactNode;
    href: string;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('../useOverviewSummary', () => ({
  useOverviewSummary: () => mockUseOverviewSummary(),
}));

describe('OverviewPage', () => {
  afterEach(() => {
    mockUseOverviewSummary.mockReset();
    mockUseOverviewSummary.mockReturnValue(baseSummary);
  });

  it('renders queue cards against their configured destination routes', () => {
    render(<OverviewPage />);

    expect(screen.getByText('2 trips in planning · 5 leads · 1 quote to review')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /trips in planning/i })[0]).toHaveAttribute('href', ROUTES.workspaces);
    expect(screen.getAllByRole('link', { name: /lead inbox/i })[0]).toHaveAttribute('href', ROUTES.inbox);
    expect(screen.getAllByRole('link', { name: /quote review/i })[0]).toHaveAttribute('href', ROUTES.approvals);

    const integrityLink = screen.getAllByRole('link', { name: /system check/i })[0];
    expect(integrityLink).not.toHaveAttribute('href', ROUTES.approvals);
    expect(integrityLink).toHaveAttribute('href', ROUTES.integrity);
  });

  it('routes overview actions to the specific intake destinations', () => {
    render(<OverviewPage />);

    const openTripsLinks = screen.getAllByRole('link', { name: /open trips/i });
    expect(openTripsLinks.length).toBeGreaterThan(0);
    openTripsLinks.forEach((link) => {
      expect(link).toHaveAttribute('href', ROUTES.workspaces);
    });
    expect(screen.getByRole('link', { name: /process new inquiry/i })).toHaveAttribute('href', ROUTES.intake);
  });

  it('shows a lead-driven empty state when inbox has leads but planning is empty', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      pipeline: [],
      recentTrips: [],
      planningTripsTotal: 0,
      leadInboxTotal: 1,
    });

    render(<OverviewPage />);

    expect(screen.getByText('No trips in planning yet')).toBeInTheDocument();
    expect(screen.getAllByText(/A lead is waiting in Lead Inbox/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: /review leads/i })).toHaveAttribute('href', ROUTES.inbox);
  });

  it('shows a true empty-account state when there are no leads or trips', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      recentTrips: [],
      planningTripsTotal: 0,
      leadInboxTotal: 0,
    });

    render(<OverviewPage />);

    expect(screen.getByText('Welcome to Waypoint')).toBeInTheDocument();
    expect(screen.getByText('Invite your team')).toBeInTheDocument();
    expect(screen.getByText('Add your first inquiry')).toBeInTheDocument();
  });

  it('keeps the trip list visible when planning already has trips', () => {
    render(<OverviewPage />);

    expect(screen.getByRole('link', { name: /open missing details/i })).toBeInTheDocument();
    expect(screen.queryByText('No trips in planning yet')).not.toBeInTheDocument();
  });

  it('renders planning work as a rich trip card instead of a sparse activity row', () => {
    render(<OverviewPage />);

    const planningCardHeading = screen.getByText('Singapore family trip');
    const planningCard = planningCardHeading.closest('[class*="rounded-2xl"]');

    expect(planningCardHeading).toBeInTheDocument();
    expect(planningCard).not.toBeNull();
    expect(within(planningCard as HTMLElement).getByText(/5 pax.*Around Feb 9–14/i)).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText('Need Customer Details')).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText(/Add budget/i)).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText('In planning')).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText('Waiting on customer')).toBeInTheDocument();
    expect(screen.getByText(/Ref 4B9E/i)).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).queryByText('Need Trip Options')).not.toBeInTheDocument();
    expect(screen.queryByText('trip_4b9e0d894872')).not.toBeInTheDocument();
    expect(screen.queryByText(/Most in Assigned/i)).not.toBeInTheDocument();
    expect(screen.getByText('Planning Status · 2 planning')).toBeInTheDocument();
  });
});
