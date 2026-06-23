import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api-client';

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

describe('api-client auth refresh retry', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('refreshes once on 401 and retries the original request', async () => {
    const fetchMock = vi.mocked(fetch);
    const events: string[] = [];
    window.addEventListener('waypoint:auth-unauthorized', () => events.push('unauthorized'));

    fetchMock
      .mockResolvedValueOnce(jsonResponse({ message: 'Unauthorized' }, 401))
      .mockResolvedValueOnce(jsonResponse({ ok: true }, 200))
      .mockResolvedValueOnce(jsonResponse({ ok: true, trip_id: 'trip-1' }, 200));

    const result = await api.get<{ ok: boolean; trip_id: string }>('/api/trips/trip-1');

    expect(result.trip_id).toBe('trip-1');
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/trips/trip-1', expect.objectContaining({
      method: 'GET',
      credentials: 'include',
    }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/auth/refresh', expect.objectContaining({
      method: 'POST',
      credentials: 'include',
    }));
    expect(fetchMock).toHaveBeenNthCalledWith(3, '/api/trips/trip-1', expect.objectContaining({
      method: 'GET',
      credentials: 'include',
    }));
    expect(events).toEqual([]);
  });
});
