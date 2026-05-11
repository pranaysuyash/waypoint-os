import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MetricDrillDownDrawer } from '../MetricDrillDownDrawer';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch
global.fetch = vi.fn();

describe('MetricDrillDownDrawer', () => {
  const mockMetric = {
    type: 'conversion' as const,
    value: 72,
    label: 'Conversion Rate',
  };

  const mockTripsResponse = {
    agentId: 'agent-1',
    metric: 'conversion',
    trips: [
      {
        tripId: 'trip-1',
        destinationName: 'Paris',
        status: 'approved' as const,
        responseTime: 2.5,
        suitabilityScore: 95,
        decisionReason: 'Excellent fit for client profile',
        createdAt: '2024-01-15T10:00:00Z',
      },
      {
        tripId: 'trip-2',
        destinationName: 'Tokyo',
        status: 'rejected' as const,
        responseTime: 4.2,
        suitabilityScore: 35,
        decisionReason: 'Budget mismatch',
        createdAt: '2024-01-14T15:30:00Z',
      },
    ],
    count: 2,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockReset();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockTripsResponse,
    });
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(
      <MetricDrillDownDrawer
        isOpen={false}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders drawer when isOpen is true', async () => {
    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    expect(await screen.findByText(/Conversion Rate Details/)).toBeInTheDocument();
    // Verify the drawer close control is accessible by name.
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
  });

  it('fetches trip data when opened', async () => {
    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/insights/agent-trips?agentId=agent-1&metric=conversion',
        { credentials: "include", cache: "no-store" }
      );
    });
  });

  it('displays loading state while fetching', async () => {
    let resolveFetch: (value: Response) => void = () => {};
    (global.fetch as any).mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        })
    );

    const { unmount } = render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    expect(screen.getByText('Loading trip data…')).toBeInTheDocument();
    await act(async () => {
      resolveFetch(new Response(JSON.stringify(mockTripsResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }));
    });
    unmount();
  });

  it('displays trips after loading', async () => {
    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Paris')).toBeInTheDocument();
      expect(screen.getByText('Tokyo')).toBeInTheDocument();
    });
  });

  it('displays trip details correctly', async () => {
    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Paris')).toBeInTheDocument();
      expect(screen.getByText('approved')).toBeInTheDocument();
      expect(screen.getByText(/2.5h/)).toBeInTheDocument();
      expect(screen.getByText(/95%/)).toBeInTheDocument();
    });
  });

  it('displays decision reason when available', async () => {
    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Excellent fit for client profile/)).toBeInTheDocument();
      expect(screen.getByText(/Budget mismatch/)).toBeInTheDocument();
    });
  });

  it('calls onTripSelect when trip is clicked', async () => {
    const mockTripSelect = vi.fn();
    const user = userEvent.setup();

    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={mockTripSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Paris')).toBeInTheDocument();
    });

    const parisButton = screen.getByText('Paris').closest('button');
    await user.click(parisButton!);

    expect(mockTripSelect).toHaveBeenCalledWith('trip-1');
  });

  it('calls onClose when close button is clicked', async () => {
    const mockClose = vi.fn();
    const user = userEvent.setup();

    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={mockClose}
        onTripSelect={vi.fn()}
      />
    );

    const closeButton = await screen.findByRole('button', { name: 'Close' });
    await user.click(closeButton);

    expect(mockClose).toHaveBeenCalled();
  });

  it('displays error message on fetch failure', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false,
      status: 500,
    });

    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch trip data/)).toBeInTheDocument();
    });
  });

  it('displays no data message when no trips found', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        agentId: 'agent-1',
        metric: 'conversion',
        trips: [],
        count: 0,
      }),
    });

    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/No trips found for this metric/)).toBeInTheDocument();
    });
  });

  it('calls onClose when overlay is clicked', async () => {
    const mockClose = vi.fn();
    const user = userEvent.setup();

    const { container } = render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={mockClose}
        onTripSelect={vi.fn()}
      />
    );

    const overlay = container.querySelector('[class*="bg-black"]');
    await user.click(overlay!);

    expect(mockClose).toHaveBeenCalled();
  });

  it('displays trip count in header', async () => {
    render(
      <MetricDrillDownDrawer
        isOpen={true}
        agentId="agent-1"
        agentName="Sarah Chen"
        metric={mockMetric}
        onClose={vi.fn()}
        onTripSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/2 trips/)).toBeInTheDocument();
    });
  });
});
