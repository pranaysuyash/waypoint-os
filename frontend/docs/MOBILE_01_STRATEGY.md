# Mobile Experience — Strategy & Platform Decisions

> Research document for mobile strategy, platform choices, and mobile-first design decisions.

---

## Key Questions

1. **Do we need a native app, a PWA, or is responsive web sufficient?**
2. **What are the primary mobile use cases for agents vs. customers?**
3. **What's the market split between iOS and Android for our target users?**
4. **What mobile capabilities do we need (push, offline, camera, location)?**
5. **What's the cost of maintaining multiple platforms?**

---

## Research Areas

### Mobile Use Cases by Role

```typescript
interface MobileUseCase {
  role: 'agent' | 'customer' | 'operations';
  scenario: string;
  frequency: 'constant' | 'frequent' | 'occasional';
  mustWorkOffline: boolean;
  requiresNative: boolean;      // Camera, push, biometrics
  priority: 'must_have' | 'should_have' | 'nice_to_have';
}

// Agent use cases:
// - View today's trip schedule (constant, offline needed)
// - Receive booking alerts and notifications (constant, push needed)
// - Quick communication with customer (frequent)
// - Update trip status on-the-go (frequent)
// - Access traveler documents in emergency (occasional, offline needed)
// - Photo upload for site inspections (occasional, camera needed)
// - GPS-based transfer tracking (occasional, location needed)

// Customer use cases:
// - View itinerary and vouchers (frequent, offline needed)
// - Receive trip updates and alerts (frequent, push needed)
// - Contact support (occasional)
// - Access boarding passes and tickets (frequent, offline needed)
// - Share trip on social media (occasional)
// - Submit feedback and photos (occasional, camera)
```

### Platform Comparison

| Approach | Pros | Cons | Cost | Reach |
|----------|------|------|------|-------|
| **Responsive web** | Single codebase, instant updates, no install | Limited native features, no offline | Low | Universal |
| **PWA** | Offline, push, install-like, single codebase | Limited iOS support, no background sync | Medium | Android-first |
| **React Native** | Native feel, shared code, full capabilities | Two builds, app store approval, native dev needed | High | Full |
| **Flutter** | Consistent UI, single codebase, full capabilities | Large app size, Dart ecosystem, new team skill | High | Full |
| **Native (Swift/Kotlin)** | Best performance, all native APIs | Two codebases, two teams | Very High | Full |

```typescript
interface PlatformDecision {
  chosen: 'pwa_first' | 'react_native' | 'responsive_only';
  rationale: string;
  phase1: string;               // Launch with this
  phase2?: string;              // Expand to this
  nativeFeaturesNeeded: NativeFeature[];
}

type NativeFeature =
  | 'push_notifications'
  | 'offline_access'
  | 'camera_access'
  | 'location_services'
  | 'biometric_auth'
  | 'background_sync'
  | 'contact_access'
  | 'calendar_integration'
  | 'apple_wallet'              // iOS boarding passes
  | 'google_pay';               // Android boarding passes
```

---

## Open Problems

1. **PWA limitations on iOS** — iOS Safari still has limited PWA support (no push in background, 50MB storage limit). Major constraint for Apple users.

2. **Offline data complexity** — Caching itinerary data for offline access means syncing when back online. Conflict resolution for changes made offline.

3. **App store vs. web distribution** — App stores provide discovery but add friction (download, update). Web is instant but less "present" on the device.

4. **Mobile agent experience** — Agents may prefer mobile for quick tasks but need desktop for complex bookings. How to design complementary experiences?

5. **Performance on low-end devices** — Target users in India may have budget Android phones. Heavy React Native or web apps may perform poorly.

---

## Next Steps

- [ ] Audit mobile web traffic and device breakdown for current users
- [ ] Research PWA capabilities on iOS Safari (latest status)
- [ ] Study travel app mobile strategies (MakeMyTrip, Goibbih, Booking.com)
- [ ] Design mobile use case priority matrix for agents and customers
- [ ] Evaluate React Native vs. PWA for a proof-of-concept
