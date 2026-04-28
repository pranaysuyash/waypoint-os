# Mobile Experience — PWA Architecture

> Research document for progressive web app architecture, service workers, and web capabilities.

---

## Key Questions

1. **What's the current state of PWA capabilities on iOS and Android?**
2. **What's the optimal caching strategy for travel content (static vs. dynamic)?**
3. **How do we handle authentication in a PWA (session persistence, biometric)?**
4. **What's the install experience, and how do we encourage it?**
5. **How do we measure PWA performance vs. native benchmarks?**

---

## Research Areas

### Service Worker Strategy

```typescript
interface ServiceWorkerConfig {
  // Caching strategies by resource type
  cachingStrategies: {
    // Static assets (JS, CSS, fonts) — cache first
    staticAssets: {
      strategy: 'cache_first';
      maxAge: '30d';
      maxEntries: 100;
    };
    // API responses — stale while revalidate
    apiData: {
      strategy: 'stale_while_revalidate';
      maxAge: '5m';
      cacheableEndpoints: string[];
    };
    // Images — cache first with fallback
    images: {
      strategy: 'cache_first';
      maxAge: '7d';
      fallback: '/placeholder.svg';
    };
    // Itinerary data — network first, cache fallback
    criticalData: {
      strategy: 'network_first';
      timeout: 3000;               // Fall back to cache after 3s
      cacheName: 'itinerary-cache';
    };
  };
  // Offline fallback page
  offlineFallback: '/offline';
  // Background sync for mutations
  backgroundSync: {
    enabled: boolean;
    queueName: 'offline-mutations';
    maxRetention: '24h';
  };
}
```

### Offline Data Model

```typescript
interface OfflineDataStore {
  // What data to cache for offline access
  entities: OfflineEntity[];
  // Sync strategy
  syncStrategy: SyncStrategy;
  // Storage budget
  maxStorageMB: number;
}

interface OfflineEntity {
  entity: string;                // 'itinerary', 'voucher', 'trip'
  syncDirection: 'read_only' | 'read_write';
  priority: 'critical' | 'important' | 'nice_to_have';
  // Which fields to cache (subset for bandwidth)
  fieldsToCache: string[];
  // How long cached data is valid
  validityPeriod: string;
  // Conflict resolution strategy
  conflictResolution: 'server_wins' | 'client_wins' | 'merge' | 'manual';
}

// Critical offline data:
// 1. Current trip itinerary (days, segments, addresses, contacts)
// 2. Booking vouchers and confirmations
// 3. Emergency contact numbers
// 4. Hotel/transfer addresses and phone numbers
// 5. Customer support chat (last 50 messages)
```

### Web Push Notifications

```typescript
interface PushConfig {
  // Push subscription management
  subscriptionEndpoint: string;
  // Notification types that can be pushed
  supportedNotifications: PushNotificationType[];
  // Permission request timing
  permissionStrategy: 'on_load' | 'after_value' | 'manual';
}

type PushNotificationType =
  | 'trip_reminder'           // "Your flight departs in 3 hours"
  | 'booking_update'          // "Your hotel booking is confirmed"
  | 'travel_alert'            // "Weather alert for your destination"
  | 'agent_message'           // "Your agent sent you a message"
  | 'payment_reminder'        // "Payment due in 24 hours"
  | 'check_in_reminder';      // "Online check-in is now open"
```

### Install Experience

```typescript
interface InstallPrompt {
  // When to show install prompt
  trigger: InstallTrigger;
  // What to show
  message: string;
  incentive?: string;
}

type InstallTrigger =
  | 'after_3_visits'          // User visited 3+ times
  | 'after_booking'           // Just completed a booking
  | 'after_itinerary_view'    // Viewed itinerary (will need offline)
  | 'manual';                 // User clicked "install" button

// iOS-specific: No auto-prompt. Must guide users to
// "Share → Add to Home Screen" with visual instructions
```

---

## Open Problems

1. **iOS PWA limitations** — No push notifications when PWA is closed, 50MB storage cap, no background sync. These are fundamental limitations that may require a native wrapper.

2. **Offline mutation complexity** — Allowing customers to make changes offline (add a note, save a preference) and syncing when online requires a robust queue and conflict resolution system.

3. **Cache invalidation** — When an itinerary is updated server-side, how to push the update to the service worker cache. Version-based invalidation with background refresh.

4. **Authentication persistence** — Keeping the user logged in across sessions without storing tokens insecurely. Need secure token storage in IndexedDB.

5. **Performance on slow networks** — 3G connections in rural India need special attention. Skeleton screens, progressive image loading, and minimal JavaScript.

---

## Next Steps

- [ ] Audit current Next.js app for PWA readiness
- [ ] Research iOS PWA support status (Webkit blog, caniuse)
- [ ] Design offline data strategy for itinerary and voucher access
- [ ] Prototype service worker with stale-while-revalidate caching
- [ ] Evaluate Capacitor/Ionic as native wrapper over PWA (best of both)
