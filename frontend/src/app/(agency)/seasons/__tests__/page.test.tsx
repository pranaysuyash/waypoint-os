import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import SeasonsPageClient from '../PageClient';

const mockCampaigns = [
  {
    plan_id: 'camp-1',
    name: 'Summer Push',
    status: 'draft',
    updated_at: '2026-06-22T00:00:00Z',
    destination: 'Bali',
    campaign_window_start_month: 6,
    campaign_window_end_month: 8,
    target_budget_min: 1000,
    target_budget_max: 5000,
    notes: '',
    blocklist: [],
  },
];

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <a href='/overview'>Back to Overview</a>,
}));

vi.mock('@/hooks/useSeasonalCampaigns', () => ({
  useSeasonalCampaigns: () => ({
    campaigns: mockCampaigns,
    total: mockCampaigns.length,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useCreateSeasonalCampaign: () => ({ mutate: vi.fn(), isSaving: false, error: null }),
  useUpdateSeasonalCampaign: () => ({ mutate: vi.fn(), isSaving: false, error: null }),
  useDeleteSeasonalCampaign: () => ({ mutate: vi.fn(), isSaving: false, error: null }),
  useSimulateSeasonalCampaign: () => ({
    mutate: vi.fn(async () => ({
      plan_id: 'camp-1',
      scenario: 'aggressive',
      projected_leads: 118,
      projected_bookings: 47,
      projected_margin_pct: 13.7,
      confidence: 0.66,
      notes: ['Simulating scenario'],
    })),
    isRunning: false,
    error: null,
  }),
  usePreflightSeasonalCampaign: () => ({ mutate: vi.fn(), isRunning: false, error: null }),
  useDispatchSeasonalCampaign: () => ({
    mutate: vi.fn(async () => ({
      plan_id: 'camp-1',
      ok: true,
      dispatched_channels: ['email', 'organic'],
      dry_run: true,
      executed_at: '2026-06-23T00:00:00Z',
    })),
    isRunning: false,
    error: null,
  }),
}));

describe('SeasonsPageClient', () => {
  it('renders a fallback when a campaign has no channel mix', () => {
    render(<SeasonsPageClient />);

    expect(screen.getByText(/No mix set/i)).toBeInTheDocument();
  });

  it('shows the active scenario in the simulation result', async () => {
    const user = userEvent.setup();
    render(<SeasonsPageClient />);

    await user.selectOptions(screen.getByLabelText('Scenario'), 'aggressive');
    await user.click(screen.getByRole('button', { name: 'Simulate' }));

    expect(await screen.findByText(/Scenario: aggressive/i)).toBeInTheDocument();
    expect(screen.getByText(/Leads: 118/i)).toBeInTheDocument();
  });

  it('keeps the selected scenario visible in the dry-run result', async () => {
    const user = userEvent.setup();
    render(<SeasonsPageClient />);

    await user.selectOptions(screen.getByLabelText('Scenario'), 'conservative');
    await user.click(screen.getByRole('button', { name: 'Dry run' }));

    expect(await screen.findByText(/Scenario: conservative/i)).toBeInTheDocument();
    expect(screen.getByText(/Dry run: Yes/i)).toBeInTheDocument();
  });
});
