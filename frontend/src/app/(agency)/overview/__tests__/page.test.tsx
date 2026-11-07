import { afterEach, describe, it, expect, vi } from 'vitest';
import { render, screen, within, fireEvent } from '@testing-library/react';
import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import OverviewPage from '../page';

// FND-0402 (2026-11-05): the overview page migrated to react-query hooks —
// every render must sit under a fresh QueryClientProvider.
function renderPage(ui: ReactNode = <OverviewPage />) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const ROUTES = {
  workspaces: '/trips',
  inbox: '/inbox',
  approvals: '/reviews',
  integrity: '/overview?panel=system-check',
  intake: '/inquiries/new?draft=new&tab=intake',
} as const;

const baseSummary = {
  headerSubtitle: '2 trips in planning · 5 enquiries · 1 quote to review',
  actionRequiredLoading: false,
  actionRequiredError: null,
  actionRequiredItems: [
    {
      id: 'trip-1',
      priority: 'high',
      source: 'trip',
      label: 'Trip',
      title: 'Japan family trip',
      subtitle: 'Travel 24 May 2026',
      meta: 'Planning overdue',
      reason: 'Customer details are still missing.',
      href: '/trips/trip_1/intake',
      ctaLabel: 'Open trip',
    },
  ],
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
        title: 'New enquiries',
        value: 5,
        sub: '5 new enquiries to review',
        ctaLabel: 'Review enquiries',
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
      label: 'New enquiries',
        sub: '5 new enquiries to review',
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
  planningTripsLoading: false,
  planningTripsError: null,
  leadInboxTotal: 5,
  leadInboxLoading: false,
  leadInboxError: null,
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

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/overview',
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock('@/components/system/SystemCheckPanel', () => ({
  default: ({ open }: { open: boolean }) => (
    open ? <div data-testid='system-check-panel'>System Check</div> : null
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
    renderPage();

    expect(screen.getByText('2 trips in planning · 5 enquiries · 1 quote to review')).toBeInTheDocument();
    expect(screen.getByText('Action Required')).toBeInTheDocument();
    expect(screen.getAllByText('Japan family trip').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Customer details are still missing.').length).toBeGreaterThan(0);
    expect(screen.getAllByRole('link', { name: /trips in planning/i })[0]).toHaveAttribute('href', ROUTES.workspaces);
    expect(screen.getAllByRole('link', { name: /new enquiries/i })[0]).toHaveAttribute('href', ROUTES.inbox);
    expect(screen.getAllByRole('link', { name: /quote review/i })[0]).toHaveAttribute('href', ROUTES.approvals);

    const integrityLink = screen.getAllByRole('link', { name: /system check/i })[0];
    expect(integrityLink).not.toHaveAttribute('href', ROUTES.approvals);
    expect(integrityLink).toHaveAttribute('href', ROUTES.integrity);
  });

  it('renders Action Required above metric cards', () => {
    renderPage();

    const actionHeading = screen.getByText('Action Required');
    const metricTitle = screen.getAllByText('Trips in Planning')[0] as HTMLElement;
    const pos = actionHeading.compareDocumentPosition(metricTitle);

    expect(pos & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('surfaces the highest-priority item as the start here banner', () => {
    renderPage();

    const banner = screen.getByLabelText('Start Here');
    expect(within(banner).getByText('Start here')).toBeInTheDocument();
    expect(within(banner).getByText('Japan family trip')).toBeInTheDocument();
    expect(within(banner).getByRole('link', { name: /open trip/i })).toHaveAttribute('href', '/trips/trip_1/intake');
  });

  it('does not show totals-only lead or system rows in Action Required', () => {
    renderPage();

    expect(screen.queryByText('New enquiries waiting')).not.toBeInTheDocument();
    expect(screen.queryByText('Agency health check')).not.toBeInTheDocument();
  });

  it('shows loading message in Action Required when summary marks action list loading', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      actionRequiredLoading: true,
      actionRequiredItems: [],
    });

    renderPage();
    expect(screen.getByText('Checking for action required…')).toBeInTheDocument();
    expect(screen.queryByText('No urgent action detected from available data.')).not.toBeInTheDocument();
  });

  it('routes overview actions to the specific intake destinations', () => {
    renderPage();

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
      planningTripsLoading: false,
      planningTripsError: null,
      leadInboxTotal: 1,
      leadInboxLoading: false,
      leadInboxError: null,
    });

    renderPage();

    expect(screen.getByText('No trips in planning yet')).toBeInTheDocument();
    expect(screen.getAllByText(/A new enquiry is waiting/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: /review enquiries/i })).toHaveAttribute('href', ROUTES.inbox);
  });

  it('groups identical recent trips into a single overview card cluster', () => {
    // FND-0402: tripPurpose is now a required brief field — without it every
    // card titles "Trip details incomplete" and all signatures collapse.
    const duplicateTrip = {
      id: 'trip_dup_1',
      destination: 'Bali',
      tripPurpose: 'Leisure',
      type: 'leisure',
      state: 'amber',
      age: 'Today',
      createdAt: '2026-04-30T00:00:00Z',
      updatedAt: '2026-04-30T00:00:00Z',
      party: 2,
      dateWindow: 'August 2026',
      origin: 'Mumbai',
      budget: '₹3L',
      status: 'in_progress',
      rawInput: { fixture_id: 'trip_dup_fixture' },
      decision: baseSummary.recentTrips[0].decision,
      validation: baseSummary.recentTrips[0].validation,
    } as const;

    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      recentTrips: [duplicateTrip, { ...duplicateTrip, id: 'trip_dup_2' }, { ...duplicateTrip, id: 'trip_unique', destination: 'Singapore' }],
    });

    renderPage();

    expect(screen.getByText(/Showing 2 grouped cards from 3 trips\./i)).toBeInTheDocument();
    expect(screen.getByText(/2 matching trips/i)).toBeInTheDocument();
  });

  it('shows a true empty-account state when there are no leads or trips', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      recentTrips: [],
      planningTripsTotal: 0,
      planningTripsLoading: false,
      planningTripsError: null,
      leadInboxTotal: 0,
      leadInboxLoading: false,
      leadInboxError: null,
      // FND-0402: the empty-account state must not inherit the base fixture's
      // header copy, action items, or loading flags — the page renders those
      // verbatim and the onboarding gate is on live loading flags.
      headerSubtitle: '',
      actionRequiredItems: [],
      recentTripsLoading: false,
    });

    renderPage();

    expect(screen.getByText('Welcome to Waypoint')).toBeInTheDocument();
    // FND-0402: onboarding migrated to outcome-derived steps (activation
    // facts) — the invite-team checklist item no longer exists.
    // The step label appears twice (list item + CTA link) — assert on count.
    expect(screen.getAllByText('Add your first inquiry').length).toBeGreaterThan(0);
    expect(screen.getByText('Ready the brief')).toBeInTheDocument();
    expect(screen.getByText('Start planning')).toBeInTheDocument();
  });

  it('keeps the trip list visible when planning already has trips', () => {
    renderPage();

    expect(screen.getAllByRole('link', { name: /open trip/i })[0]).toBeInTheDocument();
    expect(screen.queryByText('No trips in planning yet')).not.toBeInTheDocument();
  });

  it('renders planning work as a rich trip card instead of a sparse activity row', () => {
    renderPage();

    const planningCardHeading = screen.getByText('Trip details incomplete');
    const planningCard = planningCardHeading.closest('[class*="rounded-2xl"]');

    expect(planningCardHeading).toBeInTheDocument();
    expect(planningCard).not.toBeNull();
    expect(within(planningCard as HTMLElement).getByText(/5 pax.*Around Feb 9–14/i)).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText('Missing customer details')).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText(/Add budget/i)).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText(/Add origin/i)).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText('In planning')).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).getByText('Waiting on customer')).toBeInTheDocument();
    expect(screen.getByText(/Ref 4B9E/i)).toBeInTheDocument();
    expect(within(planningCard as HTMLElement).queryByText('Need Trip Options')).not.toBeInTheDocument();
    expect(screen.queryByText('trip_4b9e0d894872')).not.toBeInTheDocument();
    expect(screen.queryByText(/Most in Assigned/i)).not.toBeInTheDocument();
    expect(screen.getByText('Latest Trips Status · showing 1 of 2')).toBeInTheDocument();
  });

  it('explains when recent trips are collapsed into grouped cards', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      recentTrips: [
        baseSummary.recentTrips[0]!,
        {
          ...baseSummary.recentTrips[0]!,
          id: 'trip_4b9e0d894873',
        },
      ],
    });

    renderPage();

    expect(screen.getByText(/Showing 1 grouped card from 2 trips\./i)).toBeInTheDocument();
    expect(screen.getByText(/2 matching trips/i)).toBeInTheDocument();
  });

  it('shows single-stage collapsed pipeline with stage name in copy', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      pipeline: [{ label: 'assigned', count: 2 }],
    });

    renderPage();

    expect(screen.getByText('2 trips in planning · all Waiting for options')).toBeInTheDocument();
    expect(screen.queryByText('Expand')).not.toBeInTheDocument();
  });

  it('shows multi-stage collapsed pipeline with legend and Expand button', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      pipeline: [
        { label: 'assigned', count: 3 },
        { label: 'ready_to_book', count: 1 },
      ],
      recentTrips: [],
      planningTripsTotal: 4,
    });

    renderPage();

    expect(screen.getByText('Waiting for options · 3')).toBeInTheDocument();
    expect(screen.getByText('Ready for booking · 1')).toBeInTheDocument();
    expect(screen.getByText('Expand')).toBeInTheDocument();
  });

  it('shows expanded pipeline with stage labels after clicking Expand', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      pipeline: [
        { label: 'assigned', count: 1 },
        { label: 'ready_to_quote', count: 1 },
      ],
      recentTrips: [],
      planningTripsTotal: 2,
    });

    renderPage();

    expect(screen.getByText('Waiting for options · 1')).toBeInTheDocument();
    expect(screen.getByText('Ready for quote review · 1')).toBeInTheDocument();

    const expandButton = screen.getByText('Expand');
    fireEvent.click(expandButton);

    expect(screen.getByText('Collapse')).toBeInTheDocument();
    expect(screen.getByText('2 total')).toBeInTheDocument();
  });

  it('does not render actively being built text', () => {
    mockUseOverviewSummary.mockReturnValue({
      ...baseSummary,
      pipeline: [{ label: 'in_progress', count: 5 }],
    });

    renderPage();

    expect(screen.queryByText(/actively being built/i)).not.toBeInTheDocument();
  });
});
