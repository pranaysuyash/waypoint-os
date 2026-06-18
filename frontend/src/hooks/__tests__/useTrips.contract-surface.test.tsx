import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { usePipeline, useTripStats, useTrips } from '../useTrips';
import * as apiClient from '@/lib/api-client';

vi.mock('@/lib/api-client');

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useTrips contract-shape safety', () => {
  it('normalizes malformed trips payloads to safe defaults', async () => {
    vi.mocked(apiClient.getTrips).mockResolvedValue({} as never);

    const { result } = renderHook(() => useTrips(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it('normalizes malformed trip stats payloads to null', async () => {
    vi.mocked(apiClient.getTripStats).mockResolvedValue({} as never);

    const { result } = renderHook(() => useTripStats(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('normalizes malformed pipeline payloads to an empty array', async () => {
    vi.mocked(apiClient.getPipeline).mockResolvedValue({} as never);

    const { result } = renderHook(() => usePipeline(), { wrapper: createWrapper() });

    await act(async () => {
      await waitFor(() => expect(result.current.isLoading).toBe(false));
    });

    expect(result.current.data).toEqual([]);
    expect(result.current.error).toBeNull();
  });
});
