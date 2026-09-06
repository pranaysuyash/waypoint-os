/** @type {import('next').NextConfig} */
const nextConfig = {
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
  async rewrites() {
    const spineApiUrl = process.env.SPINE_API_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/v1/:path*',
        destination: `${spineApiUrl}/api/v1/:path*`,
      },
      {
        source: '/api/public/:path*',
        destination: `${spineApiUrl}/api/public/:path*`,
      },
    ];
  },
};

export default nextConfig;
