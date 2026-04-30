import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTrips, useTrip, useTripStats, usePipeline, useUpdateTrip, useStartPlanning } from '../useTrips';
import * as apiClient from '@/lib/api-client';
import type { Trip } from '@/lib/api-client';
import type { ReactNode } from 'react';

vi.mock('@/lib/api-client');

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

function createHarness() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { Wrapper, queryClient };
}

beforeEach(() => {
  vi.clearAllMocks();
});

function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: '1',
    destination: 'Test',
    type: 'leisure',
    state: 'green',
    age: '1d',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

describe('useTrips Hook', () => {
  it('calls getTrips API on mount', async () => {
    vi.mocked(apiClient.getTrips).mockResolvedValue({ items: [], total: 0 });

    renderHook(() => useTrips(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(apiClient.getTrips).toHaveBeenCalled();
    });
  });

  it('passes params to getTrips', async () => {
    vi.mocked(apiClient.getTrips).mockResolvedValue({ items: [], total: 0 });

    renderHook(() => useTrips({ limit: 5, state: 'pending' }), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(apiClient.getTrips).toHaveBeenCalledWith({ limit: 5, state: 'pending' });
    });
  });

  it('handles API errors gracefully and resets total', async () => {
    vi.mocked(apiClient.getTrips).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useTrips(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.error).toBeInstanceOf(Error);
    });

    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.isLoading).toBe(false);
  });

  it('deduplicates by query key (built-in TanStack Query)', async () => {
    let resolveA!: (v: { items: Trip[]; total: number }) => void;
    let resolveB!: (v: { items: Trip[]; total: number }) => void;

    vi.mocked(apiClient.getTrips)
      .mockReturnValueOnce(new Promise<{ items: Trip[]; total: number }>((r) => { resolveA = r; }))
      .mockReturnValueOnce(new Promise<{ items: Trip[]; total: number }>((r) => { resolveB = r; }));

    const { result, rerender } = renderHook(
      (props: { state?: string } = {}) => useTrips(props),
      { initialProps: { state: 'new' }, wrapper: createWrapper() },
    );

    rerender({ state: 'assigned' });

    resolveB({ items: [makeTrip({ id: 'b' })], total: 1 });

    await waitFor(() => {
      expect(result.current.data[0]?.id).toBe('b');
    });

    resolveA({ items: [makeTrip({ id: 'a' })], total: 5 });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(result.current.data[0]?.id).toBe('b');
    expect(result.current.total).toBe(1);
  });

  it('refetch returns fresh data', async () => {
    vi.mocked(apiClient.getTrips).mockResolvedValue({ items: [], total: 0 });

    const { result } = renderHook(() => useTrips(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.data).toEqual([]);
    });

    vi.mocked(apiClient.getTrips).mockResolvedValue({ items: [makeTrip()], total: 1 });

    await act(async () => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.data).toHaveLength(1);
    });
    expect(result.current.total).toBe(1);
  });

  it('clears error before each fetch', async () => {
    vi.mocked(apiClient.getTrips).mockRejectedValueOnce(new Error('Fail'))
      .mockResolvedValueOnce({ items: [], total: 0 });

    const { result } = renderHook(() => useTrips(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.error).toBeInstanceOf(Error);
    });

    await act(async () => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });
});

describe('useTrip Hook', () => {
  it('fetches trip by id', async () => {
    vi.mocked(apiClient.getTrip).mockResolvedValue(makeTrip({ id: '42', destination: 'London' }));

    const { result } = renderHook(() => useTrip('42'), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.data?.id).toBe('42');
    });
    expect(result.current.isLoading).toBe(false);
  });

  it('returns null when id is null', async () => {
    const { result } = renderHook(() => useTrip(null), { wrapper: createWrapper() });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('handles API errors gracefully', async () => {
    vi.mocked(apiClient.getTrip).mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useTrip('99'), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.error).toBeInstanceOf(Error);
    });
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('clears data when id changes (enabled toggle)', async () => {
    vi.mocked(apiClient.getTrip).mockResolvedValue(makeTrip({ id: '1' }));

    const { result, rerender } = renderHook(
      (id: string | null = '1') => useTrip(id),
      { initialProps: '1' as string | null, wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.data?.id).toBe('1');
    });

    rerender(null);

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('ignores stale responses from previous ids', async () => {
    let resolveA!: (v: Trip) => void;
    let resolveB!: (v: Trip) => void;

    vi.mocked(apiClient.getTrip)
      .mockReturnValueOnce(new Promise<Trip>((r) => { resolveA = r; }))
      .mockReturnValueOnce(new Promise<Trip>((r) => { resolveB = r; }));

    const { result, rerender } = renderHook(
      (id: string | null = 'a') => useTrip(id),
      { initialProps: 'a' as string | null, wrapper: createWrapper() },
    );

    rerender('b');

    resolveB(makeTrip({ id: 'b' }));

    await waitFor(() => {
      expect(result.current.data?.id).toBe('b');
    });

    resolveA(makeTrip({ id: 'a' }));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(result.current.data?.id).toBe('b');
  });
});

describe('useStartPlanning Hook', () => {
  it('calls the explicit start-planning transition and invalidates trip queries', async () => {
    vi.mocked((apiClient as any).startPlanningTrip).mockResolvedValue({ success: true, trip_id: '1' });

    const { Wrapper, queryClient } = createHarness();
    const invalidateQueries = vi.spyOn(queryClient, 'invalidateQueries');
    const { result } = renderHook(() => useStartPlanning(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutate('1', 'agent-1', 'Alex Agent');
    });

    expect((apiClient as any).startPlanningTrip).toHaveBeenCalledWith('1', 'agent-1', 'Alex Agent');
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['trips'],
    });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['governance', 'inboxTrips'],
    });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['governance', 'inboxStats'],
    });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['system', 'unified-state'],
    });
  });
});

describe('useTripStats Hook', () => {
  it('calls getTripStats API on mount', async () => {
    vi.mocked(apiClient.getTripStats).mockResolvedValue({ active: 5, pendingReview: 3, readyToBook: 2, needsAttention: 1 });

    renderHook(() => useTripStats(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(apiClient.getTripStats).toHaveBeenCalled();
    });
  });

  it('preserves stale data on refetch error (dashboard pattern)', async () => {
    const stats = { active: 5, pendingReview: 3, readyToBook: 2, needsAttention: 1 };
    vi.mocked(apiClient.getTripStats).mockResolvedValueOnce(stats);

    const { result } = renderHook(() => useTripStats(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.data).toEqual(stats);
    });

    vi.mocked(apiClient.getTripStats).mockRejectedValueOnce(new Error('Stats error'));

    await act(async () => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.error).toBeInstanceOf(Error);
    });
    expect(result.current.data).toEqual(stats);
  });
});

describe('usePipeline Hook', () => {
  it('calls getPipeline API on mount', async () => {
    vi.mocked(apiClient.getPipeline).mockResolvedValue([]);

    renderHook(() => usePipeline(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(apiClient.getPipeline).toHaveBeenCalled();
    });
  });

  it('resets to empty array on error', async () => {
    vi.mocked(apiClient.getPipeline).mockRejectedValue(new Error('Pipeline error'));

    const { result } = renderHook(() => usePipeline(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.error).toBeInstanceOf(Error);
    });
    expect(result.current.data).toEqual([]);
  });
});

describe('useUpdateTrip Hook', () => {
  it('returns updated trip on success', async () => {
    vi.mocked(apiClient.updateTrip).mockResolvedValue(makeTrip({ id: '1', destination: 'Paris' }));

    const { result } = renderHook(() => useUpdateTrip(), { wrapper: createWrapper() });

    await act(async () => {
      const updated = await result.current.mutate('1', { destination: 'Paris' });
      expect(updated?.id).toBe('1');
    });
    expect(result.current.isSaving).toBe(false);
  });

  it('handles save error', async () => {
    vi.mocked(apiClient.updateTrip).mockRejectedValue(new Error('Save failed'));

    const { result } = renderHook(() => useUpdateTrip(), { wrapper: createWrapper() });

    void result.current.mutate('1', { destination: 'Paris' }).catch(() => {});

    await waitFor(() => {
      expect(result.current.error).toBeInstanceOf(Error);
    });
    expect(result.current.isSaving).toBe(false);
  });

  it('is not saving initially', async () => {
    const { result } = renderHook(() => useUpdateTrip(), { wrapper: createWrapper() });

    expect(result.current.isSaving).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
