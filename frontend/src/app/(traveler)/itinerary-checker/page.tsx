import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Free Itinerary Health Check & Perks Radar — Waypoint",
  description: "Sanity check your DIY or ChatGPT trip: calculate layover connection risks, pacing burnout curves, and discover unclaimed luxury amenities.",
  openGraph: {
    title: "Free Itinerary Health Check & Perks Radar — Waypoint",
    description: "Catch impossible 50-minute airport connections, circadian exhaustion traps, and unlock hundreds in complimentary hotel privileges.",
    type: "website",
    url: "https://waypoint.app/itinerary-checker",
  },
  twitter: {
    card: "summary_large_image",
    title: "Free Itinerary Health Check & Perks Radar — Waypoint",
    description: "Check layover stress, pacing fatigue, and unclaimed VIP perks before you book.",
  },
};

export default function Page() {
  return <PageClient />;
}
