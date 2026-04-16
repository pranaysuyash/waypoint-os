import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useTrips, useTripStats, usePipeline } from '../useTrips';
import * as apiClient from '@/lib/api-client';

// Mock the entire api-client module
vi.mock('@/lib/api-client');

describe('useTrips Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls getTrips API on mount', async () => {
    vi.mocked(apiClient.getTrips).mockResolvedValue({
      items: [],
      total: 0,
    });

    renderHook(() => useTrips());

    await waitFor(
      () => {
        expect(apiClient.getTrips).toHaveBeenCalled();
      },
      { timeout: 2000 }
    );
  });

  it('passes params to getTrips', async () => {
    vi.mocked(apiClient.getTrips).mockResolvedValue({
      items: [],
      total: 0,
    });

    renderHook(() => useTrips({ limit: 5, state: 'pending' }));

    await waitFor(
      () => {
        expect(apiClient.getTrips).toHaveBeenCalledWith({ limit: 5, state: 'pending' });
      },
      { timeout: 2000 }
    );
  });

  it('handles API errors gracefully', async () => {
    vi.mocked(apiClient.getTrips).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useTrips());

    await waitFor(
      () => {
        expect(apiClient.getTrips).toHaveBeenCalled();
      },
      { timeout: 2000 }
    );

    // Error should be set after loading completes
    await waitFor(
      () => {
        expect(result.current.error).toBeInstanceOf(Error);
      },
      { timeout: 2000 }
    );
  });
});

describe('useTripStats Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls getTripStats API on mount', async () => {
    vi.mocked(apiClient.getTripStats).mockResolvedValue({
      active: 0,
      pendingReview: 0,
      readyToBook: 0,
      needsAttention: 0,
    });

    renderHook(() => useTripStats());

    await waitFor(
      () => {
        expect(apiClient.getTripStats).toHaveBeenCalled();
      },
      { timeout: 2000 }
    );
  });
});

describe('usePipeline Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls getPipeline API on mount', async () => {
    vi.mocked(apiClient.getPipeline).mockResolvedValue([]);

    renderHook(() => usePipeline());

    await waitFor(
      () => {
        expect(apiClient.getPipeline).toHaveBeenCalled();
      },
      { timeout: 2000 }
    );
  });
});
