import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

import { describe, expect, it, vi } from 'vitest';

type CacheEntry = { url: string; value: unknown };

type FakeCache = {
  entries: Map<string, unknown>;
  addAll: ReturnType<typeof vi.fn>;
  match: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
};

function createCacheStorage() {
  const cacheByName = new Map<string, FakeCache>();
  const createCache = (name: string): FakeCache => {
    const entries = new Map<string, unknown>();
    const cache: FakeCache = {
      entries,
      addAll: vi.fn(async (paths: string[]) => {
        for (const path of paths) {
          entries.set(new URL(path, 'https://companion.example').href, {
            cacheName: name,
            path,
          });
        }
      }),
      match: vi.fn(async (request: { url: string } | string) => {
        const url = typeof request === 'string' ? new URL(request, 'https://companion.example').href : request.url;
        return entries.get(url);
      }),
      put: vi.fn(async (request: { url: string } | string, value: unknown) => {
        const url = typeof request === 'string' ? new URL(request, 'https://companion.example').href : request.url;
        entries.set(url, value);
      }),
    };
    cacheByName.set(name, cache);
    return cache;
  };

  return {
    cacheByName,
    caches: {
      open: vi.fn(async (name: string) => cacheByName.get(name) ?? createCache(name)),
      keys: vi.fn(async () => [...cacheByName.keys()]),
      delete: vi.fn(async (name: string) => cacheByName.delete(name)),
    },
  };
}

async function loadWorker(fetchImpl = vi.fn()) {
  const source = await readFile(`${process.cwd()}/public/sw.js`, 'utf8');
  const events = new Map<string, (event: Record<string, unknown>) => void>();
  const cacheStorage = createCacheStorage();
  const self = {
    addEventListener: vi.fn((type: string, handler: (event: Record<string, unknown>) => void) => {
      events.set(type, handler);
    }),
    clients: { claim: vi.fn(async () => undefined) },
    location: { origin: 'https://companion.example' },
    skipWaiting: vi.fn(async () => undefined),
  };

  vm.runInNewContext(source, {
    URL,
    caches: cacheStorage.caches,
    console,
    fetch: fetchImpl,
    self,
  }, { filename: 'public/sw.js' });

  // Seed the worker-owned namespace without running lifecycle events. Tests
  // invoke install/activate explicitly when those lifecycle contracts matter.
  await cacheStorage.caches.open('waypoint-companion-shell-v2');

  return { ...cacheStorage, events, fetchImpl, self };
}

function request(url: string, init: { cache?: string; method?: string } = {}) {
  return {
    cache: init.cache ?? 'default',
    method: init.method ?? 'GET',
    url: new URL(url, 'https://companion.example').href,
  };
}

function response(value: unknown, ok = true, cacheControl?: string) {
  return {
    body: value,
    clone: vi.fn(() => response(value, ok, cacheControl)),
    ok,
    headers: { get: (name: string) => name.toLowerCase() === 'cache-control' ? cacheControl : null },
  };
}

function fetchEvent(worker: Awaited<ReturnType<typeof loadWorker>>, req: ReturnType<typeof request>) {
  const event: Record<string, unknown> & { response?: Promise<unknown> } = {
    request: req,
    respondWith: vi.fn((value: Promise<unknown>) => {
      event.response = Promise.resolve(value);
    }),
  };
  worker.events.get('fetch')?.(event);
  return event;
}

describe('companion service-worker cache boundary', () => {
  it('refreshes the allowlisted shell from the network and stores it in the v2 cache', async () => {
    const fetchImpl = vi.fn(async () => response('fresh manifest'));
    const worker = await loadWorker(fetchImpl);

    const event = fetchEvent(worker, request('/manifest.json'));

    await expect(event.response).resolves.toMatchObject({ body: 'fresh manifest' });
    expect(fetchImpl).toHaveBeenCalledOnce();
    expect(worker.cacheByName.get('waypoint-companion-shell-v2')?.put).toHaveBeenCalledOnce();
  });

  it('falls back only to the owned shell cache after a network failure', async () => {
    const fetchImpl = vi.fn(async () => { throw new Error('offline'); });
    const worker = await loadWorker(fetchImpl);
    const ownedCache = worker.cacheByName.get('waypoint-companion-shell-v2');
    ownedCache?.entries.set(
      new URL('/companion', 'https://companion.example').href,
      response('cached shell'),
    );

    const event = fetchEvent(worker, request('/companion'));

    await expect(event.response).resolves.toMatchObject({ body: 'cached shell' });
    expect(ownedCache?.match).toHaveBeenCalledOnce();
  });

  it.each(['no-store', 'private="trip"'])('does not cache a %s network response', async (cacheControl) => {
    const fetchImpl = vi.fn(async () => response('uncacheable', true, cacheControl));
    const worker = await loadWorker(fetchImpl);
    const ownedCache = worker.cacheByName.get('waypoint-companion-shell-v2');

    const event = fetchEvent(worker, request('/manifest.json'));

    await expect(event.response).resolves.toMatchObject({ body: 'uncacheable' });
    expect(ownedCache?.put).not.toHaveBeenCalled();
  });

  it('returns a fresh shell when owned-cache refresh fails', async () => {
    const fetchImpl = vi.fn(async () => response('fresh despite quota'));
    const worker = await loadWorker(fetchImpl);
    const ownedCache = worker.cacheByName.get('waypoint-companion-shell-v2');
    ownedCache?.put.mockRejectedValueOnce(new Error('quota exceeded'));

    const event = fetchEvent(worker, request('/companion'));

    await expect(event.response).resolves.toMatchObject({ body: 'fresh despite quota' });
  });

  it.each([
    ['API route', request('/api/public/journey-graph/trip-a?token=share-a')],
    ['no-store shell request', request('/companion', { cache: 'no-store' })],
    ['token query variant', request('/companion?token=share-a')],
    ['non-GET shell request', request('/companion', { method: 'POST' })],
    ['cross-origin request', { cache: 'default', method: 'GET', url: 'https://other.example/companion' }],
  ])('does not intercept %s', async (_label, req) => {
    const fetchImpl = vi.fn(async () => { throw new Error('offline'); });
    const worker = await loadWorker(fetchImpl);

    const event = fetchEvent(worker, req);

    expect(event.respondWith).not.toHaveBeenCalled();
    expect(event.response).toBeUndefined();
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it('does not replay a cached private API response after a network failure', async () => {
    const fetchImpl = vi.fn(async () => { throw new Error('offline'); });
    const worker = await loadWorker(fetchImpl);
    const ownedCache = worker.cacheByName.get('waypoint-companion-shell-v2');
    ownedCache?.entries.set(
      new URL('/api/public/journey-graph/trip-a?token=share-a', 'https://companion.example').href,
      response('private itinerary'),
    );

    const event = fetchEvent(worker, request('/api/public/journey-graph/trip-a?token=share-a'));

    expect(event.respondWith).not.toHaveBeenCalled();
    expect(event.response).toBeUndefined();
    expect(ownedCache?.match).not.toHaveBeenCalled();
  });

  it('preserves legacy and unrelated caches during activation', async () => {
    const worker = await loadWorker();
    worker.cacheByName.set('waypoint-companion-v1', worker.cacheByName.get('waypoint-companion-shell-v2')!);
    worker.cacheByName.set('unrelated-app-cache', {
      entries: new Map<string, CacheEntry>(),
      addAll: vi.fn(),
      match: vi.fn(),
      put: vi.fn(),
    });

    const event: Record<string, unknown> = {
      waitUntil: vi.fn((value: Promise<unknown>) => { event.promise = Promise.resolve(value); }),
    };
    worker.events.get('activate')?.(event);
    await event.promise;

    expect(worker.self.clients.claim).toHaveBeenCalledOnce();
    expect(worker.caches.keys).not.toHaveBeenCalled();
    expect(worker.caches.delete).not.toHaveBeenCalled();
    expect(worker.cacheByName.has('waypoint-companion-v1')).toBe(true);
    expect(worker.cacheByName.has('unrelated-app-cache')).toBe(true);
  });

  it('keeps the worker installable when optional warmup fails', async () => {
    const worker = await loadWorker(vi.fn(async () => response('install shell')));
    const ownedCache = worker.cacheByName.get('waypoint-companion-shell-v2');
    ownedCache?.put.mockRejectedValueOnce(new Error('cache unavailable'));
    const event: Record<string, unknown> = {
      waitUntil: vi.fn((value: Promise<unknown>) => { event.promise = Promise.resolve(value); }),
    };

    worker.events.get('install')?.(event);

    await expect(event.promise).resolves.toBeUndefined();
    expect(worker.self.skipWaiting).toHaveBeenCalledOnce();
  });

  it('does not store no-store responses during install warmup', async () => {
    const worker = await loadWorker(vi.fn(async () => response('online shell', true, 'no-store')));
    const ownedCache = worker.cacheByName.get('waypoint-companion-shell-v2');
    const event: Record<string, unknown> = {
      waitUntil: vi.fn((value: Promise<unknown>) => { event.promise = Promise.resolve(value); }),
    };

    worker.events.get('install')?.(event);
    await event.promise;

    expect(ownedCache?.put).not.toHaveBeenCalled();
  });
});
