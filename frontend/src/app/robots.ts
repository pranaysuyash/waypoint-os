import type { MetadataRoute } from 'next';

// GO punch-list item 4 (WOBS Part 3.7): make the public checker indexable.
// Site URL from NEXT_PUBLIC_SITE_URL; falls back to a relative-compatible host.
const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'https://waypointos.app').replace(/\/$/, '');

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/trips', '/overview', '/inbox', '/settings'],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
