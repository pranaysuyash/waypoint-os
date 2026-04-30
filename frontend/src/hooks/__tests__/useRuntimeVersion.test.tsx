import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useRuntimeVersion } from '../useRuntimeVersion';

describe('useRuntimeVersion', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('defaults to agency-facing labels instead of engineering chrome', () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    const { result } = renderHook(() => useRuntimeVersion());

    expect(result.current.versionLabel).toBe('Operations live');
    expect(result.current.detailsLabel).toBe('');
  });

  it('keeps agency-facing labels even when runtime metadata loads', async () => {
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

    const { result } = renderHook(() => useRuntimeVersion());

    await waitFor(() => {
      expect(result.current.versionLabel).toBe('Operations live');
      expect(result.current.detailsLabel).toBe('');
    });
  });
});
