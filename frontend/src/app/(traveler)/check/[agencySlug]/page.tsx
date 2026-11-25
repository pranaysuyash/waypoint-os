import type { Metadata } from 'next';
import Link from 'next/link';
import { cache } from 'react';
import ClientWrapper from './ClientWrapper';
import type { AgencyBrandingContext } from '../../itinerary-checker/PageClient';

const BACKEND_BASE = process.env.SPINE_API_URL || 'http://localhost:8000';
type AgencyLookup =
  | { state: 'found'; agency: AgencyBrandingContext }
  | { state: 'missing' | 'unavailable' };

const fetchAgencyProfile = cache(async (slug: string): Promise<AgencyLookup> => {
  try {
    const response = await fetch(`${BACKEND_BASE}/api/public-checker/agency/${encodeURIComponent(slug)}`, {
      next: { revalidate: 60 },
    });
    if (response.status === 404) return { state: 'missing' };
    if (response.ok) {
      const data = await response.json();
      if (data.ok && data.agency?.agency_id && data.agency?.display_name) {
        return { state: 'found', agency: { ...data.agency, slug } };
      }
    }
  } catch {
    return { state: 'unavailable' };
  }
  return { state: 'unavailable' };
});

export async function generateMetadata({ params }: { params: { agencySlug: string } }): Promise<Metadata> {
  const result = await fetchAgencyProfile(params.agencySlug);
  if (result.state !== 'found') return { title: 'Advisor itinerary check — Waypoint', robots: { index: false } };

  const title = `Check your itinerary with ${result.agency.display_name} — Waypoint`;
  const description = 'Review itinerary findings and choose whether to request follow-up from your advisor.';
  return {
    title,
    description,
    openGraph: { title, description, type: 'website' },
    twitter: { card: 'summary_large_image', title, description },
  };
}

export default async function Page({ params }: { params: { agencySlug: string } }) {
  const result = await fetchAgencyProfile(params.agencySlug);
  if (result.state === 'found') return <ClientWrapper agencyContext={result.agency} />;

  return (
    <main className='mx-auto max-w-xl px-6 py-16'>
      <h1 className='mb-4 text-3xl font-semibold'>
        {result.state === 'missing' ? 'Advisor link not found' : 'Advisor check temporarily unavailable'}
      </h1>
      <p className='mb-6'>
        {result.state === 'missing'
          ? 'Check the link with your advisor, or run an independent itinerary check.'
          : 'Try the advisor link again later, or run an independent itinerary check.'}
      </p>
      <Link className='underline underline-offset-4' href='/itinerary-checker'>Open the public itinerary checker</Link>
    </main>
  );
}
