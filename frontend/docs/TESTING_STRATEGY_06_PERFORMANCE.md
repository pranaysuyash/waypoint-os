# Testing Strategy Part 6: Performance Testing

> Lighthouse CI, bundle analysis, load testing, and performance budgets

**Series:** Testing Strategy
**Previous:** [Part 5: Visual Regression](./TESTING_STRATEGY_05_VISUAL.md)
**Next:** N/A (Series Complete)

---

## Table of Contents

1. [Performance Philosophy](#performance-philosophy)
2. [Performance Budgets](#performance-budgets)
3. [Lighthouse CI](#lighthouse-ci)
4. [Bundle Analysis](#bundle-analysis)
5. [Load Testing](#load-testing)
6. [Core Web Vitals](#core-web-vitals)
7. [Monitoring](#monitoring)

---

## Performance Philosophy

### Performance as a Feature

For a travel agency platform, **performance directly impacts revenue**:

| Metric | Impact | Target |
|--------|--------|--------|
| **LCP** | Booking conversion | < 2.5s |
| **FID** | User engagement | < 100ms |
| **CLS** | Form abandonment | < 0.1 |
| **TTI** | Return rate | < 3.5s |

### Performance Testing Pyramid

```
              ┌──────────────────┐
              │  Real User       │
              │  Monitoring      │  Continuous
              └──────────────────┘
              ┌──────────────────┐
              │  Load Testing    │
              │  (k6, Artillery) │  Weekly
              └──────────────────┘
              ┌──────────────────┐
              │  Lighthouse CI   │
              │  (Every PR)      │  Per PR
              └──────────────────┘
              ┌──────────────────┐
              │  Bundle Analysis │
              │  (Every build)   │  Per Build
              └──────────────────┘
```

---

## Performance Budgets

### Budget Configuration

```javascript
// .github/lighthouse-config.json

{
  "ci": {
    "collect": {
      "url": [
        "http://localhost:3000",
        "http://localhost:3000/login",
        "http://localhost:3000/booking/new",
        "http://localhost:3000/trips/trip-123"
      ],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["error", { "minScore": 0.9 }],
        "categories:seo": ["error", { "minScore": 0.9 }],

        "first-contentful-paint": ["error", { "maxNumericValue": 2000 }],
        "interactive": ["error", { "maxNumericValue": 3500 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-blocking-time": ["error", { "maxNumericValue": 300 }],
        "speed-index": ["error", { "maxNumericValue": 3400 }],

        "resource-summary": {
          "sizes": [
            {
              "resourceType": "script",
              "budget": 300
            },
            {
              "resourceType": "stylesheet",
              "budget": 75
            },
            {
              "resourceType": "total",
              "budget": 500
            },
            {
              "resourceType": "image",
              "budget": 200
            },
            {
              "resourceType": "font",
              "budget": 100
            }
          ]
        }
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

### Budget Enforcement

```typescript
// next.config.js (if using Next.js)

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({
  // Performance budgets
  experimental: {
    optimizeCss: true,
    scrollRestoration: true,
  },

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
  },

  // Compression
  compress: true,

  // SWC minification
  swcMinify: true,
});
```

### Budget by Page Type

```typescript
// performance/budgets.ts

export const performanceBudgets = {
  landing: {
    lcp: 2000,  // ms
    fid: 100,
    cls: 0.1,
    tti: 3500,
    bundleSize: 250, // KB
  },
  booking: {
    lcp: 2500,
    fid: 100,
    cls: 0.1,
    tti: 4000,
    bundleSize: 350,
  },
  dashboard: {
    lcp: 2000,
    fid: 50,
    cls: 0.05,
    tti: 3000,
    bundleSize: 200,
  },
  customerPortal: {
    lcp: 2500,
    fid: 100,
    cls: 0.1,
    tti: 4000,
    bundleSize: 300,
  },
};
```

---

## Lighthouse CI

### CI Configuration

```yaml
# .github/workflows/lighthouse-ci.yml

name: Lighthouse CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lighthouse:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Start server
        run: npm run start &
        # Wait for server to be ready
        - sleep 30

      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v10
        with:
          urls: |
            http://localhost:3000
            http://localhost:3000/login
            http://localhost:3000/booking/new
            http://localhost:3000/trips/trip-123
          uploadArtifacts: true
          temporaryPublicStorage: true
          configPath: ./.github/lighthouse-config.json

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('./lighthouse-results.json', 'utf8'));

            const comment = `## Lighthouse Results

            | Page | Performance | Accessibility | Best Practices | SEO |
            |------|-------------|---------------|----------------|-----|
            | Homepage | ${results[0].categories.performance.score * 100}% | ${results[0].categories.accessibility.score * 100}% | ${results[0].categories['best-practices'].score * 100}% | ${results[0].categories.seo.score * 100}% |
            | Login | ${results[1].categories.performance.score * 100}% | ${results[1].categories.accessibility.score * 100}% | ${results[1].categories['best-practices'].score * 100}% | ${results[1].categories.seo.score * 100}% |
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

### Lighthouse Programmatic

```typescript
// test/performance/lighthouse.test.ts

import { test, expect } from '@playwright/test';
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

interface LighthouseResult {
  scores: {
    performance: number;
    accessibility: number;
    bestPractices: number;
    seo: number;
  };
  metrics: {
    fcp: number;
    lcp: number;
    tti: number;
    cls: number;
    fid: number;
  };
}

async function runLighthouse(url: string): Promise<LighthouseResult> {
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });

  const options = {
    logLevel: 'info' as const,
    output: 'json' as const,
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    port: chrome.port,
  };

  const runnerResult = await lighthouse(url, options);
  await chrome.kill();

  const report = JSON.parse(runnerResult.report);

  return {
    scores: {
      performance: report.categories.performance.score * 100,
      accessibility: report.categories.accessibility.score * 100,
      bestPractices: report.categories['best-practices'].score * 100,
      seo: report.categories.seo.score * 100,
    },
    metrics: {
      fcp: report.audits['first-contentful-paint'].numericValue,
      lcp: report.audits['largest-contentful-paint'].numericValue,
      tti: report.audits['interactive'].numericValue,
      cls: report.audits['cumulative-layout-shift'].numericValue,
      fid: report.audits['max-potential-fid'].numericValue,
    },
  };
}

test.describe('Lighthouse Performance', () => {
  test('homepage meets performance budget', async () => {
    const result = await runLighthouse('http://localhost:3000');

    expect(result.scores.performance).toBeGreaterThanOrEqual(90);
    expect(result.metrics.lcp).toBeLessThan(2500);
    expect(result.metrics.cls).toBeLessThan(0.1);
  });

  test('booking flow pages perform well', async () => {
    const pages = [
      '/booking/new',
      '/booking/123',
      '/trips/trip-123',
    ];

    for (const page of pages) {
      const result = await runLighthouse(`http://localhost:3000${page}`);

      expect(result.scores.performance).toBeGreaterThanOrEqual(85);
      expect(result.metrics.tti).toBeLessThan(4000);
    }
  });
});
```

---

## Bundle Analysis

### Bundle Analyzer Setup

```javascript
// vite.config.ts

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
      filename: 'dist/stats.html',
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Vendor splitting
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react-vendor';
            }
            if (id.includes('@tanstack')) {
              return 'query-vendor';
            }
            if (id.includes('date-fns')) {
              return 'date-vendor';
            }
            return 'vendor';
          }
        },
      },
    },
    chunkSizeWarningLimit: 500,
  },
});
```

### Bundle Size Monitoring

```typescript
// test/performance/bundle-size.test.ts

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

const bundles = [
  { name: 'main', maxSize: 200 }, // KB
  { name: 'react-vendor', maxSize: 150 },
  { name: 'query-vendor', maxSize: 50 },
  { name: 'vendor', maxSize: 200 },
];

describe('Bundle Size', () => {
  bundles.forEach(bundle => {
    it(`${bundle.name}.js should be under ${bundle.maxSize}KB`, () => {
      const path = resolve(__dirname, `../../dist/assets/${bundle.name}-*.js`);
      const glob = require('glob');
      const files = glob.sync(path);

      if (files.length === 0) {
        console.warn(`Bundle ${bundle.name} not found, skipping`);
        return;
      }

      const size = readFileSync(files[0]).length / 1024;

      console.log(`${bundle.name}: ${size.toFixed(2)}KB`);
      expect(size).toBeLessThan(bundle.maxSize);
    });
  });
});
```

### Import Analysis

```typescript
// Performance monitoring utilities

// vite.config.ts - Module preloading
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        // Preload critical chunks
        prefetch: [
          'src/components/BookingForm/BookingForm.lazy.tsx',
          'src/components/PaymentForm/PaymentForm.lazy.tsx',
        ],
      },
    },
  },
});

// Lazy load routes
const BookingForm = lazy(() =>
  import('./components/BookingForm').then(m => ({
    default: m.BookingForm,
  }))
);

// Lazy load heavy components
const Map = lazy(() => import('./components/Map'));
const DatePicker = lazy(() => import('./components/DatePicker'));
```

---

## Load Testing

### k6 Configuration

```javascript
// load-tests/booking-flow.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export const options = {
  scenarios: {
    // Ramp up to normal load
    normal_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },  // Ramp up to 50 users
        { duration: '5m', target: 50 },  // Stay at 50
        { duration: '2m', target: 0 },   // Ramp down
      ],
    },

    // Stress test
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 0 },
      ],
      startTime: '10m',
    },

    // Soak test
    soak_test: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30m',
      startTime: '25m',
    },
  },

  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% under 500ms
    http_req_failed: ['rate<0.01'],                  // <1% errors
    errors: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

export function setup() {
  // Create test users
  const users = [];
  for (let i = 0; i < 100; i++) {
    const email = `loadtest-${i}@example.com`;
    const res = http.post(`${BASE_URL}/api/auth/register`, JSON.stringify({
      email,
      password: 'test-password',
      name: `Load Test User ${i}`,
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    if (res.status === 201) {
      users.push({ email, token: res.json().token });
    }
  }

  return { users };
}

export default function(data) {
  const user = data.users[__VU % data.users.length];

  // Login
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: user.email,
    password: 'test-password',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(loginRes, {
    'login successful': (r) => r.status === 200,
  }) || errorRate.add(1);

  const token = loginRes.json().token;

  // Browse bookings
  const bookingsRes = http.get(`${BASE_URL}/api/bookings`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  check(bookingsRes, {
    'bookings loaded': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);

  // Create booking
  const createRes = http.post(`${BASE_URL}/api/bookings`, JSON.stringify({
    destination: 'Paris',
    dates: { start: '2025-06-01', end: '2025-06-07' },
    guests: 2,
  }), {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  check(createRes, {
    'booking created': (r) => r.status === 201,
  }) || errorRate.add(1);

  sleep(2);
}

export function teardown(data) {
  // Cleanup test users
  console.log(`Load test complete. ${data.users.length} users created.`);
}
```

### API Load Tests

```javascript
// load-tests/api-supplier.js

import http from 'k6/http';
import { check, group } from 'k6';

export const options = {
  scenarios: {
    constant_load: {
      executor: 'constant-vus',
      vus: 20,
      duration: '5m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<300'],
    http_req_failed: ['rate<0.02'],
  },
};

const SUPPLIER_API = 'https://api.supplier.com';

export default function() {
  group('Hotel Search', () => {
    const res = http.get(`${SUPPLIER_API}/v1/hotels?destination=Paris&checkIn=2025-06-01&checkOut=2025-06-07&guests=2`);

    check(res, {
      'status is 200': (r) => r.status === 200,
      'has results': (r) => r.json('hotels').length > 0,
      'response time < 500ms': (r) => r.timings.duration < 500,
    });
  });

  group('Hotel Details', () => {
    const res = http.get(`${SUPPLIER_API}/v1/hotels/hotel-123`);

    check(res, {
      'status is 200': (r) => r.status === 200,
      'has name': (r) => r.json('name') !== undefined,
      'response time < 200ms': (r) => r.timings.duration < 200,
    });
  });

  group('Availability Check', () => {
    const res = http.post(`${SUPPLIER_API}/v1/hotels/hotel-123/availability`, JSON.stringify({
      checkIn: '2025-06-01',
      checkOut: '2025-06-07',
      guests: 2,
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    check(res, {
      'status is 200': (r) => r.status === 200,
      'has availability': (r) => r.json('available') === true,
    });
  });
}
```

### Running Load Tests

```bash
# Local testing
k6 run load-tests/booking-flow.js

# With environment variables
BASE_URL=https://staging.travelagency.com k6 run load-tests/booking-flow.js

# Output to InfluxDB/Cloud
k6 cloud run load-tests/booking-flow.js

# Generate HTML report
k6 run --out json=test-results.json load-tests/booking-flow.js
k6-reporter test-results.json --output test-report.html
```

---

## Core Web Vitals

### Real User Monitoring

```typescript
// src/lib/web-vitals.ts

import { CLSThresholds, FIDThresholds, LCPThresholds, onCLS, onFID, onLCP } from 'web-vitals';

interface VitalMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
}

export function reportWebVitals() {
  const vitals: VitalMetric[] = [];

  onLCP((metric) => {
    const rating = metric.rating as VitalMetric['rating'];
    vitals.push({ name: 'LCP', value: metric.value, rating });

    // Send to analytics
    sendToAnalytics({
      metric: 'LCP',
      value: metric.value,
      rating,
      page: window.location.pathname,
    });
  });

  onFID((metric) => {
    const rating = metric.rating as VitalMetric['rating'];
    vitals.push({ name: 'FID', value: metric.value, rating });

    sendToAnalytics({
      metric: 'FID',
      value: metric.value,
      rating,
      page: window.location.pathname,
    });
  });

  onCLS((metric) => {
    const rating = metric.rating as VitalMetric['rating'];
    vitals.push({ name: 'CLS', value: metric.value, rating });

    sendToAnalytics({
      metric: 'CLS',
      value: metric.value,
      rating,
      page: window.location.pathname,
    });
  });
}

function sendToAnalytics(data: any) {
  // Send to your analytics endpoint
  fetch('/api/analytics/vitals', {
    method: 'POST',
    body: JSON.stringify(data),
    keepalive: true,
  });
}
```

### Performance Observer

```typescript
// src/lib/performance-observer.ts

export function initPerformanceObserver() {
  // Long Tasks Observer
  if ('PerformanceObserver' in window) {
    const longTasksObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > 50) {
          console.warn('Long Task detected:', entry);
          sendToAnalytics({
            type: 'long-task',
            duration: entry.duration,
            startTime: entry.startTime,
          });
        }
      }
    });

    longTasksObserver.observe({ entryTypes: ['longtask'] });

    // Layout Shift Observer (custom tracking)
    const layoutShiftObserver = new PerformanceObserver((list) => {
      let clsScore = 0;

      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsScore += (entry as any).value;
        }
      }

      if (clsScore > 0) {
        sendToAnalytics({
          type: 'layout-shift',
          score: clsScore,
        });
      }
    });

    layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });

    // Element Timing Observer
    const elementTimingObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.identifier.includes('hero')) {
          sendToAnalytics({
            type: 'hero-timing',
            identifier: entry.identifier,
            renderTime: entry.startTime,
          });
        }
      }
    });

    elementTimingObserver.observe({ entryTypes: ['element'] });
  }
}
```

---

## Monitoring

### Performance Dashboard Metrics

```typescript
// lib/analytics/performance-metrics.ts

export interface PerformanceDashboard {
  pageViews: {
    total: number;
    unique: number;
  };

  coreWebVitals: {
    lcp: {
      good: number;      // < 2.5s
      needsImprovement: number; // 2.5s - 4s
      poor: number;      // > 4s
    };
    fid: {
      good: number;      // < 100ms
      needsImprovement: number; // 100ms - 300ms
      poor: number;      // > 300ms
    };
    cls: {
      good: number;      // < 0.1
      needsImprovement: number; // 0.1 - 0.25
      poor: number;      // > 0.25
    };
  };

  pageLoadTimes: {
    p50: number;  // Median
    p75: number;
    p95: number;
    p99: number;
  };

  errorRate: number;

  uptime: number;
}

// Aggregation query for dashboard
export async function getPerformanceMetrics(
  startDate: Date,
  endDate: Date
): Promise<PerformanceDashboard> {
  // Query analytics database
  const metrics = await db.query.analytics.findMany({
    where: between(timestamp, startDate, endDate),
  });

  return {
    pageViews: calculatePageViews(metrics),
    coreWebVitals: calculateCoreWebVitals(metrics),
    pageLoadTimes: calculatePercentiles(metrics, 'pageLoadTime'),
    errorRate: calculateErrorRate(metrics),
    uptime: calculateUptime(metrics),
  };
}
```

### Alerting Rules

```typescript
// monitoring/alerts.ts

export const performanceAlerts = {
  // Web Vitals alerts
  lcpThreshold: 2500, // ms
  fidThreshold: 100,
  clsThreshold: 0.1,

  // Error rate alerts
  errorRateWarning: 0.01, // 1%
  errorRateCritical: 0.05, // 5%

  // Response time alerts
  responseTimeWarning: 1000, // ms
  responseTimeCritical: 3000,

  // Uptime alerts
  uptimeWarning: 99.9, // %
  uptimeCritical: 99.5,

  // Check interval
  checkInterval: 60000, // 1 minute
};

export function checkThresholds(metrics: PerformanceDashboard) {
  const alerts = [];

  // LCP check
  if (metrics.coreWebVitals.lcp.poor > 0.1) {
    alerts.push({
      severity: 'warning',
      metric: 'LCP',
      message: 'LCP in poor state for >10% of users',
    });
  }

  // Error rate check
  if (metrics.errorRate > performanceAlerts.errorRateWarning) {
    alerts.push({
      severity: 'critical',
      metric: 'errorRate',
      message: `Error rate at ${(metrics.errorRate * 100).toFixed(2)}%`,
    });
  }

  // Response time check
  if (metrics.pageLoadTimes.p95 > performanceAlerts.responseTimeWarning) {
    alerts.push({
      severity: 'warning',
      metric: 'responseTime',
      message: `P95 response time: ${metrics.pageLoadTimes.p95}ms`,
    });
  }

  return alerts;
}
```

---

## Summary

Performance testing strategy for the travel agency platform:

- **Lighthouse CI** on every PR for automated performance regression
- **Performance budgets** enforced for bundle size and Core Web Vitals
- **Bundle analysis** to catch size regressions
- **Load testing** with k6 for API and booking flow capacity
- **Real User Monitoring** for production performance data
- **Alerting** on performance degradation

**Target Metrics:**
- LCP: < 2.5s (90th percentile)
- FID: < 100ms (90th percentile)
- CLS: < 0.1 (90th percentile)
- TTI: < 3.5s (90th percentile)
- Error rate: < 1%

---

**Series Complete!** See [Testing Strategy Master Index](./TESTING_STRATEGY_MASTER_INDEX.md)
