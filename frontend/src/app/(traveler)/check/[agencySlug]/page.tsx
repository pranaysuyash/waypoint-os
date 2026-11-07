import type { Metadata } from 'next';
import ClientWrapper from './ClientWrapper';
import type { AgencyBrandingContext } from '../../itinerary-checker/PageClient';

const BACKEND_BASE = process.env.SPINE_API_URL || 'http://localhost:8000';

async function fetchAgencyProfile(slugOrId: string): Promise<AgencyBrandingContext | null> {
  try {
    const res = await fetch(`${BACKEND_BASE}/api/public-checker/agency/${encodeURIComponent(slugOrId)}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.ok && data.agency ? data.agency : null;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { agencySlug: string };
}): Promise<Metadata> {
  const agency = await fetchAgencyProfile(params.agencySlug);
  if (!agency) {
    return {
      title: 'Travel Plan Diagnostic — Waypoint',
      description: 'Check travel quality, airport layover stress, pacing burnout, and unclaimed hotel amenities.',
    };
  }

  return {
    title: `Travel Plan Diagnostic — ${agency.display_name}`,
    description: agency.blurb || `Complimentary itinerary audit and VIP perks check curated by ${agency.display_name}.`,
    openGraph: {
      title: `Travel Plan Diagnostic — ${agency.display_name}`,
      description: agency.blurb || `Complimentary itinerary audit and VIP perks check curated by ${agency.display_name}.`,
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Travel Plan Diagnostic — ${agency.display_name}`,
      description: `Complimentary travel diagnostic by ${agency.display_name}.`,
    },
  };
}

export default async function Page({
  params,
}: {
  params: { agencySlug: string };
}) {
  const agency = await fetchAgencyProfile(params.agencySlug);
  return <ClientWrapper agencyContext={agency} />;
}
