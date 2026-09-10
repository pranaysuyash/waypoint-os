import type { MetadataRoute } from 'next';

// GO punch-list item 4: public pages only. The checker is the funnel's front
// door (WOBS Part 3: open-verifier exposure); authed surfaces stay out.
const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'https://waypointos.app').replace(/\/$/, '');

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: 'weekly', priority: 1 },
    { url: `${SITE_URL}/itinerary-checker`, lastModified: now, changeFrequency: 'daily', priority: 0.9 },
    { url: `${SITE_URL}/pricing`, lastModified: now, changeFrequency: 'weekly', priority: 0.8 },
    { url: `${SITE_URL}/signup`, lastModified: now, changeFrequency: 'monthly', priority: 0.5 },
    { url: `${SITE_URL}/login`, lastModified: now, changeFrequency: 'monthly', priority: 0.3 },
  ];
}
