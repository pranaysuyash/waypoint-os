import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuthStore } from '../auth';

function resetAuthStore() {
  useAuthStore.setState({
    user: null,
    agency: null,
    membership: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });
}

describe('auth store hydrate', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    resetAuthStore();
  });

  it('clears stale user state when hydrate cannot restore the session', async () => {
    useAuthStore.setState({
      user: { id: 'user_1', email: 'stale@example.com', name: 'Stale User' },
      agency: { id: 'agency_1', name: 'Waypoint Travel', slug: 'waypoint' },
      membership: { role: 'owner', isPrimary: true },
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: false });

    vi.stubGlobal('fetch', fetchMock);

    await useAuthStore.getState().hydrate();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(useAuthStore.getState()).toMatchObject({
      user: null,
      agency: null,
      membership: null,
      isAuthenticated: false,
      isLoading: false,
    });
  });
});
