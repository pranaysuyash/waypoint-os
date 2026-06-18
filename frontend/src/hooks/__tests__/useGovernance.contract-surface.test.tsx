import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';
import { ReactNode } from 'react';
import {
  usePipelineMetrics,
  useTeamMetrics,
  useBottleneckAnalysis,
  useOperationalAlerts,
  useRevenueMetrics,
  useInsightsSummary,
} from '../useGovernance';
import * as governanceApi from '@/lib/governance-api';

vi.mock('@/lib/governance-api');

type TestWrapperProps = { children: ReactNode };

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: TestWrapperProps) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { Wrapper };
}

describe('useGovernance contract-shape safety', () => {
  it('normalizes missing pipeline metrics payloads to an empty list', async () => {
    vi.mocked(governanceApi.getPipelineMetrics).mockResolvedValue({} as never);

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => usePipelineMetrics('30d'), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('normalizes missing team metrics payloads to an empty list', async () => {
    vi.mocked(governanceApi.getTeamMetrics).mockResolvedValue({} as never);

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useTeamMetrics('30d'), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
  });

  it('normalizes missing bottleneck payloads to an empty list', async () => {
    vi.mocked(governanceApi.getBottleneckAnalysis).mockResolvedValue({} as never);

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useBottleneckAnalysis('30d'), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
  });

  it('normalizes missing operational alerts to an empty list', async () => {
    vi.mocked(governanceApi.getOperationalAlerts).mockResolvedValue({} as never);

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useOperationalAlerts(), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
  });

  it('maps missing revenue metrics to a typed null payload and allows safe reads', async () => {
    vi.mocked(governanceApi.getRevenueMetrics).mockResolvedValue({} as never);

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useRevenueMetrics('30d'), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeNull();
  });

  it('maps missing insights summary to null payload and allows safe reads', async () => {
    vi.mocked(governanceApi.getInsightsSummary).mockResolvedValue({} as never);

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useInsightsSummary('30d'), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeNull();
  });
});
