# Performance & Scalability Part 2: Frontend Optimization

> Code splitting, lazy loading, caching, and resource optimization

**Series:** Performance & Scalability
**Previous:** [Part 1: Performance Architecture](./PERFORMANCE_SCALABILITY_01_ARCHITECTURE.md)
**Next:** [Part 3: Backend Performance](./PERFORMANCE_SCALABILITY_03_BACKEND.md)

---

## Table of Contents

1. [Code Splitting](#code-splitting)
2. [Lazy Loading](#lazy-loading)
3. [Image Optimization](#image-optimization)
4. [CSS Optimization](#css-optimization)
5. [JavaScript Optimization](#javascript-optimization)
6. [Resource Prioritization](#resource-prioritization)
7. [Caching Strategies](#caching-strategies)

---

## Code Splitting

### Route-Based Splitting

```typescript
// App.tsx - Route-based code splitting

import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// Lazy load routes
const LandingPage = lazy(() => import('./pages/LandingPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const BookingNew = lazy(() => import('./pages/BookingNew'));
const BookingDetail = lazy(() => import('./pages/BookingDetail'));
const CustomerPortal = lazy(() => import('./pages/CustomerPortal'));

// Loading fallback
const PageLoader = () => (
  <div className="page-loader">
    <Spinner />
    <p>Loading...</p>
  </div>
);

export function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/booking/new" element={<BookingNew />} />
        <Route path="/booking/:id" element={<BookingDetail />} />
        <Route path="/portal/*" element={<CustomerPortal />} />
      </Routes>
    </Suspense>
  );
}
```

### Component-Based Splitting

```typescript
// Heavy components lazy loaded

import { lazy, Suspense, useState } from 'react';

// Lazy load heavy components
const MapView = lazy(() => import('./components/MapView'));
const DatePicker = lazy(() => import('./components/DatePicker'));
const RichTextEditor = lazy(() => import('./components/RichTextEditor'));
const ImageGallery = lazy(() => import('./components/ImageGallery'));

export function BookingForm() {
  const [showMap, setShowMap] = useState(false);
  const [showGallery, setShowGallery] = useState(false);

  return (
    <form>
      {/* Immediate load */}
      <input name="destination" placeholder="Destination" />
      <input name="dates" placeholder="Dates" />

      {/* Lazy load on interaction */}
      {showMap && (
        <Suspense fallback={<MapSkeleton />}>
          <MapView destination={formData.destination} />
        </Suspense>
      )}

      {/* Lazy load when needed */}
      {showGallery && (
        <Suspense fallback={<GallerySkeleton />}>
          <ImageGallery bookingId={bookingId} />
        </Suspense>
      )}

      <button type="button" onClick={() => setShowMap(true)}>
        Show Map
      </button>
    </form>
  );
}
```

### Vendor Splitting

```typescript
// vite.config.ts

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // React and ReactDOM
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react-vendor';
          }

          // TanStack Query
          if (id.includes('node_modules/@tanstack')) {
            return 'query-vendor';
          }

          // Router
          if (id.includes('node_modules/react-router')) {
            return 'router-vendor';
          }

          // UI library
          if (id.includes('node_modules/@radix-ui')) {
            return 'ui-vendor';
          }

          // Date handling
          if (id.includes('node_modules/date-fns')) {
            return 'date-vendor';
          }

          // Other node_modules
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
  },
});
```

---

## Lazy Loading

### Intersection Observer Lazy Load

```typescript
// src/hooks/useLazyLoad.ts

import { useEffect, useRef, useState } from 'react';

interface UseLazyLoadOptions {
  rootMargin?: string;
  threshold?: number;
  triggerOnce?: boolean;
}

export function useLazyLoad(
  options: UseLazyLoadOptions = {}
) {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const elementRef = useRef<Element | null>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true);

          // Trigger once if configured
          if (options.triggerOnce) {
            observer.disconnect();
          }
        }
      },
      {
        rootMargin: options.rootMargin || '200px',
        threshold: options.threshold || 0.1,
      }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [options.rootMargin, options.threshold, options.triggerOnce]);

  return [elementRef, isIntersecting] as const;
}

// Usage
export function LazyImage({ src, alt, ...props }) {
  const [ref, isVisible] = useLazyLoad({ rootMargin: '200px', triggerOnce: true });

  return (
    <div ref={ref} {...props}>
      {isVisible ? (
        <img src={src} alt={alt} loading="lazy" />
      ) : (
        <div className="skeleton-image" />
      )}
    </div>
  );
}
```

### Progressive Image Loading

```typescript
// src/components/ProgressiveImage.tsx

import { useState, useRef, useEffect } from 'react';

interface ProgressiveImageProps {
  src: string;
  placeholder: string;
  alt: string;
  className?: string;
}

export function ProgressiveImage({
  src,
  placeholder,
  alt,
  className,
}: ProgressiveImageProps) {
  const [imgSrc, setImgSrc] = useState(placeholder);
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    // Check if image is already cached
    const img = new Image();
    img.src = src;

    if (img.complete) {
      setImgSrc(src);
      setLoaded(true);
      return;
    }

    // Load high-res image
    img.onload = () => {
      setImgSrc(src);
      setLoaded(true);
    };

    // Start loading
    img.src = src;
  }, [src]);

  return (
    <img
      ref={imgRef}
      src={imgSrc}
      alt={alt}
      className={className}
      style={{
        filter: loaded ? 'none' : 'blur(10px)',
        transition: 'filter 0.3s ease',
      }}
      loading="lazy"
    />
  );
}
```

---

## Image Optimization

### Next.js Image Component Pattern

```typescript
// src/components/OptimizedImage.tsx

import { useState } from 'react';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  priority?: boolean;
  className?: string;
}

export function OptimizedImage({
  src,
  alt,
  width,
  height,
  priority = false,
  className,
}: OptimizedImageProps) {
  const [imageSrc, setImageSrc] = useState(
    getOptimizedSrc(src, { width, height, quality: 85, format: 'webp' })
  );

  return (
    <img
      src={imageSrc}
      alt={alt}
      width={width}
      height={height}
      loading={priority ? 'eager' : 'lazy'}
      decoding={priority ? 'sync' : 'async'}
      className={className}
      onError={() => {
        // Fallback to original on error
        setImageSrc(src);
      }}
      srcSet={generateSrcSet(src, width, height)}
    />
  );
}

function getOptimizedSrc(
  src: string,
  options: { width?: number; height?: number; quality: number; format: string }
): string {
  const url = new URL(src, 'https://cdn.travelagency.com');
  url.searchParams.set('format', options.format);
  url.searchParams.set('quality', options.quality.toString());

  if (options.width) {
    url.searchParams.set('w', options.width.toString());
  }
  if (options.height) {
    url.searchParams.set('h', options.height.toString());
  }

  return url.toString();
}

function generateSrcSet(src: string, width?: number, height?: number): string {
  const sizes = [320, 640, 960, 1280, 1920];
  const baseUrl = new URL(src, 'https://cdn.travelagency.com');

  return sizes
    .filter(size => !width || size <= width)
    .map(size => {
      const url = new URL(baseUrl);
      url.searchParams.set('w', size.toString());
      url.searchParams.set('format', 'webp');
      return `${url.toString()} ${size}w`;
    })
    .join(', ');
}
```

### Responsive Images

```typescript
// src/components/ResponsiveImage.tsx

export function ResponsiveImage({
  src,
  alt,
  sizes = '100vw',
  className,
}: {
  src: string;
  alt: string;
  sizes?: string;
  className?: string;
}) {
  return (
    <picture>
      {/* AVIF for modern browsers */}
      <source
        type="image/avif"
        srcSet={generateSrcSet(src, 'avif')}
        sizes={sizes}
      />

      {/* WebP fallback */}
      <source
        type="image/webp"
        srcSet={generateSrcSet(src, 'webp')}
        sizes={sizes}
      />

      {/* JPEG fallback */}
      <img
        src={src}
        alt={alt}
        srcSet={generateSrcSet(src, 'jpg')}
        sizes={sizes}
        loading="lazy"
        className={className}
      />
    </picture>
  );
}

function generateSrcSet(src: string, format: 'avif' | 'webp' | 'jpg'): string {
  const sizes = [320, 640, 960, 1280, 1920, 2560];
  return sizes
    .map(
      size =>
        `https://cdn.travelagency.com/${src}?w=${size}&f=${format} ${size}w`
    )
    .join(', ');
}
```

---

## CSS Optimization

### Critical CSS

```typescript
// Inline critical CSS for above-the-fold content

// vite.config.ts
import { defineConfig } from 'vite';
import critical from 'rollup-plugin-critical';

export default defineConfig({
  plugins: [
    critical({
      criticalUrl: 'http://localhost:3000',
      criticalBase: 'dist/critical-css',
      criticalPages: [{ uri: 'index.html' }],
      criticalConfig: {
        // Extract above-the-fold CSS
        target: 'body > *:not(script):not(style)',
        dimensions: [
          { width: 320, height: 480 },   // Mobile
          { width: 768, height: 1024 },  // Tablet
          { width: 1920, height: 1080 }, // Desktop
        ],
      },
    }),
  ],
});
```

### Unused CSS Removal

```typescript
// PurgeCSS/Tailwind configuration

// tailwind.config.js
export default {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './public/index.html',
  ],
  safelist: [
    // Dynamic classes
    /^bg-/,
    /^text-/,
    /^p-/,
    /^m-/,
  ],
};
```

### CSS-in-JS Optimization

```typescript
// Use CSS Modules for better tree-shaking

// styles.module.css
.container {
  display: flex;
  gap: 1rem;
}

.button {
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
}

// Component
import styles from './styles.module.css';

export function MyComponent() {
  return (
    <div className={styles.container}>
      <button className={styles.button}>Click me</button>
    </div>
  );
}
```

---

## JavaScript Optimization

### Tree Shaking

```typescript
// ✅ Good: Use named exports for tree-shaking

// utils.ts
export function formatDate(date: Date) { /* ... */ }
export function formatCurrency(amount: number) { /* ... */ }
export function formatNumber(num: number) { /* ... */ }

// Usage - only imports what's used
import { formatDate } from './utils';

// ❌ Bad: Default exports can't be tree-shaken
export default {
  formatDate,
  formatCurrency,
  formatNumber,
};
```

### Memoization

```typescript
// React.memo for expensive components

import { memo } from 'react';

const BookingCard = memo(function BookingCard({ booking }) {
  return (
    <div>
      <h3>{booking.destination}</h3>
      <p>{booking.dates}</p>
    </div>
  );
}, (prev, next) => {
  // Custom comparison
  return (
    prev.booking.id === next.booking.id &&
    prev.booking.status === next.booking.status
  );
});

// useMemo for expensive calculations
function BookingSummary({ bookings }) {
  const total = useMemo(() => {
    return bookings.reduce((sum, b) => sum + b.totalPrice, 0);
  }, [bookings]);

  return <div>Total: ${total}</div>;
}

// useCallback for stable function references
function BookingList({ bookings, onSelect }) {
  const handleSelect = useCallback((id) => {
    onSelect(id);
  }, [onSelect]);

  return (
    <div>
      {bookings.map(b => (
        <BookingCard
          key={b.id}
          booking={b}
          onSelect={handleSelect}
        />
      ))}
    </div>
  );
}
```

### Virtual Scrolling

```typescript
// src/components/VirtualizedList.tsx

import { useRef, useMemo } from 'react';

interface VirtualizedListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export function VirtualizedList<T>({
  items,
  renderItem,
  itemHeight,
  containerHeight,
  overscan = 3,
}: VirtualizedListProps<T>) {
  const scrollTop = useRef(0);

  const visibleRange = useMemo(() => {
    const start = Math.max(0, Math.floor(scrollTop.current / itemHeight) - overscan);
    const end = Math.min(
      items.length,
      Math.ceil((scrollTop.current + containerHeight) / itemHeight) + overscan
    );
    return { start, end };
  }, [items.length, itemHeight, containerHeight, overscan]);

  const totalHeight = items.length * itemHeight;
  const offsetY = visibleRange.start * itemHeight;

  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={(e) => {
        scrollTop.current = e.currentTarget.scrollTop;
      }}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {items.slice(visibleRange.start, visibleRange.end).map((item, index) => (
            <div
              key={visibleRange.start + index}
              style={{ height: itemHeight }}
            >
              {renderItem(item, visibleRange.start + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## Resource Prioritization

### Fetch Priority

```html
<!-- Priority hints for critical resources -->

<!-- Critical CSS - highest priority -->
<link rel="stylesheet" href="critical.css" importance="high" fetchpriority="high" />

<!-- Hero image - high priority -->
<img src="hero.jpg" fetchpriority="high" />

<!-- Below-fold images - low priority -->
<img src="gallery-1.jpg" loading="lazy" fetchpriority="low" />
<img src="gallery-2.jpg" loading="lazy" fetchpriority="low" />

<!-- Preconnect to external origins -->
<link rel="preconnect" href="https://api.travelagency.com" />
<link rel="preconnect" href="https://cdn.travelagency.com" />
<link rel="dns-prefetch" href="https://analytics.travelagency.com" />

<!-- Preload critical resources -->
<link rel="preload" href="font.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
<link rel="preload" href="hero.webp" as="image" type="image/webp" />
```

### Preloading Routes

```typescript
// src/hooks/usePrefetchRoute.ts

export function usePrefetchRoute() {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // Prefetch likely next routes
    const prefetchMap: Record<string, string[]> = {
      '/dashboard': ['/trips', '/bookings'],
      '/trips': ['/trips/[id]'],
      '/booking/new': ['/destinations', '/hotels'],
    };

    const routesToPrefetch = prefetchMap[location.pathname] || [];

    // Defer prefetching to not block initial render
    setTimeout(() => {
      routesToPrefetch.forEach(route => {
        // Trigger webpack chunk loading
        import(`./pages/${route}.tsx`);
      });
    }, 2000);
  }, [location.pathname]);
}
```

### Resource Hints

```typescript
// src/components/Head.tsx

export function DocumentHead() {
  return (
    <>
      {/* DNS lookup for external domains */}
      <link rel="dns-prefetch" href="https://api.stripe.com" />
      <link rel="dns-prefetch" href="https://maps.googleapis.com" />

      {/* Preconnect for likely connections */}
      <link rel="preconnect" href="https://cdn.travelagency.com" crossOrigin="anonymous" />

      {/* Preload critical fonts */}
      <link
        rel="preload"
        href="/fonts/inter.woff2"
        as="font"
        type="font/woff2"
        crossOrigin="anonymous"
      />

      {/* Preload hero image */}
      <link
        rel="preload"
        href="/images/hero-bg.webp"
        as="image"
        type="image/webp"
      />

      {/* Prefetch next page */}
      <link rel="prefetch" href="/dashboard" />
    </>
  );
}
```

---

## Caching Strategies

### HTTP Caching

```typescript
// Service worker for static asset caching

// sw.ts
const CACHE_NAME = 'travel-agency-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

const STATIC_ASSETS = [
  '/',
  '/offline',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// Cache static assets on install
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

// Network-first for HTML, cache-first for assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests - network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Static assets - cache first, network fallback
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Images - cache first with stale-while-revalidate
  if (url.pathname.startsWith('/images/')) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Default - network first
  event.respondWith(networkFirst(request));
});

async function networkFirst(request: Request) {
  const cache = await caches.open(DYNAMIC_CACHE);

  try {
    const response = await fetch(request);
    if (response.ok) {
      await cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    throw new Error('Network failed and no cache available');
  }
}

async function cacheFirst(request: Request) {
  const cache = await caches.open(STATIC_CACHE);
  const cached = await cache.match(request);

  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      await cache.put(request, response.clone());
    }
    return response;
  } catch {
    throw new Error('Network failed');
  }
}

async function staleWhileRevalidate(request: Request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cached = await cache.match(request);

  // Fetch in background
  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  });

  // Return cached immediately if available
  if (cached) {
    return cached;
  }

  return fetchPromise;
}
```

### Browser Storage Caching

```typescript
// src/lib/cache/storage-cache.ts

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in ms
}

class StorageCache<T> {
  constructor(private storage: Storage, private keyPrefix: string) {}

  set(key: string, data: T, ttl: number = 5 * 60 * 1000): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
    };

    this.storage.setItem(`${this.keyPrefix}:${key}`, JSON.stringify(entry));
  }

  get(key: string): T | null {
    const item = this.storage.getItem(`${this.keyPrefix}:${key}`);

    if (!item) {
      return null;
    }

    const entry: CacheEntry<T> = JSON.parse(item);

    // Check if expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.storage.removeItem(`${this.keyPrefix}:${key}`);
      return null;
    }

    return entry.data;
  }

  delete(key: string): void {
    this.storage.removeItem(`${this.keyPrefix}:${key}`);
  }

  clear(): void {
    const keys = Object.keys(this.storage);
    keys.forEach((key) => {
      if (key.startsWith(this.keyPrefix)) {
        this.storage.removeItem(key);
      }
    });
  }
}

// Usage
const apiCache = new StorageCache<any>(localStorage, 'api');
const sessionCache = new StorageCache<any>(sessionStorage, 'session');

// API call with cache
async function fetchWithCache<T>(url: string, ttl?: number): Promise<T> {
  const cacheKey = url;
  const cached = apiCache.get<T>(cacheKey);

  if (cached) {
    return cached;
  }

  const response = await fetch(url);
  const data = await response.json();

  apiCache.set(cacheKey, data, ttl);

  return data;
}
```

---

## Summary

Frontend optimization strategies:

- **Code splitting**: Route-based, component-based, vendor chunks
- **Lazy loading**: Intersection Observer, progressive images
- **Image optimization**: WebP/AVIF, responsive images, CDNs
- **CSS optimization**: Critical CSS, purge unused, CSS modules
- **JavaScript**: Tree shaking, memoization, virtual scrolling
- **Resource prioritization**: Fetch priority, preloading, hints
- **Caching**: Service worker, HTTP cache, localStorage

**Key Targets:**
- Initial JS bundle: < 200KB gzipped
- First Contentful Paint: < 1.5s
- Largest Contentful Paint: < 2.5s
- Time to Interactive: < 3.5s

---

**Next:** [Part 3: Backend Performance](./PERFORMANCE_SCALABILITY_03_BACKEND.md) — Database optimization, caching, and API performance
