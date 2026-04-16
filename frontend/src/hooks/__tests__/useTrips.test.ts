import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useTrips, useTripStats, usePipeline } from '../useTrips';

// Mock fetch
global.fetch = vi.fn();

// Mock the api-client module
vi.mock('@/lib/api-client', () => ({
  getTrips: vi.fn(),
  getTrip: vi.fn(),
  getTripStats: vi.fn(),
  getPipeline: vi.fn(),
}));

import { getTrips, getTripStats, getPipeline } from '@/lib/api-client';

describe('useTrips Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches trips successfully', async () => {
    const mockTrips = [
      { id: '1', destination: 'Paris', type: 'leisure', state: 'green', age: '2d' },
      { id: '2', destination: 'Tokyo', type: 'business', state: 'amber', age: '1d' },
    ];

    (getTrips as any).mockResolvedValueOnce({
      items: mockTrips,
      total: 2,
    });

    const { result } = renderHook(() => useTrips());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockTrips);
    expect(result.current.total).toBe(2);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch errors', async () => {
    (getTrips as any).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useTrips());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe('Network error');
  });

  it('passes limit parameter to API', async () => {
    (getTrips as any).mockResolvedValueOnce({
      items: [],
      total: 0,
    });

    renderHook(() => useTrips({ limit: 5 }));

    expect(getTrips).toHaveBeenCalledWith({ limit: 5 });
  });
});

describe('useTripStats Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches stats successfully', async () => {
    const mockStats = {
      active: 12,
      pendingReview: 3,
      readyToBook: 5,
      needsAttention: 2,
    };

    (getTripStats as any).mockResolvedValueOnce(mockStats);

    const { result } = renderHook(() => useTripStats());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockStats);
  });
});

describe('usePipeline Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches pipeline data successfully', async () => {
    const mockPipeline = [
      { label: 'Intake', count: 5 },
      { label: 'Decision', count: 3 },
    ];

    (getPipeline as any).mockResolvedValueOnce(mockPipeline);

    const { result } = renderHook(() => usePipeline());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockPipeline);
  });
});
