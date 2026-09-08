// The companion worker owns only these public, query-free shell resources.
// It must never replay private itinerary/API responses from Cache Storage.
const CACHE_NAME = 'waypoint-companion-shell-v2';
const SHELL_PATHS = ['/companion', '/manifest.json'];
const SHELL_PATH_SET = new Set(SHELL_PATHS);

function isCacheableResponse(response) {
  if (!response || response.ok !== true) {
    return false;
  }

  const cacheControl = response.headers?.get?.('cache-control') || '';
  return !/(?:^|,)\s*(?:no-store|private)(?:\s*(?:=|,|$))/i.test(cacheControl);
}

function isOwnedShellRequest(request) {
  const url = new URL(request.url);

  return (
    url.origin === self.location.origin &&
    request.method === 'GET' &&
    request.cache !== 'no-store' &&
    url.search === '' &&
    SHELL_PATH_SET.has(url.pathname)
  );
}

async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);

    if (isCacheableResponse(networkResponse)) {
      try {
        const cache = await caches.open(CACHE_NAME);
        await cache.put(request, networkResponse.clone());
      } catch (_cacheError) {
        // A cache quota or storage error must not turn a fresh network response
        // into an outage. The shell remains usable online.
      }
    }

    return networkResponse;
  } catch (networkError) {
    try {
      const cache = await caches.open(CACHE_NAME);
      const cachedResponse = await cache.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
    } catch (_cacheError) {
      // Preserve the original network failure when the owned cache is absent
      // or unavailable; never search another cache or replay another request.
    }

    throw networkError;
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    try {
      const cache = await caches.open(CACHE_NAME);
      await Promise.all(SHELL_PATHS.map(async (path) => {
        const response = await fetch(path);
        if (isCacheableResponse(response)) {
          await cache.put(path, response.clone());
        }
      }));
    } catch (_warmupError) {
      // Warmup is an optional offline optimization. A quota or network error
      // must not prevent the online worker from installing and taking control.
    }
  })());
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Deliberately do not enumerate or delete Cache Storage entries here.
  // Legacy companion and unrelated application caches are user state; any
  // future retirement needs a separately scoped, explicit migration policy.
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  if (!isOwnedShellRequest(event.request)) {
    return;
  }

  event.respondWith(networkFirst(event.request));
});
