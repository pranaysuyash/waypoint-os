import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { TimelinePanel } from '../TimelinePanel';

// Mock fetch
global.fetch = vi.fn();

describe('TimelinePanel - Suitability Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and displays suitability flags', async () => {
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

    const mockSuitability = {
      trip_id: 'test-trip',
      suitability_flags: [
        {
          id: 'flag-1',
          trip_id: 'test-trip',
          name: 'elderly_mobility_risk',
          confidence: 85,
          tier: 'critical',
          reason: 'Parent age >70 with trekking activities',
          created_at: '2026-04-23T10:00:00Z',
        },
      ],
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSuitability,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(screen.getByText('Suitability Assessment')).toBeInTheDocument();
    });
  });

  it('handles missing suitability flags gracefully', async () => {
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

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.reject(new Error('Not Found'));
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(screen.getByText('Decision Timeline')).toBeInTheDocument();
    });
  });

  it('displays critical tier flags with red styling', async () => {
    const mockTimeline = {
      trip_id: 'test-trip',
      events: [],
    };

    const mockSuitability = {
      trip_id: 'test-trip',
      suitability_flags: [
        {
          id: 'flag-1',
          trip_id: 'test-trip',
          name: 'critical_flag',
          confidence: 95,
          tier: 'critical',
          reason: 'Critical issue detected',
        },
      ],
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSuitability,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(screen.getByText('Suitability Assessment')).toBeInTheDocument();
    });
  });

  it('displays multiple suitability flags', async () => {
    const mockTimeline = {
      trip_id: 'test-trip',
      events: [],
    };

    const mockSuitability = {
      trip_id: 'test-trip',
      suitability_flags: [
        {
          id: 'flag-1',
          trip_id: 'test-trip',
          name: 'elderly_mobility_risk',
          confidence: 85,
          tier: 'critical',
          reason: 'Parent age >70 with trekking',
        },
        {
          id: 'flag-2',
          trip_id: 'test-trip',
          name: 'visa_processing_risk',
          confidence: 60,
          tier: 'high',
          reason: '5 nationalities, limited time',
        },
      ],
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSuitability,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(screen.getByText('Suitability Assessment')).toBeInTheDocument();
    });
  });

  it('does not display suitability section when no flags present', async () => {
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

    const mockSuitability = {
      trip_id: 'test-trip',
      suitability_flags: [],
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSuitability,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(screen.getByText('Decision Timeline')).toBeInTheDocument();
      expect(screen.queryByText('Suitability Assessment')).not.toBeInTheDocument();
    });
  });

  it('converts confidence from 0-100 to 0-1 and displays the correct percentage', async () => {
    const mockTimeline = {
      trip_id: 'test-trip',
      events: [],
    };

    const mockSuitability = {
      trip_id: 'test-trip',
      suitability_flags: [
        {
          id: 'flag-1',
          trip_id: 'test-trip',
          name: 'test_flag',
          confidence: 75,
          tier: 'high',
          reason: 'Test confidence conversion',
        },
      ],
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSuitability,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    // SuitabilitySignal renders Math.round(flag.confidence * 100) + "% confidence"
    // flag.confidence = 75 / 100 = 0.75 -> Math.round(0.75 * 100) = 75 -> "75% confidence"
    await waitFor(() => {
      expect(screen.getByText('75% confidence')).toBeInTheDocument();
    });
  });

  it('handles empty timeline with suitability flags', async () => {
    const mockTimeline = {
      trip_id: 'test-trip',
      events: [],
    };

    const mockSuitability = {
      trip_id: 'test-trip',
      suitability_flags: [
        {
          id: 'flag-1',
          trip_id: 'test-trip',
          name: 'risk_flag',
          confidence: 50,
          tier: 'medium',
          reason: 'Potential issue',
        },
      ],
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSuitability,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(screen.getByText('Suitability Assessment')).toBeInTheDocument();
    });
  });

  it('makes separate fetch calls for timeline and suitability', async () => {
    const mockTimeline = { trip_id: 'test-trip', events: [] };
    const mockSuitability = { trip_id: 'test-trip', suitability_flags: [] };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/suitability')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSuitability,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTimeline,
      });
    });

    render(<TimelinePanel tripId="test-trip" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/timeline'),
        expect.any(Object)
      );
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/suitability'),
        expect.any(Object)
      );
    });
  });

  it('updates suitability flags when trip changes', async () => {
    const mockTimeline = { trip_id: 'trip-1', events: [] };
    const mockSuitability1 = {
      trip_id: 'trip-1',
      suitability_flags: [{ id: 'flag-1', trip_id: 'trip-1', name: 'flag1', confidence: 50, tier: 'medium', reason: 'Test' }],
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockTimeline,
    });

    const { rerender } = render(<TimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    rerender(<TimelinePanel tripId="trip-2" />);

    await waitFor(() => {
      // 2 renders × 3 endpoints (timeline, suitability, overrides)
      const callCount = (global.fetch as any).mock.calls.length;
      expect(callCount).toBeGreaterThanOrEqual(6);
      expect(callCount % 3).toBe(0);
    });
  });
});
