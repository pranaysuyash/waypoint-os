import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Check your itinerary before you book — Waypoint",
  description: "Paste or upload your travel plan to review flagged details and see what to confirm before booking.",
  openGraph: {
    title: "Check your itinerary before you book — Waypoint",
    description: "Paste or upload your travel plan to review flagged details and see what to confirm before booking.",
    type: "website",
    url: "https://waypoint.app/itinerary-checker",
  },
  twitter: {
    card: "summary_large_image",
    title: "Check your itinerary before you book — Waypoint",
    description: "Paste or upload your travel plan to review flagged details and see what to confirm before booking.",
  },
};

export default function Page() {
  return <PageClient />;
}
