import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useInboxStats, useWorkloadDistribution } from '../useGovernance';
import { getInboxStats, getWorkloadDistribution } from '@/lib/governance-api';

vi.mock('@/lib/governance-api', () => ({
  getWorkloadDistribution: vi.fn(),
  getInboxStats: vi.fn(),
}));

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('governance hook contract surface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns workload distribution data with safe defaults', async () => {
    vi.mocked(getWorkloadDistribution).mockResolvedValueOnce([
      { memberId: 'u1', name: 'Asha', role: 'admin', capacity: 4, assigned: 2, available: 2, loadPercentage: 50, status: 'optimal' },
    ]);

    const { result } = renderHook(() => useWorkloadDistribution(), { wrapper });

    expect(result.current.data).toEqual([]);
    await waitFor(() => expect(result.current.data).toHaveLength(1));
    expect(getWorkloadDistribution).toHaveBeenCalledOnce();
  });

  it('returns inbox stats with null while loading and backend data once resolved', async () => {
    vi.mocked(getInboxStats).mockResolvedValueOnce({ total: 5, unassigned: 2, critical: 1, atRisk: 3 });

    const { result } = renderHook(() => useInboxStats(), { wrapper });

    expect(result.current.data).toBeNull();
    await waitFor(() => expect(result.current.data).toEqual({ total: 5, unassigned: 2, critical: 1, atRisk: 3 }));
    expect(getInboxStats).toHaveBeenCalledOnce();
  });
});
