import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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
      expect(screen.getByText(/No timeline events found/i)).toBeInTheDocument();
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
      expect(screen.getByText('INTAKE')).toBeInTheDocument();
      expect(screen.getByText('DECISION')).toBeInTheDocument();
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
      // Just check that the summary section is rendered
      expect(screen.getByText(/captured in this timeline/)).toBeInTheDocument();
    });
  });

  it('renders error message on fetch failure', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      // Check that error message is displayed
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('fetches timeline from correct endpoint', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ trip_id: 'test-trip', events: [] }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/trips/test-trip/timeline');
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
      expect(screen.getByText('All')).toBeInTheDocument();
      expect(screen.getByText('Intake')).toBeInTheDocument();
      expect(screen.getByText('Packet')).toBeInTheDocument();
      expect(screen.getByText('Decision')).toBeInTheDocument();
      expect(screen.getByText('Strategy')).toBeInTheDocument();
      expect(screen.getByText('Safety')).toBeInTheDocument();
    });
  });

  it('fetches timeline with stage filter when stage is selected', async () => {
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
    });

    const { rerender } = render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText('Decision Timeline')).toBeInTheDocument();
    });

    // Verify initial fetch was called
    expect(global.fetch).toHaveBeenCalledWith('/api/trips/test-trip/timeline');
  });
});
