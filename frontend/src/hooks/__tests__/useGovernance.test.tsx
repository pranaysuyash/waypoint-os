import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useInboxTrips, useReviews } from '../useGovernance';
import * as governanceApi from '@/lib/governance-api';

vi.mock('@/lib/governance-api');

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { Wrapper, queryClient };
}

describe('useGovernance', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(governanceApi.getReviews).mockResolvedValue({
      items: [],
      total: 0,
    } as never);
    vi.mocked(governanceApi.getInboxTrips).mockResolvedValue({
      items: [],
      total: 0,
      hasMore: false,
    } as never);
  });

  it('invalidates the full reviews query family after review actions', async () => {
    vi.mocked(governanceApi.submitReviewAction).mockResolvedValue({ success: true } as never);
    const { Wrapper, queryClient } = createWrapper();
    const invalidateQueries = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useReviews({ status: 'pending' }), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(governanceApi.getReviews).toHaveBeenCalledWith({ status: 'pending' });
    });

    await act(async () => {
      await result.current.submitAction({
        review_id: 'review-1',
        action: 'approve',
      } as never);
    });

    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['governance', 'reviews'],
    });
  });

  it('invalidates inbox queues by family prefix and refreshes inbox stats after inbox actions', async () => {
    vi.mocked(governanceApi.assignTrips).mockResolvedValue({ assigned: 1 } as never);
    const { Wrapper, queryClient } = createWrapper();
    const invalidateQueries = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useInboxTrips(undefined, 1, 20), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(governanceApi.getInboxTrips).toHaveBeenCalledWith(undefined, 1, 20);
    });

    await act(async () => {
      await result.current.assignTrips({
        trip_ids: ['trip-1'],
        assignee_id: 'owner-1',
      } as never);
    });

    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['governance', 'inboxTrips'],
    });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['governance', 'inboxStats'],
    });
  });
});
