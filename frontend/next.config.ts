import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Performance optimizations
  compress: true, // Enable gzip compression

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Experimental features for performance
  experimental: {
    optimizePackageImports: ['lucide-react'], // Optimize lucide-react imports
  },

  // Turbopack configuration (Next.js 16+)
  turbopack: {
    // Fix: specify root to avoid multiple lockfile warning
    root: __dirname,
  },

  // Logging
  logging: {
    fetches: {
      fullUrl: false,
    },
  },

  // Production source maps (disabled for smaller builds)
  productionBrowserSourceMaps: false,

  // Power by headers
  poweredByHeader: false,
};

export default nextConfig;
