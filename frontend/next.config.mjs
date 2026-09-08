import { PHASE_DEVELOPMENT_SERVER } from 'next/constants.js';

/**
 * @param {string} phase
 * @returns {import('next').NextConfig}
 */
const nextConfig = (phase) => ({
  // Keep the long-lived dev server's incremental output out of the production
  // build/start directory. Production packaging remains rooted at `.next`.
  distDir: phase === PHASE_DEVELOPMENT_SERVER ? '.next-dev' : '.next',
  compress: true,
  output: 'standalone',
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  logging: {
    fetches: {
      fullUrl: false,
    },
  },
  productionBrowserSourceMaps: false,
  poweredByHeader: false,
  // F-43 (2026-09-07): the former /api/v1/* and /api/public/* wildcard
  // rewrites bypassed the BFF route-map allowlist, so any browser could reach
  // arbitrary spine routes auth-free. All consumers now route through the
  // explicit /api/[...path] catch-all allowlist in src/lib/route-map.ts —
  // do not reintroduce wildcard rewrites without re-running the route-map
  // honesty tests.
});

export default nextConfig;
