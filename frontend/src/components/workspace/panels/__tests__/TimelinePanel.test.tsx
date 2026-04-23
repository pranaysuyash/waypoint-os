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
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            state: 'extracted',
            version: '1.0',
          },
          {
            timestamp: '2026-04-23T10:01:00Z',
            stage: 'decision',
            state: 'PROCEED_TRAVELER_SAFE',
            version: '1.0',
            decision_type: 'gap_and_decision',
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
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            state: 'extracted',
            version: '1.0',
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText(/1 events captured in this timeline/i)).toBeInTheDocument();
    });
  });

  it('renders error message on fetch failure', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load timeline/i)).toBeInTheDocument();
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
            timestamp: '2026-04-23T10:00:00Z',
            stage: 'intake',
            state: 'extracted',
            version: '1.0',
            reason: 'Extraction pipeline completed',
          },
        ],
      }),
    });

    render(<TimelinePanel tripId="test-trip" />);
    
    await waitFor(() => {
      expect(screen.getByText(/extracted/i)).toBeInTheDocument();
      expect(screen.getByText(/Extraction pipeline completed/i)).toBeInTheDocument();
    });
  });
});
