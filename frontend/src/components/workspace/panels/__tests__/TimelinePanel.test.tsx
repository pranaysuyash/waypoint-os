import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TimelinePanel } from '../TimelinePanel';

// Mock fetch
global.fetch = vi.fn();

describe('TimelinePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (global.fetch as any).mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ ok: true, json: async () => ({ trip_id: 'test', events: [] }) }), 100)
      )
    );

    render(<TimelinePanel tripId="test-trip" />);
    expect(screen.getByText(/Loading timeline/i)).toBeInTheDocument();
  });

  it('renders empty state when no timeline events', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ trip_id: 'test', events: [] }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText(/No activity yet/i)).toBeInTheDocument();
    });
  });

  it('renders timeline events', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            status: 'started',
            state_snapshot: { stage: 'intake', status: 'started' },
          },
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:01:00Z',
            stage: 'decision',
            status: 'completed',
            state_snapshot: { stage: 'decision', status: 'completed' },
            decision: 'approve',
            reason: 'Decision engine completed',
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText('Decision Timeline')).toBeInTheDocument();
      expect(screen.getAllByText('Intake').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Quote Assessment').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('displays event count summary', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            status: 'started',
            state_snapshot: { stage: 'intake', status: 'started' },
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText(/captured in this timeline/)).toBeInTheDocument();
    });
  });

  it('renders error message on fetch failure', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('renders retry button on fetch failure and retries on click', async () => {
    const user = userEvent.setup();

    // First call fails
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<TimelinePanel tripId="test-trip" />);

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    // Retry button should be visible
    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();

    // Second call succeeds
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            status: 'started',
            state_snapshot: { stage: 'intake', status: 'started' },
          },
        ],
      }),
    });

    await user.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Decision Timeline')).toBeInTheDocument();
    });

    // Verify fetch was called again
    expect(global.fetch).toHaveBeenCalledWith('/api/trips/test-trip/timeline', expect.any(Object));
  });

  it('fetches timeline from correct endpoint', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ trip_id: 'test-trip', events: [] }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/trips/test-trip/timeline', {
        credentials: "include",
        cache: "no-store",
      });
    });
  });

  it('shows event details including timestamp', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            status: 'started',
            state_snapshot: { stage: 'intake', status: 'started' },
            reason: 'Extraction pipeline completed',
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText(/started/i)).toBeInTheDocument();
      expect(screen.getByText(/Extraction pipeline completed/i)).toBeInTheDocument();
    });
  });

  it('provides stage filter buttons', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            status: 'started',
            state_snapshot: { stage: 'intake', status: 'started' },
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Intake' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Trip Details' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Quote Assessment' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Options' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Safety Review' })).toBeInTheDocument();
    });
  });

  it('fetches timeline with stage filter when stage is selected', async () => {
    const user = userEvent.setup();

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'decision',
            status: 'completed',
            state_snapshot: { stage: 'decision', status: 'completed' },
          },
        ],
      }),
    }).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'decision',
            status: 'completed',
            state_snapshot: { stage: 'decision', status: 'completed' },
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText('Decision Timeline')).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledWith('/api/trips/test-trip/timeline', {
      credentials: "include",
      cache: "no-store",
    });

    await user.click(screen.getByRole("button", { name: "Quote Assessment" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/trips/test-trip/timeline?stage=decision', {
        credentials: "include",
        cache: "no-store",
      });
    });
  });

  // --- Override rendering tests ---

  it('renders override events alongside timeline events', async () => {
    const mockTimeline = {
      trip_id: 'test-trip',
      events: [
        {
          trip_id: 'test-trip',
          timestamp: '2026-04-23T10:00:00Z',
          stage: 'intake',
          status: 'started',
          state_snapshot: { stage: 'intake', status: 'started' },
        },
      ],
    };

    const mockOverrides = {
      ok: true,
      trip_id: 'test-trip',
      overrides: [
        {
          override_id: 'ovr_1',
          trip_id: 'test-trip',
          flag: 'elderly_mobility_risk',
          action: 'downgrade',
          original_severity: 'critical',
          new_severity: 'high',
          reason: 'Client confirmed trekking experience',
          overridden_by: 'agent_priya',
          created_at: '2026-04-23T10:30:00Z',
          scope: 'this_trip',
        },
      ],
      total: 1,
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/overrides')) {
        return Promise.resolve({ ok: true, json: async () => mockOverrides });
      }
      return Promise.resolve({ ok: true, json: async () => mockTimeline });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      // Override action label should be visible
      expect(screen.getByText(/downgraded from CRITICAL to HIGH/i)).toBeInTheDocument();
      // Override label
      expect(screen.getByText('Override')).toBeInTheDocument();
      // Reason text
      expect(screen.getByText(/Client confirmed trekking experience/i)).toBeInTheDocument();
      // Operator
      expect(screen.getByText(/agent_priya/i)).toBeInTheDocument();
    });
  });

  it('sorts override events relative to timeline events by timestamp', async () => {
    const mockTimeline = {
      trip_id: 'test-trip',
      events: [
        {
          trip_id: 'test-trip',
          timestamp: '2026-04-23T10:30:00Z',
          stage: 'decision',
          status: 'completed',
          state_snapshot: { stage: 'decision', status: 'completed' },
        },
      ],
    };

    const mockOverrides = {
      ok: true,
      trip_id: 'test-trip',
      overrides: [
        {
          override_id: 'ovr_1',
          trip_id: 'test-trip',
          flag: 'elderly_mobility_risk',
          action: 'downgrade',
          original_severity: 'critical',
          new_severity: 'high',
          reason: 'Override before decision',
          overridden_by: 'agent_priya',
          created_at: '2026-04-23T10:15:00Z', // Before the decision event
          scope: 'this_trip',
        },
      ],
      total: 1,
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/overrides')) {
        return Promise.resolve({ ok: true, json: async () => mockOverrides });
      }
      return Promise.resolve({ ok: true, json: async () => mockTimeline });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      const list = screen.getByRole('list', { name: /timeline events/i });
      const items = within(list).getAllByRole('listitem');
      expect(items.length).toBe(2);

      // items are sorted ascending by timestamp: override (10:15) then timeline event (10:30)
      expect(items[0].textContent).toMatch(/Override before decision/i);
      expect(items[0].textContent).toMatch(/Override/i);

      expect(items[1].textContent).toMatch(/Completed/i);
      expect(items[1].textContent).toMatch(/Quote Assessment/i);
    });
  });

  it('fetches overrides from the correct endpoint', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      return Promise.resolve({ ok: true, json: async () => {
        if (url.includes('/overrides')) return { ok: true, trip_id: 'test-trip', overrides: [], total: 0 };
        return { trip_id: 'test-trip', events: [] };
      }});
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/trips/test-trip/overrides', expect.any(Object));
    });
  });

  // --- Accessibility tests ---

  it('has accessible stage filter buttons with aria-pressed', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            status: 'started',
            state_snapshot: { stage: 'intake', status: 'started' },
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      const allButton = screen.getByRole('button', { name: 'All' });
      expect(allButton).toHaveAttribute('aria-pressed', 'true');
      const intakeButton = screen.getByRole('button', { name: 'Intake' });
      expect(intakeButton).toHaveAttribute('aria-pressed', 'false');
    });
  });

  it('has timeline event list with role="list" and items with role="listitem"', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        trip_id: 'test-trip',
        events: [
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            status: 'started',
            state_snapshot: { stage: 'intake', status: 'started' },
          },
          {
            trip_id: 'test-trip',
            timestamp: '2026-04-23T10:01:00Z',
            stage: 'decision',
            status: 'completed',
            state_snapshot: { stage: 'decision', status: 'completed' },
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(screen.getByRole('list')).toBeInTheDocument();
      expect(screen.getAllByRole('listitem').length).toBeGreaterThanOrEqual(2);
    });
  });
});
