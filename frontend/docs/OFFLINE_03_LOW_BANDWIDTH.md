# Offline & Low-Connectivity Mode — Low Bandwidth Optimization

> Research document for bandwidth-aware content delivery, image optimization, progressive loading, and degraded-mode UX.

---

## Key Questions

1. **How do we optimize the platform for low-bandwidth connections?**
2. **What image and media optimization strategies apply?**
3. **How do we progressively load content on slow connections?**
4. **What degraded-mode UX patterns maintain usability?**
5. **How do we measure and improve performance on slow networks?**

---

## Research Areas

### Bandwidth-Aware Content Delivery

```typescript
interface LowBandwidthOptimization {
  detection: ConnectionDetection;
  adaptation: ContentAdaptation;
  images: ImageOptimization;
  progressive: ProgressiveLoading;
  degradation: DegradedMode;
}

interface ConnectionDetection {
  method: DetectionMethod;
  classification: ConnectionClass;
  monitoring: ConnectionMonitor;
}

type ConnectionClass =
  | 'offline'                          // 0 Kbps
  | 'very_slow'                        // <100 Kbps (2G, poor signal)
  | 'slow'                             // 100-500 Kbps (3G, shared WiFi)
  | 'moderate'                         // 500 Kbps - 2 Mbps (4G, broadband)
  | 'fast';                            // >2 Mbps (good broadband, 5G)

// Connection detection methods:
// 1. Network Information API: navigator.connection.effectiveType
//    Returns: 'slow-2g', '2g', '3g', '4g'
//    Limitation: Only available in Chrome/Android
//
// 2. Custom bandwidth test:
//    Download a 10KB probe file, measure time
//    Run on page load and periodically (every 60s)
//    Rolling average over last 3 measurements
//
// 3. Response time monitoring:
//    Track API response times (rolling 10-request average)
//    If average >2s: Classify as slow
//    If average >5s: Classify as very_slow
//
// 4. Failure rate:
//    Track failed requests (timeout, network error)
//    If >10% failure rate in last 5 min: Downgrade classification
//
// Adaptation triggers:
// Connection class changes → Re-evaluate all active content
// Very slow → Aggressive optimization (see below)
// Slow → Moderate optimization
// Moderate → Light optimization
// Fast → Full quality

interface ContentAdaptation {
  dataReduction: DataReductionStrategy[];
  apiOptimization: APIOptimization;
  caching: AdaptiveCache;
}

// Data reduction strategies by connection class:
//
// VERY SLOW (<100 Kbps):
// - Text-only mode: No images, no media
// - Minimal API responses: Only essential fields
// - No background sync: Manual sync only
// - No real-time updates: Poll every 5 minutes
// - Compress all text responses (gzip/brotli)
// - Disable animations and transitions
// - Page size target: <50 KB per page
//
// SLOW (100-500 Kbps):
// - Low-resolution images (200px width max)
// - Lazy load everything below fold
// - Reduced API responses (top 10 results instead of 50)
// - Background sync: Only critical operations
// - Real-time: Poll every 30 seconds (not WebSocket)
// - Page size target: <200 KB per page
//
// MODERATE (500 Kbps - 2 Mbps):
// - Medium-resolution images (400px width)
// - Standard lazy loading
// - Normal API responses
// - Background sync enabled
// - WebSocket for real-time
// - Page size target: <500 KB per page
//
// FAST (>2 Mbps):
// - Full-resolution images
// - Preload below-fold content
// - Full API responses
// - Real-time sync + push
// - Page size target: <2 MB per page

// API optimization for slow connections:
// 1. Response compression: Always gzip/brotli
// 2. Field filtering: ?fields=id,name,destination (omit unnecessary fields)
// 3. Pagination: Smaller pages on slow connections (10 vs 50)
// 4. Delta updates: Only send changed fields (not full entity)
// 5. Request batching: Bundle multiple API calls into one
// 6. GraphQL: Request only needed fields
// 7. Response caching: Longer cache TTL on slow connections
//
// Example: Trip list on slow connection
// Fast connection response (50 trips, all fields):
// { trips: [{ id, destination, customer, dates, price, status, hotel, flight, activities, notes, ... }] }
// Size: ~150 KB
//
// Slow connection response (10 trips, essential fields):
// { trips: [{ id, destination, customerName, dates, price, status }] }
// Size: ~8 KB (94% reduction)
//
// Tap to load full details: GET /api/trips/TRV-45678?fields=hotel,flight

// Image optimization:
interface ImageOptimization {
  responsive: ResponsiveImages;
  format: ImageFormatOptimization;
  lazy: LazyLoading;
  placeholder: ImagePlaceholder;
}

// Responsive images:
// Generate multiple sizes at upload time:
// - Thumbnail: 200px wide, WebP, quality 60 (<10KB)
// - Small: 400px wide, WebP, quality 70 (<30KB)
// - Medium: 800px wide, WebP, quality 80 (<80KB)
// - Large: 1600px wide, WebP, quality 85 (<200KB)
// - Original: As uploaded
//
// Serve appropriate size based on connection class:
// Very slow: Thumbnail only (or skip entirely)
// Slow: Small images
// Moderate: Medium images
// Fast: Large images
//
// Format optimization:
// - WebP: 30% smaller than JPEG at same quality
// - AVIF: 50% smaller than JPEG (limited browser support)
// - JPEG fallback for older browsers
// - SVG for icons and logos (scalable, tiny file size)
//
// Lazy loading:
// - Images below fold: loading="lazy" attribute
// - On slow connections: Only load images in viewport
// - Intersection Observer: Load when within 200px of viewport
// - On very slow: Don't load until user explicitly taps "Show image"
//
// Placeholder strategy:
// - BlurHash: Compact image placeholder (20-30 characters)
//   Renders a blurry colored version instantly
// - LQIP (Low Quality Image Placeholder): 10px wide, blurred
// - Color block: Single dominant color as background
// - Skeleton: Gray rectangle with loading animation

// Progressive loading patterns:
// 1. Shell first: Render page layout (HTML/CSS) instantly from cache
// 2. Text second: Load text content from cache or fast API
// 3. Images third: Load images progressively as bandwidth allows
// 4. Media last: Videos, animations only on fast connections
// 5. Interactive: Page is interactive after step 2 (text loaded)
//
// Progressive trip detail page:
// ┌─────────────────────────────────────────┐
// │  ← Back    Kerala Trip     [⋅⋅⋅]         │  ← Instant (cached shell)
// │                                            │
// │  ████████████████████████                  │  ← Image placeholder
// │                                            │
// │  Kerala Backwaters                         │  ← Instant (cached text)
// │  Dec 15-20, 2026 · 2 travelers            │
// │  Status: Confirmed                         │
// │                                            │
// │  Hotel: Taj Residency...                   │  ← Loads from cache
// │  Flight: AI-123 Delhi→Kochi...            │
// │                                            │
// │  [View Itinerary] [Contact Agent]          │  ← Interactive immediately
// │                                            │
// │  [Loading activities...]                   │  ← Progressive (3s)
// │  [Loading map...]                          │  ← Progressive (5s)
// └─────────────────────────────────────────────┘

// Degraded mode UX:
interface DegradedMode {
  offline: OfflineUX;
  slowConnection: SlowConnectionUX;
  features: FeatureDegradation;
}

// Offline banner UI:
// ┌─────────────────────────────────────────┐
// │  📴 You're offline                         │
// │  Changes will sync when you reconnect.     │
// │  5 pending changes · Last synced 12 min ago│
// └─────────────────────────────────────────────┘
//
// Slow connection banner:
// ┌─────────────────────────────────────────┐
// │  🐌 Slow connection detected              │
// │  Using optimized mode. [Switch to full]    │
// └─────────────────────────────────────────────┘
//
// Feature degradation table:
// Feature            | Fast     | Moderate  | Slow      | Very Slow  | Offline
// -------------------|----------|-----------|-----------|------------|--------
// Trip list          | 50/page  | 25/page   | 10/page   | 5/page     | Cached
// Trip detail        | Full     | Full      | Essential | Essential  | Cached
// Images             | Full res | Medium    | Small     | Thumbnails | Cached
// Search             | Full     | Full      | Limited   | Text only  | Local only
// Messages           | Realtime | Realtime  | Poll 30s  | Poll 60s   | Queue
// Notifications      | Push     | Push      | Poll 30s  | Poll 60s   | None
// Analytics          | Full     | Full      | Summary   | Hidden     | Hidden
// Document gen       | Full     | Full      | Full      | Deferred   | Deferred
// Map                | Full     | Full      | Static    | Hidden     | Cached
// Voice/Video        | Full     | Full      | Audio only| Disabled   | Disabled
```

---

## Open Problems

1. **Detection accuracy** — Network Information API doesn't work on iOS/Safari. Custom bandwidth tests add latency on already slow connections. Finding the balance between detection accuracy and overhead is difficult.

2. **Image quality vs. speed** — Overly aggressive image compression makes destination photos look unappealing, hurting conversion. The tourism business relies on beautiful imagery; degrading it too much undermines the product.

3. **Feature parity communication** — Users on slow connections may not understand why some features are missing. Clear, non-technical explanations are needed ("Showing key details to load faster" rather than "API response truncated").

4. **Testing on real networks** — Simulating slow networks in development (Chrome DevTools throttle) doesn't capture real-world conditions (packet loss, variable latency, DNS delays). Real device testing on actual 3G connections is essential but expensive.

5. **Progressive loading complexity** — Building a truly progressive experience (shell → text → images → full) requires significant frontend engineering. Each component needs loading states, fallbacks, and connection-aware behavior.

---

## Next Steps

- [ ] Implement connection detection with adaptive content delivery
- [ ] Build responsive image pipeline with WebP/AVIF optimization
- [ ] Create progressive loading shell with text-first rendering
- [ ] Design feature degradation matrix with graceful UX for each level
- [ ] Study low-bandwidth optimization (Google Web Fundamentals, AMP, Facebook Lite, Lite Mode)
