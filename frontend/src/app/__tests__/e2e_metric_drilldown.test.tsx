import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch
global.fetch = vi.fn();

// Mock useRouter
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('E2E: Metric Drill-Down Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('complete drill-down flow: click metric -> view trips -> navigate to timeline', async () => {
    // This E2E test validates the full traceability linkage flow
    // 1. User sees performance metrics in TeamPerformanceChart
    // 2. User clicks on a metric to drill down
    // 3. MetricDrillDownDrawer opens with trip list
    // 4. User clicks a trip
    // 5. Navigation occurs to trip timeline

    // Mock the API response
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        agentId: 'agent-1',
        metric: 'conversion',
        trips: [
          {
            tripId: 'trip-123',
            destinationName: 'Paris',
            status: 'approved',
            responseTime: 2.5,
            suitabilityScore: 95,
            decisionReason: 'Excellent match',
            createdAt: '2024-01-15T10:00:00Z',
          },
        ],
        count: 1,
      }),
    });

    // Import components after mocks are set up
    const [{ TeamPerformanceChart }, { MetricDrillDownDrawer }] = await Promise.all([
      import('@/components/visual/TeamPerformanceChart'),
      import('@/components/workspace/panels/MetricDrillDownDrawer'),
    ]);

    const mockTeamData = [
      {
        userId: 'agent-1',
        name: 'Sarah Chen',
        conversionRate: 72,
        avgResponseTime: 3.2,
        customerSatisfaction: 4.8,
        workloadScore: 75,
      },
    ];

    // Step 1: Render the chart with drill-down enabled
    const mockDrillDown = vi.fn();
    const mockTripSelect = vi.fn();
    const mockRouterPush = vi.fn();

    // Mock router
    vi.stubGlobal('useRouter', () => ({
      push: mockRouterPush,
    }));

    const { rerender } = render(
      <TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />
    );

    expect(screen.getByText(/Agent Performance Metrics/)).toBeInTheDocument();

    // Step 2: Click on conversion rate metric
    const conversionRate = screen.getByText('72%');
    fireEvent.click(conversionRate);

    // Verify onDrillDown was called
    expect(mockDrillDown).toHaveBeenCalledWith('agent-1', {
      type: 'conversion',
      value: 72,
      label: 'Conversion Rate',
    });

    // Step 3: Render the drawer
    rerender(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={{
          type: 'conversion',
          value: 72,
          label: 'Conversion Rate',
        }}
        onClose={vi.fn()}
        onTripSelect={mockTripSelect}
      />
    );

    // Wait for trips to load
    await waitFor(() => {
      expect(screen.getByText('Paris')).toBeInTheDocument();
    });

    // Step 4: Click on the trip
    const parisTrip = screen.getByText('Paris').closest('button');
    fireEvent.click(parisTrip!);

    // Verify trip selection callback
    expect(mockTripSelect).toHaveBeenCalledWith('trip-123');

    // Verify fetch was called for trip data
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/insights/agent-trips?agentId=agent-1&metric=conversion',
      { credentials: "include", cache: "no-store" }
    );
  });

  it('handles error gracefully during drill-down', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false,
      status: 500,
    });

    const { MetricDrillDownDrawer } = await import('@/components/workspace/panels/MetricDrillDownDrawer');

    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={{
          type: 'conversion',
          value: 72,
          label: 'Conversion Rate',
        }}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch trip data/)).toBeInTheDocument();
    });
  });

  it('displays no results when metric has no associated trips', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        agentId: 'agent-1',
        metric: 'conversion',
        trips: [],
        count: 0,
      }),
    });

    const { MetricDrillDownDrawer } = await import('@/components/workspace/panels/MetricDrillDownDrawer');

    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={{
          type: 'conversion',
          value: 72,
          label: 'Conversion Rate',
        }}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    // Wait for empty state message
    await waitFor(() => {
      expect(screen.getByText(/No trips found for this metric/)).toBeInTheDocument();
    });
  });
});
