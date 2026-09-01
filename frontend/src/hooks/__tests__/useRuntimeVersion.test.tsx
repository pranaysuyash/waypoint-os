import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRuntimeVersion } from '../useRuntimeVersion';
import type { ReactNode } from 'react';

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

describe('useRuntimeVersion', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('defaults to agency-facing labels instead of engineering chrome', () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    const { result } = renderHook(() => useRuntimeVersion(), { wrapper: createWrapper() });

    expect(result.current.versionLabel).toBe('Operations live');
    expect(result.current.detailsLabel).toBe('');
  });

  it('hides the runtime details chip when NEXT_PUBLIC_SHOW_RUNTIME_META is unset (default)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          app: 'waypoint-os',
          version: '1.0.39',
          environment: 'development',
          gitSha: 'abcdef123456',
          generatedAt: '2026-04-30T08:00:00Z',
        }),
      })
    );

    const { result } = renderHook(() => useRuntimeVersion(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.versionLabel).toBe('v1.0.39');
      expect(result.current.detailsLabel).toBe('');
    });
  });

  it('shows runtime metadata details when NEXT_PUBLIC_SHOW_RUNTIME_META is enabled', async () => {
    vi.stubEnv('NEXT_PUBLIC_SHOW_RUNTIME_META', '1');
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          app: 'waypoint-os',
          version: '1.0.39',
          environment: 'development',
          gitSha: 'abcdef123456',
          generatedAt: '2026-04-30T08:00:00Z',
        }),
      })
    );

    const { result } = renderHook(() => useRuntimeVersion(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.versionLabel).toBe('v1.0.39');
      expect(result.current.detailsLabel).toBe('runtime · development · abcdef1');
    });
  });
});
